"""Strict parsing and correlation for the native ``xinput test-xi2`` stream.

The output of ``xinput test-xi2`` is a block structured diagnostic stream.  A
source id on its own is not evidence of an input event: the block also carries
the master/source device pair, XI event class, detail, timestamp, and (for
delivered events) the target child window.  This module deliberately parses
those complete records and has no compatibility parser for hand written
``sourceid:`` snippets.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum


class InputEventError(ValueError):
    """An XI2 stream is malformed or contains an incomplete event record."""


RAW_MOTION_PENDING_LIMIT = 8
# XTEST's MotionNotify path passes button detail 0 into the X server raw
# event, and XI2 preserves that value.  This is the one accepted RawMotion
# detail across parsing, runtime admission, calibration, and the proof helper.
RAW_MOTION_DETAIL = 0
XI2_TIMESTAMP_MASK = 0xFFFFFFFF
XI2_TIMESTAMP_HALF_RANGE = 0x80000000


def xi2_timestamp_valid(value: object) -> bool:
    """Return whether *value* is an unambiguous XI2 CARD32 timestamp."""

    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= XI2_TIMESTAMP_MASK


def xi2_timestamp_elapsed(previous: int, current: int) -> int | None:
    """Return forward elapsed milliseconds in the XI2 CARD32 domain."""

    if not xi2_timestamp_valid(previous) or not xi2_timestamp_valid(current):
        return None
    elapsed = (current - previous) & XI2_TIMESTAMP_MASK
    return elapsed if elapsed < XI2_TIMESTAMP_HALF_RANGE else None


def xi2_timestamp_forward(previous: int | None, current: int) -> bool:
    """Accept equal or forward timestamps, including one CARD32 wrap."""

    return xi2_timestamp_valid(current) and (
        previous is None or xi2_timestamp_elapsed(previous, current) is not None
    )


@dataclass
class RawMotionPairing:
    """Forward-only, one-to-one correlation for raw and delivered motion."""

    pending_timestamps: list[int] = field(default_factory=list)
    pending_endpoints: list[tuple[int, int] | None] = field(default_factory=list)
    last_delivered_timestamp: int | None = None

    def queue_raw(self, timestamp: int, endpoint: tuple[int, int] | None = None) -> bool:
        """Queue one raw record until its following primary delivery."""

        if (
            not xi2_timestamp_valid(timestamp)
            # XI2 timestamps have millisecond granularity.  Two distinct
            # raw/primary pairs may therefore share one timestamp; only an
            # older record is backward evidence.
            or not xi2_timestamp_forward(self.last_delivered_timestamp, timestamp)
            or (self.pending_timestamps and not xi2_timestamp_forward(self.pending_timestamps[-1], timestamp))
            or len(self.pending_timestamps) >= RAW_MOTION_PENDING_LIMIT
        ):
            return False
        self.pending_timestamps.append(timestamp)
        self.pending_endpoints.append(endpoint)
        return True

    def observe_delivered(self, timestamp: int) -> bool:
        """Consume exactly one preceding raw record when timestamps match."""

        if not xi2_timestamp_valid(timestamp):
            return False
        pending_head = self.pending_timestamps[0] if self.pending_timestamps else None
        pending_primary = pending_head is not None and pending_head == timestamp
        if not pending_primary and not xi2_timestamp_forward(self.last_delivered_timestamp, timestamp):
            return False
        if self.pending_timestamps and not pending_primary:
            return False
        if self.pending_timestamps:
            self.pending_timestamps.pop(0)
            if self.pending_endpoints:
                self.pending_endpoints.pop(0)
        if self.last_delivered_timestamp is None or xi2_timestamp_forward(
            self.last_delivered_timestamp, timestamp
        ):
            self.last_delivered_timestamp = timestamp
        return True

    @property
    def pending(self) -> bool:
        return bool(self.pending_timestamps)


class EventClass(StrEnum):
    RAW_KEY_PRESS = "RawKeyPress"
    KEY_PRESS = "KeyPress"
    RAW_KEY_RELEASE = "RawKeyRelease"
    KEY_RELEASE = "KeyRelease"
    RAW_BUTTON_PRESS = "RawButtonPress"
    BUTTON_PRESS = "ButtonPress"
    RAW_BUTTON_RELEASE = "RawButtonRelease"
    BUTTON_RELEASE = "ButtonRelease"
    MOTION = "Motion"
    RAW_MOTION = "RawMotion"
    DEVICE_CHANGED = "DeviceChanged"
    ENTER = "Enter"
    LEAVE = "Leave"
    TOUCH_BEGIN = "TouchBegin"
    TOUCH_UPDATE = "TouchUpdate"
    TOUCH_END = "TouchEnd"
    UNKNOWN = "Unknown"


_EVENT_TYPES = {
    1: EventClass.DEVICE_CHANGED,
    2: EventClass.KEY_PRESS,
    3: EventClass.KEY_RELEASE,
    4: EventClass.BUTTON_PRESS,
    5: EventClass.BUTTON_RELEASE,
    6: EventClass.MOTION,
    7: EventClass.ENTER,
    8: EventClass.LEAVE,
    13: EventClass.RAW_KEY_PRESS,
    14: EventClass.RAW_KEY_RELEASE,
    15: EventClass.RAW_BUTTON_PRESS,
    16: EventClass.RAW_BUTTON_RELEASE,
    17: EventClass.RAW_MOTION,
    18: EventClass.TOUCH_BEGIN,
    19: EventClass.TOUCH_UPDATE,
    20: EventClass.TOUCH_END,
}
_EVENT_NAMES = {event.value.lower(): event for event in EventClass}
_BLOCK = re.compile(r"^EVENT\s+type\s+(\d+)\s+\(([^)]+)\)\s*$")
_DEVICE = re.compile(r"^\s*device:\s*(\d+)\s*\((\d+)\)\s*$")
_TIME = re.compile(r"^\s*time:\s*(\d+)\s*$")
_DETAIL = re.compile(r"^\s*detail:\s*(-?\d+)\s*$")
_WINDOWS = re.compile(
    r"^\s*windows:\s+root\s+(0x[0-9a-fA-F]+)\s+"
    r"event\s+(0x[0-9a-fA-F]+)\s+child\s+(0x[0-9a-fA-F]+)\s*$"
)
_COORD = re.compile(
    r"^\s*(root|event)(?:\s+x/y)?\s*:\s*"
    r"(-?\d+(?:\.\d+)?)\s*(?:/|\s+/\s+)\s*(-?\d+(?:\.\d+)?)\s*$"
)
_MODIFIERS = re.compile(
    r"^\s*modifiers:.*?locked\s+(0x[0-9a-fA-F]+|\d+)\s+"
    r"latched\s+(0x[0-9a-fA-F]+|\d+)\s+base\s+(0x[0-9a-fA-F]+|\d+)"
    r"(?:\s+effective:\s*(0x[0-9a-fA-F]+|\d+))?"
)
_VALUATOR = re.compile(
    r"^\s*([+-]?\d+)\s*:\s*"
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    r"(?:\s+\(([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\))?\s*$"
)
_VALUATOR_PREFIX = re.compile(r"^\s*[+-]?\d+\s*:")


def _hex(value: str) -> int:
    return int(value, 16) if value.lower().startswith("0x") else int(value)


def _event_class(number: int, name: str) -> EventClass:
    expected = _EVENT_TYPES.get(number)
    parsed = _EVENT_NAMES.get(name.strip().lower(), EventClass.UNKNOWN)
    if expected is None:
        return parsed
    if parsed is not EventClass.UNKNOWN and parsed is not expected:
        raise InputEventError(f"XI2 event type/name mismatch: {number} ({name})")
    return expected


@dataclass(frozen=True)
class XI2Event:
    """One complete event block from ``xinput test-xi2``."""

    type_number: int
    event_class: EventClass
    master_device: int
    source_device: int
    timestamp_ms: int
    detail: int | None
    root_xid: int | None
    event_xid: int | None
    child_xid: int | None
    root_xy: tuple[float, float] | None = None
    event_xy: tuple[float, float] | None = None
    modifiers: tuple[int, int, int] | None = None
    raw_lines: tuple[str, ...] = field(default_factory=tuple, repr=False)
    modifier_effective: int | None = None
    valuators: tuple[tuple[int, float, float | None], ...] = field(default_factory=tuple)

    @property
    def device_id(self) -> int:
        """The first XI2 ``device:`` field, exactly as printed by xinput."""

        return self.master_device

    @property
    def target_xid(self) -> int | None:
        """The delivered event's child target, when XI2 reports one."""

        return self.child_xid

    @property
    def is_action_event(self) -> bool:
        return self.event_class in {
            EventClass.KEY_PRESS,
            EventClass.KEY_RELEASE,
            EventClass.BUTTON_PRESS,
            EventClass.BUTTON_RELEASE,
            EventClass.MOTION,
            EventClass.RAW_MOTION,
            EventClass.TOUCH_BEGIN,
            EventClass.TOUCH_UPDATE,
            EventClass.TOUCH_END,
        }

    @property
    def is_raw(self) -> bool:
        return self.event_class in {
            EventClass.RAW_KEY_PRESS,
            EventClass.RAW_KEY_RELEASE,
            EventClass.RAW_BUTTON_PRESS,
            EventClass.RAW_BUTTON_RELEASE,
            EventClass.RAW_MOTION,
        }


