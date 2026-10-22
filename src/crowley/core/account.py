"""Strict validation for account-state captures produced by the addon."""

from __future__ import annotations

import copy
import datetime
import math
import re
from typing import Any

from crowley.core.house import House

MAX_SAFE_INTEGER = 9_007_199_254_740_991
BIGINT_MAX = 9_223_372_036_854_775_807
BIGINT_SAFE_MAX = min(BIGINT_MAX, MAX_SAFE_INTEGER)
INTEGER_MAX = 2_147_483_647
SMALLINT_MAX = 32_767

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
ENVELOPE_FIELDS = {
    "format",
    "id",
    "house",
    "context",
    "capturedAt",
    "gold",
    "bags",
    "professions",
    "recipes",
    "cooldowns",
    "mail",
}


class AccountFormatError(ValueError):
    """An account-state envelope does not satisfy the producer contract."""


def _keys(value: Any, expected: set[str], where: str) -> None:
    if not isinstance(value, dict):
        raise AccountFormatError(f"{where} must be an object")
    unknown = set(value) - expected
    missing = expected - set(value)
    if unknown:
        raise AccountFormatError(f"{where} has unknown fields: {sorted(unknown)}")
    if missing:
        raise AccountFormatError(f"{where} is missing fields: {sorted(missing)}")


def _int(
    value: Any,
    where: str,
    *,
    minimum: int = 0,
    maximum: int = MAX_SAFE_INTEGER,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum or value > maximum:
        raise AccountFormatError(f"{where} must be a safe integer")
    return value


def _number(
    value: Any,
    where: str,
    *,
    minimum: float = 0,
    maximum: int = MAX_SAFE_INTEGER,
) -> int | float:
    finite = isinstance(value, int) or (isinstance(value, float) and math.isfinite(value))
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not finite
        or value < minimum
        or value > maximum
    ):
        raise AccountFormatError(f"{where} must be a finite non-negative number")
    return value


def _string(value: Any, where: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value):
        raise AccountFormatError(f"{where} must be a {'non-empty ' if nonempty else ''}string")
    return value


def _bool(value: Any, where: str) -> bool:
    if not isinstance(value, bool):
        raise AccountFormatError(f"{where} must be boolean")
    return value


def _timestamp(value: Any, where: str) -> int:
    epoch = _int(value, where)
    try:
        datetime.datetime.fromtimestamp(epoch, tz=datetime.UTC)
    except (OverflowError, OSError, ValueError) as exc:
        raise AccountFormatError(f"{where} is not a storable timestamp") from exc
    return epoch


def _empty_map_or_object(value: Any, where: str) -> dict[str, Any]:
    # An empty Lua table is encoded by the WoW JSON/SavedVariables writers as
    # an array.  Only the empty case is accepted here; populated maps remain
    # strict JSON objects.
    if value == []:
        return {}
    if not isinstance(value, dict):
        raise AccountFormatError(f"{where} must be an object")
    return value


def _empty_array(value: Any, where: str) -> list[Any]:
    # The SavedVariables parser also represents an empty Lua table as an empty
    # object.  It is unambiguous only while empty, so accept both wire shapes.
    if value == [] or value == {}:
        return []
    if not isinstance(value, list):
        raise AccountFormatError(f"{where} must be an array")
    return value


def _decimal_key(value: Any, where: str, *, maximum: int) -> int:
    if not isinstance(value, str) or re.fullmatch(r"[1-9][0-9]*", value) is None:
        raise AccountFormatError(f"{where} must be a positive decimal string")
    maximum_text = str(maximum)
    if len(value) > len(maximum_text) or (len(value) == len(maximum_text) and value > maximum_text):
        raise AccountFormatError(f"{where} must be a safe integer")
    try:
        numeric = int(value)
    except (ValueError, OverflowError) as exc:
        raise AccountFormatError(f"{where} must be a safe integer") from exc
    return _int(numeric, where, minimum=1, maximum=maximum)


def _error_section(value: Any, where: str) -> bool:
    if not isinstance(value, dict) or "kind" not in value:
        return False
    kind = value["kind"]
    if kind == "error":
        _keys(value, {"kind", "detail"}, where)
        _string(value["detail"], f"{where}.detail")
        return True
    if kind == "invalid_native":
        _keys(value, {"kind", "field"}, where)
        _string(value["field"], f"{where}.field")
        return True
    return False


