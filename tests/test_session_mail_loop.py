from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from crowley.session import protocol
from crowley.session.cli import SessionIPC
from crowley.session.controller import Controller, ControllerState, SessionMode
from crowley.session.journal import Journal
from crowley.session.mail_loop import (
    MailLoopBinding,
    MailLoopBoundary,
    MailOperationBounds,
    admit_mail_cycle,
)

from .test_session_executor_click import (
    _pre_evidence,
    _started_executor_projection,
    _test_anchor,
    _test_receipt,
    _wire_fixture,
)
from .test_session_mail_loop_composition import QUEUE_ID, _make_case, _start_request
from .test_session_transitions import _Driver


def _bounds() -> MailOperationBounds:
    return MailOperationBounds(1, 1, 1, 1, 1, 1, 1)


def _valid_frame() -> protocol.Frame:
    frame, _ = _wire_fixture()
    value = copy.deepcopy(frame.snapshot.value)
    value["ahOpen"] = True
    value["wallTime"] = 1760000890
    value["loaded"] = {"ackedIds": ["scan-1"], "generatedAt": 1760000001}
    value["scanner"]["phase"] = "ready"
    value["scanner"]["dueAt"] = 1760000000
    return protocol.decode_frame(protocol.encode_frame(value))


def _boundary() -> MailLoopBoundary:
    return MailLoopBoundary(
        generation=1,
        session_mode="repeat",
        repeat_phase=ControllerState.WAIT_DUE.value,
        ack_loaded_uid="scan-1",
        status_last_uid="scan-1",
        seen_ack_uids=frozenset(),
        unresolved_action=False,
        reconciliation_pending=False,
        stop_requested=False,
        closeout_pending=False,
        last_actual_start_at=1760000000,
        now=1760000890,
    )


def _seed_mail_controller(
    tmp_path: Path, *, journal: Journal | None = None
) -> tuple[Controller, protocol.Frame, object]:
    journal = journal or Journal(tmp_path / "session.json")
    controller = Controller(
        journal, driver=_Driver(), recover_on_restart=False, wall_clock=lambda: 1760000890
    )
    controller._state = ControllerState.WAIT_DUE
    controller._mode = SessionMode.REPEAT
    controller._generation = 1
    controller._lease_generation = 1
    controller._started_at = 1760000000
    controller.driver.guardian.armed = True
    controller.driver.guardian.generation = 1
    controller._last_uid = "scan-1"
    controller._evidence_meta = {"ackLoadedUID": "scan-1"}
    frame = _valid_frame()
    binding = MailLoopBinding(
        True, 1, frame.snapshot.value["executor"]["queueId"], 1, "beta-normal-alliance", "Arthur"
    )
    decision = admit_mail_cycle(frame.snapshot, binding, _boundary(), _bounds())
    return controller, frame, decision


def _begin_seeded_cycle(controller: Controller, frame: protocol.Frame, decision: object):
    capability = controller.begin_mail_cycle(
        decision=decision,
        ack_loaded_uid="scan-1",
        status_last_uid="scan-1",
        wire_ack_uids=("scan-1",),
        queue_id=decision.queue_id,
        seq=1,
        house="beta-normal-alliance",
        character="Arthur",
        snapshot=frame.snapshot,
        binding=MailLoopBinding(True, 1, decision.queue_id, 1, "beta-normal-alliance", "Arthur"),
        bounds=_bounds(),
        expected_generation=1,
        expected_lease_generation=1,
    )
    return capability


def _accept_seeded_terminal(
    controller: Controller, frame: protocol.Frame, decision: object, capability: object
) -> dict:
    """Drive the real executor archive/proof gate for completion tests."""

    started_frame, _ = _wire_fixture(started=True)
    pre_value = copy.deepcopy(frame.snapshot.value)
    pre_value["boot"] = started_frame.boot
    pre_frame = protocol.decode_frame(protocol.encode_frame(pre_value))
    pre_evidence = {
        "sha256": hashlib.sha256(pre_frame.raw_bytes).hexdigest(),
        "length": len(pre_frame.raw_bytes),
        "crc32": pre_frame.crc32,
        "rawFrameHex": pre_frame.raw_bytes.hex(),
    }
    # The physical executor attempt belongs to the already opened mailbox
    # confirmation boundary.  Keep this helper on the public one-way graph;
    # it must not begin/finalize an action while the cycle still claims the
    # route-to-mailbox phase.
    for phase in ("preparing", "mailbox_open", "awaiting_confirmation"):
        controller.transition_mail_cycle(phase, capability=capability)
    controller.begin_executor_click(
        queue_id=decision.queue_id,
        seq=1,
        generation=1,
        lease_generation=1,
        cycle_id=capability.cycle_id,
        pre_crs={
            "boot": pre_frame.boot,
            "sequence": pre_frame.sequence,
            "crc32": pre_frame.crc32,
            "identity": "client",
        },
        pre_ordinal=0,
        arms={"published": False, "session": False},
        anchor=_test_anchor(),
        confirmation="",
        pre_executor=frame.snapshot.value["executor"],
        pre_evidence=pre_evidence,
    )
    controller.finalize_executor_click(
        attempt_id=controller.executor_click_checkpoint()["intent"]["attemptId"],
        result="started",
        post_crs={
            "boot": started_frame.boot,
            "sequence": started_frame.sequence,
            "crc32": started_frame.crc32,
            "identity": "client",
        },
        receipt=_test_receipt(),
        terminal_action=False,
        post_executor=_started_executor_projection(),
        pre_evidence=pre_evidence,
        post_evidence=_pre_evidence(started=True),
    )
    controller.transition_mail_cycle("executing", capability=capability, last_executor_seq=1)
    terminal = copy.deepcopy(started_frame.snapshot.value)
    terminal["sequence"] = started_frame.sequence + 1
    terminal["uptimeMs"] = started_frame.uptime_ms + 1000
    terminal["executor"].update(
        {
            "currentSeq": 0,
            "currentKind": "",
            "phase": "complete",
            "inFlight": False,
            "clickReady": False,
            "workDone": 0,
            "workTotal": 0,
            "blocked": False,
            "latched": False,
            "lastResult": {"seq": 1, "kind": "mail_collect", "status": "succeeded"},
        }
    )
    terminal_frame = protocol.decode_frame(protocol.encode_frame(terminal))
    return controller.observe_mail_cycle_completion(
        capability=capability,
        post_crs={
            "boot": started_frame.boot,
            "sequence": terminal_frame.sequence,
            "crc32": terminal_frame.crc32,
            "identity": "client",
        },
        post_executor=terminal_frame.snapshot.value["executor"],
        post_evidence={
            "sha256": hashlib.sha256(terminal_frame.raw_bytes).hexdigest(),
            "length": len(terminal_frame.raw_bytes),
            "crc32": terminal_frame.crc32,
            "rawFrameHex": terminal_frame.raw_bytes.hex(),
        },
    )


