# NeuraFS sync findings

The original repository was read only. Remote heads were verified with ls-remote and divergence/file differences with the GitHub connector compare API. An attempted audit fetch was interrupted during slow NAS IO; API comparisons supply the completed remote verification. The audit directory is separate from the exact file snapshot.

Active local branch `codex/local-neurafs-repair-20261016` and GitHub branch both point to `e5e1fdf19716c73f7ef492717ea1fa4b04c9dff1`: zero unpushed commits, zero incoming commits on that branch. No staged or tracked working-file edits. Four untracked build/output paths remain local.

Relative to remote main (`df8bfab823d63a09c96fde79a3536ff1af47801d`), the active branch is 48 commits ahead and 1 behind. The inactive local main is 1 commit behind remote main. The active branch changes 52 files relative to the merge base.

Both sides change these files: `neurafs/cli.py`, `neurafs/core/config.py`, `neurafs/core/storage.py`. These are potential integration conflicts; no merge was attempted, so textual conflict status is not claimed. No conflicting file was overwritten.

Detailed GitHub comparison is in github-compare.json. Local observations:

## source_status

```text
## codex/local-neurafs-repair-20261016...origin/codex/local-neurafs-repair-20261016
?? build/
?? dist/
?? neurafs.egg-info/
?? neurafs_uninstall.log
```

## source_head

```text
e5e1fdf19716c73f7ef492717ea1fa4b04c9dff1
```

## source_branches

```text
* codex/local-neurafs-repair-20261016 e5e1fdf19 [origin/codex/local-neurafs-repair-20261016] log-interrupted-package-sync
  main                                077457e68 [origin/main: behind 1] Delete index.html.bak
```

## working_diff

```text
```

## staged_diff

```text
```

## remote_refs

```text
e5e1fdf19716c73f7ef492717ea1fa4b04c9dff1	refs/heads/codex/local-neurafs-repair-20261016
3a3ae126e668574a59ad6f1cf04e63d92203d30a	refs/heads/extreme4music-nexus-patch-1
df8bfab823d63a09c96fde79a3536ff1af47801d	refs/heads/main
```

## ahead_behind_upstream

```text
0	0
```

## ahead_behind_main

```text
48	1
```
