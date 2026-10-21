"""Project metadata, independent of UI, AI models and NeuraFS internals."""
from .service import WorkspaceService
from .module import WorkspaceModule

__all__ = ['WorkspaceService', 'WorkspaceModule']
