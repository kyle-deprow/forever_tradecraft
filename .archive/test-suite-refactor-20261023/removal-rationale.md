# Test-suite refactor (2026-10-23)

The pre-refactor inventory contains 1,467 test functions (2,164 collected
items after parametrization); six functions from that inventory were removed
after final tuning. Subsequent feature tests add new coverage separately.
The default now uses sixteen bounded
xdist workers with work-stealing on the verified 16-CPU host. These
four giant, process-heavy duplicate replays were removed from the default
retained suite:

| Removed function | Approx. body | Why it was low-value | Remaining independent coverage |
| --- | ---: | --- | --- |
| `tests/test_native_calibration_operator.py::test_actual_operator_measure_composes_x11_screen_daemon_and_agent` | 2,643 lines | A large matrix of the same full screen/daemon/agent composition; it repeated admission, cleanup, and failure paths already asserted individually. | `test_actual_session_ipc_composes_preflight_and_recovery_over_af_unix`, `test_control_preflight_operator_uses_actual_daemon_admissions`, `test_recover_operator_uses_actual_empty_id_recovery_admission`, `test_native_operator_routes_real_daemon_client_prepare_through_actor`, and `test_actual_measurement_error_pauses_and_recovers_with_empty_id` retain actual IPC/operator composition, admission identity, recovery, and cleanup. |
| `tests/test_session_native.py::test_paused_diagnostic_uses_actual_config_ipc_driver_and_eight_compiled_samples` | 2,108 lines | Optional paused diagnostic replay with a large fixture matrix; diagnostic rendering is not a launch-critical execution path. | `test_real_session_daemon_native_provider_route_and_stock_model_capture`, the identity/diagnostic parser tests, and the retained native runner cleanup tests cover production provider binding, evidence validation, and failure receipts. |
| `tests/test_session_native.py::test_compiled_region_composes_through_default_daemon_and_stock_model` | 1,184 lines | Duplicate full composition replay of the provider/stock decoder path. | `test_real_session_daemon_native_provider_route_and_stock_model_capture`, `test_native_operator_routes_real_daemon_client_prepare_through_actor`, and focused native capability/admission tests cover the same route and its refusal boundaries. |
| `tests/test_session_runtime.py::test_native_update_fast_trace_replay_uses_real_runner_and_provider` | 872 lines | Replayed a long real-runner trace after the fast-path contract was split into smaller eligibility, revoke, and cleanup tests. | `test_native_update_fast_eligibility_is_closed_and_revoke_blocks_producer`, `test_runtime_native_provider_delayed_agent_and_hold_use_real_publications`, and the retained native observation failure/cleanup tests cover eligibility, provider publication, revocation, and process cleanup. |

No production source, timeout, click-rate rule, financial assertion, item
identity rule, or live-service behavior was changed. The removals are not
marker deselections: the functions are absent and their independent safety
oracles remain in the default collection.

The former forwarding-only helper
`test_compiled_producer_and_stock_decoder_fixture_is_reused` was removed with
the compiled-region replay because it only called that deleted test function;
it added no independent assertion.

The retained real-Xvfb identity observer test also narrows its expensive
one-second mutation loop to six independent boundary classes (root focus,
descendant focus/ancestor, PID, geometry, invalid candidate, and duplicate
window). The protocol/property negative matrix and static request checks
remain; this removes repeated compositor waits while preserving the real
display, process lifetime/PID replacement, ancestor tree, and cleanup proof.

## Final tuning deletion (2026-10-24)

`tests/test_session_mail_loop.py::test_daemon_async_terminal_clears_matching_cycle_continuation`
(approximately 70 lines) was removed from the default collection. It duplicated
the same `_make_case(armed=True, max_messages=2)` setup, Lua mailbox events,
public IPC confirmations, route/AH flow, and ordinary daemon reconciliation
already exercised by
`tests/test_session_mail_loop_composition.py::test_armed_mail_loop_requires_two_fresh_public_confirmations`.
The retained composition now carries the deleted test's independent private
continuation oracles at the same lifecycle boundaries: the first continuation
is non-null and agrees with the controller, the second confirmation agrees
again, the later asynchronous terminal event clears both daemon/controller
tokens while entering `to_auctioneer`, and ordinary completion at `WAIT_DUE`
leaves both tokens cleared. Its existing physical-click cap, two fresh
confirmations, raw-frame/receipt-free terminal record, input fencing, strict
deadlines, no-arm/reload, queue identity, Guardian lease, and no-extra-poll
assertions remain in the retained composition. This is a literal duplicate
removal for runtime reduction, not a marker exclusion or oracle weakening.
