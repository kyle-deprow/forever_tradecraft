"""Account capture and strict account-envelope contract tests."""

from __future__ import annotations

import copy
import json

import pytest

from crowley.core import savedvars
from crowley.core.account import AccountFormatError, validate_account_envelope

from .wow_harness import WowClient


def capture(client: WowClient) -> dict:
    client.login()
    return savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]


def test_full_capture_records_only_allowed_account_fields() -> None:
    client = WowClient(
        money=98_765,
        bags={
            0: {
                "numSlots": 2,
                "freeSlots": 1,
                "slots": {
                    1: {"itemID": 100, "stackCount": 2, "isBound": True, "quality": 4},
                },
            }
        },
        professions=[{"name": "Alchemy", "skillLineID": 171, "level": 50, "maxLevel": 300}],
        trade_ready=True,
        recipe_ids=[12, 11],
        recipe_infos={11: {"learned": True}, 12: {"learned": True}},
        cooldowns={11: {"startTime": 100.5, "duration": 30.0}, 12: {"startTime": 200, "duration": 0}},
        mail_open=True,
        mail=[
            {
                "money": 20,
                "daysLeft": 2.5,
                "hasItem": True,
                "items": [{"itemID": 200, "count": 3}],
                "sender": "Sensitive Sender",
                "subject": "Sensitive Subject",
            }
        ],
    )
    account = capture(client)

    assert account["gold"] == 98_765
    assert account["bags"]["0"]["slots"]["1"] == {
        "itemID": 100,
        "count": 2,
        "bound": True,
        "quality": 4,
    }
    assert account["professions"] == [{"name": "Alchemy", "skillLineID": 171, "level": 50, "maxLevel": 300}]
    assert account["recipes"]["171"]["learned"] == [11, 12]
    assert account["cooldowns"] == {"11": {"start": 100.5, "duration": 30}}
    assert account["mail"] == {
        "kind": "observed",
        "capturedAt": 1_760_000_000,
        "messages": [{"money": 20, "daysLeft": 2.5, "items": [{"itemID": 200, "count": 3}]}],
    }
    wire = json.dumps(account)
    assert "sender" not in wire and "subject" not in wire
    assert "Sensitive Sender" not in wire and "Sensitive Subject" not in wire
    assert not client.trade_calls
    validate_account_envelope(account)


def test_account_triggers_update_only_their_sections_and_debounce_bags() -> None:
    client = WowClient(
        money=10,
        bags={0: {"numSlots": 1, "freeSlots": 1, "slots": {}}},
        trade_ready=False,
        recipe_ids=[99],
        recipe_infos={99: {"learned": True}},
        mail_open=False,
    )
    initial = capture(client)
    client.set_money(20)
    client.fire("PLAYER_MONEY")
    after_money = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert after_money["gold"] == 20
    assert after_money["bags"] == initial["bags"]
    assert after_money["mail"] == initial["mail"]

    client.set_bags(
        {
            0: {
                "numSlots": 1,
                "freeSlots": 0,
                "slots": {1: {"itemID": 10, "stackCount": 1, "isBound": False, "quality": 1}},
            }
        }
    )
    client.fire("BAG_UPDATE_DELAYED")
    client.fire("BAG_UPDATE_DELAYED")
    assert savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]["bags"] == initial["bags"]
    client.advance_with_timers(1)
    after_bags = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert after_bags["bags"]["0"]["freeSlots"] == 0
    assert after_bags["gold"] == 20

    # A non-ready UI with native recipe IDs must retain the empty sections.
    assert initial["recipes"] == {}
    assert initial["cooldowns"] == {}
    client.fire("TRADE_SKILL_LIST_UPDATE")
    not_ready = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert not_ready["recipes"] == initial["recipes"]
    assert not_ready["cooldowns"] == initial["cooldowns"]

    client.set_trade_skill(
        ready=True,
        skill_line_id=171,
        recipe_ids=[11, 12],
        recipe_infos={11: {"learned": True}, 12: {"learned": False}},
        cooldowns={11: {"startTime": 1, "duration": 2}},
    )
    client.fire("TRADE_SKILL_SHOW")
    after_trade = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert after_trade["recipes"]["171"]["learned"] == [11]
    assert after_trade["cooldowns"] == {"11": {"start": 1, "duration": 2}}
    assert after_trade["gold"] == 20
    assert after_trade["mail"] == initial["mail"]

    client.set_trade_skill(
        ready=True,
        skill_line_id=164,
        recipe_ids=[21],
        recipe_infos={21: {"learned": True}},
        cooldowns={21: {"startTime": 3, "duration": 4}},
    )
    client.fire("TRADE_SKILL_LIST_UPDATE")
    retained = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert set(retained["recipes"]) == {"164", "171"}
    assert set(retained["cooldowns"]) == {"11", "21"}

    client.set_trade_skill(
        ready=True,
        skill_line_id=171,
        recipe_ids=[11],
        recipe_infos={11: {"learned": True}},
        cooldowns={11: {"startTime": 10, "duration": 0}},
    )
    client.fire("TRADE_SKILL_SHOW")
    replaced = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert replaced["recipes"]["171"]["learned"] == [11]
    assert set(replaced["cooldowns"]) == {"21"}

    client.set_mail(open=True, messages=[{"money": 5, "daysLeft": 1, "hasItem": False, "items": []}])
    client.fire("MAIL_INBOX_UPDATE")
    after_mail = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert after_mail["mail"]["kind"] == "observed"
    assert after_mail["gold"] == 20
    assert after_mail["recipes"] == replaced["recipes"]


