# Native final-commit R8 source review (Sol)

Configured reviewer: `gpt-5.6-sol`. The collaboration tool does not expose a resolved runtime model ID. I reviewed the complete seven-file diff from `7ac5c853928bd7fb8dc29492a2059007457a807c`, including the R6/R7 construction, recovery, durable checkpoint, classifier, IPC/CLI, and test paths, plus the R8 finalization, capture-admission, lock-order, resume-fact, predecessor, and runtime-fixture changes. The frozen hashes match `native-final-commit-r8-freeze.json`; I ran no tests or builds.

## Must

1. **Close the native-capability check/process-dispatch gap.** `src/crowley/session/daemon.py:4533-4549` holds the controller lock, checks the construction capability with `_native_construction_capability_matches`, then calls `guardian.observer_dispatch_admission(start)`. The capability check itself is deliberately lock-free at `daemon.py:1069-1092`; it also treats `reservationId is None` as a wildcard and does not compare `kind`. Construction owner mutation is not uniformly serialized by the controller lock: `_native_construction_revoke_owner` clears the epoch/owner under only the construction lock at `daemon.py:965-996` before later attempting its controller checkpoint write, and expiry clears it at `daemon.py:1477-1501`.

   A reachable interleaving remains: a final/PAUSED capture passes the line-4545 check; a concurrent replayed bootstrap, failed recheck/finalize validation, or expiry clears the owner; then the old thread enters Guardian admission and spawns/releases the producer after revocation. Exact cancellation is controller-serialized, so the new cancellation tests pass, but the other public revocation paths are not. The driver's capture epoch does not close the replay/expiry case because those paths do not revoke Guardian. For an inflight empty-ID capability, the wildcard also permits a later same-generation provisional owner to satisfy the old capability if the lock-free reads straddle owner replacement.

   Hold `_native_construction_lock` inside the existing controller-locked `admit_observer` from the exact capability comparison through `guardian.observer_dispatch_admission(start)`. This preserves the required controller → construction → Guardian order: Guardian releases its own lock before callbacks, and its independent revoke changes the driver capture epoch, so a concurrent Guardian revoke still fails the gated spawn. Compare epoch, generation, kind, and reservation ID exactly, including `None == None`; do not use `None` as a wildcard. Add a barrier regression in which a valid producer admission pauses immediately after its capability check while a same-ID replay/recheck revocation attempts to clear the owner. Prove either the process admission linearizes first or revocation linearizes first with zero later dispatch; never allow owner-clear to finish before the old producer starts. Retain the existing exact-cancel-before-dispatch proof as the cancellation side of the contract.

## Should

None.

## Nits

None.

The R7 finalization defect is otherwise corrected: `daemon.py:1818-1965` revalidates all applicable bounds and commits rebind, observation, `native_calibrated`, terminal publication, owner clear, and context close under controller → construction locks. The loop at `daemon.py:7321-7394` rechecks ownership before/after capture and sleep. PAUSED no-producer capture now refuses before stock capture at `daemon.py:4488-4511`; legacy NATIVE_CALIBRATION stock behavior remains. Worker completion computes `status_dict` before the calibration-state lock (`daemon.py:1299-1322`), and deferred resume now requires finite, newer real sequence/capture facts (`daemon.py:3148-3177`). The unfenced `native_calibrated` retry is removed, the named runtime double now accepts the production admission keywords, and the controller recovery commit retains its one-write rollback.

Parent evidence records 334 native-suite passes, the named runtime pass, targeted 10-test pass, static checks, exact hashes/imports, and private runtime permissions. The separately named three-way worker/prepare/pause barrier, deadline expiry while waiting on the final transaction lock, and malformed resume-facts regression are still pending acceptance proof; I do not count them as verified or as additional source findings here.

STATUS: NEEDS WORK
