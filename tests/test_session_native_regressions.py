"""Focused native boundary regressions.

These fixtures exercise the owned calibration and X11 boundary with fake
processes, clocks, and observers.  They do not claim that a real game client
or a human input sample has passed calibration.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from crowley.session.calibration import (
    CalibrationError,
    InputCalibrationEvidence,
    InputCalibrationWorkflow,
    KeyboardProbeOperation,
    KeyboardProbeStep,
    LinuxProcStatusVmHwmReset5,
    NativeCalibrationEvidence,
    NativeCalibrationRunner,
    NativeMemoryArchiveReceipt,
    NativeMemoryMeasurement,
    NativePreconstructionEvidence,
    NativeRenderObservation,
    NativeRestorationReceipt,
    NativeResumeBoundary,
    OwnedGtkCalibrationWindow,
    OwnedWindow,
    XTestInputProfile,
)
from crowley.session.decoder import PixelDecoder
from crowley.session.driver import (
    _EXEC_ADMISSION_WRAPPER,
    DesktopDriver,
    DriverError,
    DriverProfile,
    InputMonitor,
    MeasuredAnchor,
    RecordingBackend,
    WindowIdentity,
    X11Backend,
)
from crowley.session.guardian import GuardianError, InputGuardian
from crowley.session.input_events import EventClass, XI2Event, parse_xi2_records
from crowley.session.protocol import ProtocolError, encode_frame, pack_cells
from tests.test_session_input_tool import fixture_input_tool

TARGET = 0x600119
FOREIGN = 0x1A00011


def _xtest_profile(
    hierarchy: tuple[tuple[int, int, str, str], ...],
    *,
    source: int = 4,
    parent: int = 2,
    root: int = 0x374,
) -> XTestInputProfile:
    return XTestInputProfile(
        source,
        parent,
        next((row[3] for row in hierarchy if row[0] == source), "XTEST pointer"),
        3,
        ((0, "Rel X", "relative", -1.0, -1.0, 0), (1, "Rel Y", "relative", -1.0, -1.0, 0)),
        1,
        1,
        (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
        root,
        (0, 0, 1920, 1080),
        hierarchy,
    )


def _mutter_gtk_fixture_command(
    *,
    pid: int,
    target: int,
    frame: int,
    helper: int,
    child: int,
    frame_pid: int = 5717,
    frame_for: int | None = None,
    advertised_helper: int | None = None,
    extra_frame_child: int | None = None,
    helper_stats: str | None = None,
    frame_props: str | None = None,
    helper_props: str | None = None,
):
    """Build the captured Mutter certificate command surface for GTK tests."""

    frame_for = target if frame_for is None else frame_for
    advertised_helper = helper if advertised_helper is None else advertised_helper

    def stats(x: int, y: int, width: int, height: int) -> str:
        return f"Absolute upper-left X: {x}\nAbsolute upper-left Y: {y}\nWidth: {width}\nHeight: {height}\n"

    def command(args: list[str], **_kwargs: object) -> str:
        if args[:2] == ["wmctrl", "-lp"]:
            return f"{hex(target)}  -1 {pid} host CROWLEY INPUT CALIBRATION ONLY\n"
        if args == ["xprop", "-id", hex(target)]:
            return (
                f'WM_NAME(STRING) = "CROWLEY INPUT CALIBRATION ONLY"\n'
                f"_NET_WM_PID(CARDINAL) = {pid}\n"
                "_NET_FRAME_EXTENTS(CARDINAL) = 5, 31, 5, 38\n"
            )
        if args == ["xprop", "-id", hex(frame)]:
            return frame_props or (
                f"_MUTTER_FRAME_FOR(WINDOW): window id # {hex(frame_for)}\n"
                f"_NET_WM_USER_TIME_WINDOW(WINDOW): window id # {hex(advertised_helper)}\n"
                f"_NET_WM_PID(CARDINAL) = {frame_pid}\n"
                'WM_CLASS(STRING) = "mutter-x11-frames", "mutter-x11-frames"\n'
            )
        if args == ["xprop", "-id", hex(helper)]:
            return helper_props or "_NET_WM_USER_TIME(CARDINAL) = 276992109\n"
        if args[0] == "xprop":
            raise AssertionError(args)
        if args == ["xwininfo", "-root", "-tree"]:
            extra = (
                # Deliberate mutation: retain native child syntax while adding
                # one unadvertised direct sibling to the captured tree.
                f"    {hex(extra_frame_child)} (has no name): () 1x1+1+1  +693+363\n"
                if extra_frame_child is not None
                else ""
            )
            return (
                "xwininfo: Window id: 0x374 (the root window)\n"
                f'  {hex(frame)} "CROWLEY INPUT CALIBRATION ONLY": '
                f'("mutter-x11-frames" "mutter-x11-frames") 602x401+692+362  +692+362\n'
                f'    {hex(target)} "CROWLEY INPUT CALIBRATION ONLY": ("-c" "-c") '
                "480x240+61+94  +753+456\n"
                f"      {hex(child)} (has no name): () 1x1+-1+-1  +752+455\n"
                f"    {hex(helper)} (has no name): () 1x1+-1+-1  +691+361\n" + extra
            )
        if args == ["xwininfo", "-id", hex(frame), "-stats"]:
            return stats(692, 362, 602, 401) + "Depth: 32\nBorder width: 0\nClass: InputOutput\n"
        if args == ["xwininfo", "-id", hex(target), "-stats"]:
            return (
                stats(753, 456, 480, 240)
                + "Depth: 24\nBorder width: 0\nClass: InputOutput\n"
                + "Map State: IsViewable\n"
            )
        if args == ["xwininfo", "-id", hex(helper), "-stats"]:
            return helper_stats or (
                stats(691, 361, 1, 1) + "Relative upper-left X: -1\nRelative upper-left Y: -1\n"
                "Depth: 0\nBorder width: 0\nClass: InputOnly\n"
            )
        raise AssertionError(args)

    return command


def _wait_for(predicate, *, timeout: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.001)
    return bool(predicate())


# Captured-format xinput test-xi2 blocks.  This deliberately preserves raw
# and delivered master/source pairs, releases, transitions, and the forwarded
# source-7 motion to an unrelated window.
FULL_XI2_TRACE = """EVENT type 13 (RawKeyPress)
    device: 3 (5)
    time: 232007447
    detail: 8
    valuators:
EVENT type 2 (KeyPress)
    device: 5 (5)
    time: 232007447
    detail: 8
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 14 (RawKeyRelease)
    device: 3 (5)
    time: 232007462
    detail: 8
    valuators:
EVENT type 3 (KeyRelease)
    device: 5 (5)
    time: 232007462
    detail: 8
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 1 (DeviceChanged)
    device: 2 (4)
    time: 232007470
    reason: slave_switch
EVENT type 7 (Enter)
    device: 4 (4)
    time: 232007471
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 8 (Leave)
    device: 4 (4)
    time: 232007472
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 15 (RawButtonPress)
    device: 2 (4)
    time: 232007476
    detail: 1
    valuators:
EVENT type 4 (ButtonPress)
    device: 4 (4)
    time: 232007476
    detail: 1
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 16 (RawButtonRelease)
    device: 2 (4)
    time: 232007490
    detail: 1
    valuators:
