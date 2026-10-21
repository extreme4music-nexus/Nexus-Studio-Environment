# neurafs architecture

## Responsibility
New storage service implementation behind StoragePort. Legacy source is reference data only; never import or execute it.

## Public boundary
Publish versioned contracts through `nse_contracts`; do not depend on another module implementation. Inject IO dependencies.

## Verification
Shared contract fixtures, deterministic error mapping and behavior parity on Windows, Linux and macOS. Legacy inputs remain outside package discovery, tests and runtime imports.
