# Final suite resource and lifecycle stability

Parent default final-r2: 2451 passed,25 DB skips,4 failures,164.827s external;
all79 frozen hashes unchanged.16 workers meet speed, but expose test-resource
assumptions. Production code is accepted/read-only. Failures: private Xvfb open,
old-generation immediate rearm before physical ownership cleanup, private GTK
worker crash, and modeled mail AH typing exceeding its fixed45s operation.
/tmp is31GB tmpfs,25GB used,12GB from pytest-of-dev. Do not manually delete any
existing test directories, evidence, user data or unrelated resources.

mail_design owns ONLY tests/test_session_dispatch.py,
tests/test_session_keyboard_rehearsal.py, tests/test_session_native_regressions.py
and bounded archive logs. Diagnose real private-server readiness/cleanup and crash
artifacts. Fix lifecycle synchronization, not production deadlines or guard rules.
For revoke/rearm, prove actual physical ownership release, then schedule a real
late old-generation attempt after the new lease and assert rejection. Do not turn
that race into a trivial fully-completed old call. Private Xvfb readiness probes
must bind the owned server/process/display and fail if it dies; no blind sleeps,
retries of wrong identity or global DISPLAY/Home/Popen mutations. Keep original
real X11/GTK and pointer/no-input refusal proofs, no skips/removal.

suite_implement owns ONLY test_session_mail_loop_composition.py and its archive.
The modeled key handler currently publishes/renders/decodes a whole Lua HUD for
EVERY typed character. Preserve every key argv/event/modifier/buffer effect and
semantic open/submit/target/binding/AH effects, but batch the character-only HUD
publication until actual capture/readback. The actual capture path must still
publish real Lua bytes and decode them fresh; no canned snapshots, timestamp
restamp, NO_CHANGE acceptance, deadline inflation or producer method replacement.
Prove exact typed commands/input progression and every existing safety oracle.

launch_design owns ONLY pyproject.toml and test-suite-refactor archive artifacts.
Configure standard pytest tmp_path_retention_policy='failed', keeping existing
retention count. Verify installed pytest implementation semantics: only successful
function-owned disposable tmp paths are cleaned after teardown, failure evidence
stays, no manual cleanup of existing paths. Keep16 bounded worksteal/default all
native cases; no global HOME/stdlib or production/env changes. This is ordinary
automatic cleanup of newly generated test data, not beta/backup/SavedVariables.

Each worker reads CLAUDE, handoff, client skill, R2 parent log and this plan.
Use unique logs and sharedflock/pinnedCARGO for all pytest; keep owning worker
until real output/exit saved. Scoped static checks then freeze/Sol review. Parent
owns final bare default benchmark/hash guards/docs; no commits/services/game/DB.

## Final statistics benchmark correction

Parent final-r3 completed in146.233s,2454passed25DBskips,one failure:
the330-item/240-sweep statistics benchmark used a10s wall-clock budget and
observed10.593s under16 concurrent workers. All native/mail cases passed.
Luna suite_implement owns ONLY tests/test_trading_engine.py and bounded
test-suite-refactor-20261024/statistics-timing-* evidence. The computation forks
up to8 children: aggregate CPU is a different metric from parallel elapsed
time, and invoking-worker CPU omits expensive child work. Parent rejected the
caller-CPU-only candidate. Remove the low-value local10s microbenchmark
assertion and unused time import, retaining the full330x240 calculation and
every semantic assertion. Rename the test to describe full-size coverage.
The user authorized deleting less-important tests/functions; record this
specific assertion removal honestly rather than claiming equivalent timing.
No threshold inflation, mock clocks, production changes, data reduction or
exclusions. The independent parent bare-default real wall-clock gate remains
180s. Focused verification
uses the shared lock/pinned Cargo/default16 workers, then Sol read-only review
and a new frozen parent full run. Parent owns docs and integration.
