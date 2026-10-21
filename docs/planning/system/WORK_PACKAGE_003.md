# WP-003 — Studio project browser prototype

Status: prototype package complete, 2026-10-22. Final UI parity remains open.

Goal: first real desktop surface over WorkspacePort: create, list, open, edit name/creative brief, save with expected revision, explicit reload. Existing sessions/decisions/assets are summarized. No AI/audio/NeuraFS implementation.

Checklist:
- [x] Shared dark theme and consistent Fusion widgets.
- [x] Injected WorkspacePort; implementation imports only in composition root.
- [x] Serialized background storage operations; responsive UI while NAS works.
- [x] Unsaved navigation/close protection; errors preserve text; revision conflicts never overwrite.
- [x] Local offscreen action tests and rendered preview.
- [x] Three-platform offscreen CI evidence; packaging check.

Toolkit candidate: PySide6-Essentials 6.12.0, verified on PyPI on 2026-10-22. Qt Widgets keeps application UI in Python; Essentials avoids unused Qt add-ons. Fusion plus explicit theme reduces native style variation. Tk native styles and QML were considered; this candidate minimizes additional languages and supports automated desktop action tests.

Acceptance is functional prototype parity, not final pixel parity. Native accessibility, high DPI, packaging/licensing and interactive Windows/Linux/macOS visual review remain release gates. No final UI toolkit lock until that evidence exists.

Sources: https://pypi.org/project/PySide6-Essentials/ ; https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QStyleFactory.html ; https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html .

Result: 57 local tests, independent wheel smoke and three mandatory offscreen OS jobs passed. See [verification](../../ui/VERIFICATION.md). Bundled Noto Sans/OFL added and Macedonian glyph coverage checked.
