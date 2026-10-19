# Final native R10b Sol review

Read-only review by /root/sol_final_composition_plan on exact frozen R10b bytes.
No tests/builds or edits by reviewer. Parent preserved returned findings.

## Must-Fix

None in the R10 production delta. Original Guardian generation is captured for
prepare/recovery inflight owners, retained through installed owners/tickets,
compared against live state and checked inside the actual Guardian-locked
pre-spawn callback. Lock order controller → construction → Guardian remains.
Corrected R10b cases use public PAUSED/NATIVE owners and both real revoke orders.

## Should-Fix

1. Finalization-wins proof remains incomplete (regressions.py:7408).
   not cancel_done.wait(0.2) can pass while cancel blocks in real
   _native_construction_flush_expiry on construction before controller lock.
   Gate cancel after real flush, let finalization acquire both locks, prove
   nonblocking acquire of actual controller lock fails, then block normally.
   Also add later public native_construction_recheck for cancelled terminal;
   finalized branch already rechecks at7454.
2. Recovery-restart over live reservation (regressions.py:4390) asserts exact
   error/retained owner but not refusal-before-capture. Count real provider
   calls; one for public preflight, unchanged by refused recovery restart.
   Preserve owner/inflight assertions.

## Nits

None. Green runs support these bytes, but two explicitly arbitrated proof
obligations remain absent.

STATUS: NEEDS WORK

Root arbitration: accept both as bounded test-only R10c corrections. Production
and six companion files remain frozen. No broad-suite repetition. Actual Opus
review still running; final arbitration follows its verdict.
