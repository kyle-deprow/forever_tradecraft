"""Deterministic repeating-session state machine."""

from __future__ import annotations

import copy
import hashlib
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from .driver import DesktopDriver, DriverError
from .evidence import BASELINE_MEDIAN_SECONDS, SweepEvidence
from .journal import Journal, JournalError


class _ReadOnlyDriver:
    """No desktop lease or input side effect for offline ``status``."""

    class _Guardian:
        generation = 0

        def revoke(self, reason: str) -> int:
            return 0

    guardian = _Guardian()

    def revoke(self, reason: str) -> None:
        return None


class ControllerState(StrEnum):
    STOPPED = "STOPPED"
    NATIVE_CALIBRATION = "NATIVE_CALIBRATION"
    INPUT_CALIBRATION = "INPUT_CALIBRATION"
    ARMED = "ARMED"
    RECONCILE = "RECONCILE"
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    READY = "READY"
    WAIT_DUE = "WAIT_DUE"
    SCANNING = "SCANNING"
    QUIET_SAVE = "QUIET_SAVE"
    SAVE_RELOAD_SENT = "SAVE_RELOAD_SENT"
    SAVE_RELOAD_WAIT = "SAVE_RELOAD_WAIT"
    UPLOAD_WAIT = "UPLOAD_WAIT"
    ACK_RELOAD_SENT = "ACK_RELOAD_SENT"
    ACK_RELOAD_WAIT = "ACK_RELOAD_WAIT"
    QUALIFY_PENDING = "QUALIFY_PENDING"
    REOPEN = "REOPEN"
    DISK_CLEANUP_SENT = "DISK_CLEANUP_SENT"
    DISK_CLEANUP_WAIT = "DISK_CLEANUP_WAIT"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"


class SessionMode(StrEnum):
    REPEAT = "repeat"
    VALIDATION = "validation"
    INTERACTION = "interaction"


class ActionKind(StrEnum):
    """Canonical external effect identities persisted in the journal."""

    SCAN = "scan"
    SAVE_RELOAD = "save_reload"
    UPLOAD_WAIT = "upload_wait"
    ACK_RELOAD = "ack_reload"
    LOGOUT = "logout"
    OPEN_AH = "open_ah"
    DISMISS_DISCONNECT = "dismiss_disconnect"
    RECONNECT_GAME = "reconnect_game"
    SELECT_ARTHUR = "select_arthur"
    ENTER_WORLD = "enter_world"
    PRE_LOGOUT_FENCE = "pre_logout_fence"
    STOP = "stop"


@dataclass(frozen=True)
class ActionIntent:
    """The one identity shared by preparation, dispatch and observation."""

    kind: ActionKind
    attempt: int
    deadline_at: int


_ACTION_ALIASES = {
    "/crowley scan": ActionKind.SCAN,
    "/reload": ActionKind.SAVE_RELOAD,
    "/logout": ActionKind.LOGOUT,
}

_SCANNER_PHASE_UNSET = object()

_NATIVE_CONSTRUCTION_CHECKPOINT_KEYS = frozenset(
    {"schema", "B0", "expectedConstructorBoot", "ownerGeneration", "kind", "phase"}
)
_NATIVE_CONSTRUCTION_KINDS = frozenset({"measure", "preflight"})
_NATIVE_CONSTRUCTION_PHASES = frozenset({"prepared", "recovery_required"})


