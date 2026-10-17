# Session recovery producer/consumer contract

Status: READY — implemented by the controller and journal owners.

Owner: recovery/transaction worker. Consumer: daemon/operator-wait worker.
The source fences remain disjoint. The daemon must use these public controller
boundaries and must not infer completion from a missing UID or from a generic
empty observation.

## Restart reconciliation

The public entry point is
`Controller.resolve_restart_intent(...)` (an alias of
`Controller.reconcile_restart(...)`). It is a read-only game observation
boundary and accepts the controller admission fence:

```python
controller.reconcile_restart(
    *,
    observed_boot: str,
    observed_uid: str,
    uploaded_ids: set[str] | frozenset[str],
    data_ack_ids: set[str] | frozenset[str],
    loaded_ids: set[str] | frozenset[str],
    pending_ids: set[str] | frozenset[str],
    scanner_phase: str | None | object,
    scanner_idle: bool,
    stable_scan_ids: set[str] | frozenset[str] | None,
    stable_sweep_ids: set[str] | frozenset[str] | None,
    loaded_uid: str,
    stable_format2_uid: str,
    stable_format2_evidence: SweepEvidence | None,
    stable_format2_verified: bool,
    stable_files_complete: bool,
    observed_scene: str,
    stable_saved_uid: str,
    stable_upload_timestamp: int,
    stable_data_ack_uid: str,
    stable_companion_uploaded_uid: str,
    loaded_at: int,
    loaded_boot: str,
    loaded_sequence: int,
    observed_modal: str,
    observed_character: str,
    observed_ah_open: bool | None,
    selected_arthur: bool | None,
    fence_armed: bool | None,
    action_postcondition: bool | None,
    expected_generation: int | None,
    expected_state: ControllerState | str | set[ControllerState | str] | None,
    fence: ObservationFence | None,
) -> ControllerStatus
```

The daemon must pass the actual stable file parse result as one complete
`SweepEvidence` object. `stable_format2_uid`, `stable_saved_uid`, the evidence
UID, all queue IDs, and every publication UID must agree exactly. `loaded_at`
and `loaded_sequence` are positive integers, `loaded_boot` is a nonempty string,
and the recovered load boot must equal the fresh `observed_boot`, which must be
a boot change from the persisted frame. Missing or malformed proof keeps the
original intent in `RECONCILE`; it is never treated as completion.

The daemon must capture the actual pre-effect boot B0 at the reload dispatch
boundary: `set_action_intent`/dispatch records the current frame when present,
and `expect_boot(boot=B0)` records the explicit reload expectation before any
post-effect frame is accepted. The durable `current.restartReferenceBoot`
survives pause, restart, and the first post-effect frame; the controller also
persists that first observed B1 so a later B2 boot is rejected. For an
uncertain `save_reload`, `ack_reload`, or `enter_world` intent only,
`Controller.observe_frame(...)` admits exactly one boot transition from B0.
A same-boot or second boot transition, an old boot used as a reload completion
witness, or a boot change for any other intent is rejected or remains
unresolved. When character select has no Agent boot, `enter_world` accepts the
first nonempty B1 with an empty B0; a persisted nonempty B0 still requires a
different boot. Reload resolution compares against `restartReferenceBoot`, so
observing the new frame first cannot erase the required boot-change proof.

The result for each persisted action is explicit:

| ActionKind | Required positive observation | Result |
| --- | --- | --- |
| `scan` | ready/scheduled scanner, idle, recognized scene, complete stable files, stable format-2 verification, and full evidence whose UID is the exact observed stable UID, whose `startedAt` equals the persisted dispatch start, and which differs from the prior checkpoint UID | Sets `resumeState=QUIET_SAVE`, binds the new UID, creates a fresh `save_reload` intent, and enters the calibration gate. No scan is replayed and no UID is required at dispatch. |
| `save_reload` | changed boot, exact observed UID, complete stable files, exact stable UID fields and full `SweepEvidence` | Sets `resumeState=UPLOAD_WAIT`, creates `upload_wait`, and enters the calibration gate. |
| `upload_wait` | exact uploaded/Data IDs, exact companion UID, upload timestamp within the finished-at deadline, and the same full stable evidence | Sets `resumeState=ACK_RELOAD_SENT`, creates `ack_reload`, and enters the calibration gate. |
| `ack_reload` | exact uploaded/Data/companion/loaded IDs, no pending UID, complete stable files, full stable evidence, publication/load times, fresh loaded boot and positive sequence | Reconstructs full evidence, enters temporary `QUALIFY_PENDING`, calls qualification exactly once, and returns the authorized terminal result. A disk-only fresh owner parks a completed `REOPEN`/cleanup result in `PAUSED` with that terminal state in `resumeState`; it never returns `REOPEN` before qualification. |
| `logout` | `observed_scene="character_select"`, `stable_files_complete=True`, and empty stable scan, sweep and pending queues | Completes as `STOPPED` with `completed_at_character_select`; no Agent boot, scanner phase or calibration fact is required. |
| `open_ah` | Trusted fresh named capture with `observed_scene="auction_house"`, `observed_ah_open=True`, and `action_postcondition=True`; the current boot may remain unchanged | Clears the intent and enters the calibration gate. |
| `dismiss_disconnect` | Trusted fresh named capture with `observed_scene="game_client"`, canonical `observed_modal="none"`, and `action_postcondition=True`; no Agent boot is required at menu | Clears the intent and enters the calibration gate. |
| `reconnect_game` | Trusted fresh named capture with `observed_scene="character_select"` and `action_postcondition=True`; no Agent boot is required at menu | Clears the intent and enters the calibration gate. |
| `select_arthur` | Trusted fresh named capture with `action_postcondition=True` and `observed_scene="arthur_selected"`, or character-select with `selected_arthur=True`; no Agent boot is required at menu | Clears the intent and enters the calibration gate. |
| `enter_world` | Trusted fresh Agent/world capture with `observed_scene="world"`, a nonempty fresh boot, and `action_postcondition=True` | Clears the intent and enters the calibration gate with `resumeState=READY`. |
| `pre_logout_fence` | complete stable scanner/file facts and `fence_armed=True` | Clears the old fence intent and enters the calibration gate for a fresh owner. |
| `stop` | persisted `stopRequested=True` | Resolves as `STOPPED` without dispatching another action. |

An empty stable file set for `save_reload`, `upload_wait`, or `ack_reload` is
resolved only as a durable rejected outcome (`BLOCKED`, with an explicit
reason and archived run/evidence/acknowledgement records). Other incomplete
observations remain unresolved. The controller validates all UID collections
as string sets before using them.

A dispatched `scan` observed at scanner `ready` with stable complete files and
both stable scan and sweep queues empty is a truthful rejected `scan_noop`
outcome. It has no fabricated UID, format-2 evidence, sweep, or accepted count,
clears the dispatch intent, and records the exact ready-empty reason. Incomplete
or unknown observations retain the original intent for a later fresh observation.
The public `begin_scan(...)` transition preserves an existing dispatched
`scan` intent, result, deadline, and attempt created by the daemon command
boundary; it does not mint a second scan attempt before this reconciliation.

## Normal acknowledgement completion

`ack_reload_complete(...)` requires `pending_ids`, exact `loaded_uid`, positive
`loaded_at`, and the loaded `boot` and `sequence`. When boot/sequence are
omitted by a caller, the method uses the already observed current frame; those
values must still match that frame. A supplied boot or sequence that differs
from the observed frame is rejected. The method persists:

```text
ackLoadedUID / loadedUID
ackLoadedAt
ackLoadedBoot
ackLoadedSequence
```

`record_ack_publication(...)` requires exact `uid == companion_uid == data_uid`
and a publication time at or after the exact upload timestamp. The accepted
qualification archive binds these four top-level identities:

```text
companionUploadedUID == dataAckUID == loadedUID == evidenceUID == uid
```

An outcome that cannot prove this chain is archived as `qualification="rejected"`
with `evidenceUID` left empty; it is never counted as accepted.

## Durable qualification retry

The durable retry boundary is the public controller method
`Controller.retry_pending_qualification(...)`, used after a recovered or
normal acknowledgement has staged its complete proof:

```python
controller.retry_pending_qualification(
    *,
    expected_generation: int | None = None,
    expected_state: ControllerState | str | set[ControllerState | str] | None = None,
    fence: ObservationFence | None = None,
) -> ControllerStatus
```

Before changing the outcome state or starting the archive transaction,
`qualify(...)` and recovered `ack_reload` reconciliation persist a
`QUALIFY_PENDING` checkpoint. Its top-level `qualificationPending` value
contains `startedAt`, the complete serialized `SweepEvidence` (including
`payload`, `itemEvidence`, `ownedRows`, `queryTimes`, `rowKinds`, envelope,
UID and row counts), and the complete publication witness metadata. The
checkpoint therefore contains the loaded UID, load time, fresh load boot and
positive load sequence already bound to the evidence UID and companion/Data
UID. A failed first `.pending` marker write leaves this prior checkpoint
durable; it does not use a second writer or a caller-held evidence object.

A fresh `Controller` reads that checkpoint from the journal and the daemon
retries with `retry_pending_qualification()` without supplying old records or
game observations. The controller reconstructs and revalidates the strict
evidence and witness chain, then consumes the existing checkpoint directly for
the normal single archive transaction; retry does not restage or rewrite that
checkpoint before publication. Success clears `qualificationPending` and creates exactly one
accepted or rejected outcome. A disk-only fresh owner parks a completed
terminal result in `PAUSED` with that terminal state in `resumeState` and
requires explicit `resume()` plus new native/input gates before any reopen or
logout input; same-owner ordinary qualification still returns its authorized
`REOPEN`/cleanup state. Reopening or pausing after success preserves the
archive and counters and cannot qualify the outcome a second time. A missing,
malformed, or mismatched pending proof is rejected as an unrecoverable cycle
with a durable rejected outcome.

