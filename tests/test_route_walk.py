import json
import math
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

import crowley.session.route_walk as route_walk
from crowley.session.route_walk import (
    MIN_HUMAN_HOLD_SECONDS,
    KeyEvent,
    Kinematics,
    Pose,
    Route,
    RouteFile,
    Style,
    build_route_file,
    plan_walk,
    simulate,
)


def _style() -> Style:
    return Style(
        (0.35, 0.45, 0.55),
        (0.15, 0.25, 0.35),
        (0.08, 0.1, 0.12),
        (0.08, 0.1, 0.12),
        (0.08, 0.1, 0.12),
        (0.7, 0.9, 1.1),
        (0.4, 0.5, 0.6),
    )


def _route() -> Route:
    start = Pose(0, 0, 0.6)
    end = Pose(12, 0, 2.4)
    return Route(
        "test_to_mailbox",
        1,
        0,
        start,
        end,
        (
            (0.0, 0.0),
            (1.0, 0.7),
            (2.2, 1.5),
            (3.8, 2.1),
            (5.6, 2.3),
            (7.4, 2.0),
            (9.0, 1.2),
            (10.5, 0.5),
            (12.0, 0.0),
        ),
        "Mailbox",
    )


def _write_recording(
    path: Path,
    *,
    rounds: int = 2,
    contradict: bool = False,
    same_sign: bool = False,
    short_strafe: bool = False,
) -> None:
    start = (0.0, 0.0)
    end = (10.0, 0.0)
    path.mkdir()
    rows: list[dict[str, object]] = []
    inputs: list[dict[str, object]] = []
    mono = 0.0
    path_points = [(0.0, 0.0), (2.0, 2.0), (5.0, 2.0), (8.0, 0.0), (10.0, 0.0)]
    start_facing = math.atan2(2.0, 2.0) - 0.4
    end_facing = math.pi + 0.4
    current = start
    current_facing = start_facing

    def row(x: float, y: float, facing: float, speed: float) -> None:
        rows.append(
            {
                "mono": mono,
                "x": x,
                "y": y,
                "z": 0,
                "instance": 0,
                "facing": facing,
                "speed": speed,
                "ground": "grounded",
                "falling": "false",
            }
        )

    def key(when: float, name: str, down: bool) -> None:
        inputs.append({"mono": when, "kind": "key", "key": name, "down": down})

    def click(when: float) -> None:
        inputs.append({"mono": when, "kind": "button", "button": 1, "down": True})
        inputs.append({"mono": when + 0.1, "kind": "button", "button": 1, "down": False})

    def turn(name: str, rate: float) -> None:
        nonlocal mono, current_facing
        before = current_facing
        key(mono + 0.1, name, True)
        key(mono + 0.3, name, False)
        current_facing = before + rate * 0.2
        mono += 0.5
        row(current[0], current[1], current_facing, 0)

    row(*start, start_facing, 0)
    click(0.2)
    mono = 0.6
    row(*start, start_facing, 0)
    click(0.8)
    mono = 1.2
    row(*start, start_facing, 0)

    for leg in range(rounds * 2):
        forward = leg % 2 == 0
        target_points = path_points if forward else list(reversed(path_points))
        endpoint_rate = 2.0 if forward else -2.0
        if same_sign and not forward:
            endpoint_rate = 2.0
        if leg == 0:
            # Three taps each direction are present across the otherwise idle
            # stationary departure.  Their net effect leaves the route heading.
            turn("Right", 2.0)
            turn("Left", 2.0 if same_sign else -2.0)
            turn("Right", 2.0)
        else:
            turn("Right" if forward else "Left", endpoint_rate)
        for index, (x, y) in enumerate(target_points[1:], 1):
            previous = target_points[index - 1]
            direction = math.atan2(y - previous[1], x - previous[0])
            start_time = mono
            key(start_time + 0.05, "W", True)
            key(start_time + 0.35, "W", False)
            if index <= 4:
                key(start_time + 0.1, "space", True)
                key(start_time + 0.18, "space", False)
            mono += 0.5
            movement_facing = math.pi + direction if contradict else direction
            row(x, y, movement_facing, 7)
        current = end if forward else start
        current_facing = end_facing if forward else start_facing
        mono += 0.1
        row(current[0], current[1], current_facing, 0)
        click(mono + 0.1)
        mono += 0.4
        row(current[0], current[1], current_facing, 0)
        click(mono + 0.1)
        mono += 0.5
        row(current[0], current[1], current_facing, 0)

    for index, name in enumerate(("A", "D", "A", "D")):
        key(mono + index * 0.25 + 0.01, name, True)
        key(mono + index * 0.25 + 0.06, name, False)
    if short_strafe:
        key(mono + 1.2, "A", True)
        key(mono + 1.21, "A", False)
    rows.sort(key=lambda value: float(value["mono"]))
    inputs.sort(key=lambda value: float(value["mono"]))
    (path / "telemetry.jsonl").write_text("".join(json.dumps(value) + "\n" for value in rows))
    (path / "input-xi2.jsonl").write_text("".join(json.dumps(value) + "\n" for value in inputs))


