import hashlib
import json

import pytest

from crowley.core import savedvars
from crowley.core.house import House
from crowley.core.luawriter import render_assignment, to_lua
from crowley.core.scanformat import (
    MAX_SAFE_INTEGER,
    ScanFormatError,
    decode_json_envelope,
    encode_json_payload,
    validate_v2_envelope,
)

WOW_STYLE = b"""
CrowleyDB = {
\t["scans"] = {
\t\t["us-pvp-horde-1-Bob-0001"] = {
\t\t\t["name"] = "line\\nbreak",
\t\t\t["n"] = -1.5e3,
\t\t},
\t},
\t["list"] = {
\t\t"a", -- [1]
\t\t"b\\226\\128\\148c", -- [2]
\t},
\t["flag"] = true,
\t["none"] = nil,
}
Other = 31
"""


def test_savedvars_parses_wow_output():
    data = savedvars.loads(WOW_STYLE)
    scan = data["CrowleyDB"]["scans"]["us-pvp-horde-1-Bob-0001"]
    assert scan["name"] == "line\nbreak"
    assert scan["n"] == -1500.0
    assert data["CrowleyDB"]["list"] == ["a", "b—c"]
    assert data["CrowleyDB"]["flag"] is True
    assert data["Other"] == 31


def test_savedvars_errors_have_line_numbers():
    with pytest.raises(savedvars.SavedVariablesError, match="line 2"):
        savedvars.loads(b'X = {\n ["a"] = @ }')


def test_lua_writer_roundtrips_through_parser():
    value = {"generatedAt": 1760000000, "ackedScans": ["a", 'q"uote\n'], "nested": {"x": 1.5}}
    text = render_assignment("CROWLEY_DATA", value, header="hello")
    assert text.isascii()
    assert savedvars.loads(text.encode())["CROWLEY_DATA"] == value
    assert to_lua(True) == "true" and to_lua(None) == "nil"


def test_house_validation():
    house = House("us", "pvp", "horde")
    assert house.key == "us-pvp-horde" and house.ah_cut == 0.05
    assert House.parse("eu-normal-neutral").ah_cut == 0.15
    with pytest.raises(ValueError, match="ruleset"):
        House("us", "roleplay", "horde")
    with pytest.raises(ValueError):
        House.parse("us-normal")


def _plan(item_ids: list[int] | None = None) -> tuple[str, str]:
    item_ids = item_ids or [10]
    body = {
        "schemaVersion": 2,
        "id": "first-run",
        "revision": 1,
        "catalogHash": "a" * 64,
        "targetClientBuild": "1.60.1.1",
        "cadenceSeconds": 900,
        "initialPriceLevels": 20,
        "itemIDs": item_ids,
        "pools": {"core": item_ids, "discovery": []},
    }
    text = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return text, hashlib.sha256(text.encode()).hexdigest()


def raw_scan(**overrides):
    plan_json, plan_hash = _plan()
    observation = {
        "itemID": 10,
        "ordinal": 1,
        "kind": "commodity",
        "query": {"kind": "queried", "startedAt": 1759999990, "finishedAt": 1760000000},
        "coverage": "full",
        "sourceComplete": True,
        "cutoff": {"kind": "unbounded"},
        "higherPriceWitness": {"kind": "unknown"},
        "reasonCode": "ok",
        "rowCount": 1,
        "rows": {
            "row:1": {
                "resultID": 1,
                "itemID": 10,
                "itemKey": "10",
                "rawItemKey": {
                    "itemID": 10,
                    "itemLevel": 0,
                    "itemSuffix": 0,
                    "battlePetSpeciesID": 0,
                    "bonusIDs": {},
                },
                "link": {"kind": "unknown"},
                "quantity": 2,
                "price": {"kind": "unit", "copper": 300},
                "unitPrice": {"numerator": 300, "denominator": 1},
                "owners": {
                    "names": {},
                    "totalNumberOfOwners": 0,
                    "containsOwnerItem": False,
                    "containsAccountItem": False,
                    "identityKind": "grouped",
                },
                "timeLeft": {"kind": "unknown"},
            }
        },
    }
    raw = {
        "id": "s1",
        "format": 2,
        "startedAt": 1759999990,
        "finishedAt": 1760000000,
        "numRows": 1,
        "numObservations": 1,
        "house": {
            "region": "us",
            "ruleset": "normal",
            "faction": "alliance",
            "source": "auto",
            "key": "us-normal-alliance",
        },
        "context": {
            "character": "Tester",
            "realm": "Normal",
            "playerFaction": "Alliance",
            "zone": "Orgrimmar",
            "subzone": "",
            "locale": "enUS",
            "clientVersion": "1.60.1",
            "clientBuild": "70338",
            "interface": 16001,
            "addonVersion": "0.2.0",
        },
        "payload": encode_json_payload(
            {
                "planHash": plan_hash,
                "planJSON": plan_json,
                "observations": {"10": observation},
                "owned": {
                    "status": "unqueried",
                    "query": {"kind": "unqueried"},
                    "reasonCode": "not_started",
                    "rowCount": 0,
                    "rows": {},
                },
            }
        ),
    }
    raw.update(overrides)
    return raw


