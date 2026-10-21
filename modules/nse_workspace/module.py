"""Workspace lifecycle adapter; constructors do not create files."""
from nse_contracts.modules import ModuleDescriptor
from nse_contracts.workspace import WorkspaceCode, WorkspaceError
from .service import WorkspaceService


class WorkspaceAccess:
    """Stable dependency reference; public calls require the module to be running."""
    _operations = frozenset({'create', 'open', 'save', 'list_projects', 'history',
        'update', 'add_session', 'add_decision', 'add_asset', 'export_metadata', 'restore_metadata'})

    def __init__(self, owner):
        self._owner = owner

    def __getattr__(self, name):
        if name not in self._operations:
            raise AttributeError(name)
        def call(*args, **kwargs):
            if not self._owner.running:
                raise WorkspaceError(WorkspaceCode.NOT_RUNNING, 'Workspace is not running')
            return getattr(self._owner._workspace, name)(*args, **kwargs)
        return call


class WorkspaceModule:
    descriptor = ModuleDescriptor('workspace', 'Workspace project metadata', '0.1.0',
        capabilities=frozenset({'project.create', 'project.open', 'project.save',
                                'project.history', 'project.metadata_backup'}))

    def __init__(self, root):
        self._workspace = WorkspaceService(root)
        self.running = False
        self.service = WorkspaceAccess(self)

    def initialize(self, context):
        self._workspace.initialize()

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def dispose(self):
        self.running = False

    def health(self):
        return self.running and self._workspace.repository.root.is_dir()
