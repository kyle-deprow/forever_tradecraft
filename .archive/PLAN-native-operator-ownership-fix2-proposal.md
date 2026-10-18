# Native operator ownership fix2 proposal

## Scope and invariant

Limit changes to `tools/native_calibration_operator.py` and `tests/test_native_calibration_operator.py`. Keep the three modes, public native IPC schemas and request keysets, Guardian/lease behavior, `_watchdog_entry`, and sealed release/input capabilities unchanged. The invariant is: before any dependent input, one independent process has acknowledged ownership of the canonical generation, reservation ID, and current expiry; it remains armed until it has observed an exact canonical terminal result.

## Closed ownership actor

Extend the existing cancellation actor into a closed ownership actor. Its private pipe protocol has a fixed enum and exact per-operation field validation; it cannot forward arbitrary methods or mappings. The actor performs the existing public requests that create, replace, extend, or terminate ownership: initial prepare, bootstrap, recovery begin, cancellation, recovery completion, and finalize. Public request bodies and replies remain byte-for-byte within their current schemas.

For prepare, the actor sends the request once, validates the reply, stores the canonical generation/ID/expiry, then returns the validated reply plus an ownership ACK to the helper. The helper may install its local view only from that ACK and may not issue dependent input earlier. Bootstrap follows the same path: the actor replaces the prepared expiry with the canonical post-bootstrap expiry before ACK, preventing it from aging out at the short deadline. For recovery begin, the actor retains the old binding while the request is in flight and atomically adopts the returned new generation/ID/expiry before ACK. It never retries an ambiguous admission.

A server commit followed by a lost reply is inherently indeterminate because the current public protocol does not let the client derive the server-assigned ID. The actor must report an indeterminate failure, permit no dependent input, and keep any previously known binding protected. It must not guess an ID or promise cancellation of the unknown ticket; that ticket expires under the server's existing bounded admission deadline. The same rule applies to a lost recovery-begin reply: cancel the known old binding if still valid, while the unknown new ID can only expire boundedly. Record this distinction in the receipt.

Route terminal operations through the actor as well. It disarms only after validating a canonical `cancelled`, `recovered`, or `finalized` result for its exact generation and ID and ACKing that terminal state. A transport or validation failure leaves it armed; owner EOF then drives its bounded exact cancellation attempt. A late cancel against an already-terminal ID is harmless and must never target another generation.

## Cleanup and construction

Set the protected cleanup flag before error recovery or cancellation starts. The first signal fixes the primary failure; later handled signals are recorded without raising through release, child reap, actor terminalization, or receipt cleanup. Any mandatory cleanup failure changes a provisional success receipt to failure before publication.

Build `X11Screen`, `OwnedEmitter`, `Watchdog`, and the ownership actor in stages. Register each descriptor, duplicated `NativeReleaseSpec`, and spawned child immediately in one idempotent rollback stack. On constructor/readiness failure, close both local pipe ends still owned, close duplicated specs, terminate and join started children, and then re-raise. Require a positive owner PID and sealed nonempty start identity before either independent actor starts.

## Focused proof

Add local-socket/process tests with barriers at actor receipt, canonical adoption, and ACK. Kill the real helper at each prepare, bootstrap-expiry, and recovery-handoff boundary; assert exact cancellation when the ID is known, no input before ACK, and bounded expiry with an explicit indeterminate receipt when a reply is lost. Cover cancellation transport failure and failed recovery while proving the actor remains armed through owner exit.

Add a production-lifetime normal nonzero interpreter-exit case in which release initially remains unconfirmed: `Watchdog.close()` returns boundedly, the retained release actor survives ordinary cleanup, and it later performs the exact release and exits. SIGKILL alone does not cover this path. Add real owner-process TERM/HUP/INT cases while a fixed key and button are held, plus a second signal at a cleanup barrier; assert exact release, child reap, cancellation, receipt cleanup, and preserved first failure. Finally inject every staged constructor/readiness failure and verify descriptors/specs close and no child survives.

This design closes all knowable-ID death windows within the helper while stating the existing protocol's lost-reply limit precisely. It should precede later native integration or live acceptance.
