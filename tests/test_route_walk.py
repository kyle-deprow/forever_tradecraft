import json
import math
import random
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

import crowley.session.route_walk as route_walk
from crowley.session.route_walk import (
    KEYBOARD_TURN_RATE,
    KINEMATICS_PROVENANCE,
    MAX_KEY_HOLD_SECONDS,
    MIN_HUMAN_HOLD_SECONDS,
    RUN_SPEED,
    KeyEvent,
    Kinematics,
    Pose,
    Route,
    RouteFile,
    Segment,
    Style,
    build_route_file,
    check_fix,
    plan_open_loop_walk,
    plan_segment,
    simulate,
    walk_budget,
)


def _style() -> Style:
    return Style(
        (0.35, 0.45, 0.55),
        (0.15, 0.25, 0.35),
        (0.15, 0.25, 0.35),
        (0.08, 0.10, 0.12),
        (0.08, 0.10, 0.12),
        (0.08, 0.10, 0.12),
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


def _assert_no_same_key_zero_gap(events: tuple[KeyEvent, ...]) -> None:
    releases: dict[str, float] = {}
    for event in events:
        if event.down:
            if event.key in releases:
                assert event.t - releases[event.key] >= MIN_HUMAN_HOLD_SECONDS - 1e-9
        else:
            releases[event.key] = event.t


def _oracle_point_segment_distance(
    point: tuple[float, float], first: tuple[float, float], second: tuple[float, float]
) -> float:
    dx = second[0] - first[0]
    dy = second[1] - first[1]
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return math.dist(point, first)
    fraction = max(
        0.0,
        min(1.0, ((point[0] - first[0]) * dx + (point[1] - first[1]) * dy) / length_squared),
    )
    return math.dist(point, (first[0] + fraction * dx, first[1] + fraction * dy))


def _oracle_polyline_distance(
    point: tuple[float, float], waypoints: tuple[tuple[float, float], ...]
) -> float:
    return min(
        _oracle_point_segment_distance(point, first, second)
        for first, second in zip(waypoints, waypoints[1:], strict=False)
    )


def _oracle_chord_upper_bound(
    start: tuple[float, float], target: tuple[float, float], waypoints: tuple[tuple[float, float], ...]
) -> float:
    sample_count = 4096
    chord_length = math.dist(start, target)
    sample_max = max(
        _oracle_polyline_distance(
            (
                start[0] + index / sample_count * (target[0] - start[0]),
                start[1] + index / sample_count * (target[1] - start[1]),
            ),
            waypoints,
        )
        for index in range(sample_count + 1)
    )
    return sample_max + chord_length / (2 * sample_count)


def _oracle_nearest_progress(point: tuple[float, float], waypoints: tuple[tuple[float, float], ...]) -> float:
    progress = 0.0
    best_distance = math.inf
    best_progress = 0.0
    for first, second in zip(waypoints, waypoints[1:], strict=False):
        dx = second[0] - first[0]
        dy = second[1] - first[1]
        length = math.hypot(dx, dy)
        fraction = (
            0.0
            if length == 0
            else max(
                0.0,
                min(1.0, ((point[0] - first[0]) * dx + (point[1] - first[1]) * dy) / (length * length)),
            )
        )
        candidate = (first[0] + fraction * dx, first[1] + fraction * dy)
        distance = math.dist(point, candidate)
        candidate_progress = progress + fraction * length
        if distance < best_distance:
            best_distance = distance
            best_progress = candidate_progress
        progress += length
    return best_progress


def _independent_locked_heading_travel(
    events: tuple[KeyEvent, ...], kinematics: Kinematics, heading: float
) -> float:
    active: set[str] = set()
    airborne_until = 0.0
    airborne_speed = 0.0
    current = 0.0
    distance = 0.0
    for event in events:
        elapsed = event.t - current
        assert elapsed >= -1e-9
        airborne_time = min(elapsed, max(0.0, airborne_until - current))
        ground_time = elapsed - airborne_time
        moving_time = (airborne_time if airborne_speed > 0 else 0.0) + (ground_time if "W" in active else 0.0)
        distance += math.hypot(
            kinematics.run_speed * moving_time * math.cos(heading),
            kinematics.run_speed * moving_time * math.sin(heading),
        )
        current = event.t
        if event.down:
            assert event.key not in active
            active.add(event.key)
            if event.key == "space" and current >= airborne_until - 1e-9:
                airborne_until = current + kinematics.jump_airtime
                airborne_speed = kinematics.run_speed if "W" in active else 0.0
        else:
            assert event.key in active
            active.remove(event.key)
    if airborne_speed > 0 and airborne_until > current:
        distance += math.hypot(
            kinematics.run_speed * (airborne_until - current) * math.cos(heading),
            kinematics.run_speed * (airborne_until - current) * math.sin(heading),
        )
    return distance


def _independent_route_progress(
    point: tuple[float, float], waypoints: tuple[tuple[float, float], ...]
) -> float:
    progress = 0.0
    best_distance = math.inf
    best_progress = 0.0
    for first, second in zip(waypoints, waypoints[1:], strict=False):
        dx = second[0] - first[0]
        dy = second[1] - first[1]
        length = math.hypot(dx, dy)
        fraction = (
            0.0
            if length == 0
            else max(
                0.0, min(1.0, ((point[0] - first[0]) * dx + (point[1] - first[1]) * dy) / (length * length))
            )
        )
        candidate = (first[0] + fraction * dx, first[1] + fraction * dy)
        distance = math.dist(point, candidate)
        candidate_progress = progress + fraction * length
        if distance < best_distance - 1e-9 or (
            abs(distance - best_distance) <= 1e-9 and candidate_progress > best_progress + 1e-9
        ):
            best_distance = distance
            best_progress = candidate_progress
        progress += length
    return best_progress


def _independent_drive_segment(events: tuple[KeyEvent, ...], start: Pose, kinematics: Kinematics) -> Pose:
    active: set[str] = set()
    current = 0.0
    x, y, facing = start.x, start.y, start.facing
    for event in events:
        elapsed = event.t - current
        assert elapsed >= -1e-9
        turn_key = (
            "Left" if "Left" in active and "Right" not in active else "Right" if "Right" in active else None
        )
        if "W" in active:
            x += kinematics.run_speed * elapsed * math.cos(facing)
            y += kinematics.run_speed * elapsed * math.sin(facing)
        if turn_key is not None:
            rate = kinematics.turn_rate_left if turn_key == "Left" else kinematics.turn_rate_right
            facing += rate * elapsed
        current = event.t
        assert event.key != "space"
        if event.down:
            assert event.key not in active
            active.add(event.key)
        else:
            assert event.key in active
            active.remove(event.key)
    assert not active
    return Pose(x, y, facing)


def _oracle_target_index(route: Route, pose: Pose, max_distance: float) -> int:
    waypoints = route.waypoints
    arc = [0.0]
    for first, second in zip(waypoints, waypoints[1:], strict=False):
        arc.append(arc[-1] + math.dist(first, second))
    nearest = _oracle_nearest_progress((pose.x, pose.y), waypoints)
    first_index = next(index for index, value in enumerate(arc) if value >= nearest - 1e-9)
    eligible = [
        index
        for index in range(first_index, len(waypoints))
        if math.dist((pose.x, pose.y), waypoints[index]) <= max_distance + 1e-9
        and _oracle_chord_upper_bound((pose.x, pose.y), waypoints[index], waypoints) <= 0.75
    ]
    assert eligible
    return max(eligible)


def _write_recording(
    path: Path,
    *,
    rounds: int = 2,
    contradict: bool = False,
    short_strafe: bool = False,
    recorded_speed: float = 7.0,
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
        inputs.extend(
            (
                {"mono": when, "kind": "button", "button": 1, "down": True},
                {"mono": when + 0.1, "kind": "button", "button": 1, "down": False},
            )
        )

    def turn(name: str, rate: float) -> None:
        nonlocal mono
        key(mono + 0.1, name, True)
        key(mono + 0.3, name, False)
        mono += 0.5
        row(current[0], current[1], rate * 0.2, 0)

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
        turn("Right" if forward else "Left", 2.0)
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
            row(x, y, math.pi + direction if contradict else direction, recorded_speed)
        current = end if forward else start
        mono += 0.1
        row(current[0], current[1], end_facing if forward else start_facing, 0)
        click(mono + 0.1)
        mono += 0.4
        row(current[0], current[1], end_facing if forward else start_facing, 0)
        click(mono + 0.1)
        mono += 0.5
        row(current[0], current[1], end_facing if forward else start_facing, 0)
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


def test_constants_json_and_style_validation() -> None:
    assert KEYBOARD_TURN_RATE == pytest.approx(math.pi)
    assert RUN_SPEED == pytest.approx(7.0)
    assert KINEMATICS_PROVENANCE in Kinematics(7, math.pi, -math.pi, 0.6).provenance
    style = _style()
    assert "key_gap" in style.to_dict()
    route_file = RouteFile(
        {_route().name: _route()}, style, Kinematics(7, math.pi, -math.pi, 0.6), ("synthetic",)
    )
    assert RouteFile.from_json(route_file.to_json()) == route_file
    value = route_file.to_dict()
    value["kinematics"].pop("provenance")
    with pytest.raises(ValueError, match="missing"):
        RouteFile.from_dict(value)
    with pytest.raises(ValueError):
        Style(
            (0.1, 0.2),
            (0.1, 0.2, 0.3),
            (0.1, 0.2, 0.3),
            (0.1, 0.2, 0.3),
            (0.1, 0.2, 0.3),
            (0.1, 0.2, 0.3),
            (0.1, 0.2, 0.3),
            (0.1, 0.2, 0.3),
        )
    valid_samples = (0.1, 0.2, 0.3)
    with pytest.raises(TypeError):
        Style(
            valid_samples,
            valid_samples,
            valid_samples,
            valid_samples,
            valid_samples,
            valid_samples,
            valid_samples,
        )


def test_segment_target_is_forward_and_chord_is_in_corridor() -> None:
    route = _route()
    style = _style()
    kinematics = Kinematics(7, math.pi, -math.pi, 0.15)
    cases = (
        (route.start, 4.0),
        (Pose(2.2, 1.5, math.pi), 4.0),  # off-route and facing backwards
        (Pose(7.0, 1.9, math.pi), 3.0),  # nearest progress is later on the route
    )
    for seed, (pose, max_distance) in enumerate(cases):
        expected_index = _oracle_target_index(route, pose, max_distance)
        segment = plan_segment(route, pose, style, kinematics, seed, max_distance=max_distance)
        assert segment.seed == seed
        assert segment.target_index == expected_index
        assert math.dist((pose.x, pose.y), route.waypoints[segment.target_index]) <= max_distance + 1e-9
        assert (
            _oracle_chord_upper_bound(
                (pose.x, pose.y), route.waypoints[segment.target_index], route.waypoints
            )
            <= 0.75
        )

    boundary_route = Route(
        "boundary",
        1,
        0,
        Pose(0, 0, 0),
        Pose(4, 0, 0),
        ((0, 0), (0.75, 0.4070), (1.5, 0.8141), (2.75, 0.4070), (4, 0)),
        "end",
    )
    assert _oracle_chord_upper_bound((0, 0), (4, 0), boundary_route.waypoints) > 0.75
    boundary_segment = plan_segment(
        boundary_route, boundary_route.start, style, kinematics, 9, max_distance=4
    )
    assert boundary_segment.target_index == 3

    duplicate_route = Route(
        "duplicate",
        1,
        0,
        Pose(0, 0, 0),
        Pose(2, 0, 0),
        ((0, 0), (0, 0), (1, 0), (2, 0)),
        "end",
    )
    with pytest.raises(ValueError, match="zero-length"):
        plan_segment(duplicate_route, duplicate_route.start, style, kinematics, 10, max_distance=0.1)


def test_segment_target_does_not_skip_to_parallel_return_leg() -> None:
    route = Route(
        "u-turn",
        1,
        0,
        Pose(0, 0, 0),
        Pose(0, 1.5, math.pi),
        (
            (0, 0),
            (1.5, 0),
            (3, 0),
            (4.5, 0),
            (6, 0),
            (6, 1.5),
            (4.5, 1.5),
            (3, 1.5),
            (1.5, 1.5),
            (0, 1.5),
        ),
        "end",
    )
    pose = Pose(3, 0, 0)
    segment = plan_segment(route, pose, _style(), Kinematics(7, math.pi, -math.pi, 0.15), 11)
    assert segment.target_index <= 4
    target = route.waypoints[segment.target_index]
    assert target[1] == 0
    assert _oracle_chord_upper_bound((pose.x, pose.y), target, route.waypoints) <= 0.75


@pytest.mark.parametrize(
    "route, pose",
    [
        (
            Route(
                "l-corner",
                1,
                0,
                Pose(0, 0, 0),
                Pose(6, 6, math.pi / 2),
                (
                    (0, 0),
                    (1.5, 0),
                    (3, 0),
                    (4.5, 0),
                    (6, 0),
                    (6, 1.5),
                    (6, 3),
                    (6, 4.5),
                    (6, 6),
                ),
                "end",
            ),
            Pose(6, 0, 0),
        ),
        (
            Route(
                "u-turn-corner",
                1,
                0,
                Pose(0, 0, 0),
                Pose(0, 1.5, math.pi),
                (
                    (0, 0),
                    (1.5, 0),
                    (3, 0),
                    (4.5, 0),
                    (6, 0),
                    (6, 1.5),
                    (4.5, 1.5),
                    (3, 1.5),
                    (1.5, 1.5),
                    (0, 1.5),
                ),
                "end",
            ),
            Pose(6, 0, 0),
        ),
    ],
)
def test_corner_replans_strictly_increase_independent_progress(route: Route, pose: Pose) -> None:
    style = _style()
    kinematics = Kinematics(7, math.pi, -math.pi, 0.8)
    progress = _independent_route_progress((pose.x, pose.y), route.waypoints)
    maximum_segments, _ = walk_budget(route)
    for segment_number in range(maximum_segments):
        segment = plan_segment(route, pose, style, kinematics, 100 + segment_number)
        if segment.final:
            assert segment.target_index == len(route.waypoints) - 1
            break
        next_pose = _independent_drive_segment(segment.events, pose, kinematics)
        next_progress = _independent_route_progress((next_pose.x, next_pose.y), route.waypoints)
        assert next_progress > progress + 1e-6
        pose = next_pose
        progress = next_progress
    else:
        pytest.fail("corner replan exceeded segment budget")
    assert math.dist((pose.x, pose.y), (route.end.x, route.end.y)) <= 0.5


def test_long_turns_and_plans_have_real_same_key_gaps() -> None:
    route = _route()
    style = _style()
    kinematics = Kinematics(7, math.pi, -math.pi, 0.6)
    for seed in range(100):
        plan = plan_open_loop_walk(route, route.start, style, kinematics, seed)
        _assert_no_same_key_zero_gap(plan.events)
        for first, second in zip(plan.events, plan.events[1:], strict=False):
            if first.key in {"Left", "Right"} and not first.down and second.down and first.key == second.key:
                assert second.t - first.t >= MIN_HUMAN_HOLD_SECONDS
        for event in plan.events:
            if event.down:
                release = next(
                    item
                    for item in plan.events
                    if item.key == event.key and not item.down and item.t >= event.t
                )
                assert release.t - event.t >= MIN_HUMAN_HOLD_SECONDS - 1e-9

    with pytest.raises(ValueError, match="release-to-press"):
        Segment(
            (
                KeyEvent(0.0, "W", True),
                KeyEvent(MIN_HUMAN_HOLD_SECONDS, "W", False),
                KeyEvent(MIN_HUMAN_HOLD_SECONDS, "W", True),
                KeyEvent(2 * MIN_HUMAN_HOLD_SECONDS, "W", False),
            ),
            route.start,
            0,
            1,
        )


def test_long_forward_and_turn_spans_are_split_below_autorepeat_delay() -> None:
    route = _route()
    style = Style(
        (1.5, 1.6, 1.7),
        (0.15, 0.2, 0.25),
        (0.15, 0.2, 0.25),
        (1.5, 1.6, 1.7),
        (0.08, 0.1, 0.12),
        (0.08, 0.1, 0.12),
        (0.7, 0.9, 1.1),
        (0.4, 0.5, 0.6),
    )
    kinematics = Kinematics(7, math.pi, -math.pi, 0.6)
    plan = plan_open_loop_walk(route, route.start, style, kinematics, 11)
    open_events: dict[str, float] = {}
    for event in plan.events:
        if event.down:
            open_events[event.key] = event.t
        else:
            assert event.key in open_events
            assert event.t - open_events.pop(event.key) <= MAX_KEY_HOLD_SECONDS + 1e-9
    assert not open_events


def test_segment_jump_rules_and_final_facing() -> None:
    route = Route(
        "jump",
        1,
        0,
        Pose(0, 0, 0),
        Pose(8, 0, 0),
        ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (6, 0), (8, 0)),
        "end",
    )
    style = Style(
        (0.35, 0.36, 0.36),
        (0.15, 0.15, 0.15),
        (0.15, 0.15, 0.15),
        (0.08, 0.10, 0.12),
        (0.08, 0.10, 0.12),
        (0.03, 0.03, 0.03),
        (0.03, 0.03, 0.03),
        (0.4, 0.5, 0.6),
    )
    kinematics = Kinematics(7, math.pi, -math.pi, 0.15)
    segment = plan_segment(route, route.start, style, kinematics, 1, max_distance=4)
    jumps = [event.t for event in segment.events if event.key == "space" and event.down]
    assert len(jumps) == 1
    jump_time = jumps[0]
    w_holds: list[tuple[float, float]] = []
    w_start = None
    for event in segment.events:
        if event.key == "W" and event.down:
            w_start = event.t
        elif event.key == "W" and not event.down:
            assert w_start is not None
            w_holds.append((w_start, event.t))
    assert any(
        start <= jump_time and jump_time + kinematics.jump_airtime <= end + 1e-9 for start, end in w_holds
    )
    chord = math.dist((route.start.x, route.start.y), route.waypoints[segment.target_index])
    heading = math.atan2(
        route.waypoints[segment.target_index][1] - route.start.y,
        route.waypoints[segment.target_index][0] - route.start.x,
    )
    travel = _independent_locked_heading_travel(segment.events, kinematics, heading)
    assert travel == pytest.approx(chord, abs=0.05)
    assert travel <= chord + 1e-9
    assert simulate(segment.events, route.start, kinematics)[-1][1] == segment.expected
    assert segment.target_index == 4

    short_burst_style = Style(
        (0.30, 0.31, 0.32),
        (0.15, 0.15, 0.15),
        (0.15, 0.15, 0.15),
        (0.08, 0.10, 0.12),
        (0.08, 0.10, 0.12),
        (0.03, 0.03, 0.03),
        (0.03, 0.03, 0.03),
        (0.4, 0.5, 0.6),
    )
    long_airtime = Kinematics(7, math.pi, -math.pi, 0.8)
    no_jump = plan_segment(route, route.start, short_burst_style, long_airtime, 1, max_distance=4)
    assert not any(event.key == "space" for event in no_jump.events)

    probability_style = Style(
        (1.0, 1.0, 1.0),
        (0.15, 0.15, 0.15),
        (0.15, 0.15, 0.15),
        (0.08, 0.10, 0.12),
        (0.08, 0.10, 0.12),
        (0.03, 0.03, 0.03),
        (10.0, 10.0, 10.0),
        (0.4, 0.5, 0.6),
    )
    probability = 4.0 / (7.0 * 10.0)
    expected_jumps = sum(random.Random(seed).random() < probability for seed in range(200))
    observed_jumps = sum(
        any(
            event.key == "space" and event.down
            for event in plan_segment(
                route, route.start, probability_style, kinematics, seed, max_distance=4
            ).events
        )
        for seed in range(200)
    )
    assert 0 < expected_jumps < 200
    assert observed_jumps == expected_jumps

    short_route = Route(
        "short-jump",
        1,
        0,
        Pose(0, 0, 0),
        Pose(8, 0, 0),
        ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (6, 0), (8, 0)),
        "end",
    )
    short_segment = plan_segment(short_route, short_route.start, style, kinematics, 2, max_distance=2)
    assert short_segment.target_index == 2
    assert not any(event.key == "space" for event in short_segment.events)
    near_end = plan_segment(route, Pose(4, 0, 0), style, kinematics, 3, max_distance=4)
    assert math.dist(route.waypoints[near_end.target_index], (route.end.x, route.end.y)) < 3
    assert not any(event.key == "space" for event in near_end.events)

    final = plan_segment(route, Pose(7.8, 0.0, 0.0), style, kinematics, 3)
    assert final.final
    assert final.target_index == len(route.waypoints) - 1
    assert math.dist((final.expected.x, final.expected.y), (7.8, 0.0)) == pytest.approx(0)
    assert abs(route_walk._angle_delta(final.expected.facing - route.end.facing)) <= 0.15
    assert all(event.key != "W" and event.key != "space" for event in final.events)

    with pytest.raises(ValueError, match="final turn"):
        plan_segment(
            _route(),
            Pose(11.8, 0.0, 2.39),
            _style(),
            Kinematics(7, 6, -6, 0.15),
            4,
        )


