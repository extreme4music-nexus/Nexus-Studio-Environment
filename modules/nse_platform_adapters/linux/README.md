# linux platform adapters

Implement shared PlatformPort and future filesystem/process/keyring/notification ports. Import native dependencies only here. Normalize errors, Unicode paths, capability reporting and cancellation. Do not create OS-specific UI screens or business rules. Unimplemented adapters must report unavailable capabilities; never silently emulate successful IO.
