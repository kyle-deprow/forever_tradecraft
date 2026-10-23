from __future__ import annotations

import math
import threading
import time
from types import SimpleNamespace

import pytest

import crowley.session.daemon as daemon_module
from crowley.session.daemon import SessionDaemon
from crowley.session.decoder import Sample
from crowley.session.driver import DriverError
from crowley.session.executor import DemonstrationRole, KeyRole, MotionProfile
from crowley.session.motion import (
    DEFAULT_MOVEMENT_CALIBRATION_PULSE_SECONDS,
    MAX_BASIS_DISPLACEMENT,
    MAX_WAYPOINT_CAMERA_TURNS,
    MAX_WAYPOINT_DISTANCE,
    MIN_MOVEMENT_CALIBRATION_PULSE_SECONDS,
    TRAVEL_UNCERTAINTY_FRACTION,
    WAYPOINT_TRANSLATION_HEADING_TOLERANCE,
    CameraMapping,
    MotionError,
    MotionFrame,
    MovementBasis,
    NativeMotionProvider,
    RouteEvidence,
    waypoint_heading_error,
)


class _Identity:
    fingerprint = "client-1"


def _sample(
    *,
    sequence: int = 1,
    capture: float = 10.0,
    boot: str = "boot-1",
    x: float = 0.0,
    y: float = 0.0,
    facing: float = 0.0,
    combat: bool = False,
    dead: bool = False,
    speed: float = 1.0,
) -> Sample:
    snapshot = {
        "schema": 5,
        "hover": {"kind": "none", "name": ""},
        "mailOpen": False,
        "blockingUI": {
            "staticPopupAvailable": True,
            "staticPopupShown": False,
            "gameMenuAvailable": True,
            "gameMenuShown": False,
        },
        "auctioneer": {
            "targetPresent": False,
            "targetName": "",
            "rangeAvailable": False,
            "withinTradeRange": False,
            "bindingAvailable": False,
            "ctrlF12Action": "",
            "interactionMode": "any",
        },
        "boot": boot,
        "sequence": sequence,
        "chatEdit": {"active": False, "focused": False, "text": ""},
        "motion": {
            "position": {"x": x, "y": y, "z": 0.0, "instance": 1},
            "facing": facing,
            "speed": speed,
            "combat": combat,
            "deadOrGhost": dead,
            "bindings": {
                "moveForward": "W",
                "moveBackward": "S",
                "strafeLeft": "A",
                "strafeRight": "D",
                "turnLeft": "Q",
                "jump": "SPACE",
                "turnRight": "E",
            },
            "native": {
                "ctm": {
                    "accessor": "C_CVar.GetCVarBool",
                    "cvar": "autointeract",
                    "state": "disabled",
                    "reason": "",
                },
                "ground": {
                    "state": "grounded",
                    "falling": "false",
                    "flying": "false",
                    "swimming": "false",
                    "submerged": "false",
                    "mounted": "false",
                    "taxi": "false",
                    "reason": "",
                },
                "speedTuple": {
                    "current": speed,
                    "run": 0,
                    "flight": 0,
                    "swim": 0,
                    "unitStatus": "unverified",
                },
            },
        },
        "context": {"zone": "Elwynn", "subzone": "Goldshire"},
    }
    frame = SimpleNamespace(sequence=sequence, boot=boot, snapshot=SimpleNamespace(value=snapshot))
    return Sample("FRESH", frame, capture, (0, 0, 256, 256), 1, "client-1")


def _actual_waypoint_daemon(
    *,
    target_bearing: float,
    response_factor: float,
    corrected_facing: float = 0.0,
) -> tuple[SessionDaemon, MotionFrame, MotionFrame, list[tuple[KeyRole, float]], list[int]]:
    """Build the real waypoint loop around controlled feedback boundaries."""

    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.7,
        pulse_seconds=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.7,
        strafe_pulse_seconds=0.1,
        facing_sign=1,
        handedness=1,
    )
    target_x = 0.8 * math.cos(target_bearing)
    target_y = 0.8 * math.sin(target_bearing)
    corrected_facing = corrected_facing % (2.0 * math.pi)
    before = MotionFrame.from_sample(_sample(sequence=1, capture=10.0), _Identity())
    confirmed = MotionFrame.from_sample(
        _sample(sequence=2, capture=10.01, facing=corrected_facing), _Identity()
    )
    traveled = 0.8 * response_factor
    after = MotionFrame.from_sample(
        _sample(
            sequence=3,
            capture=10.2,
            x=traveled * math.cos(corrected_facing),
            y=traveled * math.sin(corrected_facing),
            facing=corrected_facing,
            speed=0.0,
        ),
        _Identity(),
    )
    daemon._native_clock = lambda: 10.5
    daemon._require_interaction = lambda _generation: 1

    def observe_motion(
        _generation: int,
        previous: MotionFrame | None = None,
        *,
        after_release: bool = False,
        **_kwargs,
    ) -> MotionFrame:
        if after_release:
            return after
        return confirmed if previous is not None else before

    daemon._observe_motion = observe_motion
    physical_calls: list[tuple[KeyRole, float]] = []
    daemon.driver = SimpleNamespace(
        run_motion_key_hold=lambda role, duration, *_args, **_kwargs: physical_calls.append((role, duration))
    )
    camera_calls: list[int] = []

    def camera_delta(
        pixels: int,
        *,
        generation: int,
        previous: MotionFrame | None = None,
    ) -> MotionFrame:
        del generation, previous
        camera_calls.append(pixels)
        return confirmed

    daemon.execute_camera_delta = camera_delta

    def observe_route(
        generation: int,
        target_x: float,
        target_y: float,
        *,
        frame: MotionFrame,
    ) -> RouteEvidence:
        distance = math.hypot(target_x - frame.x, target_y - frame.y)
        heading = math.atan2(target_y - frame.y, target_x - frame.x) - daemon._world_forward_heading(frame)
        heading = (heading + math.pi) % (2.0 * math.pi) - math.pi
        return RouteEvidence(
            "client-1",
            frame.capture_monotonic + 0.01,
            "world",
            "clear",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=heading,
            corridor_distance=distance,
        )

    daemon._observe_route = observe_route
    daemon._waypoint_target = (target_x, target_y)
    daemon._waypoint_after = after
    return daemon, before, after, physical_calls, camera_calls


def test_native_motion_successor_accepts_sequence_gap_but_rejects_scene_identity_or_unsafe() -> None:
    first = MotionFrame.from_sample(_sample(sequence=4), _Identity())
    later = MotionFrame.from_sample(_sample(sequence=9, capture=10.2, x=0.1), _Identity())
    later.require_safe_successor(first, now=10.3)

    with pytest.raises(MotionError, match="identity"):
        later.require_safe_successor(
            MotionFrame.from_sample(_sample(sequence=4), SimpleNamespace(fingerprint="other")),
            now=10.3,
        )
    with pytest.raises(MotionError, match="unsafe"):
        MotionFrame.from_sample(_sample(combat=True), _Identity()).require_safe_successor(None, now=10.1)


def test_native_gate_blocks_unknown_or_drift_and_clears_both_retained_proofs() -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon.camera_mapping = object()
    daemon.movement_basis = object()
    admitted = MotionFrame.from_sample(_sample(sequence=1), _Identity())
    blocked_sample = _sample(sequence=2)
    blocked_value = blocked_sample.frame.snapshot.value
    blocked_value["motion"]["native"]["ctm"]["state"] = "unknown"
    blocked_value["motion"]["native"]["ctm"]["reason"] = "missing"
    blocked = MotionFrame.from_sample(blocked_sample, _Identity())
    with pytest.raises(DriverError, match="capability"):
        daemon._require_native_gate(blocked)
    assert daemon.camera_mapping is None
    assert daemon.movement_basis is None

    daemon.camera_mapping = object()
    daemon.movement_basis = object()
    drift_sample = _sample(sequence=3)
    drift_value = drift_sample.frame.snapshot.value
    drift_value["motion"]["native"]["ground"]["state"] = "not_grounded"
    drift_value["motion"]["native"]["ground"]["falling"] = "true"
    drift = MotionFrame.from_sample(drift_sample, _Identity())
    with pytest.raises(DriverError, match="capability"):
        daemon._require_native_gate(drift, matching=admitted)
    assert daemon.camera_mapping is None
    assert daemon.movement_basis is None


