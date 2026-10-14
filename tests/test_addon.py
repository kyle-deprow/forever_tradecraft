"""End-to-end: real addon Lua -> SavedVariables text -> Python parser -> scan decoding."""

from crowley.core import savedvars
from crowley.core.scanformat import compute_stats, parse_scan

from .wow_harness import Auction, WowClient

AUCTIONS = [
    Auction(itemID=2589, name="Linen Cloth", count=20, buyout=2000, owner="Bob"),
    Auction(itemID=2589, name="Linen Cloth", count=10, buyout=1500, owner=""),
    Auction(
        itemID=15500,
        name="Cutthroat's Belt of the Bear",
        count=1,
        buyout=0,
        minBid=5000,
        link="|cff1eff00|Hitem:15500::::::-1188:12345:60:::::::::|h[Cutthroat's Belt of the Bear]|h|r",
        quality=2,
        level=20,
        timeLeft=0,
    ),
    Auction(
        itemID=19019,
        name="Thunderfury",
        count=1,
        buyout=99990000,
        link="|Hitem:19019::::::::60::::2:6655:1700|h[Thunderfury]|h",
    ),
    # Item data not cached on first read; resolves after RequestLoadItemDataByID.
    Auction(itemID=2592, name="Wool Cloth", count=5, buyout=1000, hasAllInfo=False),
    # The server sometimes returns auctions for items that don't exist.
    Auction(itemID=999999, name="", count=1, buyout=1),
]


def open_ah(client: WowClient) -> None:
    client.login()
    client.fire("AUCTION_HOUSE_SHOW")


def run_scan(client: WowClient) -> dict:
    open_ah(client)
    client.set_auctions(AUCTIONS)
    client.slash("scan")
    client.fire("REPLICATE_ITEM_LIST_UPDATE")
    client.run_timers()
    scans = savedvars.loads(client.saved_variables())["CrowleyDB"]["scans"]
    assert len(scans) == 1
    return next(iter(scans.values()))


def test_scan_roundtrip():
    scan = parse_scan(run_scan(WowClient()))
    assert scan.house.key == "us-normal-horde"
    assert scan.skipped == 1
    assert len(scan.listings) == 5

    by_key = {}
    for listing in scan.listings:
        by_key.setdefault(listing.item_key, []).append(listing)
    assert set(by_key) == {"2589", "15500:s-1188", "19019:b1700.6655", "2592"}

    belt = by_key["15500:s-1188"][0]
    assert belt.buyout == 0 and belt.min_bid == 5000
    assert belt.time_left == 1  # replicate band 0 stored as 1
    assert scan.items["15500:s-1188"].name == "Cutthroat's Belt of the Bear"
    assert {lst.owner for lst in by_key["2589"]} == {"Bob", ""}

    stats = {s.item_key: s for s in compute_stats(scan.listings)}
    assert stats["2589"].min_unit == 100  # 2000c / 20 units
    assert stats["2589"].total_quantity == 30
    assert stats["15500:s-1188"].min_unit is None


def test_house_override_and_neutral_detection():
    client = WowClient(zone="Stranglethorn Vale", subzone="Booty Bay", realm="PvP")
    open_ah(client)
    assert "us-pvp-neutral" in client.chat[-1]

    client.slash("set ruleset hardcore")
    client.slash("set faction alliance")
    assert "us-hardcore-alliance" in client.chat[-1]
    client.slash("set faction auto")
    assert "us-hardcore-neutral" in client.chat[-1]
    client.slash("set faction goblins")
    assert "must be one of" in client.chat[-1]


def test_cooldown_blocks_second_scan_and_acks_prune():
    client = WowClient()
    run_scan(client)
    client.slash("scan")
    assert "cooldown" in client.chat[-1]

    # The companion acks the scan through Crowley_Data, then the player reloads.
    scan_id = next(iter(client.lua.globals().CrowleyDB.scans.keys()))
    client.lua.execute(f'CROWLEY_DATA.ackedScans = {{ "{scan_id}" }}')
    client.login()
    assert len(list(client.lua.globals().CrowleyDB.scans.keys())) == 0


def test_scan_aborts_when_ah_closes():
    client = WowClient()
    open_ah(client)
    client.set_auctions(AUCTIONS)
    client.slash("scan")
    client.fire("AUCTION_HOUSE_CLOSED")
    client.fire("REPLICATE_ITEM_LIST_UPDATE")
    client.run_timers()
    assert len(list(client.lua.globals().CrowleyDB.scans.keys())) == 0
    assert "scan aborted: auction house closed" in client.chat[-1]


def test_shopping_lists_sync_for_current_house_once():
    client = WowClient()
    client.lua.execute("""
        CROWLEY_DATA = { generatedAt = 1760000000, ackedScans = {}, shoppingLists = {
          { name = "Crowley deals", house = "us-normal-horde",
            items = { { name = "Linen Cloth", maxPrice = 12500, quantity = 200 } } },
          { name = "Other house", house = "us-pvp-alliance", items = {} },
        } }
    """)
    open_ah(client)
    assert client.shopping_lists == {"Crowley deals": ['"Linen Cloth";;;;;;;;;1.25;;;;200']}

    client.lua.execute("_lists = {}")
    client.fire("AUCTION_HOUSE_SHOW")
    assert client.shopping_lists == {}  # same data generation: not re-synced


def test_probe_records_api_surface():
    client = WowClient()
    client.login()
    client.slash("probe")
    probe = savedvars.loads(client.saved_variables())["CrowleyDB"]["probe"]
    assert "ReplicateItems" in probe["namespaces"]["C_AuctionHouse"]
    assert probe["context"]["interface"] == 16001
    assert probe["house"]["key"] == "us-normal-horde"
