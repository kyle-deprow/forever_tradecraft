from __future__ import annotations

import binascii
import json
import struct
import zlib
from pathlib import Path

import pytest
from PIL import Image

import tools.session_performance as performance
from crowley.session.decoder import PixelDecoder
from crowley.session.protocol import CAPACITY, HEADER_SIZE, ProtocolError, pack_cells
from tests.wow_harness import WowClient
from tools.session_performance import (
    MAX_INPUTS,
    MAX_PNG_BYTES,
    MAX_RECEIPT_BYTES,
    MAX_RECEIPTS,
    PerformanceInputError,
    _stage_summary,
    build_report,
)


def _lua_fixture_image() -> Image.Image:
    """Render the actual Lua CRS1 fixture through the shared addon harness."""

    client = WowClient()
    client.set_canonical_plan()
    client.login()
    client.publish_agent()
    return client.render_agent_capture()


def _write_status_png(
    path: Path,
    *,
    mutate: tuple[int, int, tuple[int, int, int]] | None = None,
) -> None:
    image = _lua_fixture_image()
    try:
        if mutate is not None:
            x, y, color = mutate
            image.putpixel((x, y), color)
        image.save(path, format="PNG")
    finally:
        image.close()


def _write_frame_png(path: Path, frame: bytes) -> None:
    rows = pack_cells(frame)
    image = Image.new("RGB", (256, 256), (0, 0, 0))
    pixels = image.load()
    for row, bits in enumerate(rows):
        for column, bit in enumerate(bits):
            if bit:
                color = (255, 255, 255)
                for dy in range(2):
                    for dx in range(2):
                        pixels[column * 2 + dx, row * 2 + dy] = color
    image.save(path, format="PNG")
    image.close()


def _lua_frame() -> bytes:
    client = WowClient()
    client.set_canonical_plan()
    client.login()
    client.publish_agent()
    return client.agent_frame


def test_stage_summary_uses_ceil_quantiles_and_preserves_samples() -> None:
    summary = _stage_summary([0.01, 0.02, 0.03, 0.04], [0.001, 0.002, 0.003, 0.004])

    assert summary["wall_p95_ms"] == pytest.approx(40.0)
    assert summary["cpu_p95_ms"] == pytest.approx(4.0)
    assert summary["wall_samples_seconds"] == [0.01, 0.02, 0.03, 0.04]


def test_real_lua_crs1_fixture_decodes_at_public_boundary() -> None:
    image = _lua_fixture_image()
    try:
        sample = PixelDecoder().decode(image, monotonic=1.0, window_identity="lua-fixture")
    finally:
        image.close()
    assert sample.kind == "FRESH"
    assert sample.frame is not None
    assert sample.frame.snapshot.value["schema"] == 3


def test_offline_report_measures_public_decode_and_pure_planners(tmp_path: Path) -> None:
    input_path = tmp_path / "status.png"
    _write_status_png(input_path)

    report = build_report([input_path], samples=2, warmups=1)

    assert report["schema"] == "crowley.runtime-performance-decision"
    assert report["decision"] == "insufficient_evidence"
    assert "no_preserved_timing_receipts" in report["reason_codes"]
    measurement = report["statistics"]["offline_measurements"][0]
    assert measurement["input_sha256"]
    assert measurement["input_dimensions"] == [256, 256]
    assert measurement["failures"] == []
    for name in (
        "png_load",
        "full_strict_decode",
        "pointer_planning",
        "click_planning",
        "key_planning",
        "camera_planning",
    ):
        assert measurement["stages"][name]["samples"] == 2
    for name in (
        "pixel_extract_2x2_validation",
        "cell_unpack",
        "frame_inflate_json_schema_validation",
    ):
        stage = measurement["stages"][name]
        assert stage["samples"] is None
        assert stage["wall_samples_seconds"] is None
        assert stage["cpu_samples_seconds"] is None
        assert stage["unmeasured_reason"]
    assert report["statistics"]["environment"]["python"]


def test_pixel_disagreement_is_refused_by_public_decoder(tmp_path: Path) -> None:
    path = tmp_path / "bad-pixel.png"
    _write_status_png(path, mutate=(0, 0, (127, 127, 127)))
    with Image.open(path) as image:
        image.load()
        with pytest.raises(ProtocolError, match="neither black nor white"):
            PixelDecoder().decode(image, monotonic=1.0, window_identity="lua-fixture")


