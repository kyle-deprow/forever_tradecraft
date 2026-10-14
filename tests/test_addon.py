"""Targeted watchlist Lua behavior using the real addon under Lua 5.1."""

import base64
import json
import zlib

from crowley.core import savedvars
from crowley.core.scanformat import validate_v2_envelope

from .wow_harness import Auction, WowClient


def run_sweep(client: WowClient, item_ids: list[int] | None = None) -> dict:
    client.login()
    client.set_plan(item_ids or [2589])
    client.set_auctions([Auction(itemID=2589, name="Linen Cloth", count=2, buyout=200)])
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    scans = savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"]
    assert len(scans) == 1
    return next(iter(scans.values()))


def envelope(raw: dict) -> dict:
    result = {
        key: raw[key]
        for key in (
            "id",
            "format",
            "startedAt",
            "finishedAt",
            "house",
            "context",
            "numRows",
            "numObservations",
        )
    }
    result["payload"] = raw["payload"]
    return result


def decoded_payload(client: WowClient) -> dict:
    raw = next(iter(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values()))
    return validate_v2_envelope(envelope(raw))["decoded"]


def test_absent_plan_refuses_actionable_collection():
    client = WowClient()
    client.login()
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    assert "scan refused: no scan plan loaded" in client.chat[-1]
    assert not list(client.lua.globals().CrowleyDB.scans.items())


def test_targeted_sweep_roundtrips_strict_v2_payload():
    raw = run_sweep(WowClient())
    parsed = validate_v2_envelope(envelope(raw))
    assert raw["format"] == 2
    observation = parsed["decoded"]["observations"]["2589"]
    assert observation["coverage"] == "full"
    assert observation["rows"]["row:1"]["unitPrice"] == {"numerator": 100, "denominator": 1}
    assert parsed["decoded"]["owned"]["status"] == "full"


def test_commodity_sweep_uses_unit_price_and_item_id_key_without_link():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([Auction(2589, "Linen Cloth", 7, 25, isCommodity=True)])
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    raw = next(iter(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values()))
    observation = validate_v2_envelope(envelope(raw))["decoded"]["observations"]["2589"]
    assert observation["kind"] == "commodity"
    assert observation["rows"]["row:1"]["itemKey"] == "2589"
    assert observation["rows"]["row:1"]["price"] == {"kind": "unit", "copper": 25}


def test_representative_full_watchlist_payload_size_is_measured():
    client = WowClient()
    client.login()
    ids = list(range(1000, 1428))
    client.set_plan(ids)
    client.set_auctions(
        [
            Auction(itemID=item_id, name=f"I{item_id}", count=1, buyout=100, auctionID=item_id)
            for item_id in ids
        ]
    )
    # A one-second response cadence keeps the real rolling 100/60s transport
    # window active while allowing all 428 initial queries to finish within the
    # 600-second sweep budget.
    client.set_event_behavior(delay=1)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    for _ in range(700):
        client.run_timers()
        if list(client.lua.globals().CrowleyDB.scans.items()):
            break
        client.advance_with_timers(1)
    raw = next(iter(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values()))
    payload = decoded_payload(client)
    assert raw["numObservations"] == 428
    assert raw["numRows"] == 428
    assert all(observation["coverage"] == "full" for observation in payload["observations"].values())
    # This is a measured representative fixture, not a wire-size promise.  Keep a
    # generous budget so a harmless encoder change cannot turn the test brittle.
    assert 10_000 < len(raw["payload"]) < 100_000


def test_sweep_timeout_dispatches_before_later_inserted_timer():
    client = WowClient()
    first = run_sweep(client)
    client.advance_with_timers(900)
    scans = list(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values())
    assert len(scans) == 2
    second = next(scan for scan in scans if scan["id"] != first["id"])
    assert decoded_payload(client)["observations"]["2589"]["coverage"] == "full"
    assert second["finishedAt"] >= second["startedAt"]


def test_finished_sweep_keeps_immutable_plan_provenance():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([Auction(2589, "Linen", 1, 100)])
    client.set_event_behavior(delay=5)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    original_hash = client.lua.globals().CROWLEY_DATA.scanPlan.planHash
    client.set_plan([2592])
    client.advance(5)
    client.run_timers()
    payload = decoded_payload(client)
    assert payload["planHash"] == original_hash
    assert json.loads(payload["planJSON"])["itemIDs"] == [2589]


