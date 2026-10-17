# Sol review: motion deadline closure r2

Reviewed only the test-only r2 delta and the production guard context needed to assess it. I did not run tests, operate the game, or reopen the broader native-capability source review. The supplied freeze records the same three changed paths and no fence violations; the production delta remains the three previously reviewed deletions. The supplied parent result is 19 strict tests passing with 126 deselected, plus the stated static checks, rather than a full-suite claim.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

The r2 assertions close both accepted test gaps. The key case at `tests/test_session_motion_integration.py:1641-1664` now requires the exact first-guard refusal, exact proof-object retention, and no keydown. The camera case at `tests/test_session_motion_integration.py:1671-1686` uses the controlled 0.6-second margin, requires the exact drag-fit refusal, and requires two actual native publications. That publication count proves the initial frame and pose-confirmation successor were both observed before the guard at `src/crowley/session/daemon.py:3171-3174`; the no-mousedown assertion proves refusal before `run_camera_drag` at `src/crowley/session/daemon.py:3182`.

The waypoint case at `tests/test_session_motion_integration.py:1693-1715` now exercises the previously uncovered second key guard. With valid numeric IPC arguments, the route is obtained and the first reserve check at `src/crowley/session/daemon.py:3043-3046` passes. Requiring exactly two native publications proves `_confirm_motion_pose` at `src/crowley/session/daemon.py:3069` returned a real successor. The exact `motion pulse cannot fit the bounded intent deadline` error, combined with that count, locates the refusal at the second guard at `src/crowley/session/daemon.py:3079-3082`. Exact proof identities survive, and the absence of keydown or mousedown establishes zero late input before `run_motion_key_hold` at `src/crowley/session/daemon.py:3087`.

These assertions would fail if the cases stopped at the earlier route/viewport evidence-budget checks, if waypoint stopped at the first key guard, or if either reviewed proof invalidation were restored.

STATUS: READY
