State your exact model ID first. Requires actual Claude Opus with no fallback.
Read-only review; no edits, git changes, tests, GUI, service/config changes or
external requests. User revoked AGENTS.md. Work only in /home/dev/repos/pegasus.

Review the completed R2 delta of the GNOME screenshot repair, not the entire
large existing working tree. Read .archive/PLAN-gnome-capture-completion.md,
gnome-capture-freeze-r2.json and exact r2 diff under .archive/executor-review/.
Use the recorded baseline to isolate new changes. Owned source is only
src/crowley/session/driver.py and tests/test_session_capture.py.

R1 review is retained in gnome-capture-opus-r1.txt and gnome-capture-sol-r1.md.
The parent accepted and requested these closures:
1. Capture admission binds a monotonic revocation epoch which rearm cannot clear;
   check it through lock/image waits/final identity/publication. A short shared
   gate must order publication with revocation without blocking input release
   during a wait. Actual delayed-writer and lock-contention tests must cover it.
2. A unique0700 per-attempt staging directory on the destination filesystem is
   retired on every exit, so late GNOME creation cannot leave an orphan image.
3. Preserve existing desktop>=client cropping compatibility. Complete wrong-size
   or wrong-format output refuses immediately, distinct from unfinished output.
4. Real-child completion-refusal tests have enough startup time to reach their
   intended guard; production deadlines remain unchanged.

Core R1 behavior was sound: private cross-process nonblocking flock, exact
GNOME argv, original capture timestamps, strict new PNG/full decoding and atomic
publication under the existing absolute deadline. Native/model/helper releases
and unrelated executors are closed. Review only R2 correctness and regressions
introduced into that behavior. Read the changed helpers, capture method,
release_held_input/activate_generation and focused tests; avoid unrelated large
files unless a concrete dependency requires them. Don't manufacture marginal
findings. Give file:line and a reachable failure for each finding, grouped as
Must-Fix/Should-Fix/Nits, then end with exactly one line:
STATUS: READY | NEEDS WORK | MAJOR ISSUES