def test_real_lua_frame_bytes_validate_before_default_ipc_status() -> None:
    frame = _valid_frame()
    assert len(frame.raw_bytes) == protocol.CAPACITY
    assert protocol.validate_snapshot(frame.snapshot.value).value == frame.snapshot.value

    class Owner:
        def mail_loop_status(self) -> dict[str, object]:
            return {"enabled": False, "cycle": {"phase": "none"}}

    response = SessionIPC(SimpleNamespace(), Owner()).dispatch({"command": "mail_loop_status"})
    assert response == {"ok": True, "status": {"enabled": False, "cycle": {"phase": "none"}}}


def test_policy_admission_consumes_exact_lua_snapshot_shape() -> None:
    frame = _valid_frame()
    decision = admit_mail_cycle(
        frame.snapshot,
        MailLoopBinding(
            enabled=True,
            generation=1,
            queue_id=frame.snapshot.value["executor"]["queueId"],
            seq=1,
            house=frame.snapshot.value["house"]["key"],
            character=frame.snapshot.value["context"]["character"],
        ),
        _boundary(),
        _bounds(),
    )
    assert decision.admitted is True
    assert decision.mail_units == 2
    assert decision.completion_deadline_at is not None


def test_daemon_immediate_mail_items_requires_fresh_confirmation_and_click_reserve(
    tmp_path: Path,
) -> None:
    """A same-callback mail_items boundary never authorizes an implicit click."""

    daemon, backend, driver, controller, _clock = _make_case(tmp_path, armed=True, max_messages=2)
    client = backend.agent_client
    assert client is not None
    try:
        client.set_auto_postconditions(True)
        assert client.ns.Executor.Arm(QUEUE_ID) is True
        client.publish_agent()
        assert _start_request(controller, daemon)["ok"] is True
        daemon.run_once()
        capability = controller.mail_cycle_capability()
        assert capability is not None
        response = SessionIPC(controller, daemon).dispatch(
            {
                "command": "executor_click",
                "generation": controller.status().generation,
                "queueId": QUEUE_ID,
                "seq": 1,
                "confirmQueueId": QUEUE_ID,
                "cycleId": capability.cycle_id,
            }
        )
        assert response["ok"] is True and response["result"] == "started"
        executor = client.snapshot_agent()["executor"]
        assert executor["phase"] == "mail_items"
        assert executor["inFlight"] is True
        assert executor["workDone"] == 1
        assert controller.mail_cycle_checkpoint()["phase"] == "awaiting_confirmation"
        assert controller.mail_cycle_checkpoint()["completedUnits"] == 1
        clicks = backend._executor_clicks
        refused = SessionIPC(controller, daemon).dispatch(
            {
                "command": "executor_click",
                "generation": controller.status().generation,
                "queueId": QUEUE_ID,
                "seq": 1,
                "confirmQueueId": "",
                "cycleId": capability.cycle_id,
            }
        )
        assert refused["ok"] is False
        assert backend._executor_clicks == clicks
        client.advance(1)
        client.update_agent()
        daemon.run_once()
        continued = SessionIPC(controller, daemon).dispatch(
            {
                "command": "executor_click",
                "generation": controller.status().generation,
                "queueId": QUEUE_ID,
                "seq": 1,
                "confirmQueueId": QUEUE_ID,
                "cycleId": capability.cycle_id,
            }
        )
        assert continued["ok"] is True and continued["result"] in {"started", "succeeded"}, continued
        assert backend._executor_clicks == clicks + 1
        after_continuation = client.snapshot_agent()["executor"]
        if continued["result"] == "started":
            assert after_continuation["phase"] == "mail_wait"
            assert after_continuation["inFlight"] is True
            assert after_continuation["workDone"] == 1
        else:
            assert after_continuation["lastResult"] == {
                "seq": 1,
                "kind": "mail_collect",
                "status": "succeeded",
            }
            assert after_continuation["phase"] == "ready"
            assert after_continuation["currentSeq"] == 2
    finally:
        driver.close()


def test_mail_budget_exact_fit_uses_current_operation_remainder(tmp_path: Path) -> None:
    """A ticking helper clock cannot reject a zero-slack exact fit."""

    daemon, backend, driver, controller, _clock = _make_case(tmp_path, armed=True, max_messages=2)
    client = backend.agent_client
    assert client is not None
    try:
        assert client.ns.Executor.Arm(QUEUE_ID) is True
        client.publish_agent()
        assert _start_request(controller, daemon)["ok"] is True
        daemon.run_once()
        capability = controller.mail_cycle_capability()
        assert capability is not None
        budget = capability.budget
        future = (
            (capability.mail_units - 1) * (budget.mail_click_seconds + budget.mail_postcondition_seconds)
            + budget.route_to_auctioneer_seconds
            + budget.ah_reopen_seconds
        )
        operation_deadline = capability.deadline_monotonic - future
        sample_now = operation_deadline - 0.5
        samples = iter((sample_now - 0.25, sample_now, sample_now + 0.05))
        calls: list[float] = []

        def ticking_clock() -> float:
            value = next(samples)
            calls.append(value)
            return value

        daemon._mail_cycle_clock = ticking_clock
        daemon._mail_cycle_require_budget(
            capability,
            budget.mail_click_seconds + budget.mail_postcondition_seconds,
            "exact-fit click",
            operation_deadline=operation_deadline,
        )
        assert len(calls) == 2
    finally:
        driver.close()


