Actual CLI review, exit0, resolved model claude-opus-5-5. Raw stream SHA256 abb886111f4520f70fbf1e8907250d5489ca5866e8bd0b6571023a998fc8978e. Six final source pins unchanged.

Model ID: `claude-opus-5-5`

# Opus R3 review: native ACK test-safety patch (two test files)

The patch does what the plan asked and I found nothing that needs changing: no Must-Fix, no Should-Fix, no Nits. The made-up process group 999999 is gone. The test now adds the PGID of its own live `sleep` process. The Guardian state is restored in `finally` on every exit, and the clean watchdog state is published and acknowledged before the `sleep` holder is terminated and reaped.

**What I checked**
- **Pins:** all six final hashes match `review-input.json`, both before and after the review. `git status` is unchanged from the start of the session.
- **The diff is exactly the R2 delta:**
  - I regenerated the R2→final diff from the preserved R2 test copies (`native-ack-parent-r2-final-20261019/source`, R2 pins `9f0c99e2…` and `a6eacc9c…`).
  - It is byte-identical to `correction.diff`, and its sha256 is `115faf64…`, which equals `patchSha256`.
  - The three production files and the operator test match R2.
- **Parent logs:** the hashes match `review-input.json`.
  - typed: 3 passed.
  - static: all four checks return 0.
  - baseline: 1 passed. The old mode fails with `native updates/4 returned 'updates'/5` after 3 accepted. The reduced mode has no error, 99 accepted, and a 1435.161 ms maximum.
- **Read-only:** no edits, no project tests, no services or GUI, no plan file. I ran one isolated Python check of how `sys.exc_info()` behaves inside `finally` on 3.12.12, which is not a project test.

## Confirmed in the test delta

**Live group replaces 999999 (`test_session_native.py:2448-2455`)**
- `start_new_session=True` runs `setsid` before `exec`, so the PGID equals `holder.pid` by the time it is added.
- `close_fds` defaults to true, so the holder cannot inherit the watchdog pipe and delay the watchdog noticing that the test process died.
- The refusal is unchanged: `daemon.py:2281-2290` only checks whether `active_process_groups` is non-empty, and `:2544` still asserts the exact message.
- Nothing in the test process signals that group. Only the watchdog's `terminate_groups` (`guardian.py:261-275`) would. `driver.close()` kills only the driver's own calibration groups (`driver.py:6821-6854`).
- Between the typed refusal and the next publish in the generation race, the watchdog's kill list contains only this test-owned live `sleep`. If the test process dies in that window, the watchdog kills only that `sleep`.
- **30 s holder lifetime:**
  - If the test is SIGKILLed, the leaked `sleep` exits on its own within 30 s.
  - If the `sleep` exits before cleanup, it stays an unreaped zombie. Nothing calls `waitpid(-1)` in `src/`, so its PID cannot be reused while the test process lives.

**Restoring after the generation race is safe (`:2757-2771`)**
- The snapshot at `:2405-2416` is taken after the typed thread has passed `observer_dispatch_admission` (`daemon.py:6190`).
- That admission (`guardian.py:791-799`) requires `_held` and `_release_failed` to be false, `_active_process_groups` to be empty, and `_watchdog_failed` to be false.
- So the late restore only writes the clean state. It cannot re-add a stale PGID or hide a real group, because this test registers no input or calibration groups.
- The block only runs for the three new faults. The other parametrizations skip it, including the final-lock-gate cases where `_lock` may have been swapped.

**Publish before reaping (`:2759-2789`)**
- The restore runs under the Guardian's re-entrant lock (`guardian.py:513`).
- `_watchdog_state()` returns true only after the watchdog sends its ACK (`:1963-1969`).
- The snapshotted `_watchdog_failed` is necessarily false, so `assert published` always applies.
- The holder is terminated and reaped only afterwards. If publication fails, the holder is still reaped and the error is reported.

**All exits, original failure kept (`:2754`, `:2794-2795`)**
- On 3.12.12, `sys.exc_info()` inside `finally` returns the exception in flight, and returns `None` on the `return` path at `:2612`.
- A watchdog-cleanup error is raised only when the test was otherwise passing, and only after `driver.close()`.
- The refusal, retirement, artifact and registry assertions (`:2543-2556`) are unchanged.

**Runtime test (`test_session_runtime.py`)**
- `:3997-4003` pins the observed outcomes, as the accepted nit asked. Old mode must fail with the daemon's ordinal-mismatch message (`daemon.py:5364/5382`) and accept fewer than 99. Reduced mode must have no error and a maximum above 900 ms.
- The `aligned` error-is-None assertion is kept.
- `:3963-3967`: the comment now attributes `owner_validation == 2` to held/100 and resume/0.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None. I considered and did not report these, because none has a reachable impact:
- The `_watchdog_failed` restore goes beyond the three injected fields, but it mirrors the existing inline restore. If the real watchdog channel failed, `_watchdog_write` would be -1, publish would return false, and the assert would fail loudly.
- The `elif` branch at `:2770` can never run, and it is harmless.
- `"returned"` is the exact marker the accepted nit asked for.
- An error from `driver.close()` would replace the deferred cleanup error. That only changes which error is shown; the test still fails.

Live qualification is still pending, and the full compiled100 and seven-case evidence remains bound to the original R2 pins.

STATUS: READY