def test_native_provider_never_turns_no_change_into_motion() -> None:
    samples = iter((_sample(sequence=1), _sample(sequence=3, capture=10.2, x=0.2)))
    clock_values = iter((10.0, 10.05, 10.1, 10.15, 10.2, 10.3))
    provider = NativeMotionProvider(
        lambda: next(samples), lambda: _Identity(), clock=lambda: next(clock_values)
    )
    first = provider.observe(1, deadline=11.0)
    second = provider.observe(1, previous=first, deadline=11.0)
    assert (first.sequence, second.sequence) == (1, 3)
    assert second.binding("moveForward") == "W"


def test_visual_named_observation_freshness_uses_capture_start() -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon.config = SimpleNamespace(
        profile=SimpleNamespace(character="Arthur", realm="Azeroth"),
    )
    daemon.capture_index = 0
    daemon._named_capture_sequence = 0
    identity = SimpleNamespace(fingerprint="client-1", child_xid=17)
    capture_times: list[float] = []
    model_times: list[float] = []

    def capture_model(*, deadline: float) -> bytes:
        del deadline
        capture_times.append(time.monotonic())
        time.sleep(0.01)
        return b"crop"

    daemon._capture_model = capture_model
    daemon._observe_model = lambda image, *, timeout: SimpleNamespace(
        state="character_select",
        facts={},
    )
    daemon._check_named_facts = lambda state, facts: None
    daemon._resolve_identity = lambda *, deadline: identity
    observation = daemon._observe_named_state(identity, "character_select")
    model_times.append(time.monotonic())

    assert observation.observed_monotonic <= capture_times[0]
    assert observation.observed_monotonic < model_times[0]


def test_motion_decode_binds_freshness_to_capture_start() -> None:
    frame = MotionFrame.from_sample(
        _sample(sequence=1, capture=104.0),
        _Identity(),
        capture_started_monotonic=100.0,
    )
    assert frame.capture_monotonic == pytest.approx(100.0)


def test_native_provider_rejects_a_sample_from_another_resolved_window() -> None:
    sample = Sample("FRESH", _sample().frame, 10.0, (0, 0, 256, 256), 1, "other-client")
    provider = NativeMotionProvider(lambda: sample, lambda: _Identity(), clock=lambda: 10.1)

    with pytest.raises(MotionError, match="identity"):
        provider.observe(1, deadline=11.0)


def test_native_provider_requires_publication_after_release_barrier() -> None:
    # Sequence 2 is the last frame published before release; a capture made
    # immediately after release can still expose it.  The provider must take
    # one such frame as the barrier and return the strictly later publication.
    samples = iter(
        (
            _sample(sequence=1, capture=10.0),
            _sample(sequence=2, capture=10.1, x=0.01),
            _sample(sequence=3, capture=10.2, x=0.2),
        )
    )
    deadlines: list[float | None] = []

    def capture(*, deadline: float | None = None) -> Sample:
        deadlines.append(deadline)
        return next(samples)

    clock_values = iter((10.0, 10.0, 10.05, 10.1, 10.1, 10.15, 10.2, 10.2, 10.25))
    provider = NativeMotionProvider(
        lambda: next(samples),
        lambda: _Identity(),
        capture_with_deadline=capture,
        clock=lambda: next(clock_values),
    )
    previous = provider.observe(1, deadline=11.0)
    after = provider.observe_after_release(1, previous=previous, deadline=11.0)
    assert after.sequence == 3
    assert after.x == pytest.approx(0.2)
    assert deadlines == [11.0, 11.0, 11.0]


def test_native_provider_rejects_disallowed_release_barrier_before_allowed_final() -> None:
    barrier = _sample(sequence=2, capture=10.1)
    barrier_value = barrier.frame.snapshot.value
    barrier_value["motion"]["native"]["ctm"]["state"] = "enabled"
    allowed_final = _sample(sequence=3, capture=10.2, x=0.2)
    samples = iter((barrier, allowed_final))
    clock_values = iter((10.05, 10.1, 10.15, 10.2, 10.25, 10.3))
    provider = NativeMotionProvider(
        lambda: next(samples),
        lambda: _Identity(),
        capture_with_deadline=lambda **_kwargs: next(samples),
        clock=lambda: next(clock_values),
    )
    previous = MotionFrame.from_sample(_sample(sequence=1, capture=10.0), _Identity())
    with pytest.raises(MotionError, match="capability"):
        provider.observe_after_release(1, previous=previous, deadline=11.0)


def test_daemon_observe_motion_gates_before_successor_pose_checks_and_clears_proofs() -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon.camera_mapping = object()
    daemon.movement_basis = object()
    daemon._motion_deadline = lambda: 11.0
    daemon._require_interaction = lambda _generation: 1
    blocked = _sample(sequence=2, capture=10.1, x=9.0)
    blocked_value = blocked.frame.snapshot.value
    blocked_value["motion"]["native"]["ctm"]["state"] = "unknown"
    blocked_value["motion"]["native"]["ctm"]["reason"] = "missing"
    daemon.motion_provider = NativeMotionProvider(lambda: blocked, lambda: _Identity(), clock=lambda: 10.2)
    with pytest.raises(DriverError, match="capability"):
        daemon._observe_motion(1, previous=MotionFrame.from_sample(_sample(), _Identity()))
    assert daemon.camera_mapping is None
    assert daemon.movement_basis is None


def test_daemon_observe_motion_clears_proofs_when_interaction_or_deadline_setup_fails() -> None:
    for failure in ("interaction", "deadline"):
        daemon = SessionDaemon.__new__(SessionDaemon)
        daemon.camera_mapping = object()
        daemon.movement_basis = object()
        if failure == "interaction":
            daemon._require_interaction = lambda _generation: (_ for _ in ()).throw(
                DriverError("generation revoked")
            )
            daemon._motion_deadline = lambda: 11.0
        else:
            daemon._require_interaction = lambda _generation: 1
            daemon._motion_deadline = lambda: (_ for _ in ()).throw(DriverError("deadline unavailable"))
        daemon.motion_provider = SimpleNamespace()
        with pytest.raises(DriverError):
            daemon._observe_motion(1)
        assert daemon.camera_mapping is None
        assert daemon.movement_basis is None


def test_waypoint_heading_is_local_and_bounded() -> None:
    frame = MotionFrame.from_sample(_sample(), _Identity())
    basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.1,
        facing_sign=1,
        handedness=1,
    )
    heading, distance = waypoint_heading_error(frame, 1.0, 0.0, basis)
    assert heading == pytest.approx(0.0)
    assert distance == pytest.approx(1.0)
    with pytest.raises(MotionError, match="bounded local distance"):
        waypoint_heading_error(frame, MAX_WAYPOINT_DISTANCE + 0.01, 0.0, basis)
    with pytest.raises(MotionError, match="measured movement basis"):
        waypoint_heading_error(frame, 1.0, 0.0, None)  # type: ignore[arg-type]


def test_waypoint_heading_uses_measured_forward_offset_and_rejects_stale_basis() -> None:
    frame = MotionFrame.from_sample(_sample(facing=1.0), _Identity())
    basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.25,
        forward_displacement=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.1,
        facing_sign=1,
        handedness=1,
    )
    heading, _distance = waypoint_heading_error(
        frame,
        math.cos(1.25),
        math.sin(1.25),
        basis,
    )
    assert heading == pytest.approx(0.0)
    stale = MovementBasis(
        identity_fingerprint="other",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.1,
        facing_sign=1,
        handedness=1,
    )
    with pytest.raises(MotionError, match="stale"):
        waypoint_heading_error(frame, 1.0, 0.0, stale)


def test_waypoint_camera_turn_budget_is_separate_from_translation_progress() -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.4,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.4,
        facing_sign=1,
        handedness=1,
    )
    frame = MotionFrame.from_sample(_sample(facing=math.pi / 2), _Identity())
    daemon._native_clock = lambda: 10.0
    daemon._require_interaction = lambda _generation: 1
    daemon._observe_motion = lambda *_args, **_kwargs: frame
    camera_turns: list[int] = []

    def camera_delta(pixels: int, *, generation: int, previous: MotionFrame | None = None) -> MotionFrame:
        del generation, previous
        camera_turns.append(pixels)
        return frame

    daemon.execute_camera_delta = camera_delta

    def observe_route(
        generation: int, target_x: float, target_y: float, *, frame: MotionFrame
    ) -> RouteEvidence:
        heading = (math.atan2(target_y - frame.y, target_x - frame.x) - frame.facing + math.pi) % (
            2.0 * math.pi
        ) - math.pi
        return RouteEvidence(
            "client-1",
            10.0,
            "world",
            "clear",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=heading,
            corridor_distance=math.hypot(target_x - frame.x, target_y - frame.y),
        )

    daemon._observe_route = observe_route
    with pytest.raises(DriverError, match="camera correction"):
        daemon.execute_waypoint(0.35, 0.0, generation=1)
    assert len(camera_turns) == MAX_WAYPOINT_CAMERA_TURNS


