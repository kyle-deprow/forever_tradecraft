"""TOML configuration for the measured local profile."""

from __future__ import annotations

import hashlib
import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from crowley.core.watchlist import load_catalog

from .driver import DriverProfile

_CANONICAL_CLIENT_VERSION, _CANONICAL_CLIENT_BUILD = load_catalog().client_build.rsplit(".", 1)


@dataclass(frozen=True)
class SessionConfig:
    profile: DriverProfile
    journal: Path
    socket: Path
    cadence_seconds: int = 900
    sweep_cap_seconds: int = 600
    quiet_margin_seconds: int = 15
    reload_deadline_seconds: int = 45
    ack_deadline_seconds: int = 60
    upload_deadline_seconds: int = 60
    model: str = "gpt-6-luna"
    cli_version: str = "codex-cli 0.162.1"
    codex_path: str = "/home/dev/.local/share/pnpm/nodejs/22.23.1/bin/codex"
    capture_dir: Path = Path("/run/user/1000/crowley/captures")
    companion_state: Path | None = None
    saved_variables: Path | None = None
    data_lua: Path | None = None
    plan_hash: str = ""
    plan_json: str = ""
    client_build: str = _CANONICAL_CLIENT_BUILD
    interface: int = 16001
    player_faction: str = "Alliance"
    locale: str = "enUS"
    client_version: str = _CANONICAL_CLIENT_VERSION
    addon_version: str = "0.2.0"
    pointer_profile: Path | None = None
    camera_profile: Path | None = None
    move_profile: Path | None = None
    telemetry_region_executable: Path | None = None
    telemetry_region_executable_sha256: str | None = None


