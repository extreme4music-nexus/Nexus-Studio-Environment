"""Registration is explicit; no plugin discovery or dynamic imports."""
from dataclasses import dataclass
from uuid import uuid4
from nse_contracts.modules import (
    CONTRACT_MAJOR, ErrorCode, Module, ModuleDescriptor, ModuleError, RuntimeIssue,
)


@dataclass(frozen=True)
class Registration:
    descriptor: ModuleDescriptor
    module: Module


class ModuleRegistry:
    def __init__(self):
        self._entries: dict[str, Registration] = {}

    def register(self, module: Module) -> None:
        descriptor = module.descriptor
        if not isinstance(descriptor, ModuleDescriptor):
            raise TypeError('module.descriptor must be a ModuleDescriptor')
        if descriptor.module_id in self._entries:
            raise ModuleError((RuntimeIssue(
                ErrorCode.DUPLICATE_MODULE, descriptor.module_id, 'register',
                f'Duplicate module ID: {descriptor.module_id}',
            ),), uuid4().hex)
        for method in ('initialize', 'start', 'stop', 'dispose', 'health'):
            if not callable(getattr(module, method, None)):
                raise TypeError(f'Module is missing lifecycle method: {method}')
        self._entries[descriptor.module_id] = Registration(descriptor, module)

    def snapshot(self) -> dict[str, Registration]:
        return dict(self._entries)


def dependency_order(entries: dict[str, Registration], correlation_id: str) -> tuple[str, ...]:
    def fail(code, module_id, message):
        raise ModuleError((RuntimeIssue(code, module_id, 'validate', message),), correlation_id)

    for name, entry in entries.items():
        if entry.descriptor.contract_major != CONTRACT_MAJOR:
            fail(ErrorCode.CONTRACT_MISMATCH, name, f'{name} requires contract major {entry.descriptor.contract_major}; supported: {CONTRACT_MAJOR}')
        for dependency in entry.descriptor.dependencies:
            if dependency not in entries:
                fail(ErrorCode.MISSING_DEPENDENCY, name, f'{name} requires missing module {dependency}')

    visiting: list[str] = []
    visited: set[str] = set()
    ordered: list[str] = []

    def visit(name):
        if name in visiting:
            cycle = visiting[visiting.index(name):] + [name]
            fail(ErrorCode.DEPENDENCY_CYCLE, name, 'Dependency cycle: ' + ' -> '.join(cycle))
        if name in visited:
            return
        visiting.append(name)
        for dependency in sorted(entries[name].descriptor.dependencies):
            visit(dependency)
        visiting.pop()
        visited.add(name)
        ordered.append(name)

    for name in sorted(entries):
        visit(name)
    return tuple(ordered)