EVENT type 5 (ButtonRelease)
    device: 4 (4)
    time: 232007490
    detail: 1
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 6 (Motion)
    device: 7 (7)
    time: 232007505
    detail: 0
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x1a00011
"""


def _evidence(
    tmp_path: Path,
    *,
    hierarchy: tuple[tuple[int, int, str, str], ...] | None = None,
    xauthority: str | None = None,
    driver_version: str = "native-x11-3",
    game_identity_fingerprint: str = "owned-game-identity",
    game_geometry: tuple[int, int, int, int] = (0, 0, 1920, 1080),
):
    records = list(parse_xi2_records(FULL_XI2_TRACE, require_event=True))
    # The forwarded motion is retained as an owned-target observation here;
    # the separate full-trace test keeps the foreign-target negative proof.
    records[-1] = replace(
        records[-1],
        child_xid=TARGET,
        event_xid=0x374,
        root_xy=(988.0, 596.0),
        event_xy=(988.0, 596.0),
    )
    records.insert(
        -1,
        replace(
            _event(EventClass.RAW_MOTION, master=2, source=4, timestamp=232007500, detail=0, child=None),
            valuators=((0, 988.0, 988.0), (1, 596.0, 596.0)),
        ),
    )
    records.insert(
        -1,
        replace(
            _event(EventClass.MOTION, master=4, source=4, timestamp=232007500, detail=0),
            valuators=((0, 988.0, 988.0), (1, 596.0, 596.0)),
        ),
    )
    key_details = {
        "Return": 36,
        "slash": 61,
        "r": 27,
        "e": 25,
        "l": 46,
        "o": 43,
        "a": 38,
        "d": 40,
    }
    profile_operations = (
        KeyboardProbeOperation(
            "open_chat",
            "",
            (KeyboardProbeStep("press", "Return"), KeyboardProbeStep("release", "Return")),
        ),
        KeyboardProbeOperation(
            "type_allowlisted_command",
            "/reload",
            tuple(
                step
                for char in "/reload"
                for step in (
                    KeyboardProbeStep("press", {"/": "slash"}.get(char, char)),
                    KeyboardProbeStep("release", {"/": "slash"}.get(char, char)),
                )
            ),
        ),
    )
    profile_keysyms = tuple(sorted(key_details.items()))
    profile_steps = [(operation, step) for operation in profile_operations for step in operation.steps]
    profile_start = 232007540
    for index, (_operation, step) in enumerate(profile_steps):
        detail = key_details[step.keysym]
        event_class = EventClass.RAW_KEY_PRESS if step.phase == "press" else EventClass.RAW_KEY_RELEASE
        delivered_class = EventClass.KEY_PRESS if step.phase == "press" else EventClass.KEY_RELEASE
        timestamp = profile_start + index * 2
        records.extend(
            (
                _event(
                    event_class,
                    master=3,
                    source=5,
                    timestamp=timestamp,
                    detail=detail,
                    child=None,
                ),
                _event(
                    delivered_class,
                    master=5,
                    source=5,
                    timestamp=timestamp + 1,
                    detail=detail,
                ),
            )
        )
    records.extend(
        [
            _event(EventClass.RAW_KEY_PRESS, master=3, source=9, timestamp=232007518, detail=8, child=None),
            _event(EventClass.KEY_PRESS, master=9, source=9, timestamp=232007520, detail=8),
            _event(EventClass.RAW_KEY_RELEASE, master=3, source=9, timestamp=232007522, detail=8, child=None),
            _event(EventClass.KEY_RELEASE, master=9, source=9, timestamp=232007524, detail=8),
            _event(
                EventClass.RAW_BUTTON_PRESS,
                master=2,
                source=7,
                timestamp=232007526,
                detail=1,
                child=None,
            ),
            _event(EventClass.BUTTON_PRESS, master=7, source=7, timestamp=232007528, detail=1),
            _event(
                EventClass.RAW_BUTTON_RELEASE,
                master=2,
                source=7,
                timestamp=232007530,
                detail=1,
                child=None,
            ),
            _event(EventClass.BUTTON_RELEASE, master=7, source=7, timestamp=232007532, detail=1),
        ]
    )
    measured_hierarchy = hierarchy or (
        (2, 0, "master", "pointer:Virtual core pointer"),
        (3, 0, "master", "keyboard:Virtual core keyboard"),
        (4, 2, "slave", "pointer:Virtual core XTEST pointer"),
        (5, 3, "slave", "keyboard:Virtual core XTEST keyboard"),
        (7, 2, "slave", "pointer:xwayland-relative-pointer"),
        (9, 3, "slave", "keyboard:xwayland-keyboard"),
    )
    measured_profile = _xtest_profile(measured_hierarchy)
    measured_window = OwnedWindow(
        os.getpid(),
        TARGET,
        "CROWLEY INPUT CALIBRATION ONLY",
        (0, 0, 480, 240),
        object(),  # type: ignore[arg-type]
        frozenset({TARGET}),
        "/usr/bin/python3",
        "owned-target-start",
        TARGET + 1,
        (0, 0, 500, 260),
        frozenset({TARGET, TARGET + 1}),
    )
    measured_transitions = InputCalibrationWorkflow._canonical_motion_transitions(
        records,
        measured_window,
        measured_profile,
    )
    return InputCalibrationEvidence._issue(
        fingerprint="owned-native-test-fingerprint",
        display=":test",
        target_pid=os.getpid(),
        target_xid=TARGET,
        target_child_xid=TARGET,
        synthetic_key_source=5,
        synthetic_pointer_source=4,
        human_key_source=9,
        human_pointer_source=7,
        xinput_hierarchy=measured_hierarchy,
        xtest_profile=measured_profile,
        synthetic_motion_transitions=measured_transitions,
        synthetic_motion_query=(987, 595, TARGET, 988, 596, 988, 596, TARGET),
        synthetic_events=tuple(
            (record.event_class.value, record.source_device, record.detail)
            for record in records
            if record.source_device in {4, 5}
        ),
        human_events=tuple(
            (record.event_class.value, record.source_device, record.detail)
            for record in records
            if record.source_device in {7, 9}
            and record.event_class
            in {
                EventClass.KEY_PRESS,
                EventClass.KEY_RELEASE,
                EventClass.RAW_KEY_PRESS,
                EventClass.RAW_KEY_RELEASE,
                EventClass.BUTTON_PRESS,
                EventClass.BUTTON_RELEASE,
                EventClass.RAW_BUTTON_PRESS,
                EventClass.RAW_BUTTON_RELEASE,
            }
        ),
        forwarded_events=(("Motion", 7, TARGET),),
        driver_version=driver_version,
        xauthority=xauthority or str(tmp_path / "Xauthority"),
        event_proof=tuple(
            (
                record.event_class.value,
                record.master_device,
                record.source_device,
                record.detail,
                record.timestamp_ms,
                record.root_xid,
                record.event_xid,
                record.child_xid,
                record.root_xy,
                record.event_xy,
                record.modifiers,
                record.modifier_effective,
            )
            for record in records
        ),
        game_identity_fingerprint=game_identity_fingerprint,
        game_geometry=game_geometry,
        target_executable="/usr/bin/python3",
        target_process_start="owned-target-start",
        target_geometry=(0, 0, 480, 240),
        managed_frame_xid=TARGET + 1,
        managed_frame_geometry=(0, 0, 500, 260),
        target_event_xids=(TARGET, TARGET + 1),
        synthetic_modifiers=(0, 0, 0),
        synthetic_echo_proof=(
            (
                "MotionEcho",
                232007505,
                7,
                7,
                TARGET,
                (988.0, 596.0),
                (988.0, 596.0),
                232007500,
                4,
                TARGET,
            ),
        ),
        keyboard_keymap=profile_keysyms,
        keyboard_profile=tuple(
            (
                operation.operation,
                operation.payload,
                tuple(
                    (
                        step.phase,
                        step.keysym,
                        key_details[step.keysym],
                        (0, 0, 0),
                        0,
                    )
                    for step in operation.steps
                ),
            )
            for operation in profile_operations
        ),
    )


def _event(
    event_class: EventClass,
    *,
    master: int,
    source: int,
    timestamp: int,
    detail: int | None,
    child: int | None = TARGET,
    root_xy: tuple[float, float] | None = None,
    event_xy: tuple[float, float] | None = None,
    root_xid: int = 0x374,
    event_xid: int = 0x374,
    valuators: tuple[tuple[int, float, float | None], ...] = (),
) -> XI2Event:
    type_numbers = {
        EventClass.RAW_KEY_PRESS: 13,
        EventClass.KEY_PRESS: 2,
        EventClass.RAW_KEY_RELEASE: 14,
        EventClass.KEY_RELEASE: 3,
        EventClass.RAW_BUTTON_PRESS: 15,
        EventClass.BUTTON_PRESS: 4,
        EventClass.RAW_BUTTON_RELEASE: 16,
        EventClass.RAW_MOTION: 17,
        EventClass.BUTTON_RELEASE: 5,
        EventClass.MOTION: 6,
        EventClass.DEVICE_CHANGED: 1,
        EventClass.ENTER: 7,
        EventClass.LEAVE: 8,
    }
    return XI2Event(
        type_numbers[event_class],
        event_class,
        master,
        source,
        timestamp,
        detail,
        root_xid if child is not None else None,
        event_xid if child is not None else None,
        child,
        root_xy=root_xy if root_xy is not None else ((987.0, 595.0) if child is not None else None),
        event_xy=event_xy if event_xy is not None else ((987.0, 595.0) if child is not None else None),
        modifiers=(0, 0, 0) if child is not None else None,
        modifier_effective=0 if child is not None else None,
        valuators=valuators,
    )


def _render_events(events: list[XI2Event]) -> str:
    blocks: list[str] = []
    for event in events:
        lines = [f"EVENT type {event.type_number} ({event.event_class.value})"]
        lines.append(f"    device: {event.master_device} ({event.source_device})")
        lines.append(f"    time: {event.timestamp_ms}")
        if event.detail is not None:
            lines.append(f"    detail: {event.detail}")
        if event.event_class is EventClass.RAW_MOTION or (
            event.event_class is EventClass.MOTION and event.source_device == 4
        ):
            lines.append("    valuators:")
            for axis, value, raw_value in event.valuators:
                suffix = f" ({raw_value:.2f})" if raw_value is not None else ""
                lines.append(f"         {axis}: {value:.2f}{suffix}")
        if event.child_xid is not None:
            root_xy = event.root_xy or (987.0, 595.0)
            event_xy = event.event_xy or root_xy
            root_xid = event.root_xid if event.root_xid is not None else 0x374
            event_xid = event.event_xid if event.event_xid is not None else root_xid
            lines.extend(
                (
                    f"    root: {root_xy[0]:.2f}/{root_xy[1]:.2f}",
                    f"    event: {event_xy[0]:.2f}/{event_xy[1]:.2f}",
                    f"    windows: root {hex(root_xid)} event {hex(event_xid)} child {hex(event.child_xid)}",
                )
            )
        elif event.event_class is not EventClass.RAW_MOTION:
            lines.append("    valuators:")
            for axis, value, raw_value in event.valuators:
                suffix = f" ({raw_value:.2f})" if raw_value is not None else ""
                lines.append(f"         {axis}: {value:.2f}{suffix}")
        if event.modifiers is not None:
            locked, latched, base = event.modifiers
            effective = event.modifier_effective
            if effective is None:
                raise AssertionError("delivered fixture event lacks effective modifier state")
            lines.append(
                f"    modifiers: locked {locked} latched {latched} base {base} effective: {effective}"
            )
        blocks.append("\n".join(lines))
    return "\n".join(blocks) + "\n"


def test_complete_xi2_fixture_preserves_pairs_releases_transitions_and_foreign_motion() -> None:
    records = parse_xi2_records(FULL_XI2_TRACE, require_event=True)
    assert len(records) == 12
    assert [
        (record.event_class, record.master_device, record.source_device, record.detail, record.target_xid)
        for record in records
    ] == [
        (EventClass.RAW_KEY_PRESS, 3, 5, 8, None),
        (EventClass.KEY_PRESS, 5, 5, 8, TARGET),
        (EventClass.RAW_KEY_RELEASE, 3, 5, 8, None),
        (EventClass.KEY_RELEASE, 5, 5, 8, TARGET),
        (EventClass.DEVICE_CHANGED, 2, 4, None, None),
        (EventClass.ENTER, 4, 4, None, TARGET),
        (EventClass.LEAVE, 4, 4, None, TARGET),
        (EventClass.RAW_BUTTON_PRESS, 2, 4, 1, None),
        (EventClass.BUTTON_PRESS, 4, 4, 1, TARGET),
        (EventClass.RAW_BUTTON_RELEASE, 2, 4, 1, None),
        (EventClass.BUTTON_RELEASE, 4, 4, 1, TARGET),
        (EventClass.MOTION, 7, 7, 0, FOREIGN),
    ]
    assert [(record.master_device, record.source_device) for record in records[:4]] == [
        (3, 5),
        (5, 5),
        (3, 5),
        (5, 5),
    ]
    assert records[1].modifiers == (0, 0, 0)
    assert records[8].modifiers == (0, 0, 0)


def test_guardian_requires_complete_correlations_and_rejects_foreign_motion(tmp_path: Path) -> None:
    records = parse_xi2_records(FULL_XI2_TRACE, require_event=True)
    guardian = InputGuardian(tmp_path / "guardian.lock", parent_pid=os.getppid())
    try:
        generation = guardian.arm(_evidence(tmp_path))
        guardian.begin_action(
            generation,
            target_xid=TARGET,
            source_device=5,
            master_device=3,
            event_classes={
                EventClass.RAW_KEY_PRESS.value,
                EventClass.KEY_PRESS.value,
                EventClass.RAW_KEY_RELEASE.value,
                EventClass.KEY_RELEASE.value,
            },
            device_by_class={
                EventClass.RAW_KEY_PRESS.value: 3,
                EventClass.KEY_PRESS.value: 5,
                EventClass.RAW_KEY_RELEASE.value: 3,
                EventClass.KEY_RELEASE.value: 5,
            },
            detail=8,
        )
        for record in records[:4]:
            assert guardian.observe(record)
        guardian.finish_action(generation)

        guardian.begin_action(
            generation,
            target_xid=TARGET,
            source_device=4,
            master_device=2,
            event_classes={
                EventClass.DEVICE_CHANGED.value,
                EventClass.ENTER.value,
                EventClass.LEAVE.value,
                EventClass.RAW_BUTTON_PRESS.value,
                EventClass.BUTTON_PRESS.value,
                EventClass.RAW_BUTTON_RELEASE.value,
                EventClass.BUTTON_RELEASE.value,
                EventClass.MOTION.value,
            },
            device_by_class={
                EventClass.DEVICE_CHANGED.value: 2,
                EventClass.ENTER.value: 4,
                EventClass.LEAVE.value: 4,
                EventClass.RAW_BUTTON_PRESS.value: 2,
                EventClass.BUTTON_PRESS.value: 4,
                EventClass.RAW_BUTTON_RELEASE.value: 2,
                EventClass.BUTTON_RELEASE.value: 4,
                EventClass.MOTION.value: 4,
            },
            target_ancestor=lambda xid: xid == TARGET,
            detail=1,
        )
        for record in records[4:11]:
            assert guardian.observe(record), record
        assert not guardian.observe(records[11])
        assert not guardian.armed
        assert guardian.action is None
    finally:
        guardian.close()


def test_guardian_rejects_unpaired_forwarded_motion_on_owned_target(tmp_path: Path) -> None:
    """A current source-7 motion needs the current source-4 echo, not old coordinates."""

    records = parse_xi2_records(FULL_XI2_TRACE, require_event=True)
    evidence = _evidence(tmp_path)
    guardian = InputGuardian(tmp_path / "unpaired-motion.lock", parent_pid=os.getppid())
    try:
        generation = guardian.arm(evidence)
        guardian.begin_action(
            generation,
            target_xid=TARGET,
            source_device=4,
            master_device=4,
            event_classes={EventClass.MOTION.value},
            target_ancestor=lambda xid: xid == TARGET,
            expected_modifiers=(0, 0, 0),
            expected_coordinates=(988.0, 596.0),
            echo_proof=evidence.synthetic_echo_proof,
        )
        stale_owned_motion = replace(
            records[-1],
            master_device=7,
            source_device=7,
            child_xid=TARGET,
            event_xid=TARGET,
            timestamp_ms=5_000,
        )
        assert not guardian.observe(stale_owned_motion)
        assert not guardian.armed
    finally:
        guardian.close()


def test_owned_calibration_click_uses_owned_geometry_plus_local_offset(tmp_path: Path) -> None:
    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend.input_tool = fixture_input_tool(tmp_path / "tool")
    backend._measured_anchors = {}
    backend._xprop = lambda *_args: (
        f'WM_NAME(STRING) = "CROWLEY INPUT CALIBRATION ONLY"\n_NET_WM_PID(CARDINAL) = {os.getpid()}\n'
    )
    calls: list[tuple[str, int, int]] = []
    backend.synthetic_calibration = lambda xid, x, y, **_kwargs: calls.append((xid, x, y))
    driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "desktop.lock")
    target = OwnedWindow(
        os.getpid(),
        TARGET,
        OwnedGtkCalibrationWindow.TITLE,
        (41, 59, 480, 240),
        SimpleNamespace(poll=lambda: None),  # type: ignore[arg-type]
        frozenset({TARGET}),
        "/usr/bin/python3",
        "owned-target-start",
        TARGET + 1,
        (0, 0, 540, 320),
        frozenset({TARGET, TARGET + 1}),
    )
    try:
        driver.begin_calibration_operation()
        with pytest.raises(DriverError, match="exact calibration ticket"):
            driver.synthetic_target_key_click(target)
        ticket = driver.issue_calibration_ticket(target)
        driver.synthetic_target_key_click(target, calibration_ticket=ticket)
        # The harmless calibration point is the owned GTK center: local
        # (240, 120), translated through the measured desktop geometry.
        assert calls == [(hex(TARGET), 281, 179)]
    finally:
        driver.close()


def test_synthetic_calibration_binds_owned_origin_and_exact_postquery(tmp_path: Path) -> None:
    """The native producer must query ownership before and after its move."""

    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend._last_synthetic_motion_query = None
    backend._calibration_focus_ticket = None
    calls: list[list[str]] = []
    pointer_reads = iter(((100, 100, TARGET), (120, 120, TARGET)))

    def run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(list(args))
        if args[:2] == ["xdotool", "getwindowgeometry"]:
            return subprocess.CompletedProcess(
                args, 0, "WINDOW=0x600119\nX=40\nY=60\nWIDTH=240\nHEIGHT=160\nSCREEN=0\n", ""
            )
        if args == ["xdotool", "getwindowfocus"]:
            return subprocess.CompletedProcess(args, 0, "6291737\n", "")
        return subprocess.CompletedProcess(args, 0, "", "")

    backend._run = run  # type: ignore[method-assign]
    backend.pointer_position = lambda **_kwargs: next(pointer_reads)  # type: ignore[method-assign]
    backend.synthetic_calibration(
        hex(TARGET),
        120,
        120,
        calibration_ticket=SimpleNamespace(epoch=1),
    )
    assert backend._last_synthetic_motion_query == (100, 100, TARGET, 120, 120, 120, 120, TARGET)
    assert [args[1] for args in calls if len(args) > 1] == [
        "getwindowgeometry",
        "windowactivate",
        "getwindowfocus",
        "key",
        "mousemove",
        "click",
    ]


def test_synthetic_calibration_refuses_outside_origin_before_motion(tmp_path: Path) -> None:
    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend._last_synthetic_motion_query = None
    backend._calibration_focus_ticket = None
    calls: list[list[str]] = []

    def run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(list(args))
        if args[:2] == ["xdotool", "getwindowgeometry"]:
            return subprocess.CompletedProcess(
                args, 0, "WINDOW=0x600119\nX=40\nY=60\nWIDTH=240\nHEIGHT=160\nSCREEN=0\n", ""
            )
        if args == ["xdotool", "getwindowfocus"]:
            return subprocess.CompletedProcess(args, 0, "6291737\n", "")
        return subprocess.CompletedProcess(args, 0, "", "")

    backend._run = run  # type: ignore[method-assign]
    backend.pointer_position = lambda **_kwargs: (100, 100, 0x700101)  # type: ignore[method-assign]
    with pytest.raises(DriverError, match="origin is outside"):
        backend.synthetic_calibration(
            hex(TARGET),
            120,
            120,
            calibration_ticket=SimpleNamespace(epoch=1),
        )
    assert all(args[1] not in {"key", "mousemove", "click"} for args in calls if len(args) > 1)


def test_synthetic_calibration_refuses_zero_displacement_before_f13_or_move(tmp_path: Path) -> None:
    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend._last_synthetic_motion_query = None
    calls: list[list[str]] = []

    def run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(list(args))
        if args[:2] == ["xdotool", "getwindowgeometry"]:
            return subprocess.CompletedProcess(
                args, 0, "WINDOW=0x600119\nX=40\nY=60\nWIDTH=240\nHEIGHT=160\nSCREEN=0\n", ""
            )
        if args == ["xdotool", "getwindowfocus"]:
            return subprocess.CompletedProcess(args, 0, "6291737\n", "")
        return subprocess.CompletedProcess(args, 0, "", "")

    backend._run = run  # type: ignore[method-assign]
    backend.pointer_position = lambda **_kwargs: (120, 120, TARGET)  # type: ignore[method-assign]
    with pytest.raises(DriverError, match="nonzero measured displacement"):
        backend.synthetic_calibration(
            hex(TARGET),
            120,
            120,
            calibration_ticket=SimpleNamespace(epoch=1),
        )
    assert all(args[1] not in {"key", "mousemove", "click"} for args in calls if len(args) > 1)


def test_calibration_gate_health_is_rechecked_after_registration_ack(tmp_path: Path) -> None:
    """A watchdog dying after group ACK cannot release the GTK helper gate."""

    profile = DriverProfile(display=":gtk-watchdog-race", xauthority=str(tmp_path / "Xauthority"))
    driver = DesktopDriver(
        profile=profile,
        backend=RecordingBackend(),
        lease_path=tmp_path / "gtk-watchdog-race.lock",
    )
    release_calls: list[bool] = []
    original_register = driver.guardian.register_calibration_bootstrap_process

    def register_then_reap_watchdog(pgid: int, epoch: int) -> None:
        original_register(pgid, epoch)
        watchdog = driver.guardian._watchdog_process
        assert watchdog is not None
        watchdog.terminate()
        watchdog.join(timeout=2)
        assert not watchdog.is_alive()

    driver.guardian.register_calibration_bootstrap_process = register_then_reap_watchdog
    try:
        driver.begin_calibration_operation()
        with pytest.raises(DriverError, match="startup admission failed"):
            driver.admit_calibration_target_process(500_100, lambda: release_calls.append(True))
        assert not release_calls
        assert not driver.guardian.active_process_groups
    finally:
        driver.close()


def test_calibration_admission_records_unregister_failure(tmp_path: Path) -> None:
    driver = DesktopDriver(
        profile=DriverProfile(display=":gtk-unregister-note", xauthority=str(tmp_path / "Xauthority")),
        backend=RecordingBackend(),
        lease_path=tmp_path / "gtk-unregister-note.lock",
    )
    original_unregister = driver.guardian.unregister_process_group

    def failing_unregister(_pgid: int) -> None:
        raise RuntimeError("synthetic unregister failure")

    driver.guardian.unregister_process_group = failing_unregister
    try:
        driver.begin_calibration_operation()
        with pytest.raises(DriverError, match="startup admission failed") as failure:
            driver.admit_calibration_target_process(
                500_200, lambda: (_ for _ in ()).throw(RuntimeError("gate"))
            )
        assert any("unregister failed" in note for note in failure.value.__notes__)
    finally:
        driver.guardian.unregister_process_group = original_unregister
        original_unregister(500_200)
        driver.close()


def test_failed_gtk_create_unregisters_bootstrap_for_same_driver_retry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A post-admission verification failure must leave calibration retryable."""

    import crowley.session.calibration as calibration_module

    profile = DriverProfile(display=":gtk-retry", xauthority=str(tmp_path / "Xauthority"))
    driver = DesktopDriver(
        profile=profile,
        backend=RecordingBackend(),
        lease_path=tmp_path / "gtk-retry.lock",
    )
    processes: list[object] = []
    lifecycle: list[str] = []
    verify_calls = 0

    class FakeProcess:
        def __init__(self, pid: int, stdout: io.TextIOBase, gate_reader: int) -> None:
            self.pid = pid
            self.stdout = stdout
            self.stdin = io.StringIO()
            self.returncode: int | None = None
            self._gate_reader = gate_reader

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            lifecycle.append("terminate")
            if self._gate_reader >= 0:
                os.close(self._gate_reader)
                self._gate_reader = -1
            self.returncode = -15

        def kill(self) -> None:
            lifecycle.append("kill")
            if self._gate_reader >= 0:
                os.close(self._gate_reader)
                self._gate_reader = -1
            self.returncode = -9

        def wait(self, timeout: float = 2.0) -> int:
            del timeout
            lifecycle.append("wait")
            if self.returncode is None:
                self.returncode = 0
            return self.returncode

    def fake_popen(_args: list[str], **_kwargs: object) -> FakeProcess:
        pid = 500_000 + len(processes)
        read_fd, write_fd = os.pipe()
        os.write(write_fd, (json.dumps({"pid": pid, "xid": TARGET}) + "\n").encode())
        os.close(write_fd)
        wrapper_index = _args.index(_EXEC_ADMISSION_WRAPPER)
        gate_reader = os.dup(int(_args[wrapper_index + 1]))
        process = FakeProcess(pid, os.fdopen(read_fd, "r", encoding="utf-8"), gate_reader)
        processes.append(process)
        return process

    def verify(
        _target: OwnedGtkCalibrationWindow,
        pid: int,
        xid: int,
        process: object,
        **_kwargs: object,
    ) -> object:
        del pid, xid
        nonlocal verify_calls
        verify_calls += 1
        if verify_calls == 1:
            raise CalibrationError("synthetic GTK verification failure")
        return SimpleNamespace(pid=process.pid, xid=TARGET, process=process)

    monkeypatch.setattr(calibration_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(OwnedGtkCalibrationWindow, "_verify", verify)
    original_unregister = driver.guardian.unregister_process_group

    def record_unregister(pgid: int) -> None:
        lifecycle.append("unregister")
        original_unregister(pgid)

    driver.guardian.unregister_process_group = record_unregister
    try:
        driver.begin_calibration_operation()
        failed = OwnedGtkCalibrationWindow(
            display=profile.display,
            xauthority=profile.xauthority,
            python_executable=sys.executable,
        )
        with pytest.raises(CalibrationError, match="synthetic GTK verification failure"):
            failed.create(startup_admission=driver.admit_calibration_target_process)
        assert lifecycle[:3] == ["terminate", "wait", "unregister"]
        assert not driver.guardian.active_process_groups
        assert not driver._calibration_bootstrap_process_groups

        # This is the liveness contract: a transient target verification
        # failure must not require closing the driver before retrying.
        driver.begin_calibration_operation()
        retry = OwnedGtkCalibrationWindow(
            display=profile.display,
            xauthority=profile.xauthority,
            python_executable=sys.executable,
        )
        window = retry.create(startup_admission=driver.admit_calibration_target_process)
        assert window.pid == processes[-1].pid
        assert driver.guardian.active_process_groups == frozenset({processes[-1].pid})
    finally:
        for process in processes:
            process.terminate()  # type: ignore[attr-defined]
            process.stdout.close()  # type: ignore[attr-defined]
        driver.close()


def test_gtk_create_waits_for_reparented_readiness_without_respawn(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Identity publication is not readiness, and one child owns the retry loop."""

    import crowley.session.calibration as calibration_module

    processes: list[object] = []
    verify_deadlines: list[float] = []
    releases: list[bool] = []

    class FakeProcess:
        def __init__(self, pid: int, stdout: io.TextIOBase, gate_reader: int) -> None:
            self.pid = pid
            self.stdout = stdout
            self.stdin = io.StringIO()
            self.returncode: int | None = None
            self.gate_reader = gate_reader

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            if self.gate_reader >= 0:
                os.close(self.gate_reader)
                self.gate_reader = -1
            self.returncode = -15

        def kill(self) -> None:
            self.terminate()
            self.returncode = -9

        def wait(self, timeout: float = 2.0) -> int:
            del timeout
            if self.returncode is None:
                self.returncode = 0
            return self.returncode

    def fake_popen(argv: list[str], **_kwargs: object) -> FakeProcess:
        pid = 601_000 + len(processes)
        read_fd, write_fd = os.pipe()
        os.write(write_fd, (json.dumps({"pid": pid, "xid": TARGET}) + "\n").encode())
        os.close(write_fd)
        wrapper_index = argv.index(_EXEC_ADMISSION_WRAPPER)
        gate_reader = os.dup(int(argv[wrapper_index + 1]))
        process = FakeProcess(pid, os.fdopen(read_fd, "r", encoding="utf-8"), gate_reader)
        processes.append(process)
        return process

    def verify(
        _target: OwnedGtkCalibrationWindow,
        pid: int,
        xid: int,
        process: object,
        **kwargs: object,
    ) -> object:
        assert kwargs["startup_readiness"] is True
        deadline = kwargs["deadline"]
        assert isinstance(deadline, float)
        verify_deadlines.append(deadline)
        if len(verify_deadlines) == 1:
            raise calibration_module._GtkStartupPending("Mutter has not reparented the client")
        return SimpleNamespace(pid=pid, xid=xid, process=process)

    monkeypatch.setattr(calibration_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(OwnedGtkCalibrationWindow, "_verify", verify)
    target = OwnedGtkCalibrationWindow(
        display=":gtk-readiness",
        xauthority=str(tmp_path / "Xauthority"),
        python_executable=sys.executable,
    )

    def admit(_pid: int, release: Callable[[], None]) -> None:
        releases.append(True)
        release()

    try:
        window = target.create(timeout=0.2, startup_admission=admit)
        assert window.pid == 601_000
        assert len(processes) == 1
        assert len(verify_deadlines) >= 2
        assert len(set(verify_deadlines)) == 1
        assert releases == [True]
    finally:
        if target.window is not None:
            target.close()
        for process in processes:
            process.stdout.close()  # type: ignore[attr-defined]


def test_gtk_create_real_verifier_replays_startup_states_and_command_budget(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """One admitted child crosses real pending states before one ready certificate."""

    import crowley.session.calibration as calibration_module

    pid = 604_000
    frame = 0x600192
    helper = 0x600193
    child = 0x600121
    frame_pid = 5717
    clock = [100.0]
    attempts = 0
    command_observations: list[tuple[float, float]] = []
    processes: list[object] = []
    admissions: list[int] = []
    registration_cleanups: list[int] = []

    class FakeProcess:
        def __init__(self, stdout: io.TextIOBase, gate_reader: int) -> None:
            self.pid = pid
            self.stdout = stdout
            self.stdin = io.StringIO()
            self.returncode: int | None = None
            self.gate_reader = gate_reader

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            if self.gate_reader >= 0:
                os.close(self.gate_reader)
                self.gate_reader = -1
            self.returncode = -15

        def kill(self) -> None:
            self.terminate()
            self.returncode = -9

        def wait(self, timeout: float = 2.0) -> int:
            del timeout
            if self.returncode is None:
                self.returncode = 0
            return self.returncode

    def fake_popen(argv: list[str], **_kwargs: object) -> FakeProcess:
        read_fd, write_fd = os.pipe()
        os.write(write_fd, (json.dumps({"pid": pid, "xid": TARGET}) + "\n").encode())
        os.close(write_fd)
        wrapper_index = argv.index(_EXEC_ADMISSION_WRAPPER)
        process = FakeProcess(os.fdopen(read_fd, "r", encoding="utf-8"), os.dup(int(argv[wrapper_index + 1])))
        processes.append(process)
        return process

    def stats(x: int, y: int, width: int, height: int, *, map_state: str | None = None) -> str:
        result = (
            f"Absolute upper-left X: {x}\nAbsolute upper-left Y: {y}\n"
            f"Width: {width}\nHeight: {height}\nDepth: 24\nBorder width: 0\nClass: InputOutput\n"
        )
        if map_state is not None:
            result += f"Map State: {map_state}\n"
        return result

    ready_command = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=frame,
        helper=helper,
        child=child,
        frame_pid=frame_pid,
    )

    def command(args: list[str], **kwargs: object) -> str:
        nonlocal attempts
        command_observations.append((clock[0], float(kwargs["timeout"])))
        clock[0] += 0.005
        if args[:2] == ["wmctrl", "-lp"]:
            attempts += 1
            return f"{hex(TARGET)} -1 {pid} host CROWLEY INPUT CALIBRATION ONLY\n"
        phase = attempts - 1
        if phase == 0 and args == ["xprop", "-id", hex(TARGET)]:
            return f'WM_NAME(STRING) = "CROWLEY INPUT CALIBRATION ONLY"\n_NET_WM_PID(CARDINAL) = {pid}\n'
        if phase < 4 and args == ["xprop", "-id", hex(TARGET)]:
            return (
                f'WM_NAME(STRING) = "CROWLEY INPUT CALIBRATION ONLY"\n'
                f"_NET_WM_PID(CARDINAL) = {pid}\n"
                "_NET_FRAME_EXTENTS(CARDINAL) = 5, 31, 5, 38\n"
            )
        if phase < 4 and args == ["xwininfo", "-id", hex(TARGET), "-stats"]:
            return stats(
                753,
                456,
                480,
                240,
                map_state="IsUnMapped" if phase < 2 else "IsViewable",
            )
        if phase == 2 and args == ["xwininfo", "-root", "-tree"]:
            return (
                "xwininfo: Window id: 0x374 (the root window)\n"
                f'  {hex(TARGET)} "CROWLEY INPUT CALIBRATION ONLY": ("-c" "-c") '
                "480x240+753+456  +753+456\n"
                '  0x700001 "CROWLEY INPUT CALIBRATION ONLY": ("-c" "-c") '
                "1x1+1+1  +1+1\n"
            )
        if phase == 3 and args == ["xwininfo", "-root", "-tree"]:
            return (
                "xwininfo: Window id: 0x374 (the root window)\n"
                f'  {hex(frame)} "CROWLEY INPUT CALIBRATION ONLY": '
                f'("mutter-x11-frames" "mutter-x11-frames") 602x401+692+362  +692+362\n'
                f'    {hex(TARGET)} "CROWLEY INPUT CALIBRATION ONLY": ("-c" "-c") '
                "480x240+61+94  +753+456\n"
                "    0x700001 (has no name): () 1x1+-1+-1  +752+455\n"
            )
        if phase == 3 and args == ["xprop", "-id", hex(frame)]:
            return (
                f"_MUTTER_FRAME_FOR(WINDOW): window id # {hex(TARGET)}\n"
                f"_NET_WM_PID(CARDINAL) = {frame_pid}\n"
                'WM_CLASS(STRING) = "mutter-x11-frames", "mutter-x11-frames"\n'
            )
        return ready_command(args, **kwargs)

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == frame_pid:
            return "/usr/libexec/mutter-x11-frames", "frame-start", "mutter-x11-fram"
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        calibration_module.time, "sleep", lambda duration: clock.__setitem__(0, clock[0] + duration)
    )
    monkeypatch.setattr(calibration_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(
        display=":gtk-real-verifier",
        xauthority=str(tmp_path / "Xauthority"),
        python_executable=sys.executable,
        command=command,
    )

    def admit(_pid: int, release: Callable[[], None]) -> Callable[[], None]:
        admissions.append(1)
        release()

        def cleanup() -> None:
            registration_cleanups.append(1)

        return cleanup

    initial_clock = clock[0]
    window = target.create(timeout=1.0, startup_admission=admit)
    try:
        assert attempts == 5
        assert len(processes) == 1
        assert len(command_observations) > 8
        assert admissions == [1]
        assert registration_cleanups == []
        assert all(
            timeout == pytest.approx(initial_clock + 1.0 - observed_clock)
            for observed_clock, timeout in command_observations
        )
        assert all(
            left[1] > right[1] > 0
            for left, right in zip(command_observations, command_observations[1:], strict=False)
        )
        assert window.allowed_event_target_xids == frozenset({frame, TARGET, child})
    finally:
        target.close()
        processes[0].stdout.close()  # type: ignore[attr-defined]


def test_gtk_create_readiness_deadline_is_shrinking_and_reaps_pending_child(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A never-ready client times out once and cannot leak or respawn a child."""

    import crowley.session.calibration as calibration_module

    processes: list[object] = []
    verify_deadlines: list[float] = []
    lifecycle: list[str] = []
    registration_cleanup_calls: list[int] = []

    class FakeProcess:
        def __init__(self, pid: int, stdout: io.TextIOBase, gate_reader: int) -> None:
            self.pid = pid
            self.stdout = stdout
            self.stdin = io.StringIO()
            self.returncode: int | None = None
            self.gate_reader = gate_reader

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            lifecycle.append("terminate")
            if self.gate_reader >= 0:
                os.close(self.gate_reader)
                self.gate_reader = -1
            self.returncode = -15

        def kill(self) -> None:
            lifecycle.append("kill")
            self.terminate()
            self.returncode = -9

        def wait(self, timeout: float = 2.0) -> int:
            del timeout
            lifecycle.append("wait")
            if self.returncode is None:
                self.returncode = 0
            return self.returncode

    def fake_popen(argv: list[str], **_kwargs: object) -> FakeProcess:
        pid = 602_000 + len(processes)
        read_fd, write_fd = os.pipe()
        os.write(write_fd, (json.dumps({"pid": pid, "xid": TARGET}) + "\n").encode())
        os.close(write_fd)
        wrapper_index = argv.index(_EXEC_ADMISSION_WRAPPER)
        gate_reader = os.dup(int(argv[wrapper_index + 1]))
        process = FakeProcess(pid, os.fdopen(read_fd, "r", encoding="utf-8"), gate_reader)
        processes.append(process)
        return process

    def verify(
        _target: OwnedGtkCalibrationWindow,
        _pid: int,
        _xid: int,
        _process: object,
        **kwargs: object,
    ) -> object:
        deadline = kwargs["deadline"]
        assert isinstance(deadline, float)
        verify_deadlines.append(deadline)
        raise calibration_module._GtkStartupPending("GTK frame remains pending")

    monkeypatch.setattr(calibration_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(OwnedGtkCalibrationWindow, "_verify", verify)
    target = OwnedGtkCalibrationWindow(
        display=":gtk-readiness-timeout",
        xauthority=str(tmp_path / "Xauthority"),
        python_executable=sys.executable,
    )

    def admit(_pid: int, release: Callable[[], None]) -> Callable[[], None]:
        release()

        def cleanup() -> None:
            registration_cleanup_calls.append(1)

        return cleanup

    with pytest.raises(CalibrationError, match="startup deadline"):
        target.create(timeout=0.025, startup_admission=admit)
    assert len(processes) == 1
    assert verify_deadlines
    assert len(set(verify_deadlines)) == 1
    assert lifecycle[:2] == ["terminate", "wait"]
    assert registration_cleanup_calls == [1]
    assert processes[0].poll() is not None
    processes[0].stdout.close()  # type: ignore[attr-defined]


def test_gtk_create_deadline_includes_startup_admission(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Admission consumes the one create budget before any certificate query."""

    import crowley.session.calibration as calibration_module

    clock = [100.0]
    verify_calls = 0
    processes: list[object] = []

    class FakeProcess:
        def __init__(self, pid: int, stdout: io.TextIOBase, gate_reader: int) -> None:
            self.pid = pid
            self.stdout = stdout
            self.stdin = io.StringIO()
            self.returncode: int | None = None
            self.gate_reader = gate_reader

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            if self.gate_reader >= 0:
                os.close(self.gate_reader)
                self.gate_reader = -1
            self.returncode = -15

        def kill(self) -> None:
            self.terminate()
            self.returncode = -9

        def wait(self, timeout: float = 2.0) -> int:
            del timeout
            if self.returncode is None:
                self.returncode = 0
            return self.returncode

    def fake_popen(argv: list[str], **_kwargs: object) -> FakeProcess:
        pid = 603_500
        read_fd, write_fd = os.pipe()
        os.write(write_fd, (json.dumps({"pid": pid, "xid": TARGET}) + "\n").encode())
        os.close(write_fd)
        wrapper_index = argv.index(_EXEC_ADMISSION_WRAPPER)
        process = FakeProcess(
            pid,
            os.fdopen(read_fd, "r", encoding="utf-8"),
            os.dup(int(argv[wrapper_index + 1])),
        )
        processes.append(process)
        return process

    def verify(*_args: object, **_kwargs: object) -> object:
        nonlocal verify_calls
        verify_calls += 1
        return SimpleNamespace(pid=603_500, xid=TARGET, process=processes[0])

    monkeypatch.setattr(calibration_module.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(calibration_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(OwnedGtkCalibrationWindow, "_verify", verify)
    target = OwnedGtkCalibrationWindow(
        display=":gtk-admission-deadline",
        xauthority=str(tmp_path / "Xauthority"),
        python_executable=sys.executable,
    )

    def admit(_pid: int, release: Callable[[], None]) -> None:
        clock[0] += 0.2
        release()

    with pytest.raises(CalibrationError, match="startup deadline"):
        target.create(timeout=0.1, startup_admission=admit)
    assert verify_calls == 0
    assert processes[0].poll() is not None
    processes[0].stdout.close()  # type: ignore[attr-defined]


def test_gtk_create_late_final_certificate_reaps_and_unregisters(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A certificate that arrives after the absolute deadline is not retained."""

    import crowley.session.calibration as calibration_module

    clock = [300.0]
    processes: list[object] = []
    cleanup_calls: list[int] = []

    class FakeProcess:
        def __init__(self, stdout: io.TextIOBase, gate_reader: int) -> None:
            self.pid = 603_600
            self.stdout = stdout
            self.stdin = io.StringIO()
            self.returncode: int | None = None
            self.gate_reader = gate_reader

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            if self.gate_reader >= 0:
                os.close(self.gate_reader)
                self.gate_reader = -1
            self.returncode = -15

        def kill(self) -> None:
            self.terminate()
            self.returncode = -9

        def wait(self, timeout: float = 2.0) -> int:
            del timeout
            if self.returncode is None:
                self.returncode = 0
            return self.returncode

    def fake_popen(argv: list[str], **_kwargs: object) -> FakeProcess:
        read_fd, write_fd = os.pipe()
        os.write(write_fd, (json.dumps({"pid": 603_600, "xid": TARGET}) + "\n").encode())
        os.close(write_fd)
        wrapper_index = argv.index(_EXEC_ADMISSION_WRAPPER)
        process = FakeProcess(os.fdopen(read_fd, "r", encoding="utf-8"), os.dup(int(argv[wrapper_index + 1])))
        processes.append(process)
        return process

    def verify(*_args: object, **_kwargs: object) -> object:
        clock[0] += 0.2
        return SimpleNamespace(pid=603_600, xid=TARGET, process=processes[0])

    monkeypatch.setattr(calibration_module.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(calibration_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(OwnedGtkCalibrationWindow, "_verify", verify)
    target = OwnedGtkCalibrationWindow(
        display=":gtk-late-certificate",
        xauthority=str(tmp_path / "Xauthority"),
        python_executable=sys.executable,
    )

    def admit(_pid: int, release: Callable[[], None]) -> Callable[[], None]:
        release()

        def cleanup() -> None:
            cleanup_calls.append(1)

        return cleanup

    with pytest.raises(CalibrationError, match="startup deadline"):
        target.create(timeout=0.1, startup_admission=admit)
    assert processes[0].poll() is not None
    assert cleanup_calls == [1]
    processes[0].stdout.close()  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("writer_open", "message"),
    [(True, "identity was incomplete"), (False, "identity channel closed before identity")],
)
def test_gtk_create_partial_identity_does_not_call_blocking_readline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, writer_open: bool, message: str
) -> None:
    """A partial identity is bounded whether its writer remains open or closes."""

    import crowley.session.calibration as calibration_module

    clock = [200.0]
    select_calls = 0
    processes: list[object] = []
    lifecycle: list[str] = []
    registration_cleanup_calls: list[int] = []

    class PartialStdout:
        def __init__(self, read_fd: int) -> None:
            self.read_fd = read_fd

        def fileno(self) -> int:
            return self.read_fd

        def readline(self) -> str:
            raise AssertionError("blocking readline called for partial identity")

        def close(self) -> None:
            os.close(self.read_fd)

    class FakeProcess:
        def __init__(self, pid: int, stdout: PartialStdout, gate_reader: int) -> None:
            self.pid = pid
            self.stdout = stdout
            self.stdin = io.StringIO()
            self.returncode: int | None = None
            self.gate_reader = gate_reader

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            lifecycle.append("terminate")
            if self.gate_reader >= 0:
                os.close(self.gate_reader)
                self.gate_reader = -1
            self.returncode = -15

        def kill(self) -> None:
            self.terminate()
            self.returncode = -9

        def wait(self, timeout: float = 2.0) -> int:
            del timeout
            lifecycle.append("wait")
            if self.returncode is None:
                self.returncode = 0
            return self.returncode

    def fake_popen(argv: list[str], **_kwargs: object) -> FakeProcess:
        pid = 603_501
        read_fd, write_fd = os.pipe()
        os.write(write_fd, b'{"pid": 603501')
        if not writer_open:
            os.close(write_fd)
        wrapper_index = argv.index(_EXEC_ADMISSION_WRAPPER)
        process = FakeProcess(
            pid,
            PartialStdout(read_fd),
            os.dup(int(argv[wrapper_index + 1])),
        )
        processes.append(process)
        if writer_open:
            # Keep the writer open: this variant is specifically a partial live line.
            process.writer = write_fd  # type: ignore[attr-defined]
        return process

    def fake_select(_read: object, _write: object, _error: object, _timeout: float):
        nonlocal select_calls
        select_calls += 1
        if select_calls == 1:
            return (_read, [], [])
        if not writer_open:
            return (_read, [], [])
        clock[0] += 0.2
        return ([], [], [])

    monkeypatch.setattr(calibration_module.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(calibration_module.select, "select", fake_select)
    monkeypatch.setattr(calibration_module.subprocess, "Popen", fake_popen)
    target = OwnedGtkCalibrationWindow(
        display=":gtk-partial-identity",
        xauthority=str(tmp_path / "Xauthority"),
        python_executable=sys.executable,
    )

    def admit(_pid: int, release: Callable[[], None]) -> Callable[[], None]:
        release()

        def cleanup() -> None:
            registration_cleanup_calls.append(1)

        return cleanup

    try:
        with pytest.raises(CalibrationError, match=rf"^GTK calibration {re.escape(message)}$"):
            target.create(timeout=0.1, startup_admission=admit)
        assert lifecycle == ["terminate", "wait"]
        assert registration_cleanup_calls == [1]
        assert processes[0].poll() is not None
    finally:
        if processes:
            if writer_open:
                os.close(processes[0].writer)  # type: ignore[attr-defined]
            processes[0].stdout.close()  # type: ignore[attr-defined]


def test_gtk_startup_rejects_wrong_present_identity_with_missing_companion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A wrong present WM_NAME is hard failure even when WM_PID is absent."""

    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    base = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
    )

    def command(args: list[str], **kwargs: object) -> str:
        if args == ["xprop", "-id", hex(TARGET)]:
            return 'WM_NAME(STRING) = "WRONG TITLE"\n'
        return base(args, **kwargs)

    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="property|properties") as failure:
        target._verify(pid, TARGET, object(), startup_readiness=True)  # type: ignore[arg-type]
    assert not isinstance(failure.value, calibration_module._GtkStartupPending)


def test_gtk_startup_rejects_duplicate_present_property_with_missing_companion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A duplicate present WM_NAME is hard failure even when WM_PID is absent."""

    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    base = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
    )

    def command(args: list[str], **kwargs: object) -> str:
        if args == ["xprop", "-id", hex(TARGET)]:
            return (
                'WM_NAME(STRING) = "CROWLEY INPUT CALIBRATION ONLY"\n'
                'WM_NAME(STRING) = "CROWLEY INPUT CALIBRATION ONLY"\n'
            )
        return base(args, **kwargs)

    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="property|properties") as failure:
        target._verify(pid, TARGET, object(), startup_readiness=True)  # type: ignore[arg-type]
    assert not isinstance(failure.value, calibration_module._GtkStartupPending)


def test_gtk_startup_rejects_wrong_present_wmctrl_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A same-XID row with a different PID cannot become a pending absence."""

    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    base = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
    )

    def command(args: list[str], **kwargs: object) -> str:
        if args[:2] == ["wmctrl", "-lp"]:
            return f"{hex(TARGET)} -1 {pid + 1} host CROWLEY INPUT CALIBRATION ONLY\n"
        return base(args, **kwargs)

    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="title/PID") as failure:
        target._verify(pid, TARGET, object(), startup_readiness=True)  # type: ignore[arg-type]
    assert not isinstance(failure.value, calibration_module._GtkStartupPending)


def test_gtk_startup_rejects_second_same_pid_title_wmctrl_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A second same-owner title cannot be discarded as an unrelated XID."""

    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    base = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
    )

    def command(args: list[str], **kwargs: object) -> str:
        if args[:2] == ["wmctrl", "-lp"]:
            return (
                f"{hex(TARGET)} -1 {pid} host CROWLEY INPUT CALIBRATION ONLY\n"
                f"0x600194 -1 {pid} host CROWLEY INPUT CALIBRATION ONLY\n"
            )
        return base(args, **kwargs)

    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="title/PID") as failure:
        target._verify(pid, TARGET, object(), startup_readiness=True)  # type: ignore[arg-type]
    assert not isinstance(failure.value, calibration_module._GtkStartupPending)


def test_gtk_startup_rejects_alternate_only_same_pid_title_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An alternate-only same-owner row is contradictory, not initial absence."""

    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    base = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
    )

    def command(args: list[str], **kwargs: object) -> str:
        if args[:2] == ["wmctrl", "-lp"]:
            return f"0x600194 -1 {pid} host CROWLEY INPUT CALIBRATION ONLY\n"
        return base(args, **kwargs)

    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="title/PID") as failure:
        target._verify(pid, TARGET, object(), startup_readiness=True)  # type: ignore[arg-type]
    assert not isinstance(failure.value, calibration_module._GtkStartupPending)


def test_gtk_startup_rejects_unavailable_published_frame_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A published frame PID with unavailable /proc identity is never pending."""

    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    frame_pid = 5717
    command = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
    )

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == frame_pid:
            raise CalibrationError("identity unavailable")
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="frame process identity is unavailable") as failure:
        target._verify(pid, TARGET, object(), startup_readiness=True)  # type: ignore[arg-type]
    assert not isinstance(failure.value, calibration_module._GtkStartupPending)


