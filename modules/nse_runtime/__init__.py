"""Explicit, synchronous module composition and lifecycle."""
from .registry import ModuleRegistry
from .runtime import Runtime

__all__ = ['ModuleRegistry', 'Runtime']