def test_waypoint_refuses_target_beyond_supported_distance_before_input() -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.4,
        pulse_seconds=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.4,
        strafe_pulse_seconds=0.1,
        facing_sign=1,
        handedness=1,
    )
    before = MotionFrame.from_sample(_sample(sequence=1, capture=10.0, speed=0.0), _Identity())
    after = MotionFrame.from_sample(_sample(sequence=2, capture=10.1, x=1.8, speed=0.0), _Identity())
    daemon._native_clock = lambda: 10.2
    daemon._require_interaction = lambda _generation: 1
    daemon._observe_motion = lambda *_args, **_kwargs: before
    daemon.driver = SimpleNamespace(run_motion_key_hold=lambda *args, **kwargs: None)
    pulses: list[float] = []

    def execute_pulse(role, duration, generation, frame, lease_generation, *, route=None):
        del role, generation, frame, lease_generation
        assert route is not None
        pulses.append(duration)
        return after

    daemon._execute_motion_key_with_frame = execute_pulse

    def observe_route(
        generation: int,
        target_x: float,
        target_y: float,
        *,
        frame: MotionFrame,
    ) -> RouteEvidence:
        distance = math.hypot(target_x - frame.x, target_y - frame.y)
        return RouteEvidence(
            "client-1",
            frame.capture_monotonic + 0.01,
            "world",
            "clear",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=math.atan2(target_y - frame.y, target_x - frame.x),
            corridor_distance=distance,
        )

    daemon._observe_route = observe_route
    with pytest.raises(DriverError, match="response-uncertainty envelope"):
        daemon.execute_waypoint(2.0, 0.0, generation=1)
    assert pulses == []


def test_waypoint_refuses_second_target_beyond_supported_distance_before_input() -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.7,
        pulse_seconds=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.7,
        strafe_pulse_seconds=0.1,
        facing_sign=1,
        handedness=1,
    )
    initial = MotionFrame.from_sample(_sample(sequence=1, capture=10.0, speed=0.0), _Identity())
    first_after = MotionFrame.from_sample(_sample(sequence=2, capture=10.1, x=1.6, speed=0.0), _Identity())
    second_after = MotionFrame.from_sample(_sample(sequence=3, capture=10.2, x=2.16, speed=0.0), _Identity())
    daemon._native_clock = lambda: 10.2
    daemon._require_interaction = lambda _generation: 1
    daemon._observe_motion = lambda *_args, **_kwargs: initial
    pulses: list[float] = []

    def execute_pulse(role, duration, generation, frame, lease_generation, *, route=None):
        del role, generation, frame, lease_generation
        assert route is not None
        pulses.append(duration)
        return first_after if len(pulses) == 1 else second_after

    daemon._execute_motion_key_with_frame = execute_pulse

    def observe_route(
        generation: int,
        target_x: float,
        target_y: float,
        *,
        frame: MotionFrame,
    ) -> RouteEvidence:
        distance = math.hypot(target_x - frame.x, target_y - frame.y)
        return RouteEvidence(
            "client-1",
            frame.capture_monotonic + 0.01,
            "world",
            "clear",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=math.atan2(target_y - frame.y, target_x - frame.x),
            corridor_distance=distance,
        )

    daemon._observe_route = observe_route
    with pytest.raises(DriverError, match="response-uncertainty envelope"):
        daemon.execute_waypoint(2.0, 0.0, generation=1)
    assert pulses == []


@pytest.mark.parametrize(
    ("target_distance", "feedback_factor"),
    ((0.5, 1.2), (0.9, 0.8), (1.0, 1.2), (1.1, 0.8)),
)
def test_waypoint_plans_minimum_pulse_aware_legs_across_target_band(
    target_distance: float,
    feedback_factor: float,
) -> None:
    """A robust one-pulse plan settles despite bounded response error."""

    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.7,
        pulse_seconds=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.7,
        strafe_pulse_seconds=0.1,
        facing_sign=1,
        handedness=1,
    )
    daemon._native_clock = lambda: 10.0
    daemon._require_interaction = lambda _generation: 1
    origin = MotionFrame.from_sample(_sample(sequence=1, capture=10.0), _Identity())
    daemon._observe_motion = lambda *_args, **_kwargs: origin
    pulses: list[float] = []
    route_calls: list[float] = []

    def observe_route(
        generation: int,
        target_x: float,
        target_y: float,
        *,
        frame: MotionFrame,
    ) -> RouteEvidence:
        distance = math.hypot(target_x - frame.x, target_y - frame.y)
        route_calls.append(distance)
        return RouteEvidence(
            "client-1",
            frame.capture_monotonic + 0.01,
            "world",
            "clear",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=0.0,
            corridor_distance=distance,
        )

    daemon._observe_route = observe_route

    def execute_pulse(
        role: KeyRole,
        duration: float,
        generation: int,
        frame: MotionFrame,
        lease_generation: int,
        *,
        route: RouteEvidence | None = None,
    ) -> MotionFrame:
        del role, generation, frame, lease_generation
        assert route is not None
        pulses.append(duration)
        return MotionFrame.from_sample(
            _sample(
                sequence=len(pulses) + 1,
                capture=10.0 + len(pulses) * 0.1,
                x=sum(7.0 * pulse * feedback_factor for pulse in pulses),
                y=0.0,
            ),
            _Identity(),
        )

    daemon._execute_motion_key_with_frame = execute_pulse
    result = daemon.execute_waypoint(target_distance, 0.0, generation=1)
    assert result.x == pytest.approx(target_distance, abs=0.28)
    assert len(pulses) == 1
    assert len(route_calls) == len(pulses)
    assert sum(7.0 * pulse * feedback_factor for pulse in pulses) <= MAX_WAYPOINT_DISTANCE


@pytest.mark.parametrize("target_bearing", (-0.19, 0.19))
@pytest.mark.parametrize("response_factor", (0.8, 1.2))
def test_execute_waypoint_admits_bearing_at_response_extremes(
    target_bearing: float,
    response_factor: float,
) -> None:
    """The actual waypoint loop settles for both signed bearings at response extremes."""

    daemon, _before, after, physical_calls, camera_calls = _actual_waypoint_daemon(
        target_bearing=target_bearing,
        response_factor=response_factor,
    )
    result = daemon.execute_waypoint(*daemon._waypoint_target, generation=1)

    assert result is after
    assert physical_calls == [(KeyRole.MOVE_FORWARD, pytest.approx(0.8 / 7.0))]
    assert camera_calls == []


@pytest.mark.parametrize("target_bearing", (-0.45, 0.45))
@pytest.mark.parametrize("response_factor", (0.8, 1.2))
def test_execute_waypoint_camera_residual_settles_at_response_extremes(
    target_bearing: float,
    response_factor: float,
) -> None:
    """A signed camera correction to a .19-radian residual still settles physically."""

    residual = math.copysign(0.19, target_bearing)
    corrected_facing = target_bearing - residual
    daemon, _before, after, physical_calls, camera_calls = _actual_waypoint_daemon(
        target_bearing=target_bearing,
        response_factor=response_factor,
        corrected_facing=corrected_facing,
    )
    result = daemon.execute_waypoint(*daemon._waypoint_target, generation=1)

    assert result is after
    assert physical_calls == [(KeyRole.MOVE_FORWARD, pytest.approx(0.8 / 7.0))]
    assert len(camera_calls) == 1
    assert camera_calls[0] * target_bearing > 0
    assert abs(camera_calls[0]) in {4, 5}


def test_waypoint_refuses_nonzero_bearing_at_response_extreme_before_input() -> None:
    """The translation gate proves the full two-dimensional endpoint error."""

    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.7,
        pulse_seconds=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.7,
        strafe_pulse_seconds=0.1,
        facing_sign=1,
        handedness=1,
    )
    before = MotionFrame.from_sample(_sample(sequence=1, capture=10.0, speed=0.0), _Identity())
    daemon._native_clock = lambda: 10.0
    daemon._require_interaction = lambda _generation: 1
    daemon._observe_motion = lambda *_args, **_kwargs: before
    physical_calls: list[float] = []

    def execute_pulse(*args, **kwargs):
        del kwargs
        physical_calls.append(float(args[1]))
        raise AssertionError("the endpoint gate admitted physical input")

    daemon._execute_motion_key_with_frame = execute_pulse
    daemon._observe_route = lambda *args, **kwargs: pytest.fail("route must not be admitted")
    heading = WAYPOINT_TRANSLATION_HEADING_TOLERANCE - 0.01
    with pytest.raises(DriverError, match="endpoint"):
        daemon.execute_waypoint(math.cos(heading), math.sin(heading), generation=1)
    assert physical_calls == []


