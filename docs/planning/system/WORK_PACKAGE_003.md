# WP-003 — Studio project browser prototype

Status: implementation in progress, 2026-10-22.

Goal: first real desktop surface over WorkspacePort: create, list, open, edit name/creative brief, save with expected revision, explicit reload. Existing sessions/decisions/assets are summarized. No AI/audio/NeuraFS implementation.

Checklist:
- [ ] Shared dark theme and consistent Fusion widgets.
- [ ] Injected WorkspacePort; implementation imports only in composition root.
- [ ] Serialized background storage operations; responsive UI while NAS works.
- [ ] Unsaved navigation/close protection; errors preserve text; revision conflicts never overwrite.
- [ ] Local offscreen action tests and rendered preview.
- [ ] Three-platform offscreen CI evidence; packaging check.

Toolkit candidate: PySide6-Essentials 6.12.0, verified on PyPI on 2026-10-22. Qt Widgets keeps application UI in Python; Essentials avoids unused Qt add-ons. Fusion plus explicit theme reduces native style variation. Tk native styles and QML were considered; this candidate minimizes additional languages and supports automated desktop action tests.

Acceptance is functional prototype parity, not final pixel parity. Bundled font, native accessibility, high DPI, packaging/licensing and interactive Windows/Linux/macOS visual review remain release gates. No final UI toolkit lock until that evidence exists.

Sources: https://pypi.org/project/PySide6-Essentials/ ; https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QStyleFactory.html ; https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html .