def test_controller_default_cycle_marker_is_durable_and_pause_blocks_same_ack(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "session.json")
    controller = Controller(
        journal, driver=_Driver(), recover_on_restart=False, wall_clock=lambda: 1760000890
    )
    controller._state = ControllerState.WAIT_DUE
    controller._mode = SessionMode.REPEAT
    controller._generation = 1
    controller._lease_generation = 1
    controller._started_at = 1760000000
    controller.driver.guardian.armed = True
    controller.driver.guardian.generation = 1
    controller._last_uid = "scan-1"
    controller._evidence_meta = {"ackLoadedUID": "scan-1"}
    frame = _valid_frame()
    decision = admit_mail_cycle(
        frame.snapshot,
        MailLoopBinding(
            True, 1, frame.snapshot.value["executor"]["queueId"], 1, "beta-normal-alliance", "Arthur"
        ),
        _boundary(),
        _bounds(),
    )
    capability = controller.begin_mail_cycle(
        decision=decision,
        ack_loaded_uid="scan-1",
        status_last_uid="scan-1",
        wire_ack_uids=("scan-1",),
        queue_id=decision.queue_id,
        seq=1,
        house="beta-normal-alliance",
        character="Arthur",
        snapshot=frame.snapshot,
        binding=MailLoopBinding(True, 1, decision.queue_id, 1, "beta-normal-alliance", "Arthur"),
        bounds=_bounds(),
        expected_generation=1,
        expected_lease_generation=1,
    )
    assert controller.mail_cycle_checkpoint()["phase"] == "to_mailbox"
    controller.pause("test pause")
    assert controller.mail_cycle_checkpoint()["phase"] == "blocked"
    with pytest.raises(RuntimeError, match="blocked mail cycle ACK"):
        controller.begin_mail_cycle(
            decision=decision,
            ack_loaded_uid="scan-1",
            status_last_uid="scan-1",
            wire_ack_uids=("scan-1",),
            queue_id=decision.queue_id,
            seq=1,
            house="beta-normal-alliance",
            character="Arthur",
            snapshot=frame.snapshot,
            binding=MailLoopBinding(True, 1, decision.queue_id, 1, "beta-normal-alliance", "Arthur"),
            bounds=_bounds(),
            expected_generation=controller.status().generation,
        )
    assert capability.cycle_id


def test_fresh_owner_blocks_nonterminal_cycle_without_retry_authority(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "session.json")
    driver = _Driver()
    controller = Controller(journal, driver=driver, recover_on_restart=False, wall_clock=lambda: 1760000890)
    controller._state = ControllerState.WAIT_DUE
    controller._mode = SessionMode.REPEAT
    controller._generation = 1
    controller._lease_generation = 1
    controller._started_at = 1760000000
    controller.driver.guardian.armed = True
    controller.driver.guardian.generation = 1
    controller._last_uid = "scan-1"
    controller._evidence_meta = {"ackLoadedUID": "scan-1"}
    frame = _valid_frame()
    decision = admit_mail_cycle(
        frame.snapshot,
        MailLoopBinding(
            True, 1, frame.snapshot.value["executor"]["queueId"], 1, "beta-normal-alliance", "Arthur"
        ),
        _boundary(),
        _bounds(),
    )
    controller.begin_mail_cycle(
        decision=decision,
        ack_loaded_uid="scan-1",
        status_last_uid="scan-1",
        wire_ack_uids=("scan-1",),
        queue_id=decision.queue_id,
        seq=1,
        house="beta-normal-alliance",
        character="Arthur",
        snapshot=frame.snapshot,
        binding=MailLoopBinding(True, 1, decision.queue_id, 1, "beta-normal-alliance", "Arthur"),
        bounds=_bounds(),
        expected_generation=1,
        expected_lease_generation=1,
    )
    fresh = Controller(journal, driver=_Driver(), recover_on_restart=True)
    assert fresh.status().state is ControllerState.BLOCKED
    assert fresh.mail_cycle_capability() is None
    assert fresh.mail_cycle_checkpoint()["phase"] == "blocked"
    assert fresh.mail_cycle_ack_seen("scan-1") is True


