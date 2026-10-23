"""Guardian correlation tests for the retained native hover prefix.

The four source-4 events below and the undelimited final Motion are copied from
the retained observer diagnostic. Modeled source-7 events in the completion and
negative tests exercise the matcher only; they are not additional native
evidence from that attempt.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from crowley.session.guardian import InputGuardian
from crowley.session.input_events import EventClass, XI2Event, XI2StreamParser

_RETAINED_RAW_BLOCKS = (
    "⎡ Virtual core pointer                    \tid=2\t[master pointer  (3)]\n"
    "⎜   ↳ Virtual core XTEST pointer              \tid=4\t[slave  pointer  (2)]\n"
    "⎜   ↳ xwayland-pointer:17                     \tid=6\t[slave  pointer  (2)]\n"
    "⎜   ↳ xwayland-relative-pointer:17            \tid=7\t[slave  pointer  (2)]\n"
    "⎜   ↳ xwayland-pointer-gestures:17            \tid=8\t[slave  pointer  (2)]\n"
    "⎣ Virtual core keyboard                   \tid=3\t[master keyboard (2)]\n"
    "    ↳ Virtual core XTEST keyboard             \tid=5\t[slave  keyboard (3)]\n"
    "    ↳ xwayland-keyboard:17                    \tid=9\t[slave  keyboard (3)]\n",
    "EVENT type 17 (RawMotion)\n"
    "    device: 2 (4)\n"
    "    time:   527685625\n"
    "    detail: 0\n"
    "    flags: \n"
    "    valuators:\n"
    "          0: 1029.00 (1029.00)\n"
    "          1: 340.00 (340.00)\n\n",
    "EVENT type 6 (Motion)\n"
    "    device: 4 (4)\n"
    "    time: 527685625\n"
    "    detail: 0\n"
    "    flags: \n"
    "    root: 1030.00/340.00\n"
    "    event: 1030.00/340.00\n"
    "    buttons:\n"
    "    modifiers: locked 0x10 latched 0 base 0 effective: 0x10\n"
    "    group: locked 0 latched 0 base 0 effective: 0\n"
    "    valuators:\n"
    "        0: 1029.00\n"
    "        1: 340.00\n"
    "    windows: root 0x374 event 0x374 child 0x3c00003\n",
    "EVENT type 17 (RawMotion)\n"
    "    device: 2 (4)\n"
    "    time:   527685658\n"
    "    detail: 0\n"
    "    flags: \n"
    "    valuators:\n"
    "          0: 1028.00 (1028.00)\n"
    "          1: 340.00 (340.00)\n\n",
)
_RETAINED_PARTIAL_TAIL = (
    "EVENT type 6 (Motion)\n"
    "    device: 4 (4)\n"
    "    time: 527685658\n"
    "    detail: 0\n"
    "    flags: \n"
    "    root: 1029.00/340.00\n"
    "    event: 1029.00/340.00\n"
    "    buttons:\n"
    "    modifiers: locked 0x10 latched 0 base 0 effective: 0x10\n"
    "    group: locked 0 latched 0 base 0 effective: 0\n"
    "    valuators:\n"
    "        0: 1028.00\n"
    "        1: 340.00\n"
    "    windows: root 0x374 event 0x374 child 0x3c00003\n"
)
_RETAINED_RAW_BLOCK_PINS = (
    (608, "02c9507265b87e126f0be0eb194d38f3b4974500e0982937f3c984666c77f6e6"),
    (168, "2d990544540f224841e564e348c0863102b242571fc6a30a76333be13e191d5d"),
    (364, "fd595440f00099dcf1ea266a5892cfbbb41b6e7f29a8971775d6578c91dbd548"),
    (168, "70844ecc686cfc25a035d0cdc49b4a0d325e9fe1048f8185e542f7f7b88b4c78"),
)
_RETAINED_PARTIAL_TAIL_PIN = (
    364,
    "30979cc2b004ef03af4d1156955b9e9f2c9885c2cc697e9049e0d93656ff3486",
)
_TARGET = 0x3C00003
_CERTIFIED_EVENT_XIDS = frozenset({0x300002A, _TARGET})
_MOTION_ENDPOINTS = (
    (1029, 340),
    (1028, 340),
    (1026, 340),
    (1025, 340),
    (1023, 340),
    (1021, 339),
    (1020, 339),
    (1018, 338),
    (1017, 337),
    (1016, 336),
    (1015, 336),
    (1014, 335),
    (1013, 335),
    (1012, 335),
    (1011, 335),
    (1010, 334),
    (1009, 334),
    (1007, 333),
    (1006, 333),
    (1005, 332),
    (1004, 331),
    (1003, 330),
    (1002, 330),
    (1002, 329),
    (1001, 329),
    (999, 328),
    (998, 328),
    (996, 327),
    (995, 327),
    (993, 327),
    (992, 327),
    (991, 327),
    (990, 327),
    (989, 327),
)
_EXPECTED_MOTION_TRACE = tuple((x, y, x, y) for x, y in _MOTION_ENDPOINTS)
_ECHO_SOURCES = frozenset({7})


def _parse_retained_prefix() -> list[XI2Event]:
    for block, (expected_length, expected_digest) in zip(
        _RETAINED_RAW_BLOCKS, _RETAINED_RAW_BLOCK_PINS, strict=True
    ):
        encoded = block.encode("utf-8")
        assert len(encoded) == expected_length
        assert hashlib.sha256(encoded).hexdigest() == expected_digest
    partial_tail = _RETAINED_PARTIAL_TAIL.encode("utf-8")
    assert len(partial_tail) == _RETAINED_PARTIAL_TAIL_PIN[0]
    assert hashlib.sha256(partial_tail).hexdigest() == _RETAINED_PARTIAL_TAIL_PIN[1]
    parser = XI2StreamParser()
    events: list[XI2Event] = []
    assert not _RETAINED_PARTIAL_TAIL.endswith("\n\n")
    for block in (*_RETAINED_RAW_BLOCKS, _RETAINED_PARTIAL_TAIL):
        for line in block.splitlines(keepends=True):
            event = parser.feed(line)
            if event is not None:
                events.append(event)
    assert parser.failure_diagnostic is None
    assert len(events) == 4
    return events


def _begin_canonical_hover(
    tmp_path: Path,
    name: str,
    *,
    expected_motion_trace: tuple[tuple[int, int, int, int], ...] = _EXPECTED_MOTION_TRACE,
) -> tuple[InputGuardian, int, object]:
    guardian = InputGuardian(tmp_path / f"{name}.lock", parent_pid=os.getppid())
    generation = guardian.arm(SimpleNamespace(is_live=True, fingerprint="retained-hover-identity"))
    event_classes = {"DeviceChanged", "RawMotion", "Motion", "Enter", "Leave"}
    action = guardian.begin_action(
        generation,
        target_xid=0x300002A,
        source_device=4,
        master_device=2,
        event_classes=event_classes,
        device_by_class={
            event_class: 2 if event_class in {"DeviceChanged", "RawMotion"} else 4
            for event_class in event_classes
        },
        optional_classes={"DeviceChanged", "Enter", "Leave"},
        target_ancestor=lambda xid: xid in _CERTIFIED_EVENT_XIDS,
        expected_modifiers=(0x10, 0, 0),
        expected_motion_trace=expected_motion_trace,
        initial_origin=(1030, 340, 1030, 340),
        expected_root_xid=0x374,
        expected_event_xid=0x374,
        expected_child_xids=_CERTIFIED_EVENT_XIDS,
        canonical_motion=True,
        echo_sources=_ECHO_SOURCES,
        timeout=5.0,
    )
    return guardian, generation, action


def _modeled_echo(
    primary: XI2Event,
    *,
    timestamp_ms: int,
    source_device: int = 7,
    master_device: int = 7,
    target: int = _TARGET,
    root_xid: int = 0x374,
    event_xid: int = 0x374,
    root_xy: tuple[float, float] | None = None,
    event_xy: tuple[float, float] | None = None,
    modifiers: tuple[int, int, int] | None = None,
) -> XI2Event:
    endpoint = tuple(
        float(value) for axis in (0, 1) for row_axis, value, _raw in primary.valuators if row_axis == axis
    )
    assert len(endpoint) == 2
    return XI2Event(
        6,
        EventClass.MOTION,
        master_device,
        source_device,
        timestamp_ms,
        0,
        root_xid,
        event_xid,
        target,
        endpoint if root_xy is None else root_xy,
        endpoint if event_xy is None else event_xy,
        primary.modifiers if modifiers is None else modifiers,
        modifier_effective=(
            (primary.modifier_effective if modifiers is None else 0)
            if modifiers is None or modifiers == primary.modifiers
            else modifiers[0] | modifiers[1] | modifiers[2]
        ),
    )


def _observe_retained_prefix(guardian: InputGuardian, events: list[XI2Event]) -> None:
    for event in events:
        assert guardian.observe(event), (event.event_class.value, guardian.revoked_reason)


def test_retained_native_partial_tail_advances_primary_fifo_but_never_completes_without_echoes(
    tmp_path: Path,
) -> None:
    """Replay the exact native prefix through the parser and production Guardian."""

    events = _parse_retained_prefix()
    assert [
        (event.event_class.value, event.source_device, event.master_device, event.timestamp_ms)
        for event in events
    ] == [
        ("RawMotion", 4, 2, 527685625),
        ("Motion", 4, 4, 527685625),
        ("RawMotion", 4, 2, 527685658),
        ("Motion", 4, 4, 527685658),
    ]
    assert events[3].target_xid == _TARGET
    assert events[3].valuators == ((0, 1028.0, None), (1, 340.0, None))

    guardian, _generation, action = _begin_canonical_hover(tmp_path, "retained-prefix")
    try:
        _observe_retained_prefix(guardian, events)
        assert guardian.armed
        assert action.motion_index == 2
        assert action.emitted_motion_count == 2
        assert action.echo_index == 0
        assert len(action.pending_echoes) == 2
        assert action.raw_motion_pairing.pending_timestamps == []
        assert not action.complete
    finally:
        guardian.close()


def test_retained_prefix_completes_only_after_bounded_fifo_echo_pairs(tmp_path: Path) -> None:
    """Modeled echoes test completion semantics, not the retained host trace."""

    events = _parse_retained_prefix()
    guardian, generation, action = _begin_canonical_hover(
        tmp_path,
        "modeled-completion",
        expected_motion_trace=_EXPECTED_MOTION_TRACE[:2],
    )
    try:
        _observe_retained_prefix(guardian, events)
        first_echo = _modeled_echo(events[1], timestamp_ms=events[3].timestamp_ms + 2)
        second_echo = _modeled_echo(events[3], timestamp_ms=events[3].timestamp_ms + 10)
        assert guardian.observe(first_echo)
        assert action.echo_index == 1
        assert len(action.pending_echoes) == 1
        assert not action.complete
        assert guardian.observe(second_echo)
        assert action.echo_index == 2
        assert not action.pending_echoes
        assert action.complete
        guardian.finish_action(generation, action)
    finally:
        guardian.close()


@pytest.mark.parametrize(
    "variant",
    (
        "unsolicited",
        "duplicate",
        "reordered",
        "late",
        "wrong-source",
        "wrong-master",
        "wrong-target",
        "wrong-root",
        "wrong-event-window",
        "wrong-endpoint",
        "wrong-modifiers",
        "unknown-physical-source",
    ),
)
def test_retained_hover_echo_contract_rejects_unpaired_or_mismatched_motion(
    tmp_path: Path,
    variant: str,
) -> None:
    events = _parse_retained_prefix()
    guardian, _generation, _action = _begin_canonical_hover(tmp_path, f"negative-{variant}")
    try:
        if variant == "unsolicited":
            event = _modeled_echo(events[1], timestamp_ms=events[1].timestamp_ms + 1)
        else:
            _observe_retained_prefix(guardian, events)
            first_echo = _modeled_echo(events[1], timestamp_ms=events[3].timestamp_ms + 2)
            second_echo = _modeled_echo(events[3], timestamp_ms=events[3].timestamp_ms + 10)
            if variant == "duplicate":
                assert guardian.observe(first_echo)
                event = first_echo
            elif variant == "reordered":
                event = second_echo
            elif variant == "late":
                event = _modeled_echo(events[1], timestamp_ms=events[1].timestamp_ms + 251)
            elif variant == "wrong-source":
                event = _modeled_echo(
                    events[1], timestamp_ms=events[3].timestamp_ms + 2, source_device=8, master_device=8
                )
            elif variant == "wrong-master":
                event = _modeled_echo(events[1], timestamp_ms=events[3].timestamp_ms + 2, master_device=2)
            elif variant == "wrong-target":
                event = _modeled_echo(events[1], timestamp_ms=events[3].timestamp_ms + 2, target=_TARGET + 1)
            elif variant == "wrong-root":
                event = _modeled_echo(events[1], timestamp_ms=events[3].timestamp_ms + 2, root_xid=0x375)
            elif variant == "wrong-event-window":
                event = _modeled_echo(events[1], timestamp_ms=events[3].timestamp_ms + 2, event_xid=0x375)
            elif variant == "wrong-endpoint":
                event = _modeled_echo(
                    events[1],
                    timestamp_ms=events[3].timestamp_ms + 2,
                    root_xy=(1030.0, 340.0),
                )
            elif variant == "wrong-modifiers":
                event = _modeled_echo(
                    events[1], timestamp_ms=events[3].timestamp_ms + 2, modifiers=(0x10, 1, 0)
                )
            else:
                event = events[3].__class__(
                    events[3].type_number,
                    events[3].event_class,
                    2,
                    9,
                    events[3].timestamp_ms + 1,
                    events[3].detail,
                    events[3].root_xid,
                    events[3].event_xid,
                    events[3].child_xid,
                    events[3].root_xy,
                    events[3].event_xy,
                    events[3].modifiers,
                    modifier_effective=events[3].modifier_effective,
                    valuators=events[3].valuators,
                )
        assert not guardian.observe(event)
        assert not guardian.armed
        assert guardian.revoked_reason.startswith("unattributed XI2 event class=Motion")
    finally:
        guardian.close()