def test_physical_pixel_disagreement_is_refused_by_public_decoder(tmp_path: Path) -> None:
    path = tmp_path / "physical-pixel.png"
    image = _lua_fixture_image()
    try:
        original = image.getpixel((0, 0))[0]
        opposite = (255, 255, 255) if original < 128 else (0, 0, 0)
        image.putpixel((1, 0), opposite)
        image.save(path, format="PNG")
    finally:
        image.close()
    with Image.open(path) as image:
        image.load()
        with pytest.raises(ProtocolError, match="physical pixels disagree"):
            PixelDecoder().decode(image, monotonic=1.0, window_identity="lua-fixture")


def test_public_decoder_exercises_sequence_and_boot_guards() -> None:
    client = WowClient()
    client.set_canonical_plan()
    client.login()
    client.publish_agent()
    first_image = client.render_agent_capture()
    client.update_agent()
    client.publish_agent()
    second_image = client.render_agent_capture()
    other = WowClient()
    other.set_canonical_plan()
    other.login()
    other.publish_agent()
    other_image = other.render_agent_capture()
    try:
        decoder = PixelDecoder()
        first = decoder.decode(first_image, monotonic=1.0, window_identity="lua-fixture")
        second = decoder.decode(second_image, monotonic=2.0, window_identity="lua-fixture")
        assert first.kind == second.kind == "FRESH"
        assert second.frame is not None and first.frame is not None
        assert second.frame.sequence > first.frame.sequence
        with pytest.raises(ProtocolError, match="sequence is stale"):
            decoder.decode(first_image, monotonic=3.0, window_identity="lua-fixture")
        assert other_image.getpixel((0, 0)) in {(0, 0, 0), (255, 255, 255)}
        with pytest.raises(ProtocolError, match="unexpected status boot change"):
            decoder.decode(other_image, monotonic=4.0, window_identity="lua-fixture")
        decoder.allow_boot_change_once()
        boot = decoder.decode(other_image, monotonic=5.0, window_identity="lua-fixture")
        assert boot.kind == "FRESH"
        assert boot.frame is not None and boot.frame.boot != second.frame.boot
    finally:
        first_image.close()
        second_image.close()
        other_image.close()


def test_crc_valid_schema_refusal_reaches_public_decoder_guard(tmp_path: Path) -> None:
    frame = _lua_frame()
    payload_length = struct.unpack_from("<H", frame, 8)[0]
    raw = zlib.decompress(frame[HEADER_SIZE : HEADER_SIZE + payload_length], -15)
    snapshot = json.loads(raw)
    snapshot["schema"] = 2
    compressor = zlib.compressobj(wbits=-15)
    payload = compressor.compress(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode())
    payload += compressor.flush()
    header = frame[:8] + struct.pack("<H", len(payload)) + frame[10:22]
    crc = struct.pack("<I", binascii.crc32(header + payload) & 0xFFFFFFFF)
    malformed = header + crc + payload + bytes(CAPACITY - len(header) - len(crc) - len(payload))
    path = tmp_path / "schema.png"
    _write_frame_png(path, malformed)
    with Image.open(path) as image:
        image.load()
        with pytest.raises(ProtocolError, match="schema"):
            PixelDecoder().decode(image, monotonic=1.0, window_identity="lua-fixture")


def test_crc_refusal_is_retained_as_a_decode_failure(tmp_path: Path) -> None:
    frame = bytearray(_lua_frame())
    frame[22] ^= 1
    path = tmp_path / "bad-crc.png"
    _write_frame_png(path, bytes(frame))

    report = build_report([path], samples=1, warmups=0)

    measurement = report["statistics"]["offline_measurements"][0]
    assert measurement["stages"]["png_load"]["samples"] == 1
    assert measurement["stages"]["full_strict_decode"]["samples"] == 0
    assert measurement["stages"]["pixel_extract_2x2_validation"]["samples"] is None
    assert measurement["failures"] == [{"sample": 0, "phase": "decode", "error_type": "ProtocolError"}]