def test_account_contained_errors_and_invalid_native_values_do_not_escape_event_dispatch() -> None:
    client = WowClient()
    capture(client)
    client.state.money = "not copper"
    client.fire("PLAYER_MONEY")
    account = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert account["gold"] == {"kind": "invalid_native", "field": "gold"}

    client.set_bags({0: {"numSlots": 1, "freeSlots": 1, "slots": {}}})
    client.state.bags[0].numSlots = "bad"
    client.fire("BAG_UPDATE_DELAYED")
    client.advance_with_timers(1)
    account = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert account["bags"]["kind"] == "invalid_native"


def test_account_native_exceptions_are_section_errors_and_recover_cleanly() -> None:
    client = WowClient(
        trade_ready=True,
        recipe_ids=[11],
        recipe_infos={11: {"learned": True}},
        cooldowns={11: {"startTime": 1, "duration": 2}},
    )
    capture(client)
    original_recipe_ids = client.lua.globals().C_TradeSkillUI.GetAllRecipeIDs
    client.lua.globals().C_TradeSkillUI.GetAllRecipeIDs = client.lua.eval(
        "function() error('native recipe failure') end"
    )
    client.fire("TRADE_SKILL_LIST_UPDATE")
    failed = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert failed["recipes"]["kind"] == "error"
    assert failed["cooldowns"]["kind"] == "error"

    client.lua.globals().C_TradeSkillUI.GetAllRecipeIDs = original_recipe_ids
    client.set_trade_skill(
        ready=True,
        skill_line_id=171,
        recipe_ids=[11],
        recipe_infos={11: {"learned": True}},
        cooldowns={11: {"startTime": 4, "duration": 5}},
    )
    client.fire("TRADE_SKILL_LIST_UPDATE")
    recovered = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert recovered["recipes"] == {"171": {"capturedAt": 1_760_000_000, "learned": [11]}}
    assert recovered["cooldowns"] == {"11": {"start": 4, "duration": 5}}
    assert "kind" not in recovered["recipes"]
    assert "kind" not in recovered["cooldowns"]

    original_ready = client.lua.globals().C_TradeSkillUI.IsTradeSkillReady
    client.lua.globals().C_TradeSkillUI.IsTradeSkillReady = client.lua.eval("function() return 'yes' end")
    client.fire("TRADE_SKILL_LIST_UPDATE")
    invalid = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert invalid["recipes"] == {"kind": "invalid_native", "field": "recipes.ready"}
    assert invalid["cooldowns"] == {"kind": "invalid_native", "field": "cooldowns.ready"}
    client.lua.globals().C_TradeSkillUI.IsTradeSkillReady = original_ready

    original_cooldown = client.lua.globals().C_Spell.GetSpellCooldown
    client.lua.globals().C_Spell.GetSpellCooldown = client.lua.eval(
        "function() return {startTime=1, duration='bad'} end"
    )
    client.fire("TRADE_SKILL_LIST_UPDATE")
    invalid_cooldown = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert invalid_cooldown["recipes"] == {"kind": "invalid_native", "field": "cooldowns.duration"}
    assert invalid_cooldown["cooldowns"] == {"kind": "invalid_native", "field": "cooldowns.duration"}
    client.lua.globals().C_Spell.GetSpellCooldown = original_cooldown