def test_documented_structured_keys_and_cumulative_paging():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.state.pageSize = 10
    client.set_auctions(
        [Auction(2589, "Linen", 1, 100 + index, auctionID=1000 + index) for index in range(25)]
    )
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    payload = decoded_payload(client)
    observation = payload["observations"]["2589"]
    assert observation["coverage"] == "bounded"
    assert len(observation["rows"]) == 20
    assert len(client.send_log) == 4  # search, two cumulative pages, owned query
    assert all(entry["kind"] in {"search", "item_page", "owned"} for entry in client.send_log)


def test_bounded_commodity_has_known_witness_and_strict_roundtrip():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_source_incomplete()
    client.set_auctions(
        [Auction(2589, "Linen", 1, price, isCommodity=True, auctionID=price) for price in range(1, 22)]
    )
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    raw = next(iter(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values()))
    parsed = validate_v2_envelope(envelope(raw))["decoded"]
    observation = parsed["observations"]["2589"]
    assert observation["coverage"] == "bounded"
    assert observation["sourceComplete"] is False
    assert observation["cutoff"] == {"kind": "price", "numerator": 20, "denominator": 1}
    assert observation["higherPriceWitness"] == {"kind": "known", "numerator": 21, "denominator": 1}
    assert len(observation["rows"]) == 20


def test_full_item_normalizes_unit_price_after_whole_buyout_source_order():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions(
        [
            Auction(2589, "Linen", 2, 2, auctionID=1),
            Auction(2589, "Linen", 1, 3, auctionID=2),
            Auction(2589, "Linen", 4, 4, auctionID=3),
        ]
    )
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    raw = next(iter(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values()))
    observation = validate_v2_envelope(envelope(raw))["decoded"]["observations"]["2589"]
    assert observation["coverage"] == "full"
    ordered_rows = [observation["rows"][f"row:{index}"] for index in range(1, 4)]
    assert [row["resultID"] for row in ordered_rows] == [1, 3, 2]
    assert [row["unitPrice"] for row in ordered_rows] == [
        {"numerator": 1, "denominator": 1},
        {"numerator": 1, "denominator": 1},
        {"numerator": 3, "denominator": 1},
    ]


def test_page_limit_preserves_sorted_partial_rows_beyond_depth():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.state.pageSize = 3
    client.set_auctions(
        [Auction(2589, "Linen", 2 if price % 2 == 0 else 1, price, auctionID=price) for price in range(1, 34)]
    )
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    raw = next(iter(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values()))
    observation = validate_v2_envelope(envelope(raw))["decoded"]["observations"]["2589"]
    assert observation["coverage"] == "incomplete"
    assert observation["reasonCode"] == "page_limit"
    assert observation["rowCount"] == 30
    assert len(observation["rows"]) > 20
    first_units = [observation["rows"][f"row:{index}"]["unitPrice"] for index in range(1, 5)]
    assert first_units == [
        {"numerator": 1, "denominator": 1},
        {"numerator": 1, "denominator": 1},
        {"numerator": 2, "denominator": 1},
        {"numerator": 3, "denominator": 1},
    ]


def test_unsafe_nonadjacent_price_product_keeps_partial_rows():
    max_safe = 9007199254740991
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions(
        [
            Auction(2589, "Linen", 1, 1, auctionID=1),
            Auction(2589, "Linen", max_safe, max_safe - 1, auctionID=2),
            Auction(2589, "Linen", 1, max_safe, auctionID=3),
        ]
    )
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    raw = next(iter(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values()))
    observation = validate_v2_envelope(envelope(raw))["decoded"]["observations"]["2589"]
    assert observation["coverage"] == "incomplete"
    assert observation["reasonCode"] == "numeric_range"
    assert observation["rowCount"] == 3


def test_advertised_missing_result_is_incomplete_not_empty_full_scope():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([Auction(2589, "Linen", 1, 100)])
    client.set_missing_results([1])
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    observation = decoded_payload(client)["observations"]["2589"]
    assert observation["coverage"] == "incomplete"
    assert observation["reasonCode"] == "identity_mismatch"
    assert observation["rowCount"] == 0


