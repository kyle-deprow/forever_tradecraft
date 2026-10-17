# Sol bounded implementation review: transition r11 final r1

Reviewer role requested: Sol at `xhigh`. This worker is not given reliable serving-model or serving-effort metadata, so I do not claim either.

I reviewed the 1,847-line, 11-path `transition-r11-final-r1.diff` against the r10 material identified in the arbitration, with only the implicated local context. I read the active plan, arbitration, prior Sol r1 report, and actual Opus r10 report. I independently verified all 43 paths against `source-freeze-transition-r11-final-r1.json` with zero hash mismatches. I made no source changes, ran no tests, sent no game input, and performed no git mutation. The parent-reported 34 focused passes, 408 affected passes, and global Ruff/format/diff checks are supplied evidence; the in-progress full DB suite is not treated as a pass.

The production changes close the prior phase-origin defect, restore the protected-click order, derive the single baseline transition from the recorded prefix, bind the new seal facts, refuse a zero-length producer move, add the helper endpoint queries and raw prerequisite, restore camera guards, and carry generation/deadline into profile reads. The new real-boundary test also carries the real harmless producer result through parsed XI2 records, builder/seal, X11 arm/profile/observer ownership, and Guardian MAX-to-zero admission. I found no new production correctness defect in that chain.

## Must-Fix

None.

## Should-Fix

1. `tests/test_session_runtime.py:374` still lets unknown native commands fall through to the inherited production `X11Backend._run`. The new `xtest_input_profile` override at line 421 prevents the one command sequence that failed the prior full run, but it does not implement the arbitration's closed fixture boundary. A new or reordered runtime read can therefore spawn host `xinput`, `xwininfo`, or another allowed native command with the fixture's fake display credentials, returning the suite to host-dependent failure before any fixture assertion. Give `LifecycleBackend` a closed command dispatcher or otherwise reject every unmodeled argv, and add a regression that an unknown argv fails locally without invoking a host executable.

2. `tests/test_session_executor_dispatch.py:410` does not prove the restored protected-click order in `driver.py:2050-2125`. The test only asserts that a stale fresh anchor prevents `mousedown`; it also passed when foreground/refresh happened before motion, which was the rejected r10 ordering. Log the motion command, identity check, refresh, consumption/prequery, click, and postquery boundaries. At minimum, the existing refresh-failure case must assert that pointer motion already occurred before refresh refused; a successful case should assert the full required order. This prevents a future reorder from hiding visual-observation latency before motion while keeping the suite green.

3. `.archive/executor-review/test_owned_gesture_proof.py:622` covers the repaired callback-to-batch success path, but it does not cover either fail-closed half of accepted S4. No test feeds the real callback a primary Motion without a preceding raw record, and no test reaches the positive or mid-hold pre-button boundary with a wrong endpoint or uncertified window. Consequently, deletion of the raw prerequisite or `_require_owned_pointer_endpoint` calls at `owned-gesture-proof.py:1630` and `:1848` leaves the focused tests green and could allow the helper to enter a button phase without proved motion ancestry/ownership. Exercise the callback with an orphan primary and exercise both helper flows with an external pointer query returning a wrong endpoint/window; assert the violation/refusal occurs before phase transition or any button command.

4. The calibration producer and seal hardening lack negative regressions at their accepted boundaries. `tests/test_session_native.py:235` still issues a zero-length `(1,1)->(1,1)` evidence fixture, no test invokes `X11Backend.synthetic_calibration` with `origin == requested` and proves that F13/move/click were not dispatched, and the generic tamper test at `tests/test_session_native.py:4059` does not mutate the new transition/query/event-root/echo-root/one-to-one bindings. A regression could remove the producer refusal or the new explicit seal checks while the positive producer chain and current tamper tests remain green. Update the direct evidence fixture to a coherent nonzero transition, add an external command-log producer refusal test, and add validly re-fingerprinted negative evidence for substituted caller transitions, query/postquery mismatch, transition versus event root/event IDs, forwarded-echo IDs, and extra/unpaired source raw/primary facts.

5. `tests/test_session_native.py:298` claims source/axis/mode/CTM coverage, but its mutations cover source ID, mode, range, and CTM only. It does not mutate the header parent or any axis index/label/count, although the plan and arbitration explicitly require parent and axes negatives. In addition, `tests/test_session_driver_actions.py:241` matches the profile-drift error from real `run`/`run_camera_drag` entrypoints but records no dispatched input, so moving the profile refusal after input would still satisfy the assertion. Add captured-output mutations for parent and exact axis structure, and use the existing external input-tool boundary to assert zero input commands before both drift refusals. The real arm-drift case and captured hierarchy/root parsing are otherwise covered by the new connected-chain test.

## Nits

None.

These findings concern the explicitly required regression and hermetic-fixture acceptance criteria. They do not establish any native, GUI, fresh-seed, game, human, or movement acceptance; that proof remains later live work.

STATUS: NEEDS WORK
