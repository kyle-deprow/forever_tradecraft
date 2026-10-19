# Native calibration operator final closure

Status: bounded helper closure implemented; production composition remains blocked by the supplied R7 development daemon inputs and the absence of a stable game window in the allowed private compositor. This record does not qualify live use or promote the helper.

## Owned source

- `tools/native_calibration_operator.py`
  - Adds explicit canonical terminal-failure validation for `error`, `restoration_required`, and `recovery_required`, while preserving normal recovery handshakes.
  - Keeps the provider deadline scoped to the initial construct/release admission and uses operation/reservation/finalize bounds for later phases.
  - Requires an actual `INPUT_CALIBRATION` terminal measurement after finalized, same-generation terminal records, a newer guardian generation on recovery, and a fresh recovery admission before input.
  - Poisons the private actor channel after an incomplete call so EOF performs exact-ID cleanup.
  - Bounds watchdog publication and GO, clears ownership before a refused GO, releases only after GO, and records named input-action cleanup failures without replacing the causal error.
  - Enforces immediate phase budget checks, terminal cleanup protection, and named mandatory cleanup events.
- `tests/test_native_calibration_operator.py`
  - Adds regressions for no-GO ownership clearing, phase-budget refusal, exact terminal-failure binding preservation, and named input cleanup failure with causal-error retention.
  - Retains the real sealed emitter/watchdog, actor peer, handoff, interruption, receipt, and owner-lifetime coverage already in the candidate.

## Verification

Owned focused checks:

- `uv run pytest -q tests/test_native_calibration_operator.py -k 'calibration_error or terminal_pause or fixed_input or phase_budget or all_fixed_measure_sequence' --maxfail=1`: 10 passed.
- `uv run pytest -q tests/test_native_calibration_operator.py -k 'input_action_cleanup_failure or causal_run_failure_survives_cleanup_close_failure or active_receipt_event_failure or run_receipt_failure' --maxfail=1`: 4 passed.
- `uv run pytest -q tests/test_native_calibration_operator.py -k 'not actual_session_ipc_composes_preflight_and_recovery_over_af_unix and not control_preflight_operator_uses_actual_daemon_admissions and not recover_operator_uses_actual_empty_id_recovery_admission and not compiled_producer_and_stock_decoder_fixture_is_reused and not measure_deferred_public_admission_retains_real_failure_status and not actual_bootstrap_reply_loss_after_prepare_expiry_cancels_known_id and not actual_measurement_error_pauses_and_recovers_with_empty_id' --maxfail=1`: 57 passed, 7 deselected, 2 known multiprocessing warnings.
- Final unfiltered `uv run pytest -q tests/test_native_calibration_operator.py`: 61 passed, 3 failed, 2 known multiprocessing warnings. The failures are `test_control_preflight_operator_uses_actual_daemon_admissions` and `test_recover_operator_uses_actual_empty_id_recovery_admission`, both returning `actor_admission_invalid` during R7 recheck, and `test_actual_bootstrap_reply_loss_after_prepare_expiry_cancels_known_id`, where the R7 actor process exits before the committed bootstrap horizon assertion. No owned-only regression was observed.
- `uv run ruff format --check tools/native_calibration_operator.py tests/test_native_calibration_operator.py`: passed.
- `uv run ruff check tools/native_calibration_operator.py tests/test_native_calibration_operator.py`: passed.
- `uv run python -m compileall -q tools/native_calibration_operator.py tests/test_native_calibration_operator.py`: passed.
- `git diff --check`: passed.

## Composition boundary

The required production proof needs `SessionDaemon`/AF_UNIX IPC, production `X11Screen.wait_reload_boundary`, the stock decoder, and real `FixedInput`/`OwnedEmitter` sequencing. The private compositor supplied to these tests has no stable discovered game window; `X11Screen.__init__` therefore cannot complete the production identity/capture boundary without replacing the reviewed resolver or using a synthetic screen. The existing synthetic fixtures are retained as supplemental correctness tests and are not live composition proof. The helper's control-region transform also assumes a 1920x1080 frame with a 220x84 panel; live UI scaling/template geometry remains unverified. A representative synthetic benchmark measured 2.606132 s for exclusive matching and 5.058175 s for dual-positive matching; no optimization or Rust migration was attempted.

The six R7 development inputs were read-only in this WT and remain unaccepted. Their hashes are recorded in the freeze manifest. No Git commit or source promotion was performed.