def _valid_native_construction_checkpoint(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != _NATIVE_CONSTRUCTION_CHECKPOINT_KEYS:
        return False
    schema = value.get("schema")
    if isinstance(schema, bool) or not isinstance(schema, int) or schema != 1:
        return False
    b0 = value.get("B0")
    expected = value.get("expectedConstructorBoot")
    try:
        b0_size = len(b0.encode("utf-8")) if isinstance(b0, str) else -1
        expected_size = len(expected.encode("utf-8")) if isinstance(expected, str) else -1
    except UnicodeError:
        return False
    if (
        not isinstance(b0, str)
        or not b0
        or b0.startswith("native-construction:")
        or b0_size > 64
        or not isinstance(expected, str)
        or expected != f"native-construction:{b0}"
        or expected_size > 96
    ):
        return False
    generation = value.get("ownerGeneration")
    kind = value.get("kind")
    phase = value.get("phase")
    return (
        isinstance(generation, int)
        and not isinstance(generation, bool)
        and generation > 0
        and isinstance(kind, str)
        and kind in _NATIVE_CONSTRUCTION_KINDS
        and isinstance(phase, str)
        and phase in _NATIVE_CONSTRUCTION_PHASES
    )


def _action_kind(action: str, *, acknowledgement: bool = False) -> ActionKind:
    if acknowledgement and action in {"/reload", "save_reload"}:
        return ActionKind.ACK_RELOAD
    try:
        return ActionKind(action)
    except ValueError:
        try:
            return _ACTION_ALIASES[action]
        except KeyError as exc:
            raise ValueError(f"unknown action intent {action!r}") from exc


@dataclass(frozen=True)
class ControllerStatus:
    state: ControllerState
    mode: SessionMode
    generation: int
    lease_generation: int
    stop_requested: bool
    closeout_requested: bool
    streak: int
    blocker: str
    last_uid: str
    started_at: int = 0
    expected_boot: str = ""
    action_intent: str = ""
    deadline_at: int = 0


@dataclass(frozen=True)
class ObservationFence:
    """Admission token captured before daemon I/O.

    A daemon worker must carry this token through file reads, decoding, and
    model work.  The controller admits the result only when both the lease
    generation and the expected state still match atomically under its lock.
    """

    generation: int
    state: ControllerState
    action_attempt: int = 0


class Controller:
    """The controller owns timing and durable intent, never scan serialization."""

    def __init__(
        self,
        journal: Journal | str | Path,
        *,
        driver: DesktopDriver | None = None,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], int] = lambda: int(time.time()),
        cadence_seconds: int = 900,
        sweep_cap_seconds: int = 600,
        reload_deadline_seconds: int = 45,
        upload_deadline_seconds: int = 60,
        ack_deadline_seconds: int = 60,
        recover_on_restart: bool = True,
    ):
        self.journal = journal if isinstance(journal, Journal) else Journal(journal)
        self.driver = driver or (DesktopDriver() if recover_on_restart else _ReadOnlyDriver())
        self.clock = clock
        self.wall_clock = wall_clock
        self.cadence_seconds = cadence_seconds
        self.sweep_cap_seconds = sweep_cap_seconds
        self.reload_deadline_seconds = reload_deadline_seconds
        self.upload_deadline_seconds = upload_deadline_seconds
        self.ack_deadline_seconds = ack_deadline_seconds
        # A fresh owner must finish any manifest that survived a publication
        # or checkpoint failure before interpreting the live checkpoint.
        self.journal.replay_archive_bundles()
        journal_was_present = self.journal.path.exists()
        value = self.journal.read()
        native_key_present = "nativeConstruction" in value
        stored_native_construction = value.get("nativeConstruction")
        if not native_key_present:
            self._native_construction: dict[str, Any] | None = None
            self._native_construction_valid = True
            self._native_construction_raw: Any = None
        elif stored_native_construction is None:
            # A present JSON null is evidence of a malformed checkpoint, not
            # the same thing as an omitted checkpoint.  Preserve it verbatim
            # so a restart cannot turn an invalid durable state into absence.
            self._native_construction = None
            self._native_construction_valid = False
            self._native_construction_raw = None
        elif _valid_native_construction_checkpoint(stored_native_construction):
            self._native_construction = copy.deepcopy(stored_native_construction)
            self._native_construction_valid = True
            self._native_construction_raw = None
        else:
            # Preserve malformed durable state verbatim.  A fresh owner must
            # fail closed and recovery may inspect it, but ordinary checkpoint
            # writes must never silently repair or erase the evidence.
            self._native_construction = None
            self._native_construction_valid = False
            self._native_construction_raw = copy.deepcopy(stored_native_construction)
        self._state = ControllerState(value.get("state", "STOPPED"))
        self._mode = SessionMode(value.get("mode", "repeat"))
        self._generation = int(value.get("generation", 0))
        self._lease_generation = int(value.get("leaseGeneration", 0))
        self._stop_requested = bool(value.get("stopRequested", False))
        self._closeout_requested = bool(value.get("closeoutRequested", False))
        self._blocker = str(value.get("blocker", ""))
        self._native_calibrated = bool(value.get("nativeCalibration", False))
        self._input_calibrated = bool(value.get("inputCalibration", False))
        stored_calibration = value.get("calibrationEvidence", {})
        self._calibration_evidence: dict[str, Any] = (
            stored_calibration if isinstance(stored_calibration, dict) else {}
        )
        stored_calibration_history = value.get("calibrationHistory", [])
        self._calibration_history: list[dict[str, Any]] = (
            [item for item in stored_calibration_history if isinstance(item, dict)][-20:]
            if isinstance(stored_calibration_history, list)
            else []
        )
        self._calibration_invalidated_reason = str(value.get("calibrationInvalidated", ""))
        stored_history = value.get("history", [])
        self._history: list[dict[str, Any]] = (
            [item for item in stored_history if isinstance(item, dict)][-200:]
            if isinstance(stored_history, list)
            else []
        )
        self._restart_uncertain = bool(value.get("restartUncertain", False))
        self._reconciliation_required = bool(value.get("reconciliationRequired", False))
        # A live calibration record is intentionally process-local.  It binds
        # the armed lease to the XInput hierarchy and target identity; after a
        # restart the record cannot be reconstructed from a journal boolean.
        self._input_evidence: Any | None = None
        qualification = value.get("qualification", {})
        self._streak = int(qualification.get("streak", 0))
        self._accepted = list(qualification.get("accepted", []))
        stored_total_accepted = qualification.get("totalAccepted", len(self._accepted))
        self._total_accepted = (
            int(stored_total_accepted)
            if isinstance(stored_total_accepted, int)
            and not isinstance(stored_total_accepted, bool)
            and stored_total_accepted >= len(self._accepted)
            else len(self._accepted)
        )
        seed = qualification.get("cadenceSeedStart")
        self._cadence_seed_start = int(seed) if isinstance(seed, int) and not isinstance(seed, bool) else None
        current = value.get("current", {})
        current_uid = str(current.get("uid", ""))
        self._pending = bool(current.get("pending", False))
        self._last_uid = current_uid or (self._accepted[-1].get("uid", "") if self._accepted else "")
        self._started_at = int(current.get("startedAt", 0))
        self._expected_boot = str(current.get("expectedBoot", ""))
        raw_action = str(current.get("action", ""))
        # The daemon and controller now share canonical IDs.  A literal slash
        # command can only be observed in an interrupted pre-round journal;
        # normalize it at the boundary before any recovery decision.
        try:
            self._action_intent = _action_kind(raw_action).value if raw_action else ""
        except ValueError:
            self._action_intent = raw_action
        self._action_attempt = int(current.get("actionAttempt", 0))
        self._action_result = str(current.get("actionResult", ""))
        self._action_started_at = int(current.get("actionStartedAt", 0))
        self._frame_boot = str(current.get("frameBoot", ""))
        self._frame_sequence = int(current.get("frameSequence", 0))
        self._frame_crc32 = int(current.get("frameCrc32", 0))
        self._restart_reference_boot = str(current.get("restartReferenceBoot", ""))
        self._restart_observed_boot = str(current.get("restartObservedBoot", ""))
        self._reload_boot = str(current.get("reloadBoot", ""))
        self._deadline_at = int(current.get("deadlineAt", 0))
        self._evidence_meta: dict[str, Any] = current.get("evidence", {})
        stored_qualification_pending = value.get("qualificationPending")
        self._qualification_pending: dict[str, Any] | None = (
            copy.deepcopy(stored_qualification_pending)
            if isinstance(stored_qualification_pending, dict)
            else None
        )
        recovery_attempts = value.get("recoveryAttempts", 0)
        recovery_actions = value.get("recoveryActions", [])
        self._recovery_attempts = int(recovery_attempts) if isinstance(recovery_attempts, int) else 0
        self._recovery_actions = (
            {item for item in recovery_actions if isinstance(item, str)}
            if isinstance(recovery_actions, list)
            else set()
        )
        self._deadline = (
            self.clock() + max(0, self._deadline_at - self.wall_clock()) if self._deadline_at else 0.0
        )
        self._fresh_owner = False
        self._mutex = threading.RLock()
        self._guardian_callback_active = False
        self._planned_revoke = False
        guardian_callback = getattr(getattr(self.driver, "guardian", None), "on_revoke", None)
        if callable(guardian_callback):
            guardian_callback(lambda reason, _generation: self._on_guardian_revocation(reason))
        self._resume_state = ControllerState(value.get("resumeState", self._state.value))
        calibration_was_invalidated = False
        if recover_on_restart and (
            self._native_calibrated
            or self._input_calibrated
            or self._calibration_evidence
            or self._calibration_history
        ):
            # Calibration booleans and serialized proof are audit evidence only.
            # A new controller process cannot reconstruct the private seal or
            # bind it to the current game PID/boot/display.  Same-process
            # pause/resume retains ``_input_evidence`` below; construction of a
            # new Controller always requires both live gates again.
            self._native_calibrated = False
            self._input_calibrated = False
            self._calibration_invalidated_reason = "process restart invalidated live calibration evidence"
            calibration_was_invalidated = True
        restart_epoch_advanced = False
        if recover_on_restart and journal_was_present:
            # A fresh controller process owns a new IPC epoch.  Persisted
            # generations are audit data only: stale daemon work from the
            # previous process must fail admission even when the durable
            # state is already PAUSED, BLOCKED, or STOPPED.
            self._generation += 1
            restart_epoch_advanced = True
            self._fresh_owner = True
        restartable_states = {
            ControllerState.STOPPED,
            ControllerState.PAUSED,
            ControllerState.BLOCKED,
            ControllerState.QUALIFY_PENDING,
        }
        if recover_on_restart and self._state not in restartable_states:
            self._resume_state = self._state
            self._restart_uncertain = bool(
                self._action_intent and self._action_result not in {"", "complete", "abandoned_after_restart"}
            )
            self._input_evidence = None
            self._state = ControllerState.PAUSED
            self._blocker = (
                "process restart with uncertain action; fresh observation required"
                if self._restart_uncertain
                else "process restart; explicit resume required"
            )
            self._save(last_action="restart_pause")
        elif calibration_was_invalidated:
            # Preserve the durable PAUSED/BLOCKED/STOPPED checkpoint while
            # recording that its old calibration booleans are no longer live.
            self._save(last_action="restart_invalidate_calibration")
        elif restart_epoch_advanced:
            self._save(last_action="restart_epoch")
        # Do not infer a missing reference from the current frame during
        # restart.  The dispatch/expect_boot boundary is the only honest
        # source of B0; if it was absent, a save/ack transition cannot later
        # claim a changed boot.

    def observation_fence(self) -> ObservationFence:
        """Capture the generation/state admission boundary for external I/O."""

        with self._mutex:
            return ObservationFence(self._generation, self._state, self._action_attempt)

    @staticmethod
    def _state_matches(current: ControllerState, expected: object | None) -> bool:
        if expected is None:
            return True
        if isinstance(expected, ControllerState):
            return current == expected
        if isinstance(expected, str):
            return current.value == expected
        if isinstance(expected, (set, frozenset, tuple, list)):
            return any(Controller._state_matches(current, item) for item in expected)
        return False

    def _admitted(
        self,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> bool:
        """Check a post-I/O result while ``self._mutex`` is held."""

        if fence is not None:
            if expected_generation is not None and expected_generation != fence.generation:
                return False
            if expected_state is not None and not self._state_matches(fence.state, expected_state):
                return False
            expected_generation = fence.generation
            expected_state = fence.state
            if fence.action_attempt != self._action_attempt:
                return False
        if expected_generation is not None and self._generation != expected_generation:
            return False
        return self._state_matches(self._state, expected_state)

    def admit_observation(
        self,
        fence: ObservationFence,
        *,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
    ) -> bool:
        """Public typed admission check for daemon workers.

        This method is deliberately small: callers should perform their file
        or screenshot I/O first, then call the transition method with the same
        fence.  A false result means the observation is stale and must be
        discarded without changing durable state.
        """

        with self._mutex:
            return self._admitted(
                fence=fence,
                expected_state=expected_state,
            )

    def _archive(self, kind: str, record: dict[str, Any]) -> None:
        # Keep archives separate from the bounded live checkpoint.  Archive
        # failures are real durability failures and must surface to the caller.
        self.journal.append_archive(kind, record)

    def _begin_intent(self, action: str, *, deadline_seconds: int | None = None) -> None:
        """Start a unique action attempt and clear the prior result/deadline."""

        if not action:
            raise ValueError("action intent must be nonempty")
        action = _action_kind(action).value
        self._action_attempt += 1
        self._action_intent = action
        self._action_result = "pending"
        self._restart_reference_boot = ""
        self._restart_observed_boot = ""
        self._action_started_at = self.wall_clock()
        self._deadline = 0.0
        self._deadline_at = 0
        if deadline_seconds is not None:
            self._deadline = self.clock() + max(0, deadline_seconds)
            self._deadline_at = self.wall_clock() + max(0, deadline_seconds)

    def _clear_intent(self, result: str = "complete") -> None:
        self._action_result = result
        self._action_intent = ""
        self._action_started_at = 0
        self._deadline = 0.0
        self._deadline_at = 0
        self._restart_reference_boot = ""
        self._restart_observed_boot = ""

    @classmethod
    def _bounded_evidence(cls, evidence: dict[str, Any]) -> dict[str, Any]:
        """Keep live checkpoints small while archives retain full item proof."""

        bounded: dict[str, Any] = {}
        for key, value in evidence.items():
            if key in {"itemEvidence", "ownedRows", "fullEvidence", "priorEvidence"}:
                continue
            bounded[key] = copy.deepcopy(value)
        for key in ("itemEvidence", "ownedRows"):
            value = evidence.get(key)
            if value is not None:
                bounded[f"{key}Count"] = len(value) if isinstance(value, (dict, list)) else 0
        full = evidence.get("fullEvidence")
        if isinstance(full, dict):
            bounded["fullEvidence"] = {
                key: full.get(key) for key in ("uid", "planHash", "startedAt", "finishedAt") if key in full
            }
        prior = evidence.get("priorEvidence")
        if isinstance(prior, dict):
            bounded["priorEvidence"] = cls._bounded_evidence(prior)
        return bounded

    def _dispatch_intent(self, action: str, *, deadline_seconds: int) -> None:
        """Record an external dispatch without silently creating a second attempt."""

        action = _action_kind(action).value
        if self._action_intent != action:
            self._begin_intent(action, deadline_seconds=deadline_seconds)
        elif not self._deadline_at:
            self._deadline = self.clock() + max(0, deadline_seconds)
            self._deadline_at = self.wall_clock() + max(0, deadline_seconds)
        if action in {"save_reload", "ack_reload", "enter_world"} and self._frame_boot:
            self._restart_reference_boot = self._frame_boot
        self._action_result = "dispatched"

    def _outcome_checkpoint(self) -> dict[str, Any]:
        """Return the bounded controller state committed with an outcome."""

        return {
            "schema": 1,
            "state": self._state.value,
            "mode": self._mode.value,
            "generation": self._generation,
            "leaseGeneration": self._lease_generation,
            "stopRequested": self._stop_requested,
            "closeoutRequested": self._closeout_requested,
            "restartRequiresResume": self._state
            in {ControllerState.PAUSED, ControllerState.BLOCKED, ControllerState.STOPPED},
            "blocker": self._blocker,
            "restartUncertain": self._restart_uncertain,
            "reconciliationRequired": self._reconciliation_required,
            # Qualification is deliberately staged as a full record before
            # its archive transaction.  This is the bounded controller's one
            # durable exception: a fresh owner can reconstruct the public
            # qualification call after the first pending-marker failure.
            "qualificationPending": copy.deepcopy(self._qualification_pending),
            "qualification": {
                "streak": self._streak,
                "totalAccepted": self._total_accepted,
                "cadenceSeedStart": self._cadence_seed_start,
                "accepted": [
                    {
                        **{key: copy.deepcopy(value) for key, value in accepted.items() if key != "evidence"},
                        **(
                            {"evidence": self._bounded_evidence(accepted["evidence"])}
                            if isinstance(accepted.get("evidence"), dict)
                            else {}
                        ),
                    }
                    for accepted in self._accepted
                ],
            },
            "resumeState": self._resume_state.value,
            "current": {
                "uid": self._last_uid if self._pending else "",
                "pending": self._pending,
                "startedAt": self._started_at,
                "expectedBoot": self._expected_boot,
                "action": self._action_intent,
                "actionAttempt": self._action_attempt,
                "actionResult": self._action_result,
                "actionStartedAt": self._action_started_at,
                "frameBoot": self._frame_boot,
                "frameSequence": self._frame_sequence,
                "frameCrc32": self._frame_crc32,
                "restartReferenceBoot": self._restart_reference_boot,
                "restartObservedBoot": self._restart_observed_boot,
                "reloadBoot": self._reload_boot,
                "deadlineAt": self._deadline_at,
                "evidence": self._bounded_evidence(self._evidence_meta),
            },
        }

    def _calibration_gate_state(self) -> ControllerState:
        if not self._native_calibrated:
            return ControllerState.NATIVE_CALIBRATION
        if not self._input_calibrated or self._input_evidence is None:
            return ControllerState.INPUT_CALIBRATION
        return ControllerState.ARMED

    def _archive_outcome(self, *, result: str, reason: str, kind: str = "rejected") -> None:
        """Archive a complete run outcome and its current acknowledgement witnesses."""
        if self._evidence_meta.get("outcomeArchived"):
            self._qualification_pending = None
            return
        evidence = copy.deepcopy(self._evidence_meta)
        uid = str(evidence.get("uid") or self._last_uid)
        outcome_id = hashlib.sha256(
            f"{uid}|{evidence.get('startedAt', 0)}|{result}|{reason}".encode()
        ).hexdigest()
        run = {
            "outcomeId": outcome_id,
            "uid": uid,
            "startedAt": evidence.get("startedAt", 0),
            "finishedAt": evidence.get("finishedAt", 0),
            "rowCount": evidence.get("rowCount", 0),
            "pricedRowCount": evidence.get("priced", evidence.get("pricedRowCount", 0)),
            "itemEvidence": copy.deepcopy(evidence.get("itemEvidence", {})),
            "ownedRows": copy.deepcopy(evidence.get("ownedRows", [])),
            "ownedPricedRowCount": evidence.get("ownedPricedRowCount", 0),
            "qualification": result,
            "streak": self._streak,
            "reason": reason,
            "evidence": evidence,
            "fullEvidence": copy.deepcopy(evidence.get("fullEvidence", {})),
            "uploadTimestamp": evidence.get("uploadTimestamp", 0),
            "uploadLatencySeconds": evidence.get("uploadLatencySeconds", 0),
            "ackPublicationAt": evidence.get("ackPublicationAt", 0),
            "ackPublicationLatencySeconds": evidence.get("ackPublicationLatencySeconds", 0),
            "ackLoadedAt": evidence.get("ackLoadedAt", 0),
            "loadedAt": evidence.get("ackLoadedAt", 0),
            "loadedBoot": evidence.get("ackLoadedBoot", ""),
            "loadedSequence": evidence.get("ackLoadedSequence", 0),
            "ackLatencySeconds": evidence.get("ackLatencySeconds", 0),
            "ackLoadedLatencySeconds": evidence.get("ackLoadedLatencySeconds", 0),
            "companionUploadedUID": evidence.get("atomicCompanionUploadedUid", ""),
            "dataAckUID": evidence.get("dataAckUid", ""),
            "loadedUID": evidence.get("ackLoadedUID", ""),
            "evidenceUID": evidence.get("qualifiedEvidenceUID", ""),
            "generation": self._generation,
        }
        cadence = {
            "outcomeId": outcome_id,
            "uid": uid,
            "result": result,
            "reason": reason,
            "acceptedBefore": evidence.get("acceptedBefore", self._streak),
            "streak": self._streak,
            "startedAt": evidence.get("startedAt", 0),
            "finishedAt": evidence.get("finishedAt", 0),
            "evidence": evidence,
            "generation": self._generation,
        }
        acknowledgement = {
            "outcomeId": outcome_id,
            "uid": uid,
            "result": result,
            "reason": reason,
            "uploadTimestamp": evidence.get("uploadTimestamp", 0),
            "uploadLatencySeconds": evidence.get("uploadLatencySeconds", 0),
            "ackPublicationAt": evidence.get("ackPublicationAt", 0),
            "ackPublicationLatencySeconds": evidence.get("ackPublicationLatencySeconds", 0),
            "ackLoadedAt": evidence.get("ackLoadedAt", 0),
            "loadedAt": evidence.get("ackLoadedAt", 0),
            "loadedBoot": evidence.get("ackLoadedBoot", ""),
            "loadedSequence": evidence.get("ackLoadedSequence", 0),
            "ackLatencySeconds": evidence.get("ackLatencySeconds", 0),
            "ackLoadedLatencySeconds": evidence.get("ackLoadedLatencySeconds", 0),
            "companionUploadedUID": evidence.get("atomicCompanionUploadedUid", ""),
            "dataAckUID": evidence.get("dataAckUid", ""),
            "loadedUID": evidence.get("ackLoadedUID", ""),
            "evidenceUID": evidence.get("qualifiedEvidenceUID", ""),
            "evidence": evidence,
            "generation": self._generation,
        }
        evidence_record = {
            "outcomeId": outcome_id,
            "uid": uid,
            "kind": kind,
            "result": result,
            "reason": reason,
            "generation": self._generation,
            "fullEvidence": copy.deepcopy(evidence.get("fullEvidence", {})),
            "evidence": evidence,
        }
        checkpoint = self._outcome_checkpoint()
        # The manifest checkpoint must carry the same terminal marker as the
        # archive.  If publication succeeds and the following live save
        # fails, a fresh owner must replay the committed outcome without
        # attempting a second logical result.
        checkpoint["current"]["evidence"]["outcomeArchived"] = True
        # The durable outcome is now self-contained; do not leave a full
        # retry payload in the committed checkpoint.
        checkpoint["qualificationPending"] = None
        self.journal.append_archive_bundle(
            {
                "runs": run,
                "evidence": evidence_record,
                "cadence": cadence,
                "acknowledgements": acknowledgement,
            },
            checkpoint=checkpoint,
        )
        self._evidence_meta["outcomeArchived"] = True
        self._qualification_pending = None

    def _set_format2_evidence(self, evidence: SweepEvidence) -> None:
        """Install the complete stable format-2 record for one UID."""

        envelope_id = evidence.envelope.get("id", evidence.uid)
        envelope_house = evidence.envelope.get("house", {})
        if envelope_id != evidence.uid or (
            isinstance(envelope_house, dict)
            and envelope_house.get("key")
            and envelope_house.get("key") != evidence.house
        ):
            raise DriverError("stable format-2 proof identity mismatch")
        self._evidence_meta = {
            "uid": evidence.uid,
            "startedAt": int(evidence.envelope["startedAt"]),
            "finishedAt": int(evidence.envelope["finishedAt"]),
            "planHash": evidence.plan_hash,
            "observations": evidence.observations,
            "attempted": evidence.attempted,
            "full": evidence.full,
            "bounded": evidence.bounded,
            "incomplete": evidence.incomplete,
            "unqueried": evidence.unqueried,
            "priced": evidence.priced,
            "rowCount": evidence.row_count,
            "kinds": list(evidence.kinds),
            "queryTimes": copy.deepcopy(evidence.query_times),
            "itemEvidence": copy.deepcopy(evidence.item_evidence),
            "ownedRows": copy.deepcopy(evidence.owned_rows),
            "ownedPricedRowCount": evidence.owned_priced_row_count,
            "fullEvidence": self._full_evidence_record(evidence),
            "qualification": "pending",
            "stableSavedUid": evidence.uid,
            "stableHouse": evidence.house,
            "stablePlanHash": evidence.plan_hash,
            "stableContext": copy.deepcopy(evidence.envelope.get("context", {})),
        }

    @staticmethod
    def _full_evidence_record(evidence: SweepEvidence) -> dict[str, Any]:
        """Serialize every field needed to reconstruct public qualification."""

        record = evidence.archive_record()
        record.update(
            {
                "payload": copy.deepcopy(evidence.payload),
                "stableVerified": evidence.stable_verified,
                "rowKinds": copy.deepcopy(evidence.row_kinds),
            }
        )
        return record

    @staticmethod
    def _evidence_from_record(record: dict[str, Any]) -> SweepEvidence:
        """Reconstruct a complete public ``SweepEvidence`` from a checkpoint."""

        if not isinstance(record, dict) or record.get("stableVerified") is not True:
            raise DriverError("qualification checkpoint lacks stable evidence")
        required = {
            "uid",
            "house",
            "planHash",
            "observations",
            "attempted",
            "full",
            "bounded",
            "incomplete",
            "unqueried",
            "pricedRowCount",
            "rowCount",
            "kinds",
            "queryDurations",
            "queryTimes",
            "itemEvidence",
            "ownedRows",
            "ownedPricedRowCount",
            "envelope",
            "payload",
        }
        if not required.issubset(record):
            raise DriverError("qualification checkpoint is incomplete")
        try:
            query_times = {
                str(key): (int(value[0]), int(value[1]))
                for key, value in record["queryTimes"].items()
                if isinstance(value, (list, tuple)) and len(value) == 2
            }
            if len(query_times) != len(record["queryTimes"]):
                raise ValueError("query timing evidence is malformed")
            return SweepEvidence(
                uid=str(record["uid"]),
                house=str(record["house"]),
                plan_hash=str(record["planHash"]),
                observations=int(record["observations"]),
                attempted=int(record["attempted"]),
                full=int(record["full"]),
                bounded=int(record["bounded"]),
                incomplete=int(record["incomplete"]),
                unqueried=int(record["unqueried"]),
                priced=int(record["pricedRowCount"]),
                row_count=int(record["rowCount"]),
                kinds=tuple(str(item) for item in record["kinds"]),
                query_durations=tuple(int(item) for item in record["queryDurations"]),
                envelope=copy.deepcopy(record["envelope"]),
                payload=copy.deepcopy(record["payload"]),
                stable_verified=True,
                query_times=query_times,
                row_kinds={str(key): int(value) for key, value in record.get("rowKinds", {}).items()},
                item_evidence=copy.deepcopy(record["itemEvidence"]),
                owned_rows=copy.deepcopy(record["ownedRows"]),
                owned_priced_row_count=int(record["ownedPricedRowCount"]),
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise DriverError(f"qualification checkpoint is malformed: {exc}") from exc

    def _stage_qualification_pending(self, evidence: SweepEvidence, *, started_at: int) -> None:
        """Durably stage full evidence before mutating the outcome transaction."""

        self._qualification_pending = {
            "startedAt": int(started_at),
            "evidence": self._full_evidence_record(evidence),
            "metadata": copy.deepcopy(self._evidence_meta),
        }
        self._state = ControllerState.QUALIFY_PENDING
        self._pending = True
        self._last_uid = evidence.uid
        self._save(last_action="qualification_pending")

    def _qualification_state_snapshot(self) -> dict[str, Any]:
        """Capture the exact staged state before an outcome is mutated."""

        fields = (
            "_state",
            "_resume_state",
            "_pending",
            "_last_uid",
            "_blocker",
            "_evidence_meta",
            "_qualification_pending",
            "_accepted",
            "_total_accepted",
            "_streak",
            "_cadence_seed_start",
            "_deadline",
            "_deadline_at",
            "_closeout_requested",
            "_stop_requested",
            "_action_intent",
            "_action_attempt",
            "_action_result",
            "_action_started_at",
            "_expected_boot",
            "_frame_boot",
            "_frame_sequence",
            "_frame_crc32",
            "_restart_reference_boot",
            "_restart_observed_boot",
            "_reload_boot",
            "_started_at",
            "_restart_uncertain",
            "_reconciliation_required",
            "_lease_generation",
            "_native_calibrated",
            "_input_calibrated",
            "_calibration_evidence",
            "_calibration_history",
            "_calibration_invalidated_reason",
        )
        return {field: copy.deepcopy(getattr(self, field)) for field in fields}

    def _restore_qualification_state(self, snapshot: dict[str, Any]) -> None:
        """Restore staged state after an outcome publication failure."""

        for field, value in snapshot.items():
            setattr(self, field, copy.deepcopy(value))

    def _archive_staged_outcome(
        self, snapshot: dict[str, Any], *, result: str, reason: str, kind: str
    ) -> None:
        """Publish an outcome without losing its durable staged retry state."""

        try:
            self._archive_outcome(result=result, reason=reason, kind=kind)
        except JournalError:
            self._restore_qualification_state(snapshot)
            raise

    def _park_recovered_terminal(self, status: ControllerStatus) -> ControllerStatus:
        """Require explicit resume and fresh gates after disk-only completion."""

        if not self._fresh_owner or status.state not in {
            ControllerState.REOPEN,
            ControllerState.DISK_CLEANUP_SENT,
        }:
            return status
        self._resume_state = status.state
        self._state = ControllerState.PAUSED
        self._reconciliation_required = True
        self._restart_uncertain = False
        self._blocker = "recovered outcome requires explicit resume and fresh calibration"
        self._fresh_owner = False
        self._save(last_action="recovered_outcome_requires_resume")
        return self.status()

    def _reject_unrecoverable_cycle(self, reason: str) -> ControllerStatus:
        """Persist a truthful rejected outcome when an in-flight cycle is disproved."""

        if not reason:
            raise ValueError("rejection reason must be nonempty")
        prior_state = self._qualification_state_snapshot()
        if not self._evidence_meta:
            self._evidence_meta = {
                "uid": self._last_uid,
                "startedAt": self._started_at,
                "finishedAt": 0,
                "qualification": "rejected",
            }
        else:
            self._evidence_meta["qualification"] = "rejected"
        self._evidence_meta["rejectionReason"] = reason
        self._pending = False
        self._restart_uncertain = False
        self._reconciliation_required = False
        self._blocker = reason
        self._state = ControllerState.BLOCKED
        self._clear_intent("rejected_after_restart")
        self._archive_staged_outcome(
            prior_state,
            result="rejected",
            reason=reason,
            kind="restart_rejection",
        )
        self._save(last_action="restart_rejected")
        return self.status()

    def _reject_empty_scan_attempt(self, reason: str) -> ControllerStatus:
        """Archive a dispatched scan that proved no new data was produced."""

        if not reason:
            raise ValueError("rejection reason must be nonempty")
        prior_state = self._qualification_state_snapshot()
        started_at = self._started_at
        self._evidence_meta = {
            "uid": "",
            "startedAt": started_at,
            "finishedAt": 0,
            "qualification": "rejected",
            "rejectionReason": reason,
            "attemptedAction": ActionKind.SCAN.value,
            "attemptObservation": "ready_empty_stable_queues",
        }
        self._pending = False
        self._restart_uncertain = False
        self._reconciliation_required = False
        self._blocker = reason
        self._state = ControllerState.BLOCKED
        self._resume_state = ControllerState.WAIT_DUE
        self._started_at = 0
        self._last_uid = ""
        self._clear_intent("rejected_ready_empty_scan")
        self._archive_staged_outcome(prior_state, result="rejected", reason=reason, kind="scan_noop")
        self._save(last_action="scan_noop_rejected")
        return self.status()

    def _save(self, *, last_action: str = "") -> None:
        with self._mutex:
            if last_action and last_action not in {"frame_observed", "frame_before_reload_dispatch"}:
                self._history.append(
                    {
                        "at": self.wall_clock(),
                        "action": last_action,
                        "state": self._state.value,
                        "generation": self._generation,
                        "uid": self._last_uid,
                    }
                )
                del self._history[:-200]
            current = self.journal.read()
            current.update(
                {
                    "state": self._state.value,
                    "mode": self._mode.value,
                    "generation": self._generation,
                    "leaseGeneration": self._lease_generation,
                    "stopRequested": self._stop_requested,
                    "closeoutRequested": self._closeout_requested,
                    "restartRequiresResume": self._state
                    in {ControllerState.PAUSED, ControllerState.BLOCKED, ControllerState.STOPPED},
                    "blocker": self._blocker,
                    "nativeCalibration": self._native_calibrated,
                    "inputCalibration": self._input_calibrated,
                    "calibrationEvidence": copy.deepcopy(self._calibration_evidence),
                    "calibrationHistory": copy.deepcopy(self._calibration_history),
                    "calibrationInvalidated": self._calibration_invalidated_reason,
                    "restartUncertain": self._restart_uncertain,
                    "reconciliationRequired": self._reconciliation_required,
                    "qualificationPending": copy.deepcopy(self._qualification_pending),
                    "recoveryAttempts": self._recovery_attempts,
                    "recoveryActions": sorted(self._recovery_actions),
                    "history": copy.deepcopy(self._history),
                    "lastAction": last_action,
                    "qualification": {
                        "streak": self._streak,
                        "totalAccepted": self._total_accepted,
                        "cadenceSeedStart": self._cadence_seed_start,
                        "accepted": [
                            {
                                **{
                                    key: copy.deepcopy(value)
                                    for key, value in accepted.items()
                                    if key != "evidence"
                                },
                                **(
                                    {"evidence": self._bounded_evidence(accepted["evidence"])}
                                    if isinstance(accepted.get("evidence"), dict)
                                    else {}
                                ),
                            }
                            for accepted in self._accepted
                        ],
                        "lastAcceptedUid": self._accepted[-1].get("uid", "") if self._accepted else "",
                        "lastAcceptedStart": self._accepted[-1].get("startedAt", 0) if self._accepted else 0,
                        "lastAcceptedFinish": self._accepted[-1].get("finishedAt", 0)
                        if self._accepted
                        else 0,
                        "lastReason": self._blocker,
                        "format2Evidence": self._bounded_evidence(self._evidence_meta),
                        "history": copy.deepcopy(self._history),
                    },
                    "resumeState": self._resume_state.value,
                    "current": {
                        "uid": self._last_uid if self._pending else "",
                        "pending": self._pending,
                        "startedAt": self._started_at,
                        "expectedBoot": self._expected_boot,
                        "action": self._action_intent,
                        "actionAttempt": self._action_attempt,
                        "actionResult": self._action_result,
                        "actionStartedAt": self._action_started_at,
                        "frameBoot": self._frame_boot,
                        "frameSequence": self._frame_sequence,
                        "frameCrc32": self._frame_crc32,
                        "restartReferenceBoot": self._restart_reference_boot,
                        "restartObservedBoot": self._restart_observed_boot,
                        "reloadBoot": self._reload_boot,
                        "deadlineAt": self._deadline_at,
                        "evidence": self._bounded_evidence(self._evidence_meta),
                    },
                }
            )
            if self._native_construction_valid:
                if self._native_construction is None:
                    current.pop("nativeConstruction", None)
                else:
                    current["nativeConstruction"] = copy.deepcopy(self._native_construction)
            else:
                # Keep malformed durable state visible for recovery/audit.  It
                # is never interpreted as an admission checkpoint.
                current["nativeConstruction"] = copy.deepcopy(self._native_construction_raw)
            self.journal.write(current)

    def _invalidate_live_calibration(self, reason: str) -> None:
        """Drop reusable gate flags after a client/display/observer change."""

        self._native_calibrated = False
        self._input_calibrated = False
        self._input_evidence = None
        self._calibration_invalidated_reason = reason

    def status(self) -> ControllerStatus:
        with self._mutex:
            return ControllerStatus(
                self._state,
                self._mode,
                self._generation,
                self._lease_generation,
                self._stop_requested,
                self._closeout_requested,
                self._streak,
                self._blocker,
                self._last_uid,
                self._started_at,
                self._expected_boot,
                self._action_intent,
                self._deadline_at,
            )

    def set_action_intent(
        self,
        action: str,
        *,
        deadline_seconds: int | None = None,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        """Persist an action fence before any desktop dispatch."""

        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            canonical = _action_kind(action).value
            # Preparation and dispatch are one effect boundary.  If the
            # caller has already prepared this exact intent, retain its
            # attempt and deadline instead of minting a second reload.
            if self._action_intent != canonical:
                self._begin_intent(canonical, deadline_seconds=deadline_seconds)
            elif deadline_seconds is not None and not self._deadline_at:
                self._deadline = self.clock() + max(0, deadline_seconds)
                self._deadline_at = self.wall_clock() + max(0, deadline_seconds)
            if canonical in {"save_reload", "ack_reload", "enter_world"} and self._frame_boot:
                self._restart_reference_boot = self._frame_boot
            self._save(last_action=f"intent:{action}")
            return self.status()

    def action_result(
        self,
        result: str,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        if not result:
            raise ValueError("action result must be nonempty")
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            self._action_result = result
            self._save(last_action=f"action:{result}")
            return self.status()

    def clear_action_intent(
        self,
        result: str = "complete",
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            self._clear_intent(result)
            self._save(last_action=f"action:{result}")
            return self.status()

    def record_recovery_attempt(
        self,
        action: str,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        if not action:
            raise ValueError("recovery action must be nonempty")
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            self._recovery_attempts += 1
            self._recovery_actions.add(action)
            self._archive(
                "interventions",
                {
                    "kind": "recovery",
                    "action": action,
                    "generation": self._generation,
                    "state": self._state.value,
                },
            )
            self._save(last_action=f"recovery:{action}")
            return self.status()

    def clear_recovery_attempts(
        self,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            self._recovery_attempts = 0
            self._recovery_actions.clear()
            self._save(last_action="recovery_clear")
            return self.status()

    def record_model_proof(
        self,
        proof: dict[str, Any],
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        """Persist measured model capture/timing/acceptance proof only."""

        if not isinstance(proof, dict):
            raise ValueError("model proof must be an object")
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            clean = self._proof_record(proof)
            self._evidence_meta["modelProof"] = copy.deepcopy(clean)
            self._archive("evidence", {"kind": "model_proof", "proof": clean, "generation": self._generation})
            self._save(last_action="model_proof")
            return self.status()

    def record_anchor_proof(
        self,
        proof: dict[str, Any],
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        """Persist the identity bound anchor capture and acceptance proof."""

        if not isinstance(proof, dict):
            raise ValueError("anchor proof must be an object")
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            clean = self._proof_record(proof)
            self._evidence_meta["anchorProof"] = copy.deepcopy(clean)
            self._archive(
                "evidence", {"kind": "anchor_proof", "proof": clean, "generation": self._generation}
            )
            self._save(last_action="anchor_proof")
            return self.status()

    archive_model_proof = record_model_proof
    archive_anchor_proof = record_anchor_proof

    @staticmethod
    def _proof_record(value: dict[str, Any]) -> dict[str, Any]:
        """Copy JSON proof while excluding private seals and chat contents."""

        def clean(item: Any) -> Any:
            if isinstance(item, dict):
                return {
                    str(key): clean(child)
                    for key, child in item.items()
                    if str(key) not in {"_seal", "chatText", "chattext", "chatEdit", "text"}
                }
            if isinstance(item, (list, tuple)):
                return [clean(child) for child in item]
            if isinstance(item, (str, int, float, bool)) or item is None:
                return item
            return str(item)

        return clean(value)

    @property
    def lock(self) -> threading.RLock:
        return self._mutex

    def native_construction_checkpoint(self) -> dict[str, Any] | None:
        """Return the durable native-construction checkpoint, if valid.

        A malformed persisted record is intentionally represented as no valid
        checkpoint.  ``native_construction_checkpoint_valid`` lets the daemon
        distinguish that fail-closed state without exposing the raw record.
        """

        with self._mutex:
            return copy.deepcopy(self._native_construction) if self._native_construction_valid else None

    def native_construction_checkpoint_valid(self) -> bool:
        with self._mutex:
            return self._native_construction_valid

    def set_native_construction_checkpoint(
        self,
        checkpoint: dict[str, Any],
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
    ) -> ControllerStatus:
        if not _valid_native_construction_checkpoint(checkpoint):
            raise ValueError("native construction checkpoint is malformed")
        if expected_generation is not None and checkpoint["ownerGeneration"] != expected_generation:
            raise ValueError("native construction checkpoint generation is stale")
        with self._mutex:
            if not self._admitted(expected_generation=expected_generation, expected_state=expected_state):
                return self.status()
            self._native_construction = copy.deepcopy(checkpoint)
            self._native_construction_valid = True
            self._native_construction_raw = None
            self._save(last_action="native_construction_checkpoint")
            return self.status()

    def mark_native_construction_recovery_required(self) -> ControllerStatus:
        with self._mutex:
            if not self._native_construction_valid or self._native_construction is None:
                raise RuntimeError("native construction checkpoint is unavailable")
            checkpoint = copy.deepcopy(self._native_construction)
            checkpoint["phase"] = "recovery_required"
            self._native_construction = checkpoint
            self._save(last_action="native_construction_recovery_required")
            return self.status()

    def clear_native_construction_checkpoint(
        self,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._native_construction_valid:
                raise RuntimeError("malformed native construction checkpoint requires recovery")
            if not self._admitted(expected_generation=expected_generation, expected_state=expected_state):
                return self.status()
            self._native_construction = None
            self._native_construction_valid = True
            self._native_construction_raw = None
            self._save(last_action="native_construction_cleared")
            return self.status()

    def rebind_native_construction_frame(
        self,
        *,
        boot: str,
        sequence: int,
        crc32: int,
        reason: str,
        expected_generation: int,
        expected_state: ControllerState | str,
    ) -> ControllerStatus:
        """Persist one closed native finalize/recovery frame identity.

        This is deliberately narrower than a generic boot setter.  The daemon
        must pass the accepted frame through ``observe_frame`` immediately
        after this durable rebind, so ordinary frame churn remains fenced.
        """

        if reason not in {"native_construction_finalize", "native_construction_recovery"}:
            raise ValueError("native construction rebind reason is not allowlisted")
        expected = ControllerState(expected_state)
        required_state = (
            ControllerState.NATIVE_CALIBRATION
            if reason == "native_construction_finalize"
            else ControllerState.PAUSED
        )
        if expected is not required_state:
            raise ValueError("native construction rebind state is not allowlisted")
        if (
            not isinstance(boot, str)
            or not boot
            or len(boot.encode("utf-8")) > 96
            or isinstance(sequence, bool)
            or not isinstance(sequence, int)
            or sequence < 0
            or isinstance(crc32, bool)
            or not isinstance(crc32, int)
            or sequence > 0xFFFFFFFF
            or crc32 < 0
            or crc32 > 0xFFFFFFFF
        ):
            raise ValueError("native construction rebind frame is malformed")
        with self._mutex:
            if not self._native_construction_valid or self._native_construction is None:
                raise RuntimeError("native construction checkpoint is unavailable")
            if not self._admitted(expected_generation=expected_generation, expected_state=expected):
                return self.status()
            self._frame_boot = boot
            self._frame_sequence = sequence
            self._frame_crc32 = crc32
            self._save(last_action=f"{reason}_rebind")
            return self.status()

    def commit_native_construction_recovery(
        self,
        *,
        boot: str,
        sequence: int,
        crc32: int,
        expected_generation: int,
        expected_state: ControllerState | str = ControllerState.PAUSED,
    ) -> ControllerStatus:
        """Atomically publish a recovery frame and consume its checkpoint.

        Recovery completion must not report success after a frame rebind has
        persisted while checkpoint deletion failed.  Both mutations therefore
        share one journal write and are rolled back in memory if that write
        fails.  The daemon performs only a read-only post-proof after this
        closed commit.
        """

        expected = ControllerState(expected_state)
        if expected is not ControllerState.PAUSED:
            raise ValueError("native recovery commit requires PAUSED state")
        if (
            not isinstance(boot, str)
            or not boot
            or len(boot.encode("utf-8")) > 96
            or isinstance(sequence, bool)
            or not isinstance(sequence, int)
            or sequence < 0
            or sequence > 0xFFFFFFFF
            or isinstance(crc32, bool)
            or not isinstance(crc32, int)
            or crc32 < 0
            or crc32 > 0xFFFFFFFF
        ):
            raise ValueError("native recovery frame is malformed")
        with self._mutex:
            if not self._native_construction_valid or self._native_construction is None:
                raise RuntimeError("native construction checkpoint is unavailable")
            if self._native_construction.get("phase") != "recovery_required":
                raise RuntimeError("native recovery checkpoint is not required")
            if not self._admitted(expected_generation=expected_generation, expected_state=expected):
                return self.status()
            old_frame = (self._frame_boot, self._frame_sequence, self._frame_crc32)
            old_checkpoint = copy.deepcopy(self._native_construction)
            old_history = copy.deepcopy(self._history)
            self._frame_boot, self._frame_sequence, self._frame_crc32 = boot, sequence, crc32
            self._native_construction = None
            self._native_construction_valid = True
            self._native_construction_raw = None
            try:
                self._save(last_action="native_construction_recovery_commit")
            except Exception:
                self._frame_boot, self._frame_sequence, self._frame_crc32 = old_frame
                self._native_construction = old_checkpoint
                self._native_construction_valid = True
                self._native_construction_raw = None
                self._history = old_history
                raise
            return self.status()

    def validate_native_construction_recovery_commit(
        self,
        *,
        boot: str,
        sequence: int,
        crc32: int,
        expected_generation: int,
        expected_state: ControllerState | str = ControllerState.PAUSED,
    ) -> ControllerStatus:
        """Read-only post-proof for a closed native recovery commit.

        The durable frame/checkpoint mutation is already closed by
        ``commit_native_construction_recovery``.  This method intentionally
        performs no journal write, so a post-commit verification failure
        cannot strand a consumed checkpoint before terminal publication.
        """

        expected = ControllerState(expected_state)
        if expected is not ControllerState.PAUSED:
            raise ValueError("native recovery proof requires PAUSED state")
        with self._mutex:
            if not self._admitted(expected_generation=expected_generation, expected_state=expected):
                return self.status()
            status = self.status()
            if status.state is not expected or status.generation != expected_generation:
                return status
            if (self._frame_boot, self._frame_sequence, self._frame_crc32) != (
                boot,
                sequence,
                crc32,
            ):
                raise RuntimeError("native recovery durable frame proof changed")
            if self._native_construction is not None:
                raise RuntimeError("native recovery checkpoint remained after closed commit")
            return status

    def tick(
        self,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if (self._deadline and self.clock() >= self._deadline) or (
                self._deadline_at and self.wall_clock() >= self._deadline_at
            ):
                return self.block(f"deadline expired in {self._state.value}")
            return self.status()

    def observe_frame(
        self,
        *,
        boot: str,
        sequence: int,
        crc32: int,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        """Persist and validate one fresh decoded frame identity.

        A reload is the only operation allowed to change the boot identity.  A
        second boot during one reload wait is boot churn and blocks the session.
        """

        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if not boot or sequence < 0 or crc32 < 0:
                return self.block("malformed frame evidence")
            restart_boot_transition = (
                self._restart_uncertain
                and self._action_intent in {"save_reload", "ack_reload", "enter_world"}
                and bool(self._restart_reference_boot)
                and self._frame_boot == self._restart_reference_boot
                and boot != self._restart_reference_boot
            )
            if (
                self._frame_boot
                and self._state
                not in {
                    ControllerState.SAVE_RELOAD_SENT,
                    ControllerState.ACK_RELOAD_SENT,
                    ControllerState.SAVE_RELOAD_WAIT,
                    ControllerState.ACK_RELOAD_WAIT,
                    ControllerState.QUALIFY_PENDING,
                }
                and boot != self._frame_boot
                and not restart_boot_transition
            ):
                return self.block("unexpected client boot change")
            if self._state in {ControllerState.SAVE_RELOAD_SENT, ControllerState.ACK_RELOAD_SENT}:
                # The sent state is entered before its reload command is
                # dispatched.  A frame from the preceding boot cannot satisfy
                # the wait; expect_boot is the durable command boundary.
                if not self._expected_boot:
                    self._frame_boot = boot
                    self._frame_sequence = sequence
                    self._frame_crc32 = crc32
                    self._save(last_action="frame_before_reload_dispatch")
                    return self.status()
                if self._expected_boot and boot == self._expected_boot:
                    return self.status()
                if self._reload_boot and boot != self._reload_boot:
                    return self.block("client boot churn during reload")
                self._reload_boot = boot
                self._expected_boot = ""
                self._state = (
                    ControllerState.ACK_RELOAD_WAIT
                    if self._state == ControllerState.ACK_RELOAD_SENT
                    else ControllerState.SAVE_RELOAD_WAIT
                )
            elif self._state in {ControllerState.SAVE_RELOAD_WAIT, ControllerState.ACK_RELOAD_WAIT}:
                if self._reload_boot and boot != self._reload_boot:
                    return self.block("client boot changed after reload")
            elif self._frame_boot and boot != self._frame_boot and not restart_boot_transition:
                return self.block("client boot changed outside reload")
            if self._action_intent in {"save_reload", "ack_reload", "enter_world"}:
                if self._restart_reference_boot and boot != self._restart_reference_boot:
                    self._restart_observed_boot = self._restart_observed_boot or boot
                elif (
                    self._action_intent == "enter_world"
                    and not self._restart_reference_boot
                    and not self._frame_boot
                ):
                    # Character select has no Agent boot.  The first real
                    # world boot is the only honest post-effect observation;
                    # it becomes the persisted identity that rejects churn.
                    self._restart_observed_boot = self._restart_observed_boot or boot
            self._frame_boot = boot
            self._frame_sequence = sequence
            self._frame_crc32 = crc32
            self._save(last_action="frame_observed")
            return self.status()

    def start(self, mode: SessionMode | str = SessionMode.REPEAT) -> ControllerStatus:
        interaction_generation: int | None = None
        with self._mutex:
            if self._state not in {ControllerState.STOPPED, ControllerState.PAUSED}:
                raise RuntimeError(f"cannot start from {self._state}")
            if self._pending:
                raise RuntimeError("pending scan work requires explicit resume")
            requested_mode = SessionMode(mode)
            if requested_mode == SessionMode.INTERACTION:
                # Interaction startup uses the same durable calibration gates as
                # repeat mode.  A stopped/paused owner has no live lease, so it
                # must never jump directly to READY or mutate the mode before a
                # gate can be represented in the journal.
                self._mode = requested_mode
                self._stop_requested = False
                self._closeout_requested = False
                self._blocker = ""
                self._generation += 1
                interaction_generation = self._generation
                gate = self._calibration_gate_state()
                if gate != ControllerState.ARMED or self._reconciliation_required:
                    self._state = gate if gate != ControllerState.ARMED else ControllerState.RECONCILE
                    self._resume_state = self._state
                    self._save(last_action="interaction_start_gate")
                    return self.status()
                self._state = ControllerState.PAUSED
                self._resume_state = ControllerState.WAIT_DUE
                self._save(last_action="interaction_start_rearm")
            else:
                self._mode = requested_mode
                if self._mode == SessionMode.VALIDATION:
                    # A validation invocation is a new qualification run.  Its
                    # first accepted sweep seeds cadence; prior accepted evidence
                    # must never satisfy the three-sweep requirement.
                    self._accepted = []
                    self._total_accepted = 0
                    self._streak = 0
                    self._cadence_seed_start = None
                    self._evidence_meta = {}
                self._stop_requested = False
                self._closeout_requested = False
                self._blocker = ""
                self._generation += 1
                self._state = ControllerState.NATIVE_CALIBRATION
                self._resume_state = self._state
                self._started_at = 0
                self._expected_boot = ""
                self._action_intent = ""
                self._action_attempt = 0
                self._action_result = ""
                self._action_started_at = 0
                self._frame_boot = ""
                self._frame_sequence = 0
                self._frame_crc32 = 0
                self._restart_reference_boot = ""
                self._restart_observed_boot = ""
                self._reload_boot = ""
                self._deadline_at = 0
                self._evidence_meta = {}
                self._cadence_seed_start = None
                self._restart_uncertain = False
                self._reconciliation_required = False
                self._recovery_attempts = 0
                self._recovery_actions.clear()
                self._save(last_action="start")
                return self.status()
        assert interaction_generation is not None
        return self.resume(expected_generation=interaction_generation)

    def enter_interaction(self, *, expected_generation: int | None = None) -> ControllerStatus:
        with self._mutex:
            if expected_generation is not None and expected_generation != self._generation:
                raise RuntimeError("stale generation")
            if self._state not in {ControllerState.READY, ControllerState.WAIT_DUE}:
                raise RuntimeError(f"cannot enter interaction from {self._state}")
            if not self._native_calibrated or not self._input_calibrated or self._input_evidence is None:
                raise RuntimeError("interaction mode requires completed native and input calibration")
            guardian = getattr(self.driver, "guardian", None)
            if guardian is None or not guardian.armed or guardian.generation != self._lease_generation:
                raise RuntimeError("interaction mode requires the current armed input lease")
            self._mode = SessionMode.INTERACTION
            self._state = ControllerState.READY
            self._action_intent = ""
            self._action_result = ""
            self._deadline_at = 0
            self._save(last_action="interaction_enter")
            return self.status()

    def reconcile_interaction(
        self,
        *,
        identity_ok: bool,
        world_ready: bool,
        expected_generation: int | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        """Move a gated interaction owner to READY without touching scan work."""

        with self._mutex:
            if not self._admitted(expected_generation=expected_generation, fence=fence):
                return self.status()
            if self._mode != SessionMode.INTERACTION:
                raise RuntimeError("controller is not in interaction mode")
            if self._state not in {
                ControllerState.ARMED,
                ControllerState.RECONCILE,
                ControllerState.READY,
                ControllerState.WAIT_DUE,
            }:
                return self.status()
            if not identity_ok:
                return self.block("interaction identity mismatch")
            if not world_ready:
                self._state = ControllerState.LOGIN_REQUIRED
                self._save(last_action="interaction_requires_world")
                return self.status()
            if not self._native_calibrated or not self._input_calibrated or self._input_evidence is None:
                self._state = self._calibration_gate_state()
                self._save(last_action="interaction_requires_calibration")
                return self.status()
            guardian = getattr(self.driver, "guardian", None)
            if guardian is None or not guardian.armed or guardian.generation != self._lease_generation:
                # Keep RECONCILE durable until the normal resume path has
                # re-armed the exact current lease.  Never claim READY here.
                self._state = ControllerState.RECONCILE
                self._save(last_action="interaction_requires_lease")
                return self.status()
            self._state = ControllerState.READY
            self._reconciliation_required = False
            self._blocker = ""
            self._save(last_action="interaction_reconcile")
            return self.status()

    def exit_interaction(self, *, expected_generation: int | None = None) -> ControllerStatus:
        with self._mutex:
            if expected_generation is not None and expected_generation != self._generation:
                raise RuntimeError("stale generation")
            if self._mode != SessionMode.INTERACTION:
                raise RuntimeError("controller is not in interaction mode")
            self._planned_revoke = True
            try:
                self._lease_generation = self.driver.revoke("interaction mode exited")
            finally:
                self._planned_revoke = False
            self._mode = SessionMode.REPEAT
            self._generation += 1
            self._state = ControllerState.PAUSED
            self._resume_state = ControllerState.PAUSED
            self._save(last_action="interaction_exit")
            return self.status()

    def native_calibrated(
        self,
        evidence: Any,
        *,
        preconstruction_proof: dict[str, Any] | None = None,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state != ControllerState.NATIVE_CALIBRATION:
                return self.block(f"native calibration is not expected in {self._state.value}")
        try:
            verify = getattr(evidence, "verify_seal", None)
            if not callable(verify):
                raise DriverError("native calibration evidence is not sealed")
            verify()
        except (DriverError, RuntimeError) as exc:
            with self._mutex:
                if not self._admitted(
                    expected_generation=expected_generation, expected_state=expected_state, fence=fence
                ):
                    return self.status()
                return self.block(str(exc))
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            self._native_calibrated = True
            record = self._evidence_record(evidence)
            if preconstruction_proof is not None:
                record["preconstruction"] = self._proof_record(preconstruction_proof)
            self._calibration_evidence["native"] = record
            self._calibration_history.append(
                {"gate": "native", "at": self.wall_clock(), "evidence": copy.deepcopy(record)}
            )
            del self._calibration_history[:-20]
            self._calibration_invalidated_reason = ""
            self._state = ControllerState.INPUT_CALIBRATION
            self._archive("evidence", {"kind": "native_calibration", "evidence": copy.deepcopy(record)})
            self._save(last_action="native_calibrated")
            return self.status()

    def input_calibrated(
        self,
        *,
        evidence: Any,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                raise DriverError("input calibration generation/state was revoked")
            if self._state != ControllerState.INPUT_CALIBRATION:
                return self.block(f"input calibration is not expected in {self._state.value}")
            try:
                # Keep the admission lock across both lease-producing calls.
                # A pause/stop cannot revoke between the post-calibration
                # check and arm, then have stale work recreate the lease.
                self.driver.input_calibration(evidence)
                if not self._admitted(
                    expected_generation=expected_generation, expected_state=expected_state, fence=fence
                ):
                    raise DriverError("input calibration generation was revoked")
                self.driver.arm(evidence)
            except (DriverError, RuntimeError) as exc:
                if not self._admitted(
                    expected_generation=expected_generation, expected_state=expected_state, fence=fence
                ):
                    return self.status()
                return self.block(str(exc))
            if (
                not self._admitted(
                    expected_generation=expected_generation, expected_state=expected_state, fence=fence
                )
            ) or self._state == ControllerState.PAUSED:
                self._planned_revoke = True
                try:
                    self._lease_generation = self.driver.guardian.revoke(
                        "input calibration generation was revoked"
                    )
                finally:
                    self._planned_revoke = False
                return self.status()
            self._input_calibrated = True
            self._input_evidence = evidence
            record = self._evidence_record(evidence)
            self._calibration_evidence["input"] = record
            self._calibration_history.append(
                {"gate": "input", "at": self.wall_clock(), "evidence": copy.deepcopy(record)}
            )
            del self._calibration_history[:-20]
            self._calibration_invalidated_reason = ""
            self._state = ControllerState.ARMED
            self._lease_generation = self.driver.guardian.generation
            self._archive("evidence", {"kind": "input_calibration", "evidence": copy.deepcopy(record)})
            self._save(last_action="input_calibrated")
            return self.status()

    def retain_input_calibration_while_paused(
        self,
        evidence: Any,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            return self._retain_input_calibration_while_paused(evidence)

    def _retain_input_calibration_while_paused(self, evidence: Any) -> ControllerStatus:
        """Keep a proven takeover result without rearming revoked input."""

        if self._state != ControllerState.PAUSED:
            return self.block("input calibration was revoked outside a paused state")
        try:
            verify = getattr(evidence, "verify_seal", None)
            if not callable(verify):
                raise DriverError("input calibration evidence is not sealed")
            verify()
        except (DriverError, RuntimeError) as exc:
            return self.block(str(exc))
        self._input_calibrated = True
        self._input_evidence = evidence
        retain = getattr(self.driver, "retain_input_evidence", None)
        if callable(retain):
            try:
                retain(evidence)
            except (DriverError, RuntimeError) as exc:
                return self.block(str(exc))
        record = self._evidence_record(evidence)
        self._calibration_evidence["input"] = record
        self._calibration_history.append(
            {"gate": "input", "at": self.wall_clock(), "evidence": copy.deepcopy(record)}
        )
        del self._calibration_history[:-20]
        self._archive("evidence", {"kind": "input_calibration_retained", "evidence": copy.deepcopy(record)})
        self._save(last_action="input_calibration_retained_paused")
        return self.status()

    @staticmethod
    def _evidence_record(evidence: Any) -> dict[str, Any]:
        """Persist identity and measured proof without serializing a live object."""

        names = (
            "fingerprint",
            "process_pid",
            "process_executable",
            "window_xid",
            "child_xid",
            "target_pid",
            "target_xid",
            "target_child_xid",
            "display",
            "geometry",
            "crop",
            "boot",
            "sequence",
            "crc32",
            "render",
            "memory_measurements",
            "native_identity_fingerprint",
            "resume_sequence",
            "resume_crc32",
            "resume_render",
            "resume_capture_monotonic",
            "capture_path",
            "capture_sha256",
            "process_start",
            "preconstruction_fingerprint",
            "evidence_hash",
            "xauthority",
            "wine_prefix",
            "rss_before_bytes",
            "rss_after_construction_bytes",
            "rss_after_updates_bytes",
            "synthetic_key_source",
            "synthetic_pointer_source",
            "human_key_source",
            "human_pointer_source",
            "xinput_hierarchy",
            "synthetic_events",
            "human_events",
            "forwarded_events",
            "event_proof",
            "synthetic_modifiers",
            "synthetic_echo_proof",
            "keyboard_keymap",
            "keyboard_profile",
            "target_executable",
            "target_process_start",
            "target_geometry",
            "target_event_xids",
            "managed_frame_xid",
            "managed_frame_geometry",
            "game_identity_fingerprint",
            "game_geometry",
            "driver_version",
            "provenance",
            "is_live",
            # Optional proof emitted by measured anchor/model providers.  The
            # controller stores the proof metadata, never private model text.
            "anchor_capture_path",
            "anchor_capture_sha256",
            "anchor_capture_monotonic",
            "anchor_identity_fingerprint",
            "anchor_bounds",
            "anchor_proof",
            "model_capture_path",
            "model_capture_sha256",
            "model_capture_monotonic",
            "model_timing",
            "model_proof",
            "accepted_proof",
        )

        def primitive(value: Any) -> Any:
            to_dict = getattr(value, "to_dict", None)
            if callable(to_dict):
                return primitive(to_dict())
            if isinstance(value, tuple):
                return [primitive(item) for item in value]
            if isinstance(value, list):
                return [primitive(item) for item in value]
            if isinstance(value, dict):
                return {
                    str(key): primitive(item)
                    for key, item in value.items()
                    if str(key) not in {"_seal", "chatText", "chattext", "chatEdit"}
                }
            if isinstance(value, (str, int, float, bool)) or value is None:
                return value
            return str(value)

        return {name: primitive(getattr(evidence, name)) for name in names if hasattr(evidence, name)}

    def reconcile(
        self,
        *,
        identity_ok: bool,
        world_ready: bool = True,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if not identity_ok:
                return self.block("identity mismatch")
            if self._restart_uncertain:
                # Fresh gates do not settle a client-side effect.  Keep the
                # observation-only boundary until the exact action witness is
                # supplied; restoring the saved phase here could replay it.
                self._state = ControllerState.RECONCILE
                self._reconciliation_required = True
                self._save(last_action="reconcile_uncertainty_pending")
                return self.status()
            if self._resume_state == ControllerState.QUALIFY_PENDING and isinstance(
                self._qualification_pending, dict
            ):
                # A staged qualification is already a complete read-only
                # recovery checkpoint.  Explicit pause/resume may re-enter
                # this boundary, but fresh input gates must never demote it
                # to WAIT_DUE or clear its retry proof.
                self._state = ControllerState.QUALIFY_PENDING
                self._reconciliation_required = False
                self._blocker = ""
                self._save(last_action="reconcile_qualification_pending")
                return self.status()
            if not world_ready:
                self._state = ControllerState.LOGIN_REQUIRED
            else:
                if not self._native_calibrated or not self._input_calibrated or self._input_evidence is None:
                    self._state = self._calibration_gate_state()
                    self._save(last_action="reconcile_requires_fresh_calibration")
                    return self.status()
                self._reconciliation_required = False
                resumable = {
                    ControllerState.SCANNING,
                    ControllerState.QUIET_SAVE,
                    ControllerState.SAVE_RELOAD_SENT,
                    ControllerState.SAVE_RELOAD_WAIT,
                    ControllerState.UPLOAD_WAIT,
                    ControllerState.ACK_RELOAD_SENT,
                    ControllerState.ACK_RELOAD_WAIT,
                    ControllerState.REOPEN,
                    ControllerState.DISK_CLEANUP_SENT,
                    ControllerState.DISK_CLEANUP_WAIT,
                }
                if self._resume_state in resumable and (self._started_at or self._last_uid):
                    self._state = self._resume_state
                else:
                    self._state = ControllerState.WAIT_DUE
                    self._clear_intent("reconcile")
                if self._state != ControllerState.WAIT_DUE and not self._deadline:
                    if self._state == ControllerState.SCANNING:
                        self._deadline = self.clock() + self.sweep_cap_seconds
                        self._deadline_at = self.wall_clock() + self.sweep_cap_seconds
                    elif self._state in {
                        ControllerState.QUIET_SAVE,
                        ControllerState.SAVE_RELOAD_SENT,
                        ControllerState.SAVE_RELOAD_WAIT,
                        ControllerState.REOPEN,
                    }:
                        self._deadline = self.clock() + self.reload_deadline_seconds
                        self._deadline_at = self.wall_clock() + self.reload_deadline_seconds
                    elif self._state in {
                        ControllerState.UPLOAD_WAIT,
                        ControllerState.ACK_RELOAD_SENT,
                        ControllerState.ACK_RELOAD_WAIT,
                        ControllerState.DISK_CLEANUP_SENT,
                        ControllerState.DISK_CLEANUP_WAIT,
                    }:
                        self._deadline = self.clock() + self.ack_deadline_seconds
                        self._deadline_at = self.wall_clock() + self.ack_deadline_seconds
            self._save(last_action="reconcile")
            return self.status()

    def resume(self, *, expected_generation: int | None = None) -> ControllerStatus:
        # IPC callers perform the generation admission while holding the
        # controller lock, then call this method without that lock because
        # re-arming the native observer may touch X11 and can block.  Repeat
        # the check at the method boundary so releasing the lock does not
        # create a stale-resume window.
        with self._mutex:
            if expected_generation is not None and self._generation != expected_generation:
                raise RuntimeError("stale generation")
            if self._state not in {ControllerState.PAUSED, ControllerState.BLOCKED, ControllerState.STOPPED}:
                raise RuntimeError(f"cannot resume from {self._state}")
            if self._resume_state == ControllerState.QUALIFY_PENDING and isinstance(
                self._qualification_pending, dict
            ):
                # A staged outcome is read-only recovery work, but returning
                # to it still requires the normal live calibration/re-arm
                # path before any retry can expose REOPEN or cleanup input.
                self._reconciliation_required = False
            # A restart never replays an uncertain command.  Resume admits a
            # new generation and enters reconciliation; fresh telemetry/files
            # decide whether the old effect completed or should be abandoned.
            if self._restart_uncertain:
                self._blocker = ""
                self._generation += 1
                self._reconciliation_required = True
                self._state = ControllerState.RECONCILE
                self._archive(
                    "interventions",
                    {
                        "kind": "restart_reconcile",
                        "generation": self._generation,
                        "intent": self._action_intent,
                        "attempt": self._action_attempt,
                    },
                )
                self._save(last_action="resume_restart_reconcile")
                return self.status()
            # A stopped owner may be resumed only to inspect/reconcile an
            # already-dispatched effect.  Clearing stop here would authorize a
            # new slash command or scan before that effect is known to settle.
            if self._stop_requested and self._state == ControllerState.STOPPED:
                self._generation += 1
                self._reconciliation_required = bool(self._action_intent and self._action_intent != "stop")
                self._state = (
                    ControllerState.RECONCILE if self._reconciliation_required else ControllerState.STOPPED
                )
                self._save(last_action="resume_stopped_reconcile")
                return self.status()
            self._stop_requested = False
            self._blocker = ""
            self._generation += 1
            resume_generation = self._generation
            resume_origin = self._state
            if self._reconciliation_required:
                if not self._native_calibrated:
                    self._state = ControllerState.NATIVE_CALIBRATION
                elif not self._input_calibrated or self._input_evidence is None:
                    self._state = ControllerState.INPUT_CALIBRATION
                else:
                    self._state = ControllerState.RECONCILE
                self._save(last_action="resume_requires_reconciliation")
                return self.status()
            if not self._native_calibrated:
                self._state = ControllerState.NATIVE_CALIBRATION
                self._save(last_action="resume_requires_native_calibration")
                return self.status()
            elif not self._input_calibrated:
                self._state = ControllerState.INPUT_CALIBRATION
                self._save(last_action="resume_requires_input_calibration")
                return self.status()
            elif self._input_evidence is None:
                # The durable flag records that the gate passed in an earlier
                # process, but its live identity evidence must be collected
                # again before this process can send input.
                self._state = ControllerState.INPUT_CALIBRATION
                self._save(last_action="resume_requires_input_calibration")
                return self.status()
            else:
                evidence = self._input_evidence

        try:
            self.driver.input_calibration(evidence)
            self.driver.arm(evidence)
        except (DriverError, RuntimeError) as exc:
            with self._mutex:
                if self._generation != resume_generation or self._state != resume_origin:
                    return self.status()
            return self.block(
                f"resume calibration evidence rejected: {exc}", expected_generation=resume_generation
            )
        with self._mutex:
            if self._generation != resume_generation or self._state != resume_origin:
                # A pause can arrive while the native observer is being
                # re-armed.  Do not let this stale resume overwrite the
                # durable pause; revoke the just-created lease and leave
                # reconciliation for the explicit resume that follows.
                self._planned_revoke = True
                try:
                    self._lease_generation = self.driver.guardian.revoke("resume generation was revoked")
                finally:
                    self._planned_revoke = False
                return self.status()
            self._lease_generation = self.driver.guardian.generation
            self._state = ControllerState.RECONCILE
            if self._resume_state == ControllerState.SCANNING:
                self._deadline = self.clock() + self.sweep_cap_seconds
                self._deadline_at = self.wall_clock() + self.sweep_cap_seconds
            elif self._resume_state in {
                ControllerState.QUIET_SAVE,
                ControllerState.SAVE_RELOAD_SENT,
                ControllerState.SAVE_RELOAD_WAIT,
            }:
                self._deadline = self.clock() + self.reload_deadline_seconds
                self._deadline_at = self.wall_clock() + self.reload_deadline_seconds
            elif self._resume_state in {
                ControllerState.UPLOAD_WAIT,
                ControllerState.ACK_RELOAD_SENT,
                ControllerState.ACK_RELOAD_WAIT,
            }:
                self._deadline = self.clock() + self.ack_deadline_seconds
                self._deadline_at = self.wall_clock() + self.ack_deadline_seconds
            self._save(last_action="resume")
            return self.status()

    def pause(self, reason: str = "explicit pause") -> ControllerStatus:
        with self._mutex:
            if not (
                self._state in {ControllerState.PAUSED, ControllerState.BLOCKED}
                and self._resume_state
                not in {ControllerState.PAUSED, ControllerState.BLOCKED, ControllerState.STOPPED}
            ):
                self._resume_state = self._state
            self._generation += 1
            self._planned_revoke = True
            try:
                self._lease_generation = self.driver.guardian.revoke(reason)
            finally:
                self._planned_revoke = False
            if self._action_intent and self._action_result not in {
                "",
                "complete",
                "abandoned_after_restart",
            }:
                self._restart_uncertain = True
                self._reconciliation_required = True
            self._state = ControllerState.PAUSED
            self._blocker = reason
            self._save(last_action="pause")
            self._archive(
                "interventions",
                {
                    "kind": "pause",
                    "reason": reason,
                    "generation": self._generation,
                    "state": self._resume_state.value,
                },
            )
            return self.status()

    def reconcile_restart(
        self,
        *,
        observed_boot: str = "",
        observed_uid: str = "",
        uploaded_ids: set[str] | frozenset[str] = frozenset(),
        data_ack_ids: set[str] | frozenset[str] = frozenset(),
        loaded_ids: set[str] | frozenset[str] = frozenset(),
        pending_ids: set[str] | frozenset[str] = frozenset(),
        scanner_phase: str | None | object = _SCANNER_PHASE_UNSET,
        scanner_idle: bool = False,
        stable_scan_ids: set[str] | frozenset[str] | None = None,
        stable_sweep_ids: set[str] | frozenset[str] | None = None,
        loaded_uid: str = "",
        stable_format2_uid: str = "",
        stable_format2_evidence: SweepEvidence | None = None,
        stable_format2_verified: bool = False,
        stable_files_complete: bool = False,
        observed_scene: str = "",
        stable_saved_uid: str = "",
        stable_upload_timestamp: int = 0,
        stable_data_ack_uid: str = "",
        stable_companion_uploaded_uid: str = "",
        loaded_at: int = 0,
        loaded_boot: str = "",
        loaded_sequence: int = 0,
        observed_modal: str = "",
        observed_character: str = "",
        observed_ah_open: bool | None = None,
        selected_arthur: bool | None = None,
        fence_armed: bool | None = None,
        action_postcondition: bool | None = None,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        """Resolve one persisted external intent from an actual new observation.

        This method is read-only with respect to the game.  Every action has a
        named postcondition; absence of an unrelated UID never resolves a
        save/upload/acknowledgement effect.  A recovered acknowledgement is
        qualified in this method from the complete stable format-2 object so a
        daemon cannot accidentally move it through ``REOPEN`` without a run
        outcome.
        """

        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if not self._restart_uncertain:
                self._reconciliation_required = False
                self._save(last_action="restart_reconcile_noop")
                return self.status()
            if (
                scanner_phase is not _SCANNER_PHASE_UNSET
                and scanner_phase is not None
                and not isinstance(scanner_phase, str)
            ):
                return self.block("malformed scanner phase")
            if not isinstance(observed_scene, str) or not isinstance(observed_modal, str):
                return self.block("malformed restart scene evidence")
            for proof_ids in (uploaded_ids, data_ack_ids, loaded_ids, pending_ids):
                if not isinstance(proof_ids, (set, frozenset)) or any(
                    not isinstance(item, str) or not item for item in proof_ids
                ):
                    return self.block("malformed restart proof UID set")
            for proof_uid in (
                observed_boot,
                observed_uid,
                loaded_uid,
                stable_format2_uid,
                stable_saved_uid,
                stable_data_ack_uid,
                stable_companion_uploaded_uid,
                loaded_boot,
            ):
                if not isinstance(proof_uid, str):
                    return self.block("malformed restart proof identity")
            for proof_time in (stable_upload_timestamp, loaded_at, loaded_sequence):
                if isinstance(proof_time, bool) or not isinstance(proof_time, int):
                    return self.block("malformed restart proof timestamp")
            uid = self._last_uid
            intent = self._action_intent
            queue_intents = {
                "scan",
                "save_reload",
                "upload_wait",
                "ack_reload",
                "logout",
                "pre_logout_fence",
            }
            if intent in queue_intents and (
                not isinstance(stable_scan_ids, (set, frozenset))
                or not isinstance(stable_sweep_ids, (set, frozenset))
            ):
                return self.block("malformed stable queue evidence")
            stable_scan_ids = (
                stable_scan_ids if isinstance(stable_scan_ids, (set, frozenset)) else frozenset()
            )
            stable_sweep_ids = (
                stable_sweep_ids if isinstance(stable_sweep_ids, (set, frozenset)) else frozenset()
            )
            if any(not isinstance(item, str) or not item for item in (*stable_scan_ids, *stable_sweep_ids)):
                return self.block("malformed stable queue UID")
            phase = scanner_phase if scanner_phase is not _SCANNER_PHASE_UNSET else None
            scene = observed_scene
            stable_scan_ids = frozenset(stable_scan_ids)
            stable_sweep_ids = frozenset(stable_sweep_ids)
            pre_effect_boot = (
                self._restart_reference_boot
                if self._restart_uncertain and intent in {"save_reload", "ack_reload", "enter_world"}
                else self._frame_boot
            )
            if pre_effect_boot:
                boot_changed = bool(observed_boot and observed_boot != pre_effect_boot)
            elif intent == "enter_world":
                # Character select has no Agent boot.  A first real world
                # boot is valid with an empty B0; once recorded, only that
                # same boot may resolve after a restart.
                boot_changed = bool(observed_boot) and (
                    not self._restart_observed_boot or observed_boot == self._restart_observed_boot
                )
            else:
                boot_changed = False
            ready_stable_facts = (
                isinstance(phase, str)
                and phase in {"ready", "scheduled"}
                and scene in {"world", "auction_house", "character_select"}
                and scanner_idle is True
                and stable_files_complete is True
            )
            complete_facts = ready_stable_facts and stable_format2_verified is True and bool(observed_boot)
            scan_completed_uid = (
                stable_format2_evidence.uid if isinstance(stable_format2_evidence, SweepEvidence) else ""
            )
            scan_completed = bool(
                intent == "scan"
                and complete_facts
                and scan_completed_uid
                and scan_completed_uid != uid
                and observed_uid == scan_completed_uid
                and stable_format2_uid == scan_completed_uid
                and stable_saved_uid == scan_completed_uid
                and scan_completed_uid in stable_scan_ids
                and int(stable_format2_evidence.envelope.get("startedAt", -1)) == self._started_at
            )
            stable_saved_matches = bool(
                uid
                and uid in stable_scan_ids
                and stable_format2_uid == uid
                and stable_saved_uid == uid
                and isinstance(stable_format2_evidence, SweepEvidence)
                and stable_format2_evidence.uid == uid
            )
            finish_at = int(self._evidence_meta.get("finishedAt", 0) or 0)
            upload_time_valid = bool(
                finish_at > 0
                and isinstance(stable_upload_timestamp, int)
                and not isinstance(stable_upload_timestamp, bool)
                and finish_at <= stable_upload_timestamp <= finish_at + self.upload_deadline_seconds
            )
            companion_uid = stable_companion_uploaded_uid
            proven_upload = bool(
                complete_facts
                and stable_saved_matches
                and uid in uploaded_ids
                and uid in data_ack_ids
                and upload_time_valid
                and stable_data_ack_uid == uid
                and companion_uid == uid
            )
            loaded_at_value = loaded_at
            loaded_boot_value = loaded_boot
            loaded_sequence_value = loaded_sequence
            proven_loaded = bool(
                complete_facts
                and uid
                and loaded_uid == uid
                and uid in loaded_ids
                and uid not in pending_ids
                and loaded_at_value > 0
                and loaded_boot_value
                and loaded_sequence_value > 0
                and loaded_boot_value == observed_boot
                and boot_changed
            )
            proven_saved = bool(
                complete_facts
                and intent == "save_reload"
                and uid
                and observed_uid == uid
                and boot_changed
                and stable_saved_matches
            )
            outcome = "restart_observation_unresolved"

            # Logout is a terminal read-only observation.  It intentionally
            # does not require an Agent boot, scanner phase, or calibration.
            disk_empty = (
                stable_files_complete is True
                and not stable_scan_ids
                and not stable_sweep_ids
                and not pending_ids
            )
            if intent == "logout" and scene == "character_select" and disk_empty:
                self._restart_uncertain = False
                self._reconciliation_required = False
                self._state = ControllerState.STOPPED
                self._stop_requested = True
                self._closeout_requested = False
                self._pending = False
                self._clear_intent("completed_at_character_select")
                outcome = "logout_completed_character_select"
            elif intent == "scan" and scan_completed:
                # A scan completed and was durably saved before the owner
                # stopped.  Continue at the save boundary; no scan is replayed.
                self._last_uid = scan_completed_uid
                self._set_format2_evidence(stable_format2_evidence)
                self._restart_uncertain = False
                self._reconciliation_required = True
                self._resume_state = ControllerState.QUIET_SAVE
                self._pending = True
                self._state = self._calibration_gate_state()
                self._begin_intent("save_reload", deadline_seconds=self.reload_deadline_seconds)
                outcome = "scan_completed_saved"
            elif intent == "save_reload" and proven_saved:
                if isinstance(stable_format2_evidence, SweepEvidence):
                    self._set_format2_evidence(stable_format2_evidence)
                self._restart_uncertain = False
                self._reconciliation_required = True
                self._resume_state = ControllerState.UPLOAD_WAIT
                self._pending = True
                self._state = self._calibration_gate_state()
                self._begin_intent("upload_wait", deadline_seconds=self.upload_deadline_seconds)
                outcome = "saved_uid_stable"
            elif intent == "upload_wait" and proven_upload:
                if isinstance(stable_format2_evidence, SweepEvidence):
                    self._set_format2_evidence(stable_format2_evidence)
                self._evidence_meta["atomicCompanionUploadedUid"] = companion_uid
                self._evidence_meta["companionUploadedUID"] = companion_uid
                self._evidence_meta["dataAckUid"] = stable_data_ack_uid
                self._evidence_meta["dataAckUID"] = stable_data_ack_uid
                self._evidence_meta["uploadTimestamp"] = stable_upload_timestamp
                self._restart_uncertain = False
                self._reconciliation_required = True
                self._resume_state = ControllerState.ACK_RELOAD_SENT
                self._pending = True
                self._state = self._calibration_gate_state()
                self._begin_intent("ack_reload", deadline_seconds=self.ack_deadline_seconds)
                outcome = "upload_observed"
            elif intent == "ack_reload" and proven_loaded and stable_saved_matches and proven_upload:
                # Rebuild the complete proof and qualify it now.  Keeping a
                # temporary QUALIFY_PENDING state makes the public boundary
                # explicit while _qualify_unlocked commits exactly one result.
                prior_witnesses = copy.deepcopy(self._evidence_meta)
                self._set_format2_evidence(stable_format2_evidence)
                for key in (
                    "ackPublicationAt",
                    "ackPublicationBoot",
                    "ackPublicationSequence",
                    "ackPublicationLatencySeconds",
                ):
                    if key in prior_witnesses:
                        self._evidence_meta[key] = prior_witnesses[key]
                publication = int(self._evidence_meta.get("ackPublicationAt", 0) or 0)
                upload = int(stable_upload_timestamp)
                if publication <= 0 or upload > publication or loaded_at_value < publication:
                    return self._reject_unrecoverable_cycle("acknowledgement timing witness is incomplete")
                self._evidence_meta.update(
                    {
                        "atomicCompanionUploadedUid": companion_uid,
                        "companionUploadedUID": companion_uid,
                        "dataAckUid": stable_data_ack_uid,
                        "dataAckUID": stable_data_ack_uid,
                        "uploadTimestamp": upload,
                        "ackLoadedUID": loaded_uid,
                        "loadedUID": loaded_uid,
                        "ackLoadedAt": loaded_at_value,
                        "ackLoadedBoot": loaded_boot_value,
                        "ackLoadedSequence": loaded_sequence_value,
                        "qualifiedEvidenceUID": "",
                    }
                )
                self._last_uid = uid
                self._pending = True
                self._restart_uncertain = False
                self._reconciliation_required = False
                self._clear_intent("reconciled_ack_loaded")
                self._state = ControllerState.QUALIFY_PENDING
                started_at = self._started_at or int(stable_format2_evidence.envelope["startedAt"])
                self._started_at = int(started_at)
                result = self._qualify_unlocked(stable_format2_evidence, started_at=started_at)
                result = self._park_recovered_terminal(result)
                self._archive(
                    "interventions",
                    {
                        "kind": "restart_resolution",
                        "outcome": "acknowledgement_loaded_and_qualified",
                        "generation": self._generation,
                        "intent": intent,
                        "attempt": self._action_attempt,
                        "uid": uid,
                        "loadedAt": loaded_at_value,
                        "loadedBoot": loaded_boot_value,
                        "loadedSequence": loaded_sequence_value,
                    },
                )
                self._save(last_action="restart_resolved:acknowledgement_loaded_and_qualified")
                return result
            elif intent == "pre_logout_fence" and complete_facts and fence_armed is True:
                self._resume_state = ControllerState.DISK_CLEANUP_SENT
                self._pending = False
                self._restart_uncertain = False
                self._reconciliation_required = True
                self._state = self._calibration_gate_state()
                self._clear_intent("fence_observation_expired")
                outcome = "pre_logout_fence_requires_fresh_owner"
            elif intent in {
                "dismiss_disconnect",
                "reconnect_game",
                "select_arthur",
                "enter_world",
                "open_ah",
            }:
                boot_required = intent == "enter_world"
                named_ok = (not boot_required or (bool(observed_boot) and boot_changed)) and (
                    (
                        intent == "dismiss_disconnect"
                        and scene == "game_client"
                        and observed_modal == "none"
                        and action_postcondition is True
                    )
                    or (
                        intent == "reconnect_game"
                        and scene == "character_select"
                        and action_postcondition is True
                    )
                    or (
                        intent == "select_arthur"
                        and action_postcondition is True
                        and (
                            scene == "arthur_selected"
                            or (scene == "character_select" and selected_arthur is True)
                        )
                    )
                    or (intent == "enter_world" and scene == "world" and action_postcondition is True)
                    or (
                        intent == "open_ah"
                        and scene == "auction_house"
                        and observed_ah_open is True
                        and action_postcondition is True
                    )
                )
                if named_ok:
                    self._restart_uncertain = False
                    self._reconciliation_required = True
                    self._pending = False
                    self._resume_state = (
                        ControllerState.READY if intent == "enter_world" else ControllerState.WAIT_DUE
                    )
                    self._state = self._calibration_gate_state()
                    self._clear_intent("postcondition_observed")
                    outcome = f"{intent}_postcondition_observed"
            elif intent == "stop" and self._stop_requested:
                self._restart_uncertain = False
                self._reconciliation_required = False
                self._state = ControllerState.STOPPED
                self._clear_intent("stop_observed")
                outcome = "stop_observed"
            elif (
                intent in {"save_reload", "upload_wait", "ack_reload"}
                and stable_files_complete is True
                and not stable_format2_uid
                and not stable_scan_ids
                and not stable_sweep_ids
            ):
                return self._reject_unrecoverable_cycle(
                    f"unrecoverable {intent} cycle: exact UID is absent from stable format-2 files"
                )
            elif (
                intent == "scan"
                and self._action_result == "dispatched"
                and ready_stable_facts
                and not stable_scan_ids
                and not stable_sweep_ids
            ):
                return self._reject_empty_scan_attempt(
                    "dispatched scan reached ready with stable empty queues"
                )
            elif intent == "scan" and ready_stable_facts and not stable_scan_ids and not stable_sweep_ids:
                # A ready/empty observation before the external scan dispatch
                # is not evidence that the attempted scan produced no data.
                # Keep the intent unresolved while the owner reacquires its
                # live calibration gates.
                self._state = self._calibration_gate_state()
                self._reconciliation_required = True
            else:
                # Keep the original intent and all pending evidence.  The
                # next owner may still prove it; clearing it would authorize a
                # duplicate external effect.
                self._reconciliation_required = True

            self._archive(
                "interventions",
                {
                    "kind": "restart_resolution",
                    "outcome": outcome,
                    "generation": self._generation,
                    "intent": intent,
                    "attempt": self._action_attempt,
                    "uid": uid,
                    "observedBoot": observed_boot,
                    "observedUid": observed_uid,
                    "scannerPhase": phase,
                    "scannerIdle": scanner_idle,
                    "scene": scene,
                    "stableSavedUid": stable_saved_uid,
                    "stableUploadTimestamp": stable_upload_timestamp,
                    "stableDataAckUid": stable_data_ack_uid,
                    "stableCompanionUploadedUid": companion_uid,
                    "stableFormat2Verified": stable_format2_verified,
                    "stableFilesComplete": stable_files_complete,
                    "stableScanIds": sorted(stable_scan_ids),
                    "stableSweepIds": sorted(stable_sweep_ids),
                },
            )
            self._save(last_action=f"restart_resolved:{outcome}")
            return self.status()

    # Descriptive alias used by the daemon worker; both names retain the same
    # atomic admission and no-replay semantics.
    resolve_restart_intent = reconcile_restart

    def _on_guardian_revocation(self, reason: str) -> None:
        """Convert an independent guardian takeover into a durable pause."""
        with self._mutex:
            if (
                self._planned_revoke
                or self._guardian_callback_active
                or self._state
                in {
                    ControllerState.PAUSED,
                    ControllerState.STOPPED,
                    ControllerState.BLOCKED,
                }
            ):
                return
            lowered = reason.lower()
            if any(
                marker in lowered
                for marker in ("identity", "hierarchy", "observer", "display", "boot", "client")
            ):
                self._invalidate_live_calibration(f"live calibration invalidated: {reason}")
            self._guardian_callback_active = True
            try:
                self.pause(f"input guardian: {reason}")
            finally:
                self._guardian_callback_active = False

    def stop(self) -> ControllerStatus:
        with self._mutex:
            self._generation += 1
            self._stop_requested = True
            self._planned_revoke = True
            try:
                self._lease_generation = self.driver.guardian.revoke("stop requested")
            finally:
                self._planned_revoke = False
            prior_intent = self._action_intent
            prior_result = self._action_result
            # The durable intent is written before the physical command.  A
            # stop racing that boundary cannot know whether the worker had
            # already crossed it, so every unresolved result remains an
            # intent-specific reconciliation obligation on the next owner.
            external_effect_pending = bool(
                prior_intent and prior_result not in {"", "complete", "abandoned_after_restart"}
            )
            if external_effect_pending:
                # Stop is orthogonal to an effect that crossed the dispatch
                # boundary.  Preserve its phase and exact intent so the next
                # owner can observe the result without replaying it.
                self._restart_uncertain = True
                self._reconciliation_required = True
            elif self._state in {
                ControllerState.STOPPED,
                ControllerState.PAUSED,
                ControllerState.BLOCKED,
                ControllerState.WAIT_DUE,
                ControllerState.READY,
                ControllerState.QUIET_SAVE,
                ControllerState.REOPEN,
                ControllerState.DISK_CLEANUP_SENT,
                ControllerState.DISK_CLEANUP_WAIT,
            }:
                self._state = ControllerState.STOPPED
            if not prior_intent or prior_result in {"", "complete", "abandoned_after_restart"}:
                self._begin_intent("stop")
            self._save(last_action="stop")
            self._archive(
                "interventions",
                {"kind": "stop", "generation": self._generation, "state": self._state.value},
            )
            return self.status()

    def closeout(self) -> ControllerStatus:
        with self._mutex:
            self._generation += 1
            self._closeout_requested = True
            if self._state in {ControllerState.WAIT_DUE, ControllerState.READY} or (
                self._state == ControllerState.STOPPED and not self._stop_requested and not self._pending
            ):
                self._state = ControllerState.DISK_CLEANUP_SENT
                self._begin_intent("logout", deadline_seconds=self.ack_deadline_seconds)
            self._archive(
                "interventions",
                {"kind": "closeout_requested", "generation": self._generation, "state": self._state.value},
            )
            self._save(last_action="closeout")
            return self.status()

    def begin_scan(
        self,
        *,
        started_at: int | None = None,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state not in {
                ControllerState.WAIT_DUE,
                ControllerState.READY,
            }:
                raise RuntimeError(f"cannot start scan from {self._state}")
            if self._stop_requested or self._closeout_requested:
                self._state = ControllerState.STOPPED
            else:
                self._state = ControllerState.SCANNING
                self._pending = True
                self._started_at = int(started_at if started_at is not None else self.wall_clock())
                # The daemon persists the scan intent before typing and marks
                # the same effect dispatched before it enters SCANNING.  Keep
                # that attempt and result when this public transition follows
                # the dispatch; creating a second attempt would turn a crash
                # into an unresolved scan and lose the truthful empty-result
                # rejection boundary.
                preserve_scan_intent = self._action_intent == "scan" and self._action_result in {
                    "pending",
                    "preparing",
                    "dispatched",
                    "chat_open",
                }
                if not preserve_scan_intent:
                    self._begin_intent("scan", deadline_seconds=self.sweep_cap_seconds)
            self._save(
                last_action=f"scan_start:{started_at if started_at is not None else self.wall_clock()}"
            )
            return self.status()

    def adopt_scan(
        self,
        *,
        started_at: int,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        """Adopt a scan that the addon started before a closeout was observed.

        ``closeoutRequested`` prevents the controller from initiating a new
        scan, but it must not make it discard an already-running addon scan.
        This transition records that observational handoff and lets the normal
        save/upload/ack path prove the resulting UID before final logout.
        Clearing ``_last_uid`` is intentional: an automatic restart may reuse
        the previous completed UID until its new SavedVariables envelope
        appears, and that old UID must never satisfy the new scan boundary.
        """

        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state != ControllerState.DISK_CLEANUP_SENT:
                raise RuntimeError(f"cannot adopt scan from {self._state}")
            if self._stop_requested or not self._closeout_requested:
                raise RuntimeError("scan adoption requires an active closeout without stop")
            if isinstance(started_at, bool) or not isinstance(started_at, int) or started_at <= 0:
                raise ValueError("adopted scan start must be a positive integer")
            self._state = ControllerState.SCANNING
            self._pending = True
            self._last_uid = ""
            self._started_at = started_at
            self._begin_intent("scan", deadline_seconds=self.sweep_cap_seconds)
            self._save(last_action=f"scan_adopt:{started_at}")
            return self.status()

    def saved(
        self,
        uid: str,
        *,
        stable: bool = False,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state != ControllerState.SCANNING:
                raise RuntimeError(f"cannot observe saved UID from {self._state}")
            if not uid:
                return self.block("empty saved UID")
            self._last_uid = uid
            self._pending = True
            # A daemon may persist the reload intent before the stable UID
            # observation returns.  That observation belongs to the same
            # effect boundary and must not mint a second attempt or erase a
            # dispatched result/deadline.
            preserve_save_intent = self._action_intent == "save_reload" and (
                self._action_result in {"pending", "preparing", "dispatched", "chat_open"}
            )
            if not preserve_save_intent:
                self._begin_intent("save_reload", deadline_seconds=self.reload_deadline_seconds)
            if self._stop_requested:
                self._state = ControllerState.STOPPED
                self._save(last_action="saved_after_stop")
                return self.status()
            self._state = ControllerState.SAVE_RELOAD_SENT if stable else ControllerState.QUIET_SAVE
            self._save(last_action="saved")
            return self.status()

    def reload_sent(
        self,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state not in {ControllerState.QUIET_SAVE, ControllerState.SAVE_RELOAD_SENT}:
                raise RuntimeError(f"cannot send save reload from {self._state}")
            if self._stop_requested:
                self._state = ControllerState.STOPPED
                self._save(last_action="reload_suppressed_after_stop")
                return self.status()
            self._state = ControllerState.SAVE_RELOAD_SENT
            self._dispatch_intent("save_reload", deadline_seconds=self.reload_deadline_seconds)
            self._save(last_action="save_reload_sent")
            return self.status()

    def reload_observed(
        self,
        *,
        acknowledgement: bool = False,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        expected = ControllerState.ACK_RELOAD_SENT if acknowledgement else ControllerState.SAVE_RELOAD_SENT
        target = ControllerState.ACK_RELOAD_WAIT if acknowledgement else ControllerState.SAVE_RELOAD_WAIT
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state != expected:
                raise RuntimeError(f"cannot observe reload from {self._state}")
            expected_intent = "ack_reload" if acknowledgement else "save_reload"
            if self._action_intent != expected_intent:
                raise RuntimeError("reload observation does not match the dispatched intent")
            self._reload_boot = self._frame_boot
            self._state = target
            self._expected_boot = ""
            self._save(last_action="reload_observed")
            return self.status()

    def stable_saved(
        self,
        evidence: SweepEvidence,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state != ControllerState.SAVE_RELOAD_WAIT:
                raise RuntimeError(f"cannot accept stable SavedVariables from {self._state}")
            if evidence.uid != self._last_uid:
                return self.block("stable SavedVariables UID mismatch")
            if not evidence.stable_verified:
                return self.block("SavedVariables evidence was not stably verified")
            try:
                self._set_format2_evidence(evidence)
            except (DriverError, KeyError, TypeError, ValueError) as exc:
                return self.block(str(exc))
            if self._stop_requested:
                # Stop revokes input and forbids a new upload/ack action.  Keep the
                # exact saved UID, evidence, and save-reload intent durable so an
                # explicit later resume can reconcile it without replaying the
                # reload.  stopRequested is orthogonal to the in-flight effect.
                self._state = ControllerState.STOPPED
                self._save(last_action="stable_saved_after_stop")
                return self.status()
            self._state = ControllerState.UPLOAD_WAIT
            self._begin_intent("upload_wait", deadline_seconds=self.upload_deadline_seconds)
            self._save(last_action="stable_saved")
            return self.status()

    def uploaded(
        self,
        uid: str,
        *,
        accepted: bool,
        upload_time: int = 0,
        data_ack_uid: str = "",
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state != ControllerState.UPLOAD_WAIT:
                raise RuntimeError(f"cannot accept upload result from {self._state}")
            if uid != self._last_uid:
                return self.block("upload UID mismatch")
            if not accepted:
                rejection_state = self._qualification_state_snapshot()
                self._evidence_meta["qualification"] = "rejected"
                self._evidence_meta["rejectionReason"] = "upload rejected"
                self._pending = False
                self._archive(
                    "evidence",
                    {
                        "kind": "upload",
                        "uid": uid,
                        "accepted": False,
                        "generation": self._generation,
                        "evidence": copy.deepcopy(self._evidence_meta),
                    },
                )
                self._archive_staged_outcome(
                    rejection_state,
                    result="rejected",
                    reason="upload rejected",
                    kind="upload",
                )
                return self.block("upload rejected")
            finish = int(self._evidence_meta.get("finishedAt", 0))
            if (
                upload_time <= 0
                or data_ack_uid != uid
                or self._evidence_meta.get("stableSavedUid") != uid
                or finish <= 0
                or upload_time < finish
                or upload_time - finish > self.upload_deadline_seconds
            ):
                return self.block("upload lacks stable companion and Data.lua acknowledgement")
            self._evidence_meta["atomicCompanionUploadedUid"] = uid
            self._evidence_meta["companionUploadedUID"] = uid
            self._evidence_meta["uploadTimestamp"] = int(upload_time)
            self._evidence_meta["dataAckUid"] = data_ack_uid
            self._evidence_meta["dataAckUID"] = data_ack_uid
            if self._evidence_meta.get("finishedAt"):
                self._evidence_meta["uploadLatencySeconds"] = max(
                    0, int(upload_time) - int(self._evidence_meta["finishedAt"])
                )
            if self._stop_requested:
                self._state = ControllerState.STOPPED
                self._deadline = 0.0
                self._deadline_at = 0
                self._save(last_action="uploaded_after_stop")
                return self.status()
            self._state = ControllerState.ACK_RELOAD_SENT
            # This is a new effect boundary.  Never carry the dispatched
            # upload result/attempt into the acknowledgement reload intent.
            self._begin_intent("ack_reload", deadline_seconds=self.ack_deadline_seconds)
            self._save(last_action="uploaded")
            return self.status()

    def record_ack_publication(
        self,
        uid: str,
        *,
        companion_uid: str,
        data_uid: str,
        publication_time: int | None = None,
        boot: str = "",
        sequence: int = 0,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        """Persist the two stable pre-reload acknowledgement witnesses."""

        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state != ControllerState.ACK_RELOAD_SENT:
                raise RuntimeError(f"cannot record acknowledgement publication from {self._state}")
            if uid != self._last_uid or companion_uid != uid or data_uid != uid:
                return self.block("acknowledgement publication UID mismatch")
            if (
                self._evidence_meta.get("uid") != uid
                or self._evidence_meta.get("stableSavedUid") != uid
                or (self._evidence_meta.get("atomicCompanionUploadedUid") or "") not in {"", uid}
                or self._evidence_meta.get("dataAckUid", "") not in {"", uid}
            ):
                return self.block("acknowledgement publication is not bound to stable evidence")
            publication = int(publication_time or 0)
            upload = int(self._evidence_meta.get("uploadTimestamp", 0))
            if upload <= 0 or publication < upload:
                return self.block("acknowledgement publication is not after the exact upload")
            self._evidence_meta["atomicCompanionUploadedUid"] = companion_uid
            self._evidence_meta["companionUploadedUID"] = companion_uid
            self._evidence_meta["dataAckUid"] = data_uid
            self._evidence_meta["dataAckUID"] = data_uid
            if publication_time is not None:
                self._evidence_meta["ackPublicationAt"] = publication
                if self._evidence_meta.get("uploadTimestamp"):
                    self._evidence_meta["ackPublicationLatencySeconds"] = max(
                        0,
                        int(publication_time) - int(self._evidence_meta["uploadTimestamp"]),
                    )
            if boot:
                self._evidence_meta["ackPublicationBoot"] = boot
            if sequence:
                self._evidence_meta["ackPublicationSequence"] = int(sequence)
            self._save(last_action="ack_publication_observed")
            return self.status()

    def ack_reload_complete(
        self,
        *,
        pending_ids: set[str],
        loaded_uid: str = "",
        loaded_at: int | None = None,
        boot: str = "",
        sequence: int = 0,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state != ControllerState.ACK_RELOAD_WAIT:
                raise RuntimeError(f"cannot complete acknowledgement reload from {self._state}")
            if loaded_uid != self._last_uid:
                return self.block("acknowledgement loaded UID is not the exact pending UID")
            if self._last_uid in pending_ids:
                self._save(last_action="ack_reload_waiting_for_disk_cleanup")
                return self.status()
            publication = int(self._evidence_meta.get("ackPublicationAt", 0))
            upload = int(self._evidence_meta.get("uploadTimestamp", 0))
            loaded_at_value = int(loaded_at or 0)
            loaded_boot = str(boot or self._frame_boot)
            loaded_sequence = int(sequence or self._frame_sequence)
            if (
                upload <= 0
                or publication < upload
                or loaded_at is None
                or loaded_at_value <= 0
                or loaded_at_value < publication
                or not loaded_boot
                or loaded_sequence <= 0
                or (self._frame_boot and loaded_boot != self._frame_boot)
                or (self._frame_sequence and loaded_sequence != self._frame_sequence)
            ):
                return self.block("acknowledgement load lacks exact publication witness")
            self._evidence_meta["ackLoadedUID"] = loaded_uid
            self._evidence_meta["loadedUID"] = loaded_uid
            self._evidence_meta["ackLoadedAt"] = loaded_at_value
            self._evidence_meta["ackLoadedBoot"] = loaded_boot
            self._evidence_meta["ackLoadedSequence"] = loaded_sequence
            if self._evidence_meta.get("finishedAt"):
                self._evidence_meta["ackLatencySeconds"] = max(
                    0, loaded_at_value - int(self._evidence_meta["finishedAt"])
                )
            if self._evidence_meta.get("ackPublicationAt"):
                self._evidence_meta["ackLoadedLatencySeconds"] = max(
                    0, loaded_at_value - int(self._evidence_meta["ackPublicationAt"])
                )
            if self._stop_requested:
                self._state = ControllerState.STOPPED
            elif self._closeout_requested:
                self._state = ControllerState.DISK_CLEANUP_SENT
            else:
                self._state = ControllerState.REOPEN
            self._clear_intent("complete")
            self._save(last_action="ack_reload_complete")
            return self.status()

    def reopen_complete(
        self,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state != ControllerState.REOPEN:
                raise RuntimeError(f"cannot complete reopen from {self._state}")
            self._state = (
                ControllerState.DISK_CLEANUP_SENT if self._closeout_requested else ControllerState.WAIT_DUE
            )
            self._clear_intent("complete")
            self._save(last_action="reopen_complete")
            return self.status()

    def expect_boot(
        self,
        boot: str,
        *,
        acknowledgement: bool = False,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state not in {ControllerState.SAVE_RELOAD_SENT, ControllerState.ACK_RELOAD_SENT}:
                raise RuntimeError(f"cannot wait for reload from {self._state}")
            if not boot:
                raise RuntimeError("reload wait requires a boot identity")
            # This is the durable pre-effect observation.  It is recorded
            # before the first post-reload frame can replace ``frameBoot`` and
            # is retained through pause/restart recovery.
            self._restart_reference_boot = boot
            self._restart_observed_boot = ""
            self._expected_boot = boot
            # A second reload starts a new one-boot window; the previous reload's
            # boot is historical evidence and must not be mistaken for churn.
            self._reload_boot = ""
            expected_intent = "ack_reload" if acknowledgement else "save_reload"
            if self._action_intent != expected_intent:
                raise RuntimeError("reload wait does not match the dispatched intent")
            self._save(last_action="expect_boot")
            return self.status()

    def ack_reload_command_sent(
        self,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state != ControllerState.ACK_RELOAD_SENT:
                raise RuntimeError(f"cannot mark ack reload command from {self._state}")
            self._dispatch_intent("ack_reload", deadline_seconds=self.ack_deadline_seconds)
            self._save(last_action="ack_reload_command_sent")
            return self.status()

    def qualify(
        self,
        evidence: SweepEvidence,
        *,
        started_at: int,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state not in {
                ControllerState.REOPEN,
                ControllerState.DISK_CLEANUP_SENT,
                ControllerState.QUALIFY_PENDING,
            }:
                raise RuntimeError(f"cannot qualify evidence from {self._state}")
            return self._qualify_unlocked(evidence, started_at=started_at)

    def retry_pending_qualification(
        self,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        """Retry staged qualification after a first archive-boundary failure.

        The complete evidence and witness metadata come from the durable
        qualification checkpoint.  A daemon must not retain or resupply an
        in-memory ``SweepEvidence`` object after owner destruction.
        """

        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state not in {
                ControllerState.QUALIFY_PENDING,
                ControllerState.PAUSED,
                ControllerState.BLOCKED,
            }:
                raise RuntimeError(f"cannot retry qualification from {self._state}")
            if self._state in {ControllerState.PAUSED, ControllerState.BLOCKED} and (
                self._resume_state == ControllerState.QUALIFY_PENDING
            ):
                raise RuntimeError("qualification retry requires explicit resume and live input gates")
            pending = self._qualification_pending
            if not isinstance(pending, dict):
                return self._reject_unrecoverable_cycle(
                    "qualification checkpoint is missing complete evidence"
                )
            metadata = pending.get("metadata")
            evidence_record = pending.get("evidence")
            started_at = pending.get("startedAt")
            if (
                not isinstance(metadata, dict)
                or isinstance(started_at, bool)
                or not isinstance(started_at, int)
                or started_at <= 0
                or not isinstance(evidence_record, dict)
            ):
                return self._reject_unrecoverable_cycle("qualification checkpoint metadata is incomplete")
            try:
                evidence = self._evidence_from_record(evidence_record)
            except DriverError as exc:
                return self._reject_unrecoverable_cycle(str(exc))
            if metadata.get("uid") != evidence.uid or metadata.get("stableSavedUid") != evidence.uid:
                return self._reject_unrecoverable_cycle(
                    "qualification checkpoint UID is not bound to stable evidence"
                )
            self._evidence_meta = copy.deepcopy(metadata)
            self._last_uid = evidence.uid
            self._pending = True
            result = self._qualify_unlocked(evidence, started_at=started_at, stage=False)
            return self._park_recovered_terminal(result)

    def _qualify_unlocked(
        self, evidence: SweepEvidence, *, started_at: int, stage: bool = True
    ) -> ControllerStatus:
        if self._evidence_meta.get("outcomeArchived"):
            return self.status()
        prior_state = self._qualification_state_snapshot()
        if stage:
            try:
                self._stage_qualification_pending(evidence, started_at=started_at)
            except JournalError:
                self._restore_qualification_state(prior_state)
                raise
        staged_state = self._qualification_state_snapshot()
        item_valid, observed_kinds = self._validate_item_evidence(evidence)
        exact_stable = (
            self._evidence_meta.get("uid") == evidence.uid == self._last_uid
            and self._evidence_meta.get("stableSavedUid") == evidence.uid
            and self._evidence_meta.get("stablePlanHash") == evidence.plan_hash
            and self._evidence_meta.get("stableHouse") == evidence.house
            and self._evidence_meta.get("fullEvidence", {}).get("uid") == evidence.uid
        )
        valid = (
            evidence.stable_verified
            and exact_stable
            and int(evidence.envelope.get("startedAt", -1)) == int(started_at)
            and evidence.observations == 428
            and evidence.attempted == 428
            and evidence.full + evidence.bounded == 428
            and evidence.incomplete == 0
            and evidence.unqueried == 0
            and evidence.priced > 0
            and item_valid
            and {"commodity", "recipe", "container", "equipment"}.issubset(observed_kinds)
            and int(self._evidence_meta.get("uploadTimestamp", 0)) > 0
            and int(self._evidence_meta.get("ackPublicationAt", 0))
            >= int(self._evidence_meta.get("uploadTimestamp", 0))
            and int(self._evidence_meta.get("ackLoadedAt", 0))
            >= int(self._evidence_meta.get("ackPublicationAt", 0))
            and self._evidence_meta.get("atomicCompanionUploadedUid") == evidence.uid
            and self._evidence_meta.get("dataAckUid") == evidence.uid
            and self._evidence_meta.get("ackLoadedUID") == evidence.uid
            and bool(self._evidence_meta.get("ackLoadedBoot", ""))
            and int(self._evidence_meta.get("ackLoadedSequence", 0)) > 0
            and (
                not evidence.query_durations
                or sorted(evidence.query_durations)[len(evidence.query_durations) // 2]
                <= BASELINE_MEDIAN_SECONDS
            )
        )
        if not valid:
            prior_streak = self._streak
            prior_seed = self._cadence_seed_start
            prior_evidence = copy.deepcopy(self._evidence_meta)
            # A rejected candidate must retain the exact witnesses that were
            # already proven for the in-flight outcome.  Keep them at the
            # top level for the bounded checkpoint and under priorEvidence
            # for audit consumers; replacing the evidence with the candidate
            # must never erase the upload/publication/load timing chain.
            preserved_witnesses = {
                key: copy.deepcopy(prior_evidence[key])
                for key in (
                    "stableSavedUid",
                    "stableHouse",
                    "stablePlanHash",
                    "stableContext",
                    "atomicCompanionUploadedUid",
                    "uploadTimestamp",
                    "uploadLatencySeconds",
                    "dataAckUid",
                    "ackPublicationAt",
                    "ackPublicationLatencySeconds",
                    "ackPublicationBoot",
                    "ackPublicationSequence",
                    "ackLoadedAt",
                    "ackLatencySeconds",
                    "ackLoadedLatencySeconds",
                    "ackLoadedBoot",
                    "ackLoadedSequence",
                )
                if key in prior_evidence
            }
            self._evidence_meta = {
                "uid": evidence.uid,
                "startedAt": int(evidence.envelope.get("startedAt", 0)),
                "finishedAt": int(evidence.envelope.get("finishedAt", 0)),
                "planHash": evidence.plan_hash,
                "observations": evidence.observations,
                "attempted": evidence.attempted,
                "full": evidence.full,
                "bounded": evidence.bounded,
                "incomplete": evidence.incomplete,
                "unqueried": evidence.unqueried,
                "priced": evidence.priced,
                "rowCount": evidence.row_count,
                "kinds": list(evidence.kinds),
                "queryTimes": copy.deepcopy(evidence.query_times),
                "itemEvidence": copy.deepcopy(evidence.item_evidence),
                "ownedRows": copy.deepcopy(evidence.owned_rows),
                "ownedPricedRowCount": evidence.owned_priced_row_count,
                "fullEvidence": self._full_evidence_record(evidence),
                "qualification": "rejected",
                "rejectionReason": "qualifying sweep evidence failed",
                "acceptedBefore": prior_streak,
                "priorCadenceSeedStart": prior_seed,
                "priorEvidence": prior_evidence,
                **preserved_witnesses,
            }
            self._pending = False
            self._blocker = "qualifying sweep evidence failed"
            self._last_uid = evidence.uid
            self._state = (
                ControllerState.STOPPED
                if self._stop_requested
                else ControllerState.DISK_CLEANUP_SENT
                if self._closeout_requested
                else ControllerState.REOPEN
            )
            if self._state == ControllerState.REOPEN:
                self._deadline = self.clock() + self.reload_deadline_seconds
                self._deadline_at = self.wall_clock() + self.reload_deadline_seconds
            self._streak = 0
            self._cadence_seed_start = None
            self._archive_staged_outcome(
                staged_state,
                result="rejected",
                reason=self._blocker,
                kind="qualification",
            )
            self._save(last_action="qualification_reset")
            return self.status()
        if self._streak and self._cadence_seed_start is not None:
            expected = self._cadence_seed_start + self._streak * self.cadence_seconds
            if abs(started_at - expected) > 5:
                accepted_before = self._streak
                prior_seed = self._cadence_seed_start
                prior_evidence = copy.deepcopy(self._evidence_meta)
                self._blocker = "cadence interval failed"
                self._evidence_meta["qualification"] = "rejected"
                self._evidence_meta["rejectionReason"] = self._blocker
                self._pending = False
                self._state = (
                    ControllerState.STOPPED
                    if self._stop_requested
                    else ControllerState.DISK_CLEANUP_SENT
                    if self._closeout_requested
                    else ControllerState.REOPEN
                )
                if self._state == ControllerState.REOPEN:
                    self._deadline = self.clock() + self.reload_deadline_seconds
                    self._deadline_at = self.wall_clock() + self.reload_deadline_seconds
                self._evidence_meta["cadenceExpectedStartedAt"] = int(expected)
                self._evidence_meta["cadenceDeltaSeconds"] = int(started_at - expected)
                self._evidence_meta["acceptedBefore"] = accepted_before
                self._evidence_meta["priorCadenceSeedStart"] = prior_seed
                self._evidence_meta["priorEvidence"] = prior_evidence
                self._streak = 0
                self._cadence_seed_start = None
                self._archive_staged_outcome(
                    staged_state,
                    result="rejected",
                    reason=self._blocker,
                    kind="cadence",
                )
                self._save(last_action="cadence_reset")
                return self.status()
        if self._streak == 0:
            self._cadence_seed_start = int(started_at)
        self._accepted.append(
            {
                "uid": evidence.uid,
                "startedAt": started_at,
                "finishedAt": int(evidence.envelope.get("finishedAt", 0)),
                "observations": evidence.observations,
                "attempted": evidence.attempted,
                "full": evidence.full,
                "bounded": evidence.bounded,
                "incomplete": evidence.incomplete,
                "unqueried": evidence.unqueried,
                "priced": evidence.priced,
                "rows": evidence.row_count,
                "kinds": list(evidence.kinds),
                "rowKinds": copy.deepcopy(evidence.row_kinds),
                "queryTimes": copy.deepcopy(evidence.query_times),
                "itemEvidence": copy.deepcopy(evidence.item_evidence),
                "ownedRows": copy.deepcopy(evidence.owned_rows),
                "ownedPricedRowCount": evidence.owned_priced_row_count,
                "fullEvidence": self._full_evidence_record(evidence),
                "evidence": copy.deepcopy(self._evidence_meta),
            }
        )
        self._total_accepted += 1
        del self._accepted[:-20]
        self._streak += 1
        self._last_uid = evidence.uid
        self._pending = False
        self._blocker = ""
        self._evidence_meta["qualification"] = "accepted"
        self._evidence_meta["qualifiedEvidenceUID"] = evidence.uid
        self._evidence_meta["evidenceUID"] = evidence.uid
        if self._accepted:
            self._accepted[-1]["evidence"] = copy.deepcopy(self._evidence_meta)
        self._evidence_meta["acceptedBefore"] = self._streak - 1
        self._deadline = 0.0
        self._deadline_at = 0
        if self._stop_requested:
            self._state = ControllerState.STOPPED
        elif (self._mode == SessionMode.VALIDATION and self._streak >= 3) or self._closeout_requested:
            self._closeout_requested = True
            self._state = ControllerState.DISK_CLEANUP_SENT
        else:
            self._state = ControllerState.REOPEN
            self._deadline = self.clock() + self.reload_deadline_seconds
            self._deadline_at = self.wall_clock() + self.reload_deadline_seconds
        self._archive_staged_outcome(
            staged_state,
            result="accepted",
            reason="qualified",
            kind="accepted",
        )
        self._save(last_action="qualify")
        return self.status()

    @staticmethod
    def _validate_item_evidence(evidence: SweepEvidence) -> tuple[bool, set[str]]:
        """Check the complete 428-item accounting proof at qualification."""

        entries = evidence.item_evidence
        if not isinstance(entries, dict) or len(entries) != 428:
            return False, set()
        categories = {"commodity", "recipe", "container", "equipment"}
        observed: set[str] = set()
        rows_total = priced_total = owned_total = owned_priced_total = 0
        for item_id, item in entries.items():
            if not isinstance(item_id, str) or not isinstance(item, dict):
                return False, observed
            category = item.get("category")
            if category not in categories or item.get("coverage") not in {"full", "bounded"}:
                return False, observed
            observed.add(category)
            row_count = item.get("rowCount")
            priced_count = item.get("pricedRowCount")
            owned_rows = item.get("ownedRows")
            owned_priced = item.get("ownedPricedRowCount")
            if any(
                isinstance(value, bool) or not isinstance(value, int) or value < 0
                for value in (row_count, priced_count, owned_priced)
            ) or not isinstance(owned_rows, list):
                return False, observed
            if priced_count > row_count or owned_priced > len(owned_rows):
                return False, observed
            valid_owned_priced = 0
            for row in owned_rows:
                if not isinstance(row, dict) or str(row.get("itemID", item_id)) != item_id:
                    return False, observed
                buyout = row.get("buyout")
                if isinstance(buyout, dict) and buyout.get("kind") == "known":
                    copper = buyout.get("copper")
                    if isinstance(copper, int) and not isinstance(copper, bool) and copper > 0:
                        valid_owned_priced += 1
            if valid_owned_priced != owned_priced:
                return False, observed
            rows_total += row_count
            priced_total += priced_count
            owned_total += len(owned_rows)
            owned_priced_total += owned_priced
        if not evidence.owned_rows or evidence.owned_priced_row_count <= 0:
            return False, observed
        if owned_total != len(evidence.owned_rows) or owned_priced_total != evidence.owned_priced_row_count:
            return False, observed
        if rows_total != evidence.row_count or priced_total != evidence.priced:
            return False, observed
        return True, observed

    def cleanup_complete(
        self,
        *,
        logout_observed: bool,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state != ControllerState.DISK_CLEANUP_WAIT:
                raise RuntimeError(f"cannot complete cleanup from {self._state}")
            if not logout_observed:
                return self.block("closeout cleanup did not observe /logout")
            self._state = ControllerState.STOPPED
            self._pending = False
            self._closeout_requested = False
            self._stop_requested = True
            self._clear_intent("complete")
            self._archive(
                "interventions",
                {"kind": "closeout_complete", "generation": self._generation, "uid": self._last_uid},
            )
            self._save(last_action="cleanup_complete")
            return self.status()

    def logout_sent(
        self,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if self._state != ControllerState.DISK_CLEANUP_SENT:
                raise RuntimeError(f"cannot send logout from {self._state}")
            self._state = ControllerState.DISK_CLEANUP_WAIT
            self._dispatch_intent("logout", deadline_seconds=self.ack_deadline_seconds)
            self._save(last_action="logout_sent")
            return self.status()

    def block(
        self,
        reason: str,
        *,
        expected_generation: int | None = None,
        expected_state: ControllerState | str | set[ControllerState | str] | None = None,
        fence: ObservationFence | None = None,
    ) -> ControllerStatus:
        with self._mutex:
            if not self._admitted(
                expected_generation=expected_generation, expected_state=expected_state, fence=fence
            ):
                return self.status()
            if isinstance(self._qualification_pending, dict) and not self._evidence_meta.get(
                "outcomeArchived"
            ):
                # An outcome publication failure leaves a complete retry proof
                # on disk.  A normal daemon error handler must not replace it
                # with mutated counters or a terminal REOPEN checkpoint.
                self._planned_revoke = True
                try:
                    self._lease_generation = self.driver.revoke(reason)
                finally:
                    self._planned_revoke = False
                self._resume_state = ControllerState.QUALIFY_PENDING
                self._state = ControllerState.QUALIFY_PENDING
                self._pending = True
                self._restart_uncertain = False
                self._reconciliation_required = False
                self._deadline = 0.0
                self._deadline_at = 0
                self._blocker = reason
                self._archive(
                    "interventions",
                    {
                        "kind": "blocked_with_qualification_pending",
                        "reason": reason,
                        "generation": self._generation,
                        "state": ControllerState.QUALIFY_PENDING.value,
                    },
                )
                self._save(last_action="blocked_with_qualification_pending")
                return self.status()
            prior_state = self._state
            rejection_state = self._qualification_state_snapshot()
            if (
                self._evidence_meta.get("uid")
                and self._evidence_meta.get("qualification", "pending") != "accepted"
                and prior_state
                in {
                    ControllerState.SAVE_RELOAD_WAIT,
                    ControllerState.UPLOAD_WAIT,
                    ControllerState.ACK_RELOAD_SENT,
                    ControllerState.ACK_RELOAD_WAIT,
                    ControllerState.REOPEN,
                }
            ):
                self._evidence_meta["qualification"] = "rejected"
                self._evidence_meta["rejectionReason"] = reason
                self._pending = False
                self._archive_staged_outcome(
                    rejection_state,
                    result="rejected",
                    reason=reason,
                    kind="blocked",
                )
            self._resume_state = self._state
            self._planned_revoke = True
            try:
                self.driver.revoke(reason)
            finally:
                self._planned_revoke = False
            self._lease_generation = self.driver.guardian.generation
            self._deadline = 0.0
            self._deadline_at = 0
            self._blocker = reason
            lowered = reason.lower()
            self._reconciliation_required = True
            if any(
                marker in lowered
                for marker in ("identity", "boot", "hierarchy", "display", "crc", "corrupt", "protocol")
            ):
                self._invalidate_live_calibration(f"live calibration invalidated: {reason}")
            self._state = ControllerState.BLOCKED
            self._streak = 0
            self._cadence_seed_start = None
            self._archive(
                "interventions",
                {
                    "kind": "blocked",
                    "reason": reason,
                    "generation": self._generation,
                    "state": self._resume_state.value,
                },
            )
            self._save(last_action="blocked")
            return self.status()


__all__ = [
    "ActionIntent",
    "ActionKind",
    "Controller",
    "ControllerState",
    "ControllerStatus",
    "ObservationFence",
    "SessionMode",
]