def test_equal_price_ties_roundtrip_in_any_result_identity_order():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions(
        [Auction(2589, "Linen", 1, 100, isCommodity=True, auctionID=index) for index in range(1, 13)]
    )
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    raw = next(iter(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values()))
    observation = validate_v2_envelope(envelope(raw))["decoded"]["observations"]["2589"]
    assert observation["coverage"] == "full"
    assert observation["rowCount"] == 12


def test_market_abort_keeps_owned_collection_unqueried():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([Auction(2589, "Linen", 1, 100)])
    client.set_event_behavior(delay=5)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.fire("PLAYER_LOGOUT")
    client.run_timers()
    raw = next(iter(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values()))
    owned = validate_v2_envelope(envelope(raw))["decoded"]["owned"]
    assert owned["status"] == "unqueried"
    assert owned["query"] == {"kind": "unqueried"}
    assert owned["reasonCode"] == "not_started"


def test_owned_house_change_is_incomplete_and_override_finalizes_before_apply():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([])
    client.set_owned([Auction(2589, "Linen", 1, 100)], complete=True)
    client.set_owned_behavior(delay=5)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    client.slash("set faction alliance")
    raw = next(iter(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values()))
    owned = validate_v2_envelope(envelope(raw))["decoded"]["owned"]
    assert owned["status"] == "incomplete"
    assert owned["reasonCode"] == "house_changed"
    assert client.lua.globals().CrowleyDB.settings.faction == "alliance"


def test_owned_result_rechecks_captured_house_before_accepting_rows():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([])
    client.set_owned([Auction(2589, "Linen", 1, 100)], complete=True)
    client.set_owned_behavior(delay=5)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    client.set_house(faction="Alliance")
    client.advance(5)
    client.run_timers()
    raw = next(iter(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values()))
    owned = validate_v2_envelope(envelope(raw))["decoded"]["owned"]
    assert owned["status"] == "incomplete"
    assert owned["reasonCode"] == "house_changed"


def test_hidden_owner_metadata_is_unknown_not_affirmative_grouping():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([Auction(2589, "Linen", 1, 100, hiddenOwners=True)])
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    observation = decoded_payload(client)["observations"]["2589"]
    row = next(iter(observation["rows"].values()))
    assert row["owners"]["identityKind"] == "unknown"
    assert row["owners"]["names"] == {}


def test_shared_boundary_level_keeps_every_row_at_cutoff():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    auctions = [Auction(2589, "Linen", 1, price, isCommodity=True, auctionID=price) for price in range(1, 20)]
    auctions.extend(
        [
            Auction(2589, "Linen", 2, 20, isCommodity=True, auctionID=2001),
            Auction(2589, "Linen", 3, 20, isCommodity=True, auctionID=2002),
            Auction(2589, "Linen", 1, 21, isCommodity=True, auctionID=2003),
        ]
    )
    client.set_auctions(auctions)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    observation = decoded_payload(client)["observations"]["2589"]
    assert observation["coverage"] == "bounded"
    assert observation["cutoff"] == {"kind": "price", "numerator": 20, "denominator": 1}
    assert len(observation["rows"]) == 21
    assert sum(row["unitPrice"]["numerator"] == 20 for row in observation["rows"].values()) == 2


def test_external_same_key_search_is_marked_incomplete():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([Auction(2589, "Linen", 1, 100)])
    client.set_event_behavior(delay=5)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.external_search(2589)
    client.advance(5)
    client.run_timers()
    assert decoded_payload(client)["observations"]["2589"]["reasonCode"] == "identity_mismatch"


def test_cumulative_page_individual_to_grouped_identity_is_incomplete():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.state.pageSize = 1
    client.set_auctions(
        [
            Auction(2589, "Linen", 1, 100, auctionID=1),
            Auction(2589, "Linen", 1, 200, auctionID=2),
        ]
    )
    client.set_event_behavior(delay=5)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.advance(5)
    client.run_timers()
    client.state.auctions[1].containsOwnerItem = True
    client.advance(5)
    client.run_timers()
    observation = decoded_payload(client)["observations"]["2589"]
    assert observation["coverage"] == "incomplete"
    assert observation["reasonCode"] == "identity_mismatch"


