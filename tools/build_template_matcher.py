"""Build and privately publish the reviewed Rust template matcher.

The executable is deliberately built twice in independent target directories.
An existing publication is accepted only after it matches the independently
rebuilt bytes and the exact source/toolchain manifest; the adjacent manifest
is never used as the binary's trust anchor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "native" / "template_matcher"
SOURCE_FILES = ("Cargo.toml", "Cargo.lock", "src/main.rs")
TARGET = "x86_64-unknown-linux-gnu"
PROTOCOL = "CRWTM001"
VERSION = "v1"
ARTIFACT_NAME = f"template_matcher-{VERSION}"
MANIFEST_NAME = f"{ARTIFACT_NAME}.manifest.json"
BUILD_CACHE_ROOT = Path.home() / ".cache" / "crowley" / "template-matcher" / "build-v1"
EXPECTED_RUSTC = "rustc 1.85.1 (4eb161250 2025-03-15)"
EXPECTED_CARGO = "cargo 1.85.1 (d73d2caf9 2024-12-31)"
EXPECTED_RUSTFMT = "rustfmt 1.8.0-stable (4eb161250e 2025-03-15)"
CARGO_CONFIG_OVERRIDES = (
    "build.rustflags=[]",
    f"target.{TARGET}.rustflags=[]",
    "net.offline=true",
)


class BuildError(RuntimeError):
    pass


def _validate_toolchain_versions(rustc_version: str, cargo_version: str, rustfmt_version: str) -> None:
    if rustc_version != EXPECTED_RUSTC:
        raise BuildError(f"rustc version is not the exact reviewed release: {rustc_version}")
    if cargo_version != EXPECTED_CARGO:
        raise BuildError(f"cargo version is not the exact reviewed release: {cargo_version}")
    if rustfmt_version != EXPECTED_RUSTFMT:
        raise BuildError(f"rustfmt version is not the exact reviewed release: {rustfmt_version}")


def _regular_file(path: Path, *, executable: bool = False) -> None:
    try:
        info = path.lstat()
    except OSError as error:
        raise BuildError(f"required path is unavailable: {path}") from error
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise BuildError(f"path is not a regular file: {path}")
    if executable and not info.st_mode & 0o100:
        raise BuildError(f"published artifact is not executable: {path}")


def _private_regular(path: Path, *, executable: bool = False) -> None:
    _regular_file(path, executable=executable)
    try:
        info = path.lstat()
    except OSError as error:
        raise BuildError(f"required path is unavailable: {path}") from error
    if info.st_mode & 0o077:
        raise BuildError(f"path is not private: {path}")


def _private_directory(path: Path) -> None:
    try:
        info = path.lstat()
    except OSError as error:
        raise BuildError(f"private build cache is unavailable: {path}") from error
    if (
        not stat.S_ISDIR(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise BuildError(f"private build cache is not user-owned and private: {path}")


def _ensure_build_cache() -> Path:
    path = BUILD_CACHE_ROOT
    if path.exists() or path.is_symlink():
        _private_directory(path)
    else:
        try:
            path.mkdir(parents=True, mode=0o700)
        except OSError as error:
            raise BuildError(f"private build cache cannot be created: {path}") from error
        os.chmod(path, 0o700)
        _private_directory(path)
    return path


def _refuse_ancestor_build_inputs(path: Path) -> None:
    current = path.absolute()
    while True:
        cargo_toml = current / "Cargo.toml"
        if cargo_toml.exists() or cargo_toml.is_symlink():
            raise BuildError(f"refusing ancestor Cargo.toml: {cargo_toml}")
        for config_name in ("config", "config.toml"):
            cargo_config = current / ".cargo" / config_name
            if cargo_config.exists() or cargo_config.is_symlink():
                raise BuildError(f"refusing ancestor Cargo config: {cargo_config}")
        if current.parent == current:
            break
        current = current.parent


def _build_workspace() -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix="crowley-template-matcher-build-", dir=_ensure_build_cache())


def _sha256_bytes(data: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def _read_stable_file(path: Path) -> bytes:
    flags = os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise BuildError(f"source file is unavailable: {path}") from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise BuildError(f"source path is not a regular file: {path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
        data = b"".join(chunks)
        if identity_before != identity_after or len(data) != before.st_size:
            raise BuildError(f"source file changed during descriptor read: {path}")
        return data
    finally:
        os.close(descriptor)


def _read_source_files(source_root: Path = SOURCE_ROOT) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for name in SOURCE_FILES:
        result[name] = _read_stable_file(source_root / name)
    return result


def _source_hashes(source_files: dict[str, bytes]) -> dict[str, str]:
    if tuple(source_files) != SOURCE_FILES:
        raise BuildError("source snapshot file set is not canonical")
    return {name: _sha256_bytes(source_files[name]) for name in SOURCE_FILES}


def _combined_source_hash(source_hashes: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for name in SOURCE_FILES:
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(source_hashes[name].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _write_snapshot_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{path.name}.", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def _prepare_source_snapshot(source_root: Path, workspace: Path) -> tuple[Path, dict[str, bytes]]:
    before = _read_source_files(source_root)
    snapshot_root = workspace / "source"
    snapshot_root.mkdir(mode=0o700)
    (snapshot_root / "src").mkdir(mode=0o700)
    for name, data in before.items():
        _write_snapshot_file(snapshot_root / name, data)
    after = _read_source_files(source_root)
    if before != after:
        raise BuildError("source changed while creating the private snapshot")
    snapshotted = _read_source_files(snapshot_root)
    if before != snapshotted:
        raise BuildError("private source snapshot failed exact verification")
    return snapshot_root, before


def _command_output(command: list[str], *, cwd: Path, env: dict[str, str]) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        details = getattr(error, "stderr", "") or str(error)
        raise BuildError(f"command failed: {' '.join(command)}\n{details.strip()}") from error
    return result.stdout.strip()


def _resolve_binary(explicit: str | None, toolchain_dir: Path | None, name: str) -> Path:
    candidate = Path(explicit) if explicit else None
    if candidate is None and toolchain_dir is not None:
        candidate = toolchain_dir / name
    if candidate is None:
        found = shutil.which(name)
        if found is None:
            raise BuildError(f"cannot locate {name}; pass --{name}")
        candidate = Path(found)
    _regular_file(candidate, executable=True)
    return candidate.resolve()


def _ensure_output_dir(path: Path) -> None:
    if path.exists():
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise BuildError(f"output path is not a private directory: {path}")
        if info.st_mode & 0o077:
            raise BuildError(f"output directory is not private: {path}")
    else:
        path.mkdir(parents=True, mode=0o700)
    os.chmod(path, 0o700)


def _build(
    cargo: Path,
    rustc: Path,
    snapshot_root: Path,
    target_dir: Path,
    *,
    cwd: Path,
    base_env: dict[str, str],
) -> Path:
    source_path = str(snapshot_root)
    remap = f"--remap-path-prefix={source_path}=/rustsrc"
    flags = " ".join(
        (
            "-C debuginfo=0",
            "-C strip=symbols",
            "-C codegen-units=1",
            remap,
        )
    )
    env = dict(base_env)
    env.update(
        {
            "RUSTC": str(rustc),
            "CARGO_INCREMENTAL": "0",
            "CARGO_PROFILE_RELEASE_DEBUG": "0",
            "CARGO_PROFILE_RELEASE_STRIP": "symbols",
            "CARGO_PROFILE_RELEASE_CODEGEN_UNITS": "1",
            "CARGO_PROFILE_RELEASE_LTO": "false",
            "CARGO_PROFILE_RELEASE_PANIC": "unwind",
            "RUSTFLAGS": flags,
            "SOURCE_DATE_EPOCH": "0",
            "LC_ALL": "C",
            "CARGO_TARGET_DIR": str(target_dir),
        }
    )
    _command_output(
        [
            str(cargo),
            "build",
            *sum((["--config", value] for value in CARGO_CONFIG_OVERRIDES), []),
            "--release",
            "--locked",
            "--offline",
            "--verbose",
            "--target",
            TARGET,
            "--manifest-path",
            str(snapshot_root / "Cargo.toml"),
        ],
        cwd=cwd,
        env=env,
    )
    artifact = target_dir / TARGET / "release" / "template_matcher"
    _regular_file(artifact, executable=True)
    return artifact


def _build_environment(workspace: Path, cargo: Path, rustc: Path) -> tuple[Path, dict[str, str]]:
    neutral_cwd = workspace / "cwd"
    neutral_cwd.mkdir(mode=0o700)
    for name in ("cargo-home", "home", "rustup-home", "tmp", "xdg-config", "xdg-cache"):
        (workspace / name).mkdir(mode=0o700)
    environment = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(workspace / "home"),
        "CARGO_HOME": str(workspace / "cargo-home"),
        "RUSTUP_HOME": str(workspace / "rustup-home"),
        "TMPDIR": str(workspace / "tmp"),
        "XDG_CONFIG_HOME": str(workspace / "xdg-config"),
        "XDG_CACHE_HOME": str(workspace / "xdg-cache"),
        "RUSTC": str(rustc),
        "CARGO_INCREMENTAL": "0",
        "CARGO_PROFILE_RELEASE_DEBUG": "0",
        "CARGO_PROFILE_RELEASE_STRIP": "symbols",
        "CARGO_PROFILE_RELEASE_CODEGEN_UNITS": "1",
        "CARGO_PROFILE_RELEASE_LTO": "false",
        "CARGO_PROFILE_RELEASE_PANIC": "unwind",
        "CARGO_NET_OFFLINE": "true",
        "CARGO_BUILD_RUSTC_WRAPPER": "",
        "CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER": "",
        "CARGO_TERM_COLOR": "never",
        "RUSTFLAGS": "",
        "SOURCE_DATE_EPOCH": "0",
        "LC_ALL": "C",
    }
    if not cargo.is_absolute() or not rustc.is_absolute():
        raise BuildError("toolchain binaries must be absolute")
    return neutral_cwd, environment


def _expected_manifest(
    source_hashes: dict[str, str],
    artifact_sha256: str,
    rustc_version: str,
    cargo_version: str,
    rustfmt_version: str,
    rustc_verbose: str,
) -> dict[str, Any]:
    return {
        "schema": "crowley.template-matcher-release",
        "schema_version": 1,
        "artifact": ARTIFACT_NAME,
        "artifact_sha256": artifact_sha256,
        "source_hashes": source_hashes,
        "source_sha256": _combined_source_hash(source_hashes),
        "source_snapshot_sha256": _combined_source_hash(source_hashes),
        "protocol": PROTOCOL,
        "target": TARGET,
        "toolchain": {
            "rustc": rustc_version,
            "rustc_verbose": rustc_verbose,
            "cargo": cargo_version,
            "rustfmt": rustfmt_version,
        },
        "build": {
            "profile": "release",
            "locked": True,
            "offline": True,
            "incremental": False,
            "debuginfo": 0,
            "strip": "symbols",
            "codegen_units": 1,
            "target_cpu": None,
            "remap_path": "/rustsrc",
            "cargo_config_overrides": list(CARGO_CONFIG_OVERRIDES),
        },
    }


def _read_manifest(path: Path) -> dict[str, Any]:
    _private_regular(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BuildError(f"published manifest is malformed: {path}") from error
    if not isinstance(value, dict):
        raise BuildError("published manifest is not an object")
    return value


def _publish(
    output_dir: Path,
    artifact_bytes: bytes,
    manifest: dict[str, Any],
) -> tuple[Path, Path]:
    artifact = output_dir / ARTIFACT_NAME
    manifest_path = output_dir / MANIFEST_NAME
    existing = artifact.exists() or manifest_path.exists()
    if existing:
        if not artifact.exists() or not manifest_path.exists():
            raise BuildError("partial publication exists; refusing to overwrite it")
        _private_regular(artifact, executable=True)
        _private_regular(manifest_path)
        if artifact.read_bytes() != artifact_bytes:
            raise BuildError("existing artifact differs from independent rebuild")
        if _read_manifest(manifest_path) != manifest:
            raise BuildError("existing manifest differs from independent rebuild")
        return artifact, manifest_path

    artifact_tmp: Path | None = None
    manifest_tmp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{ARTIFACT_NAME}.", dir=output_dir, delete=False
        ) as stream:
            artifact_tmp = Path(stream.name)
            stream.write(artifact_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(artifact_tmp, 0o700)
        os.replace(artifact_tmp, artifact)
        artifact_tmp = None

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", prefix=f".{MANIFEST_NAME}.", dir=output_dir, delete=False
        ) as stream:
            manifest_tmp = Path(stream.name)
            json.dump(manifest, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(manifest_tmp, 0o600)
        os.replace(manifest_tmp, manifest_path)
        manifest_tmp = None
        directory_fd = os.open(output_dir, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        for temporary in (artifact_tmp, manifest_tmp):
            if temporary is not None:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass
    return artifact, manifest_path


def build(
    output_dir: Path, toolchain_dir: Path | None, rustc_arg: str | None, cargo_arg: str | None
) -> dict[str, Any]:
    _ensure_output_dir(output_dir)
    rustc = _resolve_binary(rustc_arg, toolchain_dir, "rustc")
    cargo = _resolve_binary(cargo_arg, toolchain_dir, "cargo")
    rustfmt = _resolve_binary(None, toolchain_dir, "rustfmt")

    with _build_workspace() as workspace_name:
        workspace = Path(workspace_name)
        os.chmod(workspace, 0o700)
        snapshot_root, source_files = _prepare_source_snapshot(SOURCE_ROOT, workspace)
        _refuse_ancestor_build_inputs(snapshot_root.parent)
        source_hashes = _source_hashes(source_files)
        neutral_cwd, build_environment = _build_environment(workspace, cargo, rustc)
        _refuse_ancestor_build_inputs(neutral_cwd)

        rustc_version = _command_output([str(rustc), "-V"], cwd=neutral_cwd, env=build_environment)
        rustc_verbose = _command_output([str(rustc), "-vV"], cwd=neutral_cwd, env=build_environment)
        cargo_version = _command_output([str(cargo), "-V"], cwd=neutral_cwd, env=build_environment)
        rustfmt_version = _command_output([str(rustfmt), "--version"], cwd=neutral_cwd, env=build_environment)
        _validate_toolchain_versions(rustc_version, cargo_version, rustfmt_version)

        binaries: list[Path] = []
        for index in (1, 2):
            target_dir = workspace / f"target-{index}"
            target_dir.mkdir(mode=0o700)
            build_environment["CARGO_TARGET_DIR"] = str(target_dir)
            binaries.append(
                _build(
                    cargo,
                    rustc,
                    snapshot_root,
                    target_dir,
                    cwd=neutral_cwd,
                    base_env=build_environment,
                )
            )
        first_bytes = binaries[0].read_bytes()
        second_bytes = binaries[1].read_bytes()
        if first_bytes != second_bytes:
            raise BuildError("independent release builds are not byte-identical")
        artifact_sha256 = hashlib.sha256(first_bytes).hexdigest()
        manifest = _expected_manifest(
            source_hashes,
            artifact_sha256,
            rustc_version,
            cargo_version,
            rustfmt_version,
            rustc_verbose,
        )
        artifact, manifest_path = _publish(output_dir, first_bytes, manifest)

    return {
        "artifact": str(artifact),
        "manifest": str(manifest_path),
        "artifact_sha256": artifact_sha256,
        "source_sha256": manifest["source_sha256"],
        "toolchain": manifest["toolchain"],
        "target": TARGET,
        "independent_builds": 2,
        "byte_identical": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--toolchain-dir", type=Path)
    parser.add_argument("--rustc")
    parser.add_argument("--cargo")
    args = parser.parse_args()
    try:
        result = build(args.output_dir.resolve(), args.toolchain_dir, args.rustc, args.cargo)
    except BuildError as error:
        print(f"build_template_matcher: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
