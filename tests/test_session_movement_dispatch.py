from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from crowley.session.driver import DriverError, build_camera_drag_chain
from crowley.session.executor import (
    BindingMetadata,
    CameraDragPlan,
    Point,
    PointerButton,
    PointerSample,
)
from crowley.session.guardian import GuardianError, InputGuardian


def test_camera_chain_is_one_right_held_closed_argv_with_endpoint_motion() -> None:
    binding = BindingMetadata("client", "capture", 1, 2, 7, (7,), boot="boot")
    plan = CameraDragPlan(
        PointerButton.RIGHT,
        (
            PointerSample(0.0, Point(20, 20)),
            PointerSample(0.05, Point(30, 20)),
            PointerSample(0.10, Point(40, 20)),
        ),
        0.10,
        Point(20, 0),
        binding,
    )
    chain = build_camera_drag_chain(plan, (100, 200, 400, 300))
    assert chain[:3] == ["xdotool", "mousedown", "3"]
    assert chain[-2:] == ["mouseup", "3"]
    assert chain.count("mousemove") == 2
    assert chain.count("mousedown") == chain.count("mouseup") == 1
    assert sum(
        float(chain[index + 1]) for index, token in enumerate(chain) if token == "sleep"
    ) == pytest.approx(plan.duration)


def test_camera_chain_rejects_endpoint_outside_verified_client() -> None:
    binding = BindingMetadata("client", "capture", 1, 2, 7, (7,), boot="boot")
    plan = CameraDragPlan(
        PointerButton.RIGHT,
        (PointerSample(0.0, Point(20, 20)), PointerSample(0.1, Point(100, 20))),
        0.1,
        Point(80, 0),
        binding,
    )
    with pytest.raises(DriverError, match="escaped"):
        build_camera_drag_chain(plan, (100, 200, 50, 50))


def test_calibration_observer_may_coexist_only_with_certified_bootstrap_group(tmp_path) -> None:
    guardian = InputGuardian(tmp_path / "calibration-observer.lock", parent_pid=os.getpid())
    try:
        epoch = guardian.begin_calibration_operation()
        guardian.register_calibration_bootstrap_process(101, epoch)
        observer = SimpleNamespace(
            observer=SimpleNamespace(process=SimpleNamespace(pid=202)),
            release_admission_gate=lambda: None,
        )
        guardian.observer_dispatch_admission(lambda: observer, calibration=True)
        ticket = SimpleNamespace(epoch=epoch)
        guardian.issue_calibration_ticket(ticket)
        assert guardian.observer_process_groups == frozenset({202})
        with pytest.raises(GuardianError, match="physical ownership"):
            guardian.observer_dispatch_admission(
                lambda: SimpleNamespace(observer=SimpleNamespace(process=SimpleNamespace(pid=303))),
            )
        guardian.unregister_process_group(101)
        with pytest.raises(GuardianError, match="physical ownership"):
            guardian.observer_dispatch_admission(
                lambda: SimpleNamespace(observer=SimpleNamespace(process=SimpleNamespace(pid=404))),
                calibration=True,
            )
    finally:
        guardian.unregister_observer_process(202)
        guardian.unregister_process_group(101)
        guardian.close()
