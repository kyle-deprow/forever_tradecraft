"""Production-path native boundary tests with controlled process and Agent fixtures.

These tests prove rejection and fencing behavior.  They do not claim that a
live desktop or human input calibration has passed.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import time
import types
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

import crowley.session.daemon as daemon_module
import tools.session_performance as session_performance
from crowley.session import driver as driver_module
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
from crowley.session.daemon import SessionDaemon, session_config_semantic_sha256
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


def _independent_live_binding(config_path: Path, producer_path: Path) -> dict[str, object]:
    """Build the evaluator binding from known fixture inputs before a run."""

    root = Path(__file__).resolve().parents[1]
    source_paths = {
        "daemon.py": root / "src/crowley/session/daemon.py",
        "driver.py": root / "src/crowley/session/driver.py",
        "cli.py": root / "src/crowley/session/cli.py",
        "decoder.py": root / "src/crowley/session/decoder.py",
        "protocol.py": root / "src/crowley/session/protocol.py",
        "offline_harness.py": root / "tools/gnome-telemetry-region/offline_harness.py",
        "session_performance.py": root / "tools/session_performance.py",
    }
    accepted_source_hashes = {
        name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in source_paths.items()
    }
    config = load_config(config_path)
    return {
        "schema": "crowley.runtime-performance-accepted-binding",
        "schema_version": 1,
        "accepted_source_hashes": accepted_source_hashes,
        "producer_binding": {
            "binary_sha256": hashlib.sha256(producer_path.read_bytes()).hexdigest(),
            "protocol_branch": "ScreenshotArea",
        },
        "config_binding": {
            "raw_file_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
            "semantic_sha256": session_config_semantic_sha256(config),
        },
    }


def _evaluate_persisted_live_receipt(receipt: dict[str, object], path: Path, binding: dict[str, object]):
    """Run a genuine producer receipt through the public frozen evaluator."""

    binding_path = path.parent / "accepted-binding.json"
    binding_bytes = json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8")
    binding_path.write_bytes(binding_bytes)
    binding_digest = hashlib.sha256(binding_bytes).hexdigest()
    report = session_performance.build_live_report(
        [path], accepted_binding=binding_path, binding_sha256=binding_digest
    )
    run = report["runs"][0]
    return run, run["completed_pairs"] or [], report


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
        backend = object()

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
    with pytest.raises(DriverError, match="configured X11 backend"):
        daemon._capture_native_region_for_identity(identity, deadline=12.0)
    assert [call[0] for call in calls] == ["stock"]


def test_real_session_daemon_native_provider_route_and_stock_model_capture(
    tmp_path: Path,
) -> None:
    """Keep the fake backend on the stock route and reject native capture."""

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
            self.region_rectangles: list[tuple[int, int, int, int]] = []

        def capture(self, path: Path, *, identity=None, deadline_monotonic=None):  # type: ignore[no-untyped-def]
            del deadline_monotonic
            self.stock_captures += 1
            self.captures.append(path)
            desktop = Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
            desktop.paste(self.region, (80, 48))
            desktop.save(path, format="PNG")
            return identity or self.identity

        def capture_native_region(self, path: Path, *, identity, rectangle, **kwargs):  # type: ignore[no-untyped-def]
            del kwargs
            self.region_captures += 1
            self.region_rectangles.append(rectangle)
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
        canvas_crop=(123, 77, 256, 256),
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
        with pytest.raises(DriverError, match="configured X11 backend"):
            region_daemon._capture_native_region_for_identity(identity, deadline=time.monotonic() + 5.0)
        assert region_backend.region_captures == 0
        model_bytes = region_daemon._capture_model(deadline=time.monotonic() + 5.0)
        assert model_bytes
        assert region_backend.stock_captures == 1
        assert region_backend.region_captures == 0
        assert region_daemon._native_region_enabled() is True
    finally:
        region_driver.close()


def test_compiled_region_composes_through_default_daemon_and_stock_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run the frozen GNOME producer through the complete private X11 path."""

    harness_path = Path(__file__).resolve().parents[1] / "tools/gnome-telemetry-region/offline_harness.py"
    spec = importlib.util.spec_from_file_location("region_offline_harness", harness_path)
    assert spec is not None and spec.loader is not None
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)

    freeze_path = (
        Path(__file__).resolve().parents[1]
        / ".archive/executor-review/gnome-telemetry-region-r6-final-freeze.json"
    )
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    frozen_producer = Path(freeze["private_cache"]) / "prefix/bin/gnome-screenshot"
    assert frozen_producer.is_file()
    producer_sha256 = hashlib.sha256(frozen_producer.read_bytes()).hexdigest()
    assert producer_sha256 == freeze["build"]["private_binary_sha256"]

    client = WowClient()
    client.set_canonical_plan()
    client.login()
    client.publish_agent()

    def png_bytes(image: Image.Image) -> bytes:
        target = BytesIO()
        image.save(target, format="PNG")
        return target.getvalue()

    # Bootstrap observes an unconstructed surface. Later shell calls serve
    # independently rendered CRS1 frames whose sequence advances in the real
    # Lua harness between captures.
    absent_surface = Image.new("RGB", (256, 256), (127, 127, 127))
    client.update_agent(1.0)
    first_status = client.render_agent_capture()
    client.update_agent(1.0)
    native_frame = client.render_agent_capture()
    decoder_probe = PixelDecoder()
    first_decoded = decoder_probe.decode(first_status, monotonic=1.0, window_identity="fixture").frame
    second_decoded = decoder_probe.decode(native_frame, monotonic=2.0, window_identity="fixture").frame
    assert first_decoded is not None and second_decoded is not None
    assert second_decoded.sequence > first_decoded.sequence

    rectangle = (123, 77, 256, 256)
    full_desktop = Image.new("RGB", (1920, 1080), (31, 37, 41))
    full_bytes = png_bytes(full_desktop)
    session_dir = tmp_path / "compiled-region-session"
    session_dir.mkdir(mode=0o700)
    producer = session_dir / "gnome-screenshot-r6"
    producer.write_bytes(frozen_producer.read_bytes())
    producer.chmod(0o700)
    xauthority = session_dir / "Xauthority"
    xauthority.touch(mode=0o600)
    plan_json = "{}"
    plan_hash = hashlib.sha256(plan_json.encode()).hexdigest()
    codex_path = Path(
        "/home/dev/.cache/crowley/codex/0.162.1/node_modules/@openai/codex-linux-x64/"
        "vendor/x86_64-unknown-linux-musl/bin/codex"
    )
    assert codex_path.is_file(), "the authentic private Codex CLI is required for fixture startup"

    with harness.private_shell_compositor(
        payloads=[
            png_bytes(absent_surface),
            png_bytes(first_status),
            png_bytes(native_frame),
            png_bytes(native_frame),
            png_bytes(native_frame),
            png_bytes(native_frame),
        ],
        full_desktop=full_bytes,
        rectangle=rectangle,
        allow_area_gate=True,
    ) as compositor:
        monkeypatch.setattr(driver_module, "GNOME_CAPTURE_LOCK_PATH", tmp_path / "private-capture.lock")
        runtime_env = os.environ.copy()
        missing_runtime_env = runtime_env.copy()
        missing_runtime_env.pop("XDG_RUNTIME_DIR", None)
        missing_runtime = subprocess.run(
            [str(producer), "--version"],
            env=missing_runtime_env,
            text=True,
            capture_output=True,
            timeout=2.0,
            check=False,
        )
        assert missing_runtime.returncode != 0
        assert "XDG_RUNTIME_DIR" in missing_runtime.stderr

        untrusted_runtime = session_dir / "untrusted-runtime"
        untrusted_runtime.mkdir(mode=0o755)
        untrusted_runtime.chmod(0o755)
        untrusted_env = runtime_env.copy()
        untrusted_env["XDG_RUNTIME_DIR"] = str(untrusted_runtime)
        untrusted = subprocess.run(
            [str(producer), "--version"],
            env=untrusted_env,
            text=True,
            capture_output=True,
            timeout=2.0,
            check=False,
        )
        assert untrusted.returncode != 0
        assert "mode 0700" in untrusted.stderr

        symlink_runtime = session_dir / "symlink-runtime"
        symlink_runtime.symlink_to(compositor["root"], target_is_directory=True)
        symlink_env = runtime_env.copy()
        symlink_env["XDG_RUNTIME_DIR"] = str(symlink_runtime)
        symlink_result = subprocess.run(
            [str(producer), "--version"],
            env=symlink_env,
            text=True,
            capture_output=True,
            timeout=2.0,
            check=False,
        )
        assert symlink_result.returncode != 0
        assert "symlinked component" in symlink_result.stderr
        assert not compositor["area_log"].exists()
        identity = WindowIdentity(
            0x100,
            os.getpid(),
            "WowB.exe",
            "World of Warcraft",
            "wowb.exe",
            0x101,
            (0, 0, 1928, 1092),
            (0, 0, 1920, 1080),
            0x100,
            str(os.getpid()),
            compositor["display"],
            "compiled-region-private-window-identity",
            0x100,
            0x100,
            frozenset({0x100, 0x101}),
        )
        profile = DriverProfile(
            display=compositor["display"],
            xauthority=str(xauthority),
            wine_prefix="/private-fixture-only",
            client_width=1920,
            client_height=1080,
            outer_width=1928,
            outer_height=1092,
            canvas_crop=rectangle,
            model_crop=(80, 48, 640, 480),
            telemetry_region_executable=producer,
            telemetry_region_executable_sha256=producer_sha256,
        )
        backend = X11Backend(profile)
        # Window discovery is the only substituted boundary: it represents a
        # stable external game window on this owned Xvfb. The X11Backend,
        # retained executable, process admission, compiled producer, decoder,
        # daemon provider binding, and all screenshot calls remain real.
        backend.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
        driver = DesktopDriver(
            profile=profile,
            backend=backend,
            lease_path=session_dir / "desktop.lock",
        )
        real_gate_factory = driver_module.AdmissionGate
        rejected_gates = []

        def track_gate(descriptor: int):
            gate = real_gate_factory(descriptor)
            rejected_gates.append(gate)
            return gate

        monkeypatch.setattr(driver_module, "AdmissionGate", track_gate)
        watchdog_state = driver.guardian._watchdog_state
        driver.guardian._watchdog_state = lambda: False  # type: ignore[method-assign]
        rejected_output = session_dir / "rejected-after-spawn" / "capture.png"
        try:
            with pytest.raises(GuardianError, match="watchdog state was not acknowledged"):
                driver.capture_native_region_for_identity(
                    identity,
                    destination=rejected_output,
                    deadline_monotonic=time.monotonic() + 2.0,
                    observer_admission=driver.guardian.observer_dispatch_admission,
                    observer_reaped=driver.guardian.unregister_observer_process,
                )
        finally:
            driver.guardian._watchdog_state = watchdog_state  # type: ignore[method-assign]
            monkeypatch.setattr(driver_module, "AdmissionGate", real_gate_factory)
        assert len(rejected_gates) == 1 and rejected_gates[0]._closed
        with pytest.raises(OSError):
            os.fstat(rejected_gates[0].write_fd)
        assert not rejected_output.exists()
        assert not backend._active_processes and not backend.active_process_groups
        assert not driver.guardian.observer_process_groups
        config = SessionConfig(
            profile=profile,
            journal=session_dir / "journal.json",
            socket=session_dir / "session.sock",
            capture_dir=session_dir / "captures",
            plan_hash=plan_hash,
            plan_json=plan_json,
            codex_path=str(codex_path),
        )
        daemon = SessionDaemon(config, driver=driver)
        admission_events: list[tuple[str, float, int | None]] = []
        original_observer_admission = driver.guardian.observer_dispatch_admission

        def record_observer_admission(start, *, calibration: bool = False):  # type: ignore[no-untyped-def]
            admission_events.append(("admission_enter", time.monotonic(), None))
            admitted = original_observer_admission(start, calibration=calibration)
            process = getattr(admitted, "process", None) or getattr(
                getattr(admitted, "observer", None), "process", None
            )
            assert process is not None
            admission_events.append(("gate_released", time.monotonic(), process.pid))
            return admitted

        driver.guardian.observer_dispatch_admission = record_observer_admission  # type: ignore[method-assign]
        retained_capture: Path | None = None
        try:
            status = daemon.controller.start()
            assert status.state.value == "NATIVE_CALIBRATION"
            bootstrapped = daemon.native_bootstrap(expected_generation=status.generation)
            assert bootstrapped["nativeBootstrapPending"] is True
            bootstrap = daemon._native_bootstrap_observation
            assert bootstrap is not None and bootstrap["surface"] == "absent"
            assert bootstrap["geometry"] == identity.child_geometry
            assert daemon._native_region_enabled() is True

            motion = daemon.motion_provider.observe(1, deadline=time.monotonic() + 10.0)
            assert isinstance(motion, MotionFrame)
            assert motion.identity_fingerprint == identity.fingerprint
            assert motion.native.ctm_state == "disabled"
            assert motion.native.ground_state == "grounded"
            assert motion.native.speed_tuple.run == 7.0
            assert backend.last_region_receipt is not None
            motion_receipt = backend.last_region_receipt
            assert motion_receipt.owner_branch == "ScreenshotArea"
            assert motion_receipt.rectangle == rectangle
            assert motion_receipt.executable_sha256 == producer_sha256
            assert motion_receipt.attempt_retired is True

            client.update_agent(1.0)
            fresh_identity = driver.resolve_identity()
            sample, capture_sha256, retained_capture = daemon._capture_native_frame_with_capture(
                fresh_identity,
                driver.new_native_decoder(),
                deadline=time.monotonic() + 10.0,
            )
            assert sample.kind == "FRESH" and sample.frame is not None
            assert sample.frame.sequence > motion.sequence
            assert len(capture_sha256) == 64
            assert retained_capture.is_file()
            native_receipt = backend.last_region_receipt
            assert native_receipt is not None
            assert native_receipt.rectangle == rectangle
            assert native_receipt.output_sha256 == capture_sha256
            assert native_receipt.attempt_retired is True

            before_model_nonce = native_receipt.nonce
            model_bytes = daemon._capture_model(deadline=time.monotonic() + 10.0)
            assert model_bytes
            assert compositor["stock_log"].is_file()
            stock_calls = json.loads(compositor["stock_log"].read_text(encoding="utf-8"))
            assert len(stock_calls) == 1
            assert backend.last_region_receipt is not None
            assert backend.last_region_receipt.nonce == before_model_nonce
            area_calls = json.loads(compositor["area_log"].read_text(encoding="utf-8"))
            assert len(area_calls) == 3
            assert [call["index"] for call in area_calls] == [1, 2, 3]
            assert all(
                (call["x"], call["y"], call["width"], call["height"], call["flash"]) == (*rectangle, False)
                for call in area_calls
            )
            assert not backend._active_processes
            assert not backend.active_process_groups
            assert [event[0] for event in admission_events[:6]] == [
                name for _ in range(3) for name in ("admission_enter", "gate_released")
            ]
            assert all(
                admission_events[index * 2 + 1][1] * 1_000_000 <= area_calls[index]["monotonic_us"]
                for index in range(3)
            )

            # A regular stock invocation is forwarded to the active primary
            # while its asynchronous typed capture is waiting on the real
            # Shell boundary. The C guard rejects it before shared options or
            # a second Shell screenshot can be dispatched.
            blocked_target = session_dir / "guarded-capture.png"
            compositor["area_block_path"].touch(mode=0o600)
            capture_errors: list[BaseException] = []

            def blocked_capture() -> None:
                try:
                    daemon._capture_native_region_for_identity(
                        driver.resolve_identity(),
                        destination=blocked_target,
                        deadline=time.monotonic() + 8.0,
                    )
                except BaseException as exc:
                    capture_errors.append(exc)

            capture_thread = threading.Thread(target=blocked_capture, daemon=True)
            primary_process: subprocess.Popen[str] | None = None
            ordinary_invocation: subprocess.Popen[str] | None = None
            ordinary_returncode: int | None = None
            ordinary_stdout = ""
            ordinary_stderr = ""
            rpc_children: list[tuple[str, subprocess.Popen[str]]] = []
            rpc_results: dict[str, tuple[int, str, str]] = {}
            foreign_output = session_dir / "foreign-stock.png"
            ordinary_output = session_dir / "foreign-primary.png"
            before_foreign = 0
            try:
                capture_thread.start()
                gate_deadline = time.monotonic() + 4.0
                while not compositor["area_started_path"].exists() and time.monotonic() < gate_deadline:
                    time.sleep(0.01)
                assert compositor["area_started_path"].exists(), (
                    "compiled capture did not enter blocked Shell call"
                )
                with backend._process_lock:
                    blocked_processes = tuple(backend._active_processes)
                assert len(blocked_processes) == 1
                primary_process = blocked_processes[0]
                admitted_groups = driver.guardian.observer_process_groups
                assert len(admitted_groups) == 1
                before_foreign = len(json.loads(compositor["area_log"].read_text(encoding="utf-8")))
                foreign = subprocess.run(
                    [str(producer), "--file", str(foreign_output)],
                    env=os.environ.copy(),
                    text=True,
                    capture_output=True,
                    timeout=2.0,
                    check=False,
                )
                assert foreign.returncode != 0
                assert "another screenshot invocation owns" in foreign.stderr.lower()
                assert len(json.loads(compositor["area_log"].read_text(encoding="utf-8"))) == before_foreign
                assert not foreign_output.exists()

                concurrent_telemetry = subprocess.run(
                    [
                        str(producer),
                        "--telemetry-region",
                        "--telemetry-x",
                        "not-an-integer",
                    ],
                    env=os.environ.copy(),
                    text=True,
                    capture_output=True,
                    timeout=2.0,
                    check=False,
                )
                assert concurrent_telemetry.returncode != 0
                assert "another screenshot invocation owns" in concurrent_telemetry.stderr.lower()
                assert "valid 256x256 rectangle" not in concurrent_telemetry.stderr.lower()
                assert len(json.loads(compositor["area_log"].read_text(encoding="utf-8"))) == before_foreign

                # A separate owned runtime directory bypasses the producer's
                # flock, while the explicit private bus/display still address
                # the active GApplication. Popen is deliberately asynchronous:
                # waiting for a synchronous primary reply while Shell is
                # blocked would deadlock.
                ordinary_runtime = session_dir / "ordinary-runtime"
                ordinary_runtime.mkdir(mode=0o700)
                ordinary_runtime.chmod(0o700)
                ordinary_runtime_info = ordinary_runtime.stat()
                assert ordinary_runtime_info.st_uid == os.geteuid()
                assert ordinary_runtime_info.st_mode & 0o777 == 0o700
                ordinary_env = runtime_env.copy()
                ordinary_env.update(
                    {
                        "XDG_RUNTIME_DIR": str(ordinary_runtime),
                        "DBUS_SESSION_BUS_ADDRESS": compositor["bus_address"],
                        "DISPLAY": compositor["display"],
                        "GDK_BACKEND": "x11",
                    }
                )
                ordinary_invocation = subprocess.Popen(
                    [str(producer), "--file", str(ordinary_output)],
                    env=ordinary_env,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                rpc_children.append(("ordinary", ordinary_invocation))
                # Give the D-Bus client a bounded opportunity to forward while
                # the first Shell request remains blocked. The primary may
                # synchronously reject and exit here, which is also valid.
                forward_deadline = time.monotonic() + 1.0
                while ordinary_invocation.poll() is None and time.monotonic() < forward_deadline:
                    time.sleep(0.01)

                rpc_env = runtime_env.copy()
                rpc_env.update(
                    {
                        "XDG_RUNTIME_DIR": str(compositor["root"]),
                        "DBUS_SESSION_BUS_ADDRESS": compositor["bus_address"],
                        "DISPLAY": compositor["display"],
                        "GDK_BACKEND": "x11",
                    }
                )
                rpc_specs = (
                    ("activate", "org.freedesktop.Application", "Activate", "a{sv}", ("0",)),
                    (
                        "freedesktop-screen-shot",
                        "org.freedesktop.Application",
                        "ActivateAction",
                        "sava{sv}",
                        ("screen-shot", "0", "0"),
                    ),
                    (
                        "freedesktop-window-shot",
                        "org.freedesktop.Application",
                        "ActivateAction",
                        "sava{sv}",
                        ("window-shot", "0", "0"),
                    ),
                    (
                        "gtk-screen-shot",
                        "org.gtk.Actions",
                        "Activate",
                        "sava{sv}",
                        ("screen-shot", "0", "0"),
                    ),
                    (
                        "gtk-window-shot",
                        "org.gtk.Actions",
                        "Activate",
                        "sava{sv}",
                        ("window-shot", "0", "0"),
                    ),
                )
                for label, interface, method, signature, arguments in rpc_specs:
                    rpc = subprocess.Popen(
                        [
                            "busctl",
                            f"--address={compositor['bus_address']}",
                            "--auto-start=no",
                            "call",
                            "org.gnome.Screenshot",
                            "/org/gnome/Screenshot",
                            interface,
                            method,
                            signature,
                            *arguments,
                        ],
                        env=rpc_env,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    rpc_children.append((label, rpc))
                    # Let each real client put its method call on the private
                    # bus. Never wait for its reply until after gate release.
                    time.sleep(0.05)
                live_name_owner = subprocess.run(
                    [
                        "busctl",
                        f"--address={compositor['bus_address']}",
                        "--auto-start=no",
                        "call",
                        "org.freedesktop.DBus",
                        "/org/freedesktop/DBus",
                        "org.freedesktop.DBus",
                        "GetNameOwner",
                        "s",
                        "org.gnome.Screenshot",
                    ],
                    env=rpc_env,
                    text=True,
                    capture_output=True,
                    timeout=2.0,
                    check=False,
                )
                assert live_name_owner.returncode == 0
                assert not live_name_owner.stderr
                assert live_name_owner.stdout.strip().startswith('s ":')
            finally:
                compositor["area_block_path"].unlink(missing_ok=True)
                compositor["area_release_path"].touch(mode=0o600)
                capture_thread.join(timeout=8.0)
                for label, child in rpc_children:
                    try:
                        child_stdout, child_stderr = child.communicate(timeout=8.0)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child_stdout, child_stderr = child.communicate(timeout=2.0)
                    finally:
                        if child.poll() is None:
                            child.kill()
                            child.wait(timeout=2.0)
                    if label == "ordinary":
                        ordinary_stdout, ordinary_stderr = child_stdout, child_stderr
                    else:
                        rpc_results[label] = (child.returncode, child_stdout, child_stderr)
                if ordinary_invocation is not None:
                    ordinary_returncode = ordinary_invocation.returncode
            assert not capture_thread.is_alive()
            assert not capture_errors, (
                f"blocked compiled capture failed: {capture_errors!r}; "
                f"area_calls={compositor['area_log'].read_text(encoding='utf-8') if compositor['area_log'].exists() else None!r}; "
                f"owner_receipt={backend.last_region_receipt!r}; "
                f"target_exists={blocked_target.exists()}; "
                f"active_processes={backend._active_processes!r}; "
                f"active_groups={backend.active_process_groups!r}; "
                f"guardian_groups={driver.guardian.observer_process_groups!r}; "
                f"gjs_stderr={(compositor['root'] / 'gjs.stderr').read_text(encoding='utf-8') if (compositor['root'] / 'gjs.stderr').exists() else None!r}"
            )
            assert blocked_target.is_file()
            _active_guard_message = "A foreign command line arrived while telemetry capture was active."
            assert primary_process is not None
            _primary_stdout, primary_stderr = primary_process.communicate(timeout=0)
            assert primary_stderr.count(_active_guard_message) == 1
            _action_guard_message = "A foreign action arrived while telemetry capture was active."
            _activation_guard_message = "A foreign activation arrived while telemetry capture was active."
            assert primary_stderr.count(_action_guard_message) == 4
            assert primary_stderr.count(_activation_guard_message) == 1
            assert "Telemetry mode requires" not in primary_stderr
            primary_guard_lines = {line for line in primary_stderr.splitlines() if line}
            assert primary_guard_lines <= {
                _active_guard_message,
                _action_guard_message,
                _activation_guard_message,
            }
            # The forwarded command receives the primary command-line handler's
            # EXIT_FAILURE status over GApplication's D-Bus protocol; the
            # guard's diagnostic is written by the primary, not the client.
            assert ordinary_returncode == 1
            assert not ordinary_output.exists()
            assert not ordinary_stdout
            assert not ordinary_stderr
            for label, (returncode, rpc_stdout, rpc_stderr) in rpc_results.items():
                assert returncode == 0, f"{label} D-Bus call failed: {rpc_stdout!r} {rpc_stderr!r}"
                assert not rpc_stderr, f"{label} D-Bus call wrote stderr: {rpc_stderr!r}"
            assert primary_process.poll() is not None
            late_rpc = subprocess.run(
                [
                    "busctl",
                    f"--address={compositor['bus_address']}",
                    "--auto-start=no",
                    "call",
                    "org.gnome.Screenshot",
                    "/org/gnome/Screenshot",
                    "org.freedesktop.Application",
                    "Activate",
                    "a{sv}",
                    "0",
                ],
                env=rpc_env,
                text=True,
                capture_output=True,
                timeout=2.0,
                check=False,
            )
            assert late_rpc.returncode != 0
            assert not late_rpc.stdout
            assert 'Name "org.gnome.Screenshot" does not exist' in late_rpc.stderr
            late_name_owner = subprocess.run(
                [
                    "busctl",
                    f"--address={compositor['bus_address']}",
                    "--auto-start=no",
                    "call",
                    "org.freedesktop.DBus",
                    "/org/freedesktop/DBus",
                    "org.freedesktop.DBus",
                    "GetNameOwner",
                    "s",
                    "org.gnome.Screenshot",
                ],
                env=rpc_env,
                text=True,
                capture_output=True,
                timeout=2.0,
                check=False,
            )
            assert late_name_owner.returncode != 0
            assert not late_name_owner.stdout
            assert "no such name" in late_name_owner.stderr.lower()
            assert "org.gnome.Screenshot" in late_name_owner.stderr
            assert len(json.loads(compositor["area_log"].read_text(encoding="utf-8"))) == before_foreign + 1
            assert len(json.loads(compositor["stock_log"].read_text(encoding="utf-8"))) == 1
            assert not driver.guardian.observer_process_groups
            assert driver.guardian.lease.held
            assert not driver.guardian._watchdog_failed

            # Stop wins at a barrier after the daemon snapshots controller
            # state but before DesktopDriver enters the atomic admission
            # section. The barrier is outside both owner locks; no producer
            # process is registered or executed after stop linearizes.
            before_admission = threading.Event()
            release_admission = threading.Event()
            original_driver_capture = driver.capture_native_region_for_identity

            def wait_before_admission(*args, **kwargs):  # type: ignore[no-untyped-def]
                before_admission.set()
                if not release_admission.wait(2.0):
                    raise TimeoutError("pre-admission fixture barrier was not released")
                return original_driver_capture(*args, **kwargs)

            driver.capture_native_region_for_identity = wait_before_admission  # type: ignore[method-assign]
            pre_stop_target = session_dir / "stop-before-admission.png"
            pre_stop_errors: list[BaseException] = []

            def capture_before_stop() -> None:
                try:
                    daemon._capture_native_region_for_identity(
                        identity,
                        destination=pre_stop_target,
                        deadline=time.monotonic() + 8.0,
                    )
                except BaseException as exc:
                    pre_stop_errors.append(exc)

            pre_stop_events: list[tuple[str, float]] = []
            admission_count_before_stop = len(admission_events)
            shell_count_before_stop = len(json.loads(compositor["area_log"].read_text(encoding="utf-8")))
            pre_stop_thread = threading.Thread(target=capture_before_stop, daemon=True)
            pre_stop_thread.start()
            assert before_admission.wait(2.0)
            pre_stop_events.append(("pre_admission_barrier", time.monotonic()))
            daemon.controller.stop()
            pre_stop_events.append(("controller_stop", time.monotonic()))
            release_admission.set()
            pre_stop_events.append(("barrier_release", time.monotonic()))
            pre_stop_thread.join(timeout=3.0)
            assert not pre_stop_thread.is_alive()
            pre_stop_events.append(("capture_refused", time.monotonic()))
            assert [event[0] for event in pre_stop_events] == [
                "pre_admission_barrier",
                "controller_stop",
                "barrier_release",
                "capture_refused",
            ]
            assert pre_stop_events[0][1] <= pre_stop_events[1][1] <= pre_stop_events[2][1]
            assert pre_stop_errors and isinstance(pre_stop_errors[0], DriverError)
            assert "changed before observer admission" in str(pre_stop_errors[0])
            assert len(admission_events) == admission_count_before_stop
            assert (
                len(json.loads(compositor["area_log"].read_text(encoding="utf-8"))) == shell_count_before_stop
            )
            assert not pre_stop_target.exists()
            assert not backend._active_processes and not backend.active_process_groups
            assert not driver.guardian.observer_process_groups
            assert driver.guardian.lease.held
            assert driver.guardian.admission_gate_ready() is None

            # A fresh private daemon owns a fresh private canonical lease. Its
            # ordinary default route registers before Shell entry; stop then
            # revokes the capture epoch while the external compositor blocks.
            driver.close()
            cancellation_dir = session_dir / "admitted-stop"
            cancellation_dir.mkdir(mode=0o700)
            cancellation_config = replace(
                config,
                journal=cancellation_dir / "journal.json",
                socket=cancellation_dir / "session.sock",
                capture_dir=cancellation_dir / "captures",
            )
            cancellation_backend = X11Backend(profile)
            cancellation_backend.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
            cancellation_driver = DesktopDriver(
                profile=profile,
                backend=cancellation_backend,
                lease_path=cancellation_dir / "desktop.lock",
            )
            cancellation_daemon = SessionDaemon(cancellation_config, driver=cancellation_driver)
            cancellation_status = cancellation_daemon.controller.start()
            assert cancellation_status.state.value == "NATIVE_CALIBRATION"
            cancellation_target = cancellation_dir / "revoked-default-capture.png"
            # The earlier compiled-command serialization case used the same
            # compositor gate. Reset its markers so this race proves a new owner
            # process reached Shell and remains blocked there.
            compositor["area_started_path"].unlink(missing_ok=True)
            compositor["area_release_path"].unlink(missing_ok=True)
            compositor["area_block_path"].touch(mode=0o600)
            epoch_before = cancellation_backend._capture_revocation_epoch
            cancellation_errors: list[BaseException] = []

            def capture_until_stop() -> None:
                try:
                    cancellation_daemon._capture_native_region_for_identity(
                        identity,
                        destination=cancellation_target,
                        deadline=time.monotonic() + 8.0,
                    )
                except BaseException as exc:
                    cancellation_errors.append(exc)

            cancellation_thread = threading.Thread(target=capture_until_stop, daemon=True)
            try:
                cancellation_thread.start()
                shell_deadline = time.monotonic() + 4.0
                while not compositor["area_started_path"].exists() and time.monotonic() < shell_deadline:
                    time.sleep(0.01)
                assert compositor["area_started_path"].exists(), (
                    f"fresh-owner capture did not reach blocked Shell; errors={cancellation_errors!r}; "
                    f"active_processes={cancellation_backend._active_processes!r}; "
                    f"active_groups={cancellation_backend.active_process_groups!r}; "
                    f"guardian_groups={cancellation_driver.guardian.observer_process_groups!r}; "
                    f"watchdog_failed={cancellation_driver.guardian._watchdog_failed!r}; "
                    f"area_calls={compositor['area_log'].read_text(encoding='utf-8') if compositor['area_log'].exists() else None!r}; "
                    f"gjs_stderr={(compositor['root'] / 'gjs.stderr').read_text(encoding='utf-8') if (compositor['root'] / 'gjs.stderr').exists() else None!r}"
                )
                assert len(cancellation_driver.guardian.observer_process_groups) == 1
                admitted_event = admission_events[-2:]
                assert [event[0] for event in admitted_event] == ["admission_enter", "gate_released"]
                shell_started = int(compositor["area_started_path"].read_text(encoding="ascii")) / 1_000_000
                assert admitted_event[-1][1] <= shell_started
                stop_started = time.monotonic()
                cancellation_daemon.controller.stop()
                stop_finished = time.monotonic()
                assert stop_finished - stop_started < 1.0
                compositor["area_block_path"].unlink()
                compositor["area_release_path"].touch(mode=0o600)
                cancellation_thread.join(timeout=4.0)
                assert not cancellation_thread.is_alive()
                assert cancellation_errors and isinstance(cancellation_errors[0], DriverError)
                assert "revoked" in str(cancellation_errors[0]).lower()
                assert cancellation_backend._capture_revocation_epoch > epoch_before
                assert not cancellation_target.exists()
                assert not cancellation_backend._active_processes
                assert not cancellation_backend.active_process_groups
                assert not cancellation_driver.guardian.observer_process_groups
                assert cancellation_driver.guardian.lease.held
                assert not cancellation_driver.guardian._watchdog_failed
                assert cancellation_driver.guardian.admission_gate_ready() is None
            finally:
                cancellation_driver.close()
        finally:
            if retained_capture is not None:
                daemon.release_native_capture(retained_capture)
            daemon._cleanup_native_owned_captures()
            driver.close()


def test_paused_diagnostic_uses_actual_config_ipc_driver_and_eight_compiled_samples(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the opt-in runner at its real socket and compiled capture boundaries."""

    root = Path(__file__).resolve().parents[1]
    harness_spec = importlib.util.spec_from_file_location(
        "region_offline_harness_runner", root / "tools/gnome-telemetry-region/offline_harness.py"
    )
    assert harness_spec is not None and harness_spec.loader is not None
    harness = importlib.util.module_from_spec(harness_spec)
    harness_spec.loader.exec_module(harness)

    freeze = json.loads(
        (root / ".archive/executor-review/gnome-telemetry-region-r6-final-freeze.json").read_text(
            encoding="utf-8"
        )
    )
    frozen_producer = Path(freeze["private_cache"]) / "prefix/bin/gnome-screenshot"
    producer_sha256 = hashlib.sha256(frozen_producer.read_bytes()).hexdigest()
    assert producer_sha256 == freeze["build"]["private_binary_sha256"]
    width_height = (256, 256)

    client = WowClient()
    client.set_canonical_plan()
    client.login()
    client.publish_agent()
    payloads: list[bytes] = []
    decoded_sequences: list[int] = []
    probe = PixelDecoder()
    # The composed coverage below includes the late-refusal regression and a
    # second real eight-sample model-counter run; retain enough independent
    # compiled payloads for every actual ScreenshotArea call.
    for index in range(60):
        client.update_agent(1.0)
        target = BytesIO()
        client.render_agent_capture().save(target, format="PNG")
        payload = target.getvalue()
        payloads.append(payload)
        with Image.open(BytesIO(payload)) as image:
            image.load()
            decoded = probe.decode(image, monotonic=float(index + 1), window_identity="runner-fixture")
        assert decoded.frame is not None
        decoded_sequences.append(decoded.frame.sequence)
    assert decoded_sequences == sorted(set(decoded_sequences))
    alternate_client = WowClient()
    alternate_client.set_canonical_plan()
    alternate_client.login()
    alternate_client.publish_agent()
    alternate_client.update_agent(1.0)
    alternate_png = BytesIO()
    alternate_client.render_agent_capture().save(alternate_png, format="PNG")
    with Image.open(BytesIO(payloads[0])) as image:
        original_boot = PixelDecoder().decode(image, monotonic=1.0, window_identity="original").frame
    with Image.open(BytesIO(alternate_png.getvalue())) as image:
        alternate_boot = PixelDecoder().decode(image, monotonic=1.0, window_identity="alternate").frame
    assert original_boot is not None and alternate_boot is not None
    assert alternate_boot.boot != original_boot.boot

    rectangle = (123, 77, *width_height)
    desktop = BytesIO()
    Image.new("RGB", (1920, 1080), (30, 40, 50)).save(desktop, format="PNG")
    session_dir = tmp_path / "paused-runner"
    session_dir.mkdir(mode=0o700)
    producer = session_dir / "gnome-screenshot-r6"
    producer.write_bytes(frozen_producer.read_bytes())
    producer.chmod(0o700)
    xauthority = session_dir / "Xauthority"
    xauthority.touch(mode=0o600)
    socket_path = session_dir / "session.sock"
    saved_variables = session_dir / "SavedVariables.lua"
    companion_state = session_dir / "companion.json"
    data_lua = session_dir / "Data.lua"
    saved_variables.write_text("", encoding="utf-8")
    companion_state.write_text("{}", encoding="utf-8")
    data_lua.write_text("", encoding="utf-8")
    plan_json = "{}"
    plan_hash = hashlib.sha256(plan_json.encode()).hexdigest()
    codex_path = Path(
        "/home/dev/.cache/crowley/codex/0.162.1/node_modules/@openai/codex-linux-x64/"
        "vendor/x86_64-unknown-linux-musl/bin/codex"
    )
    assert codex_path.is_file()
    config_path = session_dir / "session.toml"

    def toml_string(value: str) -> str:
        return json.dumps(value)

    config_path.write_text(
        "[profile]\n"
        f"display = {toml_string(':runner-fixture')}\n"
        f"xauthority = {toml_string(str(xauthority))}\n"
        "wine_prefix = '/private-fixture-only'\n"
        "canvas_crop = [123, 77, 256, 256]\n"
        "model_crop = [80, 48, 640, 480]\n"
        f"plan_hash = '{plan_hash}'\n"
        "plan_json = '{}'\n"
        "[session]\n"
        f"socket = {toml_string(str(socket_path))}\n"
        f"journal = {toml_string(str(session_dir / 'journal.json'))}\n"
        f"capture_dir = {toml_string(str(session_dir / 'captures'))}\n"
        f"codex_path = {toml_string(str(codex_path))}\n"
        f"saved_variables = {toml_string(str(saved_variables))}\n"
        f"companion_state = {toml_string(str(companion_state))}\n"
        f"data_lua = {toml_string(str(data_lua))}\n"
        f"telemetry_region_executable = {toml_string(str(producer))}\n"
        f"telemetry_region_executable_sha256 = '{producer_sha256}'\n",
        encoding="utf-8",
    )

    identity = WindowIdentity(
        0x200,
        os.getpid(),
        "WowB.exe",
        "World of Warcraft",
        "wowb.exe",
        0x201,
        (0, 0, 1928, 1092),
        (0, 0, 1920, 1080),
        0x200,
        str(os.getpid()),
        ":runner-fixture",
        "paused-runner-private-window",
        0x200,
        0x200,
        frozenset({0x200, 0x201}),
    )
    output_dir = session_dir / "evidence"
    with harness.private_shell_compositor(
        payloads=payloads,
        full_desktop=desktop.getvalue(),
        rectangle=rectangle,
        allow_area_gate=True,
    ) as compositor:
        monkeypatch.setattr(
            driver_module, "GNOME_CAPTURE_LOCK_PATH", tmp_path / "runner-private-capture.lock"
        )
        # The private display and configured display must be the same so
        # DesktopDriver verifies and captures through its normal X11 path.
        identity = replace(identity, display=compositor["display"])
        monkeypatch.setattr(X11Backend, "resolve_identity", lambda self, **_kwargs: identity)
        text = config_path.read_text(encoding="utf-8").replace(":runner-fixture", compositor["display"])
        config_path.write_text(text, encoding="utf-8")
        config = load_config(config_path)
        daemon = SessionDaemon(config)
        driver = daemon.driver
        backend = driver.backend
        assert isinstance(backend, X11Backend)
        assert daemon.config.profile is not driver.profile
        assert driver.lease_path.is_relative_to(compositor["root"])
        receipt_publications: list[tuple[Path, dict[str, object]]] = []
        fail_success_persist = [False]
        original_persist_receipt = SessionDaemon._persist_paused_region_receipt

        def record_persist_receipt(path: Path, value: dict[str, object]) -> None:
            receipt_publications.append((path, value.copy()))
            if fail_success_persist[0] and value.get("ok") is True:
                fail_success_persist[0] = False
                raise OSError("injected durable success receipt failure")
            original_persist_receipt(path, value)

        monkeypatch.setattr(
            SessionDaemon,
            "_persist_paused_region_receipt",
            staticmethod(record_persist_receipt),
        )
        admission_events: list[tuple[str, float, int | None]] = []
        stop_revoke_events: list[float] = []
        original_observer_admission = driver.guardian.observer_dispatch_admission
        original_revoke = driver.guardian.revoke

        def record_observer_admission(start, *, calibration: bool = False):  # type: ignore[no-untyped-def]
            admission_events.append(("admission_enter", time.monotonic(), None))
            admitted = original_observer_admission(start, calibration=calibration)
            process = getattr(admitted, "process", None) or getattr(
                getattr(admitted, "observer", None), "process", None
            )
            assert process is not None
            admission_events.append(("gate_released", time.monotonic(), process.pid))
            return admitted

        driver.guardian.observer_dispatch_admission = record_observer_admission  # type: ignore[method-assign]

        def record_revoke(reason: str) -> int:
            if reason == "stop requested":
                stop_revoke_events.append(time.monotonic())
            return original_revoke(reason)

        driver.guardian.revoke = record_revoke  # type: ignore[method-assign]
        daemon.controller.pause("private runner fixture")
        from crowley.session.cli import (
            SessionIPC,
            _BoundedIPCReader,
            _encode_bounded_record,
            _parse_bounded_json,
            _socket_request,
            serve,
        )

        ipc = SessionIPC(daemon.controller, daemon)
        status_listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        status_listener.bind(str(socket_path))
        os.chmod(socket_path, 0o600)
        status_listener.listen(8)
        status_listener.settimeout(0.1)
        stop_status = threading.Event()
        request_count = [0]
        sample_count = [0]
        flip_generation_after_sample = [None]
        response_mode: list[str | None] = [None]
        late_response_started = threading.Event()
        late_response_release = threading.Event()
        late_refusal_started = threading.Event()
        late_refusal_release = threading.Event()
        ipc_workers: list[threading.Thread] = []
        dispatch_observations: list[dict[str, object]] = []
        ipc_handler_errors: list[str] = []
        ipc_late_transport_errors: list[str] = []

        def handle_ipc(connection: socket.socket) -> None:
            with connection:
                replied = False
                mode: str | None = None
                try:
                    reader = _BoundedIPCReader(connection)
                    raw = reader.read_record(4096)
                    if raw is None:
                        return
                    request = _parse_bounded_json(raw)
                    assert isinstance(request, dict)
                    request_count[0] += 1
                    mode = None
                    if request.get("command") == "paused_region_sample":
                        sample_count[0] += 1
                        mode = response_mode[0]
                        response_mode[0] = None
                    response = ipc.dispatch(request)
                    if mode is not None:
                        owner_failure = response.get("failure")
                        dispatch_observations.append(
                            {
                                "mode": mode,
                                "ok": response.get("ok"),
                                "has_sample": isinstance(response.get("sample"), dict),
                                "error": response.get("error"),
                                "owner_failure_phase": (
                                    owner_failure.get("phase") if isinstance(owner_failure, dict) else None
                                ),
                                "owner_failure_error": (
                                    owner_failure.get("error") if isinstance(owner_failure, dict) else None
                                ),
                            }
                        )
                    if mode == "late_response":
                        late_response_started.set()
                        late_response_release.wait(2.0)
                    elif mode == "late_refusal":
                        late_refusal_started.set()
                        # Deliver the durable refusal just after the owner
                        # sample deadline, while still inside the runner's
                        # bounded evidence grace.  Deriving this wait from
                        # the actual request deadline keeps the regression
                        # deterministic without replacing the production
                        # clock.
                        response_deadline = request.get("deadline")
                        if isinstance(response_deadline, (int, float)) and not isinstance(
                            response_deadline, bool
                        ):
                            late_refusal_release.wait(
                                max(0.0, float(response_deadline) - time.monotonic() + 0.03)
                            )
                        else:
                            late_refusal_release.wait(2.0)
                    sample_response = response.get("sample")
                    if (
                        mode
                        in {
                            "wrong_generation",
                            "wrong_digest",
                            "incomplete_png",
                            "changed_identity",
                        }
                        and response.get("ok") is True
                        and isinstance(sample_response, dict)
                    ):
                        if mode == "wrong_generation":
                            sample_response["generation"] += 1
                        elif mode == "wrong_digest":
                            sample_response["png_sha256"] = "0" * 64
                        elif mode == "incomplete_png":
                            sample_response["png_base64"] = sample_response["png_base64"][:-4]
                        else:
                            sample_response["identity_after"] = "changed-window"
                    if mode == "duplicate_record":
                        connection.sendall(b'{"ok":true,"ok":true}\n')
                        replied = True
                        return
                    if mode == "truncated_record":
                        connection.sendall(b'{"ok":true,"sample":')
                        replied = True
                        return
                    if mode == "oversized_record":
                        connection.sendall(b"x" * (524288 + 1))
                        replied = True
                        return
                    connection.sendall(_encode_bounded_record(response, 524288))
                    replied = True
                    if flip_generation_after_sample[0] == sample_count[0]:
                        flip_generation_after_sample[0] = None
                        daemon.controller.pause("fixture generation changed after published sample")
                except Exception as exc:
                    error_record = f"{type(exc).__name__}: {exc}"
                    late_client_disconnect = mode in {"late_response", "late_refusal"} and isinstance(
                        exc, OSError
                    )
                    if late_client_disconnect:
                        ipc_late_transport_errors.append(error_record)
                    else:
                        ipc_handler_errors.append(error_record)
                    if not replied and not late_client_disconnect:
                        try:
                            connection.sendall(
                                _encode_bounded_record(
                                    {"ok": False, "error": f"fixture IPC handler failed: {exc}"},
                                    524288,
                                )
                            )
                        except OSError as send_error:
                            ipc_handler_errors.append(f"handler error response failed: {send_error}")

        def serve_ipc() -> None:
            while not stop_status.is_set():
                try:
                    connection, _address = status_listener.accept()
                except TimeoutError:
                    continue
                except OSError:
                    return
                worker = threading.Thread(target=handle_ipc, args=(connection,), daemon=True)
                ipc_workers.append(worker)
                worker.start()

        status_thread = threading.Thread(target=serve_ipc, daemon=True)
        status_thread.start()
        try:
            initial_generation = daemon.controller.status().generation
            request_started = time.monotonic()
            valid_sample_request = {
                "command": "paused_region_sample",
                "generation": initial_generation,
                "parent_started": request_started,
                "deadline": request_started + 0.9,
                "config_file_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                "config_semantic_sha256": session_config_semantic_sha256(config),
            }
            refused = ipc.dispatch({**valid_sample_request, "generation": initial_generation - 1})
            assert refused["ok"] is False and "generation" in refused["error"]
            refused = ipc.dispatch({**valid_sample_request, "parent_started": float("nan")})
            assert refused["ok"] is False and "finite" in refused["error"]
            refused = ipc.dispatch({**valid_sample_request, "deadline": request_started + 1.01})
            assert refused["ok"] is False and "one second" in refused["error"]
            fence_held = threading.Event()
            release_fence = threading.Event()

            def hold_motion_fence() -> None:
                with daemon._motion_intent_lock:
                    fence_held.set()
                    release_fence.wait(1.0)

            fence_worker = threading.Thread(target=hold_motion_fence, daemon=True)
            fence_worker.start()
            assert fence_held.wait(0.5)
            refused = ipc.dispatch(valid_sample_request)
            release_fence.set()
            fence_worker.join(timeout=1.0)
            assert refused["ok"] is False and "another motion" in refused["error"]
            # Revoke a real armed Guardian epoch while an owned XI2 observer
            # is registered. The revoke callback releases the backend capture
            # epoch, which must make paused diagnostics fail before creating
            # their output directory.
            calibration_observer = driver.start_input_observer(calibration=False)
            assert calibration_observer.observer.process.poll() is None
            assert len(driver.guardian.observer_process_groups) == 1
            daemon.controller.start()
            canceled_generation = driver.guardian.arm(_evidence())
            driver.guardian.dispatch_admission(
                canceled_generation,
                lambda: backend.activate_generation(canceled_generation),
            )
            try:
                daemon.controller.pause("exercise retained capture cancellation")
            finally:
                driver.stop_input_observer(calibration_observer)
            assert not driver.guardian.observer_process_groups
            assert backend._cancel_active.is_set()
            canceled_status = daemon.controller.status()
            canceled_request_started = time.monotonic()
            canceled_request = {
                **valid_sample_request,
                "generation": canceled_status.generation,
                "parent_started": canceled_request_started,
                "deadline": canceled_request_started + 0.9,
            }
            before_canceled_dirs = sorted((session_dir / "captures").glob("paused-region-*"))
            refused = ipc.dispatch(canceled_request)
            assert refused["ok"] is False and "capture-revoked backend" in refused["error"]
            assert sorted((session_dir / "captures").glob("paused-region-*")) == before_canceled_dirs
            assert sample_count[0] == 0
            assert not compositor["area_log"].exists()

            # A real pause after capture revocation cannot be reused for the
            # diagnostic. Close it and construct a fresh, unarmed owner with
            # the same configured producer and private X11 environment.
            daemon._cleanup_native_owned_captures()
            driver.close()
            fresh_owner_dir = session_dir / "fresh-owner"
            fresh_owner_dir.mkdir(mode=0o700)
            config_text = config_path.read_text(encoding="utf-8")
            config_text = config_text.replace(
                str(session_dir / "journal.json"), str(fresh_owner_dir / "journal.json")
            )
            config_text = config_text.replace(
                str(session_dir / "captures"), str(fresh_owner_dir / "captures")
            )
            config_path.write_text(config_text, encoding="utf-8")
            config = load_config(config_path)
            daemon = SessionDaemon(config)
            driver = daemon.driver
            backend = driver.backend
            assert isinstance(backend, X11Backend)
            assert daemon.config.profile is not driver.profile
            assert driver.lease_path.is_relative_to(compositor["root"])
            daemon.controller.pause("private runner fixture on fresh owner")
            live_binding = _independent_live_binding(config_path, producer)
            original_observer_admission = driver.guardian.observer_dispatch_admission
            driver.guardian.observer_dispatch_admission = record_observer_admission  # type: ignore[method-assign]
            original_revoke = driver.guardian.revoke
            driver.guardian.revoke = record_revoke  # type: ignore[method-assign]
            admission_events.clear()
            stop_revoke_events.clear()
            ipc = SessionIPC(daemon.controller, daemon)
            initial_generation = daemon.controller.status().generation
            request_started = time.monotonic()
            valid_sample_request = {
                "command": "paused_region_sample",
                "generation": initial_generation,
                "parent_started": request_started,
                "deadline": request_started + 0.9,
                "config_file_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                "config_semantic_sha256": session_config_semantic_sha256(config),
            }

            result = harness.run_paused_diagnostic(config_path, output_dir)
            assert result["run_state"] == "passed"
            expected_generation = daemon.controller.status().generation
            assert result["generation"] == expected_generation
            assert len(result["attempts"]) == 8
            samples = result["attempts"]
            assert isinstance(samples, list)
            assert [sample["identity"]["sequence"] for sample in samples] == decoded_sequences[:8]
            assert all(sample["identity"]["fingerprint"] == identity.fingerprint for sample in samples)
            assert all(
                sample["owner"]["producer_binding"]["protocol_branch"] == "ScreenshotArea"
                for sample in samples
            )
            assert all(sample["owner"]["cleanup"]["attempt_retired"] is True for sample in samples)
            assert all(sample["owner"]["cleanup"]["capture_process_reaped"] is True for sample in samples)
            assert all(
                sample["owner"]["model_calls_before"] == {"started": 0, "succeeded": 0, "failed": 0}
                for sample in samples
            )
            assert all(
                sample["owner"]["model_calls_after"] == {"started": 0, "succeeded": 0, "failed": 0}
                for sample in samples
            )
            assert all(
                sample["owner"]["model_call_delta"] == {"started": 0, "succeeded": 0, "failed": 0}
                for sample in samples
            )
            assert all(
                sample["strict_decode_finished_monotonic"] - sample["outer_started_monotonic"] < 1.0
                for sample in samples
            )
            assert all(
                0.75
                <= samples[index]["outer_started_monotonic"] - samples[index - 1]["outer_started_monotonic"]
                <= 1.25
                for index in range(1, 8)
            )
            assert all(
                0.75
                <= samples[index]["sample_completed_monotonic"]
                - samples[index - 1]["sample_completed_monotonic"]
                <= 1.25
                for index in range(1, 8)
            )
            assert all(
                sample["application_compute_cpu_method"] == "time.process_time_ns" for sample in samples
            )
            persisted = json.loads((output_dir / "receipt.json").read_text(encoding="utf-8"))
            assert persisted == result
            evaluated, completed_pairs, _ = _evaluate_persisted_live_receipt(
                persisted, output_dir / "receipt.json", live_binding
            )
            assert evaluated["eligible"] is True
            assert len(completed_pairs) == 8
            assert evaluated["attempts_begun"] == 8
            success_publications = [value for _path, value in receipt_publications if value.get("ok") is True]
            assert len(success_publications) == 8
            assert all("owner_returned" in value for value in success_publications)
            assert all(
                set(value)
                == {
                    "ok",
                    "generation",
                    "parent_started",
                    "deadline",
                    "owner_entered",
                    "capture_returned",
                    "identity",
                    "identity_after",
                    "source",
                    "config",
                    "producer",
                    "receipt",
                    "png_sha256",
                    "png_bytes",
                    "png_base64",
                    "artifact_directory",
                    "artifact_png",
                    "cleanup",
                    "owner_returned",
                    "source_binding",
                    "model_calls_before",
                    "model_calls_after",
                    "model_call_delta",
                    "response_ready",
                }
                for value in success_publications
            )
            assert all(sample["owner"]["cleanup"]["lease_held"] for sample in samples)
            assert all(sample["owner"]["cleanup"]["watchdog_healthy"] for sample in samples)
            assert len(json.loads(compositor["area_log"].read_text(encoding="utf-8"))) == 8
            assert request_count[0] == 17  # eight status/sample pairs plus final status
            successful_gate_events = admission_events[:16]
            successful_shell_events = json.loads(compositor["area_log"].read_text(encoding="utf-8"))
            assert [event[0] for event in successful_gate_events] == [
                name for _ in range(8) for name in ("admission_enter", "gate_released")
            ]
            assert len(successful_shell_events) == 8
            assert all(
                successful_gate_events[index * 2 + 1][1] * 1_000_000
                <= successful_shell_events[index]["monotonic_us"]
                for index in range(8)
            )

            # A second owner boot in the next genuine Shell response fails on
            # sample 1 while retaining both client images.
            payload_paths = compositor["payload_paths"]
            assert isinstance(payload_paths, tuple)
            payload_paths[9].write_text(
                base64.b64encode(alternate_png.getvalue()).decode("ascii"), encoding="ascii"
            )
            boot_change_samples = sample_count[0]
            boot_change_calls = len(successful_shell_events)
            boot_change_dir = session_dir / "evidence-boot-change"
            with pytest.raises(RuntimeError, match="paused diagnostic failed; evidence="):
                harness.run_paused_diagnostic(config_path, boot_change_dir)
            boot_change_receipt = json.loads((boot_change_dir / "receipt.json").read_text(encoding="utf-8"))
            assert boot_change_receipt["run_state"] == "failed"
            assert boot_change_receipt["attempts"][1]["failure"] == {
                "phase": "strict_decode",
                "reason_code": "strict_decode_failed",
            }
            assert len(boot_change_receipt["attempts"]) == 2
            assert sample_count[0] == boot_change_samples + 2
            assert (
                len(json.loads(compositor["area_log"].read_text(encoding="utf-8"))) == boot_change_calls + 2
            )
            assert len(list(boot_change_dir.glob("paused-*.png"))) == 2
            boot_evaluated, boot_pairs, _ = _evaluate_persisted_live_receipt(
                boot_change_receipt, boot_change_dir / "receipt.json", live_binding
            )
            assert "strict_decode_failed" in boot_evaluated["reason_codes"]
            assert len(boot_pairs) == 1

            def area_count() -> int:
                return len(json.loads(compositor["area_log"].read_text(encoding="utf-8")))

            def run_runner_failure(mode: str, directory: Path) -> dict[str, object]:
                before_samples = sample_count[0]
                before_area = area_count()
                before_owner_directories = len(list(Path(config.capture_dir).glob("paused-region-*")))
                response_mode[0] = mode
                with pytest.raises(RuntimeError, match="evidence=.*receipt.json"):
                    harness.run_paused_diagnostic(config_path, directory)
                observed_dispatch = dispatch_observations[-1] if dispatch_observations else None
                if (
                    not isinstance(observed_dispatch, dict)
                    or observed_dispatch.get("mode") != mode
                    or observed_dispatch.get("ok") is not True
                    or observed_dispatch.get("has_sample") is not True
                ):
                    pytest.fail(
                        f"fixture could not exercise {mode}; actual owner dispatch was {observed_dispatch!r}"
                    )
                failed_receipt = json.loads((directory / "receipt.json").read_text(encoding="utf-8"))
                assert failed_receipt["run_state"] == "failed"
                assert sample_count[0] == before_samples + 1
                assert area_count() == before_area + 1
                owner_directories = sorted(Path(config.capture_dir).glob("paused-region-*"))
                assert len(owner_directories) == before_owner_directories + 1
                assert (owner_directories[-1] / "capture.png").is_file()
                assert (owner_directories[-1] / "receipt.json").is_file()
                assert len(failed_receipt["attempts"]) == 1
                assert failed_receipt["attempts"][0]["owner"] is None or isinstance(
                    failed_receipt["attempts"][0]["owner"], dict
                )
                assert not list(directory.glob("paused-*.png"))
                return failed_receipt

            for mode in (
                "wrong_generation",
                "wrong_digest",
                "incomplete_png",
                "duplicate_record",
                "truncated_record",
                "oversized_record",
            ):
                failed_receipt = run_runner_failure(mode, session_dir / f"evidence-{mode}")
                assert failed_receipt["attempts"][0]["failure"]["phase"] in {"owner_capture", "owner_ipc"}

            response_mode[0] = "changed_identity"
            changed_identity_dir = session_dir / "evidence-changed-identity"
            with pytest.raises(RuntimeError, match="evidence=.*receipt.json"):
                harness.run_paused_diagnostic(config_path, changed_identity_dir)
            changed_identity_receipt = json.loads(
                (changed_identity_dir / "receipt.json").read_text(encoding="utf-8")
            )
            assert changed_identity_receipt["attempts"][0]["failure"]["phase"] == "owner_capture"
            assert len(list(changed_identity_dir.glob("paused-*.png"))) == 1
            assert (changed_identity_dir / "paused-00.png").is_file()

            late_before_samples = sample_count[0]
            late_before_area = area_count()
            response_mode[0] = "late_response"
            with pytest.raises(RuntimeError, match="evidence=.*receipt.json"):
                harness.run_paused_diagnostic(config_path, session_dir / "evidence-late-response")
            late_receipt = json.loads(
                (session_dir / "evidence-late-response" / "receipt.json").read_text(encoding="utf-8")
            )
            assert late_receipt["run_state"] == "failed"
            assert late_receipt["attempts"][0]["failure"]["phase"] in {"deadline", "owner_ipc"}
            assert late_response_started.is_set()
            late_response_release.set()
            assert sample_count[0] == late_before_samples + 1
            assert area_count() == late_before_area + 1
            assert not list((session_dir / "evidence-late-response").glob("paused-*.png"))
            late_timeout = session_dir / "evidence-late-response" / "owner-timeout-00.json"
            assert late_timeout.is_file()
            assert late_timeout.stat().st_mode & 0o777 == 0o600

            # A real owner refusal carrying a returned sample can arrive within
            # the bounded IPC grace after its sample deadline. The runner must
            # retain the private owner refusal but classify the attempt as the
            # deadline failure before attempting client PNG publication.
            daemon.controller.pause("restore paused state for late refusal")
            fail_success_persist[0] = True
            response_mode[0] = "late_refusal"
            late_refusal_dir = session_dir / "evidence-late-refusal"
            late_refusal_owner_dirs_before = set(Path(config.capture_dir).glob("paused-region-*"))
            with pytest.raises(RuntimeError, match="evidence=.*receipt.json"):
                harness.run_paused_diagnostic(config_path, late_refusal_dir)
            late_refusal_receipt = json.loads((late_refusal_dir / "receipt.json").read_text(encoding="utf-8"))
            assert late_refusal_started.is_set()
            assert late_refusal_receipt["attempts"][0]["failure"] == {
                "phase": "deadline",
                "reason_code": "sample_deadline_missed",
            }
            assert late_refusal_receipt["attempts"][0]["owner"] is not None
            assert not list(late_refusal_dir.glob("paused-*.png"))
            late_refusal_owner_dirs = set(Path(config.capture_dir).glob("paused-region-*"))
            late_refusal_new_owner_dirs = late_refusal_owner_dirs - late_refusal_owner_dirs_before
            assert len(late_refusal_new_owner_dirs) == 1
            late_refusal_private = next(iter(late_refusal_new_owner_dirs)) / "receipt.json"
            assert late_refusal_private.is_file()
            assert json.loads(late_refusal_private.read_text(encoding="utf-8"))["ok"] is False
            late_refusal_record = late_refusal_dir / "owner-refusal-00.json"
            assert late_refusal_record.is_file()
            assert late_refusal_record.stat().st_mode & 0o777 == 0o600
            assert json.loads(late_refusal_record.read_text(encoding="utf-8"))["failure"]["phase"] == (
                "owner_receipt_persist"
            )
            late_refusal_release.set()

            # Repeating the same genuine compositor payload becomes NO_CHANGE
            # at PixelDecoder. The runner preserves both owner PNGs and stops
            # after sample 1 rather than collecting six more frames.
            payload_paths = compositor["payload_paths"]
            assert isinstance(payload_paths, tuple)
            duplicate_index = area_count() + 1
            payload_paths[duplicate_index].write_bytes(payload_paths[area_count()].read_bytes())
            no_change_samples = sample_count[0]
            no_change_calls = area_count()
            no_change_dir = session_dir / "evidence-no-change"
            with pytest.raises(RuntimeError, match="paused diagnostic failed; evidence="):
                harness.run_paused_diagnostic(config_path, no_change_dir)
            no_change_receipt = json.loads((no_change_dir / "receipt.json").read_text(encoding="utf-8"))
            assert no_change_receipt["attempts"][1]["failure"] == {
                "phase": "strict_decode",
                "reason_code": "unknown_required_stage",
            }
            assert len(no_change_receipt["attempts"]) == 2
            assert sample_count[0] == no_change_samples + 2
            assert area_count() == no_change_calls + 2
            assert len(list(no_change_dir.glob("paused-*.png"))) == 2
            assert all(path.is_file() for path in no_change_dir.glob("paused-*.png"))
            no_change_evaluated, no_change_pairs, _ = _evaluate_persisted_live_receipt(
                no_change_receipt, no_change_dir / "receipt.json", live_binding
            )
            assert no_change_evaluated.get("receipt_refused") is True
            assert no_change_evaluated["reason_codes"] == ["attempt_lifecycle_invalid"]
            assert no_change_pairs == []

            # Install one real driver anchor bound to an actual compiled
            # owner PNG, then prove the same paused owner still completes IPC.
            # The private fixture provider supplies the known control bounds;
            # capture bytes, identity, target ancestry, sequence and generation
            # are sealed by DesktopDriver's normal measured-anchor API.
            anchor_capture_started = time.monotonic()
            anchor_capture_request = {
                "command": "paused_region_sample",
                "generation": daemon.controller.status().generation,
                "parent_started": anchor_capture_started,
                "deadline": anchor_capture_started + 0.95,
                "config_file_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                "config_semantic_sha256": session_config_semantic_sha256(config),
            }
            anchor_capture_response = _socket_request(socket_path, anchor_capture_request, timeout=1.1)
            assert anchor_capture_response["ok"] is True
            anchor_sample = anchor_capture_response["sample"]
            anchor_png = Path(anchor_sample["artifact_png"])
            anchor_attempt = anchor_sample["receipt"]

            def fixture_anchor_provider(anchor_identity, action):  # type: ignore[no-untyped-def]
                assert action == "open_ah"
                return driver.build_measured_anchor(
                    action=action,
                    x=anchor_identity.child_geometry[2] // 2,
                    y=anchor_identity.child_geometry[3] // 2,
                    capture_path=anchor_png,
                    capture_id=anchor_sample["png_sha256"],
                    capture_sequence=1,
                    capture_monotonic=anchor_attempt["capture_returned"],
                    scene=DesktopDriver.ANCHOR_SCENES[action],
                    bounds=(0, 0, anchor_identity.child_geometry[2], anchor_identity.child_geometry[3]),
                    target_xid=anchor_identity.child_xid,
                    target_ancestry=(anchor_identity.xid, anchor_identity.child_xid),
                    generation=driver.guardian.generation,
                    source="native-visual",
                    facts=(("control", DesktopDriver.ANCHOR_CONTROLS[action]),),
                )

            anchor_generation = driver.guardian.arm(_evidence())
            driver.guardian.dispatch_admission(
                anchor_generation,
                lambda: backend.activate_generation(anchor_generation),
            )
            driver.measured_anchor_provider = fixture_anchor_provider
            measured_anchor = driver.measure_pointer_anchor("open_ah", generation=anchor_generation)
            assert measured_anchor.verify_seal() is None
            assert driver._measured_anchors["open_ah"] is measured_anchor
            assert backend._measured_anchors["open_ah"] is measured_anchor
            config_semantic_before_runtime_anchor_revoke = session_config_semantic_sha256(config)
            driver.guardian.revoke("finish private anchor capture proof")
            assert not driver.guardian.armed and not backend._cancel_active.is_set()
            assert session_config_semantic_sha256(config) == config_semantic_before_runtime_anchor_revoke
            after_anchor_started = time.monotonic()
            after_anchor_response = _socket_request(
                socket_path,
                {
                    **anchor_capture_request,
                    "generation": daemon.controller.status().generation,
                    "parent_started": after_anchor_started,
                    "deadline": after_anchor_started + 0.95,
                    "config_semantic_sha256": session_config_semantic_sha256(load_config(config_path)),
                },
                timeout=1.1,
            )
            assert after_anchor_response["ok"] is True

            # The default-constructed driver has an independent profile copy.
            # Drift in any real configured field must fail before producer
            # admission even while the loaded daemon config and client hash
            # remain unchanged.
            original_model_crop = driver.profile.model_crop
            semantic_config_hash = session_config_semantic_sha256(daemon.config)
            config_field_started = time.monotonic()
            config_field_request = {
                **anchor_capture_request,
                "generation": daemon.controller.status().generation,
                "parent_started": config_field_started,
                "deadline": config_field_started + 0.95,
                "config_file_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                "config_semantic_sha256": semantic_config_hash,
            }
            config_field_area_before = area_count()
            config_field_admissions_before = len(admission_events)
            config_field_dirs_before = sorted(Path(config.capture_dir).glob("paused-region-*"))
            object.__setattr__(driver.profile, "model_crop", (81, 49, 640, 480))
            try:
                config_field_response = _socket_request(socket_path, config_field_request, timeout=1.1)
            finally:
                object.__setattr__(driver.profile, "model_crop", original_model_crop)
            assert config_field_response["ok"] is False
            assert "owning driver profile does not match" in config_field_response["error"]
            assert area_count() == config_field_area_before
            assert len(admission_events) == config_field_admissions_before
            assert sorted(Path(config.capture_dir).glob("paused-region-*")) == config_field_dirs_before
            assert session_config_semantic_sha256(daemon.config) == semantic_config_hash

            # An actual non-paused owner fails before the producer is entered.
            # The failed evidence remains durable and the already collected PNGs
            # are retained for diagnosis.
            daemon.controller.start()
            failed_dir = session_dir / "evidence-status-failure"
            with pytest.raises(RuntimeError, match="evidence=.*receipt.json"):
                harness.run_paused_diagnostic(config_path, failed_dir)
            failed = json.loads((failed_dir / "receipt.json").read_text(encoding="utf-8"))
            assert failed["run_state"] == "failed"
            assert failed["attempts"][0]["failure"]["phase"] == "status"
            assert len(failed["attempts"]) == 1
            failed_evaluated, failed_pairs, _ = _evaluate_persisted_live_receipt(
                failed, failed_dir / "receipt.json", live_binding
            )
            assert "status_failed" in failed_evaluated["reason_codes"]
            assert failed_pairs == []
            assert area_count() == 8 + 2 + 6 + 1 + 1 + 1 + 2 + 2

            # A generation change after sample 0 is observed before sample 1.
            # The runner must stop without another Shell request and keep the
            # successful first PNG plus a durable failure receipt.
            daemon.controller.pause("restore paused state for generation test")
            before_samples = sample_count[0]
            flip_generation_after_sample[0] = before_samples + 1
            partial_dir = session_dir / "evidence-generation-change"
            with pytest.raises(RuntimeError, match="evidence=.*receipt.json"):
                harness.run_paused_diagnostic(config_path, partial_dir)
            partial = json.loads((partial_dir / "receipt.json").read_text(encoding="utf-8"))
            assert partial["run_state"] == "failed"
            assert partial["attempts"][1]["failure"]["phase"] == "status"
            assert len(partial["attempts"]) == 2
            partial_evaluated, partial_pairs, _ = _evaluate_persisted_live_receipt(
                partial, partial_dir / "receipt.json", live_binding
            )
            assert "status_failed" in partial_evaluated["reason_codes"]
            assert len(partial_pairs) == 1
            assert len(list(partial_dir.glob("paused-*.png"))) == 1
            assert next(partial_dir.glob("paused-*.png")).is_file()
            assert area_count() == 8 + 2 + 6 + 1 + 1 + 1 + 2 + 2 + 1

            # A success receipt write failure leaves only a durable failure
            # receipt while retaining the actual producer PNG and receipt
            # attempt evidence.
            fail_success_persist[0] = True
            before_receipt_failure_samples = sample_count[0]
            before_receipt_failure_area = area_count()
            persist_started = time.monotonic()
            persist_request = {
                "command": "paused_region_sample",
                "generation": daemon.controller.status().generation,
                "parent_started": persist_started,
                "deadline": persist_started + 0.9,
                "config_file_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                "config_semantic_sha256": session_config_semantic_sha256(config),
            }
            persist_response = _socket_request(socket_path, persist_request, timeout=1.0)
            assert persist_response["ok"] is False
            persist_failure = persist_response.get("failure")
            assert isinstance(persist_failure, dict)
            assert persist_failure["phase"] == "owner_receipt_persist"
            assert persist_failure["published_png"] is not None
            assert Path(persist_failure["published_png"]).is_file()
            failed_owner_receipt = json.loads(
                Path(persist_failure["receipt_path"]).read_text(encoding="utf-8")
            )
            assert failed_owner_receipt["ok"] is False
            assert failed_owner_receipt["failure"]["phase"] == "owner_receipt_persist"
            attempted_success = [
                value
                for path, value in receipt_publications
                if path == Path(persist_failure["receipt_path"]) and value.get("ok") is True
            ]
            assert len(attempted_success) == 1 and "owner_returned" in attempted_success[0]
            assert sample_count[0] == before_receipt_failure_samples + 1
            assert area_count() == before_receipt_failure_area + 1
            assert not fail_success_persist[0]

            # Exercise the real supervised server and its actual SessionDaemon
            # owner. The small facade only gives serve a bounded test shutdown;
            # capture dispatch, controller, driver, Guardian, producer and
            # decoder remain the same constructed production objects.
            supervised_socket = socket_path.with_name("supervised-session.sock")
            supervised_started = threading.Event()
            supervised_shutdown = threading.Event()
            supervised_failure = RuntimeError("bounded supervised fixture shutdown")
            supervised_errors: list[BaseException] = []

            class SupervisedOwner:
                def __getattr__(self, name: str):
                    return getattr(daemon, name)

                def run_forever(self) -> None:
                    daemon.run_once()
                    supervised_started.set()
                    assert supervised_shutdown.wait(3.0)
                    raise supervised_failure

                def request_shutdown(self) -> None:
                    supervised_shutdown.set()

            supervised_owner = SupervisedOwner()

            def run_supervised_server() -> None:
                try:
                    serve(
                        supervised_socket,
                        daemon.controller,
                        supervised_owner,  # type: ignore[arg-type]
                        supervise_owner=True,
                    )
                except BaseException as exc:
                    supervised_errors.append(exc)

            supervised_server = threading.Thread(target=run_supervised_server, daemon=True)
            supervised_server.start()
            assert supervised_started.wait(2.0)
            supervised_deadline = time.monotonic() + 2.0
            while not supervised_socket.exists() and time.monotonic() < supervised_deadline:
                time.sleep(0.005)
            assert supervised_socket.exists()
            served_started = time.monotonic()
            served_response = _socket_request(
                supervised_socket,
                {
                    "command": "paused_region_sample",
                    "generation": daemon.controller.status().generation,
                    "parent_started": served_started,
                    "deadline": served_started + 0.95,
                    "config_file_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                    "config_semantic_sha256": session_config_semantic_sha256(config),
                },
                timeout=1.1,
            )
            assert served_response["ok"] is True
            assert served_response["sample"]["cleanup"]["empty"] is True
            served_area_count = area_count()
            serve_fence_entered = threading.Event()
            release_serve_fence = threading.Event()

            def hold_serve_fence() -> None:
                with daemon._motion_intent_lock:
                    serve_fence_entered.set()
                    assert release_serve_fence.wait(1.0)

            serve_fence_worker = threading.Thread(target=hold_serve_fence, daemon=True)
            serve_fence_worker.start()
            assert serve_fence_entered.wait(0.5)
            busy_started = time.monotonic()
            busy_response = _socket_request(
                supervised_socket,
                {
                    "command": "paused_region_sample",
                    "generation": daemon.controller.status().generation,
                    "parent_started": busy_started,
                    "deadline": busy_started + 0.75,
                    "config_file_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                    "config_semantic_sha256": session_config_semantic_sha256(config),
                },
                timeout=1.0,
            )
            assert busy_response["ok"] is False
            assert "another motion or capture intent" in busy_response["error"]
            assert area_count() == served_area_count
            release_serve_fence.set()
            serve_fence_worker.join(timeout=1.0)
            assert not serve_fence_worker.is_alive()
            supervised_shutdown.set()
            supervised_server.join(timeout=3.0)
            assert not supervised_server.is_alive()
            assert supervised_errors and supervised_errors[0].__cause__ is supervised_failure
            assert not supervised_socket.exists()

            # Linearization case 1: lifecycle stop wins while the owner is
            # resolving identity, before Guardian admission is entered.
            identity_entered = threading.Event()
            release_identity = threading.Event()
            original_resolve = backend.resolve_identity

            def blocked_identity(**kwargs):  # type: ignore[no-untyped-def]
                pre_race_events.append(("identity_resolve_enter", time.monotonic()))
                identity_entered.set()
                if not release_identity.wait(2.0):
                    raise TimeoutError("identity fixture gate was not released")
                pre_race_events.append(("identity_resolve_return", time.monotonic()))
                return original_resolve(**kwargs)

            backend.resolve_identity = blocked_identity  # type: ignore[method-assign]
            pre_race_events: list[tuple[str, float]] = []
            admission_count_before_pre_stop = len(admission_events)
            shell_count_before_pre_stop = len(json.loads(compositor["area_log"].read_text(encoding="utf-8")))
            pre_generation = daemon.controller.status().generation
            pre_started = time.monotonic()
            pre_request = {
                "command": "paused_region_sample",
                "generation": pre_generation,
                "parent_started": pre_started,
                "deadline": pre_started + 1.0,
                "config_file_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                "config_semantic_sha256": session_config_semantic_sha256(config),
            }
            pre_result: list[dict[str, object]] = []
            prior_owner_pngs = sorted(Path(config.capture_dir).glob("paused-region-*/capture.png"))
            pre_worker = threading.Thread(
                target=lambda: pre_result.append(_socket_request(socket_path, pre_request, timeout=1.0)),
                daemon=True,
            )
            pre_worker.start()
            assert identity_entered.wait(1.0)
            stop_response = _socket_request(
                socket_path,
                {"command": "stop", "generation": pre_generation},
                timeout=0.75,
            )
            assert stop_response["ok"] is True
            pre_race_events.append(("stop_accepted", time.monotonic()))
            pre_race_events.append(("identity_barrier_released", time.monotonic()))
            release_identity.set()
            pre_worker.join(timeout=1.0)
            assert not pre_worker.is_alive() and pre_result and pre_result[0]["ok"] is False
            pre_race_events.append(("request_refused", time.monotonic()))
            assert [event[0] for event in pre_race_events] == [
                "identity_resolve_enter",
                "stop_accepted",
                "identity_barrier_released",
                "identity_resolve_return",
                "identity_resolve_enter",
                "identity_resolve_return",
                "request_refused",
            ]
            assert len(admission_events) == admission_count_before_pre_stop
            assert (
                len(json.loads(compositor["area_log"].read_text(encoding="utf-8")))
                == shell_count_before_pre_stop
            )
            assert stop_revoke_events
            pre_failure = pre_result[0].get("failure")
            assert isinstance(pre_failure, dict) and pre_failure["published_png"] is None
            assert Path(pre_failure["receipt_path"]).is_file()
            assert sample_count[0] == 8 + 2 + 6 + 1 + 1 + 1 + 2 + 1 + 1 + 1 + 2 + 1
            assert area_count() == shell_count_before_pre_stop
            assert sorted(Path(config.capture_dir).glob("paused-region-*/capture.png")) == prior_owner_pngs
            assert driver.guardian.lease.held and not driver.guardian.armed
            assert driver.guardian.admission_gate_ready() is None
            assert not driver.guardian.observer_process_groups

            # STOPPED capture ownership is terminal. Resolve the persisted stop
            # through the actual start->pause transition on one fresh owner,
            # then reopen its legitimate PAUSED journal with a second owner.
            # The transition owner is itself capture-revoked by pause and is
            # never reused for a sample.
            daemon._cleanup_native_owned_captures()
            driver.close()
            daemon = SessionDaemon(config)
            driver = daemon.driver
            backend = driver.backend
            assert isinstance(backend, X11Backend)
            assert daemon.config.profile is not driver.profile
            assert driver.lease_path.is_relative_to(compositor["root"])
            recovered_stop = daemon.controller.status()
            assert recovered_stop.stop_requested
            assert recovered_stop.action_intent == "stop"
            started_owner = daemon.controller.start()
            assert started_owner.state.name == "NATIVE_CALIBRATION"
            assert not started_owner.stop_requested
            assert not started_owner.action_intent
            guardian_generation_before_pause = driver.guardian.generation
            transition_paused = daemon.controller.pause("persist PAUSED before fresh owner")
            assert transition_paused.state.name == "PAUSED"
            assert not transition_paused.stop_requested
            assert not transition_paused.closeout_requested
            assert not transition_paused.action_intent
            assert driver.guardian.generation > guardian_generation_before_pause
            assert transition_paused.lease_generation == driver.guardian.generation
            assert not driver.guardian.armed and not driver.guardian.held
            daemon._cleanup_native_owned_captures()
            driver.close()

            daemon = SessionDaemon(config)
            driver = daemon.driver
            backend = driver.backend
            assert isinstance(backend, X11Backend)
            assert daemon.config.profile is not driver.profile
            assert driver.lease_path.is_relative_to(compositor["root"])
            final_owner_status = daemon.controller.status()
            assert final_owner_status.state.name == "PAUSED"
            assert not final_owner_status.stop_requested
            assert not final_owner_status.closeout_requested
            assert not final_owner_status.action_intent
            assert not driver.guardian.armed and not driver.guardian.held
            assert driver.guardian.lease.held
            assert not backend._cancel_active.is_set()
            assert not driver.guardian.active_process_groups
            assert not driver.guardian.observer_process_groups
            original_observer_admission = driver.guardian.observer_dispatch_admission
            driver.guardian.observer_dispatch_admission = record_observer_admission  # type: ignore[method-assign]
            original_revoke = driver.guardian.revoke
            driver.guardian.revoke = record_revoke  # type: ignore[method-assign]
            admission_events.clear()
            stop_revoke_events.clear()
            ipc = SessionIPC(daemon.controller, daemon)

            # An external identity lookup can fail after the owner creates its
            # durable request directory but before the producer is entered.
            # Exercise that failure through the real owner socket and runner,
            # retaining the original phase/error and truthful not-started
            # producer evidence.
            original_final_resolve = backend.resolve_identity
            identity_failure_message = "external identity resolution failed before producer admission"

            def fail_identity_before_capture(**kwargs):  # type: ignore[no-untyped-def]
                del kwargs
                raise DriverError(identity_failure_message)

            backend.resolve_identity = fail_identity_before_capture  # type: ignore[method-assign]
            identity_failure_dir = session_dir / "evidence-identity-before-capture"
            identity_area_before = area_count()
            identity_admissions_before = len(admission_events)
            identity_requests_before = request_count[0]
            identity_samples_before = sample_count[0]
            identity_active_processes_before = set(backend._active_processes)
            identity_active_groups_before = backend.active_process_groups
            identity_guardian_groups_before = driver.guardian.observer_process_groups
            try:
                with pytest.raises(RuntimeError, match="paused diagnostic failed; evidence="):
                    harness.run_paused_diagnostic(config_path, identity_failure_dir)
            finally:
                backend.resolve_identity = original_final_resolve  # type: ignore[method-assign]

            identity_runner_receipt = json.loads(
                (identity_failure_dir / "receipt.json").read_text(encoding="utf-8")
            )
            assert identity_runner_receipt["run_state"] == "failed"
            assert identity_runner_receipt["attempts"][0]["failure"]["phase"] == "owner_capture"
            identity_owner = identity_runner_receipt["attempts"][0]["owner"]
            assert identity_owner["failure"] == {
                "phase": "owner_capture",
                "reason_code": "owner_capture_failed",
            }
            assert identity_owner["response_ready_monotonic"] is not None
            assert identity_owner["cleanup"]["attempt_retired"] is True
            identity_refusal = identity_failure_dir / "owner-refusal-00.json"
            assert identity_refusal.is_file()
            assert identity_refusal.stat().st_mode & 0o777 == 0o600
            identity_refusal_payload = json.loads(identity_refusal.read_text(encoding="utf-8"))
            persisted_identity_failure = identity_refusal_payload["failure"]
            assert persisted_identity_failure["phase"] == "identity_before_capture"
            assert persisted_identity_failure["error"] == f"DriverError: {identity_failure_message}"
            assert persisted_identity_failure["producer_attempt"] == {
                "stage": "not_started",
                "request_started": None,
                "lock_acquired": None,
                "ack_sent": None,
                "capture_started": None,
                "capture_returned": None,
                "attempt_retired": True,
            }
            assert persisted_identity_failure["lease_held"] is True
            assert persisted_identity_failure["armed"] is False
            assert persisted_identity_failure["cleanup"]["empty"] is True
            identity_evaluated, identity_pairs, identity_report = _evaluate_persisted_live_receipt(
                identity_runner_receipt, identity_failure_dir / "receipt.json", live_binding
            )
            assert identity_evaluated["receipt_state"] == "failed"
            assert identity_evaluated["attempts_begun"] == 1
            assert identity_evaluated["reason_codes"] == ["binding_mismatch", "owner_capture_failed"]
            assert identity_report["decision"] == "insufficient_evidence"
            assert identity_report["reason_codes"] == [
                "binding_mismatch",
                "insufficient_complete_runs",
                "insufficient_completed_pairs",
                "owner_capture_failed",
            ]
            assert identity_pairs == []
            assert request_count[0] == identity_requests_before + 2  # status plus owner IPC
            assert sample_count[0] == identity_samples_before + 1
            assert area_count() == identity_area_before
            assert len(admission_events) == identity_admissions_before
            assert backend._active_processes == identity_active_processes_before
            assert backend.active_process_groups == identity_active_groups_before
            assert driver.guardian.observer_process_groups == identity_guardian_groups_before
            assert driver.guardian.lease.held and not driver.guardian.armed

            compositor["area_started_path"].unlink(missing_ok=True)
            compositor["area_release_path"].unlink(missing_ok=True)
            compositor["area_block_path"].touch(mode=0o600)
            capture_generation = daemon.controller.status().generation
            capture_started = time.monotonic()
            capture_request = {
                "command": "paused_region_sample",
                "generation": capture_generation,
                "parent_started": capture_started,
                "deadline": capture_started + 1.0,
                "config_file_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                "config_semantic_sha256": session_config_semantic_sha256(config),
            }
            capture_result: list[dict[str, object]] = []
            capture_returned_at: list[float] = []

            def perform_blocked_capture() -> None:
                try:
                    capture_result.append(_socket_request(socket_path, capture_request, timeout=1.1))
                finally:
                    capture_returned_at.append(time.monotonic())

            capture_worker = threading.Thread(
                target=perform_blocked_capture,
                daemon=True,
            )
            capture_worker.start()
            blocked_deadline = time.monotonic() + 0.75
            while not compositor["area_started_path"].is_file() and time.monotonic() < blocked_deadline:
                time.sleep(0.005)
            assert compositor["area_started_path"].is_file(), (
                f"fresh admitted owner did not reach blocked Shell; response={capture_result!r}; "
                f"active_processes={backend._active_processes!r}; active_groups={backend.active_process_groups!r}; "
                f"guardian_groups={driver.guardian.observer_process_groups!r}; "
                f"watchdog_failed={driver.guardian._watchdog_failed!r}; "
                f"area_count={area_count()}; "
                f"gjs_stderr={(compositor['root'] / 'gjs.stderr').read_text(encoding='utf-8') if (compositor['root'] / 'gjs.stderr').exists() else None!r}"
            )
            area_started_monotonic = (
                int(compositor["area_started_path"].read_text(encoding="ascii")) / 1_000_000
            )
            admitted_gate_events = admission_events[-2:]
            assert [event[0] for event in admitted_gate_events] == ["admission_enter", "gate_released"]
            assert admitted_gate_events[-1][1] <= area_started_monotonic
            assert driver.guardian.observer_process_groups
            admitted_race_events: list[tuple[str, float]] = [
                ("gate_released", admitted_gate_events[-1][1]),
                ("shell_capture_started", area_started_monotonic),
            ]
            stop_started = time.monotonic()
            admitted_stop = _socket_request(
                socket_path,
                {"command": "stop", "generation": capture_generation},
                timeout=0.75,
            )
            stop_elapsed = time.monotonic() - stop_started
            assert admitted_stop["ok"] is True and stop_elapsed < 0.75
            admitted_race_events.append(("guardian_stop_revoke", stop_revoke_events[-1]))
            capture_worker.join(timeout=1.0)
            assert not capture_worker.is_alive() and capture_result
            assert capture_returned_at
            admitted_race_events.append(("capture_failed_and_reaped", capture_returned_at[0]))
            assert [event[0] for event in admitted_race_events] == [
                "gate_released",
                "shell_capture_started",
                "guardian_stop_revoke",
                "capture_failed_and_reaped",
            ]
            assert [event[1] for event in admitted_race_events] == sorted(
                event[1] for event in admitted_race_events
            )
            assert capture_returned_at and stop_revoke_events[-1] >= area_started_monotonic
            assert capture_returned_at[0] >= stop_revoke_events[-1]
            assert capture_result[0]["ok"] is False
            owner_failure = capture_result[0].get("failure")
            assert isinstance(owner_failure, dict)
            assert owner_failure["published_png"] is None
            assert Path(owner_failure["receipt_path"]).is_file()
            persisted_owner_failure = json.loads(
                Path(owner_failure["receipt_path"]).read_text(encoding="utf-8")
            )
            assert persisted_owner_failure["ok"] is False
            assert persisted_owner_failure["failure"]["phase"] == "region_capture"
            assert owner_failure["cleanup"]["empty"] is True
            assert owner_failure["lease_held"] is True
            assert owner_failure["armed"] is False
            assert not driver.guardian.observer_process_groups
            assert not backend._active_processes and not backend.active_process_groups
            assert driver.guardian.admission_gate_ready() is None
            status_after_stop = _socket_request(socket_path, {"command": "status"}, timeout=0.5)
            assert status_after_stop["ok"] is True
            assert status_after_stop["status"]["state"] == "STOPPED"
            assert sorted(Path(config.capture_dir).glob("paused-region-*/capture.png")) == prior_owner_pngs

            # The client must bind every effective SessionConfig field, not
            # only the crop and producer that happen to be used by capture.
            # Change capture_dir while keeping the same socket, crop and
            # producer; the existing daemon owner must reject before capture.
            daemon.controller.start()
            daemon.controller.pause("prepare semantic config mismatch check")
            original_config_text = config_path.read_text(encoding="utf-8")
            original_capture_setting = f"capture_dir = {json.dumps(str(config.capture_dir))}"
            altered_capture_setting = f"capture_dir = {json.dumps(str(session_dir / 'alternate-captures'))}"
            assert original_config_text.count(original_capture_setting) == 1
            config_path.write_text(
                original_config_text.replace(original_capture_setting, altered_capture_setting),
                encoding="utf-8",
            )
            try:
                altered_config = load_config(config_path)
                altered_semantic = session_config_semantic_sha256(altered_config)
                assert altered_config.profile.canvas_crop == config.profile.canvas_crop
                assert (
                    altered_config.profile.telemetry_region_executable
                    == config.profile.telemetry_region_executable
                )
                assert (
                    altered_config.profile.telemetry_region_executable_sha256
                    == config.profile.telemetry_region_executable_sha256
                )
                assert altered_semantic != session_config_semantic_sha256(config)
                before_semantic_area = area_count()
                before_semantic_admissions = len(admission_events)
                before_semantic_dirs = sorted(Path(config.capture_dir).glob("paused-region-*"))
                semantic_mismatch_dir = session_dir / "evidence-semantic-config-mismatch"
                with pytest.raises(RuntimeError, match="paused diagnostic failed; evidence="):
                    harness.run_paused_diagnostic(config_path, semantic_mismatch_dir)
                mismatch_receipt = json.loads(
                    (semantic_mismatch_dir / "receipt.json").read_text(encoding="utf-8")
                )
                assert mismatch_receipt["run_state"] == "failed"
                assert mismatch_receipt["attempts"][0]["failure"]["phase"] == "config_binding"
                assert mismatch_receipt["attempts"] == [mismatch_receipt["attempts"][0]]
                assert len(mismatch_receipt["config_binding"]["raw_file_sha256"]) == 64
                assert len(mismatch_receipt["config_binding"]["semantic_sha256"]) == 64
                mismatch_owner = mismatch_receipt["attempts"][0]["owner"]
                assert isinstance(mismatch_owner, dict)
                assert mismatch_owner["config_binding"]["semantic_sha256"] == (
                    session_config_semantic_sha256(config)
                )
                assert mismatch_owner["config_binding"]["semantic_sha256"] != altered_semantic
                mismatch_binding = copy.deepcopy(live_binding)
                mismatch_binding["config_binding"] = {
                    "raw_file_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                    "semantic_sha256": altered_semantic,
                }
                mismatch_evaluated, _mismatch_pairs, _ = _evaluate_persisted_live_receipt(
                    mismatch_receipt,
                    semantic_mismatch_dir / "receipt.json",
                    mismatch_binding,
                )
                assert mismatch_evaluated["eligible"] is False
                assert "config_binding_mismatch" in mismatch_evaluated["reason_codes"]
                assert area_count() == before_semantic_area
                assert len(admission_events) == before_semantic_admissions
                assert sorted(Path(config.capture_dir).glob("paused-region-*")) == before_semantic_dirs
            finally:
                config_path.write_text(original_config_text, encoding="utf-8")

            # The preceding stop/revocation case deliberately leaves its
            # owner capture epoch canceled. Reopen the same real paused
            # configuration before exercising the final-status boundary.
            daemon._cleanup_native_owned_captures()
            driver.close()
            daemon = SessionDaemon(config)
            driver = daemon.driver
            backend = driver.backend
            assert isinstance(backend, X11Backend)
            compositor["area_block_path"].unlink(missing_ok=True)
            compositor["area_release_path"].touch(mode=0o600)
            daemon.controller.pause("prepare final status delay check")
            ipc = SessionIPC(daemon.controller, daemon)

            # Advance only the runner's injected clock after the real final
            # status response. The status therefore reached the boundary, but
            # completion crossed its deterministic one-second deadline and
            # must remain an uncompleted attempt in the persisted receipt.
            original_harness_time = harness.time
            original_status_from_ipc = harness._status_from_ipc
            status_calls: list[int] = [0]
            clock_offset = [0.0]

            class _DelayedRunnerClock:
                def monotonic(self) -> float:
                    return original_harness_time.monotonic() + clock_offset[0]

                def __getattr__(self, name: str):  # type: ignore[no-untyped-def]
                    return getattr(original_harness_time, name)

            def delay_final_status(config_value, *, timeout):  # type: ignore[no-untyped-def]
                status_calls[0] += 1
                result = original_status_from_ipc(config_value, timeout=timeout)
                if status_calls[0] == 9:
                    clock_offset[0] = 2.0
                return result

            harness.time = _DelayedRunnerClock()
            harness._status_from_ipc = delay_final_status
            delayed_status_dir = session_dir / "evidence-final-status-delay"
            try:
                with pytest.raises(RuntimeError, match="paused diagnostic failed; evidence="):
                    harness.run_paused_diagnostic(config_path, delayed_status_dir)
            finally:
                harness.time = original_harness_time
                harness._status_from_ipc = original_status_from_ipc
            delayed_receipt = json.loads((delayed_status_dir / "receipt.json").read_text(encoding="utf-8"))
            assert status_calls[0] == 9  # eight sample statuses plus final status
            assert delayed_receipt["run_state"] == "failed"
            delayed_attempts = delayed_receipt["attempts"]
            assert isinstance(delayed_attempts, list) and len(delayed_attempts) == 8
            assert delayed_attempts[-1]["state"] == "failed"
            assert delayed_attempts[-1]["failure"] == {
                "phase": "deadline",
                "reason_code": "sample_deadline_missed",
            }
            assert (
                delayed_attempts[-1]["sample_completed_monotonic"]
                >= delayed_attempts[-1]["deadline_monotonic"]
            )
            delayed_evaluated, delayed_pairs, _ = _evaluate_persisted_live_receipt(
                delayed_receipt, delayed_status_dir / "receipt.json", live_binding
            )
            assert delayed_evaluated["receipt_state"] == "failed"
            assert delayed_evaluated["timing_qualified"] is False
            assert "sample_deadline_missed" in delayed_evaluated["reason_codes"]
            assert len(delayed_pairs) == 8

            # A final status call that throws after strict decode leaves the
            # completion boundary absent.  The public evaluator retains the
            # eight decoded pairs and the finite status failure without
            # inventing a completion timestamp.
            original_status_from_ipc = harness._status_from_ipc
            final_status_failure_calls: list[int] = [0]

            def fail_final_status(config_value, *, timeout):  # type: ignore[no-untyped-def]
                final_status_failure_calls[0] += 1
                if final_status_failure_calls[0] == 9:
                    raise RuntimeError("fixture final status failure")
                return original_status_from_ipc(config_value, timeout=timeout)

            harness._status_from_ipc = fail_final_status
            final_status_failure_dir = session_dir / "evidence-final-status-failure"
            try:
                with pytest.raises(RuntimeError, match="paused diagnostic failed; evidence="):
                    harness.run_paused_diagnostic(config_path, final_status_failure_dir)
            finally:
                harness._status_from_ipc = original_status_from_ipc
            final_status_failure_receipt = json.loads(
                (final_status_failure_dir / "receipt.json").read_text(encoding="utf-8")
            )
            assert final_status_failure_calls[0] == 9
            assert final_status_failure_receipt["attempts"][-1]["failure"] == {
                "phase": "status",
                "reason_code": "status_failed",
            }
            assert final_status_failure_receipt["attempts"][-1]["sample_completed_monotonic"] is None
            final_status_failure_evaluated, final_status_failure_pairs, _ = _evaluate_persisted_live_receipt(
                final_status_failure_receipt,
                final_status_failure_dir / "receipt.json",
                live_binding,
            )
            assert final_status_failure_evaluated["receipt_state"] == "failed"
            assert "status_failed" in final_status_failure_evaluated["reason_codes"]
            assert len(final_status_failure_pairs) == 8

            # A valid owner response that cannot be published by the client
            # must retain the finite PNG-publication failure classification.
            original_atomic_private_png = harness._atomic_private_png
            publication_calls = [0]

            def fail_private_png(path: Path, data: bytes) -> None:
                publication_calls[0] += 1
                raise OSError("injected private PNG publication failure")

            harness._atomic_private_png = fail_private_png
            publication_failure_dir = session_dir / "evidence-client-png-publication-failure"
            try:
                with pytest.raises(RuntimeError, match="paused diagnostic failed; evidence="):
                    harness.run_paused_diagnostic(config_path, publication_failure_dir)
            finally:
                harness._atomic_private_png = original_atomic_private_png
            publication_failure_receipt = json.loads(
                (publication_failure_dir / "receipt.json").read_text(encoding="utf-8")
            )
            assert publication_calls[0] == 1
            assert publication_failure_receipt["attempts"][0]["failure"] == {
                "phase": "png_publication",
                "reason_code": "png_publication_failed",
            }

            # Interrupt the fixed target wait before the next attempt begins.
            # The common source finalizer must retain a shorter incomplete run
            # with no fabricated failed attempt for that unreached target.
            original_harness_time = harness.time
            original_runtime_source_hashes = harness._runtime_source_hashes
            source_hash_calls = [0]
            force_wait = [False]
            target_origin: list[float | None] = [None]
            delayed_wait_returned = [False]

            def record_source_hashes() -> dict[str, str]:
                source_hash_calls[0] += 1
                result = original_runtime_source_hashes()
                if source_hash_calls[0] == 1:
                    force_wait[0] = True
                return result

            class _InterruptingWaitClock:
                def monotonic(self) -> float:
                    value = original_harness_time.monotonic()
                    if force_wait[0] and target_origin[0] is None:
                        target_origin[0] = value
                        return value
                    if force_wait[0] and not delayed_wait_returned[0]:
                        delayed_wait_returned[0] = True
                        assert target_origin[0] is not None
                        return target_origin[0] - 1.0
                    return value

                def sleep(self, seconds: float) -> None:
                    del seconds
                    raise KeyboardInterrupt()

                def __getattr__(self, name: str):  # type: ignore[no-untyped-def]
                    return getattr(original_harness_time, name)

            harness.time = _InterruptingWaitClock()
            harness._runtime_source_hashes = record_source_hashes
            interrupted_wait_dir = session_dir / "evidence-target-wait-interruption"
            try:
                with pytest.raises(RuntimeError, match="paused diagnostic failed; evidence="):
                    harness.run_paused_diagnostic(config_path, interrupted_wait_dir)
            finally:
                harness.time = original_harness_time
                harness._runtime_source_hashes = original_runtime_source_hashes
            interrupted_receipt = json.loads(
                (interrupted_wait_dir / "receipt.json").read_text(encoding="utf-8")
            )
            assert interrupted_receipt["run_state"] == "incomplete"
            assert interrupted_receipt["attempts"] == []
            interrupted_evaluated, interrupted_pairs, _ = _evaluate_persisted_live_receipt(
                interrupted_receipt, interrupted_wait_dir / "receipt.json", live_binding
            )
            assert interrupted_evaluated["receipt_state"] == "incomplete"
            assert interrupted_evaluated["attempts_begun"] == 0
            assert interrupted_pairs == []

            # Exercise every real daemon model entrypoint through the shared
            # thread-safe wrapper, including exception preservation.
            model_started = threading.Event()

            class _CountingModel:
                def observe(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
                    model_started.set()
                    return {"kind": "fixture-observe"}

                def observe_route(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
                    return {"kind": "fixture-route"}

                def observe_viewport(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
                    return {"kind": "fixture-viewport"}

                def decide(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
                    return {"kind": "fixture-decision"}

            daemon.model = _CountingModel()  # type: ignore[assignment]
            entrypoint_before = daemon._model_call_snapshot()
            assert daemon._call_model_adapter("observe_route", b"frame") == {"kind": "fixture-route"}
            assert daemon._call_model_adapter("observe_viewport", b"frame") == {"kind": "fixture-viewport"}
            assert daemon._call_model_adapter("decide", b"frame") == {"kind": "fixture-decision"}

            def failing_decide(*_args, **_kwargs):  # type: ignore[no-untyped-def]
                raise RuntimeError("fixture model failure")

            daemon.model.decide = failing_decide  # type: ignore[method-assign]
            with pytest.raises(RuntimeError, match="fixture model failure"):
                daemon._call_model_adapter("decide", b"frame")
            entrypoint_counts = daemon._model_call_snapshot()
            assert entrypoint_counts == {
                "started": entrypoint_before["started"] + 4,
                "succeeded": entrypoint_before["succeeded"] + 3,
                "failed": entrypoint_before["failed"] + 1,
            }

            # Hold the actual owner's first source-gate read while a separate
            # thread calls the real daemon observe entrypoint. The persisted
            # attempt counters must capture this overlap; no receipt fields
            # are copied or rewritten by the test.
            source_gate_entered = threading.Event()
            source_gate_release = threading.Event()
            source_gate_first = [True]
            original_source_binding = daemon._runtime_source_binding_for_diagnostic

            def block_first_source_binding() -> dict[str, str]:
                if source_gate_first[0]:
                    source_gate_first[0] = False
                    source_gate_entered.set()
                    assert source_gate_release.wait(1.0)
                return original_source_binding()

            daemon._runtime_source_binding_for_diagnostic = block_first_source_binding  # type: ignore[method-assign]
            model_run_dir = session_dir / "evidence-model-call-live"
            model_run_result: list[dict[str, object]] = []
            model_run_errors: list[BaseException] = []
            model_call_result: list[object] = []
            model_call_errors: list[BaseException] = []

            def run_model_diagnostic() -> None:
                try:
                    model_run_result.append(harness.run_paused_diagnostic(config_path, model_run_dir))
                except BaseException as exc:
                    model_run_errors.append(exc)

            def call_observe_during_source_gate() -> None:
                try:
                    model_call_result.append(daemon._observe_model(b"frame", timeout=1.0))
                except BaseException as exc:
                    model_call_errors.append(exc)

            model_run_thread = threading.Thread(target=run_model_diagnostic, daemon=True)
            model_run_thread.start()
            assert source_gate_entered.wait(1.0)
            concurrent_model_thread = threading.Thread(target=call_observe_during_source_gate, daemon=True)
            concurrent_model_thread.start()
            concurrent_model_thread.join(timeout=1.0)
            assert not concurrent_model_thread.is_alive()
            assert not model_call_errors
            assert model_call_result == [{"kind": "fixture-observe"}]
            assert model_started.is_set()
            assert not source_gate_release.is_set()
            source_gate_release.set()
            model_run_thread.join(timeout=12.0)
            assert not model_run_thread.is_alive()
            daemon._runtime_source_binding_for_diagnostic = original_source_binding  # type: ignore[method-assign]
            assert not model_run_errors
            assert model_run_result and model_run_result[0]["run_state"] == "passed"

            model_receipt = json.loads((model_run_dir / "receipt.json").read_text(encoding="utf-8"))
            model_attempt = model_receipt["attempts"][0]
            assert model_attempt["owner"]["model_calls_before"] == entrypoint_counts
            assert model_attempt["owner"]["model_calls_after"] == {
                "started": entrypoint_counts["started"] + 1,
                "succeeded": entrypoint_counts["succeeded"] + 1,
                "failed": entrypoint_counts["failed"],
            }
            assert model_attempt["owner"]["model_call_delta"] == {"started": 1, "succeeded": 1, "failed": 0}
            model_evaluated, model_pairs, _ = _evaluate_persisted_live_receipt(
                model_receipt, model_run_dir / "receipt.json", live_binding
            )
            assert model_evaluated["receipt_state"] == "passed"
            assert model_evaluated["eligible"] is False
            assert "model_call_delta_nonzero" in model_evaluated["reason_codes"]
            assert len(model_pairs) == 7

            # The same unchanged evaluator independently rejects an observer
            # after-map replacement, retaining the source drift reason.
            source_drift_dir = session_dir / "evidence-owner-source-drift"
            source_drift_dir.mkdir(mode=0o700)
            source_drift_receipt = json.loads((output_dir / "receipt.json").read_text(encoding="utf-8"))
            source_drift_receipt["observer_source_hashes_after"] = dict(
                source_drift_receipt["observer_source_hashes_before"]
            )
            source_drift_receipt["observer_source_hashes_after"]["daemon.py"] = "f" * 64
            (source_drift_dir / "receipt.json").write_text(
                json.dumps(source_drift_receipt, sort_keys=True, separators=(",", ":")), encoding="utf-8"
            )
            source_drift_evaluated, source_drift_pairs, _ = _evaluate_persisted_live_receipt(
                source_drift_receipt, source_drift_dir / "receipt.json", live_binding
            )
            assert source_drift_evaluated.get("receipt_refused") is not True
            assert source_drift_evaluated["eligible"] is False
            assert source_drift_evaluated["reason_codes"] == ["source_binding_drift"]
            assert len(source_drift_pairs) == 8
        finally:
            late_response_release.set()
            late_refusal_release.set()
            stop_status.set()
            status_listener.close()
            status_thread.join(timeout=2.0)
            for worker in ipc_workers:
                worker.join(timeout=2.0)
            assert not status_thread.is_alive()
            assert not [worker.name for worker in ipc_workers if worker.is_alive()]
            assert not ipc_handler_errors, ipc_handler_errors
            assert all(isinstance(error, str) for error in ipc_late_transport_errors)
            driver.close()


def test_paused_region_performance_receipt_preserves_all_boundaries_and_model_counts() -> None:
    """The schema projection retains observed owner boundaries and adapter counts."""

    root = Path(__file__).resolve().parents[1]
    harness_spec = importlib.util.spec_from_file_location(
        "region_performance_projection", root / "tools/gnome-telemetry-region/offline_harness.py"
    )
    assert harness_spec is not None and harness_spec.loader is not None
    harness = importlib.util.module_from_spec(harness_spec)
    harness_spec.loader.exec_module(harness)

    before = {"started": 0, "succeeded": 0, "failed": 0}
    after = {"started": 1, "succeeded": 1, "failed": 0}

    attempt = {
        "stage": "published",
        "request_started": 11.0,
        "lock_acquired": 12.0,
        "ack_sent": 13.0,
        "capture_started": 14.0,
        "capture_returned": 15.0,
        "attempt_retired": True,
    }
    source_binding = {name: "a" * 64 for name in harness._RUNTIME_SOURCE_FILES}
    sample = {
        "owner_entered": 10.0,
        "owner_returned": 17.0,
        "response_ready": 16.0,
        "generation": 4,
        "receipt": attempt,
        "cleanup": {
            "backend_processes": 0,
            "backend_groups": [],
            "guardian_observer_groups": [],
            "guardian_active_groups": [],
            "attempt_directories": [],
            "lease_held": True,
            "watchdog_healthy": True,
        },
        "source_binding": source_binding,
        "config": {
            "request_config_file_sha256": "b" * 64,
            "request_config_semantic_sha256": "c" * 64,
            "owner_config_semantic_sha256": "d" * 64,
        },
        "producer": {"sha256": "d" * 64},
        "source": {"branch": "ScreenshotArea"},
        "model_calls_before": before,
        "model_calls_after": after,
        "model_call_delta": {"started": 1, "succeeded": 1, "failed": 0},
    }
    owner = harness._live_owner_evidence(sample, None, 4, None)
    assert owner["request_started_monotonic"] == 11.0
    assert owner["capture_started_monotonic"] == 14.0
    assert owner["capture_returned_monotonic"] == 15.0
    assert owner["response_ready_monotonic"] == 16.0
    assert owner["model_calls_before"] == before
    assert owner["model_calls_after"] == after
    assert owner["model_call_delta"] == {"started": 1, "succeeded": 1, "failed": 0}
    assert owner["config_binding"]["semantic_sha256"] == "d" * 64
    assert owner["cleanup"]["capture_process_reaped"] is True
    assert owner["cleanup"]["attempt_retired"] is True
    assert owner["failure"] is None


def test_paused_region_performance_failure_preserves_reached_boundaries() -> None:
    """A thrown decode keeps reached owner/protocol evidence and nulls later stages."""

    root = Path(__file__).resolve().parents[1]
    harness_spec = importlib.util.spec_from_file_location(
        "region_performance_failure_projection", root / "tools/gnome-telemetry-region/offline_harness.py"
    )
    assert harness_spec is not None and harness_spec.loader is not None
    harness = importlib.util.module_from_spec(harness_spec)
    harness_spec.loader.exec_module(harness)

    attempt = {
        "stage": "capture_started",
        "request_started": 21.0,
        "lock_acquired": 22.0,
        "ack_sent": 23.0,
        "capture_started": 24.0,
        "capture_returned": None,
        "attempt_retired": None,
    }
    harness._validate_producer_attempt(attempt, 0)
    failure = {
        "owner_entered": 20.0,
        "owner_returned": 26.0,
        "response_ready": 25.0,
        "generation": 9,
        "producer_attempt": attempt,
        "cleanup": {
            "backend_processes": 1,
            "backend_groups": [1234],
            "guardian_observer_groups": [],
            "guardian_active_groups": [5678],
            "attempt_directories": ["/private/attempt"],
            "lease_held": True,
            "watchdog_healthy": True,
        },
        "config_file_sha256": "e" * 64,
        "config_semantic_sha256": "f" * 64,
        "source_binding": {name: "a" * 64 for name in harness._RUNTIME_SOURCE_FILES},
        "model_calls_before": {"started": 3, "succeeded": 3, "failed": 0},
        "model_calls_after": {"started": 3, "succeeded": 3, "failed": 0},
        "model_call_delta": {"started": 0, "succeeded": 0, "failed": 0},
    }
    owner = harness._live_owner_evidence(None, failure, 9, harness._live_failure("strict_decode"))
    assert owner["request_started_monotonic"] == 21.0
    assert owner["ack_sent_monotonic"] == 23.0
    assert owner["capture_started_monotonic"] == 24.0
    assert owner["capture_returned_monotonic"] is None
    assert owner["failure"] == {
        "phase": "strict_decode",
        "reason_code": "strict_decode_failed",
    }
    assert owner["cleanup"]["capture_process_reaped"] is False
    assert owner["cleanup"]["attempt_retired"] is None


def test_paused_region_performance_config_refusal_preserves_actual_owner_hash() -> None:
    """A config refusal never projects the request hash as the owner hash."""

    root = Path(__file__).resolve().parents[1]
    harness_spec = importlib.util.spec_from_file_location(
        "region_config_refusal_projection", root / "tools/gnome-telemetry-region/offline_harness.py"
    )
    assert harness_spec is not None and harness_spec.loader is not None
    harness = importlib.util.module_from_spec(harness_spec)
    harness_spec.loader.exec_module(harness)

    request_hash = "a" * 64
    owner_hash = "b" * 64
    failure = {
        "owner_entered": 10.0,
        "owner_returned": 11.0,
        "response_ready": 11.0,
        "generation": 4,
        "config_file_sha256": "c" * 64,
        "config_semantic_sha256": request_hash,
        "owner_config_semantic_sha256": owner_hash,
        "producer_attempt": {"stage": "not_started"},
        "cleanup": {},
    }
    owner = harness._live_owner_evidence(None, failure, 4, harness._live_failure("config_binding"))
    assert owner["config_binding"] == {
        "raw_file_sha256": "c" * 64,
        "semantic_sha256": owner_hash,
    }

    missing_owner_hash = dict(failure)
    missing_owner_hash.pop("owner_config_semantic_sha256")
    missing_owner = harness._live_owner_evidence(
        None, missing_owner_hash, 4, harness._live_failure("config_binding")
    )
    assert missing_owner["config_binding"]["semantic_sha256"] is None


def test_paused_region_owner_failure_contract_rejects_cross_request_and_extra_fields() -> None:
    """Malformed owner refusals never become trusted projected evidence."""

    root = Path(__file__).resolve().parents[1]
    harness_spec = importlib.util.spec_from_file_location(
        "region_owner_failure_contract", root / "tools/gnome-telemetry-region/offline_harness.py"
    )
    assert harness_spec is not None and harness_spec.loader is not None
    harness = importlib.util.module_from_spec(harness_spec)
    harness_spec.loader.exec_module(harness)

    config_file_sha256 = "a" * 64
    config_semantic_sha256 = "b" * 64
    failure: dict[str, object] = {
        "phase": "config_binding",
        "error": "semantic config mismatch",
        "owner_entered": 10.0,
        "owner_returned": 11.0,
        "artifact_directory": None,
        "receipt_path": None,
        "published_png": None,
        "producer_attempt": {
            "stage": "not_started",
            "request_started": None,
            "lock_acquired": None,
            "ack_sent": None,
            "capture_started": None,
            "capture_returned": None,
            "attempt_retired": True,
        },
        "cleanup": {
            "backend_processes": 0,
            "backend_groups": [],
            "guardian_observer_groups": [],
            "guardian_active_groups": [],
            "attempt_directories": [],
            "lease_held": True,
            "watchdog_healthy": True,
            "armed": False,
            "empty": True,
        },
        "generation": 4,
        "config_file_sha256": config_file_sha256,
        "config_semantic_sha256": config_semantic_sha256,
        "owner_config_semantic_sha256": "c" * 64,
        "lease_held": True,
        "armed": False,
        "source_binding": {name: "d" * 64 for name in harness._RUNTIME_SOURCE_FILES},
        "model_calls_before": {"started": 0, "succeeded": 0, "failed": 0},
        "model_calls_after": {"started": 0, "succeeded": 0, "failed": 0},
        "model_call_delta": {"started": 0, "succeeded": 0, "failed": 0},
        "response_ready": 11.0,
    }
    harness._validate_owner_failure_payload(
        failure,
        index=0,
        generation=4,
        config_file_sha256=config_file_sha256,
        config_semantic_sha256=config_semantic_sha256,
    )
    with pytest.raises(RuntimeError, match="unexpected fields"):
        harness._validate_owner_failure_payload(
            {**failure, "unexpected": True},
            index=0,
            generation=4,
            config_file_sha256=config_file_sha256,
            config_semantic_sha256=config_semantic_sha256,
        )
    with pytest.raises(RuntimeError, match="request semantic binding"):
        harness._validate_owner_failure_payload(
            {**failure, "config_semantic_sha256": "e" * 64},
            index=0,
            generation=4,
            config_file_sha256=config_file_sha256,
            config_semantic_sha256=config_semantic_sha256,
        )
    with pytest.raises(RuntimeError, match="owner config binding"):
        harness._validate_owner_failure_payload(
            {**failure, "owner_config_semantic_sha256": None},
            index=0,
            generation=4,
            config_file_sha256=config_file_sha256,
            config_semantic_sha256=config_semantic_sha256,
        )


def test_paused_region_performance_projection_counts_guardian_groups_and_requires_observed_cleanup() -> None:
    """Guardian-owned groups and absent booleans cannot project clean teardown."""

    root = Path(__file__).resolve().parents[1]
    harness_spec = importlib.util.spec_from_file_location(
        "region_performance_guardian_projection", root / "tools/gnome-telemetry-region/offline_harness.py"
    )
    assert harness_spec is not None and harness_spec.loader is not None
    harness = importlib.util.module_from_spec(harness_spec)
    harness_spec.loader.exec_module(harness)
    source = {name: "a" * 64 for name in harness._RUNTIME_SOURCE_FILES}
    receipt = {
        "owner_entered": 10.0,
        "owner_returned": 16.0,
        "response_ready": 15.0,
        "generation": 4,
        "receipt": {
            "request_started": 11.0,
            "lock_acquired": 12.0,
            "ack_sent": 13.0,
            "capture_started": 14.0,
            "capture_returned": 15.0,
            "attempt_retired": True,
            "nonce": "private-nonce",
        },
        "cleanup": {
            "backend_processes": 0,
            "backend_groups": [],
            "guardian_observer_groups": [],
            "guardian_active_groups": [4321],
            "attempt_directories": [],
            "lease_held": True,
            "watchdog_healthy": True,
        },
        "source_binding": source,
        "producer": {"sha256": "b" * 64},
        "config": {"request_config_file_sha256": "c" * 64, "request_config_semantic_sha256": "d" * 64},
        "source": {"branch": "ScreenshotArea"},
        "model_calls_before": {"started": 0, "succeeded": 0, "failed": 0},
        "model_calls_after": {"started": 0, "succeeded": 0, "failed": 0},
        "model_call_delta": {"started": 0, "succeeded": 0, "failed": 0},
    }
    owner = harness._live_owner_evidence(receipt, None, 4, None)
    assert owner["cleanup"]["active_process_group_count"] == 1
    assert owner["cleanup"]["capture_process_reaped"] is False

    missing = dict(receipt)
    missing["cleanup"] = {
        "backend_processes": 0,
        "backend_groups": [],
        "guardian_observer_groups": [],
        "guardian_active_groups": [],
        "attempt_directories": [],
    }
    missing_owner = harness._live_owner_evidence(missing, None, 4, None)
    assert missing_owner["cleanup"]["lease_held"] is None
    assert missing_owner["cleanup"]["watchdog_healthy"] is None


def test_runtime_source_readers_reject_path_replacement_after_descriptor_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both independent readers bind the pathname to the bytes they hashed."""

    root = Path(__file__).resolve().parents[1]
    harness_spec = importlib.util.spec_from_file_location(
        "region_source_reader_race", root / "tools/gnome-telemetry-region/offline_harness.py"
    )
    assert harness_spec is not None and harness_spec.loader is not None
    harness = importlib.util.module_from_spec(harness_spec)
    harness_spec.loader.exec_module(harness)
    source = tmp_path / "source.py"
    replacement = tmp_path / "replacement.py"
    base_open = os.open
    for module, expected_error in (
        (daemon_module, DriverError),
        (harness, RuntimeError),
    ):
        source.write_bytes(b"original source\n")
        replacement.write_bytes(b"replacement source\n")
        mapping = {"source.py": Path("source.py")}
        monkeypatch.setattr(module, "_RUNTIME_SOURCE_FILES", mapping)
        if module is daemon_module:
            monkeypatch.setattr(module, "_runtime_source_root", lambda: tmp_path)
        else:
            monkeypatch.setattr(module, "ROOT", tmp_path)
        replaced = False

        def replacing_open(path, *args, **kwargs):  # type: ignore[no-untyped-def]
            nonlocal replaced
            descriptor = base_open(path, *args, **kwargs)
            if Path(path) == source and not replaced:
                source.unlink()
                replacement.rename(source)
                replaced = True
            return descriptor

        monkeypatch.setattr(module.os, "open", replacing_open)
        with pytest.raises(expected_error, match="changed during inspection"):
            module._runtime_source_hashes()


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
