from __future__ import annotations

import signal
import subprocess
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from crowley.session import cli
from crowley.session.model import CLI_VERSION, LunaAdapter, ModelError
from crowley.session.motion import DEFAULT_MOVEMENT_CALIBRATION_PULSE_SECONDS


def _stub_cli_boundary(monkeypatch, tmp_path: Path, response: dict[str, Any]):
    config = SimpleNamespace(socket=tmp_path / "session.sock", journal=tmp_path / "session.jsonl")
    requests: list[tuple[Path, dict[str, Any], float]] = []

    monkeypatch.setattr(cli, "load_config", lambda _path: config)

    def socket_request(path: Path, request: dict[str, Any], *, timeout: float) -> dict[str, Any]:
        requests.append((path, request, timeout))
        return response

    monkeypatch.setattr(cli, "_socket_request", socket_request)
    return requests


def test_motion_calibration_cli_serializes_shared_default(monkeypatch, tmp_path: Path, capsys) -> None:
    requests = _stub_cli_boundary(monkeypatch, tmp_path, {"ok": True, "status": {}})

    assert cli.main(["motion-movement-calibrate", "--generation", "11"]) == 0

    path, request, timeout = requests[0]
    assert path == tmp_path / "session.sock"
    assert request == {
        "command": "motion_movement_calibrate",
        "generation": 11,
        "pulseSeconds": DEFAULT_MOVEMENT_CALIBRATION_PULSE_SECONDS,
    }
    assert request["pulseSeconds"] == DEFAULT_MOVEMENT_CALIBRATION_PULSE_SECONDS
    assert timeout == 95.0
    assert '"ok": true' in capsys.readouterr().out


def test_motion_calibration_cli_preserves_explicit_server_rejection(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    requests = _stub_cli_boundary(
        monkeypatch,
        tmp_path,
        {"ok": False, "error": "movement basis calibration pulse is outside bounds"},
    )

    assert cli.main(["motion-movement-calibrate", "--generation", "11", "--pulse-seconds", "0.9"]) == 1

    _path, request, timeout = requests[0]
    assert request["pulseSeconds"] == 0.9
    assert timeout == 95.0
    assert "outside bounds" in capsys.readouterr().out


def test_motion_camera_calibration_cli_preserves_generation_and_boot(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    requests = _stub_cli_boundary(
        monkeypatch,
        tmp_path,
        {
            "ok": True,
            "status": {},
            "camera": {
                "identity": "client-motion",
                "generation": 11,
                "captureId": "camera:boot:1:4",
                "yawPerPixel": 0.1,
                "convention": "xy-facing-radians-v1",
                "boot": "boot",
            },
        },
    )

    assert cli.main(["motion-camera-calibrate", "--generation", "11", "--delta-pixels", "8"]) == 0

    _path, request, timeout = requests[0]
    assert request == {"command": "motion_camera_calibrate", "generation": 11, "deltaPixels": 8}
    assert timeout == 35.0
    output = capsys.readouterr().out
    assert '"generation": 11' in output
    assert '"boot": "boot"' in output


def _model_for_process_test() -> LunaAdapter:
    adapter = LunaAdapter.__new__(LunaAdapter)
    adapter.neutral_dir = Path("/tmp/crowley-model-test")
    adapter.timeout = 1.0
    adapter.model = "gpt-6-luna"
    adapter.cli_version = CLI_VERSION
    adapter.codex_path = "/bin/true"
    adapter._cancelled = threading.Event()
    adapter._process_lock = threading.RLock()
    adapter._model_call_lock = threading.RLock()
    adapter._process = None
    adapter._cancel_epoch = 0
    return adapter


def test_model_cancel_before_process_registration_is_not_cleared(monkeypatch, tmp_path: Path) -> None:
    adapter = _model_for_process_test()

    class Process:
        pid = 4242

        def __init__(self) -> None:
            self.returncode: int | None = None
            self.exited = threading.Event()

        def poll(self):
            return self.returncode

        def communicate(self, timeout=None):
            if not self.exited.wait(timeout):
                raise subprocess.TimeoutExpired(["model"], timeout)
            return "", ""

    process = Process()

    monkeypatch.setattr(
        "crowley.session.model.subprocess.run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            ["codex", "--version"], 0, stdout=f"{CLI_VERSION}\n", stderr=""
        ),
    )

    def popen(*_args, **_kwargs):
        adapter.cancel()
        return process

    monkeypatch.setattr("crowley.session.model.subprocess.Popen", popen)

    def killpg(_pid: int, signum: int) -> None:
        if signum == signal.SIGKILL:
            process.returncode = -signum
            process.exited.set()

    monkeypatch.setattr("crowley.session.model.os.killpg", killpg)
    with pytest.raises(ModelError, match="cancelled"):
        adapter._run_cli_unlocked(tmp_path / "schema", tmp_path / "image", prompt="test", timeout=0.5)
    assert process.returncode == -signal.SIGKILL
    assert adapter._process is None


def test_model_near_deadline_cleanup_is_bounded_and_retains_live_owner(monkeypatch, tmp_path: Path) -> None:
    adapter = _model_for_process_test()

    class Process:
        pid = 4343
        returncode = None

        def poll(self):
            return self.returncode

        def communicate(self, timeout=None):
            raise subprocess.TimeoutExpired(["model"], timeout)

    process = Process()
    monkeypatch.setattr(
        "crowley.session.model.subprocess.run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            ["codex", "--version"], 0, stdout=f"{CLI_VERSION}\n", stderr=""
        ),
    )
    monkeypatch.setattr("crowley.session.model.subprocess.Popen", lambda *_args, **_kwargs: process)
    monkeypatch.setattr("crowley.session.model.os.killpg", lambda *_args: None)
    started = time.monotonic()
    with pytest.raises(ModelError, match="cleanup exceeded"):
        adapter._run_cli_unlocked(tmp_path / "schema", tmp_path / "image", prompt="test", timeout=0.01)
    assert time.monotonic() - started < 0.5
    assert adapter._process is process


