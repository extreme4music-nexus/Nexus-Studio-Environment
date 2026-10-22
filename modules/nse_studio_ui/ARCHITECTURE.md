# Studio UI boundaries and states

Composition creates QApplication, applies the shared theme, injects WorkspacePort into StudioWindow and owns runtime start/stop. Startup storage IO uses the same worker queue as project actions. Application exit waits for active work before runtime shutdown.

Window states: no selection, loaded/clean, loaded/dirty, busy, operation error/conflict. One operation at a time; data/edit/navigation controls are disabled while busy. Worker results and public errors return through an explicit queued Qt signal. Widgets mutate only on the QApplication thread, checked by an action test.

The editor holds the immutable loaded Project as its base revision. Save sends only edited name/brief plus expected revision. Failed calls never replace that base or editor. Reload explicitly asks to discard dirty text. No automatic merge, stale-lock deletion, job cancellation or destructive project operation.

This prototype consumes the existing local port. Network API/SDK client adapters, module diagnostics, session/decision editors and conversation/jobs views are subsequent work; no parallel storage schema is introduced.

## WP-004 read-only record browser

RecordBrowser displays sessions/decisions from the loaded Project, without new service calls. Plain-text details include provenance and session links; empty and project-switch states clear old records. The same-project selection survives save/reload. See [browser guide](../../docs/ui/SESSION_DECISION_BROWSER.md).
