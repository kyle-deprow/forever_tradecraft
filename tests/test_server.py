"""Format-2 API tests against the temporary TimescaleDB when configured."""

import gzip
import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient

from crowley.core.scanformat import decode_json_payload, encode_json_payload, validate_envelope

DB_URL = os.environ.get("CROWLEY_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DB_URL, reason="CROWLEY_TEST_DATABASE_URL not set")
TOKEN = "test-token"


def _reset_public_schema() -> None:
    """Stop TimescaleDB jobs before replacing the disposable public schema."""

    with psycopg.connect(DB_URL, autocommit=True) as conn:
        has_timescaledb = conn.execute("SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'").fetchone()
        if has_timescaledb:
            conn.execute("SELECT _timescaledb_functions.stop_background_workers()")
            deadline = time.monotonic() + 10
            while True:
                jobs = conn.execute(
                    """
                    SELECT pid, backend_type, application_name, state, query
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                      AND pid <> pg_backend_pid()
                      AND state <> 'idle'
                      AND (
                          backend_type ILIKE '%timescaledb%'
                          OR application_name ILIKE '%timescaledb%'
                          OR query ILIKE '%_timescaledb_functions.%'
                      )
                    """
                ).fetchall()
                if not jobs:
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"TimescaleDB jobs did not stop before schema reset: {jobs!r}")
                time.sleep(0.05)
        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")


def _encode_native_payload(value: dict) -> str:
    """Encode an internal payload using WoW's empty keyed-table wire shape."""

    def native(child):
        if isinstance(child, dict):
            return {
                key: []
                if key in {"bonusIDs", "names", "rows"} and isinstance(grandchild, dict) and not grandchild
                else native(grandchild)
                for key, grandchild in child.items()
            }
        if isinstance(child, list):
            return [native(grandchild) for grandchild in child]
        return child

    return encode_json_payload(native(value))


@pytest.fixture
def client(tmp_path, monkeypatch):
    _reset_public_schema()
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
            "bonusIDs": [],
        },
        "link": {"kind": "unknown"},
        "quantity": 10,
        "price": {"kind": "unit", "copper": price},
        "unitPrice": {"numerator": price, "denominator": 1},
        "owners": {
            "names": [],
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
            "rows": [],
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
        "payload": _encode_native_payload(payload),
    }


def grouped_item_scan(uid: str, *, format: int, at: int | None = None) -> tuple[dict, dict]:
    raw = scan(uid, "horde", at=at)
    payload = decode_json_payload(raw["payload"])
    observation = payload["observations"]["2589"]
    observation["kind"] = "item"
    row = observation["rows"]["row:1"]
    row.update(
        {
            "link": {"kind": "known", "value": "|Hitem:2589:0:0:0:0:0:0:0:0:0:0:0:0|h[x]|h"},
            "quantity": 4,
            "price": {"kind": "auction", "copper": 1500},
            "unitPrice": {"numerator": 375 if format == 2 else 1500, "denominator": 1},
            "timeLeft": {"kind": "exact", "seconds": 4294967293 if format == 2 else -3},
        }
    )
    raw["format"] = format
    raw["payload"] = _encode_native_payload(payload)
    return raw, payload


def install_002_only() -> None:
    from crowley.server.db import migrate

    migration_dir = os.path.join(os.path.dirname(__file__), "..", "src", "crowley", "server", "migrations")
    _reset_public_schema()
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
        conn.execute(
            "CREATE TABLE schema_migrations (name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        for name in ("001_init.sql", "002_market_observations.sql"):
            with open(os.path.join(migration_dir, name)) as handle:
                sql = handle.read()
            if name == "001_init.sql":
                sql = sql.replace("CREATE EXTENSION IF NOT EXISTS timescaledb;\n\n", "")
            conn.execute(sql)
            conn.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (name,))
        # Keep the helper's migration import available to callers after the
        # schema is prepared; the assertion also guards this fixture's intent.
        assert migrate is not None


