# api architecture

## Responsibility
Transport boundary: validates requests, maps DTOs and errors, authentication, cancellation and timeouts. Calls core use cases; no storage internals.

## Public boundary
Publish versioned contracts through `nse_contracts`; do not depend on another module implementation. Inject IO dependencies.

## Verification
Shared contract fixtures, deterministic error mapping and behavior parity on Windows, Linux and macOS. Legacy inputs remain outside package discovery, tests and runtime imports.
