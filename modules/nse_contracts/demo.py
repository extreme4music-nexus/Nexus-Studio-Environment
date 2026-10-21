"""Small public demonstration contract; not a real storage API."""
from typing import Protocol, runtime_checkable


@runtime_checkable
class DemoLookupPort(Protocol):
    def lookup(self, key: str) -> str: ...