def insert_old_item_rows() -> tuple[dict, str, int]:
    from crowley.server.ingest import _logical_digest

    raw, payload = grouped_item_scan("migration-old", format=2, at=1_760_000_000)
    digest = _logical_digest(raw, payload)
    observation = payload["observations"]["2589"]
    row = observation["rows"]["row:1"]
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        house_id = conn.execute(
            "INSERT INTO houses (key, region, ruleset, faction) VALUES (%s,%s,%s,%s) RETURNING id",
            ("us-normal-horde", "us", "normal", "horde"),
        ).fetchone()[0]
        plan_json = json.dumps({"test": True}, sort_keys=True)
        plan_hash = "a" * 64
        conn.execute(
            "INSERT INTO market_plans (plan_hash, plan_json, plan_body) VALUES (%s,%s,%s)",
            (plan_hash, plan_json, json.dumps({"test": True})),
        )
        sweep_id = conn.execute(
            """
            INSERT INTO market_sweeps
              (sweep_uid, house_id, plan_hash, started_at, finished_at, character,
               client_version, client_build, interface, house_source, num_rows,
               num_observations, context, payload, content_digest, raw_path)
            VALUES (%s,%s,%s,to_timestamp(%s),to_timestamp(%s),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """,
            (
                raw["id"],
                house_id,
                plan_hash,
                raw["startedAt"],
                raw["finishedAt"],
                "Tester",
                "1.60.1",
                "70338",
                16001,
                "auto",
                1,
                1,
                json.dumps(raw["context"]),
                json.dumps(payload),
                digest,
                "untouched.raw.gz",
            ),
        ).fetchone()[0]
        conn.execute(
            """
            INSERT INTO market_observations
              (sweep_id, house_id, item_id, item_key, ordinal, kind, query,
               coverage, source_complete, cutoff, higher_price_witness, reason_code,
               row_count, observation)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                sweep_id,
                house_id,
                2589,
                "2589",
                1,
                "item",
                json.dumps(observation["query"]),
                observation["coverage"],
                observation["sourceComplete"],
                json.dumps(observation["cutoff"]),
                json.dumps(observation["higherPriceWitness"]),
                observation["reasonCode"],
                1,
                json.dumps(observation),
            ),
        )
        conn.execute(
            """
            INSERT INTO market_captured_rows
              (sweep_id,item_id,row_key,result_id,item_key,raw_item_key,quantity,
               unit_numerator,unit_denominator,row_data)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                sweep_id,
                2589,
                "row:1",
                row["resultID"],
                row["itemKey"],
                json.dumps(row["rawItemKey"]),
                row["quantity"],
                row["unitPrice"]["numerator"],
                row["unitPrice"]["denominator"],
                json.dumps(row),
            ),
        )
        conn.execute(
            """
            INSERT INTO owned_observations
              (sweep_id, house_id, character, status, query, reason_code, row_count, rows)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                sweep_id,
                house_id,
                "Tester",
                "unqueried",
                json.dumps({"kind": "unqueried"}),
                "not_started",
                0,
                json.dumps([]),
            ),
        )
        conn.execute(
            """
            INSERT INTO own_sale_evidence
              (house_id, character, auction_id, first_seen_sold_at, first_seen_sweep_id,
               item_id, item_key, raw_item_key, quantity, listed_buyout, item_link,
               observation_window, inconsistent)
            VALUES (%s,%s,%s,to_timestamp(%s),%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                house_id,
                "Tester",
                7001,
                1_760_000_000,
                sweep_id,
                2589,
                "2589",
                json.dumps(row["rawItemKey"]),
                row["quantity"],
                row["price"]["copper"],
                row["link"]["value"],
                json.dumps({"kind": "owned", "at": 1_760_000_000}),
                False,
            ),
        )
    return raw, digest, sweep_id


