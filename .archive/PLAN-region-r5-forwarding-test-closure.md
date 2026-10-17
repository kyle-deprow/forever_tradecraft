# R5 compiled forwarded ordinary-command regression

SolsourceR5 found one concrete test gap: same-runtime competing invocations
are refused by the new flock before reaching GApplication's active-primary
flag. Preserve that passing regression and add a second compiled forwarding case.
Root releases ONLY tests/test_session_native.py in isolated worktree
/home/dev/.cache/crowley/worktrees/region-r5-forwarding-test-20261017.
It is based at2a8d73e with all12hash-verified frozenR5 source overlays.

Read original R5 plan, frozen source and SolsourceR5 report in primary first.
No edits in frozen R5 WT, main, or any other source/test/metadata/config/service.
No build/GUI/game/capture/network/Docker/DB/Git mutations or Rust. Use existing
compiled R5 binary. The sole external display/bus must remain private fixture.
Do not commit/reset/stash/revert others. One-file scoped test correction only.

In existing actual blocked-Shell composition test, keep same-runtime flock and
malformed-telemetry checks. Launch another ordinary --file invocation with a
separate owned0700 XDG_RUNTIME_DIR and explicitly SAME privateDBUS address/display.
This models an ordinary unpatched caller bypassing the private runtime lock.
Use actual subprocess/binary/IPC, not a direct handler call or invented response.
Require exact active-primary refusal, no second Shell call/output/shared-option
reparse, and successful original capture after gate release. The synchronous
Shell call may queue the forwarded command until release: stage a real child
with Popen, observe actual lifecycle, release gate and collect bounded result;
do not deadlock by waiting for remote return while deliberately blocking primary.
Keep absolute producer deadline unchanged; a test gate must be released in
finally and every started process reaped on assertion/failure. Original scenario
must still prove initial capture current markers, valid output and healthy owner.
If production guard cannot meet requirement, preserve evidence and report that
specific blocker; do not edit/rebuild product source or weaken expected error.

Run actual exact composition node and scoped Ruff/format/py_compile/diffcheck.
Report actual outputs, test hash and unresolved facts. Do not touch full runner
payload schedules. DONE only if complete. Parent independently reproduces, then
Sol checks closure. Actual Opus remains on frozenR5; later final test delta gets
its own bounded review without overwriting earlier candidate or artifacts.