def test_gtk_startup_rejects_unavailable_frame_pid_with_missing_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A published frame PID is hard-invalid even while another property is absent."""

    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    frame_pid = 5717
    frame = 0x600192
    base = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=frame,
        helper=0x600193,
        child=0x600121,
        frame_props=(
            f"_MUTTER_FRAME_FOR(WINDOW): window id # {hex(TARGET)}\n"
            f"_NET_WM_PID(CARDINAL) = {frame_pid}\n"
            'WM_CLASS(STRING) = "mutter-x11-frames", "mutter-x11-frames"\n'
        ),
    )

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == frame_pid:
            raise CalibrationError("identity unavailable")
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=base)
    with pytest.raises(CalibrationError, match="frame process identity is unavailable") as failure:
        target._verify(pid, TARGET, object(), startup_readiness=True)  # type: ignore[arg-type]
    assert not isinstance(failure.value, calibration_module._GtkStartupPending)


def test_gtk_startup_rejects_unavailable_client_identity_with_missing_frame_property(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Published client identity is hard-invalid before frame readiness can pend."""

    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    frame_pid = 5717
    command = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
        frame_props=(
            f"_MUTTER_FRAME_FOR(WINDOW): window id # {hex(TARGET)}\n"
            f"_NET_WM_PID(CARDINAL) = {frame_pid}\n"
            'WM_CLASS(STRING) = "mutter-x11-frames", "mutter-x11-frames"\n'
        ),
    )

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            raise CalibrationError("identity unavailable")
        if process_pid == frame_pid:
            return "/usr/libexec/mutter-x11-frames", "frame-start", "mutter-x11-fram"
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="owned GTK process identity is unavailable") as failure:
        target._verify(pid, TARGET, object(), startup_readiness=True)  # type: ignore[arg-type]
    assert not isinstance(failure.value, calibration_module._GtkStartupPending)


