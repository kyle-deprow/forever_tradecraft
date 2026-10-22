"""Offline route calibration and deterministic walking plans.

This module deliberately has no connection to the session daemon or to the game.  The
recording reader is kept here because the route format is intended to be reproducible
from the raw, read-only telemetry and input captures.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple

TAU = math.tau
MIN_HUMAN_HOLD_SECONDS = 0.03
TRACE_STEP_SECONDS = 0.005
_EPS = 1e-9
_KEYS = frozenset({"W", "Left", "Right", "space"})
_CAPTURE_KEYS = frozenset(
    {"W", "A", "S", "D", "Q", "E", "space", "Up", "Down", "Left", "Right", "Shift_L", "Control_L", "F12"}
)
_GROUND_VALUES = frozenset({"grounded", "not_grounded"})
_BOOL_TEXT = frozenset({"true", "false"})
_TURN_KEYS = frozenset({"Left", "Right"})
_STYLE_FIELDS = (
    "forward_hold",
    "forward_gap",
    "turn_tap",
    "strafe_tap",
    "jump_press",
    "jump_interval",
    "arrive_pause",
)


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    return result


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _exact_bool(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def _exact_int(value: Any, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer")
    return value


def _capture_bool_text(value: Any, name: str) -> bool:
    if type(value) is not str or value not in _BOOL_TEXT:
        raise ValueError(f"{name} must be 'true' or 'false'")
    return value == "true"


def _normal_angle(angle: float) -> float:
    return angle % TAU


def _angle_delta(angle: float) -> float:
    return (angle + math.pi) % TAU - math.pi


def _strict_dict(value: Any, expected: set[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    actual = set(value)
    missing = expected - actual
    unknown = actual - expected
    if missing:
        raise ValueError(f"{name} missing keys: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"{name} has unknown keys: {', '.join(sorted(unknown))}")
    return value


@dataclass(frozen=True)
class Pose:
    x: float
    y: float
    facing: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", _finite(self.x, "x"))
        object.__setattr__(self, "y", _finite(self.y, "y"))
        object.__setattr__(self, "facing", _normal_angle(_finite(self.facing, "facing")))

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "facing": self.facing}

    @classmethod
    def from_dict(cls, value: Any) -> Pose:
        data = _strict_dict(value, {"x", "y", "facing"}, "pose")
        return cls(data["x"], data["y"], data["facing"])


@dataclass(frozen=True)
class Kinematics:
    run_speed: float
    turn_rate_left: float
    turn_rate_right: float
    jump_airtime: float

    def __post_init__(self) -> None:
        run_speed = _finite(self.run_speed, "run_speed")
        left = _finite(self.turn_rate_left, "turn_rate_left")
        right = _finite(self.turn_rate_right, "turn_rate_right")
        airtime = _finite(self.jump_airtime, "jump_airtime")
        if run_speed <= 0 or airtime <= 0 or airtime > 10:
            raise ValueError("run_speed and jump_airtime must be positive; jump_airtime must be <= 10")
        if left == 0 or right == 0:
            raise ValueError("turn rates must be non-zero")
        if left * right >= 0:
            raise ValueError("Left and Right turn rates must have opposite signs")
        object.__setattr__(self, "run_speed", run_speed)
        object.__setattr__(self, "turn_rate_left", left)
        object.__setattr__(self, "turn_rate_right", right)
        object.__setattr__(self, "jump_airtime", airtime)

    def to_dict(self) -> dict[str, float]:
        return {
            "run_speed": self.run_speed,
            "turn_rate_left": self.turn_rate_left,
            "turn_rate_right": self.turn_rate_right,
            "jump_airtime": self.jump_airtime,
        }

    @classmethod
    def from_dict(cls, value: Any) -> Kinematics:
        data = _strict_dict(
            value,
            {"run_speed", "turn_rate_left", "turn_rate_right", "jump_airtime"},
            "kinematics",
        )
        return cls(data["run_speed"], data["turn_rate_left"], data["turn_rate_right"], data["jump_airtime"])


@dataclass(frozen=True)
class Style:
    forward_hold: tuple[float, ...]
    forward_gap: tuple[float, ...]
    turn_tap: tuple[float, ...]
    strafe_tap: tuple[float, ...]
    jump_press: tuple[float, ...]
    jump_interval: tuple[float, ...]
    arrive_pause: tuple[float, ...]

    def __post_init__(self) -> None:
        for field in _STYLE_FIELDS:
            raw = getattr(self, field)
            if isinstance(raw, (str, bytes)):
                raise ValueError(f"{field} must be a sequence of samples")
            try:
                samples = tuple(_finite(item, f"{field} sample") for item in raw)
            except TypeError as exc:
                raise ValueError(f"{field} must be a sequence of samples") from exc
            if len(samples) < 3:
                raise ValueError(f"{field} needs at least 3 samples")
            if any(sample <= 0 or sample > 10 for sample in samples):
                raise ValueError(f"{field} samples must be in (0, 10]")
            if any(sample < MIN_HUMAN_HOLD_SECONDS for sample in samples):
                raise ValueError(f"{field} samples must be at least {MIN_HUMAN_HOLD_SECONDS} seconds")
            if samples != tuple(sorted(samples)):
                raise ValueError(f"{field} samples must be sorted")
            object.__setattr__(self, field, samples)

    def to_dict(self) -> dict[str, list[float]]:
        return {field: list(getattr(self, field)) for field in _STYLE_FIELDS}

    @classmethod
    def from_dict(cls, value: Any) -> Style:
        data = _strict_dict(value, set(_STYLE_FIELDS), "style")
        return cls(*(data[field] for field in _STYLE_FIELDS))


def _point(value: Any, name: str) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{name} must be a two-number array")
    return _finite(value[0], f"{name}.x"), _finite(value[1], f"{name}.y")


@dataclass(frozen=True)
class Route:
    name: str
    version: int
    instance: int
    start: Pose
    end: Pose
    waypoints: tuple[tuple[float, float], ...]
    target: str

    def __post_init__(self) -> None:
        name = _text(self.name, "route name")
        target = _text(self.target, "route target")
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version != 1:
            raise ValueError("route version must be 1")
        if isinstance(self.instance, bool) or not isinstance(self.instance, int) or self.instance < 0:
            raise ValueError("route instance must be a non-negative integer")
        if not isinstance(self.start, Pose) or not isinstance(self.end, Pose):
            raise ValueError("route start and end must be Pose values")
        try:
            waypoints = tuple(_point(point, "waypoint") for point in self.waypoints)
        except TypeError as exc:
            raise ValueError("waypoints must be a sequence") from exc
        if len(waypoints) < 3:
            raise ValueError("a route needs at least 3 waypoints")
        if math.dist(waypoints[0], (self.start.x, self.start.y)) > 1e-6:
            raise ValueError("first waypoint must equal the start position")
        if math.dist(waypoints[-1], (self.end.x, self.end.y)) > 1e-6:
            raise ValueError("last waypoint must equal the end position")
        if any(math.dist(a, b) > 2.0 + 1e-7 for a, b in zip(waypoints, waypoints[1:], strict=False)):
            raise ValueError("consecutive waypoints must be at most 2 yards apart")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "waypoints", waypoints)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "instance": self.instance,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "waypoints": [list(point) for point in self.waypoints],
            "target": self.target,
        }

    @classmethod
    def from_dict(cls, value: Any) -> Route:
        data = _strict_dict(
            value,
            {"name", "version", "instance", "start", "end", "waypoints", "target"},
            "route",
        )
        return cls(
            data["name"],
            data["version"],
            data["instance"],
            Pose.from_dict(data["start"]),
            Pose.from_dict(data["end"]),
            tuple(data["waypoints"]),
            data["target"],
        )


@dataclass(frozen=True)
class RouteFile:
    routes: dict[str, Route]
    style: Style
    kinematics: Kinematics
    sources: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.routes, dict) or not self.routes:
            raise ValueError("routes must be a non-empty object")
        routes = dict(self.routes)
        if any(not isinstance(key, str) or not key for key in routes):
            raise ValueError("route names must be non-empty strings")
        if any(not isinstance(route, Route) or route.name != key for key, route in routes.items()):
            raise ValueError("route map keys must match Route.name")
        if not isinstance(self.style, Style) or not isinstance(self.kinematics, Kinematics):
            raise ValueError("style and kinematics have invalid types")
        if isinstance(self.sources, (str, bytes)):
            raise ValueError("sources must be an array of strings")
        try:
            sources = tuple(_text(source, "source") for source in self.sources)
        except TypeError as exc:
            raise ValueError("sources must be a sequence of strings") from exc
        object.__setattr__(self, "routes", routes)
        object.__setattr__(self, "sources", sources)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": 1,
            "routes": {name: route.to_dict() for name, route in sorted(self.routes.items())},
            "style": self.style.to_dict(),
            "kinematics": self.kinematics.to_dict(),
            "sources": list(self.sources),
        }

    def to_json(self, *, indent: int | None = None) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=indent, allow_nan=False)

    @classmethod
    def from_dict(cls, value: Any) -> RouteFile:
        data = _strict_dict(value, {"format", "routes", "style", "kinematics", "sources"}, "route file")
        if type(data["format"]) is not int or data["format"] != 1:
            raise ValueError("unsupported route file format")
        if not isinstance(data["routes"], dict):
            raise ValueError("routes must be an object")
        if type(data["sources"]) is not list or any(
            not isinstance(source, str) for source in data["sources"]
        ):
            raise ValueError("sources must be a JSON array of strings")
        routes = {name: Route.from_dict(route) for name, route in data["routes"].items()}
        return cls(
            routes, Style.from_dict(data["style"]), Kinematics.from_dict(data["kinematics"]), data["sources"]
        )

    @classmethod
    def from_json(cls, value: str) -> RouteFile:
        try:
            data = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid route JSON") from exc
        return cls.from_dict(data)


class KeyEvent(NamedTuple):
    t: float
    key: str
    down: bool


class Checkpoint(NamedTuple):
    t: float
    x: float
    y: float
    facing: float


@dataclass(frozen=True)
class WalkPlan:
    events: tuple[KeyEvent, ...]
    checkpoints: tuple[Checkpoint, ...]
    final: Pose
    seed: int

    def __post_init__(self) -> None:
        try:
            events = tuple(
                KeyEvent(_finite(event[0], "event time"), str(event[1]), bool(event[2]))
                for event in self.events
            )
            checkpoints = tuple(
                Checkpoint(
                    _finite(point[0], "checkpoint time"),
                    _finite(point[1], "checkpoint x"),
                    _finite(point[2], "checkpoint y"),
                    _normal_angle(_finite(point[3], "checkpoint facing")),
                )
                for point in self.checkpoints
            )
        except (IndexError, TypeError) as exc:
            raise ValueError("invalid walk plan tuple") from exc
        if any(event.key not in _KEYS for event in events):
            raise ValueError("walk plans may contain only W, Left, Right, and space")
        if any(event.t < -_EPS for event in events) or any(
            event.t + _EPS < previous.t for previous, event in zip(events, events[1:], strict=False)
        ):
            raise ValueError("walk plan events must be ordered")
        active: set[str] = set()
        down_times: dict[str, float] = {}
        for event in events:
            if event.down:
                if event.key in active:
                    raise ValueError(f"overlapping {event.key} press")
                active.add(event.key)
                down_times[event.key] = event.t
            elif event.key not in active:
                raise ValueError(f"unmatched {event.key} release")
            else:
                if event.t - down_times[event.key] < MIN_HUMAN_HOLD_SECONDS - _EPS:
                    raise ValueError(f"{event.key} hold is shorter than human minimum")
                active.remove(event.key)
                del down_times[event.key]
        if active:
            raise ValueError("walk plan has unreleased keys")
        if not isinstance(self.final, Pose):
            raise ValueError("walk plan final value must be a Pose")
        object.__setattr__(self, "events", events)
        object.__setattr__(self, "checkpoints", checkpoints)

    @property
    def duration(self) -> float:
        return self.events[-1].t if self.events else 0.0


@dataclass(frozen=True)
class _Telemetry:
    mono: float
    x: float
    y: float
    facing: float
    speed: float
    ground: str
    falling: bool
    instance: int


@dataclass(frozen=True)
class _Input:
    mono: float
    kind: str
    key: str | None = None
    down: bool | None = None
    button: int | None = None


@dataclass(frozen=True)
class _Recording:
    path: Path
    telemetry: tuple[_Telemetry, ...]
    inputs: tuple[_Input, ...]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON in {path}:{line_number}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"JSONL row in {path}:{line_number} is not an object")
            if "error" not in value:
                rows.append(value)
    return rows


def _load_recording(path: Path) -> _Recording:
    if not path.is_dir():
        raise ValueError(f"recording is not a directory: {path}")
    telemetry_path = path / "telemetry.jsonl"
    if not telemetry_path.is_file():
        raise ValueError(f"recording has no telemetry.jsonl: {path}")
    telemetry: list[_Telemetry] = []
    for row in _read_jsonl(telemetry_path):
        try:
            ground = row["ground"]
            if type(ground) is not str or ground not in _GROUND_VALUES:
                raise ValueError("telemetry ground has an invalid enum value")
            telemetry.append(
                _Telemetry(
                    _finite(row["mono"], "telemetry mono"),
                    _finite(row["x"], "telemetry x"),
                    _finite(row["y"], "telemetry y"),
                    _finite(row["facing"], "telemetry facing"),
                    _finite(row["speed"], "telemetry speed"),
                    ground,
                    _capture_bool_text(row["falling"], "telemetry falling"),
                    _exact_int(row["instance"], "telemetry instance"),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid telemetry row in {telemetry_path}") from exc
    telemetry.sort(key=lambda row: row.mono)
    if len(telemetry) < 2:
        raise ValueError(f"recording has fewer than two telemetry fixes: {path}")
    input_path = path / "input-xi2.jsonl"
    inputs: list[_Input] = []
    if input_path.is_file():
        for row in _read_jsonl(input_path):
            try:
                kind = row["kind"]
                if type(kind) is not str or kind not in {"key", "button", "motion"}:
                    raise ValueError("input kind has an invalid enum value")
                if kind == "key":
                    key_name = row["key"]
                    if type(key_name) is not str or key_name not in _CAPTURE_KEYS:
                        raise ValueError("input key has an invalid enum value")
                    inputs.append(
                        _Input(
                            _finite(row["mono"], "input mono"),
                            kind,
                            key_name,
                            _exact_bool(row["down"], "input down"),
                        )
                    )
                elif kind == "button":
                    button = _exact_int(row["button"], "input button")
                    if button not in {1, 3}:
                        raise ValueError("input button has an invalid enum value")
                    inputs.append(
                        _Input(
                            _finite(row["mono"], "input mono"),
                            kind,
                            button=button,
                            down=_exact_bool(row["down"], "input down"),
                        )
                    )
                else:
                    _finite(row["mono"], "input mono")
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"invalid input row in {input_path}") from exc
    inputs.sort(key=lambda row: row.mono)
    return _Recording(path, tuple(telemetry), tuple(inputs))


def _distance_to_endpoint(row: _Telemetry, endpoint: tuple[float, float]) -> float:
    return math.dist((row.x, row.y), endpoint)


def _endpoint_fix_samples(
    recordings: Sequence[_Recording], endpoint: tuple[float, float], radius: float
) -> tuple[list[_Telemetry], int]:
    fixes: list[_Telemetry] = []
    presses = 0
    for recording in recordings:
        for event in recording.inputs:
            if event.kind != "button" or event.button != 1 or event.down is not True:
                continue
            candidates = [
                row
                for row in recording.telemetry
                if event.mono - 1.5 <= row.mono <= event.mono + _EPS
                and row.speed == 0
                and _distance_to_endpoint(row, endpoint) <= radius
            ]
            if candidates:
                presses += 1
                fixes.extend(candidates)
    return fixes, presses


def _circular_mean(values: Iterable[float]) -> float:
    values = tuple(values)
    if len(values) < 2:
        raise ValueError("at least two endpoint heading observations are required")
    sine = sum(math.sin(value) for value in values)
    cosine = sum(math.cos(value) for value in values)
    concentration = math.hypot(sine, cosine) / len(values)
    if concentration < 0.5:
        raise ValueError("endpoint heading observations are undefined or insufficiently concentrated")
    return _normal_angle(math.atan2(sine, cosine))


def _endpoint_pose(fixes: Sequence[_Telemetry], endpoint: tuple[float, float]) -> Pose:
    if not fixes:
        raise ValueError("no stationary endpoint fixes")
    return Pose(
        statistics.median(row.x for row in fixes),
        statistics.median(row.y for row in fixes),
        _circular_mean(row.facing for row in fixes),
    )


def _key_intervals(
    recording: _Recording, keys: Iterable[str] | None = None
) -> dict[str, list[tuple[float, float]]]:
    wanted = set(keys) if keys is not None else None
    open_times: dict[str, float] = {}
    result: dict[str, list[tuple[float, float]]] = {}
    for event in recording.inputs:
        if event.kind != "key" or event.key is None or (wanted is not None and event.key not in wanted):
            continue
        if event.down:
            if event.key not in open_times:
                open_times[event.key] = event.mono
        elif event.key in open_times:
            start = open_times.pop(event.key)
            if event.mono >= start:
                result.setdefault(event.key, []).append((start, event.mono))
    return result


def _overlap(interval: tuple[float, float], start: float, end: float) -> float:
    return max(0.0, min(interval[1], end) - max(interval[0], start))


def _input_heading_error(recordings: Sequence[_Recording]) -> None:
    errors: list[float] = []
    for recording in recordings:
        intervals = _key_intervals(recording)
        forward = intervals.get("W", [])
        turning = intervals
        rows = recording.telemetry
        for previous, current in zip(rows, rows[1:], strict=False):
            if current.mono <= previous.mono or previous.ground != "grounded" or current.ground != "grounded":
                continue
            if previous.speed <= 0 and current.speed <= 0:
                continue
            has_w = any(_overlap(item, previous.mono, current.mono) > _EPS for item in forward)
            has_other = any(
                key in turning
                and any(_overlap(item, previous.mono, current.mono) > _EPS for item in intervals.get(key, []))
                for key in ("A", "D", "Left", "Right", "Q", "E")
            )
            if not has_w or has_other:
                continue
            dx = current.x - previous.x
            dy = current.y - previous.y
            if math.hypot(dx, dy) < 0.2:
                continue
            errors.append(abs(_angle_delta(math.atan2(dy, dx) - current.facing)))
    if not errors:
        raise ValueError("recordings contain no forward-only grounded span for heading validation")
    if statistics.median(errors) > 0.35:
        median_error = statistics.median(errors)
        raise ValueError(
            f"forward heading convention contradicted by recordings (median angular error {median_error:.3f})"
        )


def _turn_rates(recordings: Sequence[_Recording]) -> tuple[float, float]:
    rates: dict[str, list[float]] = {"Left": [], "Right": []}
    for recording in recordings:
        intervals = _key_intervals(recording)
        rows = recording.telemetry
        for previous, current in zip(rows, rows[1:], strict=False):
            dt = current.mono - previous.mono
            if dt <= 0:
                continue
            overlaps = {
                key: sum(
                    _overlap(interval, previous.mono, current.mono) for interval in intervals.get(key, [])
                )
                for key in _TURN_KEYS
            }
            active = [key for key, seconds in overlaps.items() if seconds > _EPS]
            if len(active) != 1:
                continue
            if any(
                sum(_overlap(interval, previous.mono, current.mono) for interval in intervals.get(key, []))
                > _EPS
                for key in ("Q", "E")
            ):
                continue
            held = overlaps[active[0]]
            change = _angle_delta(current.facing - previous.facing)
            if abs(change) < 0.005 or held <= 0:
                continue
            rates[active[0]].append(change / held)
    if not rates["Left"] or not rates["Right"]:
        raise ValueError("could not fit both Left and Right turn rates")
    left = statistics.median(rates["Left"])
    right = statistics.median(rates["Right"])
    if left * right >= 0:
        raise ValueError("Left and Right turn rates must have opposite signs")
    ratio = abs(left) / abs(right)
    if not 0.75 <= ratio <= 1.25:
        raise ValueError("Left and Right turn rates differ by more than 25 percent")
    return left, right


def _press_pairs(recordings: Sequence[_Recording], key: str) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for recording in recordings:
        pairs.extend(_key_intervals(recording, {key}).get(key, []))
    return pairs


def _style_samples(values: Iterable[float], field: str, excluded: dict[str, int]) -> tuple[float, ...]:
    usable: list[float] = []
    for value in values:
        if value < MIN_HUMAN_HOLD_SECONDS:
            excluded[field] += 1
            continue
        if value > 10:
            continue
        usable.append(value)
    if len(usable) < 3:
        raise ValueError(f"fewer than 3 usable {field} samples")
    return tuple(sorted(usable))


def _arrival_pause_samples(
    recordings: Sequence[_Recording],
    start_xy: tuple[float, float],
    end_xy: tuple[float, float],
    radius: float,
) -> list[float]:
    pauses: list[float] = []
    for recording in recordings:
        for event in recording.inputs:
            if event.kind != "button" or event.button != 1 or event.down is not True:
                continue
            endpoint_qualified = any(
                event.mono - 1.5 <= row.mono <= event.mono + _EPS
                and row.speed == 0
                and (
                    _distance_to_endpoint(row, start_xy) <= radius
                    or _distance_to_endpoint(row, end_xy) <= radius
                )
                for row in recording.telemetry
            )
            if not endpoint_qualified:
                continue
            stops = [
                current.mono
                for previous, current in zip(recording.telemetry, recording.telemetry[1:], strict=False)
                if previous.speed > 0 and current.speed == 0 and 0 <= event.mono - current.mono <= 10
            ]
            if stops:
                pauses.append(event.mono - max(stops))
    return pauses


def _style_from_recordings(
    recordings: Sequence[_Recording],
    leg_windows: dict[Path, list[tuple[float, float]]],
    arrive_pauses: Sequence[float],
) -> tuple[Style, dict[str, int]]:
    w_pairs = _press_pairs(recordings, "W")
    left_pairs = _press_pairs(recordings, "Left")
    right_pairs = _press_pairs(recordings, "Right")
    strafe_pairs = _press_pairs(recordings, "A") + _press_pairs(recordings, "D")
    jump_pairs = _press_pairs(recordings, "space")
    holds = [end - start for start, end in w_pairs]
    gaps: list[float] = []
    jump_intervals: list[float] = []
    for recording in recordings:
        key_intervals = _key_intervals(recording, {"W", "space"})
        w = sorted(key_intervals.get("W", []))
        gaps.extend(
            next_start - previous_end
            for (_, previous_end), (next_start, _) in zip(w, w[1:], strict=False)
            if 0 <= next_start - previous_end <= 10
            and any(
                window_start <= previous_end and next_start <= window_end
                for window_start, window_end in leg_windows.get(recording.path, [])
            )
        )
        jump_downs = [
            event.mono
            for event in recording.inputs
            if event.kind == "key" and event.key == "space" and event.down
        ]
        for first, second in zip(jump_downs, jump_downs[1:], strict=False):
            if not 0 <= second - first <= 10:
                continue
            if not any(
                window_start <= first
                and second <= window_end
                and any(
                    first <= row.mono <= second and row.speed > 0 and row.ground == "grounded"
                    for row in recording.telemetry
                )
                for window_start, window_end in leg_windows.get(recording.path, [])
            ):
                continue
            jump_intervals.append(second - first)
    turn_taps = [end - start for start, end in left_pairs + right_pairs]
    strafe_taps = [end - start for start, end in strafe_pairs]
    jump_presses = [end - start for start, end in jump_pairs]
    excluded = {field: 0 for field in _STYLE_FIELDS}
    style = Style(
        _style_samples(holds, "forward_hold", excluded),
        _style_samples(gaps, "forward_gap", excluded),
        _style_samples(turn_taps, "turn_tap", excluded),
        _style_samples(strafe_taps, "strafe_tap", excluded),
        _style_samples(jump_presses, "jump_press", excluded),
        _style_samples(jump_intervals, "jump_interval", excluded),
        _style_samples(arrive_pauses, "arrive_pause", excluded),
    )
    return style, excluded


def _button_pairs(recording: _Recording, button: int) -> list[tuple[float, float]]:
    start: float | None = None
    pairs: list[tuple[float, float]] = []
    for event in recording.inputs:
        if event.kind != "button" or event.button != button:
            continue
        if event.down and start is None:
            start = event.mono
        elif not event.down and start is not None and event.mono > start:
            pairs.append((start, event.mono))
            start = None
    return pairs


def _jump_airtime(recordings: Sequence[_Recording]) -> float:
    estimates: list[float] = []
    for recording in recordings:
        presses = [
            event.mono
            for event in recording.inputs
            if event.kind == "key" and event.key == "space" and event.down
        ]
        for press in presses:
            for row in recording.telemetry:
                delta = row.mono - press
                if 0.4 <= delta <= 1.0 and row.ground == "grounded" and not row.falling:
                    estimates.append(delta)
                    break
    if not estimates:
        raise ValueError("no jump-press-to-grounded telemetry estimate in [0.4, 1.0] seconds")
    return statistics.median(estimates)


def _moving_speed(recordings: Sequence[_Recording]) -> float:
    values = [
        row.speed
        for recording in recordings
        for row in recording.telemetry
        if row.speed > 0 and row.ground == "grounded"
    ]
    if not values:
        raise ValueError("recordings contain no moving grounded fixes")
    return statistics.median(values)


def _leg_spans(
    recording: _Recording,
    start_xy: tuple[float, float],
    end_xy: tuple[float, float],
    radius: float,
) -> tuple[list[list[_Telemetry]], list[list[_Telemetry]]]:
    rows = recording.telemetry

    def state(row: _Telemetry) -> str | None:
        if _distance_to_endpoint(row, start_xy) <= radius:
            return "start"
        if _distance_to_endpoint(row, end_xy) <= radius:
            return "end"
        return None

    def collect(source: str, destination: str) -> list[list[_Telemetry]]:
        legs: list[list[_Telemetry]] = []
        cursor = 0
        while cursor < len(rows):
            while cursor < len(rows) and state(rows[cursor]) != source:
                cursor += 1
            if cursor >= len(rows):
                break
            source_run_start = cursor
            while cursor < len(rows) and state(rows[cursor]) == source:
                cursor += 1
            departure = cursor - 1
            # A return to the source before reaching the destination aborts the
            # attempted leg.  The later departure is the only route geometry we
            # retain, so restart the source run at every such transition.
            arrival = None
            scan = cursor
            while scan < len(rows):
                current_state = state(rows[scan])
                if current_state == source:
                    source_run_start = scan
                    while scan < len(rows) and state(rows[scan]) == source:
                        scan += 1
                    departure = scan - 1
                    continue
                if current_state == destination:
                    arrival = scan
                    break
                scan += 1
            if arrival is None:
                break

            first = departure
            for candidate in range(departure, source_run_start - 1, -1):
                if rows[candidate].speed == 0:
                    first = candidate
                    break
            last = arrival
            while last + 1 < len(rows) and state(rows[last + 1]) == destination:
                last += 1
                if rows[last].speed == 0:
                    break
            span = list(rows[first : last + 1])
            if len(span) >= 2:
                legs.append(span)
            # Keep the destination fix available to the independently scanned
            # reverse direction.  This direction can start its next search after
            # the arrival, because the destination is not its source here.
            cursor = last + 1
        return legs

    return collect("start", "end"), collect("end", "start")


def _resample(points: Sequence[tuple[float, float]], count: int) -> list[tuple[float, float]]:
    if not points:
        raise ValueError("cannot resample an empty path")
    if len(points) == 1:
        return [points[0]] * count
    distances = [0.0]
    for first, second in zip(points, points[1:], strict=False):
        distances.append(distances[-1] + math.dist(first, second))
    total = distances[-1]
    if total <= _EPS:
        return [points[0]] * count
    result: list[tuple[float, float]] = []
    for index in range(count):
        target = total * index / (count - 1)
        segment = next((j for j in range(1, len(distances)) if distances[j] >= target), len(distances) - 1)
        before = distances[segment - 1]
        length = distances[segment] - before
        fraction = 0.0 if length <= _EPS else (target - before) / length
        first = points[segment - 1]
        second = points[segment]
        result.append(
            (first[0] + (second[0] - first[0]) * fraction, first[1] + (second[1] - first[1]) * fraction)
        )
    return result


def _route_path(
    legs: Sequence[Sequence[_Telemetry]], start: Pose, end: Pose
) -> tuple[tuple[float, float], ...]:
    if len(legs) < 2:
        raise ValueError("at least two legs are required per direction")
    samples = [_resample([(row.x, row.y) for row in leg], 64) for leg in legs]
    median_path = [
        (
            statistics.median(path[index][0] for path in samples),
            statistics.median(path[index][1] for path in samples),
        )
        for index in range(64)
    ]
    median_path[0] = (start.x, start.y)
    median_path[-1] = (end.x, end.y)
    count = max(
        3,
        math.ceil(sum(math.dist(a, b) for a, b in zip(median_path, median_path[1:], strict=False)) / 2.0) + 1,
    )
    waypoints = _resample(median_path, count)
    waypoints[0] = (start.x, start.y)
    waypoints[-1] = (end.x, end.y)
    return tuple(waypoints)


def build_route_file(
    recordings: Sequence[Path],
    *,
    start_xy: tuple[float, float],
    end_xy: tuple[float, float],
    radius: float,
    start_target: str,
    end_target: str,
) -> RouteFile:
    start_xy = _point(start_xy, "start_xy")
    end_xy = _point(end_xy, "end_xy")
    radius = _finite(radius, "radius")
    if radius <= 0:
        raise ValueError("radius must be positive")
    start_target = _text(start_target, "start_target")
    end_target = _text(end_target, "end_target")
    if math.dist(start_xy, end_xy) <= 2 * radius:
        raise ValueError("endpoint circles must be separate")
    loaded = tuple(_load_recording(Path(path)) for path in recordings)
    if not loaded:
        raise ValueError("at least one recording is required")
    _input_heading_error(loaded)
    forward_legs: list[list[_Telemetry]] = []
    backward_legs: list[list[_Telemetry]] = []
    leg_windows: dict[Path, list[tuple[float, float]]] = {}
    for recording in loaded:
        forward, backward = _leg_spans(recording, start_xy, end_xy, radius)
        forward_legs.extend(forward)
        backward_legs.extend(backward)
        leg_windows[recording.path] = [(leg[0].mono, leg[-1].mono) for leg in (*forward, *backward) if leg]
    if len(forward_legs) < 2 or len(backward_legs) < 2:
        raise ValueError(
            f"need at least two legs per direction, got {len(forward_legs)} and {len(backward_legs)}"
        )
    start_fixes, start_presses = _endpoint_fix_samples(loaded, start_xy, radius)
    end_fixes, end_presses = _endpoint_fix_samples(loaded, end_xy, radius)
    if start_presses < 2 or end_presses < 2:
        raise ValueError(
            f"need at least two endpoint presses per endpoint, got {start_presses} and {end_presses}"
        )
    start_pose = _endpoint_pose(start_fixes, start_xy)
    end_pose = _endpoint_pose(end_fixes, end_xy)
    left_rate, right_rate = _turn_rates(loaded)
    jump_airtime = _jump_airtime(loaded)
    arrive_pauses = _arrival_pause_samples(loaded, start_xy, end_xy, radius)
    style, excluded = _style_from_recordings(loaded, leg_windows, arrive_pauses)
    kinematics = Kinematics(_moving_speed(loaded), left_rate, right_rate, jump_airtime)
    instance_values = [row.instance for recording in loaded for row in recording.telemetry]
    instance = int(statistics.median(instance_values))
    prefix = start_target.lower()
    suffix = end_target.lower()
    reverse_prefix = end_target.lower()
    reverse_suffix = start_target.lower()
    routes = {
        f"{prefix}_to_{suffix}": Route(
            f"{prefix}_to_{suffix}",
            1,
            instance,
            start_pose,
            end_pose,
            _route_path(forward_legs, start_pose, end_pose),
            end_target,
        ),
        f"{reverse_prefix}_to_{reverse_suffix}": Route(
            f"{reverse_prefix}_to_{reverse_suffix}",
            1,
            instance,
            end_pose,
            start_pose,
            _route_path(backward_legs, end_pose, start_pose),
            start_target,
        ),
    }
    sources = tuple(str(Path(path)) for path in recordings) + (
        "jump_airtime estimated from jump-press-to-next-grounded telemetry",
        "heading convention verified on forward-only grounded W spans",
        *(
            f"excluded {excluded[field]} {field} samples shorter than {MIN_HUMAN_HOLD_SECONDS:.2f}s"
            for field in _STYLE_FIELDS
        ),
    )
    return RouteFile(routes, style, kinematics, sources)


def _polyline_distance(x: float, y: float, waypoints: Sequence[tuple[float, float]]) -> float:
    best = math.inf
    for first, second in zip(waypoints, waypoints[1:], strict=False):
        vx = second[0] - first[0]
        vy = second[1] - first[1]
        length2 = vx * vx + vy * vy
        if length2 <= _EPS:
            fraction = 0.0
        else:
            fraction = max(0.0, min(1.0, ((x - first[0]) * vx + (y - first[1]) * vy) / length2))
        px = first[0] + fraction * vx
        py = first[1] + fraction * vy
        best = min(best, math.hypot(x - px, y - py))
    return best


def _polyline_position(waypoints: Sequence[tuple[float, float]], distance: float) -> tuple[float, float]:
    remaining = max(0.0, distance)
    for first, second in zip(waypoints, waypoints[1:], strict=False):
        length = math.dist(first, second)
        if remaining <= length or second == waypoints[-1]:
            fraction = 0.0 if length <= _EPS else min(1.0, remaining / length)
            return first[0] + fraction * (second[0] - first[0]), first[1] + fraction * (second[1] - first[1])
        remaining -= length
    return waypoints[-1]


def _nearest_progress(position: tuple[float, float], waypoints: Sequence[tuple[float, float]]) -> float:
    best_distance = math.inf
    best_progress = 0.0
    progress = 0.0
    for first, second in zip(waypoints, waypoints[1:], strict=False):
        vx = second[0] - first[0]
        vy = second[1] - first[1]
        length2 = vx * vx + vy * vy
        fraction = (
            0.0
            if length2 <= _EPS
            else max(0.0, min(1.0, ((position[0] - first[0]) * vx + (position[1] - first[1]) * vy) / length2))
        )
        candidate = (first[0] + fraction * vx, first[1] + fraction * vy)
        distance = math.dist(position, candidate)
        if distance < best_distance:
            best_distance = distance
            best_progress = progress + fraction * math.sqrt(length2)
        progress += math.sqrt(length2)
    return best_progress


def _lookahead(
    position: tuple[float, float], waypoints: Sequence[tuple[float, float]], lookahead: float = 2.0
) -> tuple[float, float]:
    return _polyline_position(waypoints, _nearest_progress(position, waypoints) + lookahead)


def _turn_rate(key: str, kinematics: Kinematics) -> float:
    return kinematics.turn_rate_left if key == "Left" else kinematics.turn_rate_right


def _integrate(
    position: tuple[float, float],
    facing: float,
    dt: float,
    *,
    moving: bool,
    turn_key: str | None,
    airborne: float,
    airborne_heading: float,
    airborne_speed: float,
    kinematics: Kinematics,
) -> tuple[tuple[float, float], float]:
    if dt <= 0:
        return position, _normal_angle(facing)
    rate = 0.0 if turn_key is None else _turn_rate(turn_key, kinematics)
    px, py = position
    remaining = dt
    ground_facing = facing
    if airborne > 0:
        airborne_dt = min(remaining, airborne)
        px += airborne_speed * airborne_dt * math.cos(airborne_heading)
        py += airborne_speed * airborne_dt * math.sin(airborne_heading)
        remaining -= airborne_dt
        ground_facing = facing + rate * airborne_dt
    if moving and remaining > 0:
        if abs(rate) <= _EPS:
            px += kinematics.run_speed * remaining * math.cos(ground_facing)
            py += kinematics.run_speed * remaining * math.sin(ground_facing)
        else:
            next_facing = ground_facing + rate * remaining
            px += kinematics.run_speed / rate * (math.sin(next_facing) - math.sin(ground_facing))
            py += kinematics.run_speed / rate * (-math.cos(next_facing) + math.cos(ground_facing))
    return (px, py), _normal_angle(facing + rate * dt)


def simulate(
    events: Sequence[KeyEvent | tuple[float, str, bool]], start: Pose, kinematics: Kinematics
) -> list[tuple[float, Pose]]:
    """Simulate key events and return poses at time zero and every event time."""
    normalized = sorted(
        (KeyEvent(_finite(event[0], "event time"), str(event[1]), bool(event[2])) for event in events),
        key=lambda event: event.t,
    )
    if any(event.key not in _KEYS for event in normalized):
        raise ValueError("simulation received an unsupported key")
    position = (start.x, start.y)
    facing = start.facing
    active: set[str] = set()
    airborne_until = 0.0
    airborne_heading = facing
    airborne_speed = 0.0
    now = 0.0
    result: list[tuple[float, Pose]] = [(0.0, start)]
    index = 0
    while index < len(normalized):
        target_time = normalized[index].t
        if target_time < now - _EPS:
            raise ValueError("simulation events must be ordered")
        dt = target_time - now
        airborne = max(0.0, airborne_until - now)
        turn_key = (
            "Left" if "Left" in active and "Right" not in active else "Right" if "Right" in active else None
        )
        position, facing = _integrate(
            position,
            facing,
            dt,
            moving="W" in active,
            turn_key=turn_key,
            airborne=airborne,
            airborne_heading=airborne_heading,
            airborne_speed=airborne_speed,
            kinematics=kinematics,
        )
        now = target_time
        while index < len(normalized) and math.isclose(normalized[index].t, target_time, abs_tol=1e-8):
            event = normalized[index]
            if event.down:
                if event.key in active:
                    raise ValueError(f"overlapping {event.key} press")
                active.add(event.key)
                if event.key == "space" and now >= airborne_until - _EPS:
                    airborne_until = now + kinematics.jump_airtime
                    airborne_heading = facing
                    airborne_speed = kinematics.run_speed if "W" in active else 0.0
            else:
                if event.key not in active:
                    raise ValueError(f"unmatched {event.key} release")
                active.remove(event.key)
            index += 1
        result.append((now, Pose(position[0], position[1], facing)))
    return result


def _trace(
    events: Sequence[KeyEvent], start: Pose, kinematics: Kinematics, step: float = TRACE_STEP_SECONDS
) -> list[tuple[float, Pose]]:
    """Return a dense trace for planner validation and checkpoint generation."""
    if not events:
        return [(0.0, start)]
    step = _finite(step, "trace step")
    if step <= 0:
        raise ValueError("trace step must be positive")
    normalized = tuple(events)
    if any(event.key not in _KEYS for event in normalized):
        raise ValueError("trace received an unsupported key")
    if any(event.t < -_EPS for event in normalized) or any(
        event.t + _EPS < previous.t for previous, event in zip(normalized, normalized[1:], strict=False)
    ):
        raise ValueError("trace events must be ordered")
    duration = normalized[-1].t
    active: set[str] = set()
    airborne_until = 0.0
    airborne_heading = start.facing
    airborne_speed = 0.0
    current_position = (start.x, start.y)
    current_facing = start.facing
    current_time = 0.0
    dense: list[tuple[float, Pose]] = [(0.0, start)]
    event_index = 0
    next_sample = step
    while event_index < len(normalized) or current_time < duration - _EPS or next_sample <= duration + _EPS:
        next_event = normalized[event_index].t if event_index < len(normalized) else math.inf
        next_landing = airborne_until if airborne_until > current_time + _EPS else math.inf
        target = min(next_event, next_sample, next_landing, duration)
        if target < current_time + _EPS:
            if event_index < len(normalized) and math.isclose(
                normalized[event_index].t, current_time, abs_tol=1e-8
            ):
                while event_index < len(normalized) and math.isclose(
                    normalized[event_index].t, current_time, abs_tol=1e-8
                ):
                    event = normalized[event_index]
                    if event.down:
                        if event.key in active:
                            raise ValueError(f"overlapping {event.key} press")
                        active.add(event.key)
                        if event.key == "space" and current_time >= airborne_until - _EPS:
                            airborne_until = current_time + kinematics.jump_airtime
                            airborne_heading = current_facing
                            airborne_speed = kinematics.run_speed if "W" in active else 0.0
                    else:
                        if event.key not in active:
                            raise ValueError(f"unmatched {event.key} release")
                        active.remove(event.key)
                    event_index += 1
                continue
            while next_sample <= current_time + _EPS:
                next_sample += step
            continue
        dt = target - current_time
        airborne = max(0.0, airborne_until - current_time)
        turn_key = (
            "Left" if "Left" in active and "Right" not in active else "Right" if "Right" in active else None
        )
        current_position, current_facing = _integrate(
            current_position,
            current_facing,
            dt,
            moving="W" in active,
            turn_key=turn_key,
            airborne=airborne,
            airborne_heading=airborne_heading,
            airborne_speed=airborne_speed,
            kinematics=kinematics,
        )
        current_time = target
        dense.append((current_time, Pose(current_position[0], current_position[1], current_facing)))
        while next_sample <= current_time + _EPS:
            next_sample += step
        while event_index < len(normalized) and math.isclose(
            normalized[event_index].t, current_time, abs_tol=1e-8
        ):
            event = normalized[event_index]
            if event.down:
                if event.key in active:
                    raise ValueError(f"overlapping {event.key} press")
                active.add(event.key)
                if event.key == "space" and current_time >= airborne_until - _EPS:
                    airborne_until = current_time + kinematics.jump_airtime
                    airborne_heading = current_facing
                    airborne_speed = kinematics.run_speed if "W" in active else 0.0
            else:
                if event.key not in active:
                    raise ValueError(f"unmatched {event.key} release")
                active.remove(event.key)
            event_index += 1
    return dense


def _sample(rng: random.Random, values: tuple[float, ...]) -> float:
    return values[rng.randrange(len(values))]


def _make_attempt(
    route: Route, start: Pose, style: Style, kinematics: Kinematics, rng: random.Random
) -> tuple[tuple[KeyEvent, ...], Pose]:
    events: list[KeyEvent] = []
    position = (start.x, start.y)
    facing = start.facing
    t = 0.0
    active_w = False
    w_end: float | None = None
    next_w: float | None = 0.0
    active_turn: str | None = None
    turn_end: float | None = None
    space_end: float | None = None
    airborne_until = 0.0
    airborne_heading = facing
    airborne_speed = 0.0
    next_jump = _sample(rng, style.jump_interval)
    arrived = False
    next_control = 0.0
    initial_alignment = True

    def emit(key: str, down: bool) -> None:
        events.append(KeyEvent(t, key, down))

    def advance(target: float) -> None:
        nonlocal position, facing, t
        dt = target - t
        position, facing = _integrate(
            position,
            facing,
            dt,
            moving=active_w,
            turn_key=active_turn,
            airborne=max(0.0, airborne_until - t),
            airborne_heading=airborne_heading,
            airborne_speed=airborne_speed,
            kinematics=kinematics,
        )
        t = target

    for _ in range(3000):
        if t > 30.0:
            break
        candidates = [next_control]
        if active_w and w_end is not None:
            candidates.append(w_end)
        if not active_w and next_w is not None:
            candidates.append(next_w)
        if active_turn and turn_end is not None:
            candidates.append(turn_end)
        if space_end is not None:
            candidates.append(space_end)
        if airborne_until > t + _EPS:
            candidates.append(airborne_until)
        target = min(value for value in candidates if value >= t - _EPS)
        if target < t:
            target = t
        advance(target)
        at_control = math.isclose(t, next_control, abs_tol=1e-8)
        if active_w and w_end is not None and t >= w_end - _EPS:
            emit("W", False)
            active_w = False
            w_end = None
            if not arrived:
                distance_after_release = math.dist(position, (route.end.x, route.end.y))
                next_w = (
                    t + _sample(rng, style.forward_gap)
                    if distance_after_release > 2.0
                    else t
                    if distance_after_release > 0.45
                    else None
                )
        if not active_w and next_w is not None and t >= next_w - _EPS and not arrived:
            alignment_target = _lookahead(position, route.waypoints)
            alignment_angle = _angle_delta(
                math.atan2(alignment_target[1] - position[1], alignment_target[0] - position[0]) - facing
            )
            if math.dist(position, (route.end.x, route.end.y)) > 2.0 and not (
                initial_alignment and abs(alignment_angle) > 0.25
            ):
                emit("W", True)
                active_w = True
                w_end = t + _sample(rng, style.forward_hold)
                next_w = None
            elif not initial_alignment:
                next_w = None
            else:
                next_w = t + 0.05
        if active_turn and turn_end is not None and t >= turn_end - _EPS:
            emit(active_turn, False)
            active_turn = None
            turn_end = None
        if space_end is not None and t >= space_end - _EPS:
            emit("space", False)
            space_end = None
        distance_to_end = math.dist(position, (route.end.x, route.end.y))
        if not arrived and distance_to_end <= 0.45 and t >= airborne_until - _EPS:
            if active_w:
                emit("W", False)
                active_w = False
                w_end = None
            next_w = None
            arrived = True
        if at_control or active_turn is None or not active_w:
            next_control = max(next_control + 0.05, t + 0.05)
            target_point = (route.end.x, route.end.y) if arrived else _lookahead(position, route.waypoints)
            desired = math.atan2(target_point[1] - position[1], target_point[0] - position[0])
            angle = _angle_delta(desired - facing)
            if initial_alignment and abs(angle) <= 0.25:
                initial_alignment = False
            if active_turn is None and t >= airborne_until - _EPS and abs(angle) > 0.07:
                key = (
                    "Left"
                    if angle > 0
                    and kinematics.turn_rate_left > 0
                    or angle < 0
                    and kinematics.turn_rate_left < 0
                    else "Right"
                )
                required = abs(angle / _turn_rate(key, kinematics))
                minimum = min(style.turn_tap)
                maximum = max(style.turn_tap)
                duration = max(minimum, min(maximum, required))
                emit(key, True)
                active_turn = key
                turn_end = t + duration
            elif arrived and active_turn is None and abs(angle) <= 0.07:
                break
            if (
                not arrived
                and active_w
                and active_turn is None
                and t >= airborne_until - _EPS
                and distance_to_end > 3.0 + kinematics.run_speed * kinematics.jump_airtime
                and t >= next_jump - _EPS
                and space_end is None
            ):
                press = _sample(rng, style.jump_press)
                emit("space", True)
                space_end = t + press
                airborne_until = t + kinematics.jump_airtime
                airborne_heading = facing
                airborne_speed = kinematics.run_speed
                next_jump = t + _sample(rng, style.jump_interval)
        if (
            arrived
            and not active_w
            and active_turn is None
            and space_end is None
            and t >= airborne_until - _EPS
        ):
            target_angle = _angle_delta(route.end.facing - facing)
            if abs(target_angle) <= 0.07:
                break
        if not candidates or (
            target == t and not at_control and not active_w and not active_turn and next_w is None
        ):
            next_control = t + 0.05
    if active_w:
        emit("W", False)
    if active_turn:
        emit(active_turn, False)
    if space_end is not None:
        emit("space", False)
    final = simulate(events, start, kinematics)[-1][1]
    correction_time = events[-1].t if events else 0.0
    for _ in range(128):
        angle = _angle_delta(route.end.facing - final.facing)
        if abs(angle) <= 0.15:
            break
        key = "Left" if angle * kinematics.turn_rate_left > 0 else "Right"
        duration = max(
            MIN_HUMAN_HOLD_SECONDS,
            min(max(style.turn_tap), abs(angle / _turn_rate(key, kinematics))),
        )
        events.append(KeyEvent(correction_time, key, True))
        correction_time += duration
        events.append(KeyEvent(correction_time, key, False))
        final = simulate(events, start, kinematics)[-1][1]
    return tuple(events), final


def _checkpoints(events: Sequence[KeyEvent], start: Pose, kinematics: Kinematics) -> tuple[Checkpoint, ...]:
    trace = _trace(events, start, kinematics)
    duration = trace[-1][0]
    checkpoints: list[Checkpoint] = []
    target = 1.0
    index = 0
    while target <= duration + _EPS:
        while index + 1 < len(trace) and trace[index + 1][0] < target - _EPS:
            index += 1
        if index + 1 >= len(trace):
            pose = trace[-1][1]
        else:
            first_t, first = trace[index]
            second_t, second = trace[index + 1]
            fraction = 0.0 if second_t <= first_t else (target - first_t) / (second_t - first_t)
            delta = _angle_delta(second.facing - first.facing)
            pose = Pose(
                first.x + fraction * (second.x - first.x),
                first.y + fraction * (second.y - first.y),
                first.facing + fraction * delta,
            )
        checkpoints.append(Checkpoint(target, pose.x, pose.y, pose.facing))
        target += 1.0
    return tuple(checkpoints)


def plan_walk(route: Route, start: Pose, style: Style, kinematics: Kinematics, seed: int) -> WalkPlan:
    """Create a seeded human-style walk plan, retrying only derived seeds."""
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    for attempt in range(32):
        rng = random.Random(seed * 1000 + attempt)
        events, final = _make_attempt(route, start, style, kinematics, rng)
        if not events:
            continue
        duration = events[-1].t
        if duration > 30.0:
            continue
        trace = _trace(events, start, kinematics)
        max_distance = max(_polyline_distance(pose.x, pose.y, route.waypoints) for _, pose in trace)
        continuous_bound = max_distance + kinematics.run_speed * TRACE_STEP_SECONDS
        final_distance = math.dist((final.x, final.y), (route.end.x, route.end.y))
        final_angle = abs(_angle_delta(final.facing - route.end.facing))
        if continuous_bound > 1.0 or final_distance > 0.5 or final_angle > 0.15:
            continue
        return WalkPlan(events, _checkpoints(events, start, kinematics), final, seed)
    raise ValueError("could not produce a route-corridor plan in 32 attempts")


def _parse_xy(value: str) -> tuple[float, float]:
    parts = value.split(",")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("expected X,Y")
    try:
        return _finite(float(parts[0]), "x"), _finite(float(parts[1]), "y")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _parse_pose(value: str) -> Pose:
    parts = value.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("expected X,Y,FACING")
    try:
        return Pose(float(parts[0]), float(parts[1]), float(parts[2]))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _plan_json(plan: WalkPlan, route: Route, start: Pose, kinematics: Kinematics) -> dict[str, Any]:
    trace = _trace(plan.events, start, kinematics)
    return {
        "seed": plan.seed,
        "events": [[event.t, event.key, event.down] for event in plan.events],
        "checkpoints": [list(point) for point in plan.checkpoints],
        "final": plan.final.to_dict(),
        "summary": {
            "max_distance_from_polyline": max(
                _polyline_distance(pose.x, pose.y, route.waypoints) for _, pose in trace
            ),
            "duration": plan.duration,
            "jump_count": sum(event.key == "space" and event.down for event in plan.events),
        },
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Build and plan offline WoW walking routes")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--recording", action="append", type=Path, required=True)
    build.add_argument("--start", type=_parse_xy, required=True)
    build.add_argument("--end", type=_parse_xy, required=True)
    build.add_argument("--radius", type=float, required=True)
    build.add_argument("--start-target", required=True)
    build.add_argument("--end-target", required=True)
    build.add_argument("--out", type=Path, required=True)
    plan = subparsers.add_parser("plan")
    plan.add_argument("--routes", type=Path, required=True)
    plan.add_argument("--route", required=True)
    plan.add_argument("--from", dest="from_pose", type=_parse_pose, required=True)
    plan.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    try:
        if args.command == "build":
            if args.out.exists():
                parser.error(f"refusing to overwrite existing file: {args.out}")
            route_file = build_route_file(
                args.recording,
                start_xy=args.start,
                end_xy=args.end,
                radius=args.radius,
                start_target=args.start_target,
                end_target=args.end_target,
            )
            args.out.write_text(route_file.to_json(indent=2) + "\n", encoding="utf-8")
            return 0
        route_file = RouteFile.from_json(args.routes.read_text(encoding="utf-8"))
        if args.route not in route_file.routes:
            parser.error(f"unknown route: {args.route}")
        route = route_file.routes[args.route]
        walk = plan_walk(route, args.from_pose, route_file.style, route_file.kinematics, args.seed)
        print(json.dumps(_plan_json(walk, route, args.from_pose, route_file.kinematics), sort_keys=True))
        return 0
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":  # pragma: no cover - exercised by CLI tests
    raise SystemExit(_cli())
