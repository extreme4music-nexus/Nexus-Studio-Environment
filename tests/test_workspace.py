from pathlib import Path
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
from threading import Barrier
import unittest
from unittest.mock import patch
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'modules'))
from nse_contracts.modules import ModuleDescriptor
from nse_contracts.workspace import (
    AssetReference, Decision, Project, Session, WorkspaceCode, WorkspaceError,
    project_dict, project_from_dict,
)
from nse_workspace import WorkspaceService, WorkspaceModule
from nse_workspace.repository import now, encoded
from nse_runtime.composition import compose_workspace
from nse_runtime import ModuleRegistry, Runtime


def process_writer(root, project_id, barrier, queue):
    try:
        service=WorkspaceService(root)
        project=service.open(project_id)
        barrier.wait(timeout=20)
        saved=service.save(replace(project,name=f'Writer {os.getpid()}'))
        queue.put(('saved',saved.revision))
    except WorkspaceError as exc:
        queue.put((str(exc.code),None))
    except Exception as exc:
        queue.put(('unexpected:'+type(exc).__name__,None))


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='nexus-workspace-test-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'metadata'
        self.service=WorkspaceService(self.root)

    def assert_code(self, code, callback):
        with self.assertRaises(WorkspaceError) as caught: callback()
        self.assertEqual(caught.exception.code,code)
        return caught.exception

    def head(self, project):
        path=self.root/project.project_id
        return path,json.loads((path/'HEAD.json').read_text(encoding='utf-8'))['head']

    def test_create_and_reopen_unicode_in_new_instance(self):
        project=self.service.create('Ноќна сесија 🎶','Зачувај го неправилниот groove.')
        reopened=WorkspaceService(self.root).open(project.project_id)
        self.assertEqual(reopened,project)
        self.assertEqual(project.revision,1)
        self.assertEqual(self.service.list_projects(),(project,))

    def test_sessions_decisions_and_project_isolation(self):
        a=self.service.create('A')
        b=self.service.create('B')
        a=self.service.add_session(a.project_id,a.revision,'First','Keep the motif')
        a=self.service.add_decision(a.project_id,a.revision,'Choose variation B','user selection',a.sessions[0].session_id)
        self.assertEqual(WorkspaceService(self.root).open(a.project_id),a)
        self.assertEqual(self.service.open(b.project_id).decisions,())
        self.assert_code(WorkspaceCode.INVALID_DATA,lambda:self.service.add_decision(
            b.project_id,b.revision,'Foreign session','test',a.sessions[0].session_id))
        self.assertEqual(self.service.open(b.project_id),b)

    def test_stale_save_conflicts_and_history_is_immutable(self):
        initial=self.service.create('Original')
        first=self.service.update(initial.project_id,1,name='First')
        path,pointer=self.head(first)
        content=(path/pointer['file']).read_bytes()
        self.assert_code(WorkspaceCode.CONFLICT,lambda:self.service.save(replace(initial,name='Stale')))
        self.assertEqual(self.service.open(initial.project_id),first)
        self.assertEqual((path/pointer['file']).read_bytes(),content)
        self.assertEqual([r.revision for r in self.service.history(first.project_id)],[2,1])

    def test_concurrent_clients_never_overwrite_same_revision(self):
        initial=self.service.create('Concurrent')
        barrier=Barrier(2)
        def writer(name):
            service=WorkspaceService(self.root)
            candidate=replace(service.open(initial.project_id),name=name)
            barrier.wait(timeout=10)
            try:return ('saved',service.save(candidate).name)
            except WorkspaceError as exc:return (exc.code,None)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(writer,['A','B']))
        self.assertEqual(sum(r[0]=='saved' for r in results),1)
        self.assertIn(next(r[0] for r in results if r[0]!='saved'),(WorkspaceCode.CONFLICT,WorkspaceCode.BUSY))
        self.assertEqual(self.service.open(initial.project_id).revision,2)

    def test_lock_is_reported_not_deleted_and_read_still_works(self):
        project=self.service.create('Locked')
        lock=self.root/project.project_id/'.write.lock'
        lock.write_text('existing owner',encoding='utf-8')
        self.assert_code(WorkspaceCode.BUSY,lambda:self.service.update(project.project_id,1,name='No'))
        self.assertEqual(lock.read_text(encoding='utf-8'),'existing owner')
        self.assertEqual(self.service.open(project.project_id),project)

    def test_separate_process_writers_do_not_lose_updates(self):
        project=self.service.create('Two processes')
        ctx=multiprocessing.get_context('spawn')
        barrier=ctx.Barrier(2);queue=ctx.Queue()
        processes=[ctx.Process(target=process_writer,args=(str(self.root),project.project_id,barrier,queue)) for _ in range(2)]
        try:
            for process in processes:process.start()
            results=[queue.get(timeout=30) for _ in processes]
            for process in processes:
                process.join(timeout=15)
                self.assertEqual(process.exitcode,0)
            self.assertEqual(sum(code=='saved' for code,_ in results),1)
            self.assertIn(next(code for code,_ in results if code!='saved'),('revision_conflict','workspace_busy'))
            self.assertEqual(self.service.open(project.project_id).revision,2)
        finally:
            for process in processes:
                if process.is_alive():process.terminate();process.join(timeout=5)
            queue.close()

    def test_partial_snapshot_write_never_changes_head(self):
        project=self.service.create('Stable')
        original=self.service.repository._write_new
        def partial(path,data):
            if path.name.startswith('r'):
                with path.open('xb') as stream:stream.write(data[:20])
                raise OSError('Partial write')
            original(path,data)
        with patch.object(self.service.repository,'_write_new',side_effect=partial):
            self.assert_code(WorkspaceCode.IO_ERROR,lambda:self.service.update(project.project_id,1,name='Not committed'))
        self.assertEqual(self.service.open(project.project_id),project)
        self.assertEqual(len(self.service.history(project.project_id)),1)
        self.assertEqual(self.service.update(project.project_id,1,name='Recovered').revision,2)

    def test_failed_head_commit_preserves_previous_and_ignores_orphan(self):
        project=self.service.create('Stable')
        with patch.object(self.service.repository,'_replace_head',side_effect=OSError('simulated failure')):
            self.assert_code(WorkspaceCode.IO_ERROR,lambda:self.service.update(project.project_id,1,name='Uncommitted'))
        self.assertEqual(self.service.open(project.project_id),project)
        self.assertEqual(len(self.service.history(project.project_id)),1)
        current=self.service.update(project.project_id,1,name='Committed')
        self.assertEqual(current.revision,2)
        self.assertEqual(len(self.service.history(project.project_id)),2)
        self.assertFalse((self.root/project.project_id/'.write.lock').exists())

    def test_replace_failure_cleans_temporary_head(self):
        project=self.service.create('Stable')
        with patch('nse_workspace.repository.os.replace',side_effect=PermissionError('denied')):
            self.assert_code(WorkspaceCode.IO_ERROR,lambda:self.service.update(project.project_id,1,name='No'))
        path=self.root/project.project_id
        self.assertEqual(list(path.glob('.head-*.tmp')),[])
        self.assertEqual(self.service.open(project.project_id),project)

    def test_io_failure_has_public_code_not_raw_error(self):
        with patch.object(self.service.repository,'initialize',side_effect=PermissionError('private secret')):
            error=self.assert_code(WorkspaceCode.IO_ERROR,lambda:self.service.create('No'))
        self.assertNotIn('private secret',str(error))

    def test_checksum_corruption_is_never_reset(self):
        project=self.service.create('A')
        path,pointer=self.head(project)
        snapshot=path/pointer['file']
        snapshot.write_bytes(snapshot.read_bytes()+b' ')
        before=snapshot.read_bytes()
        self.assert_code(WorkspaceCode.CORRUPT,lambda:self.service.open(project.project_id))
        self.assert_code(WorkspaceCode.CORRUPT,lambda:self.service.save(project))
        self.assertEqual(snapshot.read_bytes(),before)

    def test_missing_snapshot_and_malformed_head_are_visible(self):
        project=self.service.create('A')
        path,pointer=self.head(project)
        missing=path/pointer['file']
        missing.unlink()
        self.assert_code(WorkspaceCode.CORRUPT,lambda:self.service.open(project.project_id))
        (path/'HEAD.json').write_text('{"schema_version":1,"head":null}',encoding='utf-8')
        self.assert_code(WorkspaceCode.CORRUPT,lambda:self.service.open(project.project_id))

    def test_unknown_schema_rejected_and_unchanged(self):
        project=self.service.create('A')
        path,pointer=self.head(project)
        head=path/'HEAD.json'
        value=json.loads(head.read_text(encoding='utf-8'))
        value['schema_version']=2
        head.write_bytes(encoded(value))
        before=head.read_bytes()
        self.assert_code(WorkspaceCode.UNSUPPORTED_SCHEMA,lambda:self.service.open(project.project_id))
        self.assertEqual(head.read_bytes(),before)

    def test_future_project_schema_is_rejected_even_with_valid_checksum(self):
        project=self.service.create('A')
        path,pointer=self.head(project)
        snapshot=path/pointer['file']
        value=json.loads(snapshot.read_text(encoding='utf-8'))
        value['project']['schema_version']=2
        data=encoded(value);snapshot.write_bytes(data)
        pointer['sha256']=hashlib.sha256(data).hexdigest()
        (path/'HEAD.json').write_bytes(encoded({'schema_version':1,'head':pointer}))
        self.assert_code(WorkspaceCode.UNSUPPORTED_SCHEMA,lambda:self.service.open(project.project_id))

    def test_history_detects_missing_parent_without_rewriting_current(self):
        initial=self.service.create('A')
        path,old_pointer=self.head(initial)
        current=self.service.update(initial.project_id,1,name='B')
        (path/old_pointer['file']).unlink()
        self.assertEqual(self.service.open(current.project_id),current)
        self.assert_code(WorkspaceCode.CORRUPT,lambda:self.service.history(current.project_id))

    def test_head_traversal_and_duplicate_json_keys_rejected(self):
        project=self.service.create('A')
        path,pointer=self.head(project)
        pointer['file']='../outside.json'
        (path/'HEAD.json').write_bytes(encoded({'schema_version':1,'head':pointer}))
        self.assert_code(WorkspaceCode.CORRUPT,lambda:self.service.open(project.project_id))
        (path/'HEAD.json').write_bytes(b'{"schema_version":1,"schema_version":1,"head":{}}')
        self.assert_code(WorkspaceCode.CORRUPT,lambda:self.service.open(project.project_id))

    def test_missing_and_invalid_project_ids(self):
        self.assert_code(WorkspaceCode.NOT_FOUND,lambda:self.service.open(uuid4().hex))
        self.assert_code(WorkspaceCode.INVALID_DATA,lambda:self.service.open('../legacy'))

    def test_in_progress_creation_is_busy_not_silently_empty(self):
        id=uuid4().hex
        path=self.root/id;path.mkdir(parents=True)
        lock=path/'.write.lock';lock.write_text('creating',encoding='utf-8')
        self.assert_code(WorkspaceCode.BUSY,lambda:self.service.open(id))
        lock.unlink()
        self.assert_code(WorkspaceCode.CORRUPT,lambda:self.service.open(id))

    def test_backup_restore_empty_and_existing_with_revision_guard(self):
        initial=self.service.create('Before','Original brief')
        initial=self.service.add_session(initial.project_id,1,'Session')
        backup=self.service.export_metadata(initial.project_id)
        second=WorkspaceService(Path(self.temp.name)/'restored')
        restored=second.restore_metadata(backup)
        self.assertEqual(restored.project_id,initial.project_id)
        self.assertEqual(restored.sessions,initial.sessions)
        self.assertEqual(restored.revision,1)
        latest=self.service.update(initial.project_id,initial.revision,name='After')
        self.assert_code(WorkspaceCode.INVALID_DATA,lambda:self.service.restore_metadata(backup))
        self.assert_code(WorkspaceCode.CONFLICT,lambda:self.service.restore_metadata(backup,1))
        restored=self.service.restore_metadata(backup,latest.revision)
        self.assertEqual(restored.name,'Before')
        self.assertEqual(restored.revision,latest.revision+1)
        self.assertEqual(len(self.service.history(initial.project_id)),restored.revision)

    def test_corrupt_backup_and_unknown_version_do_not_create_projects(self):
        project=self.service.create('A')
        value=json.loads(self.service.export_metadata(project.project_id))
        fresh=WorkspaceService(Path(self.temp.name)/'fresh')
        value['project']['name']='Tampered'
        self.assert_code(WorkspaceCode.CORRUPT,lambda:fresh.restore_metadata(encoded(value)))
        self.assertFalse(fresh.repository.root.exists())
        value['backup_version']=2
        self.assert_code(WorkspaceCode.UNSUPPORTED_SCHEMA,lambda:fresh.restore_metadata(encoded(value)))

    def test_asset_provenance_metadata_only_and_no_external_reads(self):
        project=self.service.create('A')
        source=Path(self.temp.name)/'source.wav'
        source.write_bytes(b'original bytes')
        first=AssetReference(uuid4().hex,'Source',source.as_uri(),'audio',now())
        project=self.service.add_asset(project.project_id,1,first)
        derived=AssetReference(uuid4().hex,'Derived','unavailable://preview','midi',now(),derived_from=(first.asset_id,))
        project=self.service.add_asset(project.project_id,project.revision,derived)
        self.assertEqual(self.service.open(project.project_id).assets,project.assets)
        self.assertEqual(source.read_bytes(),b'original bytes')
        self.assertNotIn(b'original bytes',self.service.export_metadata(project.project_id))
        invalid=replace(derived,asset_id=uuid4().hex,derived_from=(uuid4().hex,))
        self.assert_code(WorkspaceCode.INVALID_DATA,lambda:self.service.add_asset(project.project_id,project.revision,invalid))

    def test_duplicate_ids_cycles_and_mutable_collections_are_rejected(self):
        stamp=now(); id_a=uuid4().hex; id_b=uuid4().hex
        assets=(AssetReference(id_a,'A','x','other',stamp,derived_from=(id_b,)),
                AssetReference(id_b,'B','y','other',stamp,derived_from=(id_a,)))
        project=self.service.create('A')
        with self.assertRaises(ValueError):replace(project,assets=assets)
        with self.assertRaises(ValueError):replace(project,sessions=[])
        s=Session(uuid4().hex,'s','',stamp)
        with self.assertRaises(ValueError):replace(project,sessions=(s,s))

    def test_schema_round_trip_and_creation_identity_cannot_change(self):
        project=self.service.create('A')
        value=json.loads(encoded(project_dict(project)))
        self.assertEqual(project_from_dict(value),project)
        self.assert_code(WorkspaceCode.INVALID_DATA,lambda:self.service.save(
            replace(project,created_at='2000-01-01T00:00:00+00:00')))

    def test_module_service_reference_is_stable_and_gated(self):
        runtime,service=compose_workspace(self.root)
        self.assertFalse(self.root.exists())
        self.assert_code(WorkspaceCode.NOT_RUNNING,lambda:service.create('Early'))
        runtime.start()
        project=service.create('Runtime')
        self.assertTrue(runtime.health()[0].healthy)
        runtime.stop()
        self.assert_code(WorkspaceCode.NOT_RUNNING,lambda:service.open(project.project_id))
        next_runtime,next_service=compose_workspace(self.root)
        next_runtime.start()
        self.assertEqual(next_service.open(project.project_id),project)
        next_runtime.stop()

    def test_dependent_module_can_bind_workspace_during_initialize(self):
        result=[]
        class Consumer:
            descriptor=ModuleDescriptor('consumer','Consumer','1',dependencies=('workspace',))
            service=None
            def initialize(self,context): self.workspace=context.require('workspace')
            def start(self): result.append(self.workspace.create('Dependent'))
            def stop(self):pass
            def dispose(self):pass
            def health(self):return True
        registry=ModuleRegistry()
        registry.register(Consumer());registry.register(WorkspaceModule(self.root))
        runtime=Runtime(registry);runtime.start();runtime.stop()
        self.assertEqual(len(result),1)
        self.assertEqual(self.service.open(result[0].project_id),result[0])


