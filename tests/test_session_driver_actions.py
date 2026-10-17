from __future__ import annotations

import os
import subprocess
import threading
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from crowley.session.calibration import XTestInputProfile
from crowley.session.driver import (
    DesktopDriver,
    DriverError,
    DriverProfile,
    WindowIdentity,
    X11Backend,
)
from crowley.session.executor import (
    BindingMetadata,
    CameraDragPlan,
    DemonstrationRole,
    KeyRole,
    MotionProfile,
    Point,
    PointerButton,
    PointerSample,
    PointerTarget,
    Rect,
    plan_pointer_curve,
)
from crowley.session.input_events import EventClass, XI2Event
from tests.test_session_input_tool import fixture_input_tool


def _identity() -> WindowIdentity:
    return WindowIdentity(
        0x100,
        123,
        "game.exe",
        "World of Warcraft",
        "wow",
        0x101,
        (0, 0, 400, 300),
        (0, 0, 400, 300),
        0x100,
        "start",
        ":actions",
        "identity",
        0x1,
        0x100,
        frozenset({0x100, 0x101}),
    )


def _evidence() -> SimpleNamespace:
    hierarchy = ((4, 2, "slave", "pointer:xtest"),)
    return SimpleNamespace(
        is_live=True,
        fingerprint="input-evidence",
        synthetic_key_source=4,
        synthetic_pointer_source=4,
        xinput_hierarchy=hierarchy,
        xtest_profile=XTestInputProfile(
            4,
            2,
            "pointer:xtest",
            3,
            ((0, "Rel X", "relative", -1.0, -1.0, 0), (1, "Rel Y", "relative", -1.0, -1.0, 0)),
            1,
            1,
            (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
            0x1,
            (0, 0, 1920, 1080),
            hierarchy,
        ),
        synthetic_modifiers=(0, 0, 0),
        synthetic_echo_proof=(),
        keyboard_keymap=(
            ("a", 38),
            ("d", 40),
            ("s", 39),
            ("w", 25),
        ),
        event_proof=(
            ("KeyPress", 0, 4, 4, 0, 0, 0, 0, 0, 0, (0, 0, 0), 0),
            ("KeyRelease", 0, 4, 4, 0, 0, 0, 0, 0, 0, (0, 0, 0), 0),
        ),
    )


class _EventMonitor:
    def __init__(self, events: list[SimpleNamespace]):
        self.events = events

    def wait_for_event(self, predicate, *, timeout: float) -> None:
        del timeout
        for event in self.events:
            # The callback is installed by the test on the guardian.  The
            # predicate is only a completion check, so feed events directly.
            self.callback(event)
            if predicate(self.events):
                return
        assert predicate(self.events)

    def set_callback(self, callback) -> None:
        self.callback = callback

    def stop(self) -> None:
        return None


def _event(
    event_class: EventClass,
    timestamp: int,
    *,
    source: int = 4,
    master: int = 4,
    target: int | None = 0x101,
    detail: int = 25,
    root: tuple[int, int] | None = None,
    event_xy: tuple[int, int] | None = None,
    valuators: tuple[tuple[int, float, float | None], ...] = (),
) -> SimpleNamespace:
    raw = event_class.value.startswith("Raw")
    if raw:
        master = 2
        target = None
    type_number = {
        EventClass.RAW_KEY_PRESS: 13,
        EventClass.KEY_PRESS: 2,
        EventClass.RAW_KEY_RELEASE: 14,
        EventClass.KEY_RELEASE: 3,
        EventClass.RAW_BUTTON_PRESS: 15,
        EventClass.BUTTON_PRESS: 4,
        EventClass.RAW_BUTTON_RELEASE: 16,
        EventClass.BUTTON_RELEASE: 5,
        EventClass.MOTION: 6,
        EventClass.RAW_MOTION: 17,
    }[event_class]
    return XI2Event(
        type_number,
        event_class,
        master,
        source,
        timestamp,
        0 if event_class in {EventClass.MOTION, EventClass.RAW_MOTION} else detail,
        0x1 if event_class in {EventClass.MOTION, EventClass.RAW_MOTION} else None,
        0x1 if event_class in {EventClass.MOTION, EventClass.RAW_MOTION} else None,
        target,
        root,
        event_xy if event_xy is not None else root,
        None if raw else (0, 0, 0),
        modifier_effective=None if raw else 0,
        valuators=valuators,
    )


def _motion_pair(
    timestamp: int,
    origin: tuple[int, int],
    endpoint: tuple[int, int],
) -> tuple[SimpleNamespace, SimpleNamespace]:
    valuators = ((0, float(endpoint[0]), float(endpoint[0])), (1, float(endpoint[1]), float(endpoint[1])))
    return (
        _event(
            EventClass.RAW_MOTION,
            timestamp,
            root=None,
            valuators=valuators,
        ),
        _event(
            EventClass.MOTION,
            timestamp,
            root=origin,
            event_xy=origin,
            valuators=valuators,
        ),
    )


def _driver(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, executable_source: str = "") -> DesktopDriver:
    backend = X11Backend(
        DriverProfile(display=":actions", xauthority=str(tmp_path / "Xauthority")),
        input_tool=fixture_input_tool(tmp_path / "tool", executable_source or "/bin/true"),
    )
    identity = _identity()
    backend.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
    backend.observe_keymap = lambda: {"a": 38, "d": 40, "s": 39, "w": 25}  # type: ignore[method-assign]
    backend.observe_keymap_levels = lambda: {25: ("w", "W"), 38: ("a", "A"), 39: ("s", "S"), 40: ("d", "D")}  # type: ignore[method-assign]
    monkeypatch.setattr("crowley.session.driver._resolve_wrapped_executable", lambda _command: "/bin/true")
    driver = DesktopDriver(profile=backend.profile, backend=backend, lease_path=tmp_path / "actions.lock")
    driver._input_evidence = _evidence()
    driver.input_hierarchy = lambda **_kwargs: driver._input_evidence.xinput_hierarchy  # type: ignore[method-assign]
    backend.xtest_input_profile = lambda _hierarchy, **_kwargs: driver._input_evidence.xtest_profile  # type: ignore[method-assign]
    return driver


def test_run_motion_key_hold_uses_real_driver_entrypoint_and_sealed_level_zero_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver = _driver(tmp_path, monkeypatch)
    monitor = _EventMonitor(
        [
            _event(EventClass.RAW_KEY_PRESS, 1, detail=25),
            _event(EventClass.KEY_PRESS, 2, detail=25),
            _event(EventClass.RAW_KEY_RELEASE, 3, detail=25),
            _event(EventClass.KEY_RELEASE, 4, detail=25),
        ]
    )
    monitor.set_callback(driver.guardian.observe)
    driver._monitor = monitor  # type: ignore[assignment]
    generation = driver.guardian.arm(driver._input_evidence)
    driver.backend.activate_generation(generation)
    frame = SimpleNamespace(binding=lambda role: {"moveForward": "W"}[role])
    try:
        driver.run_motion_key_hold(KeyRole.MOVE_FORWARD, 0.05, frame, generation=generation)
        assert driver.guardian.armed
    finally:
        driver.close()


def test_run_motion_key_hold_rejects_shift_level_drift_before_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver = _driver(tmp_path, monkeypatch)
    driver.backend.observe_keymap_levels = lambda: {25: ("W", "w")}  # type: ignore[method-assign]
    generation = driver.guardian.arm(driver._input_evidence)
    driver.backend.activate_generation(generation)
    frame = SimpleNamespace(binding=lambda role: {"moveForward": "W"}[role])
    try:
        with pytest.raises(DriverError, match="level-zero"):
            driver.run_motion_key_hold(KeyRole.MOVE_FORWARD, 0.05, frame, generation=generation)
    finally:
        driver.close()


@pytest.mark.parametrize("operation", ["click", "camera"])
def test_native_pointer_producers_reject_profile_drift_before_input(
    operation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver = _driver(tmp_path, monkeypatch)
    sealed = driver._input_evidence.xtest_profile
    commands: list[list[str]] = []
    monkeypatch.setattr(
        driver.backend,
        "_run",
        lambda args, **_kwargs: commands.append(list(args)) or subprocess.CompletedProcess(args, 0, "", ""),
    )
    driver.backend.xtest_input_profile = lambda _hierarchy, **_kwargs: replace(  # type: ignore[method-assign]
        sealed, root_geometry=(0, 0, 1920, 1081)
    )
    generation = driver.guardian.arm(driver._input_evidence)
    driver.backend.activate_generation(generation)
    try:
        if operation == "click":
            with pytest.raises(DriverError, match="profile changed"):
                driver.run(
                    "open_ah",
                    generation,
                    precondition=lambda _identity: True,
                    postcondition=lambda _identity: True,
                )
        else:
            binding = BindingMetadata("identity", "capture", 1, generation, 4, (4,), boot="boot")
            plan = CameraDragPlan(
                PointerButton.RIGHT,
                (PointerSample(0.0, Point(100, 100)), PointerSample(0.05, Point(110, 120))),
                0.05,
                Point(10, 20),
                binding,
            )
            with pytest.raises(DriverError, match="profile changed"):
                driver.run_camera_drag(plan, generation=generation)
        assert commands == []
    finally:
        driver.close()


def test_run_camera_drag_requires_position_press_held_motion_and_endpoint_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver = _driver(tmp_path, monkeypatch)
    pointer_positions = [(20, 20, 0x101), (130, 100, 0x101)]
    driver.backend.pointer_position = lambda **_kwargs: pointer_positions.pop(0)  # type: ignore[method-assign]
    binding = BindingMetadata("identity", "capture", 1, 1, 4, (4,), boot="boot")
    plan = CameraDragPlan(
        PointerButton.RIGHT,
        (PointerSample(0.0, Point(100, 100)), PointerSample(0.05, Point(130, 100))),
        0.05,
        Point(30, 0),
        binding,
    )
    positioning = plan_pointer_curve(
        Point(20, 20),
        PointerTarget("camera-viewport", Rect(100, 100, 1, 1), binding, padding=0),
        Rect(0, 0, 400, 300),
        profile=MotionProfile(role=DemonstrationRole.POINTER),
    )
    events: list[SimpleNamespace] = []
    timestamp = 1
    prior = positioning.samples[0].point
    for sample in positioning.samples[1:]:
        if sample.point != prior:
            events.extend(
                _motion_pair(
                    timestamp,
                    (int(prior.x), int(prior.y)),
                    (int(sample.point.x), int(sample.point.y)),
                )
            )
            timestamp += 1
            prior = sample.point
    events.extend(
        [
            _event(EventClass.RAW_BUTTON_PRESS, timestamp, detail=3),
            _event(EventClass.BUTTON_PRESS, timestamp + 1, detail=3, root=(100, 100), event_xy=(100, 100)),
            *_motion_pair(timestamp + 2, (100, 100), (130, 100)),
            _event(EventClass.RAW_BUTTON_RELEASE, timestamp + 3, detail=3),
            _event(EventClass.BUTTON_RELEASE, timestamp + 4, detail=3, root=(130, 100), event_xy=(130, 100)),
        ]
    )
    monitor = _EventMonitor(events)
    monitor.set_callback(driver.guardian.observe)
    driver._monitor = monitor  # type: ignore[assignment]
    generation = driver.guardian.arm(driver._input_evidence)
    driver.backend.activate_generation(generation)
    plan = CameraDragPlan(
        plan.button,
        plan.samples,
        plan.duration,
        plan.signed_delta,
        replace(binding, generation=generation),
    )
    try:
        driver.run_camera_drag(plan, generation=generation)
        assert driver.guardian.armed
    finally:
        driver.close()


def test_run_camera_drag_rejects_all_identical_native_samples_before_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver = _driver(tmp_path, monkeypatch)
    commands: list[list[str]] = []
    driver.backend.pointer_position = lambda **_kwargs: (100, 100, 0x101)  # type: ignore[method-assign]
    monkeypatch.setattr(
        driver.backend,
        "_run",
        lambda args, **_kwargs: commands.append(list(args)) or subprocess.CompletedProcess(args, 0, "", ""),
    )
    binding = BindingMetadata("identity", "capture", 1, 1, 4, (4,), boot="boot")
    # Bypass constructor validation deliberately to exercise the defensive driver guard.
    plan = object.__new__(CameraDragPlan)
    object.__setattr__(plan, "button", PointerButton.RIGHT)
    object.__setattr__(
        plan,
        "samples",
        (PointerSample(0.0, Point(100, 100)), PointerSample(0.05, Point(100, 100))),
    )
    object.__setattr__(plan, "duration", 0.05)
    object.__setattr__(plan, "signed_delta", Point(0, 0))
    object.__setattr__(plan, "binding", replace(binding, generation=1))
    generation = driver.guardian.arm(driver._input_evidence)
    driver.backend.activate_generation(generation)
    try:
        with pytest.raises(DriverError, match="no native motion trace"):
            driver.run_camera_drag(plan, generation=generation)
        assert commands == []
    finally:
        driver.close()


def test_run_camera_drag_allows_press_at_start_without_positioning_trace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver = _driver(tmp_path, monkeypatch)
    pointer_positions = [(100, 100, 0x101), (130, 100, 0x101)]
    driver.backend.pointer_position = lambda **_kwargs: pointer_positions.pop(0)  # type: ignore[method-assign]
    binding = BindingMetadata("identity", "capture", 1, 1, 4, (4,), boot="boot")
    plan = CameraDragPlan(
        PointerButton.RIGHT,
        (PointerSample(0.0, Point(100, 100)), PointerSample(0.05, Point(130, 100))),
        0.05,
        Point(30, 0),
        replace(binding, generation=1),
    )
    events = [
        _event(EventClass.RAW_BUTTON_PRESS, 1, detail=3),
        _event(EventClass.BUTTON_PRESS, 2, detail=3, root=(100, 100), event_xy=(100, 100)),
        *_motion_pair(3, (100, 100), (130, 100)),
        _event(EventClass.RAW_BUTTON_RELEASE, 4, detail=3),
        _event(EventClass.BUTTON_RELEASE, 5, detail=3, root=(130, 100), event_xy=(130, 100)),
    ]
    monitor = _EventMonitor(events)
    monitor.set_callback(driver.guardian.observe)
    driver._monitor = monitor  # type: ignore[assignment]
    generation = driver.guardian.arm(driver._input_evidence)
    driver.backend.activate_generation(generation)
    plan = replace(plan, binding=replace(binding, generation=generation))
    try:
        driver.run_camera_drag(plan, generation=generation)
        assert driver.guardian.armed
    finally:
        driver.close()


def test_guardian_allows_zero_motion_canonical_click_with_button_trace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver = _driver(tmp_path, monkeypatch)
    monitor = _EventMonitor(
        [
            _event(EventClass.RAW_BUTTON_PRESS, 1, detail=3),
            _event(EventClass.BUTTON_PRESS, 2, detail=3, root=(100, 100), event_xy=(100, 100)),
            _event(EventClass.RAW_BUTTON_RELEASE, 3, detail=3),
            _event(EventClass.BUTTON_RELEASE, 4, detail=3, root=(100, 100), event_xy=(100, 100)),
        ]
    )
    monitor.set_callback(driver.guardian.observe)
    driver._monitor = monitor  # type: ignore[assignment]
    generation = driver.guardian.arm(driver._input_evidence)
    driver.backend.activate_generation(generation)
    try:
        action = driver.guardian.begin_action(
            generation,
            target_xid=0x101,
            source_device=4,
            master_device=2,
            event_classes={
                EventClass.RAW_BUTTON_PRESS.value,
                EventClass.BUTTON_PRESS.value,
                EventClass.RAW_BUTTON_RELEASE.value,
                EventClass.BUTTON_RELEASE.value,
            },
            device_by_class={
                EventClass.RAW_BUTTON_PRESS.value: 2,
                EventClass.BUTTON_PRESS.value: 4,
                EventClass.RAW_BUTTON_RELEASE.value: 2,
                EventClass.BUTTON_RELEASE.value: 4,
            },
            required_sequence=(
                EventClass.RAW_BUTTON_PRESS.value,
                EventClass.BUTTON_PRESS.value,
                EventClass.RAW_BUTTON_RELEASE.value,
                EventClass.BUTTON_RELEASE.value,
            ),
            expected_modifiers=(0, 0, 0),
            expected_details=(3, 3, 3, 3),
            expected_press_coordinates=(100.0, 100.0),
            expected_press_event_coordinates=(100.0, 100.0),
            expected_release_coordinates=(100.0, 100.0),
            expected_release_event_coordinates=(100.0, 100.0),
            initial_origin=(100, 100, 100, 100),
            expected_root_xid=1,
            expected_event_xid=1,
            expected_child_xids=frozenset({0x101}),
            canonical_motion=True,
            require_motion_before_button=False,
            require_motion_before_release=False,
            held_buttons={3},
        )
        driver.guardian.dispatch_admission(generation, lambda: None)
        assert action is driver.guardian.action
        for event in monitor.events:
            assert driver.guardian.observe(event)
        assert action.complete
        driver.guardian.finish_action(generation, action)
    finally:
        driver.close()


@pytest.mark.parametrize(
    "variant",
    [
        "early-release",
        "motion-after-release",
        "wrong-coordinate",
        "motion-before-press",
        "wrong-target",
        "missing-motion",
        "late-motion",
        "wrong-release-root",
        "wrong-release-event-coordinate",
        "wrong-release-target",
    ],
)
def test_run_camera_drag_rejects_invalid_native_phase_trace(
    variant: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver = _driver(tmp_path, monkeypatch)
    driver.backend.pointer_position = lambda **_kwargs: (20, 20, 0x101)  # type: ignore[method-assign]
    binding = BindingMetadata("identity", "capture", 1, 1, 4, (4,), boot="boot")
    plan = CameraDragPlan(
        PointerButton.RIGHT,
        (PointerSample(0.0, Point(100, 100)), PointerSample(0.05, Point(130, 100))),
        0.05,
        Point(30, 0),
        binding,
    )
    positioning = plan_pointer_curve(
        Point(20, 20),
        PointerTarget("camera-viewport", Rect(100, 100, 1, 1), binding, padding=0),
        Rect(0, 0, 400, 300),
        profile=MotionProfile(role=DemonstrationRole.POINTER),
    )
    events: list[SimpleNamespace] = []
    timestamp = 1
    prior = positioning.samples[0].point
    for sample in positioning.samples[1:]:
        if sample.point != prior:
            events.extend(
                _motion_pair(
                    timestamp,
                    (int(prior.x), int(prior.y)),
                    (int(sample.point.x), int(sample.point.y)),
                )
            )
            timestamp += 1
            prior = sample.point
    if variant == "motion-before-press":
        events.extend(_motion_pair(timestamp, (int(prior.x), int(prior.y)), (60, 60)))
        timestamp += 1
    press_root = (101, 100) if variant == "wrong-coordinate" else (100, 100)
    press_target = 0x999 if variant == "wrong-target" else 0x101
    events.extend(
        [
            _event(EventClass.RAW_BUTTON_PRESS, timestamp, detail=3),
            _event(
                EventClass.BUTTON_PRESS,
                timestamp + 1,
                detail=3,
                root=press_root,
                event_xy=press_root,
                target=press_target,
            ),
        ]
    )
    if variant not in {
        "early-release",
        "wrong-coordinate",
        "wrong-target",
        "missing-motion",
    }:
        motion_timestamp = timestamp - 1 if variant == "late-motion" else timestamp + 2
        events.extend(_motion_pair(motion_timestamp, (100, 100), (130, 100)))
    if variant == "motion-after-release":
        events.extend(
            [
                _event(EventClass.RAW_BUTTON_RELEASE, timestamp + 3, detail=3),
                *_motion_pair(timestamp + 4, (100, 100), (130, 100)),
                _event(
                    EventClass.BUTTON_RELEASE,
                    timestamp + 5,
                    detail=3,
                    root=(130, 100),
                    event_xy=(130, 100),
                ),
            ]
        )
    else:
        release_at = timestamp + (2 if variant == "early-release" else 3)
        release_root = (129, 100) if variant == "wrong-release-root" else (130, 100)
        release_event = (129, 100) if variant == "wrong-release-event-coordinate" else (130, 100)
        release_target = 0x999 if variant == "wrong-release-target" else 0x101
        events.extend(
            [
                _event(EventClass.RAW_BUTTON_RELEASE, release_at, detail=3),
                _event(
                    EventClass.BUTTON_RELEASE,
                    release_at + 1,
                    detail=3,
                    root=release_root,
                    event_xy=release_event,
                    target=release_target,
                ),
            ]
        )

    class NonCompletingMonitor(_EventMonitor):
        def wait_for_event(self, predicate, *, timeout: float) -> None:
            del predicate, timeout
            for event in self.events:
                self.callback(event)

    monitor = NonCompletingMonitor(events)
    monitor.set_callback(driver.guardian.observe)
    driver._monitor = monitor  # type: ignore[assignment]
    generation = driver.guardian.arm(driver._input_evidence)
    driver.backend.activate_generation(generation)
    plan = replace(plan, binding=replace(binding, generation=generation))
    try:
        with pytest.raises(
            DriverError,
            match="did not complete|unattributed|cancelled|lease is revoked",
        ):
            driver.run_camera_drag(plan, generation=generation)
        if variant in {"wrong-release-root", "wrong-release-event-coordinate", "wrong-release-target"}:
            assert "unattributed XI2 event class=ButtonRelease" in driver.guardian.revoked_reason
    finally:
        driver.close()


def test_run_camera_drag_cancels_after_admitted_held_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cancellation must cover a real admitted process and published button hold."""

    driver = _driver(tmp_path, monkeypatch)
    script = tmp_path / "harmless-camera-boundary"
    script.write_text("#!/bin/sh\nexec /bin/sleep 30\n", encoding="utf-8")
    script.chmod(0o700)
    monkeypatch.setattr("crowley.session.driver._resolve_wrapped_executable", lambda _command: str(script))
    release_calls: list[list[str]] = []
    driver.backend._release_command = lambda args: release_calls.append(args) or True  # type: ignore[method-assign]
    driver.backend.pointer_position = lambda **_kwargs: (100, 100, 0x101)  # type: ignore[method-assign]
    binding = BindingMetadata("identity", "capture", 1, 1, 4, (4,), boot="boot")
    plan = CameraDragPlan(
        PointerButton.RIGHT,
        (PointerSample(0.0, Point(100, 100)), PointerSample(0.05, Point(130, 100))),
        0.05,
        Point(30, 0),
        binding,
    )
    monitor = _EventMonitor([])
    monitor.set_callback(driver.guardian.observe)
    driver._monitor = monitor  # type: ignore[assignment]
    generation = driver.guardian.arm(driver._input_evidence)
    driver.backend.activate_generation(generation)
    plan = replace(plan, binding=replace(binding, generation=generation))
    held = threading.Event()
    waiter_errors: list[str] = []
    observed_groups: set[int] = set()

    def revoke_after_admission() -> None:
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            if (
                driver.guardian.held
                and driver.backend._held_buttons == {3}
                and driver.guardian.active_process_groups
            ):
                observed_groups.update(driver.guardian.active_process_groups)
                held.set()
                driver.revoke("test cancellation during admitted camera hold")
                return
            time.sleep(0.005)
        waiter_errors.append("camera hold was not admitted")

    waiter = threading.Thread(target=revoke_after_admission, daemon=True)
    waiter.start()
    try:
        with pytest.raises(DriverError, match="cancelled|revoked|generation|desktop command failed"):
            driver.run_camera_drag(plan, generation=generation)
        waiter.join(timeout=3.0)
        assert not waiter.is_alive()
        assert not waiter_errors
        assert held.is_set()
        assert observed_groups
        assert not driver.guardian.active_process_groups
        assert not driver.backend.active_process_groups
        assert not driver.guardian.held
        assert not driver.backend._held_buttons
        assert all(not Path(f"/proc/{pid}").exists() for pid in observed_groups)
        assert release_calls == [["xdotool", "mouseup", "3"]]
    finally:
        driver.close()


def test_native_resolver_accepts_captured_direct_root_wine_client_certificate(
    tmp_path: Path,
) -> None:
    """The production resolver must emit the exact captured native target set."""

    outer = 0x700100
    client = 0x700101
    pid = 5717
    profile = DriverProfile(
        display=":captured",
        xauthority=str(tmp_path / "Xauthority"),
        wine_prefix=str(tmp_path / "wine"),
    )
    backend = X11Backend(profile, input_tool=fixture_input_tool(tmp_path / "tool"))
    tree = (
        "xwininfo: Window id: 0x374 (the root window)\n"
        f'  {hex(outer)} "World of Warcraft": ("wowb.exe" "wowb.exe") '
        "1928x1092+0+0  +0+0\n"
        f'    {hex(client)} "World of Warcraft": ("wowb.exe" "wowb.exe") '
        "1920x1080+0+0  +0+0\n"
    )
    outer_tree = (
        f'xwininfo: Window id: {hex(outer)} "World of Warcraft"\n'
        f'  {hex(client)} "World of Warcraft": ("wowb.exe" "wowb.exe") '
        "1920x1080+0+0  +0+0\n"
    )

    def command(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if args == ["xdotool", "search", "--name", "World of Warcraft"]:
            return subprocess.CompletedProcess(args, 0, f"{hex(outer)}\n", "")
        if args == ["xdotool", "getwindowgeometry", "--shell", hex(outer)]:
            return subprocess.CompletedProcess(
                args,
                0,
                "WINDOW=7340288\nX=0\nY=0\nWIDTH=1928\nHEIGHT=1092\nSCREEN=0\n",
                "",
            )
        if args == ["xprop", "-id", hex(outer), "WM_NAME", "_NET_WM_PID", "WM_CLASS"]:
            return subprocess.CompletedProcess(
                args,
                0,
                f'WM_NAME(STRING) = "World of Warcraft"\n_NET_WM_PID(CARDINAL) = {pid}\n'
                'WM_CLASS(STRING) = "wowb.exe", "wowb.exe"\n',
                "",
            )
        if args == ["xwininfo", "-id", hex(outer), "-tree"]:
            return subprocess.CompletedProcess(args, 0, outer_tree, "")
        if args == ["xwininfo", "-root", "-tree"]:
            return subprocess.CompletedProcess(args, 0, tree, "")
        if args == ["xdotool", "getwindowfocus"]:
            return subprocess.CompletedProcess(args, 0, f"{hex(client)}\n", "")
        if args == ["xprop", "-root", "_NET_ACTIVE_WINDOW"]:
            return subprocess.CompletedProcess(
                args, 0, f"_NET_ACTIVE_WINDOW(WINDOW): window id # {hex(client)}\n", ""
            )
        raise AssertionError(args)

    backend._run = command  # type: ignore[method-assign]
    backend._matching_game_pids = lambda: {pid}  # type: ignore[method-assign]
    backend._process_executable = lambda _pid: ("WowB.exe", "wine-start")  # type: ignore[method-assign]
    identity = backend.resolve_identity()
    assert identity.root_xid == 0x374
    assert identity.managed_frame_xid == outer
    assert identity.target_event_xids == frozenset({outer, client})
    assert identity.xid == outer
    assert identity.child_xid == client


def test_begin_action_does_not_publish_unemitted_planned_holds(tmp_path: Path) -> None:
    from crowley.session.guardian import InputGuardian

    guardian = InputGuardian(tmp_path / "planned.lock", parent_pid=os.getpid())

    class Evidence:
        is_live = True
        fingerprint = "planned"

    generation = guardian.arm(Evidence())
    action = guardian.begin_action(
        generation,
        target_xid=0x101,
        source_device=4,
        master_device=2,
        event_classes={"RawKeyPress"},
        required_sequence=("RawKeyPress",),
        held_keys={"w"},
    )
    try:
        assert not guardian.held
        assert not action.complete
    finally:
        guardian.revoke("test cleanup")
        guardian.close()


def test_publish_holds_rejects_keys_outside_planned_action(tmp_path: Path) -> None:
    from crowley.session.guardian import GuardianError, InputGuardian

    guardian = InputGuardian(tmp_path / "planned-mismatch.lock", parent_pid=os.getpid())

    class Evidence:
        is_live = True
        fingerprint = "planned-mismatch"

    generation = guardian.arm(Evidence())
    guardian.begin_action(
        generation,
        target_xid=0x101,
        source_device=4,
        master_device=2,
        event_classes={"RawKeyPress"},
        required_sequence=("RawKeyPress",),
        held_keys={"w"},
    )
    try:
        with pytest.raises(GuardianError, match="do not match"):
            guardian.publish_current_holds(generation, {"s"}, set())
        assert not guardian.held
    finally:
        guardian.revoke("test cleanup")
        guardian.close()


def test_native_window_certificate_rejects_extra_direct_helper(tmp_path: Path) -> None:
    backend = X11Backend(
        DriverProfile(display=":actions", xauthority=str(tmp_path / "Xauthority")),
        input_tool=fixture_input_tool(tmp_path / "tool"),
    )
    tree = """\
xwininfo: Window id: 0x1 (the root window)
  0x100 "outer": () 400x300+0+0
    0x101 "client": () 400x300+0+0
    0x102 "helper": () 1x1+0+0
"""
    backend._run = lambda args, **kwargs: subprocess.CompletedProcess(args, 0, tree, "")  # type: ignore[method-assign]
    with pytest.raises(DriverError, match="unexpected helper"):
        backend._verified_window_relationship(0x100, 0x101, deadline_monotonic=time.monotonic() + 1)


def test_native_target_membership_requires_nonempty_exact_certificate(tmp_path: Path) -> None:
    backend = X11Backend(
        DriverProfile(display=":actions", xauthority=str(tmp_path / "Xauthority")),
        input_tool=fixture_input_tool(tmp_path / "tool"),
    )
    identity = _identity()
    assert backend._is_owned_client_target(identity.xid, identity)
    assert backend._is_owned_client_target(identity.child_xid, identity)
    for foreign in (identity.root_xid, 0x102, 0x999):
        assert not backend._is_owned_client_target(foreign, identity)
    incomplete = replace(identity, target_event_xids=frozenset())
    assert not backend._is_owned_client_target(identity.xid, incomplete)
    assert not backend._is_owned_client_target(identity.child_xid, incomplete)


def test_native_command_deadline_terminates_before_backend_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = X11Backend(
        DriverProfile(display=":actions", xauthority=str(tmp_path / "Xauthority")),
        input_tool=fixture_input_tool(tmp_path / "tool"),
    )
    monkeypatch.setattr("crowley.session.driver._resolve_wrapped_executable", lambda _command: "/bin/sleep")
    with pytest.raises(DriverError, match="timed out|deadline"):
        backend._run(
            ["sleep", "0.5"],
            timeout=2.0,
            deadline_monotonic=time.monotonic() + 0.03,
        )
    assert not backend._active_processes


def test_desktop_identity_deadline_reaches_native_resolver(tmp_path: Path) -> None:
    backend = X11Backend(
        DriverProfile(display=":actions", xauthority=str(tmp_path / "Xauthority")),
        input_tool=fixture_input_tool(tmp_path / "tool"),
    )
    identity = _identity()
    received: list[float | None] = []

    def resolve(*, require_foreground: bool = True, deadline_monotonic: float | None = None):
        del require_foreground
        received.append(deadline_monotonic)
        return identity

    backend.resolve_identity = resolve  # type: ignore[method-assign]
    driver = DesktopDriver(profile=backend.profile, backend=backend, lease_path=tmp_path / "actions.lock")
    deadline = time.monotonic() + 1
    try:
        assert driver.resolve_identity(deadline_monotonic=deadline) is identity
        assert received == [deadline]
    finally:
        driver.close()
