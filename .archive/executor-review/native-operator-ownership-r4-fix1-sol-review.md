The two untracked helper files match the supplied hashes and the worktree is based on `68e42361d4d5dc3e0a08562e3904570690782ec0`. I did not treat the six copied native R5 dependencies or later native integration as ownership findings.

## Must-Fix

1. **The cancellation actor expires at the short prepared deadline and is not rebound after bootstrap extends ownership into the long calibration operation.**
   `_prepare()` arms the actor from the initial binding at [`native_calibration_operator.py:2305`](</home/dev/.cache/crowley/worktrees/native-calibration-operator-ownership-r4-fix1-20261018/tools/native_calibration_operator.py:2305>). Bootstrap later adopts the consumed reservation and its new expiry at lines 2525–2527, but `_adopt_reply()` never updates the actor. The actor independently exits when its original deadline arrives at lines 1373–1376. A helper killed during the subsequent measurement can therefore have no cancellation actor at all. Initial admission and recovery handoff also remain unprotected between the successful server reply and actor start/update: `_adopt_handoff()` installs the new binding before updating the actor at lines 1983–1996. A death there leaves the old actor cancelling a stale ID while the new recovery reservation remains active. Move admission/handoff across an independently owned closed protocol, or otherwise retain both exact capabilities until the actor acknowledges the canonical generation, reservation ID, and expiry. Update it after every binding or expiry transition before dependent input.

2. **Cooperative failure cleanup disarms independent cancellation before cancellation is acknowledged.**
   [`native_calibration_operator.py:2417`](</home/dev/.cache/crowley/worktrees/native-calibration-operator-ownership-r4-fix1-20261018/tools/native_calibration_operator.py:2417>) stops the actor before issuing synchronous `recovery_cancel`. If transport or validation fails, lines 2435–2436 only record an event; the helper exits with no actor left to cancel on owner death. The recovery-after-error branch has a second leak: if `_recover()` admits a new recovery ticket and then fails, lines 2569–2577 swallow that recovery exception without cancelling the new binding, and the finalizer disarms its actor at lines 2580–2585. Keep the actor armed until an exact canonical cancelled/recovered/finalized terminal is acknowledged. On synchronous cancellation failure, let the independent actor observe owner exit. A failed recovery must cancel its newly adopted ticket or retain its actor.

3. **Repeated handled signals can interrupt the mandatory cancellation/recovery phase.**
   The signal handler raises whenever `_cleanup_started` is false at [`native_calibration_operator.py:1785`](</home/dev/.cache/crowley/worktrees/native-calibration-operator-ownership-r4-fix1-20261018/tools/native_calibration_operator.py:1785>). That flag is not set until line 2581, after failure recovery and `_cancel_active_reservation()` run at lines 2556–2579. A second TERM/HUP/INT can therefore interrupt cancellation after the actor has been stopped but before IPC cancellation, directly producing the stranded state above. Enter protected cleanup mode before terminal recovery/cancellation begins; subsequent handled signals should record interruption while preserving the first failure and allowing release, reap, cancellation, and receipt cleanup to finish.

4. **Constructor and readiness failures do not roll back all owned descriptors and sealed capabilities.**
   Several production allocations violate the explicit setup rollback requirement:

   - `X11Screen` loads a pinned tool before backend/Xauthority validation at [`native_calibration_operator.py:770`](</home/dev/.cache/crowley/worktrees/native-calibration-operator-ownership-r4-fix1-20261018/tools/native_calibration_operator.py:770>); an exception before construction returns leaves `main()` with no object to close.
   - `OwnedEmitter` allocates two pipes at lines 933–934, while readiness failure at lines 959–964 has no internal rollback. `abort()` does not close the child-side descriptors if spawning failed before ownership transfer.
   - `Watchdog` allocates three pipes and a duplicated `NativeReleaseSpec` at lines 1178–1182. Its failure handler at lines 1226–1235 omits `_write`, `_ack_read`, and `_release_spec.fd`.
   - `CancellationActor` allocates three pipes at lines 1473–1475. Its start-failure cleanup at lines 1511–1525 omits `_control_write`, and partial constructor allocation has no rollback.

   Use staged construction with one idempotent close path that closes every successfully allocated descriptor/spec and terminates and joins any spawned child before re-raising.