def test_model_retained_live_owner_blocks_next_call_and_shutdown_reaps_it(
    monkeypatch, tmp_path: Path
) -> None:
    adapter = _model_for_process_test()

    class Process:
        pid = 4444

        def __init__(self) -> None:
            self.returncode: int | None = None
            self.kill_count = 0

        def poll(self):
            return self.returncode

        def communicate(self, timeout=None):
            if self.returncode is None:
                raise subprocess.TimeoutExpired(["model"], timeout)
            return "", ""

    process = Process()
    popen_calls = 0
    signals: list[int] = []
    monkeypatch.setattr(
        "crowley.session.model.subprocess.run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            ["codex", "--version"], 0, stdout=f"{CLI_VERSION}\n", stderr=""
        ),
    )

    def popen(*_args, **_kwargs):
        nonlocal popen_calls
        popen_calls += 1
        return process

    monkeypatch.setattr("crowley.session.model.subprocess.Popen", popen)

    def killpg(_pid: int, signum: int) -> None:
        signals.append(signum)
        process.kill_count += 1
        # Leave the first bounded call live so it is retained as an owner;
        # shutdown must perform the follow-up escalation and reap it.
        if process.kill_count >= 3 and signum == signal.SIGKILL:
            process.returncode = -signum

    monkeypatch.setattr("crowley.session.model.os.killpg", killpg)
    with pytest.raises(ModelError, match="cleanup exceeded"):
        adapter._run_cli_unlocked(tmp_path / "schema", tmp_path / "image", prompt="test", timeout=0.01)
    assert adapter._process is process

    with pytest.raises(ModelError):
        adapter._run_cli_unlocked(tmp_path / "schema", tmp_path / "image", prompt="again", timeout=0.5)
    assert popen_calls == 1

    adapter.shutdown()
    assert process.returncode == -signal.SIGKILL
    assert adapter._process is None
    assert signals.count(signal.SIGKILL) >= 2
