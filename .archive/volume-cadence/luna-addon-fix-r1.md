DONE — implementation scope complete.

Changed only owned addon/harness/test/docs paths, including:

- Immutable per-sweep generation and plan provenance; stale sweep timers cannot affect later sweeps.
- Earliest-deadline timer dispatch plus explicit `advance_with_timers`.
- Real 1-second 428-item acceptance fixture using the rolling throttle: 429 sends, 428 full rows, 22,616 base64 characters.
- Added regressions for timer ordering, immutable plan snapshots, and sweep timeout behavior.
- Added `SendSearchQuery` foreign-hook coverage and documented the correlation assumptions.
- Removed the leftover harness replication-state relic.

Verification:

- `21 passed` — `tests/test_addon.py`
- `46 passed` — non-DB suite excluding server/volume tests
- Ruff check, format check, and `git diff --check` passed.
