# Native operator production proofs closure

Status: offline composition candidate; no live qualification or native source acceptance is claimed.

Worktree: `/home/dev/.cache/crowley/worktrees/native-operator-production-proofs-20261018`
Base: `5829bc1`
Writable files: `tools/native_calibration_operator.py`, `tests/test_native_calibration_operator.py`.
The helper source is unchanged from the frozen candidate; the test file adds the actual composition cases.

## Actual cases

- `test_actual_session_ipc_composes_preflight_and_recovery_over_af_unix`: public preflight, recovery begin, and recovery completion through real `SessionIPC.dispatch` over AF_UNIX.
- `test_control_preflight_operator_uses_actual_daemon_admissions`: control-preflight operator path with real `DaemonClient`, independent cancellation actor, daemon admissions, and AF_UNIX dispatch.
- `test_recover_operator_uses_actual_empty_id_recovery_admission`: standalone recovery from a durable checkpoint with an empty reservation ID and a new canonical recovery reservation.
- `test_measure_deferred_public_admission_retains_real_failure_status`: public prepare, bootstrap, native-calibrate, and status lifecycle against the real daemon.
- `test_actual_measurement_error_pauses_and_recovers_with_empty_id`: real terminal measurement failure, newer PAUSED generation, empty-ID recovery admission, and recovery completion.
- `test_actual_bootstrap_reply_loss_after_prepare_expiry_cancels_known_id`: committed bootstrap reply loss after the old bound, with the real actor retaining and cancelling the exact known reservation ID.
- `test_compiled_producer_and_stock_decoder_fixture_is_reused` plus the direct native test: compiled producer/private compositor, stock decoder, and daemon fixture composition.

UI/OCR and external input in the operator cases use sealed test fixtures. Admission, reservation, generation, state history, deadlines, and IPC replies are produced by the actual daemon path; no canned successful admission or manually manufactured reservation is used.

## Verification

All commands used the main virtualenv, explicit `PYTHONPATH` to this worktree's `src`, and private mode-0700 `XDG_RUNTIME_DIR=/tmp/native-operator-production-xdg` where tests required it.

- Focused actual composition group: `6 passed, 51 deselected in 8.67s`.
- Terminal error/new-generation recovery case: `1 passed, 57 deselected in 0.65s`.
- Complete helper suite: `58 passed, 2 warnings in 41.31s`. Warnings are the existing Python 3.12 multiprocessing fork warning in two ownership tests.
- Direct compiled producer/stock decoder test: `1 passed, 147 deselected in 5.50s`.
- Ruff check, Ruff format check, and Python compileall: passed.
- `git diff --check`: passed for the six read-only development inputs.

No source/config/service/GUI/live desktop changes were made. The six copied native files remain development inputs pending their separate review and acceptance. The operator's full live X11 readiness and game qualification remain parent acceptance gates; these offline tests do not claim them.