def test_invalid_container_and_dimensions_are_refused_before_timing(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.png"
    invalid.write_bytes(b"not a PNG")
    with pytest.raises(PerformanceInputError, match="PNG container"):
        build_report([invalid], samples=1, warmups=0)

    wrong_dimensions = tmp_path / "wrong-dimensions.png"
    Image.new("RGB", (257, 256), (0, 0, 0)).save(wrong_dimensions, format="PNG")
    with pytest.raises(PerformanceInputError, match="dimensions"):
        build_report([wrong_dimensions], samples=1, warmups=0)


def test_input_drift_is_refused_before_a_sample_is_timed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "status.png"
    _write_status_png(path)
    original_load = performance._load_png
    calls = 0

    def change_after_preflight(candidate: Path, **kwargs: object) -> Image.Image:
        nonlocal calls
        image = original_load(candidate, **kwargs)
        calls += 1
        if calls == 1:
            changed = _lua_fixture_image()
            try:
                changed.putpixel((0, 0), (127, 127, 127))
                changed.save(candidate, format="PNG")
            finally:
                changed.close()
        return image

    monkeypatch.setattr(performance, "_load_png", change_after_preflight)
    with pytest.raises(PerformanceInputError, match="changed since preflight"):
        build_report([path], samples=1, warmups=0)


def test_bounds_reject_inputs_receipts_and_oversized_png(tmp_path: Path) -> None:
    path = tmp_path / "status.png"
    _write_status_png(path)
    with pytest.raises(PerformanceInputError, match="inputs"):
        build_report([path] * (MAX_INPUTS + 1), samples=1, warmups=0)
    oversized = tmp_path / "oversized.png"
    oversized.write_bytes(b"x" * (MAX_PNG_BYTES + 1))
    with pytest.raises(PerformanceInputError, match="PNG input size"):
        build_report([oversized], samples=1, warmups=0)
    with pytest.raises(PerformanceInputError, match="receipts"):
        build_report([path], [path] * (MAX_RECEIPTS + 1), samples=1, warmups=0)


def test_fabricated_accepted_receipt_is_diagnostic_only(tmp_path: Path) -> None:
    input_path = tmp_path / "status.png"
    _write_status_png(input_path)
    receipt_path = tmp_path / "private-run-identity.json"
    receipt_path.write_text(
        json.dumps(
            {
                "schema": "diagnostic-receipt",
                "boundaries": {"known": True},
                "unreviewed_user_field": "omit",
                "accepted": True,
                "accepted_source_hashes": {"fake": "source"},
                "producer_binding": {"path": "private"},
                "config_binding": {"character": "redacted"},
                "runs": [{"run_id": "private-run-identity", "samples": []}],
            }
        ),
        encoding="utf-8",
    )

    report = build_report([input_path], [receipt_path], samples=1, warmups=0)

    assert report["decision"] == "insufficient_evidence"
    assert report["accepted_source_hashes"] == {}
    assert report["producer_binding"] is None
    assert report["config_binding"] is None
    assert report["runs"] == []
    diagnostic = report["statistics"]["receipt_diagnostics"][0]
    assert diagnostic["status"] == "diagnostic_only"
    assert diagnostic["reason_code"] == "receipt_contract_unavailable"
    assert diagnostic["known_fields"] == ["boundaries", "schema"]
    assert diagnostic["unknown_field_count"] == 6
    encoded = json.dumps(report, sort_keys=True)
    assert "private-run-identity" not in encoded
    assert "redacted" not in encoded


def test_receipt_descriptor_read_refuses_growth_before_capped_read(tmp_path: Path) -> None:
    path = tmp_path / "growing.json"
    path.write_bytes(b"{}")

    class GrowingReceipt:
        def stat(self):
            return path.stat()

        def open(self, mode: str):
            assert mode == "rb"
            path.write_bytes(b"{}" + b"x" * MAX_RECEIPT_BYTES)
            return path.open(mode)

    diagnostic = performance._receipt_diagnostic(GrowingReceipt())
    assert diagnostic == {"status": "refused", "reason_code": "receipt_changed_during_read"}


def test_deeply_nested_receipt_has_bounded_json_refusal(tmp_path: Path) -> None:
    path = tmp_path / "deep.json"
    path.write_text("[" * 10000 + "]" * 10000, encoding="utf-8")
    diagnostic = performance._receipt_diagnostic(path)
    assert diagnostic["status"] == "refused"
    assert diagnostic["reason_code"] == "receipt_json_nesting_exceeded"


def test_no_receipt_metadata_is_explicitly_null_or_empty(tmp_path: Path) -> None:
    input_path = tmp_path / "status.png"
    _write_status_png(input_path)
    report = build_report([input_path], samples=1, warmups=0)

    assert report["accepted_source_hashes"] == {}
    assert report["producer_binding"] is None
    assert report["config_binding"] is None
    stats = report["statistics"]
    assert stats["pooled_application_compute_cpu_p95_seconds"] is None
    assert stats["pooled_end_to_end_wall_p95_seconds"] is None
    assert stats["ratio_of_quantiles"] is None
