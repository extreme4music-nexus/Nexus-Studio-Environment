from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'modules'))

from nse_contracts.modules import (
    ErrorCode, ModuleContext, ModuleDescriptor, ModuleError, ModuleState,
)
from nse_runtime import ModuleRegistry, Runtime
from nse_runtime.composition import RuntimeConfig, compose, parse_config
from nse_runtime.demo import build_demo


class Probe:
    def __init__(self, name, events, dependencies=(), failures=(), major=1):
        self.descriptor = ModuleDescriptor(name, name, '0.1.0', major, dependencies)
        self.events = events
        self.failures = set(failures)
        self.service = object()
        self.context = None

    def _event(self, phase):
        self.events.append((self.descriptor.module_id, phase))
        if phase in self.failures:
            raise RuntimeError('sensitive-test-value-must-not-appear-in-diagnostics')

    def initialize(self, context):
        self.context = context
        self._event('initialize')

    def start(self): self._event('start')
    def stop(self): self._event('stop')
    def dispose(self): self._event('dispose')
    def health(self):
        self._event('health')
        return True


def runtime_for(*modules):
    registry = ModuleRegistry()
    for module in modules:
        registry.register(module)
    return Runtime(registry)


class DescriptorTests(unittest.TestCase):
    def test_invalid_descriptors(self):
        for kwargs in ({'module_id': '../legacy'}, {'display_name': ''},
                       {'version': ''}, {'contract_major': True},
                       {'dependencies': ['a']}, {'dependencies': ('a', 'a')},
                       {'capabilities': {'unsafe-mutable-set'}}):
            values = dict(module_id='valid', display_name='Valid', version='1')
            values.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ModuleDescriptor(**values)

    def test_context_is_immutable_snapshot(self):
        values = {'a': object()}
        context = ModuleContext('test', values)
        values.clear()
        self.assertIsNotNone(context.require('a'))
        with self.assertRaises(TypeError): context.services['x'] = object()
        with self.assertRaises(KeyError): context.require('undeclared')


class RegistryTests(unittest.TestCase):
    def test_duplicate(self):
        registry = ModuleRegistry()
        registry.register(Probe('a', []))
        with self.assertRaises(ModuleError) as caught:
            registry.register(Probe('a', []))
        self.assertEqual(caught.exception.code, ErrorCode.DUPLICATE_MODULE)

    def test_snapshot_does_not_change_existing_runtime(self):
        registry = ModuleRegistry()
        registry.register(Probe('a', []))
        runtime = Runtime(registry)
        registry.register(Probe('b', []))
        self.assertEqual(runtime.validate(), ('a',))

    def test_missing_cycle_and_major_have_no_lifecycle_effects(self):
        cases = [
            (ErrorCode.MISSING_DEPENDENCY, [('a', ('absent',), 1)]),
            (ErrorCode.DEPENDENCY_CYCLE, [('a', ('b',), 1), ('b', ('a',), 1)]),
            (ErrorCode.DEPENDENCY_CYCLE, [('a', ('a',), 1)]),
            (ErrorCode.CONTRACT_MISMATCH, [('a', (), 2)]),
        ]
        for code, definitions in cases:
            events = []
            runtime = runtime_for(*(Probe(n, events, d, major=m) for n, d, m in definitions))
            with self.subTest(code=code), self.assertRaises(ModuleError) as caught:
                runtime.start()
            self.assertEqual(caught.exception.code, code)
            self.assertEqual(events, [])
            self.assertTrue(all(h.state == ModuleState.REGISTERED for h in runtime.health()))


