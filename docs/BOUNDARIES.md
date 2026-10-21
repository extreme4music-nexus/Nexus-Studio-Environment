# API, SDK and connector boundaries

Use immutable versioned DTOs, UTF-8 JSON at transport boundaries, UTC timestamps, stable error codes and opaque resource IDs. API v1 is the first planned transport version. Breaking schema or behavior changes require a new major contract version. SDK performs transport serialization only. Core owns business policy. Connectors own external IO; adapters own OS IO. Cancellation, deadlines, idempotency and retry policies must be explicit per operation. Secrets come from injected credential providers, never source files.

No cross-module implementation imports; import only published contracts. Compatibility is verified with shared contract fixtures.
