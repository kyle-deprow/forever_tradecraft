"""Strict validation and rendering for trade queues and execution records."""

from __future__ import annotations

import copy
import datetime
import re
import secrets
import time
from typing import Any

from crowley.core.house import House
from crowley.core.luawriter import render_assignment

MAX_SAFE_INTEGER = 9_007_199_254_740_991
MAX_QUEUE_ID_BYTES = 192
MAX_HOUSE_BYTES = 256
MAX_CHARACTER_BYTES = 256
MAX_MESSAGES = 0xFFFFFFFF
MAX_ACTIONS = 50
ACTION_KINDS = frozenset(
    {
        "buy_commodity",
        "post_commodity",
        "cancel_auction",
        "vendor_sell",
        "vendor_buy",
        "craft",
        "mail_collect",
    }
)
RESULT_STATUSES = frozenset({"dry_run", "started", "blocked", "succeeded", "failed", "refused", "skipped"})
TERMINAL_STATUSES = frozenset({"succeeded", "failed", "refused", "skipped"})

QUEUE_FIELDS = {
    "format",
    "queueId",
    "generatedAt",
    "expiresAt",
    "house",
    "character",
    "armed",
    "actions",
}
EXECUTION_FIELDS = {"queueId", "house", "character", "results"}
RESULT_FIELDS = {"seq", "kind", "status", "at", "detail"}


class QueueFormatError(ValueError):
    """A queue or execution record does not satisfy the executor contract."""


def _keys(value: Any, expected: set[str], where: str) -> None:
    if not isinstance(value, dict):
        raise QueueFormatError(f"{where} must be an object")
    unknown = set(value) - expected
    missing = expected - set(value)
    if unknown:
        raise QueueFormatError(f"{where} has unknown fields: {sorted(unknown)}")
    if missing:
        raise QueueFormatError(f"{where} is missing fields: {sorted(missing)}")


def _int(value: Any, where: str, *, minimum: int = 1, maximum: int = MAX_SAFE_INTEGER) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum or value > maximum:
        raise QueueFormatError(f"{where} must be a positive safe integer")
    return value


def _string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise QueueFormatError(f"{where} must be a non-empty string")
    return value


def _bounded_string(value: Any, where: str, maximum_bytes: int) -> str:
    value = _string(value, where)
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise QueueFormatError(f"{where} must be valid UTF-8") from exc
    if size > maximum_bytes:
        raise QueueFormatError(f"{where} exceeds {maximum_bytes} UTF-8 bytes")
    return value


def _bool(value: Any, where: str) -> bool:
    if not isinstance(value, bool):
        raise QueueFormatError(f"{where} must be boolean")
    return value


def _timestamp(value: Any, where: str) -> int:
    value = _int(value, where)
    try:
        datetime.datetime.fromtimestamp(value, tz=datetime.UTC)
    except (OverflowError, OSError, ValueError) as exc:
        raise QueueFormatError(f"{where} is not a storable timestamp") from exc
    return value


def _validate_house(value: Any, where: str = "queue.house", *, bounded: bool = True) -> str:
    value = _bounded_string(value, where, MAX_HOUSE_BYTES) if bounded else _string(value, where)
    try:
        return House.parse(value).key
    except ValueError as exc:
        raise QueueFormatError(str(exc)) from exc


