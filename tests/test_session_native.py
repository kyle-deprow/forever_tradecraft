"""Production-path native boundary tests with controlled process and Agent fixtures.

These tests prove rejection and fencing behavior.  They do not claim that a
live desktop or human input calibration has passed.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import types
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from crowley.session.calibration import (
    _GTK_SCRIPT,
    CalibrationError,
    InputCalibrationEvidence,
    InputCalibrationWorkflow,
    LinuxProcStatusVmHwmReset5,
    NativeCalibrationEvidence,
    NativeCalibrationRunner,
    NativeMemoryArchiveReceipt,
    NativePreconstructionEvidence,
    NativeRenderObservation,
    NativeRestorationReceipt,
    NativeResumeBoundary,
    OwnedGtkCalibrationWindow,
    OwnedWindow,
    XTestInputProfile,
    _GtkStartupPending,
    _parse_xinput_profile,
    _parse_xwininfo_geometry,
    _xprop_single_frame_extents,
    _xwininfo_single_map_state,
)
from crowley.session.config import SessionConfig, load_config
from crowley.session.daemon import SessionDaemon
from crowley.session.decoder import PixelDecoder
from crowley.session.driver import (
    _EXEC_ADMISSION_WRAPPER,
    DRIVER_VERSION,
    DesktopDriver,
    DriverError,
    DriverProfile,
    NamedStateObservation,
    RecordingBackend,
    WindowIdentity,
    X11Backend,
    XI2Observer,
    _parse_xwininfo_tree,
)
from crowley.session.guardian import GuardianError, InputGuardian
from crowley.session.input_events import (
    XI2_TIMESTAMP_MASK,
    EventClass,
    InputEventError,
    RawMotionPairing,
    XI2Event,
    XI2StreamParser,
    decode_xtest_motion_transition,
    parse_xi2_records,
    xi2_timestamp_elapsed,
    xi2_timestamp_forward,
    xi2_timestamp_valid,
)
from crowley.session.model import CLI_VERSION
from crowley.session.motion import MotionError, MotionFrame
from crowley.session.protocol import decode_frame, pack_cells
from tests.test_session_input_tool import fixture_input_tool

from .wow_harness import WowClient


def test_native_region_profile_is_default_off_and_hash_pinned(tmp_path: Path) -> None:
    profile = DriverProfile(xauthority=str(tmp_path / "Xauthority"))
    profile.validate()
    assert profile.telemetry_region_executable is None
    assert profile.telemetry_region_executable_sha256 is None

    executable = tmp_path / "producer"
    executable.write_bytes(b"#!/bin/sh\nexit 0\n")
    executable.chmod(0o700)
    with pytest.raises(DriverError, match="hash does not match"):
        DriverProfile(
            xauthority=str(tmp_path / "Xauthority"),
            telemetry_region_executable=executable,
            telemetry_region_executable_sha256="0" * 64,
        ).validate()


def _write_region_config(tmp_path: Path, *, telemetry: str = "") -> Path:
    saved = tmp_path / "SavedVariables.lua"
    companion = tmp_path / "companion.json"
    data = tmp_path / "Data.lua"
    saved.write_text("", encoding="utf-8")
    companion.write_text("{}", encoding="utf-8")
    data.write_text("", encoding="utf-8")
    plan_json = "{}"
    plan_hash = hashlib.sha256(plan_json.encode()).hexdigest()
    path = tmp_path / "session.toml"
    path.write_text(
        "[profile]\n"
        "display = ':config-test'\n"
        "xauthority = ''\n"
        "wine_prefix = '/tmp/wine'\n"
        "canvas_crop = [80, 48, 256, 256]\n"
        "model_crop = [80, 48, 1760, 984]\n"
        "plan_hash = '" + plan_hash + "'\n"
        "plan_json = '" + plan_json + "'\n"
        "[session]\n"
        "saved_variables = '" + str(saved) + "'\n"
        "companion_state = '" + str(companion) + "'\n"
        "data_lua = '" + str(data) + "'\n" + telemetry,
        encoding="utf-8",
    )
    return path


def test_load_config_region_capability_is_default_off(tmp_path: Path) -> None:
    config = load_config(_write_region_config(tmp_path))
    assert config.telemetry_region_executable is None
    assert config.telemetry_region_executable_sha256 is None


@pytest.mark.parametrize(
    ("telemetry", "message"),
    (
        ("telemetry_region_executable = '/tmp/producer'\n", "lowercase SHA-256"),
        (
            "telemetry_region_executable = 'producer'\ntelemetry_region_executable_sha256 = '"
            + "0" * 64
            + "'\n",
            "absolute",
        ),
        (
            "telemetry_region_executable = '/tmp/producer'\ntelemetry_region_executable_sha256 = '"
            + "0" * 64
            + "'\n",
            "unavailable",
        ),
    ),
)
def test_load_config_region_capability_rejects_incomplete_or_untrusted_values(
    tmp_path: Path, telemetry: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        load_config(_write_region_config(tmp_path, telemetry=telemetry))


def test_daemon_native_region_route_is_opt_in_and_identity_bound() -> None:
    daemon = object.__new__(SessionDaemon)
    identity = SimpleNamespace(fingerprint="fresh-identity")
    calls: list[tuple[str, object, dict[str, object]]] = []

    class Driver:
        def capture_client_crop_for_identity(self, value: object, **kwargs: object) -> str:
            calls.append(("stock", value, kwargs))
            return "stock.png"

        def capture_native_region_for_identity(self, value: object, **kwargs: object) -> str:
            calls.append(("region", value, kwargs))
            return "region.png"

    daemon.driver = Driver()
    daemon.config = SimpleNamespace(profile=SimpleNamespace())
    assert daemon._native_region_enabled() is False
    assert daemon._capture_native_region_for_identity(identity) == "stock.png"

    daemon.config.profile.telemetry_region_executable = Path("/private/gnome-screenshot")
    daemon.config.profile.telemetry_region_executable_sha256 = "a" * 64
    assert daemon._native_region_enabled() is True
    assert daemon._capture_native_region_for_identity(identity, deadline=12.0) == "region.png"
    assert [call[0] for call in calls] == ["stock", "region"]
    assert calls[-1][2] == {"destination": None, "deadline_monotonic": 12.0}


def test_real_session_daemon_native_provider_route_and_stock_model_capture(
    tmp_path: Path,
) -> None:
    """Exercise SessionDaemon -> DesktopDriver -> backend -> PixelDecoder.

    The backend is an external desktop/compositor fixture: it supplies a full
    desktop raster for the stock path and the exact region for the opt-in
    producer path.  The daemon/provider, identity checks, and decoder remain
    the production implementations.  No model turn or input operation is
    started by this test.
    """

    client = WowClient()
    client.set_canonical_plan()
    client.login()
    client.publish_agent()
    identity = WindowIdentity(
        0x100,
        os.getpid(),
        "wowb.exe",
        "World of Warcraft",
        "wowb.exe",
        0x101,
        (0, 0, 1928, 1092),
        (0, 0, 1920, 1080),
        0x100,
        "capture-region",
        ":capture-region",
        "capture-region-fingerprint",
        0x100,
        0x100,
        frozenset({0x100, 0x101}),
    )

    class DesktopFixture(RecordingBackend):
        def __init__(self, *, region: Image.Image):
            super().__init__(identity=identity)
            self.region = region.copy()
            self.stock_captures = 0
            self.region_captures = 0

        def capture(self, path: Path, *, identity=None, deadline_monotonic=None):  # type: ignore[no-untyped-def]
            del deadline_monotonic
            self.stock_captures += 1
            self.captures.append(path)
            desktop = Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
            desktop.paste(self.region, (80, 48))
            desktop.save(path, format="PNG")
            return identity or self.identity

        def capture_native_region(self, path: Path, *, identity, rectangle, **kwargs):  # type: ignore[no-untyped-def]
            del rectangle, kwargs
            self.region_captures += 1
            self.region.save(path, format="PNG")
            return identity

    region = client.render_agent_capture()

    def version_fixture(root: Path) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        executable = root / "codex-version"
        executable.write_text(f"#!/bin/sh\nprintf '{CLI_VERSION}\\n'\n", encoding="ascii")
        executable.chmod(0o700)
        return executable

    def config(profile: DriverProfile, name: str) -> SessionConfig:
        plan_json = "{}"
        return SessionConfig(
            profile=profile,
            journal=tmp_path / f"{name}.json",
            socket=tmp_path / f"{name}.sock",
            capture_dir=tmp_path / f"{name}-captures",
            plan_hash=hashlib.sha256(plan_json.encode()).hexdigest(),
            plan_json=plan_json,
            codex_path=str(version_fixture(tmp_path / name)),
        )

    stock_profile = DriverProfile(
        xauthority=str(tmp_path / "Xauthority-stock"),
        client_width=1920,
        client_height=1080,
        outer_width=1928,
        outer_height=1092,
        canvas_crop=(80, 48, 256, 256),
        model_crop=(80, 48, 640, 480),
    )
    stock_backend = DesktopFixture(region=region)
    stock_driver = DesktopDriver(
        profile=stock_profile,
        backend=stock_backend,
        lease_path=tmp_path / "stock-lease.lock",
    )
    stock_daemon = SessionDaemon(config(stock_profile, "stock"), driver=stock_driver)
    try:
        stock_sample = stock_daemon.capture_status()
        assert stock_sample.kind == "FRESH"
        assert stock_sample.frame is not None
        assert stock_backend.stock_captures == 1
        assert stock_backend.region_captures == 0
        model_bytes = stock_daemon._capture_model()
        assert model_bytes
        assert stock_backend.stock_captures == 2
        assert stock_backend.region_captures == 0
    finally:
        stock_driver.close()

    executable = tmp_path / "telemetry-region"
    executable.write_bytes(b"#!/bin/sh\nexit 0\n")
    executable.chmod(0o700)
    region_profile = replace(
        stock_profile,
        telemetry_region_executable=executable,
        telemetry_region_executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
    )
    region_backend = DesktopFixture(region=region)
    region_driver = DesktopDriver(
        profile=region_profile,
        backend=region_backend,
        lease_path=tmp_path / "region-lease.lock",
    )
    region_daemon = SessionDaemon(config(region_profile, "region"), driver=region_driver)
    try:
        frame = region_daemon.motion_provider.observe(1, deadline=time.monotonic() + 5.0)
        assert frame.native.ctm_state == "disabled"
        assert frame.native.ground_state == "grounded"
        assert frame.native.speed_tuple.run == 7.0
        assert region_backend.region_captures == 1
        assert region_backend.stock_captures == 0
        assert region_daemon._native_region_enabled() is True
    finally:
        region_driver.close()


def test_real_agent_pixel_decoder_motion_frame_binds_schema3_native_capability() -> None:
    client = WowClient()
    client.set_canonical_plan()
    client.login()
    client.publish_agent()
    decoder = PixelDecoder()
    sample = decoder.decode(client.render_agent_capture(), monotonic=10.0, window_identity="native-test")
    frame = MotionFrame.from_sample(sample, SimpleNamespace(fingerprint="native-test"))
    assert frame.native.ctm_state == "disabled"
    assert frame.native.ground_state == "grounded"
    assert frame.native.speed_tuple.run == 7.0
    assert frame.native.speed_tuple.flight == 7.0
    assert frame.native.speed_tuple.swim == pytest.approx(4.7222218513489)

    broken = dict(sample.frame.snapshot.value)
    broken["motion"] = dict(broken["motion"])
    broken["motion"]["native"] = dict(broken["motion"]["native"])
    broken["motion"]["native"]["ctm"] = dict(broken["motion"]["native"]["ctm"])
    broken["motion"]["native"]["ctm"]["state"] = "enabled"
    broken_sample = replace(
        sample,
        frame=SimpleNamespace(
            boot=sample.frame.boot,
            sequence=sample.frame.sequence + 1,
            snapshot=SimpleNamespace(value=broken),
        ),
    )
    blocked = MotionFrame.from_sample(broken_sample, SimpleNamespace(fingerprint="native-test"))
    with pytest.raises(MotionError, match="capability"):
        blocked.require_native_gate()


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("ctm", "state"), []),
        (("ctm", "reason"), []),
        (("ground", "falling"), []),
        (("ground", "reason"), []),
    ),
)
def test_motion_frame_rejects_malformed_native_types(path: tuple[str, str], value: object) -> None:
    client = WowClient()
    client.set_canonical_plan()
    client.login()
    client.publish_agent()
    decoder = PixelDecoder()
    sample = decoder.decode(client.render_agent_capture(), monotonic=10.0, window_identity="native-test")
    broken = dict(sample.frame.snapshot.value)
    broken["motion"] = dict(broken["motion"])
    broken["motion"]["native"] = dict(broken["motion"]["native"])
    native = broken["motion"]["native"]
    native[path[0]] = dict(native[path[0]])
    native[path[0]][path[1]] = value
    broken_sample = replace(
        sample,
        frame=SimpleNamespace(
            boot=sample.frame.boot,
            sequence=sample.frame.sequence + 1,
            snapshot=SimpleNamespace(value=broken),
        ),
    )
    with pytest.raises(MotionError):
        MotionFrame.from_sample(broken_sample, SimpleNamespace(fingerprint="native-test"))


def test_motion_frame_reports_a_non_dict_decoded_snapshot_as_motion_error() -> None:
    sample = SimpleNamespace(
        kind="FRESH",
        frame=SimpleNamespace(snapshot=SimpleNamespace(value=[])),
        capture_monotonic=10.0,
    )
    with pytest.raises(MotionError, match="decoded snapshot"):
        MotionFrame.from_sample(sample, SimpleNamespace(fingerprint="native-test"))


TRACE = """EVENT type 13 (RawKeyPress)
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
"""


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


def _evidence() -> InputCalibrationEvidence:
    # Complete owned evidence fixture: all identity, geometry, game binding and
    # raw/delivered event facts are present so production verification stays
    # strict even in this isolated guardian test.
    proof = (
        ("RawKeyPress", 3, 5, 8, 1, None, None, None, None, None, None),
        ("KeyPress", 5, 5, 8, 1, 0x374, 0x374, 0x600119, (1.0, 1.0), (1.0, 1.0), (0, 0, 0)),
        ("RawKeyRelease", 3, 5, 8, 2, None, None, None, None, None, None),
        ("KeyRelease", 5, 5, 8, 2, 0x374, 0x374, 0x600119, (1.0, 1.0), (1.0, 1.0), (0, 0, 0)),
        ("RawMotion", 2, 4, 0, 3, None, None, None, None, None, None),
        ("Motion", 4, 4, 0, 3, 0x374, 0x374, 0x600119, (1.0, 1.0), (1.0, 1.0), (0, 0, 0)),
        ("RawButtonPress", 2, 4, 1, 3, None, None, None, None, None, None),
        ("ButtonPress", 4, 4, 1, 3, 0x374, 0x374, 0x600119, (1.0, 1.0), (1.0, 1.0), (0, 0, 0)),
        ("RawButtonRelease", 2, 4, 1, 4, None, None, None, None, None, None),
        ("ButtonRelease", 4, 4, 1, 4, 0x374, 0x374, 0x600119, (1.0, 1.0), (1.0, 1.0), (0, 0, 0)),
        ("RawKeyPress", 3, 9, 8, 5, None, None, None, None, None, None),
        ("KeyPress", 9, 9, 8, 5, 0x374, 0x374, 0x600119, (1.0, 1.0), (1.0, 1.0), (0, 0, 0)),
        ("RawKeyRelease", 3, 9, 8, 6, None, None, None, None, None, None),
        ("KeyRelease", 9, 9, 8, 6, 0x374, 0x374, 0x600119, (1.0, 1.0), (1.0, 1.0), (0, 0, 0)),
        ("RawButtonPress", 2, 7, 1, 7, None, None, None, None, None, None),
        ("ButtonPress", 7, 7, 1, 7, 0x374, 0x374, 0x600119, (1.0, 1.0), (1.0, 1.0), (0, 0, 0)),
        ("RawButtonRelease", 2, 7, 1, 8, None, None, None, None, None, None),
        ("ButtonRelease", 7, 7, 1, 8, 0x374, 0x374, 0x600119, (1.0, 1.0), (1.0, 1.0), (0, 0, 0)),
    )
    proof = tuple(
        (*record, None if record[10] is None else record[10][0] | record[10][1] | record[10][2])
        for record in proof
    )
    keyboard_profile = (
        (
            "open_chat",
            "",
            (
                ("press", "Return", 9, (0, 0, 0), 0),
                ("release", "Return", 9, (0, 0, 0), 0),
            ),
        ),
    )
    proof = (
        proof[:4]
        + (
            ("RawKeyPress", 3, 5, 9, 10, None, None, None, None, None, None, None),
            ("KeyPress", 5, 5, 9, 10, 0x374, 0x374, 0x600119, (1.0, 1.0), (1.0, 1.0), (0, 0, 0), 0),
            ("RawKeyRelease", 3, 5, 9, 11, None, None, None, None, None, None, None),
            ("KeyRelease", 5, 5, 9, 11, 0x374, 0x374, 0x600119, (1.0, 1.0), (1.0, 1.0), (0, 0, 0), 0),
        )
        + proof[4:]
    )
    return InputCalibrationEvidence._issue(
        fingerprint="owned-test-fingerprint",
        display=":test",
        target_pid=os.getpid(),
        target_xid=0x600119,
        target_child_xid=0x600119,
        synthetic_key_source=5,
        synthetic_pointer_source=4,
        human_key_source=9,
        human_pointer_source=7,
        xinput_hierarchy=(
            (4, 2, "slave", "pointer:test"),
            (5, 3, "slave", "keyboard:test"),
            (7, 2, "slave", "pointer:human"),
            (9, 3, "slave", "keyboard:human"),
        ),
        xtest_profile=_xtest_profile(
            (
                (4, 2, "slave", "pointer:test"),
                (5, 3, "slave", "keyboard:test"),
                (7, 2, "slave", "pointer:human"),
                (9, 3, "slave", "keyboard:human"),
            )
        ),
        synthetic_events=(
            ("RawKeyPress", 5, 8),
            ("KeyPress", 5, 8),
            ("RawKeyRelease", 5, 8),
            ("KeyRelease", 5, 8),
            ("RawButtonPress", 4, 1),
            ("ButtonPress", 4, 1),
            ("RawButtonRelease", 4, 1),
            ("ButtonRelease", 4, 1),
        ),
        human_events=(
            ("RawKeyPress", 9, 8),
            ("KeyPress", 9, 8),
            ("RawKeyRelease", 9, 8),
            ("KeyRelease", 9, 8),
            ("RawButtonPress", 7, 1),
            ("ButtonPress", 7, 1),
            ("RawButtonRelease", 7, 1),
            ("ButtonRelease", 7, 1),
        ),
        forwarded_events=(
            ("RawKeyPress", 9, None),
            ("KeyPress", 9, 0x600119),
            ("RawKeyRelease", 9, None),
            ("KeyRelease", 9, 0x600119),
            ("RawButtonPress", 7, None),
            ("ButtonPress", 7, 0x600119),
            ("RawButtonRelease", 7, None),
            ("ButtonRelease", 7, 0x600119),
        ),
        driver_version="test",
        xauthority="/tmp/Xauthority",
        game_identity_fingerprint="game-test-identity",
        game_geometry=(0, 0, 1920, 1080),
        target_executable="/usr/bin/python3",
        target_process_start="test-target-start",
        target_geometry=(0, 0, 480, 240),
        managed_frame_xid=0x600118,
        managed_frame_geometry=(0, 0, 500, 260),
        target_event_xids=(0x600118, 0x600119),
        synthetic_modifiers=(0, 0, 0),
        synthetic_motion_transitions=(
            (
                "XTestMotionTransition",
                3,
                4,
                4,
                2,
                0x600119,
                0x374,
                0x374,
                (1.0, 1.0),
                (1.0, 1.0),
                (2, 2),
                (2, 2),
                ((0, 2.0, 2.0), (1, 2.0, 2.0)),
                (0, 0, 0),
                0,
            ),
        ),
        synthetic_motion_query=(1, 1, 0x600119, 2, 2, 2, 2, 0x600119),
        keyboard_keymap=(("Return", 9),),
        keyboard_profile=keyboard_profile,
        event_proof=proof,
    )


def test_captured_xi2_records_require_complete_blocks_and_preserve_target() -> None:
    records = parse_xi2_records(TRACE, require_event=True)
    assert [(record.event_class, record.source_device, record.target_xid) for record in records] == [
        (EventClass.RAW_KEY_PRESS, 5, None),
        (EventClass.KEY_PRESS, 5, 0x600119),
        (EventClass.RAW_BUTTON_PRESS, 4, None),
        (EventClass.BUTTON_PRESS, 4, 0x600119),
    ]
    assert records[1].master_device == 5
    assert records[1].timestamp_ms == 232007447
    with pytest.raises(InputEventError, match="synthetic sourceid"):
        parse_xi2_records("sourceid: 4\nsourceid: 5\n", require_event=True)
    with pytest.raises(DriverError, match="timestamp"):
        XI2Observer.records("EVENT type 2 (KeyPress)\n    device: 5 (5)\n")


def test_measured_native_profile_capture_parses_through_production_parser() -> None:
    capture = json.loads(
        Path(".archive/executor-review/native-input-profile-observed.json").read_text(encoding="utf-8")
    )
    commands = {entry["name"]: entry for entry in capture["commands"]}
    profile = _parse_xinput_profile(
        commands["xinput_list_long_source"]["stdout"],
        commands["xinput_list_props_source"]["stdout"],
        ((4, 2, "slave", "Virtual core XTEST pointer"),),
        source_device=4,
        parent_device=2,
        root_xid=0x374,
        root_geometry=(0, 0, 1920, 1080),
    )
    assert profile.classes == 3
    assert profile.axes == (
        (0, "Rel X", "relative", -1.0, -1.0, 0),
        (1, "Rel Y", "relative", -1.0, -1.0, 0),
    )


def test_measured_native_profile_parser_rejects_source_axis_mode_and_ctm_drift() -> None:
    capture = json.loads(
        Path(".archive/executor-review/native-input-profile-observed.json").read_text(encoding="utf-8")
    )
    commands = {entry["name"]: entry["stdout"] for entry in capture["commands"]}
    hierarchy = ((4, 2, "slave", "Virtual core XTEST pointer"),)

    def changed(text: str, old: str, new: str) -> str:
        assert old in text
        mutated = text.replace(old, new, 1)
        assert mutated != text
        return mutated

    mutations = (
        (
            changed(commands["xinput_list_long_source"], "id=4", "id=5"),
            commands["xinput_list_props_source"],
        ),
        (
            changed(commands["xinput_list_long_source"], "Mode: relative", "Mode: absolute"),
            commands["xinput_list_props_source"],
        ),
        (
            changed(
                commands["xinput_list_long_source"],
                "Range: -1.000000 - -1.000000",
                "Range: 0.000000 - 1.000000",
            ),
            commands["xinput_list_props_source"],
        ),
        (
            commands["xinput_list_long_source"],
            changed(
                commands["xinput_list_props_source"],
                "1.000000, 0.000000",
                "2.000000, 0.000000",
            ),
        ),
        (
            changed(
                commands["xinput_list_long_source"],
                "[slave  pointer  (2)]",
                "[slave  pointer  (3)]",
            ),
            commands["xinput_list_props_source"],
        ),
        (
            changed(
                commands["xinput_list_long_source"],
                "Detail for Valuator 0:",
                "Detail for Valuator 2:",
            ),
            commands["xinput_list_props_source"],
        ),
        (
            changed(
                commands["xinput_list_long_source"],
                "Detail for Valuator 1:",
                "Detail for Valuator 0:",
            ),
            commands["xinput_list_props_source"],
        ),
        (
            changed(commands["xinput_list_long_source"], "Label: Rel X", "Label: Abs X"),
            commands["xinput_list_props_source"],
        ),
        (
            changed(commands["xinput_list_long_source"], "Reporting 3 classes:", "Reporting 4 classes:"),
            commands["xinput_list_props_source"],
        ),
    )
    for long_text, properties_text in mutations:
        with pytest.raises(CalibrationError):
            _parse_xinput_profile(
                long_text,
                properties_text,
                hierarchy,
                source_device=4,
                parent_device=2,
                root_xid=0x374,
                root_geometry=(0, 0, 1920, 1080),
            )


def test_owned_evidence_rejects_zero_displacement_baseline_and_modifier_substitution() -> None:
    evidence = _evidence()
    zero = replace(
        evidence,
        synthetic_motion_transitions=(
            (
                *evidence.synthetic_motion_transitions[0][:10],
                (1, 1),
                (1, 1),
                evidence.synthetic_motion_transitions[0][12],
                evidence.synthetic_motion_transitions[0][13],
                evidence.synthetic_motion_transitions[0][14],
            ),
        ),
        synthetic_motion_query=(1, 1, 0x600119, 1, 1, 1, 1, 0x600119),
        fingerprint="",
    )
    zero = replace(zero, fingerprint=zero.content_fingerprint()).with_hash()
    with pytest.raises(CalibrationError, match="nonzero|displacement"):
        zero.verify_seal()

    transition = evidence.synthetic_motion_transitions[0]
    for field, value in ((13, (1, 0, 0)), (14, 1)):
        modified_transition = (*transition[:field], value, *transition[field + 1 :])
        modified = replace(
            evidence,
            synthetic_motion_transitions=(modified_transition,),
            fingerprint="",
        )
        modified = replace(modified, fingerprint=modified.content_fingerprint()).with_hash()
        with pytest.raises(CalibrationError, match="modifiers"):
            modified.verify_seal()


def test_owned_evidence_rejects_refingerprinted_transition_query_and_pairing_tampering() -> None:
    evidence = _evidence()

    def resign(**changes: object) -> InputCalibrationEvidence:
        candidate = replace(evidence, **changes, fingerprint="")
        return replace(candidate, fingerprint=candidate.content_fingerprint()).with_hash()

    transition = evidence.synthetic_motion_transitions[0]
    with pytest.raises(CalibrationError, match="transition|event proof"):
        resign(synthetic_motion_transitions=((*transition[:6], 0x375, *transition[7:]),)).verify_seal()
    with pytest.raises(CalibrationError, match="transition ancestry"):
        resign(synthetic_motion_transitions=((*transition[:7], 0x375, *transition[8:]),)).verify_seal()
    with pytest.raises(CalibrationError, match="malformed|post-query|requested"):
        resign(synthetic_motion_query=(1, 1, 0x600119, 2, 2, 3, 3, 0x600119)).verify_seal()
    with pytest.raises(CalibrationError, match="transition|ancestry"):
        resign(synthetic_motion_transitions=((*transition[:8], (1, 2), *transition[9:]),)).verify_seal()
    raw = next(row for row in evidence.event_proof if row[0] == "RawMotion")
    primary = next(row for row in evidence.event_proof if row[0] == "Motion")
    with pytest.raises(CalibrationError, match="exactly one|one-to-one"):
        resign(event_proof=(*evidence.event_proof, raw)).verify_seal()
    with pytest.raises(CalibrationError, match="exactly one|one-to-one"):
        resign(event_proof=(*evidence.event_proof, primary)).verify_seal()
    with pytest.raises(CalibrationError, match="exactly one"):
        resign(synthetic_motion_transitions=(transition, transition)).verify_seal()
    primary_index = next(index for index, proof in enumerate(evidence.event_proof) if proof[0] == "Motion")
    primary = evidence.event_proof[primary_index]
    for field in (5, 6):
        mutated_primary = (*primary[:field], 0x375, *primary[field + 1 :])
        mutated_proof = (
            evidence.event_proof[:primary_index]
            + (mutated_primary,)
            + evidence.event_proof[primary_index + 1 :]
        )
        with pytest.raises(CalibrationError, match="absent from the event proof"):
            resign(event_proof=mutated_proof).verify_seal()


@pytest.mark.parametrize(
    ("drift", "message"),
    (("invalid-ctm", "fresh XTEST input profile is invalid"), ("root-geometry", "profile changed")),
)
def test_native_action_rejects_measured_profile_drift_before_dispatch(
    drift: str, message: str, tmp_path: Path
) -> None:
    profile = DriverProfile(display=":profile-drift", xauthority=str(tmp_path / "Xauthority"))
    hierarchy = ((4, 2, "slave", "XTEST pointer"),)
    sealed = _xtest_profile(hierarchy)
    backend = X11Backend(profile, input_tool=fixture_input_tool(tmp_path / "tool"))
    driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "profile-drift.lock")
    evidence = SimpleNamespace(xtest_profile=sealed)
    drifted = (
        replace(sealed, ctm=(2.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
        if drift == "invalid-ctm"
        else replace(sealed, root_geometry=(0, 0, 1920, 1081))
    )
    backend.xtest_input_profile = lambda _hierarchy, **_kwargs: drifted  # type: ignore[method-assign]
    try:
        with pytest.raises(DriverError, match=message):
            driver._verify_current_xtest_profile(evidence, hierarchy)
    finally:
        driver.close()


def test_native_profile_recheck_forwards_generation_and_deadline_to_queries(
    tmp_path: Path,
) -> None:
    capture = json.loads(
        Path(".archive/executor-review/native-input-profile-observed.json").read_text(encoding="utf-8")
    )
    outputs = {entry["name"]: entry["stdout"] for entry in capture["commands"]}
    hierarchy = (
        (4, 2, "slave", "Virtual core XTEST pointer"),
        (5, 3, "slave", "Virtual core XTEST keyboard"),
    )
    backend = X11Backend(
        DriverProfile(display=":profile-query", xauthority=str(tmp_path / "Xauthority")),
        input_tool=fixture_input_tool(tmp_path / "tool"),
    )
    calls: list[tuple[list[str], dict[str, object]]] = []

    def run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        key = {
            ("xinput", "list", "--long", "4"): "xinput_list_long_source",
            ("xinput", "list-props", "4"): "xinput_list_props_source",
            ("xwininfo", "-root", "-stats"): "xwininfo_root_stats",
        }[tuple(args)]
        return subprocess.CompletedProcess(args, 0, outputs[key], "")

    backend._run = run  # type: ignore[method-assign]
    try:
        backend.xtest_input_profile(hierarchy, generation=7, deadline_monotonic=12.5)
        assert len(calls) == 3
        assert all(call[1] == {"generation": 7, "deadline_monotonic": 12.5} for call in calls)
    finally:
        backend.input_tool.close()

    driver = DesktopDriver(
        profile=DriverProfile(display=":profile-query", xauthority=str(tmp_path / "Xauthority")),
        backend=X11Backend(
            DriverProfile(display=":profile-query", xauthority=str(tmp_path / "Xauthority")),
            input_tool=fixture_input_tool(tmp_path / "driver-tool"),
        ),
        lease_path=tmp_path / "profile-query.lock",
    )
    sealed = _xtest_profile(hierarchy)
    evidence = SimpleNamespace(xtest_profile=sealed)
    hierarchy_calls: list[dict[str, object]] = []
    profile_calls: list[dict[str, object]] = []
    driver.input_hierarchy = lambda **kwargs: hierarchy_calls.append(kwargs) or hierarchy  # type: ignore[method-assign]
    driver.xtest_input_profile = lambda _hierarchy, **kwargs: profile_calls.append(kwargs) or sealed  # type: ignore[method-assign]
    try:
        driver._verify_current_xtest_profile(evidence, generation=9, deadline_monotonic=13.5)
        assert hierarchy_calls == [{"generation": 9, "deadline_monotonic": 13.5}]
        assert profile_calls == [{"generation": 9, "deadline_monotonic": 13.5}]
    finally:
        driver.close()


@pytest.mark.parametrize(
    ("change", "message"),
    (
        (lambda event: replace(event, source_device=5), "device/source"),
        (lambda event: replace(event, detail=1), "detail"),
        (lambda event: replace(event, root_xid=0x375), "root window"),
        (lambda event: replace(event, event_xid=0x375), "root window"),
        (lambda event: replace(event, child_xid=0x700101), "outside"),
        (lambda event: replace(event, event_xy=(2.0, 1.0)), "origin"),
        (lambda event: replace(event, valuators=((0, 20.0, 20.0),)), "exactly valuator"),
        (
            lambda event: replace(event, valuators=((0, 20.0, 20.0), (0, 30.0, 30.0))),
            "exactly valuator",
        ),
        (lambda event: replace(event, valuators=((0, float("nan"), None), (1, 30.0, 30.0))), "finite"),
    ),
)
def test_xtest_transition_decoder_rejects_unproven_native_variants(change: object, message: str) -> None:
    valid = XI2Event(
        6,
        EventClass.MOTION,
        4,
        4,
        10,
        0,
        0x374,
        0x374,
        0x600119,
        (1.0, 2.0),
        (1.0, 2.0),
        (0, 0, 0),
        modifier_effective=0,
        valuators=((0, 20.0, 20.0), (1, 30.0, 30.0)),
    )
    candidate = change(valid)  # type: ignore[operator]
    with pytest.raises(InputEventError, match=message):
        decode_xtest_motion_transition(
            candidate,
            expected_source=4,
            expected_parent=2,
            expected_root_xid=0x374,
            expected_child_xids={0x600119},
            planned_endpoint=(20, 30),
        )


def test_xtest_transition_decoder_rejects_raw_and_nonzero_root_event_delta() -> None:
    raw = XI2Event(
        17,
        EventClass.RAW_MOTION,
        2,
        4,
        10,
        0,
        None,
        None,
        None,
        valuators=((0, 20.0, 20.0), (1, 30.0, 30.0)),
    )
    with pytest.raises(InputEventError, match="delivered Motion"):
        decode_xtest_motion_transition(
            raw,
            expected_source=4,
            expected_parent=2,
            expected_root_xid=0x374,
            expected_child_xids={0x600119},
        )
    delivered = XI2Event(
        6,
        EventClass.MOTION,
        4,
        4,
        10,
        0,
        0x374,
        0x374,
        0x600119,
        (1.0, 2.0),
        (1.0, 3.0),
        (0, 0, 0),
        modifier_effective=0,
        valuators=((0, 20.0, 20.0), (1, 30.0, 30.0)),
    )
    with pytest.raises(InputEventError, match="origin"):
        decode_xtest_motion_transition(
            delivered,
            expected_source=4,
            expected_parent=2,
            expected_root_xid=0x374,
            expected_child_xids={0x600119},
        )


def test_captured_raw_motion_is_a_complete_raw_xi2_record() -> None:
    # This is a source-derived formatter expectation, not a retained live
    # capture; the next authorized seed must preserve the complete native block.
    trace = """EVENT type 17 (RawMotion)
    device: 2 (4)
    time: 232007477
    detail: 0
    flags: 
    valuators:
         0: 873.00 (873.00)
         1: 576.00 (576.00)
