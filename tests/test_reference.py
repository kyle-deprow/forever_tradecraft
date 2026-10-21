"""Item-reference addon and wire-contract tests."""

from copy import deepcopy

import pytest

from crowley.core import savedvars
from crowley.core.reference import ReferenceFormatError, validate_reference_envelope

from .wow_harness import Auction, WowClient


def capture(client: WowClient, item_ids: list[int], *, ah_open: bool = True) -> dict:
    client.set_reference_items(item_ids)
    client.login()
    if ah_open:
        client.fire("AUCTION_HOUSE_SHOW")
    client.slash("reference")
    client.run_timers()
    return savedvars.loads(client.saved_variables())["CrowleyDB"]["reference"]


def test_open_capture_records_commodity_and_noncommodity_deposits() -> None:
    client = WowClient()
    client.set_auctions(
        [
            Auction(1001, "Commodity", 20, 100, isCommodity=True, sellPrice=4),
            Auction(1002, "Equipment", 1, 100, classID=2),
        ]
    )
    reference = capture(client, [1001, 1002, 1003])

    validated = validate_reference_envelope(reference)
    assert validated["ahOpen"] is True
    assert validated["items"]["1001"]["deposit"]["kind"] == "commodity"
    assert validated["items"]["1001"]["deposit"]["values"] == [
        {"duration": 1, "quantity": 1, "copper": 4},
        {"duration": 1, "quantity": 20, "copper": 80},
        {"duration": 2, "quantity": 1, "copper": 8},
        {"duration": 2, "quantity": 20, "copper": 160},
        {"duration": 3, "quantity": 1, "copper": 12},
        {"duration": 3, "quantity": 20, "copper": 240},
    ]
    assert [
        (call["duration"], call["quantity"]) for call in client.deposit_calls if call["itemID"] == 1001
    ] == [(duration, quantity) for duration in (1, 2, 3) for quantity in (1, 20)]
    assert validated["items"]["1002"]["deposit"] == {"kind": "not_commodity"}
    assert validated["items"]["1003"]["deposit"] == {"kind": "not_commodity"}


def test_closed_capture_is_unqueried_and_delayed_loads_have_terminal_statuses() -> None:
    closed = WowClient()
    reference = capture(closed, [1001], ah_open=False)
    assert reference["items"]["1001"]["deposit"] == {"kind": "unqueried", "reason": "ah_closed"}

    delayed = WowClient()
    delayed.set_auctions([Auction(1001, "Commodity", 20, 100, isCommodity=True)])
    delayed.set_reference_load_behavior(delay=5, never=[1003], failures=[1002])
    delayed.set_reference_items([1001, 1002, 1003])
    delayed.login()
    delayed.fire("AUCTION_HOUSE_SHOW")
    delayed.slash("reference")
    delayed.advance_with_timers(31)
    items = savedvars.loads(delayed.saved_variables())["CrowleyDB"]["reference"]["items"]
    assert items["1001"]["status"] == "ok"
    assert items["1002"]["status"] == "not_found"
    assert items["1003"]["status"] == "load_timeout"


def test_reference_requests_at_most_fifty_items_at_once() -> None:
    client = WowClient()
    client.set_reference_items(list(range(1000, 1051)))
    client.set_reference_load_behavior(never=list(range(1000, 1051)))
    client.login()
    client.slash("reference")

    assert len(list(client.state.requested.items())) == 50
    client.advance_with_timers(30)
    assert set(savedvars.loads(client.saved_variables())["CrowleyDB"]["reference"]["items"]) == {
        str(item_id) for item_id in range(1000, 1051)
    }


