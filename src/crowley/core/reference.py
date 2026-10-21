"""Strict validation for item-reference captures produced by the addon."""

from __future__ import annotations

import copy
import datetime
import re
from typing import Any

from crowley.core.house import House

MAX_SAFE_INTEGER = 9_007_199_254_740_991
SMALLINT_MAX = 32_767
INTEGER_MAX = 2_147_483_647
BIGINT_MAX = 9_223_372_036_854_775_807
BIGINT_SAFE_MAX = min(BIGINT_MAX, MAX_SAFE_INTEGER)
INFO_FIELDS = {
    "quality",
    "itemLevel",
    "minLevel",
    "classID",
    "subclassID",
    "maxStack",
    "sellPrice",
    "bindType",
    "expansionID",
    "isCraftingReagent",
}
CONTEXT_FIELDS = {
    "character",
    "realm",
    "playerFaction",
    "zone",
    "subzone",
    "locale",
    "clientVersion",
    "clientBuild",
    "interface",
    "addonVersion",
}
HOUSE_FIELDS = {"region", "ruleset", "faction", "source", "key"}
ENVELOPE_FIELDS = {"format", "id", "house", "context", "startedAt", "finishedAt", "ahOpen", "items"}
ITEM_STATUSES = {"ok", "not_found", "load_timeout", "invalid_native"}


class ReferenceFormatError(ValueError):
    """A reference envelope does not satisfy the producer contract."""


def _keys(value: Any, expected: set[str], where: str) -> None:
    if not isinstance(value, dict):
        raise ReferenceFormatError(f"{where} must be an object")
    unknown = set(value) - expected
    missing = expected - set(value)
    if unknown:
        raise ReferenceFormatError(f"{where} has unknown fields: {sorted(unknown)}")
    if missing:
        raise ReferenceFormatError(f"{where} is missing fields: {sorted(missing)}")


