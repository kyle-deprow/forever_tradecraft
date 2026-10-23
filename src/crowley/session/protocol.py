"""Lossless framed status protocol used by the Crowley addon agent.

The game surface is deliberately small and strict.  This module owns the byte-level
contract; controller code consumes only :class:`Snapshot` instances returned by
``decode_frame``.
"""

from __future__ import annotations

import binascii
import json
import math
import re
import struct
import zlib
from collections.abc import Collection
from dataclasses import dataclass
from typing import Any

MAGIC = b"CRS1"
VERSION = 1
ENCODING = 1
WIDTH = HEIGHT = 128
HEADER_SIZE = 26
CAPACITY = 2048
MAX_PAYLOAD = 2000
MAX_INFLATED = 16_384
CELL_PHYSICAL = 2
MAX_U32 = 0xFFFFFFFF
HALF_U32 = 0x80000000
POSITION_LIMIT = 1_000_000.0
FACING_LIMIT = 2.0 * math.pi
SPEED_LIMIT = 1_000.0


class ProtocolError(ValueError):
    """A frame or snapshot is not admissible."""


@dataclass(frozen=True)
class Snapshot:
    value: dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self.value[key]


@dataclass(frozen=True)
class Frame:
    snapshot: Snapshot
    boot: str
    sequence: int
    wall_time: int
    uptime_ms: int
    crc32: int
    payload_length: int


def _error(path: str, message: str) -> ProtocolError:
    return ProtocolError(f"{path}: {message}")


def _integer(value: Any, path: str, *, minimum: int = 0, maximum: int = MAX_U32) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise _error(path, f"expected integer in [{minimum}, {maximum}]")
    return value


def _string(value: Any, path: str, *, empty: bool = False, limit: int = 256) -> str:
    if not isinstance(value, str) or (not empty and not value):
        raise _error(path, "expected string")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise _error(path, "value is not valid UTF-8") from exc
    if len(encoded) > limit:
        raise _error(path, "UTF-8 value is too long")
    return value


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise _error(path, "expected boolean")
    return value