def test_sequential_captures_ignore_the_first_capture_deadline() -> None:
    client = WowClient()
    client.set_reference_items([1001])
    client.login()
    client.slash("reference")
    client.run_timers()
    first = savedvars.loads(client.saved_variables())["CrowleyDB"]["reference"]

    client.advance(1)
    client.set_reference_items([1002])
    client.set_reference_load_behavior(never=[1002])
    client.slash("reference")
    client.advance_with_timers(29)
    assert client.ns.Reference.InProgress() is True
    assert savedvars.loads(client.saved_variables())["CrowleyDB"]["reference"] == first

    client.advance_with_timers(1)
    assert client.ns.Reference.InProgress() is False
    assert (
        savedvars.loads(client.saved_variables())["CrowleyDB"]["reference"]["items"]["1002"]["status"]
        == "load_timeout"
    )


def test_reference_refusal_does_not_change_an_active_sweep() -> None:
    client = WowClient()
    client.set_canonical_plan()
    client.login()
    client.fire("AUCTION_HOUSE_SHOW")
    client.slash("scan")
    before = client._json_table(client.ns.Scanner.Status())
    client.set_reference_items([1001])
    client.slash("reference")

    assert "sweep_active" in client.chat[-1]
    assert client._json_table(client.ns.Scanner.Status()) == before
    assert client.lua.globals().CrowleyDB.reference is None


def test_max_stack_one_queries_only_one_quantity() -> None:
    client = WowClient()
    client.set_auctions([Auction(1001, "Single", 1, 100, isCommodity=True, sellPrice=9)])
    reference = capture(client, [1001])
    assert reference["items"]["1001"]["info"]["maxStack"] == 1
    assert reference["items"]["1001"]["deposit"]["values"] == [
        {"duration": duration, "quantity": 1, "copper": 9 * duration} for duration in (1, 2, 3)
    ]
    assert [(call["duration"], call["quantity"]) for call in client.deposit_calls] == [
        (1, 1),
        (2, 1),
        (3, 1),
    ]


def test_deposit_errors_and_mixed_returns_are_recorded_as_contract_errors() -> None:
    error = WowClient()
    error.set_auctions([Auction(1001, "Commodity", 20, 100, isCommodity=True)])
    error.set_deposit_error(1001, "native failure")
    error_reference = capture(error, [1001])
    assert error_reference["items"]["1001"]["deposit"] == {"kind": "error", "detail": "string"}

    raised = WowClient()
    raised.set_auctions([Auction(1001, "Commodity", 20, 100, isCommodity=True)])
    raised.set_deposit_raise(1001, "native failure")
    raised_reference = capture(raised, [1001])
    assert raised_reference["items"]["1001"]["deposit"] == {"kind": "error", "detail": "error"}

    mixed = WowClient()
    mixed.set_auctions([Auction(1001, "Commodity", 20, 100, isCommodity=True)])
    mixed.state.depositReturns[1001] = mixed._to_lua({1: {1: "bad"}})
    mixed_reference = capture(mixed, [1001])
    assert mixed_reference["items"]["1001"]["deposit"] == {"kind": "error", "detail": "string"}


def test_empty_reference_list_is_refused_before_saved_variables_change() -> None:
    client = WowClient()
    client.set_reference_items([])
    client.login()
    client.fire("AUCTION_HOUSE_SHOW")
    before = savedvars.loads(client.saved_variables())
    client.slash("reference")

    assert "reference_item_ids_empty" in client.chat[-1]
    assert savedvars.loads(client.saved_variables()) == before
    assert client.ns.Reference.InProgress() is False


def test_validator_rejects_empty_item_collections_in_both_wire_shapes() -> None:
    client = WowClient()
    client.set_auctions([Auction(1001, "Commodity", 20, 100, isCommodity=True)])
    valid = capture(client, [1001])
    for empty_items in ({}, []):
        malformed = deepcopy(valid)
        malformed["items"] = empty_items
        with pytest.raises(ReferenceFormatError, match="non-empty object"):
            validate_reference_envelope(malformed)


