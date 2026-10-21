# nexus_core architecture

## Responsibility
Domain orchestration, module lifecycle and application use cases. Depends only on contracts; receives storage and connector ports by injection.

## Public boundary
Publish versioned contracts through `nse_contracts`; do not depend on another module implementation. Inject IO dependencies.

## Verification
Shared contract fixtures, deterministic error mapping and behavior parity on Windows, Linux and macOS. Legacy inputs remain outside package discovery, tests and runtime imports.