def test_waypoint_refuses_camera_turn_when_worst_residual_cannot_fit() -> None:
    """Camera admission also proves the endpoint under its named residual."""

    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.7,
        pulse_seconds=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.7,
        strafe_pulse_seconds=0.1,
        facing_sign=1,
        handedness=1,
    )
    before = MotionFrame.from_sample(_sample(sequence=1, capture=10.0, speed=0.0), _Identity())
    daemon._native_clock = lambda: 10.0
    daemon._require_interaction = lambda _generation: 1
    daemon._observe_motion = lambda *_args, **_kwargs: before
    camera_calls: list[int] = []
    daemon.execute_camera_delta = lambda pixels, **kwargs: camera_calls.append(int(pixels)) or before
    daemon._observe_route = lambda *args, **kwargs: pytest.fail("route must not be admitted")
    heading = WAYPOINT_TRANSLATION_HEADING_TOLERANCE + 0.25
    with pytest.raises(DriverError, match="endpoint"):
        daemon.execute_waypoint(math.cos(heading), math.sin(heading), generation=1)
    assert camera_calls == []


def test_waypoint_refuses_short_minimum_pulse_gap_before_input() -> None:
    """Targets below the minimum-pulse lower bound are refused preflight."""

    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.7,
        pulse_seconds=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.7,
        strafe_pulse_seconds=0.1,
        facing_sign=1,
        handedness=1,
    )
    before = MotionFrame.from_sample(_sample(sequence=1, capture=10.0, speed=0.0), _Identity())
    daemon._native_clock = lambda: 10.0
    daemon._require_interaction = lambda _generation: 1
    daemon._observe_motion = lambda *_args, **_kwargs: before
    physical_calls: list[float] = []
    daemon._execute_motion_key_with_frame = lambda *args, **kwargs: physical_calls.append(float(args[1]))
    daemon.execute_camera_delta = lambda *args, **kwargs: pytest.fail("camera must not be admitted")
    with pytest.raises(DriverError, match="minimum pulse"):
        daemon.execute_waypoint(0.35, 0.0, generation=1)
    assert physical_calls == []


def test_waypoint_refuses_profile_ceiling_before_input() -> None:
    """A target whose nominal pulse exceeds the profile ceiling is preflighted."""

    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.13,
        pulse_seconds=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.13,
        strafe_pulse_seconds=0.1,
        facing_sign=1,
        handedness=1,
    )
    before = MotionFrame.from_sample(_sample(sequence=1, capture=10.0, speed=0.0), _Identity())
    daemon._native_clock = lambda: 10.0
    daemon._require_interaction = lambda _generation: 1
    daemon._observe_motion = lambda *_args, **_kwargs: before
    physical_calls: list[float] = []
    daemon._execute_motion_key_with_frame = lambda *args, **kwargs: physical_calls.append(float(args[1]))
    daemon.execute_camera_delta = lambda *args, **kwargs: pytest.fail("camera must not be admitted")
    with pytest.raises(DriverError, match="endpoint"):
        daemon.execute_waypoint(0.48, 0.0, generation=1)
    assert physical_calls == []


def test_waypoint_admits_minimum_pulse_with_bounded_confirmation_drift() -> None:
    """A near-lower-bound pulse remains safe with the allowed confirmation pose delta."""

    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.7,
        pulse_seconds=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.7,
        strafe_pulse_seconds=0.1,
        facing_sign=1,
        handedness=1,
    )
    before = MotionFrame.from_sample(_sample(sequence=1, capture=10.0, speed=0.0), _Identity())
    confirmed = MotionFrame.from_sample(
        _sample(sequence=2, capture=10.01, x=0.015, facing=0.015, speed=0.0), _Identity()
    )
    after = MotionFrame.from_sample(
        _sample(sequence=3, capture=10.2, x=0.47, facing=0.02, speed=0.0), _Identity()
    )
    daemon._native_clock = lambda: 10.2
    daemon._require_interaction = lambda _generation: 1

    def observe_motion(
        _generation: int, previous: MotionFrame | None = None, *, after_release: bool = False, **_kwargs
    ):
        if after_release:
            return after
        return confirmed if previous is not None else before

    daemon._observe_motion = observe_motion
    physical_calls: list[float] = []
    daemon.driver = SimpleNamespace(
        run_motion_key_hold=lambda _role, duration, *_args, **_kwargs: physical_calls.append(duration)
    )

    def observe_route(
        generation: int,
        target_x: float,
        target_y: float,
        *,
        frame: MotionFrame,
    ) -> RouteEvidence:
        distance = math.hypot(target_x - frame.x, target_y - frame.y)
        return RouteEvidence(
            "client-1",
            frame.capture_monotonic + 0.01,
            "world",
            "clear",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=math.atan2(target_y - frame.y, target_x - frame.x),
            corridor_distance=distance,
        )

    daemon._observe_route = observe_route
    result = daemon.execute_waypoint(0.42, 0.0, generation=1)

    assert result is after
    assert physical_calls == [pytest.approx(0.08)]


def test_waypoint_rejects_diagonal_confirmation_position_ball_at_endpoint_limit() -> None:
    """A perpendicular confirmation offset cannot be reduced to radial target endpoints."""

    daemon = SessionDaemon.__new__(SessionDaemon)
    profile = MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)
    with pytest.raises(DriverError, match="endpoint"):
        daemon._plan_waypoint_pulse(
            0.44,
            7.0,
            0.08,
            profile,
            0.0,
            0.28,
            0.20,
        )


def test_waypoint_refuses_near_cap_without_a_guaranteed_response_plan() -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.7,
        pulse_seconds=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.7,
        strafe_pulse_seconds=0.1,
        facing_sign=1,
        handedness=1,
    )
    camera_mapping = daemon.camera_mapping
    movement_basis = daemon.movement_basis
    before = MotionFrame.from_sample(_sample(sequence=1, capture=10.0), _Identity())
    daemon._native_clock = lambda: 10.0
    daemon._require_interaction = lambda _generation: 1
    daemon._observe_motion = lambda *_args, **_kwargs: before
    physical_calls: list[float] = []
    daemon._execute_motion_key_with_frame = lambda *args, **kwargs: physical_calls.append(float(args[1]))
    camera_calls: list[int] = []
    daemon.execute_camera_delta = lambda pixels, **kwargs: camera_calls.append(int(pixels))

    with pytest.raises(DriverError, match="response-uncertainty envelope"):
        daemon.execute_waypoint(0.0, 1.68, generation=1)
    assert physical_calls == []
    assert camera_calls == []
    assert daemon.camera_mapping is camera_mapping
    assert daemon.movement_basis is movement_basis


def test_travel_envelope_arithmetic_covers_alternating_response_error() -> None:
    """Check the scalar envelope helper; executor coverage is tested separately."""

    daemon = SessionDaemon.__new__(SessionDaemon)
    nominal_distances = (0.56, 0.56)
    response_factors = (1.0 - TRAVEL_UNCERTAINTY_FRACTION, 1.0 + TRAVEL_UNCERTAINTY_FRACTION)
    actual_distances = tuple(
        distance * factor for distance, factor in zip(nominal_distances, response_factors, strict=True)
    )
    envelopes = tuple(daemon._travel_envelope(distance) for distance in nominal_distances)

    assert all(actual <= envelope for actual, envelope in zip(actual_distances, envelopes, strict=True))
    assert sum(actual_distances) <= MAX_WAYPOINT_DISTANCE
    assert sum(envelopes) <= MAX_WAYPOINT_DISTANCE


def test_waypoint_rejects_reflected_handedness_before_runtime_input() -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.7,
        pulse_seconds=0.1,
        strafe_heading_offset=math.pi / 2,
        strafe_displacement=0.7,
        strafe_pulse_seconds=0.1,
        facing_sign=1,
        handedness=-1,
    )
    daemon.movement_basis = basis
    with pytest.raises(DriverError, match="handed"):
        daemon._require_supported_route_handedness(basis)


