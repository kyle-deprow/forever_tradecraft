# Opus r4 bounded correction

Actual Claude Opus 5.5 review exit0, NEEDS WORK. C emission ownership is
source-ready; D1 has a deterministic waypoint gap. Do not expand the runtime.
Read the r4 report and parent arbitration here before editing. No GUI authority.

D1 owns daemon.py, motion.py, model.py, tests/test_session_executor_movement.py,
tests/test_session_motion_integration.py, tests/test_session_executor.py only.
Accept M1, S1, S2, S3. Replace the patchwork waypoint planner with a small,
explicit robust admissibility calculation. Keep the 2-unit cumulative envelope,
minimum pulse, 20% uncertainty and all corridor/pose/deadline guards unchanged.
Admit feasible targets (including .9,1.0,1.1 at speed7/minpulse.08) and refuse
before any translation when no guaranteed plan fits the envelope. Whole-band
convergence is mathematically incompatible with current uncertainty near2;
record the actual admissible bound, never make tests imply universal convergence.
Exercise bounded positive/negative per-pulse error, including alternating error.
Handle handedness in route model input and matching consistently, or explicitly
refuse unsupported -1 before calibration is accepted. Preserve measured sign.
Add actual runtime consumer delayed-model receipt/settling regression, not just
pure-function tests. Remove motion.py test-clock fallback; correct fixtures.
Named state freshness uses capture start. No other executor redesign.

C owns driver.py, calibration.py, tests/test_session_native_regressions.py,
tests/test_session_driver_actions.py, tests/test_session_input_tool.py only.
Accept S4: every failed GTK create after registration must unregister/reap the
owned group before returning, allowing a fresh begin on the same driver. Gate
release must recheck epoch/health while under Guardian lock. Unknown explicit
input_schema rejects before admission; keep documented legacy None behavior.
Add meaningful failure-retry/cancel-before-gate/schema tests. Preserve prior
release ordering, pin lifetime, exact typed argv and gate-only ownership.

Forbidden for both: other source, profiles/services/GUI/git/leases/real input,
wire format/budgets, bypassing observer/matchers, fallback paths. Never commit,
reset, stash or revert others. Parent owns docs and acceptance decisions.

Run scoped strict hermetic pytest via run_hermetic_tests.py with distinct private
CROWLEY_DESKTOP_LEASE and -u CROWLEY_TEST_DATABASE_URL. Scoped Ruff check/format
check and compile. Report actual handles/final results and changed file hashes;
DONE only after complete. Parent reproduces and re-reviews before live release.
