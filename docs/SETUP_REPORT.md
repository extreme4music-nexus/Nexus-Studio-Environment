# Setup report — 2026-10-21

Project: `Z:\Projects\Nexus-Studio-Environment`.
Repository: https://github.com/extreme4music-nexus/Nexus-Studio-Environment (private).

## Completed
- Fresh Python >=3.12 modular scaffold, eight module READMEs and architecture documents, contract ports, SDK/API/connector/platform boundaries, shared UI parity acceptance criteria and ADR.
- New Git main branch; private reference trees and detailed inventories excluded from Git and packaging.
- Google Drive Nexus 10: 21 files downloaded, including Legacy; all sizes and SHA-256 readback checks passed. Original metadata and hashes are in `modules/nexus_core/reference/manifest.json`.
- Full NeuraFS snapshot: 12949 files, 11702755232 bytes; every source/copy SHA-256 matches. Includes hidden files, Git history, environments and build outputs. Original Git status unchanged. Detailed inventory: `modules/neurafs/reference/manifest.json`.
- GitHub sync comparison used remote-head verification and the GitHub compare API after a slow audit fetch was interrupted; the original and exact snapshot were never fetched into. See [findings](sync/NEURAFS_SYNC.md).

## Sync findings
- Active branch versus its freshly fetched remote (local-only / remote-only commits): 0	0.
- Active branch versus remote main (local-only / main-only commits): 48	1.
- No staged or tracked working-file changes. Untracked local build/, dist/, neurafs.egg-info/ and neurafs_uninstall.log are preserved only in the local snapshot.
- Original local main tracking information is recorded separately; it is not the active branch. No merge, reset, checkout, overwrite or push was performed on the old project.

## Validation and limits
- Boundary and ignore-rule tests executed on this Windows host. CI is configured for Windows, Linux and macOS; their remote results require a completed GitHub run.
- Production runtime, final UI toolkit and pixel/behavior parity are future implementation work; parity is documented as a mandatory acceptance gate.
- NAS snapshot is point-in-time, not a continuous backup. Git status and hashes were checked during capture; later user edits do not synchronize automatically.
- Initial GitHub repository creation was temporarily rejected by automatic review; after proving legacy exclusion and that the operation created only an empty private repository, creation succeeded.