def test_gtk_startup_rejects_malformed_present_extents_with_missing_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed extents are hard failure even while map state is absent."""

    pid = os.getpid()
    base = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
    )

    def command(args: list[str], **kwargs: object) -> str:
        if args == ["xprop", "-id", hex(TARGET)]:
            return (
                f'WM_NAME(STRING) = "CROWLEY INPUT CALIBRATION ONLY"\n'
                f"_NET_WM_PID(CARDINAL) = {pid}\n"
                "_NET_FRAME_EXTENTS(CARDINAL) = 5, malformed, 5, 38\n"
            )
        if args == ["xwininfo", "-id", hex(TARGET), "-stats"]:
            return "Absolute upper-left X: 753\nAbsolute upper-left Y: 456\nWidth: 480\nHeight: 240\n"
        return base(args, **kwargs)

    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    import crowley.session.calibration as calibration_module

    with pytest.raises(CalibrationError, match="frame extents") as failure:
        target._verify(pid, TARGET, object(), startup_readiness=True)  # type: ignore[arg-type]
    assert not isinstance(failure.value, calibration_module._GtkStartupPending)


def test_gtk_startup_rejects_extra_child_before_missing_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unexpected frame child is contradictory even if the advertised helper is absent."""

    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    command = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
        advertised_helper=0x600194,
        extra_frame_child=FOREIGN,
    )
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="children") as failure:
        target._verify(pid, TARGET, object(), startup_readiness=True)  # type: ignore[arg-type]
    assert not isinstance(failure.value, calibration_module._GtkStartupPending)


def test_gtk_startup_rejects_multiple_frame_children_before_missing_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two non-client frame children are contradictory before helper publication."""

    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    frame_pid = 5717
    command = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
        extra_frame_child=FOREIGN,
        frame_props=(
            f"_MUTTER_FRAME_FOR(WINDOW): window id # {hex(TARGET)}\n"
            f"_NET_WM_PID(CARDINAL) = {frame_pid}\n"
            'WM_CLASS(STRING) = "mutter-x11-frames", "mutter-x11-frames"\n'
        ),
    )

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == frame_pid:
            return "/usr/libexec/mutter-x11-frames", "frame-start", "mutter-x11-fram"
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="children") as failure:
        target._verify(pid, TARGET, object(), startup_readiness=True)  # type: ignore[arg-type]
    assert not isinstance(failure.value, calibration_module._GtkStartupPending)


def test_gtk_startup_rejects_known_unexpected_child_before_missing_frame_property(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A published helper plus one wrong child is hard even with another property pending."""

    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    frame = 0x600192
    helper = 0x600193
    frame_pid = 5717
    frame_props = (
        f"_MUTTER_FRAME_FOR(WINDOW): window id # {hex(TARGET)}\n"
        f"_NET_WM_USER_TIME_WINDOW(WINDOW): window id # {hex(helper)}\n"
        f"_NET_WM_PID(CARDINAL) = {frame_pid}\n"
        # Deliberately omit WM_CLASS while the published helper and wrong child
        # make the tree contradiction independently conclusive.
    )
    base = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=frame,
        helper=helper,
        child=0x600121,
        extra_frame_child=FOREIGN,
        frame_props=frame_props,
    )

    def command(args: list[str], **kwargs: object) -> str:
        if args == ["xwininfo", "-root", "-tree"]:
            tree = base(args, **kwargs)
            return tree.replace(
                f"    {hex(helper)} (has no name): () 1x1+-1+-1  +691+361\n",
                "",
            )
        return base(args, **kwargs)

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == frame_pid:
            return "/usr/libexec/mutter-x11-frames", "frame-start", "mutter-x11-fram"
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="children") as failure:
        target._verify(pid, TARGET, object(), startup_readiness=True)  # type: ignore[arg-type]
    assert not isinstance(failure.value, calibration_module._GtkStartupPending)


def test_gtk_post_ready_validation_does_not_skip_map_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Post-ready certificate checks always require a complete map state."""

    pid = os.getpid()
    base = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
    )

    def command(args: list[str], **kwargs: object) -> str:
        if args == ["xwininfo", "-id", hex(TARGET), "-stats"]:
            return "Absolute upper-left X: 753\nAbsolute upper-left Y: 456\nWidth: 480\nHeight: 240\n"
        return base(args, **kwargs)

    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="map state"):
        target._verify(pid, TARGET, object())  # type: ignore[arg-type]


def test_gtk_post_ready_unmapped_state_fails_hard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A returned certificate cannot receive startup grace for an unmapped client."""

    pid = os.getpid()
    base = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
    )

    def command(args: list[str], **kwargs: object) -> str:
        if args == ["xwininfo", "-id", hex(TARGET), "-stats"]:
            return (
                "Absolute upper-left X: 753\nAbsolute upper-left Y: 456\n"
                "Width: 480\nHeight: 240\nMap State: IsUnMapped\n"
            )
        return base(args, **kwargs)

    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="IsUnMapped") as failure:
        target._verify(pid, TARGET, object())  # type: ignore[arg-type]
    import crowley.session.calibration as calibration_module

    assert not isinstance(failure.value, calibration_module._GtkStartupPending)


def test_gtk_failure_reaps_before_surface_registration_cleanup_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A cleanup exception cannot skip termination and process reap."""

    import crowley.session.calibration as calibration_module

    lifecycle: list[str] = []
    processes: list[object] = []

    class FakeProcess:
        def __init__(self, pid: int, stdout: io.TextIOBase, gate_reader: int) -> None:
            self.pid = pid
            self.stdout = stdout
            self.stdin = io.StringIO()
            self.returncode: int | None = None
            self._gate_reader = gate_reader

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            lifecycle.append("terminate")
            if self._gate_reader >= 0:
                os.close(self._gate_reader)
                self._gate_reader = -1
            self.returncode = -15

        def kill(self) -> None:
            lifecycle.append("kill")
            if self._gate_reader >= 0:
                os.close(self._gate_reader)
                self._gate_reader = -1
            self.returncode = -9

        def wait(self, timeout: float = 2.0) -> int:
            del timeout
            lifecycle.append("wait")
            if self.returncode is None:
                self.returncode = 0
            return self.returncode

    def fake_popen(_args: list[str], **_kwargs: object) -> FakeProcess:
        pid = 501_000
        read_fd, write_fd = os.pipe()
        os.write(write_fd, (json.dumps({"pid": pid, "xid": TARGET}) + "\n").encode())
        os.close(write_fd)
        wrapper_index = _args.index(_EXEC_ADMISSION_WRAPPER)
        gate_reader = os.dup(int(_args[wrapper_index + 1]))
        process = FakeProcess(pid, os.fdopen(read_fd, "r", encoding="utf-8"), gate_reader)
        processes.append(process)
        return process

    def verify(
        _target: OwnedGtkCalibrationWindow,
        _pid: int,
        _xid: int,
        _process: object,
        **_kwargs: object,
    ) -> object:
        raise CalibrationError("synthetic GTK verification failure")

    def admit(_pid: int, release: Callable[[], None]) -> Callable[[], None]:
        release()

        def cleanup() -> None:
            raise RuntimeError("synthetic registration cleanup failure")

        return cleanup

    monkeypatch.setattr(calibration_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(OwnedGtkCalibrationWindow, "_verify", verify)
    target = OwnedGtkCalibrationWindow(
        display=":gtk-cleanup-error",
        xauthority=str(tmp_path / "Xauthority"),
        python_executable=sys.executable,
    )
    try:
        with pytest.raises(CalibrationError, match="clean up GTK target") as failure:
            target.create(startup_admission=admit)
        assert isinstance(failure.value.__cause__, RuntimeError)
        assert lifecycle[:2] == ["terminate", "wait"]
    finally:
        for process in processes:
            process.terminate()  # type: ignore[attr-defined]
            process.stdout.close()  # type: ignore[attr-defined]


@pytest.mark.parametrize("identity_failure", ("timeout", "nonjson", "incomplete", "pid-mismatch"))
def test_gtk_identity_failure_reaps_unregisters_and_allows_same_driver_retry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, identity_failure: str
) -> None:
    """Startup identity failures leave the Guardian retryable in one epoch fence."""

    import crowley.session.calibration as calibration_module

    profile = DriverProfile(
        display=f":gtk-identity-{identity_failure}", xauthority=str(tmp_path / "Xauthority")
    )
    driver = DesktopDriver(
        profile=profile,
        backend=RecordingBackend(),
        lease_path=tmp_path / f"gtk-identity-{identity_failure}.lock",
    )
    processes: list[object] = []
    lifecycle: list[str] = []

    class FakeProcess:
        def __init__(self, pid: int, stdout: io.TextIOBase, gate_reader: int, writer: int) -> None:
            self.pid = pid
            self.stdout = stdout
            self.stdin = io.StringIO()
            self.returncode: int | None = None
            self._gate_reader = gate_reader
            self._writer = writer

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            lifecycle.append("terminate")
            for fd_name in ("_gate_reader", "_writer"):
                fd = getattr(self, fd_name)
                if fd >= 0:
                    os.close(fd)
                    setattr(self, fd_name, -1)
            self.returncode = -15

        def kill(self) -> None:
            lifecycle.append("kill")
            self.terminate()
            self.returncode = -9

        def wait(self, timeout: float = 2.0) -> int:
            del timeout
            lifecycle.append("wait")
            if self.returncode is None:
                self.returncode = 0
            return self.returncode

    def fake_popen(argv: list[str], **_kwargs: object) -> FakeProcess:
        pid = 510_000 + len(processes)
        read_fd, write_fd = os.pipe()
        if not processes:
            if identity_failure == "nonjson":
                os.write(write_fd, b"not-json\n")
            elif identity_failure == "incomplete":
                os.write(write_fd, b"{}\n")
            elif identity_failure == "pid-mismatch":
                os.write(write_fd, (json.dumps({"pid": pid + 1, "xid": TARGET}) + "\n").encode())
        else:
            os.write(write_fd, (json.dumps({"pid": pid, "xid": TARGET}) + "\n").encode())
        if identity_failure != "timeout" or processes:
            os.close(write_fd)
            writer = -1
        else:
            writer = write_fd
        wrapper_index = argv.index(_EXEC_ADMISSION_WRAPPER)
        gate_reader = os.dup(int(argv[wrapper_index + 1]))
        process = FakeProcess(pid, os.fdopen(read_fd, "r", encoding="utf-8"), gate_reader, writer)
        processes.append(process)
        return process

    def verify(
        _target: OwnedGtkCalibrationWindow,
        pid: int,
        xid: int,
        process: object,
        **_kwargs: object,
    ) -> object:
        return SimpleNamespace(pid=pid, xid=xid, process=process)

    monkeypatch.setattr(calibration_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(OwnedGtkCalibrationWindow, "_verify", verify)
    original_unregister = driver.guardian.unregister_process_group

    def record_unregister(pgid: int) -> None:
        lifecycle.append("unregister")
        original_unregister(pgid)

    driver.guardian.unregister_process_group = record_unregister
    try:
        driver.begin_calibration_operation()
        target = OwnedGtkCalibrationWindow(
            display=profile.display,
            xauthority=profile.xauthority,
            python_executable=sys.executable,
        )
        with pytest.raises(CalibrationError):
            target.create(timeout=0.02, startup_admission=driver.admit_calibration_target_process)
        assert lifecycle[:3] == ["terminate", "wait", "unregister"]
        assert not driver.guardian.active_process_groups
        assert not driver._calibration_bootstrap_process_groups

        driver.begin_calibration_operation()
        retry = OwnedGtkCalibrationWindow(
            display=profile.display,
            xauthority=profile.xauthority,
            python_executable=sys.executable,
        )
        window = retry.create(startup_admission=driver.admit_calibration_target_process)
        assert window.pid == processes[-1].pid
        assert driver.guardian.active_process_groups == frozenset({window.pid})
    finally:
        for process in processes:
            process.terminate()  # type: ignore[attr-defined]
            process.stdout.close()  # type: ignore[attr-defined]
        driver.close()


def test_owned_gtk_target_rejects_duplicate_identity_and_missing_ancestry() -> None:
    frame = 0x600130
    pid = os.getpid()

    def command(args: list[str], **_kwargs: object) -> str:
        if args[:2] == ["wmctrl", "-lp"]:
            return f"{hex(TARGET)}  -1 {pid} host CROWLEY INPUT CALIBRATION ONLY\n"
        if args == ["xprop", "-id", hex(TARGET)]:
            return (
                f'WM_NAME(STRING) = "CROWLEY INPUT CALIBRATION ONLY"\n'
                f"_NET_WM_PID(CARDINAL) = {pid}\n"
                "_NET_FRAME_EXTENTS(CARDINAL) = 5, 31, 5, 38\n"
            )
        if args[0] == "xwininfo" and "-tree" in args:
            return f"xwininfo: Window id: 0x374 root\n  {hex(frame)} (foreign)\n"
        if args[0] == "xwininfo":
            return (
                "Absolute upper-left X: 11\nAbsolute upper-left Y: 22\n"
                "Width: 480\nHeight: 240\nMap State: IsViewable\n"
            )
        if args[:2] == ["xdotool", "windowactivate"]:
            return ""
        if args[:2] == ["xdotool", "getwindowfocus"]:
            return "0x600119\n"
        raise AssertionError(args)

    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="ancestry"):
        target._verify(pid, TARGET, object())  # type: ignore[arg-type]


def test_owned_gtk_tree_accepts_target_and_advertised_user_time_helper_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_token = 0x374
    frame = 0x600192
    helper = 0x600193
    child = 0x600121
    frame_pid = 5717
    pid = os.getpid()

    import crowley.session.calibration as calibration_module

    def stats(x: int, y: int, width: int, height: int) -> str:
        return f"Absolute upper-left X: {x}\nAbsolute upper-left Y: {y}\nWidth: {width}\nHeight: {height}\n"

    def command(args: list[str], **_kwargs: object) -> str:
        if args[:2] == ["wmctrl", "-lp"]:
            return f"{hex(TARGET)}  -1 {pid} host CROWLEY INPUT CALIBRATION ONLY\n"
        if args == ["xprop", "-id", hex(TARGET)]:
            return (
                f'WM_NAME(STRING) = "CROWLEY INPUT CALIBRATION ONLY"\n'
                f"_NET_WM_PID(CARDINAL) = {pid}\n"
                "_NET_FRAME_EXTENTS(CARDINAL) = 5, 31, 5, 38\n"
            )
        if args == ["xprop", "-id", hex(frame)]:
            return (
                f"_MUTTER_FRAME_FOR(WINDOW): window id # {hex(TARGET)}\n"
                f"_NET_WM_USER_TIME_WINDOW(WINDOW): window id # {hex(helper)}\n"
                f"_NET_WM_PID(CARDINAL) = {frame_pid}\n"
                'WM_CLASS(STRING) = "mutter-x11-frames", "mutter-x11-frames"\n'
            )
        if args == ["xprop", "-id", hex(helper)]:
            return "_NET_WM_USER_TIME(CARDINAL) = 276992109\n"
        if args[0] == "xprop":
            raise AssertionError(args)
        if args[0] == "xwininfo" and "-tree" in args:
            return (
                f"xwininfo: Window id: {hex(root_token)} (the root window)\n"
                f'  {hex(frame)} "CROWLEY INPUT CALIBRATION ONLY": '
                f'("mutter-x11-frames" "mutter-x11-frames") 602x401+692+362  +692+362\n'
                f'    {hex(TARGET)} "CROWLEY INPUT CALIBRATION ONLY": ("-c" "-c") '
                "480x240+61+94  +753+456\n"
                f"      {hex(child)} (has no name): () 1x1+-1+-1  +752+455\n"
                f"    {hex(helper)} (has no name): () 1x1+-1+-1  +691+361\n"
            )
        if args == ["xwininfo", "-id", hex(frame), "-stats"]:
            return stats(692, 362, 602, 401) + "Depth: 32\nBorder width: 0\nClass: InputOutput\n"
        if args == ["xwininfo", "-id", hex(TARGET), "-stats"]:
            return (
                stats(753, 456, 480, 240)
                + "Depth: 24\nBorder width: 0\nClass: InputOutput\nMap State: IsViewable\n"
            )
        if args == ["xwininfo", "-id", hex(helper), "-stats"]:
            return (
                stats(691, 361, 1, 1) + "Relative upper-left X: -1\nRelative upper-left Y: -1\n"
                "Depth: 0\nBorder width: 0\nClass: InputOnly\n"
            )
        if args[:2] == ["xdotool", "windowactivate"]:
            return ""
        if args[:2] == ["xdotool", "getwindowfocus"]:
            return hex(TARGET) + "\n"
        raise AssertionError(args)

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == frame_pid:
            return "/usr/libexec/mutter-x11-frames", "frame-start", "mutter-x11-fram"
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    window = target._verify(pid, TARGET, object())  # type: ignore[arg-type]
    assert window.allowed_event_target_xids == frozenset({frame, TARGET, child})
    assert window.contains_xid(TARGET)
    assert window.contains_xid(child)
    assert not window.contains_xid(helper)
    assert not window.contains_xid(root_token)
    assert not window.contains_xid(0x600130)


@pytest.mark.parametrize(
    ("variant", "error"),
    [
        ("mismatched-frame-for", "frame identity or advertised helper"),
        ("mismatched-helper", "frame identity or advertised helper|children do not match"),
        ("missing-frame-for", "frame properties|X11 property"),
        ("duplicate-frame-for", "frame properties|X11 property"),
        ("conflicting-frame-for-type", "frame properties|X11 property"),
        ("conflicting-helper-type", "frame properties|X11 property"),
        ("zero-user-time", "user-time property is invalid"),
        ("negative-user-time", "user-time property is incomplete"),
    ],
)
def test_owned_gtk_certificate_rejects_malformed_frame_and_helper_properties(
    variant: str,
    error: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    frame = 0x600192
    helper = 0x600193
    frame_pid = 5717
    valid_frame_props = (
        f"_MUTTER_FRAME_FOR(WINDOW): window id # {hex(TARGET)}\n"
        f"_NET_WM_USER_TIME_WINDOW(WINDOW): window id # {hex(helper)}\n"
        f"_NET_WM_PID(CARDINAL) = {frame_pid}\n"
        'WM_CLASS(STRING) = "mutter-x11-frames", "mutter-x11-frames"\n'
    )
    frame_props = valid_frame_props
    helper_props: str | None = None
    if variant == "mismatched-frame-for":
        frame_props = valid_frame_props.replace(hex(TARGET), "0x600194", 1)
    elif variant == "mismatched-helper":
        frame_props = valid_frame_props.replace(hex(helper), hex(TARGET), 1)
    elif variant == "missing-frame-for":
        frame_props = valid_frame_props.replace(f"_MUTTER_FRAME_FOR(WINDOW): window id # {hex(TARGET)}\n", "")
    elif variant == "duplicate-frame-for":
        frame_props = valid_frame_props + f"_MUTTER_FRAME_FOR(WINDOW): window id # {hex(TARGET)}\n"
    elif variant == "conflicting-frame-for-type":
        frame_props = valid_frame_props + "_MUTTER_FRAME_FOR(CARDINAL) = 1\n"
    elif variant == "conflicting-helper-type":
        frame_props = valid_frame_props + "_NET_WM_USER_TIME_WINDOW(CARDINAL) = 1\n"
    elif variant == "zero-user-time":
        helper_props = "_NET_WM_USER_TIME(CARDINAL) = 0\n"
    elif variant == "negative-user-time":
        helper_props = "_NET_WM_USER_TIME(CARDINAL) = -1\n"
    else:
        raise AssertionError(variant)
    command = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=frame,
        helper=helper,
        child=0x600121,
        frame_props=frame_props,
        helper_props=helper_props,
    )

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == frame_pid:
            return "/usr/libexec/mutter-x11-frames", "frame-start", "mutter-x11-fram"
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match=error):
        target._verify(pid, TARGET, object())  # type: ignore[arg-type]


def test_owned_gtk_certificate_rejects_unadvertised_frame_sibling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    frame_pid = 5717
    command = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
        extra_frame_child=FOREIGN,
    )

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == frame_pid:
            return "/usr/libexec/mutter-x11-frames", "frame-start", "mutter-x11-fram"
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="children do not match"):
        target._verify(pid, TARGET, object())  # type: ignore[arg-type]


def test_owned_gtk_certificate_rejects_wrong_helper_geometry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    frame_pid = 5717
    wrong_helper_stats = (
        "Absolute upper-left X: 691\nAbsolute upper-left Y: 361\nWidth: 2\nHeight: 1\n"
        "Relative upper-left X: -1\nRelative upper-left Y: -1\n"
        "Depth: 0\nBorder width: 0\nClass: InputOnly\n"
    )
    command = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
        helper_stats=wrong_helper_stats,
    )

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == frame_pid:
            return "/usr/libexec/mutter-x11-frames", "frame-start", "mutter-x11-fram"
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="helper geometry or class"):
        target._verify(pid, TARGET, object())  # type: ignore[arg-type]


def test_owned_gtk_certificate_rejects_wrong_mutter_process_executable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    frame_pid = 5717
    command = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=0x600192,
        helper=0x600193,
        child=0x600121,
    )

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == frame_pid:
            return "/usr/bin/mutter-x11-frames", "frame-start", "mutter-x11-fram"
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(CalibrationError, match="not the observed Mutter frame"):
        target._verify(pid, TARGET, object())  # type: ignore[arg-type]


def test_owned_gtk_startup_direct_root_sibling_waits_for_fresh_certificate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A direct-root client and tiny same-title sibling never form a frame."""

    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    frame = 0x600192
    helper = 0x600193
    child = 0x600121
    base = _mutter_gtk_fixture_command(
        pid=pid,
        target=TARGET,
        frame=frame,
        helper=helper,
        child=child,
    )
    startup_tree = (
        "xwininfo: Window id: 0x374 (the root window)\n"
        f'  {hex(TARGET)} "CROWLEY INPUT CALIBRATION ONLY": ("-c" "-c") '
        "480x240+753+456  +753+456\n"
        f'  {hex(frame)} "CROWLEY INPUT CALIBRATION ONLY": '
        '("mutter-x11-frames" "mutter-x11-frames") 1x1+1+1  +1+1\n'
    )
    tree_calls = 0

    def command(args: list[str], **kwargs: object) -> str:
        nonlocal tree_calls
        if args == ["xwininfo", "-root", "-tree"]:
            tree_calls += 1
            if tree_calls == 1:
                return startup_tree
        return base(args, **kwargs)

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == 5717:
            return "/usr/libexec/mutter-x11-frames", "frame-start", "mutter-x11-fram"
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority", command=command)
    with pytest.raises(calibration_module._GtkStartupPending, match="reparented"):
        target._verify(pid, TARGET, object(), timeout=1.0, startup_readiness=True)  # type: ignore[arg-type]
    window = target._verify(pid, TARGET, object(), timeout=1.0, startup_readiness=True)  # type: ignore[arg-type]
    assert window.managed_frame_xid == frame
    assert tree_calls == 2