def load_config(path: str | Path) -> SessionConfig:
    target = Path(path)
    with target.open("rb") as handle:
        raw: dict[str, Any] = tomllib.load(handle)
    profile = raw.get("profile", {})
    session = raw.get("session", {})

    def tuple4(name: str, default: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        value = profile.get(name, default)
        if not isinstance(value, list) or len(value) != 4 or any(not isinstance(item, int) for item in value):
            raise ValueError(f"{name} must contain four integer coordinates")
        return tuple(value)  # type: ignore[return-value]

    origin = profile.get("canvas_origin", [80, 48])
    if not isinstance(origin, list) or len(origin) != 2 or any(not isinstance(item, int) for item in origin):
        raise ValueError("canvas_origin must contain two integer coordinates")
    window_offset = profile.get("window_client_offset", [0, 0])
    if (
        not isinstance(window_offset, list)
        or len(window_offset) != 2
        or any(not isinstance(item, int) for item in window_offset)
    ):
        raise ValueError("window_client_offset must contain two integer coordinates")
    if "action_anchors" in profile or "anchor_fingerprints" in profile:
        raise ValueError(
            "manual action anchors are not accepted; controls must be measured from a fresh live scene"
        )
    # Coordinates and copied identity fingerprints are deliberately not a
    # configuration surface.  The native visual producer measures one control
    # from one fresh scene and the driver seals it to that capture.
    anchors: dict[str, tuple[int, int]] = {}
    anchor_fingerprints: dict[str, str] = {}
    telemetry_raw = session.get("telemetry_region_executable")
    telemetry_hash = session.get("telemetry_region_executable_sha256")
    if telemetry_raw is None and telemetry_hash is None:
        telemetry_path: Path | None = None
        telemetry_digest: str | None = None
    else:
        if not isinstance(telemetry_raw, str) or not Path(telemetry_raw).is_absolute():
            raise ValueError("telemetry_region_executable must be an absolute path")
        if not isinstance(telemetry_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", telemetry_hash):
            raise ValueError("telemetry_region_executable_sha256 must be a lowercase SHA-256")
        telemetry_path = Path(telemetry_raw)
        if not telemetry_path.is_file() or not os.access(telemetry_path, os.X_OK):
            raise ValueError("telemetry region executable is unavailable")
        if hashlib.sha256(telemetry_path.read_bytes()).hexdigest() != telemetry_hash:
            raise ValueError("telemetry region executable hash does not match")
        telemetry_digest = telemetry_hash
    driver_profile = DriverProfile(
        display=str(profile.get("display", ":0")),
        xauthority=str(profile.get("xauthority", "")),
        wine_prefix=str(profile.get("wine_prefix", "")),
        client_width=int(profile.get("client_width", 1920)),
        client_height=int(profile.get("client_height", 1080)),
        outer_width=int(profile.get("outer_width", 1928)),
        outer_height=int(profile.get("outer_height", 1092)),
        window_client_offset=tuple(window_offset),
        action_anchors=anchors,
        canvas_origin=tuple(origin),
        canvas_crop=tuple4("canvas_crop", (80, 48, 256, 256)),
        model_crop=tuple4("model_crop", (80, 48, 1760, 984)),
        window_title=str(profile.get("window_title", "World of Warcraft")),
        window_class=str(profile.get("window_class", "wowb.exe")),
        executable=str(profile.get("executable", "WowB.exe")),
        character=str(profile.get("character", "Arthur")),
        realm=str(profile.get("realm", "Classic Beta PvE 2")),
        house=str(profile.get("house", "beta-normal-alliance")),
        plan_count=int(profile.get("plan_count", 428)),
        anchor_fingerprints=anchor_fingerprints,
        telemetry_region_executable=telemetry_path,
        telemetry_region_executable_sha256=telemetry_digest,
    )
    if not driver_profile.window_title or not driver_profile.window_class:
        raise ValueError("window title and class are required for one-client identity")
    if (
        driver_profile.plan_count,
        session.get("cadence_seconds", 900),
        session.get("sweep_cap_seconds", 600),
    ) != (428, 900, 600):
        raise ValueError("configured plan must be 428 items with 900/600 cadence and cap")
    if (
        str(profile.get("client_build", _CANONICAL_CLIENT_BUILD)) != _CANONICAL_CLIENT_BUILD
        or int(profile.get("interface", 16001)) != 16001
    ):
        raise ValueError(
            f"configured client must be Forever beta build {_CANONICAL_CLIENT_BUILD}/interface 16001"
        )
    if (
        str(profile.get("player_faction", "Alliance")) != "Alliance"
        or str(profile.get("locale", "enUS")) != "enUS"
        or str(profile.get("client_version", _CANONICAL_CLIENT_VERSION)) != _CANONICAL_CLIENT_VERSION
        or str(profile.get("addon_version", "0.2.0")) != "0.2.0"
    ):
        raise ValueError("configured client context does not match the pinned Forever profile")
    configured_plan_hash = profile.get("plan_hash", "")
    configured_plan_json = profile.get("plan_json", "")
    if not isinstance(configured_plan_hash, str) or not isinstance(configured_plan_json, str):
        raise ValueError("plan_hash and plan_json must be strings")
    if configured_plan_hash and not re.fullmatch(r"[0-9a-f]{64}", configured_plan_hash):
        raise ValueError("plan_hash must be a lowercase SHA-256 value")
    if bool(configured_plan_hash) != bool(configured_plan_json):
        raise ValueError("plan_hash and plan_json must be configured together")
    if not configured_plan_hash:
        raise ValueError("the canonical plan hash and plan JSON are required before startup")
    if configured_plan_json and (
        hashlib.sha256(configured_plan_json.encode()).hexdigest() != configured_plan_hash
    ):
        raise ValueError("plan_hash does not match canonical plan_json")
    left, top, width, height = driver_profile.model_crop
    if (
        driver_profile.model_crop == driver_profile.canvas_crop
        or left < 0
        or top < 0
        or width < 640
        or height < 480
        or left + width > driver_profile.client_width
        or top + height > driver_profile.client_height
    ):
        raise ValueError("model_crop must be a separately verified game-client crop")
    quiet_margin = int(session.get("quiet_margin_seconds", 15))
    reload_deadline = int(session.get("reload_deadline_seconds", 45))
    ack_deadline = int(session.get("ack_deadline_seconds", 60))
    upload_deadline = int(session.get("upload_deadline_seconds", 60))
    if (
        not 0 < quiet_margin < 900
        or not 1 <= reload_deadline <= 600
        or not 1 <= ack_deadline <= 600
        or not 1 <= upload_deadline <= 60
    ):
        raise ValueError("session deadlines are outside the pinned bounds")
    state_home = Path(os.environ.get("XDG_STATE_HOME") or "~/.local/state").expanduser()
    journal_path = Path(session.get("journal", state_home / "crowley" / "session.json")).expanduser()
    socket_path = Path(session.get("socket", "/run/user/1000/crowley/session.sock")).expanduser()
    saved_path = Path(session["saved_variables"]).expanduser() if session.get("saved_variables") else None
    companion_path = Path(session["companion_state"]).expanduser() if session.get("companion_state") else None
    data_path = Path(session["data_lua"]).expanduser() if session.get("data_lua") else None
    motion_profiles: dict[str, Path | None] = {}
    for role in ("pointer", "camera", "move"):
        configured = session.get(f"{role}_profile")
        if configured in (None, "baseline"):
            motion_profiles[role] = None
        elif isinstance(configured, str) and Path(configured).is_absolute():
            motion_profiles[role] = Path(configured)
        else:
            raise ValueError(f"{role}_profile must be 'baseline' or an absolute profile path")
    for label, required_path in (
        ("SavedVariables", saved_path),
        ("companion state", companion_path),
        ("Data.lua", data_path),
    ):
        if required_path is None:
            raise ValueError(f"{label} path is required before startup")
        if not required_path.is_absolute():
            raise ValueError(f"{label} path must be absolute")
        if not required_path.is_file():
            raise ValueError(f"{label} file does not exist: {required_path}")
    codex_path = str(session.get("codex_path", "/home/dev/.local/share/pnpm/nodejs/22.23.1/bin/codex"))
    if not Path(codex_path).is_absolute():
        raise ValueError("codex_path must be an absolute executable path")
    if (
        str(session.get("model", "gpt-6-luna")) != "gpt-6-luna"
        or str(session.get("cli_version", "codex-cli 0.162.1")) != "codex-cli 0.162.1"
    ):
        raise ValueError("model and Codex CLI version must match the pinned startup contract")
    return SessionConfig(
        profile=driver_profile,
        # The journal contains restart intent, intervention history, and
        # accepted evidence.  Keep it in the persistent user state directory;
        # only the socket/capture paths belong under the runtime directory.
        journal=journal_path,
        socket=socket_path,
        cadence_seconds=900,
        sweep_cap_seconds=600,
        quiet_margin_seconds=quiet_margin,
        reload_deadline_seconds=reload_deadline,
        ack_deadline_seconds=ack_deadline,
        upload_deadline_seconds=upload_deadline,
        model=str(session.get("model", "gpt-6-luna")),
        cli_version=str(session.get("cli_version", "codex-cli 0.162.1")),
        codex_path=codex_path,
        capture_dir=Path(session.get("capture_dir", "/run/user/1000/crowley/captures")).expanduser(),
        companion_state=companion_path,
        saved_variables=saved_path,
        data_lua=data_path,
        plan_hash=str(profile.get("plan_hash", "")),
        plan_json=str(profile.get("plan_json", "")),
        client_build=str(profile.get("client_build", _CANONICAL_CLIENT_BUILD)),
        interface=int(profile.get("interface", 16001)),
        player_faction=str(profile.get("player_faction", "Alliance")),
        locale=str(profile.get("locale", "enUS")),
        client_version=str(profile.get("client_version", _CANONICAL_CLIENT_VERSION)),
        addon_version=str(profile.get("addon_version", "0.2.0")),
        pointer_profile=motion_profiles["pointer"],
        camera_profile=motion_profiles["camera"],
        move_profile=motion_profiles["move"],
        telemetry_region_executable=telemetry_path,
        telemetry_region_executable_sha256=telemetry_digest,
    )


__all__ = ["SessionConfig", "load_config"]