If the operator pauses while `state=QUALIFY_PENDING`, the controller persists
`resumeState=QUALIFY_PENDING` and the complete pending proof. Explicit
`resume()` runs the normal live calibration/re-arm path (or enters the fresh
native/input gates for a new owner) before entering `RECONCILE` with that
resume state. `reconcile(identity_ok=True)` then restores
`QUALIFY_PENDING` without another input action or demoting the checkpoint to
`WAIT_DUE`; the next public retry consumes the same proof exactly once. A
paused owner cannot retry directly while its guardian is revoked.

Before any accepted, rejected, or cadence result mutates counters/state, the
controller writes the complete `QUALIFY_PENDING` checkpoint. If the pending
marker, manifest, artifact, or final checkpoint write fails, the live owner
restores that exact staged state and its durable checkpoint; the normal
`block()`/error path retains `QUALIFY_PENDING` instead of saving partial
counters. The same owner or a fresh owner can call
`retry_pending_qualification()` once, without a held evidence object. The
transaction identity and first immutable checkpoint remain authoritative on
retries, so later wall-clock fields cannot create a conflicting payload.

## Durable outcome transaction and replay

`Journal.append_archive_bundle(records, checkpoint=...)` assigns a strictly
monotonic `commitSequence`. It writes one immutable pending marker under
`.<journal>.archives/.pending/` before the immutable manifest under
`.bundles/`, then repairs all per-kind artifacts and applies the checkpoint in
one bounded journal write. Archive counters are derived from the artifacts and
cannot be rolled back by a stale/default checkpoint. A pending marker remains
safe to replay after successful application.

`Journal.replay_archive_bundles()` reads pending and manifest bundles, validates
the exact outcome identity and payload, sorts by `commitSequence` (then stable
filename), repairs artifacts idempotently, and applies only checkpoints with a
strictly newer commit sequence than the live journal. An equal-sequence replay
repairs missing artifacts/counters while preserving a later pause/stop
checkpoint written after the outcome. A second replay leaves archive counts,
payloads, qualification counters and controller state unchanged. Conflicting
payloads for one outcome ID raise `JournalError` without mutating the existing
archive.

If the first pending-marker write fails, no transaction checkpoint is advanced:
the prior durable `QUALIFY_PENDING` checkpoint remains intact and the fresh
owner retries through `retry_pending_qualification()` after restart. The retry
consumes that checkpoint without a replacement journal write before the archive
attempt. There is
no second writer or alternate marker schema. If manifest creation, an archive
artifact write, or the checkpoint write fails after the marker exists, the
marker and manifest remain the retry path. Startup constructs a fresh
`Controller`, which replays before reading its live checkpoint, so
accepted/rejected publication can finish without replaying game input.
Replaying two chronological outcomes preserves the later checkpoint even when
their content hashes sort in reverse lexical order, and preserves a later
pause/stop at equal commit sequence.

## Consumer changes

The daemon must pass the strict fields above from its stable SavedVariables,
companion, Data.lua and fresh frame observations. In particular, recovered
`ack_reload` calls must provide `stable_format2_evidence`,
`stable_companion_uploaded_uid`, `loaded_uid`, `loaded_at`, `loaded_boot` and
`loaded_sequence`; the controller performs qualification internally and the
daemon must not call a second qualification or skip directly from recovery to
`REOPEN`.

## Verification

The combined authorized command passed 96 tests:

```text
uv run pytest tests/test_session_transitions.py tests/test_session.py \
  tests/test_session_evidence.py tests/test_session_regressions.py -q \
  -W error::pytest.PytestUnhandledThreadExceptionWarning \
  -W error::pytest.PytestUnraisableExceptionWarning \
  -W error::DeprecationWarning:multiprocessing.popen_fork
```

`tests/test_session_runtime.py::test_runtime_qualification_retry_journal_error_preserves_checkpoint`
also passed with the same three warning filters. Ruff format/check and `uv run
python -m compileall` pass for the owned controller, journal, and authorized
transition/regression test files. The known protected pytest temporary-directory
cleanup warnings remain unrelated and were left untouched.

The final integration subset for dispatched scan-attempt preservation,
post-restart boot ordering, and the daemon durable-empty-facts path passed 27
tests: the transition neighbor run passed 26 tests, and the runtime
durable-empty-facts regression passed one test. Ruff format/check, compileall,
and owned diff checks pass after this integration correction.