def test_check_fix_thresholds_and_budget() -> None:
    route = _route()
    straight = Route(
        "straight",
        1,
        0,
        Pose(0, 0, 0),
        Pose(3, 0, 0),
        ((0, 0), (1, 0), (2, 0), (3, 0)),
        "end",
    )
    assert check_fix(straight, Pose(0, 0, 0), Pose(1, 0, 0.35)).ok
    assert check_fix(straight, Pose(0, 0, 0), Pose(0, 1, 0.35)).ok
    assert not check_fix(straight, Pose(0, 0, 0), Pose(1.000001, 0, 0)).ok
    corridor_only = check_fix(straight, Pose(0.8, 1, 0), Pose(0.8, 1.000001, 0))
    assert corridor_only.position_error < 1
    assert corridor_only.corridor_distance > 1
    assert not corridor_only.ok
    assert not check_fix(straight, Pose(0, 0, 0), Pose(0, 0, 0.350001)).ok
    length = sum(
        math.dist(first, second) for first, second in zip(route.waypoints, route.waypoints[1:], strict=False)
    )
    assert walk_budget(route) == (math.ceil(length / 2) + 6, 60)


def _actuation_errors(seed: int, count: int) -> tuple[tuple[float, float, float], ...]:
    # The live failure was systematic (turn rate 30 % off), so each run has a
    # bias plus fresh per-chunk noise; every chunk still gets its own triple.
    rng = random.Random(seed)
    turn_bias = rng.choice((-1, 1)) * rng.uniform(0.08, 0.15)
    run_bias = rng.uniform(-0.1, 0.1)
    return tuple(
        (
            1 + turn_bias + rng.uniform(-0.05, 0.05),
            1 + run_bias + rng.uniform(-0.05, 0.05),
            rng.uniform(-0.3, 0.3),
        )
        for _ in range(count)
    )