def test_owned_gtk_prompt_recertifies_ready_certificate_without_startup_grace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prompt acknowledgement cannot preserve a certificate after structural drift."""

    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"PROMPT_ACK\n")
    os.close(write_fd)
    stdout = os.fdopen(read_fd, "r", encoding="utf-8")

    class FakeProcess:
        pid = 603_001
        stdin = io.StringIO()

        def poll(self) -> None:
            return None

    process = FakeProcess()
    original = OwnedWindow(
        process.pid,
        TARGET,
        OwnedGtkCalibrationWindow.TITLE,
        (0, 0, 480, 240),
        process,  # type: ignore[arg-type]
        frozenset({TARGET}),
        "/usr/bin/python3",
        "start",
        0x600192,
        (0, 0, 500, 260),
        frozenset({TARGET, 0x600192}),
    )
    drifted = replace(original, geometry=(1, 0, 480, 240))
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="Xauthority")
    target.window = replace(original, process=process)  # type: ignore[arg-type]
    process.stdout = stdout  # type: ignore[attr-defined]
    calls: list[bool] = []

    def verify(
        _target: OwnedGtkCalibrationWindow,
        _pid: int,
        _xid: int,
        _process: object,
        **kwargs: object,
    ) -> OwnedWindow:
        calls.append(bool(kwargs.get("startup_readiness", False)))
        return drifted

    monkeypatch.setattr(OwnedGtkCalibrationWindow, "_verify", verify)
    try:
        with pytest.raises(CalibrationError, match="certificate changed"):
            target.show_human_prompt()
        assert calls == [False]
    finally:
        stdout.close()


class _WorkflowObserver:
    def __init__(self, callback, records: list[XI2Event], human: list[XI2Event], *, outside: bool):
        self.callback = callback
        self.records = records
        self.human = human
        self.outside = outside
        self._event_list: list[XI2Event] = []

    def _add(self, event: XI2Event) -> None:
        self._event_list.append(event)
        self.callback(event)

    def collect_until(self, predicate, *, timeout: float) -> str:
        for event in self.records:
            self._add(event)
        assert predicate(self._event_list)
        return _render_events(self.records)

    def wait_for_human(self, predicate, *, timeout: float) -> None:
        if self.outside:
            self._add(parse_xi2_records(FULL_XI2_TRACE, require_event=True)[-1])
        for event in self.human:
            self._add(event)

    def events(self) -> list[XI2Event]:
        return list(self._event_list)

    def stop(self) -> str:
        return _render_events(self._event_list)


class _WorkflowTarget:
    def __init__(self) -> None:
        self.window = OwnedWindow(
            os.getpid(),
            TARGET,
            OwnedGtkCalibrationWindow.TITLE,
            (0, 0, 480, 240),
            SimpleNamespace(poll=lambda: None),  # type: ignore[arg-type]
            frozenset({TARGET}),
            "/usr/bin/python3",
            "owned-target-start",
            TARGET + 1,
            (0, 0, 500, 260),
            frozenset({TARGET, TARGET + 1}),
        )
        self.prompted = False

    def create(self) -> OwnedWindow:
        return self.window

    def close(self) -> None:
        return None

    def show_human_prompt(self) -> None:
        self.prompted = True


class _WorkflowDriver:
    profile = SimpleNamespace(display=":test", xauthority="Xauthority")
    driver_version = "native-x11-3"
    xauthority = "Xauthority"

    def __init__(self, *, outside: bool):
        records = parse_xi2_records(FULL_XI2_TRACE, require_event=True)
        # Mark this deterministic observer fixture as the native X11 path so
        # the workflow seals and replays its canonical raw/primary transition.
        self.backend = object.__new__(X11Backend)
        self.backend._last_synthetic_motion_query = (
            987,
            595,
            TARGET,
            988,
            596,
            988,
            596,
            TARGET,
        )
        self.observer: _WorkflowObserver | None = None
        self.revocations: list[str] = []
        self.queued_calibration_count = 0
        self.calibration_executions = 0
        self.outside = outside
        self._records = records[:11]
        # The synthetic phase owns a source-4 delivered motion.  The human
        # suffix below supplies the independent source-7 takeover motion;
        # only the former may participate in an echo proof.
        self._records.insert(
            7,
            replace(
                _event(
                    EventClass.RAW_MOTION,
                    master=2,
                    source=4,
                    timestamp=232007474,
                    detail=0,
                    child=None,
                ),
                valuators=((0, 988.0, 988.0), (1, 596.0, 596.0)),
            ),
        )
        self._records.insert(
            8,
            replace(
                _event(EventClass.MOTION, master=4, source=4, timestamp=232007474, detail=0),
                valuators=((0, 988.0, 988.0), (1, 596.0, 596.0)),
            ),
        )
        self._keyboard_keymap = {"Return": 36}
        self._keyboard_operations = (
            KeyboardProbeOperation(
                "open_chat",
                "",
                (KeyboardProbeStep("press", "Return"), KeyboardProbeStep("release", "Return")),
            ),
        )
        for index, step in enumerate(self._keyboard_operations[0].steps):
            detail = self._keyboard_keymap[step.keysym]
            timestamp = 232007540 + index * 2
            event_class = EventClass.RAW_KEY_PRESS if step.phase == "press" else EventClass.RAW_KEY_RELEASE
            delivered_class = EventClass.KEY_PRESS if step.phase == "press" else EventClass.KEY_RELEASE
            self._records.extend(
                (
                    _event(
                        event_class,
                        master=3,
                        source=5,
                        timestamp=timestamp,
                        detail=detail,
                        child=None,
                    ),
                    _event(
                        delivered_class,
                        master=5,
                        source=5,
                        timestamp=timestamp + 1,
                        detail=detail,
                    ),
                )
            )
        self._human = [
            replace(
                _event(
                    EventClass.MOTION,
                    master=7,
                    source=7,
                    timestamp=232007505,
                    detail=0,
                ),
                root_xy=(988.0, 596.0),
                event_xy=(988.0, 596.0),
            ),
            _event(
                EventClass.RAW_KEY_PRESS,
                master=3,
                source=9,
                timestamp=232007518,
                detail=8,
                child=None,
            ),
            _event(
                EventClass.KEY_PRESS,
                master=9,
                source=9,
                timestamp=232007520,
                detail=8,
            ),
            _event(
                EventClass.RAW_KEY_RELEASE,
                master=3,
                source=9,
                timestamp=232007522,
                detail=8,
                child=None,
            ),
            _event(
                EventClass.KEY_RELEASE,
                master=9,
                source=9,
                timestamp=232007522,
                detail=8,
            ),
            _event(
                EventClass.RAW_BUTTON_PRESS,
                master=2,
                source=7,
                timestamp=232007523,
                detail=1,
                child=None,
            ),
            _event(
                EventClass.BUTTON_PRESS,
                master=7,
                source=7,
                timestamp=232007524,
                detail=1,
            ),
            _event(
                EventClass.RAW_BUTTON_RELEASE,
                master=2,
                source=7,
                timestamp=232007525,
                detail=1,
                child=None,
            ),
            _event(
                EventClass.BUTTON_RELEASE,
                master=7,
                source=7,
                timestamp=232007525,
                detail=1,
            ),
        ]
        self.calibration_due_count = 0
        self.calibration_rejected_count = 0
        self.calibration_due_deadline = 0.0
        self.calibration_epoch = 0
        self.calibration_ticket = None
        self.ready = None
        self.queue_seen_before_ready = False
        self.game_identity = WindowIdentity(
            0x700001,
            os.getpid(),
            "WowB.exe",
            "World of Warcraft",
            "wowb.exe,wowb.exe",
            0x700002,
            (0, 0, 1928, 1092),
            (0, 0, 1920, 1080),
            0x700002,
            "game-start",
            ":test",
            "owned-game-identity",
            root_xid=0x374,
            managed_frame_xid=0x700001,
            target_event_xids=frozenset({0x700001, 0x700002}),
        )

    def input_hierarchy(self):
        return (
            (2, 0, "master", "pointer:Virtual core pointer"),
            (3, 0, "master", "keyboard:Virtual core keyboard"),
            (4, 2, "slave", "pointer:Virtual core XTEST pointer"),
            (5, 3, "slave", "keyboard:Virtual core XTEST keyboard"),
            (7, 2, "slave", "pointer:xwayland-relative-pointer"),
            (9, 3, "slave", "keyboard:xwayland-keyboard"),
        )

    def xtest_input_profile(self, hierarchy, **_kwargs):
        return _xtest_profile(hierarchy)

    def begin_calibration_operation(self) -> int:
        self.calibration_epoch += 1
        self.queued_calibration_count = 0
        self.calibration_due_count = 0
        self.calibration_rejected_count = 0
        return self.calibration_epoch

    def resolve_identity(self, *, require_foreground: bool = False):
        del require_foreground
        return self.game_identity

    def notify_input_calibration_ready(self, readiness) -> None:
        self.ready = readiness

    def issue_calibration_ticket(self, window):
        assert window.contains_xid(TARGET)
        self.calibration_ticket = SimpleNamespace(epoch=self.calibration_epoch)
        return self.calibration_ticket

    def clear_input_calibration_ready(self) -> None:
        self.ready = None

    def calibration_keyboard_operations(self):
        return self._keyboard_operations

    def calibration_keyboard_keymap(self):
        return self._keyboard_keymap

    def stop_input_observer(self, observer, *, already_stopped: bool = False) -> None:
        del observer, already_stopped

    def start_input_observer(self, *, calibration: bool, callback):
        assert calibration
        self.observer = _WorkflowObserver(callback, self._records, self._human, outside=self.outside)
        return self.observer

    def synthetic_target_key_click(self, window: OwnedWindow, *, calibration_ticket) -> None:
        assert window.contains_xid(TARGET)
        assert calibration_ticket is self.calibration_ticket

    def focus_calibration_target(self, window: OwnedWindow, *, calibration_ticket) -> None:
        assert window.contains_xid(TARGET)
        assert calibration_ticket is not None

    def synthetic_target_keyboard_profile(
        self, window: OwnedWindow, *, operations, calibration_ticket
    ) -> None:
        assert window.contains_xid(TARGET)
        assert tuple(operations) == self._keyboard_operations
        assert calibration_ticket is not None

    def queue_delayed_calibration_action(
        self,
        window: OwnedWindow,
        *,
        delay: float,
        execution_gate: threading.Event | None = None,
        calibration_ticket,
    ) -> None:
        assert delay > 0.0
        assert calibration_ticket is self.calibration_ticket
        self.queue_seen_before_ready = self.ready is None
        self.queued_calibration_count += 1
        self.calibration_due_deadline = delay
        return SimpleNamespace(epoch=self.calibration_epoch)

    def cancel_calibration_actions(self) -> None:
        self.queued_calibration_count = 0

    def revoke(self, reason: str) -> int:
        self.revocations.append(reason)
        self.queued_calibration_count = 0
        self.calibration_due_count = 1
        self.calibration_rejected_count = 1
        return len(self.revocations)

    def retain_input_evidence(self, evidence) -> None:
        evidence.verify_seal()


def test_complete_owned_workflow_preserves_exact_human_and_synthetic_pairs() -> None:
    driver = _WorkflowDriver(outside=False)
    evidence = InputCalibrationWorkflow(driver, display=":test", window_factory=_WorkflowTarget).run(
        human_timeout=1
    )
    assert evidence.target_xid == TARGET
    assert evidence.synthetic_key_source == 5
    assert evidence.synthetic_pointer_source == 4
    assert evidence.human_key_source == 9
    assert evidence.human_pointer_source == 7
    records = driver._records
    assert evidence.synthetic_events == tuple(
        (record.event_class.value, record.source_device, record.detail) for record in records
    )
    assert evidence.human_events == tuple(
        (event.event_class.value, event.source_device, event.detail)
        for event in driver._human
        if event.is_action_event
    )
    expected_classes = [event.event_class.value for event in driver._records]
    expected_classes.extend(event.event_class.value for event in driver._human)
    assert [proof[0] for proof in evidence.event_proof] == expected_classes
    assert [proof[1:4] for proof in evidence.event_proof[-len(driver._human) :]] == [
        (event.master_device, event.source_device, event.detail) for event in driver._human
    ]
    assert not driver.queued_calibration_count
    assert driver.queue_seen_before_ready


def test_first_human_event_outside_owned_target_revokes_and_suppresses_due_action() -> None:
    driver = _WorkflowDriver(outside=True)
    with pytest.raises(CalibrationError, match="outside owned GTK ancestry"):
        InputCalibrationWorkflow(driver, display=":test", window_factory=_WorkflowTarget).run(human_timeout=1)
    assert driver.revocations == ["first human input during calibration"]
    assert driver.queued_calibration_count == 0
    assert driver.calibration_executions == 0


def test_arm_replaces_stopped_calibration_monitor_with_runtime_observer(tmp_path: Path) -> None:
    hierarchy = _evidence(tmp_path).xinput_hierarchy
    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend.input_tool = fixture_input_tool(tmp_path / "tool")
    backend._cancel_active = threading.Event()
    driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "monitor.lock")
    identity = WindowIdentity(
        1,
        os.getpid(),
        "WowB.exe",
        "World of Warcraft",
        "wowb.exe,wowb.exe",
        2,
        (0, 0, 1928, 1092),
        (0, 0, 1920, 1080),
        1,
        "start",
        ":test",
        "game-id",
        root_xid=0x374,
        managed_frame_xid=1,
        target_event_xids=frozenset({1, 2}),
    )
    backend.resolve_identity = lambda **_kwargs: identity
    driver.input_hierarchy = lambda **_kwargs: hierarchy  # type: ignore[method-assign]
    stopped: list[bool] = []
    runtime = SimpleNamespace(stop=lambda: stopped.append(True))
    calibration = SimpleNamespace(stop=lambda: stopped.append(True))
    driver._monitor = calibration
    driver._monitor_calibration = True
    started: list[bool] = []

    arm_evidence = _evidence(
        tmp_path,
        hierarchy=hierarchy,
        driver_version=driver.driver_version,
        game_identity_fingerprint="game-id",
        game_geometry=identity.child_geometry,
    )
    backend.xtest_input_profile = lambda _hierarchy, **_kwargs: arm_evidence.xtest_profile  # type: ignore[method-assign]

    def start(*, calibration: bool = False, callback=None):
        started.append(calibration)
        driver._monitor = runtime
        driver._monitor_calibration = calibration
        return runtime

    driver.start_input_observer = start  # type: ignore[method-assign]
    try:
        driver.arm(arm_evidence)
        assert stopped == [True]
        assert started == [False]
        assert driver._monitor is runtime
        assert not driver._monitor_calibration
    finally:
        driver.close()


def test_begin_action_generation_check_and_install_are_atomic(tmp_path: Path) -> None:
    guardian = InputGuardian(tmp_path / "atomic.lock", parent_pid=os.getppid())
    clock_entered = threading.Event()
    continue_clock = threading.Event()
    result: dict[str, object] = {}
    try:
        now = [0.0]

        def gated_clock() -> float:
            if not clock_entered.is_set():
                clock_entered.set()
                assert continue_clock.wait(2)
            return now[0]

        guardian._clock = gated_clock  # type: ignore[method-assign]
        generation = guardian.arm(_evidence(tmp_path))

        def begin() -> None:
            try:
                result["action"] = guardian.begin_action(
                    generation,
                    target_xid=TARGET,
                    source_device=5,
                    master_device=3,
                    event_classes={EventClass.KEY_PRESS.value},
                )
            except Exception as exc:  # implementation should fence this race
                result["error"] = exc

        thread = threading.Thread(target=begin)
        thread.start()
        assert clock_entered.wait(2)
        revoker = threading.Thread(target=lambda: guardian.revoke("concurrent human input"))
        revoker.start()
        continue_clock.set()
        revoker.join(2)
        thread.join(2)
        assert not thread.is_alive()
        assert not revoker.is_alive()
        assert guardian.action is None
        assert "error" in result or guardian.generation != generation
    finally:
        guardian.close()


def test_active_x11_process_group_cancellation_releases_tracked_keys_and_buttons(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend.input_tool = fixture_input_tool(tmp_path / "tool")
    backend._active_processes = set()
    backend._active_process_groups = set()
    backend._process_generations = {}
    backend._process_calibration_tickets = {}
    backend._process_lock = threading.RLock()
    backend._active_generation = 1
    backend._canceled_generations = set()
    backend._admission = lambda _generation, callback: callback()
    backend._register_process_group = lambda _generation, _pid: None
    backend._unregister_process_group = lambda _pid: None
    backend._publish_holds = None

    class CancellationFlag:
        def __init__(self) -> None:
            self.event = threading.Event()

        def set(self) -> None:
            self.event.set()

        def is_set(self) -> bool:
            return self.event.is_set()

        def clear(self) -> None:
            # Keep the cancellation visible until the blocked caller has
            # observed it; the real implementation must provide that fence.
            return None

    backend._cancel_active = CancellationFlag()
    backend._held_keys = {"F13"}
    backend._held_buttons = {1}
    terminated: list[int] = []
    releases: list[list[str]] = []

    class BlockingProcess:
        pid = 4242

        def __init__(self, gate_reader: int) -> None:
            self.returncode: int | None = None
            self.ready = threading.Event()
            self.gate_reader = gate_reader

        def communicate(self, *, timeout: float | None = None):
            if timeout is None:
                return "", ""
            assert timeout <= 0.2
            self.ready.wait(timeout)
            raise subprocess.TimeoutExpired("xdotool", timeout)

        def poll(self):
            return self.returncode

        def wait(self, timeout: float | None = None):
            self.returncode = -15
            os.close(self.gate_reader)
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def kill(self):
            self.returncode = -9

    process: BlockingProcess | None = None

    def fake_popen(args, **kwargs):
        del kwargs
        nonlocal process
        wrapper_index = args.index(_EXEC_ADMISSION_WRAPPER)
        assert args[wrapper_index - 1] == "-c"
        gate_fd_index = wrapper_index + 1
        process = BlockingProcess(os.dup(int(args[gate_fd_index])))
        return process

    monkeypatch.setattr("crowley.session.driver.subprocess.Popen", fake_popen)
    backend._terminate_process = lambda value: (terminated.append(value.pid), value.wait())
    backend._release_command = lambda args: releases.append(args)
    result: dict[str, object] = {}

    def run() -> None:
        try:
            backend._run(["xdotool", "click", "1"], timeout=5, generation=1, held_buttons={1})
        except Exception as exc:
            result["error"] = exc

    thread = threading.Thread(target=run)
    thread.start()
    assert _wait_for(lambda: bool(backend._active_processes))
    backend.release_held_input()
    thread.join(2)
    assert not thread.is_alive()
    assert terminated and set(terminated) == {4242}
    assert ["xdotool", "keyup", "F13"] in releases
    assert ["xdotool", "mouseup", "1"] in releases
    assert isinstance(result.get("error"), DriverError)


def test_xi2_monitor_has_one_stdout_reader() -> None:
    class Process:
        def __init__(self) -> None:
            self.stdout = io.StringIO("")
            self.communicate_calls = 0

        def terminate(self) -> None:
            return None

        def communicate(self, *args, **kwargs):
            self.communicate_calls += 1
            return "", ""

    process = Process()
    monitor = InputMonitor(":test", lambda _event: None, xauthority="Xauthority")
    monitor.observer.start = lambda: setattr(monitor.observer, "process", process)  # type: ignore[method-assign]
    monitor.start()
    monitor.stop()
    assert process.communicate_calls == 0


def test_xi2_reader_delivers_final_release_from_open_idle_pipe() -> None:
    read_fd, write_fd = os.pipe()
    stdout = os.fdopen(read_fd, "r", encoding="utf-8", buffering=1)
    seen: list[XI2Event] = []

    class Process:
        def __init__(self) -> None:
            self.stdout = stdout
            self.poll_result: int | None = None

        def poll(self) -> int | None:
            return self.poll_result

        def terminate(self) -> None:
            self.poll_result = 0

        def wait(self, timeout: float | None = None) -> int:
            self.poll_result = 0
            return 0

        def kill(self) -> None:
            self.poll_result = -9

    process = Process()
    monitor = InputMonitor(":test", lambda event: seen.append(event) if event is not None else None)
    monitor.observer.start = lambda: setattr(monitor.observer, "process", process)  # type: ignore[method-assign]
    release_events = [
        _event(EventClass.KEY_RELEASE, master=5, source=5, timestamp=232008000, detail=38),
        _event(EventClass.BUTTON_RELEASE, master=4, source=4, timestamp=232008001, detail=1),
    ]
    try:
        monitor.start()
        os.write(write_fd, (_render_events(release_events) + "\n").encode("utf-8"))
        monitor.wait_for_event(lambda events: len(events) == 2, timeout=2)
        assert [event.event_class for event in seen] == [
            EventClass.KEY_RELEASE,
            EventClass.BUTTON_RELEASE,
        ]
        assert process.poll() is None
    finally:
        os.close(write_fd)
        monitor.stop()
        stdout.close()


def test_real_input_monitor_emits_idle_raw_motion_and_guardian_revokes_without_next_event(
    tmp_path: Path,
) -> None:
    """A blank-delimited raw record reaches the real reader before pipe EOF."""

    # Source-derived formatter expectation; this is not a retained live
    # capture and includes the verified XTEST RawMotion detail contract.
    raw_motion = (
        "EVENT type 17 (RawMotion)\n"
        "    device: 2 (4)\n"
        "    time: 232008100\n"
        "    detail: 0\n"
        "    flags: \n"
        "    valuators:\n"
        "         0: 873.00 (873.00)\n"
        "         1: 576.00 (576.00)\n"
        "\n"
    )

    class Evidence:
        is_live = True
        fingerprint = "idle-raw-motion"

    guardian = InputGuardian(tmp_path / "idle-raw-motion.lock", parent_pid=os.getppid())
    guardian.arm(Evidence())
    observed: list[bool | None] = []
    monitor = InputMonitor(
        ":test", lambda event: observed.append(None if event is None else guardian.observe(event))
    )

    def start_observer() -> None:
        monitor.observer.process = subprocess.Popen(
            [
                sys.executable,
                "-I",
                "-S",
                "-c",
                f"import sys,time;sys.stdout.write({raw_motion!r});sys.stdout.flush();time.sleep(5)",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    monitor.observer.start = start_observer  # type: ignore[method-assign]
    try:
        monitor.start()
        monitor.wait_for_event(lambda events: len(events) == 1, timeout=2)
        assert _wait_for(lambda: not guardian.armed)
        assert observed == [False]
        assert monitor.observer.process is not None
        assert monitor.observer.process.poll() is None
    finally:
        monitor.stop()
        guardian.close()


def test_real_input_monitor_reports_malformed_raw_block_at_idle_delimiter(
    tmp_path: Path,
) -> None:
    raw_motion = (
        "EVENT type 17 (RawMotion)\n"
        "    device: 2 (4)\n"
        "    time: 232008101\n"
        "    detail: 1\n"
        "    flags: \n"
        "    valuators:\n"
        "         0: 873.00 (873.00)\n"
        "         1: 576.00 (576.00)\n"
        "\n"
    )

    class Evidence:
        is_live = True
        fingerprint = "idle-malformed-raw-motion"

    guardian = InputGuardian(tmp_path / "idle-malformed-raw-motion.lock", parent_pid=os.getppid())
    guardian.arm(Evidence())
    observed: list[bool | None] = []

    def observe(event: XI2Event | None) -> None:
        if event is None:
            guardian.revoke("malformed raw observer block")
            observed.append(None)
        else:
            observed.append(guardian.observe(event))

    monitor = InputMonitor(":test", observe)

    def start_observer() -> None:
        monitor.observer.process = subprocess.Popen(
            [
                sys.executable,
                "-I",
                "-S",
                "-c",
                f"import sys,time;sys.stdout.write({raw_motion!r});sys.stdout.flush();time.sleep(5)",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    monitor.observer.start = start_observer  # type: ignore[method-assign]
    try:
        monitor.start()
        assert _wait_for(lambda: observed == [None])
        assert not guardian.armed
        diagnostic = monitor.failure_diagnostic
        assert diagnostic is not None
        assert diagnostic["reason"] == "RawMotion: detail must be 0"
        assert diagnostic["text"] == raw_motion
    finally:
        monitor.stop()
        guardian.close()


def test_xi2_observer_clean_eof_revokes_runtime_callback() -> None:
    read_fd, write_fd = os.pipe()
    stdout = os.fdopen(read_fd, "r", encoding="utf-8", buffering=1)
    callbacks: list[XI2Event | None] = []

    class Process:
        def __init__(self) -> None:
            self.stdout = stdout
            self.poll_result: int | None = None

        def poll(self) -> int | None:
            return self.poll_result

        def terminate(self) -> None:
            self.poll_result = 0
            self.stdout.close()

        def wait(self, timeout: float | None = None) -> int:
            self.poll_result = 0
            return 0

        def kill(self) -> None:
            self.poll_result = -9

    process = Process()
    monitor = InputMonitor(":test", callbacks.append)
    monitor.observer.start = lambda: setattr(monitor.observer, "process", process)  # type: ignore[method-assign]
    try:
        monitor.start()
        os.close(write_fd)
        assert _wait_for(lambda: callbacks == [None])
    finally:
        monitor.stop()
        stdout.close()


def test_real_input_monitor_notifies_after_guardian_callback_under_lock_contention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real reader/subprocess must wake completion after callback state changes."""

    events = [
        _event(EventClass.RAW_KEY_PRESS, master=3, source=5, timestamp=1, detail=8, child=None),
        _event(EventClass.KEY_PRESS, master=5, source=5, timestamp=2, detail=8),
        _event(EventClass.RAW_KEY_RELEASE, master=3, source=5, timestamp=3, detail=8, child=None),
        _event(EventClass.KEY_RELEASE, master=5, source=5, timestamp=4, detail=8),
    ]
    prefix = _render_events(events[:3])
    final = _render_events(events[3:])
    guardian = InputGuardian(tmp_path / "monitor-race.lock", parent_pid=os.getppid())
    generation = guardian.arm(SimpleNamespace(is_live=True, fingerprint="monitor-race"))
    action = guardian.begin_action(
        generation,
        target_xid=TARGET,
        source_device=5,
        master_device=5,
        event_classes={event.event_class.value for event in events},
        required_sequence=(
            EventClass.RAW_KEY_PRESS.value,
            EventClass.KEY_PRESS.value,
            EventClass.RAW_KEY_RELEASE.value,
            EventClass.KEY_RELEASE.value,
        ),
        device_by_class={
            EventClass.RAW_KEY_PRESS.value: 3,
            EventClass.KEY_PRESS.value: 5,
            EventClass.RAW_KEY_RELEASE.value: 3,
            EventClass.KEY_RELEASE.value: 5,
        },
        expected_details=(8, 8, 8, 8),
        expected_modifiers=(0, 0, 0),
        timeout=3.0,
    )
    monitor = InputMonitor(":test", guardian.observe)

    def start_observer() -> None:
        monitor.observer.process = subprocess.Popen(
            [
                sys.executable,
                "-I",
                "-S",
                "-c",
                (
                    f"import sys;sys.stdout.write({prefix!r});sys.stdout.flush();"
                    f"sys.stdin.readline();sys.stdout.write({final!r});sys.stdout.flush();"
                    "sys.stdin.readline()"
                ),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    monkeypatch.setattr(monitor.observer, "start", start_observer)
    lock_entered = threading.Event()
    release_lock = threading.Event()

    def contend_guardian_lock() -> None:
        with guardian._lock:
            lock_entered.set()
            assert release_lock.wait(3)

    waiter_error: list[BaseException] = []
    waiter_done = threading.Event()

    def wait_for_completion() -> None:
        try:
            monitor.wait_for_event(lambda _events: action.complete, timeout=2.0)
        except BaseException as exc:
            waiter_error.append(exc)
        finally:
            waiter_done.set()

    monitor.start()
    contender: threading.Thread | None = None
    waiter: threading.Thread | None = None
    completed_action: subprocess.Popen[str] | None = None
    try:
        assert _wait_for(lambda: len(monitor.events()) == 3)
        contender = threading.Thread(target=contend_guardian_lock, daemon=True)
        contender.start()
        assert lock_entered.wait(2)
        waiter = threading.Thread(target=wait_for_completion, daemon=True)
        waiter.start()
        process = monitor.observer.process
        assert process is not None and process.stdin is not None
        process.stdin.write("\n")
        process.stdin.flush()
        assert _wait_for(lambda: len(monitor.events()) == len(events))
        # Complete a separate harmless action subprocess while the final
        # observer callback is blocked on Guardian._lock.  The action has
        # exited before the callback is released and the completed action is
        # finally retired below.
        completed_action = subprocess.Popen([sys.executable, "-I", "-S", "-c", "import sys;sys.exit(0)"])
        assert completed_action.wait(timeout=2) == 0
        release_lock.set()
        assert waiter_done.wait(2)
        assert not waiter_error
        assert action.complete
        # Stop the real reader subprocess before releasing the completed
        # action.  InputMonitor marks an unsolicited EOF as observer death;
        # the normal stop path closes that process without revoking the
        # already-complete action.
        monitor.stop()
        assert process.poll() is not None
    finally:
        release_lock.set()
        if waiter is not None:
            waiter.join(timeout=2)
        if contender is not None:
            contender.join(timeout=2)
        monitor.stop()
        if action.complete:
            guardian.finish_action(generation, action)
        else:
            guardian.revoke("monitor regression cleanup")
        guardian.close()


def test_reload_stream_correlates_each_character_without_guardian_revoke(tmp_path: Path) -> None:
    read_fd, write_fd = os.pipe()
    stdout = os.fdopen(read_fd, "r", encoding="utf-8", buffering=1)
    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend.input_tool = fixture_input_tool(tmp_path / "tool")
    backend._active_processes = set()
    backend._process_lock = threading.RLock()
    backend._cancel_active = threading.Event()
    backend._held_keys = set()
    backend._held_buttons = set()
    backend._measured_anchors = {}
    identity = WindowIdentity(
        0x700100,
        os.getpid(),
        "WowB.exe",
        "World of Warcraft",
        "wowb.exe,wowb.exe",
        TARGET,
        (0, 0, 1928, 1092),
        (0, 0, 1920, 1080),
        TARGET,
        "start",
        ":test",
        "game-fingerprint",
        root_xid=0x374,
        managed_frame_xid=0x700100,
        target_event_xids=frozenset({0x700100, TARGET}),
    )
    backend._identity_for_test = identity

    class Process:
        def __init__(self) -> None:
            self.stdout = stdout
            self.poll_result: int | None = None

        def poll(self) -> int | None:
            return self.poll_result

        def terminate(self) -> None:
            self.poll_result = 0

        def wait(self, timeout: float | None = None) -> int:
            self.poll_result = 0
            return 0

        def kill(self) -> None:
            self.poll_result = -9

    process = Process()
    monitor = InputMonitor(
        ":test", lambda event: driver._external_input(event), xauthority=profile.xauthority
    )
    monitor.observer.start = lambda: setattr(monitor.observer, "process", process)  # type: ignore[method-assign]
    details = [61, 27, 25, 46, 43, 38, 40]
    commands: list[list[str]] = []
    emitted = 0

    def fake_run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        nonlocal emitted
        commands.append(args)
        if args == ["xmodmap", "-pke"]:
            names = ["slash", "r", "e", "l", "o", "a", "d", "Return"]
            key_details = [*details, 36]
            return subprocess.CompletedProcess(
                args,
                0,
                stdout="\n".join(
                    f"keycode {detail} = {name}" for detail, name in zip(key_details, names, strict=True)
                ),
                stderr="",
            )
        if args[:3] != ["xdotool", "key", "--"]:
            raise AssertionError(args)
        index = emitted
        emitted += 1
        detail = details[index]
        timestamp = 232009000 + index * 10
        records = [
            _event(
                EventClass.RAW_KEY_PRESS, master=3, source=5, timestamp=timestamp, detail=detail, child=None
            ),
            replace(
                _event(EventClass.KEY_PRESS, master=5, source=5, timestamp=timestamp, detail=detail),
                modifiers=(0, 0, 0),
            ),
            _event(
                EventClass.RAW_KEY_RELEASE,
                master=3,
                source=5,
                timestamp=timestamp + 1,
                detail=detail,
                child=None,
            ),
            replace(
                _event(EventClass.KEY_RELEASE, master=5, source=5, timestamp=timestamp + 1, detail=detail),
                modifiers=(0, 0, 0),
            ),
        ]
        suffix = "\n" if emitted == len(details) else ""
        os.write(write_fd, (_render_events(records) + suffix).encode("utf-8"))
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    backend._run = fake_run
    backend.action = lambda _name, **kwargs: backend._type(kwargs["command"])
    driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "reload.lock")
    driver._identity = lambda **_kwargs: backend._identity_for_test  # type: ignore[method-assign]
    evidence = _evidence(
        tmp_path,
        xauthority=profile.xauthority,
        driver_version=driver.driver_version,
    )
    driver.input_calibration(evidence)
    generation = driver.guardian.arm(evidence)
    driver._monitor = monitor
    driver._monitor_calibration = False
    try:
        monitor.start()
        driver.run(
            "type_allowlisted_command",
            generation,
            command="/reload",
            precondition=lambda _identity: True,
        )
        assert [command[-1] for command in commands if command[:2] == ["xdotool", "key"]] == [
            "slash",
            "r",
            "e",
            "l",
            "o",
            "a",
            "d",
        ]
        assert driver.guardian.revoked_reason == ""
        assert driver.guardian.armed
        assert driver.guardian.action is None
    finally:
        os.close(write_fd)
        driver.stop_input_observer(monitor)
        stdout.close()
        driver.close()


def test_input_evidence_survives_revoke_for_explicit_resume_but_stays_unarmed(tmp_path: Path) -> None:
    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    driver = DesktopDriver(
        profile=profile,
        backend=RecordingBackend(),
        lease_path=tmp_path / "retained.lock",
    )
    evidence = _evidence(tmp_path)
    try:
        driver.retain_input_evidence(evidence)
        generation = driver.guardian.arm(evidence)
        driver.revoke("first human input")
        assert driver.retained_input_evidence is evidence
        assert not driver.guardian.armed
        assert driver.guardian.generation == generation + 1
    finally:
        driver.close()


def test_owner_watchdog_does_not_use_unsupported_keyup_all(tmp_path: Path) -> None:
    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend.input_tool = fixture_input_tool(tmp_path / "tool")
    driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "watchdog.lock")
    try:
        assert "--all" not in driver.guardian._watchdog_command
    finally:
        driver.close()