5. **The required ownership tests do not exercise the remaining dangerous boundaries.**
   The green suite does contain real spawned process evidence, but its labels overstate the production coverage:

   - [`test_native_calibration_operator.py:1305`](</home/dev/.cache/crowley/worktrees/native-calibration-operator-ownership-r4-fix1-20261018/tests/test_native_calibration_operator.py:1305>) kills a process running `_owner_hold_fixture`, which directly constructs `Watchdog` and `OwnedEmitter`; it is actual owner death, but not `NativeCalibrationOperator` or `main()`.
   - The all-signal test at line 1165 kills the emitter process group, not the helper owner.
   - The production `main()` composition at line 1352 proves only button hold plus helper SIGKILL. Its preparation client is replaced in-process; only cancellation uses the local socket.
   - The handled-signal test at line 1587 uses fake input, sends signals to the pytest process, and manually sets `_cleanup_started`; it does not exercise TERM/HUP/INT during a real held key/button or cancellation cleanup.
   - The persistent-release test at line 1078 directly constructs a watchdog and then SIGKILLs its owner. It never exercises normal nonzero interpreter exit through `Watchdog.close()` while the retained release actor remains alive.
   - The handoff tests at lines 1526 and 1548 verify an ordinary acknowledged update but never kill the owner before, during, or after prepare/bootstrap/new-expiry/recovery adoption.
   - The sole readiness rollback test at line 1612 checks that the watchdog process stopped; it does not check descriptor/spec closure, and there are no equivalent emitter, cancellation-actor, or `X11Screen` failure cases.

   Add real production-lifetime barriers for key and button holds, SIGKILL and handled signals, repeated signals during mandatory cleanup, normal failed-release exit, initial admission/bootstrap expiry/handoff death, and descriptor/spec rollback.

## Should-Fix

1. **A cleanup failure can leave a receipt claiming success.**
   `run()` sets `outcome = "success"` at [`native_calibration_operator.py:2553`](</home/dev/.cache/crowley/worktrees/native-calibration-operator-ownership-r4-fix1-20261018/tools/native_calibration_operator.py:2553>). If cancellation-actor or input cleanup then fails at lines 2583–2594, the process eventually raises, but `receipt.finish()` still writes `outcome="success"`; actor cleanup failure may also leave `failureCode` unset. Change the receipt to failure before publication whenever mandatory release, reap, cancellation, or close is unconfirmed.

2. **Owner start identity is optional rather than required.**
   `Watchdog` accepts `None` at lines 1175–1177, and `CancellationActor` does not validate `owner_pid` or `owner_start` at lines 1471–1472. With no sealed start identity, PID reuse can keep an orphan actor attached to an unrelated process until its deadline. Production construction should require a positive PID and nonempty start identity before spawning either actor.

## Nits

None.

## Evidence and limits

The source strongly improves the prior candidate: all fixed key/type/move/button actions use sealed spawned emitters; watchdog state is ACKed before dispatch; empty ownership is ACKed after confirmed release; the existing `_watchdog_entry` and `NativeReleaseSpec` perform exact release; abrupt cancellation EOF handles an unreaped zombie owner; and the production-main button/SIGKILL test demonstrates independent exact `mouseup 1` plus the bound cancellation request.

The parent reports the exact frozen helper suite passed `38` tests in `19.98s` with two multiprocessing fork warnings, private mode-0700 XDG, and unchanged hashes. The worker reports `38 passed` in `22.23s`. I did not rerun tests. These remain harmless compiled-fixture and local-socket results. They do not constitute live X11/game input, native R5 acceptance, full workflow composition, deployment, or promotion.

STATUS: MAJOR ISSUES