def _consume_actuation_error(
    errors: tuple[tuple[float, float, float], ...], consumed: list[tuple[float, float, float]]
) -> tuple[float, float, float]:
    index = len(consumed)
    assert index < len(errors)
    error = errors[index]
    consumed.append(error)
    return error


def _perturbed_kinematics(kinematics: Kinematics, error: tuple[float, float, float]) -> Kinematics:
    turn_factor, run_factor, _noise = error
    return Kinematics(
        kinematics.run_speed * run_factor,
        kinematics.turn_rate_left * turn_factor,
        kinematics.turn_rate_right * turn_factor,
        kinematics.jump_airtime,
    )


def _apply_actuation(
    events: tuple[KeyEvent, ...], pose: Pose, kinematics: Kinematics, error: tuple[float, float, float]
) -> Pose:
    actual_kinematics = _perturbed_kinematics(kinematics, error)
    actual = simulate(events, pose, actual_kinematics)[-1][1]
    if math.dist((actual.x, actual.y), (pose.x, pose.y)) > 1e-9:
        angle = math.atan2(actual.y - pose.y, actual.x - pose.x) + math.pi / 2
        noise = error[2]
        actual = Pose(actual.x + noise * math.cos(angle), actual.y + noise * math.sin(angle), actual.facing)
    return actual


