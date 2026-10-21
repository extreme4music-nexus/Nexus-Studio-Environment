# connectors architecture

## Responsibility
External integrations implementing ConnectorPort. Credentials supplied at runtime; normalize provider errors and enforce bounded retries.

## Public boundary
Publish versioned contracts through `nse_contracts`; do not depend on another module implementation. Inject IO dependencies.

## Verification
Shared contract fixtures, deterministic error mapping and behavior parity on Windows, Linux and macOS. Legacy inputs remain outside package discovery, tests and runtime imports.
