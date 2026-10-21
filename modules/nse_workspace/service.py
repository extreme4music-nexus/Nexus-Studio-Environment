"""Public workspace use cases and structured boundary errors."""
from dataclasses import replace
from functools import wraps
import hashlib
from uuid import uuid4
from nse_contracts.workspace import (
    AssetReference, Decision, Project, Session, WorkspaceCode, WorkspaceError,
    project_dict, project_from_dict, valid_id,
)
from .repository import JsonProjectRepository, MAX_BYTES, decoded, encoded, now, later


def boundary(function):
    @wraps(function)
    def call(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except WorkspaceError:
            raise
        except FileNotFoundError as exc:
            raise WorkspaceError(WorkspaceCode.CORRUPT, 'Committed metadata file is missing') from exc
        except OSError as exc:
            raise WorkspaceError(WorkspaceCode.IO_ERROR, 'Workspace IO failed; outcome may require reopening') from exc
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            # Invalid persisted state is marked explicitly by open/history below.
            raise WorkspaceError(WorkspaceCode.INVALID_DATA, 'Invalid workspace data') from exc
    return call


class WorkspaceService:
    def __init__(self, root):
        self.repository = JsonProjectRepository(root)

    @boundary
    def initialize(self):
        self.repository.initialize()

    @boundary
    def create(self, name, creative_brief=''):
        stamp = now()
        return self.repository.create(Project(uuid4().hex, name, creative_brief, 1, stamp, stamp))

    def _read(self, function, *args):
        try:
            return function(*args)
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise WorkspaceError(WorkspaceCode.CORRUPT, 'Invalid committed project metadata') from exc

    @boundary
    def open(self, project_id):
        valid_id(project_id)
        return self._read(self.repository.read, project_id)

    @boundary
    def save(self, project):
        if not isinstance(project, Project):
            raise ValueError('Expected immutable Project DTO')
        return self.repository.save(project)

    @boundary
    def list_projects(self):
        return self._read(self.repository.list_projects)

    @boundary
    def history(self, project_id):
        valid_id(project_id)
        return self._read(self.repository.history, project_id)

    def _current(self, project_id, expected_revision):
        if type(expected_revision) is not int or expected_revision < 1:
            raise ValueError('An expected positive revision is required')
        project = self.open(project_id)
        if project.revision != expected_revision:
            raise WorkspaceError(WorkspaceCode.CONFLICT, 'Project changed; reopen before editing')
        return project

    @boundary
    def update(self, project_id, expected_revision, *, name=None, creative_brief=None):
        project = self._current(project_id, expected_revision)
        return self.save(replace(project, name=project.name if name is None else name,
                                 creative_brief=project.creative_brief if creative_brief is None else creative_brief))

    @boundary
    def add_session(self, project_id, expected_revision, title, summary=''):
        project = self._current(project_id, expected_revision)
        session = Session(uuid4().hex, title, summary, now())
        return self.save(replace(project, sessions=(*project.sessions, session)))

    @boundary
    def add_decision(self, project_id, expected_revision, text, source, session_id=None, status='accepted'):
        project = self._current(project_id, expected_revision)
        decision = Decision(uuid4().hex, text, source, now(), session_id, status)
        return self.save(replace(project, decisions=(*project.decisions, decision)))

    @boundary
    def add_asset(self, project_id, expected_revision, asset: AssetReference):
        project = self._current(project_id, expected_revision)
        return self.save(replace(project, assets=(*project.assets, asset)))

    @boundary
    def export_metadata(self, project_id):
        payload = project_dict(self.open(project_id))
        return encoded({'backup_version': 1, 'project': payload,
                        'sha256': hashlib.sha256(encoded(payload)).hexdigest()})

    @boundary
    def restore_metadata(self, data, expected_revision=None):
        if not isinstance(data, bytes) or len(data) > MAX_BYTES:
            raise ValueError('Invalid backup size or type')
        value = decoded(data)
        if not isinstance(value, dict) or set(value) != {'backup_version', 'project', 'sha256'}:
            raise ValueError('Invalid metadata backup')
        if type(value['backup_version']) is not int or value['backup_version'] != 1:
            raise WorkspaceError(WorkspaceCode.UNSUPPORTED_SCHEMA, 'Unsupported backup version')
        if hashlib.sha256(encoded(value['project'])).hexdigest() != value['sha256']:
            raise WorkspaceError(WorkspaceCode.CORRUPT, 'Backup checksum mismatch')
        project = project_from_dict(value['project'])
        path = self.repository._path(project.project_id)
        if path.exists():
            current = self._current(project.project_id, expected_revision)
            if current.created_at != project.created_at:
                raise WorkspaceError(WorkspaceCode.CONFLICT, 'Backup belongs to another project identity')
            return self.save(replace(project, revision=expected_revision))
        if expected_revision is not None:
            raise WorkspaceError(WorkspaceCode.NOT_FOUND, 'Expected existing project was not found')
        return self.repository.create(replace(project, revision=1, updated_at=later(now(), project.created_at)))