def test_waypoint_counts_first_three_ineffective_pulses_and_stops(monkeypatch) -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.7,
        pulse_seconds=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.7,
        strafe_pulse_seconds=0.1,
        facing_sign=1,
        handedness=1,
    )
    initial = MotionFrame.from_sample(_sample(sequence=1, capture=10.0, speed=0.0), _Identity())
    # Every endpoint remains exactly one unit from the target, while each
    # pulse has a positive forward component and a bounded cumulative length.
    endpoints = [
        (0.3, math.sqrt(1.0 - 0.7**2)),
        (0.4, math.sqrt(1.0 - 0.6**2)),
        (0.5, math.sqrt(1.0 - 0.5**2)),
        (0.6, math.sqrt(1.0 - 0.4**2)),
    ]
    after_frames = [
        MotionFrame.from_sample(
            _sample(sequence=index + 2, capture=10.1 + index * 0.1, x=x, y=y, speed=0.0), _Identity()
        )
        for index, (x, y) in enumerate(endpoints)
    ]
    daemon._native_clock = lambda: 10.2
    daemon._require_interaction = lambda _generation: 1
    daemon._observe_motion = lambda *_args, **_kwargs: initial
    pulses: list[float] = []

    def execute_pulse(role, duration, generation, frame, lease_generation, *, route=None):
        del role, generation, frame, lease_generation
        assert route is not None
        pulses.append(duration)
        return after_frames[len(pulses) - 1]

    daemon._execute_motion_key_with_frame = execute_pulse
    monkeypatch.setattr(daemon_module, "waypoint_heading_error", lambda *_args: (0.0, 0.42))

    def observe_route(
        generation: int,
        target_x: float,
        target_y: float,
        *,
        frame: MotionFrame,
    ) -> RouteEvidence:
        distance = math.hypot(target_x - frame.x, target_y - frame.y)
        heading = math.atan2(target_y - frame.y, target_x - frame.x)
        return RouteEvidence(
            "client-1",
            frame.capture_monotonic + 0.01,
            "world",
            "clear",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=heading,
            corridor_distance=distance,
        )

    daemon._observe_route = observe_route
    with pytest.raises(DriverError, match="no measurable progress"):
        daemon.execute_waypoint(1.0, 0.0, generation=1)
    assert len(pulses) == 3


@pytest.mark.parametrize(
    ("after_x", "message"),
    ((0.0, "no measurable progress"), (-0.1, "wrong direction")),
)
def test_motion_key_rejects_missing_or_wrong_direction_feedback(after_x: float, message: str) -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.1,
        facing_sign=-1,
        handedness=-1,
    )
    before = MotionFrame.from_sample(_sample(sequence=1, capture=10.0, speed=0.0), _Identity())
    after = MotionFrame.from_sample(_sample(sequence=2, capture=10.1, x=after_x, speed=0.0), _Identity())
    daemon._native_clock = lambda: 10.2
    daemon._require_interaction = lambda _generation: 1
    daemon._observe_motion = lambda *_args, **kwargs: after if kwargs.get("after_release") else before
    daemon.driver = SimpleNamespace(
        resolve_identity=lambda **kwargs: _Identity(),
        run_motion_key_hold=lambda *args, **kwargs: None,
    )

    def observe_route(
        generation: int, target_x: float, target_y: float, *, frame: MotionFrame
    ) -> RouteEvidence:
        heading = (math.atan2(target_y - frame.y, target_x - frame.x) - frame.facing + math.pi) % (
            2.0 * math.pi
        ) - math.pi
        return RouteEvidence(
            "client-1",
            10.05,
            "world",
            "clear",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=heading,
            corridor_distance=math.hypot(target_x - frame.x, target_y - frame.y),
        )

    daemon._observe_route = observe_route
    with pytest.raises(DriverError, match=message):
        daemon._execute_motion_key_with_frame(
            KeyRole.MOVE_FORWARD,
            0.1,
            1,
            before,
            1,
        )


def test_daemon_shutdown_releases_driver_when_model_cleanup_fails() -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._shutdown_event = threading.Event()
    daemon._calibration_thread = None
    daemon.controller = SimpleNamespace(
        journal=SimpleNamespace(read=lambda: {"calibrationEvidence": {}}),
    )
    daemon._cleanup_native_owned_captures = lambda keep: None

    class FailingModel:
        def shutdown(self) -> None:
            raise RuntimeError("retained model owner")

    closed: list[str] = []
    daemon.model = FailingModel()
    daemon.driver = SimpleNamespace(close=lambda: closed.append("closed"))
    with pytest.raises(RuntimeError, match="shutdown"):
        daemon.request_shutdown()
    assert closed == ["closed"]


def _manual_motion_daemon(after_x: float) -> tuple[SessionDaemon, list[float], list[tuple[object, ...]]]:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.movement_basis = MovementBasis(
        identity_fingerprint="client-1",
        boot="boot-1",
        generation=1,
        capture_id="movement:boot-1:1:2",
        before_sequence=1,
        after_sequence=2,
        forward_heading_offset=0.0,
        forward_displacement=0.7,
        pulse_seconds=0.1,
        strafe_heading_offset=-math.pi / 2,
        strafe_displacement=0.7,
        strafe_pulse_seconds=0.1,
        facing_sign=1,
        handedness=1,
    )
    before = MotionFrame.from_sample(_sample(sequence=1, capture=10.0, speed=0.0), _Identity())
    after = MotionFrame.from_sample(_sample(sequence=2, capture=10.1, x=after_x, speed=0.0), _Identity())
    daemon._native_clock = lambda: 10.2
    daemon._require_interaction = lambda _generation: 1
    daemon._observe_motion = lambda *_args, **kwargs: after if kwargs.get("after_release") else before
    route_distances: list[float] = []
    physical_calls: list[tuple[object, ...]] = []

    def observe_route(
        generation: int,
        target_x: float,
        target_y: float,
        *,
        frame: MotionFrame,
    ) -> RouteEvidence:
        heading = (math.atan2(target_y - frame.y, target_x - frame.x) - frame.facing + math.pi) % (
            2.0 * math.pi
        ) - math.pi
        distance = math.hypot(target_x - frame.x, target_y - frame.y)
        route_distances.append(distance)
        return RouteEvidence(
            "client-1",
            10.05,
            "world",
            "clear",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=heading,
            corridor_distance=distance,
        )

    daemon._observe_route = observe_route
    daemon.driver = SimpleNamespace(
        run_motion_key_hold=lambda *args, **kwargs: physical_calls.append(args),
    )
    return daemon, route_distances, physical_calls


def test_motion_key_rejects_measured_speed_pulse_before_physical_input() -> None:
    daemon, route_distances, physical_calls = _manual_motion_daemon(after_x=0.56)

    with pytest.raises(DriverError, match="bounded travel envelope"):
        daemon._execute_motion_key_with_frame(KeyRole.MOVE_FORWARD, 0.35, 1, daemon._observe_motion(1), 1)

    assert route_distances == []
    assert physical_calls == []


def test_motion_key_proves_measured_travel_and_rejects_oversized_feedback() -> None:
    normal, route_distances, physical_calls = _manual_motion_daemon(after_x=0.56)
    before = normal._observe_motion(1)
    observed = normal._execute_motion_key_with_frame(KeyRole.MOVE_FORWARD, 0.08, 1, before, 1)
    assert observed.x == pytest.approx(0.56)
    assert route_distances == pytest.approx([0.7 / 0.1 * 0.08 * (1.0 + TRAVEL_UNCERTAINTY_FRACTION)])
    assert len(physical_calls) == 1

    oversized, _route_distances, oversized_calls = _manual_motion_daemon(after_x=0.8)
    with pytest.raises(DriverError, match="exceeded its proved travel envelope"):
        oversized._execute_motion_key_with_frame(
            KeyRole.MOVE_FORWARD,
            0.08,
            1,
            oversized._observe_motion(1),
            1,
        )
    assert len(oversized_calls) == 1