class LifecycleTests(unittest.TestCase):
    def test_order_injection_and_repeat_semantics(self):
        events = []
        b = Probe('b', events)
        a = Probe('a', events, ('b',))
        unrelated = Probe('z', events)
        runtime = runtime_for(a, unrelated, b)
        self.assertEqual(runtime.validate(), ('b', 'a', 'z'))
        runtime.stop()  # Stop before start does not acquire or dispose resources.
        self.assertEqual(events, [])
        runtime.start()
        self.assertEqual(events, [('b', 'initialize'), ('a', 'initialize'), ('z', 'initialize'),
                                  ('b', 'start'), ('a', 'start'), ('z', 'start')])
        self.assertIs(a.context.require('b'), b.service)
        with self.assertRaises(KeyError): a.context.require('z')
        self.assertEqual(a.context.correlation_id, runtime.correlation_id)
        self.assertTrue(all(h.healthy for h in runtime.health()))
        previous = list(events)
        runtime.start()
        self.assertEqual(events, previous)
        runtime.stop()
        self.assertEqual(events[-6:], [('z', 'stop'), ('a', 'stop'), ('b', 'stop'),
                                      ('z', 'dispose'), ('a', 'dispose'), ('b', 'dispose')])
        self.assertTrue(all(h.state == ModuleState.DISPOSED and not h.healthy for h in runtime.health()))
        previous = list(events)
        runtime.stop()
        self.assertEqual(events, previous)
        with self.assertRaises(ModuleError) as caught: runtime.start()
        self.assertEqual(caught.exception.code, ErrorCode.INVALID_STATE)

    def test_failed_initialize_disposes_failing_and_prior_modules(self):
        events = []
        runtime = runtime_for(Probe('a', events), Probe('b', events, ('a',), ('initialize',)),
                              Probe('c', events, ('b',)))
        with self.assertRaises(ModuleError) as caught: runtime.start()
        self.assertEqual(caught.exception.code, ErrorCode.INITIALIZE_FAILED)
        self.assertEqual(events, [('a', 'initialize'), ('b', 'initialize'),
                                  ('b', 'dispose'), ('a', 'dispose')])
        states = {h.descriptor.module_id: h.state for h in runtime.health()}
        self.assertEqual(states, {'a': ModuleState.DISPOSED, 'b': ModuleState.FAILED,
                                  'c': ModuleState.REGISTERED})

    def test_failed_start_preserves_root_and_all_cleanup_errors(self):
        events = []
        runtime = runtime_for(Probe('a', events, failures=('stop',)),
                              Probe('b', events, ('a',), ('start', 'dispose')))
        with self.assertRaises(ModuleError) as caught: runtime.start()
        error = caught.exception
        self.assertEqual([i.code for i in error.issues],
                         [ErrorCode.START_FAILED, ErrorCode.STOP_FAILED, ErrorCode.DISPOSE_FAILED])
        self.assertEqual(error.correlation_id, runtime.correlation_id)
        self.assertEqual(events[-4:], [('b', 'stop'), ('a', 'stop'), ('b', 'dispose'), ('a', 'dispose')])
        self.assertNotIn('sensitive-test-value', str(error))
        self.assertIsInstance(error.__cause__, RuntimeError)
        before = list(events)
        runtime.stop()
        self.assertEqual(events, before)
        self.assertTrue(all(not h.healthy for h in runtime.health()))

    def test_shutdown_continues_after_failures(self):
        events = []
        runtime = runtime_for(Probe('a', events, failures=('dispose',)),
                              Probe('b', events, ('a',), ('stop',)))
        runtime.start()
        with self.assertRaises(ModuleError) as caught: runtime.stop()
        self.assertEqual([i.code for i in caught.exception.issues],
                         [ErrorCode.STOP_FAILED, ErrorCode.DISPOSE_FAILED])
        self.assertEqual(events[-4:], [('b', 'stop'), ('a', 'stop'), ('b', 'dispose'), ('a', 'dispose')])

    def test_health_failure_is_visible_and_does_not_skip_disposal(self):
        runtime = runtime_for(Probe('a', [], failures=('health',)))
        runtime.start()
        health = runtime.health()[0]
        self.assertFalse(health.healthy)
        self.assertEqual(health.state, ModuleState.RUNNING)
        self.assertEqual(health.issues[0].code, ErrorCode.HEALTH_FAILED)
        runtime.stop()
        self.assertEqual(runtime.health()[0].state, ModuleState.DISPOSED)

    def test_real_demo_service_result(self):
        runtime = build_demo()
        runtime.start()
        self.assertTrue(all(h.healthy for h in runtime.health()))
        runtime.stop()

    def test_interrupted_start_releases_partial_resources(self):
        events = []
        class Interrupted(Probe):
            def start(self):
                self.events.append((self.descriptor.module_id, 'start'))
                raise KeyboardInterrupt()
        runtime = runtime_for(Probe('a', events), Interrupted('b', events, ('a',)))
        with self.assertRaises(KeyboardInterrupt): runtime.start()
        self.assertEqual(events[-4:], [('b', 'stop'), ('a', 'stop'), ('b', 'dispose'), ('a', 'dispose')])
        self.assertFalse(any(h.healthy for h in runtime.health()))

    def test_empty_runtime_has_valid_lifecycle(self):
        runtime = runtime_for()
        self.assertEqual(runtime.validate(), ())
        runtime.start()
        runtime.stop()
        self.assertEqual(runtime.health(), ())


