# Sol statistics benchmark cleanup review

Date: 2026-10-24

Scope: read-only review of the final statistics amendment in `.archive/PLAN-suite-stability-20261024.md`, `tests/test_trading_engine.py`, `.archive/test-suite-refactor-20261024/statistics-timing-rationale.md`, and `.archive/test-suite-refactor-20261024/statistics-timing-r3-output.txt`. No tests were run and no production source was changed by this review.

## Findings

### Must-Fix

None.

### Should-Fix

None.

### Nits

None.

## Evidence

- The scoped test diff removes exactly the unused `time` import, the `time.monotonic()` start, and the local `< 10` elapsed-wall assertion. The only other change is the accurate rename from `...full_size_statistics_gate` to `...covers_full_size_statistics`; there is no hidden threshold adjustment, skip, selection marker, input reduction, or exclusion.
- The complete test still creates 330 item series with 240 books apiece, calls the real `precompute_statistics(full)` path, and requires exactly 330 results. All existing required report-field assertions are retained unchanged.
- The rationale explicitly records deletion of the local timing guarantee rather than claiming metric equivalence. Its rejection of caller-only `process_time()` is correct because that excludes the process-pool children, while aggregate parent-plus-child CPU is a different quantity from parallel critical-path elapsed time and was already measured above the former limit.
- The independent suite-level bare-default wall gate remains the performance acceptance criterion. The stated final-r3 result of 146.233 seconds is below its 180-second limit; the next parent full run remains the final acceptance evidence.
- `.archive/test-suite-refactor-20261024/statistics-timing-r3-output.txt` reports the retained full-size case passing under 16 workers in 6.20 seconds (`WALL=6.43 EXIT=0`). This review did not rerun it.
- Production trading files have pre-existing worktree changes from the broader feature effort, but the bounded candidate diff reviewed here contains no production change; its only tracked source/test delta is the four-line test cleanup described above.

## Integrity

The reviewed artifacts were stable across the review:

- `tests/test_trading_engine.py`: `1aafac732e4ab345d0954d318b1ad927594439dfbbb367aecb90ea18037a531b`
- `.archive/test-suite-refactor-20261024/statistics-timing-rationale.md`: `422ba1b8aae5a181572a3d713f07b1a25be912d8be1430cacdfb0f2f3517e988`
- `.archive/test-suite-refactor-20261024/statistics-timing-r3-output.txt`: `87a429f1fd4aa1e1778629c4d86e139655ab01b97106d67df951f49f89cfc54d`

## Verdict

**READY**