def _validate_action(action: Any, index: int) -> dict[str, Any]:
    where = f"queue.actions[{index}]"
    if not isinstance(action, dict):
        raise QueueFormatError(f"{where} must be an object")
    if "kind" not in action:
        raise QueueFormatError(f"{where} is missing fields: ['kind']")
    kind = action["kind"]
    if not isinstance(kind, str) or kind not in ACTION_KINDS:
        raise QueueFormatError(f"{where}.kind is invalid")
    fields: dict[str, set[str]] = {
        "buy_commodity": {"seq", "kind", "itemID", "quantity", "maxUnitPrice"},
        "post_commodity": {"seq", "kind", "itemID", "quantity", "unitPrice", "durationHours"},
        "cancel_auction": {"seq", "kind", "auctionID"},
        "vendor_sell": {"seq", "kind", "itemID", "quantity"},
        "vendor_buy": {"seq", "kind", "itemID", "quantity"},
        "craft": {"seq", "kind", "recipeID", "times"},
        "mail_collect": {"seq", "kind", "maxMessages"},
    }
    _keys(action, fields[kind], where)
    _int(action["seq"], f"{where}.seq")
    if kind in {"buy_commodity", "post_commodity", "vendor_sell", "vendor_buy"}:
        _int(action["itemID"], f"{where}.itemID")
        _int(action["quantity"], f"{where}.quantity")
    if kind == "buy_commodity":
        _int(action["maxUnitPrice"], f"{where}.maxUnitPrice")
    elif kind == "post_commodity":
        _int(action["unitPrice"], f"{where}.unitPrice")
        duration = _int(action["durationHours"], f"{where}.durationHours")
        if duration not in {12, 24, 48}:
            raise QueueFormatError(f"{where}.durationHours must be 12, 24, or 48")
    elif kind == "cancel_auction":
        _int(action["auctionID"], f"{where}.auctionID")
    elif kind == "craft":
        _int(action["recipeID"], f"{where}.recipeID")
        _int(action["times"], f"{where}.times")
    elif kind == "mail_collect":
        _int(action["maxMessages"], f"{where}.maxMessages", maximum=MAX_MESSAGES)
    return action


def _queue_id_pattern(house: str, character: str, generated_at: int) -> re.Pattern[str]:
    return re.compile(re.escape(f"{house}-{character}-{generated_at}-") + r"[0-9a-f]{4}")


