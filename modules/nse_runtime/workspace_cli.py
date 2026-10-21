"""Workspace metadata commands; no model, UI or audio file IO."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
from nse_contracts.modules import ModuleError
from nse_contracts.workspace import WorkspaceError
from .composition import compose_workspace


def main(argv=None):
    parser = argparse.ArgumentParser(description='Nexus Workspace project metadata')
    parser.add_argument('--root', type=Path, required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('create')
    create.add_argument('--name', required=True)
    create.add_argument('--brief', default='')
    commands.add_parser('list')
    for name in ('show', 'history', 'backup'):
        sub = commands.add_parser(name)
        sub.add_argument('project_id')
        if name == 'backup': sub.add_argument('--output', type=Path, required=True)
    update = commands.add_parser('update')
    update.add_argument('project_id')
    update.add_argument('--revision', type=int, required=True)
    update.add_argument('--name')
    update.add_argument('--brief')
    session = commands.add_parser('session')
    session.add_argument('project_id')
    session.add_argument('--revision', type=int, required=True)
    session.add_argument('--title', required=True)
    session.add_argument('--summary', default='')
    decision = commands.add_parser('decision')
    decision.add_argument('project_id')
    decision.add_argument('--revision', type=int, required=True)
    decision.add_argument('--text', required=True)
    decision.add_argument('--source', required=True)
    decision.add_argument('--session-id')
    restore = commands.add_parser('restore')
    restore.add_argument('--input', type=Path, required=True)
    restore.add_argument('--revision', type=int)
    args = parser.parse_args(argv)
    runtime = None
    try:
        runtime, service = compose_workspace(args.root)
        runtime.start()
        if args.command == 'create': result = asdict(service.create(args.name, args.brief))
        elif args.command == 'list': result = [asdict(p) for p in service.list_projects()]
        elif args.command == 'show': result = asdict(service.open(args.project_id))
        elif args.command == 'history': result = [asdict(r) for r in service.history(args.project_id)]
        elif args.command == 'update':
            result = asdict(service.update(args.project_id, args.revision, name=args.name, creative_brief=args.brief))
        elif args.command == 'session':
            result = asdict(service.add_session(args.project_id, args.revision, args.title, args.summary))
        elif args.command == 'decision':
            result = asdict(service.add_decision(args.project_id, args.revision, args.text, args.source, args.session_id))
        elif args.command == 'backup':
            data = service.export_metadata(args.project_id)
            with args.output.open('xb') as stream: stream.write(data)
            result = {'project_id': args.project_id, 'metadata_only': True, 'bytes': len(data)}
        else:
            with args.input.open('rb') as stream: data = stream.read(8*1024*1024+1)
            result = asdict(service.restore_metadata(data, args.revision))
        runtime.stop()
        print(json.dumps({'result': result}, ensure_ascii=True))
        return 0
    except WorkspaceError as exc:
        print(json.dumps({'error': exc.code, 'message': str(exc)}))
        return 1
    except ModuleError as exc:
        print(json.dumps({'error': exc.code, 'correlation_id': exc.correlation_id}))
        return 1
    except (OSError, ValueError, TypeError):
        print(json.dumps({'error': 'invalid_data_or_io', 'message': 'Operation failed; existing files are not overwritten'}))
        return 2
    finally:
        if runtime is not None: runtime.stop()


if __name__ == '__main__':
    raise SystemExit(main())
