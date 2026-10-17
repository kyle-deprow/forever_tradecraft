# Sol source review: offline runtime schema-2 evaluator R3

I reviewed the final three-file candidate in
`/home/dev/.cache/crowley/worktrees/runtime-evaluator-20261017` against the R2
finding and the unchanged canonical offline-evaluator, deterministic-performance,
and live-instrumentation contracts. I did not run tests or the CLI, use Git, or
operate any runtime, desktop, network, database, Docker, or game path.

## Identity and scope verification

The frozen candidate hashes match the handoff exactly:

- `tools/session_performance.py`:
  `c46cae849058005e9b7387ef95c34f40f376afb5477739efaf6f40f6a36ebd8c`
- `tests/test_session_performance.py`:
  `c998aa4a9ff67ba67ddeab05a0e5a0cfa5273a296909e0b07cb79a3d06dd313a`
- `docs/RUNTIME_PERFORMANCE.md`:
  `54237c344ef0faa3392cca6fe82b75f1f986bbf697c81d3f34493b2f00e1caca`

The accepted main-tree Phase 1 files remain unchanged at
`23c0294b9037ef8edb39fd49d6af61a43216f4997298f590a6d92a838eb774fe`,
`a9133ed64f06591303f7c5849959cb4a281f16d1cc01afdbfa617fba756bab75`,
and `becbcbe0c6b9bf1154e1254661f5cc39f99dba87ae73f1c0c3d2ed38c3b62c5c`
respectively. Scope remains confined to the three authorized files. The prior
Sol R2 report matches SHA-256
`c7dc5f30b9037ae35d4a2d47731634333bc31a15759215a4e2156dcff7d0225c`.

The worker reports 65 tests passing plus Ruff, formatting, compilation, and
diff checks. Parent independently reproduced the prior R2 suite and was still
reproducing this R3 freeze at review handoff; I did not independently execute
those checks. No real accepted schema-2 receipt or binding exists, so this
review supplies no live bottleneck or Rust decision.

## Closure assessment

The R2 finding is closed. `tools/session_performance.py:724-736` defines the
decode-causal client prefix separately from the later sample-completion marker.
`tools/session_performance.py:1170-1189` requires that complete prefix, every
owner boundary, the matching owner generation, identity continuity, and nonce
for every successful decode. `tools/session_performance.py:1217-1218` still
requires all timestamps, including `sample_completed_monotonic`, when an
attempt declares `state == "completed"`.

A failed or incomplete attempt may now preserve a successful strict-decode
CPU/wall pair with `sample_completed_monotonic == null`, as required by the
canonical end-to-end boundary. The regression at
`tests/test_session_performance.py:1275-1301` exercises that exact case and
checks the retained null marker, pair, and timing-unqualified state. The causal
boundary parameterization at `tests/test_session_performance.py:1230-1272`
continues to refuse every genuinely pre-decode null boundary and a missing
owner generation, and a refused record still forces the otherwise complete
collection to `insufficient_evidence`. The owned documentation states the same
split at `docs/RUNTIME_PERFORMANCE.md:157-165`.

The earlier privacy sanitization, same-attempt provenance, cleanup-failure
retention, and counter consistency/inter-sample eligibility fixes remain in
place. The corrected sample-completion handling does not weaken source,
producer, config, identity, model-call, cleanup, cadence, quantile, or decision
gates.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
