"""Background capture, evidence, and bounded action loop for the user service."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
import os
import shutil
import stat
import tempfile
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, is_dataclass, replace
from functools import wraps
from pathlib import Path
from typing import Any

from crowley.core import savedvars
from crowley.core.watchlist import load_catalog

from .calibration import (
    LinuxProcStatusVmHwmReset5,
    NativeCalibrationRunner,
    NativeMemoryArchiveReceipt,
    NativePreconstructionEvidence,
    NativeRenderObservation,
    NativeRestorationReceipt,
)
from .config import SessionConfig
from .controller import Controller, ControllerState
from .decoder import PixelDecoder, Sample
from .driver import (
    DesktopDriver,
    DriverError,
    MeasuredAnchor,
    NamedStateObservation,
    WindowIdentity,
    X11Backend,
)
from .evidence import (
    EvidenceError,
    queues_empty,
    read_data_acknowledged_ids,
    read_stable_saved_scan,
    read_uploads,
)
from .executor import (
    BindingMetadata,
    ExecutorError,
    FreshObservation,
    KeyRole,
    Point,
    Rect,
    WaitPolicy,
    accepts_observation,
    observations_settled,
    plan_camera_drag,
    plan_context_wait,
)
from .guardian import GuardianError
from .journal import Journal, JournalError, stable_file
from .model import LunaAdapter, ModelError
from .motion import (
    DEFAULT_MOVEMENT_CALIBRATION_PULSE_SECONDS,
    MAX_BASIS_DISPLACEMENT,
    MAX_CAMERA_CALIBRATION_PIXELS,
    MAX_CAMERA_CALIBRATION_YAW,
    MAX_CAMERA_INPUT_YAW,
    MAX_CAMERA_RESPONSE_RELATIVE_ERROR,
    MAX_CAMERA_YAW_PER_PIXEL,
    MAX_CONFIRMATION_FACING_DRIFT,
    MAX_CONFIRMATION_POSITION_DRIFT,
    MAX_FRAME_AGE,
    MAX_PULSE_SECONDS,
    MAX_WAYPOINT_CAMERA_TURNS,
    MAX_WAYPOINT_DISTANCE,
    MAX_WAYPOINT_PULSES,
    MAX_WAYPOINT_SECONDS,
    MIN_BASIS_DISPLACEMENT,
    MIN_CAMERA_CALIBRATION_PIXELS,
    MIN_CAMERA_RESPONSE_ABSOLUTE_ERROR,
    MIN_MOVEMENT_CALIBRATION_PULSE_SECONDS,
    MOTION_CALIBRATION_OPERATION_SECONDS,
    MOTION_CAMERA_OPERATION_SECONDS,
    MOTION_KEY_OPERATION_SECONDS,
    MOTION_POST_RELEASE_RESERVE_SECONDS,
    TRAVEL_UNCERTAINTY_FRACTION,
    WAYPOINT_TRANSLATION_HEADING_TOLERANCE,
    CameraMapping,
    MotionError,
    MotionFrame,
    MovementBasis,
    NativeMotionProvider,
    RouteEvidence,
    ViewportEvidence,
    normalize_angle,
    waypoint_heading_error,
)
from .preferences import load_motion_profile
from .protocol import ProtocolError


def _canonical_semantic_value(value: Any) -> Any:
    """Convert dataclass configuration values to stable JSON primitives."""

    if isinstance(value, Path):
        return os.fspath(value)
    if isinstance(value, dict):
        return {str(key): _canonical_semantic_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical_semantic_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported session config value: {type(value).__name__}")


def _canonical_dataclass_json(value: Any) -> bytes:
    if not is_dataclass(value) or isinstance(value, type):
        raise TypeError("session config binding requires a dataclass instance")
    normalized = _canonical_semantic_value(asdict(value))
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def session_config_semantic_sha256(config: SessionConfig) -> str:
    """Hash the loaded semantic config independently of TOML formatting."""

    return hashlib.sha256(_canonical_dataclass_json(config)).hexdigest()


_RUNTIME_SOURCE_FILES = {
    "daemon.py": Path("src/crowley/session/daemon.py"),
    "driver.py": Path("src/crowley/session/driver.py"),
    "cli.py": Path("src/crowley/session/cli.py"),
    "decoder.py": Path("src/crowley/session/decoder.py"),
    "protocol.py": Path("src/crowley/session/protocol.py"),
    "offline_harness.py": Path("tools/gnome-telemetry-region/offline_harness.py"),
    "session_performance.py": Path("tools/session_performance.py"),
}
_RUNTIME_SOURCE_MAX_BYTES = 4 * 1024 * 1024


def _runtime_source_root() -> Path:
    """Derive the trusted project root from the installed daemon source."""

    source = Path(__file__).absolute()
    if source.is_symlink():
        raise DriverError("runtime source descriptor is a symlink")
    return source.resolve().parents[3]


def _runtime_source_hashes() -> dict[str, str]:
    """Read the exact seven bounded source descriptors, refusing drift."""

    root = _runtime_source_root()
    result: dict[str, str] = {}
    for logical_name, relative in _RUNTIME_SOURCE_FILES.items():
        path = root / relative
        try:
            before = path.lstat()
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise DriverError(f"runtime source {logical_name} is not a regular file")
            if before.st_size > _RUNTIME_SOURCE_MAX_BYTES:
                raise DriverError(f"runtime source {logical_name} exceeds its bounded size")
            flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(path, flags)
            try:
                opened = os.fstat(descriptor)
                if not stat.S_ISREG(opened.st_mode) or (
                    opened.st_dev,
                    opened.st_ino,
                    opened.st_mode,
                    opened.st_nlink,
                    opened.st_size,
                    opened.st_mtime_ns,
                    opened.st_ctime_ns,
                ) != (
                    before.st_dev,
                    before.st_ino,
                    before.st_mode,
                    before.st_nlink,
                    before.st_size,
                    before.st_mtime_ns,
                    before.st_ctime_ns,
                ):
                    raise DriverError(f"runtime source {logical_name} changed during inspection")
                digest = hashlib.sha256()
                total = 0
                while True:
                    chunk = os.read(descriptor, min(1024 * 1024, _RUNTIME_SOURCE_MAX_BYTES + 1 - total))
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > _RUNTIME_SOURCE_MAX_BYTES:
                        raise DriverError(f"runtime source {logical_name} exceeds its bounded size")
                    digest.update(chunk)
                if total != opened.st_size:
                    raise DriverError(f"runtime source {logical_name} exceeds its bounded size")
                after = os.fstat(descriptor)
                if (
                    after.st_dev,
                    after.st_ino,
                    after.st_mode,
                    after.st_nlink,
                    after.st_size,
                    after.st_mtime_ns,
                    after.st_ctime_ns,
                ) != (
                    opened.st_dev,
                    opened.st_ino,
                    opened.st_mode,
                    opened.st_nlink,
                    opened.st_size,
                    opened.st_mtime_ns,
                    opened.st_ctime_ns,
                ):
                    raise DriverError(f"runtime source {logical_name} changed during inspection")
                after_path = path.lstat()
                if (
                    stat.S_ISLNK(after_path.st_mode)
                    or not stat.S_ISREG(after_path.st_mode)
                    or (
                        after_path.st_dev,
                        after_path.st_ino,
                        after_path.st_mode,
                        after_path.st_nlink,
                        after_path.st_size,
                        after_path.st_mtime_ns,
                        after_path.st_ctime_ns,
                    )
                    != (
                        after.st_dev,
                        after.st_ino,
                        after.st_mode,
                        after.st_nlink,
                        after.st_size,
                        after.st_mtime_ns,
                        after.st_ctime_ns,
                    )
                ):
                    raise DriverError(f"runtime source {logical_name} changed during inspection")
            finally:
                os.close(descriptor)
        except FileNotFoundError as exc:
            raise DriverError(f"runtime source {logical_name} is unavailable") from exc
        except OSError as exc:
            raise DriverError(f"runtime source {logical_name} cannot be inspected") from exc
        result[logical_name] = digest.hexdigest()
    if set(result) != set(_RUNTIME_SOURCE_FILES):
        raise DriverError("runtime source descriptor map is incomplete")
    return result


def _driver_profile_matches_config(driver: Any, config: SessionConfig) -> bool:
    try:
        driver_profile = asdict(driver.profile)
        configured_profile = asdict(config.profile)
        return json.dumps(
            _canonical_semantic_value(driver_profile), sort_keys=True, separators=(",", ":"), allow_nan=False
        ) == json.dumps(
            _canonical_semantic_value(configured_profile),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError):
        return False


def _serialized_motion(method):
    """Serialize all interaction producers around one physical intent.

    IPC handlers already serialize their own requests, but the engine, a
    direct caller, and a concurrent socket can still reach the daemon at the
    same time.  The lock is deliberately acquired without waiting: a second
    intent is rejected while the first one still owns capture/model/native
    feedback and the input lease.
    """

    @wraps(method)
    def guarded(self, *args, **kwargs):
        lock = getattr(self, "_motion_intent_lock", None)
        if lock is None:
            lock = threading.RLock()
            self._motion_intent_lock = lock
        if not lock.acquire(blocking=False):
            raise DriverError("another motion intent is already in flight")
        local = getattr(self, "_motion_deadline_local", None)
        outer = local is None or not hasattr(local, "deadline")
        try:
            if outer:
                local = local or threading.local()
                operation_seconds = {
                    "execute_motion_key": MOTION_KEY_OPERATION_SECONDS,
                    "execute_camera_delta": MOTION_CAMERA_OPERATION_SECONDS,
                    "calibrate_camera_mapping": MOTION_CAMERA_OPERATION_SECONDS,
                    "calibrate_movement_basis": MOTION_CALIBRATION_OPERATION_SECONDS,
                    "execute_waypoint": MAX_WAYPOINT_SECONDS,
                }.get(method.__name__)
                if operation_seconds is None:
                    raise DriverError(f"motion operation {method.__name__!r} has no bounded deadline")
                try:
                    local.deadline = self._native_clock() + operation_seconds
                except Exception:
                    self._invalidate_motion_admission()
                    raise
                self._motion_deadline_local = local
            return method(self, *args, **kwargs)
        finally:
            if outer:
                try:
                    del local.deadline
                except AttributeError:
                    pass
            lock.release()

    return guarded


class SessionDaemon:
    """One process owns one controller, input lease, capture loop, and IPC lock."""

    # Native operator actions are deliberately outside the daemon.  These
    # bounds only determine how long the producer waits for the next actual
    # Agent publication after a readiness signal becomes visible.
    _NATIVE_FRAME_TIMEOUT_SECONDS = 30.0
    _NATIVE_POLL_INTERVAL_SECONDS = 0.05
    _MIN_CAMERA_DRAG_PIXELS = MIN_CAMERA_CALIBRATION_PIXELS

    @staticmethod
    def _load_motion_profiles(config: SessionConfig) -> dict[str, Any]:
        profiles = {
            "pointer": (config.pointer_profile, "pointer"),
            "camera": (config.camera_profile, "camera"),
            "move": (config.move_profile, "move"),
        }
        loaded: dict[str, Any] = {}
        from .executor import DemonstrationRole, MotionProfile

        baselines = {
            "pointer": MotionProfile(role=DemonstrationRole.POINTER),
            "camera": MotionProfile(role=DemonstrationRole.CAMERA),
            "move": MotionProfile(role=DemonstrationRole.MOVE),
        }
        for role, (path, _label) in profiles.items():
            if path is None:
                loaded[role] = baselines[role]
                continue
            profile = load_motion_profile(path)
            if profile.role.value != role:
                raise DriverError(f"selected {role} motion profile has role {profile.role.value!r}")
            loaded[role] = profile
        return loaded

    def __init__(
        self,
        config: SessionConfig,
        *,
        controller: Controller | None = None,
        driver: DesktopDriver | None = None,
    ):
        # Keep the loaded config immutable from runtime driver evidence. The
        # driver retains the supplied profile object and records measured
        # anchors there after real actions.
        self.config = copy.deepcopy(config)
        self._loaded_config_semantic_sha256 = session_config_semantic_sha256(self.config)
        self._model_counter_lock = threading.RLock()
        self._model_call_counters = {"started": 0, "succeeded": 0, "failed": 0}
        # Source evidence is optional for ordinary daemon operation. A source
        # installation that cannot be inspected remains usable, but its
        # paused diagnostic is refused when it reaches the qualification gate.
        try:
            self._runtime_source_binding = _runtime_source_hashes()
        except DriverError:
            self._runtime_source_binding = None
        self._motion_profiles = self._load_motion_profiles(self.config)
        self.capture_index = 0
        self._named_capture_sequence = 0
        self._last_addon_sequence = 0
        self._last_addon_boot = ""
        self._native_measurement_state: dict[str, Any] | None = None
        # NativeCalibrationRunner reuses the provider's exact crop artifact so
        # it can decode and hash the same bytes.  Keep those private paths
        # until the runner has consumed the whole 101-frame operation; then
        # discard every intermediate while retaining the final sealed proof.
        self._native_owned_capture_paths: set[Any] = set()
        self._native_bootstrap_ready = threading.Event()
        self._native_baseline_ready = threading.Event()
        self._native_bootstrap_lock = threading.RLock()
        self._native_bootstrap_observation: dict[str, Any] | None = None
        self._native_baseline_observation: dict[str, Any] | None = None
        self._native_bootstrap_proof: dict[str, Any] | None = None
        self._native_handshake: dict[str, Any] = {
            "state": "idle",
            "holdRequired": False,
            "measureReady": False,
            "resumeRequired": False,
            "resumeReady": False,
            "failure": "",
            "restored": None,
            "archiveReceipts": [],
        }
        self._shutdown_event = threading.Event()
        self._motion_intent_lock = threading.RLock()
        self._motion_deadline_local = threading.local()
        self._named_observation_deadline: float | None = None
        self._calibration_lock = threading.Lock()
        self._calibration_state_lock = threading.RLock()
        self._calibration_thread: threading.Thread | None = None
        self._calibration_operation: dict[str, Any] = {
            "state": "idle",
            "kind": "",
            "generation": 0,
            "startedAt": 0,
            "finishedAt": 0,
            "error": "",
            "readiness": None,
            "result": None,
        }
        self.driver = driver or DesktopDriver(
            copy.deepcopy(self.config.profile),
            pointer_motion_profile=self._motion_profiles["pointer"],
            camera_motion_profile=self._motion_profiles["camera"],
            move_motion_profile=self._motion_profiles["move"],
            named_state_observer=self._observe_named_state,
            native_measurement_provider=self._native_measurement_provider,
            measured_anchor_provider=self._measure_pointer_anchor,
        )
        # Keep bounded native polling and the runner on the driver's injected
        # monotonic source.  This is also the source used by the guardian and
        # makes headless operator fixtures deterministic without changing the
        # process-wide clock used by sockets, watchdogs, or pytest threads.
        configured_native_clock = getattr(self.driver, "_clock", None)
        self._native_clock = configured_native_clock if callable(configured_native_clock) else time.monotonic
        configured_anchor_provider = getattr(self.driver, "measured_anchor_provider", None)
        self._configured_anchor_provider = (
            configured_anchor_provider
            if callable(configured_anchor_provider)
            and getattr(configured_anchor_provider, "__self__", None) is not self
            else None
        )
        if isinstance(self.driver.backend, X11Backend):
            # The installed daemon owns the live providers.  A caller cannot
            # replace them with copied metrics or identity-only callbacks.  A
            # pre-bound native anchor producer is retained because the native
            # worker owns that concrete visual measurement boundary.
            self.driver._named_state_observer = self._observe_named_state
            self.driver.native_measurement_provider = self._native_measurement_provider
            if self._configured_anchor_provider is None:
                self.driver.measured_anchor_provider = self._measure_pointer_anchor
            self.driver.native_preconstruction_provider = self._native_preconstruction_provider
            # The native runner consumes provider artifacts and publishes the
            # HWM boundary through these lead-owned hooks.  Registering them
            # here prevents a caller from substituting an identity-only or
            # copied-metrics callback on the live driver.
            self.driver.notify_native_baseline_ready = self.notify_native_baseline_ready
            self.driver.notify_native_memory_reset_ready = self.notify_native_memory_reset_ready
            self.driver.notify_native_hold_required = self.notify_native_hold_required
            self.driver.notify_native_memory_ready = self.notify_native_memory_ready
            self.driver.notify_native_resume_ready = self.notify_native_resume_ready
            self.driver.notify_native_resume_required = self.notify_native_resume_required
            self.driver.notify_native_measurement_failed = self.notify_native_measurement_failed
            self.driver.release_native_capture = self.release_native_capture
        if isinstance(self.driver.backend, X11Backend) and not (
            self.config.plan_hash and self.config.plan_json
        ):
            # The driver acquires the desktop lease and starts its independent
            # guardian at construction.  Do not leave either owner alive when
            # rejecting an incomplete live profile before the controller exists.
            try:
                close = getattr(self.driver, "close", None)
                if callable(close):
                    close()
            finally:
                raise DriverError("live session requires an externally pinned canonical plan hash and JSON")
        self.controller = controller or Controller(
            Journal(self.config.journal),
            driver=self.driver,
            cadence_seconds=self.config.cadence_seconds,
            sweep_cap_seconds=self.config.sweep_cap_seconds,
            reload_deadline_seconds=self.config.reload_deadline_seconds,
            upload_deadline_seconds=self.config.upload_deadline_seconds,
            ack_deadline_seconds=self.config.ack_deadline_seconds,
        )
        self.motion_provider = NativeMotionProvider(
            self.capture_status,
            lambda: self._resolve_identity(
                require_foreground=True,
                deadline=getattr(
                    getattr(self, "_motion_deadline_local", None),
                    "deadline",
                    None,
                ),
            ),
            capture_with_deadline=self.capture_status,
            clock=self._native_clock,
        )
        self.camera_mapping: CameraMapping | None = None
        self.movement_basis: MovementBasis | None = None
        self.decoder = PixelDecoder(crop=self.config.profile.canvas_crop)
        self.last_error = ""
        self.reopen_action_sent = False
        self.current_evidence = None
        # Closeout may race the addon's automatic start.  Keep one fresh
        # scanner observation so a transient item/owned frame is not mistaken
        # for a new run; the pinned scanner intentionally leaves
        # ``activeSweepId`` empty until finish.
        self._closeout_scan_candidate: tuple[int, str] | None = None
        self._closeout_fence_observation: tuple[str, int] | None = None
        self.model = LunaAdapter(
            model=self.config.model,
            cli_version=self.config.cli_version,
            codex_path=self.config.codex_path,
        )
        journal_value = self.controller.journal.read()
        stored_recovery_actions = journal_value.get("recoveryActions", [])
        self.recovery_attempts = int(journal_value.get("recoveryAttempts", 0))
        self.recovery_actions: set[str] = (
            {item for item in stored_recovery_actions if isinstance(item, str)}
            if isinstance(stored_recovery_actions, list)
            else set()
        )
        self.last_snapshot: dict[str, Any] = journal_value.get("telemetry", {})
        self._last_action_generation = 0

        # Revocation can be raised by the independent XI2 guardian while a
        # bounded visual turn is running.  Cancel the complete model process
        # group so no late decision can reach the executor.
        on_revoke = getattr(self.driver, "on_revoke", None)
        if callable(on_revoke):
            on_revoke(lambda _reason, _generation: self.model.cancel())

    def _begin_calibration(self, kind: str, generation: int | None) -> None:
        if not self._calibration_lock.acquire(blocking=False):
            raise DriverError("a calibration operation is already running")
        with self._calibration_state_lock:
            self._calibration_operation = {
                "state": "running",
                "kind": kind,
                "generation": generation if generation is not None else -1,
                "startedAt": int(time.time()),
                "finishedAt": 0,
                "error": "",
                "readiness": None,
                "result": None,
            }

    def start_calibration(self, kind: str, *, expected_generation: int | None = None) -> dict[str, Any]:
        """Start one supervised long-running gate and return immediately.

        Calibration can legitimately wait for a human sample or 101 fresh
        frames.  Socket clients therefore receive an observable operation
        record instead of holding a request open until the gate finishes.
        """

        if kind not in {"native", "input"}:
            raise DriverError("unknown calibration operation")
        with self._calibration_state_lock:
            current = self._calibration_operation.get("state")
            if current in {"starting", "running"}:
                raise DriverError("a calibration operation is already running")
            self._calibration_operation = {
                "state": "starting",
                "kind": kind,
                "generation": expected_generation if expected_generation is not None else -1,
                "startedAt": int(time.time()),
                "finishedAt": 0,
                "error": "",
                "readiness": None,
                "result": None,
            }

        def worker() -> None:
            try:
                if kind == "native":
                    self.run_native_calibration(expected_generation=expected_generation)
                else:
                    self.run_input_calibration(expected_generation=expected_generation)
                with self._calibration_state_lock:
                    # The direct runner's return is assembled before its
                    # operation lock is released.  Pollers need the final
                    # complete/error state, so take a fresh status snapshot.
                    self._calibration_operation["result"] = self.status_dict()
            except Exception as exc:
                with self._calibration_state_lock:
                    self._calibration_operation["error"] = str(exc)
            finally:
                with self._calibration_state_lock:
                    if self._calibration_operation.get("state") == "starting":
                        self._calibration_operation["state"] = "error"
                        self._calibration_operation["finishedAt"] = int(time.time())

        thread = threading.Thread(target=worker, name=f"crowley-{kind}-calibration", daemon=True)
        self._calibration_thread = thread
        thread.start()
        return self.status_dict()

    def calibration_status(self) -> dict[str, Any]:
        return self.status_dict()

    def _finish_calibration(self, *, state: str, error: str = "") -> None:
        with self._calibration_state_lock:
            self._calibration_operation["state"] = state
            self._calibration_operation["finishedAt"] = int(time.time())
            self._calibration_operation["error"] = error
        self._calibration_lock.release()

    def _set_calibration_readiness(self, readiness: Any) -> None:
        with self._calibration_state_lock:
            self._calibration_operation["readiness"] = self._sanitize_readiness(readiness)

    @staticmethod
    def _sanitize_readiness(readiness: Any) -> dict[str, Any]:
        names = (
            "target_pid",
            "target_xid",
            "geometry",
            "synthetic_key_source",
            "synthetic_pointer_source",
            "xinput_hierarchy",
            "observed_monotonic",
        )
        result: dict[str, Any] = {}
        for name in names:
            value = getattr(readiness, name, None)
            if isinstance(value, tuple):
                value = list(value)
            elif isinstance(value, list):
                value = [list(item) if isinstance(item, tuple) else item for item in value]
            if isinstance(value, (str, int, float, bool)) or value is None or isinstance(value, list):
                result[name] = value
        result["ready"] = True
        return result

    def native_bootstrap(self, *, expected_generation: int | None = None) -> dict[str, Any]:
        """Capture the external absence boundary for the native calibration.

        This command only records the real, unconstructed client surface.  The
        runner samples the process HWM and publishes the externally visible
        ready boundary later, from ``_native_preconstruction_provider``.  That
        ordering keeps a caller from loading the addon before the baseline is
        actually bound to the absence proof.
        """

        with self.controller.lock:
            status = self.controller.status()
            if status.state != ControllerState.NATIVE_CALIBRATION:
                raise DriverError("native bootstrap requires NATIVE_CALIBRATION")
            if expected_generation is not None and status.generation != expected_generation:
                raise DriverError("native bootstrap generation was revoked")
        if not isinstance(self.driver.backend, X11Backend):
            raise DriverError("native bootstrap requires the configured X11 backend")
        with self._native_bootstrap_lock:
            if self._native_bootstrap_observation is not None:
                raise DriverError("native bootstrap is already pending consumption")
            identity = self.driver.resolve_identity()
            decoder = self.driver.new_native_decoder()
            if self._native_region_enabled():
                path = self._capture_native_region_for_identity(identity)
            else:
                path = self.driver.capture_client_crop_for_identity(identity)
            # Bind the absence proof to the instant the owned capture was
            # returned.  Retaining/copying the artifact and waiting for the
            # runner must never restamp the evidence as a newer observation.
            capture_observed = time.monotonic()
            retained: Path | None = None
            try:
                try:
                    sample = self.driver.decode_native_capture(path, identity=identity, decoder=decoder)
                except ProtocolError:
                    # Before Agent construction the calibrated crop is ordinary
                    # client pixels and cannot decode as CRS1.  Keep the actual
                    # absence crop until the runner binds the HWM baseline.
                    from PIL import Image

                    with Image.open(path) as image:
                        image.load()
                        if image.size != (
                            self.config.profile.canvas_crop[2],
                            self.config.profile.canvas_crop[3],
                        ):
                            raise DriverError(
                                "preconstruction capture has the wrong calibrated crop"
                            ) from None
                        encoded_grid = True
                        for y in range(128):
                            for x in range(128):
                                pixels = [
                                    image.getpixel((x * 2 + dx, y * 2 + dy))[:3]
                                    for dy in (0, 1)
                                    for dx in (0, 1)
                                ]
                                if len(set(pixels)) != 1 or pixels[0] not in {
                                    (0, 0, 0),
                                    (255, 255, 255),
                                }:
                                    encoded_grid = False
                                    break
                            if not encoded_grid:
                                break
                        if encoded_grid:
                            raise DriverError(
                                "preconstruction capture contains a malformed or stale status surface"
                            ) from None
                    sample = None
                if sample is not None:
                    raise DriverError("native surface is already constructed before bootstrap")
                evidence_dir = self.config.journal.expanduser().parent / "native-evidence"
                evidence_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
                os.chmod(evidence_dir, 0o700)
                retained = evidence_dir / f"preconstruction-{time.monotonic_ns()}.png"
                shutil.copyfile(path, retained)
                os.chmod(retained, 0o600)
                capture_digest = hashlib.sha256(retained.read_bytes()).hexdigest()
                self._native_owned_capture_paths.add(retained)
            except Exception:
                if retained is not None:
                    retained.unlink(missing_ok=True)
                raise
            finally:
                self._remove_native_capture(path)
            self._native_bootstrap_observation = {
                "identity": identity.fingerprint,
                "processStart": identity.process_start,
                "processExecutable": identity.executable,
                "display": identity.display,
                "windowXid": identity.xid,
                "childXid": identity.child_xid,
                "geometry": tuple(identity.child_geometry),
                "xauthority": self.driver.xauthority,
                "winePrefix": self.config.profile.wine_prefix,
                "captureDigest": capture_digest,
                "capturePath": str(retained),
                "surface": "absent",
                "capture": capture_observed,
                "provenance": "owned-live",
            }
            self._native_bootstrap_proof = None
            self._native_baseline_ready.clear()
            self._native_baseline_observation = None
        self._native_bootstrap_ready.set()
        return self.status_dict()

    def notify_native_baseline_ready(self, identity: WindowIdentity, baseline_hwm: int) -> None:
        """Publish the ready boundary after the runner sampled the HWM."""

        if not isinstance(baseline_hwm, int) or isinstance(baseline_hwm, bool) or baseline_hwm < 0:
            raise DriverError("native baseline HWM is not a valid nonnegative integer")
        with self.controller.lock:
            if self.controller.status().state != ControllerState.NATIVE_CALIBRATION:
                raise DriverError("native calibration generation was revoked")
        with self._native_bootstrap_lock:
            observation = self._native_bootstrap_observation
            if not observation or observation.get("identity") != identity.fingerprint:
                raise DriverError("native baseline-ready identity is stale")
            if observation.get("baselineHwm") is not None:
                raise DriverError("native baseline-ready boundary was already published")
            observation["baselineHwm"] = baseline_hwm
            self._native_baseline_observation = dict(observation)
            self._native_baseline_ready.set()
            self._native_handshake.update({"state": "bootstrap_ready", "failure": "", "restored": None})

    def notify_native_memory_ready(self, identity: WindowIdentity, pending: Any) -> None:
        """Bind the reset5 update window to the same live client identity."""

        with self.controller.lock:
            if self.controller.status().state != ControllerState.NATIVE_CALIBRATION:
                raise DriverError("native memory-ready generation was revoked")
        memory_meter = getattr(self.driver, "native_memory_meter", None)
        memory_executable = getattr(memory_meter, "process_executable", None)
        if not isinstance(memory_executable, str) or not memory_executable:
            raise DriverError("native reset5 memory executable is not available")
        if (
            getattr(pending, "pid", None) != identity.pid
            or getattr(pending, "process_start", None) != identity.process_start
            or getattr(pending, "process_executable", None) != memory_executable
            or getattr(pending, "identity_fingerprint", None) != identity.fingerprint
        ):
            raise DriverError("native memory-ready token is not bound to the client")
        if getattr(pending, "phase", None) != "updates" or getattr(pending, "ordinal", None) != 0:
            raise DriverError("native memory-ready token is not the held zero update boundary")
        self._native_handshake.update(
            {"state": "measure_ready", "measureReady": True, "failure": "", "restored": None}
        )

    def notify_native_memory_reset_ready(
        self, identity: WindowIdentity, record: Any
    ) -> NativeMemoryArchiveReceipt:
        """Bind the construction reset boundary before addon construction."""

        with self.controller.lock:
            if self.controller.status().state != ControllerState.NATIVE_CALIBRATION:
                raise DriverError("native construction reset generation was revoked")
        memory_meter = getattr(self.driver, "native_memory_meter", None)
        memory_executable = getattr(memory_meter, "process_executable", None)
        if not isinstance(memory_executable, str) or not memory_executable:
            raise DriverError("native reset5 memory executable is not available")
        if (
            getattr(record, "pid", None) != identity.pid
            or getattr(record, "process_start", None) != identity.process_start
            or getattr(record, "process_executable", None) != memory_executable
            or getattr(record, "identity_fingerprint", None) != identity.fingerprint
            or getattr(record, "phase", None) not in {"construction", "updates"}
            or getattr(record, "ordinal", None) != 0
        ):
            raise DriverError("native memory reset token is not bound to the client")
        # This callback is the reset5 meter's before-reset boundary.  The
        # historical accounting is journaled and fsynced before returning the
        # receipt; the meter will refuse to write clear_refs without it.
        to_dict = getattr(record, "to_dict", None)
        verify = getattr(record, "verify", None)
        if not callable(to_dict) or not callable(verify):
            raise DriverError("native reset callback received no complete reset record")
        verify()
        payload = to_dict()
        archive_id = hashlib.sha256(
            json.dumps(
                {"identity": identity.fingerprint, "record": payload},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.controller.journal.append_archive(
            "native_memory",
            {
                "archiveId": archive_id,
                "record": payload,
                "identity": identity.fingerprint,
            },
        )
        receipt = NativeMemoryArchiveReceipt.for_record(record, archive_id=archive_id)
        with self._native_bootstrap_lock:
            receipts = self._native_handshake.setdefault("archiveReceipts", [])
            receipts.append(
                {
                    "archiveId": receipt.archive_id,
                    "recordSha256": receipt.record_sha256,
                    "phase": payload.get("phase", ""),
                    "ordinal": payload.get("ordinal", 0),
                }
            )
            self._native_handshake["archiveReceipts"] = receipts[-4:]
            self._native_handshake["state"] = f"{payload.get('phase', 'native')}_reset_archived"
        return receipt

    def notify_native_hold_required(self, identity: WindowIdentity) -> None:
        """Confirm the native runner crossed its held zero boundary."""

        with self.controller.lock:
            if self.controller.status().state != ControllerState.NATIVE_CALIBRATION:
                raise DriverError("native hold boundary generation was revoked")
        if identity.fingerprint != self.driver.resolve_identity().fingerprint:
            raise DriverError("native hold boundary identity changed")
        self._native_handshake.update(
            {"state": "hold_required", "holdRequired": True, "failure": "", "restored": None}
        )

    def notify_native_resume_required(self, identity: WindowIdentity, boundary: Any) -> None:
        """Publish the validated held/100 boundary before requesting resume."""

        with self.controller.lock:
            if self.controller.status().state != ControllerState.NATIVE_CALIBRATION:
                raise DriverError("native resume-required generation was revoked")
        verify = getattr(boundary, "verify", None)
        if not callable(verify):
            raise DriverError("native resume-required boundary is not sealed")
        try:
            verify()
        except Exception as exc:
            raise DriverError("native resume-required boundary is invalid") from exc
        if (
            getattr(boundary, "identity_fingerprint", None) != identity.fingerprint
            or getattr(boundary, "process_start", None) != identity.process_start
            or getattr(boundary, "process_executable", None) != identity.executable
            or getattr(boundary, "phase", None) != "held"
            or getattr(boundary, "ordinal", None) != 100
            or not getattr(boundary, "boot", "")
            or getattr(boundary, "update_count", -1) < 0
        ):
            raise DriverError("native resume-required boundary identity or phase is stale")
        self._native_handshake.update(
            {
                "state": "resume_required",
                "resumeRequired": True,
                "resumeReady": False,
                "resumeBoundary": {
                    "identity": identity.fingerprint,
                    "boot": boundary.boot,
                    "sequence": boundary.sequence,
                    "updateCount": boundary.update_count,
                    "captureMonotonic": boundary.capture_monotonic,
                },
            }
        )

    def notify_native_resume_ready(
        self, identity: WindowIdentity, evidence: Any, resumed: Any | None = None
    ) -> None:
        """Accept the completed two-window native proof at the live boundary."""

        with self.controller.lock:
            if self.controller.status().state != ControllerState.NATIVE_CALIBRATION:
                raise DriverError("native resume-ready generation was revoked")
        if not self._native_handshake.get("resumeRequired"):
            raise DriverError("native resume-ready arrived before resume-required")
        if getattr(evidence, "native_identity_fingerprint", None) != identity.fingerprint:
            raise DriverError("native resume-ready evidence identity is stale")
        if getattr(evidence, "process_pid", None) != identity.pid:
            raise DriverError("native resume-ready evidence PID changed")
        if resumed is None or getattr(resumed, "native_phase", None) != "normal":
            raise DriverError("native resume-ready observation is missing normal phase")
        if getattr(resumed, "native_ordinal", None) != 0:
            raise DriverError("native resume-ready observation is not ordinal zero")
        resumed_metrics = getattr(resumed, "metrics", {})
        boundary = self._native_handshake.get("resumeBoundary", {})
        if (
            not isinstance(resumed_metrics, dict)
            or resumed_metrics.get("nativePhase") != "normal"
            or resumed_metrics.get("nativeOrdinal") != 0
            or resumed_metrics.get("updateCount", -1) <= boundary.get("updateCount", -1)
            or getattr(resumed, "identity_fingerprint", None) != identity.fingerprint
            or getattr(resumed, "boot", None) != boundary.get("boot")
            or getattr(resumed, "sequence", 0) <= boundary.get("sequence", 0)
        ):
            raise DriverError("native resume-ready observation is not a fresh same-boot proof")
        evidence_resume_count = getattr(evidence, "resume_update_count", None)
        if evidence_resume_count != resumed_metrics.get("updateCount"):
            raise DriverError("native resume-ready evidence count does not match the observation")
        self._native_handshake.update(
            {"state": "resume_ready", "resumeReady": True, "failure": "", "restored": True}
        )

    def notify_native_measurement_failed(
        self, identity: WindowIdentity, reason: str
    ) -> NativeRestorationReceipt:
        if identity.fingerprint != self.driver.resolve_identity().fingerprint:
            raise DriverError("native failure identity changed")
        message = str(reason) or "native measurement failed"
        self.controller.journal.append_archive(
            "interventions",
            {
                "kind": "native_restoration_required",
                "identity": identity.fingerprint,
                "reason": message,
                "durable": True,
            },
        )
        receipt = NativeRestorationReceipt("restoration_required", False, message, durable=True)
        receipt.verify()
        self._native_handshake.update(
            {
                "state": "restoration_required",
                "failure": message,
                "restored": False,
                "holdRequired": False,
                "measureReady": False,
                "resumeRequired": False,
                "resumeReady": False,
            }
        )
        return receipt

    def _ensure_native_memory_meter(self) -> LinuxProcStatusVmHwmReset5 | None:
        """Open the default reset5 meter only for a fresh verified client."""

        if self.driver.native_memory_meter is not None:
            return None
        if not isinstance(self.driver.backend, X11Backend):
            raise DriverError("native reset5 memory meter requires the configured X11 backend")
        identity = self.driver.resolve_identity()
        try:
            linux_executable = os.path.realpath(os.readlink(f"/proc/{identity.pid}/exe"))
        except OSError as exc:
            raise DriverError("native process Linux executable is unavailable") from exc
        if not linux_executable or not Path(linux_executable).is_absolute():
            raise DriverError("native process Linux executable is incomplete")
        meter = LinuxProcStatusVmHwmReset5(
            identity.pid,
            process_start=identity.process_start,
            process_executable=linux_executable,
            identity_fingerprint=identity.fingerprint,
            expected_uid=os.getuid(),
            monotonic=self._native_clock,
        )
        self.driver.native_memory_meter = meter
        return meter

    def _native_preconstruction_provider(
        self,
        identity: WindowIdentity,
        *,
        baseline_reader: Any,
        baseline_ready: Any,
    ) -> NativePreconstructionEvidence:
        if not callable(baseline_reader) or not callable(baseline_ready):
            raise DriverError("native preconstruction baseline callbacks are required")
        if self._shutdown_event.is_set():
            raise DriverError("native calibration was canceled during shutdown")
        with self.controller.lock:
            if self.controller.status().state != ControllerState.NATIVE_CALIBRATION:
                raise DriverError("native calibration generation was revoked")
        if not self._native_bootstrap_ready.is_set():
            raise DriverError("external preconstruction bootstrap handshake is not ready")
        with self._native_bootstrap_lock:
            observation = self._native_bootstrap_observation
            if not observation or observation.get("identity") != identity.fingerprint:
                raise DriverError("preconstruction bootstrap identity is stale")
            if time.monotonic() - float(observation.get("capture", 0)) > 10.0:
                raise DriverError("preconstruction bootstrap observation is stale")
            capture_path = Path(str(observation.get("capturePath", "")))
            capture_sha256 = str(observation.get("captureDigest", ""))
            if not capture_path.is_absolute() or not capture_path.is_file():
                raise DriverError("preconstruction absence capture is unavailable")
            if hashlib.sha256(capture_path.read_bytes()).hexdigest() != capture_sha256:
                raise DriverError("preconstruction absence capture changed")
            # The runner's baseline reader is deliberately called only after
            # the real capture has proved that Agent is absent.  The ready
            # callback then publishes the externally visible load boundary.
            baseline_hwm = baseline_reader(identity.pid)
            if not isinstance(baseline_hwm, int) or isinstance(baseline_hwm, bool) or baseline_hwm < 0:
                raise DriverError("native baseline reader returned an invalid HWM")
            baseline_ready(identity.pid, baseline_hwm)
            if observation.get("baselineHwm") != baseline_hwm:
                raise DriverError("native baseline-ready callback did not publish the measured HWM")
            # The absence capture predates the reset.  Construction timing
            # begins only after the baseline-ready publication has crossed the
            # reset receipt boundary, so seal this release instant separately.
            bootstrap_release = time.monotonic()
            evidence = NativePreconstructionEvidence._issue(
                identity_fingerprint=identity.fingerprint,
                process_start=identity.process_start,
                absent=True,
                baseline_id=capture_sha256,
                # Preserve the timestamp of the absence capture itself.  The
                # baseline-ready publication below is a distinct boundary;
                # the runner uses it as construction work's start time.
                observed_monotonic=float(observation["capture"]),
                bootstrap_release_monotonic=bootstrap_release,
                display=identity.display,
                process_executable=identity.executable,
                window_xid=identity.xid,
                child_xid=identity.child_xid,
                geometry=identity.child_geometry,
                xauthority=self.driver.xauthority,
                wine_prefix=self.config.profile.wine_prefix,
                baseline_hwm_bytes=baseline_hwm,
                capture_path=str(capture_path),
                capture_sha256=capture_sha256,
            )
            self._native_bootstrap_proof = {
                "identityFingerprint": evidence.identity_fingerprint,
                "processStart": evidence.process_start,
                "processExecutable": evidence.process_executable,
                "display": evidence.display,
                "absent": evidence.absent,
                "baselineId": evidence.baseline_id,
                "baselineHwmBytes": evidence.baseline_hwm_bytes,
                "windowXid": evidence.window_xid,
                "childXid": evidence.child_xid,
                "geometry": list(evidence.geometry),
                "xauthority": evidence.xauthority,
                "winePrefix": evidence.wine_prefix,
                "observedMonotonic": evidence.observed_monotonic,
                "bootstrapReleaseMonotonic": evidence.bootstrap_release_monotonic,
                "capturePath": evidence.capture_path,
                "captureSha256": evidence.capture_sha256,
                "provenance": evidence.provenance,
                "fingerprint": evidence.fingerprint,
                "evidenceHash": evidence.evidence_hash,
            }
            self._native_bootstrap_observation = None
            self._native_bootstrap_ready.clear()
            return evidence

    def request_shutdown(self) -> None:
        """Stop supervision and revoke any desktop work before IPC exits."""

        self._shutdown_event.set()
        failures: list[BaseException] = []
        try:
            self.model.shutdown()
        except BaseException as exc:
            failures.append(exc)
        try:
            close = getattr(self.driver, "close", None)
            if callable(close):
                close()
            else:
                self.driver.revoke("session supervisor stopped")
        except BaseException as exc:
            failures.append(exc)
        thread = self._calibration_thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=5)
            if thread.is_alive():
                failures.append(RuntimeError("calibration worker did not terminate during shutdown"))
        keep_capture = None
        try:
            stored = self.controller.journal.read().get("calibrationEvidence", {})
            native_record = stored.get("native", {}) if isinstance(stored, dict) else {}
            if isinstance(native_record, dict):
                keep_capture = native_record.get("capture_path")
        except Exception:
            failures.append(RuntimeError("could not inspect durable native evidence during shutdown"))
        self._cleanup_native_owned_captures(keep=keep_capture)
        if failures:
            raise RuntimeError("session owner shutdown did not complete") from failures[0]

    @staticmethod
    def _remove_native_capture(path: Any) -> None:
        """Remove the crop and source emitted by one private native capture."""

        if not hasattr(path, "unlink"):
            return
        try:
            path.unlink()
        except OSError:
            pass
        parent = getattr(path, "parent", None)
        if parent is None:
            return
        # ``capture_client_crop_for_identity`` emits these two files in a
        # temporary directory.  Removing only the crop leaves desktop.png
        # behind and leaks one directory per native-gate frame.
        for name in ("desktop.png", "desktop.crop.png"):
            sibling = parent / name
            if sibling == path:
                continue
            try:
                sibling.unlink()
            except OSError:
                pass
        try:
            parent.rmdir()
        except OSError:
            pass

    def release_native_capture(self, path: Any) -> None:
        """Release one provider artifact after the native runner consumed it."""

        try:
            candidate = Path(os.fspath(path))
        except TypeError as exc:
            raise DriverError("native capture release requires a filesystem path") from exc
        with self._native_bootstrap_lock:
            self._native_owned_capture_paths.discard(candidate)
        self._remove_native_capture(candidate)

    def _cleanup_native_owned_captures(self, *, keep: Any | None = None) -> None:
        """Release provider-owned artifacts after the native runner finishes."""

        paths = set(self._native_owned_capture_paths)
        self._native_owned_capture_paths.clear()
        keep_path = os.fspath(keep) if keep is not None else None
        for path in paths:
            if keep_path is not None and os.fspath(path) == keep_path:
                self._native_owned_capture_paths.add(path)
                continue
            self._remove_native_capture(path)

    def _capture_native_frame_with_capture(
        self,
        identity: WindowIdentity,
        decoder: PixelDecoder,
        *,
        deadline: float | None = None,
    ) -> tuple[Sample, str, Any]:
        capture_started = self._native_clock()
        path = self._capture_native_region_for_identity(identity, deadline=deadline)
        retained = None
        try:
            if deadline is not None:
                self._remaining_motion_budget(deadline)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            sample = self.driver.decode_native_capture(path, identity=identity, decoder=decoder)
            # Decoder timestamps are publication/return times.  Freshness for
            # native consumers must instead describe when this capture was
            # admitted, before the potentially slow crop/decode path began.
            sample = replace(sample, capture_monotonic=capture_started)
            if deadline is not None:
                self._remaining_motion_budget(deadline)
            # NativeCalibrationEvidence retains the final decoded crop for
            # post-review verification.  The backend's default temporary
            # capture directory is unsuitable for that durable proof, so
            # copy each provider artifact into a private persistent evidence
            # directory before returning it to the native runner.  The runner
            # then decodes and seals this exact retained path/hash.
            evidence_dir = self.config.journal.expanduser().parent / "native-evidence"
            evidence_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.chmod(evidence_dir, 0o700)
            retained = evidence_dir / f"capture-{time.monotonic_ns()}-{self.capture_index:08d}.png"
            shutil.copyfile(path, retained)
            os.chmod(retained, 0o600)
            self._remove_native_capture(path)
            self._native_owned_capture_paths.add(retained)
            return sample, digest, retained
        except Exception:
            self._remove_native_capture(path)
            if retained is not None:
                try:
                    retained.unlink()
                except OSError:
                    pass
            raise

    def _capture_native_frame_with_digest(
        self,
        identity: WindowIdentity,
        decoder: PixelDecoder,
        *,
        deadline: float | None = None,
    ) -> tuple[Sample, str]:
        sample, digest, path = self._capture_native_frame_with_capture(identity, decoder, deadline=deadline)
        try:
            return sample, digest
        finally:
            self.release_native_capture(path)

    def _capture_native_frame(
        self,
        identity: WindowIdentity,
        decoder: PixelDecoder,
        *,
        deadline: float | None = None,
    ) -> Sample:
        sample, _digest = self._capture_native_frame_with_digest(identity, decoder, deadline=deadline)
        return sample

    def _native_measurement_provider(
        self, identity: WindowIdentity, stage: str, ordinal: int
    ) -> NativeRenderObservation:
        """Wait for one actual, identity-bound Agent publication.

        Readiness callbacks are signals only.  The authorized operator drives
        ``/crowley agent hold|measure|resume`` in the game, and this producer
        polls the real status surface until that action publishes the requested
        fresh frame.  Once update 1 arrives, every later ordinal is exact.
        """

        if stage not in {"construct", "held", "updates", "resume"}:
            raise DriverError(f"unknown native measurement stage {stage!r}")
        expected_phase, expected_ordinal = {
            "construct": ("normal", 0),
            "held": ("held", ordinal),
            "updates": ("updates", ordinal),
            "resume": ("normal", 0),
        }[stage]
        if stage == "updates" and not 1 <= ordinal <= 99:
            raise DriverError("native update ordinal must be in 1..99")
        if stage == "held" and ordinal not in {0, 100}:
            raise DriverError("native held ordinal must be zero or one hundred")
        if stage in {"construct", "resume"} and ordinal != 0:
            raise DriverError(f"native {stage} ordinal must be zero")
        if self._shutdown_event.is_set():
            raise DriverError("native calibration was canceled during shutdown")
        with self.controller.lock:
            live_status = self.controller.status()
            if live_status.state != ControllerState.NATIVE_CALIBRATION:
                raise DriverError("native calibration generation was revoked")
            generation = live_status.generation
        state = self._native_measurement_state
        if stage == "construct":
            decoder = self.driver.new_native_decoder()
            prior_sequence: int | None = None
            expected_boot: str | None = None
        else:
            if (
                state is None
                or state.get("identity") != identity.fingerprint
                or state.get("generation") != generation
            ):
                raise DriverError(f"native {stage} has no matching construction identity")
            decoder = state["decoder"]
            prior_sequence = int(state["sequence"])
            expected_boot = str(state["boot"])

        deadline = self._native_clock() + self._NATIVE_FRAME_TIMEOUT_SECONDS
        accepted: tuple[Sample, str, Any] | None = None
        while self._native_clock() < deadline:
            self._check_native_poll_identity(identity, generation)
            try:
                candidate, candidate_id, candidate_path = self._capture_native_frame_with_capture(
                    identity, decoder
                )
            except ProtocolError:
                # Before Agent construction the crop is ordinary game pixels.
                # Keep polling until the operator has loaded the addon, then
                # fail closed at the bounded deadline if no valid frame arrives.
                if stage == "construct":
                    time.sleep(self._NATIVE_POLL_INTERVAL_SECONDS)
                    continue
                raise
            if candidate.kind != "FRESH" or candidate.frame is None:
                self.release_native_capture(candidate_path)
                time.sleep(self._NATIVE_POLL_INTERVAL_SECONDS)
                continue
            frame = candidate.frame
            render = frame.snapshot.value.get("render")
            if not isinstance(render, dict):
                self.release_native_capture(candidate_path)
                raise DriverError("native frame has no render metrics")
            actual_phase = render.get("nativePhase")
            actual_ordinal = render.get("nativeOrdinal")
            if expected_boot is not None and frame.boot != expected_boot:
                self.release_native_capture(candidate_path)
                raise DriverError(f"native {stage} frame boot changed during operator wait")
            if prior_sequence is not None and frame.sequence <= prior_sequence:
                self.release_native_capture(candidate_path)
                time.sleep(self._NATIVE_POLL_INTERVAL_SECONDS)
                continue

            if (actual_phase, actual_ordinal) == (expected_phase, expected_ordinal):
                if stage == "construct":
                    # A character-select/disconnected frame must never become
                    # the construction proof, even if it carries Agent data.
                    self._validate_identity(frame.snapshot.value, state=ControllerState.NATIVE_CALIBRATION)
                accepted = (candidate, candidate_id, candidate_path)
                break

            # Hold-required may see normal/0 while the operator reacts;
            # measure-ready may still see held/0 until Measure is issued; and
            # resume-required may see held/100 until Resume is issued.
            waitable = (
                (stage == "held" and ordinal == 0 and (actual_phase, actual_ordinal) == ("normal", 0))
                or (stage == "updates" and ordinal == 1 and (actual_phase, actual_ordinal) == ("held", 0))
                or (stage == "resume" and (actual_phase, actual_ordinal) == ("held", 100))
            )
            self.release_native_capture(candidate_path)
            if waitable:
                time.sleep(self._NATIVE_POLL_INTERVAL_SECONDS)
                continue
            raise DriverError(f"native {stage}/{ordinal} returned {actual_phase!r}/{actual_ordinal!r}")

        if accepted is None:
            raise DriverError(f"native {stage}/{ordinal} did not produce the requested fresh frame")
        sample, capture_id, capture_path = accepted
        assert sample.frame is not None
        if sample.capture_monotonic < 0:
            self.release_native_capture(capture_path)
            raise DriverError(f"native {stage} capture timestamp is invalid")
        render = sample.frame.snapshot.value.get("render")
        assert isinstance(render, dict)
        if stage == "construct":
            self._native_measurement_state = {
                "identity": identity.fingerprint,
                "decoder": decoder,
                "boot": sample.frame.boot,
                "sequence": sample.frame.sequence,
                "captureMonotonic": sample.capture_monotonic,
                "generation": generation,
            }
        else:
            assert state is not None
            state["sequence"] = sample.frame.sequence
            state["captureMonotonic"] = sample.capture_monotonic
        return NativeRenderObservation(
            metrics=dict(render),
            identity_fingerprint=identity.fingerprint,
            boot=sample.frame.boot,
            sequence=sample.frame.sequence,
            crc32=sample.frame.crc32,
            capture_id=capture_id,
            capture_path=str(capture_path),
            capture_sha256=capture_id,
            capture_monotonic=sample.capture_monotonic,
            native_phase=render.get("nativePhase"),
            native_ordinal=render.get("nativeOrdinal"),
        )

    def _check_native_poll_identity(self, identity: WindowIdentity, generation: int) -> None:
        if self._shutdown_event.is_set():
            raise DriverError("native calibration was canceled during operator wait")
        if self.driver.resolve_identity().fingerprint != identity.fingerprint:
            raise DriverError("native client identity changed during operator wait")
        with self.controller.lock:
            status = self.controller.status()
            if status.state != ControllerState.NATIVE_CALIBRATION or status.generation != generation:
                raise DriverError("native calibration generation was revoked")

    def _measure_pointer_anchor(self, identity: WindowIdentity, action: str) -> MeasuredAnchor:
        """Measure one named control from one fresh owned-client visual.

        The native driver owns capture admission and dispatch.  This method is
        the semantic producer: Luna reports facts and bounds from the captured
        client crop, and this method binds those values to the verified client
        identity before handing them back to the native driver.  A configured
        external provider remains usable for a separately owned native test
        boundary, but no backend method or profile coordinate is consulted.
        """

        controls = getattr(self.driver, "ANCHOR_CONTROLS", {})
        expected_control = controls.get(action)
        if not isinstance(expected_control, str) or not expected_control:
            raise DriverError(f"no named visual control contract exists for {action!r}")

        # A native worker may provide the capture/sealing half of this
        # contract.  It must already return a complete evidence record; this
        # path deliberately does not ask a backend for coordinates.
        provider = self._configured_anchor_provider
        if callable(provider):
            try:
                anchor = provider(identity, action)
            except Exception as exc:
                raise DriverError(f"native control-anchor measurement failed for {action}: {exc}") from exc
            if not isinstance(anchor, MeasuredAnchor):
                raise DriverError("native anchor producer returned unbound coordinate evidence")
            if (
                anchor.action != action
                or anchor.identity_fingerprint != identity.fingerprint
                or anchor.generation != self.driver.guardian.generation
                or dict(anchor.facts).get("control") != expected_control
                or dict(anchor.facts).get("capture") != anchor.capture_id
                or dict(anchor.facts).get("target") != str(anchor.target_xid)
            ):
                raise DriverError("native control-anchor identity, action, or control does not match")
            return anchor

        expected_state = {
            "dismiss_disconnect": "disconnect_dialog",
            "reconnect_game": "game_client",
            "select_arthur": "character_select",
            "enter_world": "arthur_selected",
            "open_ah": "world",
            "logout": "world",
        }.get(action)
        if expected_state is None:
            raise DriverError(f"action {action!r} has no visual anchor scene")

        with self.controller.lock:
            status = self.controller.status()
            generation = status.generation
            state_before = status.state
        guardian_generation = self.driver.guardian.generation
        if not self.driver.guardian.armed or guardian_generation <= 0:
            raise DriverError("visual anchor requires the current armed input lease")

        before = self.driver.resolve_identity()
        if before.fingerprint != identity.fingerprint:
            raise DriverError("anchor capture started with a stale client identity")

        capture_path: Path | None = None
        model_started = time.monotonic()
        captured_at = model_started
        proof: dict[str, Any] = {
            "action": action,
            "control": expected_control,
            "scene": expected_state,
            "generation": generation,
            "leaseGeneration": guardian_generation,
            "identity": identity.fingerprint,
            "accepted": False,
            "captureMonotonic": captured_at,
        }
        try:
            anchor_deadline = time.monotonic() + 5.0
            capture_path, digest, captured_at = self._capture_model_artifact(
                identity, generation, deadline=anchor_deadline
            )
            proof.update(
                {
                    "capturePath": str(capture_path),
                    "captureSha256": digest,
                    "captureId": digest,
                    "captureSequence": self._named_capture_sequence,
                    "captureMonotonic": captured_at,
                }
            )
            anchor_remaining = anchor_deadline - time.monotonic()
            if anchor_remaining <= 0:
                raise DriverError("visual control anchor exceeded its bounded deadline")
            observation = self._observe_model(
                capture_path.read_bytes(),
                timeout=anchor_remaining,
                requested_state=expected_state,
                requested_control=expected_control,
            )
            model_finished = time.monotonic()
            proof["modelTiming"] = {
                "startedMonotonic": model_started,
                "finishedMonotonic": model_finished,
                "durationSeconds": model_finished - model_started,
            }
            after = self.driver.resolve_identity()
            if after.fingerprint != identity.fingerprint:
                raise DriverError("client identity changed during visual anchor inference")
            if model_finished > anchor_deadline or model_finished - captured_at > 5.0:
                raise DriverError("visual control anchor inference exceeded the freshness deadline")
            if observation.state != expected_state:
                raise DriverError(
                    f"visual anchor reported {observation.state!r}, expected {expected_state!r}"
                )
            facts = dict(observation.facts)
            expected = self._named_facts(
                expected_state,
                character=self.config.profile.character,
                realm=self.config.profile.realm,
                idle="true",
            )
            expected["control"] = expected_control
            if facts != expected:
                raise DriverError(f"visual control facts did not match {action}: {facts!r}")
            bounds = observation.anchor
            if bounds is None:
                raise DriverError("visual control observation did not include measured bounds")
            x, y, width, height = bounds
            crop_x, crop_y, crop_width, crop_height = self.config.profile.model_crop
            if (
                width <= 0
                or height <= 0
                or x < 0
                or y < 0
                or x + width > crop_width
                or y + height > crop_height
            ):
                raise DriverError("visual control bounds are outside the verified model crop")
            client_bounds = (crop_x + x, crop_y + y, width, height)
            anchor_x = client_bounds[0] + width // 2
            anchor_y = client_bounds[1] + height // 2
            if not (
                0 <= anchor_x < identity.child_geometry[2] and 0 <= anchor_y < identity.child_geometry[3]
            ):
                raise DriverError("visual control anchor is outside the verified client child")
            self._named_capture_sequence += 1
            capture_id = digest
            facts["capture"] = capture_id
            facts["target"] = str(identity.child_xid)
            facts["captureMonotonic"] = str(captured_at)
            facts["modelDurationSeconds"] = str(model_finished - model_started)
            target_ancestry = (
                (identity.xid, identity.child_xid)
                if isinstance(self.driver.backend, X11Backend)
                else (identity.child_xid,)
            )
            anchor = self.driver.build_measured_anchor(
                action=action,
                x=anchor_x,
                y=anchor_y,
                capture_path=capture_path,
                capture_id=capture_id,
                capture_sequence=self._named_capture_sequence,
                capture_monotonic=captured_at,
                scene=expected_state,
                bounds=client_bounds,
                target_xid=identity.child_xid,
                target_ancestry=target_ancestry,
                generation=guardian_generation,
                source="native-visual",
                facts=tuple(sorted(facts.items())),
            )
            proof.update(
                {
                    "accepted": True,
                    "captureSequence": anchor.capture_sequence,
                    "bounds": list(anchor.bounds),
                    "targetXid": anchor.target_xid,
                    "targetAncestry": list(anchor.target_ancestry),
                    "evidenceHash": anchor.evidence_hash,
                }
            )
            self._record_visual_proof(proof, generation=generation, state=state_before)
            return anchor
        except Exception:
            proof.setdefault(
                "modelTiming",
                {
                    "startedMonotonic": model_started,
                    "finishedMonotonic": time.monotonic(),
                },
            )
            self._record_visual_proof(proof, generation=generation, state=state_before)
            raise

    def _capture_model_artifact(
        self,
        identity: WindowIdentity,
        generation: int,
        *,
        deadline: float | None = None,
    ) -> tuple[Path, str, float]:
        """Retain one lossless model crop before a visual anchor is sealed."""

        if deadline is not None and time.monotonic() >= deadline:
            raise DriverError("visual control anchor exceeded its bounded deadline")
        self.config.capture_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.config.capture_dir, 0o700)
        self.capture_index += 1
        source = self.config.capture_dir / f"anchor-{generation}-{self.capture_index:08d}.png"
        cropped: Path | None = None
        try:
            cropped = self._capture_client_crop(source, model=True, deadline=deadline)
            captured_at = time.monotonic()
            if deadline is not None and captured_at >= deadline:
                raise DriverError("visual control capture exceeded its bounded deadline")
            current = self._resolve_identity(deadline=deadline)
            if current.fingerprint != identity.fingerprint:
                raise DriverError("model capture identity changed before inference")
            evidence_dir = self.config.journal.expanduser().parent / "model-evidence"
            evidence_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.chmod(evidence_dir, 0o700)
            retained = evidence_dir / f"anchor-{generation}-{self.capture_index:08d}.png"
            shutil.copyfile(cropped, retained)
            os.chmod(retained, 0o600)
            digest = hashlib.sha256(retained.read_bytes()).hexdigest()
            if deadline is not None and time.monotonic() >= deadline:
                raise DriverError("visual control evidence exceeded its bounded deadline")
            return retained, digest, captured_at
        except Exception:
            if cropped is not None:
                cropped.unlink(missing_ok=True)
            source.unlink(missing_ok=True)
            raise
        finally:
            if cropped is not None:
                cropped.unlink(missing_ok=True)
            source.unlink(missing_ok=True)

    def _record_visual_proof(self, proof: dict[str, Any], *, generation: int, state: ControllerState) -> None:
        """Archive model and anchor acceptance without hiding the action error."""

        try:
            with self.controller.lock:
                current = self.controller.status()
            if current.generation != generation or current.state != state:
                return
            self.controller.record_model_proof(
                proof,
                expected_generation=generation,
                expected_state=state,
            )
            self.controller.record_anchor_proof(
                proof,
                expected_generation=generation,
                expected_state=state,
            )
        except (AttributeError, DriverError, OSError, RuntimeError, ValueError):
            # Proof archival must never turn a successfully sealed anchor into
            # an unbound coordinate; the native driver remains the admission
            # authority.  The immutable capture is retained for later review.
            return

    @staticmethod
    def _named_facts(state: str, *, character: str, realm: str, idle: str) -> dict[str, str]:
        facts = {
            "disconnect_dialog": {
                "scene": "disconnect_dialog",
                "character": "",
                "realm": "",
                "modal": "WOW51900319",
                "code": "WOW51900319",
                "control": "dismiss_disconnect",
                "idle": "false",
            },
            "game_client": {
                "scene": "game_client",
                "character": "",
                "realm": "",
                "modal": "none",
                "code": "",
                "control": "client",
                "idle": "false",
            },
            "character_select": {
                "scene": "character_select",
                "character": character,
                "realm": realm,
                "modal": "character_select",
                "code": "",
                "control": "character_list",
                "idle": idle,
            },
            "arthur_selected": {
                "scene": "character_select",
                "character": character,
                "realm": realm,
                "modal": "character_select",
                "code": "",
                "control": "arthur_row",
                "idle": idle,
            },
            "world": {
                "scene": "world",
                "character": character,
                "realm": realm,
                "modal": "none",
                "code": "",
                "control": "world",
                "idle": idle,
            },
            "auction_house_open": {
                "scene": "world",
                "character": character,
                "realm": realm,
                "modal": "auction_house",
                "code": "",
                "control": "auctioneer_buckler",
                "idle": idle,
            },
        }
        try:
            return facts[state]
        except KeyError as exc:
            raise DriverError(f"unknown named observation state {state!r}") from exc

    def _check_named_facts(self, state: str, facts: dict[str, str]) -> None:
        expected = self._named_facts(
            state,
            character=self.config.profile.character,
            realm=self.config.profile.realm,
            idle="true",
        )
        if facts != expected:
            raise DriverError(f"named visual facts did not match {state}: {facts!r}")

    @staticmethod
    def _scanner_idle_ready(snapshot: dict[str, Any], expected_uid: str = "") -> bool:
        """Prove the scanner is in an explicit idle phase for closeout."""

        pending = snapshot.get("pending", {})
        pending_ids = pending.get("ids", []) if isinstance(pending, dict) else []
        if pending_ids:
            return False
        scanner = snapshot.get("scanner", {})
        if not isinstance(scanner, dict) or scanner.get("activeSweepId"):
            return False
        if scanner.get("phase") not in {"ready", "scheduled"}:
            return False
        if expected_uid:
            saved = snapshot.get("lastSaved", {})
            if not isinstance(saved, dict) or saved.get("memoryUid") != expected_uid:
                return False
        return True

    @staticmethod
    def _logout_scanner_idle(snapshot: dict[str, Any], expected_uid: str = "") -> bool:
        """Prove that a final logout cannot race a newly started sweep.

        The closeout caller supplies a fresh post-ack frame and the caller's
        pre-logout schedule fence rejects any item/owned frame before this
        predicate is reached.  Only the addon's explicit idle phases are a
        valid logout witness.  ``activeSweepId`` is intentionally checked
        independently because the scanner can keep it empty during a live
        item phase.
        """

        if not SessionDaemon._scanner_idle_ready(snapshot, expected_uid):
            return False
        scanner = snapshot.get("scanner", {})
        if not isinstance(scanner, dict):
            return False
        fence = scanner.get("scheduleFence")
        return fence == {
            "state": "armed",
            "reason": "",
            "command": "/crowley session fence",
        }

    def _observe_addon_state(self, identity: WindowIdentity, state: str) -> NamedStateObservation:
        decoder = self.driver.new_native_decoder()
        baseline = self._last_addon_sequence
        named_deadline = getattr(self, "_named_observation_deadline", None)
        deadline = min(
            time.monotonic() + 8.0,
            named_deadline if isinstance(named_deadline, (int, float)) else float("inf"),
        )
        while time.monotonic() < deadline:
            sample = self._capture_native_frame(identity, decoder, deadline=deadline)
            if sample.kind != "FRESH" or sample.frame is None:
                time.sleep(0.05)
                continue
            frame = sample.frame
            # Sequence numbers are only ordered within one addon boot.  A
            # world transition legitimately publishes a fresh boot starting
            # at sequence one; comparing that counter with the prior menu
            # boot would wait forever for an impossible value.
            if frame.boot == self._last_addon_boot and frame.sequence <= baseline:
                time.sleep(0.05)
                continue
            snapshot = frame.snapshot.value
            context = snapshot.get("context", {})
            if (
                context.get("character") != self.config.profile.character
                or context.get("realm") != self.config.profile.realm
            ):
                raise DriverError("fresh addon observation has the wrong character or realm")
            ah_open = snapshot.get("ahOpen") is True
            if state == "auction_house_open" and not ah_open:
                time.sleep(0.05)
                continue
            if state == "world" and ah_open:
                time.sleep(0.05)
                continue
            # Telemetry proves the exact configured identity and AH boolean;
            # the visual observer independently proves the visible scene,
            # modal, control, and idle facts.  Neither source is allowed to
            # manufacture the other's fields.
            try:
                visual_image = self._capture_model(deadline=deadline)
                visual_remaining = deadline - time.monotonic()
                if visual_remaining <= 0:
                    continue
            except DriverError:
                break
            visual = self._observe_model(
                visual_image,
                timeout=min(5.0, visual_remaining),
            )
            if time.monotonic() > deadline:
                raise DriverError("visual addon-state inference exceeded the freshness deadline")
            after_model = self._resolve_identity(deadline=deadline)
            if after_model.fingerprint != identity.fingerprint:
                raise DriverError("client identity changed during addon-state inference")
            expected_visual_state = "auction_house_open" if state == "auction_house_open" else "world"
            if visual.state != expected_visual_state:
                time.sleep(0.05)
                continue
            facts = dict(visual.facts)
            self._check_named_facts(state, facts)
            # The model may spend seconds on one crop.  Read telemetry again
            # after inference and bind the returned observation to that fresh
            # boot/sequence instead of resetting the timestamp to ``now``.
            after_sample = self._capture_native_frame(identity, decoder, deadline=deadline)
            if (
                after_sample.kind != "FRESH"
                or after_sample.frame is None
                or after_sample.frame.boot != frame.boot
                or after_sample.frame.sequence <= frame.sequence
                or after_sample.capture_monotonic <= sample.capture_monotonic
            ):
                continue
            self._last_addon_sequence = after_sample.frame.sequence
            self._last_addon_boot = after_sample.frame.boot
            # Keep the named-observation sequence in one monotonic namespace
            # across addon-backed and model-backed scenes.  A later visual
            # postcondition must not appear older merely because it uses the
            # model capture path.
            self._named_capture_sequence = max(self._named_capture_sequence, after_sample.frame.sequence)
            return NamedStateObservation.from_facts(
                state=state,
                identity_fingerprint=identity.fingerprint,
                target_xid=identity.child_xid,
                capture_id=(
                    f"addon+visual:{after_sample.frame.boot}:{after_sample.frame.sequence}:"
                    f"{after_sample.frame.crc32:08x}:"
                    f"{hashlib.sha256(visual_image).hexdigest()}"
                ),
                capture_sequence=after_sample.frame.sequence,
                facts=facts,
                source="native-addon",
                observed_monotonic=after_sample.capture_monotonic,
                boot=after_sample.frame.boot,
            )
        raise DriverError(f"fresh addon observation for {state} did not arrive")

    def _observe_named_state(self, identity: WindowIdentity, state: str) -> NamedStateObservation:
        if state in {"world", "auction_house_open"}:
            return self._observe_addon_state(identity, state)
        named_deadline = getattr(self, "_named_observation_deadline", None)
        deadline = min(
            time.monotonic() + 5.0,
            named_deadline if isinstance(named_deadline, (int, float)) else float("inf"),
        )
        capture_started = time.monotonic()
        image = self._capture_model(deadline=deadline)
        # Keep freshness anchored to the start of the native crop capture;
        # using the return time would make a slow capture appear newer than
        # the evidence admitted at its beginning.  Deadline accounting still
        # uses the actual return clock below.
        captured_at = capture_started
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise DriverError("visual named-state capture exceeded its bounded deadline")
        observation = self._observe_model(
            image,
            timeout=remaining,
        )
        if time.monotonic() > deadline:
            raise DriverError("visual named-state inference exceeded the freshness deadline")
        current = self._resolve_identity(deadline=deadline)
        if current.fingerprint != identity.fingerprint:
            raise DriverError("client identity changed during named-state inference")
        if observation.state != state:
            raise DriverError(f"fresh visual observation reported {observation.state!r}, expected {state!r}")
        self._check_named_facts(state, observation.facts)
        self._named_capture_sequence += 1
        return NamedStateObservation.from_facts(
            state=state,
            identity_fingerprint=identity.fingerprint,
            target_xid=identity.child_xid,
            capture_id=(
                f"visual:{self.capture_index}:{self._named_capture_sequence}:"
                f"{hashlib.sha256(image).hexdigest()}"
            ),
            capture_sequence=self._named_capture_sequence,
            facts=observation.facts,
            source="native-visual",
            observed_monotonic=captured_at,
            boot="",
        )

    def _resolve_identity(
        self,
        *,
        require_foreground: bool = True,
        deadline: float | None = None,
    ) -> WindowIdentity:
        """Resolve the live client identity under the caller's deadline.

        The production driver exposes the deadline on identity resolution so
        its X11 queries cannot outlive a motion or transition intent.  Calls
        outside a bounded operation retain the driver's ordinary startup
        behavior by omitting the optional capability.
        """

        if deadline is None:
            return self.driver.resolve_identity(require_foreground=require_foreground)
        return self.driver.resolve_identity(
            require_foreground=require_foreground,
            deadline_monotonic=deadline,
        )

    def _capture_client_crop(
        self,
        path: Path,
        *,
        model: bool = False,
        deadline: float | None = None,
    ) -> Path:
        """Capture one client crop while preserving an absolute deadline."""

        if deadline is None:
            return self.driver.capture_client_crop(path, model=model)
        return self.driver.capture_client_crop(
            path,
            model=model,
            deadline_monotonic=deadline,
        )

    def _capture_client_crop_for_identity(
        self,
        identity: WindowIdentity,
        *,
        deadline: float | None = None,
    ) -> Path:
        """Capture an identity-bound crop with the same bounded capability."""

        if deadline is None:
            return self.driver.capture_client_crop_for_identity(identity)
        return self.driver.capture_client_crop_for_identity(
            identity,
            deadline_monotonic=deadline,
        )

    def _native_region_enabled(self) -> bool:
        profile = getattr(getattr(self, "config", None), "profile", None)
        if profile is None:
            return False
        executable = getattr(profile, "telemetry_region_executable", None)
        digest = getattr(profile, "telemetry_region_executable_sha256", None)
        return executable is not None and digest is not None

    def _capture_native_region_for_identity(
        self,
        identity: WindowIdentity,
        *,
        destination: Path | None = None,
        deadline: float | None = None,
    ) -> Path:
        if not self._native_region_enabled():
            return self._capture_client_crop_for_identity(identity, deadline=deadline)
        if not isinstance(self.driver.backend, X11Backend):
            raise DriverError("native region capture requires the configured X11 backend")
        with self.controller.lock:
            admitted_status = self.controller.status()
            if admitted_status.state in {
                ControllerState.PAUSED,
                ControllerState.BLOCKED,
                ControllerState.STOPPED,
            }:
                raise DriverError("controller state does not admit a native region capture")
            if admitted_status.stop_requested:
                raise DriverError("controller stop request does not admit a native region capture")
            admitted_generation = admitted_status.generation
            admitted_state = admitted_status.state

        guardian = self.driver.guardian

        def admit_observer(start: Callable[[], Any]) -> Any:
            # This is the linearization point: the controller state and its
            # generation remain stable until Guardian registers the gated
            # process and releases its nonblocking exec gate.
            with self.controller.lock:
                current = self.controller.status()
                if (
                    current.generation != admitted_generation
                    or current.state is not admitted_state
                    or current.stop_requested
                ):
                    raise DriverError("controller generation or state changed before observer admission")
                return guardian.observer_dispatch_admission(start)

        def observer_reaped(process_group: int) -> None:
            guardian.unregister_observer_process(process_group)

        capture_kwargs: dict[str, Any] = {
            "destination": destination,
            "observer_admission": admit_observer,
            "observer_reaped": observer_reaped,
        }
        if deadline is not None:
            capture_kwargs["deadline_monotonic"] = deadline
        return self.driver.capture_native_region_for_identity(identity, **capture_kwargs)

    def _read_command_buffer(self) -> str:
        # The addon publishes the native EditBox projection on its one-Hz
        # telemetry tick.  A command may be typed immediately after the last
        # frame, so consume only a fresh post-type frame within a bounded
        # interval; a duplicate pre-type frame can never prove the buffer.
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            sample = self.capture_status()
            if sample.kind == "FRESH" and sample.frame is not None:
                value = sample.frame.snapshot.value.get("chatEdit")
                if not isinstance(value, dict) or not isinstance(value.get("text"), str):
                    raise DriverError("command readback omitted the active EditBox text")
                return value["text"]
            time.sleep(0.05)
        raise DriverError("command readback did not contain a fresh frame")

    def _command(self, snapshot: dict[str, Any], command: str) -> bool:
        edit = snapshot.get("chatEdit", {})
        with self.controller.lock:
            controller_status = self.controller.status()
            if controller_status.state in {
                ControllerState.PAUSED,
                ControllerState.BLOCKED,
                ControllerState.STOPPED,
            }:
                return False
            if controller_status.stop_requested:
                return False
            if controller_status.mode.value == "interaction":
                raise DriverError("engine action is revoked by interaction mode")
            if command == "/crowley scan" and controller_status.closeout_requested:
                return False
            action = self._command_action_kind(command, controller_status.state)
            deadline = self._action_deadline(action)
            self.controller.set_action_intent(action, deadline_seconds=deadline)
            # Preparation is itself a durable uncertainty boundary. If the
            # owner pauses or crashes while opening the chat/readback path,
            # reconciliation retains the exact intent and never replays it.
            self.controller.action_result("preparing")
            controller_generation = controller_status.generation
        generation = self.driver.guardian.generation
        self._last_action_generation = generation
        expected_identity = self.driver.resolve_identity().fingerprint

        def dispatch_allowed() -> None:
            with self.controller.lock:
                current = self.controller.status()
                if current.generation != controller_generation or current.state in {
                    ControllerState.PAUSED,
                    ControllerState.BLOCKED,
                    ControllerState.STOPPED,
                }:
                    raise DriverError("command dispatch was revoked")
                if current.mode.value == "interaction":
                    raise DriverError("command dispatch was revoked by interaction mode")
                if current.action_intent != action:
                    raise DriverError("command dispatch intent was replaced")

        def identity_guard(identity: Any) -> bool:
            if identity.fingerprint != expected_identity:
                return False
            if command == "/crowley scan" and snapshot.get("ahOpen") is not True:
                return False
            if command == "/logout":
                context = snapshot.get("context", {})
                if (
                    context.get("character") != self.config.profile.character
                    or context.get("realm") != self.config.profile.realm
                    or snapshot.get("pending", {}).get("ids", [])
                ):
                    return False
                if not self._logout_scanner_idle(snapshot, controller_status.last_uid):
                    return False
            if command == "/crowley session fence" and not self._scanner_idle_ready(
                snapshot, controller_status.last_uid
            ):
                return False
            return True

        if edit.get("active") and edit.get("focused") and edit.get("text") == "":
            if command == "/logout" and isinstance(self.driver.backend, X11Backend):
                # Pair the durable logout command with a named world
                # observation.  The character-select postcondition is checked
                # after the asynchronous scene transition in cleanup wait.
                self.driver.verify_named_action("logout", "before")
            dispatch_allowed()
            self.driver.prepare_command(
                generation,
                command,
                snapshot,
                readback=self._read_command_buffer,
                precondition=identity_guard,
                postcondition=identity_guard,
            )
            with self.controller.lock:
                if self.controller.status().generation != controller_generation:
                    raise DriverError("command dispatch was revoked")
                self.controller.action_result("dispatched")
            return True
        if not edit.get("active"):
            dispatch_allowed()
            self.driver.run(
                "open_chat",
                generation,
                precondition=identity_guard,
                postcondition=identity_guard,
            )
            with self.controller.lock:
                if self.controller.status().generation == controller_generation:
                    self.controller.action_result("chat_open")
            return False
        self.driver.revoke("unexpected active chat buffer")
        raise DriverError("unexpected active chat buffer; input is revoked")

    def capture_status(self, *, deadline: float | None = None) -> Sample:
        self.config.capture_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.capture_index += 1
        source = self.config.capture_dir / f"status-{self.capture_index:08d}.png"
        if deadline is None:
            deadline_local = getattr(self, "_motion_deadline_local", None)
            deadline = getattr(deadline_local, "deadline", None) if deadline_local is not None else None
        expected = self._resolve_identity(deadline=deadline)
        if self._native_region_enabled():
            crop = self._capture_native_region_for_identity(expected, destination=source, deadline=deadline)
        else:
            crop = self._capture_client_crop(source, deadline=deadline)
        try:
            from PIL import Image

            identity = self._resolve_identity(deadline=deadline)
            if deadline is not None:
                self._remaining_motion_budget(deadline)
            if identity.fingerprint != expected.fingerprint:
                raise DriverError("status capture identity changed after crop")
            with Image.open(crop) as image:
                sample = self.decoder.decode(
                    image, monotonic=time.monotonic(), window_identity=identity.fingerprint
                )
                if deadline is not None:
                    self._remaining_motion_budget(deadline)
                if sample.kind == "FRESH" and sample.frame is not None:
                    self._last_addon_sequence = sample.frame.sequence
                    self._last_addon_boot = sample.frame.boot
                return sample
        finally:
            for target in (source, crop):
                try:
                    target.unlink()
                except FileNotFoundError:
                    pass

    def _capture_model(self, *, deadline: float | None = None) -> bytes:
        if deadline is not None:
            self._remaining_motion_budget(deadline)
        self.config.capture_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.capture_index += 1
        path = self.config.capture_dir / f"recovery-{self.capture_index:08d}.png"
        cropped = self._capture_client_crop(path, model=True, deadline=deadline)
        try:
            value = cropped.read_bytes()
            if deadline is not None:
                self._remaining_motion_budget(deadline)
            return value
        finally:
            for target in (path, cropped):
                try:
                    target.unlink()
                except FileNotFoundError:
                    pass

    def _model_call_snapshot(self) -> dict[str, int]:
        lock = getattr(self, "_model_counter_lock", None)
        if lock is None:
            lock = threading.RLock()
            self._model_counter_lock = lock
        with lock:
            counters = getattr(self, "_model_call_counters", None)
            if counters is None:
                counters = {"started": 0, "succeeded": 0, "failed": 0}
                self._model_call_counters = counters
            return {key: int(counters[key]) for key in ("started", "succeeded", "failed")}

    def _call_model_adapter(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        """Count the real adapter call without holding the counter lock over it."""

        adapter = self.model
        method = getattr(adapter, method_name, None)
        if not callable(method):
            raise ModelError(f"model adapter has no {method_name} entrypoint")
        lock = getattr(self, "_model_counter_lock", None)
        if lock is None:
            lock = threading.RLock()
            self._model_counter_lock = lock
        with lock:
            counters = getattr(self, "_model_call_counters", None)
            if counters is None:
                counters = {"started": 0, "succeeded": 0, "failed": 0}
                self._model_call_counters = counters
            counters["started"] += 1
        try:
            result = method(*args, **kwargs)
        except BaseException:
            with lock:
                counters["failed"] += 1
            raise
        else:
            with lock:
                counters["succeeded"] += 1
            return result

    def _runtime_source_binding_for_diagnostic(self) -> dict[str, str]:
        initial = getattr(self, "_runtime_source_binding", None)
        if not isinstance(initial, dict) or set(initial) != set(_RUNTIME_SOURCE_FILES):
            raise DriverError("paused region diagnostic source binding is unavailable")
        current = _runtime_source_hashes()
        if current != initial:
            raise DriverError("paused region diagnostic source binding drifted")
        return dict(current)

    def _observe_model(
        self,
        image: bytes,
        *,
        timeout: float,
        requested_state: str | None = None,
        requested_control: str | None = None,
    ) -> Any:
        """Run one visual model turn under a finite freshness budget."""

        kwargs: dict[str, Any] = {
            "target": "game-client",
            "verified_crop": self.config.profile.model_crop,
        }
        if requested_state is not None:
            kwargs["requested_state"] = requested_state
        if requested_control is not None:
            kwargs["requested_control"] = requested_control
        # The timeout is part of the visual-adapter contract.  Every provider,
        # including deterministic lifecycle fixtures, must receive the same
        # freshness bound; a type-based compatibility branch would silently
        # remove the deadline from an alternate production provider.
        kwargs["timeout"] = timeout
        return self._call_model_adapter("observe", image, **kwargs)

    def _require_interaction(self, generation: int) -> int:
        deadline_local = getattr(self, "_motion_deadline_local", None)
        if deadline_local is not None and hasattr(deadline_local, "deadline"):
            if self._native_clock() >= deadline_local.deadline:
                raise DriverError("motion intent exceeded its bounded deadline")
        with self.controller.lock:
            status = self.controller.status()
            if status.generation != generation or status.mode.value != "interaction":
                raise DriverError("motion intent requires the current interaction generation")
            if status.state != ControllerState.READY:
                raise DriverError("motion intent requires READY controller state")
            lease = self.driver.guardian
            if status.lease_generation <= 0 or not lease.armed or lease.generation != status.lease_generation:
                raise DriverError("motion intent requires the current armed input lease")
            if status.action_intent:
                raise DriverError("another interaction intent is already in flight")
            return status.lease_generation

    def _require_motion_interaction(self, generation: int) -> int:
        """Acquire motion interaction authority and invalidate on setup failure."""

        try:
            return self._require_interaction(generation)
        except Exception:
            self._invalidate_motion_admission()
            raise

    def _motion_deadline(self, *, limit: float | None = None) -> float:
        """Return the active intent deadline for a native/model helper.

        Serialized motion owns one absolute deadline across every capture,
        model call, physical action, and feedback wait.  A direct helper call
        outside an intent still receives a short bounded fallback.
        """

        local = getattr(self, "_motion_deadline_local", None)
        absolute = getattr(local, "deadline", None) if local is not None else None
        try:
            now = self._native_clock()
        except Exception:
            # Once an intent has entered the motion admission boundary, a
            # clock failure makes its existing visual proofs unusable.  The
            # serialized wrapper deliberately leaves ordinary method errors
            # alone; this helper is an explicit deadline boundary.
            self._invalidate_motion_admission()
            raise
        if absolute is not None and limit is None:
            deadline = float(absolute)
        else:
            helper_limit = 5.0 if limit is None else float(limit)
            deadline = now + helper_limit if absolute is None else min(absolute, now + helper_limit)
        if deadline <= now:
            raise DriverError("motion intent exceeded its bounded deadline")
        return deadline

    def _remaining_motion_budget(self, deadline: float) -> float:
        try:
            remaining = float(deadline) - self._native_clock()
        except Exception:
            raise
        if not math.isfinite(remaining) or remaining <= 0:
            raise DriverError("motion intent exceeded its bounded deadline")
        return remaining

    def _world_forward_heading(self, frame: MotionFrame) -> float:
        basis = getattr(self, "movement_basis", None)
        if basis is None or basis.facing_sign not in {-1, 1}:
            raise DriverError("movement coordinate basis has not been calibrated")
        return normalize_angle(basis.facing_sign * frame.facing + basis.forward_heading_offset)

    def _world_left_heading(self, frame: MotionFrame) -> float:
        basis = getattr(self, "movement_basis", None)
        if basis is None or basis.handedness not in {-1, 1} or basis.strafe_heading_offset is None:
            raise DriverError("movement left basis has not been calibrated")
        return normalize_angle(
            self._world_forward_heading(frame) + basis.handedness * math.pi / 2 + basis.strafe_heading_offset
        )

    @staticmethod
    def _require_supported_route_handedness(basis: MovementBasis | int) -> None:
        """Require the route model's documented character-left convention.

        Route prompts describe ``+pi/2`` as character-left.  A reflected
        native coordinate basis would require a different prompt contract;
        accepting it here would silently send the model a corridor with the
        opposite meaning.  Refuse before sealing or consuming such a basis.
        """

        handedness = basis.handedness if isinstance(basis, MovementBasis) else basis
        if handedness != 1:
            raise DriverError("movement route requires a positively handed coordinate basis")

    @staticmethod
    def _travel_envelope(planned_distance: float) -> float:
        """Bound planned movement plus proportional calibration uncertainty."""

        if not math.isfinite(planned_distance) or planned_distance <= 0.0:
            raise DriverError("planned movement distance is malformed")
        uncertainty = max(MIN_BASIS_DISPLACEMENT, planned_distance * TRAVEL_UNCERTAINTY_FRACTION)
        envelope = planned_distance + uncertainty
        if not math.isfinite(envelope):
            raise DriverError("planned movement envelope is malformed")
        return envelope

    def _measured_motion_speed(self, role: KeyRole) -> float:
        basis = getattr(self, "movement_basis", None)
        if basis is None:
            raise DriverError("motion pulse requires measured movement basis")
        if role in {KeyRole.MOVE_FORWARD, KeyRole.MOVE_BACKWARD}:
            if role is KeyRole.MOVE_FORWARD:
                displacement = basis.forward_displacement
                pulse = basis.pulse_seconds
            else:
                displacement = basis.backward_displacement
                pulse = basis.backward_pulse_seconds
                if displacement is None or pulse is None:
                    raise DriverError("movement basis has no measured backward speed")
        elif role in {KeyRole.STRAFE_LEFT, KeyRole.STRAFE_RIGHT}:
            if role is KeyRole.STRAFE_LEFT:
                displacement = basis.strafe_displacement
                pulse = basis.strafe_pulse_seconds
            else:
                displacement = basis.strafe_right_displacement
                pulse = basis.strafe_right_pulse_seconds
            if pulse is None:
                raise DriverError("movement basis has no measured strafe role speed")
        else:
            raise DriverError("motion pulse role is outside the measured movement basis")
        speed = displacement / pulse
        if not math.isfinite(speed) or speed <= 0.0:
            raise DriverError("movement basis has no measured role speed")
        return speed

    def _confirm_motion_pose(self, generation: int, frame: MotionFrame) -> MotionFrame:
        """Confirm model evidence survived on a fresh same-pose native frame."""

        confirmed = self._observe_motion(generation, previous=frame)
        if (
            confirmed.identity_fingerprint != frame.identity_fingerprint
            or confirmed.boot != frame.boot
            or confirmed.instance != frame.instance
            or confirmed.zone != frame.zone
            or abs(confirmed.z - frame.z) > 0.25
            or math.hypot(confirmed.x - frame.x, confirmed.y - frame.y) > MAX_CONFIRMATION_POSITION_DRIFT
            or abs(normalize_angle(confirmed.facing - frame.facing)) > MAX_CONFIRMATION_FACING_DRIFT
        ):
            self._invalidate_motion_admission()
            raise DriverError("native motion changed during visual evidence")
        if confirmed.chat_focused:
            self._invalidate_motion_admission()
            raise DriverError("native motion confirmation is refused while the chat edit box is focused")
        return confirmed

    def _invalidate_motion_admission(self) -> None:
        """Drop all retained motion proofs after a native gate failure."""

        self.camera_mapping = None
        self.movement_basis = None

    def _require_native_gate(self, frame: MotionFrame, *, matching: MotionFrame | None = None) -> None:
        try:
            frame.require_native_gate(matching=matching)
        except MotionError as exc:
            self._invalidate_motion_admission()
            raise DriverError(str(exc)) from exc

    @staticmethod
    def _route_matches_corridor(
        route: RouteEvidence,
        frame: MotionFrame,
        generation: int,
        corridor_heading: float,
        corridor_distance: float,
    ) -> bool:
        return (
            route.identity_fingerprint == frame.identity_fingerprint
            and route.generation == generation
            and route.scene == "world"
            and route.boot == frame.boot
            and route.sequence == frame.sequence
            and route.instance == frame.instance
            and route.zone == frame.zone
            and route.capture_monotonic >= frame.capture_monotonic
            and route.corridor_heading is not None
            and abs(normalize_angle(route.corridor_heading - corridor_heading)) <= 1e-6
            and route.corridor_distance is not None
            and abs(route.corridor_distance - corridor_distance) <= 1e-6
        )

    def _route_matches_frame(
        self,
        route: RouteEvidence,
        frame: MotionFrame,
        generation: int,
        target_x: float,
        target_y: float,
        forward_heading: float | None = None,
    ) -> bool:
        """Check the complete frame/corridor binding before a physical pulse."""

        if forward_heading is None:
            forward_heading = self._world_forward_heading(frame)
        expected_heading = normalize_angle(
            math.atan2(target_y - frame.y, target_x - frame.x) - forward_heading
        )
        expected_distance = math.hypot(target_x - frame.x, target_y - frame.y)
        return (
            route.identity_fingerprint == frame.identity_fingerprint
            and route.generation == generation
            and route.scene == "world"
            and route.boot == frame.boot
            and route.sequence == frame.sequence
            and route.instance == frame.instance
            and route.zone == frame.zone
            and route.capture_monotonic >= frame.capture_monotonic
            and route.corridor_heading is not None
            and abs(normalize_angle(route.corridor_heading - expected_heading)) <= 1e-6
            and route.corridor_distance is not None
            and abs(route.corridor_distance - expected_distance) <= 1e-6
        )

    def _observe_motion(
        self,
        generation: int,
        previous: MotionFrame | None = None,
        *,
        not_before: float | None = None,
        after_release: bool = False,
    ) -> MotionFrame:
        try:
            self._require_motion_interaction(generation)
            deadline = self._motion_deadline()
            if after_release:
                if previous is None:
                    raise DriverError("post-release motion observation requires its pre-action frame")
                frame = self.motion_provider.observe_after_release(
                    generation, previous=previous, deadline=deadline
                )
            else:
                frame = self.motion_provider.observe(
                    generation, previous=previous, deadline=deadline, not_before=not_before
                )
            # Every frame returned by the daemon's motion observation boundary
            # is an admission candidate.  Gate it before pose, speed, chat,
            # route, model, or driver checks so a disallowed successor cannot
            # be hidden by an earlier validation failure.
            self._require_native_gate(frame, matching=previous)
            return frame
        except MotionError as exc:
            self._invalidate_motion_admission()
            raise DriverError(str(exc)) from exc
        except Exception:
            # A required successor that cannot be obtained leaves the prior
            # camera and movement proofs unbound to the next native frame.
            self._invalidate_motion_admission()
            raise

    def _observe_route(
        self,
        generation: int,
        target_x: float | None = None,
        target_y: float | None = None,
        *,
        frame: MotionFrame | None = None,
        corridor_heading: float | None = None,
        corridor_distance: float | None = None,
    ) -> RouteEvidence:
        self._require_motion_interaction(generation)
        if frame is None:
            frame = self._observe_motion(generation)
        if frame.chat_focused:
            self._invalidate_motion_admission()
            raise DriverError("route evidence is refused while the chat edit box is focused")
        has_target = target_x is not None or target_y is not None
        if has_target and (target_x is None or target_y is None):
            raise DriverError("route evidence requires both target coordinates")
        if not has_target and (
            corridor_heading is None
            or corridor_distance is None
            or not math.isfinite(float(corridor_heading))
            or not math.isfinite(float(corridor_distance))
            or float(corridor_distance) <= 0.0
        ):
            raise DriverError("route evidence requires a positive egocentric corridor")
        if has_target:
            assert target_x is not None and target_y is not None
            if corridor_heading is None:
                try:
                    corridor_heading = normalize_angle(
                        math.atan2(target_y - frame.y, target_x - frame.x)
                        - self._world_forward_heading(frame)
                    )
                except (TypeError, ValueError):
                    raise DriverError("route evidence target coordinates are malformed") from None
            if corridor_distance is None:
                corridor_distance = math.hypot(target_x - frame.x, target_y - frame.y)
        assert corridor_heading is not None and corridor_distance is not None
        if not math.isfinite(float(corridor_heading)) or not math.isfinite(float(corridor_distance)):
            raise DriverError("route evidence corridor is malformed")
        corridor_heading = normalize_angle(float(corridor_heading))
        corridor_distance = float(corridor_distance)
        if corridor_distance <= 0.0:
            raise DriverError("route evidence corridor distance must be positive")
        deadline = self._motion_deadline()
        identity = self._resolve_identity(require_foreground=True, deadline=deadline)
        if frame.identity_fingerprint != identity.fingerprint:
            raise DriverError("route frame identity is stale")
        captured_at = self._native_clock()
        image = self._capture_model(deadline=deadline)
        remaining = self._remaining_motion_budget(deadline) - MOTION_POST_RELEASE_RESERVE_SECONDS
        if remaining <= 0:
            raise DriverError("route evidence left no post-release feedback reserve")
        observation = self._call_model_adapter(
            "observe_route",
            image,
            target="game-client",
            verified_crop=self.config.profile.model_crop,
            target_x=target_x,
            target_y=target_y,
            origin_x=frame.x,
            origin_y=frame.y,
            corridor_heading=corridor_heading,
            corridor_distance=corridor_distance,
            timeout=remaining,
        )
        if self._native_clock() > deadline - MOTION_POST_RELEASE_RESERVE_SECONDS:
            raise DriverError("route visual evidence exceeded its freshness budget")
        if (
            self._resolve_identity(require_foreground=True, deadline=deadline).fingerprint
            != identity.fingerprint
        ):
            raise DriverError("client identity changed during route evidence")
        digest = hashlib.sha256(image).hexdigest()
        return RouteEvidence(
            identity_fingerprint=identity.fingerprint,
            capture_monotonic=captured_at,
            scene=observation.scene,
            route_id=observation.route_id,
            target_visible=observation.target_visible,
            ground_clear=observation.ground_clear,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest=digest,
            corridor_heading=corridor_heading,
            corridor_distance=corridor_distance,
        )

    def _observe_viewport(self, generation: int, frame: MotionFrame) -> ViewportEvidence:
        """Bind a fresh model-measured clear world pixel to one native frame."""

        self._require_motion_interaction(generation)
        if frame.chat_focused:
            self._invalidate_motion_admission()
            raise DriverError("camera viewport proof is refused while chat is focused")
        deadline = self._motion_deadline()
        identity = self._resolve_identity(require_foreground=True, deadline=deadline)
        if frame.identity_fingerprint != identity.fingerprint:
            raise DriverError("viewport frame identity is stale")
        captured_at = self._native_clock()
        image = self._capture_model(deadline=deadline)
        remaining = self._remaining_motion_budget(deadline) - MOTION_POST_RELEASE_RESERVE_SECONDS
        if remaining <= 0:
            raise DriverError("viewport evidence left no post-release feedback reserve")
        observe_viewport = getattr(self.model, "observe_viewport", None)
        if not callable(observe_viewport):
            raise DriverError("model has no strict world viewport observation provider")
        observation = self._call_model_adapter(
            "observe_viewport",
            image,
            target="game-client",
            verified_crop=self.config.profile.model_crop,
            timeout=remaining,
        )
        if self._native_clock() > deadline - MOTION_POST_RELEASE_RESERVE_SECONDS:
            raise DriverError("viewport visual evidence exceeded its freshness budget")
        if (
            self._resolve_identity(require_foreground=True, deadline=deadline).fingerprint
            != identity.fingerprint
        ):
            raise DriverError("client identity changed during viewport evidence")
        if getattr(observation, "scene", None) != "world":
            raise DriverError("viewport evidence is not a world scene")
        ui_clear = getattr(observation, "ui_clear", None)
        units_clear = getattr(observation, "units_clear", None)
        if not isinstance(ui_clear, bool) or not isinstance(units_clear, bool):
            raise DriverError("viewport model clearance flags are malformed")
        if not ui_clear or not units_clear:
            raise DriverError("viewport evidence does not prove a clear world point")
        raw_point = getattr(observation, "point", None)
        if (
            not isinstance(raw_point, tuple)
            or len(raw_point) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) for value in raw_point)
        ):
            raise DriverError("viewport model point is malformed")
        crop_x, crop_y, crop_width, crop_height = self.config.profile.model_crop
        if not (0 <= raw_point[0] < crop_width and 0 <= raw_point[1] < crop_height):
            raise DriverError("viewport model point is outside the verified model crop")
        point = (crop_x + raw_point[0], crop_y + raw_point[1])
        client_width, client_height = identity.child_geometry[2:]
        if not (0 <= point[0] < client_width and 0 <= point[1] < client_height):
            raise DriverError("viewport model point is outside the verified client")
        return ViewportEvidence(
            identity_fingerprint=identity.fingerprint,
            capture_monotonic=captured_at,
            scene=observation.scene,
            point=point,
            ui_clear=ui_clear,
            units_clear=units_clear,
            generation=generation,
            boot=frame.boot,
            sequence=frame.sequence,
            instance=frame.instance,
            zone=frame.zone,
            screenshot_digest=hashlib.sha256(image).hexdigest(),
        )

    def _camera_drag_plan(
        self,
        frame: MotionFrame,
        delta_pixels: int,
        identity: WindowIdentity,
        generation: int,
        viewport: ViewportEvidence,
        *,
        session_generation: int,
        evidence_frame: MotionFrame | None = None,
    ) -> Any:
        if isinstance(delta_pixels, bool) or not isinstance(delta_pixels, int):
            raise DriverError("camera delta must be an integer")
        width, height = identity.child_geometry[2:]
        if not isinstance(viewport, ViewportEvidence):
            raise DriverError("camera drag requires fresh measured viewport evidence")
        proof_frame = frame if evidence_frame is None else evidence_frame
        if (
            viewport.identity_fingerprint != proof_frame.identity_fingerprint
            or viewport.identity_fingerprint != identity.fingerprint
            or viewport.generation != session_generation
            or viewport.boot != proof_frame.boot
            or viewport.sequence != proof_frame.sequence
            or viewport.instance != proof_frame.instance
            or viewport.zone != proof_frame.zone
            or viewport.capture_monotonic < proof_frame.capture_monotonic
            or not viewport.ui_clear
            or not viewport.units_clear
        ):
            raise DriverError("camera viewport evidence is stale or unbound")
        if self._native_clock() - viewport.capture_monotonic > MAX_FRAME_AGE:
            raise DriverError("camera viewport evidence is stale at dispatch")
        start = Point(*viewport.point)
        safe_margin = 4
        if not (
            safe_margin <= start.x < width - safe_margin and safe_margin <= start.y < height - safe_margin
        ):
            raise DriverError("measured world viewport point is outside the safe client interior")
        end = Point(start.x + delta_pixels, start.y)
        client = Rect(0, 0, width, height)
        if not (safe_margin <= end.x < width - safe_margin and safe_margin <= end.y < height - safe_margin):
            raise DriverError("camera drag endpoint is outside the safe client interior")
        binding = BindingMetadata(
            identity.fingerprint,
            f"motion:{frame.boot}:{frame.sequence}",
            frame.sequence,
            generation,
            identity.child_xid,
            (identity.xid, identity.child_xid),
            source="native-addon",
            boot=frame.boot,
        )
        return plan_camera_drag(
            start,
            end,
            client,
            binding,
            profile=self._motion_profiles["camera"],
        )

    @_serialized_motion
    def calibrate_camera_mapping(self, delta_pixels: int, *, generation: int) -> CameraMapping:
        """Measure signed camera response with one bounded right drag."""

        if (
            isinstance(delta_pixels, bool)
            or not isinstance(delta_pixels, int)
            or not MIN_CAMERA_CALIBRATION_PIXELS <= abs(delta_pixels) <= MAX_CAMERA_CALIBRATION_PIXELS
            or MAX_CAMERA_YAW_PER_PIXEL * abs(delta_pixels) > MAX_CAMERA_CALIBRATION_YAW
        ):
            raise DriverError("camera calibration delta must be 4..8 pixels within the sub-pi envelope")
        lease_generation = self._require_motion_interaction(generation)
        operation_local = getattr(self, "_motion_deadline_local", None)
        operation_deadline = getattr(operation_local, "deadline", None)
        before = self._observe_motion(generation)
        self._require_native_gate(before)
        viewport_route = self._observe_route(
            generation,
            frame=before,
            corridor_heading=0.0,
            corridor_distance=0.5,
        )
        if not viewport_route.target_visible or not viewport_route.ground_clear:
            raise DriverError("camera calibration lacks a clear measured world viewport")
        if not self._route_matches_corridor(viewport_route, before, generation, 0.0, 0.5):
            raise DriverError("camera calibration corridor is not bound to the native frame")
        identity = self._resolve_identity(
            require_foreground=True,
            deadline=operation_deadline,
        )
        viewport = self._observe_viewport(generation, before)
        confirmed = self._confirm_motion_pose(generation, before)
        self._require_native_gate(confirmed, matching=before)
        plan = self._camera_drag_plan(
            confirmed,
            delta_pixels,
            identity,
            lease_generation,
            viewport,
            session_generation=generation,
            evidence_frame=before,
        )
        if (
            not self._route_matches_corridor(viewport_route, before, generation, 0.0, 0.5)
            or self._native_clock() - viewport_route.capture_monotonic > MAX_FRAME_AGE
            or self._native_clock() - before.capture_monotonic > MAX_FRAME_AGE
        ):
            raise DriverError("camera calibration route evidence expired before physical commit")
        if operation_deadline is not None and (
            self._native_clock() + plan.duration + MOTION_POST_RELEASE_RESERVE_SECONDS >= operation_deadline
        ):
            raise DriverError("camera calibration cannot fit the bounded intent deadline")
        if self._native_clock() - before.capture_monotonic > MAX_FRAME_AGE:
            raise DriverError("camera calibration frame is stale at dispatch")
        lease_generation = self._require_motion_interaction(generation)
        self.driver.run_camera_drag(
            plan,
            generation=lease_generation,
            deadline_monotonic=operation_deadline,
        )
        after = self._observe_motion(generation, previous=confirmed, after_release=True)
        self._require_native_gate(after, matching=confirmed)
        if (
            after.identity_fingerprint != confirmed.identity_fingerprint
            or after.boot != confirmed.boot
            or after.sequence <= confirmed.sequence
            or after.capture_monotonic <= confirmed.capture_monotonic
            or after.instance != confirmed.instance
            or after.zone != confirmed.zone
            or abs(after.z - confirmed.z) > 0.25
            or math.hypot(after.x - confirmed.x, after.y - confirmed.y) > 0.01
        ):
            self._invalidate_motion_admission()
            raise DriverError("camera calibration changed scene or vertical position")
        # The physical drag was admitted from ``confirmed``.  Measure its
        # response from that same dispatch baseline so pre-input facing drift
        # cannot manufacture calibration progress.
        yaw_delta = (after.facing - confirmed.facing + math.pi) % (2.0 * math.pi) - math.pi
        if abs(yaw_delta) < 0.001:
            raise DriverError("camera calibration produced no measured yaw change")
        if abs(yaw_delta) > MAX_CAMERA_CALIBRATION_YAW:
            raise DriverError("camera calibration response exceeds the bounded angular motion")
        yaw_per_pixel = yaw_delta / delta_pixels
        if not math.isfinite(yaw_per_pixel) or not 0.0001 <= abs(yaw_per_pixel) <= MAX_CAMERA_YAW_PER_PIXEL:
            raise DriverError("camera calibration response exceeds the measured yaw bound")
        mapping = CameraMapping(
            identity_fingerprint=identity.fingerprint,
            generation=generation,
            capture_id=f"camera:{before.boot}:{before.sequence}:{after.sequence}",
            yaw_per_pixel=yaw_per_pixel,
            boot=before.boot,
        )
        self.camera_mapping = mapping
        return mapping

    @_serialized_motion
    def calibrate_movement_basis(
        self,
        pulse_seconds: float = DEFAULT_MOVEMENT_CALIBRATION_PULSE_SECONDS,
        *,
        generation: int,
    ) -> MovementBasis:
        """Measure every translation role and fit a circular world basis.

        Forward is repeated at two headings to establish both the facing sign
        and the circular offset.  Backward and both strafe roles are then
        measured independently; their speeds are never inferred from the
        forward probe.  The measured displacement cap and the cumulative
        two-unit cap apply to every probe.
        """

        move_profile = self._motion_profiles["move"]
        profile_limit = move_profile.max_duration
        # Calibration is the one technical probe path allowed below the
        # human motion profile minimum.  The probe still uses the driver's
        # hard pulse ceiling; runtime motion admission remains profile-bound.
        if (
            isinstance(pulse_seconds, bool)
            or not isinstance(pulse_seconds, (int, float))
            or not math.isfinite(float(pulse_seconds))
            or not MIN_MOVEMENT_CALIBRATION_PULSE_SECONDS
            <= float(pulse_seconds)
            <= min(MAX_PULSE_SECONDS, profile_limit)
        ):
            raise DriverError("movement basis calibration pulse is outside bounds")
        camera_mapping = getattr(self, "camera_mapping", None)
        if camera_mapping is None or camera_mapping.generation != generation:
            raise DriverError("movement basis calibration requires a current camera mapping")
        self._require_motion_interaction(generation)
        operation_local = getattr(self, "_motion_deadline_local", None)
        operation_deadline = getattr(operation_local, "deadline", None)
        seed = self._observe_motion(generation)
        before = self._observe_motion(generation, previous=seed)
        self._require_native_gate(before, matching=seed)
        if before.speed > 0.25:
            self._invalidate_motion_admission()
            raise DriverError("movement basis calibration requires a stationary frame")
        identity = self._resolve_identity(require_foreground=True, deadline=operation_deadline)
        if before.identity_fingerprint != identity.fingerprint:
            self._invalidate_motion_admission()
            raise DriverError("movement basis calibration identity is stale")
        if camera_mapping.boot and camera_mapping.boot != before.boot:
            self._invalidate_motion_admission()
            raise DriverError("movement basis camera mapping boot is stale")
        cumulative_probe_distance = 0.0

        def admit_probe(frame: MotionFrame, headings: tuple[float, ...]) -> RouteEvidence:
            """Prove each possible egocentric corridor before an unknown role."""

            # Reserve the complete unknown-role envelope before every probe.
            # Charging only the current measured distance would admit a pulse
            # that can still consume one full unit and discover the two-unit
            # violation only after physical input.
            if cumulative_probe_distance + MAX_BASIS_DISPLACEMENT > MAX_WAYPOINT_DISTANCE:
                raise DriverError("movement basis probe would exceed the cumulative local distance bound")
            route: RouteEvidence | None = None
            for heading in headings:
                # Each heading is proved against the same one-unit maximum
                # displacement before the role is admitted.
                route = prove_corridor(frame, heading, MAX_BASIS_DISPLACEMENT)
            assert route is not None
            return route

        def prove_corridor(frame: MotionFrame, heading: float, distance: float) -> RouteEvidence:
            route = self._observe_route(
                generation,
                frame=frame,
                corridor_heading=heading,
                corridor_distance=distance,
            )
            if not route.target_visible or not route.ground_clear:
                raise DriverError("movement calibration corridor was not positively proved")
            if not self._route_matches_corridor(route, frame, generation, heading, distance):
                raise DriverError("movement calibration corridor is not bound to the native frame")
            if self._native_clock() - frame.capture_monotonic > MAX_FRAME_AGE:
                raise DriverError("movement calibration frame is stale at dispatch")
            return route

        def probe(
            frame: MotionFrame, role: KeyRole, route: RouteEvidence, corridor_heading: float
        ) -> tuple[MotionFrame, MotionFrame, float, float, float]:
            nonlocal cumulative_probe_distance
            lease_generation = self._require_motion_interaction(generation)
            if operation_deadline is not None and (
                self._native_clock() + float(pulse_seconds) + MOTION_POST_RELEASE_RESERVE_SECONDS
                >= operation_deadline
            ):
                raise DriverError("movement calibration cannot fit the bounded intent deadline")
            # Route/model work may have taken long enough for the client to
            # reload or move.  Confirm the same native pose immediately before
            # admitting this pulse; this successor is the explicit chain from
            # the egocentric corridor proof to the physical input.
            confirmed = self._confirm_motion_pose(generation, frame)
            self._require_native_gate(confirmed, matching=frame)
            if confirmed.speed > 0.25:
                self._invalidate_motion_admission()
                raise DriverError("movement basis calibration requires a stationary frame")
            if (
                not self._route_matches_corridor(
                    route,
                    frame,
                    generation,
                    corridor_heading,
                    MAX_BASIS_DISPLACEMENT,
                )
                or self._native_clock() - route.capture_monotonic > MAX_FRAME_AGE
                or self._native_clock() - frame.capture_monotonic > MAX_FRAME_AGE
            ):
                raise DriverError("movement calibration route evidence expired before physical commit")
            if self._native_clock() - confirmed.capture_monotonic > MAX_FRAME_AGE:
                raise DriverError("movement calibration frame is stale at dispatch")
            if operation_deadline is not None and (
                self._native_clock() + float(pulse_seconds) + MOTION_POST_RELEASE_RESERVE_SECONDS
                >= operation_deadline
            ):
                raise DriverError("movement calibration cannot fit the bounded intent deadline")
            lease_generation = self._require_motion_interaction(generation)
            self.driver.run_motion_key_hold(
                role,
                float(pulse_seconds),
                confirmed,
                generation=lease_generation,
                deadline_monotonic=operation_deadline,
            )
            after = self._observe_motion(generation, previous=confirmed, after_release=True)
            self._require_native_gate(after, matching=confirmed)
            if (
                after.identity_fingerprint != identity.fingerprint
                or after.boot != confirmed.boot
                or after.sequence <= confirmed.sequence
                or after.capture_monotonic <= confirmed.capture_monotonic
                or after.instance != confirmed.instance
                or after.zone != confirmed.zone
                or abs(after.z - confirmed.z) > 0.25
            ):
                self._invalidate_motion_admission()
                raise DriverError("movement basis calibration changed identity, scene, or vertical position")
            if after.speed > 0.25:
                self._invalidate_motion_admission()
                raise DriverError("movement basis calibration requires settled post-release feedback")
            dx, dy = after.x - confirmed.x, after.y - confirmed.y
            displacement = math.hypot(dx, dy)
            if not MIN_BASIS_DISPLACEMENT <= displacement <= MAX_BASIS_DISPLACEMENT:
                raise DriverError("movement basis pulse produced an invalid displacement")
            cumulative_probe_distance += displacement
            if cumulative_probe_distance > MAX_WAYPOINT_DISTANCE:
                raise DriverError("movement basis calibration exceeded its cumulative local bound")
            return confirmed, after, dx, dy, displacement

        # The first probe is a directly-ahead egocentric corridor.  It does
        # not invent a world endpoint from the still-unknown coordinate basis.
        first_route = admit_probe(before, (0.0,))
        first_confirmed, first_after, first_dx, first_dy, first_displacement = probe(
            before, KeyRole.MOVE_FORWARD, first_route, 0.0
        )

        # A controlled camera turn supplies a second nonzero native heading.
        # Camera calibration is required because the facing delta must itself
        # be measured, and its viewport proof remains an independent gate.
        turn_pixels = max(
            self._MIN_CAMERA_DRAG_PIXELS,
            min(120, int(round(0.5 / abs(camera_mapping.yaw_per_pixel)))),
        )
        second_before = self.execute_camera_delta(
            turn_pixels,
            generation=generation,
            previous=first_after,
        )
        if (
            second_before.identity_fingerprint != identity.fingerprint
            or second_before.boot != before.boot
            or second_before.instance != before.instance
            or second_before.zone != before.zone
            or abs(second_before.z - before.z) > 0.25
        ):
            self._invalidate_motion_admission()
            raise DriverError("movement basis heading turn changed identity, scene, or vertical position")
        if second_before.speed > 0.25:
            self._invalidate_motion_admission()
            raise DriverError("movement basis calibration requires a stationary frame")
        second_route = admit_probe(second_before, (0.0,))
        second_confirmed, second_after, second_dx, second_dy, second_displacement = probe(
            second_before, KeyRole.MOVE_FORWARD, second_route, 0.0
        )
        native_heading_delta = normalize_angle(second_confirmed.facing - first_confirmed.facing)
        if abs(native_heading_delta) < 0.1:
            raise DriverError("movement basis heading turn was not measurable")
        first_world_heading = math.atan2(first_dy, first_dx)
        second_world_heading = math.atan2(second_dy, second_dx)
        world_heading_delta = normalize_angle(second_world_heading - first_world_heading)
        if abs(world_heading_delta) < 0.05:
            raise DriverError("movement basis forward headings did not change")
        facing_sign = 1 if world_heading_delta * native_heading_delta > 0 else -1
        derivative = abs(world_heading_delta / native_heading_delta)
        if not 0.5 <= derivative <= 1.5:
            raise DriverError("movement basis facing-to-world derivative is outside bounds")
        beta_first = normalize_angle(first_world_heading - facing_sign * first_confirmed.facing)
        beta_second = normalize_angle(second_world_heading - facing_sign * second_confirmed.facing)
        beta = normalize_angle(
            math.atan2(
                math.sin(beta_first) + math.sin(beta_second),
                math.cos(beta_first) + math.cos(beta_second),
            )
        )
        if abs(normalize_angle(beta_second - beta_first)) > 0.35:
            raise DriverError("movement basis facing offset was inconsistent across headings")
        forward_min = min(first_displacement, second_displacement)
        forward_max = max(first_displacement, second_displacement)
        if forward_min < MIN_BASIS_DISPLACEMENT or forward_max / forward_min > 1.5:
            raise DriverError("movement basis repeated forward probes were inconsistent")

        # All remaining translation roles are measured independently.  Their
        # distinct corridors make a wrong binding or asymmetric speed an
        # explicit calibration failure rather than an inferred value.
        strafe_before = self._observe_motion(generation, previous=second_after)
        if strafe_before.speed > 0.25:
            self._invalidate_motion_admission()
            raise DriverError("movement basis translation calibration requires a stationary frame")
        left_route = admit_probe(strafe_before, (math.pi / 2,))
        strafe_confirmed, strafe_after, strafe_dx, strafe_dy, strafe_displacement = probe(
            strafe_before, KeyRole.STRAFE_LEFT, left_route, math.pi / 2
        )

        # The forward/left cross product is enough to establish the route
        # handedness.  Refuse a reflected basis immediately, before spending
        # physical probes on backward or right strafe and before sealing any
        # movement basis.
        cross = second_dx * strafe_dy - second_dy * strafe_dx
        if abs(cross) < MIN_BASIS_DISPLACEMENT * MIN_BASIS_DISPLACEMENT:
            raise DriverError("movement basis probes are collinear")
        handedness = 1 if cross > 0 else -1
        self._require_supported_route_handedness(handedness)

        backward_before = self._observe_motion(generation, previous=strafe_after)
        if backward_before.speed > 0.25:
            self._invalidate_motion_admission()
            raise DriverError("movement basis translation calibration requires a stationary frame")
        backward_route = admit_probe(backward_before, (math.pi,))
        backward_confirmed, backward_after, backward_dx, backward_dy, backward_displacement = probe(
            backward_before, KeyRole.MOVE_BACKWARD, backward_route, math.pi
        )

        right_before = self._observe_motion(generation, previous=backward_after)
        if right_before.speed > 0.25:
            self._invalidate_motion_admission()
            raise DriverError("movement basis translation calibration requires a stationary frame")
        right_route = admit_probe(right_before, (-math.pi / 2,))
        right_confirmed, right_after, right_dx, right_dy, right_displacement = probe(
            right_before, KeyRole.STRAFE_RIGHT, right_route, -math.pi / 2
        )

        left_world_heading = math.atan2(strafe_dy, strafe_dx)
        left_fitted_forward = normalize_angle(facing_sign * strafe_confirmed.facing + beta)
        left_expected_heading = normalize_angle(left_fitted_forward + handedness * math.pi / 2)
        left_component = strafe_dx * math.cos(left_expected_heading) + strafe_dy * math.sin(
            left_expected_heading
        )
        left_lateral = strafe_dx * math.cos(left_expected_heading + math.pi / 2) + strafe_dy * math.sin(
            left_expected_heading + math.pi / 2
        )
        if left_component <= strafe_displacement * 0.2 or abs(left_lateral) > strafe_displacement * 0.75:
            raise DriverError("movement strafe-left probe moved in the wrong direction")
        left_offset = normalize_angle(
            left_world_heading - (facing_sign * strafe_confirmed.facing + beta + handedness * math.pi / 2)
        )
        # The role names are part of the measured contract.  Check the
        # independently observed vectors against the fitted forward axis so a
        # wrong or mirrored binding is rejected before sealing the basis.
        backward_fitted_forward = normalize_angle(facing_sign * backward_confirmed.facing + beta)
        backward_expected_heading = normalize_angle(backward_fitted_forward + math.pi)
        backward_component = backward_dx * math.cos(backward_expected_heading) + backward_dy * math.sin(
            backward_expected_heading
        )
        backward_lateral = backward_dx * math.cos(
            backward_expected_heading + math.pi / 2
        ) + backward_dy * math.sin(backward_expected_heading + math.pi / 2)
        if (
            backward_component <= backward_displacement * 0.2
            or abs(backward_lateral) > backward_displacement * 0.75
        ):
            raise DriverError("movement backward probe moved in the wrong direction")
        right_fitted_forward = normalize_angle(facing_sign * right_confirmed.facing + beta)
        right_expected_heading = normalize_angle(right_fitted_forward - handedness * math.pi / 2)
        right_component = right_dx * math.cos(right_expected_heading) + right_dy * math.sin(
            right_expected_heading
        )
        right_lateral = right_dx * math.cos(right_expected_heading + math.pi / 2) + right_dy * math.sin(
            right_expected_heading + math.pi / 2
        )
        if right_component <= right_displacement * 0.2 or abs(right_lateral) > right_displacement * 0.75:
            raise DriverError("movement strafe-right probe moved in the wrong direction")
        backward_world_heading = math.atan2(backward_dy, backward_dx)
        right_world_heading = math.atan2(right_dy, right_dx)
        basis = MovementBasis(
            identity_fingerprint=second_after.identity_fingerprint,
            boot=second_after.boot,
            generation=generation,
            capture_id=f"movement:{before.boot}:{before.sequence}:{right_after.sequence}",
            before_sequence=before.sequence,
            after_sequence=right_after.sequence,
            forward_heading_offset=beta,
            # A repeated forward probe may have a slightly different speed;
            # retain the conservative measured upper bound so runtime travel
            # envelopes cannot understate the faster heading.
            forward_displacement=forward_max,
            pulse_seconds=float(pulse_seconds),
            facing_sign=facing_sign,
            strafe_heading_offset=left_offset,
            strafe_displacement=strafe_displacement,
            strafe_pulse_seconds=float(pulse_seconds),
            handedness=handedness,
            backward_displacement=backward_displacement,
            backward_pulse_seconds=float(pulse_seconds),
            strafe_right_displacement=right_displacement,
            strafe_right_pulse_seconds=float(pulse_seconds),
            backward_heading_offset=normalize_angle(
                backward_world_heading - facing_sign * backward_confirmed.facing
            ),
            strafe_right_heading_offset=normalize_angle(
                right_world_heading - facing_sign * right_confirmed.facing
            ),
        )
        self.movement_basis = basis
        return basis

    @_serialized_motion
    def execute_motion_key(self, role: KeyRole, duration: float, *, generation: int) -> MotionFrame:
        duration = self._validate_motion_key_request(role, duration)
        lease_generation = self._require_motion_interaction(generation)
        frame = self._observe_motion(generation)
        self._require_native_gate(frame)
        return self._execute_motion_key_with_frame(role, duration, generation, frame, lease_generation)

    def _validate_motion_key_request(self, role: KeyRole, duration: float) -> float:
        """Validate request shape before acquiring native observation authority."""

        if not isinstance(role, KeyRole):
            raise DriverError("motion pulse role is malformed")
        try:
            duration = float(duration)
        except (TypeError, ValueError) as exc:
            raise DriverError("motion pulse duration is malformed") from exc
        minimum = max(0.05, self._motion_profiles["move"].min_duration)
        maximum = min(MAX_PULSE_SECONDS, self._motion_profiles["move"].max_duration)
        if not math.isfinite(duration) or duration < minimum or duration > maximum:
            raise DriverError("motion pulse is below the executable minimum")
        return duration

    def _motion_target(
        self,
        role: KeyRole,
        duration: float,
        frame: MotionFrame,
    ) -> tuple[float, float, float, float]:
        """Return direction, endpoint and uncertainty envelope for one pulse."""

        measured_speed = self._measured_motion_speed(role)
        planned_distance = measured_speed * duration
        travel_envelope = self._travel_envelope(planned_distance)
        if travel_envelope > MAX_WAYPOINT_DISTANCE:
            raise DriverError("motion pulse exceeds the bounded travel envelope")
        world_forward = self._world_forward_heading(frame)
        if role is KeyRole.MOVE_FORWARD:
            direction = world_forward
        elif role is KeyRole.MOVE_BACKWARD:
            if self.movement_basis is None or self.movement_basis.backward_heading_offset is None:
                raise DriverError("movement basis has no measured backward direction")
            direction = normalize_angle(
                self.movement_basis.facing_sign * frame.facing + self.movement_basis.backward_heading_offset
            )
        elif role is KeyRole.STRAFE_LEFT:
            direction = self._world_left_heading(frame)
        elif role is KeyRole.STRAFE_RIGHT:
            if self.movement_basis is None or self.movement_basis.strafe_right_heading_offset is None:
                raise DriverError("movement basis has no measured strafe-right direction")
            direction = normalize_angle(
                self.movement_basis.facing_sign * frame.facing
                + self.movement_basis.strafe_right_heading_offset
            )
        else:
            raise DriverError("motion pulse role is outside the measured movement basis")
        return (
            direction,
            frame.x + travel_envelope * math.cos(direction),
            frame.y + travel_envelope * math.sin(direction),
            travel_envelope,
        )

    def _plan_waypoint_pulse(
        self,
        distance: float,
        measured_speed: float,
        minimum_pulse: float,
        profile: Any,
        cumulative_travel: float,
        arrival_tolerance: float,
        heading: float = 0.0,
    ) -> float:
        """Return a pulse whose whole response envelope can settle the target.

        This conservative planner admits a single pulse aimed at the target.
        A target outside the calibrated response-uncertainty envelope has no
        guaranteed endpoint, so it is refused before route/camera admission.
        Inside the named translation heading allowance, admission also proves
        the complete two-dimensional miss at both response-envelope extremes.
        The cumulative two-unit envelope is checked before the caller can
        request a route or dispatch input.
        """

        minimum_distance = measured_speed * minimum_pulse
        guaranteed_distance = arrival_tolerance / TRAVEL_UNCERTAINTY_FRACTION
        if distance > guaranteed_distance + 1e-9:
            raise DriverError("waypoint exceeds the calibrated response-uncertainty envelope")
        if distance < minimum_distance:
            minimum_error = self._waypoint_endpoint_error(
                distance,
                minimum_distance,
                heading,
            )
            if minimum_error > arrival_tolerance + 1e-9:
                raise DriverError("waypoint minimum pulse cannot guarantee the target endpoint")
            pulse = minimum_pulse
        else:
            pulse = distance / measured_speed
        pulse = min(MAX_PULSE_SECONDS, profile.max_duration, pulse)
        pulse = max(minimum_pulse, pulse)
        planned_distance = measured_speed * pulse
        pulse_envelope = self._travel_envelope(planned_distance)
        remaining_distance = MAX_WAYPOINT_DISTANCE - cumulative_travel
        if pulse_envelope > remaining_distance + 1e-9:
            raise DriverError("waypoint pulse envelope exceeds the bounded local distance")
        endpoint_error = self._waypoint_endpoint_error(
            distance,
            planned_distance,
            heading,
        )
        if endpoint_error > arrival_tolerance + 1e-9:
            raise DriverError("waypoint pulse cannot guarantee the target endpoint")
        return pulse

    @staticmethod
    def _waypoint_endpoint_error(target_distance: float, planned_distance: float, heading: float) -> float:
        """Return the worst two-dimensional endpoint miss for one pulse."""

        if not all(math.isfinite(value) for value in (target_distance, planned_distance, heading)):
            raise DriverError("waypoint endpoint geometry is malformed")
        if target_distance <= 0.0 or planned_distance <= 0.0:
            raise DriverError("waypoint endpoint distance is malformed")
        uncertainty = max(MIN_BASIS_DISPLACEMENT, planned_distance * TRAVEL_UNCERTAINTY_FRACTION)
        heading_magnitude = min(math.pi, abs(heading) + MAX_CONFIRMATION_FACING_DRIFT)
        endpoint_miss = max(
            math.hypot(
                actual_distance * math.cos(heading_magnitude) - target_distance,
                actual_distance * math.sin(heading_magnitude),
            )
            for actual_distance in (planned_distance - uncertainty, planned_distance + uncertainty)
        )
        # Confirmation position drift is a full two-dimensional ball.  Its
        # worst vector can point along the endpoint-miss vector, so adding its
        # radius after the speed/facing envelope is the conservative exact
        # support function; shifting only the scalar target distance would
        # underbound diagonal and perpendicular confirmation movement.
        return endpoint_miss + MAX_CONFIRMATION_POSITION_DRIFT

    def _execute_motion_key_with_frame(
        self,
        role: KeyRole,
        duration: float,
        generation: int,
        frame: MotionFrame,
        lease_generation: int | None = None,
        *,
        route: RouteEvidence | None = None,
    ) -> MotionFrame:
        """Dispatch a pulse using the frame whose corridor was actually proved."""

        if lease_generation is None:
            lease_generation = self._require_motion_interaction(generation)
        self._require_native_gate(frame)
        if frame.chat_focused:
            self._invalidate_motion_admission()
            raise DriverError("motion pulse is refused while the chat edit box is focused")
        if self.movement_basis is None:
            raise DriverError("motion pulse requires measured movement basis")
        if (
            self.movement_basis.identity_fingerprint != frame.identity_fingerprint
            or self.movement_basis.boot != frame.boot
            or self.movement_basis.generation != generation
        ):
            raise DriverError("movement basis is stale for the native frame")
        if not isinstance(role, KeyRole):
            raise DriverError("motion pulse role is malformed")
        try:
            duration = float(duration)
        except (TypeError, ValueError) as exc:
            raise DriverError("motion pulse duration is malformed") from exc
        minimum = max(0.05, self._motion_profiles["move"].min_duration)
        if (
            not math.isfinite(duration)
            or duration < minimum
            or duration > min(MAX_PULSE_SECONDS, self._motion_profiles["move"].max_duration)
        ):
            raise DriverError("motion pulse is below the executable minimum")
        direction, target_x, target_y, travel_envelope = self._motion_target(role, duration, frame)
        operation_local = getattr(self, "_motion_deadline_local", None)
        operation_deadline = getattr(operation_local, "deadline", None)
        if operation_deadline is not None and (
            self._native_clock() + duration + MOTION_POST_RELEASE_RESERVE_SECONDS >= operation_deadline
        ):
            raise DriverError("motion pulse cannot fit the bounded intent deadline")
        if route is None:
            route = self._observe_route(
                generation,
                target_x,
                target_y,
                frame=frame,
            )
        if (
            not route.target_visible
            or not route.ground_clear
            or not self._route_matches_frame(
                route,
                frame,
                generation,
                target_x,
                target_y,
            )
            or self._native_clock() - route.capture_monotonic > MAX_FRAME_AGE
            or self._native_clock() - frame.capture_monotonic > MAX_FRAME_AGE
        ):
            raise DriverError("motion pulse corridor was not positively proved")
        route_frame = frame
        frame = self._confirm_motion_pose(generation, frame)
        self._require_native_gate(frame, matching=route_frame)
        if (
            not self._route_matches_frame(route, route_frame, generation, target_x, target_y)
            or self._native_clock() - route.capture_monotonic > MAX_FRAME_AGE
            or self._native_clock() - route_frame.capture_monotonic > MAX_FRAME_AGE
        ):
            raise DriverError("motion pulse route evidence expired before physical commit")
        if self._native_clock() - frame.capture_monotonic > MAX_FRAME_AGE:
            raise DriverError("motion pulse frame is stale at dispatch")
        if operation_deadline is not None and (
            self._native_clock() + duration + MOTION_POST_RELEASE_RESERVE_SECONDS >= operation_deadline
        ):
            raise DriverError("motion pulse cannot fit the bounded intent deadline")
        # Recheck the controller and lease immediately before the physical
        # commit.  Interaction stop may revoke while route/model confirmation
        # is in flight, so the earlier admission cannot authorize this call.
        lease_generation = self._require_motion_interaction(generation)
        self.driver.run_motion_key_hold(
            role,
            duration,
            frame,
            generation=lease_generation,
            deadline_monotonic=operation_deadline,
        )
        after = self._observe_motion(generation, previous=frame, after_release=True)
        self._require_native_gate(after, matching=frame)
        if after.speed > 0.25:
            self._invalidate_motion_admission()
            raise DriverError("motion pulse requires settled post-release feedback")
        if (
            after.identity_fingerprint != frame.identity_fingerprint
            or after.boot != frame.boot
            or after.sequence <= frame.sequence
            or after.capture_monotonic <= frame.capture_monotonic
            or abs(after.z - frame.z) > 0.25
            or after.instance != frame.instance
            or after.zone != frame.zone
        ):
            self._invalidate_motion_admission()
            raise DriverError("motion pulse changed scene or vertical position")
        moved_x = after.x - frame.x
        moved_y = after.y - frame.y
        moved = math.hypot(moved_x, moved_y)
        if moved <= MIN_BASIS_DISPLACEMENT:
            raise DriverError("motion pulse made no measurable progress")
        if moved > travel_envelope or moved > MAX_WAYPOINT_DISTANCE:
            raise DriverError("motion pulse exceeded its proved travel envelope")
        direction_component = moved_x * math.cos(direction) + moved_y * math.sin(direction)
        if direction_component <= max(MIN_BASIS_DISPLACEMENT, moved * 0.2):
            raise DriverError("motion pulse moved in the wrong direction")
        return after

    @_serialized_motion
    def execute_camera_delta(
        self,
        delta_pixels: int,
        *,
        generation: int,
        previous: MotionFrame | None = None,
    ) -> MotionFrame:
        if (
            isinstance(delta_pixels, bool)
            or not isinstance(delta_pixels, int)
            or not 1 <= abs(delta_pixels) <= 240
        ):
            raise DriverError("camera delta is outside the bounded range")
        if self.camera_mapping is None:
            raise DriverError("camera mapping has not passed controlled feedback calibration")
        raw_expected_yaw = self.camera_mapping.yaw_per_pixel * delta_pixels
        # Reject the requested angular motion before taking any viewport or
        # physical-input path.  Checking after the drag could leave a real
        # button sequence behind for a request we already know is invalid.
        if abs(raw_expected_yaw) > MAX_CAMERA_INPUT_YAW:
            raise DriverError("camera request exceeds the bounded angular motion")
        lease_generation = self._require_motion_interaction(generation)
        frame = self._observe_motion(generation, previous=previous)
        self._require_native_gate(frame, matching=previous)
        operation_local = getattr(self, "_motion_deadline_local", None)
        operation_deadline = getattr(operation_local, "deadline", None)
        identity = self._resolve_identity(
            require_foreground=True,
            deadline=operation_deadline,
        )
        if self.camera_mapping.identity_fingerprint != identity.fingerprint:
            raise DriverError("camera mapping identity is stale")
        if self.camera_mapping.generation != generation:
            raise DriverError("camera mapping generation is stale")
        if self.camera_mapping.boot and self.camera_mapping.boot != frame.boot:
            raise DriverError("camera mapping addon boot is stale")
        viewport = self._observe_viewport(generation, frame)
        confirmed = self._confirm_motion_pose(generation, frame)
        self._require_native_gate(confirmed, matching=frame)
        plan = self._camera_drag_plan(
            confirmed,
            delta_pixels,
            identity,
            lease_generation,
            viewport,
            session_generation=generation,
            evidence_frame=frame,
        )
        if operation_deadline is not None and (
            self._native_clock() + plan.duration + MOTION_POST_RELEASE_RESERVE_SECONDS >= operation_deadline
        ):
            raise DriverError("camera drag cannot fit the bounded intent deadline")
        if self._native_clock() - frame.capture_monotonic > MAX_FRAME_AGE:
            raise DriverError("camera drag frame is stale at dispatch")
        if operation_deadline is not None and (
            self._native_clock() + plan.duration + MOTION_POST_RELEASE_RESERVE_SECONDS >= operation_deadline
        ):
            raise DriverError("camera drag cannot fit the bounded intent deadline")
        lease_generation = self._require_motion_interaction(generation)
        self.driver.run_camera_drag(
            plan,
            generation=lease_generation,
            deadline_monotonic=operation_deadline,
        )
        after = self._observe_motion(generation, previous=confirmed, after_release=True)
        self._require_native_gate(after, matching=confirmed)
        if (
            after.identity_fingerprint != confirmed.identity_fingerprint
            or after.boot != confirmed.boot
            or after.sequence <= confirmed.sequence
            or after.capture_monotonic <= confirmed.capture_monotonic
            or after.instance != confirmed.instance
            or after.zone != confirmed.zone
            or abs(after.z - confirmed.z) > 0.25
            or math.hypot(after.x - confirmed.x, after.y - confirmed.y) > 0.01
        ):
            self._invalidate_motion_admission()
            raise DriverError("camera correction changed scene or vertical position")
        # Compare the response with the confirmed pose that was used for the
        # admitted drag.  Evidence-frame drift is not physical progress.
        observed_yaw = (after.facing - confirmed.facing + math.pi) % (2.0 * math.pi) - math.pi
        expected_yaw = raw_expected_yaw
        if observed_yaw * expected_yaw <= 0.0:
            self._invalidate_motion_admission()
            raise DriverError("camera response made no signed progress")
        meaningful_progress = max(0.001, abs(expected_yaw) * 0.25)
        if abs(observed_yaw) < meaningful_progress:
            self._invalidate_motion_admission()
            raise DriverError("camera response made insufficient signed progress")
        actual_cap = min(MAX_CAMERA_INPUT_YAW, MAX_CAMERA_YAW_PER_PIXEL * abs(delta_pixels))
        if abs(observed_yaw) > actual_cap:
            self._invalidate_motion_admission()
            raise DriverError("camera response exceeded the bounded angular motion")
        response_tolerance = max(
            MIN_CAMERA_RESPONSE_ABSOLUTE_ERROR,
            abs(expected_yaw) * MAX_CAMERA_RESPONSE_RELATIVE_ERROR,
        )
        if abs(observed_yaw - expected_yaw) > response_tolerance:
            self._invalidate_motion_admission()
            raise DriverError("camera response exceeded its calibrated error bound")
        return after

    @_serialized_motion
    def execute_waypoint(self, target_x: float, target_y: float, *, generation: int) -> MotionFrame:
        self._validate_waypoint_request(target_x, target_y)
        self._require_motion_interaction(generation)
        if self.camera_mapping is None:
            raise DriverError("waypoint requires a calibrated camera mapping")
        if self.movement_basis is None:
            raise DriverError("waypoint requires a measured movement basis")
        if self.camera_mapping.generation != generation:
            raise DriverError("camera mapping generation is stale")
        if self.movement_basis.generation != generation:
            raise DriverError("movement basis generation is stale")
        self._require_supported_route_handedness(self.movement_basis)
        started = self._native_clock()
        frame = self._observe_motion(generation)
        self._require_native_gate(frame)
        if self.camera_mapping.identity_fingerprint != frame.identity_fingerprint:
            raise DriverError("camera mapping identity is stale")
        translation_stalls = 0
        camera_turn_attempts = 0
        pulses = 0
        cumulative_travel = 0.0
        profile = self._motion_profiles["move"]
        measured_speed = self._measured_motion_speed(KeyRole.MOVE_FORWARD)
        if measured_speed <= 0.0 or not math.isfinite(measured_speed):
            raise DriverError("movement basis has no measured speed")
        minimum_pulse = max(0.05, profile.min_duration)
        min_pulse_displacement = max(
            MIN_BASIS_DISPLACEMENT,
            measured_speed * minimum_pulse,
        )
        if min_pulse_displacement > MAX_WAYPOINT_DISTANCE:
            raise DriverError("movement basis minimum pulse exceeds the local distance bound")
        arrival_tolerance = max(0.1, min_pulse_displacement * 0.5)
        while self._native_clock() - started < MAX_WAYPOINT_SECONDS and pulses < MAX_WAYPOINT_PULSES:
            self._require_motion_interaction(generation)
            heading, distance = waypoint_heading_error(frame, target_x, target_y, self.movement_basis)
            if distance <= arrival_tolerance:
                return frame

            # Preflight the target before either a camera correction or a
            # translation route is admitted.  A camera turn cannot make an
            # otherwise unguaranteed translation endpoint safe.
            admission_heading = math.copysign(
                min(abs(heading), WAYPOINT_TRANSLATION_HEADING_TOLERANCE),
                heading,
            )
            pulse = self._plan_waypoint_pulse(
                distance,
                measured_speed,
                minimum_pulse,
                profile,
                cumulative_travel,
                arrival_tolerance,
                admission_heading,
            )
            if abs(heading) > WAYPOINT_TRANSLATION_HEADING_TOLERANCE:
                pixels = int(round(heading / self.camera_mapping.yaw_per_pixel))
                pixels = max(-120, min(120, pixels))
                if pixels == 0:
                    raise DriverError("camera mapping cannot express the required heading")
                if camera_turn_attempts >= MAX_WAYPOINT_CAMERA_TURNS:
                    raise DriverError("waypoint exceeded its camera correction attempt budget")
                frame = self.execute_camera_delta(pixels, generation=generation, previous=frame)
                camera_turn_attempts += 1
            else:
                _, route_target_x, route_target_y, _ = self._motion_target(
                    KeyRole.MOVE_FORWARD,
                    pulse,
                    frame,
                )
                route = self._observe_route(
                    generation,
                    route_target_x,
                    route_target_y,
                    frame=frame,
                )
                if not route.target_visible or not route.ground_clear:
                    raise DriverError("route was not positively proved for translation")
                if (
                    not self._route_matches_frame(
                        route,
                        frame,
                        generation,
                        route_target_x,
                        route_target_y,
                    )
                    or self._native_clock() - route.capture_monotonic > MAX_FRAME_AGE
                    or self._native_clock() - frame.capture_monotonic > MAX_FRAME_AGE
                ):
                    raise DriverError("translation route evidence is stale")
                before_move = frame
                lease_generation = self._require_motion_interaction(generation)
                frame = self._execute_motion_key_with_frame(
                    KeyRole.MOVE_FORWARD,
                    pulse,
                    generation,
                    before_move,
                    lease_generation,
                    route=route,
                )
                moved_x = frame.x - before_move.x
                moved_y = frame.y - before_move.y
                moved = math.hypot(moved_x, moved_y)
                cumulative_travel += moved
                if cumulative_travel > MAX_WAYPOINT_DISTANCE:
                    raise DriverError("waypoint cumulative travel exceeded its local bound")
                desired_heading = self._world_forward_heading(before_move)
                forward_component = moved_x * math.cos(desired_heading) + moved_y * math.sin(desired_heading)
                if moved <= MIN_BASIS_DISPLACEMENT or forward_component <= max(
                    MIN_BASIS_DISPLACEMENT, moved * 0.2
                ):
                    raise DriverError("waypoint moved in the wrong direction or made no progress")
                if abs(frame.z - before_move.z) > 0.25:
                    raise DriverError("waypoint encountered abnormal vertical movement")
                # Compare this pulse's endpoint with the distance that was
                # proved immediately before its dispatch. This counts the
                # first ineffective pulse and gives exactly three attempts
                # before the translation-stall budget is exhausted.
                post_pulse_distance = math.hypot(frame.x - target_x, frame.y - target_y)
                if post_pulse_distance >= distance - 0.005:
                    translation_stalls += 1
                    if translation_stalls >= 3:
                        raise DriverError("waypoint made no measurable progress")
                else:
                    translation_stalls = 0
            pulses += 1
        raise DriverError("waypoint did not settle before its bounded deadline")

    @staticmethod
    def _validate_waypoint_request(target_x: float, target_y: float) -> None:
        """Reject malformed target coordinates before native observation."""

        if any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value))
            for value in (target_x, target_y)
        ):
            raise DriverError("waypoint target coordinates are malformed")

    def _recover_login(self) -> None:
        if self.recovery_attempts >= 4:
            raise ModelError("bounded login recovery attempt budget exhausted")
        decision = self._call_model_adapter(
            "decide",
            self._capture_model(),
            target="game-client",
            verified_crop=self.config.profile.model_crop,
        )
        if decision.action in self.recovery_actions:
            raise ModelError(f"login recovery action {decision.action} exceeded its one-attempt budget")
        # Consume and persist the named-action retry budget before dispatch.
        # A crash or guardian revoke after intent persistence must never replay
        # the same recovery click on the next process.
        with self.controller.lock:
            self.controller.record_recovery_attempt(decision.action)
        self.recovery_attempts = self.controller.journal.read().get(
            "recoveryAttempts", self.recovery_attempts
        )
        self.recovery_actions = set(
            self.controller.journal.read().get("recoveryActions", self.recovery_actions)
        )
        self._run_action(decision.action, self.last_snapshot, target="game-client")

    def _claim_motion_fence(self) -> threading.RLock | None:
        """Claim the one capture/decoder/physical-action ownership fence.

        The recurring engine must yield immediately when an interaction intent
        already owns the fence.  Interaction stop does not call this helper;
        it revokes the guardian directly so cancellation cannot wait behind a
        capture, model call, or held native process.
        """

        lock = getattr(self, "_motion_intent_lock", None)
        if lock is None:
            lock = threading.RLock()
            self._motion_intent_lock = lock
        if not lock.acquire(blocking=False):
            return None
        return lock

    def capture_paused_region_sample(
        self,
        *,
        expected_generation: int,
        parent_started: float,
        deadline: float,
        config_file_sha256: str,
        config_semantic_sha256: str,
    ) -> dict[str, Any]:
        """Capture one bounded, read-only region sample through this owner."""

        owner_entered = time.monotonic()
        request_dir: Path | None = None
        output: Path | None = None
        phase = "request_validation"
        published = False
        sample: dict[str, Any] | None = None
        failure: Exception | None = None
        failure_record: dict[str, Any] = {}
        capture_returned: float | None = None
        motion_fence = None
        source_binding: dict[str, str] | None = None
        model_calls_before: dict[str, int] | None = None
        model_calls_after: dict[str, int] | None = None
        model_call_delta: dict[str, int] | None = None
        response_ready: float | None = None
        driver = self.driver
        backend = driver.backend
        guardian = driver.guardian
        owner_config_semantic_sha256 = self._loaded_config_semantic_sha256
        if isinstance(getattr(backend, "last_region_attempt", None), dict):
            backend.last_region_attempt = {
                "stage": "not_started",
                "request_started": None,
                "lock_acquired": None,
                "ack_sent": None,
                "capture_started": None,
                "capture_returned": None,
                "attempt_retired": None,
            }
        if isinstance(self._runtime_source_binding, dict):
            source_binding = dict(self._runtime_source_binding)
        model_calls_before = self._model_call_snapshot()
        try:
            if (
                isinstance(expected_generation, bool)
                or not isinstance(expected_generation, int)
                or expected_generation <= 0
            ):
                raise DriverError("paused region generation must be a positive integer")
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                for value in (parent_started, deadline)
            ):
                raise DriverError("paused region timestamps must be finite monotonic numbers")
            parent_started = float(parent_started)
            deadline = float(deadline)
            for label, digest in (
                ("config file hash", config_file_sha256),
                ("semantic config hash", config_semantic_sha256),
            ):
                if (
                    not isinstance(digest, str)
                    or len(digest) != 64
                    or any(character not in "0123456789abcdef" for character in digest)
                ):
                    raise DriverError(f"paused region {label} is malformed")
            if not _driver_profile_matches_config(driver, self.config):
                phase = "config_binding"
                raise DriverError("owning driver profile does not match the daemon config")
            if config_semantic_sha256 != owner_config_semantic_sha256:
                phase = "config_binding"
                raise DriverError("paused region semantic config hash does not match the owner config")
            now = time.monotonic()
            if parent_started > now or now - parent_started > 1.0:
                raise DriverError("paused region parent start is future or expired")
            if deadline <= now or deadline > parent_started + 1.0:
                raise DriverError("paused region absolute deadline is expired or exceeds one second")

            phase = "owner_preconditions"
            motion_fence = self._claim_motion_fence()
            if motion_fence is None:
                raise DriverError("another motion or capture intent is already in flight")
            with self.controller.lock:
                self._check_paused_region_admission(expected_generation)

            if not isinstance(backend, X11Backend):
                raise DriverError("paused region sample requires the configured production X11 backend")
            if backend._cancel_active.is_set():
                raise DriverError(
                    "paused region sample refuses a capture-revoked backend; start a fresh owner"
                )
            if not guardian.lease.held:
                raise DriverError("owning daemon does not hold the canonical desktop lease")
            if guardian.armed or guardian.held:
                raise DriverError("paused region sample requires an unarmed, unheld Guardian")
            if guardian.active_process_groups or guardian.observer_process_groups:
                raise DriverError("paused region sample refuses another owned process group")
            if backend._active_processes or backend.active_process_groups:
                raise DriverError("paused region sample refuses another backend process")
            if self._native_bootstrap_ready.is_set():
                raise DriverError("paused region sample refuses pending native bootstrap evidence")
            calibration = self._calibration_operation_snapshot()
            if calibration.get("state") in {"starting", "running"}:
                raise DriverError("paused region sample refuses an active calibration operation")
            calibration_thread = self._calibration_thread
            if calibration_thread is not None and calibration_thread.is_alive():
                raise DriverError("paused region sample refuses a live calibration worker")
            if guardian._watchdog_failed:
                raise DriverError("paused region sample refuses an unhealthy input watchdog")
            guardian.admission_gate_ready()
            profile = driver.profile
            executable = profile.telemetry_region_executable
            executable_hash = profile.telemetry_region_executable_sha256
            if executable is None or executable_hash is None:
                raise DriverError("paused region sample requires a configured telemetry producer")
            profile.validate()

            root = Path(self.config.capture_dir)
            root.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.chmod(root, 0o700)
            request_dir = Path(tempfile.mkdtemp(prefix="paused-region-", dir=root))
            os.chmod(request_dir, 0o700)
            output = request_dir / "capture.png"
            # A request rejected before the native producer starts must not
            # inherit the previous request's protocol-stage timestamps.
            backend.last_region_attempt = {
                "stage": "not_started",
                "request_started": None,
                "lock_acquired": None,
                "ack_sent": None,
                "capture_started": None,
                "capture_returned": None,
                "attempt_retired": None,
            }
            phase = "source_binding"
            source_binding = self._runtime_source_binding_for_diagnostic()

            phase = "identity_before_capture"
            if time.monotonic() >= deadline:
                raise DriverError("paused region deadline expired before identity resolution")
            identity = driver.resolve_identity(deadline_monotonic=deadline)
            identity_record = {
                "pid": identity.pid,
                "process_start": identity.process_start,
                "xid": identity.xid,
                "child_xid": identity.child_xid,
                "executable": identity.executable,
                "display": identity.display,
                "fingerprint": identity.fingerprint,
                "child_geometry": list(identity.child_geometry),
            }
            before_receipt = backend.last_region_receipt

            def admit_observer(start):
                self._check_paused_region_config_binding(
                    driver, owner_config_semantic_sha256, config_semantic_sha256
                )
                with self.controller.lock:
                    self._check_paused_region_admission(expected_generation)
                    return guardian.observer_dispatch_admission(start)

            def unregister_observer(pgid: int) -> None:
                guardian.unregister_observer_process(pgid)

            phase = "region_capture"
            driver.capture_native_region_for_identity(
                identity,
                destination=output,
                deadline_monotonic=deadline,
                observer_admission=admit_observer,
                observer_reaped=unregister_observer,
            )
            capture_returned = time.monotonic()
            published = output.is_file() and not output.is_symlink()
            if not published:
                phase = "png_publication"
                raise DriverError("paused region producer returned without its PNG publication")
            output_bytes = output.read_bytes()
            if not output_bytes or len(output_bytes) > 131072:
                phase = "png_publication"
                raise DriverError("paused region PNG exceeds its bounded output size")
            receipt = backend.last_region_receipt
            if receipt is None or receipt is before_receipt:
                raise DriverError("paused region capture has no new actual producer receipt")
            actual_receipt = asdict(receipt)
            actual_receipt["rectangle"] = list(receipt.rectangle)
            if (
                receipt.executable_sha256 != executable_hash
                or receipt.output_sha256 != hashlib.sha256(output_bytes).hexdigest()
                or receipt.output_bytes != len(output_bytes)
                or receipt.attempt_retired is not True
            ):
                phase = "producer_binding"
                raise DriverError("paused region producer receipt does not bind its published PNG")
            cleanup = self._paused_region_cleanup_snapshot(output, backend, guardian)
            source = {
                "api": "org.gnome.Shell.Screenshot.ScreenshotArea",
                "branch": receipt.owner_branch,
                "rectangle": list(receipt.rectangle),
            }
            config_binding = {
                "request_config_file_sha256": config_file_sha256,
                "request_config_semantic_sha256": config_semantic_sha256,
                "owner_config_semantic_sha256": owner_config_semantic_sha256,
                "display": profile.display,
                "canvas_crop": list(profile.canvas_crop),
            }
            producer_binding = {"path": str(executable), "sha256": executable_hash}
            sample = {
                "generation": expected_generation,
                "parent_started": parent_started,
                "deadline": deadline,
                "owner_entered": owner_entered,
                "capture_returned": capture_returned,
                "identity": identity_record,
                "identity_after": None,
                "source": source,
                "config": config_binding,
                "producer": producer_binding,
                "receipt": actual_receipt,
                "png_sha256": hashlib.sha256(output_bytes).hexdigest(),
                "png_bytes": len(output_bytes),
                "png_base64": base64.b64encode(output_bytes).decode("ascii"),
                "artifact_directory": str(request_dir),
                "artifact_png": str(output),
                "cleanup": cleanup,
                "source_binding": source_binding,
                "model_calls_before": model_calls_before,
                "model_calls_after": None,
                "model_call_delta": None,
                "response_ready": None,
            }
            if time.monotonic() >= deadline:
                raise DriverError("paused region deadline expired before response serialization")
            phase = "owner_post_capture_check"
            identity_after = driver.resolve_identity(deadline_monotonic=deadline)
            if identity_after.fingerprint != identity.fingerprint:
                raise DriverError("paused region client identity changed during capture")
            try:
                self._check_paused_region_config_binding(
                    driver, owner_config_semantic_sha256, config_semantic_sha256
                )
            except Exception:
                phase = "config_binding"
                raise
            with self.controller.lock:
                self._check_paused_region_admission(expected_generation)
            if guardian.armed or not guardian.lease.held:
                raise DriverError("paused region capture changed the owning lease or armed state")
            guardian.admission_gate_ready()
            cleanup = self._paused_region_cleanup_snapshot(output, backend, guardian)
            if cleanup["empty"] is not True:
                phase = "cleanup"
                raise DriverError("paused region capture did not retire its owner process and attempts")
            sample["identity_after"] = identity_after.fingerprint
            sample["cleanup"] = cleanup
            phase = "owner_receipt_persist"
        except Exception as exc:
            failure = exc
        finally:
            if request_dir is not None:
                backend = self.driver.backend
                guardian = self.driver.guardian
                cleanup = self._paused_region_cleanup_snapshot(output, backend, guardian)
                if failure is None and source_binding is not None:
                    try:
                        if self._runtime_source_binding_for_diagnostic() != source_binding:
                            raise DriverError("paused region diagnostic source binding drifted")
                    except Exception as source_error:
                        failure = source_error
                        phase = "source_binding"
                # The after snapshot closes the full owner interval, including
                # the final source check.  A concurrent model call during that
                # last verification must remain attributable to this sample.
                model_calls_after = self._model_call_snapshot()
                if model_calls_before is not None:
                    model_call_delta = {
                        key: model_calls_after[key] - model_calls_before[key]
                        for key in ("started", "succeeded", "failed")
                    }
                response_ready = time.monotonic()
                owner_returned = time.monotonic()
                producer_attempt = dict(backend.last_region_attempt)
                if producer_attempt.get("stage") == "not_started" and isinstance(cleanup.get("empty"), bool):
                    # A pre-admission refusal has no producer receipt to retire.
                    # Its terminal cleanup ledger is the only observation that
                    # can truthfully establish that no attempt remains.
                    producer_attempt["attempt_retired"] = cleanup["empty"]
                if sample is not None:
                    sample["owner_returned"] = owner_returned
                    sample["cleanup"] = cleanup
                    sample["model_calls_after"] = model_calls_after
                    sample["model_call_delta"] = model_call_delta
                    sample["response_ready"] = response_ready
                failure_record = {
                    "phase": phase,
                    "error": f"{type(failure).__name__}: {failure}" if failure else "",
                    "owner_entered": owner_entered,
                    "owner_returned": owner_returned,
                    "artifact_directory": str(request_dir),
                    "receipt_path": str(request_dir / "receipt.json"),
                    "published_png": str(output)
                    if published and output is not None and output.is_file()
                    else None,
                    "producer_attempt": producer_attempt,
                    "cleanup": cleanup,
                    "generation": expected_generation,
                    "config_file_sha256": config_file_sha256,
                    "config_semantic_sha256": config_semantic_sha256,
                    "owner_config_semantic_sha256": owner_config_semantic_sha256,
                    "lease_held": guardian.lease.held,
                    "armed": guardian.armed,
                    "source_binding": source_binding,
                    "model_calls_before": model_calls_before,
                    "model_calls_after": model_calls_after,
                    "model_call_delta": model_call_delta,
                }
                if failure is not None:
                    failure_record["sample"] = sample
                    failure_record["response_ready"] = response_ready
                    try:
                        self._persist_paused_region_receipt(
                            request_dir / "receipt.json", {"ok": False, "failure": failure_record}
                        )
                    except Exception as persist_error:
                        failure_record["receipt_persist_error"] = str(persist_error)
            else:
                cleanup = None
                try:
                    cleanup = self._paused_region_cleanup_snapshot(output, backend, guardian)
                except Exception:
                    cleanup = {
                        "backend_processes": None,
                        "backend_groups": None,
                        "guardian_observer_groups": None,
                        "guardian_active_groups": None,
                        "attempt_directories": None,
                        "lease_held": None,
                        "watchdog_healthy": None,
                        "armed": None,
                        "empty": False,
                    }
                model_calls_after = self._model_call_snapshot()
                model_call_delta = {
                    key: model_calls_after[key] - model_calls_before[key]
                    for key in ("started", "succeeded", "failed")
                }
                response_ready = time.monotonic()
                owner_returned = time.monotonic()
                if failure is not None:
                    producer_attempt = dict(getattr(backend, "last_region_attempt", {}))
                    if producer_attempt.get("stage") == "not_started" and isinstance(
                        cleanup.get("empty"), bool
                    ):
                        producer_attempt["attempt_retired"] = cleanup["empty"]
                    failure_record = {
                        "phase": phase,
                        "error": f"{type(failure).__name__}: {failure}",
                        "owner_entered": owner_entered,
                        "owner_returned": owner_returned,
                        "artifact_directory": None,
                        "receipt_path": None,
                        "published_png": None,
                        "producer_attempt": producer_attempt,
                        "cleanup": cleanup,
                        "generation": expected_generation,
                        "config_file_sha256": config_file_sha256,
                        "config_semantic_sha256": config_semantic_sha256,
                        "owner_config_semantic_sha256": owner_config_semantic_sha256,
                        "lease_held": guardian.lease.held,
                        "armed": guardian.armed,
                        "source_binding": source_binding,
                        "model_calls_before": model_calls_before,
                        "model_calls_after": model_calls_after,
                        "model_call_delta": model_call_delta,
                        "response_ready": response_ready,
                    }
            if motion_fence is not None:
                motion_fence.release()
        if failure is None:
            assert sample is not None and request_dir is not None
            try:
                success_receipt = self._paused_region_success_receipt(sample)
                self._persist_paused_region_receipt(request_dir / "receipt.json", success_receipt)
            except Exception as persist_error:
                failure = persist_error
                failure_record["phase"] = "owner_receipt_persist"
                failure_record["error"] = f"{type(persist_error).__name__}: {persist_error}"
                failure_record["sample"] = sample
                sample["response_ready"] = response_ready
                failure_record["response_ready"] = response_ready
                try:
                    self._persist_paused_region_receipt(
                        request_dir / "receipt.json", {"ok": False, "failure": failure_record}
                    )
                except Exception:
                    pass
        if failure is not None:
            result: dict[str, Any] = {"ok": False, "error": f"{type(failure).__name__}: {failure}"}
            if sample is not None:
                result["sample"] = sample
            if failure_record:
                result["failure"] = {
                    key: (
                        {name: item for name, item in value.items() if name != "png_base64"}
                        if key == "sample" and isinstance(value, dict)
                        else value
                    )
                    for key, value in failure_record.items()
                }
            return result
        assert sample is not None
        return {"ok": True, "sample": sample}

    def _check_paused_region_config_binding(
        self, driver: Any, initial_sha256: str, requested_sha256: str
    ) -> None:
        current_sha256 = session_config_semantic_sha256(self.config)
        if (
            current_sha256 != self._loaded_config_semantic_sha256
            or current_sha256 != initial_sha256
            or current_sha256 != requested_sha256
        ):
            raise DriverError("paused region semantic config changed during capture")
        if not _driver_profile_matches_config(driver, self.config):
            raise DriverError("owning driver profile no longer matches the daemon config")

    def _check_paused_region_admission(self, expected_generation: int) -> None:
        status = self.controller.status()
        if status.state != ControllerState.PAUSED or status.generation != expected_generation:
            raise DriverError("paused region owner state or generation changed")
        if status.stop_requested or status.closeout_requested or status.action_intent:
            raise DriverError("paused region owner has an active lifecycle or action intent")
        if status.mode.value == "interaction":
            raise DriverError("paused region owner refuses interaction mode")
        if self._native_bootstrap_ready.is_set():
            raise DriverError("paused region owner has pending native bootstrap evidence")
        if self._native_baseline_ready.is_set():
            raise DriverError("paused region owner has active native baseline readiness")
        operation = self._calibration_operation_snapshot()
        if operation.get("state") in {"starting", "running"}:
            raise DriverError("paused region owner has an active calibration operation")

    @staticmethod
    def _paused_region_cleanup_snapshot(output: Path | None, backend: Any, guardian: Any) -> dict[str, Any]:
        attempts = []
        if output is not None:
            attempts = sorted(
                {
                    str(path)
                    for pattern in (
                        f".{output.name}.telemetry-*",
                        f"..{output.name}.telemetry-*.retired-*",
                    )
                    for path in output.parent.glob(pattern)
                }
            )
        active = len(backend._active_processes)
        groups = sorted(backend.active_process_groups)
        observer_groups = sorted(guardian.observer_process_groups)
        guardian_groups = sorted(guardian.active_process_groups)
        lease_held = guardian.lease.held
        watchdog_healthy = not guardian._watchdog_failed
        return {
            "backend_processes": active,
            "backend_groups": groups,
            "guardian_observer_groups": observer_groups,
            "guardian_active_groups": guardian_groups,
            "attempt_directories": attempts,
            "lease_held": lease_held,
            "watchdog_healthy": watchdog_healthy,
            "armed": guardian.armed,
            "empty": active == 0
            and groups == []
            and not observer_groups
            and not guardian_groups
            and not attempts,
        }

    @staticmethod
    def _paused_region_success_receipt(sample: dict[str, Any]) -> dict[str, Any]:
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
            "source_binding",
            "model_calls_before",
            "model_calls_after",
            "model_call_delta",
            "response_ready",
        }
        if set(sample) != expected_fields:
            raise DriverError("paused region success sample has an incomplete final schema")
        timestamps = (
            sample["owner_entered"],
            sample["capture_returned"],
            sample["response_ready"],
            sample["owner_returned"],
        )
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value))
            for value in timestamps
        ) or not (
            sample["owner_entered"]
            <= sample["capture_returned"]
            <= sample["response_ready"]
            <= sample["owner_returned"]
        ):
            raise DriverError("paused region success timestamps are incomplete or out of order")
        receipt = {"ok": True, **sample}
        encoded = (json.dumps(receipt, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode(
            "utf-8"
        )
        if len(encoded) > 196608:
            raise DriverError("paused region final receipt exceeds its durable size bound")
        if len(json.dumps(sample, separators=(",", ":"), allow_nan=False).encode("utf-8")) > 480000:
            raise DriverError("paused region response metadata exceeds its bound")
        return receipt

    @staticmethod
    def _persist_paused_region_receipt(path: Path, value: dict[str, Any]) -> None:
        encoded = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
        if len(encoded) > 196608:
            raise DriverError("paused region receipt exceeds its size bound")
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

    def _reconcile_completed_logout_without_agent(self, *, generation: int) -> bool:
        """Resolve a completed logout from read-only character-select evidence.

        Logout flushes SavedVariables and removes the Agent surface, so the
        postcondition cannot include a fabricated boot or telemetry frame.  A
        fresh named character-select observation plus stable empty files is the
        complete proof; otherwise recovery must remain pending and may not
        issue a relogin action.
        """

        with self.controller.lock:
            status = self.controller.status()
            if status.state != ControllerState.RECONCILE or status.generation != generation:
                return False
            if self.controller.journal.read().get("restartUncertain") is not True:
                return False
            if status.action_intent != "logout":
                return False
            fence = self.controller.observation_fence()
        character_select = getattr(self.driver, "character_select_observed", None)
        try:
            observed_character_select = callable(character_select) and character_select()
        except (DriverError, EvidenceError, OSError, ValueError):
            return False
        if not observed_character_select:
            return False
        if not all((self.config.saved_variables, self.config.companion_state, self.config.data_lua)):
            raise EvidenceError("completed logout reconciliation paths are not configured")
        assert self.config.saved_variables is not None
        assert self.config.companion_state is not None
        assert self.config.data_lua is not None
        try:
            stable_empty = queues_empty(
                self.config.saved_variables,
                self.config.companion_state,
                self.config.data_lua,
                settled_uid=status.last_uid or None,
            )
        except (EvidenceError, OSError, ValueError):
            return False
        if not stable_empty:
            return False
        with self.controller.lock:
            current = self.controller.status()
            if current.generation != generation or current.state != ControllerState.RECONCILE:
                return False
            self.controller.resolve_restart_intent(
                observed_boot="",
                observed_uid="",
                uploaded_ids=set(),
                data_ack_ids=set(),
                loaded_ids=set(),
                pending_ids=set(),
                scanner_phase=None,
                scanner_idle=False,
                stable_scan_ids=frozenset(),
                stable_sweep_ids=frozenset(),
                stable_format2_verified=False,
                stable_files_complete=True,
                observed_scene="character_select",
                expected_generation=current.generation,
                expected_state=ControllerState.RECONCILE,
                fence=fence,
            )
        return self.controller.status().state == ControllerState.STOPPED

    def _reconcile_menu_intent_without_agent(self, *, generation: int) -> bool:
        """Consume a persisted menu intent from one fresh visual observation.

        Disconnect and character-select screens do not publish the Agent
        surface.  A missing frame therefore cannot authorize login recovery or
        replay the uncertain click.  The driver's named observer captures the
        current client and binds the scene facts to the verified window
        identity; the controller then clears only the already-persisted intent.
        A failed or mismatched observation deliberately leaves RECONCILE in
        place for the next owner poll.
        """

        menu_states = {
            "dismiss_disconnect": "game_client",
            "reconnect_game": "character_select",
            "select_arthur": "arthur_selected",
        }
        with self.controller.lock:
            status = self.controller.status()
            if status.state != ControllerState.RECONCILE or status.generation != generation:
                return False
            if self.controller.journal.read().get("restartUncertain") is not True:
                return False
            expected_state = menu_states.get(status.action_intent)
            if expected_state is None:
                return False
            fence = self.controller.observation_fence()

        observe = getattr(self.driver, "observe_named_state", None)
        if not callable(observe):
            return True
        try:
            observation = observe(expected_state)
        except (DriverError, OSError, ValueError):
            # A stale scene or a transient capture is still an unresolved
            # external effect.  Never fall through to _recover_login.
            return True
        if not isinstance(observation, NamedStateObservation):
            return True
        facts = dict(observation.facts)
        if observation.state != expected_state:
            return True
        if observation.identity_fingerprint != self.driver.resolve_identity().fingerprint:
            return True
        scene = "character_select" if expected_state == "arthur_selected" else expected_state
        observed_modal = facts.get("modal", "")
        observed_character = facts.get("character", "")
        selected_arthur = expected_state == "arthur_selected"
        # The named visual producer is the positive postcondition.  It is
        # capture-bound and identity-bound; a menu scene has no Agent boot, so
        # this consumer must never copy a stale telemetry boot or synthesize a
        # new one.  The controller's menu-intent branch accepts this explicit
        # no-Agent observation boundary.
        with self.controller.lock:
            current = self.controller.status()
            if current.generation != generation or current.state != ControllerState.RECONCILE:
                return True
            self.controller.resolve_restart_intent(
                observed_boot="",
                observed_uid="",
                uploaded_ids=set(),
                data_ack_ids=set(),
                loaded_ids=set(),
                pending_ids=set(),
                scanner_phase=None,
                scanner_idle=False,
                stable_scan_ids=frozenset(),
                stable_sweep_ids=frozenset(),
                stable_format2_verified=False,
                stable_files_complete=False,
                observed_scene=scene,
                observed_modal=observed_modal,
                observed_character=observed_character,
                selected_arthur=selected_arthur,
                action_postcondition=True,
                expected_generation=current.generation,
                expected_state=ControllerState.RECONCILE,
                fence=fence,
            )
        return True

    @staticmethod
    def _command_action_kind(command: str, state: ControllerState) -> str:
        if command == "/reload":
            if state in {ControllerState.ACK_RELOAD_SENT, ControllerState.ACK_RELOAD_WAIT}:
                return "ack_reload"
            return "save_reload"
        mapping = {
            "/crowley scan": "scan",
            "/crowley session fence": "pre_logout_fence",
            "/logout": "logout",
        }
        try:
            return mapping[command]
        except KeyError as exc:
            raise DriverError(f"unsupported command {command!r}") from exc

    def _action_deadline(self, action: str) -> int:
        if action == "scan":
            return self.config.sweep_cap_seconds
        if action == "save_reload":
            return self.config.reload_deadline_seconds
        if action in {"ack_reload", "logout", "pre_logout_fence"}:
            return self.config.ack_deadline_seconds
        return self.config.reload_deadline_seconds

    def _run_action(self, name: str, snapshot: dict[str, Any], **kwargs: Any) -> None:
        with self.controller.lock:
            status = self.controller.status()
            if status.state in {
                ControllerState.PAUSED,
                ControllerState.BLOCKED,
                ControllerState.STOPPED,
            }:
                raise DriverError("action dispatch is not allowed in the current state")
            if status.stop_requested:
                raise DriverError("action dispatch is not allowed after stop")
            if status.mode.value == "interaction":
                raise DriverError("engine action is not allowed in interaction mode")
            self.controller.set_action_intent(name, deadline_seconds=self._action_deadline(name))
            self.controller.action_result("preparing")
            controller_generation = status.generation
        generation = self.driver.guardian.generation
        self._last_action_generation = generation
        expected_identity = self.driver.resolve_identity().fingerprint

        def dispatch_allowed() -> None:
            with self.controller.lock:
                current = self.controller.status()
                if current.generation != controller_generation or current.state in {
                    ControllerState.PAUSED,
                    ControllerState.BLOCKED,
                    ControllerState.STOPPED,
                }:
                    raise DriverError("action dispatch was revoked")
                if current.mode.value == "interaction" or current.action_intent != name:
                    raise DriverError("action dispatch was revoked by interaction mode")
                if (
                    current.lease_generation != self.driver.guardian.generation
                    or not self.driver.guardian.armed
                ):
                    raise DriverError("action input lease is stale or revoked")

        def guard(identity: Any) -> bool:
            if identity.fingerprint != expected_identity:
                return False
            if name == "open_ah" and snapshot.get("ahOpen") is True:
                return False
            if name == "logout":
                context = snapshot.get("context", {})
                pending = snapshot.get("pending", {}).get("ids", [])
                if context.get("character") != self.config.profile.character:
                    return False
                if context.get("realm") != self.config.profile.realm:
                    return False
                if pending:
                    return False
                if not self._logout_scanner_idle(snapshot, self.controller.status().last_uid):
                    return False
            return True

        native_named = isinstance(self.driver.backend, X11Backend) and name in {
            "dismiss_disconnect",
            "reconnect_game",
            "select_arthur",
            "enter_world",
            "open_ah",
        }
        if native_named:
            dispatch_allowed()
            self.driver.verify_named_action(name, "before")
        before_observation = self.driver.last_named_observation if native_named else None
        dispatch_allowed()
        self.driver.run(name, generation, precondition=guard, postcondition=guard, **kwargs)
        if native_named:
            if before_observation is None:
                raise DriverError(f"{name} has no sealed pre-action observation")
            transition_started_at = self._native_clock()
            identity = self.driver.resolve_identity()
            ancestry = tuple(dict.fromkeys((identity.child_xid, identity.xid)))
            try:
                wait_plan = plan_context_wait(
                    self.driver._NAMED_ACTION_STATES[name][1],
                    BindingMetadata(
                        identity_fingerprint=before_observation.identity_fingerprint,
                        capture_id=before_observation.capture_id,
                        capture_sequence=before_observation.capture_sequence,
                        generation=generation,
                        target_xid=identity.child_xid,
                        target_ancestry=ancestry,
                        source=before_observation.source,
                        boot=before_observation.boot,
                    ),
                    started_at=transition_started_at,
                    policy=WaitPolicy(
                        timeout=20.0,
                        poll_interval=0.25,
                        settle_count=2,
                        max_observation_age=5.0,
                    ),
                    allow_source_boot_change=name == "enter_world",
                )
            except ExecutorError as exc:
                raise DriverError(f"{name} transition wait plan is invalid: {exc}") from exc
            observations: list[FreshObservation] = []
            last_error: DriverError | None = None
            settled_observation: NamedStateObservation | None = None
            wait_deadline = wait_plan.started_at + wait_plan.policy.timeout
            for poll_at in wait_plan.poll_times():
                now = self._native_clock()
                if now >= wait_deadline:
                    break
                sleep_for = min(max(0.0, poll_at - now), wait_deadline - now)
                if sleep_for > 0:
                    time.sleep(sleep_for)
                if self._native_clock() >= wait_deadline:
                    break
                # Admission and revocation failures are terminal.  Only the
                # observation itself may be retried while the absolute
                # deadline remains.
                try:
                    dispatch_allowed()
                    self.driver.guardian.check(generation)
                except GuardianError as exc:
                    raise DriverError(str(exc)) from exc
                if self._native_clock() >= wait_deadline:
                    break
                try:
                    # The driver owns the capture/model implementation, but
                    # this wait still has one absolute transition deadline.
                    # Publish it as a scoped capability so every native and
                    # visual producer in ``observe_named_state`` can consume
                    # the same remaining budget instead of starting a fresh
                    # timeout for each poll.
                    self._named_observation_deadline = wait_deadline
                    try:
                        observed = self.driver.observe_named_state(wait_plan.expected_context)
                    finally:
                        self._named_observation_deadline = None
                    fresh = FreshObservation(
                        context=observed.state,
                        identity_fingerprint=observed.identity_fingerprint,
                        generation=generation,
                        capture_sequence=observed.capture_sequence,
                        observed_at=observed.observed_monotonic,
                        source=observed.source,
                        boot=observed.boot,
                        capture_id=observed.capture_id,
                        received_at=self._native_clock(),
                    )
                    current_now = self._native_clock()
                    if accepts_observation(wait_plan, fresh, now=current_now):
                        observations.append(fresh)
                        if observations_settled(
                            wait_plan,
                            tuple(observations),
                            now=current_now,
                        ):
                            settled_observation = observed
                            break
                    else:
                        # A rejected capture is a broken consecutive settle
                        # run; it must never silently preserve prior evidence.
                        observations.clear()
                except (DriverError, ExecutorError, ModelError) as exc:
                    last_error = exc if isinstance(exc, DriverError) else DriverError(str(exc))
                    observations.clear()
                    if self._native_clock() >= wait_deadline:
                        break
                    continue
            if settled_observation is None:
                raise last_error or DriverError(f"{name} named postcondition did not settle before deadline")
            try:
                self.driver.verify_named_action(name, "after", observation=settled_observation)
            except DriverError:
                raise
            finally:
                settled_observation = None
        with self.controller.lock:
            if self.controller.status().generation == controller_generation:
                self.controller.clear_action_intent("complete")

    def run_native_calibration(self, *, expected_generation: int | None = None) -> dict[str, Any]:
        """Own the live render gate; callers cannot supply copied measurements."""
        self._begin_calibration("native", expected_generation)
        self._native_measurement_state = None
        self._native_handshake = {
            "state": "running",
            "holdRequired": False,
            "measureReady": False,
            "resumeRequired": False,
            "resumeReady": False,
            "failure": "",
            "restored": None,
            "archiveReceipts": [],
        }
        succeeded = False
        owned_meter: LinuxProcStatusVmHwmReset5 | None = None
        # The native runner owns the measurement provider and captures each
        # construction/update frame itself.  Passing a metrics dict copied from
        # one ordinary telemetry frame would turn the gate into an assertion.
        try:
            with self.controller.lock:
                status_before = self.controller.status()
                if status_before.state != ControllerState.NATIVE_CALIBRATION:
                    raise DriverError("native calibration requires an unarmed native-calibration state")
                if expected_generation is not None and status_before.generation != expected_generation:
                    raise DriverError("native calibration generation was revoked")
            owned_meter = self._ensure_native_memory_meter()
            # A new native gate supersedes any previous final capture.  The
            # runner retains only its final artifact for sealed evidence.
            pending_path = None
            with self._native_bootstrap_lock:
                if self._native_bootstrap_observation is not None:
                    pending_path = self._native_bootstrap_observation.get("capturePath")
            self._cleanup_native_owned_captures(keep=pending_path)
            evidence = NativeCalibrationRunner(self.driver, monotonic=self._native_clock).run()
            with self.controller.lock:
                if (
                    expected_generation is not None
                    and self.controller.status().generation != expected_generation
                ):
                    raise DriverError("native calibration generation was revoked")
                status = self.controller.native_calibrated(
                    evidence,
                    preconstruction_proof=self._native_bootstrap_proof,
                )
            self._cleanup_native_owned_captures(keep=getattr(evidence, "capture_path", None))
            # The bootstrap token is one-use evidence.  The controller has
            # already copied it into its durable calibration record; keeping
            # the daemon-side object would let a later gate accidentally
            # reuse an observation from the previous client construction.
            self._native_bootstrap_proof = None
            self._native_baseline_ready.clear()
            self._native_baseline_observation = None
            succeeded = True
            result = self.status_dict() | {"calibration": "native", "state": status.state.value}
        except Exception as exc:
            # A failed native run cannot reuse the preconstruction capture:
            # the operator may have loaded/reloaded the client while the
            # provider was running.  Require a new external bootstrap token.
            self._native_bootstrap_proof = None
            self._native_measurement_state = None
            self._native_baseline_ready.clear()
            self._native_baseline_observation = None
            with self._native_bootstrap_lock:
                self._native_bootstrap_observation = None
                self._native_bootstrap_ready.clear()
            self._cleanup_native_owned_captures()
            if self._native_handshake.get("state") not in {"restoration_required", "resume_ready"}:
                self._native_handshake.update(
                    {
                        "state": "error",
                        "failure": str(exc),
                        "restored": False,
                        "holdRequired": False,
                        "measureReady": False,
                        "resumeRequired": False,
                        "resumeReady": False,
                    }
                )
            self._finish_calibration(state="error", error=str(exc))
            raise
        finally:
            if owned_meter is not None:
                try:
                    owned_meter.close()
                finally:
                    if self.driver.native_memory_meter is owned_meter:
                        self.driver.native_memory_meter = None
        self._native_measurement_state = None
        self._finish_calibration(state="complete" if succeeded else "error")
        return result

    def run_input_calibration(self, *, expected_generation: int | None = None) -> dict[str, Any]:
        """Own the closed input calibration and deliberate takeover boundary."""
        from .calibration import InputCalibrationWorkflow

        self._begin_calibration("input", expected_generation)
        try:
            self._validate_runtime_paths()
            with self.controller.lock:
                status_before = self.controller.status()
                if status_before.state != ControllerState.INPUT_CALIBRATION:
                    raise DriverError("input calibration requires the native gate to be complete")
                if expected_generation is not None and status_before.generation != expected_generation:
                    raise DriverError("input calibration generation was revoked")
            # Pointer anchors are measured lazily by the native executor from
            # the fresh named scene immediately before each action.  The
            # input gate proves only the XTEST/guardian boundary; it must not
            # claim future disconnect, character-select, or AH controls are
            # simultaneously visible in the current world scene.
            evidence = InputCalibrationWorkflow(
                self.driver,
                display=self.config.profile.display,
                on_ready=self._set_calibration_readiness,
            ).run()
            with self.controller.lock:
                current = self.controller.status()
            if expected_generation is not None and current.generation != expected_generation:
                # The deliberate human sample is itself expected to revoke
                # the guardian.  Preserve the sealed evidence in the durable
                # paused process while requiring an explicit resume to arm it.
                if current.state == ControllerState.PAUSED:
                    status = self.controller.retain_input_calibration_while_paused(evidence)
                    result = self.status_dict() | {"calibration": "input", "state": status.state.value}
                    self._finish_calibration(state="complete")
                    return result
                raise DriverError("input calibration generation was revoked")
            status = self.controller.input_calibrated(
                evidence=evidence,
                expected_generation=expected_generation,
            )
            result = self.status_dict() | {"calibration": "input", "state": status.state.value}
            self._finish_calibration(state="complete")
            return result
        except Exception as exc:
            self._finish_calibration(state="error", error=str(exc))
            raise

    def _validate_runtime_paths(self) -> None:
        """Validate configured durable locations before arming desktop input."""

        paths = {
            "SavedVariables": self.config.saved_variables,
            "companion state": self.config.companion_state,
            "Data.lua": self.config.data_lua,
        }
        for label, path in paths.items():
            if path is None:
                raise DriverError(f"{label} path is not configured")
            parent = path.expanduser().parent
            if not parent.exists() or not parent.is_dir():
                raise DriverError(f"{label} parent directory does not exist: {parent}")
            if path.exists() and path.is_dir():
                raise DriverError(f"{label} path is a directory: {path}")

    def _reconcile_durable_files(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Read every durable queue before releasing a blocked controller.

        Resume from a rejected acknowledgement is an observation boundary,
        not permission to retry the old action.  Stable reads prove that the
        three writers agree on a complete schema; the next state still checks
        the exact UID and deadlines before dispatching anything.
        """

        if not all((self.config.saved_variables, self.config.companion_state, self.config.data_lua)):
            raise EvidenceError("reconciliation paths are not configured")
        assert self.config.saved_variables is not None
        assert self.config.companion_state is not None
        assert self.config.data_lua is not None
        try:
            root = savedvars.loads(stable_file(self.config.saved_variables))
        except (OSError, UnicodeError, ValueError, TypeError, JournalError) as exc:
            raise EvidenceError(f"SavedVariables reconciliation failed: {exc}") from exc
        db = root.get("CrowleyDB")
        if not isinstance(db, dict):
            raise EvidenceError("SavedVariables reconciliation has no CrowleyDB")
        if "scans" not in db or "sweeps" not in db:
            raise EvidenceError("SavedVariables reconciliation is missing explicit queue fields")
        for name in ("scans", "sweeps"):
            if not isinstance(db[name], dict):
                raise EvidenceError(f"SavedVariables reconciliation has malformed {name}")
        stable_scan_ids = frozenset(uid for uid in db["scans"] if isinstance(uid, str) and uid)
        stable_sweep_ids = frozenset(uid for uid in db["sweeps"] if isinstance(uid, str) and uid)
        if len(stable_scan_ids) != len(db["scans"]) or len(stable_sweep_ids) != len(db["sweeps"]):
            raise EvidenceError("SavedVariables reconciliation queue IDs are malformed")
        scan_kwargs = self._saved_scan_kwargs(snapshot)
        stable_evidence = None
        for uid in sorted(stable_scan_ids, key=lambda item: item.encode()):
            parsed = read_stable_saved_scan(
                self.config.saved_variables,
                uid=uid,
                planned=self.config.profile.plan_count,
                **scan_kwargs,
            )
            if uid == str(snapshot.get("lastSaved", {}).get("memoryUid", "")):
                stable_evidence = parsed
        uploads = read_uploads(self.config.companion_state)
        data_ids = read_data_acknowledged_ids(
            self.config.data_lua,
            expected_plan_json=self.config.plan_json,
            expected_plan_hash=self.config.plan_hash,
            expected_client_build=load_catalog().scan_plan()["targetClientBuild"],
        )
        scanner = snapshot.get("scanner")
        pending = snapshot.get("pending")
        if not isinstance(scanner, dict) or not isinstance(pending, dict):
            raise EvidenceError("restart reconciliation telemetry queues are malformed")
        phase = scanner.get("phase")
        active_sweep = scanner.get("activeSweepId")
        pending_ids = pending.get("ids")
        pending_count = pending.get("count")
        if (
            not isinstance(phase, str)
            or not isinstance(active_sweep, str)
            or not isinstance(pending_ids, list)
            or any(not isinstance(uid, str) or not uid for uid in pending_ids)
            or isinstance(pending_count, bool)
            or not isinstance(pending_count, int)
            or pending_count != len(pending_ids)
        ):
            raise EvidenceError("restart reconciliation telemetry queue facts are malformed")
        stable_uid = ""
        last_saved = snapshot.get("lastSaved")
        observed_uid = last_saved.get("memoryUid", "") if isinstance(last_saved, dict) else ""
        if isinstance(observed_uid, str) and observed_uid in stable_scan_ids:
            stable_uid = observed_uid
        return {
            "scanner_phase": phase,
            # Both explicit idle phases are valid.  ``item``/``owned`` and an
            # empty activeSweepId are not a completed scan witness.  A pending
            # UID is a separate acknowledgement proof and may remain after a
            # saved sweep has completed.
            "scanner_idle": phase in {"ready", "scheduled"} and not active_sweep,
            "stable_scan_ids": stable_scan_ids,
            "stable_sweep_ids": stable_sweep_ids,
            "stable_format2_uid": stable_uid,
            "stable_format2_evidence": stable_evidence,
            "stable_saved_uid": stable_uid,
            "stable_format2_verified": bool(stable_evidence is not None and stable_evidence.stable_verified),
            "stable_files_complete": True,
            "uploaded_ids": frozenset(uploads),
            "upload_timestamps": dict(uploads),
            "data_ack_ids": frozenset(data_ids),
        }

    def run_once(self) -> dict[str, Any]:
        lock = self._claim_motion_fence()
        if lock is None:
            return self.status_dict()
        try:
            return self._run_once_owned()
        finally:
            lock.release()

    def _run_once_owned(self) -> dict[str, Any]:
        with self.controller.lock:
            # REOPEN is resolved from the fresh frame below.  Its action may
            # itself cause the fake or real client to advance to the next
            # cadence boundary before the next capture (the client can finish
            # the transition between two frames).  Let that one post-action
            # frame prove AH-open; _advance enforces the deadline while the
            # frame still reports it closed.
            current = self.controller.status()
            fence = self.controller.observation_fence()
            status = current if current.state == ControllerState.REOPEN else self.controller.tick(fence=fence)
            generation = status.generation
            # A transition may have completed between a previous owner tick
            # and this capture.  Re-read mode under the same fence before any
            # producer work, so an engine observation cannot be admitted as an
            # interaction observation or vice versa.
            if status.mode.value == "interaction" and status.state not in {
                ControllerState.NATIVE_CALIBRATION,
                ControllerState.INPUT_CALIBRATION,
                ControllerState.READY,
                ControllerState.RECONCILE,
                ControllerState.LOGIN_REQUIRED,
            }:
                return self.status_dict()
        if status.mode.value == "interaction" and status.state in {
            ControllerState.NATIVE_CALIBRATION,
            ControllerState.INPUT_CALIBRATION,
        }:
            # Interaction startup is a durable gate, not an immediate READY
            # shortcut.  Run each gate through the existing supervised
            # calibration worker and let the next owner tick reconcile the
            # resulting ARMED/RECONCILE state.  A running operation is left
            # alone; no second calibration or input lease may be queued.
            with self._calibration_state_lock:
                operation_state = self._calibration_operation.get("state")
            if operation_state not in {"starting", "running"}:
                try:
                    self.start_calibration(
                        "native" if status.state == ControllerState.NATIVE_CALIBRATION else "input",
                        expected_generation=generation,
                    )
                except DriverError as exc:
                    if "already running" not in str(exc):
                        self.last_error = str(exc)
            return self.status_dict()
        if status.state in {
            ControllerState.STOPPED,
            ControllerState.PAUSED,
            ControllerState.BLOCKED,
            ControllerState.NATIVE_CALIBRATION,
            ControllerState.INPUT_CALIBRATION,
        }:
            return self.status_dict()
        # READY interaction is intentionally quiescent.  The recurring engine
        # must not take a capture/reconciliation turn or rewrite its journal
        # while an operator is idle; explicit intents own their own fresh
        # capture and physical-action fence.
        if (
            status.mode.value == "interaction"
            and status.state == ControllerState.READY
            and not status.action_intent
        ):
            return self.status_dict()
        if status.state == ControllerState.QUALIFY_PENDING:
            # Qualification staged its complete evidence and publication
            # witnesses before the archive boundary.  A fresh owner retries
            # from that durable checkpoint without recapturing the game or
            # retaining an old in-memory SweepEvidence object.
            try:
                self.controller.retry_pending_qualification(
                    expected_generation=status.generation,
                    expected_state=ControllerState.QUALIFY_PENDING,
                    fence=fence,
                )
            except JournalError as exc:
                # The controller preserves the exact QUALIFY_PENDING
                # checkpoint when disk-only publication cannot write.  Do not
                # call block(), whose journal save would overwrite that retry
                # boundary; the owner can restart and retry from disk.
                self.last_error = str(exc)
                return self.status_dict()
            except (DriverError, EvidenceError, ModelError, OSError, ValueError) as exc:
                self.last_error = str(exc)
                self._block_if_current(self.last_error, generation)
            return self.status_dict()
        try:
            sample = self.capture_status()
        except (DriverError, EvidenceError, OSError, ValueError) as exc:
            # Reloads can remove the telemetry canvas while the client loads. The
            # durable expected boot/deadline handles this bounded absence.
            menu_or_logout_reconcile = (
                status.state == ControllerState.RECONCILE
                and self.controller.journal.read().get("restartUncertain") is True
                and status.action_intent
                in {
                    "logout",
                    "dismiss_disconnect",
                    "reconnect_game",
                    "select_arthur",
                    "enter_world",
                }
            )
            if isinstance(exc, ProtocolError) and not menu_or_logout_reconcile:
                self.last_error = str(exc)
                self._block_if_current(f"corrupt telemetry frame: {exc}", generation)
                return self.status_dict()
            if status.state in {ControllerState.SAVE_RELOAD_SENT, ControllerState.ACK_RELOAD_SENT}:
                return self.status_dict()
            if status.state == ControllerState.DISK_CLEANUP_WAIT:
                try:
                    self._advance({})
                except (DriverError, EvidenceError, OSError, ValueError) as cleanup_error:
                    self.last_error = str(cleanup_error)
                    self._block_if_current(self.last_error, generation)
                return self.status_dict()
            if status.state in {
                ControllerState.ARMED,
                ControllerState.RECONCILE,
                ControllerState.LOGIN_REQUIRED,
            }:
                try:
                    uncertain_reconcile = (
                        status.state == ControllerState.RECONCILE
                        and self.controller.journal.read().get("restartUncertain") is True
                    )
                    menu_reconciled = uncertain_reconcile and self._reconcile_menu_intent_without_agent(
                        generation=generation
                    )
                    if menu_reconciled:
                        return self.status_dict()
                    completed_logout = uncertain_reconcile and self._reconcile_completed_logout_without_agent(
                        generation=generation
                    )
                    if completed_logout:
                        return self.status_dict()
                    if uncertain_reconcile:
                        # RECONCILE owns an uncertain external effect.  A
                        # missing canvas or filesystem read is an unresolved
                        # observation, never permission to issue login input.
                        # Enter-world can legitimately have no Agent while the
                        # scene loads; the durable deadline will bound this
                        # wait.  A malformed frame still fails closed below.
                        if isinstance(exc, OSError):
                            return self.status_dict()
                        if status.action_intent in {
                            "logout",
                            "dismiss_disconnect",
                            "reconnect_game",
                            "select_arthur",
                        }:
                            return self.status_dict()
                        if status.action_intent == "enter_world" and isinstance(exc, ProtocolError):
                            return self.status_dict()
                        if isinstance(exc, ProtocolError):
                            self.last_error = str(exc)
                            self._block_if_current(f"corrupt telemetry frame: {exc}", generation)
                            return self.status_dict()
                        return self.status_dict()
                    if status.state != ControllerState.LOGIN_REQUIRED:
                        with self.controller.lock:
                            current_status = self.controller.status()
                            if current_status.generation != generation:
                                return self.status_dict()
                            self.controller.reconcile(
                                identity_ok=True,
                                world_ready=False,
                                expected_generation=current_status.generation,
                                expected_state=current_status.state,
                                fence=self.controller.observation_fence(),
                            )
                    self._recover_login()
                except (DriverError, EvidenceError, ModelError, OSError, ValueError) as recovery_error:
                    self.last_error = str(recovery_error)
                    self._block_if_current(self.last_error, generation)
                return self.status_dict()
            self.last_error = str(exc)
            self._block_if_current(self.last_error, generation)
            return self.status_dict()
        if sample.kind == "NO_CHANGE":
            return self.status_dict()
        if sample.capture_monotonic < 0:
            self.last_error = "stale capture sample"
            self._block_if_current(self.last_error, generation)
            return self.status_dict()
        snapshot = sample.frame.snapshot.value if sample.frame else {}
        self.last_snapshot = snapshot
        persisted = dict(snapshot)
        if isinstance(persisted.get("chatEdit"), dict):
            persisted["chatEdit"] = dict(persisted["chatEdit"])
            persisted["chatEdit"]["text"] = ""

        def persist_telemetry(value: dict[str, Any]) -> None:
            # Journal updates are optimistic as well as serialized.  If IPC
            # pause/stop advanced the durable generation while a capture was
            # being decoded, this callback must leave the operator's state
            # untouched rather than writing an old telemetry snapshot over it.
            current_status = self.controller.status()
            if (
                current_status.generation != generation
                or value.get("generation") != generation
                or value.get("state")
                in {
                    ControllerState.PAUSED.value,
                    ControllerState.BLOCKED.value,
                    ControllerState.STOPPED.value,
                }
            ):
                # A journal implementation may have read its value before an
                # operator pause while waiting in a writer hook.  Refresh the
                # entire object so the eventual replace preserves that pause.
                if current_status.generation != generation:
                    fresh = self.controller.journal.read()
                    value.clear()
                    value.update(fresh)
                return
            value["telemetry"] = persisted

        with self.controller.lock:
            if not self.controller.admit_observation(fence):
                return self.status_dict()
            self.controller.journal.update(persist_telemetry)
        try:
            with self.controller.lock:
                if not self.controller.admit_observation(fence):
                    return self.status_dict()
                current = self.controller.observe_frame(
                    boot=sample.frame.boot,
                    sequence=sample.frame.sequence,
                    crc32=sample.frame.crc32,
                    fence=fence,
                )
                if current.state == ControllerState.BLOCKED:
                    return self.status_dict()
            if current.state not in {
                ControllerState.DISK_CLEANUP_SENT,
                ControllerState.DISK_CLEANUP_WAIT,
            }:
                self._validate_identity(snapshot, state=current.state)
            with self.controller.lock:
                if self.controller.status().generation != generation:
                    return self.status_dict()
                next_fence = self.controller.observation_fence()
            self._advance(snapshot, fence=next_fence)
        except (DriverError, EvidenceError, ModelError, OSError, ValueError) as exc:
            if (
                isinstance(exc, OSError)
                and current.state == ControllerState.RECONCILE
                and self.controller.journal.read().get("restartUncertain") is True
            ):
                # A stable-file or capture read that temporarily disappears
                # cannot authorize a new action while an external effect is
                # still uncertain.  Keep the durable reconcile intent intact.
                return self.status_dict()
            self.last_error = str(exc)
            self._block_if_current(self.last_error, generation)
        else:
            self.last_error = ""
        return self.status_dict()

    def _block_if_current(self, reason: str, generation: int) -> None:
        """Block only the live observation epoch that raised ``reason``.

        Capture, model, and durable-file I/O happen outside the controller
        mutex. An operator pause or stop may therefore win while that work is
        in flight; this helper refuses to overwrite that newer state.
        """

        with self.controller.lock:
            current = self.controller.status()
            if current.generation != generation or current.state in {
                ControllerState.PAUSED,
                ControllerState.BLOCKED,
                ControllerState.STOPPED,
            }:
                return
            self.controller.block(
                reason,
                expected_generation=current.generation,
                expected_state=current.state,
                fence=self.controller.observation_fence(),
            )

    def _validate_identity(self, snapshot: dict[str, Any], *, state: ControllerState) -> None:
        context = snapshot.get("context", {})
        house = snapshot.get("house", {})
        plan = snapshot.get("plan", {})
        expected = self.config.profile
        expected_context = {
            "character": expected.character,
            "realm": expected.realm,
            "playerFaction": self.config.player_faction,
            "locale": self.config.locale,
            "clientVersion": self.config.client_version,
            "clientBuild": self.config.client_build,
            "interface": self.config.interface,
            "addonVersion": self.config.addon_version,
        }
        mismatched = [key for key, value in expected_context.items() if context.get(key) != value]
        if mismatched:
            raise EvidenceError(f"configured client context does not match telemetry: {mismatched}")
        if house.get("key") != expected.house or plan.get("count") != expected.plan_count:
            raise EvidenceError("configured house or plan does not match telemetry")
        if self.config.plan_hash and plan.get("hash") != self.config.plan_hash:
            raise EvidenceError("telemetry plan hash is not externally pinned")
        cursor = snapshot.get("scanner", {}).get("cursorItemID", 0)
        configured_ids = frozenset(load_catalog().scan_plan()["itemIDs"])
        if (
            isinstance(cursor, bool)
            or not isinstance(cursor, int)
            or cursor < 0
            or (cursor and cursor not in configured_ids)
        ):
            raise EvidenceError("telemetry cursor is outside the configured scan plan")

    def _saved_scan_kwargs(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Return the immutable identity contract for format-2 evidence."""

        plan_hash = self.config.plan_hash or str(snapshot.get("plan", {}).get("hash", ""))
        if not plan_hash:
            raise EvidenceError("saved scan evidence has no externally pinned plan hash")
        return {
            "house": self.config.profile.house,
            "plan_hash": plan_hash,
            "expected_plan_json": self.config.plan_json or None,
            "expected_context": {
                "character": self.config.profile.character,
                "realm": self.config.profile.realm,
                "playerFaction": self.config.player_faction,
                "locale": self.config.locale,
                "clientVersion": self.config.client_version,
                "clientBuild": self.config.client_build,
                "interface": self.config.interface,
                "addonVersion": self.config.addon_version,
            },
        }

    def _advance(self, snapshot: dict[str, Any], *, fence: Any | None = None) -> None:
        with self.controller.lock:
            status = self.controller.status()
            fence = fence or self.controller.observation_fence()
        if status.mode.value == "interaction":
            context = snapshot.get("context", {})
            world_ready = (
                isinstance(context, dict)
                and context.get("character") == self.config.profile.character
                and context.get("realm") == self.config.profile.realm
            )
            self.controller.reconcile_interaction(
                identity_ok=True,
                world_ready=world_ready,
                expected_generation=status.generation,
                fence=fence,
            )
            return
        if status.state == ControllerState.DISK_CLEANUP_WAIT:
            if not all((self.config.saved_variables, self.config.companion_state, self.config.data_lua)):
                raise EvidenceError("closeout paths are not configured")
            character_select = getattr(self.driver, "character_select_observed", None)
            if not callable(character_select) or not character_select():
                return
            if queues_empty(
                self.config.saved_variables,
                self.config.companion_state,
                self.config.data_lua,
                settled_uid=(
                    status.last_uid
                    if self.controller.journal.read()
                    .get("current", {})
                    .get("evidence", {})
                    .get("qualification")
                    != "rejected"
                    and status.last_uid
                    else None
                ),
            ):
                self.controller.cleanup_complete(
                    logout_observed=True,
                    expected_generation=status.generation,
                    expected_state=ControllerState.DISK_CLEANUP_WAIT,
                    fence=fence,
                )
            return
        context = snapshot.get("context", {})
        character_ready = (
            context.get("character") == self.config.profile.character
            and context.get("realm") == self.config.profile.realm
        )
        if status.state == ControllerState.RECONCILE and self.controller.journal.read().get(
            "reconciliationRequired"
        ):
            stable_facts = self._reconcile_durable_files(snapshot)
            if stable_facts.get("stable_format2_evidence") is not None:
                self.current_evidence = stable_facts["stable_format2_evidence"]
            uploads = stable_facts["uploaded_ids"]
            data_ids = stable_facts["data_ack_ids"]
            loaded_ids = set(snapshot.get("loaded", {}).get("ackedIds", []))
            pending_ids = set(snapshot.get("pending", {}).get("ids", []))
            loaded = snapshot.get("loaded", {})
            if not isinstance(loaded, dict):
                raise EvidenceError("restart reconciliation loaded telemetry is malformed")
            loaded_uid = status.last_uid if status.last_uid in loaded_ids else ""
            loaded_at = int(snapshot.get("wallTime", 0) or 0) if loaded_uid else 0
            loaded_boot = str(snapshot.get("boot", "")) if loaded_uid else ""
            loaded_sequence = int(snapshot.get("sequence", 0) or 0) if loaded_uid else 0
            last_saved = snapshot.get("lastSaved", {})
            observed_uid = str(last_saved.get("memoryUid", "")) if isinstance(last_saved, dict) else ""
            context = snapshot.get("context", {})
            # Missing scene facts are unresolved.  Treating an incomplete
            # capture as world would permit a login/input recovery action on a
            # stale or character-select frame.
            scene = ""
            if isinstance(context, dict):
                if not context.get("character"):
                    scene = "character_select"
                elif snapshot.get("ahOpen") is True:
                    scene = "auction_house"
                elif snapshot.get("ahOpen") is False and context.get("realm"):
                    scene = "world"
            scanner = snapshot.get("scanner", {})
            fence_armed = None
            if isinstance(scanner, dict):
                schedule_fence = scanner.get("scheduleFence")
                if isinstance(schedule_fence, dict):
                    fence_armed = schedule_fence.get("state") == "armed"
            observed_character = context.get("character", "") if isinstance(context, dict) else ""
            observed_modal = snapshot.get("modal", "")
            if not isinstance(observed_modal, str):
                observed_modal = ""
            selected_arthur = (
                observed_character == self.config.profile.character if isinstance(context, dict) else None
            )
            stable_upload_timestamp = stable_facts["upload_timestamps"].get(status.last_uid, 0)
            stable_companion_uploaded_uid = status.last_uid if status.last_uid in uploads else ""
            stable_data_ack_uid = status.last_uid if status.last_uid in data_ids else ""
            with self.controller.lock:
                current = self.controller.resolve_restart_intent(
                    observed_boot=str(snapshot.get("boot", "")),
                    observed_uid=observed_uid,
                    uploaded_ids=set(uploads),
                    data_ack_ids=set(data_ids),
                    loaded_ids=loaded_ids,
                    pending_ids=pending_ids,
                    scanner_phase=stable_facts["scanner_phase"],
                    scanner_idle=stable_facts["scanner_idle"],
                    stable_scan_ids=stable_facts["stable_scan_ids"],
                    stable_sweep_ids=stable_facts["stable_sweep_ids"],
                    stable_format2_uid=stable_facts["stable_format2_uid"],
                    stable_format2_evidence=stable_facts["stable_format2_evidence"],
                    stable_saved_uid=stable_facts["stable_saved_uid"],
                    stable_upload_timestamp=stable_upload_timestamp,
                    stable_data_ack_uid=stable_data_ack_uid,
                    stable_companion_uploaded_uid=stable_companion_uploaded_uid,
                    loaded_uid=loaded_uid,
                    loaded_at=loaded_at,
                    loaded_boot=loaded_boot,
                    loaded_sequence=loaded_sequence,
                    stable_format2_verified=stable_facts["stable_format2_verified"],
                    stable_files_complete=stable_facts["stable_files_complete"],
                    observed_scene=scene,
                    observed_modal=observed_modal,
                    observed_character=observed_character,
                    observed_ah_open=snapshot.get("ahOpen")
                    if isinstance(snapshot.get("ahOpen"), bool)
                    else None,
                    selected_arthur=selected_arthur,
                    fence_armed=fence_armed,
                    action_postcondition=(
                        True
                        if (status.action_intent == "enter_world" and scene == "world")
                        else (snapshot.get("ahOpen") is True if status.action_intent == "open_ah" else None)
                    ),
                    expected_generation=status.generation,
                    expected_state=ControllerState.RECONCILE,
                    fence=fence,
                )
                if current.state != ControllerState.RECONCILE:
                    return
        if status.state in {ControllerState.ARMED, ControllerState.RECONCILE}:
            if status.state == ControllerState.RECONCILE and self.controller.journal.read().get(
                "restartUncertain", False
            ):
                # Read-only restart reconciliation owns this frame.  Never
                # relog or issue a named action while its effect remains
                # unproved, including a character-select observation.
                return self.status_dict()
            self.controller.reconcile(
                identity_ok=True,
                world_ready=character_ready,
                expected_generation=status.generation,
                expected_state=status.state,
                fence=fence,
            )
            if not character_ready:
                self._recover_login()
            return
        if status.state == ControllerState.LOGIN_REQUIRED:
            if character_ready:
                self.controller.reconcile(
                    identity_ok=True,
                    world_ready=True,
                    expected_generation=status.generation,
                    expected_state=status.state,
                    fence=fence,
                )
                with self.controller.lock:
                    self.controller.clear_recovery_attempts()
                self.recovery_attempts = 0
                self.recovery_actions.clear()
            else:
                self._recover_login()
            return
        scanner = snapshot["scanner"]
        phase = scanner["phase"]
        if status.state in {ControllerState.READY, ControllerState.WAIT_DUE}:
            if status.closeout_requested:
                # A closeout retained across a stop/restart must not turn an
                # idle reconciliation frame into a newly initiated scan.
                self.controller.closeout()
                return
            if (
                phase in {"item", "owned"}
                and int(scanner.get("startedAt", 0) or 0) > 0
                and int(scanner.get("ordinal", 0) or 0) > 0
            ):
                self.controller.begin_scan(
                    started_at=int(scanner["startedAt"]),
                    expected_generation=status.generation,
                    expected_state=status.state,
                    fence=fence,
                )
                return
            if phase == "ready" and snapshot["wallTime"] >= scanner["dueAt"]:
                if not snapshot.get("ahOpen"):
                    self._run_action("open_ah", snapshot)
                    return
                if self._command(snapshot, "/crowley scan"):
                    self.controller.begin_scan(
                        started_at=snapshot["wallTime"],
                        expected_generation=status.generation,
                        expected_state=status.state,
                        fence=fence,
                    )
            return
        saved = snapshot.get("lastSaved", {})
        uid = str(saved.get("memoryUid", ""))
        finished_at = int(saved.get("finishedAt", 0))
        if (
            status.state == ControllerState.SCANNING
            and uid
            and uid != status.last_uid
            and finished_at >= status.started_at
        ):
            self.controller.saved(
                uid,
                expected_generation=status.generation,
                expected_state=ControllerState.SCANNING,
                fence=fence,
            )
            return
        if status.state == ControllerState.QUIET_SAVE:
            due_at = int(scanner.get("dueAt", 0))
            if due_at and int(snapshot["wallTime"]) + self.config.quiet_margin_seconds >= due_at:
                raise EvidenceError("save/reload has no quiet margin before the next due start")
            if self._command(snapshot, "/reload"):
                self.decoder.allow_boot_change_once()
                self.controller.reload_sent(
                    expected_generation=status.generation,
                    expected_state=ControllerState.QUIET_SAVE,
                )
                self.controller.expect_boot(snapshot["boot"])
            return
        if status.state == ControllerState.SAVE_RELOAD_WAIT and self.config.saved_variables:
            evidence = read_stable_saved_scan(
                self.config.saved_variables,
                uid=status.last_uid,
                **self._saved_scan_kwargs(snapshot),
            )
            self.current_evidence = evidence
            self.controller.stable_saved(
                evidence,
                expected_generation=status.generation,
                expected_state=ControllerState.SAVE_RELOAD_WAIT,
                fence=fence,
            )
            return
        if status.state == ControllerState.UPLOAD_WAIT and self.config.companion_state:
            evidence = self.current_evidence
            meta = (
                evidence.envelope
                if evidence is not None
                else self.controller.journal.read().get("current", {}).get("evidence", {})
            )
            if evidence is None and self.config.saved_variables and meta.get("planHash"):
                evidence = read_stable_saved_scan(
                    self.config.saved_variables,
                    uid=status.last_uid,
                    **self._saved_scan_kwargs(snapshot),
                )
                self.current_evidence = evidence
                meta = evidence.envelope
            if not meta:
                raise EvidenceError("upload wait has no durable sweep evidence")
            upload_time = read_uploads(self.config.companion_state).get(status.last_uid)
            data_uid = ""
            if self.config.data_lua:
                data_ids = read_data_acknowledged_ids(
                    self.config.data_lua,
                    expected_plan_json=self.config.plan_json,
                    expected_plan_hash=self.config.plan_hash,
                    expected_client_build=load_catalog().scan_plan()["targetClientBuild"],
                )
                if status.last_uid in data_ids:
                    data_uid = status.last_uid
                else:
                    return
            finish = int(meta["finishedAt"])
            if upload_time is None:
                return
            if upload_time < finish or upload_time - finish > self.config.upload_deadline_seconds:
                raise EvidenceError("upload was outside the 60-second finish deadline")
            self.controller.uploaded(
                status.last_uid,
                accepted=True,
                upload_time=upload_time,
                data_ack_uid=data_uid,
                expected_generation=status.generation,
                expected_state=ControllerState.UPLOAD_WAIT,
                fence=fence,
            )
            return
        if status.state == ControllerState.ACK_RELOAD_SENT:
            if status.action_intent == "ack_reload":
                # The addon acknowledgement and companion upload must both be
                # stable before the reload command is dispatched.  This
                # closes the Data.lua publication race and records the exact
                # witnesses in the journal before any input.
                if self.config.data_lua:
                    if status.last_uid not in read_data_acknowledged_ids(
                        self.config.data_lua,
                        expected_plan_json=self.config.plan_json,
                        expected_plan_hash=self.config.plan_hash,
                        expected_client_build=load_catalog().scan_plan()["targetClientBuild"],
                    ):
                        return
                companion_uid = status.last_uid
                if self.config.companion_state:
                    if status.last_uid not in read_uploads(self.config.companion_state):
                        return
                with self.controller.lock:
                    self.controller.record_ack_publication(
                        status.last_uid,
                        companion_uid=companion_uid,
                        data_uid=status.last_uid,
                        publication_time=int(snapshot.get("wallTime", 0)),
                        boot=str(snapshot.get("boot", "")),
                        sequence=int(snapshot.get("sequence", 0)),
                        expected_generation=status.generation,
                        expected_state=ControllerState.ACK_RELOAD_SENT,
                        fence=fence,
                    )
                if self._command(snapshot, "/reload"):
                    self.decoder.allow_boot_change_once()
                    self.controller.ack_reload_command_sent(
                        expected_generation=status.generation,
                        expected_state=ControllerState.ACK_RELOAD_SENT,
                    )
                    self.controller.expect_boot(snapshot["boot"], acknowledgement=True)
            return
        if status.state == ControllerState.ACK_RELOAD_WAIT:
            loaded = set(snapshot.get("loaded", {}).get("ackedIds", []))
            pending = set(snapshot.get("pending", {}).get("ids", []))
            # Data.lua is a pre-reload publication witness.  It is allowed to
            # be refreshed or emptied by the acknowledgement reload, so the
            # post-reload proof uses fresh addon loaded/pending telemetry plus
            # the durable stage values recorded before dispatch.
            if status.last_uid in loaded and status.last_uid not in pending:
                # Reconstruct the complete stable format-2 object before
                # clearing ACK_RELOAD_WAIT.  A loaded UID without its exact
                # evidence is unresolved; it must never be parked for a
                # future sweep or move the controller to REOPEN first.
                evidence = self.current_evidence
                if evidence is not None and evidence.uid != status.last_uid:
                    evidence = None
                if evidence is None:
                    if not self.config.saved_variables:
                        raise EvidenceError("acknowledgement has no configured stable evidence path")
                    evidence = read_stable_saved_scan(
                        self.config.saved_variables,
                        uid=status.last_uid,
                        **self._saved_scan_kwargs(snapshot),
                    )
                if evidence.uid != status.last_uid or not evidence.stable_verified:
                    raise EvidenceError("acknowledgement lacks complete stable format-2 evidence")
                self.current_evidence = evidence
                completed = self.controller.ack_reload_complete(
                    pending_ids=pending,
                    loaded_uid=status.last_uid,
                    loaded_at=int(snapshot.get("wallTime", 0)),
                    boot=str(snapshot.get("boot", "")),
                    sequence=int(snapshot.get("sequence", 0)),
                    expected_generation=status.generation,
                    expected_state=ControllerState.ACK_RELOAD_WAIT,
                    fence=fence,
                )
                # Completing the reload intent moves the controller to
                # REOPEN (or closeout cleanup), so the ACK_RELOAD_WAIT fence
                # is stale by design. Qualify under a fresh fence for the
                # state produced by ack_reload_complete.
                with self.controller.lock:
                    qualification_fence = self.controller.observation_fence()
                self.controller.qualify(
                    evidence,
                    started_at=status.started_at,
                    expected_generation=completed.generation,
                    expected_state=completed.state,
                    fence=qualification_fence,
                )
                self.current_evidence = None
            else:
                self.last_error = f"ack telemetry loaded={loaded!r} pending={pending!r}"
            return
        if status.state == ControllerState.REOPEN:
            if (
                status.deadline_at
                and int(snapshot.get("wallTime", 0)) >= status.deadline_at
                and not snapshot.get("ahOpen")
            ):
                self.controller.block("reopen deadline expired")
                return
            if snapshot.get("ahOpen"):
                self.controller.reopen_complete(
                    expected_generation=status.generation,
                    expected_state=ControllerState.REOPEN,
                    fence=fence,
                )
                self.reopen_action_sent = False
            elif not self.reopen_action_sent:
                self._run_action("open_ah", snapshot)
                self.reopen_action_sent = True
            return
        if status.state == ControllerState.DISK_CLEANUP_SENT:
            # Closeout is a final client boundary.  Do not issue logout from
            # the frame that merely caused entry into cleanup: one more fresh
            # frame must prove the scanner and pending queue are still idle
            # after the acknowledgement reload.
            closeout_sample = self.capture_status()
            if closeout_sample.kind != "FRESH" or closeout_sample.frame is None:
                return
            snapshot = closeout_sample.frame.snapshot.value
            scanner_state = snapshot.get("scanner", {})
            loaded_ids = set(snapshot.get("loaded", {}).get("ackedIds", []))
            pending_ids = set(snapshot.get("pending", {}).get("ids", []))
            phase = scanner_state.get("phase")
            active_uid = str(scanner_state.get("activeSweepId") or "")
            ordinal = int(scanner_state.get("ordinal", 0) or 0)
            started_at = int(scanner_state.get("startedAt", 0) or 0)
            scan_active = bool(active_uid) or (phase in {"item", "owned"} and started_at > 0 and ordinal > 0)
            last_saved = snapshot.get("lastSaved", {})
            saved_uid = str(last_saved.get("memoryUid") or "") if isinstance(last_saved, dict) else ""
            saved_finished = int(last_saved.get("finishedAt", 0)) if isinstance(last_saved, dict) else 0
            # An addon auto-start can race the closeout request.  Adopt that
            # already-running scan before considering logout.  Only a frame
            # that proves the exact prior UID finished after this scan began
            # can be treated as the one normal item->owned->loaded lag.
            completed_lag = (
                scan_active
                and not active_uid
                and bool(status.last_uid)
                and saved_uid == status.last_uid
                and saved_finished >= started_at > 0
                and status.last_uid in loaded_ids
                and not pending_ids
            )
            if scan_active and not completed_lag:
                candidate = (started_at, active_uid)
                if active_uid or self._closeout_scan_candidate == candidate:
                    with self.controller.lock:
                        self.controller.adopt_scan(
                            started_at=started_at or int(snapshot.get("wallTime", 0)),
                            expected_generation=status.generation,
                            expected_state=ControllerState.DISK_CLEANUP_SENT,
                            fence=fence,
                        )
                    self._closeout_scan_candidate = None
                else:
                    self._closeout_scan_candidate = candidate
                return
            self._closeout_scan_candidate = None
            if not snapshot.get("pending", {}).get("ids"):
                if not all((self.config.saved_variables, self.config.companion_state, self.config.data_lua)):
                    raise EvidenceError("closeout paths are not configured")
                evidence_status = (
                    self.controller.journal.read()
                    .get("current", {})
                    .get("evidence", {})
                    .get("qualification", "")
                )
                uploads = read_uploads(self.config.companion_state)
                if status.last_uid and evidence_status != "rejected" and status.last_uid not in uploads:
                    return
                # Arm the addon's atomic pre-logout fence first.  The command
                # itself is only preparation; logout requires a newer frame
                # from the same boot proving that the fence was accepted.
                if not self._scanner_idle_ready(snapshot, status.last_uid):
                    return
                fence_observation = self._closeout_fence_observation
                if (
                    fence_observation is None
                    or fence_observation[0] != str(snapshot.get("boot", ""))
                    or int(snapshot.get("sequence", 0)) <= fence_observation[1]
                ):
                    # The addon's armed bit is not process-local proof that
                    # this owner sent the fence.  On restart always dispatch a
                    # fresh exact fence command, then require a newer frame
                    # from the same boot before logout.
                    if self._command(snapshot, "/crowley session fence"):
                        self._closeout_fence_observation = (
                            str(snapshot.get("boot", "")),
                            int(snapshot.get("sequence", 0)),
                        )
                    return
                if not self._logout_scanner_idle(snapshot, status.last_uid):
                    return
                self._closeout_fence_observation = None
                # The final logout is the client's durable SavedVariables
                # flush.  The precondition is exact pending telemetry plus a
                # settled upload; the postcondition below reads all three
                # stable files without expecting another Agent frame.
                if self._command(snapshot, "/logout"):
                    if self._last_action_generation != self.driver.guardian.generation:
                        return
                    with self.controller.lock:
                        latest = self.controller.status()
                        if (
                            latest.generation != status.generation
                            or latest.state != ControllerState.DISK_CLEANUP_SENT
                        ):
                            return
                        logout_fence = self.controller.observation_fence()
                        self.controller.logout_sent(
                            expected_generation=latest.generation,
                            expected_state=ControllerState.DISK_CLEANUP_SENT,
                            fence=logout_fence,
                        )
            return

    def status_dict(self) -> dict[str, Any]:
        value = self.controller.status()
        durable = self.controller.journal.read()
        return {
            "state": value.state.value,
            "mode": value.mode.value,
            "generation": value.generation,
            "leaseGeneration": value.lease_generation,
            "stopRequested": value.stop_requested,
            "closeoutRequested": value.closeout_requested,
            "streak": value.streak,
            "blocker": value.blocker or self.last_error,
            "lastUid": value.last_uid,
            "startedAt": value.started_at,
            "expectedBoot": value.expected_boot,
            "actionIntent": value.action_intent,
            "deadlineAt": value.deadline_at,
            "reconciliationRequired": bool(durable.get("reconciliationRequired", False)),
            "boot": self.last_snapshot.get("boot", ""),
            "sequence": self.last_snapshot.get("sequence", 0),
            "phase": self.last_snapshot.get("scanner", {}).get("phase", ""),
            "dueAt": self.last_snapshot.get("scanner", {}).get("dueAt", 0),
            "lastSaved": self.last_snapshot.get("lastSaved", {}),
            "pending": self.last_snapshot.get("pending", {}),
            "loaded": self.last_snapshot.get("loaded", {}),
            "nativeCalibration": bool(durable.get("nativeCalibration", False)),
            "inputCalibration": bool(durable.get("inputCalibration", False)),
            "calibrationOperation": self._calibration_operation_snapshot(),
            "calibrationEvidence": {
                name: record.get("fingerprint", "")
                for name, record in durable.get("calibrationEvidence", {}).items()
                if isinstance(record, dict)
            },
            "calibrationHistory": durable.get("calibrationHistory", []),
            "calibrationInvalidated": durable.get("calibrationInvalidated", ""),
            "nativeBootstrapPending": self._native_bootstrap_ready.is_set(),
            "nativeBootstrapReady": self._native_baseline_ready.is_set(),
            "nativeBootstrap": self._native_baseline_observation or self._native_bootstrap_observation,
            # These fields are the operator-visible native8 handshake.  They
            # are facts emitted by callbacks from the live runner, not claims
            # inferred from a calibration boolean.
            "nativeHandshake": dict(self._native_handshake),
        }

    def _calibration_operation_snapshot(self) -> dict[str, Any]:
        with self._calibration_state_lock:
            value = dict(self._calibration_operation)
            if isinstance(value.get("readiness"), dict):
                value["readiness"] = dict(value["readiness"])
            return value

    def run_forever(self, *, interval: float = 1.0) -> None:
        while not self._shutdown_event.is_set():
            self.run_once()
            self._shutdown_event.wait(interval)


__all__ = ["SessionDaemon"]
