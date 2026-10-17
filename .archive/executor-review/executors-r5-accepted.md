# R5 final bounded contract correction

Actual Opus r5 exit0/claude-opus-5-5 NEEDS WORK. Read its complete report.
This replaces repeated scalar waypoint patches with explicit 2D endpoint
admission and completes the concrete startup-cancellation contract. Independent
live RawMotion trace identified a distinct parser gap; integrate it coherently,
not by ignoring an unknown event or weakening delivered-motion evidence.

## D1 fence and acceptance

Own daemon.py, motion.py, tests/test_session_executor_movement.py,
tests/test_session_motion_integration.py, tests/test_session_runtime.py only.
Accept Opus M1/S1 and lower-gap/early-handedness nits. Use one named heading
allowance consistently in dispatch and exact 2D worst-case endpoint admission.
Pick a supported conservative allowance and calculate max miss at both calibrated
speed-envelope extremes and that heading allowance. Keep min pulse/profile
ceiling/20% uncertainty/cumulative2 units/corridor/pose/deadline unchanged.
Preflight before camera or translation must refuse unsupported requests; after
camera correction re-evaluate actual bearing before translation. Document the
actual admitted ranges including the lower minimum-pulse gap; no universal1.4
or whole-band guarantee. Preserve usable .9/1.0/1.1 straight-ahead targets when
feasible, but correctness is measured by exact 2D proof, not retaining a number.
Tests must call actual executor for nonzero positive/negative bearing at error
extremes; minimum-pulse admitted [~.392,.56), too-short refusal (~.28,.392),
profile ceiling refusal, and calibration with mirrored strafe refusing before
basis assignment. Fix/rename old2.0 tests that only reach preflight now; replace
arithmetic-only tests where they claim executor coverage.
Also repair observed full-suite clock-domain defect: native capture-start uses
self._native_clock consistently with driver/calibration. No test-clock fallback,
fixture timestamp tolerance or validator relaxation. Add direct regression and
reproduce three-cycle socket lifecycle. No C/helper/profile/wire/GUI/git edits.

## C fence and acceptance

Own input_events.py, guardian.py, driver.py, calibration.py,
tests/test_session_native.py, tests/test_session_native_regressions.py,
tests/test_session_dispatch.py, .archive/executor-review/owned-gesture-proof.py,
.md and test_owned_gesture_proof.py only. Existing C input-tool tests may run
but not be edited without a concrete contract need reported to parent.
Accept Opus M2/S2 and unregister-error note nit. Compare Guardian current epoch
with the exact driver-recorded begin epoch under the lock at both GTK admission
and ticket issue. Do not adopt a new epoch after stop/revoke. Cancel/revoke after
begin => no release/no registration; revoke after admission => no ticket. Cover
real GTK startup identity timeout/nonJSON/incomplete/PID mismatch with reap then
unregister then immediate same-driver retry; preserve cleanup on cleanup failure.

Add explicit XI2 type17 RawMotion and is_raw classification. Raw records never
prove endpoint/target/action or complete an action. They can be admitted ONLY
inside the same current pointer action/epoch from its measured XTEST source and
raw master pair, queued until a same-server-timestamp primary delivered Motion.
Retain exact delivered ancestry/coordinates/path/echo matcher and release order.
Pending unpaired raw prevents finish; wrong source/master/time, human or idle/
post-release raw revokes. Additional raw evidence may not be discarded; normal
legacy no-raw fixture traces still require unchanged delivered evidence (this
is one correlation algorithm, not a weaker alternate injection path). Share the
pairing logic across runtime/calibration/owned helper to avoid drift. No hardcoded
source IDs;4/2 raw and4/4 delivered are this host's measured example only.

Tests: actual captured type17 block, complete incremental parser delivery,
valid same-time raw+delivered pair, raw without delivered never completes,
wrong source/master/time/target and human/idle/post-release raw reject;
existing no-raw delivered contracts and final releases remain strict. Evidence
serialization includes bounded raw_lines to diagnose valuators, without inventing
axis meaning. Add bounded owned GTK seed-only mode to diagnose ONE pointer move,
no click, after parent review; no live run in coding scope. Full positive/cancel
modes still stop on first failed invariant. Do not mask the existing wrong-
coordinate receipt or assume compositor cause before the next exact trace.

## Workflow / prohibitions

Read CLAUDE/AGENTS/applicable skills and this entire plan. No production arming,
GUI/input, global leases during tests, services/display/streaming changes, saved
data, commits/resets/stash/reverts. Keep exact disjoint fences. Run strict
hermetic targeted tests using run_hermetic_tests.py and unique private test lease,
scoped Ruff/format/compile. Retain handles and actual final summaries. Report red
regressions before repairs, final changed paths, limitations and DONE only when
complete. Parent reproduces, freezes, Sol reviews and actual focused Opus review
follow. Full suite641passed/one real clock failure is baseline, not acceptance.

### Parent inspection completion in the same fence

First C parent strict run167 passed154.21s. Before independent review, replace
copied raw queues with one shared forward-only one-to-one pairing state: overflow
rejects instead of truncating unresolved evidence; no backward pairing to already
seen delivered history; duplicate raw records need distinct following primaries.
Tests cover actual consumers, not just helper arithmetic. GTK unregister failures
must be attached as notes, not swallowed.

D1 pre-camera proof cannot assume heading0 when current bearing exceeds the
translation gate: camera may finish anywhere inside the admitted residual bound.
Use conservative admissibility or an explicitly enforced per-target heading
contract. Include final confirmed-pose drift in endpoint feasibility, using the
actual confirmed dispatch frame before keys or conservative shared tolerances.
Tests include infeasible camera-required request with zero physical calls and
admitted confirmation drift. Preserve single corridor proof/final pose admission.
