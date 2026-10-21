from typing import Protocol

class StoragePort(Protocol):
    def read_bytes(self, resource_id: str) -> bytes: ...

class ConnectorPort(Protocol):
    def capabilities(self) -> frozenset[str]: ...

class PlatformPort(Protocol):
    def capabilities(self) -> frozenset[str]: ...