class CompositionTests(unittest.TestCase):
    def test_config_validation(self):
        invalid = [None, {}, {'schema_version': True, 'modules': []},
                   {'schema_version': 2, 'modules': []},
                   {'schema_version': 1, 'modules': ['a', 'a']},
                   {'schema_version': 1, 'modules': [2]},
                   {'schema_version': 1, 'modules': [], 'import': 'arbitrary.code'}]
        for config in invalid:
            with self.subTest(config=config), self.assertRaises(ValueError): parse_config(config)

    def test_unknown_names_rejected_before_any_factory_runs(self):
        called = []
        with self.assertRaises(ModuleError) as caught:
            compose(RuntimeConfig(('known', 'unknown')), {'known': lambda: called.append(True)})
        self.assertEqual(caught.exception.code, ErrorCode.INVALID_CONFIG)
        self.assertEqual(called, [])

    def test_mismatched_factory_descriptor(self):
        with self.assertRaises(ModuleError) as caught:
            compose(RuntimeConfig(('a',)), {'a': lambda: Probe('b', [])})
        self.assertEqual(caught.exception.code, ErrorCode.INVALID_CONFIG)

    def test_direct_config_cannot_bypass_validation(self):
        for config in (RuntimeConfig(('a', 'a')), RuntimeConfig((), True), RuntimeConfig(['a'])):
            with self.subTest(config=config), self.assertRaises(ModuleError) as caught:
                compose(config, {})
            self.assertEqual(caught.exception.code, ErrorCode.INVALID_CONFIG)


class CommandTests(unittest.TestCase):
    def command(self, *args):
        env = dict(os.environ, PYTHONPATH=str(ROOT/'modules'), PYTHONDONTWRITEBYTECODE='1')
        with tempfile.TemporaryDirectory() as unrelated:
            result = subprocess.run([sys.executable, '-m', 'nse_runtime', *args], cwd=unrelated,
                                    env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.stderr, '')
        return result.returncode, json.loads(result.stdout)

    def test_success_from_unrelated_working_directory(self):
        code, data = self.command('demo', '--config', str(ROOT/'examples/runtime-demo.json'))
        self.assertEqual(code, 0)
        self.assertTrue(data['simulation'])
        self.assertEqual(data['result'], 'FAKE module connection verified')
        self.assertTrue(all(m['healthy'] for m in data['running']))
        self.assertTrue(all(m['state'] == 'disposed' for m in data['after_stop']))

    def test_failure_has_nonzero_exit_and_cleaned_module_states(self):
        code, data = self.command('failure-demo')
        self.assertEqual(code, 1)
        self.assertEqual(data['error'], 'start_failed')
        states = {m['descriptor']['module_id']: m['state'] for m in data['modules']}
        self.assertEqual(states, {'demo.nexus': 'failed', 'demo.storage': 'disposed'})

    def test_validate_does_not_start_modules(self):
        code, data = self.command('validate')
        self.assertEqual(code, 0)
        self.assertEqual(data['order'], ['demo.storage', 'demo.nexus'])
        self.assertTrue(all(m['state'] == 'registered' for m in data['modules']))

    def test_missing_config_is_machine_readable(self):
        code, data = self.command('list', '--config', str(ROOT/'not-present.json'))
        self.assertEqual(code, 2)
        self.assertEqual(data['error'], 'invalid_config')