def validate_queue(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and deep-copy a complete queue in executor wire format."""

    _keys(raw, QUEUE_FIELDS, "queue")
    if _int(raw["format"], "queue.format") != 1:
        raise QueueFormatError("unsupported queue format")
    queue_id = _bounded_string(raw["queueId"], "queue.queueId", MAX_QUEUE_ID_BYTES)
    generated_at = _timestamp(raw["generatedAt"], "queue.generatedAt")
    expires_at = _timestamp(raw["expiresAt"], "queue.expiresAt")
    if expires_at <= generated_at:
        raise QueueFormatError("queue.expiresAt must be greater than queue.generatedAt")
    house = _validate_house(raw["house"])
    character = _bounded_string(raw["character"], "queue.character", MAX_CHARACTER_BYTES)
    _bool(raw["armed"], "queue.armed")
    actions = raw["actions"]
    if actions == {}:
        actions = []
    if not isinstance(actions, list):
        raise QueueFormatError("queue.actions must be an array")
    if len(actions) > MAX_ACTIONS:
        raise QueueFormatError("queue.actions may contain at most 50 actions")
    for expected_seq, action in enumerate(actions, start=1):
        action = _validate_action(action, expected_seq)
        if action["seq"] != expected_seq:
            raise QueueFormatError("queue action seq values must be contiguous starting at 1")
    if _queue_id_pattern(house, character, generated_at).fullmatch(queue_id) is None:
        raise QueueFormatError("queue.queueId does not match house, character and generatedAt")
    result = copy.deepcopy(raw)
    result["house"] = house
    result["actions"] = copy.deepcopy(actions)
    return result


def _new_queue_id(house: str, character: str, generated_at: int) -> str:
    return f"{house}-{character}-{generated_at}-{secrets.token_hex(2)}"


def build_queue(
    spec: dict[str, Any],
    *,
    generated_at: int | None = None,
    armed: bool | None = None,
) -> dict[str, Any]:
    """Build a complete queue from a publish specification.

    A specification contains the contract's house, character, expiry and actions.  A
    complete queue may also be supplied, which is useful when a caller is replaying a
    previously generated dry preview.
    """

    if not isinstance(spec, dict):
        raise QueueFormatError("queue specification must be an object")
    allowed = QUEUE_FIELDS | {"source"}
    unknown = set(spec) - allowed
    if unknown:
        raise QueueFormatError(f"queue specification has unknown fields: {sorted(unknown)}")
    now = int(time.time()) if generated_at is None else generated_at
    if "generatedAt" in spec:
        now = spec["generatedAt"]
    supplied_armed = spec.get("armed", False)
    if "armed" in spec:
        _bool(supplied_armed, "queue.armed")
    if "queueId" in spec or "format" in spec:
        if "queueId" not in spec:
            raise QueueFormatError("complete queue specifications require queueId")
        queue = {key: value for key, value in spec.items() if key != "source"}
        queue.setdefault("format", 1)
        if armed is not None:
            _bool(armed, "queue.armed")
            queue["armed"] = armed
        return validate_queue(queue)
    try:
        house = _validate_house(spec.get("house"))
        character = _bounded_string(spec.get("character"), "queue.character", MAX_CHARACTER_BYTES)
        expires_at = spec["expiresAt"]
        actions = spec["actions"]
    except KeyError as exc:
        raise QueueFormatError(f"queue specification is missing {exc.args[0]!r}") from exc
    queue = {
        "format": 1,
        "queueId": _new_queue_id(house, character, now),
        "generatedAt": now,
        "expiresAt": expires_at,
        "house": house,
        "character": character,
        "armed": supplied_armed if armed is None else armed,
        "actions": actions,
    }
    return validate_queue(queue)


def render_queue_lua(queue: dict[str, Any] | None) -> str:
    """Render a queue file, including the explicit empty-queue false value."""

    value: Any = False if queue is None else validate_queue(queue)
    return render_assignment(
        "CROWLEY_QUEUE",
        value,
        header="Written by the Crowley companion. Do not edit; it is overwritten.",
    )


def _validate_detail(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise QueueFormatError(f"{where} must be an object")
    return value


def validate_execution_record(raw: dict[str, Any], queue: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate one ``CrowleyDB.executions[queueId]`` record.

    ``queue`` is required when the record is being accepted by the server so each
    result can be checked against the requested action.  It is optional for callers
    inspecting a saved record without its queue.
    """

    _keys(raw, EXECUTION_FIELDS, "execution")
    queue_id = _string(raw["queueId"], "execution.queueId")
    house = _validate_house(raw["house"], bounded=False)
    character = _string(raw["character"], "execution.character")
    action_map: dict[int, dict[str, Any]] | None = None
    if queue is not None:
        queue = validate_queue(queue)
        if queue_id != queue["queueId"]:
            raise QueueFormatError("execution.queueId does not match queue")
        if house != queue["house"] or character != queue["character"]:
            raise QueueFormatError("execution identity does not match queue")
        action_map = {action["seq"]: action for action in queue["actions"]}
    else:
        if re.fullmatch(r".+-.+-[1-9][0-9]*-[0-9a-f]{4}", queue_id) is None:
            raise QueueFormatError("execution.queueId is malformed")
    results = raw["results"]
    if results == {}:
        results = []
    if not isinstance(results, list):
        raise QueueFormatError("execution.results must be an array")
    validated_results = []
    for index, result in enumerate(results, start=1):
        where = f"execution.results[{index}]"
        _keys(result, RESULT_FIELDS, where)
        seq = _int(result["seq"], f"{where}.seq")
        kind = result["kind"]
        if not isinstance(kind, str) or kind not in ACTION_KINDS:
            raise QueueFormatError(f"{where}.kind is invalid")
        if action_map is not None:
            action = action_map.get(seq)
            if action is None:
                raise QueueFormatError(f"{where}.seq does not identify an action")
            if action["kind"] != kind:
                raise QueueFormatError(f"{where}.kind does not match its action")
        status = result["status"]
        if not isinstance(status, str) or status not in RESULT_STATUSES:
            raise QueueFormatError(f"{where}.status is invalid")
        at = _timestamp(result["at"], f"{where}.at")
        detail = _validate_detail(result["detail"], f"{where}.detail")
        if status == "blocked" and (not isinstance(detail.get("reason"), str) or not detail["reason"]):
            raise QueueFormatError(f"{where}.detail.reason is required for blocked results")
        validated_results.append(
            {"seq": seq, "kind": kind, "status": status, "at": at, "detail": copy.deepcopy(detail)}
        )
    result = copy.deepcopy(raw)
    result["house"] = house
    result["results"] = validated_results
    return result


# Names used by callers that prefer the contract's noun-oriented terminology.
validate_execution = validate_execution_record
build = build_queue


__all__ = [
    "ACTION_KINDS",
    "MAX_CHARACTER_BYTES",
    "MAX_ACTIONS",
    "MAX_HOUSE_BYTES",
    "MAX_MESSAGES",
    "MAX_QUEUE_ID_BYTES",
    "RESULT_STATUSES",
    "TERMINAL_STATUSES",
    "QueueFormatError",
    "build",
    "build_queue",
    "render_queue_lua",
    "validate_execution",
    "validate_execution_record",
    "validate_queue",
]