"""
    records = parse_xi2_records(trace, require_event=True)
    assert len(records) == 1
    record = records[0]
    assert record.event_class is EventClass.RAW_MOTION
    assert record.is_raw
    assert record.master_device == 2
    assert record.source_device == 4
    assert record.target_xid is None
    assert record.raw_lines[-1] == "         1: 576.00 (576.00)"

    parser = XI2StreamParser()
    emitted = [
        event for line in (trace + "\n").splitlines(keepends=True) if (event := parser.feed(line)) is not None
    ]
    assert emitted[-1] is not None
    assert emitted[-1].event_class is record.event_class
    assert emitted[-1].master_device == record.master_device
    assert emitted[-1].source_device == record.source_device
    assert tuple(line.rstrip("\r\n") for line in emitted[-1].raw_lines) == record.raw_lines
    assert parser.finish() is None


def test_xi2_card32_order_and_raw_pairing_accept_wrap_reject_ambiguous_domain() -> None:
    maximum = XI2_TIMESTAMP_MASK
    assert xi2_timestamp_valid(maximum)
    assert xi2_timestamp_valid(0)
    assert not xi2_timestamp_valid(maximum + 1)
    assert xi2_timestamp_elapsed(maximum, 0) == 1
    assert xi2_timestamp_forward(maximum, 0)
    assert not xi2_timestamp_forward(0, maximum)
    assert not xi2_timestamp_forward(0, 0x80000000)

    pairing = RawMotionPairing()
    assert pairing.queue_raw(maximum)
    assert pairing.observe_delivered(maximum)
    assert pairing.queue_raw(0)
    assert pairing.observe_delivered(0)
    assert not pairing.queue_raw(maximum + 1)
    assert not pairing.queue_raw(0x80000000)
    assert not pairing.observe_delivered(maximum + 1)


@pytest.mark.parametrize("detail", (None, 1))
def test_raw_motion_requires_source_established_zero_detail(detail: int | None) -> None:
    trace = f"""EVENT type 17 (RawMotion)
    device: 2 (4)
    time: 232007477
    detail: {detail if detail is not None else 1}
    valuators:
    0: 873.00 (873.00)

"""
    if detail is None:
        trace = trace.replace("    detail: 1\n", "", 1)
    with pytest.raises(InputEventError, match="detail must be 0"):
        parse_xi2_records(trace, require_event=True)


def test_raw_motion_blank_delimiter_rejects_partial_valuator_payload() -> None:
    parser = XI2StreamParser()
    partial = """EVENT type 17 (RawMotion)
    device: 2 (4)
    time: 232007477
    detail: 0
    valuators:

"""
    with pytest.raises(InputEventError, match="missing complete valuator data"):
        for line in partial.splitlines(keepends=True):
            parser.feed(line)
    assert parser.failure_diagnostic is not None
    assert "EVENT type 17 (RawMotion)" in parser.failure_diagnostic["text"]
    assert parser.failure_diagnostic["reason"] == "RawMotion: missing complete valuator data"
    with pytest.raises(InputEventError, match="complete valuator"):
        parser.finish()


def test_raw_motion_pairing_allows_forward_pairs_with_equal_xi2_time() -> None:
    pairing = RawMotionPairing()
    assert pairing.queue_raw(17)
    assert pairing.observe_delivered(17)
    assert pairing.queue_raw(17)
    assert pairing.pending
    assert pairing.observe_delivered(17)
    assert not pairing.pending


def test_live_crossing_fields_and_idle_release_are_complete() -> None:
    trace = """EVENT type 7 (Enter)
    device: 4 (4)
    time: 7
    windows: root 0x374 event 0x374 child 0x0
    mode: NotifyGrab (detail NotifyInferior)
    modifiers: locked 0x10 latched 0 base 0 effective: 0
    root x/y: 987.00 / 595.00
    event x/y: 987.00 / 595.00
EVENT type 5 (ButtonRelease)
    device: 4 (4)
    time: 8
    detail: 1
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0x10 latched 0 base 0 effective: 0x10
    windows: root 0x374 event 0x374 child 0x600119
"""
    records = parse_xi2_records(trace, require_event=True)
    assert records[0].event_class is EventClass.ENTER
    assert records[0].child_xid == 0
    assert records[0].root_xy == (987.0, 595.0)
    assert records[0].modifier_effective == 0
    parser = XI2StreamParser()
    emitted = [event for line in trace.splitlines(keepends=True) if (event := parser.feed(line)) is not None]
    assert emitted[-1].event_class is EventClass.BUTTON_RELEASE


def test_owned_sequence_accepts_nonzero_locked_modifiers_and_rejects_changed_state() -> None:
    from crowley.session.calibration import InputCalibrationWorkflow, OwnedWindow

    trace = """EVENT type 13 (RawKeyPress)
    device: 3 (5)
    time: 1
    detail: 8
EVENT type 2 (KeyPress)
    device: 5 (5)
    time: 1
    detail: 8
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0x10 latched 0 base 0 effective: 0x10
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 14 (RawKeyRelease)
    device: 3 (5)
    time: 2
    detail: 8
EVENT type 3 (KeyRelease)
    device: 5 (5)
    time: 2
    detail: 8
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0x10 latched 0 base 0 effective: 0x10
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 17 (RawMotion)
    device: 2 (4)
    time: 3
    detail: 0
    flags: 
    valuators:
         0: 987.00 (987.00)
         1: 595.00 (595.00)
EVENT type 6 (Motion)
    device: 4 (4)
    time: 3
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0x10 latched 0 base 0 effective: 0x10
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 15 (RawButtonPress)
    device: 2 (4)
    time: 4
    detail: 1
EVENT type 4 (ButtonPress)
    device: 4 (4)
    time: 4
    detail: 1
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0x10 latched 0 base 0 effective: 0x10
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 16 (RawButtonRelease)
    device: 2 (4)
    time: 5
    detail: 1
EVENT type 5 (ButtonRelease)
    device: 4 (4)
    time: 5
    detail: 1
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0x10 latched 0 base 0 effective: 0x10
    windows: root 0x374 event 0x374 child 0x600119
"""
    records = parse_xi2_records(trace, require_event=True)
    window = OwnedWindow(
        31415,
        0x600119,
        "CROWLEY INPUT CALIBRATION ONLY",
        (0, 0, 480, 240),
        object(),  # type: ignore[arg-type]
        frozenset({0x600119}),
        "/usr/bin/python3",
        "target-start",
        0x600118,
        (0, 0, 500, 260),
        frozenset({0x600118, 0x600119}),
    )
    hierarchy = ((4, 2, "slave", "XTEST pointer"), (5, 3, "slave", "XTEST keyboard"))
    InputCalibrationWorkflow._validate_sequence(
        records,
        5,
        window,
        hierarchy,
        pointer=False,
        expected_detail=8,
        expected_modifiers=(0x10, 0, 0),
    )
    InputCalibrationWorkflow._validate_sequence(
        records,
        4,
        window,
        hierarchy,
        pointer=True,
        require_motion=True,
        expected_detail=1,
        expected_modifiers=(0x10, 0, 0),
    )
    wrong_raw_detail = [
        replace(record, detail=1) if record.event_class is EventClass.RAW_MOTION else record
        for record in records
    ]
    with pytest.raises(CalibrationError, match="raw motion detail"):
        InputCalibrationWorkflow._validate_sequence(
            wrong_raw_detail,
            4,
            window,
            hierarchy,
            pointer=True,
            require_motion=True,
            expected_detail=1,
            expected_modifiers=(0x10, 0, 0),
        )
    mismatched_raw = [
        replace(record, timestamp_ms=9) if record.event_class is EventClass.RAW_MOTION else record
        for record in records
    ]
    with pytest.raises(CalibrationError, match="timestamps|raw motion"):
        InputCalibrationWorkflow._validate_sequence(
            mismatched_raw,
            4,
            window,
            hierarchy,
            pointer=True,
            require_motion=True,
            expected_detail=1,
            expected_modifiers=(0x10, 0, 0),
        )
    changed = [
        replace(record, modifiers=(0, 0, 0), modifier_effective=0)
        if record.event_class is EventClass.KEY_RELEASE
        else record
        for record in records
    ]
    with pytest.raises(CalibrationError, match="modifier state changed"):
        InputCalibrationWorkflow._validate_sequence(
            changed,
            5,
            window,
            hierarchy,
            pointer=False,
            expected_detail=8,
            expected_modifiers=(0x10, 0, 0),
        )


def test_owned_sequence_raw_motion_pairing_is_forward_one_to_one_and_bounded() -> None:
    from crowley.session.calibration import InputCalibrationWorkflow

    pointer_trace = """EVENT type 15 (RawButtonPress)
    device: 2 (4)
    time: 1
    detail: 1
