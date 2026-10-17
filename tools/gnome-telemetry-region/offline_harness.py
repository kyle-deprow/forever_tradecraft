#!/usr/bin/env python3
# ruff: noqa: E501
"""Offline producer/admission checks for the typed telemetry-region contract."""

from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import json
import math
import os
import re
import select
import shlex
import shutil
import signal
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(
    os.environ.get("GNOME_TELEMETRY_REGION_STAGE", "/home/dev/.cache/crowley/gnome-telemetry-region-r6")
)
BINARY = Path(os.environ.get("GNOME_TELEMETRY_REGION_BINARY", STAGE / "prefix/bin/gnome-screenshot"))
PATCH = ROOT / "tools/gnome-telemetry-region/0001-typed-telemetry-area.patch"
MANIFEST = ROOT / "tools/gnome-telemetry-region/manifest.example.json"


def _png_256() -> bytes:
    raw = b"".join(b"\x00" + b"\x00\x00\x00\xff" * 256 for _ in range(256))

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 256, 256, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def _strict_argv(argv: list[str]) -> bool:
    counts: dict[str, int] = {}
    values: dict[str, str] = {}
    scalar = {
        "--telemetry-x",
        "--telemetry-y",
        "--telemetry-width",
        "--telemetry-height",
        "--telemetry-owner-fd",
        "--telemetry-exec-fd",
        "--telemetry-nonce",
        "--file",
    }
    conflicts = {"--window", "--area", "--interactive", "--clipboard", "--include-pointer", "--delay"}
    telemetry = "--telemetry-region" in argv
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--telemetry-region":
            counts[token] = counts.get(token, 0) + 1
            index += 1
            continue
        if token in scalar or token == "-f":
            name = "--file" if token == "-f" else token
            counts[token] = counts.get(token, 0) + 1
            if index + 1 >= len(argv):
                return False
            counts[name] = counts.get(name, 0) + (1 if token == "-f" else 0)
            values[name] = argv[index + 1]
            index += 2
            continue
        if token.startswith("--") and any(token.startswith(name + "=") for name in scalar):
            name, value = token.split("=", 1)
            counts[name] = counts.get(name, 0) + 1
            values[name] = value
        elif token in conflicts or token == "-d" or token.startswith("-d="):
            return False if telemetry else True
        index += 1
    if not telemetry:
        return not any(key.startswith("--telemetry-") for key in counts)
    if counts.get("--telemetry-region", 0) != 1:
        return False
    if any(counts.get(key, 0) != 1 for key in scalar):
        return False
    try:

        def canonical_int(value: str) -> int:
            if re.fullmatch(r"0|-?[1-9][0-9]*", value) is None:
                raise ValueError(value)
            return int(value, 10)

        rectangle = tuple(
            canonical_int(values[key])
            for key in ("--telemetry-x", "--telemetry-y", "--telemetry-width", "--telemetry-height")
        )
        owner_fd = canonical_int(values["--telemetry-owner-fd"])
        exec_fd = canonical_int(values["--telemetry-exec-fd"])
    except (KeyError, ValueError):
        return False
    return (
        rectangle[2:] == (256, 256)
        and owner_fd > 2
        and exec_fd > 2
        and bool(values["--telemetry-nonce"])
        and Path(values["--file"]).is_absolute()
    )


def _readline(sock: socket.socket, deadline: float) -> dict[str, object]:
    data = bytearray()
    while b"\n" not in data:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("protocol deadline")
        ready, _, _ = select.select([sock], [], [], min(0.1, remaining))
        if not ready:
            continue
        # Read one byte at a time so a fast child cannot coalesce the next
        # protocol record into this call and leave it discarded.
        part = sock.recv(1)
        if not part:
            raise RuntimeError("protocol EOF")
        data.extend(part)
    value = json.loads(data.split(b"\n", 1)[0])
    if not isinstance(value, dict):
        raise RuntimeError("protocol object required")
    return value


