# Parent correction verification, 2026-10-16

The full frozen baseline before this correction passed579 tests, skipped15
database tests and emitted one unrelated Starlette/httpx deprecation warning in
455.65seconds. This baseline does not accept the later C or D1 source changes.

After D1's regression-first movement/model/chat corrections, parent reproduced:

```text
env -u CROWLEY_TEST_DATABASE_URL CROWLEY_DESKTOP_LEASE=/tmp/crowley-parent-d1-isolated-r4.lock uv run python .archive/executor-review/run_hermetic_tests.py tests/test_session_executor_movement.py tests/test_session_cli_motion.py
27 passed in 0.27s
```

The runner hides the installed private input artifact and promotes unhandled
thread, unraisable and multiprocessing fork warnings to errors. Scoped Ruff
passed for daemon/motion/model/CLI and their three tests. These checks include
the cumulative minimum-pulse envelope, exact three non-progress translations,
retained model admission/shutdown and per-role calibration regressions. They
are component checks; installed IPC/driver/Guardian integration remains to be
rerun after the concurrent C API repair is coherent and frozen.

Parent source inspection found the new model shutdown error could skip desktop
cleanup. Luna placed that call in the existing cleanup error aggregation and
added a daemon regression asserting cleanup still executes. The canonical model
contract is shutdown(), with test adapters updated rather than a production
fallback. C owns the shared runtime fixture update.

After the C constructor API became coherent, parent reproduced the complete
three-file D1 scope under a fresh private lease and the same strict hermetic
runner: **50 passed in101.44seconds**. Scoped Ruff, format and diff checks pass.
Source/tests remain frozen for the independent Sol rereview. C's full correction
verification is separate and still in progress.

No GUI input, service arming, native acceptance or database mutation was part
of these checks. Final independent Sol and actual Opus reviews remain pending.

The subsequent Sol r4 review found two material gaps (left residual beta and
unsettled post-release feedback); read sol-integration-r4.md. Luna reproduced
all three new regressions failing, then corrected the source. Parent reproduced
the complete frozen D1 scope again: **52 passed in123.73seconds**, strict and
hermetic under a fresh private lease. Scoped Ruff/format/diff checks pass.
The focused final Sol review of those repairs is running; actual Opus remains
pending until the separate C correction passes independent review.
