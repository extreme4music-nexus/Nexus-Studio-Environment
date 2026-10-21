"""Public module contracts. No runtime or platform implementation imports."""
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping, Protocol
import re

CONTRACT_MAJOR = 1


class ModuleState(StrEnum):
    REGISTERED = 'registered'
    INITIALIZED = 'initialized'
    RUNNING = 'running'
    STOPPED = 'stopped'
    DISPOSED = 'disposed'
    FAILED = 'failed'


class ErrorCode(StrEnum):
    DUPLICATE_MODULE = 'duplicate_module'
    MISSING_DEPENDENCY = 'missing_dependency'
    DEPENDENCY_CYCLE = 'dependency_cycle'
    CONTRACT_MISMATCH = 'contract_mismatch'
    INVALID_CONFIG = 'invalid_config'
    INVALID_STATE = 'invalid_state'
    INITIALIZE_FAILED = 'initialize_failed'
    START_FAILED = 'start_failed'
    STOP_FAILED = 'stop_failed'
    DISPOSE_FAILED = 'dispose_failed'
    HEALTH_FAILED = 'health_failed'


@dataclass(frozen=True)
class ModuleDescriptor:
    module_id: str
    display_name: str
    version: str
    contract_major: int = CONTRACT_MAJOR
    dependencies: tuple[str, ...] = ()
    capabilities: frozenset[str] = frozenset()

    def __post_init__(self):
        if not isinstance(self.module_id, str) or not re.fullmatch(r'[a-z][a-z0-9_.-]*', self.module_id):
            raise ValueError('module_id must be a stable lowercase identifier')
        if not isinstance(self.display_name, str) or not self.display_name.strip():
            raise ValueError('display_name is required')
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError('version is required')
        if type(self.contract_major) is not int or self.contract_major < 1:
            raise ValueError('contract_major must be a positive integer')
        if not isinstance(self.dependencies, tuple) or any(not isinstance(d, str) or not d for d in self.dependencies):
            raise ValueError('dependencies must be a tuple of module IDs')
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError('duplicate dependencies')
        if not isinstance(self.capabilities, frozenset) or any(not isinstance(c, str) or not c for c in self.capabilities):
            raise ValueError('capabilities must be a frozenset of names')


@dataclass(frozen=True)
class RuntimeIssue:
    code: ErrorCode
    module_id: str | None
    phase: str
    message: str


class ModuleError(RuntimeError):
    def __init__(self, issues: tuple[RuntimeIssue, ...], correlation_id: str):
        if not issues:
            raise ValueError('at least one issue is required')
        self.issues = issues
        self.correlation_id = correlation_id
        self.code = issues[0].code
        super().__init__(f'{self.code}: {issues[0].message}')


@dataclass(frozen=True)
class ModuleContext:
    correlation_id: str
    services: Mapping[str, object]

    def __post_init__(self):
        object.__setattr__(self, 'services', MappingProxyType(dict(self.services)))

    def require(self, module_id: str) -> object:
        """Only declared dependencies are supplied by the composition root."""
        return self.services[module_id]


@dataclass(frozen=True)
class ModuleHealth:
    descriptor: ModuleDescriptor
    state: ModuleState
    healthy: bool
    correlation_id: str
    issues: tuple[RuntimeIssue, ...] = ()


class Module(Protocol):
    descriptor: ModuleDescriptor
    service: object

    def initialize(self, context: ModuleContext) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def dispose(self) -> None: ...
    def health(self) -> bool: ...
