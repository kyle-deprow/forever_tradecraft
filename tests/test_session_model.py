from __future__ import annotations

import json

import pytest

from crowley.session.model import OBSERVED_CONTROLS, OBSERVED_STATES, LunaAdapter, ModelError


def _observation(state: str = "executor_mailbox", control: str = "crowley_executor_button") -> str:
    answer = json.dumps(
        {
            "state": state,
            "facts": {
                "scene": "world",
                "character": "Arthur",
                "realm": "Classic Beta PvE 2",
                "modal": "mailbox",
                "code": "",
                "control": control,
                "idle": "true",
            },
            "anchor": {"x": 320, "y": 180, "width": 120, "height": 48},
        },
        separators=(",", ":"),
    )
    events = [
        {"type": "thread.started", "thread_id": "thread-test"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"id": "answer-1", "type": "agent_message", "text": answer}},
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 1,
                "cached_input_tokens": 0,
                "cache_write_input_tokens": 0,
                "output_tokens": 1,
                "reasoning_output_tokens": 0,
            },
        },
    ]
    return "\n".join(json.dumps(event, separators=(",", ":")) for event in events)


def test_executor_mailbox_is_a_strict_named_model_state() -> None:
    assert "executor_mailbox" in OBSERVED_STATES
    assert "crowley_executor_button" in OBSERVED_CONTROLS
    parsed = LunaAdapter._parse_observation(_observation())
    assert parsed.state == "executor_mailbox"
    assert parsed.facts["control"] == "crowley_executor_button"
    assert parsed.anchor == (320, 180, 120, 48)
    assert "executor_mailbox" in LunaAdapter._observation_schema()


def test_executor_mailbox_rejects_a_wrong_control_or_state() -> None:
    with pytest.raises(ModelError, match="named visual state"):
        LunaAdapter._parse_observation(_observation(state="executor"))
    wrong_control = json.loads(_observation().splitlines()[2])
    wrong_control["item"]["text"] = wrong_control["item"]["text"].replace(
        '"control":"crowley_executor_button"', '"control":3'
    )
    wrong_control = "\n".join(
        [
            _observation().splitlines()[0],
            _observation().splitlines()[1],
            json.dumps(wrong_control, separators=(",", ":")),
            _observation().splitlines()[3],
        ]
    )
    with pytest.raises(ModelError, match="facts"):
        LunaAdapter._parse_observation(wrong_control)