def test_format2_validates_exact_payload_and_counts():
    parsed = validate_v2_envelope(raw_scan())
    assert parsed["plan"]["cadenceSeconds"] == 900
    assert parsed["decoded"]["observations"]["10"]["rowCount"] == 1


def test_format2_rejects_old_format_and_malformed_scope():
    with pytest.raises(ScanFormatError, match="format 2"):
        validate_v2_envelope(raw_scan(format=1))
    malformed = raw_scan(numRows=2)
    with pytest.raises(ScanFormatError, match="counts"):
        validate_v2_envelope(malformed)


def test_format2_rejects_fraction_not_reduced_and_unknown_fields():
    raw = raw_scan()
    decoded = validate_v2_envelope(raw)["decoded"]
    row = decoded["observations"]["10"]["rows"]["row:1"]
    row["unitPrice"] = {"numerator": 2, "denominator": 2}
    raw["payload"] = encode_json_payload(decoded)
    with pytest.raises(ScanFormatError, match="not reduced"):
        validate_v2_envelope(raw)


def test_outer_json_decoder_rejects_duplicate_keys():
    with pytest.raises(ScanFormatError, match="duplicate"):
        decode_json_envelope('{"id":"a","id":"b"}')


def test_unqueried_abort_tail_preserves_reason_and_invariants():
    raw = raw_scan()
    plan_json, plan_hash = _plan([10, 11])
    payload = validate_v2_envelope(raw)["decoded"]
    payload["planJSON"] = plan_json
    payload["planHash"] = plan_hash
    payload["observations"]["10"]["ordinal"] = 1
    payload["observations"]["11"] = {
        "itemID": 11,
        "ordinal": 2,
        "kind": "unknown",
        "query": {"kind": "unqueried"},
        "coverage": "unqueried",
        "sourceComplete": False,
        "cutoff": {"kind": "unknown"},
        "higherPriceWitness": {"kind": "unknown"},
        "reasonCode": "logout",
        "rowCount": 0,
        "rows": {},
    }
    raw["numObservations"] = 2
    raw["payload"] = encode_json_payload(payload)
    assert validate_v2_envelope(raw)["decoded"]["observations"]["11"]["reasonCode"] == "logout"


def test_full_depth_over_plan_is_rejected():
    raw = raw_scan()
    payload = validate_v2_envelope(raw)["decoded"]
    observation = payload["observations"]["10"]
    rows = {}
    for index in range(1, 22):
        row = dict(observation["rows"]["row:1"])
        row["resultID"] = index
        row["price"] = {"kind": "unit", "copper": 100 + index}
        row["unitPrice"] = {"numerator": 100 + index, "denominator": 1}
        rows[f"row:{index}"] = row
    observation["rows"] = rows
    observation["rowCount"] = 21
    raw["numRows"] = 21
    raw["payload"] = encode_json_payload(payload)
    with pytest.raises(ScanFormatError, match="plan depth"):
        validate_v2_envelope(raw)


@pytest.mark.parametrize("field,value", [("context", None), ("startedAt", "bad"), ("numRows", None)])
def test_malformed_wire_types_raise_scan_format_error(field, value):
    raw = raw_scan(**{field: value})
    with pytest.raises(ScanFormatError):
        validate_v2_envelope(raw)