def test_async_terminal_observation_releases_one_started_mail_without_a_second_click(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "session.json")
    controller = Controller(
        journal, driver=_Driver(), recover_on_restart=False, wall_clock=lambda: 1760000890
    )
    controller._state = ControllerState.WAIT_DUE
    controller._mode = SessionMode.REPEAT
    controller._generation = 1
    controller._lease_generation = 1
    controller._started_at = 1760000000
    controller.driver.guardian.armed = True
    controller.driver.guardian.generation = 1
    controller._last_uid = "scan-1"
    controller._evidence_meta = {"ackLoadedUID": "scan-1"}
    frame = _valid_frame()
    decision = admit_mail_cycle(
        frame.snapshot,
        MailLoopBinding(
            True, 1, frame.snapshot.value["executor"]["queueId"], 1, "beta-normal-alliance", "Arthur"
        ),
        _boundary(),
        _bounds(),
    )
    capability = controller.begin_mail_cycle(
        decision=decision,
        ack_loaded_uid="scan-1",
        status_last_uid="scan-1",
        wire_ack_uids=("scan-1",),
        queue_id=decision.queue_id,
        seq=1,
        house="beta-normal-alliance",
        character="Arthur",
        snapshot=frame.snapshot,
        binding=MailLoopBinding(True, 1, decision.queue_id, 1, "beta-normal-alliance", "Arthur"),
        bounds=_bounds(),
        expected_generation=1,
        expected_lease_generation=1,
    )
    started_frame, _ = _wire_fixture(started=True)
    pre_value = copy.deepcopy(frame.snapshot.value)
    pre_value["boot"] = started_frame.boot
    pre_frame = protocol.decode_frame(protocol.encode_frame(pre_value))
    pre_evidence = {
        "sha256": hashlib.sha256(pre_frame.raw_bytes).hexdigest(),
        "length": len(pre_frame.raw_bytes),
        "crc32": pre_frame.crc32,
        "rawFrameHex": pre_frame.raw_bytes.hex(),
    }
    controller.begin_executor_click(
        queue_id=decision.queue_id,
        seq=1,
        generation=1,
        lease_generation=1,
        cycle_id=capability.cycle_id,
        pre_crs={
            "boot": pre_frame.boot,
            "sequence": pre_frame.sequence,
            "crc32": pre_frame.crc32,
            "identity": "client",
        },
        pre_ordinal=0,
        arms={"published": False, "session": False},
        anchor=_test_anchor(),
        confirmation="",
        pre_executor=frame.snapshot.value["executor"],
        pre_evidence=pre_evidence,
    )
    started_executor = _started_executor_projection()
    controller.finalize_executor_click(
        attempt_id=controller.executor_click_checkpoint()["intent"]["attemptId"],
        result="started",
        post_crs={
            "boot": started_frame.boot,
            "sequence": started_frame.sequence,
            "crc32": started_frame.crc32,
            "identity": "client",
        },
        receipt=_test_receipt(),
        terminal_action=False,
        post_executor=started_executor,
        pre_evidence=pre_evidence,
        post_evidence=_pre_evidence(started=True),
    )
    controller.transition_mail_cycle("preparing", capability=capability)
    controller.transition_mail_cycle("mailbox_open", capability=capability)
    controller.transition_mail_cycle("awaiting_confirmation", capability=capability)
    controller.transition_mail_cycle("executing", capability=capability, last_executor_seq=1)
    partial_executor = copy.deepcopy(started_executor)
    partial_executor["workDone"] = 1
    controller.record_mail_cycle_progress(capability=capability, executor=partial_executor)
    assert controller.mail_cycle_checkpoint()["completedUnits"] == 1
    terminal = copy.deepcopy(started_frame.snapshot.value)
    terminal["sequence"] = started_frame.sequence + 1
    terminal["uptimeMs"] = started_frame.uptime_ms + 1000
    terminal["executor"].update(
        {
            "currentSeq": 0,
            "currentKind": "",
            "phase": "complete",
            "inFlight": False,
            "clickReady": False,
            "workDone": 0,
            "workTotal": 0,
            "blocked": False,
            "latched": False,
            "lastResult": {"seq": 1, "kind": "mail_collect", "status": "succeeded"},
        }
    )
    terminal_frame = protocol.decode_frame(protocol.encode_frame(terminal))
    post_crs = {
        "boot": started_frame.boot,
        "sequence": terminal_frame.sequence,
        "crc32": terminal_frame.crc32,
        "identity": "client",
    }
    controller.record_mail_cycle_progress(
        capability=capability,
        executor=terminal_frame.snapshot.value["executor"],
    )
    record = controller.observe_mail_cycle_completion(
        capability=capability,
        post_crs=post_crs,
        post_executor=terminal_frame.snapshot.value["executor"],
        post_evidence={
            "sha256": hashlib.sha256(terminal_frame.raw_bytes).hexdigest(),
            "length": len(terminal_frame.raw_bytes),
            "crc32": terminal_frame.crc32,
            "rawFrameHex": terminal_frame.raw_bytes.hex(),
        },
    )
    assert record["kind"] == "terminal_observation"
    assert controller.mail_cycle_checkpoint()["phase"] == "to_auctioneer"
    assert controller.executor_click_checkpoint() is None


def test_standalone_async_terminal_observation_releases_private_continuation(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "session.json")
    controller = Controller(journal, driver=_Driver(), recover_on_restart=False)
    controller._state = ControllerState.READY
    controller._mode = SessionMode.INTERACTION
    controller._generation = 7
    controller._lease_generation = 3
    controller.driver.guardian.armed = True
    controller.driver.guardian.generation = 3
    started_frame, _ = _wire_fixture(started=True)
    initial = _valid_frame()
    initial_value = copy.deepcopy(initial.snapshot.value)
    initial_value["boot"] = started_frame.boot
    initial = protocol.decode_frame(protocol.encode_frame(initial_value))
    pre_evidence = {
        "sha256": hashlib.sha256(initial.raw_bytes).hexdigest(),
        "length": len(initial.raw_bytes),
        "crc32": initial.crc32,
        "rawFrameHex": initial.raw_bytes.hex(),
    }
    controller.begin_executor_click(
        queue_id=initial.snapshot.value["executor"]["queueId"],
        seq=1,
        generation=7,
        lease_generation=3,
        cycle_id="",
        pre_crs={
            "boot": initial.boot,
            "sequence": initial.sequence,
            "crc32": initial.crc32,
            "identity": "client",
        },
        pre_ordinal=0,
        arms={"published": False, "session": False},
        anchor=_test_anchor(),
        confirmation="",
        pre_executor=initial.snapshot.value["executor"],
        pre_evidence=pre_evidence,
    )
    controller.finalize_executor_click(
        attempt_id=controller.executor_click_checkpoint()["intent"]["attemptId"],
        result="started",
        post_crs={
            "boot": started_frame.boot,
            "sequence": started_frame.sequence,
            "crc32": started_frame.crc32,
            "identity": "client",
        },
        receipt={**_test_receipt(), "generation": 3},
        terminal_action=False,
        post_executor=_started_executor_projection(),
        pre_evidence=pre_evidence,
        post_evidence=_pre_evidence(started=True),
    )
    continuation = controller.executor_continuation_capability()
    assert isinstance(continuation, str)
    terminal = copy.deepcopy(started_frame.snapshot.value)
    terminal["sequence"] = started_frame.sequence + 1
    terminal["uptimeMs"] = started_frame.uptime_ms + 1000
    terminal["executor"].update(
        {
            "currentSeq": 0,
            "currentKind": "",
            "phase": "complete",
            "inFlight": False,
            "clickReady": False,
            "workDone": 0,
            "workTotal": 0,
            "blocked": False,
            "latched": False,
            "lastResult": {"seq": 1, "kind": "mail_collect", "status": "succeeded"},
        }
    )
    terminal_frame = protocol.decode_frame(protocol.encode_frame(terminal))
    post_crs = {
        "boot": started_frame.boot,
        "sequence": terminal_frame.sequence,
        "crc32": terminal_frame.crc32,
        "identity": "client",
    }
    record = controller.observe_executor_completion(
        continuation_capability=continuation,
        post_crs=post_crs,
        post_executor=terminal_frame.snapshot.value["executor"],
        post_evidence={
            "sha256": hashlib.sha256(terminal_frame.raw_bytes).hexdigest(),
            "length": len(terminal_frame.raw_bytes),
            "crc32": terminal_frame.crc32,
            "rawFrameHex": terminal_frame.raw_bytes.hex(),
        },
    )
    assert record["kind"] == "terminal_observation"
    assert controller.executor_click_checkpoint() is None


