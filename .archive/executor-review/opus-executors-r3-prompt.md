You are the independent Opus reviewer of Crowley's natural interaction executors.
Read-only review: do not edit files, write plans, run commands, commit, reset,
change services, operate the desktop, or create evidence. Only Read/Grep/Glob
are available. State your actual model. Review the current source rather than
treating prior reports or test counts as acceptance.

Read CLAUDE.md, AGENTS.md, .archive/PLAN-natural-executors.md, the current top
of docs/HANDOFF.md, and .agents/skills/local-game-control/SKILL.md. For schema2
context read .agents/skills/crowley-client-contracts/SKILL.md. The requested
result is realistic, bounded pointer curves/click dwell/waits/key pulses/camera
drags/local waypoint executors with per-role numeric preferences, integrated
with the existing controller, input lease, asynchronous XI2 correlation and
actual native feedback. Protected trading remains one user click per action.
Also read .archive/PLAN-private-xdotool.md for the canonical injection correction
and its independently reviewed ownership/release requirements.

Review these source paths and their direct contracts:
src/crowley/session/{executor,preferences,motion,driver,guardian,daemon,controller,
model,config,cli,calibration}.py. Source files are currently untracked relative
to HEAD, so read the files rather than relying on a tracked diff. Focus on the
natural-executor implementation and integration, preserving native wire and
existing scan requirements. Do not review unrelated catalog/server changes.
Include src/crowley/session/input_tool.py and tools/build_crowley_xdotool.py.
Include src/crowley/session/process_admission.py and the shared process-gate
contract across runtime, XI2 observer and owned GTK bootstrap.

Relevant tests: tests/test_session_executor.py,
test_session_preferences.py, test_session_executor_dispatch.py,
test_session_executor_movement.py, test_session_movement_dispatch.py,
test_session_driver_actions.py, test_session_motion_integration.py,
test_session_cli_motion.py,
test_session_input_tool.py,
test_session_runtime.py, test_session_transitions.py, test_session_native.py,
test_session_native_regressions.py, and the two guardian-fixture regression
tests named in the latest plan. Check real production entrypoints; test doubles
must stay at genuine external process/capture/model boundaries and must not
replace the controller/lease/driver/Guardian contract being asserted.

The prior actual Opus report is .archive/executor-review/opus-executors-r2.txt;
its accepted specification is executors-r2-accepted.md. Independent Sol reports
are sol-profile-r1.md, sol-gtk-certificate-r1.md, sol-c-r3.md,
sol-private-tool-r1.md, sol-integration-r4.md and sol-integration-r5.md. Final correction reports and
parent verification will be listed below before this round launches. Evaluate actual repairs and
new regressions independently. Pay equal attention to plausible timings and
curves, role learning/persistence, and effective feedback/ownership/deadlines.
Distinguish automated source tests, synthetic owned-GTK observations, actual
native telemetry, and physical-human or real WoW executor evidence. Missing
live evidence must remain explicit; do not infer proof from numeric imports or
planner-only tests.

Measured current native game structure is fullscreen root→outer→one Wine client;
the implementation pins this exact supported relationship. The owned GTK target
separately has a certified Mutter frame plus an advertised InputOnly helper,
excluded from allowed input targets. Do not require guessed alternate WM support.
The current production GTK certificate-only run passed under the global lease
with target reaping, all registries empty and lease released. The positive gesture
attempt retained17 pointer motions from a non-XTEST source and failed before
click/controlled-echo acceptance. The installed xdotool absolute motion was
independently confirmed to use XWarpPointer. This explains a concrete mismatch
with the required XTEST path; it does not establish a Wayland defect or permit
loosening event attribution. The private emitter correction must be assessed
using its actual final source and retained verification evidence. No human
input calibration or WoW executor proof follows from that failed attempt.

Frozen verification context: source-freeze-r4.json records41 source/test/artifact
hashes. Parent independently reproduced52 strict hermetic D1 checks in123.73s
and63 strict hermetic C/tool/driver checks in12.34s. Global Ruff, formatting
(177 files) and diff checks pass; parent only corrected two formatting-only
changes after the C check. The final full strict hermetic repository suite is
running against this frozen source. Earlier pre-correction full baseline was
579passed/15database skips in455.65s; do not call it final acceptance.
D1's final focused actual Sol review is READY (sol-integration-r5.md). C's final
Sol review could not start: two attempts returned selected-model-at-capacity.
That round is blocked, not READY, and this requested independent Opus review
does not establish a Sol verdict. C's earlier actual Sol report was MAJOR ISSUES;
evaluate the accepted corrections independently using current source/tests.
Worker's later focused native/input checks143passed/150.98s, builder4passed/5s,
watchdog/replacement3passed/1.68s; earlier broad scope323passed/369.40s. These
worker results are supplemental to the parent's focused checks and pending full
run. No native input has been sent using this new tool; the prior failed GTK
attempt remains the only live motion trace. Native proof stays separate.

Report concrete findings with path:line and reproducing conditions, grouped
Must-Fix, Should-Fix and Nits. Check correctness, regressions, error handling,
scope, meaningful tests, typing and input ownership. Prioritize material defects
over hypothetical refactors. Finish with STATUS: READY, NEEDS WORK or MAJOR ISSUES.