def _validate_house(value: Any) -> dict[str, Any]:
    _keys(value, HOUSE_FIELDS, "envelope.house")
    for key in HOUSE_FIELDS:
        _string(value[key], f"envelope.house.{key}")
    try:
        house = House(value["region"], value["ruleset"], value["faction"])
    except ValueError as exc:
        raise AccountFormatError(str(exc)) from exc
    if house.key != value["key"]:
        raise AccountFormatError("house key does not match its fields")
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
    _int(value["interface"], "envelope.context.interface", minimum=1, maximum=INTEGER_MAX)
    return value


def _validate_bags(value: Any) -> dict[str, Any] | None:
    if _error_section(value, "envelope.bags"):
        return None
    bags = _empty_map_or_object(value, "envelope.bags")
    if set(bags) != {str(index) for index in range(5)}:
        raise AccountFormatError('envelope.bags must contain exactly keys "0" through "4"')
    for bag_key, bag in bags.items():
        where = f"envelope.bags.{bag_key}"
        _keys(bag, {"numSlots", "freeSlots", "slots"}, where)
        num_slots = _int(bag["numSlots"], f"{where}.numSlots", maximum=INTEGER_MAX)
        _int(bag["freeSlots"], f"{where}.freeSlots", maximum=num_slots)
        slots = _empty_map_or_object(bag["slots"], f"{where}.slots")
        for slot_key, slot in slots.items():
            if not isinstance(slot_key, str) or re.fullmatch(r"(?:0|[1-9][0-9]*)", slot_key) is None:
                raise AccountFormatError(f"{where}.slots keys must be decimal strings")
            if slot_key == "0":
                raise AccountFormatError(f"{where}.slots keys must be positive decimal strings")
            slot_number = _decimal_key(slot_key, f"{where}.slots.{slot_key} key", maximum=INTEGER_MAX)
            if slot_number < 1 or slot_number > num_slots:
                raise AccountFormatError(f"{where}.slots.{slot_key} is outside the bag")
            slot_where = f"{where}.slots.{slot_key}"
            _keys(slot, {"itemID", "count", "bound", "quality"}, slot_where)
            _int(slot["itemID"], f"{slot_where}.itemID", minimum=1, maximum=BIGINT_SAFE_MAX)
            _int(slot["count"], f"{slot_where}.count", minimum=1, maximum=INTEGER_MAX)
            _bool(slot["bound"], f"{slot_where}.bound")
            _int(slot["quality"], f"{slot_where}.quality", maximum=SMALLINT_MAX)
    return bags


def _validate_professions(value: Any) -> list[dict[str, Any]] | None:
    if _error_section(value, "envelope.professions"):
        return None
    value = _empty_array(value, "envelope.professions")
    seen: set[int] = set()
    for index, profession in enumerate(value, start=1):
        where = f"envelope.professions[{index}]"
        _keys(profession, {"name", "skillLineID", "level", "maxLevel"}, where)
        _string(profession["name"], f"{where}.name")
        skill_line = _int(profession["skillLineID"], f"{where}.skillLineID", minimum=1, maximum=INTEGER_MAX)
        level = _int(profession["level"], f"{where}.level", maximum=INTEGER_MAX)
        max_level = _int(profession["maxLevel"], f"{where}.maxLevel", maximum=INTEGER_MAX)
        if level > max_level:
            raise AccountFormatError(f"{where}.level exceeds maxLevel")
        if skill_line in seen:
            raise AccountFormatError(f"{where}.skillLineID is duplicated")
        seen.add(skill_line)
    return value


def _positive_decimal_map(value: Any, where: str, *, maximum: int = BIGINT_SAFE_MAX) -> dict[str, Any] | None:
    if _error_section(value, where):
        return None
    records = _empty_map_or_object(value, where)
    for key in records:
        if not isinstance(key, str) or re.fullmatch(r"[1-9][0-9]*", key) is None:
            raise AccountFormatError(f"{where} keys must be positive decimal strings")
        _decimal_key(key, f"{where}.{key} key", maximum=maximum)
    return records


