# Native construction: daemon and controller implementation

Status: offline slice prepared; implementation starts only after the frozen final addon obtains Sol and actual Opus READY. Root owns promotion, deployment and git. No live input or calibration is released here.

Read the frozen Stage B R3 plan, closure amendment and native-entry-map in full. The closure overrides conflicting older R3 details (fixed recover command, complete predecessor table, seven-second reserve, durable B0). Preserve all their unchanged invariants. Implement against accepted main after addon promotion in a separate worktree; do not edit any frozen tree.

## Scope and sequence

Own only src/crowley/session/controller.py, daemon.py, cli.py and tests/test_session_native.py, test_session_native_regressions.py, test_session_transitions.py. No other source, addon, config, private helper, guardian, driver, calibration, protocol, service, GUI, git commit/reset/stash/revert is allowed. Source dependencies are read-only. Order: durable controller checkpoint/rebind; closed CLI/IPC; one reservation owner/guards; deferred provider/handshake/finalize; recovery/revocation; production composition tests. Do not leave stubs or add generic input execution.

## Concrete interface decisions

IPC command values use underscores; CLI uses matching hyphens. Exact key sets are closed:

- native_construction_prepare and native_construction_control_preflight: command, generation.
- native_construction_bootstrap: command, generation, reservationId, expectedConstructorBoot. This is distinct from unchanged native_bootstrap.
- native_construction_recheck and native_construction_finalize_admit: command, generation, reservationId.
- native_construction_recovery_begin: command, generation, reservationId. An empty string is allowed ONLY when there is no process-local reservation and the durable checkpoint authorizes restart recovery; otherwise it must name the existing preflight reservation for atomic handoff. Return a new recovery reservationId so old preflight inputs cannot be replayed.
- native_construction_recovery_complete and native_construction_recovery_cancel: command, generation, reservationId. Cancel may revoke a named prepare/preflight/recovery record; it never clears durable B0. No token or caller-provided boot is accepted for recovery.

Every generation is a positive non-bool int, reservationId is a bounded nonempty opaque string except the one explicit recovery-begin empty case, and expectedConstructorBoot must exactly echo the daemon-derived value. Register real argparse options --generation, --reservation-id and --expected-constructor-boot as applicable; recovery-begin defaults reservation-id to the explicit empty string. No aliases or arbitrary kwargs.

Private successful replies wrap the exact canonical fourteen-field record under reservation. Additional operational data belongs under handshake, never as reservation aliases. Recheck returns this same record plus the strict current handshake and native monotonic observation time; it runs all current ownership/generation/identity/profile/lease/expiry checks and performs no input. Public status must not leak durable B0 or the reservation. Existing legacy public handshake semantics remain unchanged. A helper can use these closed replies for every future pre-input boundary without reading daemon private attributes.

Define profileFingerprint once: SHA256 of UTF-8 json.dumps(_canonical_semantic_value(asdict(driver.profile)), sort_keys=True, separators=(comma,colon), allow_nan=False). Use actual comma/colon JSON separators. It is not the whole config semantic hash. ownerPid is os.getpid(); ownerProcessStart is existing module-level crowley.session.driver._proc_start(ownerPid) (import that function; it is not a DesktopDriver method), preserving its string type. identityFingerprint is the freshly resolved WindowIdentity fingerprint. Other canonical fields derive from the real Guardian lease/armed/generation, not guessed attributes. Reuse cryptographically random bounded process-local IDs.

All reservations have finite native-clock expiry. Preparation/preflight/recovery use the existing reload_deadline_seconds bound. The atomic bootstrap consume may bind a finite operation bound derived from the existing native stage envelope; state and document that derivation in the completion report. Never extend any existing individual provider, freshness, release, click or finalize deadline, or refresh expiry merely because recheck polls. Expiry always revokes local admission/ticket and preserves recovery-required B0. Closure admission/state invariants take precedence over convenience.

The controller-owned closed six-field schema1 checkpoint survives every _save and restart. Invalid persisted shapes fail closed and must not silently disappear. Closed rebind validates reason/state/generation plus frame trio and preserves controller state/generation; no generic setter or IPC rebind. Recovery-complete commits a new ordinary boot and clears the checkpoint only after strict proof; explicit existing resume remains a separate owner action. Finalize preserves durable B0 for later ordinary recovery.

One construction lock owns reservation transitions, admission of bootstrap/calibration/interaction/diagnostic/tickets and recovery. Integrate real competing entry points rather than only testing private predicates. Never hold controller mutex during capture/waits. Check generation/identity/lease/profile both before and after blocking boundaries. Arrange lock order explicitly to avoid pause deadlocks. Revocation must preserve first causal failure and independent Guardian release behavior.

## Acceptance

Cover every requirement in the closure native-slice section through public dispatch/parser and the real daemon runner callbacks. Tests may inject offline clocks, captures, identity and meters, but must call the production composition instead of manually advancing private handshake states as proof. Demonstrate legacy compatibility; all twelve predecessors and wrong edges; post-reset sealed absence with deleted PNG/retained metadata; exact five-second and provider/constructor/finalize boundaries; no-attempt-per-generation admission; reservation races/handoff/drift/expiry/cancel/shutdown; daemon restart with durable B0; terminal-error pause; all three recovery begin cases; newer ordinary unarmed completion; both durable boot rebinds plus observe_frame acceptance and unrelated boot refusal after fresh controller reconstruction. No live desktop in tests.

Run uv run pytest -q tests/test_session_native.py tests/test_session_native_regressions.py tests/test_session_transitions.py --maxfail=1; scoped ruff check and format --check on the six owned files; python3 -m compileall -q on them; git diff --check. Root independently reruns checks then Sol and actual Opus review. Freeze exact six-file SHA256 map and base commit; report real output, any incomplete requirements and chosen finite operation bound. DONE only when complete. Keep progress reports concise at substantive milestones; take the whole bounded task without per-function permission requests.