def _nominal_open_loop_segments(
    route: Route, start: Pose, style: Style, kinematics: Kinematics, seed: int
) -> list[Segment]:
    current = start
    segments: list[Segment] = []
    maximum_segments, _ = walk_budget(route)
    for segment_number in range(maximum_segments):
        segment_seed = seed + segment_number
        segment = route_walk._plan_segment_with_rng(
            route, current, style, kinematics, random.Random(segment_seed), segment_seed
        )
        segments.append(segment)
        current = segment.expected
        if segment.final:
            return segments
    raise AssertionError("open-loop planner exceeded walk budget")


def test_closed_loop_reaches_curved_route_within_budget() -> None:
    route = _route()
    style = _style()
    kinematics = Kinematics(7, math.pi, -math.pi, 0.15)
    max_segments, _ = walk_budget(route)
    for seed in range(50):
        errors = _actuation_errors(seed, max_segments)
        pose = route.start
        for segment_number in range(max_segments):
            segment = plan_segment(
                route, pose, style, kinematics, seed * 100 + segment_number, max_distance=4
            )
            pose = _apply_actuation(segment.events, pose, kinematics, errors[segment_number])
            verdict = check_fix(route, segment.expected, pose)
            if not verdict.ok:
                break
            if math.dist((pose.x, pose.y), (route.end.x, route.end.y)) <= 0.5:
                break
        else:
            pytest.fail(f"seed {seed} exceeded segment budget")
        assert math.dist((pose.x, pose.y), (route.end.x, route.end.y)) <= 0.5