def test_item_buyout_quantity_uses_reduced_fraction_without_float_division():
    raw = raw_scan()
    payload = validate_v2_envelope(raw)["decoded"]
    observation = payload["observations"]["10"]
    observation["kind"] = "item"
    row = observation["rows"]["row:1"]
    row["link"] = {"kind": "known", "value": "|Hitem:10:0:0:0:0:0:0:0:1:0:0:0:0|h[x]|h"}
    row["quantity"] = 2
    row["price"] = {"kind": "auction", "copper": 3}
    row["unitPrice"] = {"numerator": 3, "denominator": 2}
    row["owners"] = {
        "names": {"Seller": True},
        "totalNumberOfOwners": 1,
        "containsOwnerItem": False,
        "containsAccountItem": False,
        "identityKind": "individual",
    }
    raw["payload"] = encode_json_payload(payload)
    assert validate_v2_envelope(raw)["decoded"]["observations"]["10"]["rows"]["row:1"]["unitPrice"] == {
        "numerator": 3,
        "denominator": 2,
    }


def test_numeric_range_partial_preserves_safe_fractional_rows_without_cross_product():
    raw = raw_scan()
    payload = validate_v2_envelope(raw)["decoded"]
    observation = payload["observations"]["10"]
    observation.update(
        {
            "kind": "item",
            "coverage": "incomplete",
            "sourceComplete": False,
            "cutoff": {"kind": "unknown"},
            "higherPriceWitness": {"kind": "unknown"},
            "reasonCode": "numeric_range",
        }
    )
    link = {"kind": "known", "value": "|Hitem:10:0:0:0:0:0:0:0:1:0:0:0:0|h[x]|h"}
    owners = {
        "names": {"Seller": True},
        "totalNumberOfOwners": 1,
        "containsOwnerItem": False,
        "containsAccountItem": False,
        "identityKind": "individual",
    }
    first_copper = MAX_SAFE_INTEGER
    first_quantity = MAX_SAFE_INTEGER - 1
    second_copper = MAX_SAFE_INTEGER - 1
    second_quantity = MAX_SAFE_INTEGER - 2
    observation["rows"] = {
        "row:1": {
            **observation["rows"]["row:1"],
            "resultID": 1,
            "link": link,
            "owners": owners,
            "quantity": first_quantity,
            "price": {"kind": "auction", "copper": first_copper},
            "unitPrice": {
                "numerator": first_copper,
                "denominator": first_quantity,
            },
        },
        "row:2": {
            **observation["rows"]["row:1"],
            "resultID": 2,
            "link": link,
            "owners": owners,
            "quantity": second_quantity,
            "price": {"kind": "auction", "copper": second_copper},
            "unitPrice": {
                "numerator": second_copper,
                "denominator": second_quantity,
            },
        },
    }
    observation["rowCount"] = 2
    raw["numRows"] = 2
    raw["payload"] = encode_json_payload(payload)
    parsed = validate_v2_envelope(raw)
    assert parsed["decoded"]["observations"]["10"]["reasonCode"] == "numeric_range"
    assert parsed["decoded"]["observations"]["10"]["rowCount"] == 2


def test_successful_scope_rejects_unsafe_nonadjacent_price_product():
    raw = raw_scan()
    payload = validate_v2_envelope(raw)["decoded"]
    observation = payload["observations"]["10"]
    observation["kind"] = "item"
    link = {"kind": "known", "value": "|Hitem:10:0:0:0:0:0:0:0:1:0:0:0:0|h[x]|h"}
    owners = {
        "names": {"Seller": True},
        "totalNumberOfOwners": 1,
        "containsOwnerItem": False,
        "containsAccountItem": False,
        "identityKind": "individual",
    }
    fractions = [
        (MAX_SAFE_INTEGER - 1, MAX_SAFE_INTEGER),
        (1, 1),
        (MAX_SAFE_INTEGER, MAX_SAFE_INTEGER - 1),
    ]
    rows = {}
    for index, (copper, quantity) in enumerate(fractions, 1):
        row = dict(observation["rows"]["row:1"])
        row.update(
            {
                "resultID": index,
                "link": link,
                "owners": owners,
                "quantity": quantity,
                "price": {"kind": "auction", "copper": copper},
                "unitPrice": {"numerator": copper, "denominator": quantity},
            }
        )
        rows[f"row:{index}"] = row
    observation["rows"] = rows
    observation["rowCount"] = len(rows)
    raw["numRows"] = len(rows)
    raw["payload"] = encode_json_payload(payload)
    with pytest.raises(ScanFormatError, match="unsafe"):
        validate_v2_envelope(raw)


