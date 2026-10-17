# Final input contract correction

Read AGENTS.md, CLAUDE.md and existing local-game-control skill. Do not commit, reset, stash, revert others, perform GUI input, modify production services/data, or change motion budgets. Keep source frozen once tests finish.

## Scope and order
1. Shared CARD32 timestamp validation, forward/equal order and bounded elapsed helper in input_events.py. Reject invalid/ambiguous timestamps. Use in RawMotionPairing, Guardian retained arrival clock/echo windows, calibration sequence+echo consumer, diagnostic helper duration/order. Exact pending FIFO-head primary Motion alone may bypass later raw arrival time; retain arrival-domain maximum modulo32. Preserve every existing attribution, echo, target, coordinate, modifier, pending and release check.
2. Strict RawMotion parser must reject malformed detail at its native blank delimiter immediately. Preserve raw failing observer text and exact parser reason for private diagnostic receipt; use a small explicit monitor diagnostic API rather than weakening event validity. Test open-idle stream malformed block and final private diagnostic output. Keep detail exactly0.
3. Seed-only uses existing 1ms _run_seed_chain, returning actual process result/error, preserving start/requested/post even on dispatch failure. Reject start==endpoint before dispatch. Receipt scope accurately excludes clicks, holds, cancellation, calibration, human/game acceptance.
4. Add actual runtime open_ah detail0 raw before delivered motion and camera-ordered press/raw/motion/echo/release test with real driver begin_action arguments. Full native formatter shape flags/accelerated(raw) in relevant idle regression fixtures. Correct provenance to matching xwayland-24.1.6 tag, verify source if not already available.

## Owned files
src/crowley/session/input_events.py
src/crowley/session/guardian.py
src/crowley/session/calibration.py
src/crowley/session/driver.py (only monitor error/raw diagnostics required in step2)
tests/test_session_native.py
tests/test_session_native_regressions.py
tests/test_session_dispatch.py
.archive/executor-review/owned-gesture-proof.py
.archive/executor-review/test_owned_gesture_proof.py
.archive/executor-review/owned-gesture-proof.md

No daemon/motion/movement tests/docs or other files. The parent owns freeze/diff/review/docs. D1 nit handled separately.

## Acceptance / verification
Real Guardian and calibration consumers: raw11/raw12/primary11/primary12 accepted; incomplete pending rejected; non-head primary rejected; rawMAX/primaryMAX/raw0/primary0 accepted; invalid/backward/half-domain timestamps rejected. Exact echo matching and elapsed durations cross wrap. Parser invalid raw detail raises at blank delimiter, carries complete failed raw text+cause into diagnostics. Real click/camera entrypoint action arguments exercised including required modifiers and coordinates. Seed process success/failure and no-op-before-dispatch covered.
Run env -u CROWLEY_TEST_DATABASE_URL CROWLEY_DESKTOP_LEASE=/tmp/crowley-luna-final-card32.lock uv run python .archive/executor-review/run_hermetic_tests.py tests/test_session_native.py tests/test_session_native_regressions.py tests/test_session_dispatch.py .archive/executor-review/test_owned_gesture_proof.py
Also scoped ruff check/format checks. No live input or installed artifact changes. Report exact files/tests/results/unresolved issues; final DONE only complete.
