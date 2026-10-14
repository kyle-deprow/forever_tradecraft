"""Format-2 API tests against the temporary TimescaleDB when configured."""

import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import UTC, datetime

import psycopg
import pytest
from fastapi.testclient import TestClient

from crowley.core.scanformat import decode_json_payload, encode_json_payload

DB_URL = os.environ.get("CROWLEY_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DB_URL, reason="CROWLEY_TEST_DATABASE_URL not set")
TOKEN = "test-token"


@pytest.fixture
def client(tmp_path, monkeypatch):
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")
    monkeypatch.setenv("CROWLEY_DATABASE_URL", DB_URL)
    monkeypatch.setenv("CROWLEY_API_TOKEN", TOKEN)
    monkeypatch.setenv("CROWLEY_DATA_DIR", str(tmp_path))
    from crowley.server.app import app
    from crowley.server.config import get_settings

    get_settings.cache_clear()
    with TestClient(app, headers={"Authorization": f"Bearer {TOKEN}"}) as test_client:
        yield test_client
    get_settings.cache_clear()


def scan(uid: str, faction: str, *, ruleset: str = "normal", price: int = 100, at: int | None = None) -> dict:
    at = at or int(time.time())
    body = {
        "schemaVersion": 2,
        "id": "first-run",
        "revision": 9,
        "catalogHash": "b" * 64,
        "targetClientBuild": "1.60.1.1",
        "cadenceSeconds": 900,
        "initialPriceLevels": 20,
        "itemIDs": [2589],
        "pools": {"core": [2589], "discovery": []},
    }
    plan_json = json.dumps(body, sort_keys=True, separators=(",", ":"))
    plan_hash = hashlib.sha256(plan_json.encode()).hexdigest()
    row = {
        "resultID": 1,
        "itemID": 2589,
        "itemKey": "2589",
        "rawItemKey": {
            "itemID": 2589,
            "itemLevel": 0,
            "itemSuffix": 0,
            "battlePetSpeciesID": 0,
            "bonusIDs": {},
        },
        "link": {"kind": "unknown"},
        "quantity": 10,
        "price": {"kind": "unit", "copper": price},
        "unitPrice": {"numerator": price, "denominator": 1},
        "owners": {
            "names": {},
            "totalNumberOfOwners": 0,
            "containsOwnerItem": False,
            "containsAccountItem": False,
            "identityKind": "grouped",
        },
        "timeLeft": {"kind": "unknown"},
    }
    observation = {
        "itemID": 2589,
        "ordinal": 1,
        "kind": "commodity",
        "query": {"kind": "queried", "startedAt": at - 10, "finishedAt": at},
        "coverage": "full",
        "sourceComplete": True,
        "cutoff": {"kind": "unbounded"},
        "higherPriceWitness": {"kind": "unknown"},
        "reasonCode": "ok",
        "rowCount": 1,
        "rows": {"row:1": row},
    }
    payload = {
        "planHash": plan_hash,
        "planJSON": plan_json,
        "observations": {"2589": observation},
        "owned": {
            "status": "unqueried",
            "query": {"kind": "unqueried"},
            "reasonCode": "not_started",
            "rowCount": 0,
            "rows": {},
        },
    }
    return {
        "id": uid,
        "format": 2,
        "startedAt": at - 10,
        "finishedAt": at,
        "numRows": 1,
        "numObservations": 1,
        "house": {
            "region": "us",
            "ruleset": ruleset,
            "faction": faction,
            "source": "auto",
            "key": f"us-{ruleset}-{faction}",
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
        "payload": encode_json_payload(payload),
    }


def test_houses_are_kept_separate(client):
    now = int(time.time())
    assert (
        client.post("/v1/scans", json=scan("a", "horde", price=100, at=now - 60)).json()["status"]
        == "created"
    )
    assert (
        client.post("/v1/scans", json=scan("b", "alliance", price=300, at=now - 30)).json()["status"]
        == "created"
    )
    assert (
        client.post("/v1/scans", json=scan("c", "neutral", ruleset="pvp", price=900, at=now)).status_code
        == 200
    )
    houses = {h["key"]: h for h in client.get("/v1/houses").json()}
    assert set(houses) == {"us-normal-horde", "us-normal-alliance", "us-pvp-neutral"}
    assert houses["us-normal-horde"]["sweeps"] == 1


def test_uploads_are_idempotent_and_acked(client):
    upload = scan("dup", "horde")
    assert client.post("/v1/scans", json=upload).json()["status"] == "created"
    assert client.post("/v1/scans", json=upload).json()["status"] == "duplicate"
    data = client.post("/v1/addon-data", json={"scan_ids": ["dup", "unknown"]}).json()
    assert data["ackedScans"] == ["dup"]
    plan = client.get("/v1/scan-plan").json()
    assert plan["schemaVersion"] == 2
    assert plan["planHash"] and plan["planJSON"]


def test_v1_and_malformed_v2_are_rejected(client):
    old = {"id": "old", "format": 1}
    assert client.post("/v1/scans", json=old).status_code == 422
    bad = scan("bad", "horde")
    bad["numRows"] = 2
    assert client.post("/v1/scans", json=bad).status_code == 422
    assert client.get("/v1/houses", headers={"Authorization": "Bearer nope"}).status_code == 401
    assert client.get("/v1/houses/us-normal-orcs/latest").status_code == 400


def test_volume_route_uses_market_rows_only(client):
    now = int(time.time())
    assert client.post("/v1/scans", json=scan("v1", "horde", at=now - 30)).status_code == 200
    assert client.post("/v1/scans", json=scan("v2", "horde", price=120, at=now)).status_code == 200
    response = client.get("/v1/houses/us-normal-horde/items/2589/volume?hours=24")
    assert response.status_code == 200
    body = response.json()
    assert body["intervals"][0]["kind"] == "commodity"
    assert body["marketActualSalesEstimate"] is None


def test_real_addon_envelope_reaches_archive_history_and_volume(client):
    from .test_addon import envelope, run_sweep
    from .wow_harness import WowClient

    addon = WowClient()
    # The harness clock starts in a fixed historical fixture epoch.  Advance it
    # into the API's 168-hour volume window before producing SavedVariables.
    addon.advance(365 * 24 * 60 * 60)
    raw = run_sweep(addon)
    response = client.post("/v1/scans", json=envelope(raw))
    assert response.status_code == 200, response.text

    history_response = client.get("/v1/houses/us-normal-horde/items/2589/history?days=365")
    assert history_response.status_code == 200, history_response.text
    history = history_response.json()
    assert len(history["observations"]) == 1
    assert history["observations"][0]["observation"]["rows"]
    volume_response = client.get("/v1/houses/us-normal-horde/items/2589/volume?hours=168")
    assert volume_response.status_code == 200, volume_response.text
    volume = volume_response.json()
    assert volume["latestObservation"]["itemID"] == 2589
    assert volume["marketActualSalesEstimate"] is None


def test_upload_rejects_duplicate_outer_json_keys_before_archive(client):
    body = json.dumps(scan("duplicate-key", "horde"), separators=(",", ":"))
    body = body.replace('"id":"duplicate-key"', '"id":"duplicate-key","id":"other"', 1)
    response = client.post("/v1/scans", content=body, headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert client.get("/v1/houses").json() == []


def test_uid_conflict_including_changed_payload_is_409(client):
    assert client.post("/v1/scans", json=scan("same-uid", "horde", price=100)).status_code == 200
    changed = scan("same-uid", "horde", price=101)
    response = client.post("/v1/scans", json=changed)
    assert response.status_code == 409
    houses = client.get("/v1/houses").json()
    assert houses[0]["sweeps"] == 1


def test_variant_history_projects_exact_canonical_rows(client):
    now = int(time.time())
    base = scan("base-variant", "horde", at=now - 60)
    variant = scan("level-variant", "horde", at=now - 30)
    decoded = decode_json_payload(variant["payload"])
    row = decoded["observations"]["2589"]["rows"]["row:1"]
    row["rawItemKey"] = dict(row["rawItemKey"], itemLevel=17)
    row["itemKey"] = "2589:l17"
    variant["payload"] = encode_json_payload(decoded)
    assert client.post("/v1/scans", json=base).status_code == 200
    assert client.post("/v1/scans", json=variant).status_code == 200

    plain = client.get("/v1/houses/us-normal-horde/items/2589/history?days=365").json()
    level = client.get("/v1/houses/us-normal-horde/items/2589:l17/history?days=365").json()
    assert [len(entry["observation"]["rows"]) for entry in plain["observations"]] == [1, 0]
    assert [len(entry["observation"]["rows"]) for entry in level["observations"]] == [0, 1]


def test_variant_projection_sorts_numeric_jsonb_row_ordinals(client):
    raw = scan("numeric-rows", "horde")
    decoded = decode_json_payload(raw["payload"])
    observation = decoded["observations"]["2589"]
    template = observation["rows"]["row:1"]
    rows = {}
    variant_rows = {2, 10, 12}
    for index in range(1, 13):
        row = deepcopy(template)
        row["resultID"] = index
        row["price"] = {"kind": "unit", "copper": index * 10}
        row["unitPrice"] = {"numerator": index * 10, "denominator": 1}
        if index in variant_rows:
            row["rawItemKey"] = dict(row["rawItemKey"], itemLevel=17)
            row["itemKey"] = "2589:l17"
        rows[f"row:{index}"] = row
    observation["rows"] = rows
    observation["rowCount"] = len(rows)
    raw["numRows"] = len(rows)
    raw["payload"] = encode_json_payload(decoded)
    response = client.post("/v1/scans", json=raw)
    assert response.status_code == 200, response.text

    history = client.get("/v1/houses/us-normal-horde/items/2589:l17/history?days=365").json()
    projected = history["observations"][0]["observation"]
    assert list(projected["rows"]) == ["row:1", "row:2", "row:3"]
    assert [row["unitPrice"]["numerator"] for row in projected["rows"].values()] == [20, 100, 120]
    volume = client.get("/v1/houses/us-normal-horde/items/2589:l17/volume?hours=24").json()
    latest = volume["latestObservation"]
    assert [row["unitPrice"]["numerator"] for row in latest["rows"].values()] == [20, 100, 120]


def test_owned_sold_uses_owned_window_and_excludes_inconsistent_evidence(client):
    link = "item:2589:0:0:0:0:0:0:0:0:0:0:0:0"

    def owned(raw: dict, auction_id: int, quantity: int, *, earlier: int) -> dict:
        decoded = decode_json_payload(raw["payload"])
        decoded["owned"] = {
            "status": "full",
            "query": {"kind": "queried", "startedAt": earlier - 4, "finishedAt": earlier - 2},
            "reasonCode": "ok",
            "rowCount": 1,
            "rows": {
                str(auction_id): {
                    "auctionID": auction_id,
                    "itemID": 2589,
                    "itemKey": "2589",
                    "rawItemKey": {
                        "itemID": 2589,
                        "itemLevel": 0,
                        "itemSuffix": 0,
                        "battlePetSpeciesID": 0,
                        "bonusIDs": {},
                    },
                    "itemLink": link,
                    "quantity": quantity,
                    "buyout": {"kind": "known", "copper": 100},
                    "status": "sold",
                }
            },
        }
        raw["payload"] = encode_json_payload(decoded)
        return raw

    now = int(time.time())
    first = owned(scan("owned-first", "horde", at=now - 10), 77, 2, earlier=now - 15)
    second = owned(scan("owned-earlier", "horde", at=now - 30), 77, 3, earlier=now - 35)
    response = client.post("/v1/scans", json=first)
    assert response.status_code == 200, response.text
    assert client.post("/v1/scans", json=second).status_code == 200
    report = client.get("/v1/houses/us-normal-horde/items/2589/volume?hours=24").json()
    assert report["ownConfirmed"]["units"] == 0
    assert report["ownConfirmed"]["evidence"][0]["inconsistent"] is True
    assert report["ownConfirmed"]["evidence"][0]["observation_window"]["finishedAt"] == now - 37


def test_concurrent_connections_claim_one_uid_and_archive(client):
    from crowley.server.config import get_settings
    from crowley.server.ingest import SweepConflictError, ingest_market_sweep

    raw = scan("concurrent", "horde")
    data_dir = get_settings().data_dir

    def ingest(raw_upload: dict) -> str:
        with psycopg.connect(DB_URL) as conn:
            try:
                return ingest_market_sweep(conn, raw_upload, data_dir).status
            except SweepConflictError:
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(ingest, [raw, raw]))
    assert sorted(statuses) == ["created", "duplicate"]

    changed = scan("concurrent-conflict", "horde", price=100)
    changed_copy = scan("concurrent-conflict", "horde", price=101)
    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(ingest, [changed, changed_copy]))
    assert sorted(statuses) == ["conflict", "created"]
    with psycopg.connect(DB_URL) as conn:
        assert conn.execute("SELECT count(*) FROM market_sweeps").fetchone()[0] == 2
    archives = list(data_dir.glob("raw/format2/*/*.json.gz"))
    assert len(archives) == 2
    assert all(archive.parent.parent == data_dir / "raw" / "format2" for archive in archives)


def test_legacy_uid_collision_is_409(client):
    from crowley.core.house import House

    raw = scan("legacy-uid", "horde")
    at = datetime.fromtimestamp(raw["finishedAt"], tz=UTC)
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        house = House("us", "normal", "horde")
        house_id = conn.execute(
            "INSERT INTO houses (key, region, ruleset, faction) VALUES (%s,%s,%s,%s) RETURNING id",
            (house.key, house.region, house.ruleset, house.faction),
        ).fetchone()[0]
        conn.execute(
            """
            INSERT INTO scans
              (scan_uid, house_id, house_source, started_at, scanned_at, character,
               client_build, interface, num_listings, num_items, skipped, context, raw_path)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                raw["id"],
                house_id,
                "auto",
                at,
                at,
                "Legacy",
                "old",
                16001,
                0,
                0,
                0,
                json.dumps({}),
                "legacy.json.gz",
            ),
        )
    assert client.post("/v1/scans", json=raw).status_code == 409


def test_unstorable_timestamp_is_422_without_archive(client):
    from crowley.server.config import get_settings

    raw = scan("bad-time", "horde")
    raw["finishedAt"] = 10**12
    response = client.post("/v1/scans", json=raw)
    assert response.status_code == 422
    assert list(get_settings().data_dir.rglob("*.gz")) == []


def test_database_rollback_leaves_no_sweep_reference(monkeypatch, client):
    from crowley.server import ingest as ingest_module
    from crowley.server.config import get_settings

    raw = scan("rollback", "horde")
    data_dir = get_settings().data_dir

    def fail(*args, **kwargs):
        raise RuntimeError("forced test rollback")

    monkeypatch.setattr(ingest_module, "_insert_owned", fail)
    with psycopg.connect(DB_URL) as conn:
        with pytest.raises(RuntimeError, match="forced test rollback"):
            ingest_module.ingest_market_sweep(conn, raw, data_dir)
        assert conn.execute("SELECT count(*) FROM market_sweeps").fetchone()[0] == 0
    # The immutable archive may be left unreferenced after a DB rollback; it is
    # not committed evidence because no sweep points at it.
    archives = list(data_dir.glob("raw/format2/*/*.json.gz"))
    assert len(archives) == 1


def test_uid_path_is_content_addressed(client):
    from crowley.server.config import get_settings

    raw = scan("../../outside/raw", "horde")
    assert client.post("/v1/scans", json=raw).status_code == 200
    data_dir = get_settings().data_dir
    archives = list(data_dir.glob("raw/format2/*/*.json.gz"))
    assert len(archives) == 1
    assert archives[0].resolve().is_relative_to(data_dir.resolve())
