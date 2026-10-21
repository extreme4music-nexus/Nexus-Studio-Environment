# studio_ui architecture

## Responsibility
One shared Python UI implementation and shared assets, design tokens and state machine across Windows, Linux and macOS. No per-OS screen forks; platform calls only through ports.

## Public boundary
Publish versioned contracts through `nse_contracts`; do not depend on another module implementation. Inject IO dependencies.

## Verification
Shared contract fixtures, deterministic error mapping and behavior parity on Windows, Linux and macOS. Legacy inputs remain outside package discovery, tests and runtime imports.