def test_types_and_json_strictness() -> None:
    assert Pose(1, 2, 2 * math.pi).facing == 0
    with pytest.raises(ValueError):
        Style(
            (0.1, 0.2),
            (0.1, 0.2, 0.3),
            (0.1, 0.2, 0.3),
            (0.1, 0.2, 0.3),
            (0.1, 0.2, 0.3),
            (0.1, 0.2, 0.3),
            (0.1, 0.2, 0.3),
        )
    route_file = RouteFile(
        {_route().name: _route()},
        _style(),
        Kinematics(7, -2, 2, 0.6),
        ("synthetic",),
    )
    assert RouteFile.from_json(route_file.to_json()) == route_file
    value = route_file.to_dict()
    value["unexpected"] = True
    with pytest.raises(ValueError, match="unknown"):
        RouteFile.from_dict(value)
    for bad_format in (True, 1.0):
        value = route_file.to_dict()
        value["format"] = bad_format
        with pytest.raises(ValueError, match="format"):
            RouteFile.from_dict(value)
    value = route_file.to_dict()
    value["sources"] = "synthetic"
    with pytest.raises(ValueError, match="sources"):
        RouteFile.from_dict(value)
    value = route_file.to_dict()
    value["style"]["click_hold"] = [0.1, 0.2, 0.3]
    with pytest.raises(ValueError, match="unknown"):
        RouteFile.from_dict(value)


def test_simulation_and_planner_are_deterministic() -> None:
    route = _route()
    style = _style()
    kinematics = Kinematics(7, -2, 2, 0.6)
    first = plan_walk(route, route.start, style, kinematics, 7)
    second = plan_walk(route, route.start, style, kinematics, 7)
    other = plan_walk(route, route.start, style, kinematics, 8)
    assert first == second
    assert first.events != other.events
    assert math.dist((first.final.x, first.final.y), (route.end.x, route.end.y)) <= 0.5
    assert abs((first.final.facing - route.end.facing + math.pi) % (2 * math.pi) - math.pi) <= 0.15
    states = simulate(first.events, route.start, kinematics)
    assert states[-1][1] == first.final
    active: set[str] = set()
    down_times: dict[str, float] = {}
    for event in first.events:
        if event.down:
            assert event.key not in active
            active.add(event.key)
            down_times[event.key] = event.t
        else:
            assert event.t - down_times[event.key] >= MIN_HUMAN_HOLD_SECONDS
            active.remove(event.key)
            del down_times[event.key]


def test_landing_turn_uses_post_landing_facing() -> None:
    kinematics = Kinematics(1, -1, 1, 0.5)
    events = (
        KeyEvent(0, "W", True),
        KeyEvent(0, "Left", True),
        KeyEvent(0, "space", True),
        KeyEvent(0.1, "space", False),
        KeyEvent(1, "Left", False),
        KeyEvent(1, "W", False),
    )
    final = simulate(events, Pose(0, 0, 0), kinematics)[-1][1]
    expected_x = 0.5 + (math.sin(-1.0) - math.sin(-0.5)) / -1.0
    expected_y = (-math.cos(-1.0) + math.cos(-0.5)) / -1.0
    assert final.x == pytest.approx(expected_x)
    assert final.y == pytest.approx(expected_y)
    assert final.y < -0.1
    assert any(math.isclose(time, 0.5) for time, _ in route_walk._trace(events, Pose(0, 0, 0), kinematics))


