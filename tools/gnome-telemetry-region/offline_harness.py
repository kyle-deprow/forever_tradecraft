#!/usr/bin/env python3
# ruff: noqa: E501
"""Offline producer/admission checks for the typed telemetry-region contract."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import select
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

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(
    os.environ.get("GNOME_TELEMETRY_REGION_STAGE", "/home/dev/.cache/crowley/gnome-telemetry-region-r2")
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
        if token in scalar:
            counts[token] = counts.get(token, 0) + 1
            if index + 1 >= len(argv):
                return False
            values[token] = argv[index + 1]
            index += 2
            continue
        if token.startswith("--") and any(token.startswith(name + "=") for name in scalar):
            name, value = token.split("=", 1)
            counts[name] = counts.get(name, 0) + 1
            values[name] = value
        elif token in conflicts:
            return False if telemetry else True
        index += 1
    if not telemetry:
        return not any(key.startswith("--telemetry-") for key in counts)
    if counts.get("--telemetry-region", 0) != 1:
        return False
    if any(counts.get(key, 0) != 1 for key in scalar):
        return False
    try:
        rectangle = tuple(
            int(values[key], 10)
            for key in ("--telemetry-x", "--telemetry-y", "--telemetry-width", "--telemetry-height")
        )
        owner_fd = int(values["--telemetry-owner-fd"], 10)
        exec_fd = int(values["--telemetry-exec-fd"], 10)
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
            "ack=os.read(fd,4096).decode(); assert ack == json.dumps({'type':'ACK','protocol':1,'nonce':nonce},separators=(',',':'))+'\\n'\n"
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
        parent.sendall(
            (
                json.dumps({"type": "ACK", "protocol": 1, "nonce": nonce}, separators=(",", ":")) + "\n"
            ).encode()
        )
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
            "GLib.timeout_add(GLib.PRIORITY_DEFAULT, 250, () => { GLib.file_set_contents(ARGV[1], 'ready'); return GLib.SOURCE_REMOVE; });\n"
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
            f"exec gjs {shell} {payload_path} {ready_path} >{root / 'gjs.stdout'} 2>{root / 'gjs.stderr'}\n"
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    options = parser.parse_args()
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