def test_open_loop_is_sensitive_to_the_same_actuation_errors() -> None:
    route = _route()
    style = _style()
    kinematics = Kinematics(7, math.pi, -math.pi, 0.15)
    misses = 0
    for seed in range(50):
        max_segments, _ = walk_budget(route)
        errors = _actuation_errors(seed, max_segments)
        closed_consumed: list[tuple[float, float, float]] = []
        closed_pose = route.start
        for segment_number in range(max_segments):
            segment = plan_segment(
                route, closed_pose, style, kinematics, seed * 100 + segment_number, max_distance=4
            )
            closed_pose = _apply_actuation(
                segment.events,
                closed_pose,
                kinematics,
                _consume_actuation_error(errors, closed_consumed),
            )
            verdict = check_fix(route, segment.expected, closed_pose)
            if not verdict.ok:
                break
            if math.dist((closed_pose.x, closed_pose.y), (route.end.x, route.end.y)) <= 0.5:
                break
        else:
            pytest.fail(f"seed {seed} exceeded closed-loop segment budget")
        assert math.dist((closed_pose.x, closed_pose.y), (route.end.x, route.end.y)) <= 0.5
        plan = plan_open_loop_walk(route, route.start, style, kinematics, seed)
        segments = _nominal_open_loop_segments(route, route.start, style, kinematics, seed)
        assert segments[-1].final
        assert (
            math.dist((plan.final.x, plan.final.y), (segments[-1].expected.x, segments[-1].expected.y))
            <= 1e-9
        )
        assert abs(route_walk._angle_delta(plan.final.facing - segments[-1].expected.facing)) <= 1e-9
        open_consumed: list[tuple[float, float, float]] = []
        final = route.start
        for segment_number, segment in enumerate(segments):
            assert segment_number == len(open_consumed)
            final = _apply_actuation(
                segment.events,
                final,
                kinematics,
                _consume_actuation_error(errors, open_consumed),
            )
        assert closed_consumed == list(errors[: len(closed_consumed)])
        assert open_consumed == list(errors[: len(open_consumed)])
        assert closed_consumed[: len(open_consumed)] == open_consumed[: len(closed_consumed)]
        if math.dist((final.x, final.y), (route.end.x, route.end.y)) > 1:
            misses += 1
    assert misses > 25


