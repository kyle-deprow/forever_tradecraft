import pytest

from crowley.core import savedvars
from crowley.core.house import House
from crowley.core.luawriter import render_assignment, to_lua
from crowley.core.scanformat import (
    Listing,
    ScanFormatError,
    compute_stats,
    decode_rows,
    encode_rows,
    parse_scan,
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
    assert data["CrowleyDB"]["list"] == ["a", "b—c"]  # UTF-8 bytes via \ddd escapes
    assert data["CrowleyDB"]["flag"] is True
    assert data["Other"] == 31


def test_savedvars_errors_have_line_numbers():
    with pytest.raises(savedvars.SavedVariablesError, match="line 2"):
        savedvars.loads(b'X = {\n ["a"] = @ }')


def test_lua_writer_roundtrips_through_parser():
    value = {
        "generatedAt": 1760000000,
        "ackedScans": ["a", 'q"uote\n'],
        "nested": {"x": 1.5},
        "shoppingLists": [{"name": "Crowley — deals", "items": [{"name": "Linen Cloth"}]}],
    }
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


def test_rows_roundtrip_raw_deflate():
    assert decode_rows(encode_rows("1,1,1,1,0,0,1,x")) == "1,1,1,1,0,0,1,x"


def raw_scan(**overrides):
    rows = "10,10,2,300,0,0,4,A\n10,10,1,100,0,0,4,"
    scan = {
        "id": "s1",
        "format": 1,
        "startedAt": 1759999990,
        "finishedAt": 1760000000,
        "numRows": 2,
        "skipped": 0,
        "house": {"region": "us", "ruleset": "normal", "faction": "alliance", "source": "auto"},
        "context": {"character": "Tester", "clientBuild": "70338", "interface": 16001},
        "rows": encode_rows(rows),
        "items": {"10": {"n": "Thing", "q": 1, "l": 5}},
    }
    scan.update(overrides)
    return scan


def test_parse_scan_validates():
    assert len(parse_scan(raw_scan()).listings) == 2
    assert parse_scan(raw_scan(numRows=0, rows="", items={})).listings == []
    with pytest.raises(ScanFormatError, match="declares 3"):
        parse_scan(raw_scan(numRows=3))
    with pytest.raises(ScanFormatError, match="format"):
        parse_scan(raw_scan(format=2))
    with pytest.raises(ScanFormatError, match="ruleset"):
        parse_scan(raw_scan(house={"region": "us", "ruleset": "x", "faction": "horde", "source": "auto"}))
    with pytest.raises(ScanFormatError):
        parse_scan(raw_scan(rows=encode_rows("x,1,1,1,0,0,1,A"), numRows=1))


def test_stats_are_quantity_weighted():
    listings = [
        Listing(1, "1", quantity=19, buyout=19 * 100, min_bid=0, bid=0, time_left=4, owner=""),
        Listing(1, "1", quantity=1, buyout=10, min_bid=0, bid=0, time_left=4, owner=""),
        Listing(1, "1", quantity=80, buyout=80 * 500, min_bid=0, bid=0, time_left=4, owner=""),
    ]
    (stats,) = compute_stats(listings)
    assert stats.min_unit == 10
    assert stats.p10_unit == 100  # 10th unit of 100 is in the 100c stack
    assert stats.p25_unit == 500
    # cheapest 15 units: 1 @10 + 14 @100
    assert stats.market_value == pytest.approx((10 + 14 * 100) / 15)
    assert stats.total_quantity == 100 and stats.num_auctions == 3
