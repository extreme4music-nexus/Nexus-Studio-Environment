"""Version-one workspace DTOs and the public project service port."""
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import StrEnum
from typing import Protocol
import re

SCHEMA_VERSION = 1


class WorkspaceCode(StrEnum):
    INVALID_DATA = 'invalid_data'
    NOT_FOUND = 'not_found'
    CONFLICT = 'revision_conflict'
    BUSY = 'workspace_busy'
    CORRUPT = 'corrupt_metadata'
    UNSUPPORTED_SCHEMA = 'unsupported_schema'
    IO_ERROR = 'workspace_io_error'
    NOT_RUNNING = 'workspace_not_running'


class WorkspaceError(RuntimeError):
    def __init__(self, code: WorkspaceCode, message: str):
        self.code = code
        super().__init__(message)


def valid_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{32}', value):
        raise ValueError('Expected a lowercase UUID hex identifier')


def text(value, *, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()) or '\x00' in value:
        raise ValueError('Expected valid text')
    value.encode('utf-8')


def timestamp(value):
    text(value)
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError('Timestamp must be UTC and timezone aware')
    return parsed


@dataclass(frozen=True)
class Session:
    session_id: str
    title: str
    summary: str
    created_at: str

    def __post_init__(self):
        valid_id(self.session_id)
        text(self.title)
        text(self.summary, empty=True)
        timestamp(self.created_at)


@dataclass(frozen=True)
class Decision:
    decision_id: str
    text: str
    source: str
    created_at: str
    session_id: str | None = None
    status: str = 'accepted'

    def __post_init__(self):
        valid_id(self.decision_id)
        text(self.text)
        text(self.source)
        timestamp(self.created_at)
        if self.session_id is not None:
            valid_id(self.session_id)
        if self.status not in ('proposed', 'accepted', 'rejected'):
            raise ValueError('Unknown decision status')


@dataclass(frozen=True)
class AssetReference:
    asset_id: str
    name: str
    location: str
    kind: str
    created_at: str
    sha256: str | None = None
    derived_from: tuple[str, ...] = ()

    def __post_init__(self):
        valid_id(self.asset_id)
        text(self.name)
        text(self.location)
        timestamp(self.created_at)
        if self.kind not in ('audio', 'midi', 'document', 'other'):
            raise ValueError('Unknown asset kind')
        if self.sha256 is not None and (not isinstance(self.sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', self.sha256)):
            raise ValueError('Expected SHA-256 hex digest')
        if not isinstance(self.derived_from, tuple):
            raise ValueError('Expected unique source IDs')
        for source in self.derived_from:
            valid_id(source)
        if len(set(self.derived_from)) != len(self.derived_from):
            raise ValueError('Expected unique source IDs')


@dataclass(frozen=True)
class Project:
    project_id: str
    name: str
    creative_brief: str
    revision: int
    created_at: str
    updated_at: str
    sessions: tuple[Session, ...] = ()
    decisions: tuple[Decision, ...] = ()
    assets: tuple[AssetReference, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self):
        valid_id(self.project_id)
        text(self.name)
        text(self.creative_brief, empty=True)
        if type(self.schema_version) is not int or self.schema_version != SCHEMA_VERSION:
            raise ValueError('Unsupported project schema')
        if type(self.revision) is not int or self.revision < 1:
            raise ValueError('Revision must be a positive integer')
        if timestamp(self.updated_at) < timestamp(self.created_at):
            raise ValueError('Project timestamps are out of order')
        for values, cls, field in ((self.sessions, Session, 'session_id'),
                                   (self.decisions, Decision, 'decision_id'),
                                   (self.assets, AssetReference, 'asset_id')):
            if not isinstance(values, tuple) or any(not isinstance(v, cls) for v in values):
                raise ValueError('Invalid project collection')
            if len({getattr(v, field) for v in values}) != len(values):
                raise ValueError('Duplicate IDs in project collection')
        sessions = {s.session_id for s in self.sessions}
        if any(d.session_id is not None and d.session_id not in sessions for d in self.decisions):
            raise ValueError('Decision refers to a session outside this project')
        graph = {a.asset_id: a.derived_from for a in self.assets}
        # Iterative traversal avoids recursion limits on large metadata graphs.
        complete = set()
        for origin in graph:
            pending = [(origin, False)]
            active = set()
            while pending:
                node, exiting = pending.pop()
                if exiting:
                    active.remove(node)
                    complete.add(node)
                    continue
                if node not in graph:
                    raise ValueError('Unknown source asset')
                if node in active:
                    raise ValueError('Cyclic asset provenance')
                if node in complete:
                    continue
                active.add(node)
                pending.append((node, True))
                pending.extend((child, False) for child in reversed(graph[node]))


def project_dict(project: Project) -> dict:
    return asdict(project)


def project_from_dict(value: object) -> Project:
    if not isinstance(value, dict):
        raise ValueError('Project must be an object')
    if type(value.get('schema_version')) is not int or value['schema_version'] != SCHEMA_VERSION:
        raise WorkspaceError(WorkspaceCode.UNSUPPORTED_SCHEMA, 'Unsupported project schema')
    data = dict(value)
    for field, cls in (('sessions', Session), ('decisions', Decision), ('assets', AssetReference)):
        values = data.get(field)
        if not isinstance(values, list):
            raise ValueError('Project collections must be JSON arrays')
        converted = []
        for item in values:
            if not isinstance(item, dict):
                raise ValueError('Collection item must be an object')
            entry = dict(item)
            if cls is AssetReference:
                if not isinstance(entry.get('derived_from'), list):
                    raise ValueError('derived_from must be a JSON array')
                entry['derived_from'] = tuple(entry['derived_from'])
            converted.append(cls(**entry))
        data[field] = tuple(converted)
    return Project(**data)


@dataclass(frozen=True)
class Revision:
    revision: int
    updated_at: str
    sha256: str


class WorkspacePort(Protocol):
    def create(self, name: str, creative_brief: str = '') -> Project: ...
    def open(self, project_id: str) -> Project: ...
    def save(self, project: Project) -> Project: ...
    def list_projects(self) -> tuple[Project, ...]: ...
    def history(self, project_id: str) -> tuple[Revision, ...]: ...
    def update(self, project_id: str, expected_revision: int, *, name: str | None = None,
               creative_brief: str | None = None) -> Project: ...
    def add_session(self, project_id: str, expected_revision: int, title: str, summary: str = '') -> Project: ...
    def add_decision(self, project_id: str, expected_revision: int, text: str, source: str,
                     session_id: str | None = None, status: str = 'accepted') -> Project: ...
    def add_asset(self, project_id: str, expected_revision: int, asset: AssetReference) -> Project: ...
    def export_metadata(self, project_id: str) -> bytes: ...
    def restore_metadata(self, data: bytes, expected_revision: int | None = None) -> Project: ...
