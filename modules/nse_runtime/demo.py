"""FAKE modules for wiring demonstrations. No AI, storage IO or NeuraFS."""
from nse_contracts.demo import DemoLookupPort
from nse_contracts.modules import ModuleContext, ModuleDescriptor
from .composition import RuntimeConfig, compose


class FakeStorage:
    descriptor = ModuleDescriptor('demo.storage', 'FAKE in-memory lookup', '0.1.0',
                                  capabilities=frozenset({'demo.lookup'}))

    def __init__(self):
        self.service = self
        self.running = False

    def initialize(self, context: ModuleContext) -> None:
        pass

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def dispose(self) -> None:
        self.running = False

    def health(self) -> bool:
        return self.running

    def lookup(self, key: str) -> str:
        if not self.running:
            raise RuntimeError('FAKE lookup is not running')
        if key != 'greeting':
            raise KeyError(key)
        return 'FAKE module connection verified'


class FakeNexus:
    descriptor = ModuleDescriptor('demo.nexus', 'FAKE Nexus client', '0.1.0',
                                  dependencies=('demo.storage',),
                                  capabilities=frozenset({'demo.result'}))

    def __init__(self, fail_start: bool = False):
        self.service = self
        self.fail_start = fail_start
        self.result = None
        self.running = False

    def initialize(self, context: ModuleContext) -> None:
        service = context.require('demo.storage')
        if not isinstance(service, DemoLookupPort):
            raise TypeError('Missing DemoLookupPort')
        self.lookup = service

    def start(self) -> None:
        if self.fail_start:
            raise RuntimeError('Intentional FAKE startup failure')
        self.result = self.lookup.lookup('greeting')
        self.running = True

    def stop(self) -> None:
        self.running = False

    def dispose(self) -> None:
        self.running = False
        self.lookup = None

    def health(self) -> bool:
        return self.running


def demo_factories(fail_start: bool = False):
    return {'demo.storage': FakeStorage, 'demo.nexus': lambda: FakeNexus(fail_start)}


def build_demo(fail_start: bool = False):
    return compose(RuntimeConfig(('demo.nexus', 'demo.storage')), demo_factories(fail_start))
