# Consolidated C/D1 correction contract

Actual Opus executors-r2 exited0, model claude-opus-5-5, MAJOR ISSUES.
Read its full report. All M1–M8 and material S1–S10 are accepted. Sol's
independent source review agrees on six blockers and three should-fixes;
its reported model was gpt-6.1-sol, so the final named-pair re-review will use
a fresh explicitly configured gpt-5.6-sol worker. No earlier green unit test
or review establishes live executor acceptance.

The repair must traverse installed/default entrypoints. This is a D1 contract
revision rather than another planner-only patch. Implement in this order:

1. One ownership fence for engine/interaction intents; controller generation
   admits requests, lease generation admits actual input. Keep these distinct
   after pause/takeover/restart/block. Fix anchor ownership too. Interaction
   startup/resume must retain reconciliation and real proof/arming gates;
   only READY with the current armed lease permits intents. Exit revokes and
   releases an in-flight action. Never queue a second concurrent motion intent.
2. Explicit KeyRole -> wire-field -> supported unmodified level-0 X keysym and
   measured keycode. Native W must dispatch lowercase/unshifted w, with no Shift.
   Dedicated positive argv schemas for key pulse, motion, single click and
   right-held camera drag, tied to the typed plan. Test real _run dispatch using
   a harmless executable, not just recorded argument equality.
3. Shared certified outer/client/WM-frame target predicate for every action.
   Wait for asynchronous complete XI2 correlation before clearing ownership;
   incomplete finish must reject/revoke. Camera press at start BEFORE motion,
   ordered motion/echo WHILE held, release at endpoint. Verify exact held set
   and cancellation during both motion and dwell. Camera starts on a fresh
   measured world-viewport point clear of UI/units, with meaningful drag length.
   Key movement refuses focused chat/edit state.
4. One end-to-end absolute deadline through capture/native polling/model/action
   and waits. Cross-domain transitions use post-dispatch capture lower bounds;
   the first accepted post observation establishes source/boot, then strictly
   increasing own-domain sequences/times. Never compare raw counters across
   boot/source. Judge each observation's freshness on arrival and only latest
   freshness at decision. Any hidden rejection/error resets settle evidence.
   Model/capture work must fit remaining age/action/deadline budgets.
5. Real post-effect motion feedback must be published after release, not merely
   newer than pre-effect. Observe/drain the sequence visible after completion,
   then require a later publication, or an equally rigorous calibrated clock
   boundary. Preserve one identity/boot/instance/zone/frame chain throughout.
6. Native frame FIRST, then a screenshot-derived egocentric corridor for the
   actual upcoming direction/distance. Bind route evidence to frame identity,
   controller generation, boot/sequence, instance/zone, screenshot digest and
   requested corridor. Prove a directly-ahead corridor for basis calibration,
   not an assumed world +X endpoint. Re-prove after turns and before all manual
   translation pulses; enforce freshness at dispatch. An honest negative route
   observation is a valid rejection, not malformed data. Camera turns alone
   are not translational route progress.
7. Measure both orientation and handedness of native facing -> XY, using
   non-collinear native feedback (second heading or measured strafe). One
   offset at one heading does not establish handedness. No caller-supplied
   mappings/prefix assertions; remove unused install_camera_mapping. Store
   actual calibrated displacement/pulse duration and use measured speed, not
   stationary GetUnitSpeed=0, to size bounded pulses. Defaults and displacement
   bounds must agree. Arrival tolerance must be achievable at minimum pulse.
8. Cap cumulative measured travel at two world units per local intent; stop
   immediately on meaningful wrong-direction travel, abnormal Z/scene change,
   excessive camera response error, stale frames or failure to progress. Keep
   distinct finite turn/no-motion budgets. Preserve frame chaining before
   every physical commitment. Both calibration probes share a cumulative cap.
9. Executable, realistic profile bounds, including minimum press dwell and
   minimum usable sample count. Fit a reproducible timing model across target
   difficulties; target_width means minimum safe dimension. Replay measured
   peak curvature rather than half its value. MOVE summaries must change a
   role-appropriate pulse preference actually used with measured displacement;
   role files must affect only their executor. Do not claim numeric summaries
   are actual live-human demonstrations.
10. CLI timeouts exceed the bounded server operation/cleanup window. A socket
    timeout or capture OSError must not claim the daemon is absent while input
    continues: cancel/revoke or report explicit indeterminate operation state.
    Catch operational errors without stranding a handler or held input.

Required tests exercise real SessionIPC -> controller epoch -> lease epoch ->
real driver/binding lookup/positive argv/Guardian completion. Cover restart and
takeover drift, delayed/missing/wrong-target events, camera phase permutations,
cross-source/new-boot enter_world through the real observer, negative route,
changed boot/instance/zone/Z before each dispatch, wrong direction, cumulative
travel, camera-only correction, calibrated run speed and selected wrong/missing
role files. Stop replacing the whole interaction gate/driver/route path with
stubs. Fakes belong only at genuine external capture/model/process boundaries;
production never branches on fake/backend type to alter its contract.

Prior small test issues are accepted: real WINDOW=outer fixture with certified
ancestry; small accepted model-box jitter; genuine coalesced skipped events;
no vacuous profile/trace assertions. Preserve all D0 schema2/CRS1/atlas/native
budgets and scan data. No production arming or WoW input during coding.

Independent GTK prerequisite worker owns ONLY calibration.py create child env
and _verify geometry commands plus native tests. It pins child GDK_BACKEND=x11
and fixes unsupported xwininfo -geometry to -stats. C/D1 worker must not touch
that fence until explicit transfer. Further native sibling certification
requires an actual complete owned-target tree/properties receipt, not the
current truncated diagnostic or relaxed parent/sibling checks. Remove helper
compatibility wrappers before acceptance. Synthetic GTK pointer timing alone
does not prove D1 runtime action correlation or native WoW mouselook warps.

Freeze C correctness milestone with targeted production-path checks before
continuing D1 repairs, then report FINALDONE with all scoped strict checks.
Parent verifies and reruns fresh Sol + actual Opus; no claim of native execution
until real evidence. No commit/reset/stash/revert or unowned source edits.
