# Sol plan review: runtime live instrumentation compatibility

Reviewed the production instrumentation plan against the accepted offline
schema-2 evaluator. This is a plan review only; I did not run tests, execute a
receipt, operate the desktop, or inspect live state.

## Inputs checked

- `.archive/PLAN-runtime-live-instrumentation.md` — SHA-256
  `8de705fc7905270bb3c3f9400741bc0c6f63372273268fc49f2e8adf6675e118`
- `.archive/PLAN-runtime-instrumentation-offline-evaluator.md` — SHA-256
  `5de77b319af1ebf377943b83ceb6a81d25d6e45d7bf7cb00d97650cb12a73549`
- `docs/RUNTIME_PERFORMANCE.md` — SHA-256
  `54237c344ef0faa3392cca6fe82b75f1f986bbf697c81d3f34493b2f00e1caca`
- `tools/session_performance.py` — SHA-256
  `c46cae849058005e9b7387ef95c34f40f376afb5477739efaf6f40f6a36ebd8c`
- `tests/test_session_performance.py` — SHA-256
  `c998aa4a9ff67ba67ddeab05a0e5a0cfa5273a296909e0b07cb79a3d06dd313a`

## Must-Fix

1. **Update the dependency and ownership fence to the accepted R6 successor and
   accepted evaluator.**

   - File: `.archive/PLAN-runtime-live-instrumentation.md:1`, `:5-10`,
     `:17-30`, `:38-56`, `:141-158`, `:167`, `:173`, `:198`
   - The plan still makes final R5 acceptance its prerequisite, calls the
     accepted schema-2 evaluator future work, pins obsolete Phase 1 tool/doc
     hashes, and gives Luna ownership of the now-accepted evaluator, its tests,
     and its schema documentation. Implementing this literally could bind the
     receipt to the wrong native source or change the evaluator alongside the
     producer that it is meant to check.
   - Correction: name the accepted R6 successor as the native prerequisite and
     record its reviewed source/producer identities in the private binding.
     Pin the three accepted evaluator hashes listed above. Treat
     `tools/session_performance.py`, `tests/test_session_performance.py`, and
     `docs/RUNTIME_PERFORMANCE.md` as read-only compatibility authorities for
     this slice; remove them from Luna's production ownership and validation
     commands unless a separate, reviewed evaluator change becomes necessary.
     Limit production edits to `driver.py`, `daemon.py`, `offline_harness.py`,
     and the focused native tests.

2. **Make both source-binding producers emit the evaluator's exact seven-key
   map.**

   - File: `.archive/PLAN-runtime-live-instrumentation.md:53-58`, `:71-76`,
     `:107-110`
   - The accepted evaluator requires the exact logical keys `daemon.py`,
     `driver.py`, `cli.py`, `decoder.py`, `protocol.py`, `offline_harness.py`,
     and `session_performance.py` in both top-level observer maps and every
     owner's `source_binding` (`docs/RUNTIME_PERFORMANCE.md:78-108`,
     `:113-127`, `:167-173`). The plan tells the observer to hash only three
     files and lets the daemon read only an unspecified owner subset. Those
     receipts are deterministically refused before measurement eligibility.
   - Correction: assign exact responsibility for all seven fixed logical paths.
     The observer must descriptor-hash all seven before and after the run; the
     owner must return the exact same seven-key map for each attempt after its
     own stable descriptor checks. Derive paths from a trusted fixed project
     root, never request data, and preserve the existing caps, no-symlink,
     identity, and drift checks. All three maps must equal the separately
     supplied accepted binding.

3. **Adopt the accepted receipt shape as an exact producer contract rather than
   an illustrative extension of existing receipts.**

   - File: `.archive/PLAN-runtime-live-instrumentation.md:62-110`
   - The evaluator rejects missing and extra keys. The plan does not currently
     require the exact root, attempt, owner, counter, cleanup, identity, and
     failure objects, and it does not name the mandatory
     `application_compute_cpu_method`. In particular, `cleanup` cannot merely
     be "preserved": it must contain exactly the four booleans and three
     nonnegative counts in `docs/RUNTIME_PERFORMANCE.md:167-208`. Counter
     snapshots must each contain exactly `started`, `succeeded`, and `failed`,
     with nullable values and the accepted arithmetic/monotonic rules. A
     well-formed failure must use the accepted phase and reason-code sets.
   - Correction: make the exact schema in the accepted documentation and tool
     normative by its hashes above. Require every exact key to be present, with
     unreached nullable values represented by JSON `null`; do not add private
     diagnostic keys. Emit `application_compute_cpu_method` as
     `time.process_time_ns` exactly when full application CPU is present and
     `null` otherwise. Populate the exact cleanup object only from the final
     post-reap/post-retirement owner snapshot, including zero active process,
     process-group, and observer-group counts for an eligible pair. Map every
     failure to the accepted two-field object and fixed enums.

4. **Define strict-decode completion and sample completion as separate observed
   boundaries.**

   - File: `.archive/PLAN-runtime-live-instrumentation.md:92-105`
   - "Finalize that record in `finally`" plus a generic "sample completion"
     timestamp leaves room to stamp completion merely because cleanup ran. The
     accepted evaluator intentionally preserves a successful decode/CPU pair
     when a failed or incomplete attempt ends after decode but before sample
     completion; in that case `sample_completed_monotonic` may be `null`.
     Conversely, a declared `completed` attempt must have the later marker
     (`docs/RUNTIME_PERFORMANCE.md:149-165`). Aliasing the two clocks would lose
     the intended after-decode failure evidence or falsely claim completion.
   - Correction: stamp `strict_decode_finished_monotonic` immediately when the
     public decoder returns and measure its CPU around that call. Stamp
     `sample_completed_monotonic` only at the actual later successful sample
     completion boundary; leave it `null` if failure/cancellation interrupts
     that boundary, even when the decode pair exists. `finally` should only
     preserve/finalize the record, not invent a reached timestamp. State also
     that the scheduled targets are exactly `t0 + i * 1.0` for eight indices,
     each deadline remains exactly `target + 1.0`, and neither a late start nor
     completion rebases later targets.

## Should-Fix

1. **Use the evaluator's evidence gates in the collection instruction instead
   of collecting until 15 passed runs.**

   - File: `.archive/PLAN-runtime-live-instrumentation.md:188-195`
   - Requiring "at least 15 distinct passed runs" is stronger than the accepted
     baseline and can drive extra owner use while beta collection remains the
     priority. The accepted contract counts 120 valid decoded pairs across 15
     independent fixed-target runs, permits truthful failed runs to contribute,
     then applies either the 15-full-pair-run primary gate or the distinct
     three-run counterfactual gate (`docs/RUNTIME_PERFORMANCE.md:234-254`).
   - Correction: predeclare a bounded collection count (within the evaluator's
     64-receipt cap), retain every outcome, and evaluate the whole collection.
     Describe the 15-run/120-pair baseline and the two gates exactly; do not
     extend collection selectively until 15 successes or discard failed runs.

## Nits

None.

The plan correctly keeps the eight original targets, one-second per-target
deadlines, all begun attempts and failures, zero-retry behavior, model-call
counters, and external-process CPU as unknown. The findings above are bounded
contract and sequencing corrections; they do not require changing the accepted
offline evaluator or the migration thresholds.

STATUS: NEEDS WORK
