# Architecture

Dependency direction: UI -> SDK -> API -> core -> contracts. NeuraFS, connectors and platform adapters implement contracts and are injected by the future composition root. Domain logic is pure Python. Native code requires an ADR and a stable port, with identical behavior contract on all operating systems. No legacy directory belongs on sys.path or package discovery.

Module lifecycle: discover explicit registrations, validate contract version and capabilities, initialize injected dependencies, start, stop and release resources. No implicit plugin execution. Runtime implementation remains future work.