def test_corridor_validation_rejects_landing_boundary_excursion(monkeypatch: pytest.MonkeyPatch) -> None:
    route = Route(
        "corridor",
        1,
        0,
        Pose(0, 0, math.pi / 2),
        Pose(2, 0, 0),
        ((0, 0), (1, 0), (2, 0)),
        "end",
    )
    style = _style()
    kinematics = Kinematics(7, -7 * math.pi / 0.15, 7 * math.pi / 0.15, 0.15)
    events = (
        KeyEvent(0, "W", True),
        KeyEvent(0, "space", True),
        KeyEvent(0, "Left", True),
        KeyEvent(0.03, "space", False),
        KeyEvent(0.15, "Left", False),
        KeyEvent(0.2, "W", False),
    )

    # Independent oracle: airborne horizontal velocity is locked to the initial
    # upward heading, so the landing point is exactly 7 * .15 = 1.05 yards from
    # the x-axis. The following grounded slice returns to .70 yards by t=.20.
    true_max_distance = max(7 * 0.15, 7 * 0.15 - 7 * (0.2 - 0.15))
    round1_sample_distance = max(7 * 0.05, 7 * 0.10, 7 * 0.15 - 7 * (0.2 - 0.15))
    assert true_max_distance == pytest.approx(1.05)
    assert round1_sample_distance == pytest.approx(0.7)
    assert true_max_distance > 1.0 > round1_sample_distance

    monkeypatch.setattr(route_walk, "_make_attempt", lambda *args: (events, route.end))
    with pytest.raises(ValueError, match="corridor"):
        plan_walk(route, route.start, style, kinematics, 1)


def test_circular_mean_rejects_antipodal_headings() -> None:
    with pytest.raises(ValueError, match="undefined"):
        route_walk._circular_mean((0.0, math.pi))


def test_leg_segmentation_keeps_last_departure_and_one_frame_arrival() -> None:
    def fix(mono: float, x: float, speed: float) -> route_walk._Telemetry:
        return route_walk._Telemetry(mono, x, 0.0, 0.0, speed, "grounded", False, 0)

    rows = (
        fix(0, 0, 0),
        fix(1, 2, 7),
        fix(2, 0, 0),
        fix(3, 2, 7),
        fix(4, 5, 7),
        fix(5, 10, 0),
        fix(6, 8, 7),
        fix(7, 5, 7),
        fix(8, 0, 0),
    )
    recording = route_walk._Recording(Path("synthetic"), rows, ())
    forward, backward = route_walk._leg_spans(recording, (0, 0), (10, 0), 1)
    assert [row.mono for row in forward[0]] == [2, 3, 4, 5]
    assert [row.mono for row in backward[0]] == [5, 6, 7, 8]


