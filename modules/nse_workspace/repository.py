"""Cooperating writers, immutable revisions and a replaceable HEAD pointer."""
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timezone
from functools import wraps
import hashlib
import json
import os
from pathlib import Path
import re
from uuid import uuid4
from nse_contracts.workspace import (
    Project, Revision, WorkspaceCode, WorkspaceError, project_dict, project_from_dict, valid_id, timestamp,
)

MAX_BYTES = 8 * 1024 * 1024


def now():
    return datetime.now(timezone.utc).isoformat()


def later(*values):
    return max(timestamp(v) for v in values).isoformat()


def metadata(function):
    @wraps(function)
    def call(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise WorkspaceError(WorkspaceCode.CORRUPT, 'Invalid committed metadata') from exc
    return call


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def decoded(data):
    def unique_keys(pairs):
        values = {}
        for key, value in pairs:
            if key in values:
                raise ValueError('Duplicate JSON key')
            values[key] = value
        return values
    return json.loads(data.decode('utf-8'), object_pairs_hook=unique_keys)


class JsonProjectRepository:
    def __init__(self, root):
        self.root = Path(root).absolute()

    def initialize(self):
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, project_id):
        valid_id(project_id)
        path = self.root/project_id
        if path.is_symlink():
            raise WorkspaceError(WorkspaceCode.INVALID_DATA, 'Project directory must not be a symbolic link')
        return path

    def _read(self, path, limit=MAX_BYTES):
        if path.is_symlink():
            raise WorkspaceError(WorkspaceCode.CORRUPT, 'Metadata links are not supported')
        with path.open('rb') as stream:
            data = stream.read(limit+1)
        if len(data) > limit:
            raise WorkspaceError(WorkspaceCode.CORRUPT, 'Metadata exceeds supported size')
        return data

    @staticmethod
    def _pointer(value):
        if (not isinstance(value, dict) or set(value) != {'file', 'revision', 'sha256'}
                or type(value['revision']) is not int or value['revision'] < 1
                or not isinstance(value['file'], str)
                or not re.fullmatch(r'r[0-9]+-[0-9a-f]{32}\.json', value['file'])
                or value['file'].split('-')[0] != f"r{value['revision']:08d}"
                or not isinstance(value['sha256'], str)
                or not re.fullmatch(r'[0-9a-f]{64}', value['sha256'])):
            raise ValueError('Invalid revision pointer')
        return value

    @metadata
    def _head(self, path):
        try:
            data = decoded(self._read(path/'HEAD.json', 65536))
        except FileNotFoundError as exc:
            if (path/'.write.lock').exists():
                raise WorkspaceError(WorkspaceCode.BUSY, 'Initial project commit is locked or incomplete') from exc
            code = WorkspaceCode.CORRUPT if path.exists() else WorkspaceCode.NOT_FOUND
            raise WorkspaceError(code, 'Project has no committed HEAD') from exc
        if not isinstance(data, dict) or set(data) != {'schema_version', 'head'}:
            raise ValueError('Invalid HEAD')
        if type(data['schema_version']) is not int or data['schema_version'] != 1:
            raise WorkspaceError(WorkspaceCode.UNSUPPORTED_SCHEMA, 'Unsupported HEAD schema')
        return self._pointer(data['head'])

    @metadata
    def _load(self, path, pointer):
        data = self._read(path/pointer['file'])
        if hashlib.sha256(data).hexdigest() != pointer['sha256']:
            raise WorkspaceError(WorkspaceCode.CORRUPT, 'Revision checksum mismatch')
        value = decoded(data)
        if not isinstance(value, dict) or set(value) != {'schema_version', 'project', 'parent'}:
            raise ValueError('Invalid snapshot envelope')
        if type(value['schema_version']) is not int or value['schema_version'] != 1:
            raise WorkspaceError(WorkspaceCode.UNSUPPORTED_SCHEMA, 'Unsupported snapshot schema')
        project = project_from_dict(value['project'])
        if project.project_id != path.name or project.revision != pointer['revision']:
            raise ValueError('Snapshot identity mismatch')
        parent = value['parent']
        if project.revision == 1:
            if parent is not None:
                raise ValueError('Initial revision cannot have a parent')
        else:
            self._pointer(parent)
            if parent['revision'] != project.revision-1:
                raise ValueError('Invalid parent revision')
        return project, parent

    def read(self, project_id):
        path = self._path(project_id)
        return self._load(path, self._head(path))[0]

    @contextmanager
    def _lock(self, path):
        lock = path/'.write.lock'
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise WorkspaceError(WorkspaceCode.BUSY, 'Project writer lock exists; no automatic unlock') from exc
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(encoded({'pid': os.getpid(), 'token': uuid4().hex, 'created_at': now()}))
                stream.flush()
                os.fsync(stream.fileno())
            yield
        finally:
            # Only remove the lock acquired by this operation, never a stale lock.
            lock.unlink()

    @staticmethod
    def _write_new(path, data):
        with path.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())

    def _replace_head(self, path, pointer):
        temp = path/f'.head-{uuid4().hex}.tmp'
        try:
            self._write_new(temp, encoded({'schema_version': 1, 'head': pointer}))
            os.replace(temp, path/'HEAD.json')
        finally:
            if temp.exists():
                temp.unlink()

    def _commit(self, path, project, parent):
        data = encoded({'schema_version': 1, 'project': project_dict(project), 'parent': parent})
        if len(data) > MAX_BYTES:
            raise ValueError('Project metadata exceeds supported size')
        filename = f'r{project.revision:08d}-{uuid4().hex}.json'
        self._write_new(path/filename, data)
        pointer = {'file': filename, 'revision': project.revision,
                   'sha256': hashlib.sha256(data).hexdigest()}
        self._replace_head(path, pointer)
        return project

    def create(self, project):
        self.initialize()
        path = self._path(project.project_id)
        try:
            path.mkdir()
        except FileExistsError as exc:
            raise WorkspaceError(WorkspaceCode.CONFLICT, 'Project ID already exists') from exc
        with self._lock(path):
            return self._commit(path, project, None)

    def save(self, project):
        path = self._path(project.project_id)
        if not path.is_dir():
            raise WorkspaceError(WorkspaceCode.NOT_FOUND, 'Project does not exist')
        with self._lock(path):
            parent = self._head(path)
            current, _ = self._load(path, parent)
            if project.revision != current.revision:
                raise WorkspaceError(WorkspaceCode.CONFLICT, 'Project changed; reopen before saving')
            if project.created_at != current.created_at:
                raise ValueError('Project creation identity cannot change')
            # Clock rollback must not produce an invalid time ordering.
            updated = later(now(), current.updated_at)
            committed = replace(project, revision=current.revision+1, updated_at=updated)
            return self._commit(path, committed, parent)

    def list_projects(self):
        self.initialize()
        projects = []
        for path in self.root.iterdir():
            if re.fullmatch(r'[0-9a-f]{32}', path.name) and (path.is_dir() or path.is_symlink()):
                projects.append(self.read(path.name))
        return tuple(sorted(projects, key=lambda p: (p.updated_at, p.project_id), reverse=True))

    def history(self, project_id):
        path = self._path(project_id)
        pointer = self._head(path)
        entries = []
        while pointer is not None:
            project, parent = self._load(path, pointer)
            entries.append(Revision(project.revision, project.updated_at, pointer['sha256']))
            pointer = parent
        return tuple(entries)
