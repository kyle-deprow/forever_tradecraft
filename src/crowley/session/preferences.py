"""Bounded, explicit motion-profile preferences.

Profiles are imported from deliberate numeric demonstration summaries.  This
module only persists the aggregate profile and its count; it never records
desktop input, raw events, or free-form user text.
"""

from __future__ import annotations

import json
import math
import os
import stat
import tempfile
from pathlib import Path
from typing import Any

from .executor import DemonstrationRole, MotionProfile

SCHEMA_VERSION = 2
MAX_DEMONSTRATIONS = 256
MAX_PROFILE_DOCUMENT_BYTES = 16 * 1024
MAX_INLINE_JSON_BYTES = 64 * 1024

_TOP_LEVEL_FIELDS = frozenset({"schemaVersion", "role", "demonstrationCount", "profile"})
_PROFILE_FIELDS = frozenset(
    {
        "preferredSpeed",
        "minDuration",
        "maxDuration",
        "sampleHz",
        "curvature",
        "minDwell",
        "maxDwell",
        "durationIntercept",
        "durationSlope",
    }
)


class PreferenceError(ValueError):
    """Raised when a profile document is invalid or outside its bounds."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PreferenceError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise PreferenceError(f"non-finite JSON number: {value}")


def _require_object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PreferenceError(f"{name} must be an object")
    return value


def _require_exact_fields(value: dict[str, Any], expected: frozenset[str], name: str) -> None:
    actual = frozenset(value)
    missing = expected - actual
    unknown = actual - expected
    if missing:
        raise PreferenceError(f"{name} is missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise PreferenceError(f"{name} has unknown fields: {', '.join(sorted(unknown))}")


def _require_int(value: Any, name: str, *, lower: int, upper: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PreferenceError(f"{name} must be an integer")
    if not lower <= value <= upper:
        raise PreferenceError(f"{name} must be in [{lower}, {upper}]")
    return value


def _require_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PreferenceError(f"{name} must be a number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise PreferenceError(f"{name} is outside the finite numeric bounds") from exc
    if not math.isfinite(result):
        raise PreferenceError(f"{name} must be finite")
    return result


def _profile_document(profile: MotionProfile, demonstration_count: int) -> dict[str, Any]:
    if not isinstance(profile, MotionProfile):
        raise PreferenceError("profile must be MotionProfile")
    count = _require_int(
        demonstration_count,
        "demonstrationCount",
        lower=0,
        upper=MAX_DEMONSTRATIONS,
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "role": profile.role.value,
        "demonstrationCount": count,
        "profile": {
            "preferredSpeed": float(profile.preferred_speed),
            "minDuration": float(profile.min_duration),
            "maxDuration": float(profile.max_duration),
            "sampleHz": float(profile.sample_hz),
            "curvature": float(profile.curvature),
            "minDwell": float(profile.min_dwell),
            "maxDwell": float(profile.max_dwell),
            "durationIntercept": float(profile.duration_intercept),
            "durationSlope": float(profile.duration_slope),
        },
    }


def _document_to_profile(document: dict[str, Any]) -> MotionProfile:
    _require_exact_fields(document, _TOP_LEVEL_FIELDS, "profile document")
    schema_version = _require_int(
        document["schemaVersion"],
        "schemaVersion",
        lower=0,
        upper=2**31 - 1,
    )
    if schema_version != SCHEMA_VERSION:
        raise PreferenceError("unsupported profile schema version")
    role_value = document["role"]
    if not isinstance(role_value, str):
        raise PreferenceError("role must be text")
    try:
        role = DemonstrationRole(role_value)
    except ValueError as exc:
        raise PreferenceError("role is not a supported motion role") from exc
    demonstration_count = _require_int(
        document["demonstrationCount"],
        "demonstrationCount",
        lower=0,
        upper=MAX_DEMONSTRATIONS,
    )
    profile_values = _require_object(document["profile"], "profile")
    _require_exact_fields(profile_values, _PROFILE_FIELDS, "profile")
    values = {
        "preferred_speed": _require_number(profile_values["preferredSpeed"], "preferredSpeed"),
        "min_duration": _require_number(profile_values["minDuration"], "minDuration"),
        "max_duration": _require_number(profile_values["maxDuration"], "maxDuration"),
        "sample_hz": _require_number(profile_values["sampleHz"], "sampleHz"),
        "curvature": _require_number(profile_values["curvature"], "curvature"),
        "min_dwell": _require_number(profile_values["minDwell"], "minDwell"),
        "max_dwell": _require_number(profile_values["maxDwell"], "maxDwell"),
        "duration_intercept": _require_number(profile_values["durationIntercept"], "durationIntercept"),
        "duration_slope": _require_number(profile_values["durationSlope"], "durationSlope"),
        "role": role,
    }
    try:
        profile = MotionProfile(**values)
    except (TypeError, ValueError) as exc:
        raise PreferenceError(f"profile values are outside bounds: {exc}") from exc
    baseline = MotionProfile(role=role)
    if demonstration_count == 0 and profile != baseline:
        raise PreferenceError("non-baseline profile requires at least one demonstration")
    return profile


def _read_document(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        metadata = path.stat()
    except FileNotFoundError:
        raise
    if metadata.st_size > MAX_PROFILE_DOCUMENT_BYTES:
        raise PreferenceError(f"profile file exceeds the maximum size of {MAX_PROFILE_DOCUMENT_BYTES} bytes")
    mode = stat.S_IMODE(metadata.st_mode)
    if mode != 0o600:
        raise PreferenceError("profile file permissions must be exactly 0600")
    with path.open("rb") as stream:
        raw = stream.read(MAX_PROFILE_DOCUMENT_BYTES + 1)
    if len(raw) > MAX_PROFILE_DOCUMENT_BYTES or path.stat().st_size > MAX_PROFILE_DOCUMENT_BYTES:
        raise PreferenceError(f"profile file exceeds the maximum size of {MAX_PROFILE_DOCUMENT_BYTES} bytes")
    try:
        decoded = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except PreferenceError:
        raise
    except (UnicodeDecodeError, ValueError) as exc:
        raise PreferenceError("profile file is not valid UTF-8 JSON") from exc
    document = _require_object(decoded, "profile document")
    _document_to_profile(document)
    return document, raw


def load_motion_profile(path: str | os.PathLike[str]) -> MotionProfile:
    """Load one explicitly selected role profile.

    A missing or invalid selected file raises instead of silently selecting a
    baseline profile.  The demonstration count is validated but is not part
    of the runtime return value; callers that need it can inspect the CLI
    document with ``motion_profile_document``.
    """

    document, _ = _read_document(Path(path))
    return _document_to_profile(document)


def motion_profile_document(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Return the validated aggregate document for the ``show`` command."""

    document, _ = _read_document(Path(path))
    return document


def save_motion_profile(
    path: str | os.PathLike[str],
    profile: MotionProfile,
    demonstration_count: int = 0,
) -> None:
    """Atomically save a canonical aggregate profile with mode ``0600``."""

    document = _profile_document(profile, demonstration_count)
    # Validate the complete wire document before touching an existing target.
    # This keeps the persisted count/profile invariant symmetric with load and
    # guarantees a rejected default-count learned profile cannot replace a
    # previously valid file.
    _document_to_profile(document)
    payload = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    destination = Path(path)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if destination.exists():
        if not destination.is_file():
            raise PreferenceError("existing profile target is not a regular file")
        _read_document(destination)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        dir=destination.parent,
    )
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, destination)
        os.chmod(destination, 0o600)
        directory_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


__all__ = [
    "MAX_DEMONSTRATIONS",
    "MAX_INLINE_JSON_BYTES",
    "MAX_PROFILE_DOCUMENT_BYTES",
    "PreferenceError",
    "SCHEMA_VERSION",
    "load_motion_profile",
    "motion_profile_document",
    "save_motion_profile",
]
