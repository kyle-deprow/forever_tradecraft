from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
import multiprocessing
import os
import re
import shutil
import signal
import socket
import struct
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from PIL import Image

from tools import template_matcher_runtime as matcher_runtime

MODULE_PATH = Path(__file__).parents[1] / "tools" / "native_calibration_operator.py"
sys.path.insert(0, str(MODULE_PATH.parent))
spec = importlib.util.spec_from_file_location("native_calibration_operator", MODULE_PATH)
assert spec and spec.loader
operator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = operator
spec.loader.exec_module(operator)


@dataclass(frozen=True)
class Identity:
    fingerprint: str = "a" * 64
    child_geometry: tuple[int, int, int, int] = (0, 0, 1280, 720)
    target_event_xids: frozenset[int] = frozenset({1})


class FakeScreen:
    def __init__(self, root: Path, construct: Path, restore: Path):
        self.root = root
        self.construct = construct
        self.restore = restore
        self.identity = Identity()
        self.last_point = (0, 0, 1)
        self.chat_crop = (0, 0, 64, 64)
        self.agent_crop = (0, 0, 64, 64)

    def wait_reload_boundary(self, *, deadline_monotonic=None, proof="ordinary"):
        return self.identity

    def resolve_identity(self, *, require_foreground: bool = True, deadline_monotonic=None):
        assert require_foreground
        return self.identity

    def capture(self, path: Path, *, identity: Identity, deadline_monotonic=None):
        assert identity is self.identity
        if "post-reload-controls" in path.name and hasattr(self, "dual"):
            source = self.dual
        else:
            source = self.restore if "restore-control" in path.name else self.construct
        path.write_bytes(source.read_bytes())
        os.chmod(path, 0o600)
        return self.identity

    def pointer_position(self, *, deadline_monotonic=None):
        return self.last_point


class FakeInput:
    def __init__(self, screen: FakeScreen, ocr_text: str = "", dispatch=None):
        self.screen = screen
        self.ocr_text = ocr_text
        self.dispatch = dispatch
        self.pending_command = None
        self.calls: list[tuple[str, str]] = []
        self.closed = False

    def key_return(self, *, deadline_monotonic=None):
        self.calls.append(("key", "Return"))
        if self.pending_command is not None and self.dispatch is not None:
            self.dispatch(self.pending_command)
            self.pending_command = None

    def key_escape(self, *, deadline_monotonic=None):
        self.calls.append(("key", "Escape"))

    def type_command(self, command: str, *, deadline_monotonic=None):
        self.calls.append(("type", command))
        self.pending_command = command

    def click(self, match, *, identity, before_press=None, deadline_monotonic=None):
        self.calls.append(("click", match.role))
        self.screen.last_point = (*match.click, 1)
        if before_press is not None:
            before_press()
        if self.dispatch is not None:
            self.dispatch(match.role)

    def close(self):
        self.closed = True


@dataclass
class FakeBinding:
    reservation_id: str = "reservation-1"
    kind: str = "measure"
    state: str = "prepared"

    def record(self, generation: int) -> dict:
        return {
            "reservationId": self.reservation_id,
            "reservationKind": self.kind,
            "reservationState": self.state,
            "controllerGeneration": generation,
            "desktopLeaseHeld": True,
            "guardianGeneration": 0,
            "guardianArmed": False,
            "ownerPid": 1234,
            "ownerProcessStart": "start-1",
            "profileFingerprint": "b" * 64,
            "identityFingerprint": "a" * 64,
            "B0": "boot-1",
            "expectedConstructorBoot": "native-construction:boot-1",
            "expiresMonotonic": 1000000000000.0,
        }


class FakeClient:
    # Explicit test-only supplement for workflows that do not provide the
    # production local SessionIPC socket.  Production clients may never use
    # this bypass.
    _allow_cancellation_actor_bypass = True

    def __init__(
        self,
        generation: int,
        states: list[str],
        *,
        kind: str = "measure",
        recovery_kind: str = "ordinary_reload",
    ):
        self.generation = generation
        self.states = list(states)
        self.kind = kind
        self.recovery_kind = recovery_kind
        self.binding = FakeBinding(kind=kind)
        self.calls: list[dict] = []
        self.history: list[dict] = []
        self.calibration_status_calls = 0
        self.current_state = "construction_prepared"

    def _reply(self, state: str, *, binding: FakeBinding | None = None) -> dict:
        item = binding or self.binding
        if state == "running" and item.kind == "measure":
            item.state = "consumed"
        if state == "finalized":
            item.state = "finalized"
        if not self.history or self.history[-1]["state"] != state:
            self.history.append({"state": state, "nativeClock": float(len(self.history) + 1)})
        handshake = {"state": state, "stateHistory": list(self.history)}
        if state in {
            "construction_released",
            "hold_required",
            "updates_reset_archived",
            "measure_ready",
            "resume_required",
            "resume_ready",
            "finalize_required",
            "finalized",
        }:
            handshake.update(
                {
                    "operationDeadline": 1000000000000.0,
                    "providerDeadline": 1000000000000.0,
                    "constructorClickDeadline": 1000000000000.0,
                }
            )
        if state in {"finalize_required", "finalized"}:
            handshake["finalizeDeadline"] = 1000000000000.0
        return {
            "ok": True,
            "reservation": item.record(self.generation),
            "handshake": handshake,
        }

    def dispatch(self, action: str) -> None:
        transitions = {
            "/crowley agent defer": "construction_prepared",
            "/reload": "construction_prepared",
            "/crowley agent release": "construction_released",
            "construct": "hold_required",
            "/crowley agent hold": "measure_ready",
            "/crowley agent measure": "resume_required",
            "/crowley agent resume": "resume_ready",
            "/crowley agent finalize": "finalized",
            "restore": "recovered",
        }
        target = transitions.get(action)
        if target is None:
            return
        if action == "/crowley agent hold":
            self._reply("updates_reset_archived")
        self.current_state = target

    def prepare(self, generation: int, *, preflight: bool = False):
        assert generation == self.generation
        self.calls.append({"command": "prepare", "preflight": preflight})
        if preflight:
            self.binding = FakeBinding(kind="preflight")
        self.current_state = "construction_prepared"
        return self._reply(self.current_state)

    def bootstrap(self, generation: int, reservation):
        self.calls.append({"command": "bootstrap", "expected": reservation.expected_constructor_boot})
        self.binding.state = "consumed"
        self.current_state = "running"
        return self._reply(self.current_state)

    def native_calibrate(self, generation: int, *, deadline=None):
        assert generation == self.generation
        self.calls.append({"command": "native_calibrate", "generation": generation})
        # The real native worker publishes the reset/baseline barriers before
        # exposing the release gate.  Keep this fixture event driven while
        # retaining that durable history prefix; the operator must observe the
        # new suffix rather than accepting a synthetic recheck progression.
        self._reply("construction_reset_archived")
        self._reply("baseline_bound")
        self._reply("construction_released")
        self.current_state = "construction_released"
        return {
            "ok": True,
            "status": {
                "state": "NATIVE_CALIBRATION",
                "generation": generation,
                "calibrationOperation": {
                    "state": "running",
                    "kind": "native",
                    "generation": generation,
                    "error": "",
                },
            },
        }

    def calibration_status(self, *, deadline=None):
        self.calibration_status_calls += 1
        self.calls.append({"command": "calibration_status"})
        return {
            "ok": True,
            "status": {
                # The real daemon exposes INPUT_CALIBRATION only after the
                # finalized construction handshake has been committed.
                "state": "INPUT_CALIBRATION",
                "generation": self.generation,
                "calibrationOperation": {
                    "state": "complete" if self.calibration_status_calls > 0 else "running",
                    "kind": "native",
                    "generation": self.generation,
                    "error": "",
                },
            },
        }

    def recheck(self, generation: int, reservation_id: str, *, deadline: float | None = None):
        assert generation == self.generation
        assert reservation_id == self.binding.reservation_id
        self.calls.append({"command": "recheck", "reservationId": reservation_id})
        if self.states:
            state = self.states.pop(0)
            return self._reply(state)
        return self._reply(self.current_state)

    def finalize_admit(self, generation: int, reservation_id: str):
        self.calls.append({"command": "finalize_admit", "reservationId": reservation_id})
        self.current_state = "finalize_required"
        return self._reply(self.current_state)

    def recovery_begin(self, generation: int, reservation_id: str = ""):
        self.binding = FakeBinding(reservation_id="ticket-1", kind="recovery", state="recovery")
        self.history = []
        self.current_state = "recovery_required"
        self.calls.append({"command": "recovery_begin", "reservationId": reservation_id})
        return {
            "ok": True,
            "reservation": self.binding.record(self.generation),
            "handshake": {
                "state": self.current_state,
                "recoveryKind": self.recovery_kind,
                "stateHistory": [{"state": "recovery_required", "nativeClock": 1.0}],
            },
        }

    def recovery_complete(self, generation: int, reservation_id: str):
        self.calls.append({"command": "recovery_complete", "reservationId": reservation_id})
        self.binding.state = "recovered"
        self.history = [{"state": "recovery_required", "nativeClock": 1.0}]
        self.current_state = "recovered"
        return self._reply(self.current_state)

    def recovery_cancel(self, generation: int, reservation_id: str):
        self.calls.append({"command": "recovery_cancel", "reservationId": reservation_id})
        self.binding.state = "cancelled"
        self.history = [{"state": "recovery_required", "nativeClock": 1.0}]
        return self._reply("cancelled")

    def status(self, *, deadline=None):
        return {
            "ok": True,
            "status": {
                "state": "PAUSED",
                "generation": self.generation,
                "calibrationOperation": {
                    "state": "error",
                    "kind": "native",
                    "generation": self.generation,
                    "error": "",
                },
            },
        }

    def pause(self, generation: int, *, deadline=None):
        self.calls.append({"command": "pause", "generation": generation})
        return self.status()


class FakeWatchdog:
    def __init__(self):
        self.states: list[dict] = []
        self.closed = False

    def publish(self, *, groups, buttons, keys=frozenset()):
        self.states.append({"groups": set(groups), "buttons": set(buttons), "keys": set(keys)})

    def clear(self):
        self.states.append({"groups": set(), "buttons": set(), "keys": set()})

    def close(self):
        self.closed = True


def _owner_hold_fixture(
    artifact: str, marker: str, action: tuple[str, str], release: tuple[str, str], status
):
    tool = operator.PinnedInputTool.from_root(artifact)
    environment = {"CROWLEY_RECORDER": marker}
    watchdog = operator.Watchdog(
        tool,
        interval=0.02,
        environment=environment,
        owner_pid=os.getpid(),
        owner_start=operator._proc_start(os.getpid()),
    )
    emitter = operator.OwnedEmitter(
        tool,
        action=action,
        release_action=release,
        environment=environment,
    )
    emitter.start()
    assert emitter.pgid and emitter.pgid > 0
    owned_keys = {action[1]} if action[0] == "keydown" else set()
    owned_buttons = {int(action[1])} if action[0] == "mousedown" else set()
    watchdog.publish(groups={emitter.pgid}, buttons=owned_buttons, keys=owned_keys)
    emitter.press()
    assert emitter._process is not None and emitter._process.is_alive()
    status.send((watchdog._process.pid, operator._proc_start(watchdog._process.pid), emitter.pgid))
    while True:
        time.sleep(0.2)


def _production_main_owner_fixture(
    artifact: str,
    release_marker: str,
    gate_marker: str,
    socket_path: str,
    scene_path: str,
    config_path: str,
    templates_path: str,
    error_path: str,
    release_enable: str = "",
):
    class MainConfig:
        socket = Path(socket_path)

    class MainScreen:
        def __init__(self, _config_path, _root):
            self.config_path = Path(config_path)
            self.config = MainConfig()
            self.tool = operator.PinnedInputTool.from_root(Path(artifact))
            self.input_environment = {"CROWLEY_RECORDER": release_marker}
            if release_enable:
                self.input_environment["CROWLEY_RELEASE_ENABLE"] = release_enable
            self.chat_crop = (0, 0, 64, 64)
            self.agent_crop = (0, 0, 64, 64)
            self._pointer_calls = 0

        def resolve_identity(self, *, require_foreground=True, deadline_monotonic=None):
            assert require_foreground
            return Identity()

        def capture(self, path, *, identity, deadline_monotonic=None):
            assert isinstance(identity, Identity)
            shutil.copyfile(scene_path, path)
            os.chmod(path, 0o600)
            return identity

        def pointer_position(self, *, deadline_monotonic=None):
            return (1144, 24, 1)

        def close(self):
            self.tool.close()

    class MainClient:
        def __init__(self, socket):
            self.socket_path = Path(socket)
            self.generation = 7
            self.binding = FakeBinding(kind="preflight")
            self.history = [{"state": "construction_prepared", "nativeClock": 1.0}]

        def _reply(self):
            reservation = self.binding.record(self.generation)
            reservation["expiresMonotonic"] = time.monotonic() + 8.0
            return {
                "ok": True,
                "reservation": reservation,
                "handshake": {"state": "construction_prepared", "stateHistory": list(self.history)},
            }

        def prepare(self, generation, *, preflight=False):
            assert preflight and generation == self.generation
            return self._reply()

        def recheck(self, generation, reservation_id, *, deadline=None):
            assert generation == self.generation
            assert reservation_id == self.binding.reservation_id
            return self._reply()

    real_operator = operator.NativeCalibrationOperator

    class DebugOperator(real_operator):
        @staticmethod
        def _ocr_file(path):
            if Path(path).name.startswith("chat-closed-"):
                return ""
            return "say: /crowley agent defer"

        def run(self):
            try:
                return super().run()
            except BaseException as exc:
                Path(error_path).write_text(f"{type(exc).__name__}: {exc}", encoding="utf-8")
                raise

    operator.X11Screen = MainScreen
    operator.DaemonClient = MainClient
    operator.NativeCalibrationOperator = DebugOperator
    real_press = operator.OwnedEmitter.press

    def gated_press(emitter):
        if emitter.action == ("mousedown", "1"):
            Path(gate_marker).write_text("button-watchdog-armed", encoding="utf-8")
        result = real_press(emitter)
        if emitter.action == ("mousedown", "1"):
            while True:
                time.sleep(0.1)
        return result

    operator.OwnedEmitter.press = gated_press
    operator._source_bindings = lambda _screen, _manifest, _matcher_runtime=None: {}
    raise SystemExit(
        operator.main(
            [
                operator.MODE_CONTROL_PREFLIGHT,
                "--generation",
                "7",
                "--config",
                config_path,
                "--templates",
                templates_path,
            ]
        )
    )


def _persistent_release_owner_fixture(artifact: str, marker: str, enable: str, status):
    tool = operator.PinnedInputTool.from_root(Path(artifact))
    watchdog = operator.Watchdog(
        tool,
        interval=0.02,
        environment={
            "CROWLEY_RECORDER": marker,
            "CROWLEY_RELEASE_ENABLE": enable,
        },
        owner_pid=os.getpid(),
        owner_start=operator._proc_start(os.getpid()),
    )
    watchdog.publish(groups=set(), buttons=set(), keys={"Return"})
    status.send((watchdog._process.pid, operator._proc_start(watchdog._process.pid)))
    while True:
        time.sleep(0.2)


def _normal_exit_failed_release_fixture(artifact: str, marker: str, enable: str, status):
    """Exercise ordinary SystemExit while the independent release is pending."""

    tool = operator.PinnedInputTool.from_root(Path(artifact))
    watchdog = operator.Watchdog(
        tool,
        interval=0.02,
        environment={
            "CROWLEY_RELEASE_MARKER": marker,
            "CROWLEY_RELEASE_ENABLE": enable,
        },
        owner_pid=os.getpid(),
        owner_start=operator._proc_start(os.getpid()),
    )
    watchdog.publish(groups=set(), buttons=set(), keys={"Return"})
    assert watchdog._process is not None
    status.send((watchdog._process.pid, operator._proc_start(watchdog._process.pid)))
    try:
        watchdog.close()
    except operator.OperatorError:
        pass
    raise SystemExit(2)


def _cancellation_owner_fixture(socket_path: str, status):
    actor = operator.CancellationActor(
        Path(socket_path),
        generation=17,
        reservation_id="reservation-live",
        deadline=time.monotonic() + 8.0,
        owner_pid=os.getpid(),
        owner_start=operator._proc_start(os.getpid()),
    )
    actor.start()
    assert actor._process is not None
    status.send(actor._process.pid)
    while True:
        time.sleep(0.2)


def _actor_admission_owner_fixture(socket_path: str, status):
    """Real owner process whose actor performs an admission while it is killed."""

    owner_pid = os.getpid()
    owner_start = operator._proc_start(owner_pid)
    actor = operator.CancellationActor(
        Path(socket_path),
        generation=31,
        reservation_id="",
        deadline=time.monotonic() + 12.0,
        owner_pid=owner_pid,
        owner_start=owner_start,
    )
    actor.start()
    assert actor._process is not None
    status.send((owner_pid, owner_start, actor._process.pid))
    try:
        actor.call(
            "prepare",
            generation=31,
            preflight=False,
            deadline=time.monotonic() + 10.0,
        )
    except BaseException:
        pass
    while True:
        time.sleep(0.2)


def _peer_pid(connection: socket.socket) -> int:
    raw = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    pid, _uid, _gid = struct.unpack("3i", raw)
    return pid


def _admission_reply(
    *,
    owner_pid: int,
    owner_start: str,
    generation: int,
    reservation_id: str,
    kind: str,
    state: str,
    handshake_state: str,
    history: list[str],
    expiry: float | None = None,
    guardian_generation: int = 4,
) -> dict:
    if expiry is None:
        expiry = time.monotonic() + 20.0
    record = {
        "reservationId": reservation_id,
        "reservationKind": kind,
        "reservationState": state,
        "controllerGeneration": generation,
        "desktopLeaseHeld": True,
        "guardianGeneration": guardian_generation,
        "guardianArmed": False,
        "ownerPid": owner_pid,
        "ownerProcessStart": owner_start,
        "profileFingerprint": "b" * 64,
        "identityFingerprint": "a" * 64,
        "B0": "boot-31",
        "expectedConstructorBoot": "native-construction:boot-31",
        "expiresMonotonic": expiry,
    }
    return {
        "ok": True,
        "reservation": record,
        "handshake": {"state": handshake_state},
        "stateHistory": [
            {"state": value, "nativeClock": float(index + 1)} for index, value in enumerate(history)
        ],
    }