def test_builder_uses_measured_constants_and_records_key_gaps(tmp_path: Path) -> None:
    recordings = []
    for index in range(2):
        recording = tmp_path / f"recording-{index}"
        _write_recording(recording, short_strafe=index == 0, recorded_speed=3.5)
        recordings.append(recording)
    route_file = build_route_file(
        recordings,
        start_xy=(0, 0),
        end_xy=(10, 0),
        radius=1,
        start_target="Auctioneer",
        end_target="Mailbox",
    )
    assert route_file.kinematics.run_speed == RUN_SPEED
    assert route_file.kinematics.turn_rate_left == KEYBOARD_TURN_RATE
    assert route_file.kinematics.turn_rate_right == -KEYBOARD_TURN_RATE
    assert route_file.kinematics.provenance == KINEMATICS_PROVENANCE
    assert all(sample >= MIN_HUMAN_HOLD_SECONDS for sample in route_file.style.key_gap)
    assert any("excluded 1 strafe_tap" in source for source in route_file.sources)


def test_cli_plan_segment_and_refuses_overwrite(tmp_path: Path) -> None:
    route_file = RouteFile(
        {_route().name: _route()}, _style(), Kinematics(7, math.pi, -math.pi, 0.15), ("synthetic",)
    )
    routes = tmp_path / "routes.json"
    routes.write_text(route_file.to_json())
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "crowley.session.route_walk",
            "plan-segment",
            "--routes",
            str(routes),
            "--route",
            _route().name,
            "--from",
            "0,0,0.6",
            "--seed",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert set(value) == {"events", "expected", "final", "seed", "target_index"}
    assert value["seed"] == 1
    existing = tmp_path / "existing.json"
    existing.write_text("keep me")
    recording = tmp_path / "recording"
    _write_recording(recording)
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
            str(existing),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "refusing to overwrite" in result.stderr
    assert existing.read_text() == "keep me"


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
            (0.1, 0.2, 0.3),
        )
    route_file = RouteFile(
        {_route().name: _route()},
        _style(),
        Kinematics(7, KEYBOARD_TURN_RATE, -KEYBOARD_TURN_RATE, 0.6),
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
    kinematics = Kinematics(7, KEYBOARD_TURN_RATE, -KEYBOARD_TURN_RATE, 0.6)
    first = plan_open_loop_walk(route, route.start, style, kinematics, 7)
    second = plan_open_loop_walk(route, route.start, style, kinematics, 7)
    other = plan_open_loop_walk(route, route.start, style, kinematics, 8)
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
            assert event.t - down_times[event.key] >= MIN_HUMAN_HOLD_SECONDS - 1e-9
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
    true_max_distance = max(7 * 0.15, 7 * 0.15 - 7 * (0.2 - 0.15))
    round1_sample_distance = max(7 * 0.05, 7 * 0.10, 7 * 0.15 - 7 * (0.2 - 0.15))
    assert true_max_distance == pytest.approx(1.05)
    assert round1_sample_distance == pytest.approx(0.7)
    assert true_max_distance > 1.0 > round1_sample_distance
    monkeypatch.setattr(route_walk, "_make_attempt", lambda *args: (events, route.end))
    with pytest.raises(ValueError, match="corridor"):
        plan_open_loop_walk(route, route.start, style, kinematics, 1)


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
    kinematics = Kinematics(7, KEYBOARD_TURN_RATE, -KEYBOARD_TURN_RATE, 0.6)
    for seed in range(50):
        plan = plan_open_loop_walk(route, route.start, style, kinematics, seed)
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
    assert route_file.kinematics.run_speed == pytest.approx(RUN_SPEED)
    assert route_file.kinematics.turn_rate_left == pytest.approx(KEYBOARD_TURN_RATE)
    assert route_file.kinematics.turn_rate_right == pytest.approx(-KEYBOARD_TURN_RATE)
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
