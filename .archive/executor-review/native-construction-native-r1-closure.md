# Native construction native slice r1 closure

Base: `e6e17bb42474b0251365590e61b87c9307b447fe`.
Worktree: `/home/dev/.cache/crowley/worktrees/native-construction-native-20261018`.

The bounded six-file slice implements the controller-owned schema-1 durable checkpoint, strict public native-construction IPC shapes, canonical private reservation binding, deferred twelve-state handshake, recovery ticket and new ordinary boot proof, reservation race/admission checks, expiry/revocation behavior, and production runner callback integration. The consumed operation bound is 127 seconds: four existing 30-second native provider stages plus the fixed seven-second constructor reserve. Existing per-stage, freshness, release, and finalize deadlines remain independent.

A composed regression uses the production `SessionDaemon.run_native_calibration` and `NativeCalibrationRunner` path. It generates real encoded status PNGs, decodes each through `PixelDecoder`, re-decodes retained artifacts in the runner, uses an injected fresh monotonic clock and the real reset5 meter against an owned harmless process, drives the actual daemon callbacks, consumes finalize admission, and verifies the durable checkpoint remains after finalization. The same path exposed and fixed deferred preconstruction rejecting its initial `running` predecessor, consumed reservations retaining the shorter prepare expiry, and early deletion of the absence artifact before runner seal verification. Preflight cancellation now preserves durable B0; only verified ordinary recovery clears it.

Checks completed in the worker worktree:

- `4 passed, 86 deselected in 33.02s` for native construction regressions.
- `2 passed, 60 deselected in 0.26s` for native construction transitions.
- `90 passed in 51.07s` for all `tests/test_session_native_regressions.py`.
- Scoped Ruff check, format check, compileall, and `git diff --check` passed.

The exact broad suite was attempted during implementation. The environment stopped at the durable runtime test because the installed host executable reports `codex-cli 0.163.0` while the repository boundary requires `0.162.1`; earlier host-load attempts also stopped compiled-region/paused-diagnostic cases on their owner deadline. Parent independently ran the two compiled cases on the accepted baseline with the authentic pinned CLI and obtained `2 passed, 146 deselected in 73.48s`. These broad-suite observations remain recorded as evidence and were not relabeled as source compatibility.

Final and read-only baseline hashes are frozen in `native-construction-native-r1-freeze.json`. No source outside the six-file fence was edited, and no commit, service, GUI, capture, or deployment operation was performed by this worker.
