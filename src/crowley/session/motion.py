"""Bounded native motion feedback and waypoint control primitives.

The provider consumes the already decoded schema-4 status surface. It never
manufactures a frame when the addon has not published one, and all higher
level control is finite, generation-bound, and feedback driven.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class MotionError(RuntimeError):
    """Raised when native motion feedback or a bounded intent is unsafe."""


@dataclass(frozen=True, slots=True)
class CtmCapability:
    accessor: str
    cvar: str
    state: str
    reason: str


@dataclass(frozen=True, slots=True)
class GroundCapability:
    state: str
    falling: str
    flying: str
    swimming: str
    submerged: str
    mounted: str
    taxi: str
    reason: str


@dataclass(frozen=True, slots=True)
class SpeedTuple:
    current: float
    run: float
    flight: float
    swim: float
    unit_status: str

    @property
    def unitStatus(self) -> str:
        return self.unit_status


@dataclass(frozen=True, slots=True)
class NativeCapability:
    ctm: CtmCapability
    ground: GroundCapability
    speed_tuple: SpeedTuple

    @property
    def speedTuple(self) -> SpeedTuple:
        return self.speed_tuple

    @property
    def ctm_state(self) -> str:
        return self.ctm.state

    @property
    def ground_state(self) -> str:
        return self.ground.state

    @property
    def admitted(self) -> bool:
        return self.ctm.state == "disabled" and self.ground.state == "grounded"

    @property
    def admission_signature(self) -> tuple[str, ...]:
        return (
            self.ctm.state,
            self.ctm.reason,
            self.ground.state,
            self.ground.reason,
            self.ground.falling,
            self.ground.flying,
            self.ground.swimming,
            self.ground.submerged,
            self.ground.mounted,
        ) + (self.ground.taxi,)


_NATIVE_FAILURES = {"", "call_error", "missing", "wrong_type", "nil_result"}
_GROUND_VALUES = {"false", "true", "unknown"}


def _native_capability(value: Any, speed: Any) -> NativeCapability:
    if not isinstance(value, dict) or set(value) != {"ctm", "ground", "speedTuple"}:
        raise MotionError("native motion capability object is malformed")
    ctm = value["ctm"]
    if not isinstance(ctm, dict) or set(ctm) != {"accessor", "cvar", "state", "reason"}:
        raise MotionError("native CTM capability is malformed")
    if ctm["accessor"] != "C_CVar.GetCVarBool" or ctm["cvar"] != "autointeract":
        raise MotionError("native CTM accessor identity is invalid")
    if not isinstance(ctm["state"], str) or ctm["state"] not in {"disabled", "enabled", "unknown"}:
        raise MotionError("native CTM state is invalid")
    if not isinstance(ctm["reason"], str) or ctm["reason"] not in _NATIVE_FAILURES:
        raise MotionError("native CTM failure code is invalid")
    if (ctm["state"] == "unknown") != bool(ctm["reason"]):
        raise MotionError("native CTM state/reason combination is invalid")

    ground = value["ground"]
    expected_ground = {"state", "falling", "flying", "swimming", "submerged", "mounted", "taxi", "reason"}
    if not isinstance(ground, dict) or set(ground) != expected_ground:
        raise MotionError("native ground capability is malformed")
    if not isinstance(ground["state"], str) or ground["state"] not in {
        "grounded",
        "not_grounded",
        "unknown",
    }:
        raise MotionError("native ground state is invalid")
    ground_values = tuple(
        ground[name] for name in ("falling", "flying", "swimming", "submerged", "mounted", "taxi")
    )
    if any(not isinstance(value, str) or value not in _GROUND_VALUES for value in ground_values):
        raise MotionError("native ground predicate state is invalid")
    if not isinstance(ground["reason"], str) or ground["reason"] not in _NATIVE_FAILURES:
        raise MotionError("native ground failure code is invalid")
    unknown = any(value == "unknown" for value in ground_values)
    if unknown:
        if ground["state"] != "unknown" or not ground["reason"]:
            raise MotionError("native ground state/reason combination is invalid")
    elif ground["reason"] or ground["state"] != ("not_grounded" if "true" in ground_values else "grounded"):
        raise MotionError("native ground state contradicts predicates")

    speed_tuple = value["speedTuple"]
    expected_speed = {"current", "run", "flight", "swim", "unitStatus"}
    if not isinstance(speed_tuple, dict) or set(speed_tuple) != expected_speed:
        raise MotionError("native speed tuple is malformed")
    speeds: list[float] = []
    for name in ("current", "run", "flight", "swim"):
        item = speed_tuple[name]
        parsed = _finite(item, f"motion.native.speedTuple.{name}")
        if not 0.0 <= parsed <= 1000.0:
            raise MotionError("native speed tuple is outside bounds")
        speeds.append(parsed)
    if speed_tuple["unitStatus"] != "unverified":
        raise MotionError("native speed tuple unit status is invalid")
    parsed_speed = _finite(speed, "motion.speed")
    if parsed_speed != speeds[0]:
        raise MotionError("motion.speed does not match native speed tuple current")
    return NativeCapability(
        ctm=CtmCapability(str(ctm["accessor"]), str(ctm["cvar"]), str(ctm["state"]), str(ctm["reason"])),
        ground=GroundCapability(
            str(ground["state"]),
            str(ground["falling"]),
            str(ground["flying"]),
            str(ground["swimming"]),
            str(ground["submerged"]),
            str(ground["mounted"]),
            str(ground["taxi"]),
            str(ground["reason"]),
        ),
        speed_tuple=SpeedTuple(speeds[0], speeds[1], speeds[2], speeds[3], str(speed_tuple["unitStatus"])),
    )


MAX_FRAME_AGE = 5.0
MAX_PULSE_SECONDS = 0.35
MAX_WAYPOINT_DISTANCE = 2.0
MAX_WAYPOINT_SECONDS = 20.0
MAX_WAYPOINT_PULSES = 64
MAX_WAYPOINT_CAMERA_TURNS = 8
# The daemon owns one finite operation deadline.  Keep the values here so the
# IPC client and the producer cannot silently drift apart.  A one-Hz native
# publication cadence means the two frames after release must remain inside
# the same deadline; model work is charged before this reserve.
MOTION_KEY_OPERATION_SECONDS = 30.0
MOTION_CAMERA_OPERATION_SECONDS = 30.0
# Five translation probes each need the native one-Hz successor after release,
# the camera heading turn needs the same feedback chain, and the operation
# still keeps a transport/cleanup reserve.  Keep a finite ninety-second
# producer budget so the real publication cadence and model/capture work fit
# without weakening freshness or admission bounds.
MOTION_CALIBRATION_PROBE_COUNT = 5
MOTION_FEEDBACK_JITTER_SECONDS = 0.25
MOTION_CLEANUP_MARGIN_SECONDS = 1.0
MOTION_TRANSPORT_MARGIN_SECONDS = 5.0
MOTION_FEEDBACK_PERIOD_SECONDS = 1.0
MOTION_POST_RELEASE_PUBLICATIONS = 2
MOTION_POST_RELEASE_RESERVE_SECONDS = (
    MOTION_FEEDBACK_PERIOD_SECONDS * MOTION_POST_RELEASE_PUBLICATIONS
    + MOTION_FEEDBACK_JITTER_SECONDS * MOTION_POST_RELEASE_PUBLICATIONS
    + MOTION_CLEANUP_MARGIN_SECONDS
)
MOTION_CALIBRATION_OPERATION_SECONDS = 90.0
MIN_BASIS_DISPLACEMENT = 0.01
MAX_BASIS_DISPLACEMENT = 1.0
# Calibration uses a short technical pulse so the repeated-forward and four
# role probes fit inside the two-unit intent budget at the normal measured speed.
# Runtime/user motion still uses the selected move profile minimum.
MIN_MOVEMENT_CALIBRATION_PULSE_SECONDS = 0.03
DEFAULT_MOVEMENT_CALIBRATION_PULSE_SECONDS = MIN_MOVEMENT_CALIBRATION_PULSE_SECONDS
TRAVEL_UNCERTAINTY_FRACTION = 0.20
# A forward pulse is admitted without a camera correction only inside this
# named bearing allowance.  Waypoint admission uses the same value when it
# proves the two-dimensional endpoint envelope.
WAYPOINT_TRANSLATION_HEADING_TOLERANCE = 0.20
# The final native confirmation is allowed this small pose delta.  Waypoint
# admission includes the same bound before any camera or key dispatch.
MAX_CONFIRMATION_POSITION_DRIFT = 0.02
MAX_CONFIRMATION_FACING_DRIFT = 0.02
MAX_CAMERA_YAW_PER_PIXEL = 0.25
# Camera calibration is deliberately limited to a small, pre-input angular
# envelope. The limit is derived from the declared worst-case sensitivity,
# rather than from a normalized post-drag endpoint that can alias a full turn.
MIN_CAMERA_CALIBRATION_PIXELS = 4
MAX_CAMERA_CALIBRATION_PIXELS = 8
MAX_CAMERA_CALIBRATION_YAW = 2.0
MAX_CAMERA_INPUT_YAW = math.pi - 0.05
MAX_CAMERA_RESPONSE_RELATIVE_ERROR = 0.75
MIN_CAMERA_RESPONSE_ABSOLUTE_ERROR = 0.05


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise MotionError(f"{name} must be finite")
    return float(value)


def _text(value: Any, name: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not empty and not value):
        raise MotionError(f"{name} must be text")
    if len(value) > 256:
        raise MotionError(f"{name} is too long")
    return value


@dataclass(frozen=True, slots=True)
class MotionFrame:
    boot: str
    sequence: int
    capture_monotonic: float
    identity_fingerprint: str
    source: str
    zone: str
    instance: int
    x: float
    y: float
    z: float
    facing: float
    speed: float
    native: NativeCapability
    combat: bool
    dead_or_ghost: bool
    chat_focused: bool
    bindings: tuple[tuple[str, str], ...]

    @classmethod
    def from_sample(
        cls,
        sample: Any,
        identity: Any,
        *,
        capture_started_monotonic: float | None = None,
    ) -> MotionFrame:
        if getattr(sample, "kind", None) != "FRESH" or getattr(sample, "frame", None) is None:
            raise MotionError("native motion requires a fresh schema-4 frame")
        frame = sample.frame
        snapshot_object = getattr(frame, "snapshot", None)
        snapshot = getattr(snapshot_object, "value", None)
        if not isinstance(snapshot, dict):
            raise MotionError("native motion frame has no decoded snapshot")
        if snapshot.get("schema") != 4:
            raise MotionError("native motion requires schema 4")
        identity_fingerprint = _text(getattr(identity, "fingerprint", ""), "motion.identity")
        motion = snapshot.get("motion")
        context = snapshot.get("context")
        chat_edit = snapshot.get("chatEdit")
        if not isinstance(motion, dict) or not isinstance(context, dict):
            raise MotionError("native motion frame is missing motion/context")
        if (
            not isinstance(chat_edit, dict)
            or not isinstance(chat_edit.get("active"), bool)
            or not isinstance(chat_edit.get("focused"), bool)
        ):
            raise MotionError("native motion frame is missing chat-edit focus state")
        position = motion.get("position")
        bindings = motion.get("bindings")
        if not isinstance(position, dict) or not isinstance(bindings, dict):
            raise MotionError("native motion fields are malformed")
        required = ("moveForward", "moveBackward", "strafeLeft", "strafeRight", "turnLeft")
        if set(bindings) != set(required):
            raise MotionError("native motion bindings are incomplete")
        parsed_bindings: list[tuple[str, str]] = []
        for role in required:
            value = _text(bindings[role], f"motion.bindings.{role}")
            parsed_bindings.append((role, value))
        sequence = frame.sequence
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence <= 0:
            raise MotionError("native motion sequence is malformed")
        instance = position.get("instance")
        if isinstance(instance, bool) or not isinstance(instance, int) or instance < 0:
            raise MotionError("native motion instance is malformed")
        facing = _finite(motion.get("facing"), "motion.facing")
        if not 0.0 <= facing <= 2.0 * math.pi:
            raise MotionError("native motion facing is outside bounds")
        speed = _finite(motion.get("speed"), "motion.speed")
        if not 0.0 <= speed <= 1000.0:
            raise MotionError("native motion speed is outside bounds")
        combat = motion.get("combat")
        dead = motion.get("deadOrGhost")
        if not isinstance(combat, bool) or not isinstance(dead, bool):
            raise MotionError("native motion safety flags are malformed")
        native = _native_capability(motion.get("native"), speed)
        zone = _text(context.get("zone"), "motion.zone", empty=True)
        subzone = _text(context.get("subzone"), "motion.subzone", empty=True)
        capture_monotonic = (
            _finite(capture_started_monotonic, "motion.capture_started_monotonic")
            if capture_started_monotonic is not None
            else _finite(sample.capture_monotonic, "motion.capture_monotonic")
        )
        return cls(
            boot=_text(frame.boot, "motion.boot"),
            sequence=sequence,
            capture_monotonic=capture_monotonic,
            identity_fingerprint=identity_fingerprint,
            source="native-addon",
            zone=f"{zone}\x1f{subzone}",
            instance=instance,
            x=_finite(position.get("x"), "motion.position.x"),
            y=_finite(position.get("y"), "motion.position.y"),
            z=_finite(position.get("z"), "motion.position.z"),
            facing=facing,
            speed=speed,
            native=native,
            combat=combat,
            dead_or_ghost=dead,
            chat_focused=chat_edit["active"] and chat_edit["focused"],
            bindings=tuple(parsed_bindings),
        )

    def binding(self, role: str) -> str:
        for name, value in self.bindings:
            if name == role:
                return value
        raise MotionError(f"native motion has no binding for {role}")

    def require_native_gate(self, *, matching: MotionFrame | None = None) -> None:
        """Require the exact native state needed before physical admission."""

        if not self.native.admitted:
            raise MotionError("native motion capability gate is not admitted")
        if matching is not None and self.native.admission_signature != matching.native.admission_signature:
            raise MotionError("native motion capability changed during admission")

    def require_safe_successor(
        self,
        previous: MotionFrame | None,
        *,
        now: float,
        max_age: float = MAX_FRAME_AGE,
    ) -> None:
        now = _finite(now, "motion.now")
        if not 0.0 <= now - self.capture_monotonic <= max_age:
            raise MotionError("native motion capture is stale")
        if self.combat or self.dead_or_ghost:
            raise MotionError("native motion is unsafe during combat or death")
        if previous is None:
            return
        if self.identity_fingerprint != previous.identity_fingerprint:
            raise MotionError("native motion client identity changed")
        if self.source != previous.source:
            raise MotionError("native motion source changed")
        if self.boot != previous.boot:
            raise MotionError("native motion addon boot changed")
        if self.sequence <= previous.sequence:
            raise MotionError("native motion sequence did not advance")
        if self.capture_monotonic <= previous.capture_monotonic:
            raise MotionError("native motion capture timestamp did not advance")
        if self.instance != previous.instance or self.zone != previous.zone:
            raise MotionError("native motion scene or instance changed")


class NativeMotionProvider:
    """Production provider backed by the daemon's real status-capture method."""

    def __init__(
        self,
        capture: Callable[[], Any],
        identity: Callable[[], Any],
        *,
        capture_with_deadline: Callable[..., Any] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._capture = capture
        self._capture_with_deadline = capture_with_deadline
        self._identity = identity
        self._clock = clock

    def observe(
        self,
        generation: int,
        *,
        previous: MotionFrame | None = None,
        deadline: float | None = None,
        not_before: float | None = None,
    ) -> MotionFrame:
        if isinstance(generation, bool) or not isinstance(generation, int) or generation <= 0:
            raise MotionError("motion observation requires a positive generation")
        if deadline is None:
            deadline = self._clock() + MAX_FRAME_AGE
        if not_before is not None:
            not_before = _finite(not_before, "motion.not_before")
        while True:
            if deadline is not None and self._clock() >= deadline:
                raise MotionError("native motion observation exceeded its deadline")
            identity = self._identity()
            capture_started = self._clock()
            if self._capture_with_deadline is None:
                sample = self._capture()
            else:
                sample = self._capture_with_deadline(deadline=deadline)
            if getattr(sample, "kind", None) != "FRESH":
                remaining = deadline - self._clock()
                if remaining <= 0:
                    raise MotionError("native motion observation exceeded its deadline")
                time.sleep(min(0.05, remaining))
                continue
            sample_identity = getattr(sample, "window_identity", None)
            if sample_identity != getattr(identity, "fingerprint", None):
                raise MotionError("native motion sample identity does not match the resolved client")
            # A provider's capture timestamp is always the instant the native
            # read began.  The decoder timestamp is necessarily later and
            # would make a slow capture appear fresher than the evidence that
            # was actually admitted.
            frame = MotionFrame.from_sample(
                sample,
                identity,
                capture_started_monotonic=capture_started,
            )
            if not_before is not None and frame.capture_monotonic < not_before:
                remaining = deadline - self._clock()
                if remaining <= 0:
                    raise MotionError("native motion observation exceeded its deadline")
                time.sleep(min(0.05, remaining))
                continue
            frame.require_safe_successor(previous, now=self._clock())
            return frame

    def observe_after_release(
        self,
        generation: int,
        *,
        previous: MotionFrame,
        deadline: float | None = None,
    ) -> MotionFrame:
        """Require a publication strictly later than the post-release barrier.

        A capture made after XTEST release can still contain the last addon
        publication from before release.  The first fresh frame establishes
        what was visible at the release boundary; only the next own-domain
        publication is returned as action feedback.
        """

        if deadline is None:
            deadline = self._clock() + MAX_FRAME_AGE
        barrier = self.observe(generation, previous=previous, deadline=deadline)
        # The first post-release publication is itself evidence at the release
        # boundary.  A disallowed barrier cannot be hidden by a later allowed
        # publication; the daemon must clear every retained admission proof.
        barrier.require_native_gate(matching=previous)
        final = self.observe(generation, previous=barrier, deadline=deadline)
        final.require_native_gate(matching=barrier)
        return final


@dataclass(frozen=True, slots=True)
class RouteEvidence:
    identity_fingerprint: str
    capture_monotonic: float
    scene: str
    route_id: str
    target_visible: bool
    ground_clear: bool
    generation: int = 0
    boot: str = ""
    sequence: int = 0
    instance: int = 0
    zone: str = ""
    screenshot_digest: str = ""
    corridor_heading: float | None = None
    corridor_distance: float | None = None

    def __post_init__(self) -> None:
        _text(self.identity_fingerprint, "route.identity")
        _finite(self.capture_monotonic, "route.capture_monotonic")
        _text(self.scene, "route.scene")
        if not isinstance(self.route_id, str) or len(self.route_id) > 256:
            raise MotionError("route.route_id is malformed")
        if not isinstance(self.target_visible, bool) or not isinstance(self.ground_clear, bool):
            raise MotionError("route evidence flags are malformed")
        if isinstance(self.generation, bool) or not isinstance(self.generation, int) or self.generation <= 0:
            raise MotionError("route.generation is malformed")
        _text(self.boot, "route.boot")
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence <= 0:
            raise MotionError("route.sequence is malformed")
        if isinstance(self.instance, bool) or not isinstance(self.instance, int) or self.instance < 0:
            raise MotionError("route.instance is malformed")
        _text(self.zone, "route.zone", empty=True)
        _text(self.screenshot_digest, "route.screenshot_digest")
        if self.corridor_heading is not None:
            heading = _finite(self.corridor_heading, "route.corridor_heading")
            if not -math.pi <= heading <= math.pi:
                raise MotionError("route.corridor_heading is outside bounds")
        if self.corridor_distance is not None:
            _finite(self.corridor_distance, "route.corridor_distance")


@dataclass(frozen=True, slots=True)
class ViewportEvidence:
    """Fresh visual proof for the point at which a camera drag may begin."""

    identity_fingerprint: str
    capture_monotonic: float
    scene: str
    point: tuple[int, int]
    ui_clear: bool
    units_clear: bool
    generation: int
    boot: str
    sequence: int
    instance: int
    zone: str
    screenshot_digest: str

    def __post_init__(self) -> None:
        _text(self.identity_fingerprint, "viewport.identity")
        _finite(self.capture_monotonic, "viewport.capture_monotonic")
        if self.scene != "world":
            raise MotionError("viewport scene must be world")
        if (
            not isinstance(self.point, tuple)
            or len(self.point) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) for value in self.point)
            or any(value < 0 for value in self.point)
        ):
            raise MotionError("viewport point is malformed")
        if not isinstance(self.ui_clear, bool) or not isinstance(self.units_clear, bool):
            raise MotionError("viewport clearance flags are malformed")
        if not self.ui_clear or not self.units_clear:
            raise MotionError("viewport point is not clear of UI or units")
        if isinstance(self.generation, bool) or not isinstance(self.generation, int) or self.generation <= 0:
            raise MotionError("viewport.generation is malformed")
        _text(self.boot, "viewport.boot")
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence <= 0:
            raise MotionError("viewport.sequence is malformed")
        if isinstance(self.instance, bool) or not isinstance(self.instance, int) or self.instance < 0:
            raise MotionError("viewport.instance is malformed")
        _text(self.zone, "viewport.zone", empty=True)
        _text(self.screenshot_digest, "viewport.screenshot_digest")