def test_cumulative_page_grouped_to_individual_identity_is_incomplete():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.state.pageSize = 1
    client.set_auctions(
        [
            Auction(2589, "Linen", 1, 100, auctionID=1, containsOwnerItem=True),
            Auction(2589, "Linen", 1, 200, auctionID=2),
        ]
    )
    client.set_event_behavior(delay=5)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.advance(5)
    client.run_timers()
    client.state.auctions[1].containsOwnerItem = False
    client.advance(5)
    client.run_timers()
    observation = decoded_payload(client)["observations"]["2589"]
    assert observation["coverage"] == "incomplete"
    assert observation["reasonCode"] == "identity_mismatch"


def test_cumulative_page_individual_to_hidden_owner_identity_is_incomplete():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.state.pageSize = 1
    client.set_auctions(
        [
            Auction(2589, "Linen", 1, 100, auctionID=1),
            Auction(2589, "Linen", 1, 200, auctionID=2),
        ]
    )
    client.set_event_behavior(delay=5)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.advance(5)
    client.run_timers()
    hidden = client.lua.table()
    client.state.auctions[1].owners = hidden
    client.state.auctions[1].totalOwners = 0
    client.advance(5)
    client.run_timers()
    observation = decoded_payload(client)["observations"]["2589"]
    assert observation["coverage"] == "incomplete"
    assert observation["reasonCode"] == "identity_mismatch"


def test_no_payload_received_event_cannot_complete_search():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([Auction(2589, "Linen", 1, 100)])
    client.set_event_behavior(kind="RECEIVED")
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    assert not list(client.lua.globals().CrowleyDB.scans.items())
    client.advance(30)
    client.run_timers()
    assert decoded_payload(client)["observations"]["2589"]["reasonCode"] == "query_timeout"


def test_stale_unrelated_result_event_does_not_complete_active_query():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([Auction(2589, "Linen", 1, 100)])
    client.set_event_behavior(stale=True)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    assert decoded_payload(client)["observations"]["2589"]["coverage"] == "full"


def test_logout_preserves_partial_and_marks_tail_reason():
    client = WowClient()
    client.login()
    client.set_plan([2589, 2592])
    client.set_auctions([Auction(2589, "Linen", 1, 100)])
    client.set_event_behavior(delay=5)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.fire("PLAYER_LOGOUT")
    client.run_timers()
    observations = decoded_payload(client)["observations"]
    assert observations["2589"]["reasonCode"] == "logout"
    assert observations["2592"]["reasonCode"] == "logout"
    assert observations["2592"]["coverage"] == "unqueried"


def test_start_cadence_and_no_overlap():
    client = WowClient()
    first = run_sweep(client)
    client.slash("scan")
    assert "due in" in client.chat[-1]
    client.advance(899)
    client.run_timers()
    assert len(list(client.lua.globals().CrowleyDB.scans.items())) == 1
    client.advance(1)
    client.fire("AUCTION_HOUSE_SHOW")
    client.run_timers()
    assert len(list(client.lua.globals().CrowleyDB.scans.items())) == 2
    starts = sorted(scan["startedAt"] for _, scan in client.lua.globals().CrowleyDB.scans.items())
    assert first["startedAt"] + 900 == starts[-1]


def test_ah_close_finalizes_partial_without_replaying_callback():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([Auction(2589, "Linen Cloth", 2, 200)])
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.fire("AUCTION_HOUSE_CLOSED")
    client.run_timers()
    scans = list(client.lua.globals().CrowleyDB.scans.items())
    assert len(scans) == 1
    assert "sweep saved" in client.chat[-1]


def test_owned_and_query_api_are_reported_by_probe():
    client = WowClient()
    client.login()
    client.slash("probe")
    probe = savedvars.loads(client.saved_variables())["CrowleyDB"]["probe"]
    names = probe["namespaces"]["C_AuctionHouse"]
    assert "SendSellSearchQuery" in names
    assert "QueryOwnedAuctions" in names


