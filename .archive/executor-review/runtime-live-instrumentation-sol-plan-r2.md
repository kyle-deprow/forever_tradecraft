# Sol plan review R2: runtime live instrumentation compatibility

This was a bounded read-only plan review against the accepted schema-2 offline
evaluator. I did not run tests, execute receipts, inspect runtime state, or make
source changes.

## Inputs checked

- `.archive/PLAN-runtime-live-instrumentation.md` — SHA-256
  `f425d32a257a1ab730532f8043de45a2e4b07642e81604664f854987270c9ebb`
- `docs/RUNTIME_PERFORMANCE.md` — SHA-256
  `54237c344ef0faa3392cca6fe82b75f1f986bbf697c81d3f34493b2f00e1caca`
- `tools/session_performance.py` — SHA-256
  `c46cae849058005e9b7387ef95c34f40f376afb5477739efaf6f40f6a36ebd8c`
- `tests/test_session_performance.py` — SHA-256
  `c998aa4a9ff67ba67ddeab05a0e5a0cfa5273a296909e0b07cb79a3d06dd313a`

The three accepted evaluator hashes match the plan's pins.

## R1 closure

- **Dependency and ownership:** closed at
  `.archive/PLAN-runtime-live-instrumentation.md:5-35` and `:39-53`. The plan
  now waits for the accepted native successor (currently R6), treats the
  accepted evaluator as read-only, and limits implementation to the four
  production/test paths.
- **Seven-source binding:** closed at
  `.archive/PLAN-runtime-live-instrumentation.md:55-101` and `:153-156`. Both
  owner and observer use the evaluator's exact seven logical keys with stable,
  bounded descriptor checks and trusted-root paths.
- **Exact schema and owner cleanup:** closed at
  `.archive/PLAN-runtime-live-instrumentation.md:73-78` and `:103-127`. The
  accepted tool/documentation are normative; exact nullable fields, counter
  arithmetic, identity, fixed failure enums, and post-reap/post-retirement
  cleanup are specified without adding receipt keys.
- **Decode versus completion and schedule:** closed at
  `.archive/PLAN-runtime-live-instrumentation.md:129-151`. The plan preserves
  eight targets at `t0 + i*1.0`, deadlines at `target + 1.0`, no rebasing, the
  CPU method string, and a nullable later completion marker after a successful
  decode.
- **Bounded unbiased collection:** closed at
  `.archive/PLAN-runtime-live-instrumentation.md:238-250`. One 16-run batch is
  declared before collection, every outcome is retained, and the accepted
  baseline, primary route, alternative route, and insufficient-evidence result
  are kept distinct.

## Must-Fix

None.

## Should-Fix

1. **Remove the stale evaluator-unit cases from the production-test sentence.**

   - File: `.archive/PLAN-runtime-live-instrumentation.md:208-215`
   - Lines 208-212 tell the four-file production slice to cover oversized and
     malformed receipts, 14-versus-15 runs, 119-versus-120 pairs, duplicate
     runs, exact quantiles, all decisions, and report privacy. Lines 213-215
     correctly say those are already covered by the accepted evaluator and
     must not be duplicated. Leaving both instructions can expand
     `tests/test_session_native.py` into a second evaluator suite even though
     the evaluator is a pinned read-only authority.
   - Correction: keep production tests limited to emitted schema/boundary
     clocks, success/failure lifecycle, counters, bindings, cleanup, and one
     end-to-end compatibility pass through the unmodified evaluator. Retain the
     accepted evaluator test command as a regression check, but assign malformed
     inputs, threshold math, quantiles, decisions, and privacy solely to its
     existing test suite.

## Nits

None.

The remaining correction does not block feasibility or schema compatibility.
Implementation remains gated on acceptance of the native successor and the
specified Sol/actual Opus review and sole-operator release sequence.

STATUS: READY