EVENT type 4 (ButtonPress)
    device: 4 (4)
    time: 1
    detail: 1
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 17 (RawMotion)
    device: 2 (4)
    time: 2
    detail: 0
    flags: 
    valuators:
         0: 987.00 (987.00)
         1: 595.00 (595.00)
EVENT type 6 (Motion)
    device: 4 (4)
    time: 2
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 16 (RawButtonRelease)
    device: 2 (4)
    time: 3
    detail: 1
EVENT type 5 (ButtonRelease)
    device: 4 (4)
    time: 3
    detail: 1
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
"""
    records = parse_xi2_records(pointer_trace, require_event=True)
    raw_index = next(
        index for index, event in enumerate(records) if event.event_class is EventClass.RAW_MOTION
    )
    motion_index = next(
        index for index, event in enumerate(records) if event.event_class is EventClass.MOTION
    )
    raw_motion = records[raw_index]

    class Window:
        def contains_xid(self, xid: int | None) -> bool:
            return xid == 0x600119

    window = Window()
    hierarchy = ((4, 2, "slave", "XTEST pointer"), (5, 3, "slave", "XTEST keyboard"))
    kwargs = {
        "pointer": True,
        "require_motion": True,
        "expected_detail": 1,
        "expected_modifiers": (0, 0, 0),
    }

    duplicate = records[:motion_index] + [raw_motion] + records[motion_index:]
    with pytest.raises(CalibrationError, match="following|one-to-one"):
        InputCalibrationWorkflow._validate_sequence(duplicate, 4, window, hierarchy, **kwargs)

    non_head_primary = [replace(raw_motion, timestamp_ms=11), replace(raw_motion, timestamp_ms=12)]
    non_head_primary.append(replace(records[motion_index], timestamp_ms=12))
    with pytest.raises(CalibrationError, match="following|one-to-one"):
        InputCalibrationWorkflow._validate_sequence(non_head_primary, 4, window, hierarchy, **kwargs)

    without_raw = records[:raw_index] + records[raw_index + 1 :]
    delivered_index = next(
        index for index, event in enumerate(without_raw) if event.event_class is EventClass.MOTION
    )
    backward = without_raw[: delivered_index + 1] + [raw_motion] + without_raw[delivered_index + 1 :]
    with pytest.raises(CalibrationError, match="forward|one-to-one|following"):
        InputCalibrationWorkflow._validate_sequence(backward, 4, window, hierarchy, **kwargs)

    overflow = records[:raw_index] + [raw_motion] * 9 + records[raw_index + 1 :]
    with pytest.raises(CalibrationError, match="forward|one-to-one"):
        InputCalibrationWorkflow._validate_sequence(overflow, 4, window, hierarchy, **kwargs)


def test_owned_sequence_raw_motion_pairing_accepts_card32_wrap() -> None:
    from crowley.session.calibration import InputCalibrationWorkflow

    pointer_trace = """EVENT type 15 (RawButtonPress)
    device: 2 (4)
    time: 4294967294
    detail: 1
EVENT type 4 (ButtonPress)
    device: 4 (4)
    time: 4294967294
    detail: 1
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 17 (RawMotion)
    device: 2 (4)
    time: 4294967295
    detail: 0
    flags: 
    valuators:
         0: 987.00 (987.00)
         1: 595.00 (595.00)
EVENT type 6 (Motion)
    device: 4 (4)
    time: 4294967295
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 17 (RawMotion)
    device: 2 (4)
    time: 0
    detail: 0
    flags: 
    valuators:
         0: 987.00 (987.00)
         1: 595.00 (595.00)
EVENT type 6 (Motion)
    device: 4 (4)
    time: 0
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 16 (RawButtonRelease)
    device: 2 (4)
    time: 1
    detail: 1
EVENT type 5 (ButtonRelease)
    device: 4 (4)
    time: 1
    detail: 1
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
"""
    records = parse_xi2_records(pointer_trace, require_event=True)

    class Window:
        def contains_xid(self, xid: int | None) -> bool:
            return xid == 0x600119

    InputCalibrationWorkflow._validate_sequence(
        records,
        4,
        Window(),
        ((4, 2, "slave", "XTEST pointer"),),
        pointer=True,
        require_motion=True,
        expected_detail=1,
        expected_modifiers=(0, 0, 0),
    )


def test_owned_sequence_raw_motion_pairing_retains_forward_arrival_clock() -> None:
    from crowley.session.calibration import InputCalibrationWorkflow

    pointer_trace = """EVENT type 15 (RawButtonPress)
    device: 2 (4)
    time: 1
    detail: 1
EVENT type 4 (ButtonPress)
    device: 4 (4)
    time: 1
    detail: 1
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 17 (RawMotion)
    device: 2 (4)
    time: 2
    detail: 0
    flags: 
    valuators:
         0: 987.00 (987.00)
         1: 595.00 (595.00)
EVENT type 6 (Motion)
    device: 4 (4)
    time: 2
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
EVENT type 16 (RawButtonRelease)
    device: 2 (4)
    time: 3
    detail: 1
EVENT type 5 (ButtonRelease)
    device: 4 (4)
    time: 3
    detail: 1
    root: 987.00/595.00
    event: 987.00/595.00
    modifiers: locked 0 latched 0 base 0 effective: 0
    windows: root 0x374 event 0x374 child 0x600119