def test_invalid_native_is_recorded_and_malformed_reference_is_rejected() -> None:
    client = WowClient()
    client.set_reference_item_info(
        1001,
        {
            "name": "Bad",
            "link": "",
            "quality": -1,
            "itemLevel": 0,
            "minLevel": 0,
            "itemType": "Trade Goods",
            "itemSubType": "",
            "stackCount": 1,
            "equipLoc": "",
            "texture": 1,
            "sellPrice": 0,
            "classID": 7,
            "subclassID": 0,
            "bindType": 0,
            "expansionID": 1,
            "setID": 0,
            "isCraftingReagent": False,
        },
    )
    reference = capture(client, [1001])
    assert reference["items"]["1001"] == {"itemID": 1001, "status": "invalid_native", "field": "quality"}

    malformed = deepcopy(reference)
    malformed["items"]["1001"]["extra"] = True
    with pytest.raises(ReferenceFormatError):
        validate_reference_envelope(malformed)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("quality", 32768),
        ("bindType", 32768),
        ("itemLevel", 2147483648),
        ("minLevel", 2147483648),
        ("classID", 2147483648),
        ("subclassID", 2147483648),
        ("maxStack", 2147483648),
        ("expansionID", 2147483648),
    ],
)
def test_native_values_are_limited_to_database_storage_ranges(field: str, value: int) -> None:
    client = WowClient()
    client.set_reference_item_info(
        1001,
        {
            "name": "Bounded",
            "link": "",
            "quality": 1,
            "itemLevel": 0,
            "minLevel": 0,
            "itemType": "Trade Goods",
            "itemSubType": "",
            "stackCount": 20,
            "equipLoc": "",
            "texture": 1,
            "sellPrice": 0,
            "classID": 7,
            "subclassID": 0,
            "bindType": 0,
            "expansionID": 1,
            "setID": 0,
            "isCraftingReagent": False,
            ("stackCount" if field == "maxStack" else field): value,
        },
    )
    reference = capture(client, [1001])
    assert reference["items"]["1001"] == {"itemID": 1001, "status": "invalid_native", "field": field}


def test_validator_rejects_malformed_fields_wrong_quantities_and_house_mismatch() -> None:
    client = WowClient()
    client.set_auctions([Auction(1001, "Commodity", 20, 100, isCommodity=True)])
    valid = capture(client, [1001])

    malformed = deepcopy(valid)
    malformed["items"]["1001"]["info"]["classID"] = "7"
    with pytest.raises(ReferenceFormatError):
        validate_reference_envelope(malformed)

    wrong_quantity = deepcopy(valid)
    wrong_quantity["items"]["1001"]["deposit"]["values"][0]["quantity"] = 2
    with pytest.raises(ReferenceFormatError):
        validate_reference_envelope(wrong_quantity)

    empty_values = deepcopy(valid)
    empty_values["items"]["1001"]["deposit"]["values"] = []
    with pytest.raises(ReferenceFormatError):
        validate_reference_envelope(empty_values)

    house_mismatch = deepcopy(valid)
    house_mismatch["house"]["key"] = "us-normal-alliance"
    with pytest.raises(ReferenceFormatError):
        validate_reference_envelope(house_mismatch)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("quality", 32768),
        ("bindType", 32768),
        ("itemLevel", 2147483648),
        ("minLevel", 2147483648),
        ("classID", 2147483648),
        ("subclassID", 2147483648),
        ("maxStack", 2147483648),
        ("expansionID", 2147483648),
    ],
)
def test_validator_rejects_values_that_do_not_fit_reference_columns(field: str, value: int) -> None:
    client = WowClient()
    client.set_auctions([Auction(1001, "Commodity", 20, 100, isCommodity=True)])
    reference = capture(client, [1001])
    reference["items"]["1001"]["info"][field] = value
    with pytest.raises(ReferenceFormatError):
        validate_reference_envelope(reference)


def test_reference_refuses_without_ids_or_during_a_running_capture() -> None:
    missing = WowClient()
    missing.login()
    missing.slash("reference")
    assert "reference refused" in missing.chat[-1]

    running = WowClient()
    running.set_reference_items([1001])
    running.set_reference_load_behavior(never=[1001])
    running.login()
    running.fire("AUCTION_HOUSE_SHOW")
    running.slash("reference")
    running.slash("reference")
    assert "capture_running" in running.chat[-1]
