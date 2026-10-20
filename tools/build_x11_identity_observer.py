"""Hermetic double-build and private publication for the X11 identity observer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "native" / "x11_identity_observer"
TARGET = "x86_64-unknown-linux-gnu"
TOOLCHAIN = Path("/home/dev/.cache/crowley/rust-toolchain-1.85.1/toolchain/bin")
LINKER = Path("/usr/bin/cc")
STATIC_INPUTS = tuple(
    Path(p)
    for p in (
        "/usr/lib/x86_64-linux-gnu/libX11.a",
        "/usr/lib/x86_64-linux-gnu/libxcb.a",
        "/usr/lib/x86_64-linux-gnu/libXau.a",
        "/usr/lib/x86_64-linux-gnu/libXdmcp.a",
    )
)
EXPECTED_SOURCE_FILES = frozenset({"Cargo.toml", "Cargo.lock", "src/main.rs"})
EXPECTED_SOURCE_DIRS = frozenset({"src"})


def digest(path: Path) -> str:
    h = hashlib.sha256()
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as exc:
        raise RuntimeError(f"cannot open stable input: {path}") from exc
    try:
        before = os.fstat(fd)
        while chunk := os.read(fd, 1024 * 1024):
            h.update(chunk)
        after = os.fstat(fd)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise RuntimeError(f"input changed while being read: {path}")
    finally:
        os.close(fd)
    return h.hexdigest()


def _metadata(path: Path) -> tuple[int, int, int, int, int]:
    try:
        info = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"input is unavailable: {path}") from exc
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"input is not a regular non-symlink file: {path}")
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_mode)


def _version(path: Path) -> str:
    return subprocess.check_output([str(path), "--version"], text=True).splitlines()[0]


def linker_inputs() -> dict[str, dict[str, str]]:
    """Resolve and pin both the compiler driver and the linker it selects."""

    driver = Path(os.path.realpath(LINKER))
    selected = subprocess.check_output(
        [str(LINKER), "--print-prog-name=ld"],
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        text=True,
    ).strip()
    linker = Path(selected)
    if not linker.is_absolute():
        for candidate in (Path("/usr/bin") / linker, Path("/bin") / linker):
            if candidate.is_file():
                linker = candidate
                break
        else:
            raise RuntimeError(f"selected linker is not an absolute system file: {selected!r}")
    linker = Path(os.path.realpath(linker))
    if not driver.is_file() or not linker.is_file():
        raise RuntimeError("compiler driver or selected linker is unavailable")
    return {
        "driver": {
            "path": str(LINKER),
            "realpath": str(driver),
            "sha256": digest(driver),
            "version": _version(LINKER),
        },
        "ld": {
            "path": selected,
            "realpath": str(linker),
            "sha256": digest(linker),
            "version": _version(linker),
        },
    }


def exact_toolchain() -> dict[str, str]:
    values = {}
    for name in ("rustc", "cargo", "rustfmt"):
        values[name] = subprocess.check_output([str(TOOLCHAIN / name), "--version"], text=True).strip()
    expected = {
        "rustc": "rustc 1.85.1 (4eb161250 2025-03-15)",
        "cargo": "cargo 1.85.1 (d73d2caf9 2024-12-31)",
        "rustfmt": "rustfmt 1.8.0-stable (4eb161250e 2025-03-15)",
    }
    if values != expected:
        raise RuntimeError(f"unexpected reviewed toolchain: {values}")
    return values


def copy_source(destination: Path, *, source_snapshot: Path) -> None:
    shutil.copytree(source_snapshot / "source", destination, ignore=shutil.ignore_patterns("target"))
    shutil.copytree(source_snapshot / "deps", destination / "deps")


def validate_source_tree(source: Path) -> None:
    """Reject build configuration, symlinks, and unreviewed Rust inputs."""

    if not source.is_dir() or source.is_symlink():
        raise RuntimeError("observer source root is not a directory")
    seen_files: set[str] = set()
    seen_dirs: set[str] = set()
    for entry in source.rglob("*"):
        relative = entry.relative_to(source)
        if relative.parts and relative.parts[0] == "target":
            continue
        if entry.is_symlink():
            raise RuntimeError(f"observer source contains a symlink: {relative}")
        if entry.is_dir():
            seen_dirs.add(relative.as_posix())
        elif entry.is_file():
            seen_files.add(relative.as_posix())
        else:
            raise RuntimeError(f"observer source contains unsupported input: {relative}")
    if seen_files != EXPECTED_SOURCE_FILES:
        raise RuntimeError(f"observer source files are not the reviewed three-file set: {sorted(seen_files)}")
    if seen_dirs != EXPECTED_SOURCE_DIRS:
        raise RuntimeError(f"observer source directories are not the reviewed layout: {sorted(seen_dirs)}")


def refuse_ambient_cargo_configuration(source: Path) -> None:
    """Do not let an ancestor-owned Cargo config alter the reviewed build."""

    resolved = source.resolve()
    for ancestor in (resolved, *resolved.parents):
        for name in (".cargo/config", ".cargo/config.toml"):
            candidate = ancestor / name
            if candidate.exists():
                raise RuntimeError(f"ambient Cargo configuration is not allowed: {candidate}")


def make_source_snapshot(destination: Path) -> dict[str, object]:
    """Capture all source/link inputs once, before either independent build."""

    destination.mkdir(mode=0o700, parents=True)
    copy_source_tree = destination / "source"
    validate_source_tree(SOURCE)
    refuse_ambient_cargo_configuration(SOURCE)
    source_metadata_before = {name: _metadata(SOURCE / name) for name in EXPECTED_SOURCE_FILES}
    source_hashes_before = {
        f"native/x11_identity_observer/{name}": digest(SOURCE / name) for name in EXPECTED_SOURCE_FILES
    }
    shutil.copytree(SOURCE, copy_source_tree, ignore=shutil.ignore_patterns("target"))
    validate_source_tree(copy_source_tree)
    source_hashes_snapshot = {
        f"native/x11_identity_observer/{name}": digest(copy_source_tree / name)
        for name in EXPECTED_SOURCE_FILES
    }
    source_hashes_after = {
        f"native/x11_identity_observer/{name}": digest(SOURCE / name) for name in EXPECTED_SOURCE_FILES
    }
    source_metadata_after = {name: _metadata(SOURCE / name) for name in EXPECTED_SOURCE_FILES}
    if (
        source_hashes_before != source_hashes_snapshot
        or source_hashes_before != source_hashes_after
        or source_metadata_before != source_metadata_after
    ):
        raise RuntimeError("observer source changed while taking the build snapshot")
    (destination / "deps").mkdir(mode=0o700)
    static_before = {str(path): (digest(path), _metadata(path)) for path in STATIC_INPUTS}
    for dep in STATIC_INPUTS:
        shutil.copy2(dep, destination / "deps" / dep.name)
    input_hashes = {}
    for dep in STATIC_INPUTS:
        copied = destination / "deps" / dep.name
        copied_hash = digest(copied)
        if copied_hash != static_before[str(dep)][0]:
            raise RuntimeError(f"static X11 input changed while being copied: {dep}")
        input_hashes[str(dep)] = copied_hash
    static_after = {str(path): (digest(path), _metadata(path)) for path in STATIC_INPUTS}
    if static_before != static_after:
        raise RuntimeError("static X11 inputs changed during the build snapshot")
    return {"source_sha256": source_hashes_snapshot, "static_inputs": input_hashes}


def _atomic_private_publish(path: Path, data: bytes, mode: int) -> None:
    """Durably publish one owner-only artifact without replacing different bytes."""

    if path.is_symlink():
        raise RuntimeError(f"refusing to replace a symlink: {path}")
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(fd, mode)
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise RuntimeError(f"could not write temporary publication: {path}")
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = -1
        if path.exists() and digest(path) != hashlib.sha256(data).hexdigest():
            raise RuntimeError(f"refusing to replace a different published artifact: {path}")
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if fd >= 0:
            os.close(fd)
        if temporary.exists():
            temporary.unlink()


def build_once(source: Path, target: Path, cargo_home: Path) -> Path:
    # Cargo resolves configuration from the build working directory and every
    # ancestor of it.  The reviewed source snapshot is copied into a private
    # temporary tree, so checking only ``SOURCE`` would miss a config planted
    # above that real cwd.
    refuse_ambient_cargo_configuration(source)
    env = {
        "PATH": f"{TOOLCHAIN}:/usr/bin:/bin",
        "HOME": str(cargo_home),
        "TMPDIR": str(target.parent / "tmp"),
        "CARGO_HOME": str(cargo_home),
        "CARGO_NET_OFFLINE": "true",
        "CARGO_TERM_COLOR": "never",
        "RUSTC": str(TOOLCHAIN / "rustc"),
        "RUSTC_WRAPPER": "",
        "RUSTC_WORKSPACE_WRAPPER": "",
        "SOURCE_DATE_EPOCH": "0",
        "TZ": "UTC",
        "LC_ALL": "C",
        "RUSTFLAGS": (
            f"-L native={source / 'deps'} -C linker={LINKER} "
            f"--remap-path-prefix={source}=/crowley/x11-identity-observer"
        ),
    }
    Path(env["TMPDIR"]).mkdir(mode=0o700, parents=True, exist_ok=True)
    subprocess.run(
        [
            str(TOOLCHAIN / "cargo"),
            "build",
            "--release",
            "--locked",
            "--offline",
            "--target",
            TARGET,
            "--target-dir",
            str(target),
        ],
        cwd=source,
        env=env,
        check=True,
    )
    return target / TARGET / "release" / "x11_identity_observer"


def publish(output: Path) -> dict[str, object]:
    toolchain = exact_toolchain()
    tool_inputs = linker_inputs()
    with tempfile.TemporaryDirectory(prefix="crowley-x11-observer-") as temp:
        root = Path(temp)
        snapshot = make_source_snapshot(root / "snapshot")
        first, second = root / "source-a", root / "source-b"
        copy_source(first, source_snapshot=root / "snapshot")
        copy_source(second, source_snapshot=root / "snapshot")
        cargo_home = root / "cargo-home"
        cargo_home.mkdir(mode=0o700)
        a = build_once(first, root / "target-a", cargo_home)
        b = build_once(second, root / "target-b", cargo_home)
        first_bytes, second_bytes = a.read_bytes(), b.read_bytes()
        if first_bytes != second_bytes:
            raise RuntimeError("independent observer builds differ")
        if linker_inputs() != tool_inputs:
            raise RuntimeError("compiler/linker inputs changed during publication")
        output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        parent_info = output.parent.stat()
        if parent_info.st_uid != os.getuid() or parent_info.st_mode & 0o077:
            raise RuntimeError("observer publication directory is not private and user-owned")
        os.chmod(output.parent, 0o700)
        _atomic_private_publish(output, first_bytes, 0o700)
    manifest = {
        "schema": "crowley.x11-identity-observer.v1",
        "target": TARGET,
        "binary": str(output),
        "binary_sha256": digest(output),
        "source_sha256": snapshot["source_sha256"],
        "static_inputs": snapshot["static_inputs"],
        "toolchain": toolchain,
        "linker": tool_inputs,
    }
    manifest_path = output.with_suffix(".manifest.json")
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_private_publish(manifest_path, manifest_bytes, 0o600)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path.home() / ".cache/crowley/x11-identity-observer/v1/observer"
    )
    args = parser.parse_args()
    print(json.dumps(publish(args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