def _status_image(frame: bytes) -> Image.Image:
    image = Image.new("RGB", (256, 256), (0, 0, 0))
    for row, cells in enumerate(pack_cells(frame)):
        for column, bit in enumerate(cells):
            color = (255, 255, 255) if bit else (0, 0, 0)
            for dy in range(2):
                for dx in range(2):
                    image.putpixel((column * 2 + dx, row * 2 + dy), color)
    return image


def test_native_calibration_proves_all_four_physical_pixels_per_cell(tmp_path: Path) -> None:
    from .test_session_runtime import _snapshot

    frame = encode_frame(_snapshot(1000, sequence=1))
    image = _status_image(frame)
    bits = pack_cells(frame)
    one_cell = next(
        (row, column) for row, cells in enumerate(bits) for column, bit in enumerate(cells) if bit
    )
    row, column = one_cell
    image.putpixel((column * 2, row * 2), (0, 0, 0))
    path = tmp_path / "crop.png"
    image.save(path)
    with pytest.raises(CalibrationError, match="physical|cell"):
        NativeCalibrationRunner._validate_cells(path)


def test_pixel_decoder_rejects_crc_change_for_same_boot_sequence() -> None:
    from .test_session_runtime import _snapshot

    first = _status_image(encode_frame(_snapshot(1000, sequence=1)))
    second = _status_image(encode_frame(_snapshot(1001, sequence=1)))
    decoder = PixelDecoder()
    decoder.decode(first, monotonic=1.0, window_identity="identity")
    with pytest.raises(ProtocolError, match="CRC|CRC|duplicate"):
        decoder.decode(second, monotonic=1.1, window_identity="identity")


