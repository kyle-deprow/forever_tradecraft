# Sol source review: offline runtime schema-2 evaluator R2

I reviewed the final three-file candidate in
`/home/dev/.cache/crowley/worktrees/runtime-evaluator-20261017` against the four
R1 findings and the corrected canonical evaluator and performance contracts. I
did not run tests or the CLI, use Git, or operate any runtime, desktop, network,
database, Docker, or game path.

## Identity and scope verification

The frozen candidate hashes match the handoff exactly:

- `tools/session_performance.py`:
  `478e8b2b4a3039b6d60ff5d56358bdef81d7a2a47b54d485c109e8418f6d0000`
- `tests/test_session_performance.py`:
  `1ccc3095a236d13d6cdeb05fc3e7089b924feb72956021ef2bfb4fa183af0f65`
- `docs/RUNTIME_PERFORMANCE.md`:
  `17f407f44d7a50c44cfe467e2f990b886455628ca750260107604c1d0f8b1bc3`

The accepted main-tree Phase 1 files remain unchanged at
`23c0294b9037ef8edb39fd49d6af61a43216f4997298f590a6d92a838eb774fe`,
`a9133ed64f06591303f7c5849959cb4a281f16d1cc01afdbfa617fba756bab75`,
and `becbcbe0c6b9bf1154e1254661f5cc39f99dba87ae73f1c0c3d2ed38c3b62c5c`
respectively. Scope remains confined to the three authorized files. The
canonical offline-evaluator, deterministic-performance, and live-instrumentation
plans remain at SHA-256
`5de77b319af1ebf377943b83ceb6a81d25d6e45d7bf7cb00d97650cb12a73549`,
`08479c262c6b36e152f6b6ceee8f714aa360633f83c9020ae5b4a5354447de80`,
and `8de705fc7905270bb3c3f9400741bc0c6f63372273268fc49f2e8adf6675e118`.

The worker reports 65 tests passing plus Ruff, formatting, compilation, and
diff checks. Parent reproduction was still in progress at review handoff; I did
not independently execute those checks. No real accepted schema-2 receipt or
binding exists, so this review supports no live bottleneck or Rust verdict.

## R1 closure

All four R1 findings are substantively addressed:

- `tools/session_performance.py:1417-1420` now refuses malformed top-level
  producer/config objects before any value can enter the public run report;
  exact-shape digest mismatches remain safely inspectable. The regression at
  `tests/test_session_performance.py:674` checks the encoded report for private
  strings and extra keys.
- `tools/session_performance.py:1163-1188` now requires every client/owner
  boundary through strict decode, the exact owner generation, identity
  continuity, nonce, and other paired provenance for late decoded attempts.
  The mixed full-collection regression at
  `tests/test_session_performance.py:1253` proves a refused malformed receipt
  forces `insufficient_evidence` rather than contributing a pair.
- A structurally valid post-decode cleanup failure now reaches the normal pair
  exclusion and run-ineligibility logic at
  `tools/session_performance.py:1264-1291` and
  `tools/session_performance.py:1542-1547`; its timestamps, CPU diagnostic, and
  cleanup fields remain visible. `tests/test_session_performance.py:1326`
  exercises that behavior.
- Counter triplets now enforce outcome totals at
  `tools/session_performance.py:951-959`. The receipt validator detects
  decreasing cumulative counters and retains inter-sample increases at
  `tools/session_performance.py:1428-1461`, then makes the run ineligible at
  lines 1528-1531. The three independent counter regressions begin at
  `tests/test_session_performance.py:723`.

The fixes preserve the corrected collection-level rules: late decode timing is
separate from pair provenance, inter-sample model activity excludes the whole
run from pooled statistics, and malformed evidence cannot be ignored when an
otherwise complete collection meets a threshold.

## Must-Fix

1. **The causal-boundary fix incorrectly makes a post-decode timestamp
   mandatory for every successfully decoded pair.**
   `tools/session_performance.py:1169-1171` checks every name in
   `_LIVE_CLIENT_CLOCKS`, which includes `sample_completed_monotonic`, and
   refuses the whole receipt when that value is null. But the canonical
   end-to-end interval ends at strict-decode completion, and the corrected plan
   explicitly says a successfully returned strict decode supplies the CPU/wall
   pair while failed attempts retain null for unreached later boundaries
   (`.archive/PLAN-runtime-live-instrumentation.md:99-105,116-137` and
   `.archive/PLAN-runtime-instrumentation-offline-evaluator.md:35-39,78-89`).
   A strict decode can therefore finish with valid CPU, identity, owner,
   binding, cleanup, and all causal interval evidence, followed by failure or
   interruption before the separate sample-completion marker. R2 turns that
   real pair and its reached failure evidence into an opaque
   `missing_required_stage` refusal. The parameterized regression at
   `tests/test_session_performance.py:1230-1273` encodes the same overconstraint
   by treating `sample_completed_monotonic` like a pre-decode boundary.

   Require all client timestamps only through
   `strict_decode_finished_monotonic` plus every causal owner boundary and the
   owner generation. Keep `sample_completed_monotonic` mandatory for a declared
   completed attempt, but allow it to remain null on a failed or incomplete
   post-decode attempt. Preserve the decoded pair, use strict-decode finish for
   its end-to-end/deadline measurement, and retain the null completion marker
   and later failure separately. Remove `sample_completed_monotonic` from the
   missing-causal-boundary refusal parameterization and add a focused failed or
   incomplete post-decode case proving the pair survives with that field null.

## Should-Fix

None.

## Nits

None.

STATUS: NEEDS WORK
