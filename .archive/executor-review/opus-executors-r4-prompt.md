You are the independent read-only Opus reviewer of the bounded executors-r3
correction. State actual model. Use only Read/Grep/Glob; no edits, plans, tests,
commands, desktop, services, credentials or git mutations.

Read CLAUDE.md, AGENTS.md, executors-r3-accepted.md and opus-executors-r3.txt in
.archive/executor-review. Read the current HUD/executor section at the top of
docs/HANDOFF.md and .agents/skills/local-game-control/SKILL.md. Review actual
current source, largely untracked, not just reports. source-freeze-r5.json binds
41 source/test/artifact paths and identifies the frozen correction snapshot.
This round focuses on the accepted r3 repairs and direct consumers/regressions;
the prior whole-integration review already covered unchanged surrounding code.
Do not expand into unrelated catalog/server or archived scan history.

C scope: driver.py InputMonitor callback/notification ordering, all three
completion-wait consumers, hold publication and final positive admission commit,
camera optional positioning versus held-drag order, pinned close retention and
isolated wrappers. guardian.py held publishers, health, state construction/write/
ACK serialization, complete final-state drain despite ACK failure, physical
release ordering and close/retry. calibration.py only OwnedGtk bootstrap gate
and cleanup. Check actual async reader/subprocess/lock-contention, watchdog
death after registration ACK before hold publication, pointer-at-start camera,
release/callback order, single gate close and failed-close retry regressions in
test_session_input_tool.py, driver_actions.py, native.py and native_regressions.py.

D1 scope: executor.py FreshObservation receipt and observations_settled contract;
daemon.py arrival/final freshness, MotionFrame capture-start provenance,
minimum-pulse-aware waypoint leg choice and cumulative envelope, one shared
fresh route proof through _execute_motion_key_with_frame, last permitted camera
turn handling and idle interaction READY behavior. motion.py frame provenance;
model.py explicit route zero/sign/native frame/scale/camera-alignment/refusal
prompt. Direct consumers and relevant cases in test_session_executor.py,
executor_movement.py, motion_integration.py and cli_motion.py. In particular,
verify missing/invalid receipt is refused, real model latency can settle,
1.4–1.96-unit target band converges without loosening the two-unit uncertainty
cap, and model/ownership/feedback contracts were not replaced by test doubles.

Proof-helper scope: .archive/executor-review/owned-gesture-proof.py and .md now
use canonical typed schema plus exact expected_argv at every dispatch, including
seed, trajectories, click and both cancellation modes. It proves only typed
emitter/echo/timing/release/cancellation on an owned target; no claim of D1
completion, WoW motion, physical human input or native game calibration.

Preserve the r3 arbitrations: S1 actual capture/model timing, S4 mouselook and
S5/S6 quantization/camera threshold/Click-to-Move remain required live capability
work. Read .archive/PLAN-motion-live-prerequisites.md. No new game movement,
camera action or production arming has been authorized; the game remains
disconnected. API artifacts identify candidates, not actual70425 support/units.
Do not infer native acceptance from tests or scoped source readiness. Flag any
remaining source defect that undermines the accepted C/D1 correction; distinguish
it from these deliberately open native-game prerequisites. Give explicit scoped
findings/readiness for C emission ownership and D1 core as well as one final
overall status, so unresolved game prerequisites are not confused with a safe
owned-GTK emitter experiment.

Verification before launch: parent independently reproduced52 strict hermetic
C correction checks in8.42s and then the strengthened real-watchdog/async-reader
tests2passed/.53s. Global Ruff/format (180files) and diff pass; parent helper
Ruff/format/compile passes. The worker173-collected broad C run lost its final
exit and is NOT claimed passed. Prior full604passed/15DBskips was pre-r3 repair.
Parent independently reproduced all82 strict hermetic D1/executor checks in
123.45s after the explicit receipt fix. The new full strict hermetic repository
run is starting against the unchanged frozen source concurrently with this
review; its result is pending. C final Sol review was unavailable after3 capacity
attempts; no substitution or READY verdict is claimed.

Report material reachable findings with file:line, reproducing conditions and
correct behavior, grouped Must-Fix/Should-Fix/Nits. Do not manufacture marginal
refactors or require speculative alternate APIs/backends. End with one line
STATUS: READY, NEEDS WORK or MAJOR ISSUES.
