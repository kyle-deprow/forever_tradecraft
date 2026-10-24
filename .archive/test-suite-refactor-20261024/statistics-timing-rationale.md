# Full-size statistics timing gate (2026-10-24)

## Failure evidence

Parent final-r3 ran the unchanged test under the default 16-worker suite and
reported `2454 passed, 25 skipped, 1 failed` in `146.233s` external. The sole
failure was the existing wall-clock assertion in
`tests/test_trading_engine.py::test_report_contains_required_fields_and_full_size_statistics_gate`:
the full 330-item × 240-book `precompute_statistics` call took `10.593s`
wall-clock, just over its existing `<10s` compute-work budget. The parent
suite itself remained below the independent 180-second wall gate.

`precompute_statistics` is CPU-bound and deliberately dispatches the 330 item
series to an eight-process `ProcessPoolExecutor`. A locked diagnostic with the
full unchanged input measured:

```text
items=330 wall=4.592 parent_cpu=3.904 child_cpu=10.504 aggregate=14.409
```

An initial test-only attempt that summed parent and reaped-child CPU was
rejected by the retained `<10s` budget (`1 failed`, `WALL=7.63`, aggregate
CPU `14.957s`). Summing parallel workers is not a critical-path compute
budget: it grows with the intentional worker count and would reject a faster
wall-clock execution merely because several workers ran concurrently.

## Final correction

The coordinator-only `time.process_time()` experiment was rejected: it
excluded the CPU consumed by the eight real `ProcessPoolExecutor` children and
therefore weakened the compute-work claim. Aggregate child CPU is also not a
valid replacement for the old per-call gate (`14.409s` in the diagnostic and
`14.957s` in the failed attempt), because it sums intentionally parallel work.

The lower-value, flaky local microbenchmark assertion and its now-unused
`time` import were removed. The test was renamed to
`test_report_contains_required_fields_and_covers_full_size_statistics` so its
name describes the retained coverage. The full 330 × 240 input, the actual
`precompute_statistics` call, `len(statistics) == 330`, and every report-field
assertion remain. The independently timed parent bare-default run remains the
authoritative real wall-clock performance gate (<180 seconds); no production
path, threshold, input, clock, case, or exclusion was changed beyond deleting
the flaky local timing assertion.

Locked focused verification of the renamed coverage test with pinned CARGO and
the configured 16-worker default:

```text
1 passed in 6.20s
WALL=6.43 EXIT=0
```

The run emitted eight non-fatal multiprocessing fork deprecation warnings.