def test_sweep_timeout_keeps_active_item_partial_and_unqueried_tail():
    client = WowClient()
    client.login()
    ids = list(range(2589, 2611))
    client.set_plan(ids)
    client.set_auctions([Auction(2589, "Linen", 1, 100)])
    client.set_metadata_pending(ids)
    client.state.metadataDelay = 601
    client.set_event_behavior(delay=601)
    client.set_owned_behavior(emit=False)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.advance_with_timers(600)
    payload = decoded_payload(client)
    observations = payload["observations"]
    assert any(
        observation["reasonCode"] == "sweep_timeout" and observation["query"]["kind"] == "queried"
        for observation in observations.values()
    )
    assert observations[str(ids[-1])]["coverage"] == "unqueried"
    assert observations[str(ids[-1])]["reasonCode"] == "sweep_timeout"
    assert payload["owned"]["status"] == "unqueried"
    assert payload["owned"]["query"] == {"kind": "unqueried"}
    assert payload["owned"]["reasonCode"] == "not_started"


def test_invalid_house_setting_keeps_delayed_sweep_and_settings_unchanged():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([Auction(2589, "Linen", 1, 100)])
    client.set_event_behavior(delay=5)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    assert client.ns.Scanner.InProgress()
    assert client.lua.globals().CrowleyDB.settings.faction is None
    client.slash("set faction goblins")
    assert client.ns.Scanner.InProgress()
    assert client.lua.globals().CrowleyDB.settings.faction is None
    client.advance(5)
    client.run_timers()
    observation = decoded_payload(client)["observations"]["2589"]
    assert observation["coverage"] == "full"
    assert observation["reasonCode"] == "ok"


def test_owned_timeout_starts_before_throttled_send_and_finalizes():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([])
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.set_throttled()
    client.run_timers()
    assert not list(client.lua.globals().CrowleyDB.scans.items())
    client.advance(30)
    client.run_timers()
    assert decoded_payload(client)["owned"]["reasonCode"] == "query_timeout"


def test_rolling_message_window_never_exceeds_100_sends():
    client = WowClient()
    client.login()
    ids = list(range(1000, 1428))
    client.set_plan(ids)
    client.set_auctions([])
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    for _ in range(1000):
        client.run_timers()
        if list(client.lua.globals().CrowleyDB.scans.items()):
            break
        client.advance(1)
    timestamps = [entry["at"] for entry in client.send_log]
    assert timestamps
    assert all(sum(now - 60 < then <= now for then in timestamps) <= 100 for now in timestamps)


def test_capped_sweeps_rotate_after_last_attempted_item():
    client = WowClient()
    client.login()
    ids = [2589, 2592, 2593]
    client.set_plan(ids)
    client.set_auctions([Auction(itemID=item_id, name="Item", count=1, buyout=100) for item_id in ids])
    client.set_event_behavior(delay=601)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.advance(600)
    client.run_timers()
    first_id = next(iter(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values()))["id"]
    client.advance(300)
    client.set_event_behavior(delay=601)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan force")
    client.advance(600)
    client.run_timers()
    scans = list(savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"].values())
    assert len(scans) == 2
    second = next(scan for scan in scans if scan["id"] != first_id)
    second_payload = json.loads(zlib.decompress(base64.b64decode(second["payload"]), -15))
    assert second_payload["observations"]["2592"]["query"]["kind"] == "queried"


def test_owned_partial_event_waits_for_full_completion():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    client.set_auctions([])
    client.set_owned([Auction(2589, "Linen", 1, 100, status="sold", auctionID=77)], complete=False)
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    client.run_timers()
    assert not list(client.lua.globals().CrowleyDB.scans.items())
    client.state.ownedFull = True
    client.fire("OWNED_AUCTIONS_UPDATED")
    assert decoded_payload(client)["owned"]["status"] == "full"
    assert "77" in decoded_payload(client)["owned"]["rows"]


def test_six_pending_sweeps_pause_without_eviction_until_ack_reload():
    client = WowClient()
    client.login()
    client.set_plan([2589])
    for index in range(6):
        client.set_auctions([Auction(2589, "Linen Cloth", 1, 100 + index)])
        client.fire("AUCTION_HOUSE_SHOW")
        client.slash("scan")
        client.run_timers()
        if index < 5:
            client.advance(900)
    assert len(list(client.lua.globals().CrowleyDB.scans.items())) == 6
    client.slash("scan force")
    assert "storage blocked" in client.chat[-1]
    ids = [scan_id for scan_id, _ in client.lua.globals().CrowleyDB.scans.items()]
    client.lua.globals().CROWLEY_DATA.ackedScans = client._to_lua(ids)
    client.login()
    assert not list(client.lua.globals().CrowleyDB.scans.items())
