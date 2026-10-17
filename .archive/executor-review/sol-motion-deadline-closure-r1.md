# Sol review: motion deadline closure r1

Reviewed only the policy arbitration and three-file delta in `parent-motion-deadline-closure-r1.diff`. I did not run tests, operate the game, or inspect unrelated native-capability behavior. The supplied freeze records three changed paths and no fence violations. The supplied validation evidence is 27 focused worker tests passing and 19 strict parent tests passing with 126 deselected; this is not a claim that the full suite is green or that live qualification is complete.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

The production delta implements the authoritative timing policy without weakening a refusal boundary. `src/crowley/session/daemon.py:3043-3046` and `src/crowley/session/daemon.py:3079-3082` still reject a pulse that cannot preserve the post-release reserve, and both checks remain before `run_motion_key_hold` at `src/crowley/session/daemon.py:3087`. Only proof invalidation was removed. The shared budget helper at `src/crowley/session/daemon.py:2014-2020` now reports budget/clock failure without mutating motion proofs, which is consistent with its motion and non-motion callers. Initial deadline setup failure still clears both proofs at `src/crowley/session/daemon.py:134-138`, interaction/lease/generation failure still clears through `src/crowley/session/daemon.py:1977-1984`, and failed required native observation or successor validation still clears through `src/crowley/session/daemon.py:2188-2214`.

The focused regressions exercise the intended distinction. `tests/test_session_motion_integration.py:1641-1664` retains the exact proof objects and observes no keydown for a key pulse that cannot fit the reserve. The camera case at `tests/test_session_motion_integration.py:1671-1685` retains both exact objects and observes no mousedown, while the unchanged camera guard remains before `run_camera_drag`. The waypoint case at `tests/test_session_motion_integration.py:1692-1713` uses valid numeric IPC arguments, reaches daemon budget handling, retains both exact objects, and observes neither key nor mouse input. The genuine daemon response-envelope case at `tests/test_session_executor_movement.py:1084-1125` additionally proves that the pre-input waypoint refusal preserves both objects and calls neither physical executor.

The lock assertion is no longer vacuous. `tests/test_session_motion_integration.py:1341-1382` first reaches the real initial-clock failure, then has a different thread acquire and release the daemon's actual `RLock`, joins that thread, and requires successful acquisition. If the dispatching thread retained the lock, the cross-thread timed acquisition would fail and the test would fail.

STATUS: READY