def test_movement_calibration_measures_reflected_nonzero_heading_mapping() -> None:
    """Infer φ=-θ+β from two forward headings and an independent strafe."""

    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.movement_basis = None
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon._native_clock = lambda: 10.2
    daemon._require_interaction = lambda generation: 1
    beta = 0.8
    first_facing = 0.4
    second_facing = 1.2
    first_world = -first_facing + beta
    second_world = -second_facing + beta
    first_dx, first_dy = 0.2 * math.cos(first_world), 0.2 * math.sin(first_world)
    second_dx, second_dy = 0.2 * math.cos(second_world), 0.2 * math.sin(second_world)
    left_world = second_world + math.pi / 2
    strafe_dx, strafe_dy = 0.2 * math.cos(left_world), 0.2 * math.sin(left_world)
    frames = [
        MotionFrame.from_sample(
            _sample(sequence=1, capture=10.0, facing=first_facing, speed=0.0), _Identity()
        ),
        MotionFrame.from_sample(
            _sample(sequence=2, capture=10.1, facing=first_facing, speed=0.0), _Identity()
        ),
        MotionFrame.from_sample(
            _sample(sequence=3, capture=10.2, facing=first_facing, speed=0.0),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(sequence=4, capture=10.3, facing=first_facing, x=first_dx, y=first_dy, speed=0.0),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=5,
                capture=10.4,
                facing=second_facing,
                x=first_dx,
                y=first_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=6,
                capture=10.5,
                facing=second_facing,
                x=first_dx,
                y=first_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=7,
                capture=10.6,
                facing=second_facing,
                x=first_dx + second_dx,
                y=first_dy + second_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=8,
                capture=10.7,
                facing=second_facing,
                x=first_dx + second_dx,
                y=first_dy + second_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=9,
                capture=10.8,
                facing=second_facing,
                x=first_dx + second_dx,
                y=first_dy + second_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=10,
                capture=10.9,
                facing=second_facing,
                x=first_dx + second_dx + strafe_dx,
                y=first_dy + second_dy + strafe_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        # Backward probe: opposite the second forward heading.
        MotionFrame.from_sample(
            _sample(
                sequence=11,
                capture=11.0,
                facing=second_facing,
                x=first_dx + second_dx + strafe_dx,
                y=first_dy + second_dy + strafe_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=12,
                capture=11.1,
                facing=second_facing,
                x=first_dx + second_dx + strafe_dx,
                y=first_dy + second_dy + strafe_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=13,
                capture=11.2,
                facing=second_facing,
                x=first_dx + strafe_dx,
                y=first_dy + strafe_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        # Right strafe probe: opposite the measured left vector.
        MotionFrame.from_sample(
            _sample(
                sequence=14,
                capture=11.3,
                facing=second_facing,
                x=first_dx + strafe_dx,
                y=first_dy + strafe_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=15,
                capture=11.4,
                facing=second_facing,
                x=first_dx + strafe_dx,
                y=first_dy + strafe_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=16,
                capture=11.5,
                facing=second_facing,
                x=first_dx,
                y=first_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
    ]

    def observe(
        generation: int,
        previous: MotionFrame | None = None,
        *,
        not_before: float | None = None,
        after_release: bool = False,
    ) -> MotionFrame:
        del generation, not_before, after_release
        frame = frames.pop(0)
        frame.require_safe_successor(previous, now=frame.capture_monotonic + 0.01)
        return frame

    daemon._observe_motion = observe
    route_calls: list[tuple[float, float]] = []

    def observe_route(
        generation: int,
        target_x: float | None = None,
        target_y: float | None = None,
        *,
        frame: MotionFrame | None = None,
        corridor_heading: float | None = None,
        corridor_distance: float | None = None,
    ) -> RouteEvidence:
        del generation, target_x, target_y
        assert frame is not None
        assert corridor_heading is not None
        assert corridor_distance is not None
        route_calls.append((corridor_heading, corridor_distance))
        return RouteEvidence(
            "client-1",
            frame.capture_monotonic + 0.01,
            "world",
            "clear",
            True,
            True,
            generation=1,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=1,
            zone="Elwynn\x1fGoldshire",
            screenshot_digest="route-digest",
            corridor_heading=corridor_heading,
            corridor_distance=corridor_distance,
        )

    daemon._observe_route = observe_route

    class _Driver:
        def resolve_identity(
            self,
            *,
            require_foreground: bool = False,
            deadline_monotonic: float | None = None,
        ) -> _Identity:
            assert require_foreground
            assert deadline_monotonic is not None
            return _Identity()

        def run_motion_key_hold(
            self,
            role,
            duration,
            frame,
            *,
            generation,
            deadline_monotonic: float | None = None,
        ) -> None:
            assert role.value in {"move_forward", "strafe_left", "move_backward", "strafe_right"}
            assert duration == pytest.approx(0.20)
            assert frame.sequence in {3, 6, 8, 9, 12, 15}
            assert generation == 1
            if frame.sequence in {3, 6, 9, 12, 15}:
                assert deadline_monotonic is not None

    daemon.driver = _Driver()
    daemon.execute_camera_delta = lambda _pixels, *, generation, previous=None: frames.pop(0)
    basis = daemon.calibrate_movement_basis(0.20, generation=1)
    assert basis.forward_heading_offset == pytest.approx(beta)
    assert basis.facing_sign == -1
    assert basis.forward_displacement == pytest.approx(0.2)
    assert basis.strafe_heading_offset == pytest.approx(0.0)
    assert basis.handedness == 1
    assert [heading for heading, _distance in route_calls] == pytest.approx(
        [0.0, 0.0, math.pi / 2, math.pi, -math.pi / 2]
    )
    assert daemon.movement_basis is basis

    # A fresh, nonzero heading uses the measured reflected convention.  The
    # native target error and the physical left pulse therefore agree with
    # the measured world vectors instead of raw facing axes.
    new_facing = 1.7
    new_origin = (0.7, -0.4)
    new_world_forward = -new_facing + beta
    forward_target = (
        new_origin[0] + math.cos(new_world_forward),
        new_origin[1] + math.sin(new_world_forward),
    )
    left_target_heading = new_world_forward + math.pi / 2
    left_target = (
        new_origin[0] + math.cos(left_target_heading),
        new_origin[1] + math.sin(left_target_heading),
    )
    forward_error, _ = waypoint_heading_error(
        MotionFrame.from_sample(
            _sample(sequence=8, capture=10.8, facing=new_facing, x=new_origin[0], y=new_origin[1]),
            _Identity(),
        ),
        *forward_target,
        basis,
    )
    left_error, _ = waypoint_heading_error(
        MotionFrame.from_sample(
            _sample(sequence=8, capture=10.8, facing=new_facing, x=new_origin[0], y=new_origin[1]),
            _Identity(),
        ),
        *left_target,
        basis,
    )
    assert forward_error == pytest.approx(0.0)
    assert left_error == pytest.approx(-math.pi / 2)

    new_frame = MotionFrame.from_sample(
        _sample(sequence=8, capture=10.8, facing=new_facing, x=new_origin[0], y=new_origin[1]),
        _Identity(),
    )
    left_dx, left_dy = 0.2 * math.cos(left_target_heading), 0.2 * math.sin(left_target_heading)
    new_after = MotionFrame.from_sample(
        _sample(
            sequence=9,
            capture=10.9,
            facing=new_facing,
            x=new_origin[0] + left_dx,
            y=new_origin[1] + left_dy,
            speed=0.0,
        ),
        _Identity(),
    )

    route_target_headings: list[float] = []

    def execute_route(
        generation: int,
        target_x: float,
        target_y: float,
        *,
        frame: MotionFrame,
    ) -> RouteEvidence:
        assert generation == 1
        route_target_headings.append(math.atan2(target_y - frame.y, target_x - frame.x))
        heading = math.atan2(target_y - frame.y, target_x - frame.x) - (-frame.facing + beta)
        heading = (heading + math.pi) % (2.0 * math.pi) - math.pi
        return RouteEvidence(
            "client-1",
            10.85,
            "world",
            "clear",
            True,
            True,
            generation=1,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=heading,
            corridor_distance=math.hypot(target_x - frame.x, target_y - frame.y),
        )

    daemon._observe_route = execute_route
    daemon._observe_motion = lambda *_args, **kwargs: new_after if kwargs.get("after_release") else new_frame
    daemon._native_clock = lambda: 10.95
    observed = daemon._execute_motion_key_with_frame(KeyRole.STRAFE_LEFT, 0.20, 1, new_frame, 1)
    assert observed.sequence == new_after.sequence
    actual_heading = math.atan2(observed.y - new_frame.y, observed.x - new_frame.x)
    assert actual_heading == pytest.approx(left_target_heading)
    assert route_target_headings == pytest.approx([left_target_heading])


def test_movement_calibration_rejects_sideways_backward_role() -> None:
    """A backward binding that produces lateral travel must never seal a basis."""

    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.movement_basis = None
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
        boot="boot-1",
    )
    daemon._native_clock = lambda: 10.2
    daemon._require_interaction = lambda _generation: 1

    def add_position(position: tuple[float, float], *, sequence: int, capture: float, facing: float) -> None:
        frames.append(
            MotionFrame.from_sample(
                _sample(
                    sequence=sequence,
                    capture=capture,
                    facing=facing,
                    x=position[0],
                    y=position[1],
                    speed=0.0,
                ),
                _Identity(),
            )
        )

    # The fitted convention is facing -> world-forward with beta=0.  The
    # backward probe below deliberately moves along the right axis; the
    # later right probe remains valid so this test isolates the role check.
    facing = 0.8
    forward = (0.2, 0.0)
    second = (forward[0] + 0.2 * math.cos(facing), forward[1] + 0.2 * math.sin(facing))
    left_heading = facing + math.pi / 2
    left = (second[0] + 0.2 * math.cos(left_heading), second[1] + 0.2 * math.sin(left_heading))
    right_heading = facing - math.pi / 2
    sideways_backward = (
        left[0] + 0.2 * math.cos(right_heading),
        left[1] + 0.2 * math.sin(right_heading),
    )
    right = (
        sideways_backward[0] + 0.2 * math.cos(right_heading),
        sideways_backward[1] + 0.2 * math.sin(right_heading),
    )

    frames: list[MotionFrame] = []
    add_position((0.0, 0.0), sequence=1, capture=10.0, facing=0.0)
    add_position((0.0, 0.0), sequence=2, capture=10.1, facing=0.0)
    add_position((0.0, 0.0), sequence=3, capture=10.2, facing=0.0)
    add_position(forward, sequence=4, capture=10.3, facing=0.0)
    add_position(forward, sequence=5, capture=10.4, facing=facing)
    add_position(forward, sequence=6, capture=10.5, facing=facing)
    add_position(second, sequence=7, capture=10.6, facing=facing)
    add_position(second, sequence=8, capture=10.7, facing=facing)
    add_position(second, sequence=9, capture=10.8, facing=facing)
    add_position(left, sequence=10, capture=10.9, facing=facing)
    add_position(left, sequence=11, capture=11.0, facing=facing)
    add_position(left, sequence=12, capture=11.1, facing=facing)
    add_position(sideways_backward, sequence=13, capture=11.2, facing=facing)
    add_position(sideways_backward, sequence=14, capture=11.3, facing=facing)
    add_position(sideways_backward, sequence=15, capture=11.4, facing=facing)
    add_position(right, sequence=16, capture=11.5, facing=facing)

    def observe(
        generation: int,
        previous: MotionFrame | None = None,
        *,
        not_before: float | None = None,
        after_release: bool = False,
    ) -> MotionFrame:
        del generation, not_before, after_release
        frame = frames.pop(0)
        frame.require_safe_successor(previous, now=frame.capture_monotonic + 0.01)
        return frame

    daemon._observe_motion = observe

    def observe_route(
        generation: int,
        target_x: float | None = None,
        target_y: float | None = None,
        *,
        frame: MotionFrame | None = None,
        corridor_heading: float | None = None,
        corridor_distance: float | None = None,
    ) -> RouteEvidence:
        del target_x, target_y
        assert frame is not None and corridor_heading is not None and corridor_distance is not None
        return RouteEvidence(
            "client-1",
            frame.capture_monotonic + 0.01,
            "world",
            "clear",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=corridor_heading,
            corridor_distance=corridor_distance,
        )

    daemon._observe_route = observe_route
    daemon.driver = SimpleNamespace(
        resolve_identity=lambda **kwargs: _Identity(),
        run_motion_key_hold=lambda *args, **kwargs: None,
    )
    daemon.execute_camera_delta = lambda _pixels, *, generation, previous=None: frames.pop(0)

    with pytest.raises(DriverError, match="movement backward probe moved in the wrong direction"):
        daemon.calibrate_movement_basis(0.03, generation=1)


def test_movement_calibration_admits_no_probe_after_cumulative_budget() -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.movement_basis = None
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon._native_clock = lambda: 10.2
    daemon._require_interaction = lambda _generation: 1
    second_dx, second_dy = 0.9 * math.cos(0.5), 0.9 * math.sin(0.5)
    frames = [
        MotionFrame.from_sample(_sample(sequence=1, capture=10.0, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=2, capture=10.1, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=3, capture=10.2, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=4, capture=10.3, x=0.9, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=5, capture=10.4, facing=0.5, x=0.9, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=6, capture=10.5, facing=0.5, x=0.9, speed=0.0), _Identity()),
        MotionFrame.from_sample(
            _sample(
                sequence=7,
                capture=10.6,
                facing=0.5,
                x=0.9 + second_dx,
                y=second_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=8,
                capture=10.7,
                facing=0.5,
                x=0.9 + second_dx,
                y=second_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=9,
                capture=10.8,
                facing=0.5,
                x=0.9 + second_dx,
                y=second_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=10,
                capture=10.9,
                facing=0.5,
                x=0.9 + second_dx,
                y=second_dy + 0.9,
                speed=0.0,
            ),
            _Identity(),
        ),
    ]

    def observe(
        generation: int,
        previous: MotionFrame | None = None,
        *,
        not_before: float | None = None,
        after_release: bool = False,
    ) -> MotionFrame:
        del generation, not_before, after_release
        frame = frames.pop(0)
        frame.require_safe_successor(previous, now=frame.capture_monotonic + 0.01)
        return frame

    daemon._observe_motion = observe
    route_distances: list[float] = []

    def observe_route(
        generation: int,
        target_x: float | None = None,
        target_y: float | None = None,
        *,
        frame: MotionFrame | None = None,
        corridor_heading: float | None = None,
        corridor_distance: float | None = None,
    ) -> RouteEvidence:
        del target_x, target_y
        assert frame is not None
        assert corridor_heading is not None and corridor_distance is not None
        route_distances.append(corridor_distance)
        return RouteEvidence(
            "client-1",
            frame.capture_monotonic + 0.01,
            "world",
            "clear",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=corridor_heading,
            corridor_distance=corridor_distance,
        )

    daemon._observe_route = observe_route
    physical_roles: list[KeyRole] = []

    class _Driver:
        def resolve_identity(self, **kwargs: object) -> _Identity:
            return _Identity()

        def run_motion_key_hold(self, role: KeyRole, *args: object, **kwargs: object) -> None:
            del args, kwargs
            physical_roles.append(role)

    daemon.driver = _Driver()
    daemon.execute_camera_delta = lambda _pixels, *, generation, previous=None: frames.pop(0)

    with pytest.raises(DriverError, match="cumulative local"):
        daemon.calibrate_movement_basis(0.20, generation=1)

    assert physical_roles == [KeyRole.MOVE_FORWARD, KeyRole.MOVE_FORWARD]
    assert route_distances == pytest.approx([MAX_BASIS_DISPLACEMENT] * 2)


def test_movement_calibration_rejects_inconsistent_repeated_forward_speed() -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.movement_basis = None
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
        boot="boot-1",
    )
    daemon._native_clock = lambda: 10.2
    daemon._require_interaction = lambda _generation: 1
    second_dx, second_dy = math.cos(0.5), math.sin(0.5)
    frames = [
        MotionFrame.from_sample(_sample(sequence=1, capture=10.0, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=2, capture=10.1, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=3, capture=10.2, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=4, capture=10.3, x=0.2, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=5, capture=10.4, facing=0.5, x=0.2, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=6, capture=10.5, facing=0.5, x=0.2, speed=0.0), _Identity()),
        MotionFrame.from_sample(
            _sample(
                sequence=7,
                capture=10.6,
                facing=0.5,
                x=0.2 + second_dx,
                y=second_dy,
                speed=0.0,
            ),
            _Identity(),
        ),
    ]

    def observe(
        generation: int,
        previous: MotionFrame | None = None,
        *,
        not_before: float | None = None,
        after_release: bool = False,
    ) -> MotionFrame:
        del generation, not_before, after_release
        frame = frames.pop(0)
        frame.require_safe_successor(previous, now=frame.capture_monotonic + 0.01)
        return frame

    daemon._observe_motion = observe

    def observe_route(
        generation: int,
        target_x: float | None = None,
        target_y: float | None = None,
        *,
        frame: MotionFrame | None = None,
        corridor_heading: float | None = None,
        corridor_distance: float | None = None,
    ) -> RouteEvidence:
        del target_x, target_y
        assert frame is not None and corridor_heading is not None and corridor_distance is not None
        return RouteEvidence(
            "client-1",
            frame.capture_monotonic + 0.01,
            "world",
            "forward-repeat",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=corridor_heading,
            corridor_distance=corridor_distance,
        )

    daemon._observe_route = observe_route
    daemon.driver = SimpleNamespace(
        resolve_identity=lambda **kwargs: _Identity(),
        run_motion_key_hold=lambda *args, **kwargs: None,
    )
    daemon.execute_camera_delta = lambda _pixels, *, generation, previous=None: frames.pop(0)

    with pytest.raises(DriverError, match="repeated forward probes were inconsistent"):
        daemon.calibrate_movement_basis(0.03, generation=1)


def test_default_movement_calibration_completes_five_role_probes_at_measured_speed() -> None:
    """The technical .03 s calibration pulse leaves room for all role probes."""

    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.movement_basis = None
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
        boot="boot-1",
    )
    daemon._native_clock = lambda: 10.2
    daemon._require_interaction = lambda _generation: 1
    pulse = DEFAULT_MOVEMENT_CALIBRATION_PULSE_SECONDS
    assert pulse == MIN_MOVEMENT_CALIBRATION_PULSE_SECONDS == pytest.approx(0.03)
    second_dx, second_dy = 0.21 * math.cos(0.5), 0.21 * math.sin(0.5)
    left_heading = 0.5 + math.pi / 2
    first_position = (0.21, 0.0)
    second_position = (0.21 + second_dx, second_dy)
    strafe_position = (
        second_position[0] + 0.21 * math.cos(left_heading),
        second_position[1] + 0.21 * math.sin(left_heading),
    )
    backward_position = (strafe_position[0] - second_dx, strafe_position[1] - second_dy)
    right_position = (
        backward_position[0] - 0.21 * math.cos(left_heading),
        backward_position[1] - 0.21 * math.sin(left_heading),
    )
    frames = [
        MotionFrame.from_sample(_sample(sequence=1, capture=10.0, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=2, capture=10.1, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=3, capture=10.2, speed=0.0), _Identity()),
        MotionFrame.from_sample(
            _sample(sequence=4, capture=10.3, x=first_position[0], y=first_position[1], speed=0.0),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=5, capture=10.4, facing=0.5, x=first_position[0], y=first_position[1], speed=0.0
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=6, capture=10.5, facing=0.5, x=first_position[0], y=first_position[1], speed=0.0
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=7, capture=10.6, facing=0.5, x=second_position[0], y=second_position[1], speed=0.0
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=8, capture=10.7, facing=0.5, x=second_position[0], y=second_position[1], speed=0.0
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=9, capture=10.8, facing=0.5, x=second_position[0], y=second_position[1], speed=0.0
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=10, capture=10.9, facing=0.5, x=strafe_position[0], y=strafe_position[1], speed=0.0
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=11, capture=11.0, facing=0.5, x=strafe_position[0], y=strafe_position[1], speed=0.0
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=12,
                capture=11.1,
                facing=0.5,
                x=strafe_position[0],
                y=strafe_position[1],
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=13,
                capture=11.2,
                facing=0.5,
                x=backward_position[0],
                y=backward_position[1],
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=14,
                capture=11.3,
                facing=0.5,
                x=backward_position[0],
                y=backward_position[1],
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=15,
                capture=11.4,
                facing=0.5,
                x=backward_position[0],
                y=backward_position[1],
                speed=0.0,
            ),
            _Identity(),
        ),
        MotionFrame.from_sample(
            _sample(
                sequence=16,
                capture=11.5,
                facing=0.5,
                x=right_position[0],
                y=right_position[1],
                speed=0.0,
            ),
            _Identity(),
        ),
    ]

    def observe(
        generation: int,
        previous: MotionFrame | None = None,
        *,
        not_before: float | None = None,
        after_release: bool = False,
    ) -> MotionFrame:
        del generation, not_before, after_release
        frame = frames.pop(0)
        frame.require_safe_successor(previous, now=frame.capture_monotonic + 0.01)
        return frame

    daemon._observe_motion = observe
    route_distances: list[float] = []

    def observe_route(
        generation: int,
        target_x: float | None = None,
        target_y: float | None = None,
        *,
        frame: MotionFrame | None = None,
        corridor_heading: float | None = None,
        corridor_distance: float | None = None,
    ) -> RouteEvidence:
        del target_x, target_y
        assert frame is not None
        assert corridor_heading is not None and corridor_distance is not None
        route_distances.append(corridor_distance)
        return RouteEvidence(
            "client-1",
            frame.capture_monotonic + 0.01,
            "world",
            "clear",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=corridor_heading,
            corridor_distance=corridor_distance,
        )

    daemon._observe_route = observe_route
    physical_roles: list[tuple[KeyRole, float]] = []

    class _Driver:
        def resolve_identity(self, **kwargs: object) -> _Identity:
            return _Identity()

        def run_motion_key_hold(
            self, role: KeyRole, duration: float, *args: object, **kwargs: object
        ) -> None:
            del args, kwargs
            physical_roles.append((role, duration))

    daemon.driver = _Driver()
    daemon.execute_camera_delta = lambda _pixels, *, generation, previous=None: frames.pop(0)

    basis = daemon.calibrate_movement_basis(generation=1)
    assert basis.forward_displacement / basis.pulse_seconds == pytest.approx(7.0)
    assert basis.pulse_seconds == pytest.approx(pulse)
    assert basis.strafe_pulse_seconds == pytest.approx(pulse)
    assert basis.forward_displacement == pytest.approx(0.21)
    assert basis.strafe_displacement == pytest.approx(0.21)
    assert basis.backward_displacement == pytest.approx(0.21)
    assert basis.strafe_right_displacement == pytest.approx(0.21)
    assert len(physical_roles) == 5
    assert all(duration == pytest.approx(pulse) for _role, duration in physical_roles)
    assert sum((0.21, 0.21, 0.21, 0.21, 0.21)) < MAX_WAYPOINT_DISTANCE
    assert route_distances == pytest.approx([MAX_BASIS_DISPLACEMENT] * 5)


def test_movement_calibration_rejects_degenerate_heading_probe() -> None:
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._motion_profiles = {"move": MotionProfile(role=DemonstrationRole.MOVE, max_duration=0.35)}
    daemon.movement_basis = None
    daemon.camera_mapping = CameraMapping(
        identity_fingerprint="client-1",
        generation=1,
        capture_id="camera:boot-1:1:2",
        yaw_per_pixel=0.1,
    )
    daemon._native_clock = lambda: 10.2
    daemon._require_interaction = lambda _generation: 1
    facing_a, facing_b, world = 0.4, 1.2, 0.6
    dx, dy = 0.2 * math.cos(world), 0.2 * math.sin(world)
    frames = [
        MotionFrame.from_sample(_sample(sequence=1, capture=10.0, facing=facing_a, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=2, capture=10.1, facing=facing_a, speed=0.0), _Identity()),
        MotionFrame.from_sample(_sample(sequence=3, capture=10.2, facing=facing_a, speed=0.0), _Identity()),
        MotionFrame.from_sample(
            _sample(sequence=4, capture=10.3, facing=facing_a, x=dx, y=dy, speed=0.0), _Identity()
        ),
        MotionFrame.from_sample(
            _sample(sequence=5, capture=10.4, facing=facing_b, x=dx, y=dy, speed=0.0), _Identity()
        ),
        MotionFrame.from_sample(
            _sample(sequence=6, capture=10.5, facing=facing_b, x=dx, y=dy, speed=0.0), _Identity()
        ),
        MotionFrame.from_sample(
            _sample(sequence=7, capture=10.6, facing=facing_b, x=2 * dx, y=2 * dy, speed=0.0), _Identity()
        ),
    ]

    def observe(
        generation: int,
        previous: MotionFrame | None = None,
        *,
        not_before: float | None = None,
        after_release: bool = False,
    ) -> MotionFrame:
        del generation, not_before, after_release
        frame = frames.pop(0)
        frame.require_safe_successor(previous, now=frame.capture_monotonic + 0.01)
        return frame

    daemon._observe_motion = observe
    daemon._observe_route = lambda generation, *args, frame, corridor_heading, corridor_distance: (
        RouteEvidence(
            "client-1",
            frame.capture_monotonic + 0.01,
            "world",
            "clear",
            True,
            True,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest="route-digest",
            corridor_heading=corridor_heading,
            corridor_distance=corridor_distance,
        )
    )
    daemon.execute_camera_delta = lambda _pixels, *, generation, previous=None: frames.pop(0)
    daemon.driver = SimpleNamespace(
        resolve_identity=lambda **kwargs: _Identity(),
        run_motion_key_hold=lambda *args, **kwargs: None,
    )
    with pytest.raises(DriverError, match="headings did not change"):
        daemon.calibrate_movement_basis(0.20, generation=1)