def test_mail_admission_requires_snapshot_and_rechecks_exact_policy_inputs(tmp_path: Path) -> None:
    controller, frame, decision = _seed_mail_controller(tmp_path)
    with pytest.raises(RuntimeError, match="validated protocol Snapshot"):
        controller.begin_mail_cycle(
            decision=decision,
            ack_loaded_uid="scan-1",
            status_last_uid="scan-1",
            wire_ack_uids=("scan-1",),
            queue_id=decision.queue_id,
            seq=1,
            house="beta-normal-alliance",
            character="Arthur",
            snapshot=None,  # type: ignore[arg-type]
            binding=MailLoopBinding(True, 1, decision.queue_id, 1, "beta-normal-alliance", "Arthur"),
            bounds=_bounds(),
            expected_generation=1,
            expected_lease_generation=1,
        )
    controller._last_uid = "different-current-uid"
    with pytest.raises(RuntimeError, match="controller-owned current evidence"):
        _begin_seeded_cycle(controller, frame, decision)
    assert controller.mail_cycle_capability() is None
    assert controller.mail_cycle_checkpoint()["phase"] == "none"


@pytest.mark.parametrize("replace_before_raise", [False, True])
def test_mail_admission_checkpoint_failure_fences_and_archives_before_next_tick(
    tmp_path: Path, replace_before_raise: bool
) -> None:
    controller, frame, decision = _seed_mail_controller(tmp_path)
    original_write = controller.journal.write
    failed = True

    def fail_once(value: dict) -> None:
        nonlocal failed
        if failed:
            failed = False
            if replace_before_raise:
                original_write(value)
            raise RuntimeError("admission checkpoint write failed")
        original_write(value)

    controller.journal.write = fail_once  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="admission checkpoint"):
        _begin_seeded_cycle(controller, frame, decision)
    assert controller.mail_cycle_capability() is None
    assert controller.status().state is ControllerState.BLOCKED
    assert controller.mail_cycle_checkpoint()["phase"] == "blocked"
    assert controller.mail_cycle_ack_seen("scan-1") is True

    fresh = Controller(controller.journal, driver=_Driver(), recover_on_restart=True)
    assert fresh.mail_cycle_capability() is None
    assert fresh.mail_cycle_checkpoint()["phase"] == "blocked"
    assert fresh.mail_cycle_ack_seen("scan-1") is True


def test_mail_phase_graph_rejects_skip_and_completion_bypass(tmp_path: Path) -> None:
    controller, frame, decision = _seed_mail_controller(tmp_path)
    capability = _begin_seeded_cycle(controller, frame, decision)
    with pytest.raises(RuntimeError, match="cannot transition"):
        controller.transition_mail_cycle("mailbox_open", capability=capability)
    controller.transition_mail_cycle("preparing", capability=capability)
    controller.transition_mail_cycle("mailbox_open", capability=capability)
    controller.transition_mail_cycle("awaiting_confirmation", capability=capability)
    controller.transition_mail_cycle("executing", capability=capability)
    with pytest.raises(RuntimeError, match="ready for completion"):
        controller.complete_mail_cycle(
            capability=capability,
            ah_open_proof={
                "fresh": True,
                "ahOpen": True,
                "mailOpen": False,
                "identity": "client",
                "generation": 1,
                "leaseGeneration": 1,
            },
        )


def test_mail_terminal_return_requires_durable_executor_proof(tmp_path: Path) -> None:
    controller, frame, decision = _seed_mail_controller(tmp_path)
    capability = _begin_seeded_cycle(controller, frame, decision)
    for phase in ("preparing", "mailbox_open", "awaiting_confirmation"):
        controller.transition_mail_cycle(phase, capability=capability)
    before = controller.mail_cycle_checkpoint()
    with pytest.raises(RuntimeError, match="cannot transition"):
        controller.transition_mail_cycle("to_auctioneer", capability=capability)
    with pytest.raises(RuntimeError, match="not durably archived"):
        controller.accept_mail_terminal(capability=capability, outcome_id="forged-terminal")
    assert controller.mail_cycle_checkpoint() == before


