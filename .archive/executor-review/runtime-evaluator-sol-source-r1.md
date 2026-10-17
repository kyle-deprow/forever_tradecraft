# Sol source review: offline runtime schema-2 evaluator R1

I reviewed the isolated three-file candidate in
`/home/dev/.cache/crowley/worktrees/runtime-evaluator-20261017` against the
accepted Phase 1 implementation, the corrected offline-evaluator plan, the
canonical deterministic-performance decision contract, and the proposed live
instrumentation contract. I compared the working files directly with the
accepted main-tree files. I did not run tests or the CLI, use Git, or operate
any runtime, desktop, network, database, Docker, or game path.

## Identity and scope verification

The candidate hashes match the handoff exactly:

- `tools/session_performance.py`:
  `5dd6cca0c8885713a9f3faed4de7b783f6b58afcaf169f2752c6d4682f5292e3`
- `tests/test_session_performance.py`:
  `07be278c2f7c3cf3e91a84c92012e179663adce9cfa71c7e32703e91928bdffa`
- `docs/RUNTIME_PERFORMANCE.md`:
  `a4e1b2015e5c2f91946be3e08baf21295ee6cd8c2bfb07e9e415241ade1b09ba`

The accepted main-tree Phase 1 files remain at
`23c0294b9037ef8edb39fd49d6af61a43216f4997298f590a6d92a838eb774fe`,
`a9133ed64f06591303f7c5849959cb4a281f16d1cc01afdbfa617fba756bab75`,
and `becbcbe0c6b9bf1154e1254661f5cc39f99dba87ae73f1c0c3d2ed38c3b62c5c`
respectively. The candidate diff is confined to the three authorized files.

The reviewed plan hashes are:

- Offline evaluator plan:
  `5de77b319af1ebf377943b83ceb6a81d25d6e45d7bf7cb00d97650cb12a73549`
- Deterministic performance plan:
  `08479c262c6b36e152f6b6ceee8f714aa360633f83c9020ae5b4a5354447de80`
- Live instrumentation plan:
  `8de705fc7905270bb3c3f9400741bc0c6f63372273268fc49f2e8adf6675e118`

The Phase 1 replay path remains intact. The new mode is explicit and offline,
uses capped stable descriptor reads and strict JSON parsing, keeps failed and
refused inputs visible, separates wall time from process CPU, and applies the
canonical nearest-rank quantile. Its collection-level decision logic correctly
keeps late successful strict decodes as measured pairs while separating timing
qualification; requires the 120-pair/15-run baseline; adds the 15 full-pair-run
requirement only to the primary repeatability route; and leaves the alternate
three-distinct-run counterfactual route independent of that extra primary gate.
There is no qualifying real schema-2 input in this review.

The parent reports 41 tests passing in 3.96 seconds plus Ruff, formatting,
compile, diff, and scope-hash checks. I did not independently execute them.

## Must-Fix

1. **A malformed receipt can copy private producer or configuration data into
   the public report.** `tools/session_performance.py:1401-1407` treats an
   invalidly shaped top-level `producer_binding` or `config_binding` as a normal
   mismatch instead of a schema refusal. `tools/session_performance.py:1531-1532`
   then emits those untrusted values verbatim. A receipt can therefore put a
   producer path, config values, identity, or arbitrary nested data in either
   object and have it serialized into the nominally privacy-safe decision,
   contradicting `docs/RUNTIME_PERFORMANCE.md:104-108` and
   `docs/RUNTIME_PERFORMANCE.md:200-210`. Validate each object against its exact
   digest-only schema before retaining a mismatch: structurally invalid values
   must become a sanitized refused-record entry, while exact-shape values with a
   different digest may retain only those validated hash/branch fields. Add a
   live-mode regression beside `tests/test_session_performance.py:994` that puts
   recognizable private strings and extra keys in both bindings and proves none
   appear anywhere in encoded output.

2. **A failed or incomplete decoded attempt can enter the 120-pair and primary
   migration gates without the required same-attempt boundaries or owner
   generation.** `tools/session_performance.py:1180-1205` requires every causal
   timestamp only when `state == "completed"`; for a late decode marked
   `failed`, it removes `null` holes and merely orders the remaining values.
   `tools/session_performance.py:1252-1262` then admits a pair using only the
   end-to-end and strict-decode intervals, and never requires
   `owner["generation"]` to be present and equal to the run generation.
   `tools/session_performance.py:1429-1435` counts that pair. Thus fifteen
   eight-attempt failed runs can omit lock/ACK/capture/IPC/PNG boundaries (or
   the owner generation), remain eligible, and satisfy the primary threshold.
   This violates the documented matching-generation and reached-stage contract
   at `docs/RUNTIME_PERFORMANCE.md:145-150` and makes missing provenance look
   measured. Once strict decode completes, require every causally prior client
   and owner boundary needed by the declared intervals, require the exact owner
   generation, and refuse impossible `null` holes as `missing_required_stage`;
   preserve the allowed late timing outcome separately. Extend the late-decode
   regression at `tests/test_session_performance.py:1090` to remove each prior
   boundary and the owner generation in turn, and prove no such receipt can add
   a completed pair or leave the overall collection decidable.

## Should-Fix

1. **A real cleanup failure after successful decode is collapsed into an opaque
   schema refusal instead of retaining the failure evidence.** At
   `tools/session_performance.py:1163-1171`, any decoded attempt whose exact
   cleanup object reports `attempt_retired=false`, an unreaped process, an
   unhealthy watchdog, or a nonzero ledger count immediately raises
   `attempt_lifecycle_invalid`. The later logic at lines 1252-1277 and
   1500-1502 is already designed to retain that attempt, exclude its pair, and
   report `cleanup_invalid`, but is unreachable. Preserve a structurally valid
   cleanup failure as an ineligible attempt/run with its reached timestamps,
   CPU diagnostic, cleanup fields, and fixed failure reason; only malformed or
   missing cleanup structure should be a schema refusal. Add a regression near
   `tests/test_session_performance.py:1161` for successful strict decode followed
   by failed cleanup.

2. **Counter snapshots are checked only within one before/after pair, so
   impossible non-monotonic counters can qualify.**
   `tools/session_performance.py:1089-1103` verifies nonnegative values and the
   claimed per-attempt subtraction, but accepts a snapshot where
   `succeeded + failed > started` and accepts a later attempt whose cumulative
   counters are lower than the prior attempt's `after` values. All claimed
   deltas can still be zero, so the run remains eligible and asserts that no
   model call occurred. Validate the cumulative counter invariants and
   monotonicity across attempts; retain any real increase between sample
   snapshots as model-call evidence and make the run ineligible rather than
   presenting it as a zero-call pure path. Add independent regressions alongside
   `tests/test_session_performance.py:777` for an impossible triplet, a decreasing
   next snapshot, and an increase between attempts.

## Nits

None.

STATUS: NEEDS WORK
