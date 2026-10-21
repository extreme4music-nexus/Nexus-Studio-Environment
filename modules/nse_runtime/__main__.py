"""JSON diagnostics: list, validate and explicitly FAKE lifecycle demos."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
from nse_contracts.modules import ModuleError
from .composition import RuntimeConfig, compose, parse_config
from .demo import FakeNexus, FakeStorage, demo_factories


def snapshots(runtime):
    return [{**asdict(h), 'descriptor': {
        **asdict(h.descriptor), 'capabilities': sorted(h.descriptor.capabilities),
    }} for h in runtime.health()]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Nexus module skeleton — FAKE modules only')
    parser.add_argument('command', choices=('list', 'validate', 'demo', 'failure-demo'))
    parser.add_argument('--config', type=Path)
    args = parser.parse_args(argv)
    runtime = None
    try:
        config = (parse_config(json.loads(args.config.read_text(encoding='utf-8')))
                  if args.config else RuntimeConfig(('demo.nexus', 'demo.storage')))
        if args.command in ('demo', 'failure-demo') and set(config.modules) != {'demo.nexus', 'demo.storage'}:
            raise ValueError('Lifecycle demos require both explicitly FAKE modules')
        fail = args.command == 'failure-demo'
        nexus = FakeNexus(fail)
        factories = demo_factories(fail)
        factories['demo.nexus'] = lambda: nexus
        factories['demo.storage'] = FakeStorage
        runtime = compose(config, factories)
        order = runtime.validate()
        if args.command in ('list', 'validate'):
            print(json.dumps({'simulation': True, 'order': order, 'modules': snapshots(runtime)}))
            return 0
        runtime.start()
        running = snapshots(runtime)
        result = nexus.result
        runtime.stop()
        print(json.dumps({'simulation': True, 'result': result, 'running': running,
                          'after_stop': snapshots(runtime)}))
        return 0
    except ModuleError as exc:
        print(json.dumps({'simulation': True, 'error': exc.code,
                          'correlation_id': exc.correlation_id,
                          'issues': [asdict(i) for i in exc.issues],
                          'modules': snapshots(runtime) if runtime else []}))
        return 1
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'simulation': True, 'error': 'invalid_config',
                          'message': f'Configuration could not be loaded ({type(exc).__name__})'}))
        return 2
    finally:
        if runtime is not None:
            runtime.stop()


if __name__ == '__main__':
    raise SystemExit(main())
