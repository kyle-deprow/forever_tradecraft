You are the independent read-only gpt-5.6-sol/xhigh reviewer of the private XTEST
input tool and its process ownership/release integration. Read CLAUDE.md,
AGENTS.md, .agents/skills/local-game-control/SKILL.md, the current top of
docs/HANDOFF.md, .archive/PLAN-private-xdotool.md and the accepted prior report
.archive/executor-review/sol-private-tool-r1.md. Review actual current source;
files are largely untracked relative to HEAD, so do not rely on tracked diffs.

Intent: one fixed pinned-source xdotool artifact whose absolute screen-zero
motion uses XTestFakeMotionEvent. A verified sealed executable image must serve
runtime, calibration, normal release and the independent watchdog consistently.
Exact target/argument/Guardian contracts remain intact. Process helpers require
explicit positive admission after ownership publication; owner EOF aborts.
Owner death, cancellation, disk publication replacement and all constructor
failure exits must retain/release only the exact owned processes and held inputs.
This supports bounded natural executors; no trading or general desktop authority.

Scope: src/crowley/session/{input_tool,process_admission,driver,guardian}.py,
tools/build_crowley_xdotool.py, vendor/README.md and pinned source provenance.
In calibration.py inspect only OwnedGtkCalibrationWindow bootstrap/create
admission and cleanup, preserving its already reviewed native certificate/API.
Read relevant tests in test_session_input_tool.py and the driver/actions,
executor/dispatch, movement/dispatch, native/regressions, runtime/transitions,
session/dispatch/regressions files named in the private-tool plan. The D1
daemon/motion/model/CLI and its three motion tests are separately reviewed;
inspect direct calls only as needed, do not duplicate that broad review.

The installed old xdotool absolute path was independently confirmed to use
XWarpPointer; the previous failed native trace does not establish a Wayland
defect or permit source whitelists. Correct mechanism and source tests are not
actual native XTEST proof. GTK and game tests remain separate live boundaries.

Parent verification results will be supplied at launch after the source is
frozen. Do not launch this draft against a mutable/incomplete implementation.

Do not edit files, run tests/application code, operate desktop, create evidence,
commit/reset or mutate services/data. Assess correctness, lifecycle/error exits,
meaningful external-boundary tests, typing, security and scope. Report material
reachable findings with path:line and reproducing conditions, grouped Must-Fix,
Should-Fix and Nits. Do not manufacture marginal refactors. Finish with exactly
one STATUS: READY, NEEDS WORK or MAJOR ISSUES line.
