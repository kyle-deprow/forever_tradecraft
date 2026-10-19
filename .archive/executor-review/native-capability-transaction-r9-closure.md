# Native capability transaction R9 closure

Status: candidate pending parent verification and final review. The worktree is `/home/dev/.cache/crowley/worktrees/native-capability-transaction-r9-20261018` at base `2d637770dab7caad8dc3636bd60318e25b6d7906`. No commit, deployment, service restart, live desktop operation, game input, or qualification claim was made.

The R9 source fence is `src/crowley/session/daemon.py`, `src/crowley/session/controller.py` (native calibration rollback only), `tests/test_session_native_regressions.py`, and `tests/test_session_native.py` (compiled STOPPED fixture only). The copied read-only files are `src/crowley/session/cli.py`, `tests/test_session_transitions.py`, and `tests/test_session_runtime.py`. Their final SHA256 values and the base values are in the freeze JSON. Imports were resolved from the explicit worktree `PYTHONPATH`.

## Evidence

- The final pre-additive native suite run was the exact three-suite command using the main repository venv, explicit worktree `PYTHONPATH`, and private 0700 `XDG_RUNTIME_DIR`. It completed **353 passed in 481.06s**, exit 0. The complete private log is `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-capability-transaction-r9-20261018/final-native-three-suites-rerun.log`, SHA256 `9526fc0cd1cc99a6a10a138e563402857b208056ce5d27439d2017f2196b016b`, mode 0600.
- The named runtime meter/child cleanup check completed **2 passed in 1.64s**, exit 0. Log SHA256 is `2b5ed8f88f5d4aba2bb00363dc3650435dc8faf20f56c6b9829163245f610d43`.
- The additive owner-runner durability regression completed **2 passed, 139 deselected in 44.41s**, exit 0. It uses the real PNG runner and authentic pinned plan, starts the real `start_calibration("native")` worker, admits `resume_ready` through `native_construction_finalize_admit`, injects one failure at each `native_calibrated` archive/state journal boundary, and verifies that the original error handler's later recovery checkpoint save succeeds. It then verifies persisted `nativeCalibration=false`, `NATIVE_CALIBRATION`, no false finalized terminal, and a fresh owner sees the recovery checkpoint. Log SHA256 is `bc66dd32c97d7c85988c71642301526bdf7040eb8fc5bcf8b22a3d9ce8b171c5`.
- The adjacent direct rollback proofs plus scoped Ruff, format, `py_compile`, and diff checks completed **4 passed, 137 deselected in 44.99s**, all static checks passed, exit 0. Log SHA256 is `5850d300ff6cfdcbf90db89ab88c034fb39d2e9b401a9206455557b1da4339be`.

The additive proof was appended only after the 353-pass run. The pre-additive regression-file hash was `5511124bfb23adc33c4c79194742cb7edd32e48a94019c225f007aa24de1af11`; the final additive hash is recorded in the freeze JSON. The other six final hashes are unchanged between the broad run and the additive proof.

## Requirement map

- Capability identity transaction, exact epoch/generation/kind/reservation matching, controller→construction→Guardian lock order, real public owner revocation, and legitimate inflight `None` ownership are covered by `test_native_capability_admission_and_owner_clear_linearize`, `test_native_capability_matches_exact_owner_facts_and_inflight_none_id`, and the related public predecessor/cancel cases in the 353-pass run.
- Final capture identity and Guardian generation binding, cancel/finalize serialization, and all finalize deadline boundaries are covered by `test_native_construction_composes_real_png_runner_and_finalize`, `test_native_finalize_transaction_rechecks_final_binding_before_mutation`, and `test_native_finalize_transaction_wait_expiry_refuses_before_mutation` in the 353-pass run.
- Recovery barriers and malformed resume facts are covered by the named recovery begin/cancel/complete tests and `test_native_resume_ready_malformed_facts_refuse_before_publication` in the 353-pass run.
- Async worker original-operation identity and three-way worker/prepare/pause locking are covered by `test_completed_worker_cannot_publish_into_next_operation_record` and `test_native_worker_prepare_pause_three_way_lock_barrier` in the 353-pass run.
- STOPPED producer refusal and the configured compiled fixture are covered by `test_compiled_region_composes_through_default_daemon_and_stock_model` plus `named-runtime-and-stopped.log`.
- Native durable rollback is covered by `test_native_calibrated_rolls_back_on_transient_durable_write` and the additive original-owner proof described above.

The initial broad attempt retained two failures: one compiled producer route and one paused diagnostic warmup exceeded the fixed 0.9-second owner protocol deadline. A standalone diagnostic rerun reproduced the latter with owner return approximately 0.9099 seconds after entry; no deadline or assertion was relaxed. The corrected full rerun passed all 353 cases. The retained failed logs are `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-capability-transaction-r9-20261018/final-native-three-suites.log` (SHA256 `faf89bc0391ea6774648fe79c861afbe307f88a84d4996a8eb0d1fa765d476d4`) and `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-capability-transaction-r9-20261018/diagnostic-rerun.log` (SHA256 `10e7ec2bb4ed886a83173c57023e5d0b88562763798b94677ff33ed4073d460e`).

All private logs are mode 0600. Parent review, hash verification, Sol review, and actual Opus review remain parent-owned gates.
