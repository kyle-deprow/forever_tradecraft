"""Pure admission and budget policy for a future mailbox interaction cycle.

This module deliberately has no controller, journal, IPC, clock, filesystem, or
input side effects.  Runtime code must perform its own atomic checkpoint and
lease/capability admission before using the returned decision.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from crowley.session.protocol import Snapshot

EFFECTIVE_DUE_INTERVAL_SECONDS = 900.0
_WAIT_DUE = "WAIT_DUE"
_SCANNER_PHASES = frozenset({"ready", "scheduled"})


class MailLoopPolicyError(ValueError):
    """The caller supplied a malformed policy input or operation bound."""


@dataclass(frozen=True)
class MailLoopBinding:
    """Process-local opt-in binding; the default has no scheduling authority."""

    enabled: bool = False
    generation: int = 0
    queue_id: str = ""
    seq: int = 0
    house: str = ""
    character: str = ""


@dataclass(frozen=True)
class MailLoopBoundary:
    """Controller-owned observations consumed without mutation by the policy."""

    generation: int
    session_mode: str
    repeat_phase: str
    ack_loaded_uid: str
    status_last_uid: str
    seen_ack_uids: frozenset[str]
    unresolved_action: bool
    reconciliation_pending: bool
    stop_requested: bool
    closeout_pending: bool
    last_actual_start_at: float | None
    now: float


@dataclass(frozen=True)
class MailOperationBounds:
    """Finite positive worst-case limits supplied by the eventual runtime."""

    route_to_mailbox_seconds: float
    world_click_seconds: float
    mail_click_seconds: float
    mail_postcondition_seconds: float
    route_to_auctioneer_seconds: float
    ah_reopen_seconds: float
    safety_margin_seconds: float


@dataclass(frozen=True)
class MailBudget:
    """Expanded immutable bound for exactly the admitted current action."""

    mail_units: int
    route_to_mailbox_seconds: float
    world_click_seconds: float
    mail_click_seconds: float
    mail_postcondition_seconds: float
    route_to_auctioneer_seconds: float
    ah_reopen_seconds: float
    safety_margin_seconds: float
    operational_seconds: float
    total_seconds: float


@dataclass(frozen=True)
class MailLoopDecision:
    """Admitted or deferred pure result; it is not a lease or click capability."""

    admitted: bool
    deferred: bool
    reason: str
    queue_id: str
    admitted_seq: int
    ack_uid: str
    mail_units: int
    effective_due_at: float | None
    latest_start_at: float | None
    completion_deadline_at: float | None
    budget: MailBudget | None


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise MailLoopPolicyError(f"{name} must be a positive integer")
    return value


def _finite_nonnegative(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MailLoopPolicyError(f"{name} must be a finite non-negative number")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise MailLoopPolicyError(f"{name} must be a finite non-negative number") from exc
    if not math.isfinite(result) or result < 0:
        raise MailLoopPolicyError(f"{name} must be a finite non-negative number")
    return result


def _finite_positive(value: Any, name: str) -> float:
    result = _finite_nonnegative(value, name)
    if result <= 0:
        raise MailLoopPolicyError(f"{name} must be positive")
    return result


def _nonempty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise MailLoopPolicyError(f"{name} must be a non-empty string")
    return value


def _wire_string(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise MailLoopPolicyError(f"{name} must be a string")
    return value


def _wire_boolean(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise MailLoopPolicyError(f"{name} must be boolean")
    return value


def _wire_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise MailLoopPolicyError(f"{name} must be an integer")
    return value


def _validate_binding(binding: MailLoopBinding) -> None:
    if type(binding) is not MailLoopBinding:
        raise MailLoopPolicyError("binding must be a MailLoopBinding")
    if not isinstance(binding.enabled, bool):
        raise MailLoopPolicyError("binding.enabled must be boolean")
    # Validate wire-shaped scalar types before checking disabled sentinels.
    # Python's equality/truthiness would otherwise let False, 0.0, or None
    # masquerade as the canonical zero/empty dry-run values.
    if isinstance(binding.generation, bool) or not isinstance(binding.generation, int):
        raise MailLoopPolicyError("binding.generation must be an integer")
    if isinstance(binding.seq, bool) or not isinstance(binding.seq, int):
        raise MailLoopPolicyError("binding.seq must be an integer")
    for name in ("queue_id", "house", "character"):
        if not isinstance(getattr(binding, name), str):
            raise MailLoopPolicyError(f"binding.{name} must be a string")
    if not binding.enabled:
        if (
            binding.generation != 0
            or binding.seq != 0
            or any(value for value in (binding.queue_id, binding.house, binding.character))
        ):
            raise MailLoopPolicyError("disabled binding must have empty zero defaults")
        return
    _positive_integer(binding.generation, "binding.generation")
    _positive_integer(binding.seq, "binding.seq")
    _nonempty_string(binding.queue_id, "binding.queue_id")
    _nonempty_string(binding.house, "binding.house")
    _nonempty_string(binding.character, "binding.character")


def _validate_strings(values: frozenset[str], name: str) -> None:
    if type(values) is not frozenset:
        raise MailLoopPolicyError(f"{name} must be an immutable frozenset")
    for value in values:
        _nonempty_string(value, f"{name}[]")


def _validate_boundary(boundary: MailLoopBoundary) -> None:
    if type(boundary) is not MailLoopBoundary:
        raise MailLoopPolicyError("boundary must be a MailLoopBoundary")
    _positive_integer(boundary.generation, "boundary.generation")
    if not isinstance(boundary.session_mode, str):
        raise MailLoopPolicyError("boundary.session_mode must be a string")
    if not isinstance(boundary.repeat_phase, str):
        raise MailLoopPolicyError("boundary.repeat_phase must be a string")
    if not isinstance(boundary.ack_loaded_uid, str):
        raise MailLoopPolicyError("boundary.ack_loaded_uid must be a string")
    if not isinstance(boundary.status_last_uid, str):
        raise MailLoopPolicyError("boundary.status_last_uid must be a string")
    _validate_strings(boundary.seen_ack_uids, "boundary.seen_ack_uids")
    for name in ("unresolved_action", "reconciliation_pending", "stop_requested", "closeout_pending"):
        if not isinstance(getattr(boundary, name), bool):
            raise MailLoopPolicyError(f"boundary.{name} must be boolean")
    if boundary.last_actual_start_at is not None:
        _finite_nonnegative(boundary.last_actual_start_at, "boundary.last_actual_start_at")
    _finite_nonnegative(boundary.now, "boundary.now")


def _validate_bounds(bounds: MailOperationBounds) -> dict[str, float]:
    if type(bounds) is not MailOperationBounds:
        raise MailLoopPolicyError("bounds must be a MailOperationBounds")
    fields = (
        "route_to_mailbox_seconds",
        "world_click_seconds",
        "mail_click_seconds",
        "mail_postcondition_seconds",
        "route_to_auctioneer_seconds",
        "ah_reopen_seconds",
        "safety_margin_seconds",
    )
    return {name: _finite_positive(getattr(bounds, name), f"bounds.{name}") for name in fields}


def _make_budget(bounds: MailOperationBounds, mail_units: int) -> MailBudget:
    values = _validate_bounds(bounds)
    operational = (
        values["route_to_mailbox_seconds"]
        + values["world_click_seconds"]
        + mail_units * (values["mail_click_seconds"] + values["mail_postcondition_seconds"])
        + values["route_to_auctioneer_seconds"]
        + values["ah_reopen_seconds"]
    )
    total = operational + values["safety_margin_seconds"]
    if not math.isfinite(operational):
        raise MailLoopPolicyError("bounds operational total must be finite")
    if not math.isfinite(total):
        raise MailLoopPolicyError("bounds total must be finite")
    return MailBudget(mail_units=mail_units, operational_seconds=operational, total_seconds=total, **values)


def _defer(
    reason: str,
    *,
    queue_id: str = "",
    ack_uid: str = "",
    effective_due_at: float | None = None,
    latest_start_at: float | None = None,
    completion_deadline_at: float | None = None,
    budget: MailBudget | None = None,
) -> MailLoopDecision:
    return MailLoopDecision(
        admitted=False,
        deferred=True,
        reason=reason,
        queue_id=queue_id,
        admitted_seq=0,
        ack_uid=ack_uid,
        mail_units=budget.mail_units if budget else 0,
        effective_due_at=effective_due_at,
        latest_start_at=latest_start_at,
        completion_deadline_at=completion_deadline_at,
        budget=budget,
    )


def admit_mail_cycle(
    snapshot: Snapshot,
    binding: MailLoopBinding,
    boundary: MailLoopBoundary,
    bounds: MailOperationBounds,
) -> MailLoopDecision:
    """Evaluate one exact current mail action without side effects.

    The result admits only the current ``mail_collect`` sequence and ACK.  It
    never selects a successor, mints authority, changes durable state, or
    requires the executor button to be visible/click-ready while still at AH.
    """

    if type(snapshot) is not Snapshot:
        raise MailLoopPolicyError("snapshot must be the validated protocol Snapshot type")
    value = snapshot.value
    _validate_binding(binding)
    _validate_boundary(boundary)
    _validate_bounds(bounds)
    if not binding.enabled:
        return _defer("disabled")
    if boundary.session_mode != "repeat":
        return _defer("session_not_repeat")
    if boundary.repeat_phase != _WAIT_DUE:
        return _defer("not_wait_due")
    if binding.generation != boundary.generation:
        return _defer("generation_mismatch")

    if not boundary.ack_loaded_uid or not boundary.status_last_uid:
        return _defer("ack_missing")
    if boundary.ack_loaded_uid != boundary.status_last_uid:
        return _defer("ack_status_mismatch", ack_uid=boundary.ack_loaded_uid)
    if boundary.ack_loaded_uid in boundary.seen_ack_uids:
        return _defer("ack_already_seen", ack_uid=boundary.ack_loaded_uid)
    if any(
        (
            boundary.unresolved_action,
            boundary.reconciliation_pending,
            boundary.stop_requested,
            boundary.closeout_pending,
        )
    ):
        return _defer("unresolved_boundary", ack_uid=boundary.ack_loaded_uid)

    if boundary.last_actual_start_at is None or boundary.last_actual_start_at <= 0:
        return _defer("start_missing", ack_uid=boundary.ack_loaded_uid)
    if boundary.last_actual_start_at > boundary.now:
        return _defer("start_after_now", ack_uid=boundary.ack_loaded_uid)

    if not isinstance(value, dict):
        raise MailLoopPolicyError("snapshot value must be an object")
    loaded = value.get("loaded")
    pending = value.get("pending")
    scanner = value.get("scanner")
    house = value.get("house")
    context = value.get("context")
    if not all(type(item) is dict for item in (loaded, pending, scanner, house, context)):
        raise MailLoopPolicyError("snapshot loaded/pending/scanner/house/context must be objects")
    acked_ids = loaded.get("ackedIds")
    pending_ids = pending.get("ids")
    if type(acked_ids) is not list or type(pending_ids) is not list:
        raise MailLoopPolicyError("snapshot ACK and pending IDs must be wire arrays")
    if any(not isinstance(item, str) or not item for item in acked_ids + pending_ids):
        raise MailLoopPolicyError("snapshot ACK and pending IDs must be non-empty strings")
    scanner_phase = scanner.get("phase")
    scanner_due_at = scanner.get("dueAt")
    _wire_string(scanner_phase, "snapshot.scanner.phase")
    if _wire_integer(scanner_due_at, "snapshot.scanner.dueAt") < 0:
        raise MailLoopPolicyError("snapshot.scanner.dueAt must be a non-negative integer")
    wire_house = house.get("key")
    wire_character = context.get("character")
    _wire_string(wire_house, "snapshot.house.key")
    _wire_string(wire_character, "snapshot.context.character")
    wall_time = value.get("wallTime")
    if _wire_integer(wall_time, "snapshot.wallTime") < 0:
        raise MailLoopPolicyError("snapshot.wallTime must be a non-negative integer")
    if boundary.now < wall_time:
        return _defer("clock_before_frame", ack_uid=boundary.ack_loaded_uid)
    if boundary.ack_loaded_uid not in acked_ids:
        return _defer("ack_wire_mismatch", ack_uid=boundary.ack_loaded_uid)
    if pending_ids:
        return _defer("pending_work", ack_uid=boundary.ack_loaded_uid)
    if scanner_phase not in _SCANNER_PHASES:
        return _defer("scanner_not_ready", ack_uid=boundary.ack_loaded_uid)

    executor = value.get("executor")
    if not isinstance(executor, dict):
        raise MailLoopPolicyError("snapshot.executor must be an object")
    ah_open = value.get("ahOpen")
    _wire_boolean(ah_open, "snapshot.ahOpen")
    if not ah_open:
        return _defer("auction_house_not_open", ack_uid=boundary.ack_loaded_uid)
    for field in ("availability", "queueId", "house", "character", "currentKind", "phase"):
        _wire_string(executor.get(field), f"snapshot.executor.{field}")
    for field in ("inFlight", "blocked", "latched", "ambiguous"):
        _wire_boolean(executor.get(field), f"snapshot.executor.{field}")
    _wire_integer(executor.get("currentSeq"), "snapshot.executor.currentSeq")
    work_done = executor.get("workDone")
    work_total = executor.get("workTotal")
    if any(
        (
            executor.get("availability") != "valid",
            executor.get("queueId") != binding.queue_id,
            executor.get("house") != binding.house,
            executor.get("character") != binding.character,
            wire_house != binding.house,
            wire_character != binding.character,
            executor.get("currentSeq") != binding.seq,
            executor.get("currentKind") != "mail_collect",
            executor.get("phase") != "ready",
            executor.get("inFlight") is not False,
            executor.get("blocked") is not False,
            executor.get("latched") is not False,
            executor.get("ambiguous") is not False,
        )
    ):
        return _defer("executor_not_initial_mail", ack_uid=boundary.ack_loaded_uid)
    if isinstance(work_done, bool) or not isinstance(work_done, int):
        return _defer("executor_progress_invalid", ack_uid=boundary.ack_loaded_uid)
    if isinstance(work_total, bool) or not isinstance(work_total, int):
        return _defer("executor_work_total_invalid", ack_uid=boundary.ack_loaded_uid)
    if work_done != 0:
        return _defer("executor_progress_not_initial", ack_uid=boundary.ack_loaded_uid)
    if isinstance(work_total, bool) or not isinstance(work_total, int) or work_total < 1:
        return _defer("executor_work_total_invalid", ack_uid=boundary.ack_loaded_uid)

    budget = _make_budget(bounds, work_total)
    effective_due_at = max(
        float(scanner_due_at),
        float(boundary.last_actual_start_at) + EFFECTIVE_DUE_INTERVAL_SECONDS,
    )
    latest_start_at = effective_due_at - budget.total_seconds
    completion_deadline_at = effective_due_at - budget.safety_margin_seconds
    if boundary.now + budget.total_seconds > effective_due_at:
        return _defer(
            "insufficient_due_budget",
            queue_id=binding.queue_id,
            ack_uid=boundary.ack_loaded_uid,
            effective_due_at=effective_due_at,
            latest_start_at=latest_start_at,
            completion_deadline_at=completion_deadline_at,
            budget=budget,
        )
    return MailLoopDecision(
        admitted=True,
        deferred=False,
        reason="admitted",
        queue_id=binding.queue_id,
        admitted_seq=binding.seq,
        ack_uid=boundary.ack_loaded_uid,
        mail_units=work_total,
        effective_due_at=effective_due_at,
        latest_start_at=latest_start_at,
        completion_deadline_at=completion_deadline_at,
        budget=budget,
    )


__all__ = [
    "EFFECTIVE_DUE_INTERVAL_SECONDS",
    "MailBudget",
    "MailLoopBinding",
    "MailLoopBoundary",
    "MailLoopDecision",
    "MailLoopPolicyError",
    "MailOperationBounds",
    "admit_mail_cycle",
]