@pytest.mark.parametrize("mutation", ["boot", "sequence", "identity", "queue", "house", "character"])
def test_terminal_raw_causal_mutation_cannot_mint_return_authority(tmp_path: Path, mutation: str) -> None:
    """Each validly encoded foreign/stale post frame leaves the owner intact."""

    controller, frame, decision = _seed_mail_controller(tmp_path)
    capability = _begin_seeded_cycle(controller, frame, decision)
    for phase in ("preparing", "mailbox_open", "awaiting_confirmation"):
        controller.transition_mail_cycle(phase, capability=capability)

    started_frame, _ = _wire_fixture(started=True)
    pre_value = copy.deepcopy(frame.snapshot.value)
    pre_value["boot"] = started_frame.boot
    pre_frame = protocol.decode_frame(protocol.encode_frame(pre_value))
    pre_executor = copy.deepcopy(pre_frame.snapshot.value["executor"])
    pre_evidence = {
        "sha256": hashlib.sha256(pre_frame.raw_bytes).hexdigest(),
        "length": len(pre_frame.raw_bytes),
        "crc32": pre_frame.crc32,
        "rawFrameHex": pre_frame.raw_bytes.hex(),
    }
    controller.begin_executor_click(
        queue_id=decision.queue_id,
        seq=1,
        generation=1,
        lease_generation=1,
        cycle_id=capability.cycle_id,
        pre_crs={
            "boot": pre_frame.boot,
            "sequence": pre_frame.sequence,
            "crc32": pre_frame.crc32,
            "identity": "client",
        },
        pre_ordinal=pre_executor["clickOrdinal"],
        arms={"published": False, "session": False},
        anchor=_test_anchor(),
        confirmation="",
        pre_executor=pre_executor,
        pre_evidence=pre_evidence,
    )

    terminal_value = copy.deepcopy(started_frame.snapshot.value)
    terminal_value["boot"] = pre_frame.boot
    terminal_value["sequence"] = started_frame.sequence + 1
    terminal_value["uptimeMs"] = started_frame.uptime_ms + 1000
    terminal_value["executor"].update(
        {
            "currentSeq": 0,
            "currentKind": "",
            "phase": "complete",
            "inFlight": False,
            "clickReady": False,
            "workDone": 0,
            "workTotal": 0,
            "blocked": False,
            "latched": False,
            "lastResult": {"seq": 1, "kind": "mail_collect", "status": "succeeded"},
        }
    )
    if mutation == "boot":
        terminal_value["boot"] = "foreign-boot"
    elif mutation == "sequence":
        terminal_value["sequence"] = pre_frame.sequence
    elif mutation == "queue":
        terminal_value["executor"]["queueId"] = "foreign-house-1760000000-executor"
    elif mutation == "house":
        terminal_value["executor"]["house"] = "beta-normal-horde"
    elif mutation == "character":
        terminal_value["executor"]["character"] = "Other"
    terminal_frame = protocol.decode_frame(protocol.encode_frame(terminal_value))
    post_crs = {
        "boot": terminal_frame.boot,
        "sequence": terminal_frame.sequence,
        "crc32": terminal_frame.crc32,
        "identity": "foreign" if mutation == "identity" else "client",
    }
    post_executor = terminal_frame.snapshot.value["executor"]
    post_evidence = {
        "sha256": hashlib.sha256(terminal_frame.raw_bytes).hexdigest(),
        "length": len(terminal_frame.raw_bytes),
        "crc32": terminal_frame.crc32,
        "rawFrameHex": terminal_frame.raw_bytes.hex(),
    }
    before_cycle = controller.mail_cycle_checkpoint()
    before_checkpoint = controller.executor_click_checkpoint()
    before_journal = controller.journal.read()
    with pytest.raises(ValueError, match="causally bound"):
        controller.finalize_executor_click(
            attempt_id=controller.executor_click_checkpoint()["intent"]["attemptId"],
            result="succeeded",
            post_crs=post_crs,
            receipt=_test_receipt(),
            terminal_action=True,
            post_executor=post_executor,
            pre_evidence=pre_evidence,
            post_evidence=post_evidence,
        )
    assert controller.mail_cycle_checkpoint() == before_cycle
    assert controller.executor_click_checkpoint() == before_checkpoint
    assert controller.journal.read() == before_journal
    assert controller.mail_cycle_capability() is capability


@pytest.mark.parametrize("mutation", ["boot", "sequence", "identity", "queue", "house", "character"])
def test_durable_terminal_post_mutation_cannot_mint_return_authority(tmp_path: Path, mutation: str) -> None:
    """The archive-backed acceptance gate rechecks each valid post witness."""

    controller, frame, decision = _seed_mail_controller(tmp_path)
    capability = _begin_seeded_cycle(controller, frame, decision)
    original_accept = controller.accept_mail_terminal
    controller.accept_mail_terminal = lambda **_: controller.journal.archives("executor")[-1]  # type: ignore[method-assign]
    try:
        observed = _accept_seeded_terminal(controller, frame, decision, capability)
    finally:
        controller.accept_mail_terminal = original_accept  # type: ignore[method-assign]

    artifact = next(
        path
        for path in (controller.journal.archive_path / "executor").glob("*.json")
        if json.loads(path.read_text(encoding="utf-8")).get("outcomeId") == observed["outcomeId"]
    )
    record = json.loads(artifact.read_text(encoding="utf-8"))
    post_evidence = record["postEvidence"]
    if mutation == "identity":
        record["postCrs"]["identity"] = "foreign"
    else:
        changed = copy.deepcopy(
            protocol.decode_frame(bytes.fromhex(post_evidence["rawFrameHex"])).snapshot.value
        )
        if mutation == "boot":
            changed["boot"] = "foreign-terminal-boot"
        elif mutation == "sequence":
            changed["sequence"] = record["preCrs"]["sequence"]
        elif mutation == "queue":
            changed["executor"]["queueId"] = "foreign-house-1760000000-executor"
        elif mutation == "house":
            changed["executor"]["house"] = "beta-normal-horde"
        elif mutation == "character":
            changed["executor"]["character"] = "Other"
        changed_raw = protocol.encode_frame(changed)
        changed_frame = protocol.decode_frame(changed_raw)
        record["postExecutor"] = copy.deepcopy(changed_frame.snapshot.value["executor"])
        record["postCrs"].update(
            {
                "boot": changed_frame.boot,
                "sequence": changed_frame.sequence,
                "crc32": changed_frame.crc32,
            }
        )
        post_evidence.update(
            {
                "sha256": hashlib.sha256(changed_raw).hexdigest(),
                "length": len(changed_raw),
                "crc32": changed_frame.crc32,
                "rawFrameHex": changed_raw.hex(),
            }
        )
    artifact.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

    before_cycle = controller.mail_cycle_checkpoint()
    before_checkpoint = controller.executor_click_checkpoint()
    before_authority = controller._mail_cycle_terminal_authority
    before_journal = controller.journal.read()
    with pytest.raises(RuntimeError, match="causal|raw|identity|successor"):
        original_accept(capability=capability, outcome_id=observed["outcomeId"])
    assert controller.mail_cycle_checkpoint() == before_cycle
    assert controller.executor_click_checkpoint() == before_checkpoint
    assert controller._mail_cycle_terminal_authority == before_authority
    assert controller.journal.read() == before_journal