class WorkspaceCommandTests(unittest.TestCase):
    def test_independent_commands_reopen_conflict_and_backup(self):
        env=dict(os.environ,PYTHONPATH=str(ROOT/'modules'),PYTHONDONTWRITEBYTECODE='1')
        with tempfile.TemporaryDirectory(prefix='nexus-workspace-cli-') as temp:
            area=Path(temp);root=area/'projects'
            def run(*args, expected=0):
                p=subprocess.run([sys.executable,'-B','-m','nse_runtime.workspace_cli','--root',str(root),*args],
                                 cwd=area,env=env,text=True,capture_output=True,timeout=30)
                self.assertEqual(p.returncode,expected,p.stdout+p.stderr)
                self.assertEqual(p.stderr,'')
                return json.loads(p.stdout)
            project=run('create','--name','Мој проект')['result']
            id=project['project_id']
            self.assertEqual(run('show',id)['result'],project)
            updated=run('update',id,'--revision','1','--brief','Keep groove')['result']
            self.assertEqual(updated['revision'],2)
            self.assertEqual(run('update',id,'--revision','1','--name','stale',expected=1)['error'],'revision_conflict')
            backup=area/'backup.json'
            run('backup',id,'--output',str(backup))
            before=backup.read_bytes()
            run('backup',id,'--output',str(backup),expected=2)
            self.assertEqual(backup.read_bytes(),before)
            self.assertEqual(len(run('history',id)['result']),2)