def test_harness_keeps_mail_frame_probe_surface_scoped() -> None:
    assert WowClient(account_fakes=False).lua.globals().MailFrame is None
    assert (
        WowClient(account_fakes=False, trade_frames={"MailFrame": True}).lua.globals().MailFrame is not None
    )


def test_account_caps_native_loop_bounds_and_contains_timer_failures() -> None:
    client = WowClient()
    capture(client)

    client.set_bags(
        {
            0: {
                "numSlots": 36,
                "freeSlots": 35,
                "slots": {36: {"itemID": 636, "stackCount": 1, "isBound": False, "quality": 1}},
            }
        }
    )
    client.fire("BAG_UPDATE_DELAYED")
    client.advance_with_timers(1)
    account = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert account["bags"]["0"]["numSlots"] == 36
    assert account["bags"]["0"]["slots"]["36"]["itemID"] == 636

    client.set_bags({0: {"numSlots": 37, "freeSlots": 37, "slots": {}}})
    client.fire("BAG_UPDATE_DELAYED")
    client.advance_with_timers(1)
    account = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert account["bags"] == {"kind": "invalid_native", "field": "bags.numSlots"}

    original_after = client.lua.globals().C_Timer.After
    client.lua.globals().C_Timer.After = client.lua.eval("function() error('timer failure') end")
    client.fire("BAG_UPDATE_DELAYED")
    account = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert account["bags"]["kind"] == "error"
    client.lua.globals().C_Timer.After = original_after

    messages = [{"money": 1, "daysLeft": 1, "hasItem": False, "items": {}} for _ in range(100)]
    messages[-1] = {
        "money": 1,
        "daysLeft": 1,
        "hasItem": True,
        "items": {index: {"itemID": 700 + index, "count": 1} for index in range(1, 17)},
    }
    client.set_mail(open=True, messages=messages)
    client.fire("MAIL_INBOX_UPDATE")
    account = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert account["mail"]["kind"] == "observed"
    assert len(account["mail"]["messages"]) == 100
    assert len(account["mail"]["messages"][-1]["items"]) == 16
    assert account["mail"]["messages"][-1]["items"][-1]["itemID"] == 716

    client.set_mail(open=True, messages=[{"money": 1, "daysLeft": 1, "hasItem": False, "items": {}}] * 101)
    client.fire("MAIL_INBOX_UPDATE")
    account = savedvars.loads(client.saved_variables())["CrowleyDB"]["account"]
    assert account["mail"] == {"kind": "invalid_native", "field": "mail.count"}


def test_account_validator_rejects_malformed_fields_and_unknown_keys() -> None:
    client = WowClient()
    base = capture(client)
    cases = [
        ("format", 2),
        ("capturedAt", -1),
        ("gold", -1),
        ("house", {**base["house"], "key": "wrong"}),
        ("context", {**base["context"], "interface": 0}),
        ("bags", {**base["bags"], "5": base["bags"]["0"]}),
        ("professions", [{"name": "Alchemy"}]),
        ("recipes", {"171": {"capturedAt": base["capturedAt"], "learned": [2, 1]}}),
        ("cooldowns", {"11": {"start": 1, "duration": 0}}),
        ("mail", {"kind": "observed", "capturedAt": base["capturedAt"], "messages": [{"money": 1}]}),
    ]
    for field, value in cases:
        malformed = copy.deepcopy(base)
        malformed[field] = value
        with pytest.raises(AccountFormatError):
            validate_account_envelope(malformed)

    malformed = copy.deepcopy(base)
    malformed["unknown"] = True
    with pytest.raises(AccountFormatError):
        validate_account_envelope(malformed)

    malformed = copy.deepcopy(base)
    malformed["recipes"] = {"9" * 5000: {"capturedAt": base["capturedAt"], "learned": []}}
    with pytest.raises(AccountFormatError):
        validate_account_envelope(malformed)

    malformed = copy.deepcopy(base)
    malformed["bags"]["0"]["slots"] = {"9" * 5000: base["bags"]["0"]["slots"].get("1", {})}
    with pytest.raises(AccountFormatError):
        validate_account_envelope(malformed)