def make_template(path: Path, color: tuple[int, int, int]) -> str:
    image = Image.new("RGB", (4, 4), color)
    image.save(path, format="PNG")
    os.chmod(path, 0o600)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _wait_pid_identity_exit(pid: int, start: str | None, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            current = operator._proc_start(pid)
        except Exception:
            current = None
        if current is None or (start is not None and current != start):
            return True
        time.sleep(0.05)
    try:
        return operator._proc_start(pid) is None
    except Exception:
        return True


def make_scenes(tmp_path: Path):
    construct = tmp_path / "construct.png"
    restore = tmp_path / "restore.png"
    construct_hash = make_template(construct, (255, 0, 0))
    restore_hash = make_template(restore, (0, 255, 0))
    manifest_file = tmp_path / "templates.json"
    manifest_file.write_text(
        json.dumps(
            {
                "construct": {"path": str(construct), "sha256": construct_hash, "threshold": 5.0},
                "restore": {"path": str(restore), "sha256": restore_hash, "threshold": 5.0},
            }
        )
    )
    os.chmod(manifest_file, 0o600)
    scene_construct = Image.new("RGB", (1280, 720), (0, 0, 0))
    scene_restore = Image.new("RGB", (1280, 720), (0, 0, 0))
    scene_construct.paste(Image.open(construct), (1142, 22))
    scene_restore.paste(Image.open(restore), (1211, 22))
    scene_construct_path = tmp_path / "scene-construct.png"
    scene_restore_path = tmp_path / "scene-restore.png"
    scene_construct.save(scene_construct_path, format="PNG")
    scene_restore.save(scene_restore_path, format="PNG")
    return operator.TemplateManifest.load(manifest_file), scene_construct_path, scene_restore_path


def make_recording_artifact(tmp_path: Path) -> Path:
    source = tmp_path / "recorder.c"
    executable = tmp_path / "recorder"
    source.write_text(
        """
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int main(int argc, char **argv) {
    const char *path = getenv("CROWLEY_RECORDER");
    if (path == NULL || argc < 3) return 2;
    int fd = open(path, O_WRONLY | O_CREAT | O_APPEND, 0600);
    if (fd < 0) return 3;
    dprintf(fd, "%s %s\\n", argv[1], argv[2]);
    close(fd);
    return 0;
}
""",
        encoding="utf-8",
    )
    subprocess.run(["cc", "-O2", str(source), "-o", str(executable)], check=True)
    from crowley.session.input_tool import (
        ARCHIVE_BASENAME,
        MANIFEST_BASENAME,
        PINNED_ARCHIVE_SHA256,
        PINNED_COMMIT,
        PRIVATE_TOOL_BASENAME,
    )

    artifact = tmp_path / "sealed-tool"
    artifact.mkdir(mode=0o700)
    shutil.copyfile(executable, artifact / PRIVATE_TOOL_BASENAME)
    shutil.copyfile(
        MODULE_PATH.parents[1] / "vendor" / "xdotool-source.tar.gz",
        artifact / ARCHIVE_BASENAME,
    )
    executable_sha256 = hashlib.sha256((artifact / PRIVATE_TOOL_BASENAME).read_bytes()).hexdigest()
    (artifact / MANIFEST_BASENAME).write_text(
        json.dumps(
            {
                "commit": PINNED_COMMIT,
                "archive_sha256": PINNED_ARCHIVE_SHA256,
                "executable": PRIVATE_TOOL_BASENAME,
                "executable_sha256": executable_sha256,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (artifact / PRIVATE_TOOL_BASENAME).chmod(0o700)
    (artifact / ARCHIVE_BASENAME).chmod(0o600)
    (artifact / MANIFEST_BASENAME).chmod(0o600)
    return artifact


def make_gated_recording_artifact(tmp_path: Path) -> Path:
    """Build a sealed fixture image that reports each owned action and waits for ACK."""

    source = tmp_path / "gated-recorder.c"
    executable = tmp_path / "gated-recorder"
    source.write_text(
        r"""
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
int main(int argc, char **argv) {
    const char *log = getenv("CROWLEY_ACTION_LOG");
    const char *acks = getenv("CROWLEY_ACTION_ACK_DIR");
    if (!log || !acks || argc < 2) return 2;
    int fd = open(log, O_WRONLY | O_CREAT | O_APPEND, 0600);
    if (fd < 0) return 3;
    dprintf(fd, "%ld\t%d", (long)getpid(), argc - 1);
    for (int i = 1; i < argc; i++) dprintf(fd, "\t%s", argv[i]);
    dprintf(fd, "\n");
    close(fd);
    char ack[4096];
    snprintf(ack, sizeof(ack), "%s/%ld", acks, (long)getpid());
    for (int i = 0; i < 800; i++) {
        if (access(ack, F_OK) == 0) return 0;
        usleep(10000);
    }
    return 4;
}
""",
        encoding="utf-8",
    )
    subprocess.run(["cc", "-O2", str(source), "-o", str(executable)], check=True)
    from crowley.session.input_tool import (
        ARCHIVE_BASENAME,
        MANIFEST_BASENAME,
        PINNED_ARCHIVE_SHA256,
        PINNED_COMMIT,
        PRIVATE_TOOL_BASENAME,
    )

    artifact = tmp_path / "sealed-gated-tool"
    artifact.mkdir(mode=0o700)
    shutil.copyfile(executable, artifact / PRIVATE_TOOL_BASENAME)
    shutil.copyfile(
        MODULE_PATH.parents[1] / "vendor" / "xdotool-source.tar.gz",
        artifact / ARCHIVE_BASENAME,
    )
    digest = hashlib.sha256((artifact / PRIVATE_TOOL_BASENAME).read_bytes()).hexdigest()
    (artifact / MANIFEST_BASENAME).write_text(
        json.dumps(
            {
                "commit": PINNED_COMMIT,
                "archive_sha256": PINNED_ARCHIVE_SHA256,
                "executable": PRIVATE_TOOL_BASENAME,
                "executable_sha256": digest,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (artifact / PRIVATE_TOOL_BASENAME).chmod(0o700)
    (artifact / ARCHIVE_BASENAME).chmod(0o600)
    (artifact / MANIFEST_BASENAME).chmod(0o600)
    return artifact


def test_manifest_and_exclusive_template_match(tmp_path):
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    matcher = operator.TemplateMatcher(
        manifest,
        artifact_root=matcher_runtime.DEFAULT_ARTIFACT_ROOT,
    )
    assert matcher.source_bindings["template-matcher-binary"] == matcher_runtime.EXPECTED_ARTIFACT_SHA256
    for source_name, source_digest in matcher_runtime.EXPECTED_SOURCE_HASHES.items():
        assert matcher.source_bindings[f"template-matcher-{source_name}"] == source_digest
    region = operator.NativeCalibrationOperator._control_region(Identity())
    deadline = time.monotonic() + 10.0
    try:
        match = matcher.require_exclusive(
            construct_scene,
            "construct",
            region=region,
            deadline_monotonic=deadline,
        )
        assert match.accepted
        assert match.click == (1144, 24)
        dual = Image.new("RGB", (1280, 720), (0, 0, 0))
        dual.paste(Image.open(construct_scene).crop((1142, 22, 1146, 26)), (1142, 22))
        dual.paste(Image.open(restore_scene).crop((1211, 22, 1215, 26)), (1211, 22))
        dual_path = tmp_path / "scene-dual-visible.png"
        dual.save(dual_path, format="PNG")
        assert matcher.require_exclusive(
            dual_path,
            "construct",
            region=region,
            deadline_monotonic=deadline,
        ).accepted
        assert matcher.require_exclusive(
            dual_path,
            "restore",
            region=region,
            deadline_monotonic=deadline,
        ).accepted
        with pytest.raises(operator.OperatorError, match="distinct"):
            operator.TemplateManifest(
                manifest.construct,
                operator.TemplateRole(manifest.construct.path, manifest.construct.sha256, 5.0),
            ).verify()
    finally:
        matcher.close()


def test_template_matcher_forwards_one_absolute_deadline_to_search_and_score(tmp_path: Path) -> None:
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    root = matcher_runtime.DEFAULT_ARTIFACT_ROOT
    calls: list[tuple[str, float]] = []

    class RecordingRuntime:
        def __init__(self) -> None:
            self.delegate = matcher_runtime.TemplateMatcherRuntime(root)

        @property
        def source_bindings(self) -> dict[str, str]:
            return self.delegate.source_bindings

        def search(self, *args: Any, deadline_monotonic: float, **kwargs: Any):
            calls.append(("search", deadline_monotonic))
            return self.delegate.search(*args, deadline_monotonic=deadline_monotonic, **kwargs)

        def score_at(self, *args: Any, deadline_monotonic: float, **kwargs: Any):
            calls.append(("score_at", deadline_monotonic))
            return self.delegate.score_at(*args, deadline_monotonic=deadline_monotonic, **kwargs)

        def close(self) -> None:
            self.delegate.close()

    screen = FakeScreen(tmp_path, construct_scene, restore_scene)
    screen_deadlines: list[tuple[str, float | None]] = []
    original_capture = screen.capture
    original_resolve = screen.resolve_identity

    def recording_capture(path: Path, *, identity: Identity, deadline_monotonic: float | None = None):
        screen_deadlines.append(("capture", deadline_monotonic))
        return original_capture(path, identity=identity, deadline_monotonic=deadline_monotonic)

    def recording_resolve(*, require_foreground: bool = True, deadline_monotonic: float | None = None):
        screen_deadlines.append(("resolve", deadline_monotonic))
        return original_resolve(
            require_foreground=require_foreground,
            deadline_monotonic=deadline_monotonic,
        )

    screen.capture = recording_capture
    screen.resolve_identity = recording_resolve
    attempt = tmp_path / "attempt"
    attempt.mkdir(mode=0o700)
    candidate = object.__new__(operator.NativeCalibrationOperator)
    candidate.clock = time.monotonic
    candidate.receipt = SimpleNamespace(attempt=attempt, event=lambda *_args, **_kwargs: None)
    candidate.screen = screen
    candidate._identity_guard = lambda *_args, **_kwargs: screen.identity
    candidate._deadline = lambda *_args, **_kwargs: deadline

    recording = RecordingRuntime()
    matcher = operator.TemplateMatcher(manifest, runtime=recording)
    deadline = time.monotonic() + 20.0
    try:
        candidate.matcher = matcher
        assert candidate._capture("construct-control", require_exclusive="construct")[2].accepted
        assert calls == [("search", deadline), ("score_at", deadline)]
        assert screen_deadlines == [("capture", deadline), ("resolve", deadline)]

        calls.clear()
        screen_deadlines.clear()
        dual = Image.new("RGB", (1280, 720), (0, 0, 0))
        with Image.open(construct_scene) as construct, Image.open(restore_scene) as restore:
            dual.paste(construct.crop((1142, 22, 1146, 26)), (1142, 22))
            dual.paste(restore.crop((1211, 22, 1215, 26)), (1211, 22))
        dual_path = tmp_path / "dual-deadline.png"
        dual.save(dual_path, format="PNG")
        screen.dual = dual_path
        assert candidate._capture("post-reload-controls", require_dual=True)[2].accepted
        assert calls == [("search", deadline), ("search", deadline)]
        assert screen_deadlines == [("capture", deadline), ("resolve", deadline)]
    finally:
        matcher.close()


@pytest.mark.parametrize("failure", ["runtime", "timeout", "rejected"])
def test_click_matcher_failure_refuses_before_fixed_input_or_action_log(
    tmp_path: Path,
    failure: str,
) -> None:
    manifest, construct_scene, _restore_scene = make_scenes(tmp_path)
    delegate = matcher_runtime.TemplateMatcherRuntime(matcher_runtime.DEFAULT_ARTIFACT_ROOT)

    class FailingRuntime:
        @property
        def source_bindings(self) -> dict[str, str]:
            return delegate.source_bindings

        def search(self, *args: Any, deadline_monotonic: float, **kwargs: Any):
            result = delegate.search(*args, deadline_monotonic=deadline_monotonic, **kwargs)
            if failure == "runtime":
                raise matcher_runtime.MatcherError("recorded matcher failure")
            if failure == "timeout":
                raise matcher_runtime.MatcherTimeout("recorded matcher timeout")
            return matcher_runtime.MatcherResult(
                "rejected",
                result.count * 6,
                result.count,
                result.box,
            )

        def score_at(self, *args: Any, deadline_monotonic: float, **kwargs: Any):
            return delegate.score_at(*args, deadline_monotonic=deadline_monotonic, **kwargs)

        def close(self) -> None:
            delegate.close()

    attempt = tmp_path / "attempt"
    attempt.mkdir(mode=0o700)
    receipt = SimpleNamespace(attempt=attempt, event=lambda *_args, **_kwargs: None)
    screen = FakeScreen(tmp_path, construct_scene, construct_scene)
    action_log = tmp_path / "actions.log"
    action_log.touch(mode=0o600)
    emitter_calls: list[str] = []

    class Tool:
        pass

    def forbidden_emitter() -> Any:
        emitter_calls.append("allocated")
        raise AssertionError("FixedInput allocated an emitter after matcher refusal")

    input_device = operator.FixedInput(
        Tool(),
        watchdog=FakeWatchdog(),
        run=lambda *_args, **_kwargs: action_log.write_text("dispatched", encoding="utf-8"),
        emitter_factory=forbidden_emitter,
    )
    matcher = operator.TemplateMatcher(manifest, runtime=FailingRuntime())
    candidate = object.__new__(operator.NativeCalibrationOperator)
    candidate.mode = operator.MODE_CONTROL_PREFLIGHT
    candidate._phase_deadlines = {}
    candidate._release_dispatch = None
    candidate.clock = time.monotonic
    candidate._recheck = lambda *_args, **_kwargs: {}
    candidate._identity_guard = lambda *_args, **_kwargs: screen.identity
    candidate._deadline = lambda *_args, **_kwargs: time.monotonic() + 20.0
    candidate.receipt = receipt
    candidate.screen = screen
    candidate.matcher = matcher
    candidate.input = input_device
    try:
        with pytest.raises(
            operator.OperatorError, match="native .*template matching failed|not role-exclusive"
        ):
            candidate._click("construct")
        assert emitter_calls == []
        assert action_log.read_text(encoding="utf-8") == ""
    finally:
        matcher.close()


def test_reservation_binding_rejects_boot_substitution():
    record = FakeBinding().record(7)
    record["expectedConstructorBoot"] = "boot-1"
    with pytest.raises(operator.OperatorError, match="expected constructor boot"):
        operator.ReservationBinding.from_record(record, expected_generation=7, now=1.0)


def test_reservation_binding_allows_zero_initial_guardian_generation():
    binding = operator.ReservationBinding.from_record(FakeBinding().record(7), expected_generation=7, now=1.0)
    assert binding.guardian_generation == 0
    assert binding.expected_constructor_boot == "native-construction:boot-1"


def test_daemon_client_uses_exact_closed_request_and_no_retry(tmp_path):
    calls = []

    def request(path, request, *, timeout):
        calls.append((path, request, timeout))
        return {
            "ok": True,
            "reservation": FakeBinding().record(7),
            "handshake": {"state": "construction_prepared"},
        }

    client = operator.DaemonClient(tmp_path / "session.sock", request_fn=request, clock=lambda: 1.0)
    client.prepare(7)
    client.recheck(7, "reservation-1", deadline=2.0)
    client.native_calibrate(7, deadline=2.0)
    client.calibration_status(deadline=2.0)
    client.status(deadline=2.0)
    client.pause(7, deadline=2.0)
    assert calls[0][1] == {"command": "native_construction_prepare", "generation": 7}
    with pytest.raises(operator.OperatorError):
        client.request({"command": "native_construction_prepare", "generation": 7, "extra": True})
    assert calls[1][1] == {
        "command": "native_construction_recheck",
        "generation": 7,
        "reservationId": "reservation-1",
    }
    assert calls[2][1] == {"command": "native_calibrate", "generation": 7}
    assert calls[3][1] == {"command": "calibration_status"}
    assert calls[4][1] == {"command": "status"}
    assert calls[5][1] == {
        "command": "pause",
        "generation": 7,
        "reason": "native construction recovery",
    }
    assert len(calls) == 6


def test_receipt_is_private_atomic_and_rejects_forbidden_fields(tmp_path):
    writer = operator.ReceiptWriter(tmp_path / "root", operator.MODE_CONTROL_PREFLIGHT)
    writer.begin()
    writer.event("safe", generation=7)
    with pytest.raises(operator.ReceiptError):
        writer.event("bad", path="/secret")
    writer.finish("refused", "visual_evidence_refused")
    receipt = writer.attempt / "receipt.json"
    assert receipt.stat().st_mode & 0o077 == 0
    loaded = json.loads(receipt.read_text())
    assert loaded["outcome"] == "refused"
    assert not (writer.attempt / ".receipt.json.tmp").exists()


def test_fixed_input_publishes_before_press_and_clears_after_release():
    class Tool:
        proc_path = "/proc/self/fd/5"

        class Image:
            fd = 5

        image = Image()

    calls = []
    watchdog = FakeWatchdog()
    emitter_events = []

    class Emitter:
        pgid = 77

        def start(self):
            emitter_events.append("start")

        def press(self):
            emitter_events.append("press")

        def release(self):
            emitter_events.append("release")

        def abort(self):
            emitter_events.append("abort")

    def run(argv, **kwargs):
        calls.append(tuple(argv[1:]))

    input_device = operator.FixedInput(Tool(), watchdog=watchdog, run=run, emitter_factory=lambda: Emitter())
    identity = Identity()
    match = operator.TemplateMatch("construct", True, 0.0, (5, 5, 4, 4), (7, 7), "c" * 64)
    input_device.click(match, identity=identity)
    assert calls == []
    assert emitter_events == ["start", "press", "release", "start", "press", "release"]
    assert watchdog.states == [
        {"groups": {77}, "buttons": set(), "keys": set()},
        {"groups": set(), "buttons": set(), "keys": set()},
        {"groups": {77}, "buttons": {1}, "keys": set()},
        {"groups": set(), "buttons": set(), "keys": set()},
    ]


def test_fixed_input_type_publishes_exact_nonempty_keysyms_and_long_budget():
    class Tool:
        proc_path = "/proc/self/fd/5"

        class Image:
            fd = 5

        image = Image()

    watchdog = FakeWatchdog()
    events = []

    class Emitter:
        pgid = 91

        def start(self):
            events.append("start")

        def press(self):
            events.append("press")

        def release(self):
            events.append("release")

        def abort(self):
            events.append("abort")

    command = "/crowley agent finalize"
    input_device = operator.FixedInput(Tool(), watchdog=watchdog, emitter_factory=lambda: Emitter())
    input_device.type_command(command)
    assert events == ["start", "press", "release"]
    assert watchdog.states[0]["keys"] == operator._text_keysyms(command)
    assert watchdog.states[0]["keys"]
    assert operator._action_timeout(("type", "--delay", "130", command)) > 2.0
    with pytest.raises(operator.OperatorError, match="allowlisted"):
        operator._action_timeout(("type", "--delay", "130", "/not-fixed"))


def test_fixed_input_refusal_before_go_clears_ownership_without_release():
    class Tool:
        proc_path = "/proc/self/fd/5"

        class Image:
            fd = 5

        image = Image()

    watchdog = FakeWatchdog()
    events = []

    class Emitter:
        pgid = 92

        def start(self):
            events.append("start")

        def press(self):
            events.append("press")

        def release(self):
            events.append("release")

        def abort(self):
            events.append("abort")

    input_device = operator.FixedInput(Tool(), watchdog=watchdog, emitter_factory=lambda: Emitter())
    match = operator.TemplateMatch("construct", True, 0.0, (5, 5, 4, 4), (7, 7), "c" * 64)
    identity = Identity()

    def refuse_before_press():
        raise operator.OperatorError("identity drift")

    with pytest.raises(operator.OperatorError, match="identity drift"):
        input_device.click(match, identity=identity, before_press=refuse_before_press)
    assert events == ["start", "press", "release", "start", "abort", "abort"]
    assert watchdog.states[-1] == {"groups": set(), "buttons": set(), "keys": set()}


def test_fixed_input_phase_budget_refuses_before_go():
    class Tool:
        proc_path = "/proc/self/fd/5"

        class Image:
            fd = 5

        image = Image()

    watchdog = FakeWatchdog()
    events = []

    class Emitter:
        pgid = 93

        def start(self):
            events.append("start")

        def press(self):
            events.append("press")

        def release(self):
            events.append("release")

        def abort(self):
            events.append("abort")

    input_device = operator.FixedInput(Tool(), watchdog=watchdog, emitter_factory=lambda: Emitter())
    with pytest.raises(operator.OperatorError, match="cannot fit"):
        input_device.type_command("/crowley agent finalize", deadline_monotonic=time.monotonic() + 0.001)
    assert events == ["start", "abort"]
    assert watchdog.states[-1] == {"groups": set(), "buttons": set(), "keys": set()}


def test_action_budget_refuses_before_physical_dispatch_and_deadline_is_monotone():
    action = ("type", "--delay", "130", "/crowley agent finalize")
    with pytest.raises(operator.OperatorError, match="cannot fit"):
        operator._action_timeout(action, deadline=time.monotonic() + 0.001)

    candidate = object.__new__(operator.NativeCalibrationOperator)
    candidate._reservation_deadline = 10.0
    candidate._operation_deadline = 20.0
    candidate._phase_deadlines = {"constructor": 30.0}
    assert candidate._deadline("constructor") == 10.0
    candidate._reservation_deadline = None
    assert candidate._deadline("constructor") == 20.0


def test_record_operation_deadline_never_extends_an_observed_bound():
    candidate = object.__new__(operator.NativeCalibrationOperator)
    candidate._operation_deadline = None
    candidate._phase_deadlines = {}
    candidate._handshake = "running"

    candidate._record_operation_deadline(
        {
            "handshake": {
                "operationDeadline": 200.0,
                "constructorClickDeadline": 210.0,
                "providerDeadline": 250.0,
                "finalizeHookDeadline": 260.0,
                "finalizeDeadline": 270.0,
            }
        }
    )
    assert candidate._operation_deadline == 200.0
    assert candidate._phase_deadlines == {
        "constructor": 210.0,
        "provider": 250.0,
        "finalize_hook": 260.0,
        "finalize": 270.0,
    }
    candidate._record_operation_deadline(
        {
            "handshake": {
                "operationDeadline": 300.0,
                "constructorClickDeadline": 310.0,
                "providerDeadline": 350.0,
                "finalizeHookDeadline": 360.0,
                "finalizeDeadline": 370.0,
            }
        }
    )
    assert candidate._operation_deadline == 200.0
    assert candidate._phase_deadlines == {
        "constructor": 210.0,
        "provider": 250.0,
        "finalize_hook": 260.0,
        "finalize": 270.0,
    }
    candidate._record_operation_deadline(
        {
            "handshake": {
                "operationDeadline": 150.0,
                "constructorClickDeadline": 205.0,
                "providerDeadline": 175.0,
                "finalizeHookDeadline": 255.0,
                "finalizeDeadline": 265.0,
            }
        }
    )
    assert candidate._operation_deadline == 150.0
    assert candidate._phase_deadlines == {
        "constructor": 205.0,
        "provider": 175.0,
        "finalize_hook": 255.0,
        "finalize": 265.0,
    }

    # A later provider response may advertise a longer value, but the
    # constructor recheck/click path must still refuse after the original
    # constructor bound.  This is the release+10 bounded phase, not a
    # provider deadline that can widen it.
    candidate.mode = operator.MODE_MEASURE_DEFERRED
    candidate.clock = time.monotonic
    candidate._phase_deadlines["constructor"] = time.monotonic() - 1.0
    candidate._release_dispatch = time.monotonic() - 9.0
    with pytest.raises(operator.OperatorError, match="constructor click deadline expired"):
        candidate._click("construct")


def test_owned_emitter_invalid_process_group_reaps_child_and_closes_fds(tmp_path, monkeypatch):
    artifact = make_gated_recording_artifact(tmp_path)
    tool = operator.PinnedInputTool.from_root(artifact)
    emitter = operator.OwnedEmitter(tool, context=multiprocessing.get_context("fork"))
    monkeypatch.setattr(operator.os, "getpgid", lambda _pid: 0)
    try:
        with pytest.raises(operator.OperatorError, match="process group is malformed"):
            emitter.start()
        assert emitter._process is not None
        assert not emitter._process.is_alive()
        assert emitter._process.exitcode is not None
        assert emitter.pgid == 0
        assert all(
            getattr(emitter, descriptor) == -1
            for descriptor in ("_gate_read", "_gate_write", "_status_read", "_status_write")
        )
    finally:
        emitter.abort()
        tool.close()


def test_watchdog_missing_owner_start_refuses_before_child_allocation(tmp_path, monkeypatch):
    artifact = make_recording_artifact(tmp_path)
    tool = operator.PinnedInputTool.from_root(artifact)
    context_calls: list[str] = []

    def forbidden_context(name: str):
        context_calls.append(name)
        raise AssertionError("watchdog child context was allocated")

    monkeypatch.setattr(operator.multiprocessing, "get_context", forbidden_context)
    try:
        with pytest.raises(operator.OperatorError, match="owner start identity is unavailable"):
            operator.Watchdog(tool, owner_pid=os.getpid(), owner_start="")
        assert context_calls == []
    finally:
        tool.close()


def test_cancellation_child_closes_inherited_nonprotocol_fd_and_keeps_protocol(tmp_path, monkeypatch):
    socket_path = tmp_path / "cancellation-fd.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(1)
    sentinel_read, sentinel_write = os.pipe()
    fork_context = multiprocessing.get_context("fork")
    monkeypatch.setattr(operator.multiprocessing, "get_context", lambda _name: fork_context)
    actor = operator.CancellationActor(
        socket_path,
        generation=31,
        reservation_id="",
        deadline=time.monotonic() + 20.0,
        owner_pid=os.getpid(),
        owner_start=operator._proc_start(os.getpid()),
    )
    server_thread: threading.Thread | None = None
    received: list[dict] = []

    def serve_once() -> None:
        connection, _address = listener.accept()
        with connection:
            frame = bytearray()
            while not frame.endswith(b"\n"):
                chunk = connection.recv(4096)
                if not chunk:
                    raise AssertionError("cancellation actor closed protocol before request")
                frame.extend(chunk)
            received.append(json.loads(frame[:-1].decode("utf-8")))
            reply = _admission_reply(
                owner_pid=os.getpid(),
                owner_start=operator._proc_start(os.getpid()) or "server-start",
                generation=31,
                reservation_id="measure-31",
                kind="measure",
                state="prepared",
                handshake_state="construction_prepared",
                history=["construction_prepared"],
            )
            connection.sendall(json.dumps(reply, separators=(",", ":")).encode() + b"\n")

    try:
        actor.start()
        assert actor._process is not None
        actor_pid = actor._process.pid
        assert actor_pid is not None
        try:
            os.readlink(f"/proc/{actor_pid}/fd/{sentinel_read}")
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("cancellation child retained a nonprotocol descriptor")
        server_thread = threading.Thread(target=serve_once, daemon=True)
        server_thread.start()
        response = actor.call(
            "prepare",
            generation=31,
            preflight=False,
            deadline=time.monotonic() + 10.0,
        )
        assert response["reservation"]["reservationId"] == "measure-31"
        assert received == [{"command": "native_construction_prepare", "generation": 31}]
    finally:
        actor.close()
        if server_thread is not None:
            server_thread.join(timeout=3.0)
        listener.close()
        os.close(sentinel_read)
        os.close(sentinel_write)
    assert actor._process is not None and not actor._process.is_alive()


def test_production_reload_boundary_uses_profile_bound_strict_absence(tmp_path, monkeypatch):
    identity = Identity()
    screen = object.__new__(operator.X11Screen)
    screen.root = tmp_path
    screen.config = SimpleNamespace(
        profile=SimpleNamespace(canvas_crop=(0, 0, 4, 4), client_width=4, client_height=4)
    )
    calls = []

    def resolve_identity(*, require_foreground=True, deadline_monotonic=None):
        assert require_foreground
        return identity

    def capture(path, *, identity, deadline_monotonic=None):
        Image.new("RGB", (4, 4), (0, 0, 0)).save(path, format="PNG")
        return identity

    screen.resolve_identity = resolve_identity
    screen.capture = capture
    monkeypatch.setattr(
        operator,
        "_strict_native_absence_image",
        lambda path, *, expected_size: calls.append((path, expected_size)) or True,
    )
    result = screen.wait_reload_boundary(
        deadline_monotonic=time.monotonic() + 2.0,
        proof="absence",
    )
    assert result is identity
    assert calls and calls[0][1] == (4, 4)
    assert not list(tmp_path.iterdir())


def test_chat_readback_mismatch_escapes_without_submit(tmp_path):
    manifest, _construct_scene, restore_scene = make_scenes(tmp_path)
    screen = FakeScreen(tmp_path, restore_scene, restore_scene)
    input_device = FakeInput(screen)
    client = FakeClient(7, ["construction_prepared", "construction_prepared"])
    op = operator.NativeCalibrationOperator(
        mode=operator.MODE_CONTROL_PREFLIGHT,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=client,
        screen=screen,
        input_device=input_device,
        ocr=lambda path: "" if "chat-closed" in path.name else "say: /wrong",
        receipt_root=tmp_path / "receipts",
    )
    op.receipt.begin()
    op._binding = operator.ReservationBinding.from_record(
        FakeBinding().record(7), expected_generation=7, now=1.0
    )
    op._reservation_deadline = 1000000000000.0
    op._handshake = "construction_prepared"
    with pytest.raises(operator.OperatorError, match="readback"):
        op._chat("/crowley agent defer", expected_state="construction_prepared")
    assert ("key", "Escape") in input_device.calls
    assert ("key", "Return") not in input_device.calls[2:]
    op.input.close()


def test_control_preflight_ordinary_reload_branch_is_fixed_and_no_resume(tmp_path):
    manifest, _construct_scene, restore_scene = make_scenes(tmp_path)
    screen = FakeScreen(tmp_path, restore_scene, restore_scene)
    input_device = FakeInput(screen)
    client = FakeClient(7, ["recovery_required"] * 8)
    op = operator.NativeCalibrationOperator(
        mode=operator.MODE_RECOVER,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=client,
        screen=screen,
        input_device=input_device,
        ocr=lambda path: "" if "chat-closed" in path.name else "say: /reload",
        receipt_root=tmp_path / "receipts",
    )
    result = op.run()
    assert result["ok"] is True
    assert ("type", "/reload") in input_device.calls
    assert not any(call == ("type", "/crowley agent recover") for call in input_device.calls)
    assert not any(call == ("type", "/crowley agent resume") for call in input_device.calls)


def test_terminal_pause_requires_strictly_newer_generation(tmp_path):
    manifest, _construct_scene, restore_scene = make_scenes(tmp_path)
    screen = FakeScreen(tmp_path, restore_scene, restore_scene)

    class ErrorClient(FakeClient):
        def status(self, *, deadline=None):
            return {
                "ok": True,
                "status": {
                    "state": "NATIVE_CALIBRATION",
                    "generation": self.generation,
                    "calibrationOperation": {
                        "state": "error",
                        "kind": "native",
                        "generation": self.generation,
                    },
                },
            }

        def pause(self, generation: int, *, deadline=None):
            self.calls.append({"command": "pause", "generation": generation})
            return {
                "ok": True,
                "status": {
                    "state": "PAUSED",
                    "generation": self.generation,
                    "calibrationOperation": {"state": "idle", "kind": "native"},
                    "guardian": {"armed": False},
                },
            }

    client = ErrorClient(7, [])
    candidate = operator.NativeCalibrationOperator(
        mode=operator.MODE_MEASURE_DEFERRED,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=client,
        screen=screen,
        input_device=FakeInput(screen),
    )
    candidate._calibration_started = True
    candidate._calibration_terminal_error = True
    assert candidate._pause_after_terminal_error() is False
    assert any(call["command"] == "pause" for call in client.calls)


def test_calibration_error_is_observed_before_construction_recheck(tmp_path):
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    screen = FakeScreen(tmp_path, construct_scene, restore_scene)

    class ErrorStatusClient(FakeClient):
        def calibration_status(self, *, deadline=None):
            return {
                "ok": True,
                "status": {
                    "state": "NATIVE_CALIBRATION",
                    "generation": self.generation,
                    "calibrationOperation": {
                        "kind": "native",
                        "generation": self.generation,
                        "state": "error",
                        "error": "original daemon failure",
                    },
                },
            }

        def recheck(self, *args, **kwargs):
            raise AssertionError("terminal error must precede construction recheck")

    candidate = operator.NativeCalibrationOperator(
        mode=operator.MODE_MEASURE_DEFERRED,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=ErrorStatusClient(7, []),
        screen=screen,
        input_device=FakeInput(screen),
    )
    candidate._calibration_started = True
    candidate._reservation_deadline = time.monotonic() + 5.0
    with pytest.raises(operator.OperatorError, match="original daemon failure"):
        candidate._await_calibration_terminal()
    assert candidate._calibration_terminal_error is True


def test_terminal_failure_recheck_preserves_exact_binding_before_pause(tmp_path):
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    candidate = operator.NativeCalibrationOperator(
        mode=operator.MODE_MEASURE_DEFERRED,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=FakeClient(7, []),
        screen=FakeScreen(tmp_path, construct_scene, restore_scene),
        input_device=FakeInput(FakeScreen(tmp_path, construct_scene, restore_scene)),
    )
    original = operator.ReservationBinding.from_record(FakeBinding(state="consumed").record(7), now=1.0)
    candidate._binding = original
    candidate._handshake = "running"
    candidate._state_history = [("construction_prepared", 1.0), ("running", 2.0)]
    failed_record = FakeBinding(state="restoration_required").record(7)
    reply = {
        "ok": True,
        "reservation": failed_record,
        "handshake": {
            "state": "restoration_required",
            "failure": "worker failed",
            "stateHistory": [
                {"state": "construction_prepared", "nativeClock": 1.0},
                {"state": "running", "nativeClock": 2.0},
                {"state": "restoration_required", "nativeClock": 3.0},
            ],
        },
    }
    with pytest.raises(operator.OperatorError, match="worker failed"):
        candidate._adopt_reply(reply)
    assert candidate._calibration_terminal_error is True
    assert candidate._binding == original


def test_control_preflight_runs_actual_construct_then_ordinary_recovery(tmp_path):
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    screen = FakeScreen(tmp_path, construct_scene, restore_scene)
    input_device = FakeInput(screen)
    client = FakeClient(7, [], kind="preflight")
    input_device.dispatch = client.dispatch
    commands = iter(["/crowley agent defer", "/reload"])
    op = operator.NativeCalibrationOperator(
        mode=operator.MODE_CONTROL_PREFLIGHT,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=client,
        screen=screen,
        input_device=input_device,
        ocr=lambda path: "" if "chat-closed" in path.name else "say: " + next(commands),
        receipt_root=tmp_path / "receipts",
        sleep=lambda _delay: None,
    )
    result = op.run()
    assert result["ok"] is True
    assert [value for kind, value in input_device.calls if kind == "type"] == [
        "/crowley agent defer",
        "/reload",
    ]
    assert any(kind == "click" and value == "construct" for kind, value in input_device.calls)
    assert any(call.get("command") == "recovery_begin" for call in client.calls)
    assert any(call.get("command") == "recovery_complete" for call in client.calls)


def test_recover_restore_branch_uses_actual_restore_click(tmp_path):
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    screen = FakeScreen(tmp_path, construct_scene, restore_scene)
    input_device = FakeInput(screen)
    client = FakeClient(7, [], recovery_kind="restore")
    input_device.dispatch = client.dispatch
    op = operator.NativeCalibrationOperator(
        mode=operator.MODE_RECOVER,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=client,
        screen=screen,
        input_device=input_device,
        ocr=lambda path: "" if "chat-closed" in path.name else "say: /crowley agent recover",
        receipt_root=tmp_path / "receipts",
        sleep=lambda _delay: None,
    )
    result = op.run()
    assert result["ok"] is True
    assert ("type", "/crowley agent recover") in input_device.calls
    assert any(kind == "click" and value == "restore" for kind, value in input_device.calls)


def test_handshake_skip_is_refused(tmp_path):
    manifest, _construct_scene, restore_scene = make_scenes(tmp_path)
    screen = FakeScreen(tmp_path, restore_scene, restore_scene)
    input_device = FakeInput(screen)
    client = FakeClient(7, [])
    op = operator.NativeCalibrationOperator(
        mode=operator.MODE_RECOVER,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=client,
        screen=screen,
        input_device=input_device,
        receipt_root=tmp_path / "receipts",
    )
    op.receipt.begin()
    op._binding = operator.ReservationBinding.from_record(
        FakeBinding().record(7), expected_generation=7, now=1.0
    )
    op._handshake = "construction_prepared"
    client.current_state = "baseline_bound"
    client.states = ["baseline_bound"]
    with pytest.raises(operator.OperatorError, match="skipped"):
        op._recheck()


def test_state_history_skip_is_refused_before_input(tmp_path):
    manifest, _construct_scene, restore_scene = make_scenes(tmp_path)
    screen = FakeScreen(tmp_path, restore_scene, restore_scene)
    op = operator.NativeCalibrationOperator(
        mode=operator.MODE_MEASURE_DEFERRED,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=FakeClient(7, []),
        screen=screen,
        input_device=FakeInput(screen),
        receipt_root=tmp_path / "receipts",
    )
    op.receipt.begin()
    reply = FakeClient(7, []).prepare(7)
    reply["handshake"] = {
        "state": "baseline_bound",
        "stateHistory": [
            {"state": "construction_prepared", "nativeClock": 1.0},
            {"state": "baseline_bound", "nativeClock": 2.0},
        ],
    }
    with pytest.raises(operator.OperatorError, match="skipped"):
        op._adopt_reply(reply)
    op.input.close()


def test_owned_emitter_gate_and_release_subprocess(tmp_path):
    log = tmp_path / "events.log"
    script = tmp_path / "pinned-emitter"
    script.write_text(f"#!/bin/sh\nprintf '%s\n' \"$*\" >> {log}\n")
    script.chmod(0o700)
    fd = os.open(script, os.O_RDONLY)

    class Tool:
        proc_path = f"/proc/self/fd/{fd}"

        class Image:
            pass

        image = Image()
        image.fd = fd

    emitter = operator.OwnedEmitter(Tool(), context=multiprocessing.get_context("fork"))
    try:
        emitter.start()
        assert emitter.pgid and emitter.pgid > 0
        emitter.press()
        emitter.release()
    finally:
        emitter.abort()
        os.close(fd)
    assert log.read_text().splitlines() == ["mousedown 1", "mouseup 1"]


def test_owned_emitter_gate_eof_is_bounded(tmp_path):
    script = tmp_path / "pinned-emitter"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o700)
    fd = os.open(script, os.O_RDONLY)

    class Tool:
        proc_path = f"/proc/self/fd/{fd}"

        class Image:
            pass

        image = Image()
        image.fd = fd

    emitter = operator.OwnedEmitter(Tool(), context=multiprocessing.get_context("fork"))
    try:
        emitter.start()
        os.close(emitter._gate_write)
        emitter._gate_write = -1
        with pytest.raises((EOFError, TimeoutError, operator.OperatorError)):
            emitter.press()
    finally:
        emitter.abort()
        os.close(fd)


def test_spawned_sealed_emitter_uses_real_pinned_image_and_acknowledges_release():
    tool = operator.PinnedInputTool.load()
    emitter = operator.OwnedEmitter(
        tool,
        action=("--help",),
        release_action=(),
        environment={},
    )
    try:
        emitter.start()
        assert emitter.pgid and emitter.pgid > 0
        emitter.press()
        emitter.release()
        assert emitter._process is not None
        assert not emitter._process.is_alive()
    finally:
        emitter.abort()
        tool.close()


def test_spawned_watchdog_entry_acknowledges_owned_state_and_empty_clear():
    tool = operator.PinnedInputTool.load()
    watchdog = operator.Watchdog(tool, interval=0.02, environment={})
    try:
        watchdog.publish(groups=set(), buttons=set(), keys={"Return"})
        watchdog.clear()
        assert watchdog._process.is_alive()
    finally:
        watchdog.close()
        tool.close()
    assert not watchdog._process.is_alive()


def test_watchdog_and_cancellation_actor_have_independent_sessions():
    tool = operator.PinnedInputTool.load()
    watchdog = operator.Watchdog(tool, interval=0.02, environment={})
    actor = operator.CancellationActor(
        Path("/tmp/native-calibration-unused.sock"),
        generation=7,
        reservation_id="session-check",
        deadline=time.monotonic() + 8.0,
        owner_pid=os.getpid(),
        owner_start=operator._proc_start(os.getpid()),
    )
    actor.start()
    try:
        assert watchdog._process is not None and watchdog._process.pid is not None
        assert actor._process is not None and actor._process.pid is not None
        assert os.getsid(watchdog._process.pid) == watchdog._process.pid
        assert os.getsid(actor._process.pid) == actor._process.pid
    finally:
        actor.close()
        watchdog.close()
        tool.close()


def test_spawned_watchdog_ack_loss_fails_closed_and_retains_actor():
    tool = operator.PinnedInputTool.load()
    watchdog = operator.Watchdog(tool, interval=0.02, environment={})
    try:
        os.close(watchdog._ack_read)
        watchdog._ack_read = -1
        with pytest.raises(operator.OperatorError, match="acknowledgement"):
            watchdog.publish(groups=set(), buttons=set(), keys=set())
        assert watchdog._process.is_alive()
    finally:
        watchdog.close()
        tool.close()


def test_unconfirmed_release_retains_actor_and_owner_close_is_bounded(tmp_path):
    artifact = make_recording_artifact(tmp_path)
    from crowley.session.input_tool import PRIVATE_TOOL_BASENAME

    executable = artifact / PRIVATE_TOOL_BASENAME
    delayed_source = tmp_path / "delayed.c"
    delayed_binary = tmp_path / "delayed"
    release_marker = tmp_path / "release-first-attempt"
    release_log = tmp_path / "release-log"
    delayed_source.write_text(
        """
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(int argc, char **argv) {
    const char *marker = getenv("CROWLEY_RELEASE_MARKER");
    const char *log = getenv("CROWLEY_RELEASE_LOG");
    if (argc > 1 && (argv[1][0] == 'k' || argv[1][0] == 'm') && marker && access(marker, F_OK) != 0) {
        int fd = open(marker, O_WRONLY | O_CREAT | O_EXCL, 0600);
        if (fd >= 0) close(fd);
        usleep(4000000);
        return 1;
    }
    if (argc > 1 && (argv[1][0] == 'k' || argv[1][0] == 'm') && marker && access(marker, F_OK) == 0)
        usleep(2000000);
    if (argc > 1 && log) {
        int fd = open(log, O_WRONLY | O_CREAT | O_APPEND, 0600);
        if (fd >= 0) {
            write(fd, argv[1], strlen(argv[1]));
            write(fd, "\\n", 1);
            close(fd);
        }
    }
    return 0;
}
""",
        encoding="utf-8",
    )
    subprocess.run(["cc", "-O2", str(delayed_source), "-o", str(delayed_binary)], check=True)
    executable.unlink()
    shutil.copyfile(delayed_binary, executable)
    executable.chmod(0o700)
    manifest = artifact / "manifest.json"
    record = json.loads(manifest.read_text(encoding="utf-8"))
    record["executable_sha256"] = hashlib.sha256(executable.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
    tool = operator.PinnedInputTool.from_root(artifact)
    watchdog = operator.Watchdog(
        tool,
        interval=0.02,
        environment={
            "CROWLEY_RELEASE_MARKER": str(release_marker),
            "CROWLEY_RELEASE_LOG": str(release_log),
        },
    )
    try:
        watchdog.publish(groups=set(), buttons=set(), keys={"Return"})
        started = time.monotonic()
        with pytest.raises(operator.OperatorError, match="confirm release"):
            watchdog.close()
        assert time.monotonic() - started < 4.5
        assert watchdog._process.is_alive()
        deadline = time.monotonic() + 8.0
        while watchdog._process.is_alive() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert not watchdog._process.is_alive()
        assert release_marker.is_file()
        assert release_log.read_text(encoding="utf-8") == "keyup\n"
    finally:
        try:
            watchdog.close()
        except Exception:
            pass
        tool.close()


def test_real_owner_exit_is_bounded_while_failed_release_actor_survives(tmp_path):
    artifact = make_recording_artifact(tmp_path)
    from crowley.session.input_tool import PRIVATE_TOOL_BASENAME

    executable = artifact / PRIVATE_TOOL_BASENAME
    source = tmp_path / "persistent-release.c"
    binary = tmp_path / "persistent-release"
    source.write_text(
        """
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(int argc, char **argv) {
    const char *enable = getenv("CROWLEY_RELEASE_ENABLE");
    const char *log = getenv("CROWLEY_RECORDER");
    if (argc > 1 && strcmp(argv[1], "keyup") == 0 && (!enable || access(enable, F_OK) != 0)) {
        usleep(5000000);
        return 1;
    }
    if (argc > 1 && log) {
        int fd = open(log, O_WRONLY | O_CREAT | O_APPEND, 0600);
        if (fd >= 0) {
            write(fd, argv[1], strlen(argv[1]));
            write(fd, "\\n", 1);
            close(fd);
        }
    }
    return 0;
}
""",
        encoding="utf-8",
    )
    subprocess.run(["cc", "-O2", str(source), "-o", str(binary)], check=True)
    executable.unlink()
    shutil.copyfile(binary, executable)
    executable.chmod(0o700)
    manifest = artifact / "manifest.json"
    record = json.loads(manifest.read_text(encoding="utf-8"))
    record["executable_sha256"] = hashlib.sha256(executable.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")

    release_marker = tmp_path / "persistent-release-actions"
    enable_marker = tmp_path / "enable-release"
    status_read, status_write = multiprocessing.get_context("spawn").Pipe(duplex=False)
    owner = multiprocessing.get_context("spawn").Process(
        target=_persistent_release_owner_fixture,
        args=(str(artifact), str(release_marker), str(enable_marker), status_write),
        name="native-calibration-persistent-release-owner",
        daemon=False,
    )
    owner.start()
    status_write.close()
    watchdog_pid = watchdog_start = None
    try:
        assert status_read.poll(5.0), "persistent-release owner did not publish ownership"
        watchdog_pid, watchdog_start = status_read.recv()
        kill_started = time.monotonic()
        owner.kill()
        owner.join(timeout=5.0)
        assert not owner.is_alive()
        assert owner.exitcode == -operator.signal.SIGKILL
        assert time.monotonic() - kill_started < 5.0
        assert watchdog_pid and watchdog_start
        time.sleep(0.5)
        assert not _wait_pid_identity_exit(watchdog_pid, watchdog_start, 0.0)
        enable_marker.touch(mode=0o600)
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            if release_marker.exists() and release_marker.read_text(encoding="utf-8").splitlines() == [
                "keyup"
            ]:
                break
            time.sleep(0.05)
        assert release_marker.read_text(encoding="utf-8").splitlines() == ["keyup"]
        assert _wait_pid_identity_exit(watchdog_pid, watchdog_start, 5.0)
    finally:
        if owner.is_alive():
            owner.kill()
        owner.join(timeout=2.0)
        status_read.close()


def test_normal_systemexit_keeps_failed_release_actor_alive_until_enabled(tmp_path):
    artifact = make_recording_artifact(tmp_path)
    from crowley.session.input_tool import PRIVATE_TOOL_BASENAME

    executable = artifact / PRIVATE_TOOL_BASENAME
    source = tmp_path / "normal-exit-release.c"
    binary = tmp_path / "normal-exit-release"
    source.write_text(
        """
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(int argc, char **argv) {
    const char *enable = getenv("CROWLEY_RELEASE_ENABLE");
    const char *marker = getenv("CROWLEY_RELEASE_MARKER");
    if (argc > 1 && strcmp(argv[1], "keyup") == 0) {
        for (int i = 0; i < 120 && (!enable || access(enable, F_OK) != 0); ++i)
            usleep(50000);
        if (!enable || access(enable, F_OK) != 0) return 1;
    }
    if (argc > 1 && marker) {
        int fd = open(marker, O_WRONLY | O_CREAT | O_APPEND, 0600);
        if (fd >= 0) { write(fd, argv[1], strlen(argv[1])); write(fd, "\\n", 1); close(fd); }
    }
    return 0;
}
""",
        encoding="utf-8",
    )
    subprocess.run(["cc", "-O2", str(source), "-o", str(binary)], check=True)
    executable.unlink()
    shutil.copyfile(binary, executable)
    executable.chmod(0o700)
    manifest = artifact / "manifest.json"
    record = json.loads(manifest.read_text(encoding="utf-8"))
    record["executable_sha256"] = hashlib.sha256(executable.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")

    release_marker = tmp_path / "normal-exit-release-actions"
    enable_marker = tmp_path / "normal-exit-enable"
    context = multiprocessing.get_context("spawn")
    status_read, status_write = context.Pipe(duplex=False)
    owner = context.Process(
        target=_normal_exit_failed_release_fixture,
        args=(str(artifact), str(release_marker), str(enable_marker), status_write),
        name="native-calibration-normal-systemexit-owner",
        daemon=False,
    )
    owner.start()
    status_write.close()
    try:
        assert status_read.poll(5.0), "normal SystemExit owner did not publish actor"
        watchdog_pid, watchdog_start = status_read.recv()
        owner.join(timeout=5.0)
        assert not owner.is_alive()
        assert owner.exitcode == 2
        assert watchdog_pid and watchdog_start
        assert not _wait_pid_identity_exit(watchdog_pid, watchdog_start, 0.0)
        enable_marker.touch(mode=0o600)
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            if release_marker.exists() and release_marker.read_text(encoding="utf-8").splitlines() == [
                "keyup"
            ]:
                break
            time.sleep(0.05)
        assert release_marker.read_text(encoding="utf-8").splitlines() == ["keyup"]
        assert _wait_pid_identity_exit(watchdog_pid, watchdog_start, 5.0)
    finally:
        if owner.is_alive():
            owner.kill()
        owner.join(timeout=2.0)
        status_read.close()


@pytest.mark.parametrize(
    "signum",
    [operator.signal.SIGTERM, operator.signal.SIGHUP, operator.signal.SIGINT, operator.signal.SIGKILL],
)
def test_spawned_emitter_group_death_is_observed_before_press(signum):
    tool = operator.PinnedInputTool.load()
    emitter = operator.OwnedEmitter(
        tool,
        action=("--help",),
        release_action=(),
        environment={},
    )
    try:
        emitter.start()
        assert emitter.pgid and emitter.pgid > 0
        os.killpg(emitter.pgid, signum)
        with pytest.raises(operator.OperatorError, match="press acknowledgement"):
            emitter.press()
    finally:
        emitter.abort()
        tool.close()


def test_spawned_emitter_gate_eof_with_real_sealed_image_is_bounded():
    tool = operator.PinnedInputTool.load()
    emitter = operator.OwnedEmitter(tool, action=("--help",), release_action=(), environment={})
    try:
        emitter.start()
        os.close(emitter._gate_write)
        with pytest.raises(operator.OperatorError, match="press acknowledgement"):
            emitter.press()
    finally:
        emitter.abort()
        tool.close()


def test_spawned_emitter_abort_reaps_late_child():
    tool = operator.PinnedInputTool.load()
    emitter = operator.OwnedEmitter(tool, action=("--help",), release_action=(), environment={})
    try:
        emitter.start()
        process = emitter._process
        assert process is not None and process.is_alive()
        emitter.abort()
        assert not process.is_alive()
    finally:
        emitter.abort()
        tool.close()


def test_spawned_owner_kill_during_confirmed_key_hold_releases_exact_action(tmp_path):
    source = tmp_path / "recorder.c"
    executable = tmp_path / "recorder"
    source.write_text(
        """
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int main(int argc, char **argv) {
    const char *path = getenv("CROWLEY_RECORDER");
    if (path == NULL || argc < 3) return 2;
    int fd = open(path, O_WRONLY | O_CREAT | O_APPEND, 0600);
    if (fd < 0) return 3;
    dprintf(fd, "%s %s\\n", argv[1], argv[2]);
    close(fd);
    return 0;
}
""",
        encoding="utf-8",
    )
    subprocess.run(["cc", "-O2", str(source), "-o", str(executable)], check=True)
    from crowley.session.input_tool import (
        ARCHIVE_BASENAME,
        MANIFEST_BASENAME,
        PINNED_ARCHIVE_SHA256,
        PINNED_COMMIT,
        PRIVATE_TOOL_BASENAME,
    )

    artifact = tmp_path / "sealed-tool"
    artifact.mkdir(mode=0o700)
    shutil.copyfile(executable, artifact / PRIVATE_TOOL_BASENAME)
    shutil.copyfile(
        MODULE_PATH.parents[1] / "vendor" / "xdotool-source.tar.gz",
        artifact / ARCHIVE_BASENAME,
    )
    executable_sha256 = hashlib.sha256((artifact / PRIVATE_TOOL_BASENAME).read_bytes()).hexdigest()
    (artifact / MANIFEST_BASENAME).write_text(
        json.dumps(
            {
                "commit": PINNED_COMMIT,
                "archive_sha256": PINNED_ARCHIVE_SHA256,
                "executable": PRIVATE_TOOL_BASENAME,
                "executable_sha256": executable_sha256,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (artifact / PRIVATE_TOOL_BASENAME).chmod(0o700)
    (artifact / ARCHIVE_BASENAME).chmod(0o600)
    (artifact / MANIFEST_BASENAME).chmod(0o600)

    marker = tmp_path / "released-actions"
    tool = operator.PinnedInputTool.from_root(artifact)
    watchdog = operator.Watchdog(tool, interval=0.02, environment={"CROWLEY_RECORDER": str(marker)})
    emitter = operator.OwnedEmitter(
        tool,
        action=("keydown", "Return"),
        release_action=("keyup", "Return"),
        environment={"CROWLEY_RECORDER": str(marker)},
    )
    try:
        emitter.start()
        assert emitter.pgid and emitter.pgid > 0
        watchdog.publish(groups={emitter.pgid}, buttons=set(), keys={"Return"})
        emitter.press()
        process = emitter._process
        assert process is not None and process.is_alive()
        os.killpg(emitter.pgid, operator.signal.SIGKILL)
        emitter.abort()
        watchdog.close()
        assert not process.is_alive()
        assert marker.read_text(encoding="utf-8").splitlines() == [
            "keydown Return",
            "keyup Return",
        ]
    finally:
        emitter.abort()
        try:
            watchdog.close()
        except Exception:
            pass
        tool.close()


@pytest.mark.parametrize(
    ("action", "release", "expected"),
    [
        (("keydown", "Return"), ("keyup", "Return"), "keydown Return\nkeyup Return"),
        (("mousedown", "1"), ("mouseup", "1"), "mousedown 1\nmouseup 1"),
    ],
)
def test_actual_helper_owner_sigkill_releases_key_or_button_via_independent_watchdog(
    tmp_path, action, release, expected
):
    artifact = make_recording_artifact(tmp_path)
    marker = tmp_path / "owner-release-actions"
    context = multiprocessing.get_context("spawn")
    status_read, status_write = multiprocessing.Pipe(duplex=False)
    owner = context.Process(
        target=_owner_hold_fixture,
        args=(str(artifact), str(marker), action, release, status_write),
        name="native-calibration-owner-fixture",
        daemon=False,
    )
    owner.start()
    status_write.close()
    watchdog_pid = None
    watchdog_start = None
    emitter_pgid = None
    try:
        assert status_read.poll(5.0), "owner fixture did not publish confirmed hold"
        watchdog_pid, watchdog_start, emitter_pgid = status_read.recv()
        assert owner.is_alive()
        kill_started = time.monotonic()
        owner.kill()
        owner.join(timeout=5.0)
        assert not owner.is_alive()
        assert owner.exitcode == -operator.signal.SIGKILL
        assert time.monotonic() - kill_started < 5.0
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if marker.exists() and marker.read_text(encoding="utf-8").splitlines() == expected.splitlines():
                break
            time.sleep(0.05)
        assert marker.read_text(encoding="utf-8").splitlines() == expected.splitlines()
        assert emitter_pgid and emitter_pgid > 0
        with pytest.raises(ProcessLookupError):
            os.killpg(emitter_pgid, 0)
        assert watchdog_pid and watchdog_pid > 0
        assert watchdog_start
        assert _wait_pid_identity_exit(watchdog_pid, watchdog_start, 5.0)
    finally:
        if owner.is_alive():
            owner.kill()
        owner.join(timeout=2.0)
        status_read.close()


def test_production_main_lifetime_arms_release_and_cancel_for_button_hold(tmp_path):
    manifest, construct_scene, _restore_scene = make_scenes(tmp_path)
    templates_path = tmp_path / "main-templates.json"
    templates_path.write_text(
        json.dumps(
            {
                "construct": {
                    "path": str(manifest.construct.path),
                    "sha256": manifest.construct.sha256,
                    "threshold": 5.0,
                },
                "restore": {
                    "path": str(manifest.restore.path),
                    "sha256": manifest.restore.sha256,
                    "threshold": 5.0,
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    templates_path.chmod(0o600)
    config_path = tmp_path / "main-config.toml"
    config_path.write_text("test-only", encoding="utf-8")
    config_path.chmod(0o600)
    artifact = make_recording_artifact(tmp_path)
    release_marker = tmp_path / "main-release-actions"
    gate_marker = tmp_path / "main-button-gate"
    error_path = tmp_path / "main-error"
    socket_path = tmp_path / "main-session.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(1)
    received: list[dict] = []

    def serve_once():
        connection, _address = listener.accept()
        with connection:
            chunks = []
            while True:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            received.append(json.loads(b"".join(chunks).decode("utf-8")))
            connection.sendall(b'{"ok":true}\n')

    import threading

    server_thread = threading.Thread(target=serve_once, daemon=True)
    server_thread.start()
    context = multiprocessing.get_context("spawn")
    owner = context.Process(
        target=_production_main_owner_fixture,
        args=(
            str(artifact),
            str(release_marker),
            str(gate_marker),
            str(socket_path),
            str(construct_scene),
            str(config_path),
            str(templates_path),
            str(error_path),
        ),
        name="native-calibration-production-main-owner",
        daemon=False,
    )
    owner.start()
    try:
        deadline = time.monotonic() + 8.0
        while not gate_marker.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert gate_marker.exists(), (
            error_path.read_text(encoding="utf-8")
            if error_path.exists()
            else "production main did not reach acknowledged button hold"
        )
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            if (
                release_marker.exists()
                and "mousedown 1" in release_marker.read_text(encoding="utf-8").splitlines()
            ):
                break
            time.sleep(0.05)
        assert "mousedown 1" in release_marker.read_text(encoding="utf-8").splitlines()
        owner.kill()
        server_thread.join(timeout=8.0)
        assert not server_thread.is_alive()
        owner.join(timeout=5.0)
        assert not owner.is_alive()
        assert owner.exitcode == -operator.signal.SIGKILL
        assert received == [
            {
                "command": "native_construction_recovery_cancel",
                "generation": 7,
                "reservationId": "reservation-1",
            }
        ]
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            if release_marker.exists() and release_marker.read_text(encoding="utf-8").splitlines()[-1:] == [
                "mouseup 1"
            ]:
                break
            time.sleep(0.05)
        lines = release_marker.read_text(encoding="utf-8").splitlines()
        assert "mousedown 1" in lines
        assert lines[-1] == "mouseup 1"
    finally:
        if owner.is_alive():
            owner.kill()
        owner.join(timeout=2.0)
        listener.close()


def test_production_main_handled_term_returns_nonzero_and_retains_release_actor(tmp_path):
    manifest, construct_scene, _restore_scene = make_scenes(tmp_path)
    templates_path = tmp_path / "main-term-templates.json"
    templates_path.write_text(
        json.dumps(
            {
                "construct": {
                    "path": str(manifest.construct.path),
                    "sha256": manifest.construct.sha256,
                    "threshold": 5.0,
                },
                "restore": {
                    "path": str(manifest.restore.path),
                    "sha256": manifest.restore.sha256,
                    "threshold": 5.0,
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    templates_path.chmod(0o600)
    config_path = tmp_path / "main-term-config.toml"
    config_path.write_text("test-only", encoding="utf-8")
    config_path.chmod(0o600)
    artifact = make_recording_artifact(tmp_path)
    from crowley.session.input_tool import PRIVATE_TOOL_BASENAME

    executable = artifact / PRIVATE_TOOL_BASENAME
    source = tmp_path / "term-release.c"
    binary = tmp_path / "term-release"
    source.write_text(
        """
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(int argc, char **argv) {
    const char *enable = getenv("CROWLEY_RELEASE_ENABLE");
    const char *marker = getenv("CROWLEY_RECORDER");
    if (argc > 1 && strcmp(argv[1], "mouseup") == 0) {
        for (int i = 0; i < 120 && (!enable || access(enable, F_OK) != 0); ++i)
            usleep(50000);
        if (!enable || access(enable, F_OK) != 0) return 1;
    }
    if (argc > 1 && marker) {
        int fd = open(marker, O_WRONLY | O_CREAT | O_APPEND, 0600);
        if (fd >= 0) { write(fd, argv[1], strlen(argv[1])); write(fd, "\\n", 1); close(fd); }
    }
    return 0;
}
""",
        encoding="utf-8",
    )
    subprocess.run(["cc", "-O2", str(source), "-o", str(binary)], check=True)
    executable.unlink()
    shutil.copyfile(binary, executable)
    executable.chmod(0o700)
    record = json.loads((artifact / "manifest.json").read_text(encoding="utf-8"))
    record["executable_sha256"] = hashlib.sha256(executable.read_bytes()).hexdigest()
    (artifact / "manifest.json").write_text(json.dumps(record, sort_keys=True), encoding="utf-8")

    release_marker = tmp_path / "main-term-release-actions"
    enable_marker = tmp_path / "main-term-enable-release"
    gate_marker = tmp_path / "main-term-button-gate"
    error_path = tmp_path / "main-term-error"
    socket_path = tmp_path / "main-term-session.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(1)
    received: list[dict] = []

    def serve_once():
        connection, _address = listener.accept()
        with connection:
            chunks = []
            while True:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            received.append(json.loads(b"".join(chunks).decode("utf-8")))
            connection.sendall(b'{"ok":true}\n')

    import threading

    server_thread = threading.Thread(target=serve_once, daemon=True)
    server_thread.start()
    context = multiprocessing.get_context("spawn")
    owner = context.Process(
        target=_production_main_owner_fixture,
        args=(
            str(artifact),
            str(release_marker),
            str(gate_marker),
            str(socket_path),
            str(construct_scene),
            str(config_path),
            str(templates_path),
            str(error_path),
            str(enable_marker),
        ),
        name="native-calibration-production-main-term-owner",
        daemon=False,
    )
    owner.start()
    try:
        deadline = time.monotonic() + 8.0
        while not gate_marker.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert gate_marker.exists(), (
            error_path.read_text(encoding="utf-8") if error_path.exists() else "no button gate"
        )
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            if (
                release_marker.exists()
                and "mousedown" in release_marker.read_text(encoding="utf-8").splitlines()
            ):
                break
            time.sleep(0.05)
        assert "mousedown" in release_marker.read_text(encoding="utf-8").splitlines()
        started = time.monotonic()
        os.kill(owner.pid, operator.signal.SIGTERM)
        time.sleep(0.15)
        if owner.is_alive():
            os.kill(owner.pid, operator.signal.SIGINT)
            os.kill(owner.pid, operator.signal.SIGHUP)
        owner.join(timeout=8.0)
        assert not owner.is_alive()
        assert owner.exitcode == 2
        assert time.monotonic() - started < 8.0
        server_thread.join(timeout=8.0)
        assert not server_thread.is_alive()
        assert received == [
            {
                "command": "native_construction_recovery_cancel",
                "generation": 7,
                "reservationId": "reservation-1",
            }
        ]
        enable_marker.touch(mode=0o600)
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            if release_marker.exists() and release_marker.read_text(encoding="utf-8").splitlines()[-1:] == [
                "mouseup"
            ]:
                break
            time.sleep(0.05)
        assert release_marker.read_text(encoding="utf-8").splitlines()[-1:] == ["mouseup"]
    finally:
        if owner.is_alive():
            owner.kill()
        owner.join(timeout=2.0)
        listener.close()


def test_actual_cancellation_actor_sends_exact_admitted_ipc_after_owner_sigkill(tmp_path):
    socket_path = tmp_path / "session.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(1)
    received: list[dict] = []

    def serve_once():
        connection, _address = listener.accept()
        with connection:
            chunks = []
            while True:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            received.append(json.loads(b"".join(chunks).decode("utf-8")))
            connection.sendall(b'{"ok":true}\n')

    import threading

    server_thread = threading.Thread(target=serve_once, daemon=True)
    server_thread.start()
    context = multiprocessing.get_context("spawn")
    status_read, status_write = context.Pipe(duplex=False)
    owner = context.Process(
        target=_cancellation_owner_fixture,
        args=(str(socket_path), status_write),
        name="native-calibration-cancellation-owner-fixture",
    )
    owner.start()
    status_write.close()
    try:
        assert status_read.poll(5.0), "cancellation owner did not start its actor"
        actor_pid = status_read.recv()
        assert actor_pid and actor_pid > 0
        kill_started = time.monotonic()
        owner.kill()
        server_thread.join(timeout=5.0)
        assert not server_thread.is_alive()
        assert time.monotonic() - kill_started < 5.0
        assert received == [
            {
                "command": "native_construction_recovery_cancel",
                "generation": 17,
                "reservationId": "reservation-live",
            }
        ]
        owner.join(timeout=5.0)
        assert not owner.is_alive()
    finally:
        if owner.is_alive():
            owner.kill()
        owner.join(timeout=2.0)
        status_read.close()
        listener.close()


def test_actor_owns_prepare_bootstrap_finalize_recheck_cancel_via_peer_credentials(tmp_path):
    socket_path = tmp_path / "admission.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(8)
    owner_pid = os.getpid()
    owner_start = operator._proc_start(owner_pid)
    actor_pid: int | None = None
    seen: list[tuple[dict, int]] = []
    replies = [
        _admission_reply(
            owner_pid=owner_pid,
            owner_start=owner_start,
            generation=31,
            reservation_id="measure-31",
            kind="measure",
            state="prepared",
            handshake_state="construction_prepared",
            history=["construction_prepared"],
        ),
        _admission_reply(
            owner_pid=owner_pid,
            owner_start=owner_start,
            generation=31,
            reservation_id="measure-31",
            kind="measure",
            state="consumed",
            handshake_state="running",
            history=["construction_prepared", "running"],
            expiry=time.monotonic() + 3130.0,
        ),
        _admission_reply(
            owner_pid=owner_pid,
            owner_start=owner_start,
            generation=31,
            reservation_id="measure-31",
            kind="measure",
            state="consumed",
            handshake_state="finalize_required",
            history=[
                "construction_prepared",
                "running",
                "construction_reset_archived",
                "baseline_bound",
                "construction_released",
                "hold_required",
                "updates_reset_archived",
                "measure_ready",
                "resume_required",
                "resume_ready",
                "finalize_required",
            ],
            expiry=time.monotonic() + 3130.0,
        ),
        _admission_reply(
            owner_pid=owner_pid,
            owner_start=owner_start,
            generation=31,
            reservation_id="measure-31",
            kind="measure",
            state="consumed",
            handshake_state="finalize_required",
            history=[
                "construction_prepared",
                "running",
                "construction_reset_archived",
                "baseline_bound",
                "construction_released",
                "hold_required",
                "updates_reset_archived",
                "measure_ready",
                "resume_required",
                "resume_ready",
                "finalize_required",
            ],
            expiry=time.monotonic() + 3130.0,
        ),
        _admission_reply(
            owner_pid=owner_pid,
            owner_start=owner_start,
            generation=31,
            reservation_id="measure-31",
            kind="measure",
            state="cancelled",
            handshake_state="cancelled",
            history=[
                "construction_prepared",
                "running",
                "construction_reset_archived",
                "baseline_bound",
                "construction_released",
                "hold_required",
                "updates_reset_archived",
                "measure_ready",
                "resume_required",
                "resume_ready",
                "finalize_required",
                "cancelled",
            ],
            expiry=time.monotonic() + 3130.0,
        ),
    ]

    def serve():
        try:
            for response in replies:
                connection, _address = listener.accept()
                with connection:
                    peer = _peer_pid(connection)
                    raw = bytearray()
                    while True:
                        chunk = connection.recv(4096)
                        if not chunk:
                            break
                        raw.extend(chunk)
                    seen.append((json.loads(bytes(raw).decode("utf-8")), peer))
                    connection.sendall((json.dumps(response, separators=(",", ":")) + "\n").encode())
        finally:
            listener.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    actor = operator.CancellationActor(
        socket_path,
        generation=31,
        reservation_id="",
        deadline=time.monotonic() + 20.0,
        owner_pid=owner_pid,
        owner_start=owner_start,
    )
    actor.start()
    actor_pid = actor._process.pid if actor._process is not None else None
    assert actor_pid and actor_pid != owner_pid
    try:
        prepared = actor.call("prepare", generation=31, preflight=False, deadline=time.monotonic() + 10.0)
        assert prepared["reservation"]["reservationId"] == "measure-31"
        actor.call(
            "bootstrap",
            generation=31,
            reservation_id="measure-31",
            expected_constructor_boot="native-construction:boot-31",
            deadline=actor.deadline,
        )
        assert actor.deadline - time.monotonic() > 3000.0
        actor.call("finalize", generation=31, reservation_id="measure-31", deadline=actor.deadline)
        actor.call("recheck", generation=31, reservation_id="measure-31", deadline=actor.deadline)
        cancelled = actor.call("cancel", generation=31, reservation_id="measure-31", deadline=actor.deadline)
        assert cancelled["reservation"]["reservationState"] == "cancelled"
    finally:
        actor.close()
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert len(seen) == 5
    assert {peer for _request, peer in seen} == {actor_pid}
    assert all(peer != owner_pid for _request, peer in seen)
    assert [request["command"] for request, _peer in seen] == [
        "native_construction_prepare",
        "native_construction_bootstrap",
        "native_construction_finalize_admit",
        "native_construction_recheck",
        "native_construction_recovery_cancel",
    ]
    print(f"actor_pid={actor_pid} owner_pid={owner_pid} peer_pids={[peer for _request, peer in seen]}")


def test_actor_owns_recovery_begin_and_complete_with_new_canonical_id(tmp_path):
    socket_path = tmp_path / "recovery-admission.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(4)
    owner_pid = os.getpid()
    owner_start = operator._proc_start(owner_pid)
    seen: list[tuple[dict, int]] = []
    preflight = _admission_reply(
        owner_pid=owner_pid,
        owner_start=owner_start,
        generation=31,
        reservation_id="preflight-31",
        kind="preflight",
        state="prepared",
        handshake_state="construction_prepared",
        history=["construction_prepared"],
    )
    recovery_begin = _admission_reply(
        owner_pid=owner_pid,
        owner_start=owner_start,
        generation=32,
        reservation_id="recovery-31",
        kind="recovery",
        state="recovery",
        handshake_state="recovery_required",
        history=["recovery_required"],
        expiry=time.monotonic() + 600.0,
        guardian_generation=5,
    )
    recovery_begin["handshake"]["recoveryKind"] = "restore"
    recovery_complete = _admission_reply(
        owner_pid=owner_pid,
        owner_start=owner_start,
        generation=32,
        reservation_id="recovery-31",
        kind="recovery",
        state="recovered",
        handshake_state="recovered",
        history=["recovery_required", "recovered"],
        expiry=time.monotonic() + 600.0,
        guardian_generation=5,
    )
    recovery_complete["handshake"]["recoveryKind"] = "restore"

    def serve():
        try:
            for response in (preflight, recovery_begin, recovery_complete):
                connection, _address = listener.accept()
                with connection:
                    peer = _peer_pid(connection)
                    raw = bytearray()
                    while True:
                        chunk = connection.recv(4096)
                        if not chunk:
                            break
                        raw.extend(chunk)
                    seen.append((json.loads(bytes(raw).decode("utf-8")), peer))
                    connection.sendall((json.dumps(response, separators=(",", ":")) + "\n").encode())
        finally:
            listener.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    actor = operator.CancellationActor(
        socket_path,
        generation=31,
        reservation_id="",
        deadline=time.monotonic() + 20.0,
        owner_pid=owner_pid,
        owner_start=owner_start,
    )
    actor.start()
    actor_pid = actor._process.pid if actor._process is not None else None
    assert actor_pid and actor_pid != owner_pid
    try:
        actor.call("prepare", generation=31, preflight=True, deadline=time.monotonic() + 10.0)
        completed = actor.call(
            "recovery_begin",
            generation=32,
            reservation_id="",
            deadline=actor.deadline,
        )
        assert completed["reservation"]["reservationId"] == "recovery-31"
        assert actor.reservation_id == "recovery-31"
        terminal = actor.call(
            "recovery_complete",
            generation=32,
            reservation_id="recovery-31",
            deadline=actor.deadline,
        )
        assert terminal["reservation"]["reservationState"] == "recovered"
    finally:
        actor.close()
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert len(seen) == 3
    assert {peer for _request, peer in seen} == {actor_pid}
    assert all(peer != owner_pid for _request, peer in seen)
    assert [request["command"] for request, _peer in seen] == [
        "native_construction_control_preflight",
        "native_construction_recovery_begin",
        "native_construction_recovery_complete",
    ]
    assert seen[1][0]["reservationId"] == ""
    print(f"recovery_actor_pid={actor_pid} owner_pid={owner_pid} peer_pids={[peer for _r, peer in seen]}")


def test_native_operator_routes_real_daemon_client_prepare_through_actor(tmp_path):
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    socket_path = tmp_path / "operator-admission.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(2)
    owner_pid = os.getpid()
    seen: list[tuple[dict, int]] = []
    response = _admission_reply(
        # The daemon's canonical leased owner is distinct from this helper;
        # actor peer ownership is proved independently below.
        owner_pid=4242,
        owner_start="daemon-start-31",
        generation=31,
        reservation_id="operator-measure-31",
        kind="measure",
        state="prepared",
        handshake_state="construction_prepared",
        history=["construction_prepared"],
    )

    def serve():
        try:
            connection, _address = listener.accept()
            with connection:
                peer = _peer_pid(connection)
                raw = bytearray()
                while True:
                    chunk = connection.recv(4096)
                    if not chunk:
                        break
                    raw.extend(chunk)
                seen.append((json.loads(bytes(raw).decode("utf-8")), peer))
                connection.sendall((json.dumps(response, separators=(",", ":")) + "\n").encode())
        finally:
            listener.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    client = operator.DaemonClient(socket_path, timeout=10.0)
    screen = FakeScreen(tmp_path, construct_scene, restore_scene)
    input_device = FakeInput(screen)
    candidate = operator.NativeCalibrationOperator(
        mode=operator.MODE_MEASURE_DEFERRED,
        generation=31,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=client,
        screen=screen,
        input_device=input_device,
        receipt_root=tmp_path / "receipts",
    )
    candidate.receipt.begin()
    try:
        binding = candidate._prepare(preflight=False)
        assert binding.reservation_id == "operator-measure-31"
        assert input_device.calls == []
        actor = candidate._cancellation_actor
        assert actor is not None and actor._process is not None
        actor_pid = actor._process.pid
        assert actor_pid != owner_pid
    finally:
        candidate._stop_cancellation_actor()
        input_device.close()
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert len(seen) == 1
    assert seen[0][0] == {"command": "native_construction_prepare", "generation": 31}
    assert seen[0][1] == actor_pid
    assert seen[0][1] != owner_pid
    print(f"operator_prepare_actor_pid={actor_pid} owner_pid={owner_pid} peer_pid={seen[0][1]}")


def test_actor_refusal_keeps_admission_actor_armed(tmp_path):
    socket_path = tmp_path / "refusal.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(3)
    owner_pid = os.getpid()
    owner_start = operator._proc_start(owner_pid)
    prepare = _admission_reply(
        owner_pid=owner_pid,
        owner_start=owner_start,
        generation=31,
        reservation_id="refusal-measure-31",
        kind="measure",
        state="prepared",
        handshake_state="construction_prepared",
        history=["construction_prepared"],
    )
    seen: list[dict] = []

    def serve():
        try:
            connection, _address = listener.accept()
            with connection:
                raw = bytearray()
                while chunk := connection.recv(4096):
                    raw.extend(chunk)
                seen.append(json.loads(bytes(raw).decode("utf-8")))
                connection.sendall((json.dumps(prepare) + "\n").encode())
            connection, _address = listener.accept()
            with connection:
                raw = bytearray()
                while chunk := connection.recv(4096):
                    raw.extend(chunk)
                seen.append(json.loads(bytes(raw).decode("utf-8")))
                connection.sendall(b'{"ok":false}\n')
        finally:
            listener.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    actor = operator.CancellationActor(
        socket_path,
        generation=31,
        reservation_id="",
        deadline=time.monotonic() + 20.0,
        owner_pid=owner_pid,
        owner_start=owner_start,
    )
    actor.start()
    try:
        actor.call("prepare", generation=31, preflight=False, deadline=time.monotonic() + 10.0)
        with pytest.raises(operator.OperatorError, match="actor_admission_invalid"):
            actor.call(
                "finalize",
                generation=31,
                reservation_id="refusal-measure-31",
                deadline=actor.deadline,
            )
        assert actor._process is not None and actor._process.is_alive()
    finally:
        actor.close()
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert [request["command"] for request in seen] == [
        "native_construction_prepare",
        "native_construction_finalize_admit",
    ]


def test_actor_lost_admission_reply_is_indeterminate_and_remains_armed(tmp_path):
    socket_path = tmp_path / "lost-reply.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(2)
    seen: list[dict] = []

    def serve():
        try:
            connection, _address = listener.accept()
            with connection:
                raw = bytearray()
                while chunk := connection.recv(4096):
                    raw.extend(chunk)
                seen.append(json.loads(bytes(raw).decode("utf-8")))
        finally:
            listener.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    actor = operator.CancellationActor(
        socket_path,
        generation=31,
        reservation_id="",
        deadline=time.monotonic() + 20.0,
        owner_pid=os.getpid(),
        owner_start=operator._proc_start(os.getpid()),
    )
    actor.start()
    try:
        with pytest.raises(operator.AdmissionIndeterminate):
            actor.call("prepare", generation=31, preflight=False, deadline=time.monotonic() + 10.0)
        assert actor._process is not None and actor._process.is_alive()
    finally:
        actor.close()
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert seen == [{"command": "native_construction_prepare", "generation": 31}]


def test_actor_admission_survives_owner_death_and_cancels_late_reply(tmp_path):
    socket_path = tmp_path / "held-admission.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(4)
    context = multiprocessing.get_context("spawn")
    status_read, status_write = context.Pipe(duplex=False)
    first_received = threading.Event()
    release_reply = threading.Event()
    seen: list[tuple[dict, int]] = []
    owner_info: dict[str, object] = {}

    def serve():
        try:
            connection, _address = listener.accept()
            with connection:
                peer = _peer_pid(connection)
                raw = bytearray()
                while True:
                    chunk = connection.recv(4096)
                    if not chunk:
                        break
                    raw.extend(chunk)
                request = json.loads(bytes(raw).decode("utf-8"))
                seen.append((request, peer))
                first_received.set()
                assert release_reply.wait(8.0)
                response = _admission_reply(
                    owner_pid=int(owner_info["owner_pid"]),
                    owner_start=str(owner_info["owner_start"]),
                    generation=31,
                    reservation_id="late-measure-31",
                    kind="measure",
                    state="prepared",
                    handshake_state="construction_prepared",
                    history=["construction_prepared"],
                )
                connection.sendall((json.dumps(response, separators=(",", ":")) + "\n").encode())
            connection, _address = listener.accept()
            with connection:
                peer = _peer_pid(connection)
                raw = bytearray()
                while True:
                    chunk = connection.recv(4096)
                    if not chunk:
                        break
                    raw.extend(chunk)
                request = json.loads(bytes(raw).decode("utf-8"))
                seen.append((request, peer))
                response = _admission_reply(
                    owner_pid=int(owner_info["owner_pid"]),
                    owner_start=str(owner_info["owner_start"]),
                    generation=31,
                    reservation_id="late-measure-31",
                    kind="measure",
                    state="cancelled",
                    handshake_state="cancelled",
                    history=["construction_prepared", "cancelled"],
                )
                connection.sendall((json.dumps(response, separators=(",", ":")) + "\n").encode())
        finally:
            listener.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    owner = context.Process(
        target=_actor_admission_owner_fixture,
        args=(str(socket_path), status_write),
        name="native-calibration-actor-admission-owner",
        daemon=False,
    )
    owner.start()
    status_write.close()
    try:
        assert status_read.poll(8.0)
        owner_pid, owner_start, actor_pid = status_read.recv()
        owner_info.update(owner_pid=owner_pid, owner_start=owner_start)
        assert first_received.wait(8.0)
        assert actor_pid != owner_pid
        os.kill(owner_pid, signal.SIGKILL)
        owner.join(timeout=4.0)
        release_reply.set()
        thread.join(timeout=8.0)
        assert not thread.is_alive()
        assert len(seen) == 2
        assert seen[0][1] == actor_pid and seen[1][1] == actor_pid
        assert all(peer != owner_pid for _request, peer in seen)
        assert seen[0][0]["command"] == "native_construction_prepare"
        assert seen[1][0] == {
            "command": "native_construction_recovery_cancel",
            "generation": 31,
            "reservationId": "late-measure-31",
        }
        print(
            f"late_reply_actor_pid={actor_pid} dead_owner_pid={owner_pid} peers={[peer for _r, peer in seen]}"
        )
    finally:
        release_reply.set()
        if owner.is_alive():
            owner.kill()
        owner.join(timeout=3.0)
        status_read.close()
        thread.join(timeout=3.0)


def test_cancellation_actor_acknowledges_canonical_handoff_without_replacement(tmp_path):
    actor = operator.CancellationActor(
        tmp_path / "unused.sock",
        generation=7,
        reservation_id="reservation-old",
        deadline=time.monotonic() + 8.0,
        owner_pid=os.getpid(),
        owner_start=operator._proc_start(os.getpid()),
    )
    actor.start()
    try:
        actor.update(
            generation=8,
            reservation_id="reservation-new",
            deadline=time.monotonic() + 8.0,
        )
        assert actor.generation == 8
        assert actor.reservation_id == "reservation-new"
    finally:
        actor.close()


def test_operator_handoff_updates_existing_cancellation_actor(tmp_path):
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    client = FakeClient(7, [])
    client.socket_path = tmp_path / "unused.sock"
    screen = FakeScreen(tmp_path, construct_scene, restore_scene)
    input_device = FakeInput(screen)
    candidate = operator.NativeCalibrationOperator(
        mode=operator.MODE_CONTROL_PREFLIGHT,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=client,
        screen=screen,
        input_device=input_device,
        receipt_root=tmp_path / "receipts",
    )
    candidate.receipt.begin()
    try:
        candidate._prepare(preflight=True)
        actor = candidate._cancellation_actor
        assert actor is not None
        bootstrap_reply = client._reply("running")
        bootstrap_reply["reservation"]["expiresMonotonic"] = actor.deadline + 3130.0
        candidate._adopt_reply(bootstrap_reply, expected_state="running")
        assert actor.deadline == bootstrap_reply["reservation"]["expiresMonotonic"]
        assert candidate._reservation_deadline == bootstrap_reply["reservation"]["expiresMonotonic"]
        recovery = FakeBinding(reservation_id="recovery-1", kind="recovery", state="recovery")
        reply = {
            "ok": True,
            "reservation": recovery.record(7),
            "handshake": {
                "state": "recovery_required",
                "stateHistory": [{"state": "recovery_required", "nativeClock": 1.0}],
            },
        }
        candidate._adopt_handoff(reply, expected_state="recovery_required")
        assert candidate._cancellation_actor is actor
        assert actor.generation == 7
        assert actor.reservation_id == "recovery-1"
    finally:
        candidate._stop_cancellation_actor()
        input_device.close()


def test_handled_signal_handlers_remain_during_cleanup_and_ignore_repeats(tmp_path):
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    candidate = operator.NativeCalibrationOperator(
        mode=operator.MODE_CONTROL_PREFLIGHT,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=FakeClient(7, []),
        screen=FakeScreen(tmp_path, construct_scene, restore_scene),
        input_device=FakeInput(FakeScreen(tmp_path, construct_scene, restore_scene)),
    )
    candidate._defer_signal_restore = True
    try:
        with pytest.raises(operator.OperatorInterrupted):
            with candidate._signals():
                os.kill(os.getpid(), operator.signal.SIGTERM)
        assert candidate._old_handlers
        candidate._cleanup_started = True
        os.kill(os.getpid(), operator.signal.SIGINT)
        assert candidate._aborted
    finally:
        candidate._defer_signal_restore = False
        candidate._restore_signals()


def test_watchdog_readiness_failure_rolls_back_spawned_process(monkeypatch):
    tool = operator.PinnedInputTool.load()
    real_context = multiprocessing.get_context("spawn")
    spawned = []

    class ContextProxy:
        def Process(self, *args, **kwargs):
            process = real_context.Process(*args, **kwargs)
            spawned.append(process)
            return process

    monkeypatch.setattr(operator.multiprocessing, "get_context", lambda _name: ContextProxy())
    monkeypatch.setattr(
        operator,
        "_read_bounded",
        lambda _fd, _size, *, timeout: (_ for _ in ()).throw(TimeoutError("fixture readiness timeout")),
    )
    try:
        with pytest.raises(operator.OperatorError, match="watchdog readiness"):
            operator.Watchdog(tool, interval=0.02, environment={})
        assert spawned and all(not process.is_alive() for process in spawned)
    finally:
        tool.close()


def test_receipt_publication_failure_is_retained_as_receipt_error(tmp_path, monkeypatch):
    writer = operator.ReceiptWriter(tmp_path / "root", operator.MODE_CONTROL_PREFLIGHT)
    writer.begin()
    monkeypatch.setattr(operator.os, "replace", lambda *_args: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(operator.ReceiptError, match="publication"):
        writer.finish("failure", "operator_failure")
    assert writer.attempt is not None
    assert (writer.attempt / ".receipt.json.tmp").exists()


def test_run_receipt_failure_does_not_skip_input_cleanup(tmp_path):
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    screen = FakeScreen(tmp_path, construct_scene, restore_scene)
    input_device = FakeInput(screen)
    client = FakeClient(7, [], kind="preflight")
    input_device.dispatch = client.dispatch
    commands = iter(["/crowley agent defer", "/reload"])
    op = operator.NativeCalibrationOperator(
        mode=operator.MODE_CONTROL_PREFLIGHT,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=client,
        screen=screen,
        input_device=input_device,
        ocr=lambda path: "" if "chat-closed" in path.name else "say: " + next(commands),
        receipt_root=tmp_path / "receipts",
        sleep=lambda _delay: None,
    )

    def fail_finish(*_args, **_kwargs):
        raise operator.ReceiptError("forced receipt failure")

    op.receipt.finish = fail_finish
    with pytest.raises(operator.ReceiptError, match="forced receipt failure"):
        op.run()
    assert input_device.closed


def test_active_receipt_event_failure_blocks_first_physical_dispatch(tmp_path):
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    screen = FakeScreen(tmp_path, construct_scene, restore_scene)
    input_device = FakeInput(screen)
    op = operator.NativeCalibrationOperator(
        mode=operator.MODE_CONTROL_PREFLIGHT,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=FakeClient(7, [], kind="preflight"),
        screen=screen,
        input_device=input_device,
        receipt_root=tmp_path / "receipts",
    )

    def fail_event(*_args, **_kwargs):
        raise operator.ReceiptError("event publication failed")

    op.receipt.event = fail_event
    with pytest.raises(operator.ReceiptError, match="event publication failed"):
        op.run()
    assert input_device.calls == []
    assert input_device.closed


def test_causal_run_failure_survives_cleanup_close_failure(tmp_path):
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    screen = FakeScreen(tmp_path, construct_scene, restore_scene)

    class CausalClient(FakeClient):
        def prepare(self, generation: int, *, preflight: bool = False):
            raise operator.OperatorError("causal prepare refusal")

    class BrokenInput(FakeInput):
        def close(self):
            self.closed = True
            raise RuntimeError("cleanup close failure")

    input_device = BrokenInput(screen)
    op = operator.NativeCalibrationOperator(
        mode=operator.MODE_CONTROL_PREFLIGHT,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=CausalClient(7, []),
        screen=screen,
        input_device=input_device,
        receipt_root=tmp_path / "receipts",
    )
    with pytest.raises(operator.OperatorError, match="causal prepare refusal"):
        op.run()
    assert input_device.closed
    assert op.receipt.attempt is not None
    receipt = json.loads((op.receipt.attempt / "receipt.json").read_text())
    assert receipt["outcome"] == "failure"


def test_input_action_cleanup_failure_is_named_and_retains_causal_error(tmp_path):
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    screen = FakeScreen(tmp_path, construct_scene, restore_scene)

    class CausalClient(FakeClient):
        def prepare(self, generation: int, *, preflight: bool = False):
            raise operator.OperatorError("causal prepare refusal")

    class BrokenActionInput(FakeInput):
        cleanup_failures = ["pointer.release_now"]

    input_device = BrokenActionInput(screen)
    op = operator.NativeCalibrationOperator(
        mode=operator.MODE_CONTROL_PREFLIGHT,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=CausalClient(7, [], kind="preflight"),
        screen=screen,
        input_device=input_device,
        receipt_root=tmp_path / "receipts",
    )
    with pytest.raises(operator.OperatorError, match="causal prepare refusal"):
        op.run()
    receipt = json.loads((op.receipt.attempt / "receipt.json").read_text())
    events = receipt["events"]
    assert any(
        event["name"] == "mandatory_cleanup_failed" and event["stage"] == "pointer.release_now"
        for event in events
    )
    assert receipt["outcome"] == "failure"


def test_all_fixed_measure_sequence_uses_only_allowlisted_chat_and_ipc(tmp_path):
    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    screen = FakeScreen(tmp_path, construct_scene, restore_scene)
    dual = Image.new("RGB", (1280, 720), (0, 0, 0))
    dual.paste(Image.open(construct_scene).crop((1142, 22, 1146, 26)), (1142, 22))
    dual.paste(Image.open(restore_scene).crop((1211, 22, 1215, 26)), (1211, 22))
    screen.dual = tmp_path / "scene-dual.png"
    dual.save(screen.dual, format="PNG")
    input_device = FakeInput(screen)
    client = FakeClient(7, [])
    input_device.dispatch = client.dispatch
    commands = iter(
        [
            "/crowley agent defer",
            "/reload",
            "/crowley agent release",
            "/crowley agent hold",
            "/crowley agent measure",
            "/crowley agent resume",
            "/crowley agent finalize",
        ]
    )

    def ocr(path):
        if "chat-closed" in path.name:
            return ""
        return "say: " + next(commands)

    op = operator.NativeCalibrationOperator(
        mode=operator.MODE_MEASURE_DEFERRED,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=client,
        screen=screen,
        input_device=input_device,
        ocr=ocr,
        receipt_root=tmp_path / "receipts",
        sleep=lambda _delay: None,
        absence_checker=lambda _path, *, expected_size: True,
    )
    result = op.run()
    assert result["ok"] is True
    typed = [value for kind, value in input_device.calls if kind == "type"]
    assert typed == [
        "/crowley agent defer",
        "/reload",
        "/crowley agent release",
        "/crowley agent hold",
        "/crowley agent measure",
        "/crowley agent resume",
        "/crowley agent finalize",
    ]
    assert all(call.get("command") != "native_bootstrap" for call in client.calls)
    assert any(call.get("command") == "bootstrap" for call in client.calls)
    assert any(call.get("command") == "native_calibrate" for call in client.calls)
    assert any(call.get("command") == "calibration_status" for call in client.calls)


def test_actual_session_ipc_composes_preflight_and_recovery_over_af_unix(tmp_path: Path) -> None:
    """Exercise public native admissions through the real daemon IPC parser."""

    from crowley.session.cli import (
        _BoundedIPCReader,
        _encode_bounded_record,
        _parse_bounded_json,
        _socket_request,
    )
    from crowley.session.controller import ControllerState
    from tests.test_session_native_regressions import _construction_daemon, _construction_frame

    daemon, driver, identity, child = _construction_daemon(tmp_path, state=ControllerState.PAUSED)
    identity = replace(identity, fingerprint="a" * 64)
    driver.backend.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
    socket_path = tmp_path / "actual-session.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    os.chmod(socket_path, 0o600)
    listener.listen(8)
    listener.settimeout(0.1)
    stop = threading.Event()
    workers: list[threading.Thread] = []

    begin = _construction_frame(identity, boot="boot-a", sequence=2)
    begin["captureMonotonic"] = 1.0
    ordinary = _construction_frame(identity, boot="ordinary-new", sequence=3)
    ordinary["captureMonotonic"] = 2.0
    observation_count = 0

    def observation_provider() -> dict[str, object]:
        nonlocal observation_count
        observation_count += 1
        return begin if observation_count <= 2 else ordinary

    daemon._native_construction_observation_provider = observation_provider

    from crowley.session.cli import SessionIPC

    ipc = SessionIPC(daemon.controller, owner=daemon)

    def serve_connection(connection: socket.socket) -> None:
        with connection:
            reader = _BoundedIPCReader(connection)
            raw = reader.read_record(4096)
            if raw is None:
                return
            request = _parse_bounded_json(raw)
            assert isinstance(request, dict)
            try:
                response = ipc.dispatch(request)
            except Exception as exc:
                response = {"ok": False, "error": str(exc)}
            try:
                connection.sendall(_encode_bounded_record(response, 524288))
            except OSError:
                # The bounded client may close after its absolute deadline;
                # production `serve` treats that as a transport teardown.
                pass

    def serve() -> None:
        while not stop.is_set():
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            except OSError:
                if stop.is_set():
                    return
                raise
            worker = threading.Thread(target=serve_connection, args=(connection,), daemon=True)
            workers.append(worker)
            worker.start()

    server = threading.Thread(target=serve, daemon=True)
    server.start()
    client = operator.DaemonClient(socket_path, request_fn=_socket_request, timeout=15.0)
    try:
        preflight = _socket_request(
            socket_path,
            {"command": "native_construction_control_preflight", "generation": 7},
            timeout=15.0,
        )
        assert preflight.get("ok") is True, preflight
        # The next public admission is consumed by the closed client facade;
        # no reservation is manufactured by the test.
        assert preflight["ok"] is True
        preflight_id = preflight["reservation"]["reservationId"]
        started = client.recovery_begin(7, preflight_id)
        assert started["ok"] is True
        recovery_id = started["reservation"]["reservationId"]
        assert started["handshake"]["state"] == "recovery_required"
        completed = client.recovery_complete(7, recovery_id)
        assert completed["ok"] is True
        assert completed["handshake"]["state"] == "recovered"
        assert completed["reservation"]["reservationState"] == "recovered"
        assert completed["reservation"]["reservationKind"] == "recovery"
    finally:
        stop.set()
        listener.close()
        server.join(timeout=2.0)
        for worker in workers:
            worker.join(timeout=2.0)
        driver.close()
        child.terminate()
        child.wait(timeout=3)


def test_control_preflight_operator_uses_actual_daemon_admissions(tmp_path: Path) -> None:
    """Run the control-preflight mode with a production DaemonClient/actor."""

    from crowley.session.cli import (
        SessionIPC,
        _BoundedIPCReader,
        _encode_bounded_record,
        _parse_bounded_json,
        _socket_request,
    )
    from crowley.session.controller import ControllerState
    from tests.test_session_native_regressions import _construction_daemon, _construction_frame

    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    # The production transform searches the reviewed 220x84 top-right panel
    # in a 1920x1080 client capture.  Keep the same sealed template bytes but
    # place the construct role inside that exact region.
    full_construct = Image.new("RGB", (1920, 1080), (0, 0, 0))
    with Image.open(manifest.construct.path) as template:
        full_construct.paste(template, (1680, 28))
    full_construct_path = tmp_path / "scene-construct-full.png"
    full_construct.save(full_construct_path, format="PNG")
    full_restore = Image.new("RGB", (1920, 1080), (0, 0, 0))
    with Image.open(manifest.restore.path) as template:
        full_restore.paste(template, (1770, 28))
    full_restore_path = tmp_path / "scene-restore-full.png"
    full_restore.save(full_restore_path, format="PNG")
    construct_scene, restore_scene = full_construct_path, full_restore_path
    daemon, driver, identity, child = _construction_daemon(tmp_path, state=ControllerState.PAUSED)
    identity = replace(identity, fingerprint="a" * 64)
    driver.backend.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
    socket_path = tmp_path / "control-operator.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    os.chmod(socket_path, 0o600)
    listener.listen(8)
    listener.settimeout(0.1)
    stop = threading.Event()
    workers: list[threading.Thread] = []
    begin = _construction_frame(identity, boot="boot-a", sequence=2)
    begin["captureMonotonic"] = 1.0
    ordinary = _construction_frame(identity, boot="ordinary-new", sequence=3)
    ordinary["captureMonotonic"] = 2.0
    observations = iter((begin, begin, ordinary))
    daemon._native_construction_observation_provider = lambda: next(observations)
    ipc = SessionIPC(daemon.controller, owner=daemon)

    def serve_connection(connection: socket.socket) -> None:
        with connection:
            reader = _BoundedIPCReader(connection)
            raw = reader.read_record(4096)
            if raw is None:
                return
            request = _parse_bounded_json(raw)
            assert isinstance(request, dict)
            try:
                response = ipc.dispatch(request)
            except Exception as exc:
                response = {"ok": False, "error": str(exc)}
            try:
                connection.sendall(_encode_bounded_record(response, 524288))
            except OSError:
                pass

    def serve() -> None:
        while not stop.is_set():
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            except OSError:
                if stop.is_set():
                    return
                raise
            worker = threading.Thread(target=serve_connection, args=(connection,), daemon=True)
            workers.append(worker)
            worker.start()

    server = threading.Thread(target=serve, daemon=True)
    server.start()
    screen = FakeScreen(tmp_path, construct_scene, restore_scene)
    screen.identity = Identity(
        fingerprint=identity.fingerprint,
        child_geometry=identity.child_geometry,
        target_event_xids=frozenset(identity.target_event_xids),
    )
    input_device = FakeInput(screen)
    commands = iter(("/crowley agent defer", "/reload"))
    client = operator.DaemonClient(socket_path, request_fn=_socket_request, timeout=15.0)
    op = operator.NativeCalibrationOperator(
        mode=operator.MODE_CONTROL_PREFLIGHT,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=client,
        screen=screen,
        input_device=input_device,
        ocr=lambda path: "" if "chat-closed" in path.name else "say: " + next(commands),
        receipt_root=tmp_path / "receipts",
        sleep=lambda _delay: None,
    )
    try:
        result = op.run()
        assert result["ok"] is True
        assert [value for kind, value in input_device.calls if kind == "type"] == [
            "/crowley agent defer",
            "/reload",
        ]
        assert any(kind == "click" and value == "construct" for kind, value in input_device.calls)
    finally:
        stop.set()
        listener.close()
        server.join(timeout=2.0)
        for worker in workers:
            worker.join(timeout=2.0)
        driver.close()
        child.terminate()
        child.wait(timeout=3)


def test_recover_operator_uses_actual_empty_id_recovery_admission(tmp_path: Path) -> None:
    """Run standalone recovery through a real durable checkpoint and socket."""

    from crowley.session.cli import (
        SessionIPC,
        _BoundedIPCReader,
        _encode_bounded_record,
        _parse_bounded_json,
        _socket_request,
    )
    from crowley.session.controller import ControllerState
    from tests.test_session_native_regressions import _construction_daemon, _construction_frame

    manifest, construct_scene, restore_scene = make_scenes(tmp_path)
    daemon, driver, identity, child = _construction_daemon(tmp_path, state=ControllerState.PAUSED)
    identity = replace(identity, fingerprint="a" * 64)
    driver.backend.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
    daemon.controller.set_native_construction_checkpoint(
        {
            "schema": 1,
            "B0": "boot-a",
            "expectedConstructorBoot": "native-construction:boot-a",
            "ownerGeneration": 7,
            "kind": "measure",
            "phase": "prepared",
        },
        expected_generation=7,
        expected_state=ControllerState.PAUSED,
    )
    begin = _construction_frame(identity, boot="boot-a", sequence=2)
    begin["captureMonotonic"] = 1.0
    ordinary = _construction_frame(identity, boot="ordinary-new", sequence=3)
    ordinary["captureMonotonic"] = 2.0
    observation_count = 0

    def observation_provider() -> dict[str, object]:
        nonlocal observation_count
        observation_count += 1
        return begin if observation_count == 1 else ordinary

    daemon._native_construction_observation_provider = observation_provider
    socket_path = tmp_path / "recover-operator.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    os.chmod(socket_path, 0o600)
    listener.listen(8)
    listener.settimeout(0.1)
    stop = threading.Event()
    workers: list[threading.Thread] = []
    ipc = SessionIPC(daemon.controller, owner=daemon)

    def serve_connection(connection: socket.socket) -> None:
        with connection:
            reader = _BoundedIPCReader(connection)
            raw = reader.read_record(4096)
            if raw is None:
                return
            request = _parse_bounded_json(raw)
            assert isinstance(request, dict)
            try:
                response = ipc.dispatch(request)
            except Exception as exc:
                response = {"ok": False, "error": str(exc)}
            try:
                connection.sendall(_encode_bounded_record(response, 524288))
            except OSError:
                pass

    def serve() -> None:
        while not stop.is_set():
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            except OSError:
                if stop.is_set():
                    return
                raise
            worker = threading.Thread(target=serve_connection, args=(connection,), daemon=True)
            workers.append(worker)
            worker.start()

    server = threading.Thread(target=serve, daemon=True)
    server.start()
    screen = FakeScreen(tmp_path, construct_scene, restore_scene)
    screen.identity = Identity(
        fingerprint=identity.fingerprint,
        child_geometry=identity.child_geometry,
        target_event_xids=frozenset(identity.target_event_xids),
    )
    input_device = FakeInput(screen)
    client = operator.DaemonClient(socket_path, request_fn=_socket_request, timeout=15.0)
    op = operator.NativeCalibrationOperator(
        mode=operator.MODE_RECOVER,
        generation=7,
        config_path=tmp_path / "config.toml",
        template_manifest=manifest,
        client=client,
        screen=screen,
        input_device=input_device,
        ocr=lambda path: "" if "chat-closed" in path.name else "say: /reload",
        receipt_root=tmp_path / "receipts",
        sleep=lambda _delay: None,
    )
    try:
        result = op.run()
        assert result["ok"] is True
        assert ("type", "/reload") in input_device.calls
        assert daemon.controller.native_construction_checkpoint() is None
    finally:
        stop.set()
        listener.close()
        server.join(timeout=2.0)
        for worker in workers:
            worker.join(timeout=2.0)
        driver.close()
        child.terminate()
        child.wait(timeout=3)


def test_compiled_producer_and_stock_decoder_fixture_is_reused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Retain the real compiled producer/decoder/daemon composition in this proof slice."""

    from tests.test_session_native import test_compiled_region_composes_through_default_daemon_and_stock_model

    test_compiled_region_composes_through_default_daemon_and_stock_model(tmp_path, monkeypatch)


@pytest.mark.parametrize(
    ("operation_mode", "measurement_failure", "recovery_kind", "fixture_case"),
    [
        (operator.MODE_MEASURE_DEFERRED, False, "", ""),
        (operator.MODE_MEASURE_DEFERRED, True, "", ""),
        (operator.MODE_CONTROL_PREFLIGHT, False, "", ""),
        (operator.MODE_RECOVER, False, "ordinary_reload", ""),
        (operator.MODE_RECOVER, False, "restore", ""),
        (operator.MODE_MEASURE_DEFERRED, False, "", "watchdog-readiness"),
        (operator.MODE_MEASURE_DEFERRED, False, "", "pressed-budget"),
        (operator.MODE_MEASURE_DEFERRED, False, "", "post-handoff-cancel"),
    ],
    ids=[
        "success",
        "measurement-failure",
        "control-preflight",
        "recover-ordinary",
        "recover-restore",
        "watchdog-readiness",
        "pressed-budget",
        "post-handoff-cancel",
    ],
)
def test_actual_operator_measure_composes_x11_screen_daemon_and_agent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation_mode: str,
    measurement_failure: bool,
    recovery_kind: str,
    fixture_case: str,
) -> None:
    """Run real compiled measurement and control-preflight causal workflows."""

    from io import BytesIO

    from crowley.core.watchlist import load_catalog
    from crowley.session import driver as session_driver
    from crowley.session.calibration import LinuxProcStatusVmHwmReset5
    from crowley.session.cli import (
        SessionIPC,
        _BoundedIPCReader,
        _encode_bounded_record,
        _parse_bounded_json,
        _socket_request,
    )
    from crowley.session.config import SessionConfig, load_config
    from crowley.session.controller import Controller, ControllerState
    from crowley.session.daemon import SessionDaemon
    from crowley.session.driver import DesktopDriver, WindowIdentity, X11Backend, _proc_start
    from crowley.session.journal import DEFAULT_STATE, Journal
    from tests.test_session_native import _evidence
    from tests.test_session_native_regressions import AUTHENTIC_CODEX_PATH
    from tests.wow_harness import WowClient

    harness_path = Path(__file__).resolve().parents[1] / "tools/gnome-telemetry-region/offline_harness.py"
    harness_spec = importlib.util.spec_from_file_location("causal_region_harness", harness_path)
    assert harness_spec is not None and harness_spec.loader is not None
    harness = importlib.util.module_from_spec(harness_spec)
    harness_spec.loader.exec_module(harness)

    freeze_path = (
        Path(__file__).resolve().parents[1]
        / ".archive/executor-review/gnome-telemetry-region-r6-final-freeze.json"
    )
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    producer = Path(freeze["private_cache"]) / "prefix/bin/gnome-screenshot"
    assert producer.is_file()
    producer_sha256 = hashlib.sha256(producer.read_bytes()).hexdigest()
    assert producer_sha256 == freeze["build"]["private_binary_sha256"]

    # Keep this isolated compositor from contending with a live session's
    # process-global screenshot lock.  The production lock implementation and
    # admission semantics remain unchanged; only this test's lock resource is
    # private and created before the real backend/driver are constructed.
    monkeypatch.setattr(
        session_driver,
        "GNOME_CAPTURE_LOCK_PATH",
        tmp_path / "gnome-screenshot.lock",
    )

    def png_bytes(image: Image.Image) -> bytes:
        output = BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()

    # Build the exact Agent publication stream with the unmodified Lua harness.
    ordinary = WowClient(faction="Alliance", realm="Normal")
    ordinary.set_canonical_plan()
    ordinary.login()
    ordinary.publish_agent()
    ordinary.update_agent(1.0)
    baseline_image = ordinary.render_agent_capture()
    ordinary_boot = str(ordinary.ns.Agent.Boot())
    ordinary_saved = ordinary._json_table(ordinary.lua.globals().CrowleyDB)
    assert ordinary_saved is not None
    # Keep the actual client unarmed until the helper dispatches its real
    # /agent defer action.  A separate harness VM supplies only the saved
    # variables for static construction images; pre-arming the live VM would
    # turn the helper's action into an ignored duplicate refusal.
    construction_seed = WowClient(faction="Alliance", realm="Normal")
    construction_seed.set_canonical_plan()
    construction_seed.inject_saved_variables(ordinary_saved)
    construction_seed.login()
    construction_seed.slash("agent defer")
    construction_saved = construction_seed._json_table(construction_seed.lua.globals().CrowleyDB)
    assert construction_saved is not None
    recovery_ordinary = WowClient(faction="Alliance", realm="Normal")
    recovery_ordinary.set_canonical_plan()
    recovery_ordinary.inject_saved_variables(ordinary_saved)
    # The harness starts each isolated Lua VM with the same deterministic RNG;
    # seed this fresh ordinary boot separately so the native recovery proof
    # observes a genuinely newer ordinary frame boot.
    recovery_ordinary.lua.globals().math.randomseed(987654)
    recovery_ordinary.login()
    assert recovery_ordinary.ns.Agent.Lifecycle() == "ordinary"
    recovery_baseline_image = recovery_ordinary.render_agent_capture()
    post_success_ordinary = WowClient(faction="Alliance", realm="Normal")
    post_success_ordinary.set_canonical_plan()
    post_success_ordinary.inject_saved_variables(ordinary_saved)
    post_success_ordinary.lua.globals().math.randomseed(13579)
    post_success_ordinary.login()
    assert post_success_ordinary.ns.Agent.Lifecycle() == "ordinary"
    post_success_baseline_image = post_success_ordinary.render_agent_capture()
    deferred = WowClient(faction="Alliance", realm="Normal")
    deferred.set_canonical_plan()
    deferred.inject_saved_variables(construction_saved)
    deferred.login()
    assert deferred.ns.Agent.Lifecycle() == "deferred"
    # Keep the actual runtime client untouched for the composed bridge.  The
    # second harness instance supplies only the deterministic future payloads
    # consumed by the sealed compositor; no reply or observation is faked.
    visual = WowClient(faction="Alliance", realm="Normal")
    visual.set_canonical_plan()
    visual.inject_saved_variables(construction_saved)
    visual.login()
    assert visual.ns.Agent.Lifecycle() == "deferred"
    visual.slash("agent release")
    visual.click_native("construct")
    construct_image = visual.render_agent_capture()
    visual.slash("agent hold")
    held_zero_image = visual.render_agent_capture()
    visual.slash("agent measure")
    update_images = [visual.render_agent_capture()]
    for _ordinal in range(2, 100):
        visual.advance_with_timers(1)
        update_images.append(visual.render_agent_capture())
    visual.advance_with_timers(1)
    held_hundred_image = visual.render_agent_capture()
    visual.slash("agent resume")
    resume_image = visual.render_agent_capture()
    visual.slash("agent finalize")
    final_image = visual.render_agent_capture()
    restore_live = WowClient(faction="Alliance", realm="Normal")
    restore_live.set_canonical_plan()
    restore_live.inject_saved_variables(construction_saved)
    restore_live.login()
    restore_live.slash("agent release")
    restore_live.click_native("construct")
    restore_live.slash("agent hold")
    restore_live_image = restore_live.render_agent_capture()
    restore_live_saved = restore_live._json_table(restore_live.lua.globals().CrowleyDB)
    assert restore_live_saved is not None
    restore_live_marker = restore_live_saved.get("nativeConstruction")
    assert isinstance(restore_live_marker, dict)
    assert restore_live_marker.get("state") == "constructed"
    restore_constructor_boot = restore_live_marker.get("token")
    assert isinstance(restore_constructor_boot, str) and restore_constructor_boot

    absent_image = Image.new("RGB", (256, 256), (127, 127, 127))
    area_payloads = [
        png_bytes(baseline_image),
        png_bytes(absent_image),
        png_bytes(absent_image),
        # The provider begins before the corresponding operator action. The
        # compositor selects the current pre-action surface from the actual
        # dispatch state file, so retries do not consume synthetic future
        # frames or grow the owner receipt with avoidable mismatches.
        png_bytes(absent_image),
        png_bytes(construct_image),
        png_bytes(held_zero_image),
        *(png_bytes(image) for image in update_images),
        png_bytes(held_hundred_image),
        png_bytes(resume_image),
        png_bytes(final_image),
    ]
    recovery_payload_index = len(area_payloads)
    area_payloads.append(png_bytes(recovery_baseline_image))
    restore_payload_index = len(area_payloads)
    area_payloads.append(png_bytes(restore_live_image))
    post_success_payload_index = len(area_payloads)
    area_payloads.append(png_bytes(post_success_baseline_image))
    initial_payload_index = (
        restore_payload_index if operation_mode == operator.MODE_RECOVER and recovery_kind == "restore" else 0
    )

    construct_template = tmp_path / "construct-template.png"
    restore_template = tmp_path / "restore-template.png"
    Image.new("RGB", (100, 28), (220, 36, 36)).save(construct_template)
    Image.new("RGB", (100, 28), (36, 220, 36)).save(restore_template)
    construct_template.chmod(0o600)
    restore_template.chmod(0o600)
    construct_sha = hashlib.sha256(construct_template.read_bytes()).hexdigest()
    restore_sha = hashlib.sha256(restore_template.read_bytes()).hexdigest()
    template_path = tmp_path / "templates.json"
    template_path.write_text(
        json.dumps(
            {
                "construct": {"path": str(construct_template), "sha256": construct_sha, "threshold": 5.0},
                "restore": {"path": str(restore_template), "sha256": restore_sha, "threshold": 5.0},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    template_path.chmod(0o600)
    manifest = operator.TemplateManifest.load(template_path)

    def full_desktop(agent: Image.Image) -> bytes:
        image = Image.new("RGB", (1920, 1080), (20, 24, 28))
        image.paste(Image.open(construct_template), (1684, 32))
        image.paste(Image.open(restore_template), (1788, 32))
        image.paste(agent, (80, 48))
        return png_bytes(image)

    initial_agent_image = (
        restore_live_image
        if operation_mode == operator.MODE_RECOVER and recovery_kind == "restore"
        else baseline_image
    )
    initial_desktop = full_desktop(initial_agent_image)
    gated_tool_root = make_gated_recording_artifact(tmp_path)
    action_log = tmp_path / "owned-actions.log"
    action_ack = tmp_path / "owned-action-acks"
    action_ack.mkdir(mode=0o700)
    action_log.touch(mode=0o600)
    frame_state_path = tmp_path / "frame-state-index"
    # Index 1 is the strict absent surface until the real construct click;
    # rows 1..3 still use their fixed baseline/absence entries by area index.
    frame_state_path.write_text("1", encoding="ascii")
    monkeypatch.setenv("CROWLEY_CAUSAL_FRAME_STATE", str(frame_state_path))
    payload_state_path = tmp_path / "payload-state-index"
    payload_state_path.write_text(str(initial_payload_index), encoding="ascii")
    monkeypatch.setenv("CROWLEY_CAUSAL_PAYLOAD_STATE", str(payload_state_path))
    pending_area_path = tmp_path / "pending-area.json"
    monkeypatch.setenv("CROWLEY_CAUSAL_PENDING_AREA", str(pending_area_path))

    # The stock fixture's area gate is intentionally re-entrant here: a
    # blocked ScreenshotArea call must not stop the same private Shell service
    # from serving the full-desktop Screenshot calls used by X11Screen's
    # untouched reload boundary and chat checks.  Rewrite only the temporary
    # compositor script before its private process starts; the compiled
    # producer and all production Python seams remain unchanged.
    original_popen = subprocess.Popen
    private_bus_config = tmp_path / "private-bus.conf"
    private_bus_config.write_text(
        "<busconfig>\n"
        "<type>session</type>\n"
        "<listen>unix:tmpdir=/tmp</listen>\n"
        "<auth>EXTERNAL</auth>\n"
        '<policy context="default">\n'
        '<allow send_destination="*" eavesdrop="true"/>\n'
        '<allow receive_sender="*" eavesdrop="true"/>\n'
        '<allow own="*"/>\n'
        "</policy>\n"
        "</busconfig>\n",
        encoding="utf-8",
    )
    private_bus_config.chmod(0o600)
    monkeypatch.setenv("NO_AT_BRIDGE", "1")

    class ReentrantCompositorPopen(original_popen):
        def __init__(self, command: Any, *args: Any, **kwargs: Any) -> None:
            if isinstance(command, list) and command and command[0] == "dbus-run-session":
                command = [
                    command[0],
                    f"--config-file={private_bus_config}",
                    *command[1:],
                ]
            if isinstance(command, list) and command and command[0] == "dbus-run-session":
                shell_script = next((str(item) for item in command if "compositor.js" in str(item)), None)
                if shell_script is not None:
                    match = re.search(r"(/tmp/[^'\s]+/compositor\.js)", shell_script)
                    if match is not None:
                        script_path = Path(match.group(1))
                        replacement = (
                            "let gateStarted = GLib.get_monotonic_time(); "
                            "let pendingPath = GLib.getenv('CROWLEY_CAUSAL_PENDING_AREA'); "
                            "if (pendingPath) GLib.file_set_contents(pendingPath, JSON.stringify({filename: filename, payload_index: payloadIndex, gate_started: gateStarted})); "
                            "while (true) { while (!GLib.file_test(ARGV[12], GLib.FileTest.EXISTS)) { "
                            "GLib.MainContext.default().iteration(false); GLib.usleep(1000); } "
                            "let releasedAt = 0; try { releasedAt = Number(readText(ARGV[12]).trim()); } catch (_) {} "
                            "if (Number.isFinite(releasedAt) && releasedAt >= gateStarted) break; "
                            "try { Gio.File.new_for_path(ARGV[12]).delete(null); } catch (_) {} } "
                            "try { Gio.File.new_for_path(ARGV[12]).delete(null); } catch (_) {}"
                        )
                        script = script_path.read_text(encoding="utf-8")
                        script = script.replace(
                            "while (!GLib.file_test(ARGV[12], GLib.FileTest.EXISTS)) GLib.usleep(10000);",
                            replacement,
                        )
                        script = script.replace(
                            "const payload = payloadPaths[areaIndex++]; if (!payload) throw new Error('unexpected ScreenshotArea retry');",
                            "let payloadIndex = areaIndex++; let payload = null;",
                        )
                        script = script.replace(
                            "index: areaIndex, filename, monotonic_us:",
                            "index: areaIndex, payload_index: payloadIndex, filename, monotonic_us:",
                        )
                        synchronous_gate = (
                            "  if (GLib.file_test(ARGV[10], GLib.FileTest.EXISTS)) { "
                            "let gateStarted = GLib.get_monotonic_time(); "
                            "let pendingPath = GLib.getenv('CROWLEY_CAUSAL_PENDING_AREA'); "
                            "if (pendingPath) GLib.file_set_contents(pendingPath, JSON.stringify({filename: filename, payload_index: payloadIndex, gate_started: gateStarted})); "
                            "GLib.file_set_contents(ARGV[11], String(gateStarted)); "
                            "while (true) { while (!GLib.file_test(ARGV[12], GLib.FileTest.EXISTS)) { "
                            "GLib.MainContext.default().iteration(false); GLib.usleep(1000); } "
                            "let releasedAt = 0; try { releasedAt = Number(readText(ARGV[12])); } catch (_) {} "
                            "if (Number.isFinite(releasedAt) && releasedAt >= gateStarted) break; "
                            "try { Gio.File.new_for_path(ARGV[12]).delete(null); } catch (_) {} } "
                            "try { Gio.File.new_for_path(ARGV[12]).delete(null); } catch (_) {} }\n"
                        )
                        # Keep the producer's normal synchronous output
                        # contract.  The loop pumps the private GJS main
                        # context so the real Screenshot service remains
                        # re-entrant while the gated area response waits.
                        asynchronous_gate = synchronous_gate
                        script = script.replace(synchronous_gate, asynchronous_gate)
                        script = script.replace(
                            "  GLib.file_set_contents(filename, readBase64(payload));",
                            "  let selectorPath = GLib.getenv('CROWLEY_CAUSAL_PAYLOAD_STATE'); "
                            "if (selectorPath && GLib.file_test(selectorPath, GLib.FileTest.EXISTS)) { "
                            "let selected = Number(readText(selectorPath).trim()); "
                            "if (Number.isInteger(selected) && selected >= 0) payloadIndex = selected; } "
                            "payload = payloadPaths[payloadIndex]; if (!payload) throw new Error('unexpected ScreenshotArea retry'); "
                            "GLib.file_set_contents(filename, readBase64(payload));",
                        )
                        script = script.replace(
                            "append(ARGV[1], {x, y, width, height, flash, index: areaIndex, payload_index: payloadIndex, filename, monotonic_us: GLib.get_monotonic_time()}); return [true, filename];",
                            "append(ARGV[1], {x, y, width, height, flash, index: areaIndex, payload_index: payloadIndex, filename, monotonic_us: GLib.get_monotonic_time()}); "
                            "let pendingDone = GLib.getenv('CROWLEY_CAUSAL_PENDING_AREA'); "
                            "if (pendingDone) { try { Gio.File.new_for_path(pendingDone).delete(null); } catch (_) {} } "
                            "return [true, filename];",
                        )
                        script_path.write_text(script, encoding="utf-8")
            super().__init__(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", ReentrantCompositorPopen)

    with harness.private_shell_compositor(
        payloads=area_payloads,
        full_desktop=initial_desktop,
        rectangle=(80, 48, 256, 256),
        allow_area_gate=True,
    ) as compositor:
        xauthority = Path(compositor["root"]) / "Xauthority"
        xauthority.touch(mode=0o600)
        config_path = tmp_path / "screen-config.toml"
        canonical_plan = load_catalog().scan_plan()
        plan_json = canonical_plan["planJSON"]
        plan_hash = canonical_plan["planHash"]
        config_path.write_text(
            "[profile]\n"
            f"display = {json.dumps(compositor['display'])}\n"
            f"xauthority = {json.dumps(str(xauthority))}\n"
            'wine_prefix = "/private/crowley-fixture"\n'
            'character = "Tester"\nrealm = "Normal"\n'
            'house = "us-normal-alliance"\n'
            "client_width = 1920\nclient_height = 1080\nouter_width = 1928\nouter_height = 1092\n"
            "canvas_origin = [80, 48]\ncanvas_crop = [80, 48, 256, 256]\n"
            "model_crop = [80, 48, 1760, 984]\n"
            f"plan_hash = {json.dumps(plan_hash)}\n"
            f"plan_json = {json.dumps(plan_json)}\n"
            "\n[session]\n"
            f"journal = {json.dumps(str(tmp_path / 'screen-journal.json'))}\n"
            f"socket = {json.dumps(str(tmp_path / 'operator.sock'))}\n"
            f"saved_variables = {json.dumps(str(tmp_path / 'SavedVariables.lua'))}\n"
            f"companion_state = {json.dumps(str(tmp_path / 'companion.json'))}\n"
            f"data_lua = {json.dumps(str(tmp_path / 'Data.lua'))}\n"
            f"telemetry_region_executable = {json.dumps(str(producer))}\n"
            f"telemetry_region_executable_sha256 = {json.dumps(producer_sha256)}\n",
            encoding="utf-8",
        )
        for path in (
            config_path,
            tmp_path / "SavedVariables.lua",
            tmp_path / "companion.json",
            tmp_path / "Data.lua",
        ):
            path.touch(mode=0o600, exist_ok=True)
        screen_config = load_config(config_path)
        child = subprocess.Popen(["/bin/sleep", "600"])
        process_start = _proc_start(child.pid)
        process_executable = os.path.realpath(os.readlink(f"/proc/{child.pid}/exe"))
        identity = WindowIdentity(
            0x400,
            child.pid,
            process_executable,
            "World of Warcraft",
            "wowb.exe",
            0x401,
            (0, 0, 1928, 1092),
            (0, 0, 1920, 1080),
            0x400,
            process_start,
            compositor["display"],
            "a" * 64,
            root_xid=0x374,
            managed_frame_xid=0x400,
            target_event_xids=frozenset({0x400, 0x401}),
        )

        backend = X11Backend(screen_config.profile)
        backend.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
        pointer = [0, 0, 0x400]
        backend.pointer_position = lambda **_kwargs: tuple(pointer)  # type: ignore[method-assign]
        driver = DesktopDriver(
            profile=screen_config.profile,
            backend=backend,
            lease_path=tmp_path / "desktop.lock",
        )
        driver.input_hierarchy = lambda **_kwargs: _evidence().xinput_hierarchy  # type: ignore[method-assign]
        native_clock = [time.monotonic()]
        driver.native_memory_meter = LinuxProcStatusVmHwmReset5(
            child.pid,
            process_start=process_start,
            process_executable=process_executable,
            identity_fingerprint=identity.fingerprint,
            monotonic=lambda: native_clock[0],
        )
        driver.guardian.lease.acquire()

        journal_path = tmp_path / "daemon-journal.json"
        journal_value = copy.deepcopy(DEFAULT_STATE)
        journal_value.update(
            {
                "state": (
                    ControllerState.PAUSED.value
                    if operation_mode in {operator.MODE_CONTROL_PREFLIGHT, operator.MODE_RECOVER}
                    else ControllerState.NATIVE_CALIBRATION.value
                ),
                "generation": 7,
                "current": {"frameBoot": "ordinary", "frameSequence": 1, "frameCrc32": 1},
            }
        )
        journal = Journal(journal_path)
        journal.write(journal_value)
        socket_path = tmp_path / "operator.sock"
        daemon_config = SessionConfig(
            profile=screen_config.profile,
            journal=journal_path,
            socket=socket_path,
            plan_hash=plan_hash,
            plan_json=plan_json,
            codex_path=AUTHENTIC_CODEX_PATH,
        )
        controller = Controller(journal, driver=driver, recover_on_restart=False)
        daemon = SessionDaemon(daemon_config, controller=controller, driver=driver)
        if operation_mode == operator.MODE_RECOVER:
            checkpoint_boot = restore_constructor_boot if recovery_kind == "restore" else ordinary_boot
            daemon.controller.set_native_construction_checkpoint(
                {
                    "schema": 1,
                    "B0": checkpoint_boot,
                    "expectedConstructorBoot": f"native-construction:{checkpoint_boot}",
                    "ownerGeneration": 7,
                    "kind": "measure",
                    "phase": "prepared",
                },
                expected_generation=7,
                expected_state=ControllerState.PAUSED,
            )
        native_provider_trace: list[dict[str, Any]] = []
        measurement_error_seen = False
        original_native_provider = daemon._native_measurement_provider

        def traced_native_provider(identity: Any, stage: str, ordinal: int) -> Any:
            nonlocal measurement_error_seen
            # Keep the real daemon/provider path and timestamps untouched.
            # The compositor ticker below publishes actual deferred-client
            # state once per real second; this wrapper only records the
            # resulting observations.
            try:
                observation = original_native_provider(identity, stage, ordinal)
            except BaseException as exc:
                native_provider_trace.append(
                    {"stage": stage, "ordinal": ordinal, "error": str(exc), "at": time.monotonic()}
                )
                raise
            if measurement_failure and stage == "updates" and ordinal == 1:
                measurement_error_seen = True
                native_provider_trace.append(
                    {"stage": stage, "ordinal": ordinal, "error": "actual fixture measurement failure"}
                )
                raise RuntimeError("actual fixture measurement failure")
            if fixture_case == "post-handoff-cancel" and stage == "updates" and ordinal == 1:
                os.kill(os.getpid(), signal.SIGINT)
            native_provider_trace.append(
                {
                    "stage": stage,
                    "ordinal": ordinal,
                    "capture": observation.capture_monotonic,
                    "at": time.monotonic(),
                    "phase": observation.native_phase,
                }
            )
            return observation

        daemon._native_measurement_provider = traced_native_provider  # type: ignore[method-assign]
        driver.native_measurement_provider = traced_native_provider
        ipc = SessionIPC(daemon.controller, owner=daemon)
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(socket_path))
        socket_path.chmod(0o600)
        listener.listen(16)
        listener.settimeout(0.1)
        stop_server = threading.Event()
        server_workers: list[threading.Thread] = []

        def serve_connection(connection: socket.socket) -> None:
            with connection:
                reader = _BoundedIPCReader(connection)
                raw = reader.read_record(4096)
                if raw is None:
                    return
                if raw.startswith(b"A"):
                    operation = _parse_bounded_json(raw[1:])
                    if not isinstance(operation, dict):
                        response = {"ok": False, "error": "actor_operation_fields"}
                    else:
                        op = operation.get("op")
                        commands = {
                            "prepare": "native_construction_control_preflight"
                            if operation.get("preflight") is True
                            else "native_construction_prepare",
                            "bootstrap": "native_construction_bootstrap",
                            "recovery_begin": "native_construction_recovery_begin",
                            "recovery_complete": "native_construction_recovery_complete",
                            "cancel": "native_construction_recovery_cancel",
                            "finalize": "native_construction_finalize_admit",
                            "recheck": "native_construction_recheck",
                        }
                        command_name = commands.get(op)
                        if command_name is None:
                            response = {"ok": False, "error": "actor_operation_fields"}
                        else:
                            request = {
                                "command": command_name,
                                "generation": operation.get("generation"),
                            }
                            if op != "prepare":
                                request["reservationId"] = operation.get("reservationId", "")
                            if op == "bootstrap":
                                request["expectedConstructorBoot"] = operation.get("expectedConstructorBoot")
                            try:
                                response = ipc.dispatch(request)
                            except Exception:
                                raise
                    frame = (
                        b"J" + json.dumps(response, sort_keys=True, separators=(",", ":")).encode() + b"\n"
                    )
                    try:
                        connection.sendall(frame)
                    except OSError:
                        pass
                    return
                request = _parse_bounded_json(raw)
                assert isinstance(request, dict)
                try:
                    response = ipc.dispatch(request)
                except Exception as exc:
                    response = {"ok": False, "error": str(exc)}
                try:
                    connection.sendall(_encode_bounded_record(response, 524288))
                except OSError:
                    pass

        def serve_socket() -> None:
            while not stop_server.is_set():
                try:
                    connection, _ = listener.accept()
                except TimeoutError:
                    continue
                except OSError:
                    if stop_server.is_set():
                        return
                    raise
                worker = threading.Thread(target=serve_connection, args=(connection,), daemon=True)
                server_workers.append(worker)
                worker.start()

        server_thread = threading.Thread(target=serve_socket, daemon=True)
        server_thread.start()

        screen_backend: list[Any] = []
        original_backend_factory = operator.X11Backend

        def screen_backend_factory(profile, *, input_tool=None):
            created = original_backend_factory(profile, input_tool=input_tool)
            created.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
            created.pointer_position = lambda **_kwargs: tuple(pointer)  # type: ignore[method-assign]
            screen_backend.append(created)
            return created

        monkeypatch.setattr(operator, "X11Backend", screen_backend_factory)
        gated_tool = operator.PinnedInputTool.from_root(gated_tool_root)
        # The real screen backend and FixedInput must consume the same sealed
        # executable artifact.  The production loader remains unchanged; this
        # test-only factory supplies the private recorder artifact to both
        # owners so the receipt pin covers one actual input image.
        monkeypatch.setattr(operator.PinnedInputTool, "load", lambda: gated_tool)
        screen = operator.X11Screen(config_path, tmp_path / "screen-receipts")
        watchdog_env = {
            "DISPLAY": compositor["display"],
            "XAUTHORITY": str(xauthority),
            "CROWLEY_ACTION_LOG": str(action_log),
            "CROWLEY_ACTION_ACK_DIR": str(action_ack),
        }
        watchdog = operator.Watchdog(gated_tool, interval=0.02, environment=watchdog_env)
        input_device = operator.FixedInput(gated_tool, watchdog=watchdog, environment=watchdog_env)
        client = operator.DaemonClient(socket_path, request_fn=_socket_request, timeout=45.0)
        state_lock = threading.RLock()
        state = {
            "client": (
                restore_live
                if operation_mode == operator.MODE_RECOVER and recovery_kind == "restore"
                else ordinary
            ),
            "chat": False,
            "text": "",
            "offset": 0,
            "construct_refused": False,
        }

        def set_frame_index(index: int) -> None:
            temporary = frame_state_path.with_name(".frame-state-index.tmp")
            temporary.write_text(str(index), encoding="ascii")
            os.replace(temporary, frame_state_path)

        def set_payload_index(index: int) -> None:
            temporary = payload_state_path.with_name(".payload-state-index.tmp")
            temporary.write_text(str(index), encoding="ascii")
            os.replace(temporary, payload_state_path)

        def reload_current_client(payload_index: int, *, expect_ordinary: bool = True) -> None:
            """Recreate the Lua VM only after an accepted ReloadUI/reload action."""

            nonlocal post_success_ordinary
            source = state["client"]
            saved_after_action = source._json_table(source.lua.globals().CrowleyDB)
            assert saved_after_action is not None
            fresh = WowClient(faction="Alliance", realm="Normal")
            fresh.set_canonical_plan()
            fresh.inject_saved_variables(saved_after_action)
            fresh.lua.globals().math.randomseed(10000 + reload_count)
            fresh.login()
            # The harness executes the world-ready restore path synchronously;
            # leave this bounded timer drain for the real addon readiness poll
            # when a fixture client schedules it.
            fresh.advance_with_timers(2)
            if expect_ordinary:
                assert fresh.ns.Agent.Lifecycle() == "ordinary"
            else:
                assert fresh.ns.Agent.Lifecycle() == "deferred"
            state["client"] = fresh
            if post_success_recovery:
                post_success_ordinary = fresh
            image = current_agent_image()
            encoded_image = png_bytes(image)
            # The private compositor may have an in-flight area request whose
            # ordinal was assigned before the accepted reload.  Refresh every
            # sealed payload slot at this causal boundary so no stale gray or
            # pre-reload frame can be decoded as the fresh boot.
            payload_paths = (
                compositor["payload_paths"]
                if payload_index != 1
                else (compositor["payload_paths"][payload_index],)
            )
            for payload_path in payload_paths:
                payload_path.write_text(base64.b64encode(encoded_image).decode("ascii"), encoding="ascii")
                os.chmod(payload_path, 0o600)
            area_payloads[payload_index] = encoded_image
            publish_full(image)
            set_frame_index(0)
            set_payload_index(payload_index)
            with gate_state_lock:
                area_block_path.unlink(missing_ok=True)
                area_release_path.touch(mode=0o600, exist_ok=True)
                gate_state["release_next"] = True

        full_desktop_path = Path(compositor["root"]) / "full-desktop.b64"
        area_log_path = Path(compositor["area_log"])
        area_block_path = Path(compositor["area_block_path"])
        area_started_path = Path(compositor["area_started_path"])
        area_release_path = Path(compositor["area_release_path"])
        gate_state = {
            "auto_updates": False,
            "last_count": 0,
            "target": 1,
            "manual": False,
            "started": "",
            "release_next": False,
        }
        gate_state_lock = threading.Lock()

        def publish_full(image: Image.Image) -> None:
            temporary = full_desktop_path.with_name(f".{full_desktop_path.name}.tmp")
            temporary.write_text(base64.b64encode(full_desktop(image)).decode("ascii"), encoding="ascii")
            os.replace(temporary, full_desktop_path)

        def normalized(command: str) -> str:
            if command == "/reload":
                return "reload"
            return command.removeprefix("/crowley ")

        def current_agent_image() -> Image.Image:
            try:
                return state["client"].render_agent_capture()
            except (AssertionError, TypeError):
                # Deferred release deliberately precedes the construct click;
                # the real client has no surface in this interval.
                return absent_image

        def set_actual_payload(index: int, image: Image.Image) -> None:
            """Bind one producer payload to the current real Lua VM frame."""

            encoded = png_bytes(image)
            area_payloads[index] = encoded
            payload_path = compositor["payload_paths"][index]
            payload_path.write_text(base64.b64encode(encoded).decode("ascii"), encoding="ascii")
            os.chmod(payload_path, 0o600)

        def assert_actual_publication(index: int) -> None:
            """Bind each gated PNG to the state of the actual dispatched client."""

            with state_lock:
                actual = current_agent_image()
            expected = actual.convert("RGB")
            try:
                if expected.size != (256, 256):
                    raise AssertionError(f"actual Agent publication size mismatch at payload {index}")
                # The compositor response is read back from the exact current
                # Lua VM, including the first three captures; an index alone
                # never establishes scene causality.
                served = Image.open(BytesIO(area_payloads[index])).convert("RGB")
                try:
                    if served.size != expected.size or served.tobytes() != expected.tobytes():
                        raise AssertionError(
                            f"actual Agent publication mismatched dispatched state at payload {index}"
                        )
                finally:
                    served.close()
            finally:
                expected.close()

        def release_area_gate() -> float:
            deadline = time.monotonic() + 12.0
            # The compositor writes the exact current request (including its
            # output filename) before entering the gate.  This is the
            # synchronization boundary; area-log rows are appended only after
            # release and therefore cannot safely drive this write.
            pending: dict[str, Any] = {}
            while not pending_area_path.exists() and time.monotonic() < deadline and not stop_server.is_set():
                time.sleep(0.001)
            released_at = time.monotonic()
            while pending_area_path.exists() and time.monotonic() < deadline and not stop_server.is_set():
                try:
                    pending = json.loads(pending_area_path.read_text(encoding="utf-8"))
                    filename = Path(str(pending["filename"]))
                    index = int(payload_state_path.read_text(encoding="ascii").strip())
                    if 0 <= index < len(area_payloads):
                        with state_lock:
                            actual = current_agent_image()
                        filename.write_bytes(png_bytes(actual))
                        os.chmod(filename, 0o600)
                    gate_started = float(pending.get("gate_started", 0.0)) / 1_000_000.0
                except (OSError, TypeError, ValueError, KeyError, IndexError):
                    gate_started = 0.0
                released_at = max(time.monotonic(), gate_started + 0.002)
                try:
                    area_release_path.unlink(missing_ok=True)
                    area_release_path.write_text(str(int(released_at * 1_000_000)), encoding="ascii")
                    os.chmod(area_release_path, 0o600)
                except FileNotFoundError:
                    pass
                # A token can be consumed by a request whose gate started
                # just before this pending record was replaced.  Re-read and
                # release the newest pending request until the compositor
                # confirms publication by deleting the record.
                wait_until = min(deadline, time.monotonic() + 0.25)
                while pending_area_path.exists() and time.monotonic() < wait_until:
                    time.sleep(0.001)
            return released_at

        def drive_updates() -> None:
            """Publish actual deferred Agent state on a real one-second ticker."""

            # Measure publishes update/1 immediately.  Wait only for that
            # real accepted capture to establish the ticker origin; subsequent
            # producer polls remain unblocked and reject duplicate frames
            # until the external publication tick advances the actual client.
            deadline = time.monotonic() + 20.0
            first_capture: float | None = None
            while time.monotonic() < deadline and not stop_server.is_set():
                for entry in native_provider_trace:
                    if entry.get("stage") == "updates" and entry.get("ordinal") == 1:
                        first_capture = float(entry["capture"])
                        break
                if first_capture is not None:
                    break
                time.sleep(0.005)
            if first_capture is None:
                return
            # The unmodified producer starts its next poll while the first
            # accepted PNG is still being decoded.  Start the first external
            # publication with that measured ~100 ms launch lead; later ticks
            # remain exactly one real second apart.
            next_tick = first_capture + 0.9
            for ordinal in range(2, 100):
                while time.monotonic() < next_tick and not stop_server.is_set():
                    if measurement_error_seen:
                        return
                    time.sleep(min(0.01, max(0.0, next_tick - time.monotonic())))
                if measurement_error_seen or stop_server.is_set():
                    return
                with state_lock:
                    active = state["client"]
                    active.advance_with_timers(1)
                    image = active.render_agent_capture()
                    set_actual_payload(6 + ordinal - 1, image)
                    publish_full(image)
                    set_frame_index(6 + ordinal - 1)
                    set_payload_index(6 + ordinal - 1)
                    assert_actual_publication(6 + ordinal - 1)
                next_tick += 1.0
            while time.monotonic() < next_tick and not stop_server.is_set():
                if measurement_error_seen:
                    return
                time.sleep(min(0.01, max(0.0, next_tick - time.monotonic())))
            if measurement_error_seen or stop_server.is_set():
                return
            with state_lock:
                active = state["client"]
                active.advance_with_timers(1)
                image = active.render_agent_capture()
                set_actual_payload(105, image)
                publish_full(image)
                set_frame_index(105)
                set_payload_index(105)
                assert_actual_publication(105)
            # Let the real resume chat continue while the daemon polls the
            # held/100 surface.  Keeping the area subprocess blocked here
            # would also hold the production capture lock and deadlock the
            # operator's full-screen chat capture before Resume is dispatched.
            with gate_state_lock:
                gate_state["auto_updates"] = False
                area_block_path.unlink(missing_ok=True)
                area_release_path.touch(mode=0o600, exist_ok=True)

        reload_count = 0
        post_success_recovery = False
        action_history: list[dict[str, Any]] = []
        control_history: list[dict[str, Any]] = []

        def record_action(
            command: str,
            before_client: Any,
            before_boot: str,
            before_chat_count: int,
            before_client_reload_count: int,
            reload_count_before: int,
        ) -> None:
            after_client = state["client"]
            after_chat = list(after_client.chat)
            chat_delta = after_chat[before_chat_count:] if after_client is before_client else after_chat
            action_history.append(
                {
                    "command": command,
                    "beforeBoot": before_boot,
                    "afterBoot": str(after_client.ns.Agent.Boot()),
                    "beforeChatCount": before_chat_count,
                    "chatDelta": chat_delta,
                    "afterChatCount": len(after_chat),
                    "beforeClientReloadCount": before_client_reload_count,
                    "afterClientReloadCount": after_client.reload_calls,
                    "reloadCountBefore": reload_count_before,
                    "reloadCountAfter": reload_count,
                }
            )

        def assert_agent_actions(expected: list[str], *, exact: bool = False) -> None:
            for entry in action_history:
                command = entry["command"]
                if command.startswith("agent "):
                    assert any(f"{command} accepted" in line for line in entry["chatDelta"]), entry
            actual = [entry["command"] for entry in action_history]
            if exact:
                assert actual == expected, (actual, expected, action_history)
            else:
                assert actual[: len(expected)] == expected, (actual, expected, action_history)

        def assert_controls(expected: list[tuple[str, bool]]) -> None:
            actual = [(entry["role"], entry["accepted"]) for entry in control_history]
            assert actual == expected, (actual, expected, control_history)

        def persist_action_history() -> None:
            history_path = tmp_path / "action-history.json"
            history_path.write_text(
                json.dumps(
                    {"actions": action_history, "controls": control_history},
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
            history_path.chmod(0o600)

        def apply_action(arguments: list[str]) -> bool | str:
            nonlocal reload_count
            with state_lock:
                if not arguments:
                    return False
                if arguments[0] == "type" and len(arguments) == 4:
                    state["chat"] = True
                    state["text"] = arguments[3]
                    return False
                elif arguments[0] == "key" and len(arguments) >= 2 and arguments[1] == "Return":
                    if not state["chat"]:
                        state["chat"] = True
                        return False
                    command = normalized(str(state["text"]))
                    state["chat"] = False
                    state["text"] = ""
                    before_client = state["client"]
                    before_boot = str(before_client.ns.Agent.Boot())
                    before_chat_count = len(before_client.chat)
                    before_client_reload_count = before_client.reload_calls
                    reload_count_before = reload_count
                    if command == "reload":
                        reload_count += 1
                        payload_index = 1
                        if post_success_recovery:
                            payload_index = post_success_payload_index
                        elif operation_mode == operator.MODE_RECOVER or (
                            measurement_failure and reload_count > 1
                        ):
                            payload_index = recovery_payload_index
                        reload_current_client(
                            payload_index,
                            expect_ordinary=(
                                operation_mode != operator.MODE_MEASURE_DEFERRED or reload_count > 1
                            ),
                        )
                        # The accepted reload creates a fresh Lua VM before
                        # the next production ScreenshotArea call starts.
                        # Release that real post-reload area request through
                        # the same private compositor gate used by the
                        # initial capture; a preemptive token can be
                        # consumed by the preceding request and leave the
                        # recovery proof waiting for its full deadline.
                        record_action(
                            command,
                            before_client,
                            before_boot,
                            before_chat_count,
                            before_client_reload_count,
                            reload_count_before,
                        )
                        return False
                    if command == "agent defer":
                        # The helper's actual chat action belongs to the
                        # currently visible Lua VM.  A new deferred VM is
                        # created only by the later accepted /reload action.
                        before_defer_lifecycle = state["client"].ns.Agent.Lifecycle()
                        before_defer_marker = (
                            state["client"]
                            ._json_table(state["client"].lua.globals().CrowleyDB)
                            .get("nativeConstruction")
                        )
                        before_defer_reload = state["client"].reload_calls
                        state["client"].slash(command)
                        record_action(
                            command,
                            before_client,
                            before_boot,
                            before_chat_count,
                            before_client_reload_count,
                            reload_count_before,
                        )
                        after_defer_marker = (
                            state["client"]
                            ._json_table(state["client"].lua.globals().CrowleyDB)
                            .get("nativeConstruction")
                        )
                        if operation_mode in {
                            operator.MODE_MEASURE_DEFERRED,
                            operator.MODE_CONTROL_PREFLIGHT,
                        }:
                            assert before_defer_lifecycle == "ordinary"
                            assert before_defer_marker is None
                            assert state["client"].reload_calls == before_defer_reload
                            assert state["client"].ns.Agent.Lifecycle() == "ordinary"
                            assert isinstance(after_defer_marker, dict)
                            assert after_defer_marker.get("state") == "armed"
                            assert after_defer_marker.get("token") == state["client"].ns.Agent.Boot()
                            assert state["client"].ns.Scanner.NativeConstructionFence() is True
                        if operation_mode == operator.MODE_CONTROL_PREFLIGHT:
                            # The preflight recovery capture follows the
                            # intentional Construct refusal and must decode
                            # this newly armed ordinary fence.  Replace the
                            # already-consumed baseline payload with the
                            # actual post-defer frame; no future mode uses
                            # payload zero as a synthetic baseline.
                            state["client"].publish_agent()
                            armed_image = current_agent_image()
                            armed_payload = compositor["payload_paths"][0]
                            set_actual_payload(0, armed_image)
                            os.chmod(armed_payload, 0o600)
                            armed_image.close()
                            publish_full(current_agent_image())
                        return False
                    state["client"].slash(command)
                    record_action(
                        command,
                        before_client,
                        before_boot,
                        before_chat_count,
                        before_client_reload_count,
                        reload_count_before,
                    )
                    publish_full(current_agent_image())
                    if command == "agent hold":
                        held_image = current_agent_image()
                        set_actual_payload(5, held_image)
                        publish_full(held_image)
                        set_frame_index(5)
                        set_payload_index(5)
                        assert_actual_publication(5)
                        area_block_path.touch(mode=0o600, exist_ok=True)
                        area_release_path.unlink(missing_ok=True)
                        return True
                    if command == "agent measure":
                        measured_image = current_agent_image()
                        set_actual_payload(6, measured_image)
                        publish_full(measured_image)
                        set_frame_index(6)
                        set_payload_index(6)
                        with gate_state_lock:
                            gate_state["auto_updates"] = True
                            area_block_path.unlink(missing_ok=True)
                            area_release_path.touch(mode=0o600, exist_ok=True)
                        assert_actual_publication(6)
                        return "measure"
                    if command == "agent resume":
                        resumed_image = current_agent_image()
                        set_actual_payload(106, resumed_image)
                        publish_full(resumed_image)
                        set_frame_index(106)
                        set_payload_index(106)
                        with gate_state_lock:
                            gate_state["auto_updates"] = False
                            area_block_path.unlink(missing_ok=True)
                            area_release_path.unlink(missing_ok=True)
                            pending_area_path.unlink(missing_ok=True)
                        assert_actual_publication(106)
                        return False
                    if command == "agent finalize":
                        finalized_image = current_agent_image()
                        set_actual_payload(107, finalized_image)
                        publish_full(finalized_image)
                        set_frame_index(107)
                        set_payload_index(107)
                        assert_actual_publication(107)
                        return False
                    return False
                elif arguments[0] == "mousemove" and len(arguments) >= 4:
                    pointer[:] = [int(arguments[-2]), int(arguments[-1]), 0x400]
                    return False
                elif arguments[0] == "mousedown":
                    # Derive the Lua control from the real emitted pointer;
                    # operation mode never rewrites Construct into Restore.
                    role = "restore" if pointer[0] >= 1788 else "construct"
                    before_lifecycle = state["client"].ns.Agent.Lifecycle()
                    before_marker = (
                        state["client"]
                        ._json_table(state["client"].lua.globals().CrowleyDB)
                        .get("nativeConstruction")
                    )
                    before_reload = state["client"].reload_calls
                    state["client"].click_native(role)
                    after_lifecycle = state["client"].ns.Agent.Lifecycle()
                    after_marker = (
                        state["client"]
                        ._json_table(state["client"].lua.globals().CrowleyDB)
                        .get("nativeConstruction")
                    )
                    accepted = (role == "restore" and state["client"].reload_calls > before_reload) or (
                        role == "construct"
                        and before_lifecycle == "deferred"
                        and after_lifecycle == "constructed"
                        and isinstance(after_marker, dict)
                        and after_marker.get("state") == "constructed"
                    )
                    control_history.append(
                        {
                            "role": role,
                            "beforeLifecycle": before_lifecycle,
                            "afterLifecycle": after_lifecycle,
                            "beforeMarker": before_marker,
                            "afterMarker": after_marker,
                            "beforeReloadCount": before_reload,
                            "afterReloadCount": state["client"].reload_calls,
                            "accepted": accepted,
                        }
                    )
                    if not accepted:
                        # The armed ordinary VM intentionally refuses a
                        # preflight Construct click.  Keep its fence and
                        # SavedVariables visible until recovery admission;
                        # no synthetic scene or reload is allowed here.
                        if role != "construct":
                            raise AssertionError("unexpected refused native control")
                        if before_lifecycle != after_lifecycle or before_marker != after_marker:
                            raise AssertionError("refused Construct mutated the Lua state")
                        if state["client"].reload_calls != before_reload:
                            raise AssertionError("refused Construct reloaded the Lua VM")
                        state["construct_refused"] = True
                        publish_full(current_agent_image())
                        return False
                    if role == "restore":
                        # Restore's accepted Lua handler calls ReloadUI.  Read
                        # that VM's just-written SavedVariables and construct
                        # the fresh boot only at this boundary.
                        reload_current_client(
                            post_success_payload_index if post_success_recovery else recovery_payload_index
                        )
                    publish_full(current_agent_image())
                    if role == "construct":
                        constructed_image = current_agent_image()
                        set_actual_payload(4, constructed_image)
                        publish_full(constructed_image)
                        set_frame_index(4)
                        set_payload_index(4)
                        assert_actual_publication(4)
                        area_block_path.touch(mode=0o600, exist_ok=True)
                        area_release_path.unlink(missing_ok=True)
                        # The producer's construct frame is held until the
                        # actual addon click has committed on the runtime
                        # client; this is the physical game boundary.
                        return True
                return False

        def action_bridge() -> None:
            while not stop_server.is_set():
                try:
                    with action_log.open("r", encoding="utf-8") as stream:
                        stream.seek(int(state["offset"]))
                        while True:
                            line = stream.readline()
                            if not line:
                                state["offset"] = stream.tell()
                                break
                            fields = line.rstrip("\n").split("\t")
                            if len(fields) < 3:
                                continue
                            pid = fields[0]
                            arguments = fields[2:]
                            release_after_ack = apply_action(arguments)
                            (action_ack / pid).touch(mode=0o600, exist_ok=True)
                            if release_after_ack == "measure":
                                threading.Thread(target=drive_updates, daemon=True).start()
                            elif release_after_ack:
                                threading.Thread(target=release_area_gate, daemon=True).start()
                except OSError:
                    pass
                time.sleep(0.002)

        bridge_thread = threading.Thread(target=action_bridge, daemon=True)
        bridge_thread.start()

        # Hold every producer request behind an explicit stage boundary.  The
        # initial release lets the first absence frame through; subsequent
        # releases are issued either by the corresponding addon action or by
        # the 1 Hz update scheduler after it advances the real runtime client.
        area_block_path.unlink(missing_ok=True)
        area_release_path.unlink(missing_ok=True)

        def area_gate_controller() -> None:
            """Keep each real producer request behind the corresponding game boundary."""

            while not stop_server.is_set():
                try:
                    rows = (
                        json.loads(area_log_path.read_text(encoding="utf-8"))
                        if area_log_path.exists()
                        else []
                    )
                    count = len(rows) if isinstance(rows, list) else 0
                    with gate_state_lock:
                        target = int(gate_state["target"])
                        auto_updates = bool(gate_state["auto_updates"])
                        release_next = bool(gate_state["release_next"])
                        if count >= target:
                            gate_state["last_count"] = count
                            next_target = count + 1
                            gate_state["target"] = next_target
                            gate_state["manual"] = next_target in {4, 5, 6}
                            gate_state["started"] = (
                                area_started_path.read_text(encoding="ascii")
                                if area_started_path.exists()
                                else ""
                            )
                    if release_next and pending_area_path.exists():
                        area_release_path.write_text(str(int(time.monotonic() * 1_000_000)), encoding="ascii")
                        os.chmod(area_release_path, 0o600)
                        with gate_state_lock:
                            gate_state["release_next"] = False
                    elif count >= target:
                        with gate_state_lock:
                            auto_updates = bool(gate_state["auto_updates"])
                            if auto_updates:
                                area_block_path.unlink(missing_ok=True)
                                area_release_path.touch(mode=0o600, exist_ok=True)
                            else:
                                area_block_path.unlink(missing_ok=True)
                                area_release_path.touch(mode=0o600, exist_ok=True)
                    elif target < 4:
                        # Entry, reload, and post-reset absence captures are
                        # ordinary producer calls. Release them without
                        # waiting for a state transition; only construction
                        # and later measurement frames are held deliberately.
                        area_release_path.touch(mode=0o600, exist_ok=True)
                except (OSError, ValueError, TypeError):
                    pass
                time.sleep(0.01)

        area_gate_thread = threading.Thread(target=area_gate_controller, daemon=True)
        area_gate_thread.start()

        def ocr(_path: Path) -> str:
            with state_lock:
                return "say: " + str(state["text"]) if state["chat"] else ""

        operator_instance = operator.NativeCalibrationOperator(
            mode=operation_mode,
            generation=7,
            config_path=config_path,
            template_manifest=manifest,
            client=client,
            screen=screen,
            input_device=input_device,
            ocr=ocr,
            receipt_root=tmp_path / "operator-receipts",
            helper_source_sha256=hashlib.sha256(Path(operator.__file__).read_bytes()).hexdigest(),
            dependencies=operator._source_bindings(screen, manifest),
        )
        assert not driver.backend._cancel_active.is_set()
        try:
            if fixture_case == "watchdog-readiness":
                input_device.watchdog.close()
                with pytest.raises(operator.OperatorError):
                    operator_instance.run()
                assert action_log.read_text(encoding="utf-8") == ""
                assert list(action_ack.iterdir()) == []
                receipt = json.loads(
                    next((tmp_path / "operator-receipts").glob("*/receipt.json")).read_text()
                )
                assert receipt["outcome"] == "failure"
                assert any(event["name"] == "terminal" for event in receipt["events"])
                assert action_history == []
                assert reload_count == 0
                return

            if fixture_case == "pressed-budget":
                # Keep the production OwnedEmitter and Watchdog.  The test
                # only supplies a bounded scheduling seam: after the first
                # real keyboard emitter has reported READY and the watchdog
                # has acknowledged ownership, consume its short deadline
                # before the helper can send GO.
                created_emitters: list[Any] = []
                real_new_emitter = input_device._new_emitter

                def record_emitter(
                    action: Any,
                    *,
                    release_action: Any = (),
                    deadline_monotonic: float | None = None,
                ) -> Any:
                    emitter = real_new_emitter(
                        action,
                        release_action=release_action,
                        deadline_monotonic=deadline_monotonic,
                    )
                    created_emitters.append(emitter)
                    return emitter

                input_device._new_emitter = record_emitter  # type: ignore[method-assign]
                real_key_return = input_device.key_return
                first_key_deadline = time.monotonic() + 5.0

                def bounded_first_key(*, deadline_monotonic: float | None = None) -> None:
                    return real_key_return(deadline_monotonic=first_key_deadline)

                input_device.key_return = bounded_first_key  # type: ignore[method-assign]
                real_publish_watchdog = operator._publish_watchdog
                watchdog_acknowledged = False
                real_watchdog_clear = input_device.watchdog.clear
                watchdog_clear_count = 0

                def clear_watchdog() -> None:
                    nonlocal watchdog_clear_count
                    watchdog_clear_count += 1
                    return real_watchdog_clear()

                input_device.watchdog.clear = clear_watchdog  # type: ignore[method-assign]

                def consume_after_watchdog(*args: Any, **kwargs: Any) -> None:
                    nonlocal watchdog_acknowledged
                    real_publish_watchdog(*args, **kwargs)
                    keys = kwargs.get("keys", frozenset())
                    if keys == {"Return"} and not watchdog_acknowledged:
                        watchdog_acknowledged = True
                        time.sleep(5.2)

                monkeypatch.setattr(operator, "_publish_watchdog", consume_after_watchdog)
                with pytest.raises(operator.OperatorError, match="cannot fit"):
                    operator_instance.run()
                assert watchdog_acknowledged
                assert watchdog_clear_count == 1
                assert action_log.read_text(encoding="utf-8") == ""
                assert list(action_ack.iterdir()) == []
                assert input_device.cleanup_failures == []
                assert created_emitters
                first_emitter = created_emitters[0]
                assert first_emitter._process is not None
                assert not first_emitter._process.is_alive()
                assert first_emitter._process.exitcode is not None
                assert all(
                    getattr(first_emitter, descriptor) == -1
                    for descriptor in ("_gate_read", "_gate_write", "_status_read", "_status_write")
                )
                receipt = json.loads(
                    next((tmp_path / "operator-receipts").glob("*/receipt.json")).read_text()
                )
                assert receipt["outcome"] == "failure"
                assert any(event["name"] == "terminal" for event in receipt["events"])
                assert action_history == []
                assert reload_count == 0
                return

            if fixture_case == "post-handoff-cancel":
                with pytest.raises(operator.OperatorInterrupted):
                    operator_instance.run()
                receipt = json.loads(
                    next((tmp_path / "operator-receipts").glob("*/receipt.json")).read_text()
                )
                assert receipt["outcome"] == "failure"
                assert receipt["failureCode"] == "interrupted"
                assert any(event["name"] == "reservation_cancelled" for event in receipt["events"])
                assert not driver.guardian.armed
                assert_agent_actions(
                    ["agent defer", "reload", "agent release", "agent hold", "agent measure"],
                    exact=True,
                )
                assert reload_count == 1
                assert_controls([("construct", True)])
                return

            if measurement_failure:
                with pytest.raises(operator.OperatorError, match="actual fixture measurement failure"):
                    operator_instance.run()
                assert daemon.controller.status().state is ControllerState.PAUSED
                assert not driver.guardian.armed
                receipt_paths = list((tmp_path / "operator-receipts").glob("*/receipt.json"))
                assert len(receipt_paths) == 1
                receipt = json.loads(receipt_paths[0].read_text(encoding="utf-8"))
                assert receipt["outcome"] == "failure"
                assert receipt["failureCode"] == "native_admission_refused"
                assert any(event["name"] == "recovery_complete" for event in receipt["events"])
                assert any(
                    event["name"] == "terminal" and event.get("state") == "failure"
                    for event in receipt["events"]
                )
                assert_agent_actions(
                    [
                        "agent defer",
                        "reload",
                        "agent release",
                        "agent hold",
                        "agent measure",
                        "agent recover",
                    ],
                    exact=True,
                )
                assert reload_count == 1
                assert_controls([("construct", True), ("restore", True)])
                return

            if operation_mode == operator.MODE_CONTROL_PREFLIGHT:
                result = operator_instance.run()
                assert result["ok"] is True
                assert daemon.controller.status().state is ControllerState.PAUSED
                assert not driver.guardian.armed
                assert any(
                    event["name"] == "recovery_complete"
                    for event in json.loads(
                        next((tmp_path / "operator-receipts").glob("*/receipt.json")).read_text()
                    )["events"]
                )
                assert_agent_actions(["agent defer", "agent recover"], exact=True)
                assert state["construct_refused"] is True
                assert reload_count == 0
                assert_controls([("construct", False), ("restore", True)])
                return

            if operation_mode == operator.MODE_RECOVER:
                result = operator_instance.run()
                assert result["ok"] is True
                assert daemon.controller.status().state is ControllerState.PAUSED
                assert not driver.guardian.armed
                assert daemon.controller.native_construction_checkpoint() is None
                receipt = json.loads(
                    next((tmp_path / "operator-receipts").glob("*/receipt.json")).read_text()
                )
                recovery_events = [event for event in receipt["events"] if event["name"] == "recovery_begin"]
                assert recovery_events and recovery_events[-1]["kind"] == recovery_kind
                assert any(event["name"] == "recovery_complete" for event in receipt["events"])
                assert_agent_actions(
                    ["agent recover"] if recovery_kind == "restore" else ["reload"],
                    exact=True,
                )
                assert reload_count == (0 if recovery_kind == "restore" else 1)
                assert_controls([("restore", True)] if recovery_kind == "restore" else [])
                return

            result = operator_instance.run()
            assert result["ok"] is True
            expected_provider_stages = [
                ("construct", 0),
                ("held", 0),
                *(("updates", ordinal) for ordinal in range(1, 100)),
                ("held", 100),
                ("resume", 0),
            ]
            actual_provider_stages = [
                (entry["stage"], entry["ordinal"]) for entry in native_provider_trace if "error" not in entry
            ]
            assert actual_provider_stages == expected_provider_stages
            assert_agent_actions(
                [
                    "agent defer",
                    "reload",
                    "agent release",
                    "agent hold",
                    "agent measure",
                    "agent resume",
                    "agent finalize",
                ],
                exact=True,
            )
            assert reload_count == 1
            assert_controls([("construct", True)])
            assert state["client"].ns.Agent.Lifecycle() == "finalized"
            assert daemon.controller.status().state is ControllerState.INPUT_CALIBRATION
            assert not driver.guardian.armed
            assert daemon.controller._native_calibrated is True
            assert daemon.controller._input_calibrated is False
            assert daemon.controller.native_construction_checkpoint() is not None
            # Exercise the same public AF_UNIX boundary as the helper.  The
            # controller object is deliberately not used as a test shortcut:
            # the immediate pause response carries only controller fields,
            # and the fresh recovery owner must use its returned generation.
            before_pause = client.status(deadline=time.monotonic() + 8.0)["status"]
            paused_reply = client.pause(7, deadline=time.monotonic() + 8.0)
            paused_status = paused_reply["status"]
            assert paused_status["state"] == ControllerState.PAUSED.value
            assert paused_status["generation"] > 7
            assert paused_status["generation"] > before_pause["generation"]
            assert paused_status["leaseGeneration"] > before_pause["leaseGeneration"]
            paused_generation = paused_status["generation"]
            assert daemon.controller._native_calibrated is True
            assert daemon.controller._input_calibrated is False
            assert not driver.guardian.armed
            assert recovery_ordinary.ns.Agent.Lifecycle() == "ordinary"
            assert recovery_ordinary.ns.Agent.Boot() != ordinary_boot
            post_success_recovery = True
            with state_lock:
                # Keep the actual finalized native-construction VM visible
                # through the fresh recovery admission.  The Restore click
                # below is the only boundary that creates its ordinary boot.
                final_image = current_agent_image()
                payload_path = compositor["payload_paths"][post_success_payload_index]
                set_actual_payload(post_success_payload_index, final_image)
                os.chmod(payload_path, 0o600)
                publish_full(final_image)
                set_frame_index(0)
                set_payload_index(post_success_payload_index)
            fresh_gated_tool = operator.PinnedInputTool.from_root(gated_tool_root)
            monkeypatch.setattr(operator.PinnedInputTool, "load", lambda: fresh_gated_tool)
            fresh_screen = operator.X11Screen(config_path, tmp_path / "fresh-screen-receipts")
            fresh_watchdog = operator.Watchdog(fresh_gated_tool, interval=0.02, environment=watchdog_env)
            fresh_input = operator.FixedInput(
                fresh_gated_tool,
                watchdog=fresh_watchdog,
                environment=watchdog_env,
            )
            fresh_operator = operator.NativeCalibrationOperator(
                mode=operator.MODE_RECOVER,
                generation=paused_generation,
                config_path=config_path,
                template_manifest=manifest,
                client=client,
                screen=fresh_screen,
                input_device=fresh_input,
                ocr=ocr,
                receipt_root=tmp_path / "operator-receipts",
                helper_source_sha256=hashlib.sha256(Path(operator.__file__).read_bytes()).hexdigest(),
                dependencies=operator._source_bindings(fresh_screen, manifest),
            )
            recovered = fresh_operator.run()
            fresh_screen.close()
            assert_agent_actions(
                [
                    "agent defer",
                    "reload",
                    "agent release",
                    "agent hold",
                    "agent measure",
                    "agent resume",
                    "agent finalize",
                    "agent recover",
                ],
                exact=True,
            )
            assert_controls([("construct", True), ("restore", True)])
            assert recovered["ok"] is True
            recovered_status = daemon.controller.status()
            assert recovered_status.state is ControllerState.PAUSED
            assert daemon.controller._native_calibrated is True
            assert daemon.controller._input_calibrated is False
            assert daemon.controller.native_construction_checkpoint() is None
            assert not driver.guardian.armed
            assert post_success_ordinary.ns.Agent.Lifecycle() == "ordinary"
            assert post_success_ordinary.ns.Agent.Boot() != recovery_ordinary.ns.Agent.Boot()
            receipt_paths = list((tmp_path / "operator-receipts").glob("*/receipt.json"))
            assert len(receipt_paths) == 2
            receipt = json.loads(sorted(receipt_paths)[-1].read_text(encoding="utf-8"))
            post_recovery_events = [event for event in receipt["events"] if event["name"] == "recovery_begin"]
            assert post_recovery_events and post_recovery_events[-1]["kind"] == "restore"
            assert (
                receipt["helperSourceSha256"]
                == hashlib.sha256(Path(operator.__file__).read_bytes()).hexdigest()
            )
            dependency_hashes = receipt["dependencySha256"]
            for dependency_name in (
                "profile-config",
                "template-construct",
                "template-restore",
                "producer-manifest",
                "pinned-input-tool",
            ):
                assert re.fullmatch(r"[0-9a-f]{64}", dependency_hashes[dependency_name])
            # Read every expected dependency independently from the receipt;
            # a digest-shaped value copied out of the receipt is not
            # provenance evidence.  The helper binds these eight native
            # modules by basename, so assert the exact known bytes for each.
            native_module_names = (
                "crowley.session.guardian",
                "crowley.session.input_tool",
                "crowley.session.config",
                "crowley.session.driver",
                "crowley.session.decoder",
                "crowley.session.cli",
                "crowley.session.daemon",
                "crowley.session.controller",
            )
            expected_dependencies: dict[str, str] = {}
            for module_name in native_module_names:
                native_module = importlib.import_module(module_name)
                native_path = Path(native_module.__file__ or "")
                assert native_path.is_file()
                expected_dependencies[native_path.name] = hashlib.sha256(native_path.read_bytes()).hexdigest()
            expected_dependencies["profile-config"] = hashlib.sha256(config_path.read_bytes()).hexdigest()
            expected_dependencies["template-construct"] = hashlib.sha256(
                Path(manifest.construct.path).read_bytes()
            ).hexdigest()
            expected_dependencies["template-restore"] = hashlib.sha256(
                Path(manifest.restore.path).read_bytes()
            ).hexdigest()
            producer_path = Path(screen.config.profile.telemetry_region_executable)
            expected_dependencies["producer-manifest"] = hashlib.sha256(
                producer_path.read_bytes()
            ).hexdigest()
            expected_dependencies["producer-" + producer_path.name] = expected_dependencies[
                "producer-manifest"
            ]
            from crowley.session.input_tool import PRIVATE_TOOL_BASENAME

            expected_dependencies["pinned-input-tool"] = hashlib.sha256(
                (gated_tool_root / PRIVATE_TOOL_BASENAME).read_bytes()
            ).hexdigest()
            from tools import template_matcher_runtime as matcher_runtime

            matcher_binary = matcher_runtime.DEFAULT_ARTIFACT_ROOT / matcher_runtime.ARTIFACT_NAME
            matcher_binary_digest = hashlib.sha256(matcher_binary.read_bytes()).hexdigest()
            assert matcher_binary_digest == matcher_runtime.EXPECTED_ARTIFACT_SHA256
            expected_dependencies["template-matcher-binary"] = matcher_binary_digest
            expected_dependencies["template-matcher-runtime.py"] = hashlib.sha256(
                Path(matcher_runtime.__file__).read_bytes()
            ).hexdigest()
            for source_name, source_digest in matcher_runtime.EXPECTED_SOURCE_HASHES.items():
                expected_dependencies[f"template-matcher-{source_name}"] = source_digest
            for dependency_name, expected_digest in expected_dependencies.items():
                assert dependency_name in dependency_hashes
                assert dependency_hashes[dependency_name] == expected_digest
        finally:
            persist_action_history()
            stop_server.set()
            listener.close()
            server_thread.join(timeout=3.0)
            bridge_thread.join(timeout=1.0)
            area_gate_thread.join(timeout=1.0)
            for worker in server_workers:
                worker.join(timeout=2.0)
            # FixedInput owns the real watchdog and its sealed input tool;
            # close that production owner before the driver's Guardian is
            # asked to prove the desktop is released.
            input_device.close()
            screen.close()
            for created in screen_backend:
                created.input_tool.close()
            driver.close()
            child.terminate()
            child.wait(timeout=3)


def test_measure_deferred_public_admission_retains_real_failure_status(tmp_path: Path) -> None:
    """Exercise prepare/bootstrap/native-calibrate/status on the actual daemon path."""

    from crowley.session.cli import (
        SessionIPC,
        _BoundedIPCReader,
        _encode_bounded_record,
        _parse_bounded_json,
        _socket_request,
    )
    from tests.test_session_native_regressions import _construction_daemon, _construction_frame

    daemon, driver, identity, child = _construction_daemon(tmp_path)
    identity = replace(identity, fingerprint="a" * 64)
    driver.backend.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
    begin = _construction_frame(identity, boot="boot-a", sequence=2)
    begin["captureMonotonic"] = 1.0
    daemon._native_construction_observation_provider = lambda: begin
    socket_path = tmp_path / "measure-operator.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    os.chmod(socket_path, 0o600)
    listener.listen(8)
    listener.settimeout(0.1)
    stop = threading.Event()
    workers: list[threading.Thread] = []
    ipc = SessionIPC(daemon.controller, owner=daemon)

    def serve_connection(connection: socket.socket) -> None:
        with connection:
            reader = _BoundedIPCReader(connection)
            raw = reader.read_record(4096)
            if raw is None:
                return
            request = _parse_bounded_json(raw)
            assert isinstance(request, dict)
            try:
                response = ipc.dispatch(request)
            except Exception as exc:
                response = {"ok": False, "error": str(exc)}
            try:
                connection.sendall(_encode_bounded_record(response, 524288))
            except OSError:
                pass

    def serve() -> None:
        while not stop.is_set():
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            except OSError:
                if stop.is_set():
                    return
                raise
            worker = threading.Thread(target=serve_connection, args=(connection,), daemon=True)
            workers.append(worker)
            worker.start()

    server = threading.Thread(target=serve, daemon=True)
    server.start()
    client = operator.DaemonClient(socket_path, request_fn=_socket_request, timeout=15.0)
    try:
        prepared = client.prepare(7)
        binding = operator.ReservationBinding.from_record(prepared["reservation"], expected_generation=7)
        bootstrapped = client.bootstrap(7, binding)
        assert bootstrapped["handshake"]["state"] == "running"
        started = client.native_calibrate(7, deadline=time.monotonic() + 8.0)
        status = started["status"]
        assert status["state"] == "NATIVE_CALIBRATION"
        assert status["calibrationOperation"]["kind"] == "native"
        deadline = time.monotonic() + 12.0
        while time.monotonic() < deadline:
            status = client.calibration_status(deadline=deadline)["status"]
            operation = status["calibrationOperation"]
            if operation["state"] in {"complete", "error"}:
                break
            time.sleep(0.05)
        assert operation["state"] in {"complete", "error"}
        if operation["state"] == "error":
            assert isinstance(operation["error"], str) and operation["error"]
    finally:
        stop.set()
        listener.close()
        server.join(timeout=2.0)
        for worker in workers:
            worker.join(timeout=2.0)
        daemon.request_shutdown()
        driver.close()
        child.terminate()
        child.wait(timeout=3)


def test_actual_bootstrap_reply_loss_after_prepare_expiry_cancels_known_id(tmp_path: Path) -> None:
    """Keep exact cleanup for a committed bootstrap whose reply misses its short bound."""

    from crowley.session.cli import (
        SessionIPC,
        _BoundedIPCReader,
        _encode_bounded_record,
        _parse_bounded_json,
    )
    from tests.test_session_native_regressions import _construction_daemon, _construction_frame

    daemon, driver, identity, child = _construction_daemon(tmp_path)
    # Keep the real prepare expiry just beyond the five-second cleanup grace
    # so the owner can cross the old bound while the actor remains armed.
    daemon.config = replace(daemon.config, reload_deadline_seconds=6.0)
    identity = replace(identity, fingerprint="a" * 64)
    driver.backend.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
    begin = _construction_frame(identity, boot="boot-a", sequence=2)
    begin["captureMonotonic"] = 1.0
    daemon._native_construction_observation_provider = lambda: begin
    socket_path = tmp_path / "bootstrap-loss.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    os.chmod(socket_path, 0o600)
    listener.listen(8)
    listener.settimeout(0.1)
    stop = threading.Event()
    workers: list[threading.Thread] = []
    seen: list[dict[str, object]] = []
    cancel_records: list[dict[str, object]] = []
    ipc = SessionIPC(daemon.controller, owner=daemon)

    def serve_connection(connection: socket.socket) -> None:
        with connection:
            reader = _BoundedIPCReader(connection)
            raw = reader.read_record(4096)
            if raw is None:
                return
            request = _parse_bounded_json(raw)
            assert isinstance(request, dict)
            seen.append(request)
            response = ipc.dispatch(request)
            if request.get("command") == "native_construction_recovery_cancel":
                cancel_records.append(response)
            if request.get("command") == "native_construction_bootstrap":
                # The daemon has committed and extended the same reservation
                # before this deliberate transport loss.
                time.sleep(0.6)
            try:
                connection.sendall(_encode_bounded_record(response, 524288))
            except OSError:
                pass

    def serve() -> None:
        while not stop.is_set():
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            except OSError:
                if stop.is_set():
                    return
                raise
            worker = threading.Thread(target=serve_connection, args=(connection,), daemon=True)
            workers.append(worker)
            worker.start()

    server = threading.Thread(target=serve, daemon=True)
    server.start()
    actor = operator.CancellationActor(
        socket_path,
        generation=7,
        reservation_id="",
        deadline=time.monotonic() + 20.0,
        owner_pid=os.getpid(),
        owner_start=operator._proc_start(os.getpid()),
    )
    actor.start()
    try:
        prepared = actor.call("prepare", generation=7, preflight=False, deadline=time.monotonic() + 10.0)
        reservation = prepared["reservation"]
        old_expiry = float(reservation["expiresMonotonic"])
        with pytest.raises(operator.AdmissionIndeterminate):
            actor.call(
                "bootstrap",
                generation=7,
                reservation_id=reservation["reservationId"],
                expected_constructor_boot=reservation["expectedConstructorBoot"],
                deadline=time.monotonic() + 0.2,
            )
        remaining = old_expiry - time.monotonic()
        if remaining > 0:
            time.sleep(remaining + 0.2)
        # The private read deadline may expire before the actor serializes its
        # complete indeterminate frame.  In that incomplete-reply case EOF is
        # allowed to cancel the known ID before the old expiry; either outcome
        # is valid only with one exact cancellation and no retry.
        assert actor._process is not None
        if actor._process.is_alive():
            actor.abandon()
            actor._process.join(timeout=4.0)
        assert not actor._process.is_alive()
        assert [request["command"] for request in seen] == [
            "native_construction_prepare",
            "native_construction_bootstrap",
            "native_construction_recovery_cancel",
        ]
    finally:
        # EOF is the owner-death path: the actor must retain its exact known
        # reservation and issue cancellation before it exits.
        actor.abandon()
        if actor._process is not None:
            actor._process.join(timeout=4.0)
        stop.set()
        listener.close()
        server.join(timeout=3.0)
        for worker in workers:
            worker.join(timeout=3.0)
        driver.close()
        child.terminate()
        child.wait(timeout=3)
    assert [request["command"] for request in seen] == [
        "native_construction_prepare",
        "native_construction_bootstrap",
        "native_construction_recovery_cancel",
    ]
    assert seen[2]["reservationId"] == reservation["reservationId"]
    assert len(cancel_records) == 1
    assert cancel_records[0]["handshake"]["state"] == "cancelled"
    assert cancel_records[0]["reservation"]["reservationId"] == reservation["reservationId"]


def test_complete_bootstrap_server_loss_retains_actor_until_owner_eof(tmp_path: Path) -> None:
    """A complete indeterminate reply keeps exact-ID ownership until EOF."""

    from crowley.session.cli import (
        SessionIPC,
        _BoundedIPCReader,
        _encode_bounded_record,
        _parse_bounded_json,
    )
    from tests.test_session_native_regressions import _construction_daemon, _construction_frame

    daemon, driver, identity, child = _construction_daemon(tmp_path)
    daemon.config = replace(daemon.config, reload_deadline_seconds=6.0)
    identity = replace(identity, fingerprint="a" * 64)
    driver.backend.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
    begin = _construction_frame(identity, boot="boot-a", sequence=2)
    begin["captureMonotonic"] = 1.0
    daemon._native_construction_observation_provider = lambda: begin
    socket_path = tmp_path / "bootstrap-complete-loss.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    os.chmod(socket_path, 0o600)
    listener.listen(8)
    listener.settimeout(0.1)
    stop = threading.Event()
    workers: list[threading.Thread] = []
    seen: list[dict[str, object]] = []
    cancel_records: list[dict[str, object]] = []
    ipc = SessionIPC(daemon.controller, owner=daemon)

    def serve_connection(connection: socket.socket) -> None:
        with connection:
            reader = _BoundedIPCReader(connection)
            raw = reader.read_record(4096)
            if raw is None:
                return
            request = _parse_bounded_json(raw)
            assert isinstance(request, dict)
            seen.append(request)
            response = ipc.dispatch(request)
            if request.get("command") == "native_construction_bootstrap":
                # The daemon has committed the extension.  The peer then
                # disappears before delivering the complete response frame.
                return
            if request.get("command") == "native_construction_recovery_cancel":
                cancel_records.append(response)
            try:
                connection.sendall(_encode_bounded_record(response, 524288))
            except OSError:
                pass

    def serve() -> None:
        while not stop.is_set():
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            except OSError:
                if stop.is_set():
                    return
                raise
            worker = threading.Thread(target=serve_connection, args=(connection,), daemon=True)
            workers.append(worker)
            worker.start()

    server = threading.Thread(target=serve, daemon=True)
    server.start()
    actor = operator.CancellationActor(
        socket_path,
        generation=7,
        reservation_id="",
        deadline=time.monotonic() + 20.0,
        owner_pid=os.getpid(),
        owner_start=operator._proc_start(os.getpid()),
    )
    actor.start()
    reservation = None
    try:
        prepared = actor.call("prepare", generation=7, preflight=False, deadline=time.monotonic() + 10.0)
        reservation = prepared["reservation"]
        old_expiry = float(reservation["expiresMonotonic"])
        with pytest.raises(operator.AdmissionIndeterminate):
            actor.call(
                "bootstrap",
                generation=7,
                reservation_id=reservation["reservationId"],
                expected_constructor_boot=reservation["expectedConstructorBoot"],
                deadline=time.monotonic() + 5.0,
            )
        assert actor._channel_poisoned
        assert actor._control_write >= 0
        with pytest.raises(operator.OperatorError, match="unusable"):
            actor.update(
                generation=7,
                reservation_id=reservation["reservationId"],
                deadline=time.monotonic() + 5.0,
            )
        with pytest.raises(operator.OperatorError, match="(?:unusable|poisoned)"):
            actor.call(
                "recheck",
                generation=7,
                reservation_id=reservation["reservationId"],
                deadline=time.monotonic() + 5.0,
            )
        remaining = old_expiry - time.monotonic()
        if remaining > 0:
            time.sleep(remaining + 0.2)
        assert actor._process is not None and actor._process.is_alive()
        assert [request["command"] for request in seen] == [
            "native_construction_prepare",
            "native_construction_bootstrap",
        ]
        actor.close()
        assert actor._process is not None and not actor._process.is_alive()
    finally:
        actor.abandon()
        if actor._process is not None:
            actor._process.join(timeout=4.0)
        stop.set()
        listener.close()
        server.join(timeout=3.0)
        for worker in workers:
            worker.join(timeout=3.0)
        driver.close()
        child.terminate()
        child.wait(timeout=3)
    assert reservation is not None
    assert [request["command"] for request in seen] == [
        "native_construction_prepare",
        "native_construction_bootstrap",
        "native_construction_recovery_cancel",
    ]
    assert seen[-1]["reservationId"] == reservation["reservationId"]
    assert len(cancel_records) == 1
    assert cancel_records[0]["handshake"]["state"] == "cancelled"
    assert cancel_records[0]["reservation"]["reservationId"] == reservation["reservationId"]


def test_actual_measurement_error_pauses_and_recovers_with_empty_id(tmp_path: Path) -> None:
    """A real terminal native error must hand off through a newer PAUSED generation."""

    from crowley.session.cli import (
        SessionIPC,
        _BoundedIPCReader,
        _encode_bounded_record,
        _parse_bounded_json,
        _socket_request,
    )
    from tests.test_session_native_regressions import _construction_daemon, _construction_frame

    daemon, driver, identity, child = _construction_daemon(tmp_path)
    identity = replace(identity, fingerprint="a" * 64)
    driver.backend.resolve_identity = lambda **_kwargs: identity  # type: ignore[method-assign]
    begin = _construction_frame(identity, boot="boot-a", sequence=2)
    begin["captureMonotonic"] = 1.0
    ordinary = _construction_frame(identity, boot="ordinary-new", sequence=3)
    ordinary["captureMonotonic"] = 2.0
    observation_count = 0

    def observation_provider() -> dict[str, object]:
        nonlocal observation_count
        observation_count += 1
        return begin if observation_count <= 2 else ordinary

    daemon._native_construction_observation_provider = observation_provider

    def fail_native_meter() -> None:
        raise RuntimeError("fixture native measurement failure")

    # This injects the real daemon's owned measurement boundary failure.  The
    # public prepare/bootstrap/calibrate/status/pause/recovery calls remain
    # production dispatches and must retain the causal error.
    daemon._ensure_native_memory_meter = fail_native_meter  # type: ignore[method-assign]
    socket_path = tmp_path / "terminal-error.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    os.chmod(socket_path, 0o600)
    listener.listen(8)
    listener.settimeout(0.1)
    stop = threading.Event()
    workers: list[threading.Thread] = []
    ipc = SessionIPC(daemon.controller, owner=daemon)

    def serve_connection(connection: socket.socket) -> None:
        with connection:
            reader = _BoundedIPCReader(connection)
            raw = reader.read_record(4096)
            if raw is None:
                return
            request = _parse_bounded_json(raw)
            assert isinstance(request, dict)
            try:
                response = ipc.dispatch(request)
            except Exception as exc:
                response = {"ok": False, "error": str(exc)}
            try:
                connection.sendall(_encode_bounded_record(response, 524288))
            except OSError:
                pass

    def serve() -> None:
        while not stop.is_set():
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            except OSError:
                if stop.is_set():
                    return
                raise
            worker = threading.Thread(target=serve_connection, args=(connection,), daemon=True)
            workers.append(worker)
            worker.start()

    server = threading.Thread(target=serve, daemon=True)
    server.start()
    client = operator.DaemonClient(socket_path, request_fn=_socket_request, timeout=15.0)
    try:
        prepared = client.prepare(7)
        binding = operator.ReservationBinding.from_record(prepared["reservation"], expected_generation=7)
        bootstrapped = client.bootstrap(7, binding)
        assert bootstrapped["handshake"]["state"] == "running"
        started = client.native_calibrate(7, deadline=time.monotonic() + 8.0)
        assert started["status"]["state"] == "NATIVE_CALIBRATION"
        operation = started["status"]["calibrationOperation"]
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            status = client.calibration_status(deadline=deadline)["status"]
            operation = status["calibrationOperation"]
            if operation["state"] in {"complete", "error"}:
                break
            time.sleep(0.02)
        assert operation["state"] == "error"
        assert operation["error"] == "fixture native measurement failure"

        paused = client.pause(7, deadline=time.monotonic() + 8.0)
        paused_status = paused["status"]
        assert paused_status["state"] == "PAUSED"
        assert paused_status["generation"] > 7
        new_generation = paused_status["generation"]
        recovery = client.recovery_begin(new_generation, "")
        assert recovery["handshake"]["state"] == "recovery_required"
        recovery_binding = recovery["reservation"]
        assert recovery_binding["reservationKind"] == "recovery"
        assert recovery_binding["reservationId"] != binding.reservation_id
        terminal = client.recovery_complete(new_generation, recovery_binding["reservationId"])
        assert terminal["handshake"]["state"] == "recovered"
        assert terminal["reservation"]["reservationState"] == "recovered"
    finally:
        stop.set()
        listener.close()
        server.join(timeout=2.0)
        for worker in workers:
            worker.join(timeout=2.0)
        daemon.request_shutdown()
        driver.close()
        child.terminate()
        child.wait(timeout=3)