def test_incomplete_partial_may_exceed_depth_and_preserve_unordered_rows():
    raw = raw_scan()
    payload = validate_v2_envelope(raw)["decoded"]
    observation = payload["observations"]["10"]
    observation.update(
        {
            "coverage": "incomplete",
            "sourceComplete": False,
            "cutoff": {"kind": "unknown"},
            "higherPriceWitness": {"kind": "unknown"},
            "reasonCode": "page_limit",
        }
    )
    rows = {}
    for index in range(1, 22):
        row = dict(observation["rows"]["row:1"])
        row["resultID"] = index
        row["price"] = {"kind": "unit", "copper": 1000 - index}
        row["unitPrice"] = {"numerator": 1000 - index, "denominator": 1}
        rows[f"row:{index}"] = row
    observation["rows"] = rows
    observation["rowCount"] = len(rows)
    raw["numRows"] = len(rows)
    raw["payload"] = encode_json_payload(payload)
    assert validate_v2_envelope(raw)["decoded"]["observations"]["10"]["rowCount"] == 21


def test_successful_equal_price_rows_use_numeric_ordinals_and_allow_any_tie_order():
    raw = raw_scan()
    payload = validate_v2_envelope(raw)["decoded"]
    observation = payload["observations"]["10"]
    rows = {}
    for index in range(1, 13):
        row = dict(observation["rows"]["row:1"])
        row["resultID"] = index
        rows[f"row:{index}"] = row
    observation["rows"] = rows
    observation["rowCount"] = len(rows)
    raw["numRows"] = len(rows)
    raw["payload"] = encode_json_payload(payload)
    assert validate_v2_envelope(raw)["decoded"]["observations"]["10"]["rowCount"] == 12


def test_bounded_success_requires_ok_and_exact_plan_depth():
    raw = raw_scan()
    payload = validate_v2_envelope(raw)["decoded"]
    observation = payload["observations"]["10"]
    observation.update(
        {
            "coverage": "bounded",
            "sourceComplete": False,
            "cutoff": {"kind": "price", "numerator": 20, "denominator": 1},
            "higherPriceWitness": {"kind": "known", "numerator": 21, "denominator": 1},
        }
    )
    rows = {}
    for index in range(1, 21):
        row = dict(observation["rows"]["row:1"])
        row["resultID"] = index
        row["price"] = {"kind": "unit", "copper": index}
        row["unitPrice"] = {"numerator": index, "denominator": 1}
        rows[f"row:{index}"] = row
    observation["rows"] = rows
    observation["rowCount"] = len(rows)
    raw["numRows"] = len(rows)
    raw["payload"] = encode_json_payload(payload)
    assert validate_v2_envelope(raw)["decoded"]["observations"]["10"]["coverage"] == "bounded"
    last_row = dict(rows["row:20"])
    del observation["rows"]["row:20"]
    observation["rowCount"] = 19
    raw["numRows"] = 19
    raw["payload"] = encode_json_payload(payload)
    with pytest.raises(ScanFormatError, match="bounded"):
        validate_v2_envelope(raw)
    observation["rows"]["row:20"] = last_row
    observation["rowCount"] = 20
    raw["numRows"] = 20
    observation["reasonCode"] = "page_limit"
    raw["payload"] = encode_json_payload(payload)
    with pytest.raises(ScanFormatError, match="bounded"):
        validate_v2_envelope(raw)


def test_owned_house_changed_is_an_incomplete_queried_batch():
    raw = raw_scan()
    payload = validate_v2_envelope(raw)["decoded"]
    payload["owned"] = {
        "status": "incomplete",
        "query": {"kind": "queried", "startedAt": 1759999990, "finishedAt": 1760000000},
        "reasonCode": "house_changed",
        "rowCount": 0,
        "rows": {},
    }
    raw["payload"] = encode_json_payload(payload)
    assert validate_v2_envelope(raw)["decoded"]["owned"]["reasonCode"] == "house_changed"


def test_owned_unqueried_status_requires_unqueried_query():
    raw = raw_scan()
    payload = validate_v2_envelope(raw)["decoded"]
    payload["owned"]["query"] = {"kind": "queried", "startedAt": 1759999990, "finishedAt": 1760000000}
    raw["payload"] = encode_json_payload(payload)
    with pytest.raises(ScanFormatError, match="unqueried"):
        validate_v2_envelope(raw)


def test_owned_queried_status_requires_queried_query():
    raw = raw_scan()
    payload = validate_v2_envelope(raw)["decoded"]
    payload["owned"] = {
        "status": "incomplete",
        "query": {"kind": "unqueried"},
        "reasonCode": "not_started",
        "rowCount": 0,
        "rows": {},
    }
    raw["payload"] = encode_json_payload(payload)
    with pytest.raises(ScanFormatError, match="unqueried"):
        validate_v2_envelope(raw)