def _protocol_fixture() -> None:
    import socket

    from crowley.session.driver import _EXEC_ADMISSION_WRAPPER, _open_sealed_executable
    from crowley.session.process_admission import AdmissionGate

    with tempfile.TemporaryDirectory(prefix="crowley-region-selftest-") as temporary:
        root = Path(temporary)
        payload = _png_256()
        encoded = base64.b64encode(payload).decode("ascii")
        script = root / "producer.py"
        script.write_text(
            "#!/usr/bin/python3\n"
            "import base64,hashlib,json,os, pathlib,sys,time\n"
            "args=sys.argv[1:]\n"
            "def value(name): return args[args.index(name)+1]\n"
            "fd=int(value('--telemetry-owner-fd')); efd=int(value('--telemetry-exec-fd')); nonce=value('--telemetry-nonce'); out=pathlib.Path(value('--file'))\n"
            "tail=open('/proc/self/stat').read().rsplit(')',1)[1].split()\n"
            "start=tail[19]; digest=hashlib.sha256(open('/proc/self/fd/%d'%efd,'rb').read()).hexdigest()\n"
            "rect=[int(value('--telemetry-x')),int(value('--telemetry-y')),int(value('--telemetry-width')),int(value('--telemetry-height'))]\n"
            "pathdigest=hashlib.sha256(str(out).encode()).hexdigest()\n"
            "def send(v): os.write(fd,(json.dumps(v,separators=(',',':'))+'\\n').encode())\n"
            "send({'type':'owner_ready','protocol':1,'nonce':nonce,'pid':os.getpid(),'process_start':start,'ppid':os.getppid(),'pgid':os.getpgrp(),'exec_fd':efd,'executable_sha256':digest,'primary_owner':True,'remote':False,'branch':'ScreenshotArea','rectangle':rect,'output_path_digest':pathdigest})\n"
            "ack=bytearray()\n"
            "while b'\\n' not in ack:\n"
            "    piece=os.read(fd,1)\n"
            "    if not piece: raise SystemExit(4)\n"
            "    ack.extend(piece)\n"
            "assert bytes(ack).decode() == json.dumps({'type':'ACK','protocol':1,'nonce':nonce},separators=(',',':'))+'\\n'\n"
            "send({'type':'capture_started','protocol':1,'nonce':nonce,'branch':'ScreenshotArea','rectangle':rect,'output_path_digest':pathdigest,'capture_started':time.monotonic()})\n"
            "data=base64.b64decode(" + repr(encoded) + "); out.write_bytes(data)\n"
            "send({'type':'capture_complete','protocol':1,'nonce':nonce,'branch':'ScreenshotArea','rectangle':rect,'output_path_digest':pathdigest,'output_sha256':hashlib.sha256(data).hexdigest(),'output_bytes':len(data)})\n",
            encoding="utf-8",
        )
        script.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        image_fd, digest = _open_sealed_executable(script, hashlib.sha256(script.read_bytes()).hexdigest())
        parent, child = socket.socketpair()
        gate_read, gate_write = os.pipe()
        nonce = "selftest-nonce"
        output = root / "out.png"
        target = f"/proc/self/fd/{image_fd}"
        args = [
            target,
            "--telemetry-x",
            "10",
            "--telemetry-y",
            "20",
            "--telemetry-width",
            "256",
            "--telemetry-height",
            "256",
            "--telemetry-owner-fd",
            str(child.fileno()),
            "--telemetry-exec-fd",
            str(image_fd),
            "--telemetry-nonce",
            nonce,
            "--file",
            str(output),
        ]
        process = subprocess.Popen(
            [sys.executable, "-I", "-S", "-c", _EXEC_ADMISSION_WRAPPER, str(gate_read), target, *args[1:]],
            start_new_session=True,
            pass_fds=(gate_read, child.fileno(), image_fd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        child.close()
        AdmissionGate(gate_write).release()
        os.close(gate_read)
        owner = _readline(parent, time.monotonic() + 5)
        assert owner["pid"] == process.pid and owner["executable_sha256"] == digest
        ack = (
            json.dumps({"type": "ACK", "protocol": 1, "nonce": nonce}, separators=(",", ":")) + "\n"
        ).encode()
        midpoint = max(1, len(ack) // 2)
        parent.sendall(ack[:midpoint])
        time.sleep(0.01)
        parent.sendall(ack[midpoint:])
        started = _readline(parent, time.monotonic() + 5)
        completed = _readline(parent, time.monotonic() + 5)
        assert started["branch"] == "ScreenshotArea" and completed["output_bytes"] == len(payload)
        assert output.read_bytes() == payload
        assert process.wait(timeout=5) == 0
        parent.close()
        os.close(image_fd)


def _compiled_private_shell_fixture() -> None:
    """Run the compiled producer against a private bus/display compositor.

    The service is an external test compositor.  The producer, argument
    parser, D-Bus ``ScreenshotArea`` call, PNG readback, and telemetry records
    are real; the host desktop and production Shell are never contacted.
    """

    for command in ("dbus-run-session", "gjs", "Xvfb"):
        if shutil.which(command) is None:
            raise RuntimeError(f"compiled private producer fixture needs {command}")
    with tempfile.TemporaryDirectory(prefix="crowley-region-dbus-") as temporary:
        root = Path(temporary)
        payload = _png_256()
        payload_path = root / "payload.png"
        payload_path.write_text(base64.b64encode(payload).decode("ascii"), encoding="ascii")
        display_path = root / "display"
        bus_path = root / "bus"
        ready_path = root / "ready"
        release_path = root / "release-screenshot-owner"
        released_path = root / "released-screenshot-owner"
        shell = root / "shell.js"
        shell.write_text(
            "const { Gio, GLib } = imports.gi;\n"
            'const xml = `<node><interface name="org.gnome.Shell.Screenshot">'
            '<method name="ScreenshotArea">'
            '<arg type="i" direction="in"/><arg type="i" direction="in"/>'
            '<arg type="i" direction="in"/><arg type="i" direction="in"/>'
            '<arg type="b" direction="in"/><arg type="s" direction="in"/>'
            '<arg type="b" direction="out"/></method></interface></node>`;\n'
            "const service = { ScreenshotArea(x, y, w, h, flash, path) {\n"
            "  if (x !== 80 || y !== 48 || w !== 256 || h !== 256 || flash !== false) throw new Error('bad ScreenshotArea request');\n"
            "  let [ok, bytes] = GLib.file_get_contents(ARGV[0]); if (!ok) throw new Error('payload missing');\n"
            "  GLib.file_set_contents(path, GLib.base64_decode(imports.byteArray.toString(bytes))); return true;\n"
            "} };\n"
            "let bus = Gio.bus_get_sync(Gio.BusType.SESSION, null);\n"
            "let exported = Gio.DBusExportedObject.wrapJSObject(xml, service);\n"
            "exported.export(bus, '/org/gnome/Shell/Screenshot');\n"
            "let owner = Gio.bus_own_name_on_connection(bus, 'org.gnome.Shell.Screenshot', Gio.BusNameOwnerFlags.NONE, null, null);\n"
            "let competing = Gio.bus_own_name_on_connection(bus, 'org.gnome.Screenshot', Gio.BusNameOwnerFlags.NONE, null, null);\n"
            "GLib.timeout_add(GLib.PRIORITY_DEFAULT, 250, () => { GLib.file_set_contents(ARGV[1], 'ready'); return GLib.SOURCE_REMOVE; });\n"
            "GLib.timeout_add(GLib.PRIORITY_DEFAULT, 10, () => { if (!GLib.file_test(ARGV[2], GLib.FileTest.EXISTS)) return GLib.SOURCE_CONTINUE; Gio.bus_unown_name(competing); GLib.file_set_contents(ARGV[3], 'released'); return GLib.SOURCE_REMOVE; });\n"
            "new GLib.MainLoop(null, false).run();\n",
            encoding="utf-8",
        )
        session_script = (
            "set -eu\n"
            f"Xvfb -displayfd 9 -screen 0 1920x1080x24 9>{display_path} 2>{root / 'xvfb.stderr'} &\n"
            "xv=$!\n"
            "trap 'kill $xv 2>/dev/null || true' EXIT\n"
            f"while [ ! -s {display_path} ]; do sleep 0.01; done\n"
            f"display=$(cat {display_path}); export DISPLAY=:$display GDK_BACKEND=x11\n"
            f"printf '%s\\n' \"$DBUS_SESSION_BUS_ADDRESS\" > {bus_path}\n"
            f"exec gjs {shell} {payload_path} {ready_path} {release_path} {released_path} >{root / 'gjs.stdout'} 2>{root / 'gjs.stderr'}\n"
        )
        session = subprocess.Popen(
            ["dbus-run-session", "--", "bash", "-lc", session_script],
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            ready_deadline = time.monotonic() + 8.0
            while (not bus_path.exists() or not display_path.exists()) and time.monotonic() < ready_deadline:
                if session.poll() is not None:
                    raise RuntimeError(f"private compositor exited: {session.stderr.read()}")
                time.sleep(0.02)
            if not bus_path.exists() or not display_path.exists():
                if session.poll() is not None:
                    detail = session.stderr.read()
                else:
                    detail = "<session still running>"
                raise RuntimeError(f"private compositor did not publish bus/display: {detail}")
            display = ":" + display_path.read_text(encoding="utf-8").strip()
            time.sleep(1.0)
            environment = os.environ.copy()
            environment.update(
                {
                    "DBUS_SESSION_BUS_ADDRESS": bus_path.read_text(encoding="utf-8").strip(),
                    "DISPLAY": display,
                    "GDK_BACKEND": "x11",
                }
            )
            # Compose the genuine binary with the production parent boundary
            # before the direct protocol checks below.  The D-Bus/X11 service
            # is an owned external fixture; the parent, sealed memfd, strict
            # records, decoder-sized PNG and identity path remain real.
            from crowley.session.driver import DriverError, DriverProfile, X11Backend

            xauthority = root / "Xauthority"
            xauthority.touch(mode=0o600)
            local_binary = root / "gnome-screenshot-r6"
            shutil.copyfile(BINARY, local_binary)
            local_binary.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            profile = DriverProfile(
                display=display,
                xauthority=str(xauthority),
                client_width=1920,
                client_height=1080,
                outer_width=1928,
                outer_height=1092,
                canvas_crop=(80, 48, 256, 256),
                model_crop=(80, 48, 640, 480),
                telemetry_region_executable=local_binary,
                telemetry_region_executable_sha256=hashlib.sha256(local_binary.read_bytes()).hexdigest(),
            )
            production_identity = SimpleNamespace(
                fingerprint="compiled-private-production-identity",
                child_geometry=(0, 0, 1920, 1080),
            )
            production_backend = X11Backend(profile, input_tool=SimpleNamespace())
            production_backend.resolve_identity = lambda **_kwargs: production_identity  # type: ignore[method-assign]
            saved_bus = os.environ.get("DBUS_SESSION_BUS_ADDRESS")
            os.environ["DBUS_SESSION_BUS_ADDRESS"] = environment["DBUS_SESSION_BUS_ADDRESS"]
            composed_output = root / "production-parent-capture.png"
            try:
                competing_output = root / "competing-owner.png"
                try:
                    production_backend.capture_native_region(
                        competing_output,
                        identity=production_identity,
                        rectangle=(80, 48, 256, 256),
                        deadline_monotonic=time.monotonic() + 5.0,
                        _allow_unobserved_fixture=True,
                    )
                except DriverError:
                    pass
                else:
                    raise RuntimeError("compiled producer forwarded through a competing canonical owner")
                if competing_output.exists() or production_backend.active_process_groups:
                    raise RuntimeError("competing canonical owner left a capture or process group")
                release_path.touch(mode=0o600)
                released_deadline = time.monotonic() + 5.0
                while not released_path.exists() and time.monotonic() < released_deadline:
                    time.sleep(0.01)
                if not released_path.exists():
                    raise RuntimeError("private compositor did not release competing canonical owner")
                captured_identity = production_backend.capture_native_region(
                    composed_output,
                    identity=production_identity,
                    rectangle=(80, 48, 256, 256),
                    deadline_monotonic=time.monotonic() + 12.0,
                    _allow_unobserved_fixture=True,
                )
            finally:
                if saved_bus is None:
                    os.environ.pop("DBUS_SESSION_BUS_ADDRESS", None)
                else:
                    os.environ["DBUS_SESSION_BUS_ADDRESS"] = saved_bus
            if captured_identity.fingerprint != production_identity.fingerprint:
                raise RuntimeError("production parent rejected its own compiled region identity")
            with Image.open(composed_output) as composed_image, Image.open(BytesIO(payload)) as expected:
                composed_image.load()
                expected.load()
                if (
                    composed_image.size != (256, 256)
                    or composed_image.convert("RGBA").tobytes() != expected.convert("RGBA").tobytes()
                ):
                    raise RuntimeError("production parent composed PNG did not preserve exact pixels")
            parent, child = socket.socketpair()
            image_fd = os.open(BINARY, os.O_RDONLY)
            output = root / "capture.png"
            nonce = "compiled-private-fixture"
            process = subprocess.Popen(
                [
                    str(BINARY),
                    "--telemetry-region",
                    "--telemetry-x",
                    "80",
                    "--telemetry-y",
                    "48",
                    "--telemetry-width",
                    "256",
                    "--telemetry-height",
                    "256",
                    "--telemetry-owner-fd",
                    str(child.fileno()),
                    "--telemetry-exec-fd",
                    str(image_fd),
                    "--telemetry-nonce",
                    nonce,
                    "--file",
                    str(output),
                ],
                pass_fds=(child.fileno(), image_fd),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            child.close()
            os.close(image_fd)
            try:
                parent.settimeout(12.0)
                owner = _readline(parent, time.monotonic() + 10.0)
                if owner.get("type") != "owner_ready" or owner.get("nonce") != nonce:
                    raise RuntimeError(f"compiled producer owner record is invalid: {owner}")
                parent.sendall(
                    (
                        json.dumps({"type": "ACK", "protocol": 1, "nonce": nonce}, separators=(",", ":"))
                        + "\n"
                    ).encode()
                )
                try:
                    started = _readline(parent, time.monotonic() + 10.0)
                except RuntimeError as exc:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=2.0)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=2.0)
                    stderr = process.stderr.read()
                    session_diagnostic = ""
                    if session.poll() is not None:
                        session_diagnostic = session.stderr.read()
                    raise RuntimeError(
                        f"compiled producer failed after ACK: {exc}; stderr={stderr!r}; "
                        f"session={session.poll()} {session_diagnostic!r}"
                    ) from exc
                try:
                    completed = _readline(parent, time.monotonic() + 10.0)
                except RuntimeError as exc:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=2.0)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=2.0)
                    stderr = process.stderr.read()
                    gjs_stderr = (root / "gjs.stderr").read_text(encoding="utf-8")
                    raise RuntimeError(
                        f"compiled producer failed before completion: {exc}; stderr={stderr!r}; "
                        f"gjs_stderr={gjs_stderr!r}"
                    ) from exc
                if started.get("branch") != "ScreenshotArea" or completed.get("output_bytes", 0) <= 0:
                    raise RuntimeError(f"compiled producer records are invalid: {started} {completed}")
                if process.wait(timeout=10.0) != 0:
                    raise RuntimeError(f"compiled producer failed: {process.stderr.read()}")
                with Image.open(output) as observed, Image.open(BytesIO(payload)) as expected:
                    observed.load()
                    expected.load()
                    if (
                        observed.size != (256, 256)
                        or observed.convert("RGBA").tobytes() != expected.convert("RGBA").tobytes()
                    ):
                        raise RuntimeError("private compositor PNG did not preserve exact pixels")
            finally:
                parent.close()
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=2.0)

            def run_compiled_owner_refusal(label: str, response: bytes | None) -> None:
                """Exercise the rebuilt C producer's owner-pipe refusal path."""

                refusal_output = root / f"{label}.png"
                owner_parent, owner_child = socket.socketpair()
                executable_fd = os.open(BINARY, os.O_RDONLY)
                refusal = subprocess.Popen(
                    [
                        str(BINARY),
                        "--telemetry-region",
                        "--telemetry-x",
                        "80",
                        "--telemetry-y",
                        "48",
                        "--telemetry-width",
                        "256",
                        "--telemetry-height",
                        "256",
                        "--telemetry-owner-fd",
                        str(owner_child.fileno()),
                        "--telemetry-exec-fd",
                        str(executable_fd),
                        "--telemetry-nonce",
                        f"{label}-nonce",
                        "--file",
                        str(refusal_output),
                    ],
                    pass_fds=(owner_child.fileno(), executable_fd),
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                owner_child.close()
                os.close(executable_fd)
                try:
                    owner_parent.settimeout(4.0)
                    record = _readline(owner_parent, time.monotonic() + 3.0)
                    if record.get("type") != "owner_ready":
                        raise RuntimeError(f"{label}: unexpected owner record {record}")
                    if response is not None:
                        owner_parent.sendall(response)
                    else:
                        owner_parent.close()
                        owner_parent = None
                    try:
                        exit_code = refusal.wait(timeout=4.0)
                    except subprocess.TimeoutExpired as exc:
                        raise RuntimeError(f"{label}: producer did not refuse promptly") from exc
                    if exit_code == 0 or refusal_output.exists():
                        raise RuntimeError(
                            f"{label}: producer accepted owner failure or published output "
                            f"(exit={exit_code}, output={refusal_output.exists()})"
                        )
                finally:
                    if owner_parent is not None:
                        owner_parent.close()
                    if refusal.poll() is None:
                        refusal.kill()
                        refusal.wait(timeout=2.0)

            run_compiled_owner_refusal(
                "compiled-wrong-ack",
                b'{"type":"ACK","protocol":1,"nonce":"wrong-nonce"}\n',
            )
            run_compiled_owner_refusal("compiled-owner-eof", None)
        finally:
            if session.poll() is None:
                os.killpg(session.pid, signal.SIGTERM)
                try:
                    session.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    os.killpg(session.pid, signal.SIGKILL)
                    session.wait(timeout=3.0)


@contextlib.contextmanager
def private_shell_compositor(
    *,
    payloads: list[bytes],
    full_desktop: bytes,
    rectangle: tuple[int, int, int, int],
    allow_area_gate: bool = False,
):
    """Own a private Xvfb, D-Bus session, and external Screenshot compositor."""

    for command in ("dbus-run-session", "gjs", "Xvfb"):
        if shutil.which(command) is None:
            raise RuntimeError(f"private compositor fixture needs {command}")
    with tempfile.TemporaryDirectory(prefix="crowley-region-composed-") as temporary:
        root = Path(temporary)
        payload_paths: list[str] = []
        for index, payload in enumerate(payloads):
            payload_path = root / f"payload-{index:02d}.b64"
            payload_path.write_text(base64.b64encode(payload).decode("ascii"), encoding="ascii")
            payload_paths.append(str(payload_path))
        payload_list = root / "payloads.json"
        payload_list.write_text(json.dumps(payload_paths), encoding="utf-8")
        full_path = root / "full-desktop.b64"
        full_path.write_text(base64.b64encode(full_desktop).decode("ascii"), encoding="ascii")
        area_log = root / "area-calls.json"
        stock_log = root / "stock-calls.json"
        bus_path = root / "bus-address"
        display_path = root / "display-number"
        ready_path = root / "compositor-ready"
        area_block_path = root / "block-next-area"
        area_started_path = root / "area-blocked"
        area_release_path = root / "release-area"
        cache_home = root / "cache"
        cache_home.mkdir(mode=0o700)
        shell = root / "compositor.js"
        shell.write_text(
            "const { Gio, GLib } = imports.gi;\n"
            'const xml = `<node><interface name="org.gnome.Shell.Screenshot">'
            '<method name="ScreenshotArea">'
            '<arg type="i" direction="in"/><arg type="i" direction="in"/>'
            '<arg type="i" direction="in"/><arg type="i" direction="in"/>'
            '<arg type="b" direction="in"/><arg type="s" direction="in"/>'
            '<arg type="b" direction="out"/><arg type="s" direction="out"/>'
            '</method><method name="Screenshot">'
            '<arg type="b" direction="in"/><arg type="b" direction="in"/>'
            '<arg type="s" direction="in"/><arg type="b" direction="out"/>'
            '<arg type="s" direction="out"/></method></interface></node>`;\n'
            "function readText(path) { let [ok, bytes] = GLib.file_get_contents(path); if (!ok) throw new Error('fixture text missing'); return imports.byteArray.toString(bytes); }\n"
            "function readBase64(path) { return GLib.base64_decode(readText(path)); }\n"
            "function append(path, value) { let rows = []; if (GLib.file_test(path, GLib.FileTest.EXISTS)) { rows = JSON.parse(readText(path)); } rows.push(value); GLib.file_set_contents(path, JSON.stringify(rows)); }\n"
            "let payloadPaths = JSON.parse(readText(ARGV[0]));\n"
            "let areaIndex = 0;\n"
            "const expected = [Number(ARGV[3]), Number(ARGV[4]), Number(ARGV[5]), Number(ARGV[6])];\n"
            "const service = { ScreenshotArea(x, y, width, height, flash, filename) {\n"
            "  if (x !== expected[0] || y !== expected[1] || width !== expected[2] || height !== expected[3] || flash !== false) throw new Error('bad ScreenshotArea request');\n"
            "  const payload = payloadPaths[areaIndex++]; if (!payload) throw new Error('unexpected ScreenshotArea retry');\n"
            + (
                "  if (GLib.file_test(ARGV[10], GLib.FileTest.EXISTS)) { GLib.file_set_contents(ARGV[11], String(GLib.get_monotonic_time())); while (!GLib.file_test(ARGV[12], GLib.FileTest.EXISTS)) GLib.usleep(10000); }\n"
                if allow_area_gate
                else ""
            )
            + "  GLib.file_set_contents(filename, readBase64(payload));\n"
            "  append(ARGV[1], {x, y, width, height, flash, index: areaIndex, filename, monotonic_us: GLib.get_monotonic_time()}); return [true, filename];\n"
            "}, Screenshot(includeCursor, flash, filename) {\n"
            "  GLib.file_set_contents(filename, readBase64(ARGV[2]));\n"
            "  append(ARGV[7], {includeCursor, flash, filename}); return [true, filename];\n"
            "} };\n"
            "let bus = Gio.bus_get_sync(Gio.BusType.SESSION, null);\n"
            "let exported = Gio.DBusExportedObject.wrapJSObject(xml, service);\n"
            "exported.export(bus, '/org/gnome/Shell/Screenshot');\n"
            "let owner = Gio.bus_own_name_on_connection(bus, 'org.gnome.Shell.Screenshot', Gio.BusNameOwnerFlags.NONE, null, null);\n"
            "GLib.file_set_contents(ARGV[8], GLib.getenv('DBUS_SESSION_BUS_ADDRESS'));\n"
            "GLib.timeout_add(GLib.PRIORITY_DEFAULT, 100, () => { GLib.file_set_contents(ARGV[9], 'ready'); return GLib.SOURCE_REMOVE; });\n"
            "new GLib.MainLoop(null, false).run();\n",
            encoding="utf-8",
        )
        args = [
            str(payload_list),
            str(area_log),
            str(full_path),
            *(str(value) for value in rectangle),
            str(stock_log),
            str(bus_path),
            str(ready_path),
            str(area_block_path),
            str(area_started_path),
            str(area_release_path),
        ]
        quoted_args = " ".join(shlex.quote(value) for value in [str(shell), *args])
        session_script = (
            "set -eu\n"
            f"Xvfb -displayfd 9 -screen 0 1920x1080x24 -nolisten tcp 9>{shlex.quote(str(display_path))} 2>{shlex.quote(str(root / 'xvfb.stderr'))} &\n"
            "xv=$!\n"
            "trap 'kill $xv 2>/dev/null || true' EXIT\n"
            f"while [ ! -s {shlex.quote(str(display_path))} ]; do sleep 0.01; done\n"
            f"display=$(cat {shlex.quote(str(display_path))}); export DISPLAY=:$display GDK_BACKEND=x11\n"
            f"printf '%s\\n' \"$DBUS_SESSION_BUS_ADDRESS\" > {shlex.quote(str(bus_path))}\n"
            f"exec gjs {quoted_args} >{shlex.quote(str(root / 'gjs.stdout'))} 2>{shlex.quote(str(root / 'gjs.stderr'))}\n"
        )
        session = subprocess.Popen(
            ["dbus-run-session", "--", "bash", "-lc", session_script],
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        saved_environment = {
            name: os.environ.get(name)
            for name in (
                "DBUS_SESSION_BUS_ADDRESS",
                "DISPLAY",
                "GDK_BACKEND",
                "XDG_RUNTIME_DIR",
                "XDG_CACHE_HOME",
            )
        }
        try:
            deadline = time.monotonic() + 8.0
            while not ready_path.exists() and time.monotonic() < deadline:
                if session.poll() is not None:
                    raise RuntimeError(f"private compositor exited: {session.stderr.read()}")
                time.sleep(0.01)
            if not ready_path.exists() or not bus_path.exists() or not display_path.exists():
                detail = session.stderr.read() if session.poll() is not None else "<session still running>"
                raise RuntimeError(f"private compositor did not become ready: {detail}")
            bus_address = bus_path.read_text(encoding="utf-8").strip()
            display = ":" + display_path.read_text(encoding="ascii").strip()
            if not bus_address or not display[1:].isdigit():
                raise RuntimeError("private compositor published a malformed bus or display")
            os.environ["DBUS_SESSION_BUS_ADDRESS"] = bus_address
            os.environ["DISPLAY"] = display
            os.environ["GDK_BACKEND"] = "x11"
            os.environ["XDG_RUNTIME_DIR"] = str(root)
            os.environ["XDG_CACHE_HOME"] = str(cache_home)
            time.sleep(0.15)
            yield {
                "root": root,
                "display": display,
                "bus_address": bus_address,
                "payload_paths": tuple(Path(path) for path in payload_paths),
                "area_log": area_log,
                "stock_log": stock_log,
                "area_block_path": area_block_path,
                "area_started_path": area_started_path,
                "area_release_path": area_release_path,
                "session": session,
            }
        finally:
            for name, value in saved_environment.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
            if session.poll() is None:
                os.killpg(session.pid, signal.SIGTERM)
                try:
                    session.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    os.killpg(session.pid, signal.SIGKILL)
                    session.wait(timeout=3.0)


def _finite_time(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise RuntimeError(f"{label} is not a finite monotonic timestamp")
    return float(value)


def _status_from_ipc(config: object, *, timeout: float) -> dict[str, object]:
    from crowley.session.cli import _socket_request

    response = _socket_request(config.socket, {"command": "status"}, timeout=timeout)  # type: ignore[attr-defined]
    if not isinstance(response, dict) or response.get("ok") is not True:
        raise RuntimeError(f"session IPC status request failed: {response!r}")
    status = response.get("status")
    if not isinstance(status, dict):
        raise RuntimeError("session IPC status response is not an object")
    return status


def _check_paused_status(status: dict[str, object], *, expected_generation: int | None) -> int:
    if status.get("state") != "PAUSED":
        raise RuntimeError("paused diagnostic requires actual controller state PAUSED")
    generation = status.get("generation")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
        raise RuntimeError("session IPC status has no integer generation")
    if expected_generation is not None and generation != expected_generation:
        raise RuntimeError("session generation changed during paused diagnostic")
    operation = status.get("calibrationOperation")
    if not isinstance(operation, dict) or not isinstance(operation.get("state"), str):
        raise RuntimeError("session IPC status has no calibration operation state")
    if operation["state"] in {"starting", "running"}:
        raise RuntimeError("paused diagnostic refuses an in-flight calibration operation")
    action = status.get("actionIntent")
    if action not in (None, ""):
        raise RuntimeError("paused diagnostic refuses an in-flight action")
    if status.get("nativeBootstrapPending") is not False:
        raise RuntimeError("paused diagnostic refuses pending native bootstrap evidence")
    return generation


def _identity_record(identity: object) -> dict[str, object]:
    fields = (
        "pid",
        "process_start",
        "xid",
        "child_xid",
        "executable",
        "display",
        "fingerprint",
        "child_geometry",
    )
    result: dict[str, object] = {}
    for name in fields:
        value = getattr(identity, name, None)
        if name == "child_geometry":
            if not isinstance(value, tuple) or len(value) != 4:
                raise RuntimeError("desktop identity has no verified client geometry")
            value = list(value)
        if name == "pid" and (not isinstance(value, int) or isinstance(value, bool) or value <= 0):
            raise RuntimeError("desktop identity has no verified PID")
        if name in {"process_start", "fingerprint", "display", "executable"} and (
            not isinstance(value, str) or not value
        ):
            raise RuntimeError(f"desktop identity has no verified {name}")
        result[name] = value
    return result


def _atomic_receipt(path: Path, value: dict[str, object]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.monotonic_ns()}.tmp")
    encoded = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _atomic_private_png(path: Path, data: bytes) -> None:
    if not data or len(data) > 131072:
        raise RuntimeError("owner PNG exceeds its bounded size")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _owner_png_bytes(
    sample: dict[str, object],
    profile: object,
    producer_hash: str,
    config_file_sha256: str,
    config_semantic_sha256: str,
    expected_generation: int,
    expected_parent_started: float,
    expected_deadline: float,
    capture_root: Path,
    index: int,
) -> bytes:
    expected_fields = {
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
    }
    if set(sample) != expected_fields:
        raise RuntimeError(f"paused diagnostic owner sample {index} has unexpected fields")
    encoded = sample.get("png_base64")
    if not isinstance(encoded, str) or len(encoded) > 4 * ((131072 + 2) // 3):
        raise RuntimeError(f"paused diagnostic owner sample {index} PNG encoding is oversized")
    try:
        data = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise RuntimeError(f"paused diagnostic owner sample {index} PNG base64 is malformed") from exc
    if (
        not data
        or len(data) > 131072
        or sample.get("png_bytes") != len(data)
        or sample.get("png_sha256") != hashlib.sha256(data).hexdigest()
    ):
        raise RuntimeError(f"paused diagnostic owner sample {index} PNG digest or length is invalid")
    if (
        not isinstance(sample.get("generation"), int)
        or isinstance(sample["generation"], bool)
        or sample["generation"] != expected_generation
    ):
        raise RuntimeError(f"paused diagnostic owner sample {index} generation is malformed")
    parent_started = _finite_time(sample.get("parent_started"), f"sample {index} parent start")
    deadline = _finite_time(sample.get("deadline"), f"sample {index} deadline")
    owner_entered = _finite_time(sample.get("owner_entered"), f"sample {index} owner entry")
    capture_returned = _finite_time(sample.get("capture_returned"), f"sample {index} capture return")
    owner_returned = _finite_time(sample.get("owner_returned"), f"sample {index} owner return")
    if (
        parent_started != expected_parent_started
        or deadline != expected_deadline
        or not parent_started <= owner_entered <= capture_returned <= owner_returned < deadline
    ):
        raise RuntimeError(f"paused diagnostic owner sample {index} timestamps are not request-bound")
    identity = sample.get("identity")
    if not isinstance(identity, dict) or set(identity) != {
        "pid",
        "process_start",
        "xid",
        "child_xid",
        "executable",
        "display",
        "fingerprint",
        "child_geometry",
    }:
        raise RuntimeError(f"paused diagnostic owner sample {index} identity is malformed")
    if (
        not isinstance(identity.get("pid"), int)
        or isinstance(identity.get("pid"), bool)
        or identity["pid"] <= 0
        or not all(
            isinstance(identity.get(key), str) and identity[key]
            for key in ("process_start", "executable", "display", "fingerprint")
        )
        or not isinstance(identity.get("child_geometry"), list)
        or len(identity["child_geometry"]) != 4
    ):
        raise RuntimeError(f"paused diagnostic owner sample {index} identity fields are malformed")
    geometry = identity["child_geometry"]
    if any(not isinstance(value, int) or isinstance(value, bool) for value in geometry):
        raise RuntimeError(f"paused diagnostic owner sample {index} client geometry is malformed")
    source = sample.get("source")
    if not isinstance(source, dict) or set(source) != {"api", "branch", "rectangle"}:
        raise RuntimeError(f"paused diagnostic owner sample {index} source is malformed")
    config_binding = sample.get("config")
    expected_config = {
        "request_config_file_sha256": config_file_sha256,
        "request_config_semantic_sha256": config_semantic_sha256,
        "owner_config_semantic_sha256": config_semantic_sha256,
        "display": profile.display,  # type: ignore[attr-defined]
        "canvas_crop": list(profile.canvas_crop),  # type: ignore[attr-defined]
    }
    if config_binding != expected_config:
        raise RuntimeError(f"paused diagnostic owner sample {index} config binding changed")
    producer = sample.get("producer")
    if not isinstance(producer, dict) or producer != {
        "path": str(profile.telemetry_region_executable),  # type: ignore[attr-defined]
        "sha256": producer_hash,
    }:
        raise RuntimeError(f"paused diagnostic owner sample {index} producer binding changed")
    receipt = sample.get("receipt")
    expected_receipt_fields = {
        "nonce",
        "rectangle",
        "executable_sha256",
        "owner_pid",
        "owner_process_start",
        "owner_ppid",
        "owner_pgid",
        "owner_exec_fd",
        "owner_branch",
        "request_started",
        "lock_acquired",
        "ack_sent",
        "capture_started",
        "capture_returned",
        "output_path_digest",
        "output_sha256",
        "output_bytes",
        "capture_epoch",
        "attempt_retired",
    }
    if not isinstance(receipt, dict) or set(receipt) != expected_receipt_fields:
        raise RuntimeError(f"paused diagnostic owner sample {index} producer receipt schema changed")
    if (
        not isinstance(receipt.get("nonce"), str)
        or re.fullmatch(r"[0-9a-f]{32}", receipt["nonce"]) is None
        or not isinstance(receipt.get("owner_pid"), int)
        or isinstance(receipt.get("owner_pid"), bool)
        or receipt["owner_pid"] <= 0
        or not isinstance(receipt.get("owner_process_start"), str)
        or not receipt["owner_process_start"]
        or not isinstance(receipt.get("owner_ppid"), int)
        or isinstance(receipt.get("owner_ppid"), bool)
        or receipt["owner_ppid"] <= 0
        or receipt.get("owner_pgid") != receipt.get("owner_pid")
        or isinstance(receipt.get("owner_pgid"), bool)
        or not isinstance(receipt.get("owner_exec_fd"), int)
        or isinstance(receipt.get("owner_exec_fd"), bool)
        or receipt["owner_exec_fd"] < 0
        or not isinstance(receipt.get("capture_epoch"), int)
        or isinstance(receipt.get("capture_epoch"), bool)
        or receipt["capture_epoch"] < 0
        or not isinstance(receipt.get("output_path_digest"), str)
        or re.fullmatch(r"[0-9a-f]{64}", receipt["output_path_digest"]) is None
    ):
        raise RuntimeError(f"paused diagnostic owner sample {index} receipt identity is malformed")
    for key in ("request_started", "lock_acquired", "ack_sent", "capture_started", "capture_returned"):
        _finite_time(receipt.get(key), f"sample {index} receipt {key}")
    receipt_times = [
        float(receipt[key])
        for key in ("request_started", "lock_acquired", "ack_sent", "capture_started", "capture_returned")
    ]
    if (
        not parent_started
        <= receipt_times[0]
        <= receipt_times[1]
        <= receipt_times[2]
        <= receipt_times[3]
        <= capture_returned
    ):
        raise RuntimeError(f"paused diagnostic owner sample {index} receipt times are unordered")
    rectangle = receipt.get("rectangle")
    expected_rectangle = [
        geometry[0] + profile.canvas_crop[0],  # type: ignore[attr-defined]
        geometry[1] + profile.canvas_crop[1],  # type: ignore[attr-defined]
        profile.canvas_crop[2],  # type: ignore[attr-defined]
        profile.canvas_crop[3],  # type: ignore[attr-defined]
    ]
    if (
        not isinstance(rectangle, list)
        or len(rectangle) != 4
        or any(not isinstance(value, int) or isinstance(value, bool) for value in rectangle)
        or rectangle != expected_rectangle
    ):
        raise RuntimeError(f"paused diagnostic owner sample {index} rectangle is not profile-derived")
    artifact_directory = sample.get("artifact_directory")
    artifact_png = sample.get("artifact_png")
    if not isinstance(artifact_directory, str) or not isinstance(artifact_png, str):
        raise RuntimeError(f"paused diagnostic owner sample {index} artifact paths are malformed")
    root = capture_root.resolve()
    owner_directory = Path(artifact_directory)
    owner_png = Path(artifact_png)
    if (
        not owner_directory.is_absolute()
        or owner_directory.name.startswith("paused-region-") is False
        or owner_directory.parent.resolve() != root
        or owner_png != owner_directory / "capture.png"
        or owner_directory.is_symlink()
        or owner_png.is_symlink()
        or not owner_png.is_file()
        or owner_png.stat().st_size != len(data)
        or owner_png.read_bytes() != data
    ):
        raise RuntimeError(
            f"paused diagnostic owner sample {index} artifacts are outside the configured root"
        )
    if (
        receipt.get("owner_branch") != "ScreenshotArea"
        or receipt.get("executable_sha256") != producer_hash
        or receipt.get("output_sha256") != hashlib.sha256(data).hexdigest()
        or receipt.get("output_bytes") != len(data)
        or receipt.get("attempt_retired") is not True
        or source.get("api") != "org.gnome.Shell.Screenshot.ScreenshotArea"
        or source.get("branch") != "ScreenshotArea"
        or source.get("rectangle") != receipt.get("rectangle")
    ):
        raise RuntimeError(f"paused diagnostic owner sample {index} receipt does not bind the PNG")
    return data


def _bounded_failure_response(response: dict[str, object]) -> dict[str, object]:
    value: dict[str, object] = {key: item for key, item in response.items() if key != "sample"}
    sample = response.get("sample")
    if isinstance(sample, dict):
        value["sample"] = {key: item for key, item in sample.items() if key != "png_base64"}
    return value


def _validate_producer_attempt(value: object, index: int) -> None:
    """Validate truthful stage/timing evidence even when a capture fails."""

    fields = {"stage", "request_started", "lock_acquired", "ack_sent"}
    stages = {
        "not_started",
        "capture_lock_wait",
        "attempt_setup",
        "observer_admission",
        "owner_ready",
        "capture_started",
        "capture_complete",
        "identity_postcheck",
        "published",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise RuntimeError(f"paused diagnostic owner failure {index} producer attempt schema is malformed")
    stage = value.get("stage")
    if not isinstance(stage, str) or stage not in stages:
        raise RuntimeError(f"paused diagnostic owner failure {index} producer stage is unknown")
    if stage == "not_started":
        if any(value.get(key) is not None for key in ("request_started", "lock_acquired", "ack_sent")):
            raise RuntimeError(
                f"paused diagnostic owner failure {index} not-started stage has timing evidence"
            )
        return
    request_started = _finite_time(value.get("request_started"), f"failure {index} producer request")
    lock_value = value.get("lock_acquired")
    ack_value = value.get("ack_sent")
    lock_acquired = (
        _finite_time(lock_value, f"failure {index} capture lock") if lock_value is not None else None
    )
    ack_sent = _finite_time(ack_value, f"failure {index} producer ACK") if ack_value is not None else None
    if lock_acquired is not None and lock_acquired < request_started:
        raise RuntimeError(f"paused diagnostic owner failure {index} lock time precedes its request")
    if ack_sent is not None and (lock_acquired is None or ack_sent < lock_acquired):
        raise RuntimeError(f"paused diagnostic owner failure {index} ACK time precedes its lock")
    if (stage == "capture_lock_wait") != (lock_acquired is None) or (
        stage in {"capture_started", "capture_complete", "identity_postcheck", "published"}
    ) != (ack_sent is not None):
        raise RuntimeError(f"paused diagnostic owner failure {index} stage disagrees with its timestamps")


def _attempt_directories(output: Path) -> list[str]:
    matches = list(output.parent.glob(f".{output.name}.telemetry-*"))
    matches.extend(output.parent.glob(f"..{output.name}.telemetry-*.retired-*"))
    return sorted(str(path) for path in matches)


def _backend_cleanup_snapshot(driver: object, output: Path | None = None) -> dict[str, object]:
    backend = getattr(driver, "backend", None)
    processes = getattr(backend, "_active_processes", None)
    groups = getattr(backend, "active_process_groups", None)
    if not isinstance(processes, set) or not isinstance(groups, (set, frozenset)):
        return {"registries_observable": False, "active_processes": None, "active_process_groups": None}
    attempts = _attempt_directories(output) if output is not None else []
    return {
        "registries_observable": True,
        "active_processes": len(processes),
        "active_process_groups": sorted(groups),
        "attempt_directories": attempts,
        "empty": not processes and not groups and not attempts,
    }


def _receipt_record(receipt: object) -> dict[str, object]:
    fields = (
        "nonce",
        "rectangle",
        "executable_sha256",
        "owner_pid",
        "owner_process_start",
        "owner_ppid",
        "owner_pgid",
        "owner_exec_fd",
        "owner_branch",
        "request_started",
        "lock_acquired",
        "ack_sent",
        "capture_started",
        "capture_returned",
        "output_path_digest",
        "output_sha256",
        "output_bytes",
        "capture_epoch",
        "attempt_retired",
    )
    result = {name: getattr(receipt, name) for name in fields}
    result["rectangle"] = list(result["rectangle"])  # type: ignore[arg-type]
    return result


def run_paused_diagnostic(config_path: Path, output_dir: Path) -> dict[str, object]:
    """Run eight strict samples through the paused session's existing owner."""

    output_dir = output_dir.expanduser().absolute()
    if output_dir.exists() or output_dir.is_symlink():
        raise RuntimeError("paused diagnostic evidence directory must be new")
    output_dir.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    output_dir.mkdir(mode=0o700)
    os.chmod(output_dir, 0o700)
    receipt_path = output_dir / "receipt.json"
    receipt: dict[str, object] = {
        "schema": 1,
        "state": "running",
        "config_path": str(config_path.expanduser().resolve()),
        "evidence_directory": str(output_dir),
        "targets": [],
        "samples": [],
        "failure": None,
        "cleanup": {
            "client_driver_created": False,
            "client_driver_closed": False,
            "daemon_closed": False,
            "daemon_lease_released": False,
            "published_client_pngs": [],
        },
    }
    decoder = None
    expected_generation: int | None = None
    expected_boot: str | None = None
    identity_baseline: dict[str, object] | None = None
    failure: Exception | None = None
    phase = "configuration"
    try:
        from crowley.session.cli import _socket_request
        from crowley.session.config import load_config
        from crowley.session.daemon import session_config_semantic_sha256
        from crowley.session.decoder import PixelDecoder

        config_bytes = config_path.read_bytes()
        config = load_config(config_path)
        profile = config.profile
        producer = profile.telemetry_region_executable
        producer_hash = profile.telemetry_region_executable_sha256
        if producer is None or producer_hash is None:
            raise RuntimeError("paused diagnostic requires the configured telemetry-region producer")
        profile.validate()
        config_file_sha256 = hashlib.sha256(config_bytes).hexdigest()
        config_semantic_sha256 = session_config_semantic_sha256(config)
        receipt["config_file_sha256"] = config_file_sha256
        receipt["config_semantic_sha256"] = config_semantic_sha256
        receipt["producer"] = str(producer)
        receipt["producer_sha256"] = producer_hash
        receipt["controller_socket"] = str(config.socket)
        decoder = PixelDecoder(crop=profile.canvas_crop)
        target_origin = time.monotonic()
        targets = [target_origin + float(index + 1) for index in range(8)]
        receipt["targets"] = targets
        previous_start: float | None = None
        previous_completion: float | None = None
        previous_sequence: int | None = None

        for index, target in enumerate(targets):
            phase = f"sample_{index}_target_wait"
            delay = target - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            actual_start = time.monotonic()
            deadline = target + 1.0
            if actual_start >= deadline:
                raise RuntimeError(f"paused diagnostic missed sample {index} deadline before status")
            phase = f"sample_{index}_status_before"
            status = _status_from_ipc(config, timeout=min(0.25, max(0.001, deadline - time.monotonic())))
            generation = _check_paused_status(status, expected_generation=expected_generation)
            if expected_generation is None:
                expected_generation = generation
                receipt["controller_generation"] = generation
                receipt["controller_boot_before_first_frame"] = status.get("boot", "")
            if time.monotonic() >= deadline:
                raise RuntimeError(f"paused diagnostic status exceeded sample {index} deadline")

            phase = f"sample_{index}_owner_capture_ipc"
            output = output_dir / f"paused-{index:02d}.png"
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError(f"paused diagnostic exhausted sample {index} budget before owner IPC")
            sample_request = {
                "command": "paused_region_sample",
                "generation": generation,
                "parent_started": actual_start,
                "deadline": deadline,
                "config_file_sha256": receipt["config_file_sha256"],
                "config_semantic_sha256": receipt["config_semantic_sha256"],
            }
            try:
                response = _socket_request(
                    config.socket,
                    sample_request,
                    timeout=remaining,
                    response_deadline=deadline,
                    failure_evidence_grace=0.25,
                )
            except TimeoutError as exc:
                receipt["late_failure_evidence"] = {
                    "state": "unknown",
                    "grace_seconds": 0.25,
                    "error": str(exc),
                }
                raise
            ipc_returned = time.monotonic()
            if (
                not isinstance(response, dict)
                or response.get("ok") is not True
                and response.get("ok") is not False
            ):
                raise RuntimeError(f"paused diagnostic owner IPC response {index} has an invalid schema")
            if ipc_returned >= deadline:
                late_response = _bounded_failure_response(response)
                receipt["late_owner_response"] = late_response
                if response.get("ok") is False:
                    receipt["owner_failure"] = late_response
                raise RuntimeError(
                    f"paused diagnostic owner IPC response {index} arrived after its qualification deadline"
                )
            if response.get("ok") is False:
                # Retain bounded owner failure/artifact metadata before any
                # optional sample validation can fail on a secondary issue.
                receipt["owner_failure"] = _bounded_failure_response(response)
            if response["ok"] is True:
                if set(response) != {"ok", "sample"}:
                    raise RuntimeError(
                        f"paused diagnostic successful IPC response {index} has unexpected fields"
                    )
            else:
                expected_failure_fields = {"ok", "error"}
                if "failure" in response:
                    expected_failure_fields.add("failure")
                if "sample" in response:
                    expected_failure_fields.add("sample")
                if set(response) != expected_failure_fields or not isinstance(response.get("error"), str):
                    raise RuntimeError(f"paused diagnostic failed IPC response {index} has invalid fields")
                owner_failure = response.get("failure")
                if owner_failure is not None:
                    failure_fields = {
                        "phase",
                        "error",
                        "owner_entered",
                        "owner_returned",
                        "artifact_directory",
                        "receipt_path",
                        "published_png",
                        "producer_attempt",
                        "cleanup",
                        "generation",
                        "config_file_sha256",
                        "config_semantic_sha256",
                        "owner_config_semantic_sha256",
                        "lease_held",
                        "armed",
                    }
                    if isinstance(owner_failure, dict) and "sample" in owner_failure:
                        failure_fields.add("sample")
                    if isinstance(owner_failure, dict) and "receipt_persist_error" in owner_failure:
                        failure_fields.add("receipt_persist_error")
                    if not isinstance(owner_failure, dict) or set(owner_failure) != failure_fields:
                        raise RuntimeError(f"paused diagnostic owner failure {index} has invalid fields")
                    _validate_producer_attempt(owner_failure.get("producer_attempt"), index)
                    if (
                        owner_failure.get("generation") != generation
                        or owner_failure.get("config_file_sha256") != receipt["config_file_sha256"]
                        or owner_failure.get("config_semantic_sha256") != receipt["config_semantic_sha256"]
                        or owner_failure.get("owner_config_semantic_sha256")
                        != receipt["config_semantic_sha256"]
                        or not isinstance(owner_failure.get("phase"), str)
                        or not isinstance(owner_failure.get("error"), str)
                    ):
                        raise RuntimeError(f"paused diagnostic owner failure {index} is not request-bound")
            sample_data = response.get("sample")
            if sample_data is not None:
                if not isinstance(sample_data, dict):
                    raise RuntimeError(f"paused diagnostic owner sample {index} is not an object")
                output_bytes = _owner_png_bytes(
                    sample_data,
                    profile,
                    producer_hash,
                    str(receipt["config_file_sha256"]),
                    str(receipt["config_semantic_sha256"]),
                    generation,
                    actual_start,
                    deadline,
                    Path(config.capture_dir),
                    index,
                )
                _atomic_private_png(output, output_bytes)
                cleanup = receipt["cleanup"]
                assert isinstance(cleanup, dict)
                published = cleanup["published_client_pngs"]
                assert isinstance(published, list)
                published.append(str(output))
                # A failed owner post-check can still return a real published
                # capture. Save it before failing this sample.
                if response.get("ok") is not True:
                    raise RuntimeError(
                        f"paused diagnostic owner refused sample {index}: {response.get('error')}"
                    )
            elif response.get("ok") is not True:
                raise RuntimeError(f"paused diagnostic owner refused sample {index}: {response.get('error')}")
            else:
                raise RuntimeError(f"paused diagnostic owner omitted sample {index}")
            assert isinstance(sample_data, dict)
            identity = sample_data["identity"]
            assert isinstance(identity, dict)
            live_identity = identity
            if identity_baseline is None:
                identity_baseline = live_identity
                receipt["identity"] = identity_baseline
            elif live_identity != identity_baseline:
                raise RuntimeError(f"paused diagnostic identity changed at sample {index}")
            rectangle = tuple(sample_data["source"]["rectangle"])  # type: ignore[index]
            attempt_data = sample_data["receipt"]
            assert isinstance(attempt_data, dict)
            output_sha256 = hashlib.sha256(output_bytes).hexdigest()
            if sample_data.get("identity_after") != identity.get("fingerprint"):
                raise RuntimeError(f"paused diagnostic sample {index} identity changed after capture")
            cleanup_snapshot = sample_data["cleanup"]
            if not isinstance(cleanup_snapshot, dict) or cleanup_snapshot.get("empty") is not True:
                raise RuntimeError(f"paused diagnostic sample {index} did not retire its owned capture")
            if not (
                cleanup_snapshot.get("lease_held") is True
                and cleanup_snapshot.get("watchdog_healthy") is True
                and cleanup_snapshot.get("armed") is False
            ):
                raise RuntimeError(f"paused diagnostic owner lease/watchdog state changed at sample {index}")
            owner_returned = _finite_time(sample_data.get("owner_returned"), f"sample {index} owner return")
            capture_returned = _finite_time(
                sample_data.get("capture_returned"), f"sample {index} capture return"
            )
            receipt_request = _finite_time(
                attempt_data.get("request_started"), f"sample {index} receipt request"
            )
            lock_acquired = _finite_time(
                attempt_data.get("lock_acquired"), f"sample {index} screenshot lock acquisition"
            )
            ack_sent = _finite_time(attempt_data.get("ack_sent"), f"sample {index} receipt ack")
            capture_started = _finite_time(
                attempt_data.get("capture_started"), f"sample {index} receipt start"
            )
            receipt_returned = _finite_time(
                attempt_data.get("capture_returned"), f"sample {index} receipt return"
            )
            if (
                not actual_start
                <= receipt_request
                <= lock_acquired
                <= ack_sent
                <= capture_started
                <= receipt_returned
                <= capture_returned
                <= owner_returned
                <= ipc_returned
            ):
                raise RuntimeError(f"paused diagnostic sample {index} receipt timestamps are out of order")
            if receipt_returned > deadline or owner_returned > deadline or ipc_returned >= deadline:
                raise RuntimeError(f"paused diagnostic owner IPC exceeded sample {index} deadline")
            phase = f"sample_{index}_decode"
            decode_started = time.monotonic()
            with Image.open(output) as image:
                image.load()
                if image.format != "PNG" or image.size != (256, 256):
                    raise RuntimeError(f"paused diagnostic sample {index} is not an exact 256x256 PNG")
                png_loaded = time.monotonic()
                # Preserve the outer pre-work timestamp as PixelDecoder's
                # observation time.  The producer's later Shell timestamp is
                # evidence only and never rejuvenates this frame.
                sample = decoder.decode(
                    image,
                    monotonic=actual_start,
                    window_identity=str(identity["fingerprint"]),
                )
            decode_end = time.monotonic()
            if sample.capture_monotonic != actual_start:
                raise RuntimeError(f"paused diagnostic decoder changed sample {index} observation time")
            if sample.kind != "FRESH" or sample.frame is None:
                raise RuntimeError(f"paused diagnostic sample {index} is not a fresh decoded frame")
            frame = sample.frame
            if expected_boot is None:
                expected_boot = frame.boot
                receipt["controller_boot_at_first_frame"] = frame.boot
            if frame.boot != expected_boot:
                raise RuntimeError(f"paused diagnostic frame boot changed at sample {index}")
            if previous_sequence is not None and frame.sequence <= previous_sequence:
                raise RuntimeError(f"paused diagnostic sequence did not advance at sample {index}")
            if hashlib.sha256(config_path.read_bytes()).hexdigest() != receipt["config_file_sha256"]:
                raise RuntimeError(f"paused diagnostic config changed during sample {index}")
            sample_completed = time.monotonic()
            duration = sample_completed - actual_start
            if not math.isfinite(duration) or duration >= 1.0 or sample_completed >= deadline:
                raise RuntimeError(f"paused diagnostic sample {index} exceeded the strict one-second gate")
            if previous_start is not None and not 0.75 <= actual_start - previous_start <= 1.25:
                raise RuntimeError(
                    f"paused diagnostic sample {index} start interval is outside 0.75..1.25 seconds"
                )
            if previous_completion is not None and not 0.75 <= sample_completed - previous_completion <= 1.25:
                raise RuntimeError(
                    f"paused diagnostic sample {index} completion interval is outside 0.75..1.25 seconds"
                )
            sample_record: dict[str, object] = {
                "index": index,
                "target_monotonic": target,
                "actual_start_monotonic": actual_start,
                "deadline_monotonic": deadline,
                "owner_capture_returned_monotonic": capture_returned,
                "owner_returned_monotonic": owner_returned,
                "ipc_returned_monotonic": ipc_returned,
                "decode_started_monotonic": decode_started,
                "png_loaded_monotonic": png_loaded,
                "decode_end_monotonic": decode_end,
                "sample_completed_monotonic": sample_completed,
                "png_load_seconds": png_loaded - decode_started,
                "pixel_decoder_seconds": decode_end - png_loaded,
                "duration_seconds": duration,
                "controller_state": status["state"],
                "controller_generation": generation,
                "controller_boot": status.get("boot", ""),
                "kind": sample.kind,
                "boot": frame.boot,
                "sequence": frame.sequence,
                "identity": live_identity,
                "rectangle": list(rectangle),
                "capture_sha256": output_sha256,
                "capture_bytes": len(output_bytes),
                "attempt": attempt_data,
                "cleanup": cleanup_snapshot,
                "owner_artifact_directory": sample_data["artifact_directory"],
                "owner_artifact_png": sample_data["artifact_png"],
                "png": str(output),
            }
            samples = receipt["samples"]
            assert isinstance(samples, list)
            samples.append(sample_record)
            previous_sequence = frame.sequence
            previous_start = actual_start
            previous_completion = sample_completed

        phase = "status_after_run"
        status_after = _status_from_ipc(config, timeout=1.0)
        final_generation = _check_paused_status(status_after, expected_generation=expected_generation)
        receipt["controller_generation_after_run"] = final_generation
        receipt["controller_boot_after_run"] = status_after.get("boot", "")
        if len(receipt["samples"]) != 8:  # type: ignore[arg-type]
            raise RuntimeError("paused diagnostic did not complete exactly eight samples")
        receipt["state"] = "passed"
        receipt["finished_monotonic"] = time.monotonic()
    except Exception as exc:
        failure = exc
        receipt["state"] = "failed"
        receipt["failure"] = {"phase": phase, "error": f"{type(exc).__name__}: {exc}"}
        receipt["finished_monotonic"] = time.monotonic()
    finally:
        cleanup = receipt["cleanup"]
        assert isinstance(cleanup, dict)
        cleanup["published_client_pngs"] = sorted(str(path) for path in output_dir.glob("paused-*.png"))
        try:
            _atomic_receipt(receipt_path, receipt)
        except Exception as exc:
            if failure is None:
                failure = exc
            raise RuntimeError(f"paused diagnostic could not persist receipt {receipt_path}: {exc}") from exc
    if failure is not None:
        detail = receipt.get("failure")
        raise RuntimeError(
            f"paused diagnostic failed; evidence={receipt_path}; failure={detail}"
        ) from failure
    receipt["receipt_path"] = str(receipt_path)
    return receipt


def _compiled_parser_checks() -> None:
    if not BINARY.is_file():
        raise RuntimeError(f"private binary missing: {BINARY}")
    cases = [
        ["--telemetry-region"],
        ["--telemetry-region", "--telemetry-x", "1", "--telemetry-x", "1"],
        [
            "--telemetry-region",
            "--telemetry-x",
            "1",
            "--telemetry-y",
            "2",
            "--telemetry-width",
            "256",
            "--telemetry-height",
            "256",
            "--telemetry-owner-fd",
            "3",
            "--telemetry-exec-fd",
            "4",
            "--telemetry-nonce",
            "n",
            "--file",
            "/tmp/x",
            "--area",
        ],
        [
            "--telemetry-region",
            "--telemetry-x",
            "1",
            "--telemetry-y",
            "2",
            "--telemetry-width",
            "256",
            "--telemetry-height",
            "256",
            "--telemetry-owner-fd",
            "3",
            "--telemetry-exec-fd",
            "4",
            "--telemetry-nonce",
            "n",
            "--file",
            "relative.png",
        ],
        [
            "--telemetry-region",
            "--telemetry-x",
            "1",
            "--telemetry-y",
            "2",
            "--telemetry-width",
            "256",
            "--telemetry-height",
            "256",
            "--telemetry-owner-fd",
            "3",
            "--telemetry-exec-fd",
            "4",
            "--telemetry-nonce",
            "n",
            "--file",
            "/tmp/x",
            "--telemetry-xfoo",
        ],
        [
            "--telemetry-region",
            "--telemetry-x",
            "1",
            "--telemetry-y",
            "2",
            "--telemetry-width",
            "256",
            "--telemetry-height",
            "256",
            "--telemetry-owner-fd",
            "3",
            "--telemetry-exec-fd",
            "4",
            "--telemetry-nonce",
            "n",
            "--file",
            "/tmp/x",
            "-f",
            "/tmp/y",
        ],
        [
            "--telemetry-region",
            "--telemetry-x",
            "1",
            "--telemetry-y",
            "2",
            "--telemetry-width",
            "256",
            "--telemetry-height",
            "256",
            "--telemetry-owner-fd",
            "3",
            "--telemetry-exec-fd",
            "4",
            "--telemetry-nonce",
            "n",
            "-f",
            "/tmp/x",
            "-d",
            "0",
        ],
        [
            "--telemetry-region",
            "--telemetry-x",
            "1",
            "--telemetry-y",
            "2",
            "--telemetry-width",
            "128",
            "--telemetry-height",
            "256",
            "--telemetry-owner-fd",
            "3",
            "--telemetry-exec-fd",
            "4",
            "--telemetry-nonce",
            "n",
            "--file",
            "/tmp/x",
        ],
    ]
    for args in cases:
        result = subprocess.run([str(BINARY), *args], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            raise RuntimeError(f"compiled parser accepted invalid telemetry argv: {args}")


def self_check() -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert document["telemetry_options"]["branch"] == "ScreenshotArea"
    assert document["telemetry_options"]["exact_size"] == [256, 256]
    text = PATCH.read_text(encoding="utf-8")
    for required in ("ScreenshotArea", "telemetry_owner_fd", "primary_owner", "flash"):
        assert required in text, required
    if not _strict_argv(
        [
            "--telemetry-region",
            "--telemetry-x",
            "1",
            "--telemetry-y",
            "2",
            "--telemetry-width",
            "256",
            "--telemetry-height",
            "256",
            "--telemetry-owner-fd",
            "3",
            "--telemetry-exec-fd",
            "4",
            "--telemetry-nonce",
            "n",
            "--file",
            "/tmp/x",
        ]
    ):
        raise RuntimeError("offline typed option model rejected the valid contract")
    if _strict_argv(
        [
            "--telemetry-region",
            "--telemetry-x",
            "1",
            "--telemetry-y",
            "2",
            "--telemetry-width",
            "128",
            "--telemetry-height",
            "256",
            "--telemetry-owner-fd",
            "3",
            "--telemetry-exec-fd",
            "4",
            "--telemetry-nonce",
            "n",
            "--file",
            "/tmp/x",
        ]
    ):
        raise RuntimeError("offline typed option model accepted wrong dimensions")
    for invalid in (
        ["--telemetry-region", "--telemetry-x", "010", "--telemetry-y", "2"],
        ["--telemetry-region", "--file", "/tmp/x", "-f", "/tmp/y"],
        ["--telemetry-region", "-d", "0"],
    ):
        if _strict_argv(invalid):
            raise RuntimeError(f"offline typed option model accepted forbidden argv: {invalid}")
    for value in (0.0, 1.0, 42.5):
        if _finite_time(value, "self-check timestamp") != float(value):
            raise RuntimeError("paused diagnostic timestamp parser changed a finite value")
    for invalid_time in (True, float("nan"), float("inf"), "1.0"):
        try:
            _finite_time(invalid_time, "self-check timestamp")
        except RuntimeError:
            pass
        else:
            raise RuntimeError("paused diagnostic accepted a malformed monotonic timestamp")
    for interval in (0.75, 1.0, 1.25):
        if not 0.75 <= interval <= 1.25:
            raise RuntimeError("paused diagnostic rejected an allowed interval boundary")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--paused-diagnostic", action="store_true")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--evidence-dir", type=Path)
    options = parser.parse_args()
    if options.paused_diagnostic:
        if options.self_test or options.self_check:
            parser.error("--paused-diagnostic cannot be combined with offline self-checks")
        if options.config is None or options.evidence_dir is None:
            parser.error("--paused-diagnostic requires --config and --evidence-dir")
        result = run_paused_diagnostic(options.config, options.evidence_dir)
        print(
            json.dumps(
                {
                    "state": result["state"],
                    "receipt": result["receipt_path"],
                    "samples": len(result["samples"]),  # type: ignore[arg-type]
                    "producer": result["producer"],
                },
                sort_keys=True,
            )
        )
        return 0
    if options.config is not None or options.evidence_dir is not None:
        parser.error("--config and --evidence-dir require --paused-diagnostic")
    if not options.self_test and not options.self_check:
        parser.error("choose --self-test and/or --self-check")
    if options.self_check:
        self_check()
    if options.self_test:
        _compiled_parser_checks()
        _protocol_fixture()
        _compiled_private_shell_fixture()
    print(
        json.dumps(
            {"self_check": options.self_check, "self_test": options.self_test, "binary": str(BINARY)},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