def _int(
    value: Any,
    where: str,
    *,
    minimum: int = 0,
    maximum: int = MAX_SAFE_INTEGER,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum or value > maximum:
        raise ReferenceFormatError(f"{where} must be a safe integer")
    return value


def _string(value: Any, where: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value):
        raise ReferenceFormatError(f"{where} must be a {'non-empty ' if nonempty else ''}string")
    return value


def _bool(value: Any, where: str) -> bool:
    if not isinstance(value, bool):
        raise ReferenceFormatError(f"{where} must be boolean")
    return value


def _timestamp(value: Any, where: str) -> int:
    epoch = _int(value, where)
    try:
        datetime.datetime.fromtimestamp(epoch, tz=datetime.UTC)
    except (OverflowError, OSError, ValueError) as exc:
        raise ReferenceFormatError(f"{where} is not a storable timestamp") from exc
    return epoch


def _validate_house(value: Any) -> dict[str, Any]:
    _keys(value, HOUSE_FIELDS, "envelope.house")
    for key in HOUSE_FIELDS:
        _string(value[key], f"envelope.house.{key}")
    try:
        house = House(value["region"], value["ruleset"], value["faction"])
    except ValueError as exc:
        raise ReferenceFormatError(str(exc)) from exc
    if house.key != value["key"]:
        raise ReferenceFormatError("house key does not match its fields")
    return value


def _validate_context(value: Any) -> dict[str, Any]:
    _keys(value, CONTEXT_FIELDS, "envelope.context")
    for key in (
        "character",
        "realm",
        "playerFaction",
        "locale",
        "clientVersion",
        "clientBuild",
        "addonVersion",
    ):
        _string(value[key], f"envelope.context.{key}")
    for key in ("zone", "subzone"):
        _string(value[key], f"envelope.context.{key}", nonempty=False)
    _int(value["interface"], "envelope.context.interface", minimum=1)
    return value


def _validate_info(value: Any, where: str) -> dict[str, Any]:
    _keys(value, INFO_FIELDS, where)
    maximums = {
        "quality": SMALLINT_MAX,
        "itemLevel": INTEGER_MAX,
        "minLevel": INTEGER_MAX,
        "classID": INTEGER_MAX,
        "subclassID": INTEGER_MAX,
        "maxStack": INTEGER_MAX,
        "sellPrice": BIGINT_SAFE_MAX,
        "bindType": SMALLINT_MAX,
        "expansionID": INTEGER_MAX,
    }
    for key in INFO_FIELDS - {"isCraftingReagent"}:
        _int(
            value[key],
            f"{where}.{key}",
            minimum=1 if key == "maxStack" else 0,
            maximum=maximums[key],
        )
    _bool(value["isCraftingReagent"], f"{where}.isCraftingReagent")
    return value


def _quantities(max_stack: int) -> set[int]:
    return {1} if max_stack == 1 else {1, max_stack}


def _validate_deposit(value: Any, max_stack: int, ah_open: bool, where: str) -> str:
    if not isinstance(value, dict) or "kind" not in value:
        raise ReferenceFormatError(f"{where} must be a deposit object")
    kind = value["kind"]
    if ah_open:
        allowed = {"commodity", "not_commodity", "error"}
    else:
        allowed = {"unqueried"}
    if not isinstance(kind, str) or kind not in allowed:
        raise ReferenceFormatError(f"{where}.kind is invalid")
    if kind == "commodity":
        _keys(value, {"kind", "values"}, where)
        values = value["values"]
        expected_count = 3 if max_stack == 1 else 6
        if not isinstance(values, list) or len(values) != expected_count:
            raise ReferenceFormatError(f"{where}.values has the wrong number of entries")
        seen: set[tuple[int, int]] = set()
        for index, entry in enumerate(values, start=1):
            entry_where = f"{where}.values[{index}]"
            _keys(entry, {"duration", "quantity", "copper"}, entry_where)
            duration = _int(entry["duration"], f"{entry_where}.duration", minimum=1)
            if duration not in {1, 2, 3}:
                raise ReferenceFormatError(f"{entry_where}.duration is invalid")
            quantity = _int(entry["quantity"], f"{entry_where}.quantity", minimum=1)
            if quantity not in _quantities(max_stack):
                raise ReferenceFormatError(f"{entry_where}.quantity is invalid")
            _int(entry["copper"], f"{entry_where}.copper", maximum=BIGINT_SAFE_MAX)
            pair = (duration, quantity)
            if pair in seen:
                raise ReferenceFormatError(f"{where}.values has duplicate duration and quantity")
            seen.add(pair)
        expected = {(duration, quantity) for duration in (1, 2, 3) for quantity in _quantities(max_stack)}
        if seen != expected:
            raise ReferenceFormatError(f"{where}.values does not cover every duration and quantity")
    elif kind == "not_commodity":
        _keys(value, {"kind"}, where)
    elif kind == "error":
        _keys(value, {"kind", "detail"}, where)
        _string(value["detail"], f"{where}.detail")
    else:
        _keys(value, {"kind", "reason"}, where)
        if value["reason"] != "ah_closed":
            raise ReferenceFormatError(f"{where}.reason is invalid")
    return kind


def _validate_item(key: Any, value: Any, ah_open: bool) -> dict[str, Any]:
    if not isinstance(key, str) or not re.fullmatch(r"[1-9][0-9]*", key):
        raise ReferenceFormatError("items keys must be positive decimal strings")
    try:
        item_id = _int(int(key), f"items.{key}.itemID", minimum=1, maximum=BIGINT_SAFE_MAX)
    except ValueError as exc:
        raise ReferenceFormatError(f"items.{key}.itemID must be a safe integer") from exc
    if not isinstance(value, dict) or "status" not in value:
        raise ReferenceFormatError(f"items.{key} must be an object")
    status = value["status"]
    if not isinstance(status, str) or status not in ITEM_STATUSES:
        raise ReferenceFormatError(f"items.{key}.status is invalid")
    expected = {"itemID", "status"}
    if status == "ok":
        expected.update({"info", "deposit"})
    elif status == "invalid_native":
        expected.add("field")
    _keys(value, expected, f"items.{key}")
    if _int(value["itemID"], f"items.{key}.itemID", minimum=1, maximum=BIGINT_SAFE_MAX) != item_id:
        raise ReferenceFormatError(f"items.{key}.itemID does not match its key")
    if status == "ok":
        info = _validate_info(value["info"], f"items.{key}.info")
        _validate_deposit(value["deposit"], info["maxStack"], ah_open, f"items.{key}.deposit")
    elif status == "invalid_native":
        field = _string(value["field"], f"items.{key}.field")
        if field not in INFO_FIELDS:
            raise ReferenceFormatError(f"items.{key}.field is invalid")
    return value


def validate_reference_envelope(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize one addon item-reference envelope."""

    if not isinstance(raw, dict):
        raise ReferenceFormatError("envelope must be an object")
    _keys(raw, ENVELOPE_FIELDS, "envelope")
    _int(raw["format"], "envelope.format", minimum=1)
    if raw["format"] != 1:
        raise ReferenceFormatError("unsupported reference format")
    _string(raw["id"], "envelope.id")
    started = _timestamp(raw["startedAt"], "envelope.startedAt")
    finished = _timestamp(raw["finishedAt"], "envelope.finishedAt")
    if started > finished:
        raise ReferenceFormatError("envelope timestamps are unordered")
    _validate_house(raw["house"])
    _validate_context(raw["context"])
    _bool(raw["ahOpen"], "envelope.ahOpen")
    items = raw["items"]
    if not isinstance(items, dict) or not items:
        raise ReferenceFormatError("envelope.items must be a non-empty object")
    normalized_items = items
    for key, value in normalized_items.items():
        _validate_item(key, value, raw["ahOpen"])
    normalized = copy.deepcopy(raw)
    normalized["items"] = copy.deepcopy(normalized_items)
    return normalized
