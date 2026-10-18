# Operator ownership closure R4: bounded rescope

R3 is frozen as an unqualified partial candidate. Do not repeat another whole
workflow rewrite/review. The actual compiled test called owner kill kills only
emitter.pgid; root helper and watchdog stay alive and root explicitly closes the
watchdog. This proves child-death release, not helper-owner-death. The source
also has no independent admitted-reservation cancellation actor, and retained
non-daemon multiprocessing watchdogs can block interpreter exit when release
cannot be confirmed. Those required R3 items remain open.

## Worktree and fence

Root creates native-calibration-operator-ownership-r4-20261018 from ca5f706,
copies the exact frozen two R3 helper files and exact six frozen native R5
files as DEVELOPMENT dependencies. R3 remains immutable. Own ONLY
tools/native_calibration_operator.py and tests/test_native_calibration_operator.py.
The six native files and every other source/dependency/addon/service/config/GUI
file are read-only. Root owns all git operations. Do not commit/reset/stash/revert
others. No live input, services, network credentials or production data changes.
The candidate native R5 is under independent checks and Sol/Opus review; its
presence is not acceptance or live qualification.

## Complete this narrower stage first

1. Independently spawned input-release watchdog observes actual HELPER owner
   PID + start identity, survives owner SIGKILL/EOF, kills/reaps owned emitters,
   and releases exactly published owned keys/buttons. Reuse sealed capabilities
   and existing _watchdog_entry. No second Guardian/lease, alternate release
   executable, unowned modifier clearing or GUI input.
2. Independent bounded cancellation observes actual helper death and cancels
   only its admitted generation/reservationId through existing fixed IPC.
   Canonical admission/handoff updates are acknowledged before dependent input;
   no stale generation/ID can cancel a later reservation. Keep input release
   independent of IPC/receipt failure. No arbitrary command/new public mode.
3. Bound setup/readiness/ACK/EOF/cleanup. A watchdog with unconfirmed release
   MUST survive; helper interpreter MUST exit nonzero within a bound rather
   than hang on multiprocessing's non-daemon atexit join. Never kill the release
   actor just to make exit pass. Close every owned fd/spec/child on constructor
   failures. Repeated SIGTERM/HUP/INT during cleanup do not interrupt mandatory
   cleanup. Receipt begin/event/finish failure never skips release/reap/revoke.
4. Test with a harmless compiled trusted fixture passed through production
   PinnedInputTool.from_root sealing/NativeReleaseSpec and real spawn plus real
   _watchdog_entry. Run the HELPER in a distinct process and signal THAT PID
   during confirmed key hold AND button hold. Assert actual independent release
   logs, child reaping, exact cancellation request, no later input and bounded
   owner termination. Include SIGKILL, TERM/HUP/INT, repeated signals, ACK loss,
   gate EOF, late child, setup/readiness failure, receipt failures, and delayed /
   failed release showing retained actor + bounded owner exit. No actual X input.
   Use production lifetime/orchestration paths, not parallel test-only owner code.
5. Keep existing workflow behavior; do not repair unrelated workflow details
   during this stage. Upgrade pure absence interface imports only as needed for
   exact frozen R5 deps. Do not count FakeClient/FakeInput / --help smoke as death
   qualification. Do not claim full native composition or live success.

Run focused ownership tests first, then full helper test file ONCE after final
source. No unrelated full native/performance suites; native R5 has its own
independent run. Scope Ruff/format/compile/diff to owned two files. Preserve
private full logs, command/import origins, exact two-file/dependency hashes and
write MAIN .archive/executor-review/native-operator-ownership-r4.md as the only
report artifact. State actual covered and uncovered cases literally. Send a
short actual-results milestone after ownership group; root independently tests
then Sol + actual Opus source review. DONE only if this bounded stage is complete.