def test_mail_terminal_proof_settles_upper_bound_without_inventing_inbox_count(
    tmp_path: Path,
) -> None:
    controller, frame, decision = _seed_mail_controller(tmp_path)
    capability = _begin_seeded_cycle(controller, frame, decision)
    record = _accept_seeded_terminal(controller, frame, decision, capability)
    assert record["result"] == "succeeded"
    cycle = controller.mail_cycle_checkpoint()
    assert cycle["phase"] == "to_auctioneer"
    assert cycle["terminalOutcomeId"] == record["outcomeId"]
    # The fixture terminal frame reports no collected inbox units; the
    # admitted maxMessages remains a bound, not fabricated progress.
    assert cycle["completedUnits"] == 0
    assert cycle["mailUnits"] == decision.mail_units


@pytest.mark.parametrize("mutation", ["raw", "sha256", "crc32", "projection"])
def test_mail_terminal_accept_revalidates_archived_pre_evidence(tmp_path: Path, mutation: str) -> None:
    """Archive acceptance must not trust mutable or foreign pre-frame evidence."""

    controller, frame, decision = _seed_mail_controller(tmp_path)
    capability = _begin_seeded_cycle(controller, frame, decision)
    original_accept = controller.accept_mail_terminal

    # Let the real observation path publish the terminal archive, but hold the
    # cycle at executing so the public acceptance gate is exercised separately.
    controller.accept_mail_terminal = lambda **_: controller.journal.archives("executor")[-1]  # type: ignore[method-assign]
    try:
        observed = _accept_seeded_terminal(controller, frame, decision, capability)
    finally:
        controller.accept_mail_terminal = original_accept  # type: ignore[method-assign]

    artifact = next(
        path
        for path in (controller.journal.archive_path / "executor").glob("*.json")
        if json.loads(path.read_text(encoding="utf-8")).get("outcomeId") == observed["outcomeId"]
    )
    record = json.loads(artifact.read_text(encoding="utf-8"))
    physical = next(
        item for item in controller.journal.archives("executor") if item.get("result") == "started"
    )
    assert record["archiveOrdinal"] == int(artifact.stem)
    assert record["commitSequence"] > physical["commitSequence"]
    assert "receipt" not in record
    assert record["physicalOutcomeId"] == physical["outcomeId"]
    evidence = record["preEvidence"]
    if mutation == "raw":
        evidence["rawFrameHex"] = ("00" if evidence["rawFrameHex"][:2] != "00" else "ff") + evidence[
            "rawFrameHex"
        ][2:]
    elif mutation == "sha256":
        evidence["sha256"] = "0" * 64
    elif mutation == "crc32":
        evidence["crc32"] = int(evidence["crc32"]) ^ 1
    else:
        raw = bytes.fromhex(evidence["rawFrameHex"])
        decoded = protocol.decode_frame(raw)
        changed = copy.deepcopy(decoded.snapshot.value)
        changed["executor"]["character"] = "Foreign"
        changed_raw = protocol.encode_frame(changed)
        evidence.update(
            {
                "rawFrameHex": changed_raw.hex(),
                "sha256": hashlib.sha256(changed_raw).hexdigest(),
                "length": len(changed_raw),
                "crc32": protocol.decode_frame(changed_raw).crc32,
            }
        )
    artifact.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

    before_cycle = controller.mail_cycle_checkpoint()
    before_checkpoint = controller.executor_click_checkpoint()
    before_journal = controller.journal.read()
    with pytest.raises(RuntimeError, match="pre evidence"):
        original_accept(capability=capability, outcome_id=observed["outcomeId"])
    assert controller.mail_cycle_checkpoint() == before_cycle
    assert controller.executor_click_checkpoint() == before_checkpoint
    assert controller.journal.read() == before_journal


def test_mail_admission_revoke_failure_still_archives_blocked_ack(tmp_path: Path) -> None:
    controller, frame, decision = _seed_mail_controller(tmp_path)
    original_write = controller.journal.write
    failed = True

    def fail_admission_write(value: dict) -> None:
        nonlocal failed
        if failed:
            failed = False
            raise RuntimeError("admission checkpoint write failed")
        original_write(value)

    controller.journal.write = fail_admission_write  # type: ignore[method-assign]

    def revoke_then_fail(_reason: str) -> int:
        controller.driver.guardian.generation += 1
        raise RuntimeError("guardian revoke failed")

    controller.driver.revoke = revoke_then_fail  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="guardian revoke failed"):
        _begin_seeded_cycle(controller, frame, decision)
    assert controller.status().state is ControllerState.BLOCKED
    assert controller.mail_cycle_checkpoint()["phase"] == "blocked"
    assert controller.mail_cycle_ack_seen("scan-1") is True
    with pytest.raises(RuntimeError, match="restart/recovery fence"):
        controller.resume()


def test_closeout_refuses_live_mail_owner_without_mutation_then_pause_remains_usable(
    tmp_path: Path,
) -> None:
    controller, frame, decision = _seed_mail_controller(tmp_path)
    capability = _begin_seeded_cycle(controller, frame, decision)
    before = controller.status()
    with pytest.raises(RuntimeError, match="mail cycle owns interaction"):
        controller.closeout()
    after = controller.status()
    assert after.generation == before.generation
    assert after.closeout_requested is False
    assert controller.mail_cycle_capability() is capability
    controller.pause("operator pause")
    assert controller.mail_cycle_capability() is None
    assert controller.mail_cycle_checkpoint()["phase"] == "blocked"
    assert controller.mail_cycle_ack_seen("scan-1") is True


