import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from crowley.session.executor import DemonstrationRole, MotionProfile
from crowley.session.preferences import (
    MAX_DEMONSTRATIONS,
    MAX_INLINE_JSON_BYTES,
    MAX_PROFILE_DOCUMENT_BYTES,
    PreferenceError,
    load_motion_profile,
    save_motion_profile,
)

FIELDS = {
    "role": "pointer",
    "distance": 240.0,
    "duration": 0.8,
    "target_width": 24.0,
    "dwell": 0.12,
    "curvature": 0.06,
}


def _demonstration_json(*, role: str = "pointer", **changes: object) -> str:
    value = {**FIELDS, "role": role, **changes}
    return json.dumps([value], separators=(",", ":"))


def _cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(root / "src")
    return subprocess.run(
        [sys.executable, "-m", "crowley.session.cli", *arguments],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_real_cli_build_show_reset_is_daemon_and_config_independent(tmp_path: Path) -> None:
    profile_path = tmp_path / "prefs" / "camera.json"
    built = _cli(
        "motion-profile",
        "build",
        "--demonstrations",
        _demonstration_json(role="camera"),
        "--output",
        str(profile_path),
    )
    assert built.returncode == 0, built.stderr
    document = json.loads(built.stdout)
    assert document["schemaVersion"] == 2
    assert document["role"] == "camera"
    assert document["demonstrationCount"] == 1
    assert set(document) == {"schemaVersion", "role", "demonstrationCount", "profile"}
    assert stat.S_IMODE(profile_path.stat().st_mode) == 0o600
    assert "demonstrations" not in profile_path.read_text()

    shown = _cli("motion-profile", "show", "--profile", str(profile_path))
    assert shown.returncode == 0, shown.stderr
    assert json.loads(shown.stdout) == document

    reset = _cli("motion-profile", "reset", "--profile", str(profile_path))
    assert reset.returncode == 0, reset.stderr
    assert not profile_path.exists()


@pytest.mark.parametrize("role", list(DemonstrationRole))
def test_roundtrip_preserves_each_closed_role(tmp_path: Path, role: DemonstrationRole) -> None:
    path = tmp_path / f"{role.value}.json"
    original = MotionProfile(role=role, preferred_speed=321.5, curvature=-0.12)
    save_motion_profile(path, original, demonstration_count=4)
    assert load_motion_profile(path) == original
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_save_replaces_existing_file_atomically_and_restores_private_mode(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"
    save_motion_profile(path, MotionProfile(), demonstration_count=1)
    path.chmod(0o644)
    with pytest.raises(PreferenceError, match="permissions"):
        save_motion_profile(path, MotionProfile(preferred_speed=1200), demonstration_count=2)
    path.chmod(0o600)
    save_motion_profile(path, MotionProfile(preferred_speed=1200), demonstration_count=2)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert load_motion_profile(path).preferred_speed == 1200
    assert not list(tmp_path.glob(f".{path.name}.*"))


def test_save_validates_complete_document_before_replacing_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"
    save_motion_profile(path, MotionProfile(), demonstration_count=1)
    original = path.read_bytes()
    learned = MotionProfile(preferred_speed=1200)

    with pytest.raises(PreferenceError, match="non-baseline profile"):
        save_motion_profile(path, learned)
    assert path.read_bytes() == original

    save_motion_profile(path, learned, demonstration_count=1)
    assert load_motion_profile(path) == learned


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value.update(extra=True), "unknown"),
        (lambda value: value.pop("role"), "missing"),
        (lambda value: value["profile"].update(extra=1), "unknown"),
        (lambda value: value["profile"].pop("sampleHz"), "missing"),
        (lambda value: value.update(schemaVersion=1), "unsupported"),
        (lambda value: value.update(role="unknown"), "supported"),
        (lambda value: value["profile"].update(preferredSpeed=0), "bounds"),
        (lambda value: value.update(demonstrationCount=MAX_DEMONSTRATIONS + 1), "must be in"),
    ],
)
def test_load_rejects_unknown_missing_and_out_of_bound_schema(tmp_path: Path, mutation, message: str) -> None:
    path = tmp_path / "invalid.json"
    save_motion_profile(path, MotionProfile(), demonstration_count=1)
    document = json.loads(path.read_text())
    mutation(document)
    path.write_text(json.dumps(document))
    path.chmod(0o600)
    with pytest.raises(PreferenceError, match=message):
        load_motion_profile(path)


