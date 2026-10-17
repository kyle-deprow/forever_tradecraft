# Sol source review — native-memory Stage A test closure R1

## Scope and identity

- Reviewed only `/home/dev/.cache/crowley/worktrees/native-memory-test-closure-20261017/tests/test_session_native_regressions.py` against the accepted Stage A candidate.
- Verified candidate SHA-256: `07d0dbcc66c78554d3b378208e6e1b7be68bd64617a1ac898f3a5f05b7245945`.
- Verified unchanged companion `tests/test_session_native.py` SHA-256: `5519aa12759042935fbab00108673452f3cc4a5b8e46a2f4054e712843026e35`.
- I did not run tests or commands that exercise the product. Parent-reported evidence is 9 focused tests passing in 1.90 seconds; worker-reported evidence is 9 passing in 1.64 seconds with Ruff, formatting, and diff checks passing.

The closure is meaningful and does not weaken the accepted behavior. The helper now closes the meter created by `_native_driver` before clearing its reference (`tests/test_session_native_regressions.py:4076`), removing the leaked pinned descriptor. The append-fault branch increments a local counter at the injected append boundary and requires exactly one call (`tests/test_session_native_regressions.py:4217`), proving the intended fault was reached without exposing the private sentinel.

The new boundary regression obtains its meter through `SessionDaemon._ensure_native_memory_meter`, confirms the production callback is installed, and wraps that callback only to observe invocation (`tests/test_session_native_regressions.py:4264`). It drives both `growth == limit` and `growth == limit - 1`, compares the complete returned `NativeMemoryMeasurement`, and proves no callback call, archive, diagnostic, handshake mutation, qualification mutation, or controller-state change occurs (`tests/test_session_native_regressions.py:4259`). Its `finally` closes the meter, driver, and child process (`tests/test_session_native_regressions.py:4343`). This directly closes Opus's sole Should-Fix and the two specified test-hygiene nits.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