def _finish(lines: list[str], header: tuple[int, str] | None) -> XI2Event:
    if header is None:
        raise InputEventError("event block has no EVENT header")
    number, name = header
    event_class = _event_class(number, name)
    master: int | None = None
    source: int | None = None
    timestamp: int | None = None
    detail: int | None = None
    root_xid: int | None = None
    event_xid: int | None = None
    child_xid: int | None = None
    root_xy: tuple[float, float] | None = None
    event_xy: tuple[float, float] | None = None
    modifiers: tuple[int, int, int] | None = None
    modifier_effective: int | None = None
    valuators: tuple[tuple[int, float, float | None], ...] = ()
    valuators_index: int | None = None
    for line_index, line in enumerate(lines):
        if match := _DEVICE.match(line):
            master, source = int(match.group(1)), int(match.group(2))
        elif match := _TIME.match(line):
            timestamp = int(match.group(1))
        elif match := _DETAIL.match(line):
            detail = int(match.group(1))
        elif match := _WINDOWS.match(line):
            root_xid, event_xid, child_xid = (_hex(match.group(i)) for i in range(1, 4))
        elif match := _COORD.match(line):
            point = (float(match.group(2)), float(match.group(3)))
            if match.group(1) == "root":
                root_xy = point
            else:
                event_xy = point
        elif match := _MODIFIERS.match(line):
            modifiers = tuple(_hex(match.group(i)) for i in range(1, 4))  # type: ignore[assignment]
            if match.group(4) is not None:
                modifier_effective = _hex(match.group(4))
        elif line.strip().startswith("valuators:"):
            if valuators_index is not None:
                raise InputEventError(f"{event_class}: duplicate valuators section")
            valuators_index = line_index
    if master is None or source is None:
        raise InputEventError(f"{event_class}: missing master/source device")
    if timestamp is None:
        raise InputEventError(f"{event_class}: missing timestamp")
    if not xi2_timestamp_valid(timestamp):
        raise InputEventError(f"{event_class}: timestamp is outside the XI2 CARD32 domain")
    if (
        event_class
        in {
            EventClass.KEY_PRESS,
            EventClass.KEY_RELEASE,
            EventClass.BUTTON_PRESS,
            EventClass.BUTTON_RELEASE,
            EventClass.RAW_KEY_PRESS,
            EventClass.RAW_KEY_RELEASE,
            EventClass.RAW_BUTTON_PRESS,
            EventClass.RAW_BUTTON_RELEASE,
        }
        and detail is None
    ):
        raise InputEventError(f"{event_class}: missing detail")
    # Raw and DeviceChanged blocks intentionally have no windows line.  Every
    # delivered key/button/motion record must have one so a source cannot be
    # correlated by device id alone.
    if (
        event_class
        in {
            EventClass.KEY_PRESS,
            EventClass.KEY_RELEASE,
            EventClass.BUTTON_PRESS,
            EventClass.BUTTON_RELEASE,
            EventClass.MOTION,
            EventClass.TOUCH_BEGIN,
            EventClass.TOUCH_UPDATE,
            EventClass.TOUCH_END,
        }
        and child_xid is None
    ):
        raise InputEventError(f"{event_class}: missing delivered child window")
    # The delivered key/button records are the physical-input contract used by
    # calibration and the runtime guardian.  A source/device pair without the
    # modifier snapshot or coordinates cannot prove which operation occurred.
    if event_class in {
        EventClass.KEY_PRESS,
        EventClass.KEY_RELEASE,
        EventClass.BUTTON_PRESS,
        EventClass.BUTTON_RELEASE,
    }:
        if modifiers is None:
            raise InputEventError(f"{event_class}: missing modifier state")
        if root_xy is None or event_xy is None:
            raise InputEventError(f"{event_class}: missing pointer coordinates")
        if modifier_effective is None:
            raise InputEventError(f"{event_class}: missing effective modifier state")
    if event_class is EventClass.MOTION and (root_xy is None or event_xy is None or modifiers is None):
        raise InputEventError(f"{event_class}: missing motion coordinates or modifier state")
    if event_class is EventClass.MOTION and modifier_effective is None:
        raise InputEventError(f"{event_class}: missing effective modifier state")
    if event_class is EventClass.RAW_MOTION:
        if detail != RAW_MOTION_DETAIL:
            raise InputEventError(f"{event_class}: detail must be {RAW_MOTION_DETAIL}")
        if valuators_index is None:
            raise InputEventError(f"{event_class}: missing valuators section")
    if valuators_index is not None:
        parsed_valuators: list[tuple[int, float, float | None]] = []
        seen_axes: set[int] = set()
        for line in lines[valuators_index + 1 :]:
            match = _VALUATOR.fullmatch(line)
            if match is None:
                if _VALUATOR_PREFIX.match(line):
                    raise InputEventError(f"{event_class}: malformed valuator row")
                continue
            axis = int(match.group(1))
            value = float(match.group(2))
            raw_value = float(match.group(3)) if match.group(3) is not None else None
            if (
                axis < 0
                or not math.isfinite(value)
                or (raw_value is not None and not math.isfinite(raw_value))
            ):
                raise InputEventError(f"{event_class}: non-finite or malformed valuator")
            if axis in seen_axes:
                raise InputEventError(f"{event_class}: duplicate valuator axis {axis}")
            seen_axes.add(axis)
            parsed_valuators.append((axis, value, raw_value))
        valuators = tuple(parsed_valuators)
        if event_class is EventClass.RAW_MOTION and not valuators:
            raise InputEventError(f"{event_class}: missing complete valuator data")
    # Crossing notifications are optional in a bounded pointer sequence, but
    # when present they still need the complete XI2 target/coordinate/state
    # record.  The live diagnostic uses ``root x/y`` rather than the slash
    # spelling used by delivered button records, so both forms are parsed
    # above.  A crossing's child may be zero (the root/frame transition), but
    # an absent child would make it impossible to correlate the transition.
    if event_class in {EventClass.ENTER, EventClass.LEAVE}:
        if child_xid is None:
            raise InputEventError(f"{event_class}: missing crossing child window")
        if root_xy is None or event_xy is None or modifiers is None:
            raise InputEventError(f"{event_class}: missing crossing coordinates or modifier state")
        if modifier_effective is None:
            raise InputEventError(f"{event_class}: missing crossing effective modifier state")
    return XI2Event(
        number,
        event_class,
        master,
        source,
        timestamp,
        detail,
        root_xid,
        event_xid,
        child_xid,
        root_xy,
        event_xy,
        modifiers,
        tuple(lines),
        modifier_effective,
        valuators,
    )


