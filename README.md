# Nexus Studio Environment

Fresh Python-first modular project. Legacy files are isolated references, not application code.

Python >=3.12. Run `python -m unittest discover -s tests` from the project root. Optional editable install: `python -m pip install -e .`.

See [architecture](docs/ARCHITECTURE.md), [boundaries](docs/BOUNDARIES.md), [UI parity](docs/UI_PARITY.md), and [setup report](docs/SETUP_REPORT.md).

- `modules/nexus_core`: Domain orchestration, module lifecycle and application use cases. Depends only on contracts; receives storage and connector ports by injection.
- `modules/neurafs`: New storage service implementation behind StoragePort. Legacy source is reference data only; never import or execute it.
- `modules/contracts`: Versioned DTOs, errors, capability identifiers and Python Protocol ports. No imports from other modules or OS libraries.
- `modules/api`: Transport boundary: validates requests, maps DTOs and errors, authentication, cancellation and timeouts. Calls core use cases; no storage internals.
- `modules/sdk`: Public Python client for versioned API contracts. No direct imports of core, storage or platform implementations.
- `modules/connectors`: External integrations implementing ConnectorPort. Credentials supplied at runtime; normalize provider errors and enforce bounded retries.
- `modules/platform_adapters`: OS-specific filesystem, process, keyring and notification implementations. Windows, Linux and macOS implement the same ports and capability reporting.
- `modules/studio_ui`: One shared Python UI implementation and shared assets, design tokens and state machine across Windows, Linux and macOS. No per-OS screen forks; platform calls only through ports.

This scaffold does not yet implement the production runtime or UI.

## Работен план

[План, потврдена состојба, одлуки и дневник](docs/planning/README.md). Планот е предлог за заедничка разработка пред имплементација.

## Целосен системски план

[Голема слика, архитектура, модули, фази и чек-листа](docs/planning/system/README.md). Прв развоен пакет: модулски runtime костур; новиот системски план е актуелен извор за редоследот.

## Прв функционален костур

Модулскиот runtime е имплементиран со contracts, registry, dependency validation, lifecycle/cleanup и JSON diagnostics. [Стартување и документација](docs/runtime/README.md). Демо-модулите се fake; не се реален Nexus или NeuraFS.
