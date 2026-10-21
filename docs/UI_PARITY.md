# Cross-platform UI and behavior

Requirement: identical screens, interactions and results on Windows, Linux and macOS. Use one Python UI source tree, bundled fonts, shared icons, fixed design tokens, explicit locale/timezone and a single state machine. Select the rendering toolkit through an ADR after a parity prototype. Native chrome, font rasterization and DPI differ, so 100% parity is a requirement to test, not a verified claim at scaffold stage.

Acceptance gate: identical action traces and serialized state; screenshot baselines at fixed viewport/DPI/font/locale; keyboard, focus, accessibility, path, Unicode, case sensitivity, permissions and cancellation scenarios on all three OSes. Platform capabilities must yield the same visible fallback and error semantics.
