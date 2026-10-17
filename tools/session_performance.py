"""Bounded, offline measurements for the Crowley session decode boundary.

This command only reads explicitly named PNGs and JSON timing receipts. It
never captures a desktop, sends input, starts a session, or consults a live
service. The production decoder and pure executor planners remain the
reference implementations. Where the production decoder exposes no public
substep boundary, this module reports one combined strict-decode interval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, TypeVar

from PIL import Image

from crowley.session.decoder import PixelDecoder
from crowley.session.executor import (
    BindingMetadata,
    KeyRole,
    Point,
    PointerTarget,
    Rect,
    plan_camera_drag,
    plan_key_hold,
    plan_pointer_curve,
    plan_single_click,
)
from crowley.session.protocol import ProtocolError

MAX_SAMPLES = 1_000
MAX_INPUTS = 16
MAX_RECEIPTS = 16
MAX_PNG_BYTES = 1_048_576
MAX_RECEIPT_BYTES = 1_048_576
EXPECTED_DIMENSIONS = (256, 256)
STAGE_NAMES = (
    "png_load",
    "pixel_extract_2x2_validation",
    "cell_unpack",
    "frame_inflate_json_schema_validation",
    "full_strict_decode",
    "pointer_planning",
    "click_planning",
    "key_planning",
    "camera_planning",
)
SOURCE_FILES = (
    "src/crowley/session/decoder.py",
    "src/crowley/session/protocol.py",
    "src/crowley/session/executor.py",
)
T = TypeVar("T")


class PerformanceInputError(ValueError):
    """An explicit offline artifact is malformed or outside its bounds."""


@dataclass(frozen=True)
class Timed:
    value: Any
    wall_seconds: float
    cpu_seconds: float


def _reject_constant(value: str) -> Any:
    del value
    raise PerformanceInputError("receipt_invalid_json_constant")


def _strict_json(raw: bytes) -> Any:
    def hook(values: list[tuple[str, Any]]) -> dict[str, Any]:
        keys = [key for key, _ in values]
        if any(not isinstance(key, str) for key in keys) or len(keys) != len(set(keys)):
            raise PerformanceInputError("receipt_duplicate_or_non_string_key")
        return dict(values)

    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=hook,
            parse_constant=_reject_constant,
        )
    except PerformanceInputError:
        raise
    except RecursionError as exc:
        raise PerformanceInputError("receipt_json_nesting_exceeded") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PerformanceInputError("receipt_invalid_utf8_or_json") from exc


def _timed[T](function: Callable[[], T]) -> Timed:
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    value = function()
    wall = (time.perf_counter_ns() - wall_start) / 1_000_000_000
    cpu = (time.process_time_ns() - cpu_start) / 1_000_000_000
    return Timed(value, wall, cpu)


def _read_bounded(path: Path) -> tuple[bytes, int]:
    """Read an explicitly named file without trusting a racing stat result."""

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise PerformanceInputError(f"unable to stat explicit input {path.name!r}") from exc
    if size <= 0 or size > MAX_PNG_BYTES:
        raise PerformanceInputError(f"PNG input size must be in 1..{MAX_PNG_BYTES} bytes")
    try:
        with path.open("rb") as handle:
            if os.fstat(handle.fileno()).st_size != size:
                raise PerformanceInputError("input file changed during bounded read")
            raw = handle.read(MAX_PNG_BYTES + 1)
    except PerformanceInputError:
        raise
    except OSError as exc:
        raise PerformanceInputError("unable to read explicit input") from exc
    if len(raw) > MAX_PNG_BYTES or len(raw) != size:
        raise PerformanceInputError("input file changed during bounded read")
    try:
        if path.stat().st_size != size:
            raise PerformanceInputError("input file changed during bounded read")
    except OSError as exc:
        raise PerformanceInputError("unable to stat explicit input") from exc
    return raw, size


def _load_png(
    path: Path,
    *,
    expected_sha256: str | None = None,
    expected_size: int | None = None,
) -> Image.Image:
    try:
        raw, size = _read_bounded(path)
        if expected_size is not None and size != expected_size:
            raise PerformanceInputError("input bytes changed since preflight")
        if expected_sha256 is not None and hashlib.sha256(raw).hexdigest() != expected_sha256:
            raise PerformanceInputError("input bytes changed since preflight")
        with Image.open(BytesIO(raw)) as image:
            if image.format != "PNG":
                raise PerformanceInputError("PNG container or format is invalid")
            if image.size != EXPECTED_DIMENSIONS:
                raise PerformanceInputError(f"PNG dimensions are not {EXPECTED_DIMENSIONS!r}")
            image.load()
            return image.copy()
    except PerformanceInputError:
        raise
    except (OSError, ValueError) as exc:
        raise PerformanceInputError("PNG container or decode is invalid") from exc


def _source_hashes(repo_root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in SOURCE_FILES:
        path = repo_root / relative
        try:
            result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise PerformanceInputError("required source boundary is unavailable") from exc
    return result


def _planner_inputs() -> tuple[Point, PointerTarget, Rect, BindingMetadata]:
    binding = BindingMetadata(
        identity_fingerprint="offline-performance-client",
        capture_id="offline-performance-capture",
        capture_sequence=1,
        generation=1,
        target_xid=1,
        target_ancestry=(1,),
        source="offline-fixture",
        boot="offline-boot",
    )
    client = Rect(0, 0, 800, 600)
    target = PointerTarget("offline-control", Rect(120, 100, 80, 40), binding)
    return Point(20, 20), target, client, binding


def _planner_timings() -> dict[str, Timed]:
    start, target, client, binding = _planner_inputs()
    return {
        "pointer_planning": _timed(lambda: plan_pointer_curve(start, target, client)),
        "click_planning": _timed(lambda: plan_single_click(target, client)),
        "key_planning": _timed(lambda: plan_key_hold(KeyRole.MOVE_FORWARD, 0.1, binding)),
        "camera_planning": _timed(
            lambda: plan_camera_drag(Point(200, 200), Point(260, 200), client, binding)
        ),
    }


def _stage_summary(wall: list[float], cpu: list[float]) -> dict[str, Any]:
    if len(wall) != len(cpu):
        raise PerformanceInputError("stage wall and CPU samples have different lengths")
    if not wall:
        return {
            "samples": 0,
            "wall_p50_ms": None,
            "wall_p95_ms": None,
            "wall_p99_ms": None,
            "wall_max_ms": None,
            "cpu_p50_ms": None,
            "cpu_p95_ms": None,
            "cpu_p99_ms": None,
            "cpu_max_ms": None,
            "wall_samples_seconds": [],
            "cpu_samples_seconds": [],
        }

    def quantile(values: Sequence[float], quantile_value: float) -> float:
        index = math.ceil(quantile_value * len(values)) - 1
        return sorted(values)[index]

    return {
        "samples": len(wall),
        "wall_p50_ms": quantile(wall, 0.50) * 1000,
        "wall_p95_ms": quantile(wall, 0.95) * 1000,
        "wall_p99_ms": quantile(wall, 0.99) * 1000,
        "wall_max_ms": max(wall) * 1000,
        "cpu_p50_ms": quantile(cpu, 0.50) * 1000,
        "cpu_p95_ms": quantile(cpu, 0.95) * 1000,
        "cpu_p99_ms": quantile(cpu, 0.99) * 1000,
        "cpu_max_ms": max(cpu) * 1000,
        "wall_samples_seconds": list(wall),
        "cpu_samples_seconds": list(cpu),
    }


def _unmeasured_stage(reason: str) -> dict[str, Any]:
    """Describe a production substep that has no public timing boundary."""

    return {
        "samples": None,
        "wall_p50_ms": None,
        "wall_p95_ms": None,
        "wall_p99_ms": None,
        "wall_max_ms": None,
        "cpu_p50_ms": None,
        "cpu_p95_ms": None,
        "cpu_p99_ms": None,
        "cpu_max_ms": None,
        "wall_samples_seconds": None,
        "cpu_samples_seconds": None,
        "unmeasured_reason": reason,
    }


def _environment_metadata() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "pillow": str(getattr(Image, "__version__", "unknown")),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "wall_clock": "time.perf_counter_ns (monotonic)",
        "cpu_clock": "time.process_time_ns (process CPU)",
    }


def _measure_input(path: Path, *, samples: int, warmups: int) -> dict[str, Any]:
    raw, size = _read_bounded(path)
    digest = hashlib.sha256(raw).hexdigest()
    # Validate the explicit container and dimensions before any timed sample.
    # Pixel/CRC/protocol refusal remains a measured strict-decode failure.
    preflight = _load_png(path, expected_sha256=digest, expected_size=size)
    preflight.close()
    stage_values: dict[str, tuple[list[float], list[float]]] = {name: ([], []) for name in STAGE_NAMES}
    failures: list[dict[str, Any]] = []

    def run_once(index: int, *, retain: bool) -> None:
        image: Image.Image | None = None
        try:
            loaded = _timed(lambda: _load_png(path, expected_sha256=digest, expected_size=size))
            image = loaded.value
            if retain:
                stage_values["png_load"][0].append(loaded.wall_seconds)
                stage_values["png_load"][1].append(loaded.cpu_seconds)

            full = _timed(
                lambda: PixelDecoder().decode(
                    image,
                    monotonic=time.monotonic(),
                    window_identity="offline-performance-client",
                )
            )
            if full.value.kind != "FRESH" or full.value.frame is None:
                raise ProtocolError("fresh decoder did not return a FRESH frame")
            if retain:
                stage_values["full_strict_decode"][0].append(full.wall_seconds)
                stage_values["full_strict_decode"][1].append(full.cpu_seconds)
        except PerformanceInputError:
            raise
        except (OSError, ProtocolError, TypeError, ValueError) as exc:
            if retain:
                failures.append({"sample": index, "phase": "decode", "error_type": type(exc).__name__})
        finally:
            if image is not None:
                image.close()

        try:
            planners = _planner_timings()
            if retain:
                for name, timing in planners.items():
                    stage_values[name][0].append(timing.wall_seconds)
                    stage_values[name][1].append(timing.cpu_seconds)
        except (TypeError, ValueError) as exc:
            if retain:
                failures.append({"sample": index, "phase": "planning", "error_type": type(exc).__name__})

    for index in range(warmups):
        run_once(index, retain=False)
    for index in range(samples):
        run_once(index, retain=True)

    stages = {name: _stage_summary(wall, cpu) for name, (wall, cpu) in stage_values.items()}
    for name in (
        "pixel_extract_2x2_validation",
        "cell_unpack",
        "frame_inflate_json_schema_validation",
    ):
        stages[name] = _unmeasured_stage(
            "production decoder exposes no public boundary; included in full_strict_decode"
        )

    return {
        "input_sha256": digest,
        "input_size_bytes": size,
        "input_dimensions": list(EXPECTED_DIMENSIONS),
        "warmups": warmups,
        "samples_requested": samples,
        "failures": failures,
        "stages": stages,
    }


_RECEIPT_KNOWN_FIELDS = frozenset(
    {
        "artifacts",
        "binary",
        "boundaries",
        "candidate_status",
        "canonical",
        "claims",
        "container",
        "created_utc",
        "generated_utc",
        "harness",
        "integration_status",
        "predecessors",
        "private_build",
        "production",
        "review_required_before_live",
        "schema",
        "schema_version",
        "receipt_kind",
        "stage2_attestation",
        "scope",
        "status",
        "started_utc",
        "finished_utc",
        "source_hashes",
        "source",
        "build",
        "build_config",
        "receipt",
        "samples",
        "stages",
        "run_return",
        "failure",
        "failures",
        "capture",
        "io",
        "application_compute",
        "end_to_end_wall",
        "verification",
    }
)
_NESTED_RECEIPT_KNOWN_FIELDS = frozenset({"kind", "schema"})


def _receipt_diagnostic(path: Path) -> dict[str, Any]:
    """Read only bounded receipt metadata; never treat it as accepted evidence."""

    try:
        initial = path.stat()
    except OSError:
        return {"status": "refused", "reason_code": "receipt_unreadable"}
    if initial.st_size <= 0 or initial.st_size > MAX_RECEIPT_BYTES:
        return {"status": "refused", "reason_code": "receipt_size_out_of_bounds"}
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if (opened.st_dev, opened.st_ino, opened.st_size) != (
                initial.st_dev,
                initial.st_ino,
                initial.st_size,
            ):
                return {"status": "refused", "reason_code": "receipt_changed_during_read"}
            raw = handle.read(MAX_RECEIPT_BYTES + 1)
            finished = os.fstat(handle.fileno())
    except OSError:
        return {"status": "refused", "reason_code": "receipt_unreadable"}
    if (finished.st_dev, finished.st_ino, finished.st_size) != (
        opened.st_dev,
        opened.st_ino,
        opened.st_size,
    ):
        return {"status": "refused", "reason_code": "receipt_changed_during_read"}
    if len(raw) == 0 or len(raw) > MAX_RECEIPT_BYTES or len(raw) != opened.st_size:
        return {"status": "refused", "reason_code": "receipt_changed_during_read"}
    digest = hashlib.sha256(raw).hexdigest()
    try:
        value = _strict_json(raw)
    except PerformanceInputError as exc:
        return {
            "status": "refused",
            "reason_code": str(exc),
            "receipt_sha256": digest,
            "size_bytes": len(raw),
        }
    if not isinstance(value, dict):
        return {
            "status": "refused",
            "reason_code": "receipt_root_not_object",
            "receipt_sha256": digest,
            "size_bytes": len(raw),
        }
    keys = [key for key in value if isinstance(key, str)]
    nested = value.get("receipt")
    nested_keys = [key for key in nested if isinstance(key, str)] if isinstance(nested, dict) else []
    return {
        "status": "diagnostic_only",
        "reason_code": "receipt_contract_unavailable",
        "receipt_sha256": digest,
        "size_bytes": len(raw),
        "root_type": "object",
        "known_fields": sorted(set(keys) & _RECEIPT_KNOWN_FIELDS),
        "unknown_field_count": len(set(keys) - _RECEIPT_KNOWN_FIELDS),
        "nested_receipt_known_fields": sorted(set(nested_keys) & _NESTED_RECEIPT_KNOWN_FIELDS),
        "nested_receipt_unknown_field_count": len(set(nested_keys) - _NESTED_RECEIPT_KNOWN_FIELDS),
        "accepted_flag_present": "accepted" in value,
        "source_hashes_present": isinstance(value.get("source_hashes"), dict)
        or isinstance(value.get("accepted_source_hashes"), dict),
        "producer_binding_present": value.get("producer_binding") is not None,
        "config_binding_present": value.get("config_binding") is not None,
        "run_records_present": isinstance(value.get("runs"), list),
    }


def _decision(
    measurements: list[dict[str, Any]],
    receipt_paths: Sequence[Path],
    *,
    source_hashes: dict[str, str],
) -> dict[str, Any]:
    diagnostics = [_receipt_diagnostic(path) for path in receipt_paths]
    reasons = [
        "no_accepted_matching_region_instrumentation",
        "paired_cpu_and_end_to_end_intervals_unavailable",
        "insufficient_eight_sample_runs",
    ]
    if not receipt_paths:
        reasons.append("no_preserved_timing_receipts")
    else:
        reasons.append("receipt_contract_unavailable")
        if any(item.get("status") == "refused" for item in diagnostics):
            reasons.append("receipt_refused")
    limitations = [
        "Offline measurements never capture the desktop, send input, invoke Luna, or claim live freshness.",
        "PNG load is timed from an explicit path; the offline run does not measure native capture or IPC.",
        "Full strict decode includes all private pixel, cell, frame, JSON, and schema work.",
        (
            "The supplied receipt format is retained for bounded diagnostics only; it is not an "
            "accepted live instrumentation contract."
        ),
        (
            "Local decoder source hashes identify measured code, not an accepted region producer "
            "or runtime binding."
        ),
    ]
    receipt_counts = {
        "supplied": len(receipt_paths),
        "read": sum(item.get("receipt_sha256") is not None for item in diagnostics),
        "refused": sum(item.get("status") == "refused" for item in diagnostics),
    }
    return {
        "schema": "crowley.runtime-performance-decision",
        "schema_version": 1,
        "accepted_source_hashes": {},
        "producer_binding": None,
        "config_binding": None,
        "runs": [],
        "statistics": {
            "offline_measurements": measurements,
            "environment": _environment_metadata(),
            "cold_start_excluded": True,
            "measured_source_hashes": source_hashes,
            "receipt_counts": receipt_counts,
            "receipt_diagnostics": diagnostics,
            "quantile_definition": "sorted_samples[ceil(N*q)-1]",
            "eligibility": "insufficient_evidence",
            "eligible_run_count": 0,
            "pooled_completed_count": 0,
            "pooled_application_compute_cpu_p95_seconds": None,
            "pooled_end_to_end_wall_p95_seconds": None,
            "ratio_of_quantiles": None,
            "run_trigger_repeatability": {
                "trigger_runs": None,
                "eligible_runs": 0,
                "minimum_fraction": 0.80,
                "passed": None,
                "runs": [],
            },
            "deadline_failure_candidates": [],
        },
        "decision": "insufficient_evidence",
        "reason_codes": sorted(set(reasons)),
        "limitations": limitations,
    }


def build_report(
    inputs: Sequence[Path],
    receipts: Sequence[Path] = (),
    *,
    samples: int = 100,
    warmups: int = 5,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    if not 1 <= samples <= MAX_SAMPLES:
        raise PerformanceInputError(f"samples must be in 1..{MAX_SAMPLES}")
    if not 0 <= warmups <= MAX_SAMPLES:
        raise PerformanceInputError(f"warmups must be in 0..{MAX_SAMPLES}")
    if not 1 <= len(inputs) <= MAX_INPUTS:
        raise PerformanceInputError(f"inputs must contain 1..{MAX_INPUTS} explicit PNGs")
    if len(receipts) > MAX_RECEIPTS:
        raise PerformanceInputError(f"receipts must contain at most {MAX_RECEIPTS} explicit files")
    source_root = repo_root or Path(__file__).resolve().parents[1]
    source_hashes = _source_hashes(source_root)
    measurements = [_measure_input(path, samples=samples, warmups=warmups) for path in inputs]
    return _decision(measurements, receipts, source_hashes=source_hashes)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", dest="inputs", action="append", type=Path, required=True)
    parser.add_argument("--receipt", dest="receipts", action="append", type=Path, default=[])
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--warmups", type=int, default=5)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = build_report(
            args.inputs,
            args.receipts,
            samples=args.samples,
            warmups=args.warmups,
        )
    except PerformanceInputError as exc:
        print(f"session_performance: {exc}", file=sys.stderr)
        return 2
    encoded = json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.output is None:
        sys.stdout.write(encoded)
    else:
        args.output.write_text(encoded, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the CLI
    raise SystemExit(main())
