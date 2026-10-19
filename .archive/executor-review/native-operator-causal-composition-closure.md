# Native operator causal composition closure

Status: bounded offline helper stage complete; unqualified for live release.

The causal composition fixture now exercises the real `X11Screen` constructor and
reload boundary, stock `X11Backend`/`PixelDecoder`, compiled pinned producer,
`SessionDaemon` and AF_UNIX `SessionIPC`, and sealed `FixedInput`/`OwnedEmitter`/
`Watchdog` fixtures. It uses a private no-service-dirs session bus and a private
capture lock only in the test fixture. Production admission and provider timing
are forwarded unchanged. During the update window, duplicate real producer polls
are allowed to return the current publication and are rejected by the unchanged
provider until an external real-monotonic ticker advances the actual deferred
WowClient. The fixture checks each gated PNG against the actual dispatched client
state, then asserts the exact provider sequence construct/0, held/0, updates/1..99,
held/100, resume/0.

The final test command was:

`PYTHONPATH=/home/dev/.cache/crowley/worktrees/native-operator-causal-composition-20261018/src /home/dev/repos/pegasus/.venv/bin/python -m pytest -q tests/test_native_calibration_operator.py --maxfail=1`

Result: `66 passed, 2 warnings in 189.07s`.

Scoped checks passed:

- Ruff format check and Ruff lint for the two owned files.
- Python compile check for the two owned files.
- `git diff --check`.
- Focused composed case: `1 passed in 137.13s` after the final provider-sequence and actual-state assertions.
- Focused AF_UNIX/admission/reply-loss/error recovery group: `6 passed in 15.69s`.

Owned final SHA256:

- `tools/native_calibration_operator.py`: `ffc8ae4f2e338d36d521002e7de5d894c3876a06f621aca5166361055fa9b2e5`
- `tests/test_native_calibration_operator.py`: `d4834f543333a66e9bc9d31e150ef9e085195a27cc93656df5c8d81683fd8b48`

The fixture remains offline development evidence. It does not qualify live UI
geometry, live addon behavior, native dependency promotion, or deployment.

## Verification supplement

- Base commit: `2d637770dab7caad8dc3636bd60318e25b6d7906`.
- Final full-suite command returned exit code 0:
  `PYTHONPATH=/home/dev/.cache/crowley/worktrees/native-operator-causal-composition-20261018/src /home/dev/repos/pegasus/.venv/bin/python -m pytest -q tests/test_native_calibration_operator.py --maxfail=1`.
  The raw terminal log was not retained as a separate file, so there is no log path or log SHA to report.
- The two warnings were the same `DeprecationWarning` from Python's
  `multiprocessing/popen_fork.py:66`: a multithreaded process uses `fork()` and
  may deadlock. They occurred in `test_owned_emitter_gate_and_release_subprocess`
  and `test_owned_emitter_gate_eof_is_bounded`; both tests passed.
- Focused composition command returned exit code 0:
  `PYTHONPATH=/home/dev/.cache/crowley/worktrees/native-operator-causal-composition-20261018/src /home/dev/repos/pegasus/.venv/bin/python -m pytest -q tests/test_native_calibration_operator.py::test_actual_operator_measure_composes_x11_screen_daemon_and_agent --maxfail=1`.
  Its raw terminal log was also not retained separately.
- The test imports `native_calibration_operator.py` from the worktree by its
  explicit test loader; `crowley.session.*` resolves from the worktree `src`
  through `PYTHONPATH`; the WoW harness resolves from the worktree `tests`.
  No XDG override was used. Pytest private temporary roots and their socket,
  bus, lock, receipt, and sealed-tool artifacts were mode 0700/0600 as created
  by the fixture; no retained private artifact is part of this report.
- Cleanup evidence is assertion-backed in the composed test: actual
  `FixedInput.close`, `X11Screen.close`, each created backend input-tool close,
  `DesktopDriver.close`, child termination/wait, Guardian disarmed, server and
  worker joins. After the final run, no owned pytest/compositor process remained.
- The seven read-only development dependencies stayed outside the owned-file
  fence. Their final hashes are recorded in the freeze JSON; no dependency
  promotion occurred.

Coverage map:

| Requirement | Actual test |
| --- | --- |
| Measure-deferred all-state production composition and exact provider sequence | `test_actual_operator_measure_composes_x11_screen_daemon_and_agent` |
| Control-preflight mode over actual daemon admissions | `test_control_preflight_operator_uses_actual_daemon_admissions`; `test_actual_session_ipc_composes_preflight_and_recovery_over_af_unix` |
| Recover mode with empty-ID admission and restore lifecycle | `test_recover_operator_uses_actual_empty_id_recovery_admission`; `test_actual_session_ipc_composes_preflight_and_recovery_over_af_unix` |
| Terminal measurement error, PAUSED transition, fresh empty-ID recovery | `test_actual_measurement_error_pauses_and_recovers_with_empty_id`; `test_measure_deferred_public_admission_retains_real_failure_status` |
| Lost prepare/bootstrap reply with known-ID cancellation | `test_actual_bootstrap_reply_loss_after_prepare_expiry_cancels_known_id`; `test_complete_bootstrap_server_loss_retains_actor_until_owner_eof` |
| Indeterminate actor reply and retained ownership | `test_actor_lost_admission_reply_is_indeterminate_and_remains_armed`; `test_actor_admission_survives_owner_death_and_cancels_late_reply` |
| Actor peer-owned prepare/bootstrap/recovery/finalize/recheck/cancel | `test_actor_owns_prepare_bootstrap_finalize_recheck_cancel_via_peer_credentials`; `test_actor_owns_recovery_begin_and_complete_with_new_canonical_id` |
| Pre-dispatch budget/readiness refusal | `test_fixed_input_phase_budget_refuses_before_go`; `test_action_budget_refuses_before_physical_dispatch_and_deadline_is_monotone` |
| Cleanup and causal-error preservation | `test_causal_run_failure_survives_cleanup_close_failure`; `test_input_action_cleanup_failure_is_named_and_retains_causal_error`; `test_run_receipt_failure_does_not_skip_input_cleanup` |
