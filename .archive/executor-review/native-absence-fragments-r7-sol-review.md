Configured reviewer: `gpt-5.6-sol` (collaboration request). The tool does not expose a resolved runtime model ID; the original self-description is not verification.

I reviewed the complete six-file candidate diff from `eb2c69ee2bd8aad8055abb90af294aac96d995b1`, including the R6 admission, lock, terminal, and durable-recovery paths and the R7 absence classifier. The candidate and base hashes match `native-absence-fragments-r7-freeze.json` for all six files.

## Must

1. **Make deferred finalization and same-generation cancellation one controller-first ownership transaction.** In `src/crowley/session/daemon.py:7134-7174`, the finalize-frame loop checks controller generation/state but never revalidates the immutable run ID, epoch, reservation, or deadline before/after each capture and sleep. More critically, `daemon.py:7177-7184` snapshots the reservation and releases the construction lock; frame rebind, observation, `native_calibrated`, and terminal publication then occur separately through `daemon.py:7186-7258`. `native_construction_recovery_cancel` can acquire controller then construction at `daemon.py:2549-2584`, record `cancelled`, and clear that exact same-generation owner while leaving the controller in `NATIVE_CALIBRATION`. The stale runner can consequently persist the final frame, advance to `INPUT_CALIBRATION`, and publish `finalized` (with a `None` reservation) after cancellation already returned success.

   Revalidate the exact `runId`/epoch/reservation and both deadlines before and after every finalize capture/sleep. For the final mutation, acquire `controller.lock` then `_native_construction_lock`, validate the same owner and `NATIVE_CALIBRATION` generation, and keep both locks through rebind/observe, admitted `native_calibrated`, terminal capture, owner clear, and context close. If cancel wins, no controller mutation or later capture may occur; if finalization wins, cancel must observe the completed/unknown owner and cannot publish a competing terminal.

   Add two barriers to the real composed PNG runner through public `SessionIPC`: (a) cancel while the finalize loop is between attempts and assert no subsequent capture, no `INPUT_CALIBRATION`, checkpoint `recovery_required`, and the immutable `cancelled` receipt; (b) stop inside `rebind_native_construction_frame` before its underlying call, launch exact-ID cancel concurrently, and prove the controller-first commit lock serializes the two operations so exactly one terminal outcome wins. Existing tests at `tests/test_session_native_regressions.py:4445-4512`, `5315-5420`, and `5446-5624` cover recovery-complete cancellation, earlier pause races, and happy finalization, but not this final commit interleaving.

2. **Do not let the stock PAUSED capture bypass the exact admission gate.** `_capture_native_region_for_identity` returns through `_capture_client_crop_for_identity` at `src/crowley/session/daemon.py:4317-4318` before any controller generation/state or native-capability check at `daemon.py:4321-4363`. Because the telemetry-region producer is optional, a public PAUSED preflight/recovery on an otherwise valid X11 profile can use this branch. A cancellation between the caller's earlier validation and this return can therefore spawn the stock screenshot after its owner was revoked. The stock call at `src/crowley/session/driver.py:6577-6598` has no construction capability or Guardian exec-gate callback, and `Guardian.cancel_calibration_operation` only revokes calibration tickets; it does not revoke the X11 capture epoch.

   Within the six-file fence, fail closed for PAUSED native construction when the configured telemetry-region producer is unavailable; preserve the legacy `NATIVE_CALIBRATION` stock-capture path. Move controller admission ahead of the fallback decision and allow PAUSED only through the existing configured-producer gate, where the exact caller capability is checked again at dispatch. Add a public `SessionIPC` PAUSED preflight/recovery test with the producer unset that asserts a typed refusal and zero stock-backend calls, plus a cancel-before-admission barrier showing no process dispatch. The configured-producer success test at `tests/test_session_native_regressions.py:5222-5312` does not exercise this early-return branch.

## Should

None.

## Nits

None.

The R7 classifier at `src/crowley/session/daemon.py:133-233` correctly treats each aligned eight-cell mixed flat group as an encoded fragment independently of header survival, retains closed malformed/loading behavior, and has generated whole-header-plus-payload coverage. The controller recovery commit at `src/crowley/session/controller.py:1376-1470` rolls back its in-memory frame/checkpoint/history on journal failure and performs only read-only post-proof. The fixed eight IPC shapes, CLI round trips, bounded terminal receipts, recovery polling, and successful twelve-state history are otherwise represented in the candidate tests.

Parent verification on these exact frozen bytes completed with 330 passing tests using the worktree imports, authentic private Codex 0.162.1, and private mode-0700 XDG runtime (log SHA-256 `bd9b8f95ee6eb11a22c80262119fd4e0d8bf3a19033d05504ede8048f68b2c3b`). I ran no tests or builds under this read-only review. That pass does not exercise the two interleavings above.

STATUS: NEEDS WORK