def _native_driver(tmp_path: Path) -> tuple[DesktopDriver, WindowIdentity, subprocess.Popen[str]]:
    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"), wine_prefix="prefix")
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend.input_tool = fixture_input_tool(tmp_path / "tool")
    child = subprocess.Popen(["/bin/sleep", "30"])
    stat = Path(f"/proc/{child.pid}/stat").read_text(encoding="ascii")
    process_start = stat[stat.rfind(")") + 2 :].split()[19]
    process_executable = os.path.realpath(os.readlink(f"/proc/{child.pid}/exe"))
    identity = WindowIdentity(
        1,
        child.pid,
        process_executable,
        "World of Warcraft",
        "wowb.exe,wowb.exe",
        2,
        (0, 0, 1928, 1092),
        (0, 0, 1920, 1080),
        1,
        process_start,
        ":test",
        "native-identity",
        root_xid=0x374,
        managed_frame_xid=1,
        target_event_xids=frozenset({1, 2}),
    )
    backend.resolve_identity = lambda **_kwargs: identity
    driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "native.lock")
    native_clock = [time.monotonic()]
    driver._native_test_clock = native_clock  # type: ignore[attr-defined]
    driver.input_hierarchy = lambda **_kwargs: _evidence(tmp_path).xinput_hierarchy  # type: ignore[method-assign]
    driver.new_native_decoder = lambda: object()  # type: ignore[method-assign]
    driver.native_memory_meter = LinuxProcStatusVmHwmReset5(
        child.pid,
        process_start=process_start,
        process_executable=process_executable,
        identity_fingerprint=identity.fingerprint,
        monotonic=lambda: native_clock[0],
    )

    preconstruction_path = tmp_path / "preconstruction.png"
    preconstruction_path.write_bytes(b"absence-capture")
    preconstruction_sha256 = hashlib.sha256(preconstruction_path.read_bytes()).hexdigest()

    def preconstruction(observed, *, baseline_reader, baseline_ready):
        baseline = baseline_reader(observed.pid)
        baseline_ready(observed.pid, baseline)
        return NativePreconstructionEvidence._issue(
            identity_fingerprint=observed.fingerprint,
            process_start=observed.process_start,
            absent=True,
            baseline_id=preconstruction_sha256,
            observed_monotonic=driver._native_test_clock[0],  # type: ignore[attr-defined]
            bootstrap_release_monotonic=driver._native_test_clock[0],  # type: ignore[attr-defined]
            display=observed.display,
            process_executable=observed.executable,
            window_xid=observed.xid,
            child_xid=observed.child_xid,
            geometry=observed.child_geometry,
            xauthority=profile.xauthority,
            wine_prefix=profile.wine_prefix,
            baseline_hwm_bytes=baseline,
            capture_path=str(preconstruction_path),
            capture_sha256=preconstruction_sha256,
        )

    driver.native_preconstruction_provider = preconstruction
    driver.notify_native_baseline_ready = lambda _identity, _value: None  # type: ignore[method-assign]
    driver.notify_native_memory_reset_ready = (  # type: ignore[method-assign]
        lambda _identity, record: NativeMemoryArchiveReceipt.for_record(
            record, archive_id=f"native-regression-{record.phase}-{record.ordinal}"
        )
    )
    driver.notify_native_hold_required = lambda _identity: None  # type: ignore[method-assign]
    driver.notify_native_memory_ready = lambda _identity, _pending: None  # type: ignore[method-assign]
    driver.notify_native_resume_required = lambda _identity, _boundary: None  # type: ignore[method-assign]
    driver.notify_native_resume_ready = lambda _identity, _evidence, _resumed: None  # type: ignore[method-assign]
    driver.notify_native_measurement_failed = (  # type: ignore[method-assign]
        lambda _identity, reason: NativeRestorationReceipt(
            "restoration_required", False, reason, durable=True
        )
    )
    driver.release_native_capture = lambda path: path.unlink(missing_ok=True)  # type: ignore[method-assign]
    return driver, identity, child


def _metrics(update_count: int, phase: str = "held", ordinal: int = 100) -> dict[str, object]:
    return {
        "constructionSeconds": 0.1,
        "updateCount": update_count,
        "updateP99Ms": 10,
        "textureCount": 16_384,
        "effectiveScale": 1,
        "cellSize": (2, 2),
        "luaHeap": {
            "method": "collectgarbage_count",
            "available": True,
            "beforeKiB": 1,
            "afterKiB": 2,
            "netKiB": 1,
        },
        "nativePhase": phase,
        "nativeOrdinal": ordinal,
    }