@dataclass(frozen=True)
class XTestMotionTransition:
    """One canonical attached-XTEST slave transition.

    ``origin_*`` are the native root-window coordinates printed by the slave
    Motion record.  ``endpoint_*`` are the integer-equivalent delivered
    valuators.  The two are intentionally retained separately: a slave event
    reports the pointer before the absolute XTEST transition while its
    valuators carry the requested endpoint.
    """

    timestamp_ms: int
    device_id: int
    source_device: int
    parent_device: int
    target_xid: int
    root_xid: int
    event_xid: int
    origin_root: tuple[float, float]
    origin_event: tuple[float, float]
    endpoint_root: tuple[int, int]
    endpoint_event: tuple[int, int]
    valuators: tuple[tuple[int, float, float | None], ...]
    modifiers: tuple[int, int, int]
    modifier_effective: int


def decode_xtest_motion_transition(
    event: XI2Event,
    *,
    expected_source: int,
    expected_parent: int,
    expected_root_xid: int,
    expected_child_xids: frozenset[int] | set[int] | tuple[int, ...],
    planned_endpoint: tuple[int, int] | None = None,
) -> XTestMotionTransition:
    """Decode one profile-bound absolute-XTEST primary Motion.

    This helper only interprets a delivered slave Motion.  Raw ancestry is
    correlated by the caller's FIFO state; human relative motion never enters
    this decoder.  Integer-equivalent finite valuators are required exactly,
    with no rounding or root/event coordinate translation.
    """

    if not isinstance(event, XI2Event) or event.event_class is not EventClass.MOTION:
        raise InputEventError("canonical XTEST transition requires a delivered Motion")
    if (
        isinstance(expected_source, bool)
        or not isinstance(expected_source, int)
        or expected_source <= 0
        or isinstance(expected_parent, bool)
        or not isinstance(expected_parent, int)
        or expected_parent <= 0
        or isinstance(expected_root_xid, bool)
        or not isinstance(expected_root_xid, int)
        or expected_root_xid <= 0
    ):
        raise InputEventError("canonical XTEST transition profile is malformed")
    if event.device_id != expected_source or event.source_device != expected_source:
        raise InputEventError("canonical XTEST Motion has the wrong device/source identity")
    if event.detail != RAW_MOTION_DETAIL:
        raise InputEventError("canonical XTEST Motion detail is not zero")
    if event.root_xid != expected_root_xid or event.event_xid != expected_root_xid:
        raise InputEventError("canonical XTEST Motion is not rooted at the observed root window")
    if event.child_xid not in expected_child_xids:
        raise InputEventError("canonical XTEST Motion origin is outside the owned target")
    if (
        event.root_xy is None
        or event.event_xy is None
        or event.root_xy != event.event_xy
        or event.modifiers is None
        or event.modifier_effective is None
    ):
        raise InputEventError("canonical XTEST Motion origin or modifier facts are malformed")
    if event.modifier_effective != event.modifiers[0] | event.modifiers[1] | event.modifiers[2]:
        raise InputEventError("canonical XTEST Motion modifier effects are malformed")
    if {axis for axis, _value, _raw in event.valuators} != {0, 1} or len(event.valuators) != 2:
        raise InputEventError("canonical XTEST Motion must contain exactly valuator axes 0 and 1")
    endpoints: list[int] = []
    for axis in (0, 1):
        rows = [value for row_axis, value, _raw in event.valuators if row_axis == axis]
        if len(rows) != 1 or not math.isfinite(rows[0]) or not rows[0].is_integer():
            raise InputEventError("canonical XTEST Motion valuators must be finite integer-equivalent values")
        endpoints.append(int(rows[0]))
    endpoint = (endpoints[0], endpoints[1])
    if planned_endpoint is not None and endpoint != planned_endpoint:
        raise InputEventError("canonical XTEST Motion endpoint differs from the planned endpoint")
    return XTestMotionTransition(
        event.timestamp_ms,
        event.device_id,
        event.source_device,
        expected_parent,
        int(event.child_xid),
        int(event.root_xid),
        int(event.event_xid),
        event.root_xy,
        event.event_xy,
        endpoint,
        endpoint,
        event.valuators,
        event.modifiers,
        event.modifier_effective,
    )


