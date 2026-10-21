"""Real metadata persistence demonstration, using only an owned temporary workspace."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
from nse_runtime.composition import compose_workspace
from nse_contracts.workspace import WorkspaceError, WorkspaceCode


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--parent',type=Path,help='Existing directory for a temporary test workspace')
    args=parser.parse_args()
    parent=args.parent.resolve() if args.parent else None
    with tempfile.TemporaryDirectory(prefix='nexus-workspace-smoke-',dir=parent) as temp:
        area=Path(temp).resolve()
        if parent is not None: area.relative_to(parent)
        runtime,service=compose_workspace(area/'projects')
        runtime.start()
        try:
            project=service.create('Smoke project','Keep the original groove')
            stale=project
            project=service.add_session(project.project_id,project.revision,'First session')
            project=service.add_decision(project.project_id,project.revision,'Keep motif A','smoke test',project.sessions[0].session_id)
            backup=service.export_metadata(project.project_id)
            try:
                service.save(stale)
                raise AssertionError('Stale write unexpectedly succeeded')
            except WorkspaceError as exc:
                assert exc.code==WorkspaceCode.CONFLICT
        finally:runtime.stop()
        runtime,service=compose_workspace(area/'projects')
        runtime.start()
        try:
            assert service.open(project.project_id)==project
            history=service.history(project.project_id)
        finally:runtime.stop()
        restore_runtime,restored=compose_workspace(area/'restored')
        restore_runtime.start()
        try:
            recovered=restored.restore_metadata(backup)
            assert recovered.decisions==project.decisions
        finally:restore_runtime.stop()
        print(json.dumps({'metadata_only':True,'reopen':'passed','stale_write':'rejected',
            'restore':'passed','committed_revisions':len(history),'runtime_cleanup':'passed'}))


if __name__=='__main__':main()