def _number(value: Any, path: str, *, minimum: float = 0.0, maximum: float = 1_000_000.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _error(path, "expected finite number")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise _error(path, "expected finite number") from exc
    if result != result or result in (float("inf"), float("-inf")) or not minimum <= result <= maximum:
        raise _error(path, "number is outside the allowed range")
    return result


def _finite_number(
    value: Any,
    path: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _error(path, "expected finite number")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise _error(path, "expected finite number") from exc
    if (
        result != result
        or result in (float("inf"), float("-inf"))
        or (minimum is not None and result < minimum)
        or (maximum is not None and result > maximum)
    ):
        raise _error(path, "expected finite number in the allowed range")
    return result


def _binding(value: Any, path: str) -> str:
    binding = _string(value, path, limit=32)
    if not re.fullmatch(r"[A-Z0-9]+(?:-[A-Z0-9]+)*", binding):
        raise _error(path, "must use the observed native binding syntax")
    return binding


_NATIVE_FAILURES = {"call_error", "missing", "wrong_type", "nil_result"}
_GROUND_VALUES = {"false", "true", "unknown"}


def _validate_native(value: Any, *, speed: Any) -> None:
    native = _keys(value, {"ctm", "ground", "speedTuple"}, "motion.native")
    ctm = _keys(native["ctm"], {"accessor", "cvar", "state", "reason"}, "motion.native.ctm")
    if ctm["accessor"] != "C_CVar.GetCVarBool":
        raise _error("motion.native.ctm.accessor", "must be C_CVar.GetCVarBool")
    if ctm["cvar"] != "autointeract":
        raise _error("motion.native.ctm.cvar", "must be autointeract")
    ctm_state = ctm["state"]
    if not isinstance(ctm_state, str) or ctm_state not in {"disabled", "enabled", "unknown"}:
        raise _error("motion.native.ctm.state", "invalid state")
    ctm_reason = ctm["reason"]
    if not isinstance(ctm_reason, str) or ctm_reason not in {"", *_NATIVE_FAILURES}:
        raise _error("motion.native.ctm.reason", "invalid failure code")
    if ctm_state == "unknown" and not ctm_reason:
        raise _error("motion.native.ctm", "unknown state requires a failure code")
    if ctm_state != "unknown" and ctm_reason:
        raise _error("motion.native.ctm", "known state requires an empty reason")

    ground = _keys(
        native["ground"],
        {"state", "falling", "flying", "swimming", "submerged", "mounted", "taxi", "reason"},
        "motion.native.ground",
    )
    ground_state = ground["state"]
    if not isinstance(ground_state, str) or ground_state not in {"grounded", "not_grounded", "unknown"}:
        raise _error("motion.native.ground.state", "invalid state")
    unknown_fields = []
    any_true = False
    for name in ("falling", "flying", "swimming", "submerged", "mounted", "taxi"):
        predicate = ground[name]
        if not isinstance(predicate, str) or predicate not in _GROUND_VALUES:
            raise _error(f"motion.native.ground.{name}", "invalid predicate state")
        unknown_fields.append(name) if predicate == "unknown" else None
        any_true = any_true or predicate == "true"
    ground_reason = ground["reason"]
    if not isinstance(ground_reason, str) or ground_reason not in {"", *_NATIVE_FAILURES}:
        raise _error("motion.native.ground.reason", "invalid failure code")
    if unknown_fields:
        if ground_state != "unknown" or not ground_reason:
            raise _error(
                "motion.native.ground", "unknown predicate requires unknown state and a failure code"
            )
    else:
        if ground_reason:
            raise _error("motion.native.ground", "known predicates require an empty reason")
        expected_state = "not_grounded" if any_true else "grounded"
        if ground_state != expected_state:
            raise _error("motion.native.ground", "state contradicts predicate values")

    speed_tuple = _keys(
        native["speedTuple"],
        {"current", "run", "flight", "swim", "unitStatus"},
        "motion.native.speedTuple",
    )
    for name in ("current", "run", "flight", "swim"):
        _finite_number(
            speed_tuple[name],
            f"motion.native.speedTuple.{name}",
            minimum=0.0,
            maximum=SPEED_LIMIT,
        )
    if speed_tuple["unitStatus"] != "unverified":
        raise _error("motion.native.speedTuple.unitStatus", "must be unverified")
    if speed_tuple["current"] != speed:
        raise _error("motion.native.speedTuple.current", "must equal motion.speed")


def _validate_motion(value: Any) -> None:
    motion = _keys(
        value,
        {"position", "facing", "speed", "combat", "deadOrGhost", "bindings", "native"},
        "motion",
    )
    position = _keys(motion["position"], {"x", "y", "z", "instance"}, "motion.position")
    for axis in ("x", "y", "z"):
        _finite_number(
            position[axis],
            f"motion.position.{axis}",
            minimum=-POSITION_LIMIT,
            maximum=POSITION_LIMIT,
        )
    _integer(position["instance"], "motion.position.instance", maximum=MAX_U32)
    _finite_number(motion["facing"], "motion.facing", minimum=0.0, maximum=FACING_LIMIT)
    _finite_number(motion["speed"], "motion.speed", minimum=0.0, maximum=SPEED_LIMIT)
    _boolean(motion["combat"], "motion.combat")
    _boolean(motion["deadOrGhost"], "motion.deadOrGhost")
    bindings = _keys(
        motion["bindings"],
        {"moveForward", "moveBackward", "strafeLeft", "strafeRight", "turnLeft"},
        "motion.bindings",
    )
    for name in ("moveForward", "moveBackward", "strafeLeft", "strafeRight", "turnLeft"):
        _binding(bindings[name], f"motion.bindings.{name}")
    _validate_native(motion["native"], speed=motion["speed"])


def _keys(value: Any, expected: set[str], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _error(path, "expected object")
    # JSON objects normally have string keys, but callers can hand this
    # validator a decoded Python object directly.  Do the type check before
    # producing diagnostics so malformed values always use ProtocolError
    # instead of leaking a heterogeneous-key TypeError from sorted().
    if any(not isinstance(key, str) for key in value):
        raise _error(path, "object keys must be strings")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual, key=lambda item: item.encode("utf-8"))
        unknown = sorted(actual - expected, key=lambda item: item.encode("utf-8"))
        raise _error(path, f"keys differ; missing={missing}, unknown={unknown}")
    return value


def _uid(value: Any, path: str, *, empty: bool = False) -> str:
    return _string(value, path, empty=empty, limit=192)


def _uid_array(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise _error(path, "expected array")
    result = [_uid(item, f"{path}[]") for item in value]
    if len(result) != len(set(result)) or result != sorted(result, key=lambda item: item.encode()):
        raise _error(path, "UIDs must be unique and byte-sorted")
    return result


def validate_snapshot(value: Any, *, plan_item_ids: Collection[int] | None = None) -> Snapshot:
    """Validate the complete snapshot and its cross-field invariants."""

    top = _keys(
        value,
        {
            "schema",
            "boot",
            "sequence",
            "wallTime",
            "uptimeMs",
            "context",
            "house",
            "plan",
            "ahOpen",
            "auctioneer",
            "blockingUI",
            "scanner",
            "lastSaved",
            "pending",
            "loaded",
            "chatEdit",
            "motion",
            "render",
        },
        "snapshot",
    )
    if _integer(top["schema"], "schema", minimum=4, maximum=4) != 4:
        raise _error("schema", "must be 4")
    _string(top["boot"], "boot", limit=96)
    # The addon increments before its first publication; zero is reserved for
    # an absent/uninitialized frame and cannot establish freshness.
    _integer(top["sequence"], "sequence", minimum=1)
    wall_time = _integer(top["wallTime"], "wallTime")
    _integer(top["uptimeMs"], "uptimeMs")

    render = _keys(
        top["render"],
        {
            "constructionSeconds",
            "updateCount",
            "updateP99Ms",
            "textureCount",
            "effectiveScale",
            "cellSize",
            "luaHeap",
            "nativePhase",
            "nativeOrdinal",
        },
        "render",
    )
    _number(render["constructionSeconds"], "render.constructionSeconds", maximum=60)
    _integer(render["updateCount"], "render.updateCount", maximum=10_000_000)
    _number(render["updateP99Ms"], "render.updateP99Ms", maximum=60_000)
    # Texture count is a bounded native diagnostic.  The pixel, timing, and
    # memory gates establish the actual render contract; this field must stay
    # finite and positive without freezing the implementation to the retired
    # one-texture-per-bit layout.
    _integer(render["textureCount"], "render.textureCount", minimum=1, maximum=16_384)
    _number(render["effectiveScale"], "render.effectiveScale", minimum=0.0001, maximum=100)
    heap = _keys(
        render["luaHeap"],
        {"method", "available", "beforeKiB", "afterKiB", "netKiB"},
        "render.luaHeap",
    )
    if heap["method"] != "collectgarbage_count":
        raise _error("render.luaHeap.method", "must be collectgarbage_count")
    _boolean(heap["available"], "render.luaHeap.available")
    before_heap = _finite_number(heap["beforeKiB"], "render.luaHeap.beforeKiB", minimum=0)
    after_heap = _finite_number(heap["afterKiB"], "render.luaHeap.afterKiB", minimum=0)
    net_heap = _finite_number(heap["netKiB"], "render.luaHeap.netKiB")
    if not heap["available"]:
        if before_heap != 0 or after_heap != 0 or net_heap != 0:
            raise _error("render.luaHeap", "unavailable measurement must use zero values")
    elif net_heap != after_heap - before_heap:
        raise _error("render.luaHeap.netKiB", "must equal afterKiB-beforeKiB")
    phase = render["nativePhase"]
    # Check the wire type before membership: malformed JSON lists/dicts must
    # become the protocol error exposed to callers, never an unhashable-value
    # TypeError from the set lookup.
    if not isinstance(phase, str) or phase not in {"normal", "held", "updates"}:
        raise _error("render.nativePhase", "must be normal, held, or updates")
    ordinal = _integer(render["nativeOrdinal"], "render.nativeOrdinal", maximum=100)
    if phase == "normal" and ordinal != 0:
        raise _error("render.nativeOrdinal", "normal phase requires ordinal zero")
    if phase == "held" and ordinal not in {0, 100}:
        raise _error("render.nativeOrdinal", "held phase requires ordinal zero or one hundred")
    if phase == "updates" and not 1 <= ordinal <= 99:
        raise _error("render.nativeOrdinal", "updates phase requires ordinal 1..99")
    cell_size = render["cellSize"]
    if (
        not isinstance(cell_size, list)
        or len(cell_size) != 2
        or any(isinstance(value, bool) or not isinstance(value, int) or value != 2 for value in cell_size)
    ):
        raise _error("render.cellSize", "must be the pinned [2, 2] physical grid")

    context = _keys(
        top["context"],
        {
            "addonVersion",
            "interface",
            "clientBuild",
            "character",
            "realm",
            "playerFaction",
            "zone",
            "subzone",
            "locale",
            "clientVersion",
        },
        "context",
    )
    for key in (
        "addonVersion",
        "clientBuild",
        "character",
        "realm",
        "playerFaction",
        "locale",
        "clientVersion",
    ):
        _string(context[key], f"context.{key}", empty=key in {"character", "realm"})
    for key in ("zone", "subzone"):
        _string(context[key], f"context.{key}", empty=True)
    _integer(context["interface"], "context.interface", minimum=1)

    house = _keys(top["house"], {"key", "source"}, "house")
    _string(house["key"], "house.key")
    _string(house["source"], "house.source")

    plan = _keys(
        top["plan"], {"hash", "count", "cadenceSeconds", "sweepCapSeconds", "initialPriceLevels"}, "plan"
    )
    _string(plan["hash"], "plan.hash")
    if not re.fullmatch(r"[0-9a-f]{64}", plan["hash"]):
        raise _error("plan.hash", "must be lowercase SHA-256 hex")
    if _integer(plan["count"], "plan.count", minimum=1) != 428:
        raise _error("plan.count", "must be 428")
    if (
        _integer(plan["cadenceSeconds"], "plan.cadenceSeconds", minimum=900, maximum=900) != 900
        or _integer(plan["sweepCapSeconds"], "plan.sweepCapSeconds", minimum=600, maximum=600) != 600
        or _integer(plan["initialPriceLevels"], "plan.initialPriceLevels", minimum=20, maximum=20) != 20
    ):
        raise _error("plan", "cadence, cap, and retained levels must be 900/600/20")

    _boolean(top["ahOpen"], "ahOpen")
    auctioneer = _keys(
        top["auctioneer"],
        {
            "targetPresent",
            "targetName",
            "rangeAvailable",
            "withinTradeRange",
            "bindingAvailable",
            "ctrlF12Action",
            "interactionMode",
        },
        "auctioneer",
    )
    target_present = _boolean(auctioneer["targetPresent"], "auctioneer.targetPresent")
    target_name = _string(auctioneer["targetName"], "auctioneer.targetName", empty=True, limit=128)
    range_available = _boolean(auctioneer["rangeAvailable"], "auctioneer.rangeAvailable")
    within_trade_range = _boolean(auctioneer["withinTradeRange"], "auctioneer.withinTradeRange")
    binding_available = _boolean(auctioneer["bindingAvailable"], "auctioneer.bindingAvailable")
    binding_action = _string(auctioneer["ctrlF12Action"], "auctioneer.ctrlF12Action", empty=True, limit=128)
    interaction_mode = auctioneer["interactionMode"]
    if not isinstance(interaction_mode, str) or interaction_mode not in {
        "disabled",
        "gamepad",
        "keyboard",
        "any",
        "unavailable",
    }:
        raise _error("auctioneer.interactionMode", "invalid native SoftTargetInteract mode")
    if not target_present and (target_name or range_available or within_trade_range):
        raise _error("auctioneer", "absent target must have empty name and unavailable range")
    if target_present and not target_name:
        raise _error("auctioneer.targetName", "present target requires a native name")
    if within_trade_range and not range_available:
        raise _error("auctioneer.withinTradeRange", "cannot be true when range is unavailable")
    if not binding_available and binding_action:
        raise _error("auctioneer.ctrlF12Action", "unavailable binding must have an empty action")
    blocking_ui = _keys(
        top["blockingUI"],
        {
            "staticPopupAvailable",
            "staticPopupShown",
            "gameMenuAvailable",
            "gameMenuShown",
        },
        "blockingUI",
    )
    for name in ("staticPopupAvailable", "staticPopupShown", "gameMenuAvailable", "gameMenuShown"):
        _boolean(blocking_ui[name], f"blockingUI.{name}")
    if blocking_ui["staticPopupShown"] and not blocking_ui["staticPopupAvailable"]:
        raise _error("blockingUI.staticPopupShown", "cannot be true when unavailable")
    if blocking_ui["gameMenuShown"] and not blocking_ui["gameMenuAvailable"]:
        raise _error("blockingUI.gameMenuShown", "cannot be true when unavailable")
    scanner = _keys(
        top["scanner"],
        {
            "phase",
            "activeSweepId",
            "startedAt",
            "dueAt",
            "ordinal",
            "planned",
            "cursorItemID",
            "scheduleFence",
        },
        "scanner",
    )
    phase = scanner["phase"]
    if not isinstance(phase, str) or phase not in {"ready", "scheduled", "item", "owned", "blocked"}:
        raise _error("scanner.phase", "invalid phase")
    active_id = _uid(scanner["activeSweepId"], "scanner.activeSweepId", empty=True)
    started = _integer(scanner["startedAt"], "scanner.startedAt")
    due = _integer(scanner["dueAt"], "scanner.dueAt")
    ordinal = _integer(scanner["ordinal"], "scanner.ordinal")
    planned = _integer(scanner["planned"], "scanner.planned", minimum=0)
    cursor_item_id = _integer(scanner["cursorItemID"], "scanner.cursorItemID")
    schedule_fence = _keys(
        scanner["scheduleFence"],
        {"state", "reason", "command"},
        "scanner.scheduleFence",
    )
    fence_state = schedule_fence["state"]
    if not isinstance(fence_state, str) or fence_state not in {"inactive", "armed", "refused"}:
        raise _error("scanner.scheduleFence.state", "must be inactive, armed, or refused")
    if schedule_fence["command"] != "/crowley session fence":
        raise _error("scanner.scheduleFence.command", "must be /crowley session fence")
    if fence_state == "refused":
        if schedule_fence["reason"] != "scan_active":
            raise _error("scanner.scheduleFence.reason", "refused fence must report scan_active")
    elif schedule_fence["reason"] != "":
        raise _error("scanner.scheduleFence.reason", "non-refused fence must have an empty reason")
    _string(schedule_fence["reason"], "scanner.scheduleFence.reason", empty=True, limit=64)
    if plan_item_ids is not None:
        try:
            configured_ids = frozenset(plan_item_ids)
        except TypeError as exc:
            raise _error("plan.itemIDs", "configured item IDs are not iterable") from exc
        if any(isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in configured_ids):
            raise _error("plan.itemIDs", "configured item IDs are invalid")
        if cursor_item_id and cursor_item_id not in configured_ids:
            raise _error("scanner.cursorItemID", "cursor is outside the configured plan")
    if planned != 428:
        raise _error("scanner.planned", "must be 428")
    if phase in {"ready", "scheduled", "blocked"} and (active_id or started):
        raise _error("scanner", "inactive phase cannot have active ID/start")
    if phase == "scheduled" and due == 0:
        raise _error("scanner.dueAt", "scheduled phase needs a due time")
    if phase == "scheduled" and due < wall_time:
        raise _error("scanner.dueAt", "scheduled due time is stale")
    if phase in {"item", "owned"}:
        # The existing scanner creates its UID only at Finish.  The empty string is
        # an explicit wire sentinel; Lua nil must never be used for this field.
        if active_id or started == 0 or due != started + 900 or not 1 <= ordinal <= planned:
            raise _error("scanner", "active phase timing/ordinal invariant failed")
        if not started <= wall_time <= due:
            raise _error("scanner", "active phase is outside its cadence interval")
    if phase == "blocked" and ordinal != 0:
        raise _error("scanner.ordinal", "blocked phase must have ordinal zero")

    last = _keys(
        top["lastSaved"],
        {"memoryUid", "finishedAt", "planned", "attempted", "failures", "rows", "persistence"},
        "lastSaved",
    )
    memory_uid = _uid(last["memoryUid"], "lastSaved.memoryUid", empty=True)
    finished = _integer(last["finishedAt"], "lastSaved.finishedAt")
    last_planned = _integer(last["planned"], "lastSaved.planned")
    attempted = _integer(last["attempted"], "lastSaved.attempted")
    failures = _integer(last["failures"], "lastSaved.failures")
    _integer(last["rows"], "lastSaved.rows")
    if last["persistence"] != "unknown":
        raise _error("lastSaved.persistence", "must be unknown")
    if not memory_uid:
        if finished or any(last[key] for key in ("planned", "attempted", "failures", "rows")):
            raise _error("lastSaved", "empty UID requires zero counters")
    elif (
        finished == 0
        or last_planned != 428
        or attempted > last_planned
        or failures < last_planned - attempted
        or failures > last_planned
    ):
        raise _error("lastSaved", "counter invariant failed")
    if failures > attempted + (last_planned - attempted):
        raise _error("lastSaved.failures", "outside planned tail bound")

    pending = _keys(top["pending"], {"ids", "count", "cap", "blocked", "reason"}, "pending")
    pending_ids = _uid_array(pending["ids"], "pending.ids")
    pending_count = _integer(pending["count"], "pending.count", maximum=6)
    pending_cap = _integer(pending["cap"], "pending.cap", minimum=6, maximum=6)
    if pending_count != len(pending_ids) or pending_cap != 6 or pending_count > 6:
        raise _error("pending", "count/cap invariant failed")
    blocked = _boolean(pending["blocked"], "pending.blocked")
    reason = _string(pending["reason"], "pending.reason", empty=True)
    if blocked and reason not in {"queue_full", "plan_invalid"}:
        raise _error("pending.reason", "blocked queue reason is not recognized")
    if not blocked and reason:
        raise _error("pending", "blocked/reason invariant failed")
    if reason == "queue_full" and pending["count"] != pending["cap"]:
        raise _error("pending.reason", "queue_full requires a full queue")
    if phase == "blocked" and not blocked:
        raise _error("scanner.phase", "blocked phase requires pending.blocked")
    if blocked and phase != "blocked":
        raise _error("pending", "blocked queue requires blocked scanner phase")

    loaded = _keys(top["loaded"], {"ackedIds", "generatedAt"}, "loaded")
    _uid_array(loaded["ackedIds"], "loaded.ackedIds")
    _integer(loaded["generatedAt"], "loaded.generatedAt")
    chat = _keys(top["chatEdit"], {"active", "focused", "text"}, "chatEdit")
    _boolean(chat["active"], "chatEdit.active")
    _boolean(chat["focused"], "chatEdit.focused")
    _string(chat["text"], "chatEdit.text", empty=True, limit=128)
    _validate_motion(top["motion"])
    return Snapshot(dict(top))


def _u16(value: int) -> bytes:
    return struct.pack("<H", value)


def _u32(value: int) -> bytes:
    return struct.pack("<I", value & MAX_U32)


def encode_payload(snapshot: dict[str, Any], *, plan_item_ids: Collection[int] | None = None) -> bytes:
    validate_snapshot(snapshot, plan_item_ids=plan_item_ids)
    raw = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    compressor = zlib.compressobj(wbits=-15)
    compressed = compressor.compress(raw) + compressor.flush()
    if not 1 <= len(compressed) <= MAX_PAYLOAD:
        raise ProtocolError(f"compressed payload length {len(compressed)} outside 1..{MAX_PAYLOAD}")
    return compressed


def encode_frame(snapshot: dict[str, Any], *, plan_item_ids: Collection[int] | None = None) -> bytes:
    """Encode a validated snapshot into the exact 2048-byte frame."""

    validate_snapshot(snapshot, plan_item_ids=plan_item_ids)
    payload = encode_payload(snapshot, plan_item_ids=plan_item_ids)
    header = b"".join(
        (
            MAGIC,
            bytes((VERSION, ENCODING, WIDTH, HEIGHT)),
            _u16(len(payload)),
            _u32(snapshot["sequence"]),
            _u32(snapshot["wallTime"]),
            _u32(snapshot["uptimeMs"]),
        )
    )
    checksum = binascii.crc32(header + payload) & MAX_U32
    frame = header + _u32(checksum) + payload
    if len(frame) > CAPACITY:
        raise ProtocolError("frame exceeds canvas capacity")
    return frame + bytes(CAPACITY - len(frame))


def _inflate(payload: bytes) -> bytes:
    decompressor = zlib.decompressobj(-15)
    try:
        raw = decompressor.decompress(payload, MAX_INFLATED + 1)
        if len(raw) > MAX_INFLATED:
            raise ProtocolError("inflated payload exceeds limit")
        remaining = MAX_INFLATED + 1 - len(raw)
        raw += decompressor.flush(remaining)
    except ProtocolError:
        raise
    except (zlib.error, ValueError) as exc:
        raise ProtocolError(f"invalid raw deflate: {exc}") from exc
    if (
        len(raw) > MAX_INFLATED
        or not decompressor.eof
        or decompressor.unused_data
        or decompressor.unconsumed_tail
    ):
        raise ProtocolError("inflated payload exceeds limit or is truncated")
    return raw


def decode_frame(frame: bytes, *, plan_item_ids: Collection[int] | None = None) -> Frame:
    if not isinstance(frame, (bytes, bytearray)) or len(frame) != CAPACITY:
        raise ProtocolError(f"frame must be exactly {CAPACITY} bytes")
    if frame[:4] != MAGIC:
        raise ProtocolError("bad magic")
    if frame[4] != VERSION or frame[5] != ENCODING or frame[6] != WIDTH or frame[7] != HEIGHT:
        raise ProtocolError("unsupported frame header")
    payload_length = struct.unpack_from("<H", frame, 8)[0]
    if not 1 <= payload_length <= MAX_PAYLOAD:
        raise ProtocolError("payload length outside 1..2000")
    sequence, wall_time, uptime_ms, expected_crc = struct.unpack_from("<IIII", frame, 10)
    payload = frame[HEADER_SIZE : HEADER_SIZE + payload_length]
    if any(frame[HEADER_SIZE + payload_length :]):
        raise ProtocolError("nonzero padding")
    actual_crc = binascii.crc32(frame[:22] + payload) & MAX_U32
    if actual_crc != expected_crc:
        raise ProtocolError("CRC mismatch")
    try:
        value = json.loads(_inflate(payload).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"invalid snapshot JSON: {exc}") from exc
    snapshot = validate_snapshot(value, plan_item_ids=plan_item_ids)
    if (
        snapshot["sequence"] != sequence
        or snapshot["wallTime"] != wall_time
        or snapshot["uptimeMs"] != uptime_ms
    ):
        raise ProtocolError("header and JSON freshness fields disagree")
    return Frame(snapshot, snapshot["boot"], sequence, wall_time, uptime_ms, expected_crc, payload_length)


def pack_cells(frame: bytes) -> list[list[int]]:
    """Return 128 rows of 128 black/white cell bits, LSB-first."""

    if len(frame) != CAPACITY:
        raise ProtocolError("frame must be encoded before cell packing")
    rows: list[list[int]] = []
    for row in range(HEIGHT):
        bits: list[int] = []
        for byte in frame[row * 16 : (row + 1) * 16]:
            bits.extend((byte >> bit) & 1 for bit in range(8))
        rows.append(bits)
    return rows


def unpack_cells(rows: list[list[int]]) -> bytes:
    if len(rows) != HEIGHT or any(len(row) != WIDTH for row in rows):
        raise ProtocolError("cell grid must be 128x128")
    output = bytearray(CAPACITY)
    for cell, value in enumerate(bit for row in rows for bit in row):
        if isinstance(value, bool) or value not in (0, 1):
            raise ProtocolError("cell must be black or white")
        output[cell // 8] |= value << (cell % 8)
    return bytes(output)


def unsigned_delta(new: int, old: int) -> int:
    """Wrap-safe uint32 delta, rejecting the ambiguous half-range."""

    delta = (new - old) & MAX_U32
    if delta >= HALF_U32:
        raise ProtocolError("ambiguous or backwards uint32 freshness value")
    return delta
