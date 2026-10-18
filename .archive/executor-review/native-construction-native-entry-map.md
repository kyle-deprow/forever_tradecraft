# Native-construction native entry map

Scope: current `main` entry points for the three-file native slice in `controller.py`, `daemon.py`, and `cli.py`. This is an offline read-only map of the R3 plan plus closure amendment; it does not release implementation or live operation. The accepted addon slice remains the prerequisite.

## CLI and IPC admission

- `cli.py:796-844` is the real argparse surface. Commands are registered explicitly, hyphens become underscores at `cli.py:892`, `generation` is copied at `cli.py:905-906`, and `_socket_request(config.socket, request, timeout=...)` is the live transport at `cli.py:926`.
- Add the fixed commands beside `native-bootstrap` at `cli.py:809`: `native-construction-prepare`, `native-construction-control-preflight`, `native-construction-finalize-admit`, `native-construction-recovery-begin`, `-complete`, and `-cancel`. Prepare, preflight, and finalize-admit have the plan's required `--generation`; recovery still checks the current paused generation, although R3 does not settle its exact CLI argument spelling.
- `SessionIPC.dispatch(request)` at `cli.py:53` is the command admission boundary. Follow the exact-set pattern at `cli.py:60-79` and `188-199`: check owner presence, exact request keys, non-bool integer generation, and types before indexing/calling the daemon. Do not use the generic mutating fallthrough at `cli.py:323-356`; it lacks per-command shape checks and runs under the controller mutex.
- Legacy admission is `native_bootstrap(expected_generation=...)` at `cli.py:118-133`; preserve its request and response. Deferred bootstrap needs a distinct dispatch/method and `expected_constructor_boot`, without changing legacy callers.
- Existing recovery pause can use direct production IPC `{"command":"pause","generation":g,"reason":"native construction recovery"}`; dispatch forwards `reason` at `cli.py:347-348`. The public pause parser has no `--reason` (`cli.py:802-807`), so the later helper must use the IPC request path rather than simulate admission.
- Private reservation/ticket replies use only the canonical names in closure lines 40-43 and stay separate from `status`.

## Controller persistence and boot identity

- `Controller.__init__` reads the journal at `controller.py:169-181`; load and strictly validate the internal root `nativeConstruction` record there. Its only closed forms are the closure's schema-1 six-field record and absence.
- `_save(last_action=...)` rereads the root and updates it before `Journal.write` (`controller.py:886-972`). It currently preserves unknown root members, but the controller-owned record must be an attribute and explicitly written so transitions are not accidental pass-through. `Journal.write` is atomic, 0600, and directory-fsynced (`journal.py:100-167`).
- Keep the record out of `ControllerStatus` (`controller.py:982-998`) and `SessionDaemon.status_dict()` (`daemon.py:6137-6179`); neither may expose the record or `B0` in public status.
- The durable trio loads from `current.frameBoot/frameSequence/frameCrc32` at `controller.py:219-241` and saves at `952-968`. `observe_frame(boot, sequence, crc32, expected_generation, expected_state, fence)` rejects unrelated boot changes at `controller.py:1204-1290`.
- Put the closed non-IPC rebind beside `observe_frame`, reuse `_admitted(...)` (`controller.py:342-362`), require the exact reason/state pair and valid frame trio, update only that trio, then `_save`. Neither plan specifies its Python name; do not create a generic/public boot setter.
- Finalize rebinds for `native_construction_finalize` in exact `NATIVE_CALIBRATION` immediately before `native_calibrated`. Recovery-complete rebinds for `native_construction_recovery` in exact `PAUSED` immediately before `resume(expected_generation=...)` (`controller.py:1776-1898`). Tests then pass the accepted frame through real `observe_frame`; unrelated boot changes remain blocked.
- `native_calibrated(evidence, preconstruction_proof=..., expected_generation=..., expected_state=..., fence=...)` is the terminal commit at `controller.py:1443-1489`; it verifies, archives, saves, and enters `INPUT_CALIBRATION`. Deferred mode cannot call it before finalize proof.

## Daemon ownership and legacy composition

- `SessionDaemon.__init__` owns `_calibration_lock`, `_calibration_state_lock`, the operation record, bootstrap events/lock/observations, and `_native_handshake` at `daemon.py:640-681`. Provider and seven callbacks are wired onto the driver at `daemon.py:704-725`; tests should use that composition.
- `start_calibration("native", expected_generation=g)` creates the asynchronous worker/operation at `daemon.py:810-858`; `_begin_calibration` is the single-operation guard at `795-808`. Admission precedes worker start under one daemon construction/reservation lock. No current lock covers reservation, recovery ticket, bootstrap, operation, and helper ownership together; that state holder is concretely missing.
- Legacy `native_bootstrap(*, expected_generation=None)` at `daemon.py:897-1004` requires exact `NATIVE_CALIBRATION`, captures strict absence, retains the private artifact, and sets `_native_bootstrap_ready`.
- `_native_preconstruction_provider(identity, *, baseline_reader, baseline_ready)` at `daemon.py:1342-1427` performs absence/hash check -> `baseline_reader(pid)` -> `baseline_ready(pid,hwm)` -> sealed evidence -> clear. Preserve this legacy provider.