def parse_xi2_records(text: str, *, require_event: bool = False) -> list[XI2Event]:
    """Parse complete XI2 records from a captured trace.

    ``sourceid:`` fixtures are intentionally rejected.  A trace containing a
    source id but no complete ``EVENT`` record raises instead of being treated
    as calibration evidence.  Event blocks may be separated by arbitrary
    non-event diagnostic lines; a trailing partial block is an error.
    """

    if not isinstance(text, str):
        raise InputEventError("XI2 trace must be text")
    if re.search(r"\bsourceid\s*[:=]", text, re.IGNORECASE):
        raise InputEventError("synthetic sourceid fixture is not an XI2 record")
    records: list[XI2Event] = []
    header: tuple[int, str] | None = None
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        match = _BLOCK.match(line)
        if match:
            if header is not None:
                records.append(_finish(lines, header))
            header = (int(match.group(1)), match.group(2))
            lines = []
            continue
        if header is not None:
            lines.append(line)
    if header is not None:
        records.append(_finish(lines, header))
    if require_event and not records:
        raise InputEventError("XI2 trace contains no complete EVENT record")
    return records


class XI2StreamParser:
    """Incremental parser used by the runtime monitor."""

    def __init__(self) -> None:
        self._header: tuple[int, str] | None = None
        self._header_text = ""
        self._lines: list[str] = []
        self._saw_synthetic = False
        self._failure_reason: str | None = None
        self._failure_text = ""

    @property
    def failure_diagnostic(self) -> dict[str, str] | None:
        """Return the exact failed block and parser reason, when available."""

        if self._failure_reason is None:
            return None
        return {"text": self._failure_text, "reason": self._failure_reason}

    def _remember_failure(self, exc: InputEventError) -> None:
        self._failure_reason = str(exc)
        self._failure_text = "\n".join((self._header_text, *self._lines, ""))

    def _complete_if_ready(self, *, event_delimiter: bool = False) -> XI2Event | None:
        """Finish a block once its strict required fields have arrived.

        ``xinput test-xi2`` terminates each block with a blank line.  A raw
        motion block is committed only at that native delimiter: its
        valuator payload can span several reads, and an early header or
        valuator section must never become evidence.
        """

        if self._header is None:
            return None
        # RawMotion carries its diagnostic valuator payload after the required
        # device/time fields.  Keep the complete block buffered until the
        # native blank-line delimiter so a fragmented stream cannot emit it
        # before all valuator lines arrive.
        if _event_class(*self._header) is EventClass.RAW_MOTION and not event_delimiter:
            return None
        try:
            event = _finish(self._lines, self._header)
        except InputEventError as exc:
            if event_delimiter and _event_class(*self._header) is EventClass.RAW_MOTION:
                self._remember_failure(exc)
                raise
            return None
        self._header = None
        self._header_text = ""
        self._lines = []
        return event

    def feed(self, line: str) -> XI2Event | None:
        if re.search(r"\bsourceid\s*[:=]", line, re.IGNORECASE):
            self._saw_synthetic = True
            raise InputEventError("synthetic sourceid fixture is not an XI2 record")
        match = _BLOCK.match(line.rstrip("\r"))
        if match:
            if self._header is not None and _event_class(*self._header) is EventClass.RAW_MOTION:
                # A raw block is complete only after its native blank-line
                # delimiter.  A following header cannot silently terminate a
                # partial valuator payload.
                self._remember_failure(InputEventError("RawMotion: missing blank-line delimiter"))
                raise InputEventError("RawMotion: missing blank-line delimiter")
            completed = _finish(self._lines, self._header) if self._header is not None else None
            self._header = (int(match.group(1)), match.group(2))
            self._header_text = line.rstrip("\r\n")
            self._lines = []
            return completed
        if self._header is not None:
            normalized = line.rstrip("\r")
            if not normalized.strip():
                return self._complete_if_ready(event_delimiter=True)
            self._lines.append(normalized)
            # The final release in an idle open pipe must be observable as soon
            # as its complete windows/modifier record arrives.  Waiting for a
            # later EVENT header or EOF loses the very release that closes a
            # calibration operation.  _finish remains strict, so incomplete
            # blocks stay buffered until their required fields arrive.
            return self._complete_if_ready()
        return None

    def finish(self) -> XI2Event | None:
        if self._header is None:
            return None
        try:
            completed = _finish(self._lines, self._header)
        except InputEventError as exc:
            self._remember_failure(exc)
            raise
        self._header = None
        self._header_text = ""
        self._lines = []
        return completed


def event_name(value: EventClass | str) -> EventClass:
    """Normalize a caller's expected event name without accepting source ids."""

    if isinstance(value, EventClass):
        return value
    try:
        return _EVENT_NAMES[value.lower()]
    except KeyError as exc:
        raise InputEventError(f"unknown XI2 event class {value!r}") from exc


def source_ids(records: Iterable[XI2Event]) -> set[int]:
    """Return IDs from parsed records, including raw/device-change records."""

    return {record.source_device for record in records}


__all__ = [
    "EventClass",
    "InputEventError",
    "RAW_MOTION_PENDING_LIMIT",
    "XI2_TIMESTAMP_HALF_RANGE",
    "XI2_TIMESTAMP_MASK",
    "RawMotionPairing",
    "XI2Event",
    "XTestMotionTransition",
    "XI2StreamParser",
    "decode_xtest_motion_transition",
    "event_name",
    "parse_xi2_records",
    "source_ids",
    "xi2_timestamp_elapsed",
    "xi2_timestamp_forward",
    "xi2_timestamp_valid",
]
