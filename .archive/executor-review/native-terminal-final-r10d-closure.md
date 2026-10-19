# Native terminal proof R10d closure

R10d made the minimal test-only correction requested after source inspection found that the cancel-wins branch did not perform the later public terminal recheck it claimed. The worktree was `/home/dev/.cache/crowley/worktrees/native-terminal-final-r10d-20261019` at base `c5e577200adadb8c158b1009643aa0f746d98753`. Only `tests/test_session_native_regressions.py` changed relative to R10c; the six other fenced files are byte-identical.

In `test_native_construction_composes_real_png_runner_and_finalize`, the cancel-wins branch now calls `daemon.native_construction_recheck(expected_generation=7, reservation_id=reservation["reservationId"])` immediately after the existing `capture_index == 105` assertion. It asserts both `terminal["handshake"]["state"] == "cancelled"` and `terminal["reservation"]["reservationState"] == "cancelled"`. The earlier cancel response, worker error, no-rebind/no-observe/no-native-calibrated, controller-state, checkpoint, and capture-count assertions remain intact. The final two composed cases passed:

- `2 passed in 43.30s; exit_code=0`
- Log: `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-terminal-final-r10d-20261019/focused-r10d-two.log`
- Log SHA256: `fbd30386a9d948992b7f9337adfa6f16f89b69b9a22609448d2cf8b3b5cbec2a`

The supplementary `/bin/sleep` child-admission test docstring now says it exercises outer capability refusal and child cleanup. It explicitly leaves the four compiled producer cases as the Guardian-generation fence proof; no surrogate test is counted for that proof.

Scoped checks passed on all seven fenced files: Ruff format check, Ruff lint, Python compileall, and `git diff --check`. The static log is `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-terminal-final-r10d-20261019/static-r10d.log` (SHA256 `c1e2b58277b81886a2f23a2fbcccc6ea461b521dc3b623fcb86c76a10c5a9b24`). The AST fence log is `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-terminal-final-r10d-20261019/ast-fence-r10d.log` (SHA256 `d89764f70148bba6628069e6850fc4455f02aa3cc9acec90b45109c03b6ae61d`); it reports only `test_native_construction_composes_real_png_runner_and_finalize` and `test_native_guardian_generation_fence_covers_real_child_admission` changed against R10c. All private evidence logs are mode 0600 in a mode 0700 directory, and no stale pytest, producer, Xvfb, or dbus-run-session processes remained.

The exact six readonly hashes and final writable-file hash are recorded in `native-terminal-final-r10d-freeze.json`. No production file, helper, driver, Guardian, configuration, service, GUI, or Git state was changed. No full suite or unrelated focused suite was rerun. Parent source inspection and review remain pending; this report makes no deployment or live acceptance claim.
