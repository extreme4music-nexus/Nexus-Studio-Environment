"""Composition root: the only place selecting concrete module factories."""
from dataclasses import dataclass
from typing import Callable, Mapping
from uuid import uuid4
from nse_contracts.modules import ErrorCode, Module, ModuleError, RuntimeIssue
from .registry import ModuleRegistry
from .runtime import Runtime


@dataclass(frozen=True)
class RuntimeConfig:
    modules: tuple[str, ...]
    schema_version: int = 1


def parse_config(value: object) -> RuntimeConfig:
    if (not isinstance(value, dict) or set(value) != {'schema_version', 'modules'}
            or type(value['schema_version']) is not int or value['schema_version'] != 1
            or not isinstance(value['modules'], list)
            or any(not isinstance(n, str) or not n for n in value['modules'])
            or len(set(value['modules'])) != len(value['modules'])):
        raise ValueError('Expected schema_version=1 and a unique list of known module names')
    return RuntimeConfig(tuple(value['modules']))


def compose(config: RuntimeConfig, factories: Mapping[str, Callable[[], Module]]) -> Runtime:
    correlation_id = uuid4().hex
    def invalid(message):
        return ModuleError((RuntimeIssue(ErrorCode.INVALID_CONFIG, None, 'compose', message),), correlation_id)
    if (type(config.schema_version) is not int or config.schema_version != 1
            or not isinstance(config.modules, tuple)
            or any(not isinstance(n, str) or not n for n in config.modules)
            or len(set(config.modules)) != len(config.modules)):
        raise invalid('Invalid runtime configuration')
    unknown = set(config.modules) - set(factories)
    if unknown:
        raise invalid('Unknown module names: ' + ', '.join(sorted(unknown)))
    registry = ModuleRegistry()
    for name in config.modules:
        module = factories[name]()
        if module.descriptor.module_id != name:
            raise invalid(f'Factory descriptor does not match configured module ID: {name}')
        registry.register(module)
    runtime = Runtime(registry)
    runtime.validate()
    return runtime
