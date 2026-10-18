# Native addon construction R2 closure

Status: frozen after the three reproduced R2 regressions were corrected in the isolated worktree.

The malformed SavedVariables path now validates the marker type before every field read. A scalar or other malformed marker keeps the Agent unconstructed, keeps the Scanner fenced, and leaves the Commands-owned Restore control reachable. The exact `agent recover` command is the current addon-owned admission actor; the Restore control remains inert before that command, and command arguments are rejected by the fixed grammar. Deferred construction installs the same 1 Hz surface publication callback used by ordinary boots before its first publication, so real `update_agent(1)` advances the frame after construction and after the Resume/Finalize fence.

R1 files outside the two production files and focused regressions are byte-identical to the frozen R1 tree. The exact checks and SHA-256 values are recorded in `native-addon-construction-r2-freeze.json`.

Verified:

- 75 native lifecycle tests passed, with 99 deselected.
- 179 addon and companion tests passed.
- 4 compiled atlas/frame smoke tests passed, with 63 deselected.
- Ruff check, Ruff format check, Python compileall, and `git diff --check` passed.

No live game, deployment, daemon/helper, or service changes were made.