def _migration_untouched_snapshot(sweep_id: int) -> dict[str, list[tuple]]:
    with psycopg.connect(DB_URL) as conn:
        return {
            "market_sweeps": conn.execute("SELECT * FROM market_sweeps WHERE id=%s", (sweep_id,)).fetchall(),
            "market_plans": conn.execute("SELECT * FROM market_plans ORDER BY plan_hash").fetchall(),
            "owned_observations": conn.execute(
                "SELECT * FROM owned_observations WHERE sweep_id=%s", (sweep_id,)
            ).fetchall(),
            "own_sale_evidence": conn.execute(
                "SELECT * FROM own_sale_evidence WHERE first_seen_sweep_id=%s", (sweep_id,)
            ).fetchall(),
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


def test_item_reference_ingest_is_typed_idempotent_and_exposed_in_latest_view(client):
    from crowley.core.watchlist import load_catalog

    from .test_reference import capture
    from .wow_harness import Auction, WowClient

    addon = WowClient()
    addon.set_auctions([Auction(2589, "Linen Cloth", 20, 100, isCommodity=True, sellPrice=3)])
    raw = capture(addon, [2589])
    first = client.post("/v1/item-reference", json=raw)
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "created"
    duplicate = client.post("/v1/item-reference", json=raw)
    assert duplicate.status_code == 200
    assert duplicate.json()["status"] == "duplicate"

    changed = dict(raw, finishedAt=raw["finishedAt"] + 1)
    conflict = client.post("/v1/item-reference", json=changed)
    assert conflict.status_code == 409, conflict.text

    with psycopg.connect(DB_URL) as conn:
        capture_row = conn.execute(
            "SELECT client_build, ah_open, content_digest FROM item_reference_captures"
        ).fetchone()
        typed = conn.execute(
            "SELECT status, max_stack, sell_price, deposit_kind FROM item_reference"
        ).fetchone()
        deposits = conn.execute("SELECT count(*) FROM item_deposits").fetchone()[0]
    assert capture_row[:2] == ("70450", True)
    assert len(capture_row[2]) == 64
    assert typed == ("ok", 20, 3, "commodity")
    assert deposits == 6

    latest = client.get("/v1/houses/us-normal-horde/item-reference")
    assert latest.status_code == 200
    assert latest.json()["items"][0]["item_id"] == 2589
    addon_data = client.post("/v1/addon-data", json={"scan_ids": []}).json()
    assert addon_data["referenceItemIDs"] == sorted(item.item_id for item in load_catalog().items)


def test_item_reference_auth_storage_limits_and_latest_selection(client):
    from .test_reference import capture
    from .wow_harness import Auction, WowClient

    addon = WowClient()
    addon.set_auctions([Auction(2589, "Linen Cloth", 20, 100, isCommodity=True, sellPrice=3)])
    raw = capture(addon, [2589])

    assert (
        client.post(
            "/v1/item-reference",
            json=raw,
            headers={"Authorization": "Bearer nope"},
        ).status_code
        == 401
    )
    assert (
        client.get(
            "/v1/houses/us-normal-horde/item-reference",
            headers={"Authorization": "Bearer nope"},
        ).status_code
        == 401
    )

    too_large = deepcopy(raw)
    too_large["id"] = "us-normal-horde-1760000000-Tester-overflow"
    too_large["items"]["2589"]["info"]["quality"] = 32768
    assert client.post("/v1/item-reference", json=too_large).status_code == 422

    assert client.post("/v1/item-reference", json=raw).status_code == 200
    other_build = deepcopy(raw)
    other_build["id"] = "us-normal-horde-1760000001-Tester-build2"
    other_build["startedAt"] += 1
    other_build["finishedAt"] += 1
    other_build["context"]["clientBuild"] = "70451"
    assert client.post("/v1/item-reference", json=other_build).status_code == 200

    newer_not_ok = deepcopy(raw)
    newer_not_ok["id"] = "us-normal-horde-1760000002-Tester-not-ok"
    newer_not_ok["startedAt"] += 2
    newer_not_ok["finishedAt"] += 2
    newer_not_ok["items"]["2589"] = {"itemID": 2589, "status": "not_found"}
    assert client.post("/v1/item-reference", json=newer_not_ok).status_code == 200

    latest = client.get("/v1/houses/us-normal-horde/item-reference")
    assert latest.status_code == 200
    rows = latest.json()["items"]
    assert {(row["client_build"], row["status"]) for row in rows} == {
        ("70450", "ok"),
        ("70451", "ok"),
    }


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


def test_ingest_normalizes_format2_but_keeps_received_payload_and_accepts_format3(client):
    from crowley.server.ingest import _logical_digest

    format2, _ = grouped_item_scan("normalize-format2", format=2)
    response = client.post("/v1/scans", json=format2)
    assert response.status_code == 200, response.text
    with psycopg.connect(DB_URL) as conn:
        stored = conn.execute(
            "SELECT payload, content_digest, raw_path FROM market_sweeps WHERE sweep_uid=%s",
            (format2["id"],),
        ).fetchone()
        observation, captured = conn.execute(
            """
            SELECT mo.observation, mcr.row_data
            FROM market_observations mo
            JOIN market_captured_rows mcr USING (sweep_id, item_id)
            WHERE mo.sweep_id = (SELECT id FROM market_sweeps WHERE sweep_uid=%s)
            """,
            (format2["id"],),
        ).fetchone()
    received_decoded = validate_envelope(format2)["decoded"]
    assert stored[0] == received_decoded
    assert stored[1] == _logical_digest(format2, received_decoded)
    assert json.loads(gzip.open(stored[2], "rb").read()) == format2
    assert observation["rows"]["row:1"]["unitPrice"] == {"numerator": 1500, "denominator": 1}
    assert observation["rows"]["row:1"]["timeLeft"] == {"kind": "exact", "seconds": -3}
    assert captured["unitPrice"] == {"numerator": 1500, "denominator": 1}
    assert captured["timeLeft"] == {"kind": "exact", "seconds": -3}

    format3, _ = grouped_item_scan("normalize-format3", format=3)
    response = client.post("/v1/scans", json=format3)
    assert response.status_code == 200, response.text
    with psycopg.connect(DB_URL) as conn:
        stored_payload, observation, cutoff, witness, unit_numerator, unit_denominator, captured = (
            conn.execute(
                """
            SELECT ms.payload, mo.observation, mo.cutoff, mo.higher_price_witness,
                   mcr.unit_numerator, mcr.unit_denominator, mcr.row_data
            FROM market_sweeps ms
            JOIN market_observations mo ON mo.sweep_id = ms.id
            JOIN market_captured_rows mcr
              ON mcr.sweep_id = mo.sweep_id AND mcr.item_id = mo.item_id
            WHERE ms.sweep_uid=%s
            """,
                (format3["id"],),
            ).fetchone()
        )
    received = validate_envelope(format3)["decoded"]
    received_observation = received["observations"]["2589"]
    received_row = received_observation["rows"]["row:1"]
    assert stored_payload == received
    assert observation == received_observation
    assert cutoff == received_observation["cutoff"]
    assert witness == received_observation["higherPriceWitness"]
    assert (unit_numerator, unit_denominator) == (
        received_row["unitPrice"]["numerator"],
        received_row["unitPrice"]["denominator"],
    )
    assert captured == received_row


def test_migration_003_normalizes_old_rows_and_guards_invalid_data():
    from crowley.server.db import migrate

    install_002_only()
    raw, digest, sweep_id = insert_old_item_rows()
    untouched_before = _migration_untouched_snapshot(sweep_id)
    with psycopg.connect(DB_URL) as conn:
        before = conn.execute(
            "SELECT payload, content_digest, raw_path FROM market_sweeps WHERE id=%s", (sweep_id,)
        ).fetchone()
        migration_dir = Path(__file__).parents[1] / "src" / "crowley" / "server" / "migrations"
        expected_migrations = sorted(
            path.name
            for path in migration_dir.glob("*.sql")
            if path.name not in {"001_init.sql", "002_market_observations.sql"}
        )
        assert migrate(conn) == expected_migrations
        captured = conn.execute(
            "SELECT unit_numerator, unit_denominator, row_data FROM market_captured_rows WHERE sweep_id=%s",
            (sweep_id,),
        ).fetchone()
        observation = conn.execute(
            "SELECT observation FROM market_observations WHERE sweep_id=%s", (sweep_id,)
        ).fetchone()[0]
        after = conn.execute(
            "SELECT payload, content_digest, raw_path FROM market_sweeps WHERE id=%s", (sweep_id,)
        ).fetchone()
        assert migrate(conn) == []
    assert before == after
    assert untouched_before == _migration_untouched_snapshot(sweep_id)
    assert before[0] == decode_json_payload(raw["payload"])
    assert before[1] == digest
    assert captured[0:2] == (1500, 1)
    assert captured[2]["unitPrice"] == {"numerator": 1500, "denominator": 1}
    assert captured[2]["timeLeft"] == {"kind": "exact", "seconds": -3}
    assert observation["rows"]["row:1"]["unitPrice"] == {"numerator": 1500, "denominator": 1}
    assert observation["rows"]["row:1"]["timeLeft"] == {"kind": "exact", "seconds": -3}
    assert captured[2]["unitPrice"] == observation["rows"]["row:1"]["unitPrice"]

    for violation in ("bounded", "captured_time", "captured_price", "observation_time", "observation_price"):
        install_002_only()
        _, _, _ = insert_old_item_rows()
        with psycopg.connect(DB_URL, autocommit=True) as conn:
            if violation == "bounded":
                conn.execute("UPDATE market_observations SET coverage='bounded'")
            elif violation == "captured_time":
                conn.execute(
                    "UPDATE market_captured_rows SET row_data=jsonb_set(row_data, '{timeLeft,seconds}', '172801'::jsonb)"
                )
            elif violation == "captured_price":
                conn.execute(
                    "UPDATE market_captured_rows SET row_data=jsonb_set(row_data, '{price,kind}', %s::jsonb)",
                    ('"unit"',),
                )
            elif violation == "observation_time":
                conn.execute(
                    """
                    UPDATE market_observations
                    SET observation=jsonb_set(
                        observation, '{rows,row:1,timeLeft,seconds}', '172801'::jsonb
                    )
                    """
                )
            else:
                conn.execute(
                    """
                    UPDATE market_observations
                    SET observation=jsonb_set(
                        observation, '{rows,row:1,price,kind}', %s::jsonb
                    )
                    """,
                    ('"unit"',),
                )
            with pytest.raises(psycopg.Error, match="cannot normalize"):
                migrate(conn)


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
    variant["payload"] = _encode_native_payload(decoded)
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
    raw["payload"] = _encode_native_payload(decoded)
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
                        "bonusIDs": [],
                    },
                    "itemLink": link,
                    "quantity": quantity,
                    "buyout": {"kind": "known", "copper": 100},
                    "status": "sold",
                }
            },
        }
        raw["payload"] = _encode_native_payload(decoded)
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