def test_mail_cycle_persists_immutable_budget_and_causal_progress(tmp_path: Path) -> None:
    controller, frame, decision = _seed_mail_controller(tmp_path)
    capability = _begin_seeded_cycle(controller, frame, decision)
    cycle = controller.mail_cycle_checkpoint()
    assert cycle["budget"]["mailUnits"] == decision.mail_units
    assert cycle["budget"]["totalSeconds"] == decision.budget.total_seconds
    controller.transition_mail_cycle("preparing", capability=capability)
    controller.transition_mail_cycle("mailbox_open", capability=capability)
    controller.transition_mail_cycle("awaiting_confirmation", capability=capability)
    started = copy.deepcopy(_wire_fixture(started=True)[0].snapshot.value["executor"])
    controller.transition_mail_cycle("executing", capability=capability, last_executor_seq=1)
    controller.record_mail_cycle_progress(capability=capability, executor=started)
    assert controller.mail_cycle_checkpoint()["completedUnits"] == 0
    started["workDone"] = 1
    controller.record_mail_cycle_progress(capability=capability, executor=started)
    assert controller.mail_cycle_checkpoint()["completedUnits"] == 1


def test_blocked_mail_outcome_is_archived_and_replayed_after_publication_failure(
    tmp_path: Path,
) -> None:
    controller, frame, decision = _seed_mail_controller(tmp_path)
    capability = _begin_seeded_cycle(controller, frame, decision)
    original_append = controller.journal.append_archive_bundle

    def fail_archive(*_args: object, **_kwargs: object) -> dict:
        raise RuntimeError("mail archive publication failed")

    controller.journal.append_archive_bundle = fail_archive  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="mail archive publication failed"):
        controller.block_mail_cycle("executor outcome failed", capability=capability)
    assert controller.mail_cycle_capability() is None
    staged = controller.journal.read()["current"]["mailCycleStage"]
    assert staged["archive"]["result"] == "blocked"
    controller.journal.append_archive_bundle = original_append  # type: ignore[method-assign]
    fresh = Controller(controller.journal, driver=_Driver(), recover_on_restart=True)
    assert fresh.mail_cycle_checkpoint()["phase"] == "blocked"
    assert fresh.mail_cycle_ack_seen("scan-1") is True
    assert fresh.journal.read()["current"]["mailCycleStage"] is None


def test_complete_mail_outcome_is_staged_before_archive_failure(tmp_path: Path) -> None:
    controller, frame, decision = _seed_mail_controller(tmp_path)
    capability = _begin_seeded_cycle(controller, frame, decision)
    _accept_seeded_terminal(controller, frame, decision, capability)
    controller.transition_mail_cycle("opening_ah", capability=capability)
    original_append = controller.journal.append_archive_bundle

    def fail_archive(*_args: object, **_kwargs: object) -> dict:
        raise RuntimeError("complete archive publication failed")

    controller.journal.append_archive_bundle = fail_archive  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="complete archive publication failed"):
        controller.complete_mail_cycle(
            capability=capability,
            ah_open_proof={
                "fresh": True,
                "ahOpen": True,
                "mailOpen": False,
                "identity": "client",
                "generation": 1,
                "leaseGeneration": 1,
            },
        )
    assert controller.mail_cycle_capability() is None
    staged = controller.journal.read()["current"]["mailCycleStage"]
    assert staged["archive"]["result"] == "complete"
    assert staged["checkpoint"]["current"]["mailCycle"]["phase"] == "complete"
    controller.journal.append_archive_bundle = original_append  # type: ignore[method-assign]
    fresh = Controller(controller.journal, driver=_Driver(), recover_on_restart=True)
    assert fresh.mail_cycle_ack_seen("scan-1") is True
    assert fresh.journal.read()["current"]["mailCycleStage"] is None


@pytest.mark.parametrize("boundary", ["pending", "manifest", "artifact", "checkpoint"])
def test_complete_mail_outcome_replays_after_each_real_journal_boundary(
    tmp_path: Path, boundary: str
) -> None:
    class BoundaryJournal(Journal):
        def __init__(self, path: Path) -> None:
            super().__init__(path)
            self.boundary = ""
            self.in_bundle = False

        def append_archive_bundle(self, records: dict, *, checkpoint: dict | None = None) -> dict:
            self.in_bundle = True
            try:
                return super().append_archive_bundle(records, checkpoint=checkpoint)
            finally:
                self.in_bundle = False

        def _fail(self, name: str) -> None:
            if self.in_bundle and self.boundary == name:
                self.boundary = ""
                raise RuntimeError(f"injected {name} boundary failure")

        def _write_pending_artifact(self, destination, value, directory):  # type: ignore[no-untyped-def]
            self._fail("pending")
            return super()._write_pending_artifact(destination, value, directory)

        def _write_json_artifact(self, destination, value, directory):  # type: ignore[no-untyped-def]
            self._fail("manifest")
            return super()._write_json_artifact(destination, value, directory)

        def _write_archive_artifact(self, kind, ordinal, record):  # type: ignore[no-untyped-def]
            self._fail("artifact")
            return super()._write_archive_artifact(kind, ordinal, record)

        def write(self, value: dict) -> None:
            self._fail("checkpoint")
            return super().write(value)

    journal = BoundaryJournal(tmp_path / "session.json")
    controller, frame, decision = _seed_mail_controller(tmp_path, journal=journal)
    capability = _begin_seeded_cycle(controller, frame, decision)
    _accept_seeded_terminal(controller, frame, decision, capability)
    controller.transition_mail_cycle("opening_ah", capability=capability)
    journal.boundary = boundary
    with pytest.raises(RuntimeError, match=f"injected {boundary}"):
        controller.complete_mail_cycle(
            capability=capability,
            ah_open_proof={
                "fresh": True,
                "ahOpen": True,
                "mailOpen": False,
                "identity": "client",
                "generation": 1,
                "leaseGeneration": 1,
            },
        )
    fresh = Controller(journal, driver=_Driver(), recover_on_restart=True)
    assert fresh.mail_cycle_ack_seen("scan-1") is True
    assert fresh.journal.read()["current"]["mailCycleStage"] is None
