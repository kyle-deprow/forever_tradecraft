"""API tests against a real TimescaleDB. Skipped unless CROWLEY_TEST_DATABASE_URL is set, e.g.

docker compose -f deploy/docker-compose.yml exec db createdb -U crowley crowley_test
CROWLEY_TEST_DATABASE_URL=postgresql://crowley:<pw>@127.0.0.1:5432/crowley_test uv run pytest
"""

import os
import time

import psycopg
import pytest
from fastapi.testclient import TestClient

from crowley.core.scanformat import encode_rows

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


def scan(uid, faction, ruleset="normal", price=100, at=None):
    at = at or int(time.time())
    return {
        "id": uid,
        "format": 1,
        "startedAt": at - 10,
        "finishedAt": at,
        "numRows": 1,
        "skipped": 0,
        "house": {"region": "us", "ruleset": ruleset, "faction": faction, "source": "auto"},
        "context": {"character": "Tester", "clientBuild": "70338", "interface": 16001},
        "rows": encode_rows(f"2589,2589,10,{price * 10},0,0,4,Seller"),
        "items": {"2589": {"n": "Linen Cloth", "q": 1, "l": 1}},
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

    def latest_min(key):
        return client.get(f"/v1/houses/{key}/latest").json()["items"][0]["min_unit"]

    assert latest_min("us-normal-horde") == 100
    assert latest_min("us-normal-alliance") == 300
    assert latest_min("us-pvp-neutral") == 900

    history = client.get("/v1/houses/us-normal-horde/items/2589/history").json()
    assert history["item"]["name"] == "Linen Cloth"
    assert len(history["points"]) == 1


def test_uploads_are_idempotent_and_acked(client):
    assert client.post("/v1/scans", json=scan("dup", "horde")).json()["status"] == "created"
    assert client.post("/v1/scans", json=scan("dup", "horde")).json()["status"] == "duplicate"
    data = client.post("/v1/addon-data", json={"scan_ids": ["dup", "unknown"]}).json()
    assert data["ackedScans"] == ["dup"]


def test_rejects_bad_scans_and_tokens(client):
    assert client.post("/v1/scans", json={**scan("x", "horde"), "numRows": 5}).status_code == 422
    assert client.get("/v1/houses", headers={"Authorization": "Bearer nope"}).status_code == 401
    assert client.get("/v1/houses/us-normal-orcs/latest").status_code == 400
    assert client.get("/v1/houses/eu-normal-horde/latest").status_code == 404
