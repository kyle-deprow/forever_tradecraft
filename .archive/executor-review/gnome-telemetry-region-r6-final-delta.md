# R5 to R6 final activation/action and PNG publication closure

This successor freeze is based on the hash-verified R5 forwarding candidate at
`2a8d73e`. It keeps the R3/R5 caches, binaries, source freezes, and all
previous failure evidence immutable. The private R6 build remains the existing
stage-only artifact in `/home/dev/.cache/crowley/gnome-telemetry-region-r6`,
with the pinned image
`sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858`.

The compiled producer rejects GApplication activation and every application
action route at the telemetry process boundary before shared-option mutation,
capture, or UI. The native forwarding regression drives genuine private-bus
`Activate`, `ActivateAction`, and `org.gtk.Actions.Activate` calls while a real
Shell capture is blocked, releases the gate before waiting for synchronous
children, and joins/reaps all started children. It checks exact primary guard
diagnostics, no remote output or extra Shell capture, the stock model, and
completion of the original capture. The stale fake backend regression now
asserts production X11-only refusal while preserving the stock-model half.

R6 also removes the stale profile-anchor exclusion from full profile
comparison, records pre-producer failures as typed `not_started` evidence, and
binds the example and harness to the R6 producer, manifest, patch, and binary.

The parent plan amendment extends the original eight-file R6 ownership by
exactly two paths:

- `src/crowley/session/driver.py`, limited to `_wait_for_complete_png`;
- `tests/test_session_capture.py`, limited to deterministic helper regressions.

After an incomplete read, `_wait_for_complete_png` retains the single process
poll result. Nonzero exit remains terminal. For clean exit, the existing epoch
check runs before one final PNG validation and again after it; a newly complete
PNG returns, fresh incomplete output fails with its fresh producer diagnostic,
and invalid output remains terminal. There is no added sleep, retry loop,
deadline extension, fallback, or relaxed identity/protocol check. The three
new helper tests cover atomic completion during `poll()`, clean exit with
truncated output, and revocation winning before the final read.

Verification passed:

- `tests/test_session_capture.py`: 35 passed;
- compiled default composition: 1 passed;
- real paused eight-sample runner: 1 passed;
- stale fake backend production-refusal/stock-model regression: 1 passed;
- offline harness self-test and self-check;
- scoped Ruff, format, `py_compile`, JSON/TOML parsing, clean-archive patch
  dry run, and source-only diff check.

The earlier three-way stress failure, the R5 parent batch's stale fake backend
failure, and both pre-fix R6 serial undecodable-PNG observations remain
retained in the successor freeze. The pre-fix evidence does not establish a
blanket live reliability claim; the amended helper boundary is supported by
the deterministic regressions and the two compiled integration nodes.

The historical
`.archive/executor-review/gnome-telemetry-region-r6-freeze.json` and
`gnome-telemetry-region-r6-delta.md` are preserved unchanged. No deployment,
live opt-in, or Git mutation was performed.