@dataclass(frozen=True, slots=True)
class MovementBasis:
    """Measured relation between native facing and the world movement axes.

    ``world_forward = facing_sign * native_facing + forward_heading_offset``;
    the strafe offset is the measured residual from that forward axis and the
    calibrated native-left handedness quarter-turn.
    """

    identity_fingerprint: str
    boot: str
    generation: int
    capture_id: str
    before_sequence: int
    after_sequence: int
    forward_heading_offset: float
    forward_displacement: float
    pulse_seconds: float = 0.08
    facing_sign: int = 1
    strafe_heading_offset: float | None = None
    strafe_displacement: float | None = None
    handedness: int | None = None
    convention: str = "native-xy-forward-radians-v2"
    # Appended after the original fields so callers that construct the
    # measured basis positionally retain their prior field order.
    strafe_pulse_seconds: float | None = None
    backward_displacement: float | None = None
    backward_pulse_seconds: float | None = None
    strafe_right_displacement: float | None = None
    strafe_right_pulse_seconds: float | None = None
    backward_heading_offset: float | None = None
    strafe_right_heading_offset: float | None = None

    def __post_init__(self) -> None:
        _text(self.identity_fingerprint, "movement.identity")
        _text(self.boot, "movement.boot")
        if isinstance(self.generation, bool) or not isinstance(self.generation, int) or self.generation <= 0:
            raise MotionError("movement.generation is malformed")
        capture_id = _text(self.capture_id, "movement.capture_id")
        if not capture_id.startswith("movement:"):
            raise MotionError("movement basis lacks a controlled calibration capture")
        for value, name in (
            (self.before_sequence, "movement.before_sequence"),
            (self.after_sequence, "movement.after_sequence"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise MotionError(f"{name} is malformed")
        if self.after_sequence <= self.before_sequence:
            raise MotionError("movement basis sequences did not advance")
        offset = _finite(self.forward_heading_offset, "movement.forward_heading_offset")
        if not -math.pi <= offset <= math.pi:
            raise MotionError("movement heading offset is outside bounds")
        displacement = _finite(self.forward_displacement, "movement.forward_displacement")
        if not MIN_BASIS_DISPLACEMENT <= displacement <= MAX_BASIS_DISPLACEMENT:
            raise MotionError("movement basis displacement is outside bounds")
        pulse = _finite(self.pulse_seconds, "movement.pulse_seconds")
        if not MIN_MOVEMENT_CALIBRATION_PULSE_SECONDS <= pulse <= MAX_PULSE_SECONDS:
            raise MotionError("movement basis pulse is outside bounds")
        if isinstance(self.facing_sign, bool) or self.facing_sign not in {-1, 1}:
            raise MotionError("movement facing sign is not calibrated")
        if self.strafe_heading_offset is None or self.strafe_displacement is None or self.handedness is None:
            raise MotionError("movement basis lacks non-collinear handedness calibration")
        strafe_offset = _finite(self.strafe_heading_offset, "movement.strafe_heading_offset")
        if not -math.pi <= strafe_offset <= math.pi:
            raise MotionError("movement strafe heading offset is outside bounds")
        strafe_displacement = _finite(self.strafe_displacement, "movement.strafe_displacement")
        if not MIN_BASIS_DISPLACEMENT <= strafe_displacement <= MAX_BASIS_DISPLACEMENT:
            raise MotionError("movement strafe displacement is outside bounds")
        if self.strafe_pulse_seconds is not None:
            strafe_pulse = _finite(self.strafe_pulse_seconds, "movement.strafe_pulse_seconds")
            if not MIN_MOVEMENT_CALIBRATION_PULSE_SECONDS <= strafe_pulse <= MAX_PULSE_SECONDS:
                raise MotionError("movement strafe pulse is outside bounds")
        if isinstance(self.handedness, bool) or self.handedness not in {-1, 1}:
            raise MotionError("movement handedness is not calibrated")
        if self.convention != "native-xy-forward-radians-v2":
            raise MotionError("movement coordinate convention is not calibrated")
        for displacement, pulse, name in (
            (self.backward_displacement, self.backward_pulse_seconds, "backward"),
            (self.strafe_right_displacement, self.strafe_right_pulse_seconds, "strafe_right"),
        ):
            if displacement is not None:
                value = _finite(displacement, f"movement.{name}_displacement")
                if not MIN_BASIS_DISPLACEMENT <= value <= MAX_BASIS_DISPLACEMENT:
                    raise MotionError(f"movement {name} displacement is outside bounds")
            if pulse is not None:
                value = _finite(pulse, f"movement.{name}_pulse_seconds")
                if not MIN_MOVEMENT_CALIBRATION_PULSE_SECONDS <= value <= MAX_PULSE_SECONDS:
                    raise MotionError(f"movement {name} pulse is outside bounds")
            if (displacement is None) != (pulse is None):
                raise MotionError(f"movement {name} measure is incomplete")
        for offset, name in (
            (self.backward_heading_offset, "backward_heading_offset"),
            (self.strafe_right_heading_offset, "strafe_right_heading_offset"),
        ):
            if offset is not None and not -math.pi <= _finite(offset, f"movement.{name}") <= math.pi:
                raise MotionError(f"movement {name} is outside bounds")
        if (self.backward_heading_offset is None) != (self.backward_displacement is None):
            raise MotionError("movement backward measure is incomplete")
        if (self.strafe_right_heading_offset is None) != (self.strafe_right_displacement is None):
            raise MotionError("movement strafe-right measure is incomplete")


@dataclass(frozen=True, slots=True)
class CameraMapping:
    """A mapping established by a controlled native feedback calibration."""

    identity_fingerprint: str
    generation: int
    capture_id: str
    yaw_per_pixel: float
    convention: str = "xy-facing-radians-v1"
    boot: str = ""

    def __post_init__(self) -> None:
        _text(self.identity_fingerprint, "camera.identity")
        if isinstance(self.generation, bool) or not isinstance(self.generation, int) or self.generation <= 0:
            raise MotionError("camera.generation is malformed")
        _text(self.capture_id, "camera.capture_id")
        if self.boot:
            _text(self.boot, "camera.boot")
        value = _finite(self.yaw_per_pixel, "camera.yaw_per_pixel")
        if not 0.0001 <= abs(value) <= MAX_CAMERA_YAW_PER_PIXEL:
            raise MotionError("camera yaw mapping is outside bounds")
        if self.convention != "xy-facing-radians-v1":
            raise MotionError("camera coordinate convention is not calibrated")


def normalize_angle(value: float) -> float:
    value = _finite(value, "angle")
    return (value + math.pi) % (2.0 * math.pi) - math.pi


def waypoint_heading_error(
    frame: MotionFrame,
    target_x: float,
    target_y: float,
    basis: MovementBasis,
) -> tuple[float, float]:
    if not isinstance(basis, MovementBasis):
        raise MotionError("waypoint requires a measured movement basis")
    if basis.identity_fingerprint != frame.identity_fingerprint or basis.boot != frame.boot:
        raise MotionError("movement basis is stale for the native frame")
    if basis.handedness not in {-1, 1}:
        raise MotionError("movement coordinate handedness is not calibrated")
    target_x = _finite(target_x, "waypoint.x")
    target_y = _finite(target_y, "waypoint.y")
    dx, dy = target_x - frame.x, target_y - frame.y
    distance = math.hypot(dx, dy)
    if distance > MAX_WAYPOINT_DISTANCE:
        raise MotionError("waypoint exceeds the bounded local distance")
    if distance == 0:
        return 0.0, distance
    world_heading = math.atan2(dy, dx)
    native_heading = basis.facing_sign * (world_heading - basis.forward_heading_offset)
    return normalize_angle(native_heading - frame.facing), distance


__all__ = [
    "CameraMapping",
    "MAX_FRAME_AGE",
    "MAX_PULSE_SECONDS",
    "MAX_WAYPOINT_DISTANCE",
    "MAX_WAYPOINT_PULSES",
    "MAX_WAYPOINT_SECONDS",
    "MAX_WAYPOINT_CAMERA_TURNS",
    "MAX_BASIS_DISPLACEMENT",
    "MIN_MOVEMENT_CALIBRATION_PULSE_SECONDS",
    "DEFAULT_MOVEMENT_CALIBRATION_PULSE_SECONDS",
    "MIN_BASIS_DISPLACEMENT",
    "TRAVEL_UNCERTAINTY_FRACTION",
    "WAYPOINT_TRANSLATION_HEADING_TOLERANCE",
    "MAX_CONFIRMATION_POSITION_DRIFT",
    "MAX_CONFIRMATION_FACING_DRIFT",
    "MAX_CAMERA_YAW_PER_PIXEL",
    "MIN_CAMERA_CALIBRATION_PIXELS",
    "MAX_CAMERA_CALIBRATION_PIXELS",
    "MAX_CAMERA_CALIBRATION_YAW",
    "MAX_CAMERA_INPUT_YAW",
    "MAX_CAMERA_RESPONSE_RELATIVE_ERROR",
    "MIN_CAMERA_RESPONSE_ABSOLUTE_ERROR",
    "MOTION_KEY_OPERATION_SECONDS",
    "MOTION_CAMERA_OPERATION_SECONDS",
    "MOTION_CALIBRATION_OPERATION_SECONDS",
    "MOTION_CALIBRATION_PROBE_COUNT",
    "MOTION_TRANSPORT_MARGIN_SECONDS",
    "MOTION_FEEDBACK_PERIOD_SECONDS",
    "MOTION_FEEDBACK_JITTER_SECONDS",
    "MOTION_CLEANUP_MARGIN_SECONDS",
    "MOTION_POST_RELEASE_PUBLICATIONS",
    "MOTION_POST_RELEASE_RESERVE_SECONDS",
    "MotionError",
    "CtmCapability",
    "GroundCapability",
    "SpeedTuple",
    "NativeCapability",
    "MotionFrame",
    "MovementBasis",
    "NativeMotionProvider",
    "RouteEvidence",
    "ViewportEvidence",
    "normalize_angle",
    "waypoint_heading_error",
]