def _validate_recipes(value: Any) -> dict[str, Any] | None:
    recipes = _positive_decimal_map(value, "envelope.recipes", maximum=INTEGER_MAX)
    if recipes is None:
        return None
    for skill_line, record in recipes.items():
        where = f"envelope.recipes.{skill_line}"
        _keys(record, {"capturedAt", "learned"}, where)
        _timestamp(record["capturedAt"], f"{where}.capturedAt")
        learned = _empty_array(record["learned"], f"{where}.learned")
        previous = 0
        for index, spell_id in enumerate(learned, start=1):
            spell_id = _int(spell_id, f"{where}.learned[{index}]", minimum=1, maximum=BIGINT_SAFE_MAX)
            if spell_id <= previous:
                raise AccountFormatError(f"{where}.learned must be sorted and unique")
            previous = spell_id
    return recipes


def _validate_cooldowns(value: Any) -> dict[str, Any] | None:
    cooldowns = _positive_decimal_map(value, "envelope.cooldowns")
    if cooldowns is None:
        return None
    for spell_id, record in cooldowns.items():
        where = f"envelope.cooldowns.{spell_id}"
        _keys(record, {"start", "duration"}, where)
        _number(record["start"], f"{where}.start")
        duration = _number(record["duration"], f"{where}.duration")
        if duration <= 0:
            raise AccountFormatError(f"{where}.duration must be positive")
    return cooldowns


def _validate_mail(value: Any) -> dict[str, Any]:
    if _error_section(value, "envelope.mail"):
        return value
    if not isinstance(value, dict) or "kind" not in value:
        raise AccountFormatError("envelope.mail must be an object")
    if value["kind"] == "unknown":
        _keys(value, {"kind"}, "envelope.mail")
        return value
    if value["kind"] != "observed":
        raise AccountFormatError("envelope.mail.kind is invalid")
    _keys(value, {"kind", "capturedAt", "messages"}, "envelope.mail")
    _timestamp(value["capturedAt"], "envelope.mail.capturedAt")
    messages = value["messages"]
    messages = _empty_array(messages, "envelope.mail.messages")
    for index, message in enumerate(messages, start=1):
        where = f"envelope.mail.messages[{index}]"
        _keys(message, {"money", "daysLeft", "items"}, where)
        _int(message["money"], f"{where}.money", maximum=BIGINT_SAFE_MAX)
        _number(message["daysLeft"], f"{where}.daysLeft")
        items = _empty_array(message["items"], f"{where}.items")
        for item_index, item in enumerate(items, start=1):
            item_where = f"{where}.items[{item_index}]"
            _keys(item, {"itemID", "count"}, item_where)
            _int(item["itemID"], f"{item_where}.itemID", minimum=1, maximum=BIGINT_SAFE_MAX)
            _int(item["count"], f"{item_where}.count", minimum=1, maximum=INTEGER_MAX)
    return value


def validate_account_envelope(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and copy one account-state envelope."""

    if not isinstance(raw, dict):
        raise AccountFormatError("envelope must be an object")
    _keys(raw, ENVELOPE_FIELDS, "envelope")
    if _int(raw["format"], "envelope.format", minimum=1) != 1:
        raise AccountFormatError("unsupported account format")
    _string(raw["id"], "envelope.id")
    captured_at = _timestamp(raw["capturedAt"], "envelope.capturedAt")
    house = _validate_house(raw["house"])
    context = _validate_context(raw["context"])
    if context["character"] not in raw["id"]:
        raise AccountFormatError("capture id does not contain context character")
    expected_prefix = f"{house['key']}-{context['character']}-{captured_at}-"
    if re.fullmatch(re.escape(expected_prefix) + r"[0-9]{4}", raw["id"]) is None:
        raise AccountFormatError("capture id does not match house, character and timestamp")

    gold = raw["gold"]
    if not _error_section(gold, "envelope.gold"):
        _int(gold, "envelope.gold", maximum=BIGINT_SAFE_MAX)
    _validate_bags(raw["bags"])
    _validate_professions(raw["professions"])
    recipes = _validate_recipes(raw["recipes"])
    cooldowns = _validate_cooldowns(raw["cooldowns"])
    if recipes is not None and cooldowns is not None:
        learned = {str(spell_id) for record in recipes.values() for spell_id in record["learned"]}
        if set(cooldowns) - learned:
            raise AccountFormatError("envelope.cooldowns contains an unlearned recipe")
    _validate_mail(raw["mail"])
    return copy.deepcopy(raw)
