# Runtime live instrumentation: Sol source review R3

This was a read-only review of the frozen R3 successor at
`/home/dev/.cache/crowley/worktrees/runtime-instrumentation-r3-20261017`. I
reviewed the R2-to-R3 correction delta and the directly affected callers against
the unchanged canonical plan and accepted evaluator. I did not edit the
candidate, run tests or the harness, use Git, or access any runtime, game, GUI,
network, or database. The only file I wrote is this report.

## Identity and scope

The supplied review artifacts match exactly:

- `.archive/executor-review/runtime-live-instrumentation-r3-freeze.json`:
  `b81b0125da6e11039763927e7352fa561ffd1aa3f86a4bd943d21629a2aa68e3`
- `.archive/executor-review/runtime-live-instrumentation-r2-to-r3.diff`:
  `2ddb6a6171b257f5731e450a6ce8779534d04896f8903923c508cd2cb1c1d391`
- `.archive/executor-review/runtime-live-instrumentation-r3-parent-delta.diff`:
  `70a688e72da6acd45fe26923f1a2a04a41f3515d6859859beaf46c9643138b75`
- `.archive/PLAN-runtime-live-instrumentation.md`:
  `a563e4df1450eaac3cb44b87fb3143a823bbed5b23f4209d168703a010a0bb62`
- prior Sol R2 review:
  `22540b7d6901d320f5271cc2a04ba7d30e10036aab79486ff8602ca1312fc271`
- actual Opus R2 review:
  `5392e43ee94667aa67e421a44fa84b688f815d2bc875b824db532b0b492e14fd`

All four frozen candidate files match the freeze:

- `src/crowley/session/driver.py`:
  `fb907096007e10ed59f67dceb52dd20a3e54c37ff02e011d21c61f292806938d`
- `src/crowley/session/daemon.py`:
  `22d156727f87d3b7aa84ce614754023cc68c6edf0da40d6ea4ac001dd8803683`
- `tools/gnome-telemetry-region/offline_harness.py`:
  `22272f498a62d1a0fa83c8447411cfba3328439e846c781d0e4c1e7d3e64ec47`
- `tests/test_session_native.py`:
  `422792783d0a52e57972cb4b7c6ce8481310a9d95fefd7e8d98e2df7c60d7553`

The accepted evaluator remains byte-identical at
`c46cae849058005e9b7387ef95c34f40f376afb5477739efaf6f40f6a36ebd8c`,
its tests at
`c998aa4a9ff67ba67ddeab05a0e5a0cfa5273a296909e0b07cb79a3d06dd313a`,
and its documentation at
`54237c344ef0faa3392cca6fe82b75f1f986bbf697c81d3f34493b2f00e1caca`.
The inspected correction remains inside the authorized four-file fence.

Parent reports the 134 native checks, 65 evaluator checks, compiled composition,
harness checks, Ruff, formatting, compilation, and scoped diff checks passing. I
did not rerun them.

## Closure assessment

The R3 production delta closes the causal R2 findings:

- `driver.py:3172-3210` computes final retirement even when no attempt directory
  was created. `daemon.py:3991-3996,4059-4063` turns a genuinely not-started
  producer into a boolean terminal result from the final cleanup ledger, so
  pre-admission refusals no longer emit structurally invalid null cleanup.
- `offline_harness.py:1519-1616,1909-1934` requires an exact boolean response,
  the appropriate success/failure outer shape, and request-bound generation and
  config hashes before projecting a refusal. Late refusals and timeouts retain
  bounded private evidence, and a returned failure PNG is validated and saved.
- `offline_harness.py:1671-1709` projects the daemon's actual owner semantic
  config hash without falling back to the request hash. The real mismatch path
  at `tests/test_session_native.py:2358-2389` also proves the two values differ.
- `offline_harness.py:1822-1836` routes target-wait termination through the
  common source and receipt finalizer as an incomplete run without fabricating
  an attempt. `offline_harness.py:2085-2106` performs the required final status
  under the original deadline before stamping completion and rechecks the
  deadline afterward.
- Failure classification is now finite and fail-closed. Returned non-fresh
  decode results preserve their real CPU interval and use the post-decode
  `unknown_required_stage`; config rereads, owner source/config/producer checks,
  client PNG publication, final status, and unknown internal phases retain their
  causal classification.
- The public evaluator path now uses a binding calculated from known fixture
  source, producer, and config inputs. Actual owner refusal, wait interruption,
  source drift, and nonzero model-call evidence are retained in the focused
  regression. All four real model wrapper entrypoints and success/failure
  counter transitions are exercised.

I found no causal production defect or regression in the correction delta. The
documented meaning of `response_ready` and the cost of repeated source reads are
unchanged nonblocking limitations, as previously adjudicated.

## Must-Fix

None.

## Should-Fix (nonblocking test precision)

1. **The real config-refusal regression still bypasses the public evaluator and
   derives two accepted-binding sections from the receipt under test.**

   - File: `tests/test_session_native.py:2372-2387`
   - The production projection is correct, and the test directly proves the
     owner semantic hash differs from the request. However, the final evaluator
     assertion calls private `_validate_live_receipt` and copies source and
     producer bindings from that same receipt. This does not provide the exact
     independent-binding plus `build_live_report` proof requested in the Opus R2
     closure; a simultaneous source/producer projection error would be accepted
     by this one regression.
   - Correction: copy the independently computed `live_binding`, replace only
     its config object with the raw digest calculated from the altered fixture
     file and `altered_semantic`, then call `_evaluate_persisted_live_receipt`.
     Assert the public run is retained, ineligible, and reports
     `config_binding_mismatch`.

2. **The real identity-refusal regression does not inspect the retained private
   refusal it claims preserves the original phase and error.**

   - File: `tests/test_session_native.py:2201-2221`
   - It verifies the normalized schema-2 `owner_capture` result and the private
     file's existence/mode, but never reads that file. A regression overwriting
     the daemon phase or causal error could pass while the normalization remains
     unchanged.
   - Correction: parse `owner-refusal-00.json` and assert the original
     `identity_before_capture` phase, the injected causal error, a `not_started`
     producer with `attempt_retired: true`, and the final lease/armed/empty
     cleanup facts.

## Nits

None.

This review qualifies the frozen source correction only. It does not qualify a
schema-2 collection, the performance gates, or a Rust decision.

STATUS: READY