def test_load_rejects_malformed_duplicate_and_non_private_files(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"
    path.write_text('{"schemaVersion": 1, "schemaVersion": 1}')
    path.chmod(0o600)
    with pytest.raises(PreferenceError, match="duplicate"):
        load_motion_profile(path)
    path.write_text("not-json")
    with pytest.raises(PreferenceError, match="valid UTF-8 JSON"):
        load_motion_profile(path)
    path.unlink()
    save_motion_profile(path, MotionProfile())
    path.chmod(0o644)
    with pytest.raises(PreferenceError, match="0600"):
        load_motion_profile(path)


def test_load_rejects_oversized_profile_before_unbounded_read(tmp_path: Path) -> None:
    path = tmp_path / "large.json"
    path.write_bytes(b"{" + b" " * MAX_PROFILE_DOCUMENT_BYTES)
    path.chmod(0o600)
    with pytest.raises(PreferenceError, match="maximum size"):
        load_motion_profile(path)


def test_large_integer_overflow_is_a_preference_error(tmp_path: Path) -> None:
    path = tmp_path / "overflow.json"
    document = {
        "schemaVersion": 2,
        "role": "pointer",
        "demonstrationCount": 1,
        "profile": {
            "preferredSpeed": int("9" * 1001),
            "minDuration": 0.08,
            "maxDuration": 2.0,
            "sampleHz": 60.0,
            "curvature": 0.08,
            "minDwell": 0.05,
            "maxDwell": 0.35,
            "durationIntercept": 0.25,
            "durationSlope": 0.095,
        },
    }
    path.write_text(json.dumps(document))
    path.chmod(0o600)
    with pytest.raises(PreferenceError, match="finite numeric bounds"):
        load_motion_profile(path)


def test_json_digit_limit_is_a_preference_error_for_load_and_cli(tmp_path: Path) -> None:
    digits = "9" * 4301
    path = tmp_path / "digit-limit.json"
    path.write_text(
        '{"schemaVersion":1,"role":"pointer","demonstrationCount":1,"profile":'
        f'{{"preferredSpeed":{digits},"minDuration":0.08,"maxDuration":2.0,'
        '"sampleHz":60.0,"curvature":0.08,"minDwell":0.05,"maxDwell":0.35,'
        '"durationIntercept":0.25,"durationSlope":0.095}}}'
    )
    path.chmod(0o600)
    with pytest.raises(PreferenceError, match="valid UTF-8 JSON"):
        load_motion_profile(path)

    demonstrations = (
        f'{{"role":"pointer","distance":{digits},"duration":0.8,'
        '"target_width":24.0,"dwell":0.12,"curvature":0.06}'
    )
    demonstrations = f"[{demonstrations}]"
    result = _cli(
        "motion-profile",
        "build",
        "--demonstrations",
        demonstrations,
        "--output",
        str(tmp_path / "cli-digit-limit.json"),
    )
    assert result.returncode == 1
    assert "valid JSON" in result.stderr


def test_save_propagates_directory_fsync_open_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import crowley.session.preferences as preferences

    original_open = preferences.os.open

    def failing_open(path, flags, *arguments):
        if Path(path) == tmp_path:
            raise OSError("directory fsync open failed")
        return original_open(path, flags, *arguments)

    monkeypatch.setattr(preferences.os, "open", failing_open)
    with pytest.raises(OSError, match="directory fsync open failed"):
        save_motion_profile(tmp_path / "profile.json", MotionProfile())


def test_cli_rejects_invalid_selected_profile_and_invalid_demonstrations(tmp_path: Path) -> None:
    missing = _cli("motion-profile", "show", "--profile", str(tmp_path / "missing.json"))
    assert missing.returncode == 1
    assert "No such file" in missing.stderr

    malformed = _cli(
        "motion-profile",
        "build",
        "--demonstrations",
        json.dumps([{**FIELDS, "unknown": 1}]),
        "--output",
        str(tmp_path / "bad.json"),
    )
    assert malformed.returncode == 1
    assert "unknown" in malformed.stderr

    mixed = _cli(
        "motion-profile",
        "build",
        "--demonstrations",
        json.dumps([FIELDS, {**FIELDS, "role": "camera"}]),
        "--output",
        str(tmp_path / "mixed.json"),
    )
    assert mixed.returncode == 1
    assert "one motion role" in mixed.stderr


def test_cli_rejects_oversized_and_overflow_demonstration_json(tmp_path: Path) -> None:
    oversized = _cli(
        "motion-profile",
        "build",
        "--demonstrations",
        " " * (MAX_INLINE_JSON_BYTES + 1),
        "--output",
        str(tmp_path / "oversized.json"),
    )
    assert oversized.returncode == 1
    assert "maximum JSON size" in oversized.stderr

    overflow = _cli(
        "motion-profile",
        "build",
        "--demonstrations",
        json.dumps([{**FIELDS, "distance": int("9" * 1001)}]),
        "--output",
        str(tmp_path / "overflow.json"),
    )
    assert overflow.returncode == 1
    assert "outside its bounds" in overflow.stderr