"""
    records = parse_xi2_records(pointer_trace, require_event=True)

    class Window:
        def contains_xid(self, xid: int | None) -> bool:
            return xid == 0x600119

    raw_motion_positions = [
        index for index, event in enumerate(records) if event.event_class is EventClass.RAW_MOTION
    ]
    motion_positions = [
        index for index, event in enumerate(records) if event.event_class is EventClass.MOTION
    ]

    def retimed(raw_first: int, raw_second: int, primary_first: int, primary_second: int):
        output = []
        for index, event in enumerate(records):
            if index in raw_motion_positions:
                output.extend(
                    (
                        replace(event, timestamp_ms=raw_first),
                        replace(event, timestamp_ms=raw_second),
                    )
                )
            elif index in motion_positions:
                output.extend(
                    (
                        replace(event, timestamp_ms=primary_first),
                        replace(event, timestamp_ms=primary_second),
                    )
                )
            elif event.event_class is EventClass.RAW_BUTTON_PRESS:
                output.append(replace(event, timestamp_ms=(raw_first - 1) & XI2_TIMESTAMP_MASK))
            elif event.event_class is EventClass.BUTTON_PRESS:
                output.append(replace(event, timestamp_ms=(raw_first - 1) & XI2_TIMESTAMP_MASK))
            elif event.event_class is EventClass.RAW_BUTTON_RELEASE:
                output.append(replace(event, timestamp_ms=(primary_second + 1) & XI2_TIMESTAMP_MASK))
            elif event.event_class is EventClass.BUTTON_RELEASE:
                output.append(replace(event, timestamp_ms=(primary_second + 2) & XI2_TIMESTAMP_MASK))
            else:
                output.append(event)
        return output

    kwargs = {
        "pointer": True,
        "require_motion": True,
        "expected_detail": 1,
        "expected_modifiers": (0, 0, 0),
    }
    for values in ((11, 12, 11, 12), (XI2_TIMESTAMP_MASK, 0, XI2_TIMESTAMP_MASK, 0)):
        InputCalibrationWorkflow._validate_sequence(
            retimed(*values),
            4,
            Window(),
            ((4, 2, "slave", "XTEST pointer"),),
            **kwargs,
        )

    lagged = retimed(11, 12, 11, 12)
    first_motion = next(index for index, event in enumerate(lagged) if event.event_class is EventClass.MOTION)
    nonpending = replace(
        lagged[first_motion],
        event_class=EventClass.DEVICE_CHANGED,
        source_device=4,
        master_device=2,
        timestamp_ms=11,
        event_xid=None,
        child_xid=None,
        root_xy=None,
        event_xy=None,
        modifiers=None,
        modifier_effective=None,
    )
    with pytest.raises(CalibrationError, match="timestamps|forward"):
        InputCalibrationWorkflow._validate_sequence(
            lagged[: first_motion + 1] + [nonpending],
            4,
            Window(),
            ((4, 2, "slave", "XTEST pointer"),),
            **kwargs,
        )


def test_forwarded_motion_requires_exact_controlled_echo_pair() -> None:
    from crowley.session.calibration import InputCalibrationWorkflow, OwnedWindow
    from crowley.session.input_events import XI2Event

    window = OwnedWindow(
        31415,
        0x600119,
        "CROWLEY INPUT CALIBRATION ONLY",
        (0, 0, 480, 240),
        object(),  # type: ignore[arg-type]
        frozenset({0x600119}),
        "/usr/bin/python3",
        "target-start",
        0x600118,
        (0, 0, 500, 260),
        frozenset({0x600118, 0x600119}),
    )
    hierarchy = ((4, 2, "slave", "XTEST pointer"),)

    def motion(source: int, target: int, timestamp: int, x: float = 10.0) -> XI2Event:
        return XI2Event(
            6,
            EventClass.MOTION,
            source,
            source,
            timestamp,
            None,
            0x374,
            0x374,
            target,
            (x, 20.0),
            (x, 20.0),
            (0x10, 0, 0),
            modifier_effective=0x10,
        )

    synthetic = motion(4, 0x600119, 100)
    unrelated = motion(7, 0x1A00011, 101)
    with pytest.raises(CalibrationError, match="outside|unproven"):
        InputCalibrationWorkflow._controlled_echo_proof([synthetic, unrelated], window, 5, 4, hierarchy)

    proven = motion(7, 0x600119, 101)
    proof = InputCalibrationWorkflow._controlled_echo_proof([synthetic, proven], window, 5, 4, hierarchy)
    assert proof == (
        (
            "MotionEcho",
            101,
            7,
            7,
            0x600119,
            (10.0, 20.0),
            (10.0, 20.0),
            100,
            4,
            0x600119,
        ),
    )

    for primary_timestamp, forwarded_timestamp, accepted in (
        (XI2_TIMESTAMP_MASK, 0, True),
        (100, 350, True),
        (100, 351, False),
        (100, 50, False),
    ):
        pair = [
            motion(4, 0x600119, primary_timestamp),
            motion(7, 0x600119, forwarded_timestamp),
        ]
        if accepted:
            assert InputCalibrationWorkflow._controlled_echo_proof(pair, window, 5, 4, hierarchy)
        else:
            with pytest.raises(CalibrationError, match="exact controlled synthetic echo"):
                InputCalibrationWorkflow._controlled_echo_proof(pair, window, 5, 4, hierarchy)


def test_guardian_accepts_actual_calibration_card32_wrap_echo_proof(tmp_path: Path) -> None:
    """The real calibration proof, including MAX→0, is admitted unchanged."""

    window = OwnedWindow(
        31415,
        0x600119,
        "CROWLEY INPUT CALIBRATION ONLY",
        (0, 0, 480, 240),
        object(),  # type: ignore[arg-type]
        frozenset({0x600119}),
        "/usr/bin/python3",
        "target-start",
        0x600118,
        (0, 0, 500, 260),
        frozenset({0x600118, 0x600119}),
    )
    hierarchy = ((4, 2, "slave", "XTEST pointer"), (7, 2, "slave", "human pointer"))

    def motion(source: int, master: int, timestamp: int) -> object:
        from crowley.session.input_events import XI2Event

        return XI2Event(
            6,
            EventClass.MOTION,
            source,
            master,
            timestamp,
            None,
            0x374,
            0x374,
            0x600119,
            (10.0, 20.0),
            (10.0, 20.0),
            (0x10, 0, 0),
            modifier_effective=0x10,
        )

    proof = InputCalibrationWorkflow._controlled_echo_proof(
        [motion(4, 4, XI2_TIMESTAMP_MASK), motion(7, 7, 0)],
        window,
        5,
        4,
        hierarchy,
    )
    assert proof[0][1] == 0
    assert proof[0][7] == XI2_TIMESTAMP_MASK

    guardian = InputGuardian(tmp_path / "guardian-card32-wrap.lock", parent_pid=os.getppid())
    try:
        generation = guardian.arm(_evidence())
        action = guardian.begin_action(
            generation,
            target_xid=0x600119,
            source_device=4,
            master_device=2,
            event_classes={"Motion"},
            device_by_class={"Motion": 4},
            optional_classes={"Motion"},
            expected_modifiers=(0x10, 0, 0),
            echo_proof=proof,
        )
        assert guardian.observe(motion(4, 4, XI2_TIMESTAMP_MASK))
        assert guardian.observe(motion(7, 7, 0))
        assert action.complete
        guardian.finish_action(generation, action)
    finally:
        guardian.close()


def test_workflow_built_native_evidence_arms_and_accepts_endpoint_echo(tmp_path: Path) -> None:
    """Exercise the production evidence builder through arm and Guardian admission."""

    from crowley.session.calibration import KeyboardProbeOperation, KeyboardProbeStep
    from crowley.session.input_events import XI2Event

    base = _evidence()
    window = OwnedWindow(
        os.getpid(),
        0x600119,
        "CROWLEY INPUT CALIBRATION ONLY",
        (0, 0, 480, 240),
        object(),  # type: ignore[arg-type]
        frozenset({0x600119}),
        "/usr/bin/python3",
        "target-start",
        0x600118,
        (0, 0, 500, 260),
        frozenset({0x600118, 0x600119}),
    )
    hierarchy = base.xinput_hierarchy

    def from_proof(record: tuple[object, ...]) -> XI2Event:
        event_class = EventClass(record[0])
        type_number = {
            EventClass.RAW_KEY_PRESS: 13,
            EventClass.KEY_PRESS: 2,
            EventClass.RAW_KEY_RELEASE: 14,
            EventClass.KEY_RELEASE: 3,
            EventClass.RAW_BUTTON_PRESS: 15,
            EventClass.BUTTON_PRESS: 4,
            EventClass.RAW_BUTTON_RELEASE: 16,
            EventClass.BUTTON_RELEASE: 5,
            EventClass.RAW_MOTION: 17,
            EventClass.MOTION: 6,
        }[event_class]
        timestamp = int(record[4])
        if int(record[2]) == 4 and event_class in {EventClass.RAW_MOTION, EventClass.MOTION}:
            # The one baseline source-4 transition is placed at MAX so the
            # forwarded source-7 echo proves the CARD32 MAX-to-zero boundary.
            timestamp = XI2_TIMESTAMP_MASK
        return XI2Event(
            type_number,
            event_class,
            int(record[1]),
            int(record[2]),
            timestamp,
            record[3],  # type: ignore[arg-type]
            record[5],  # type: ignore[arg-type]
            record[6],  # type: ignore[arg-type]
            record[7],  # type: ignore[arg-type]
            record[8],  # type: ignore[arg-type]
            record[9],  # type: ignore[arg-type]
            record[10],  # type: ignore[arg-type]
            modifier_effective=record[11],  # type: ignore[arg-type]
            valuators=(
                ((0, 20.0, 20.0), (1, 30.0, 30.0))
                if event_class in {EventClass.RAW_MOTION, EventClass.MOTION} and int(record[2]) == 4
                else ()
            ),
        )

    records = [from_proof(record) for record in base.event_proof]
    first_human_pointer = next(
        index for index, event in enumerate(records) if event.source_device == base.human_pointer_source
    )
    primary_index = first_human_pointer
    forwarded_zero = XI2Event(
        6,
        EventClass.MOTION,
        7,
        7,
        0,
        0,
        0x374,
        0x374,
        0x600119,
        (20.0, 30.0),
        (20.0, 30.0),
        (0, 0, 0),
        modifier_effective=0,
    )
    records.insert(primary_index, forwarded_zero)
    profile = base.xtest_profile
    assert profile is not None
    transitions = InputCalibrationWorkflow._canonical_motion_transitions(records, window, profile)
    driver = DesktopDriver(
        profile=DriverProfile(display=":test", xauthority="/tmp/Xauthority"),
        backend=RecordingBackend(),
        lease_path=tmp_path / "workflow-built-evidence.lock",
    )
    try:

        def build(
            supplied_transitions: tuple[tuple[object, ...], ...] = transitions,
            query: tuple[int, ...] = (1, 1, 0x600119, 20, 30, 20, 30, 0x600119),
            prefix_records: list[object] = records,
        ) -> InputCalibrationEvidence:
            return InputCalibrationWorkflow._build_evidence(
                records,
                window,
                driver.driver_version,
                hierarchy=hierarchy,
                display=":test",
                xauthority="/tmp/Xauthority",
                synthetic_key_source=5,
                synthetic_pointer_source=4,
                game_identity_fingerprint="game-test-identity",
                game_geometry=(0, 0, 1920, 1080),
                target_executable="/usr/bin/python3",
                target_process_start="target-start",
                target_geometry=(0, 0, 480, 240),
                keyboard_operations=(
                    KeyboardProbeOperation(
                        "open_chat",
                        "",
                        (KeyboardProbeStep("press", "Return"), KeyboardProbeStep("release", "Return")),
                    ),
                ),
                keyboard_keymap=(("Return", 9),),
                xtest_profile=profile,
                synthetic_motion_transitions=supplied_transitions,
                synthetic_motion_query=query,
                synthetic_prefix_records=prefix_records,
            )

        with pytest.raises(CalibrationError, match="caller-supplied"):
            build(
                supplied_transitions=((*transitions[0][:10], (21, 31), (21, 31), *transitions[0][12:]),),
                query=(1, 1, 0x600119, 21, 31, 21, 31, 0x600119),
            )
        with pytest.raises(CalibrationError, match="nonzero displacement"):
            build(query=(1, 1, 0x600119, 1, 1, 1, 1, 0x600119))
        zero_prefix = [
            replace(
                event,
                valuators=((0, 1.0, 1.0), (1, 1.0, 1.0)),
            )
            if event.source_device == 4 and event.event_class in {EventClass.RAW_MOTION, EventClass.MOTION}
            else event
            for event in records
        ]
        with pytest.raises(CalibrationError, match="nonzero displacement"):
            build(prefix_records=zero_prefix)
        evidence = build()
        evidence.verify_seal()
        generation = driver.arm(evidence)
        action = driver.guardian.begin_action(
            generation,
            target_xid=0x600119,
            source_device=4,
            master_device=2,
            event_classes={EventClass.RAW_MOTION.value, EventClass.MOTION.value},
            device_by_class={EventClass.RAW_MOTION.value: 2, EventClass.MOTION.value: 4},
            optional_classes={EventClass.RAW_MOTION.value, EventClass.MOTION.value},
            expected_modifiers=(0, 0, 0),
            expected_motion_trace=((20, 30, 20, 30),),
            initial_origin=(1, 1, 1, 1),
            expected_root_xid=0x374,
            expected_event_xid=0x374,
            expected_child_xids=frozenset({0x600119}),
            canonical_motion=True,
            echo_proof=evidence.synthetic_echo_proof,
            require_motion_before_button=False,
            required_sequence=(),
        )
        baseline_raw = next(
            event
            for event in records
            if event.event_class is EventClass.RAW_MOTION and event.source_device == 4
        )
        baseline_primary = next(
            event for event in records if event.event_class is EventClass.MOTION and event.source_device == 4
        )
        assert driver.guardian.observe(baseline_raw)
        assert driver.guardian.observe(baseline_primary)
        assert driver.guardian.observe(forwarded_zero)
        assert action.complete
        driver.guardian.finish_action(generation, action)
    finally:
        driver.close()


def test_real_x11_producer_result_reaches_arm_and_guardian_max_to_zero_echo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep the producer, parser, native arm checks, and Guardian proof connected."""

    from crowley.session import driver as driver_module
    from crowley.session.calibration import KeyboardProbeOperation, KeyboardProbeStep, xinput_hierarchy
    from tests.test_session_native_regressions import _render_events as render_native_events

    capture = json.loads(
        Path(".archive/executor-review/native-input-profile-observed.json").read_text(encoding="utf-8")
    )
    outputs = {entry["name"]: entry["stdout"] for entry in capture["commands"]}
    xinput_script = tmp_path / "xinput-fixture"
    xinput_script.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        "  '--list --short') cat <<'EOF'\n" + outputs["xinput_list_short"] + "EOF\n    ;;\n"
        "  'list --long 4') cat <<'EOF'\n" + outputs["xinput_list_long_source"] + "EOF\n    ;;\n"
        "  'list-props 4') cat <<'EOF'\n" + outputs["xinput_list_props_source"] + "EOF\n    ;;\n"
        "  *) exit 97 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    xinput_script.chmod(0o700)
    xwininfo_script = tmp_path / "xwininfo-fixture"
    xwininfo_script.write_text(
        "#!/bin/sh\n"
        'if [ "$*" = "-root -stats" ]; then cat <<\'EOF\'\n' + outputs["xwininfo_root_stats"] + "EOF\n"
        "else exit 97; fi\n",
        encoding="utf-8",
    )
    xwininfo_script.chmod(0o700)
    pointer_file = tmp_path / "pointer"
    pointer_file.write_text("1 1\n", encoding="ascii")
    xdotool_source = tmp_path / "xdotool-fixture.c"
    xdotool_binary = tmp_path / "xdotool-fixture"
    xdotool_source.write_text(
        r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    const char *pointer = getenv("CROWLEY_FIXTURE_POINTER");
    if (argc < 2 || pointer == NULL) return 97;
    if (strcmp(argv[1], "getwindowgeometry") == 0) {
        puts("WINDOW=0x600119\nX=0\nY=0\nWIDTH=480\nHEIGHT=240\nSCREEN=0");
        return 0;
    }
    if (strcmp(argv[1], "getwindowfocus") == 0) {
        puts("6291737");
        return 0;
    }
    if (strcmp(argv[1], "getmouselocation") == 0) {
        FILE *stream = fopen(pointer, "r");
        int x = 0, y = 0;
        if (stream == NULL || fscanf(stream, "%d %d", &x, &y) != 2) return 97;
        if (stream != NULL) fclose(stream);
        printf("X=%d\nY=%d\nSCREEN=0\nWINDOW=0x600119\n", x, y);
        return 0;
    }
    if (strcmp(argv[1], "mousemove") == 0) {
        const char *x = argc > 2 && strcmp(argv[2], "--screen") == 0 ? argv[4] : argv[2];
        const char *y = argc > 2 && strcmp(argv[2], "--screen") == 0 ? argv[5] : argv[3];
        FILE *stream = fopen(pointer, "w");
        if (stream == NULL || x == NULL || y == NULL) return 97;
        fprintf(stream, "%s %s\n", x, y);
        fclose(stream);
        return 0;
    }
    if (strcmp(argv[1], "windowactivate") == 0 || strcmp(argv[1], "key") == 0 ||
        strcmp(argv[1], "click") == 0) return 0;
    return 97;
}
""",
        encoding="utf-8",
    )
    subprocess.run(["cc", "-O2", str(xdotool_source), "-o", str(xdotool_binary)], check=True)
    monkeypatch.setenv("CROWLEY_FIXTURE_POINTER", str(pointer_file))
    xprop_script = tmp_path / "xprop-fixture"
    xprop_script.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' 'WM_NAME(STRING) = \"CROWLEY INPUT CALIBRATION ONLY\"' "
        "'_NET_WM_PID(CARDINAL) = " + str(os.getpid()) + "'\n",
        encoding="utf-8",
    )
    xprop_script.chmod(0o700)
    real_which = driver_module.shutil.which

    def fixture_which(command: str, mode: int = os.F_OK | os.X_OK) -> str | None:
        del mode
        if command == "xinput":
            return str(xinput_script)
        if command == "xwininfo":
            return str(xwininfo_script)
        if command == "xprop":
            return str(xprop_script)
        return real_which(command)

    monkeypatch.setattr(driver_module.shutil, "which", fixture_which)
    xauthority = tmp_path / "Xauthority"
    xauthority.write_bytes(b"fixture")
    profile = DriverProfile(display=":test", xauthority=str(xauthority))
    backend = X11Backend(profile, input_tool=fixture_input_tool(tmp_path / "tool", str(xdotool_binary)))
    driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "desktop.lock")
    identity = WindowIdentity(
        0x600119,
        os.getpid(),
        "/usr/bin/python3",
        "World of Warcraft",
        "python3",
        0x600119,
        (0, 0, 1920, 1080),
        (0, 0, 1920, 1080),
        0x600119,
        "target-start",
        ":test",
        "game-test-identity",
        root_xid=0x374,
        managed_frame_xid=0x600118,
        target_event_xids=frozenset({0x600118, 0x600119}),
    )
    backend.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
    hierarchy = xinput_hierarchy(outputs["xinput_list_short"])
    window = OwnedWindow(
        os.getpid(),
        0x600119,
        "CROWLEY INPUT CALIBRATION ONLY",
        (0, 0, 480, 240),
        object(),  # type: ignore[arg-type]
        frozenset({0x600119}),
        "/usr/bin/python3",
        "target-start",
        0x600118,
        (0, 0, 500, 260),
        frozenset({0x600118, 0x600119}),
    )
    try:
        driver.begin_calibration_operation()
        ticket = driver.issue_calibration_ticket(window)
        driver.focus_calibration_target(window, calibration_ticket=ticket)
        backend.synthetic_calibration("0x600119", 20, 30, calibration_ticket=ticket)
        query = backend._last_synthetic_motion_query
        assert query == (1, 1, 0x600119, 20, 30, 20, 30, 0x600119)

        base = _evidence()
        profile_capture = backend.xtest_input_profile(hierarchy)
        assert profile_capture.root_xid == 0x374

        def from_proof(record: tuple[object, ...]) -> XI2Event:
            classes = {
                EventClass.RAW_KEY_PRESS: 13,
                EventClass.KEY_PRESS: 2,
                EventClass.RAW_KEY_RELEASE: 14,
                EventClass.KEY_RELEASE: 3,
                EventClass.RAW_BUTTON_PRESS: 15,
                EventClass.BUTTON_PRESS: 4,
                EventClass.RAW_BUTTON_RELEASE: 16,
                EventClass.BUTTON_RELEASE: 5,
                EventClass.RAW_MOTION: 17,
                EventClass.MOTION: 6,
            }
            event_class = EventClass(record[0])
            timestamp = (
                XI2_TIMESTAMP_MASK
                if int(record[2]) == 4
                and event_class
                in {
                    EventClass.RAW_MOTION,
                    EventClass.MOTION,
                }
                else int(record[4])
            )
            source4_motion = int(record[2]) == 4 and event_class in {
                EventClass.RAW_MOTION,
                EventClass.MOTION,
            }
            return XI2Event(
                classes[event_class],
                event_class,
                int(record[1]),
                int(record[2]),
                timestamp,
                record[3],  # type: ignore[arg-type]
                record[5],  # type: ignore[arg-type]
                record[6],  # type: ignore[arg-type]
                record[7],  # type: ignore[arg-type]
                (1.0, 1.0) if source4_motion and event_class is EventClass.MOTION else record[8],  # type: ignore[arg-type]
                (1.0, 1.0) if source4_motion and event_class is EventClass.MOTION else record[9],  # type: ignore[arg-type]
                record[10],  # type: ignore[arg-type]
                modifier_effective=record[11],  # type: ignore[arg-type]
                valuators=((0, 20.0, 20.0), (1, 30.0, 30.0)) if source4_motion else (),
            )

        records = [from_proof(record) for record in base.event_proof]
        forwarded_zero = XI2Event(
            6,
            EventClass.MOTION,
            7,
            7,
            0,
            0,
            0x374,
            0x374,
            0x600119,
            (20.0, 30.0),
            (20.0, 30.0),
            (0, 0, 0),
            modifier_effective=0,
        )
        records.insert(
            next(index for index, event in enumerate(records) if event.source_device == 7), forwarded_zero
        )
        for index, event in enumerate(records):
            if event.source_device == 4 and event.event_class in {
                EventClass.BUTTON_PRESS,
                EventClass.BUTTON_RELEASE,
            }:
                records[index] = replace(event, root_xy=(20.0, 30.0), event_xy=(20.0, 30.0))
            elif event.source_device == 7 and event.event_class is EventClass.MOTION:
                records[index] = replace(event, timestamp_ms=0, root_xy=(20.0, 30.0), event_xy=(20.0, 30.0))
        rendered_trace = render_native_events(records)
        records = list(parse_xi2_records(rendered_trace, require_event=True))
        transitions = InputCalibrationWorkflow._canonical_motion_transitions(records, window, profile_capture)
        keyboard_operation = KeyboardProbeOperation(
            "open_chat", "", (KeyboardProbeStep("press", "Return"), KeyboardProbeStep("release", "Return"))
        )
        evidence = InputCalibrationWorkflow._build_evidence(
            records,
            window,
            driver.driver_version,
            hierarchy=hierarchy,
            display=profile.display,
            xauthority=str(xauthority),
            synthetic_key_source=5,
            synthetic_pointer_source=4,
            game_identity_fingerprint=identity.fingerprint,
            game_geometry=identity.child_geometry,
            target_executable="/usr/bin/python3",
            target_process_start="target-start",
            target_geometry=window.geometry,
            keyboard_operations=(keyboard_operation,),
            keyboard_keymap=(("Return", 9),),
            xtest_profile=profile_capture,
            synthetic_motion_transitions=transitions,
            synthetic_motion_query=query,
            synthetic_prefix_records=records,
        )
        evidence.verify_seal()
        assert evidence.synthetic_echo_proof
        forwarded_index = next(
            index
            for index, proof in enumerate(evidence.event_proof)
            if proof[0] == "Motion" and proof[2] != evidence.synthetic_pointer_source
        )
        forwarded_proof = evidence.event_proof[forwarded_index]
        bad_forwarded = replace(
            evidence,
            event_proof=evidence.event_proof[:forwarded_index]
            + ((*forwarded_proof[:5], 0x375, *forwarded_proof[6:]),)
            + evidence.event_proof[forwarded_index + 1 :],
            fingerprint="",
        )
        bad_forwarded = replace(bad_forwarded, fingerprint=bad_forwarded.content_fingerprint()).with_hash()
        with pytest.raises(CalibrationError, match="forwarded echo root/event"):
            bad_forwarded.verify_seal()
        bad_forwarded_event = replace(
            evidence,
            event_proof=evidence.event_proof[:forwarded_index]
            + ((*forwarded_proof[:6], 0x375, *forwarded_proof[7:]),)
            + evidence.event_proof[forwarded_index + 1 :],
            fingerprint="",
        )
        bad_forwarded_event = replace(
            bad_forwarded_event,
            fingerprint=bad_forwarded_event.content_fingerprint(),
        ).with_hash()
        with pytest.raises(CalibrationError, match="forwarded echo root/event"):
            bad_forwarded_event.verify_seal()

        drift_backend = X11Backend(
            profile,
            input_tool=fixture_input_tool(tmp_path / "drift-tool", str(xdotool_binary)),
        )
        drift_driver = DesktopDriver(
            profile=profile,
            backend=drift_backend,
            lease_path=tmp_path / "drift-arm.lock",
        )
        drift_backend.xtest_input_profile = lambda _hierarchy, **_kwargs: replace(
            profile_capture, root_geometry=(0, 0, 1920, 1081)
        )  # type: ignore[method-assign]
        drift_driver.input_hierarchy = lambda **_kwargs: hierarchy  # type: ignore[method-assign]
        drift_backend.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
        try:
            with pytest.raises(DriverError, match="XTEST profile changed"):
                drift_driver.arm(evidence)
            assert not drift_driver.guardian.armed
        finally:
            drift_driver.close()

        def gated_observer_start(observer: XI2Observer) -> None:
            gate_read, gate_write = os.pipe()
            try:
                observer.process = subprocess.Popen(
                    [
                        sys.executable,
                        "-I",
                        "-S",
                        "-c",
                        _EXEC_ADMISSION_WRAPPER,
                        str(gate_read),
                        "/bin/sleep",
                        "30",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env={**os.environ, "DISPLAY": profile.display, "XAUTHORITY": str(xauthority)},
                    start_new_session=True,
                    pass_fds=(gate_read,),
                )
                os.close(gate_read)
                observer._admission_gate_write = gate_write
                observer._admission_gate = __import__(
                    "crowley.session.process_admission", fromlist=["AdmissionGate"]
                ).AdmissionGate(gate_write)
                observer._expected_executable = os.path.realpath("/bin/sleep")
                observer._expected_process_start = observer._process_start(observer.process.pid)
            except Exception:
                os.close(gate_read)
                os.close(gate_write)
                raise

        monkeypatch.setattr(XI2Observer, "start", gated_observer_start)
        generation = driver.arm(evidence)
        monitor = driver._monitor
        assert monitor is not None and monitor.alive
        action = driver.guardian.begin_action(
            generation,
            target_xid=0x600119,
            source_device=4,
            master_device=2,
            event_classes={EventClass.RAW_MOTION.value, EventClass.MOTION.value},
            device_by_class={EventClass.RAW_MOTION.value: 2, EventClass.MOTION.value: 4},
            optional_classes={EventClass.RAW_MOTION.value, EventClass.MOTION.value},
            expected_modifiers=(0, 0, 0),
            expected_motion_trace=((20, 30, 20, 30),),
            initial_origin=(1, 1, 1, 1),
            expected_root_xid=0x374,
            expected_event_xid=0x374,
            expected_child_xids=frozenset({0x600118, 0x600119}),
            canonical_motion=True,
            echo_proof=evidence.synthetic_echo_proof,
            required_sequence=(),
        )
        baseline_raw = next(event for event in records if event.event_class is EventClass.RAW_MOTION)
        baseline_primary = next(
            event for event in records if event.event_class is EventClass.MOTION and event.source_device == 4
        )
        forwarded = next(
            event for event in records if event.event_class is EventClass.MOTION and event.source_device == 7
        )
        monitor._record_event(baseline_raw)
        monitor._record_event(baseline_primary)
        monitor._record_event(forwarded)
        assert action.complete
        driver.guardian.finish_action(generation, action)
    finally:
        driver.close()


def test_guardian_revoke_increments_generation_releases_input_and_keeps_lease(tmp_path: Path) -> None:
    released: list[str] = []
    callbacks: list[tuple[str, int]] = []
    guardian = InputGuardian(
        tmp_path / "desktop.lock",
        release_input=lambda: released.append("released"),
        parent_pid=os.getppid(),
    )
    guardian.on_revoke(lambda reason, generation: callbacks.append((reason, generation)))
    generation = guardian.arm(_evidence())
    action = guardian.begin_action(
        generation,
        target_xid=0x600119,
        source_device=5,
        master_device=5,
        event_classes={EventClass.KEY_PRESS.value},
        detail=8,
    )
    assert action.generation == generation
    guardian.revoke("deliberate human takeover")
    assert guardian.generation == generation + 1
    assert released == ["released"]
    assert callbacks[-1][1] == generation + 1
    assert guardian.lease.held
    with pytest.raises(GuardianError, match="stale"):
        guardian.check(generation)
    guardian.close()


def test_guardian_releases_physical_input_before_revoke_callbacks(tmp_path: Path) -> None:
    order: list[str] = []
    guardian = InputGuardian(
        tmp_path / "revoke-order.lock",
        release_input=lambda: order.append("physical-release"),
        parent_pid=os.getppid(),
    )
    guardian.on_revoke(lambda _reason, _generation: order.append("revoke-callback"))

    class Evidence:
        is_live = True
        fingerprint = "revoke-order"

    guardian.arm(Evidence())
    with guardian._lock:
        guardian._held = True
        guardian._held_keys = {"w"}
    try:
        guardian.revoke("ordered takeover")
        assert order[:2] == ["physical-release", "revoke-callback"]
    finally:
        guardian.close()


def test_guardian_rejects_wrong_target_source_and_detail() -> None:
    guardian = InputGuardian(
        Path("/tmp") / f"crowley-native-test-{os.getpid()}.lock", parent_pid=os.getppid()
    )
    generation = guardian.arm(_evidence())
    guardian.begin_action(
        generation,
        target_xid=0x600119,
        source_device=5,
        master_device=5,
        event_classes={EventClass.KEY_PRESS.value},
        detail=8,
    )
    event = parse_xi2_records(TRACE, require_event=True)[1]
    assert guardian.observe(event)
    # A forwarded source cannot be ignored by source ID or event class.
    wrong = event.__class__(
        event.type_number,
        event.event_class,
        event.master_device,
        7,
        event.timestamp_ms,
        event.detail,
        event.root_xid,
        event.event_xid,
        event.child_xid,
        event.root_xy,
        event.event_xy,
        event.modifiers,
    )
    assert not guardian.observe(wrong)
    assert not guardian.armed
    guardian.close()


def test_guardian_correlates_actual_raw_and_delivered_device_pairs() -> None:
    guardian = InputGuardian(
        Path("/tmp") / f"crowley-native-pair-{os.getpid()}.lock", parent_pid=os.getppid()
    )
    generation = guardian.arm(_evidence())
    guardian.begin_action(
        generation,
        target_xid=0x600119,
        source_device=5,
        master_device=3,
        event_classes={EventClass.RAW_KEY_PRESS.value, EventClass.KEY_PRESS.value},
        device_by_class={EventClass.RAW_KEY_PRESS.value: 3, EventClass.KEY_PRESS.value: 5},
        target_ancestor=lambda xid: xid == 0x600119,
        detail=8,
    )
    records = parse_xi2_records(TRACE, require_event=True)
    assert records[0].master_device == 3
    assert records[1].master_device == 5
    assert guardian.observe(records[0])
    assert guardian.observe(records[1])
    assert guardian.armed
    guardian.close()


def test_guardian_correlates_pointer_device_change_and_button_pair() -> None:
    guardian = InputGuardian(
        Path("/tmp") / f"crowley-native-pointer-{os.getpid()}.lock", parent_pid=os.getppid()
    )
    generation = guardian.arm(_evidence())
    guardian.begin_action(
        generation,
        target_xid=0x600119,
        source_device=4,
        master_device=2,
        event_classes={
            EventClass.RAW_BUTTON_PRESS.value,
            EventClass.BUTTON_PRESS.value,
            EventClass.RAW_BUTTON_RELEASE.value,
            EventClass.BUTTON_RELEASE.value,
            EventClass.DEVICE_CHANGED.value,
        },
        device_by_class={
            EventClass.RAW_BUTTON_PRESS.value: 2,
            EventClass.BUTTON_PRESS.value: 4,
            EventClass.RAW_BUTTON_RELEASE.value: 2,
            EventClass.BUTTON_RELEASE.value: 4,
            EventClass.DEVICE_CHANGED.value: 2,
        },
        target_ancestor=lambda xid: xid == 0x600119,
        detail=1,
    )
    records = parse_xi2_records(TRACE, require_event=True)
    assert guardian.observe(records[2])
    assert guardian.observe(records[3])
    guardian.close()


def test_pointer_guardian_accepts_measured_motion_and_device_change_records() -> None:
    guardian = InputGuardian(
        Path("/tmp") / f"crowley-native-pointer-extra-{os.getpid()}.lock", parent_pid=os.getppid()
    )
    generation = guardian.arm(_evidence())
    guardian.begin_action(
        generation,
        target_xid=0x600119,
        source_device=4,
        master_device=2,
        event_classes={
            EventClass.DEVICE_CHANGED.value,
            EventClass.MOTION.value,
            EventClass.RAW_BUTTON_PRESS.value,
            EventClass.BUTTON_PRESS.value,
        },
        device_by_class={
            EventClass.DEVICE_CHANGED.value: 2,
            EventClass.MOTION.value: 4,
            EventClass.RAW_BUTTON_PRESS.value: 2,
            EventClass.BUTTON_PRESS.value: 4,
        },
        target_ancestor=lambda xid: xid == 0x600119,
        detail=1,
    )
    records = parse_xi2_records(TRACE, require_event=True)
    device_change = records[2].__class__(
        1,
        EventClass.DEVICE_CHANGED,
        2,
        4,
        232007470,
        None,
        None,
        None,
        None,
        None,
        None,
        (0, 0, 0),
    )
    motion = records[3].__class__(
        6,
        EventClass.MOTION,
        4,
        4,
        232007475,
        None,
        0x374,
        0x374,
        0x600119,
        None,
        None,
        (0, 0, 0),
        modifier_effective=0,
    )
    assert guardian.observe(device_change)
    assert guardian.observe(motion)
    guardian.close()


def test_delayed_owned_target_is_cancelled_before_due_time(tmp_path: Path) -> None:
    backend = RecordingBackend()
    focus_calls: list[int] = []
    backend.calibration_focus = focus_calls.append  # type: ignore[attr-defined]
    driver = DesktopDriver(backend=backend, lease_path=tmp_path / "cancel.lock")

    class LiveProcess:
        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            return None

    from crowley.session.calibration import OwnedWindow

    window = OwnedWindow(
        31415,
        0x600119,
        "CROWLEY INPUT CALIBRATION ONLY",
        (0, 0, 480, 240),
        LiveProcess(),  # type: ignore[arg-type]
        descendant_xids=frozenset({0x600119}),
        executable="/usr/bin/python3",
        process_start="delayed-target-start",
        managed_frame_xid=0x600118,
        managed_frame_geometry=(0, 0, 500, 260),
        certified_event_target_xids=frozenset({0x600118, 0x600119}),
    )
    driver.begin_calibration_operation()
    ticket = driver.issue_calibration_ticket(window)
    driver.queue_delayed_calibration_action(window, delay=0.2, calibration_ticket=ticket)
    generation = driver.guardian.generation
    driver.revoke("first human input")
    time.sleep(0.25)
    assert driver.guardian.generation == generation + 1
    assert not focus_calls
    assert driver.calibration_executions == 0
    assert driver.queued_calibration_count == 0
    driver.close()


def test_independent_watchdog_releases_on_fake_owner_death(tmp_path: Path) -> None:
    marker = tmp_path / "released"
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"H{}\n")
    os.close(write_fd)
    from crowley.session.guardian import _watchdog_entry

    _watchdog_entry(
        2**31,
        None,
        read_fd,
        0.01,
        (sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"),
        os.environ.copy(),
    )
    assert marker.exists()


def test_native_runner_uses_real_agent_bytes_and_reset5_identity_bound_updates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    profile = DriverProfile(xauthority="/tmp/Xauthority", wine_prefix="/tmp/wine")
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend.input_tool = fixture_input_tool(tmp_path / "tool")
    child = subprocess.Popen(["/bin/sleep", "30"])
    try:
        stat = Path(f"/proc/{child.pid}/stat").read_text(encoding="ascii")
        process_start = stat[stat.rfind(")") + 2 :].split()[19]
        process_executable = os.path.realpath(os.readlink(f"/proc/{child.pid}/exe"))
        identity = WindowIdentity(
            1,
            child.pid,
            # The window identity is the Windows client executable.  The
            # reset5 meter below deliberately binds the distinct Linux
            # /proc/PID/exe channel for the same harmless child.
            "WowB.exe",
            "World of Warcraft",
            "wowb.exe,wowb.exe",
            2,
            (0, 0, 1928, 1092),
            (0, 0, 1920, 1080),
            1,
            process_start,
            ":0",
            "native-test-identity",
            root_xid=0x374,
            managed_frame_xid=1,
            target_event_xids=frozenset({1, 2}),
        )
        backend.resolve_identity = lambda *, require_foreground=True: identity  # type: ignore[attr-defined]
        driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "native-run.lock")
        driver.input_hierarchy = lambda: ((4, 2, "slave", "xtest pointer"),)  # type: ignore[method-assign]
        from crowley.session.calibration import LinuxProcStatusVmHwmReset5

        clock = [1000.0]
        driver.native_memory_meter = LinuxProcStatusVmHwmReset5(
            child.pid,
            process_start=process_start,
            process_executable=process_executable,
            identity_fingerprint=identity.fingerprint,
            monotonic=lambda: clock[0],
        )
        from hashlib import sha256

        from PIL import Image

        released: list[Path] = []
        order: list[str] = []
        client = WowClient()
        client.set_canonical_plan()
        client.login()
        # Start from a published nonzero Agent count; the runner must preserve
        # this count through hold, measurement, and resume.
        client.publish_agent()

        def write_capture(path: Path) -> str:
            Image.new("RGB", (256, 256), (0, 0, 0)).save(path)
            return sha256(path.read_bytes()).hexdigest()

        def release(path: Path) -> None:
            released.append(path)
            path.unlink(missing_ok=True)

        driver.release_native_capture = release  # type: ignore[attr-defined]
        driver.notify_native_baseline_ready = lambda observed, value: order.append("ready")  # type: ignore[attr-defined]

        def archive_reset(observed: WindowIdentity, record: object) -> NativeMemoryArchiveReceipt:
            order.append("reset-archive")
            with (tmp_path / "native-memory-journal.jsonl").open("ab") as journal:
                journal.write((json.dumps(record.to_dict(), sort_keys=True) + "\n").encode("utf-8"))  # type: ignore[attr-defined]
                journal.flush()
                os.fsync(journal.fileno())
            return NativeMemoryArchiveReceipt.for_record(record, archive_id=f"reset-{len(order)}")  # type: ignore[arg-type]

        driver.notify_native_memory_reset_ready = archive_reset  # type: ignore[attr-defined]

        def hold_required(observed: WindowIdentity) -> None:
            order.append("hold-required")
            # Model the operator's response window: a normal publication may
            # arrive before the hold command takes effect.
            client.publish_agent()
            client.slash("agent hold")

        def updates_ready(observed: WindowIdentity, pending: object) -> None:
            order.append("updates-ready")
            client.slash("agent measure")

        def resume_required(observed: WindowIdentity, evidence: object) -> None:
            order.append("resume-required")
            client.slash("agent resume")

        driver.notify_native_hold_required = hold_required  # type: ignore[attr-defined]
        driver.notify_native_memory_ready = updates_ready  # type: ignore[attr-defined]
        driver.notify_native_resume_required = resume_required  # type: ignore[attr-defined]
        driver.notify_native_resume_ready = lambda observed, evidence, resumed: order.append("resume")  # type: ignore[attr-defined]
        driver.notify_native_measurement_failed = lambda observed, reason: NativeRestorationReceipt(  # type: ignore[attr-defined]
            "restoration_required", False, reason, durable=True
        )

        def preconstruction(
            observed: WindowIdentity, *, baseline_reader: object, baseline_ready: object
        ) -> NativePreconstructionEvidence:
            order.append("absence")
            path = tmp_path / "preconstruction.png"
            digest = write_capture(path)
            capture_time = clock[0]
            clock[0] += 0.1
            baseline = baseline_reader(observed.pid)  # type: ignore[operator]
            order.append("hwm")
            clock[0] += 0.2
            baseline_ready(observed.pid, baseline)  # type: ignore[operator]
            return NativePreconstructionEvidence._issue(
                identity_fingerprint=observed.fingerprint,
                process_start=observed.process_start,
                absent=True,
                baseline_id=digest,
                observed_monotonic=capture_time,
                bootstrap_release_monotonic=clock[0],
                display=observed.display,
                process_executable=observed.executable,
                window_xid=observed.xid,
                child_xid=observed.child_xid,
                geometry=observed.child_geometry,
                xauthority=profile.xauthority,
                wine_prefix=profile.wine_prefix,
                baseline_hwm_bytes=baseline,
                capture_path=str(path),
                capture_sha256=digest,
            )

        driver.native_preconstruction_provider = preconstruction  # type: ignore[attr-defined]

        def write_agent_capture(path: Path, frame_bytes: bytes) -> str:
            """Turn the real Agent surface bytes into the calibrated crop."""

            from PIL import Image

            bits = [bit for row in pack_cells(frame_bytes) for bit in row]
            image = Image.new("1", (128, 128))
            image.putdata(bits)
            image.resize((256, 256), Image.Resampling.NEAREST).convert("RGB").save(path)
            return sha256(path.read_bytes()).hexdigest()

        def provider(observed_identity: WindowIdentity, phase: str, ordinal: int) -> NativeRenderObservation:
            assert observed_identity.fingerprint == identity.fingerprint
            assert phase in {"construct", "held", "updates", "resume"}
            if phase == "held" and ordinal == 0:
                clock[0] += 0.1
            elif phase == "updates" and ordinal == 1:
                clock[0] += 0.1
            elif phase == "updates":
                client.advance_with_timers(1)
                clock[0] += 1.0
            elif phase == "held" and ordinal == 100:
                client.advance_with_timers(1)
                clock[0] += 1.0
            elif phase == "resume":
                order.append("provider-resume")
                clock[0] += 0.1
            frame_bytes = client.agent_frame
            decoded = decode_frame(frame_bytes)
            render = decoded.snapshot.value["render"]
            path = tmp_path / f"{phase}-{ordinal}.png"
            digest = write_agent_capture(path, frame_bytes)
            return NativeRenderObservation(
                render,
                identity.fingerprint,
                boot=decoded.boot,
                sequence=decoded.sequence,
                crc32=decoded.crc32,
                capture_id=digest,
                capture_path=str(path),
                capture_sha256=digest,
                capture_monotonic=clock[0],
                native_phase=render["nativePhase"],
                native_ordinal=ordinal,
            )

        driver.native_measurement_provider = provider
        evidence = NativeCalibrationRunner(driver, monotonic=lambda: clock[0]).run()
        assert order[:10] == [
            "absence",
            "reset-archive",
            "hwm",
            "ready",
            "hold-required",
            "reset-archive",
            "updates-ready",
            "resume-required",
            "provider-resume",
            "resume",
        ]
        assert evidence.sequence == 104
        assert evidence.render["nativePhase"] == "held"
        assert evidence.render["nativeOrdinal"] == 100
        assert evidence.resume_sequence == evidence.sequence + 1
        assert evidence.resume_update_count == evidence.render["updateCount"] + 1
        assert evidence.construction_update_count == 1
        assert evidence.held_update_count == 3
        assert evidence.resume_update_count == 104
        assert len(evidence.memory_measurements) == 2
        assert evidence.process_executable == "WowB.exe"
        assert all(
            measurement.process_executable == process_executable
            for measurement in evidence.memory_measurements
        )
        evidence.verify_seal()
        assert len(released) == 103
        assert len((tmp_path / "native-memory-journal.jsonl").read_bytes().splitlines()) == 2
        driver.close()
        driver.native_memory_meter.close()
    finally:
        child.terminate()
        child.wait(timeout=2)


class _NativeRunnerHarness:
    """Real Agent producer with injectable runner-boundary faults."""

    def __init__(self, tmp_path: Path, *, fault: str | None = None) -> None:
        profile = DriverProfile(xauthority="/tmp/Xauthority", wine_prefix="/tmp/wine")
        backend = object.__new__(X11Backend)
        backend.profile = profile
        backend.xauthority = profile.xauthority
        backend.input_tool = fixture_input_tool(tmp_path / "tool")
        self.child = subprocess.Popen(["/bin/sleep", "30"])
        stat = Path(f"/proc/{self.child.pid}/stat").read_text(encoding="ascii")
        process_start = stat[stat.rfind(")") + 2 :].split()[19]
        process_executable = os.path.realpath(os.readlink(f"/proc/{self.child.pid}/exe"))
        self.identity = WindowIdentity(
            1,
            self.child.pid,
            process_executable,
            "World of Warcraft",
            "wowb.exe,wowb.exe",
            2,
            (0, 0, 1928, 1092),
            (0, 0, 1920, 1080),
            1,
            process_start,
            ":0",
            "native-matrix-identity",
            root_xid=0x374,
            managed_frame_xid=1,
            target_event_xids=frozenset({1, 2}),
        )
        backend.resolve_identity = lambda require_foreground=True: self.identity  # type: ignore[attr-defined]
        self.driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "matrix.lock")
        self.driver.input_hierarchy = lambda: ((4, 2, "slave", "xtest pointer"),)  # type: ignore[method-assign]
        self.clock = [1000.0]
        self.meter = LinuxProcStatusVmHwmReset5(
            self.child.pid,
            process_start=process_start,
            process_executable=process_executable,
            identity_fingerprint=self.identity.fingerprint,
            monotonic=lambda: self.clock[0],
        )
        self.driver.native_memory_meter = self.meter
        self.tmp_path = tmp_path
        self.fault = fault
        self.released: list[Path] = []
        self.created: list[Path] = []
        self.archived: list[object] = []
        self.clear_ref_writes = 0
        self.order: list[str] = []
        self.absence_time = -1.0
        self.reset_time = -1.0
        self.release_time = -1.0
        self.preconstruction_evidence: NativePreconstructionEvidence | None = None
        self.slow_p99_marks: set[tuple[str, int]] = set()
        self.client = WowClient()
        self.client.set_canonical_plan()
        self.client.login()
        self.client.publish_agent()
        self.published_frames: dict[tuple[str, int], bytes] = {("normal", 0): self.client.agent_frame}
        if self.fault in {"slow_p99", "early_slow_late_resume"}:
            self._install_slow_p99_profile()
        self._configure()

    def _install_slow_p99_profile(self) -> None:
        original = self.client.lua.globals().debugprofilestop
        current: tuple[str, int] | None = None
        calls = 0

        def profile() -> float:
            nonlocal current, calls
            state = self.client.ns.Agent.NativeState()
            key = (str(state["phase"]), int(state["ordinal"]))
            if key != current:
                current = key
                calls = 0
            calls += 1
            value = float(original())
            slow_keys = (
                {("updates", 1), ("updates", 2)}
                if self.fault == "early_slow_late_resume"
                else {("updates", 99), ("held", 100)}
            )
            if key in slow_keys and calls == 2:
                self.slow_p99_marks.add(key)
                return value + 300.0
            return value

        self.client.lua.globals().debugprofilestop = profile

    def _configure(self) -> None:
        def release(path: Path) -> None:
            self.released.append(path)
            path.unlink(missing_ok=True)

        def archive(_identity: WindowIdentity, record: object) -> NativeMemoryArchiveReceipt:
            self.archived.append(record)
            return NativeMemoryArchiveReceipt.for_record(record, archive_id=f"matrix-{len(self.archived)}")  # type: ignore[arg-type]

        def failure(_identity: WindowIdentity, reason: str) -> NativeRestorationReceipt:
            if self.fault == "update_identity":
                self.client.slash("agent resume")
            return NativeRestorationReceipt("restoration_required", False, reason, durable=True)

        self.driver.release_native_capture = release  # type: ignore[attr-defined]
        self.driver.notify_native_memory_reset_ready = archive  # type: ignore[attr-defined]
        self.driver.notify_native_measurement_failed = failure  # type: ignore[attr-defined]
        self.driver.notify_native_baseline_ready = lambda *_args: None  # type: ignore[attr-defined]

        def hold_required(_identity: WindowIdentity) -> None:
            self.client.publish_agent()
            if self.fault == "wrong_normal:held:0":
                # Leave the real Agent in normal/0 for the requested held
                # observation.  This is a producer phase fault, not a
                # rewritten observation record.
                return
            self.client.slash("agent hold")

        def updates_ready(_identity: WindowIdentity, _pending: object) -> None:
            if self.fault == "wrong_normal:updates:1":
                # This is a real Agent transition: resume from held/0 and let
                # the requested updates/1 observation see normal/0 bytes.
                self.client.slash("agent resume")
            elif self.fault == "update_identity":
                # Leave the real Agent at held/0 so the durable failure
                # callback can restore normal/0 before the retry.
                return
            else:
                self.client.slash("agent measure")

        def resume_required(_identity: WindowIdentity, _boundary: object) -> None:
            if self.fault != "missing_resume":
                self.client.slash("agent resume")

        self.driver.notify_native_hold_required = hold_required  # type: ignore[attr-defined]
        self.driver.notify_native_memory_ready = updates_ready  # type: ignore[attr-defined]
        self.driver.notify_native_resume_required = resume_required  # type: ignore[attr-defined]
        self.driver.notify_native_resume_ready = lambda *_args: None  # type: ignore[attr-defined]

        def preconstruction(
            identity: WindowIdentity, *, baseline_reader: object, baseline_ready: object
        ) -> NativePreconstructionEvidence:
            path = self.tmp_path / f"preconstruction-{len(self.created)}.png"
            digest = self._write_blank(path)
            self.created.append(path)
            capture_time = self.clock[0]
            self.absence_time = capture_time
            self.clock[0] += 0.1
            baseline = baseline_reader(identity.pid)  # type: ignore[operator]
            assert self.meter._pending_window is not None
            self.reset_time = self.meter._pending_window.reset_completed_monotonic
            # The release timestamp is intentionally later than the absence
            # capture and reset completion.
            self.clock[0] += 0.2
            baseline_ready(identity.pid, baseline)  # type: ignore[operator]
            self.release_time = self.clock[0]
            evidence = NativePreconstructionEvidence._issue(
                identity_fingerprint=identity.fingerprint,
                process_start=identity.process_start,
                absent=True,
                baseline_id=digest,
                observed_monotonic=capture_time,
                bootstrap_release_monotonic=self.clock[0],
                display=identity.display,
                process_executable=identity.executable,
                window_xid=identity.xid,
                child_xid=identity.child_xid,
                geometry=identity.child_geometry,
                xauthority=self.driver.xauthority,
                wine_prefix=self.driver.profile.wine_prefix,
                baseline_hwm_bytes=baseline,
                capture_path=str(path),
                capture_sha256=digest,
            )
            self.preconstruction_evidence = evidence
            return evidence

        self.driver.native_preconstruction_provider = preconstruction  # type: ignore[attr-defined]
        self.driver.native_measurement_provider = self._provider

    @staticmethod
    def _write_blank(path: Path) -> str:
        from PIL import Image

        Image.new("RGB", (256, 256), (0, 0, 0)).save(path)
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _write_agent_capture(self, path: Path, frame: bytes) -> str:
        from PIL import Image

        bits = [bit for row in pack_cells(frame) for bit in row]
        image = Image.new("1", (128, 128))
        image.putdata(bits)
        image.resize((256, 256), Image.Resampling.NEAREST).convert("RGB").save(path)
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _provider(self, identity: WindowIdentity, phase: str, ordinal: int) -> NativeRenderObservation:
        assert identity.fingerprint == self.identity.fingerprint
        if self.fault == "construction_identity" and phase == "construct":
            identity_fingerprint = "foreign"
        else:
            identity_fingerprint = identity.fingerprint
        if phase == "held" and ordinal == 0:
            self.clock[0] += 0.1
        elif phase == "updates" and ordinal == 1:
            self.clock[0] += 0.1
        elif phase == "updates":
            if self.fault == "skipped_update" and ordinal == 2:
                # Run two real Agent timer publications before observing the
                # requested ordinal, leaving an actual update/3 frame.
                self.client.advance_with_timers(2)
                self.clock[0] += 2.0
            else:
                self.client.advance_with_timers(1)
                self.clock[0] += 0.1 if self.fault == "bad_cadence" and ordinal == 2 else 1.0
        elif phase == "held" and ordinal == 100:
            self.client.advance_with_timers(1)
            self.clock[0] += 1.0
            if self.fault == "wrong_normal:held:100":
                # Agent.Resume emits a real normal/0 publication after the
                # held/100 timer publication; no metadata is fabricated.
                self.client.slash("agent resume")
        elif phase == "resume":
            self.clock[0] += 0.1
            if self.fault == "early_slow_late_resume":
                # Publish one additional real normal/0 Agent frame before the
                # provider captures it.  The runner must reject this shifted
                # window instead of accepting a later rolling p99.
                self.client.publish_agent()
        frame = self.client.agent_frame
        fault = self.fault or ""
        if fault.startswith("wrong_normal:"):
            _, expected_phase, expected_ordinal = fault.split(":")
            if phase == expected_phase and ordinal == int(expected_ordinal) and expected_phase != "held":
                frame = self.published_frames[("normal", 0)]
        if self.fault in {"old_update", "cached_update"} and phase == "updates" and ordinal == 2:
            frame = self.published_frames[("updates", 1)]
        if self.fault in {"old_final", "cached_final"} and phase == "held" and ordinal == 100:
            frame = self.published_frames[("updates", 99)]
        decoded = decode_frame(frame)
        render = decoded.snapshot.value["render"]
        self.published_frames.setdefault((render["nativePhase"], render["nativeOrdinal"]), frame)
        path = self.tmp_path / f"capture-{len(self.created)}-{phase}-{ordinal}.png"
        digest = self._write_agent_capture(path, frame)
        self.created.append(path)
        if self.fault == "stale_artifact" and phase == "held" and ordinal == 0:
            path.write_bytes(b"stale")
        sequence = decoded.sequence + (
            2 if self.fault == "sequence_gap" and phase == "updates" and ordinal == 2 else 0
        )
        capture_path: str | object = str(path)
        if self.fault == "malformed_capture_path" and phase == "construct":
            path.unlink()
            capture_path = object()
        return NativeRenderObservation(
            render,
            identity_fingerprint,
            boot=decoded.boot,
            sequence=sequence,
            crc32=decoded.crc32,
            capture_id=digest,
            capture_path=capture_path,  # type: ignore[arg-type]
            capture_sha256=digest,
            capture_monotonic=self.clock[0],
            native_phase=render["nativePhase"],
            native_ordinal=render["nativeOrdinal"],
        )

    def run(self) -> NativeCalibrationEvidence:
        return NativeCalibrationRunner(self.driver, monotonic=lambda: self.clock[0]).run()

    def close(self) -> None:
        for path in self.created:
            path.unlink(missing_ok=True)
        self.driver.close()
        self.meter.close()
        self.child.terminate()
        self.child.wait(timeout=3)


@pytest.mark.parametrize(
    "fault",
    [
        "wrong_normal:held:0",
        "wrong_normal:updates:1",
        "wrong_normal:held:100",
        "skipped_update",
        "old_update",
        "old_final",
        "cached_update",
        "cached_final",
        "sequence_gap",
        "bad_cadence",
        "missing_resume",
        "stale_artifact",
        "malformed_capture_path",
    ],
)
def test_native_runner_rejects_lifecycle_matrix_and_cleans_artifacts(tmp_path: Path, fault: str) -> None:
    harness = _NativeRunnerHarness(tmp_path, fault=fault)
    try:
        with pytest.raises(CalibrationError):
            harness.run()
        assert harness.meter._pending_window is None
        assert harness.released
        assert all(not path.exists() for path in harness.created)
    finally:
        harness.close()


@pytest.mark.parametrize(
    ("fault", "message"),
    [("construction_identity", "identity"), ("malformed_capture_path", "capture path")],
)
def test_native_runner_failure_aborts_window_and_retries_same_meter(
    tmp_path: Path, fault: str, message: str
) -> None:
    harness = _NativeRunnerHarness(tmp_path, fault=fault)
    try:
        with pytest.raises(CalibrationError, match=message):
            harness.run()
        assert harness.meter._pending_window is None
        assert all(not path.exists() for path in harness.created)
        harness.fault = None
        evidence = harness.run()
        assert evidence.render["nativePhase"] == "held"
        assert harness.absence_time < harness.reset_time <= harness.release_time
        assert harness.preconstruction_evidence is not None
        with pytest.raises(CalibrationError, match="preconstruction|incomplete"):
            replace(
                harness.preconstruction_evidence,
                bootstrap_release_monotonic=harness.absence_time - 0.1,
            ).verify_seal()
        assert harness.meter._pending_window is None
        assert all(not path.exists() for path in harness.created if path != Path(evidence.capture_path))
    finally:
        harness.close()


def test_native_runner_gates_completed_resume_p99_from_real_agent_updates(tmp_path: Path) -> None:
    harness = _NativeRunnerHarness(tmp_path, fault="slow_p99")
    try:
        with pytest.raises(CalibrationError, match="completed update p99"):
            harness.run()
        assert harness.slow_p99_marks == {("updates", 99), ("held", 100)}
        assert harness.meter._pending_window is None
    finally:
        harness.close()


def test_native_runner_rejects_shifted_resume_window_from_real_agent(tmp_path: Path) -> None:
    harness = _NativeRunnerHarness(tmp_path, fault="early_slow_late_resume")
    try:
        with pytest.raises(CalibrationError, match="phase/ordinal/update count"):
            harness.run()
        assert harness.slow_p99_marks == {("updates", 1), ("updates", 2)}
        assert harness.meter._pending_window is None
        assert all(not path.exists() for path in harness.created)
    finally:
        harness.close()


def test_native_runner_update_window_failure_aborts_before_same_meter_retry(tmp_path: Path) -> None:
    harness = _NativeRunnerHarness(tmp_path, fault="update_identity")
    original_verify = harness.meter._verify_identity
    calls = 0

    def fail_after_update_reset() -> None:
        nonlocal calls
        calls += 1
        if calls == 5:
            assert harness.meter._pending_window is not None
            assert [getattr(record, "phase", None) for record in harness.archived] == [
                "construction",
                "updates",
            ]
            raise CalibrationError("identity changed after update reset")
        original_verify()

    harness.meter._verify_identity = fail_after_update_reset  # type: ignore[method-assign]
    try:
        with pytest.raises(CalibrationError, match="update reset"):
            harness.run()
        assert calls == 5
        assert harness.meter._pending_window is None
        assert [getattr(record, "phase", None) for record in harness.archived] == [
            "construction",
            "updates",
        ]
        assert all(not path.exists() for path in harness.created)
        harness.meter._verify_identity = original_verify  # type: ignore[method-assign]
        harness.fault = None
        evidence = harness.run()
        assert evidence.render["nativePhase"] == "held"
        assert harness.meter._pending_window is None
    finally:
        harness.close()


def _owned_child_identity(child: subprocess.Popen[str]) -> tuple[str, str]:
    stat = Path(f"/proc/{child.pid}/stat").read_text(encoding="ascii")
    return (
        stat[stat.rfind(")") + 2 :].split()[19],
        os.path.realpath(os.readlink(f"/proc/{child.pid}/exe")),
    )


def test_reset5_preserves_transient_peak_after_rss_falls_and_requires_two_windows() -> None:
    child = subprocess.Popen(
        [
            sys.executable,
            "-u",
            "-c",
            "import sys,time\nbuf=None\nfor line in sys.stdin:\n if line == 'alloc\\n':\n  buf=bytearray(48*1024*1024)\n  for i in range(0,len(buf),4096): buf[i]=1\n  print('allocated', flush=True)\n elif line == 'free\\n':\n  buf=None\n  print('freed', flush=True)\n elif line == 'stop\\n':\n  break\n",
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
        archived: list[object] = []

        def archive_record(record: object) -> NativeMemoryArchiveReceipt:
            archived.append(record)
            return NativeMemoryArchiveReceipt.for_record(record, archive_id=f"archive-{len(archived)}")  # type: ignore[arg-type]

        first = meter.begin_window(
            "construction",
            0,
            limit_bytes=128 * 1024 * 1024,
            before_reset=archive_record,
        )
        assert child.stdin is not None and child.stdout is not None
        child.stdin.write("alloc\n")
        child.stdin.flush()
        assert child.stdout.readline().strip() == "allocated"
        child.stdin.write("free\n")
        child.stdin.flush()
        assert child.stdout.readline().strip() == "freed"
        measurement = meter.finish_window(
            first,
            workload_start_monotonic=first.reset_completed_monotonic,
            workload_end_monotonic=time.monotonic(),
            workload_start_ordinal=0,
            workload_end_ordinal=0,
        )
        assert measurement.growth_bytes >= 32 * 1024 * 1024
        assert measurement.final_rss_bytes < measurement.final_hwm_bytes
        with pytest.raises(CalibrationError, match="bounds"):
            replace(measurement, limit_bytes=16 * 1024 * 1024).verify()
        second = meter.begin_window(
            "updates",
            0,
            limit_bytes=16 * 1024 * 1024,
            before_reset=archive_record,
        )
        assert len(archived) == 2
        for record in archived:
            record.verify()  # type: ignore[attr-defined]
        with pytest.raises(CalibrationError, match="bounds|incomplete"):
            replace(archived[0], limit_bytes=16 * 1024 * 1024).verify()  # type: ignore[arg-type]
        second_measurement = meter.finish_window(
            second,
            workload_start_monotonic=second.reset_completed_monotonic,
            workload_end_monotonic=time.monotonic(),
            workload_start_ordinal=1,
            workload_end_ordinal=100,
        )
        assert second_measurement.phase == "updates"
        with pytest.raises(CalibrationError, match="already consumed"):
            meter.finish_window(
                second,
                workload_start_monotonic=second.reset_completed_monotonic,
                workload_end_monotonic=time.monotonic(),
                workload_start_ordinal=1,
                workload_end_ordinal=100,
            )
        abandoned = meter.begin_window(
            "updates",
            0,
            limit_bytes=16 * 1024 * 1024,
            before_reset=archive_record,
        )
        meter.abort_window(abandoned)
        retry = meter.begin_window(
            "updates",
            0,
            limit_bytes=16 * 1024 * 1024,
            before_reset=archive_record,
        )
        meter.finish_window(
            retry,
            workload_start_monotonic=retry.reset_completed_monotonic,
            workload_end_monotonic=time.monotonic(),
            workload_start_ordinal=1,
            workload_end_ordinal=100,
        )
    finally:
        if child.stdin is not None:
            child.stdin.write("stop\n")
            child.stdin.flush()
        child.terminate()
        child.wait(timeout=3)
        if meter is not None:
            meter.close()


def test_reset5_rejects_identity_write_and_fsync_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    child = subprocess.Popen(["/bin/sleep", "20"])
    try:
        process_start, executable = _owned_child_identity(child)
        with pytest.raises(CalibrationError, match="identity"):
            LinuxProcStatusVmHwmReset5(
                child.pid,
                process_start="wrong-start",
                process_executable=executable,
                identity_fingerprint="owned-child",
            )
        meter = LinuxProcStatusVmHwmReset5(
            child.pid,
            process_start=process_start,
            process_executable=executable,
            identity_fingerprint="owned-child",
        )
        original_write = os.write
        monkeypatch.setattr(
            "crowley.session.calibration.os.write",
            lambda _fd, _data: (_ for _ in ()).throw(PermissionError("denied")),
        )
        with pytest.raises(CalibrationError, match="denied"):
            meter.begin_window(
                "construction",
                0,
                limit_bytes=128 * 1024 * 1024,
                before_reset=lambda record: NativeMemoryArchiveReceipt.for_record(
                    record, archive_id="denied"
                ),
            )
        monkeypatch.setattr("crowley.session.calibration.os.write", original_write)
        monkeypatch.setattr(
            "crowley.session.calibration.os.fsync", lambda _fd: (_ for _ in ()).throw(OSError(5, "fsync"))
        )
        with pytest.raises(CalibrationError, match="durable"):
            meter.begin_window(
                "construction",
                0,
                limit_bytes=128 * 1024 * 1024,
                before_reset=lambda record: NativeMemoryArchiveReceipt.for_record(record, archive_id="fsync"),
            )
        meter.close()
    finally:
        child.terminate()
        child.wait(timeout=3)


def test_reset5_archive_failure_happens_before_clear_refs_and_allows_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    child = subprocess.Popen(["/bin/sleep", "20"])
    meter: LinuxProcStatusVmHwmReset5 | None = None
    try:
        process_start, executable = _owned_child_identity(child)
        meter = LinuxProcStatusVmHwmReset5(
            child.pid,
            process_start=process_start,
            process_executable=executable,
            identity_fingerprint="archive-order",
        )
        clear_refs_opens: list[str] = []
        original_open_pid = meter._open_pid

        def observe_open(name: str, flags: int) -> int:
            if name == "clear_refs":
                clear_refs_opens.append(name)
            return original_open_pid(name, flags)

        monkeypatch.setattr(meter, "_open_pid", observe_open)

        def fail_archive(_record: object) -> NativeMemoryArchiveReceipt:
            raise CalibrationError("archive unavailable")

        with pytest.raises(CalibrationError, match="archive"):
            meter.begin_window(
                "construction",
                0,
                limit_bytes=128 * 1024 * 1024,
                before_reset=fail_archive,
            )
        assert clear_refs_opens == []
        assert meter._pending_window is None
        pending = meter.begin_window(
            "construction",
            0,
            limit_bytes=128 * 1024 * 1024,
            before_reset=lambda record: NativeMemoryArchiveReceipt.for_record(record, archive_id="retry"),
        )
        assert clear_refs_opens == ["clear_refs"]
        meter.abort_window(pending)
    finally:
        if meter is not None:
            meter.close()
        child.terminate()
        child.wait(timeout=3)


def test_reset5_post_reset_identity_failure_retains_pending_window_for_abort() -> None:
    child = subprocess.Popen(["/bin/sleep", "20"])
    meter: LinuxProcStatusVmHwmReset5 | None = None
    try:
        process_start, executable = _owned_child_identity(child)
        meter = LinuxProcStatusVmHwmReset5(
            child.pid,
            process_start=process_start,
            process_executable=executable,
            identity_fingerprint="post-reset-failure",
        )
        original_verify = meter._verify_identity
        calls = 0

        def fail_after_reset() -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise CalibrationError("identity changed after reset")
            original_verify()

        meter._verify_identity = fail_after_reset  # type: ignore[method-assign]
        with pytest.raises(CalibrationError, match="after reset"):
            meter.begin_window(
                "construction",
                0,
                limit_bytes=128 * 1024 * 1024,
                before_reset=lambda record: NativeMemoryArchiveReceipt.for_record(
                    record, archive_id="pending"
                ),
            )
        assert meter._pending_window is not None
        meter.abort_window()
        assert meter._pending_window is None
    finally:
        if meter is not None:
            meter.close()
        child.terminate()
        child.wait(timeout=3)


def test_reset5_pinned_pid_directory_replacement_writes_old_fd_only(tmp_path: Path) -> None:
    proc_root = tmp_path / "proc"
    pid = 4242
    old = proc_root / str(pid)

    def write_proc(directory: Path, *, start: str, clear_refs: str) -> None:
        directory.mkdir(parents=True)
        (directory / "status").write_text(
            f"Name:\tfake\nVmHWM:\t1 kB\nVmRSS:\t1 kB\nUid:\t{os.getuid()}\t{os.getuid()}\t{os.getuid()}\t{os.getuid()}\n",
            encoding="ascii",
        )
        # The parser reads field 22 (index 19 after the comm field).
        (directory / "stat").write_text("4242 (fake) " + " ".join(["R", *(["0"] * 18), start]) + "\n")
        (directory / "exe").symlink_to("/bin/sleep")
        (directory / "clear_refs").write_text(clear_refs, encoding="ascii")

    write_proc(old, start="old-start", clear_refs="0")
    meter = LinuxProcStatusVmHwmReset5(
        pid,
        process_start="old-start",
        process_executable="/bin/sleep",
        identity_fingerprint="pinned-proc",
        proc_root=proc_root,
    )
    try:
        old.rename(proc_root / f"{pid}.old")
        replacement = proc_root / str(pid)
        write_proc(replacement, start="replacement-start", clear_refs="replacement")
        pending = meter.begin_window(
            "construction",
            0,
            limit_bytes=128 * 1024 * 1024,
            before_reset=lambda record: NativeMemoryArchiveReceipt.for_record(record, archive_id="fixture"),
        )
        meter.abort_window(pending)
        assert (proc_root / f"{pid}.old" / "clear_refs").read_text(encoding="ascii") == "5"
        assert (replacement / "clear_refs").read_text(encoding="ascii") == "replacement"
        assert meter._start() == "old-start"
    finally:
        meter.close()


@pytest.mark.parametrize(
    ("phase", "ordinal"),
    [("normal", 1), ("held", 1), ("updates", 0), ("updates", 100), ("held", 99)],
)
def test_native_render_gate_rejects_wrong_phase_ordinal_pairs(phase: str, ordinal: int) -> None:
    metrics = {
        "constructionSeconds": 0.1,
        "updateCount": max(100, ordinal),
        "updateP99Ms": 10,
        "textureCount": 16_384,
        "effectiveScale": 1,
        "cellSize": (2, 2),
        "luaHeap": {
            "method": "collectgarbage_count",
            "available": False,
            "beforeKiB": 0,
            "afterKiB": 0,
            "netKiB": 0,
        },
        "nativePhase": phase,
        "nativeOrdinal": ordinal,
    }
    with pytest.raises(CalibrationError, match="phase|ordinal"):
        NativeCalibrationRunner._validate_metrics(metrics, minimum_updates=0)


@pytest.mark.parametrize(
    ("available", "before", "after", "net"),
    [(False, 1, 0, -1), (True, 1, 2, 0), (True, -1, 0, 1)],
)
def test_native_render_gate_rejects_invalid_lua_heap_diagnostic(
    available: bool, before: int, after: int, net: int
) -> None:
    metrics = {
        "constructionSeconds": 0.1,
        "updateCount": 100,
        "updateP99Ms": 10,
        "textureCount": 16_384,
        "effectiveScale": 1,
        "cellSize": (2, 2),
        "luaHeap": {
            "method": "collectgarbage_count",
            "available": available,
            "beforeKiB": before,
            "afterKiB": after,
            "netKiB": net,
        },
        "nativePhase": "held",
        "nativeOrdinal": 100,
    }
    with pytest.raises(CalibrationError, match="Lua heap"):
        NativeCalibrationRunner._validate_metrics(metrics, minimum_updates=100)


@pytest.mark.parametrize("capture_time", [float("nan"), float("inf"), 1.0, 11.0])
def test_native_runner_rejects_nonfinite_or_out_of_window_capture_times(capture_time: float) -> None:
    observation = NativeRenderObservation(
        {},
        "identity",
        capture_monotonic=capture_time,
    )
    with pytest.raises(CalibrationError, match="capture timestamp"):
        NativeCalibrationRunner._validate_capture_time(observation, -1.0, now=10.0)


def test_native_failure_receipt_accepts_only_durable_restoration_required_state() -> None:
    with pytest.raises(CalibrationError, match="restoration-required"):
        NativeRestorationReceipt("normal", True, "failed").verify()
    required = NativeRestorationReceipt("restoration_required", False, "retry", durable=True)
    required.verify()
    with pytest.raises(CalibrationError, match="durable"):
        NativeRestorationReceipt("restoration_required", False, "retry").verify()


def test_native_resume_boundary_type_guards_raise_calibration_error() -> None:
    render = {
        "constructionSeconds": 0.1,
        "updateCount": 100,
        "updateP99Ms": 10,
        "textureCount": 16_384,
        "effectiveScale": 1,
        "cellSize": (2, 2),
        "luaHeap": {
            "method": "collectgarbage_count",
            "available": False,
            "beforeKiB": 0,
            "afterKiB": 0,
            "netKiB": 0,
        },
        "nativePhase": "held",
        "nativeOrdinal": 100,
    }
    boundary = NativeResumeBoundary._issue(
        identity_fingerprint="identity",
        process_start="start",
        process_executable="/bin/sleep",
        boot="boot",
        sequence=10,
        crc32=1,
        update_count=100,
        capture_monotonic=10.0,
        capture_sha256="a" * 64,
        render=render,
    )
    for field, value in (
        ("sequence", "10"),
        ("crc32", object()),
        ("update_count", "100"),
        ("capture_monotonic", "10.0"),
        ("capture_sha256", object()),
        ("render", None),
        ("phase", []),
        ("ordinal", "100"),
    ):
        with pytest.raises(CalibrationError):
            replace(boundary, **{field: value}).verify()


def test_native_evidence_gates_completed_resume_p99_at_exact_250ms(tmp_path: Path) -> None:
    harness = _NativeRunnerHarness(tmp_path)
    try:
        evidence = harness.run()
        bounded_render = dict(evidence.resume_render)
        bounded_render["updateP99Ms"] = 250
        bounded = replace(evidence, resume_render=bounded_render, fingerprint="")
        bounded = replace(bounded, fingerprint=bounded.content_fingerprint()).with_hash()
        bounded.verify_seal()

        rejected_render = dict(bounded.resume_render)
        rejected_render["updateP99Ms"] = 250.1
        with pytest.raises(CalibrationError, match="completed update p99"):
            replace(bounded, resume_render=rejected_render).verify_seal()

        shifted_count = replace(
            bounded,
            resume_update_count=bounded.render["updateCount"] + 2,
            fingerprint="",
        )
        shifted_count = replace(shifted_count, fingerprint=shifted_count.content_fingerprint()).with_hash()
        with pytest.raises(CalibrationError, match="native resume frame"):
            shifted_count.verify_seal()

        shifted_sequence = replace(bounded, resume_sequence=bounded.sequence + 2, fingerprint="")
        shifted_sequence = replace(
            shifted_sequence,
            fingerprint=shifted_sequence.content_fingerprint(),
        ).with_hash()
        with pytest.raises(CalibrationError, match="native resume frame"):
            shifted_sequence.verify_seal()
    finally:
        harness.close()


def test_guardian_fake_clock_deadline_revokes_and_releases(tmp_path: Path) -> None:
    now = [10.0]
    released: list[bool] = []
    guardian = InputGuardian(
        tmp_path / "deadline.lock",
        release_input=lambda: released.append(True),
        parent_pid=os.getppid(),
        monotonic=lambda: now[0],
    )
    generation = guardian.arm(_evidence())
    guardian.begin_action(
        generation,
        target_xid=0x600119,
        source_device=5,
        master_device=5,
        event_classes={EventClass.KEY_PRESS.value},
        timeout=2.0,
    )
    now[0] = 13.0
    with pytest.raises(GuardianError, match="deadline"):
        guardian.check(generation)
    assert released == [True]
    guardian.close()


def test_driver_never_arms_from_boolean_or_copied_trace(tmp_path: Path) -> None:
    driver = DesktopDriver(backend=RecordingBackend(), lease_path=tmp_path / "driver.lock")
    with pytest.raises(DriverError, match="owned live"):
        driver.arm(True)
    with pytest.raises(DriverError, match="owned live"):
        driver.input_calibration({"syntheticSources": [4, 5]})
    with pytest.raises(DriverError, match="cannot arm"):
        driver.calibrate_input_events(TRACE)
    driver.close()


def test_named_action_requires_fresh_explicit_state_facts(tmp_path: Path) -> None:
    clock = [100.0]
    driver = DesktopDriver(
        backend=RecordingBackend(),
        lease_path=tmp_path / "named-state.lock",
        monotonic=lambda: clock[0],
    )
    identity = driver.resolve_identity()
    before = NamedStateObservation.from_facts(
        state="world",
        identity_fingerprint=identity.fingerprint,
        target_xid=identity.child_xid,
        capture_id="boot-a:frame-8",
        capture_sequence=8,
        facts={
            "scene": "world",
            "character": driver.profile.character,
            "realm": driver.profile.realm,
            "modal": "none",
            "code": "",
            "control": "world",
            "idle": "true",
        },
        source="native-addon",
        observed_monotonic=100.0,
    )
    observation = NamedStateObservation.from_facts(
        state="character_select",
        identity_fingerprint=identity.fingerprint,
        target_xid=identity.child_xid,
        capture_id="boot-a:frame-9",
        capture_sequence=9,
        facts={
            "scene": "character_select",
            "character": driver.profile.character,
            "realm": driver.profile.realm,
            "modal": "character_select",
            "code": "",
            "control": "character_list",
            "idle": "true",
        },
        source="native-visual",
        observed_monotonic=100.1,
    )
    assert driver.verify_named_action("logout", "before", before)
    assert driver.verify_named_action("logout", "after", observation)
    with pytest.raises(DriverError, match="identity-only"):
        driver._named_state_observer = lambda _identity, _state: True  # type: ignore[assignment]
        driver.verify_named_action("logout", "after")
    driver.close()


def test_owned_gtk_identity_verification_is_read_only_and_checks_identity_geometry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []
    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    client_xid = 0x03C00003
    frame_xid = 0x600192
    helper_xid = 0x600193
    frame_pid = 5717

    def stats(x: int, y: int, width: int, height: int) -> str:
        return f"Absolute upper-left X: {x}\nAbsolute upper-left Y: {y}\nWidth: {width}\nHeight: {height}\n"

    def command(args: list[str], *, display: str, xauthority: str, timeout: float = 5.0) -> str:
        calls.append(args)
        if args[:2] == ["wmctrl", "-lp"]:
            return f"{hex(client_xid)}  -1  {pid} host CROWLEY INPUT CALIBRATION ONLY\n"
        if args == ["xprop", "-id", hex(client_xid)]:
            return (
                f'WM_NAME(STRING) = "CROWLEY INPUT CALIBRATION ONLY"\n'
                f"_NET_WM_PID(CARDINAL) = {pid}\n"
                "_NET_FRAME_EXTENTS(CARDINAL) = 5, 31, 5, 38\n"
            )
        if args == ["xprop", "-id", hex(frame_xid)]:
            return (
                f"_MUTTER_FRAME_FOR(WINDOW): window id # {hex(client_xid)}\n"
                f"_NET_WM_USER_TIME_WINDOW(WINDOW): window id # {hex(helper_xid)}\n"
                f"_NET_WM_PID(CARDINAL) = {frame_pid}\n"
                'WM_CLASS(STRING) = "mutter-x11-frames", "mutter-x11-frames"\n'
            )
        if args == ["xprop", "-id", hex(helper_xid)]:
            return "_NET_WM_USER_TIME(CARDINAL) = 276992109\n"
        if args[0] == "xprop":
            raise AssertionError(args)
        if args[0] == "xwininfo":
            if "-tree" in args:
                return (
                    "xwininfo: Window id: 0x374 (the root window)\n"
                    f'  {hex(frame_xid)} "CROWLEY INPUT CALIBRATION ONLY": '
                    f'("mutter-x11-frames" "mutter-x11-frames") 602x401+692+362  +692+362\n'
                    f'    {hex(client_xid)} "CROWLEY INPUT CALIBRATION ONLY": ("-c" "-c") '
                    "480x240+61+94  +753+456\n"
                    f"      0x03c00004 (has no name): () 1x1+-1+-1  +752+455\n"
                    f"    {hex(helper_xid)} (has no name): () 1x1+-1+-1  +691+361\n"
                )
            if args == ["xwininfo", "-id", hex(frame_xid), "-stats"]:
                return stats(692, 362, 602, 401) + "Depth: 32\nBorder width: 0\nClass: InputOutput\n"
            if args == ["xwininfo", "-id", hex(client_xid), "-stats"]:
                return (
                    stats(753, 456, 480, 240)
                    + "Depth: 24\nBorder width: 0\nClass: InputOutput\nMap State: IsViewable\n"
                )
            if args == ["xwininfo", "-id", hex(helper_xid), "-stats"]:
                return (
                    stats(691, 361, 1, 1) + "Relative upper-left X: -1\nRelative upper-left Y: -1\n"
                    "Depth: 0\nBorder width: 0\nClass: InputOnly\n"
                )
            raise AssertionError(args)
        if args[:2] == ["xdotool", "windowactivate"]:
            return ""
        if args[:2] == ["xdotool", "getwindowfocus"]:
            return f"{hex(client_xid)}\n"
        raise AssertionError(args)

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == frame_pid:
            return "/usr/libexec/mutter-x11-frames", "frame-start", "mutter-x11-fram"
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="/tmp/Xauthority", command=command)
    process = object()
    window = target._verify(pid, client_xid, process)  # type: ignore[arg-type]
    assert window.pid == pid
    assert window.xid == client_xid
    assert window.managed_frame_xid == frame_xid
    assert window.geometry == (753, 456, 480, 240)
    assert window.allowed_event_target_xids == frozenset({frame_xid, client_xid, 0x03C00004})
    assert helper_xid not in window.allowed_event_target_xids
    assert window.contains_xid(frame_xid)
    assert not window.contains_xid(0x374)
    assert not any(call and call[0] == "xdotool" for call in calls)
    assert calls
    assert ["xwininfo", "-id", hex(client_xid), "-stats"] in calls
    assert ["xwininfo", "-id", hex(frame_xid), "-stats"] in calls


def test_gtk_script_requests_mouse_placement_at_the_toolkit_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    class FakeWindow:
        def set_title(self, _title: str) -> None:
            pass

        def set_default_size(self, _width: int, _height: int) -> None:
            pass

        def set_resizable(self, _resizable: bool) -> None:
            pass

        def add(self, _child: object) -> None:
            pass

        def connect(self, _signal: str, _callback: object) -> None:
            pass

        def set_position(self, position: object) -> None:
            calls.append(("set_position", position))

        def show_all(self) -> None:
            calls.append("show_all")

        def get_window(self) -> object:
            return object()

    class FakeBox:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def pack_start(self, *_args: object) -> None:
            pass

    class FakeLabel:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def set_text(self, _text: str) -> None:
            pass

    class FakeEntry:
        def set_name(self, _name: str) -> None:
            pass

        def set_placeholder_text(self, _text: str) -> None:
            pass

        def grab_focus(self) -> None:
            pass

    gi = types.ModuleType("gi")
    gi.require_version = lambda *_args: None  # type: ignore[attr-defined]
    repository = types.ModuleType("gi.repository")
    gtk = types.ModuleType("gi.repository.Gtk")
    gtk.Window = FakeWindow  # type: ignore[attr-defined]
    gtk.Box = FakeBox  # type: ignore[attr-defined]
    gtk.Label = FakeLabel  # type: ignore[attr-defined]
    gtk.Entry = FakeEntry  # type: ignore[attr-defined]
    gtk.Orientation = types.SimpleNamespace(VERTICAL=1)  # type: ignore[attr-defined]
    gtk.WindowPosition = types.SimpleNamespace(MOUSE="mouse")  # type: ignore[attr-defined]
    gtk.main_iteration_do = lambda _blocking: None  # type: ignore[attr-defined]
    gtk.main_quit = lambda: None  # type: ignore[attr-defined]
    gtk.main = lambda: None  # type: ignore[attr-defined]
    glib = types.ModuleType("gi.repository.GLib")
    glib.IO_IN = 1  # type: ignore[attr-defined]
    glib.io_add_watch = lambda *_args: None  # type: ignore[attr-defined]
    gdkx11 = types.ModuleType("gi.repository.GdkX11")
    gdkx11.X11Window = types.SimpleNamespace(get_xid=lambda _window: 0x600119)  # type: ignore[attr-defined]
    repository.Gtk = gtk  # type: ignore[attr-defined]
    repository.GLib = glib  # type: ignore[attr-defined]
    repository.GdkX11 = gdkx11  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "gi", gi)
    monkeypatch.setitem(sys.modules, "gi.repository", repository)
    monkeypatch.setitem(sys.modules, "gi.repository.Gtk", gtk)
    monkeypatch.setitem(sys.modules, "gi.repository.GLib", glib)
    monkeypatch.setitem(sys.modules, "gi.repository.GdkX11", gdkx11)
    monkeypatch.setattr(sys, "stdin", types.SimpleNamespace(fileno=lambda: 0))

    exec(_GTK_SCRIPT, {"__name__": "__main__"})
    assert calls == [("set_position", "mouse"), "show_all"]


def test_xwininfo_geometry_parser_requires_actual_stats_fields() -> None:
    stats = "Absolute upper-left X: 11\nAbsolute upper-left Y: 22\nWidth: 480\nHeight: 240\n"
    assert _parse_xwininfo_geometry(stats) == (11, 22, 480, 240)


@pytest.mark.parametrize(
    "invalid",
    [
        "Absolute upper-left X: 11\nAbsolute upper-left Y: 22\nWidth: 480\n",
        "Absolute upper-left X: 11\nAbsolute upper-left Y: 22\nWidth: 480\nWidth: 480\nHeight: 240\n",
        "Absolute upper-left X: 11\nAbsolute upper-left Y: 22\nWidth: 481\nWidth: 480\nHeight: 240\n",
        "Absolute upper-left X: 11\nAbsolute upper-left Y: 22\nWidth: 480 trailing\nHeight: 240\n",
        "Absolute upper-left X: 11\nAbsolute upper-left Y: 22\nWidth: 0\nHeight: 240\n",
        "Absolute upper-left X: 11\nAbsolute upper-left Y: 22\nWidth: 480\nHeight: -1\n",
        "  -geometry 480x240+11+22\n",
    ],
)
def test_xwininfo_geometry_parser_rejects_incomplete_or_invalid_stats(invalid: str) -> None:
    with pytest.raises(CalibrationError, match="stats"):
        _parse_xwininfo_geometry(invalid)


def test_gtk_startup_readiness_parsers_distinguish_pending_from_malformed() -> None:
    viewable = (
        "Absolute upper-left X: 753\n"
        "Absolute upper-left Y: 456\n"
        "Width: 480\n"
        "Height: 240\n"
        "Map State: IsViewable\n"
    )
    assert _xwininfo_single_map_state(viewable) == "IsViewable"
    with pytest.raises(_GtkStartupPending, match="map state"):
        _xwininfo_single_map_state(viewable.replace("Map State: IsViewable\n", ""))
    with pytest.raises(CalibrationError, match="map state"):
        _xwininfo_single_map_state(viewable + "Map State: IsViewable\n")
    frame_extents = "_NET_FRAME_EXTENTS(CARDINAL) = 5, 31, 5, 38\n"
    assert _xprop_single_frame_extents(frame_extents) == (5, 31, 5, 38)
    with pytest.raises(_GtkStartupPending, match="frame extents"):
        _xprop_single_frame_extents("")
    with pytest.raises(CalibrationError, match="frame extents"):
        _xprop_single_frame_extents(frame_extents + frame_extents)
    with pytest.raises(CalibrationError, match="frame extents"):
        _xprop_single_frame_extents("_NET_FRAME_EXTENTS(CARDINAL) = 5, nope, 5, 38\n")


def test_owned_gtk_create_pins_x11_backend_only_for_child(monkeypatch: pytest.MonkeyPatch) -> None:
    import crowley.session.calibration as calibration_module

    pid = os.getpid()
    client_xid = 0x03C00003
    frame_xid = 0x600192
    helper_xid = 0x600193
    frame_pid = 5717
    popen_calls: list[tuple[list[str], dict[str, object]]] = []

    def stats(x: int, y: int, width: int, height: int) -> str:
        return f"Absolute upper-left X: {x}\nAbsolute upper-left Y: {y}\nWidth: {width}\nHeight: {height}\n"

    def command(args: list[str], *, display: str, xauthority: str, timeout: float = 5.0) -> str:
        assert display == ":test"
        assert xauthority == "/tmp/Xauthority"
        if args == ["wmctrl", "-lp"]:
            return f"{hex(client_xid)}  -1  {pid} host CROWLEY INPUT CALIBRATION ONLY\n"
        if args == ["xprop", "-id", hex(client_xid)]:
            return (
                f'WM_NAME(STRING) = "CROWLEY INPUT CALIBRATION ONLY"\n'
                f"_NET_WM_PID(CARDINAL) = {pid}\n"
                "_NET_FRAME_EXTENTS(CARDINAL) = 5, 31, 5, 38\n"
            )
        if args == ["xprop", "-id", hex(frame_xid)]:
            return (
                f"_MUTTER_FRAME_FOR(WINDOW): window id # {hex(client_xid)}\n"
                f"_NET_WM_USER_TIME_WINDOW(WINDOW): window id # {hex(helper_xid)}\n"
                f"_NET_WM_PID(CARDINAL) = {frame_pid}\n"
                'WM_CLASS(STRING) = "mutter-x11-frames", "mutter-x11-frames"\n'
            )
        if args == ["xprop", "-id", hex(helper_xid)]:
            return "_NET_WM_USER_TIME(CARDINAL) = 276992109\n"
        if args[0] == "xprop":
            raise AssertionError(args)
        if args == ["xwininfo", "-root", "-tree"]:
            return (
                "xwininfo: Window id: 0x374 (the root window)\n"
                f'  {hex(frame_xid)} "CROWLEY INPUT CALIBRATION ONLY": '
                f'("mutter-x11-frames" "mutter-x11-frames") 602x401+692+362  +692+362\n'
                f'    {hex(client_xid)} "CROWLEY INPUT CALIBRATION ONLY": ("-c" "-c") '
                "480x240+61+94  +753+456\n"
                f"      0x03c00004 (has no name): () 1x1+-1+-1  +752+455\n"
                f"    {hex(helper_xid)} (has no name): () 1x1+-1+-1  +691+361\n"
            )
        if args == ["xwininfo", "-id", hex(frame_xid), "-stats"]:
            return stats(692, 362, 602, 401) + "Depth: 32\nBorder width: 0\nClass: InputOutput\n"
        if args == ["xwininfo", "-id", hex(client_xid), "-stats"]:
            return (
                stats(753, 456, 480, 240)
                + "Depth: 24\nBorder width: 0\nClass: InputOutput\n"
                + "Map State: IsViewable\n"
            )
        if args == ["xwininfo", "-id", hex(helper_xid), "-stats"]:
            return (
                stats(691, 361, 1, 1) + "Relative upper-left X: -1\nRelative upper-left Y: -1\n"
                "Depth: 0\nBorder width: 0\nClass: InputOnly\n"
            )
        raise AssertionError(args)

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == frame_pid:
            return "/usr/libexec/mutter-x11-frames", "frame-start", "mutter-x11-fram"
        raise AssertionError(process_pid)

    class FakeProcess:
        def __init__(self, stdout, gate_reader: int) -> None:
            self.pid = pid
            self.stdout = stdout
            self.stdin = None
            self._gate_reader = gate_reader
            self.returncode = None

        def poll(self):
            return self.returncode

        def terminate(self) -> None:
            if self._gate_reader >= 0:
                os.close(self._gate_reader)
                self._gate_reader = -1
            self.returncode = -15
            return None

        def kill(self) -> None:
            self.terminate()
            self.returncode = -9
            return None

        def wait(self, timeout: float = 2.0) -> int:
            del timeout
            if self.returncode is None:
                self.returncode = 0
            return 0

    def fake_popen(args: list[str], **kwargs):
        read_fd, write_fd = os.pipe()
        os.write(write_fd, (json.dumps({"pid": pid, "xid": client_xid}) + "\n").encode())
        os.close(write_fd)
        stdout = os.fdopen(read_fd, "r", encoding="utf-8")
        popen_calls.append((args, kwargs))
        wrapper_index = args.index(_EXEC_ADMISSION_WRAPPER)
        assert args[1:4] == ["-I", "-S", "-c"]
        gate_reader = os.dup(int(args[wrapper_index + 1]))
        return FakeProcess(stdout, gate_reader)

    monkeypatch.setenv("GDK_BACKEND", "wayland")
    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    monkeypatch.setattr(calibration_module.subprocess, "Popen", fake_popen)
    target = OwnedGtkCalibrationWindow(
        display=":test",
        xauthority="/tmp/Xauthority",
        python_executable=sys.executable,
        command=command,
    )
    window = target.create(startup_admission=lambda _pid, release: release())
    try:
        assert window.geometry == (753, 456, 480, 240)
        assert len(popen_calls) == 1
        _, kwargs = popen_calls[0]
        child_env = kwargs["env"]
        assert isinstance(child_env, dict)
        assert child_env["DISPLAY"] == ":test"
        assert child_env["XAUTHORITY"] == "/tmp/Xauthority"
        assert child_env["GDK_BACKEND"] == "x11"
        assert os.environ["GDK_BACKEND"] == "wayland"
        assert kwargs["env"] is not os.environ
    finally:
        window.process.stdout.close()


def test_owned_gtk_create_closes_admission_gate_once_on_startup_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from crowley.session.process_admission import AdmissionGate

    observed_open: list[bool] = []
    original_close = AdmissionGate.close

    def close_once(gate: AdmissionGate) -> None:
        try:
            os.fstat(gate.write_fd)
        except OSError:
            observed_open.append(False)
        else:
            observed_open.append(True)
        original_close(gate)

    monkeypatch.setattr(AdmissionGate, "close", close_once)
    target = OwnedGtkCalibrationWindow(
        display=":test",
        xauthority="/tmp/Xauthority",
        python_executable=sys.executable,
    )

    def reject_startup(_pid: int, _release: object) -> None:
        raise RuntimeError("startup rejected")

    with pytest.raises(CalibrationError, match="startup rejected"):
        target.create(startup_admission=reject_startup)
    assert observed_open == [True]


def test_captured_xwininfo_tree_uses_header_for_production_game_child_geometry() -> None:
    captured = (
        'xwininfo: Window id: 0x1800001 "World of Warcraft"\n'
        "\n"
        "  Root window id: 0x374 (the root window) (has no name)\n"
        "  Parent window id: 0x374 (the root window) (has no name)\n"
        "     1 child:\n"
        "     0x1600011 (has no name): () 1920x1080+0+0  +0+0\n"
    )
    root, parents, geometries = _parse_xwininfo_tree(captured)
    assert root == 0x1800001
    assert parents == {0x1600011: 0x1800001}
    assert geometries == {0x1600011: (0, 0, 1920, 1080)}

    named_parent = (
        "xwininfo: Window id: 0x374 (the root window) (has no name)\n"
        '  0x1800001 "World of Warcraft": ("wowb.exe" "wowb.exe") 1928x1092+0+0  +0+0\n'
        "    0x1600011 (has no name): () 1920x1080+0+0  +0+0\n"
    )
    named_root, named_parents, named_geometries = _parse_xwininfo_tree(named_parent)
    assert named_root == 0x374
    assert named_parents == {0x1800001: 0x374, 0x1600011: 0x1800001}
    assert named_geometries[0x1800001] == (0, 0, 1928, 1092)
    assert named_geometries[0x1600011] == (0, 0, 1920, 1080)

    backend = object.__new__(X11Backend)
    backend.profile = DriverProfile()
    backend._run = lambda _args, **_kwargs: SimpleNamespace(stdout=captured)  # type: ignore[attr-defined]
    assert backend._child_geometry("0x1800001", (0, 0, 1928, 1092)) == (
        0x1600011,
        (0, 0, 1920, 1080),
    )

    for invalid in (
        captured.replace("0x1800001", "0x1800002", 1),
        captured.replace(
            "     1 child:\n     0x1600011",
            "     2 children:\n     0x1600011",
        ).replace(
            "     0x1600011 (has no name): () 1920x1080+0+0  +0+0\n",
            "     0x1600011 (has no name): () 1920x1080+0+0  +0+0\n"
            "     0x1600012 (has no name): () 1920x1080+0+0  +0+0\n",
        ),
    ):
        backend._run = lambda _args, invalid=invalid, **_kwargs: SimpleNamespace(stdout=invalid)  # type: ignore[attr-defined]
        with pytest.raises(DriverError):
            backend._child_geometry("0x1800001", (0, 0, 1928, 1092))


@pytest.mark.parametrize(
    "tree",
    [
        'xwininfo: Window id: 0x1800001 "World of Warcraft"\n'
        "  Root window id: 0x374 (the root window) (has no name)\n"
        "  Parent window id: 0x374 (the root window) (has no name)\n"
        "     0 children:\n",
        "  0x1600011 (has no name): () 1920x1080+0+0\n",
        'xwininfo: Window id: 0x1800001 "World of Warcraft"\n'
        'xwininfo: Window id: 0x1800002 "World of Warcraft"\n'
        "  0x1600011 (has no name): () 1920x1080+0+0\n",
        'xwininfo: Window id: 0x1800001 "World of Warcraft"\n  0x1800001 (has no name): () 1920x1080+0+0\n',
    ],
)
def test_xwininfo_tree_rejects_missing_or_ambiguous_structure(tree: str) -> None:
    with pytest.raises(DriverError):
        _parse_xwininfo_tree(tree)


@pytest.mark.parametrize(
    "startup_readiness",
    [False, True],
)
@pytest.mark.parametrize(
    ("case", "tree"),
    [
        (
            "root",
            "xwininfo: Window id: 0x374 (the root window)\n  0x03c00003 (has no name): () 480x240+11+22\n",
        ),
        (
            "parent",
            "xwininfo: Window id: 0x374 (the root window)\n"
            '  0x600118 "unrelated parent": ("other" "other") 500x260+1+2\n'
            '    0x600119 "managed frame": ("python3" "python3") 500x260+1+2\n'
            "      0x03c00003 (has no name): () 480x240+11+22\n",
        ),
        (
            "sibling",
            "xwininfo: Window id: 0x374 (the root window)\n"
            '  0x600119 "managed frame": ("python3" "python3") 500x260+1+2\n'
            "    0x03c00003 (has no name): () 480x240+11+22\n"
            # Deliberate mutation: one native-form extra direct sibling.
            "    0x03c00005 (has no name): () 1x1+1+1  +693+363\n",
        ),
    ],
)
def test_owned_gtk_rejects_root_unrelated_parent_and_sibling(
    startup_readiness: bool, case: str, tree: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    pid = os.getpid()
    client_xid = 0x03C00003
    frame_xid = 0x600119
    helper_xid = 0x600193
    frame_pid = 5717

    import crowley.session.calibration as calibration_module

    def stats(x: int, y: int, width: int, height: int) -> str:
        return f"Absolute upper-left X: {x}\nAbsolute upper-left Y: {y}\nWidth: {width}\nHeight: {height}\n"

    def command(args: list[str], *, display: str, xauthority: str, timeout: float = 5.0) -> str:
        if args[:2] == ["wmctrl", "-lp"]:
            return f"{hex(client_xid)}  -1  {pid} host CROWLEY INPUT CALIBRATION ONLY\n"
        if args == ["xprop", "-id", hex(client_xid)]:
            return (
                f'WM_NAME(STRING) = "CROWLEY INPUT CALIBRATION ONLY"\n'
                f"_NET_WM_PID(CARDINAL) = {pid}\n"
                "_NET_FRAME_EXTENTS(CARDINAL) = 5, 31, 5, 38\n"
            )
        if case == "sibling" and args == ["xprop", "-id", hex(frame_xid)]:
            return (
                f"_MUTTER_FRAME_FOR(WINDOW): window id # {hex(client_xid)}\n"
                f"_NET_WM_USER_TIME_WINDOW(WINDOW): window id # {hex(helper_xid)}\n"
                f"_NET_WM_PID(CARDINAL) = {frame_pid}\n"
                'WM_CLASS(STRING) = "mutter-x11-frames", "mutter-x11-frames"\n'
            )
        if args[0] == "xprop":
            raise AssertionError(args)
        if args[0] == "xwininfo":
            if "-tree" in args:
                return tree
            if args == ["xwininfo", "-id", hex(frame_xid), "-stats"]:
                return stats(1, 2, 500, 260)
            if args == ["xwininfo", "-id", hex(client_xid), "-stats"]:
                return stats(11, 22, 480, 240) + "Map State: IsViewable\n"
            raise AssertionError(args)
        if args[:2] == ["xdotool", "windowactivate"]:
            return ""
        if args[:2] == ["xdotool", "getwindowfocus"]:
            return f"{hex(client_xid)}\n"
        raise AssertionError(args)

    def process_identity(process_pid: int) -> tuple[str, str, str]:
        if process_pid == pid:
            return "/usr/bin/python3", "client-start", "python3"
        if process_pid == frame_pid:
            return "/usr/libexec/mutter-x11-frames", "frame-start", "mutter-x11-fram"
        raise AssertionError(process_pid)

    monkeypatch.setattr(calibration_module, "_process_identity", process_identity)
    target = OwnedGtkCalibrationWindow(display=":test", xauthority="/tmp/Xauthority", command=command)
    expected = _GtkStartupPending if startup_readiness and case == "root" else CalibrationError
    with pytest.raises(expected, match="root|parent|sibling|ancestry|children") as failure:
        target._verify(pid, client_xid, object(), startup_readiness=startup_readiness)  # type: ignore[arg-type]
    if expected is CalibrationError:
        assert not isinstance(failure.value, _GtkStartupPending)


def test_owned_input_evidence_rejects_foreign_forwarded_target() -> None:
    from crowley.session.calibration import InputCalibrationWorkflow, OwnedWindow

    records = parse_xi2_records(TRACE, require_event=True)
    records.extend(
        [
            XI2Event(
                17,
                EventClass.RAW_MOTION,
                2,
                4,
                3,
                0,
                None,
                None,
                None,
                valuators=((0, 10.0, 10.0), (1, 20.0, 20.0)),
            ),
            XI2Event(
                6,
                EventClass.MOTION,
                4,
                4,
                3,
                0,
                0x374,
                0x374,
                0x600119,
                (987.0, 595.0),
                (987.0, 595.0),
                (0, 0, 0),
                modifier_effective=0,
                valuators=((0, 10.0, 10.0), (1, 20.0, 20.0)),
            ),
        ]
    )
    human = records[1].__class__(
        2,
        EventClass.KEY_PRESS,
        5,
        9,
        1,
        8,
        0x374,
        0x374,
        0x600119,
    )
    click = records[3].__class__(
        4,
        EventClass.BUTTON_PRESS,
        4,
        7,
        2,
        1,
        0x374,
        0x374,
        0x600119,
    )
    foreign_motion = records[1].__class__(
        6,
        EventClass.MOTION,
        2,
        7,
        3,
        0,
        0x374,
        0x374,
        0x1A00011,
    )
    window = OwnedWindow(
        31415,
        0x600119,
        "CROWLEY INPUT CALIBRATION ONLY",
        (0, 0, 480, 240),
        object(),  # type: ignore[arg-type]
        frozenset({0x600119}),
        "",
        "",
        0x600118,
        (0, 0, 500, 260),
        frozenset({0x600118, 0x600119}),
    )
    with pytest.raises(CalibrationError, match="unrelated|outside"):
        InputCalibrationWorkflow._build_evidence(
            [*records, human, click, foreign_motion],
            window,
            "test",
            hierarchy=((4, 2, "slave", "pointer:test"),),
            xtest_profile=_xtest_profile(((4, 2, "slave", "pointer:test"),)),
            synthetic_motion_query=(987, 595, 0x600119, 10, 20, 10, 20, 0x600119),
            display=":test",
            xauthority="/tmp/Xauthority",
            game_identity_fingerprint="game-test-identity",
            game_geometry=(0, 0, 1920, 1080),
            target_executable="/usr/bin/python3",
            target_process_start="target-start",
            target_geometry=(0, 0, 480, 240),
        )


def test_action_anchor_requires_measured_identity_and_native_calibration_rejects_fake_metrics(
    tmp_path: Path,
) -> None:
    profile = DriverProfile(action_anchors={"open_ah": (10, 10)})
    with pytest.raises(DriverError, match="measured identity"):
        profile.validate()
    driver = DesktopDriver(backend=RecordingBackend(), lease_path=tmp_path / "native.lock")
    with pytest.raises(DriverError):
        driver.native_calibration(
            {
                "origin": (80, 48),
                "crop": (80, 48, 256, 256),
                "effectiveScale": 1,
                "constructionSeconds": 1,
                "updateP99Ms": 1,
                "textureCount": 16_384,
                "updateCount": 100,
                "cellSize": (2, 2),
                "luaTransientKiB": 1,
            }
        )
    driver.close()


def test_owned_input_workflow_revokes_on_first_human_event_and_cancels_queue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from crowley.session.calibration import InputCalibrationWorkflow, OwnedWindow

    base = parse_xi2_records(TRACE, require_event=True)[0]

    def event(
        number: int,
        event_class: EventClass,
        master: int,
        source: int,
        timestamp: int,
        detail: int | None,
        child: int | None,
        valuators: tuple[tuple[int, float, float | None], ...] = (),
    ) -> object:
        return base.__class__(
            number,
            event_class,
            master,
            source,
            timestamp,
            detail,
            0x374 if child is not None else None,
            0x374 if child is not None else None,
            child,
            (1.0, 1.0) if child is not None else None,
            (1.0, 1.0) if child is not None else None,
            (0, 0, 0)
            if child is not None
            and event_class
            in {
                EventClass.KEY_PRESS,
                EventClass.KEY_RELEASE,
                EventClass.BUTTON_PRESS,
                EventClass.BUTTON_RELEASE,
                EventClass.MOTION,
            }
            else None,
            modifier_effective=0 if child is not None else None,
            valuators=valuators,
        )

    synthetic = [
        event(13, EventClass.RAW_KEY_PRESS, 3, 5, 232007447, 8, None),
        event(2, EventClass.KEY_PRESS, 5, 5, 232007447, 8, 0x600119),
        event(14, EventClass.RAW_KEY_RELEASE, 3, 5, 232007460, 8, None),
        event(3, EventClass.KEY_RELEASE, 5, 5, 232007460, 8, 0x600119),
        event(13, EventClass.RAW_KEY_PRESS, 3, 5, 232007461, 9, None),
        event(2, EventClass.KEY_PRESS, 5, 5, 232007461, 9, 0x600119),
        event(14, EventClass.RAW_KEY_RELEASE, 3, 5, 232007462, 9, None),
        event(3, EventClass.KEY_RELEASE, 5, 5, 232007462, 9, 0x600119),
        event(
            17,
            EventClass.RAW_MOTION,
            2,
            4,
            232007475,
            0,
            None,
            ((0, 2.0, 2.0), (1, 2.0, 2.0)),
        ),
        event(1, EventClass.DEVICE_CHANGED, 2, 4, 232007476, None, None),
        event(
            6,
            EventClass.MOTION,
            4,
            4,
            232007475,
            0,
            0x600119,
            ((0, 2.0, 2.0), (1, 2.0, 2.0)),
        ),
        event(15, EventClass.RAW_BUTTON_PRESS, 2, 4, 232007476, 1, None),
        event(4, EventClass.BUTTON_PRESS, 4, 4, 232007476, 1, 0x600119),
        event(7, EventClass.ENTER, 4, 4, 232007476, None, 0),
        event(16, EventClass.RAW_BUTTON_RELEASE, 2, 4, 232007476, 1, None),
        event(5, EventClass.BUTTON_RELEASE, 4, 4, 232007476, 1, 0x600119),
        event(8, EventClass.LEAVE, 4, 4, 232007476, None, 0),
    ]
    human_key = [
        event(13, EventClass.RAW_KEY_PRESS, 3, 9, 232007500, 8, None),
        event(2, EventClass.KEY_PRESS, 9, 9, 232007500, 8, 0x600119),
        event(14, EventClass.RAW_KEY_RELEASE, 3, 9, 232007510, 8, None),
        event(3, EventClass.KEY_RELEASE, 9, 9, 232007510, 8, 0x600119),
    ]
    human_click = [
        event(6, EventClass.MOTION, 7, 7, 232007515, None, 0x600119),
        event(15, EventClass.RAW_BUTTON_PRESS, 2, 7, 232007520, 1, None),
        event(4, EventClass.BUTTON_PRESS, 7, 7, 232007520, 1, 0x600119),
        event(16, EventClass.RAW_BUTTON_RELEASE, 2, 7, 232007521, 1, None),
        event(5, EventClass.BUTTON_RELEASE, 7, 7, 232007521, 1, 0x600119),
    ]

    def as_trace(event: object) -> str:
        parsed = event  # type: ignore[assignment]
        return (
            f"EVENT type {parsed.type_number} ({parsed.event_class.value})\n"
            f"    device: {parsed.master_device} ({parsed.source_device})\n"
            f"    time: {parsed.timestamp_ms}\n"
            + (f"    detail: {parsed.detail}\n" if parsed.detail is not None else "")
            + (
                "    root: 1.00/1.00\n"
                "    event: 1.00/1.00\n"
                "    modifiers: locked 0 latched 0 base 0 effective: 0\n"
                f"    windows: root 0x374 event 0x374 child {hex(parsed.child_xid)}\n"
                if parsed.child_xid is not None
                else ""
            )
            + (
                "    valuators:\n"
                + "".join(
                    f"         {axis}: {value:.2f} ({(raw if raw is not None else value):.2f})\n"
                    for axis, value, raw in parsed.valuators
                )
                if parsed.valuators
                else ""
            )
        )

    synthetic_trace = "\n".join(as_trace(event) for event in synthetic)
    all_trace = synthetic_trace + "\n" + "\n".join(as_trace(event) for event in [*human_key, *human_click])

    class FakeObserver:
        def __init__(self, callback: object) -> None:
            self.callback = callback
            self._events = []

        def _add(self, event: object) -> None:
            self._events.append(event)
            self.callback(event)

        def events(self) -> list[object]:
            return list(self._events)

        def collect_until(self, predicate: object, *, timeout: float) -> str:
            for event in synthetic:
                self._add(event)
            assert predicate(self.events())
            return synthetic_trace

        def wait_for_human(self, predicate: object, *, timeout: float) -> None:
            for event in [*human_key, *human_click]:
                self._add(event)
            assert predicate(self.events())

        def stop(self) -> str:
            return all_trace

    ready_order: list[str] = []

    class FakeTarget:
        def __init__(self) -> None:
            self.window = OwnedWindow(
                31415,
                0x600119,
                "CROWLEY INPUT CALIBRATION ONLY",
                (0, 0, 480, 240),
                object(),  # type: ignore[arg-type]
                frozenset({0x600119}),
                "/usr/bin/python3",
                "target-start",
                0x600118,
                (0, 0, 500, 260),
                frozenset({0x600118, 0x600119}),
            )

        def create(self) -> OwnedWindow:
            return self.window

        def close(self) -> None:
            return None

        def show_human_prompt(self) -> None:
            ready_order.append("prompt")

    class FakeDriver:
        profile = SimpleNamespace(display=":test", xauthority="/tmp/Xauthority")
        driver_version = DRIVER_VERSION
        xauthority = "/tmp/Xauthority"
        queued_calibration_count = 0
        calibration_executions = 0
        calibration_due_count = 1

        def __init__(self) -> None:
            self.generation = 0
            self.observer: FakeObserver | None = None
            self.ticket = SimpleNamespace(epoch=1)
            self.retained: object | None = None
            # Keep the fake process/observer boundary while exercising the
            # canonical native transition proof and seal path.
            self.backend = object.__new__(X11Backend)
            self.backend._last_synthetic_motion_query = (
                1,
                1,
                0x600119,
                2,
                2,
                2,
                2,
                0x600119,
            )

        def begin_calibration_operation(self) -> int:
            return 1

        def calibration_keyboard_operations(self) -> tuple[object, ...]:
            from crowley.session.calibration import KeyboardProbeOperation, KeyboardProbeStep

            return (
                KeyboardProbeOperation(
                    "open_chat",
                    "",
                    (KeyboardProbeStep("press", "Return"), KeyboardProbeStep("release", "Return")),
                ),
            )

        def calibration_keyboard_keymap(self) -> dict[str, int]:
            return {"Return": 9}

        def notify_input_calibration_ready(self, readiness: object) -> None:
            assert readiness is not None
            ready_order.append("ready")

        def stop_input_observer(self, observer: FakeObserver, *, already_stopped: bool = False) -> None:
            assert already_stopped

        def resolve_identity(self, *, require_foreground: bool = False) -> SimpleNamespace:
            del require_foreground
            return SimpleNamespace(
                fingerprint="game-test-identity",
                child_geometry=(0, 0, 1920, 1080),
                executable="WowB.exe",
                process_start="game-start",
            )

        def input_hierarchy(self) -> tuple[tuple[int, int, str, str], ...]:
            return (
                (2, 3, "master", "pointer"),
                (3, 2, "master", "keyboard"),
                (4, 2, "slave", "XTEST pointer"),
                (5, 3, "slave", "XTEST keyboard"),
                (7, 2, "slave", "human pointer"),
                (9, 3, "slave", "human keyboard"),
            )

        def xtest_input_profile(self, hierarchy, **_kwargs):
            return _xtest_profile(hierarchy)

        def start_input_observer(self, *, calibration: bool, callback: object) -> FakeObserver:
            assert calibration
            self.observer = FakeObserver(callback)
            return self.observer

        def focus_calibration_target(self, window: OwnedWindow, *, calibration_ticket: object) -> None:
            assert calibration_ticket is self.ticket
            assert window.xid == 0x600119

        def issue_calibration_ticket(self, window: OwnedWindow) -> object:
            assert window.xid == 0x600119
            return self.ticket

        def synthetic_target_keyboard_profile(
            self, window: OwnedWindow, *, operations: object, calibration_ticket: object
        ) -> None:
            assert calibration_ticket is self.ticket
            assert window.xid == 0x600119
            assert operations

        def queue_delayed_calibration_action(
            self,
            window: OwnedWindow,
            *,
            delay: float,
            execution_gate: object = None,
            calibration_ticket: object = None,
        ) -> object:
            assert delay > 0
            assert calibration_ticket is self.ticket
            self.queued_calibration_count = 1
            return self.ticket

        def revoke(self, reason: str) -> int:
            assert reason
            self.generation += 1
            self.queued_calibration_count = 0
            return self.generation

        def retain_input_evidence(self, evidence: object) -> None:
            self.retained = evidence

    driver = FakeDriver()
    evidence = InputCalibrationWorkflow(driver, window_factory=FakeTarget, display=":test").run(
        human_timeout=1
    )
    assert evidence.target_xid == 0x600119
    assert evidence.human_key_source == 9
    assert evidence.human_pointer_source == 7
    evidence.verify_seal()
    assert driver.retained is evidence
    assert driver.generation == 1
    assert driver.queued_calibration_count == 0
    assert ready_order == ["prompt", "ready"]

    # Exercise the real X11 arm/observer path without opening a desktop
    # window.  The observer process is a gated, harmless sleep launched in a
    # fresh process group; it is registered before guardian.arm and reaped by
    # the normal stop/unregister lifecycle.  A stale GTK group would instead
    # appear in active_process_groups and block this arm boundary.
    identity = WindowIdentity(
        0x700100,
        os.getpid(),
        "WowB.exe",
        "World of Warcraft",
        "wowb.exe,WowB.exe",
        0x700101,
        (0, 0, 1928, 1092),
        (0, 0, 1920, 1080),
        0x700100,
        "game-start",
        ":test",
        "game-test-identity",
        root_xid=0x374,
        managed_frame_xid=0x700100,
        target_event_xids=frozenset({0x700100, 0x700101}),
    )
    profile = DriverProfile(display=":test", xauthority="/tmp/Xauthority")
    backend = X11Backend(profile, input_tool=fixture_input_tool(tmp_path / "tool"))
    backend.resolve_identity = lambda require_foreground=True: identity  # type: ignore[method-assign]

    def hierarchy() -> tuple[tuple[int, int, str, str], ...]:
        return evidence.xinput_hierarchy

    def gated_observer_start(observer: XI2Observer) -> None:
        from crowley.session.process_admission import AdmissionGate

        gate_read, gate_write = os.pipe()
        try:
            observer.process = subprocess.Popen(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    "-c",
                    _EXEC_ADMISSION_WRAPPER,
                    str(gate_read),
                    "/bin/sleep",
                    "30",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
                pass_fds=(gate_read,),
            )
            os.close(gate_read)
            observer._admission_gate_write = gate_write
            observer._admission_gate = AdmissionGate(gate_write)
            observer._expected_executable = os.path.realpath("/bin/sleep")
            observer._expected_process_start = observer._process_start(observer.process.pid)
            observer._exec_verified = False
        except Exception:
            os.close(gate_read)
            os.close(gate_write)
            raise

    monkeypatch.setattr(XI2Observer, "start", gated_observer_start)
    resumed = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "resume.lock")
    try:
        evidence = replace(evidence, driver_version=resumed.driver_version, fingerprint="")
        evidence = replace(evidence, fingerprint=evidence.content_fingerprint()).with_hash()
        resumed.input_hierarchy = hierarchy  # type: ignore[method-assign]
        resumed.xtest_input_profile = lambda _hierarchy: evidence.xtest_profile  # type: ignore[method-assign]
        resumed.retain_input_evidence(evidence)
        generation = resumed.arm(resumed.retained_input_evidence)
        assert generation == 1
        monitor = resumed._monitor
        assert monitor is not None
        process = monitor.observer.process
        assert process is not None
        assert process.poll() is None
        assert resumed.guardian.observer_process_groups == frozenset({process.pid})
        assert resumed.guardian.active_process_groups == frozenset()
        assert resumed._calibration_target_process_groups == set()
    finally:
        process = resumed._monitor.observer.process if resumed._monitor is not None else None
        resumed.close()
        assert process is not None and process.poll() is not None
        assert resumed.guardian.observer_process_groups == frozenset()
        assert resumed.guardian.active_process_groups == frozenset()


def test_owned_evidence_rejects_blank_or_tampered_canonical_seals() -> None:
    evidence = _evidence()
    with pytest.raises(CalibrationError, match="canonical seal"):
        replace(evidence, evidence_hash="").verify_seal()
    with pytest.raises(CalibrationError, match="fingerprint|seal"):
        replace(evidence, game_geometry=(1, 2, 3, 4)).verify_seal()
    with pytest.raises(CalibrationError, match="fingerprint|seal"):
        replace(evidence, target_event_xids=(0x600118, 0x600119, 0x03C00004)).verify_seal()
    with pytest.raises(CalibrationError, match="fingerprint|seal|modifier"):
        replace(evidence, synthetic_modifiers=(0x10, 0, 0)).verify_seal()
    with pytest.raises(CalibrationError, match="identity|geometry"):
        replace(evidence, game_identity_fingerprint="").verify_seal()


def test_owned_keyboard_profile_seals_each_step_and_measured_nonzero_modifier() -> None:
    evidence = _evidence()
    proof = list(evidence.event_proof)
    proof[5] = (*proof[5][:10], (0x10, 0, 0), 0x10)
    proof[7] = (*proof[7][:10], (0x10, 0, 0), 0x10)
    profile = (
        (
            "open_chat",
            "",
            (
                ("press", "Return", 9, (0x10, 0, 0), 0x10),
                ("release", "Return", 9, (0x10, 0, 0), 0x10),
            ),
        ),
    )
    measured = replace(evidence, event_proof=tuple(proof), keyboard_profile=profile, fingerprint="")
    measured = replace(measured, fingerprint=measured.content_fingerprint()).with_hash()
    measured.verify_seal()

    tampered = list(proof)
    tampered[7] = (*tampered[7][:10], (0x20, 0, 0), 0x20)
    invalid = replace(measured, event_proof=tuple(tampered), fingerprint="")
    invalid = replace(invalid, fingerprint=invalid.content_fingerprint()).with_hash()
    with pytest.raises(CalibrationError, match="keyboard profile|modifier"):
        invalid.verify_seal()


def test_owned_keyboard_profile_rejects_missing_or_unexpected_steps() -> None:
    evidence = _evidence()
    with pytest.raises(CalibrationError, match="keyboard keymap|operation profile"):
        replace(evidence, keyboard_profile=()).verify_seal()
    unexpected = (
        (
            "open_chat",
            "",
            (
                ("press", "Control_L", 9, (0, 0, 0), 0),
                ("release", "Control_L", 9, (0, 0, 0), 0),
            ),
        ),
    )
    with pytest.raises(CalibrationError, match="transition|keyboard profile"):
        replace(evidence, keyboard_profile=unexpected).verify_seal()
