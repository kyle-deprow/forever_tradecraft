# Native R8 proof closure — Sol review

Reviewer: configured `gpt-5.6-sol`  
Scope: only the 535 appended lines in frozen `tests/test_session_native_regressions.py` (`6447c6a4470334650034ae277dc00d30e67c2ce29179f812a14c52f3dae042a8`) against the original R8 file (`093b97e15d81c407d40564815ee3eb867003bbd43146acb85a0ed7a1fdd4bba5`). I did not review R9, reconsider the accepted R8 capability race, or rerun tests.

## Must

1. **The deadline regression expires at the outer revalidation, before the final transaction.** In `tests/test_session_native_regressions.py:6444-6453`, the wrapper stops the third call to `_native_construction_revalidate_finalize_owner` only after that call has succeeded. After release, production performs another revalidation at `src/crowley/session/daemon.py:7389-7394` before invoking `_native_construction_finalize_transaction` at `7395-7404`. The fixture acquires the controller lock and advances the clock at test lines `6540-6543`, so that fourth revalidation blocks and then raises the selected deadline error. The transaction at `daemon.py:1864-1965` is never reached. Consequently all three parameter cases would still pass if its after-lock deadline checks at `1902-1910` were removed, which leaves the assigned waiting-transaction proof open.

   Replace the revalidation-count barrier with a thin observation wrapper around `_native_construction_finalize_transaction`. Signal on entry to that wrapper, have the main test thread acquire `controller.lock`, advance only the named bound past expiry while keeping the other bounds valid, release the wrapper, and delegate to the original transaction. The original transaction must then wait for the held controller lock and raise the exact final/hook/operation error after it acquires the lock. Retain the zero-call assertions for rebind, observe, and `native_calibrated`, and add an assertion that the transaction wrapper was entered exactly once. This is a test-only correction; no timing allowance or production change is needed.

## Should

1. **Assert bounded completion of the calibration worker in the three-way case.** `tests/test_session_native_regressions.py:5989-5998` joins and checks the prepare and pause threads, but the calibration worker is only joined without an assertion in `6001-6003`. The test otherwise reaches the real worker status boundary, prepare's construction-to-calibration edge, and pause's synchronous controller-to-construction callback, and its `worker_status_entered` assertion would reject the old worker lock order. After the prepare and pause assertions, join `daemon._calibration_thread` with the same bounded timeout and assert it is no longer alive. Keep the `finally` join for failure cleanup.

## Nits

None.

The two malformed-resume cases at `tests/test_session_native_regressions.py:5399-5451` are adequate. `missing_capture` and NaN `sequence` pass the earlier freshness predicate and reach the deferred fact validation at `daemon.py:3148-3159`; the assertions establish that neither `resume_ready` nor `INPUT_CALIBRATION` was published, then exercise the real failure cleanup. The three-way fixture also gives useful, regression-sensitive coverage once the worker-completion assertion is added.

The recorded six-case passes establish the current test behavior but do not close the final-transaction proof because of Must 1.

STATUS: NEEDS WORK