def _native_observation(
    tmp_path: Path,
    identity: WindowIdentity,
    phase: str,
    ordinal: int,
    *,
    sequence: int,
    capture_monotonic: float,
):
    path = tmp_path / f"{phase}-{ordinal}.png"
    Image.new("RGB", (256, 256), (0, 0, 0)).save(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if phase == "construct":
        update_count = 1
        telemetry_phase = "normal"
    elif phase == "held" and ordinal == 0:
        update_count = 3
        telemetry_phase = "held"
    elif phase == "updates":
        update_count = 3 + ordinal
        telemetry_phase = "updates"
    elif phase == "held" and ordinal == 100:
        update_count = 103
        telemetry_phase = "held"
    elif phase == "resume":
        update_count = 104
        telemetry_phase = "normal"
    else:
        raise AssertionError((phase, ordinal))
    return NativeRenderObservation(
        _metrics(
            update_count,
            telemetry_phase,
            ordinal,
        ),
        identity.fingerprint,
        boot="boot-a",
        sequence=sequence,
        crc32=sequence,
        capture_id=digest,
        capture_path=str(path),
        capture_sha256=digest,
        capture_monotonic=capture_monotonic,
        native_phase=telemetry_phase,
        native_ordinal=ordinal,
    )


def _owned_child_identity(child: subprocess.Popen[str]) -> tuple[str, str]:
    stat = Path(f"/proc/{child.pid}/stat").read_text(encoding="ascii")
    return (
        stat[stat.rfind(")") + 2 :].split()[19],
        os.path.realpath(os.readlink(f"/proc/{child.pid}/exe")),
    )


def test_reset5_archives_historical_hwm_before_each_owned_window(tmp_path: Path) -> None:
    child = subprocess.Popen(
        [
            sys.executable,
            "-u",
            "-c",
            "import sys\nbuf=None\nfor line in sys.stdin:\n"
            " if line == 'alloc\\n':\n  buf=bytearray(32*1024*1024)\n"
            "  for i in range(0,len(buf),4096): buf[i]=1\n  print('allocated', flush=True)\n"
            " elif line == 'free\\n':\n  buf=None\n  print('freed', flush=True)\n"
            " elif line == 'stop\\n': break\n",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    meter: LinuxProcStatusVmHwmReset5 | None = None
    try:
        process_start, executable = _owned_child_identity(child)
        meter = LinuxProcStatusVmHwmReset5(
            child.pid,
            process_start=process_start,
            process_executable=executable,
            identity_fingerprint="owned-child",
        )
        archived = []
        pending = meter.begin_window(
            "construction",
            0,
            limit_bytes=128 * 1024 * 1024,
            before_reset=lambda record: (
                archived.append(record),
                NativeMemoryArchiveReceipt.for_record(record, archive_id=f"archive-{len(archived)}"),
            )[1],
        )
        assert archived[0].method == "linux_proc_status_vmhwm_reset5"
        assert archived[0].reset_value == 5
        assert child.stdin is not None and child.stdout is not None
        child.stdin.write("alloc\n")
        child.stdin.flush()
        assert child.stdout.readline().strip() == "allocated"
        child.stdin.write("free\n")
        child.stdin.flush()
        assert child.stdout.readline().strip() == "freed"
        measurement = meter.finish_window(
            pending,
            workload_start_monotonic=pending.reset_completed_monotonic,
            workload_end_monotonic=time.monotonic(),
            workload_start_ordinal=0,
            workload_end_ordinal=0,
        )
        assert measurement.growth_bytes >= 8 * 1024 * 1024
        assert measurement.growth_bytes == max(
            0, measurement.final_hwm_bytes - measurement.post_reset_hwm_bytes
        )
        second = meter.begin_window(
            "updates",
            0,
            limit_bytes=16 * 1024 * 1024,
            before_reset=lambda record: (
                archived.append(record),
                NativeMemoryArchiveReceipt.for_record(record, archive_id=f"archive-{len(archived)}"),
            )[1],
        )
        assert len(archived) == 2
        assert second.historical_hwm_bytes >= second.post_reset_hwm_bytes
    finally:
        if child.stdin is not None:
            child.stdin.write("stop\n")
            child.stdin.flush()
        child.terminate()
        child.wait(timeout=3)
        if meter is not None:
            meter.close()


def test_native_runner_samples_hwm_before_constructor_and_each_update(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    del monkeypatch
    driver, identity, child = _native_driver(tmp_path)
    clock = driver._native_test_clock  # type: ignore[attr-defined]
    order: list[tuple[str, str | int]] = []
    sequence = [0]
    decoded: dict[Path, int] = {}
    metrics_by_path: dict[Path, dict[str, object]] = {}

    def provider(observed: WindowIdentity, phase: str, ordinal: int) -> NativeRenderObservation:
        order.append(("provider", phase))
        assert observed.fingerprint == identity.fingerprint
        if phase == "construct":
            clock[0] += 0.1
        elif phase == "held" and ordinal == 0:
            clock[0] += 0.1
        elif phase == "updates" and ordinal == 1:
            clock[0] += 0.1
        elif phase == "updates":
            clock[0] += 1.0
        elif phase == "held" and ordinal == 100:
            clock[0] += 1.0
        elif phase == "resume":
            clock[0] += 0.1
        observation = _native_observation(
            tmp_path,
            identity,
            phase,
            ordinal,
            sequence=len(metrics_by_path) + 1,
            capture_monotonic=clock[0],
        )
        assert observation.capture_path is not None
        metrics_by_path[Path(observation.capture_path)] = observation.metrics
        return observation

    def decode(_path: Path, *, identity: WindowIdentity, decoder: object):
        if _path not in decoded:
            sequence[0] += 1
            decoded[_path] = sequence[0]
        current = decoded[_path]
        return SimpleNamespace(
            frame=SimpleNamespace(
                boot="boot-a",
                sequence=current,
                crc32=current,
                snapshot=SimpleNamespace(value={"render": metrics_by_path[_path]}),
            )
        )

    driver.native_measurement_provider = provider
    driver.decode_native_capture = decode  # type: ignore[method-assign]
    resume_order: list[str] = []

    def resume_required(_identity: WindowIdentity, boundary: object) -> None:
        assert isinstance(boundary, NativeResumeBoundary)
        assert boundary.render["nativePhase"] == "held"
        assert boundary.render["nativeOrdinal"] == 100
        order.append(("callback", "resume-required"))
        resume_order.append("resume-required")

    driver.notify_native_resume_required = resume_required  # type: ignore[method-assign]
    driver.notify_native_resume_ready = (  # type: ignore[method-assign]
        lambda _identity, _evidence, _resumed: (
            order.append(("callback", "resume-ready")),
            resume_order.append("resume-ready"),
        )[-1]
    )
    try:
        evidence = NativeCalibrationRunner(driver, monotonic=lambda: clock[0]).run()
        assert order[0] == ("provider", "construct")
        assert sum(kind == "provider" and phase == "updates" for kind, phase in order) == 99
        assert evidence.construction_update_count == 1
        assert evidence.held_update_count == 3
        assert evidence.render["updateCount"] == 103
        assert evidence.resume_update_count == 104
        assert order[-3:] == [
            ("callback", "resume-required"),
            ("provider", "resume"),
            ("callback", "resume-ready"),
        ]
        assert resume_order == ["resume-required", "resume-ready"]
    finally:
        driver.close()
        driver.native_memory_meter.close()  # type: ignore[union-attr]
        child.terminate()
        child.wait(timeout=2)


def test_native_runner_rejects_boot_churn_across_101_bound_frames(tmp_path: Path) -> None:
    driver, identity, child = _native_driver(tmp_path)
    clock = driver._native_test_clock  # type: ignore[attr-defined]
    sequence = [0]
    decoded: dict[Path, int] = {}
    metrics_by_path: dict[Path, dict[str, object]] = {}

    def decode(_path: Path, *, identity: WindowIdentity, decoder: object):
        if _path not in decoded:
            sequence[0] += 1
            decoded[_path] = sequence[0]
        current = decoded[_path]
        boot = "boot-a" if current <= 50 else "boot-b"
        return SimpleNamespace(
            frame=SimpleNamespace(
                boot=boot,
                sequence=current,
                crc32=current,
                snapshot=SimpleNamespace(value={"render": metrics_by_path[_path]}),
            )
        )

    driver.decode_native_capture = decode  # type: ignore[method-assign]

    def provider(observed: WindowIdentity, phase: str, ordinal: int) -> NativeRenderObservation:
        if phase == "construct":
            clock[0] += 0.1
        elif phase == "held" and ordinal == 0:
            clock[0] += 0.1
        elif phase == "updates" and ordinal == 1:
            clock[0] += 0.1
        elif phase == "updates":
            clock[0] += 1.0
        elif phase == "held" and ordinal == 100:
            clock[0] += 1.0
        elif phase == "resume":
            clock[0] += 0.1
        observation = _native_observation(
            tmp_path,
            identity,
            phase,
            ordinal,
            sequence=len(metrics_by_path) + 1,
            capture_monotonic=clock[0],
        )
        assert observation.capture_path is not None
        metrics_by_path[Path(observation.capture_path)] = observation.metrics
        return observation

    driver.native_measurement_provider = provider
    try:
        with pytest.raises(CalibrationError, match="boot|identity"):
            NativeCalibrationRunner(driver, monotonic=lambda: clock[0]).run()
    finally:
        driver.close()
        driver.native_memory_meter.close()  # type: ignore[union-attr]
        child.terminate()
        child.wait(timeout=2)


def test_measured_anchor_installation_rejects_manual_provenance_and_stale_identity(tmp_path: Path) -> None:
    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend.input_tool = fixture_input_tool(tmp_path / "tool")
    backend._measured_anchors = {}
    identity = WindowIdentity(
        1,
        os.getpid(),
        "WowB.exe",
        "World of Warcraft",
        "wowb.exe,wowb.exe",
        2,
        (0, 0, 1928, 1092),
        (0, 0, 1920, 1080),
        1,
        "start",
        ":test",
        "identity-a",
        root_xid=0x374,
        managed_frame_xid=1,
        target_event_xids=frozenset({1, 2}),
    )
    backend.resolve_identity = lambda **_kwargs: identity
    backend.is_descendant = lambda xid, ancestor: xid == ancestor
    driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "anchor.lock")
    observed = time.monotonic()
    anchors = tuple(
        MeasuredAnchor(
            action,
            10,
            10,
            identity.fingerprint,
            identity.child_xid,
            f"capture-{index}",
            index + 1,
            "manual-anchor",
            observed,
        )
        for index, action in enumerate(sorted(driver.POINTER_ACTIONS))
    )
    try:
        with pytest.raises(DriverError, match="measure_pointer_anchor"):
            driver.install_measured_anchors(anchors)
        capture = tmp_path / "anchor.png"
        Image.new("RGB", (32, 32), (0, 0, 0)).save(capture)
        positive_driver = DesktopDriver(
            profile=profile,
            backend=RecordingBackend(),
            lease_path=tmp_path / "anchor-positive.lock",
        )
        positive_driver._identity = lambda **_kwargs: identity  # type: ignore[method-assign]
        generation = positive_driver.guardian.arm(_evidence(tmp_path))
        valid_list: list[MeasuredAnchor] = []
        for index, action in enumerate(sorted(positive_driver.POINTER_ACTIONS)):
            anchor_capture = tmp_path / f"anchor-{index}.png"
            Image.new("RGB", (32, 32), (0, 0, 0)).save(anchor_capture)
            capture_digest = hashlib.sha256(anchor_capture.read_bytes()).hexdigest()
            valid_list.append(
                positive_driver.build_measured_anchor(
                    action=action,
                    x=10,
                    y=10,
                    capture_path=anchor_capture,
                    capture_id=capture_digest,
                    capture_sequence=index + 1,
                    capture_monotonic=observed + index * 0.01,
                    scene={
                        "dismiss_disconnect": "disconnect_dialog",
                        "reconnect_game": "game_client",
                        "select_arthur": "character_select",
                        "enter_world": "character_select",
                        "open_ah": "world",
                        "logout": "world",
                    }[action],
                    bounds=(0, 0, 1920, 1080),
                    target_xid=identity.child_xid,
                    target_ancestry=(identity.child_xid,),
                    generation=generation,
                )
            )
        valid = tuple(valid_list)
        positive_driver.install_measured_anchors(valid)
        unproved = tuple(replace(anchor, facts=()) for anchor in valid)
        with pytest.raises(DriverError, match="facts|proof|control|visual"):
            positive_driver.install_measured_anchors(unproved)
        stale_identity = WindowIdentity(
            identity.xid,
            identity.pid,
            identity.executable,
            identity.title,
            identity.wm_class,
            identity.child_xid,
            identity.outer_geometry,
            identity.child_geometry,
            identity.foreground_xid,
            identity.process_start,
            identity.display,
            "identity-b",
            root_xid=identity.root_xid,
            managed_frame_xid=identity.managed_frame_xid,
            target_event_xids=identity.target_event_xids,
        )
        positive_driver._identity = lambda **_kwargs: stale_identity  # type: ignore[method-assign]
        with pytest.raises(DriverError, match="stale|identity|calibration"):
            positive_driver.install_measured_anchors(valid)
        positive_driver.close()
    finally:
        driver.close()


def test_generation_revoke_after_begin_action_blocks_backend_dispatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A revoke between admission and the backend call must be a hard fence."""

    backend = RecordingBackend()
    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "dispatch.lock")
    evidence = _evidence(tmp_path)
    driver.input_calibration(evidence)
    generation = driver.guardian.arm(evidence)
    original_begin = driver.guardian.begin_action

    def revoke_after_admission(*args: object, **kwargs: object):
        action = original_begin(*args, **kwargs)
        driver.revoke("test revoke at dispatch barrier")
        return action

    monkeypatch.setattr(driver.guardian, "begin_action", revoke_after_admission)
    try:
        with pytest.raises(DriverError, match="revoked|stale|cancel"):
            driver.run(
                "open_chat",
                generation,
                precondition=lambda _identity: True,
                postcondition=lambda _identity: True,
            )
        assert backend.events == []
        assert not driver.guardian.armed
    finally:
        driver.close()


def test_spawn_registration_revoke_cannot_let_a_gated_child_escape(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Cancellation during Popen must cover the registration gap as well."""

    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend.input_tool = fixture_input_tool(tmp_path / "tool")
    backend._active_processes = set()
    backend._active_process_groups = set()
    backend._process_generations = {}
    backend._process_calibration_tickets = {}
    backend._process_lock = threading.RLock()
    backend._cancel_active = threading.Event()
    backend._active_generation = 2
    backend._canceled_generations = set()
    backend._admission = lambda _generation, callback: callback()
    backend._register_process_group = lambda _generation, _pid: None
    backend._unregister_process_group = lambda _pid: None
    backend._held_keys = set()
    backend._held_buttons = set()
    backend._release_command = lambda _args: True
    backend._publish_holds = None
    terminated: list[int] = []

    class GatedChild:
        pid = 7401

        def __init__(self) -> None:
            self.returncode: int | None = None

        def poll(self) -> int | None:
            return self.returncode

        def communicate(self, *, timeout: float | None = None):
            # If the cancellation fence is lost, _run would incorrectly
            # accept this child as a successful desktop action.
            if timeout is not None and self.returncode is None:
                time.sleep(min(timeout, 0.01))
            return "", ""

        def wait(self, timeout: float | None = None) -> int:
            self.returncode = -15
            return self.returncode

        def terminate(self) -> None:
            self.returncode = -15

        def kill(self) -> None:
            self.returncode = -9

    child = GatedChild()

    def terminate(process: GatedChild) -> None:
        terminated.append(process.pid)
        process.terminate()

    backend._terminate_process = terminate

    def spawn(*_args: object, **_kwargs: object) -> GatedChild:
        # Revoke before _run receives the Popen return value.  This is the
        # precise Popen-to-active-process registration window under review.
        backend.release_held_input()
        return child

    monkeypatch.setattr("crowley.session.driver.subprocess.Popen", spawn)
    try:
        with pytest.raises(DriverError, match="cancel"):
            backend._run(["xdotool", "click", "1"], timeout=0.2, generation=1, held_buttons={1})
        assert child.returncode == -9
        assert terminated == []
        assert not backend._active_processes
    finally:
        backend._cancel_active.set()


def test_real_executed_wrapper_success_and_process_group_cancellation(tmp_path: Path) -> None:
    """Exercise the production wrapper with harmless processes, including revoke."""

    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend.input_tool = fixture_input_tool(tmp_path / "tool")
    backend._active_processes = set()
    backend._active_process_groups = set()
    backend._process_generations = {}
    backend._process_calibration_tickets = {}
    backend._process_lock = threading.RLock()
    backend._cancel_active = threading.Event()
    backend._canceled_generations = set()
    backend._active_generation = None
    backend._held_keys = set()
    backend._held_buttons = set()
    backend._release_command = lambda _args: True
    backend._publish_holds = None

    success = backend._run(["/usr/bin/true"], timeout=2)
    assert success.returncode == 0
    assert backend.active_process_groups == frozenset()

    result: dict[str, BaseException] = {}

    def run_sleep() -> None:
        try:
            backend._run(["/usr/bin/sleep", "30"], timeout=10)
        except BaseException as exc:
            result["error"] = exc

    worker = threading.Thread(target=run_sleep)
    worker.start()
    assert _wait_for(lambda: bool(backend.active_process_groups))
    backend.release_held_input()
    worker.join(timeout=3)
    assert not worker.is_alive()
    assert isinstance(result.get("error"), DriverError)
    assert backend._cancel_active.is_set()
    assert backend.active_process_groups == frozenset()


def test_sealed_input_and_native_facts_cannot_be_replaced_after_issue(tmp_path: Path) -> None:
    input_evidence = _evidence(tmp_path)
    input_evidence.verify_seal()
    with pytest.raises(CalibrationError, match="seal|fingerprint|tamper|evidence"):
        replace(input_evidence, synthetic_key_source=999).verify_seal()

    capture = tmp_path / "capture.png"
    capture.write_bytes(b"native-capture")
    capture_sha256 = hashlib.sha256(capture.read_bytes()).hexdigest()
    native = NativeCalibrationEvidence._issue(
        fingerprint="a" * 64,
        process_pid=os.getpid(),
        process_executable="/usr/bin/python3",
        process_start="owned-process-start",
        window_xid=1,
        child_xid=2,
        geometry=(0, 0, 1920, 1080),
        xinput_hierarchy=input_evidence.xinput_hierarchy,
        crop=(80, 48, 256, 256),
        boot="boot-a",
        sequence=101,
        crc32=0xABCD,
        render=_metrics(102),
        construction_update_count=1,
        held_update_count=2,
        resume_update_count=103,
        memory_measurements=(
            NativeMemoryMeasurement(
                method="linux_proc_status_vmhwm_reset5",
                phase="construction",
                ordinal=0,
                pid=os.getpid(),
                process_start="owned-process-start",
                process_executable="/usr/bin/python3",
                identity_fingerprint="owned-native-identity",
                uid=os.getuid(),
                kernel_release="test-kernel",
                historical_hwm_bytes=100,
                rss_before_reset_bytes=100,
                reset_completed_monotonic=1.0,
                post_reset_hwm_bytes=100,
                rss_after_reset_bytes=100,
                workload_start_monotonic=1.1,
                workload_end_monotonic=1.2,
                workload_start_ordinal=0,
                workload_end_ordinal=0,
                final_hwm_bytes=100,
                final_rss_bytes=100,
                growth_bytes=0,
                limit_bytes=128 * 1024 * 1024,
            ),
            NativeMemoryMeasurement(
                method="linux_proc_status_vmhwm_reset5",
                phase="updates",
                ordinal=0,
                pid=os.getpid(),
                process_start="owned-process-start",
                process_executable="/usr/bin/python3",
                identity_fingerprint="owned-native-identity",
                uid=os.getuid(),
                kernel_release="test-kernel",
                historical_hwm_bytes=100,
                rss_before_reset_bytes=100,
                reset_completed_monotonic=2.0,
                post_reset_hwm_bytes=100,
                rss_after_reset_bytes=100,
                workload_start_monotonic=2.1,
                workload_end_monotonic=2.2,
                workload_start_ordinal=1,
                workload_end_ordinal=100,
                final_hwm_bytes=100,
                final_rss_bytes=100,
                growth_bytes=0,
                limit_bytes=16 * 1024 * 1024,
            ),
        ),
        native_identity_fingerprint="owned-native-identity",
        resume_sequence=102,
        resume_crc32=0xABCE,
        resume_render=_metrics(103, phase="normal", ordinal=0),
        resume_capture_monotonic=2.0,
        capture_path=str(capture),
        xauthority=str(tmp_path / "Xauthority"),
        wine_prefix="/owned/wine",
        capture_sha256=capture_sha256,
        capture_monotonic=1.0,
        preconstruction_fingerprint="owned-preconstruction",
    )
    native.verify_seal()
    with pytest.raises(CalibrationError, match="seal|fingerprint|tamper|evidence"):
        replace(native, boot="boot-replaced").verify_seal()


def test_guardian_rejects_nonzero_delivered_modifier_state(tmp_path: Path) -> None:
    records = parse_xi2_records(FULL_XI2_TRACE, require_event=True)
    guardian = InputGuardian(tmp_path / "modifier.lock", parent_pid=os.getppid())
    try:
        generation = guardian.arm(_evidence(tmp_path))
        guardian.begin_action(
            generation,
            target_xid=TARGET,
            source_device=5,
            master_device=3,
            event_classes={
                EventClass.RAW_KEY_PRESS.value,
                EventClass.KEY_PRESS.value,
                EventClass.RAW_KEY_RELEASE.value,
                EventClass.KEY_RELEASE.value,
            },
            device_by_class={
                EventClass.RAW_KEY_PRESS.value: 3,
                EventClass.KEY_PRESS.value: 5,
                EventClass.RAW_KEY_RELEASE.value: 3,
                EventClass.KEY_RELEASE.value: 5,
            },
            detail=8,
        )
        assert guardian.observe(records[0])
        nonzero_modifier = replace(records[1], modifiers=(1, 0, 0))
        assert not guardian.observe(nonzero_modifier)
        assert not guardian.armed
    finally:
        guardian.close()


def test_guardian_close_reports_failed_release_and_keeps_fallback(tmp_path: Path) -> None:
    failed = [True]

    def release() -> None:
        if failed[0]:
            raise DriverError("native release failed")

    guardian = InputGuardian(
        tmp_path / "close-failure.lock",
        parent_pid=os.getppid(),
        release_input=release,
        watch_interval=0.01,
    )
    try:
        generation = guardian.arm(_evidence(tmp_path))
        guardian.begin_action(
            generation,
            target_xid=TARGET,
            source_device=5,
            master_device=3,
            event_classes={EventClass.KEY_PRESS.value},
            held_keys={"F13"},
        )
        guardian.publish_current_holds(generation, {"F13"}, set())
        with pytest.raises((GuardianError, DriverError), match="release|close|held"):
            guardian.close()
        assert guardian.held
        assert guardian.lease.held
    finally:
        failed[0] = False
        guardian.close()


def test_delayed_calibration_ticket_due_after_revoke_never_spawns_action(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    timers: list[object] = []

    class DeferredTimer:
        def __init__(self, _delay: float, callback, args: tuple[object, ...]):
            self.callback = callback
            self.args = args
            self.daemon = False

        def start(self) -> None:
            timers.append(self)

    monkeypatch.setattr("crowley.session.driver.threading.Timer", DeferredTimer)
    backend = RecordingBackend()
    profile = DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority"))
    driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "due.lock")
    target = OwnedWindow(
        os.getpid(),
        TARGET,
        OwnedGtkCalibrationWindow.TITLE,
        (0, 0, 480, 240),
        SimpleNamespace(poll=lambda: None),  # type: ignore[arg-type]
        frozenset({TARGET}),
        "/usr/bin/python3",
        "owned-target-start",
        TARGET + 1,
        (0, 0, 500, 260),
        frozenset({TARGET, TARGET + 1}),
    )
    try:
        driver.begin_calibration_operation()
        ticket = driver.issue_calibration_ticket(target)
        driver.queue_delayed_calibration_action(target, delay=0.25, calibration_ticket=ticket)
        assert len(timers) == 1
        driver.revoke("human response after timeout plus margin")
        timers[0].callback(*timers[0].args)  # type: ignore[attr-defined]
        assert backend.events == []
        assert driver.calibration_executions == 0
        assert driver.calibration_due_count == 1
    finally:
        driver.close()


def test_valid_calibration_ticket_executes_before_revoke(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    timers: list[object] = []

    class DeferredTimer:
        def __init__(self, _delay: float, callback, args: tuple[object, ...]):
            self.callback = callback
            self.args = args
            self.daemon = False

        def start(self) -> None:
            timers.append(self)

    monkeypatch.setattr("crowley.session.driver.threading.Timer", DeferredTimer)
    backend = RecordingBackend()
    driver = DesktopDriver(
        profile=DriverProfile(display=":test", xauthority=str(tmp_path / "Xauthority")),
        backend=backend,
        lease_path=tmp_path / "due-valid.lock",
    )
    target = _WorkflowTarget().window
    try:
        driver.begin_calibration_operation()
        ticket = driver.issue_calibration_ticket(target)
        driver.queue_delayed_calibration_action(target, delay=120.5, calibration_ticket=ticket)
        assert len(timers) == 1
        timers[0].callback(*timers[0].args)  # type: ignore[attr-defined]
        assert backend.events == [{"name": "calibration_focus", "xid": TARGET}]
        assert driver.calibration_executions == 1
        assert driver.calibration_rejected_count == 0
    finally:
        driver.close()


def test_synthetic_readiness_waits_for_open_stream_releases(tmp_path: Path) -> None:
    """A press pair cannot publish readiness while releases remain buffered."""

    read_fd, write_fd = os.pipe()
    stdout = os.fdopen(read_fd, "r", encoding="utf-8", buffering=1)
    partial = parse_xi2_records(FULL_XI2_TRACE, require_event=True)[:10]
    release = parse_xi2_records(FULL_XI2_TRACE, require_event=True)[10]
    # A complete subsequent Motion block flushes the release while the
    # observer's stdout remains open and idle.  DeviceChanged has no
    # rendered reason field in this synthetic pipe fixture, so use the
    # captured Motion record as the legal trailing block.
    trailing = replace(
        parse_xi2_records(FULL_XI2_TRACE, require_event=True)[-1],
        child_xid=TARGET,
        event_xid=TARGET,
    )
    process_events: list[XI2Event | None] = []

    class Process:
        poll_result: int | None = None

        def __init__(self) -> None:
            self.stdout = stdout

        def poll(self) -> int | None:
            return self.poll_result

        def terminate(self) -> None:
            self.poll_result = 0
            self.stdout.close()

        def wait(self, timeout: float | None = None) -> int:
            self.poll_result = 0
            return 0

        def kill(self) -> None:
            self.poll_result = -9

    process = Process()
    monitor = InputMonitor(":test", process_events.append, xauthority="Xauthority")
    monitor.observer.start = lambda: setattr(monitor.observer, "process", process)  # type: ignore[method-assign]
    window = _WorkflowTarget().window
    hierarchy = _WorkflowDriver(outside=False).input_hierarchy()
    probe_operations = (
        KeyboardProbeOperation(
            "open_chat",
            "",
            (KeyboardProbeStep("press", "Return"), KeyboardProbeStep("release", "Return")),
        ),
    )
    probe_keymap = (("Return", 36),)
    try:
        monitor.start()
        os.write(write_fd, _render_events(partial).encode())
        monitor.wait_for_event(
            lambda events: any(event.event_class is EventClass.BUTTON_PRESS for event in events),
            timeout=2,
        )
        assert not InputCalibrationWorkflow._has_synthetic(
            monitor.events(),
            window,
            5,
            4,
            hierarchy,
            keyboard_operations=probe_operations,
            keyboard_keymap=probe_keymap,
        )
        # The pipe stays open and idle after the final block; a new EVENT block
        # is supplied only to flush the complete ButtonRelease record.
        profile_events = [
            _event(
                EventClass.RAW_KEY_PRESS,
                master=3,
                source=5,
                timestamp=232008010,
                detail=36,
                child=None,
            ),
            _event(EventClass.KEY_PRESS, master=5, source=5, timestamp=232008011, detail=36),
            _event(
                EventClass.RAW_KEY_RELEASE,
                master=3,
                source=5,
                timestamp=232008012,
                detail=36,
                child=None,
            ),
            _event(EventClass.KEY_RELEASE, master=5, source=5, timestamp=232008013, detail=36),
        ]
        os.write(write_fd, _render_events([release, trailing, *profile_events]).encode())
        monitor.wait_for_event(
            lambda events: InputCalibrationWorkflow._has_synthetic(
                events,
                window,
                5,
                4,
                hierarchy,
                keyboard_operations=probe_operations,
                keyboard_keymap=probe_keymap,
            ),
            timeout=2,
        )
        assert InputCalibrationWorkflow._has_synthetic(
            monitor.events(),
            window,
            5,
            4,
            hierarchy,
            keyboard_operations=probe_operations,
            keyboard_keymap=probe_keymap,
        )
        assert process.poll() is None
    finally:
        os.close(write_fd)
        monitor.stop()
        stdout.close()


def test_calibration_human_response_budget_reaches_two_minutes_with_fake_clock() -> None:
    """The harmless due ticket cannot turn the 120-second human window into 250ms."""

    clock = [0.0]
    waits: list[float] = []
    driver = _WorkflowDriver(outside=False)
    original_start = driver.start_input_observer

    def start_observer(*, calibration: bool, callback):
        observer = original_start(calibration=calibration, callback=callback)

        def wait_for_human(predicate, *, timeout: float) -> None:
            waits.append(timeout)
            remaining = max(0.0, 119.0 - clock[0])
            clock[0] += min(timeout, remaining)
            if clock[0] >= 119.0 and not predicate(observer.events()):
                for event in observer.human:
                    observer._add(event)

        observer.wait_for_human = wait_for_human  # type: ignore[method-assign]
        return observer

    driver.start_input_observer = start_observer  # type: ignore[method-assign]
    workflow = InputCalibrationWorkflow(
        driver,
        display=":test",
        window_factory=_WorkflowTarget,
        monotonic=lambda: clock[0],
    )
    evidence = workflow.run(human_timeout=120)
    assert evidence.human_key_source == 9
    assert clock[0] >= 119.0
    assert waits
