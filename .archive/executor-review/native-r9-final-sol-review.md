# Final native R9 Sol review

Read-only review by `/root/sol_final_composition_plan`, exact frozen R9 plus
private-fixture hashes, relative to the preserved R8-proof baseline. No tests or
builds run by reviewer. Parent curated the returned findings below.

## Must-Fix

Independent Guardian revoke can dispatch the configured producer after Guardian
generation changes (daemon.py:4581–4598). Native admission holds controller and
construction locks, but the capability does not bind Guardian generation.
Guardian.revoke increments generation under its own lock(guardian.py:1896–1903).
With no registered observer/action, active is false and release_input is skipped;
the backend capture epoch remains unchanged. Revoke's callback blocks on the
controller lock held by admission. observer_dispatch_admission does not check
generation, so it calls start and releases the producer before owner clear.

Bind each private capability to immutable Guardian generation captured at owner
creation, including provisional/inflight owners. Compare it inside the real
Guardian-locked start callback before spawning. Test both orders with an actual
configured capture: revoke first means zero producer starts; admission first may
start and must remain owned through revoke/reap.

## Should-Fix

1. Finalization-wins proof does not establish controller-lock contention
   (native_regressions.py:6988–7005). cancel_attempted precedes IPC dispatch, but
   public cancel first calls flush_expiry and blocks on construction lock before
   reaching controller lock. Gate cancel after its real expiry flush, let final
   transaction own both locks, then observe actual controller-mutex contention.
   Also call later public recheck for both orders and verify immutable finalized
   or cancelled terminal; initial cancel response is insufficient.
2. Missing and None resume-sequence inputs remain unproved
   (daemon.py:3147–3179; native_regressions.py:5559–5586). Source type ordering is
   correct, but negatives cover only missing capture time and NaN sequence. Add
   missing/None sequence cases, exact malformed-facts error, no resume_ready.

## Reviewed changes that hold

Exact epoch/controller generation/kind/reservation-ID matching closes R8 owner
borrowing. Final snapshot validation remains outside locks with identity/Guardian
checks repeated before mutation. Deadline proof reaches the real transaction.
Durable rollback and composed owner/fresh-owner recovery are verified. Async
workers retain their operation object. STOPPED capture is closed. The private
bus fixture preserves real GTK/GJS/producer/decoder and Popen class semantics.

Substantial existing validation does not cover the independent Guardian ordering.
This is source review, not live qualification.

STATUS: NEEDS WORK