@pytest.mark.parametrize(
    ("field", "value"),
    [("instance", 1.5), ("falling", False), ("ground", True)],
)
def test_recording_fields_require_exact_shapes(tmp_path: Path, field: str, value: object) -> None:
    path = tmp_path / field
    path.mkdir()
    rows = [
        {
            "mono": 0.0,
            "x": 0.0,
            "y": 0.0,
            "instance": 0,
            "facing": 0.0,
            "speed": 0.0,
            "ground": "grounded",
            "falling": "false",
        },
        {
            "mono": 1.0,
            "x": 0.0,
            "y": 0.0,
            "instance": 0,
            "facing": 0.0,
            "speed": 0.0,
            "ground": "grounded",
            "falling": "false",
        },
    ]
    rows[0][field] = value
    (path / "telemetry.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(ValueError, match="invalid telemetry"):
        route_walk._load_recording(path)


def test_input_boolean_fields_require_exact_shapes(tmp_path: Path) -> None:
    path = tmp_path / "input"
    path.mkdir()
    row = {
        "mono": 0.0,
        "x": 0.0,
        "y": 0.0,
        "instance": 0,
        "facing": 0.0,
        "speed": 0.0,
        "ground": "grounded",
        "falling": "false",
    }
    (path / "telemetry.jsonl").write_text(json.dumps(row) + "\n" + json.dumps({**row, "mono": 1.0}) + "\n")
    (path / "input-xi2.jsonl").write_text(
        json.dumps({"mono": 0.1, "kind": "key", "key": "W", "down": "false"}) + "\n"
    )
    with pytest.raises(ValueError, match="invalid input"):
        route_walk._load_recording(path)


def test_short_style_samples_are_excluded_and_recorded(tmp_path: Path) -> None:
    recordings = []
    for index in range(2):
        recording = tmp_path / f"short-{index}"
        _write_recording(recording, short_strafe=index == 0)
        recordings.append(recording)
    route_file = build_route_file(
        recordings,
        start_xy=(0, 0),
        end_xy=(10, 0),
        radius=1,
        start_target="A",
        end_target="B",
    )
    for field in route_walk._STYLE_FIELDS:
        assert all(sample >= MIN_HUMAN_HOLD_SECONDS for sample in getattr(route_file.style, field))
    assert any("excluded 1 strafe_tap" in source for source in route_file.sources)
    assert "click_hold" not in route_file.style.to_dict()


def test_arrive_pause_has_no_telemetry_fallback(tmp_path: Path) -> None:
    paths = []
    for index in range(2):
        path = tmp_path / f"pause-{index}"
        _write_recording(path)
        paths.append(path)
    recordings = tuple(route_walk._load_recording(path) for path in paths)
    windows = {}
    for recording in recordings:
        forward, backward = route_walk._leg_spans(recording, (0, 0), (10, 0), 1)
        windows[recording.path] = [(leg[0].mono, leg[-1].mono) for leg in (*forward, *backward)]
    with pytest.raises(ValueError, match="arrive_pause"):
        route_walk._style_from_recordings(recordings, windows, ())


def test_three_second_arrival_pause_is_kept() -> None:
    telemetry = (
        route_walk._Telemetry(0, 0, 0, 0, 7, "grounded", False, 0),
        route_walk._Telemetry(1, 10, 0, 0, 7, "grounded", False, 0),
        route_walk._Telemetry(2, 10, 0, 0, 0, "grounded", False, 0),
        route_walk._Telemetry(4, 10, 0, 0, 0, "grounded", False, 0),
    )
    recording = route_walk._Recording(
        Path("pause-3s"),
        telemetry,
        (
            route_walk._Input(5, "button", down=True, button=1),
            route_walk._Input(5.1, "button", down=False, button=1),
        ),
    )
    assert route_walk._arrival_pause_samples((recording,), (0, 0), (10, 0), 1) == [3]


def test_jump_intervals_do_not_cross_recordings(tmp_path: Path) -> None:
    first_path = tmp_path / "first"
    second_path = tmp_path / "second"
    _write_recording(first_path)
    _write_recording(second_path)
    first = route_walk._load_recording(first_path)
    second_base = route_walk._load_recording(second_path)
    first_jumps = [
        event.mono for event in first.inputs if event.kind == "key" and event.key == "space" and event.down
    ]
    second_jumps = [
        event.mono
        for event in second_base.inputs
        if event.kind == "key" and event.key == "space" and event.down
    ]
    cross_interval = 0.123
    offset = max(first_jumps) + cross_interval - min(second_jumps)
    artificial_fix_time = max(first_jumps) + cross_interval / 2
    first = replace(
        first,
        telemetry=tuple(
            sorted(
                (
                    *first.telemetry,
                    route_walk._Telemetry(artificial_fix_time, 100, 100, 0, 7, "grounded", False, 0),
                ),
                key=lambda row: row.mono,
            )
        ),
    )
    second = replace(
        second_base,
        path=second_path,
        telemetry=tuple(replace(row, mono=row.mono + offset) for row in second_base.telemetry),
        inputs=tuple(replace(event, mono=event.mono + offset) for event in second_base.inputs),
    )
    recordings = (first, second)
    windows = {}
    for recording in recordings:
        forward, backward = route_walk._leg_spans(recording, (0, 0), (10, 0), 1)
        windows[recording.path] = [(leg[0].mono, leg[-1].mono) for leg in (*forward, *backward)]
    pauses = route_walk._arrival_pause_samples(recordings, (0, 0), (10, 0), 1)
    style, _ = route_walk._style_from_recordings(recordings, windows, pauses)
    assert all(abs(value - cross_interval) > 1e-6 for value in style.jump_interval)


def test_planner_stays_in_corridor_for_50_seeds() -> None:
    route = _route()
    style = _style()
    kinematics = Kinematics(7, -2, 2, 0.6)
    for seed in range(50):
        plan = plan_walk(route, route.start, style, kinematics, seed)
        trace = route_walk._trace(plan.events, route.start, kinematics)
        assert (
            max(route_walk._polyline_distance(pose.x, pose.y, route.waypoints) for _, pose in trace)
            + kinematics.run_speed * route_walk.TRACE_STEP_SECONDS
            <= 1.0
        )
        states = simulate(plan.events, route.start, kinematics)
        poses_by_time = {time: pose for time, pose in states}
        for event in plan.events:
            if event.key == "space" and event.down:
                pose = poses_by_time[event.t]
                assert math.dist((pose.x, pose.y), (route.end.x, route.end.y)) > 3.0


def test_builder_recovers_synthetic_recordings(tmp_path: Path) -> None:
    recordings = []
    for index in range(2):
        recording = tmp_path / f"recording-{index}"
        _write_recording(recording)
        recordings.append(recording)
    route_file = build_route_file(
        recordings,
        start_xy=(0, 0),
        end_xy=(10, 0),
        radius=1,
        start_target="Auctioneer",
        end_target="Mailbox",
    )
    route = route_file.routes["auctioneer_to_mailbox"]
    assert len(route.waypoints) >= 3
    assert route_file.kinematics.run_speed == pytest.approx(7)
    assert route_file.kinematics.turn_rate_left == pytest.approx(-2.0)
    assert route_file.kinematics.turn_rate_right == pytest.approx(2.0)
    assert route_file.kinematics.jump_airtime == pytest.approx(0.4)
    assert route.start.x == pytest.approx(0)
    assert route.start.y == pytest.approx(0)
    assert route.end.x == pytest.approx(10)
    assert route.end.y == pytest.approx(0)
    assert route.start.facing == pytest.approx(math.atan2(2.0, 2.0) - 0.4)
    assert route.end.facing == pytest.approx(math.pi + 0.4)
    assert max(y for _, y in route.waypoints) > 1.0
    reverse = route_file.routes["mailbox_to_auctioneer"]
    assert reverse.waypoints[1][0] > reverse.waypoints[-2][0]
    assert max(y for _, y in reverse.waypoints) > 1.0
    assert any("excluded" in source for source in route_file.sources)


def test_builder_rejects_bad_heading_and_insufficient_legs(tmp_path: Path) -> None:
    bad_heading = tmp_path / "bad-heading"
    _write_recording(bad_heading, contradict=True)
    with pytest.raises(ValueError, match="heading"):
        build_route_file(
            [bad_heading, bad_heading],
            start_xy=(0, 0),
            end_xy=(10, 0),
            radius=1,
            start_target="A",
            end_target="B",
        )
    one_round = tmp_path / "one-round"
    _write_recording(one_round, rounds=1)
    with pytest.raises(ValueError, match="legs"):
        build_route_file(
            [one_round],
            start_xy=(0, 0),
            end_xy=(10, 0),
            radius=1,
            start_target="A",
            end_target="B",
        )


def test_builder_rejects_same_sign_turns(tmp_path: Path) -> None:
    recording = tmp_path / "same-sign"
    _write_recording(recording, same_sign=True)
    with pytest.raises(ValueError, match="opposite signs"):
        build_route_file(
            [recording, recording],
            start_xy=(0, 0),
            end_xy=(10, 0),
            radius=1,
            start_target="A",
            end_target="B",
        )


def test_cli_refuses_to_overwrite(tmp_path: Path) -> None:
    recording = tmp_path / "recording"
    _write_recording(recording)
    output = tmp_path / "existing.json"
    output.write_text("keep me")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "crowley.session.route_walk",
            "build",
            "--recording",
            str(recording),
            "--start",
            "0,0",
            "--end",
            "10,0",
            "--radius",
            "1",
            "--start-target",
            "A",
            "--end-target",
            "B",
            "--out",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "refusing to overwrite" in result.stderr
    assert output.read_text() == "keep me"
