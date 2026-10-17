# Runtime live instrumentation: Sol R3 test-only closure review

This was a read-only review of the one-file test delta in
`/home/dev/.cache/crowley/worktrees/runtime-instrumentation-r3-test-closure-20261017`.
I did not edit the candidate, run tests, use Git, or access any runtime, game,
GUI, network, or database. The only file I wrote is this report.

## Identity and scope

- Freeze:
  `a56d8b688d0b6533c66f0ec9c12dd9c988c3134485b7896811a9cfa4f3b070c9`
- Test-only delta:
  `0974d1615d8ce190856111878a0beabf095258780656fec6fb0d89261ba672aa`
- Reviewed `tests/test_session_native.py`:
  `c742c01a8a3b75518590ebb57afef87388c2d7f6887e814cabf758f9cacab37a`

The three production hashes remain byte-identical to frozen R3:

- `src/crowley/session/driver.py`:
  `fb907096007e10ed59f67dceb52dd20a3e54c37ff02e011d21c61f292806938d`
- `src/crowley/session/daemon.py`:
  `22d156727f87d3b7aa84ce614754023cc68c6edf0da40d6ea4ac001dd8803683`
- `tools/gnome-telemetry-region/offline_harness.py`:
  `22272f498a62d1a0fa83c8447411cfba3328439e846c781d0e4c1e7d3e64ec47`

The evaluator, evaluator tests, and documentation also retain their accepted
hashes `c46cae849058...`, `c998aa4a9ff6...`, and `54237c344ef0...`
respectively. The delta contains only the two requested test corrections.
Worker reports the focused actual-composition test and Ruff, formatting,
compilation, and diff checks passing; I did not rerun them.

## Closure

- `tests/test_session_native.py:2214-2232` now parses the private identity
  refusal and checks its original `identity_before_capture` phase, exact causal
  `DriverError`, complete `not_started` producer record with terminal retirement,
  and final lease, armed, and empty-cleanup facts. This proves the raw causal
  evidence independently of its normalized schema-2 projection.
- `tests/test_session_native.py:2389-2400` now deep-copies the independently
  computed fixture binding, derives only the changed raw and semantic config
  digests from the known altered fixture, and sends the real persisted receipt
  through `_evaluate_persisted_live_receipt`, which uses public
  `build_live_report` with a separately hashed accepted-binding file. No binding
  section is copied from the receipt under test.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
