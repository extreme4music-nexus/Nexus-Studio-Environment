# Studio prototype

WP-003: Python Qt Widgets UI with injected WorkspacePort. Install `pip install ".[ui]"`, launch `nexus-studio --root <metadata-directory>`. Headless runtime and Workspace installation do not require Qt.

Supported: create/list/open projects, edit name and creative brief, save with revision checks, explicit reload, counts of existing sessions/decisions/assets. Storage runs on a serialized worker; all widget changes run on the UI thread. Busy close is rejected until the operation finishes; this prototype does not cancel filesystem operations.

Dirty text requires discard confirmation for navigation/reload/close. A failed save retains the editor and its expected revision. A revision conflict requires manually preserving notes before an explicit reload; automatic merging is not implemented. Startup failure is displayed; restart after resolving root access. No audio, AI or NeuraFS control is active.

Common appearance: Fusion style, shared colors/spacing, Noto Sans bundled under SIL OFL (assets/OFL.txt). Native window decorations and rasterization may vary. UI-01/02 are candidate evidence, not completed final platform parity. UI-03 remains partial: diagnostics via SDK and full session/decision browsing are future work.

Font provenance: downloaded 2026-10-22 from https://github.com/google/fonts/tree/main/ofl/notosans . Packaged font and license hashes are recorded in assets/manifest.json. Qt distribution/license compliance must be reviewed before release: https://doc.qt.io/qtforpython-6/licenses.html .

Checks: `python -B -m unittest discover -s tests -v`; render synthetic-only preview with `python examples/studio-preview.py --output preview.png`. CI runs these actions offscreen on Windows/Linux/macOS. Interactive desktop, screen-reader, high-DPI and visual comparison checks remain pending.