## Runner and deferred handshake order

- `NativeCalibrationRunner.run()` supplies the unchanged call order: preconstruction invokes construction reset/archive and baseline-ready (`calibration.py:4426-4476`); provider `construct/0` and construction memory finish (`4551-4655`); hold-required and provider `held/0` (`4658-4677`); update reset/archive then memory-ready (`4678-4695`); providers `updates/1..99` and `held/100` (`4697-4742`); resume-required, provider `resume/0`, then resume-ready (`4759-4834`).
- Real callbacks are `notify_native_baseline_ready` (`daemon.py:1006`), `notify_native_memory_reset_ready` (`1048`), `notify_native_hold_required` (`1108`), `notify_native_memory_ready` (`1025`), `notify_native_resume_required` (`1120`), `notify_native_resume_ready` (`1158`), and `notify_native_measurement_failed` (`1195`).
- The reset callback already records `<phase>_reset_archived` at `daemon.py:1094-1106`; deferred handling must enforce the closure predecessor table, including `updates_reset_archived` before `measure_ready`, instead of overwriting states.
- Legacy baseline-ready emits `bootstrap_ready` at `daemon.py:1023`. Deferred baseline emits `baseline_bound`, performs and seals the post-reset absence capture, deletes the verified PNG, then atomically publishes `construction_released` with `_native_bootstrap_ready`; it never emits `bootstrap_ready`.
- `_native_measurement_provider(identity, stage, ordinal)` is the real 30-second poll at `daemon.py:1583-1722`; stages are exactly `construct`, `held`, `updates`, `resume`. At deferred `construct` entry derive `constructorClickDeadline = provider_deadline - 7.0`, bind it to reservation/generation/boot/capture/attempt, and retain the existing provider deadline.
- `run_native_calibration()` currently calls the runner then immediately `controller.native_calibrated` at `daemon.py:5037-5091`. Deferred mode inserts the 30-second finalize hook, finalize-admit transition/deadline, strict newer frame, and controller rebind between those calls; legacy timing is unchanged.
- Failure cleanup at `daemon.py:5092-5127` clears proof/state/artifacts and records terminal operation error while leaving `NATIVE_CALIBRATION`. Revoke reservation and Guardian ticket there while preserving the first causal error. Recovery then uses `Controller.pause(reason)` (`controller.py:1900-1933`), which increments generation and calls `guardian.revoke` before saving `PAUSED`.

## Lease, tickets, revocation, and later helper API

- Canonical lease facts are `driver.guardian.lease.held`, `.generation`, and `.armed`. `InputGuardian` acquires the process-lifetime `InputLease` at `guardian.py:483-507`. `revoke(reason)` increments generation, disarms, cancels its calibration epoch/ticket, releases owned input before callbacks, and returns the generation (`guardian.py:1894-1941`).
- Ticket primitives are `begin_calibration_operation()` (`guardian.py:875-889`), `issue_calibration_ticket(ticket)` (`891-913`), `calibration_ticket_current(ticket)` (`914-920`), and `cancel_calibration_operation(ticket=None)` (`936-941`). Driver `issue_calibration_ticket(target)` is GTK-`OwnedWindow` specific (`driver.py:4478-4552`); it is not future game-helper admission.
- Later helper reference only: `PinnedInputTool.load()` and `duplicate_release_spec()` produce a sealed `NativeReleaseSpec` (`input_tool.py:263-307`); `verify_image()` checks memfd seals/digest (`input_tool.py:106-138`).
- The independent entry is `_watchdog_entry(owner_pid, owner_start, read_fd, interval, release_command, release_env, write_fd=None, release_fd=None, ready_fd=None, release_spec=None, ack_fd=None)` at `guardian.py:176-188`. `T` carries exact `groups/keys/buttons`, is ACKed, and releases exact items on owner loss (`guardian.py:282-379`). The native slice does not implement the helper.

## Real contract gaps

- R3 requires a distinct deferred bootstrap request/method but gives no exact command name or complete request keys. Recovery begin/complete/cancel have fixed names but no exact argument sets. Choose closed shapes once, enforce exact sets, and pin them in native tests; accept no aliases.
- `profileFingerprint` has no current producer/definition. `_loaded_config_semantic_sha256` is a whole-config hash, not a named profile fingerprint. `ownerPid/ownerProcessStart` exist only as Guardian private fields (`guardian.py:516-524`). Define one deterministic native-slice derivation for each; do not silently relabel the config hash or treat private attributes as an already-defined contract.
