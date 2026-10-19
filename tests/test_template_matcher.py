"""Independent protocol and scoring checks for the native template matcher."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import random
import shutil
import stat
import struct
import subprocess
import sys
from pathlib import Path

import pytest

MAGIC = b"CRWTM001"
SEARCH = 1
SCORE_AT = 2
MAX_INPUT_BYTES = 64 * 1024 * 1024
PROJECT = Path(__file__).resolve().parents[1] / "native" / "template_matcher"
BUILDER = Path(__file__).resolve().parents[1] / "tools" / "build_template_matcher.py"
SOURCE_FILES = ("Cargo.toml", "Cargo.lock", "src/main.rs")
ARTIFACT_NAME = "template_matcher-v1"
MANIFEST_NAME = f"{ARTIFACT_NAME}.manifest.json"


def _source_pins() -> dict[str, str]:
    return {name: hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() for name in SOURCE_FILES}


def _combined_source_pin(source_hashes: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for name in SOURCE_FILES:
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(source_hashes[name].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _verify_configured_artifact(binary: Path) -> None:
    if binary.name != ARTIFACT_NAME:
        raise AssertionError("configured artifact name is not versioned")
    try:
        binary_info = binary.lstat()
        parent_info = binary.parent.lstat()
        manifest = binary.parent.joinpath(MANIFEST_NAME)
        manifest_info = manifest.lstat()
        raw_manifest = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AssertionError("configured artifact publication is unreadable") from error
    if (
        stat.S_ISLNK(binary_info.st_mode)
        or not stat.S_ISREG(binary_info.st_mode)
        or binary_info.st_mode & 0o077
        or not binary_info.st_mode & 0o100
        or stat.S_ISLNK(parent_info.st_mode)
        or not stat.S_ISDIR(parent_info.st_mode)
        or parent_info.st_mode & 0o077
        or stat.S_ISLNK(manifest_info.st_mode)
        or not stat.S_ISREG(manifest_info.st_mode)
        or manifest_info.st_mode & 0o077
    ):
        raise AssertionError("configured artifact publication is not private")
    if not isinstance(raw_manifest, dict):
        raise AssertionError("configured artifact manifest is malformed")
    source_hashes = _source_pins()
    expected_source = _combined_source_pin(source_hashes)
    if (
        raw_manifest.get("schema") != "crowley.template-matcher-release"
        or raw_manifest.get("schema_version") != 1
        or raw_manifest.get("artifact") != ARTIFACT_NAME
        or raw_manifest.get("source_hashes") != source_hashes
        or raw_manifest.get("source_sha256") != expected_source
        or raw_manifest.get("source_snapshot_sha256") != expected_source
        or raw_manifest.get("target") != "x86_64-unknown-linux-gnu"
    ):
        raise AssertionError("configured artifact source manifest is stale")
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    if raw_manifest.get("artifact_sha256") != digest:
        raise AssertionError("configured artifact digest does not match its manifest")


def _fresh_build_binary(project: Path, target_dir: Path) -> Path:
    cargo = os.environ.get("CARGO")
    if not cargo and os.environ.get("RUSTC"):
        sibling = Path(os.environ["RUSTC"]).with_name("cargo")
        if sibling.is_file():
            cargo = str(sibling)
    cargo = cargo or shutil.which("cargo")
    if cargo is None:
        pytest.fail("build the matcher or set CARGO")
    target_dir.mkdir(mode=0o700)
    environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "CARGO_TARGET_DIR": str(target_dir),
        "CARGO_HOME": str(target_dir / "cargo-home"),
        "CARGO_NET_OFFLINE": "true",
        "CARGO_INCREMENTAL": "0",
        "CARGO_TERM_COLOR": "never",
    }
    (target_dir / "cargo-home").mkdir(mode=0o700)
    if os.environ.get("RUSTC"):
        environment["RUSTC"] = os.environ["RUSTC"]
    result = subprocess.run(
        [
            cargo,
            "build",
            "--release",
            "--locked",
            "--offline",
            "--target",
            "x86_64-unknown-linux-gnu",
            "--manifest-path",
            str(project / "Cargo.toml"),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path("/"),
        env=environment,
    )
    if result.returncode != 0:
        pytest.fail(f"cargo build failed:\n{result.stdout}\n{result.stderr}")
    binary = target_dir / "x86_64-unknown-linux-gnu" / "release" / "template_matcher"
    if not binary.is_file():
        pytest.fail(f"cargo did not produce {binary}")
    return binary


@pytest.fixture(scope="session")
def matcher_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    configured = os.environ.get("CROWLEY_TEMPLATE_MATCHER_BIN")
    if configured:
        binary = Path(configured)
        try:
            _verify_configured_artifact(binary)
        except AssertionError as error:
            pytest.fail(f"CROWLEY_TEMPLATE_MATCHER_BIN publication refused: {error}")
        return binary
    return _fresh_build_binary(PROJECT, tmp_path_factory.mktemp("matcher-build"))


def make_request(
    operation: int,
    frame_width: int,
    frame_height: int,
    template_width: int,
    template_height: int,
    region: tuple[int, int, int, int],
    frame: bytes,
    template: bytes,
    *,
    reserved: int = 0,
    magic: bytes = MAGIC,
) -> bytes:
    return (
        struct.pack(
            "<8s10I",
            magic,
            operation,
            reserved,
            frame_width,
            frame_height,
            template_width,
            template_height,
            *region,
        )
        + frame
        + template
    )


def invoke(binary: Path, payload: bytes) -> dict[str, object]:
    result = subprocess.run(
        [str(binary)],
        input=payload,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert result.stderr == b""
    assert result.stdout.endswith(b"\n")
    return json.loads(result.stdout)


def invoke_error(binary: Path, payload: bytes, expected: str) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        [str(binary)],
        input=payload,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert result.returncode != 0
    assert result.stdout == b""
    assert result.stderr == f"template_matcher: {expected}\n".encode()
    return result


def reference(
    frame_width: int,
    frame_height: int,
    template_width: int,
    template_height: int,
    region: tuple[int, int, int, int],
    frame: bytes,
    template: bytes,
    *,
    operation: int = SEARCH,
) -> dict[str, object]:
    region_x, region_y, region_width, region_height = region
    count = len(template)

    def sad_at(x: int, y: int) -> int:
        total = 0
        for row in range(template_height):
            frame_start = ((y + row) * frame_width + x) * 3
            template_start = row * template_width * 3
            for offset in range(template_width * 3):
                total += abs(frame[frame_start + offset] - template[template_start + offset])
        return total

    if operation == SCORE_AT:
        x, y = region_x, region_y
        sad = sad_at(x, y)
        status = "matched" if sad <= 5 * count else "rejected"
        return {"status": status, "sad": sad, "count": count, "box": [x, y, template_width, template_height]}

    candidates = [
        (sad_at(x, y), x, y)
        for y in range(region_y, region_y + region_height - template_height + 1)
        for x in range(region_x, region_x + region_width - template_width + 1)
    ]
    best = min(candidates)
    accepted = [candidate for candidate in candidates if candidate[0] <= 5 * count]
    _, x, y = best

    def intersects(other_x: int, other_y: int) -> bool:
        return (
            x < other_x + template_width
            and other_x < x + template_width
            and y < other_y + template_height
            and other_y < y + template_height
        )

    ambiguous = any(
        (other_x, other_y) != (x, y) and not intersects(other_x, other_y) for _, other_x, other_y in accepted
    )
    status = "ambiguous" if ambiguous else "matched" if best[0] <= 5 * count else "rejected"
    return {
        "status": status,
        "sad": best[0],
        "count": count,
        "box": [x, y, template_width, template_height],
    }


def rgb_frame(width: int, height: int, value: int) -> bytes:
    return bytes([value]) * (width * height * 3)


def replace_rgb_pixel(image: bytearray, width: int, x: int, y: int, rgb: tuple[int, int, int]) -> None:
    start = (y * width + x) * 3
    image[start : start + 3] = bytes(rgb)


def test_exact_edge_match_and_reference_parity(matcher_binary: Path) -> None:
    frame_width, frame_height = 6, 5
    template_width, template_height = 2, 2
    template = bytes((10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120))
    frame = bytearray(rgb_frame(frame_width, frame_height, 255))
    for row in range(template_height):
        for column in range(template_width):
            start = (row * template_width + column) * 3
            replace_rgb_pixel(
                frame,
                frame_width,
                4 + column,
                3 + row,
                tuple(template[start : start + 3]),
            )
    payload = make_request(
        SEARCH,
        frame_width,
        frame_height,
        template_width,
        template_height,
        (2, 1, 4, 4),
        bytes(frame),
        template,
    )
    expected = reference(
        frame_width,
        frame_height,
        template_width,
        template_height,
        (2, 1, 4, 4),
        bytes(frame),
        template,
    )
    assert invoke(matcher_binary, payload) == expected
    assert expected["box"] == [4, 3, 2, 2]


def test_best_tie_uses_x_then_y_and_reports_disjoint_ambiguity(matcher_binary: Path) -> None:
    frame_width, frame_height = 6, 3
    template_width, template_height = 2, 2
    frame = bytearray(rgb_frame(frame_width, frame_height, 255))
    template = bytes(12)
    for origin_x, origin_y in ((0, 0), (4, 1)):
        for row in range(template_height):
            for column in range(template_width):
                replace_rgb_pixel(frame, frame_width, origin_x + column, origin_y + row, (0, 0, 0))
    payload = make_request(
        SEARCH,
        frame_width,
        frame_height,
        template_width,
        template_height,
        (0, 0, frame_width, frame_height),
        bytes(frame),
        template,
    )
    result = invoke(matcher_binary, payload)
    assert result == reference(
        frame_width,
        frame_height,
        template_width,
        template_height,
        (0, 0, frame_width, frame_height),
        bytes(frame),
        template,
    )
    assert result["status"] == "ambiguous"
    assert result["box"] == [0, 0, 2, 2]


def test_equal_sad_tie_prioritizes_x_before_y(matcher_binary: Path) -> None:
    frame = bytearray(rgb_frame(3, 3, 255))
    template = bytes(3)
    replace_rgb_pixel(frame, 3, 1, 0, (0, 0, 0))
    replace_rgb_pixel(frame, 3, 0, 1, (0, 0, 0))
    payload = make_request(SEARCH, 3, 3, 1, 1, (0, 0, 3, 3), bytes(frame), template)
    result = invoke(matcher_binary, payload)
    assert result["sad"] == 0
    assert result["box"] == [0, 1, 1, 1]
    assert result["status"] == "ambiguous"


def test_ambiguity_uses_best_box_with_overlapping_second_and_disjoint_later(
    matcher_binary: Path,
) -> None:
    frame = bytearray(rgb_frame(6, 2, 255))
    template = bytes(12)
    for origin_x in (0, 1, 4):
        for row in range(2):
            for column in range(2):
                replace_rgb_pixel(frame, 6, origin_x + column, row, (0, 0, 0))
    payload = make_request(SEARCH, 6, 2, 2, 2, (0, 0, 6, 2), bytes(frame), template)
    result = invoke(matcher_binary, payload)
    assert result == {
        "status": "ambiguous",
        "sad": 0,
        "count": 12,
        "box": [0, 0, 2, 2],
    }


def test_overlapping_acceptable_candidates_are_not_ambiguous(matcher_binary: Path) -> None:
    frame = rgb_frame(3, 2, 0)
    template = rgb_frame(2, 2, 0)
    payload = make_request(SEARCH, 3, 2, 2, 2, (0, 0, 3, 2), frame, template)
    assert invoke(matcher_binary, payload) == {
        "status": "matched",
        "sad": 0,
        "count": 12,
        "box": [0, 0, 2, 2],
    }


@pytest.mark.parametrize(
    ("pixel", "status", "sad"),
    [((5, 5, 5), "matched", 15), ((5, 5, 6), "rejected", 16)],
)
def test_integer_threshold_boundary(
    matcher_binary: Path, pixel: tuple[int, int, int], status: str, sad: int
) -> None:
    payload = make_request(SCORE_AT, 1, 1, 1, 1, (0, 0, 1, 1), bytes(pixel), bytes(3))
    assert invoke(matcher_binary, payload) == {
        "status": status,
        "sad": sad,
        "count": 3,
        "box": [0, 0, 1, 1],
    }


def test_score_at_is_exact_candidate_and_absent_search_is_rejected(matcher_binary: Path) -> None:
    frame = rgb_frame(5, 4, 255)
    template = rgb_frame(2, 2, 0)
    score_at = make_request(SCORE_AT, 5, 4, 2, 2, (3, 2, 2, 2), frame, template)
    assert invoke(matcher_binary, score_at) == {
        "status": "rejected",
        "sad": 3060,
        "count": 12,
        "box": [3, 2, 2, 2],
    }

    search = make_request(SEARCH, 5, 4, 2, 2, (0, 0, 5, 4), frame, template)
    assert invoke(matcher_binary, search) == reference(5, 4, 2, 2, (0, 0, 5, 4), frame, template)


def test_seeded_differential_reference_corpus(matcher_binary: Path) -> None:
    generator = random.Random(20261019)
    for _ in range(24):
        frame_width = generator.randint(2, 8)
        frame_height = generator.randint(2, 8)
        template_width = generator.randint(1, frame_width)
        template_height = generator.randint(1, frame_height)
        region_x = generator.randint(0, frame_width - template_width)
        region_y = generator.randint(0, frame_height - template_height)
        region_width = generator.randint(template_width, frame_width - region_x)
        region_height = generator.randint(template_height, frame_height - region_y)
        frame = bytes(generator.randrange(256) for _ in range(frame_width * frame_height * 3))
        template = bytes(generator.randrange(256) for _ in range(template_width * template_height * 3))
        region = (region_x, region_y, region_width, region_height)
        payload = make_request(
            SEARCH,
            frame_width,
            frame_height,
            template_width,
            template_height,
            region,
            frame,
            template,
        )
        assert invoke(matcher_binary, payload) == reference(
            frame_width,
            frame_height,
            template_width,
            template_height,
            region,
            frame,
            template,
        )


def test_actual_shape_seeded_frame_parity(matcher_binary: Path) -> None:
    frame_width, frame_height = 220, 84
    template_width, template_height = 98, 27
    generator = random.Random(98127)
    frame = bytearray(generator.randrange(256) for _ in range(frame_width * frame_height * 3))
    template = bytes(generator.randrange(256) for _ in range(template_width * template_height * 3))
    origin_x, origin_y = 112, 41
    for row in range(template_height):
        start = row * template_width * 3
        frame_start = ((origin_y + row) * frame_width + origin_x) * 3
        frame[frame_start : frame_start + template_width * 3] = template[start : start + template_width * 3]
    region = (0, 0, frame_width, frame_height)
    payload = make_request(
        SEARCH,
        frame_width,
        frame_height,
        template_width,
        template_height,
        region,
        bytes(frame),
        template,
    )
    assert invoke(matcher_binary, payload) == reference(
        frame_width,
        frame_height,
        template_width,
        template_height,
        region,
        bytes(frame),
        template,
    )


def test_malformed_header_payloads_are_refused(matcher_binary: Path) -> None:
    valid = make_request(SEARCH, 2, 2, 1, 1, (0, 0, 2, 2), rgb_frame(2, 2, 0), bytes(3))
    invoke_error(matcher_binary, b"", "input is shorter than the 48-byte header")
    invoke_error(matcher_binary, valid[:47], "input is shorter than the 48-byte header")
    invoke_error(matcher_binary, valid[:-1], "input is truncated")
    invoke_error(matcher_binary, valid + b"x", "input has trailing bytes")
    invoke_error(
        matcher_binary,
        make_request(99, 2, 2, 1, 1, (0, 0, 2, 2), b"", b""),
        "operation is unknown",
    )
    invoke_error(
        matcher_binary,
        make_request(SEARCH, 2, 2, 1, 1, (0, 0, 2, 2), b"", b"", reserved=1),
        "reserved header field is nonzero",
    )
    invoke_error(
        matcher_binary,
        make_request(SEARCH, 2, 2, 1, 1, (0, 0, 2, 2), b"", b"", magic=b"BADMAGIC"),
        "protocol magic is invalid",
    )


@pytest.mark.parametrize(
    "payload,expected",
    [
        (
            make_request(SEARCH, 0, 2, 1, 1, (0, 0, 1, 1), b"", b""),
            "frame dimensions are outside the fixed bounds",
        ),
        (
            make_request(SEARCH, 2, 0, 1, 1, (0, 0, 1, 1), b"", b""),
            "frame dimensions are outside the fixed bounds",
        ),
        (
            make_request(SEARCH, 4097, 1, 1, 1, (0, 0, 1, 1), b"", b""),
            "frame dimensions are outside the fixed bounds",
        ),
        (
            make_request(SEARCH, 2, 2, 0, 1, (0, 0, 1, 1), b"", b""),
            "template dimensions are outside the fixed bounds",
        ),
        (
            make_request(SEARCH, 2, 2, 513, 1, (0, 0, 1, 1), b"", b""),
            "template dimensions are outside the fixed bounds",
        ),
        (
            make_request(SEARCH, 2, 2, 1, 1, (0, 0, 0, 1), b"", b""),
            "search region dimensions must be positive",
        ),
        (make_request(SEARCH, 2, 2, 1, 1, (2, 0, 1, 1), b"", b""), "search region is outside the frame"),
        (
            make_request(SEARCH, 2, 2, 1, 1, (0xFFFFFFFF, 0, 1, 1), b"", b""),
            "search region is outside the frame",
        ),
        (
            make_request(SEARCH, 2, 2, 2, 2, (0, 0, 1, 1), b"", b""),
            "template is larger than the search region",
        ),
        (
            make_request(SCORE_AT, 2, 2, 1, 1, (0, 0, 2, 1), b"", b""),
            "SCORE_AT region must equal template dimensions",
        ),
        (
            make_request(SEARCH, 4096, 4096, 512, 512, (0, 0, 4096, 4096), b"", b""),
            "comparison byte count exceeds 2^31",
        ),
    ],
)
def test_dimensions_bounds_and_comparison_cap_are_refused(
    matcher_binary: Path, payload: bytes, expected: str
) -> None:
    invoke_error(matcher_binary, payload, expected)


def test_oversized_input_is_refused_before_protocol_work(matcher_binary: Path) -> None:
    invoke_error(matcher_binary, b"x" * (MAX_INPUT_BYTES + 1), "input exceeds 64 MiB")


def test_configured_artifact_requires_private_current_manifest_and_digest(tmp_path: Path) -> None:
    publication = tmp_path / "publication"
    publication.mkdir(mode=0o700)
    binary = publication / ARTIFACT_NAME
    binary.write_bytes(b"reviewed-artifact")
    binary.chmod(0o700)
    source_hashes = _source_pins()
    source_pin = _combined_source_pin(source_hashes)
    manifest = {
        "schema": "crowley.template-matcher-release",
        "schema_version": 1,
        "artifact": ARTIFACT_NAME,
        "artifact_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "source_hashes": source_hashes,
        "source_sha256": source_pin,
        "source_snapshot_sha256": source_pin,
        "target": "x86_64-unknown-linux-gnu",
    }
    manifest_path = publication / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    manifest_path.chmod(0o600)
    _verify_configured_artifact(binary)

    binary.write_bytes(b"tampered-artifact")
    binary.chmod(0o700)
    with pytest.raises(AssertionError, match="digest"):
        _verify_configured_artifact(binary)

    binary.write_bytes(b"reviewed-artifact")
    binary.chmod(0o700)
    manifest["source_hashes"]["Cargo.toml"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    manifest_path.chmod(0o600)
    with pytest.raises(AssertionError, match="stale"):
        _verify_configured_artifact(binary)


def test_default_build_ignores_stale_repository_target(tmp_path: Path) -> None:
    project = tmp_path / "template-matcher"
    shutil.copytree(PROJECT, project)
    stale = project / "target" / "x86_64-unknown-linux-gnu" / "release"
    stale.mkdir(parents=True, mode=0o700)
    stale_binary = stale / "template_matcher"
    stale_binary.write_bytes(b"stale")
    stale_binary.chmod(0o700)
    fresh = _fresh_build_binary(project, tmp_path / "fresh-target")
    assert fresh.read_bytes() != b"stale"


def test_builder_ignores_contaminated_cargo_configuration_and_wrappers(tmp_path: Path) -> None:
    cargo = os.environ.get("CARGO")
    if not cargo and os.environ.get("RUSTC"):
        sibling = Path(os.environ["RUSTC"]).with_name("cargo")
        if sibling.is_file():
            cargo = str(sibling)
    toolchain_dir = Path(cargo).parent if cargo and Path(cargo).is_absolute() else None
    if toolchain_dir is None or not (toolchain_dir / "rustc").is_file():
        pytest.skip("scoped test requires the pinned explicit toolchain")
    marker = tmp_path / "wrapper-used"
    wrapper = tmp_path / "wrapper"
    wrapper.write_text(f"#!/bin/sh\nprintf used > {marker}\nexit 91\n", encoding="utf-8")
    wrapper.chmod(0o700)
    contaminated_home = tmp_path / "contaminated-cargo-home"
    (contaminated_home / ".cargo").mkdir(parents=True, mode=0o700)
    (contaminated_home / ".cargo" / "config.toml").write_text(
        f"[build]\nrustc-wrapper = {json.dumps(str(wrapper))}\n", encoding="utf-8"
    )
    contaminated_tmp = tmp_path / "contaminated-tmp"
    (contaminated_tmp / ".cargo").mkdir(parents=True, mode=0o700)
    (contaminated_tmp / ".cargo" / "config.toml").write_text(
        "[build]\n"
        f"rustc-wrapper = {json.dumps(str(wrapper))}\n"
        "[target.x86_64-unknown-linux-gnu]\n"
        f"linker = {json.dumps(str(wrapper))}\n"
        "[profile.release]\nopt-level = 0\n",
        encoding="utf-8",
    )
    output = tmp_path / "publication"
    output.mkdir(mode=0o700)
    command = [
        sys.executable,
        str(BUILDER),
        "--output-dir",
        str(output),
        "--toolchain-dir",
        str(toolchain_dir),
    ]
    clean_environment = {
        **os.environ,
        "CARGO_HOME": str(tmp_path / "clean-cargo-home"),
        "TMPDIR": str(tmp_path / "clean-tmp"),
        "RUSTFLAGS": "",
        "CARGO_ENCODED_RUSTFLAGS": "",
    }
    for name in ("RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "CARGO_BUILD_RUSTC_WRAPPER"):
        clean_environment.pop(name, None)
    clean_result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        cwd=Path("/"),
        env=clean_environment,
    )
    assert clean_result.returncode == 0, f"{clean_result.stdout}\n{clean_result.stderr}"
    clean_binary = (output / ARTIFACT_NAME).read_bytes()
    clean_manifest = (output / MANIFEST_NAME).read_bytes()
    environment = {
        **os.environ,
        "CARGO_HOME": str(contaminated_home),
        "TMPDIR": str(contaminated_tmp),
        "RUSTC_WRAPPER": str(wrapper),
        "RUSTC_WORKSPACE_WRAPPER": str(wrapper),
        "CARGO_BUILD_RUSTC_WRAPPER": str(wrapper),
        "CARGO_ENCODED_RUSTFLAGS": "-C\x1fpanic=abort",
        "RUSTFLAGS": "-C panic=abort",
    }
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        cwd=Path("/"),
        env=environment,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    assert not marker.exists()
    assert (output / MANIFEST_NAME).is_file()
    assert (output / ARTIFACT_NAME).read_bytes() == clean_binary
    assert (output / MANIFEST_NAME).read_bytes() == clean_manifest


@pytest.mark.parametrize("poison", ["Cargo.toml", ".cargo/config.toml"])
def test_builder_refuses_ancestor_cargo_inputs_before_execution(
    tmp_path: Path, monkeypatch, poison: str
) -> None:
    spec = importlib.util.spec_from_file_location("template_matcher_builder_ancestor", BUILDER)
    assert spec and spec.loader
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    cargo = os.environ.get("CARGO")
    if not cargo and os.environ.get("RUSTC"):
        sibling = Path(os.environ["RUSTC"]).with_name("cargo")
        if sibling.is_file():
            cargo = str(sibling)
    if not cargo or not Path(cargo).is_absolute():
        pytest.skip("scoped test requires the pinned explicit toolchain")
    toolchain_dir = Path(cargo).parent
    cache = tmp_path / "build-cache"
    cache.mkdir(mode=0o700)
    marker = tmp_path / "linker-executed"
    linker = tmp_path / "linker"
    linker.write_text(f"#!/bin/sh\nprintf executed > {marker}\nexit 91\n", encoding="utf-8")
    linker.chmod(0o700)
    if poison == "Cargo.toml":
        (cache / poison).write_text("[workspace]\nmembers = []\n", encoding="utf-8")
    else:
        (cache / ".cargo").mkdir(mode=0o700)
        (cache / poison).write_text(
            "[target.x86_64-unknown-linux-gnu]\n"
            f"linker = {json.dumps(str(linker))}\n"
            "[profile.release]\nopt-level = 0\n",
            encoding="utf-8",
        )
    output = tmp_path / "publication"
    output.mkdir(mode=0o700)
    monkeypatch.setattr(builder, "BUILD_CACHE_ROOT", cache)
    with pytest.raises(builder.BuildError, match="refusing ancestor"):
        builder.build(output, toolchain_dir, None, None)
    assert not marker.exists()


def test_source_snapshot_rejects_mutation_between_descriptor_snapshots(tmp_path: Path, monkeypatch) -> None:
    spec = importlib.util.spec_from_file_location("template_matcher_builder", BUILDER)
    assert spec and spec.loader
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    source = tmp_path / "source"
    shutil.copytree(PROJECT, source)
    workspace = tmp_path / "workspace"
    workspace.mkdir(mode=0o700)
    original = builder._read_source_files
    calls = 0

    def mutate_after_first_read(root: Path) -> dict[str, bytes]:
        nonlocal calls
        snapshot = original(root)
        calls += 1
        if calls == 1:
            path = source / "src" / "main.rs"
            path.write_bytes(path.read_bytes() + b"\n")
        return snapshot

    monkeypatch.setattr(builder, "_read_source_files", mutate_after_first_read)
    with pytest.raises(builder.BuildError, match="changed"):
        builder._prepare_source_snapshot(source, workspace)


def test_builder_requires_exact_official_toolchain_versions() -> None:
    spec = importlib.util.spec_from_file_location("template_matcher_builder_versions", BUILDER)
    assert spec and spec.loader
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    builder._validate_toolchain_versions(
        builder.EXPECTED_RUSTC,
        builder.EXPECTED_CARGO,
        builder.EXPECTED_RUSTFMT,
    )
    rejected = (
        ("rustc 1.85.2 (4eb161250 2025-03-15)", builder.EXPECTED_CARGO, builder.EXPECTED_RUSTFMT),
        (builder.EXPECTED_RUSTC + " suffix", builder.EXPECTED_CARGO, builder.EXPECTED_RUSTFMT),
        (builder.EXPECTED_RUSTC, "cargo 1.85.2 (d73d2caf9 2024-12-31)", builder.EXPECTED_RUSTFMT),
        (builder.EXPECTED_RUSTC, builder.EXPECTED_CARGO + " suffix", builder.EXPECTED_RUSTFMT),
        (builder.EXPECTED_RUSTC, builder.EXPECTED_CARGO, "rustfmt 1.8.1-stable (4eb161250e 2025-03-15)"),
        (builder.EXPECTED_RUSTC, builder.EXPECTED_CARGO, builder.EXPECTED_RUSTFMT + " suffix"),
    )
    for versions in rejected:
        with pytest.raises(builder.BuildError):
            builder._validate_toolchain_versions(*versions)


def test_public_benchmark_normalizes_relative_binary_and_rejects_symlink(tmp_path: Path, monkeypatch) -> None:
    benchmark_path = Path(__file__).resolve().parents[1] / "tools" / "benchmark_template_matcher.py"
    spec = importlib.util.spec_from_file_location("template_matcher_benchmark", benchmark_path)
    assert spec and spec.loader
    benchmark = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(benchmark)
    configured = os.environ.get("CROWLEY_TEMPLATE_MATCHER_BIN")
    if not configured:
        pytest.fail("CROWLEY_TEMPLATE_MATCHER_BIN must point to the retained private release")
    source_binary = Path(configured)
    source_manifest = source_binary.parent / MANIFEST_NAME
    publication = tmp_path / "release"
    publication.mkdir(mode=0o700)
    shutil.copy2(source_binary, publication / ARTIFACT_NAME)
    shutil.copy2(source_manifest, publication / MANIFEST_NAME)
    (publication / ARTIFACT_NAME).chmod(0o700)
    (publication / MANIFEST_NAME).chmod(0o600)
    monkeypatch.chdir(tmp_path)
    _source_hashes, _source_pin, digest = benchmark._source_binding(PROJECT, Path("release") / ARTIFACT_NAME)
    assert digest == hashlib.sha256((publication / ARTIFACT_NAME).read_bytes()).hexdigest()

    symlink_dir = tmp_path / "symlink-release"
    symlink_dir.mkdir(mode=0o700)
    (symlink_dir / ARTIFACT_NAME).symlink_to(publication / ARTIFACT_NAME)
    shutil.copy2(publication / MANIFEST_NAME, symlink_dir / MANIFEST_NAME)
    (symlink_dir / MANIFEST_NAME).chmod(0o600)
    with pytest.raises(benchmark.BenchmarkError, match="regular file"):
        benchmark._source_binding(PROJECT, symlink_dir / ARTIFACT_NAME)
