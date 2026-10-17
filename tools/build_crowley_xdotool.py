#!/usr/bin/env python3
"""Build and atomically publish the pinned private XTEST xdotool artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from crowley.session.input_tool import (
    ARCHIVE_BASENAME,
    MANIFEST_BASENAME,
    PINNED_ARCHIVE_SHA256,
    PINNED_COMMIT,
    PRIVATE_TOOL_BASENAME,
    PRIVATE_TOOL_ROOT,
    InputToolError,
    verify_artifact,
)

VENDORED_SOURCE_ARCHIVE = Path(__file__).resolve().parents[1] / "vendor" / "xdotool-source.tar.gz"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=cwd, check=True, env=env)


def _assert_static_linkage(binary: Path) -> None:
    readelf = shutil.which("readelf")
    if readelf is None:
        raise RuntimeError("readelf is required to verify private xdotool linkage")
    dynamic = subprocess.run([readelf, "-d", str(binary)], check=True, text=True, capture_output=True)
    if "libxdo" in dynamic.stdout:
        raise RuntimeError("private xdotool unexpectedly has a NEEDED libxdo dependency")
    symbols = subprocess.run([readelf, "-Ws", str(binary)], check=True, text=True, capture_output=True)
    if "XTestFakeMotionEvent" not in symbols.stdout:
        raise RuntimeError("private xdotool does not contain XTestFakeMotionEvent")
    source = subprocess.run([readelf, "-Ws", str(binary)], check=True, text=True, capture_output=True)
    if "xdo_move_mouse" not in source.stdout:
        raise RuntimeError("private xdotool does not contain the expected xdo_move_mouse implementation")
    objdump = shutil.which("objdump")
    if objdump is None:
        raise RuntimeError("objdump is required to verify the xdo_move_mouse call path")
    disassembly = subprocess.run(
        [objdump, "-d", "--disassemble=xdo_move_mouse", str(binary)],
        check=True,
        text=True,
        capture_output=True,
    )
    if "XTestFakeMotionEvent" not in disassembly.stdout:
        raise RuntimeError("xdo_move_mouse does not reference XTestFakeMotionEvent")


def build(archive: Path, destination: Path) -> Path:
    archive = archive.resolve()
    if sha256(archive) != PINNED_ARCHIVE_SHA256:
        raise RuntimeError("source archive digest does not match the pinned upstream archive")
    if destination.is_symlink():
        raise RuntimeError("private artifact destination cannot be a symlink")
    if destination.exists():
        try:
            verify_artifact(destination)
            _assert_static_linkage(destination / PRIVATE_TOOL_BASENAME)
        except InputToolError as exc:
            raise RuntimeError("existing private artifact is not the pinned publication") from exc
        except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
            raise RuntimeError("existing private artifact failed static XTEST linkage verification") from exc
        return destination
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="crowley-xdotool-build-") as temporary:
        work = Path(temporary)
        with tarfile.open(archive, "r:gz") as source:
            expected_root = f"xdotool-{PINNED_COMMIT}"
            root_members = [
                member for member in source.getmembers() if member.name.rstrip("/") == expected_root
            ]
            if len(root_members) != 1 or not root_members[0].isdir():
                raise RuntimeError("source archive root is not the pinned commit")
            build_env = os.environ.copy()
            build_env["SOURCE_DATE_EPOCH"] = str(int(root_members[0].mtime))
            source.extractall(work, filter="data")
        roots = [item for item in work.iterdir() if item.is_dir()]
        if len(roots) != 1 or roots[0].name != expected_root:
            raise RuntimeError("source archive root is not the pinned commit")
        source_root = roots[0]
        # Upstream's static target directly links xdo.o and xdo_search.o; all
        # X11 libraries remain ordinary dynamic dependencies of the executable.
        run(["make", "clean"], cwd=source_root, env=build_env)
        run(["make", "-B", "static"], cwd=source_root, env=build_env)
        built = source_root / "xdotool.static"
        if not built.is_file() or not os.access(built, os.X_OK):
            raise RuntimeError("upstream static target did not produce an executable")
        _assert_static_linkage(built)
        # Stage beside the destination so the final directory rename remains
        # atomic even when the build happens under /tmp on another filesystem.
        staging = destination.parent / f".{destination.name}.staging-{os.getpid()}"
        if staging.exists():
            raise RuntimeError("unexpected existing publication staging path")
        staging.mkdir(mode=0o700)
        executable = staging / PRIVATE_TOOL_BASENAME
        shutil.copyfile(built, executable)
        executable.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        source_copy = staging / ARCHIVE_BASENAME
        shutil.copyfile(archive, source_copy)
        source_copy.chmod(stat.S_IRUSR | stat.S_IWUSR)
        manifest = {
            "commit": PINNED_COMMIT,
            "archive_sha256": PINNED_ARCHIVE_SHA256,
            "executable": PRIVATE_TOOL_BASENAME,
            "executable_sha256": sha256(executable),
        }
        manifest_path = staging / MANIFEST_BASENAME
        manifest_path.write_text(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
        )
        manifest_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        try:
            if destination.is_symlink():
                raise RuntimeError("private artifact destination appeared as a symlink during publication")
            if destination.exists():
                try:
                    verify_artifact(destination)
                    _assert_static_linkage(destination / PRIVATE_TOOL_BASENAME)
                except InputToolError as exc:
                    raise RuntimeError("existing private artifact is not the pinned publication") from exc
                except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
                    raise RuntimeError(
                        "existing private artifact failed static XTEST linkage verification"
                    ) from exc
                return destination
            os.replace(staging, destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    verify_artifact(destination)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=VENDORED_SOURCE_ARCHIVE)
    # Publication is deliberately fixed; callers cannot redirect production
    # resolution through an arbitrary configured executable directory.
    args = parser.parse_args(argv)
    build(args.archive, PRIVATE_TOOL_ROOT)
    print(PRIVATE_TOOL_ROOT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
