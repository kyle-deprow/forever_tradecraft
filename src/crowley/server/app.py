from __future__ import annotations

import hmac
import json
import logging
import re
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from psycopg.rows import dict_row
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from crowley.core.house import House
from crowley.core.scanformat import ScanFormatError
from crowley.core.volume import project_observation_variant, volume_report
from crowley.core.watchlist import load_catalog

from .config import ServerSettings, get_settings
from .db import create_pool, migrate
from .ingest import SweepConflictError, ingest_market_sweep

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    load_catalog()  # Fail at startup if the shipped plan is invalid.
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    pool = create_pool(settings.database_url)
    with pool.connection() as conn:
        applied = migrate(conn)
        if applied:
            log.info("applied migrations: %s", ", ".join(applied))
    app.state.pool = pool
    try:
        yield
    finally:
        pool.close()


app = FastAPI(title="Crowley", version="0.1.0", lifespan=lifespan)

Settings = Annotated[ServerSettings, Depends(get_settings)]


def require_token(settings: Settings, authorization: str = Header(default="")) -> None:
    expected = f"Bearer {settings.api_token.get_secret_value()}"
    if not hmac.compare_digest(authorization.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="invalid or missing bearer token")


Authed = Depends(require_token)


def _strict_json_object(body: bytes) -> dict[str, Any]:
    """Decode one upload body while rejecting duplicate keys at every depth."""

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in items:
            if key in value:
                raise ValueError("duplicate JSON object key")
            value[key] = item
        return value

    def constant(value: str) -> Any:
        raise ValueError(f"invalid JSON constant {value}")

    try:
        value = json.loads(body.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail="malformed JSON upload") from exc
    if not isinstance(value, dict):
        raise HTTPException(status_code=422, detail="upload body must be a JSON object")
    return value


def _base_item_id(item_key: str) -> int:
    match = re.fullmatch(r"([1-9][0-9]*)(?::.*)?", item_key)
    if not match:
        raise HTTPException(status_code=400, detail="item key must start with a positive item ID")
    return int(match.group(1))


def _persist_market_sweep(pool: Any, raw: dict[str, Any], data_dir: Any) -> Any:
    """Run synchronous validation, DB writes and archiving off the ASGI loop."""
    with pool.connection() as conn:
        return ingest_market_sweep(conn, raw, data_dir)


def _house_id(conn, key: str) -> int:
    try:
        house = House.parse(key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    row = conn.execute("SELECT id FROM houses WHERE key = %s", (house.key,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"no data for house {house.key}")
    return row[0]


@app.get("/healthz")
def healthz(request: Request) -> dict[str, str]:
    with request.app.state.pool.connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.post("/v1/scans", dependencies=[Authed])
async def upload_scan(request: Request, settings: Settings) -> dict[str, Any]:
    """Upload the single accepted format-2 envelope."""
    raw = _strict_json_object(await request.body())
    try:
        result = await run_in_threadpool(
            _persist_market_sweep, request.app.state.pool, raw, settings.data_dir
        )
    except ScanFormatError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SweepConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return result.__dict__


@app.post("/v1/probes", dependencies=[Authed])
def upload_probe(probe: dict[str, Any], request: Request) -> dict[str, str]:
    with request.app.state.pool.connection() as conn:
        conn.execute(
            "INSERT INTO client_probes (probed_at, probe) VALUES (%s, %s) ON CONFLICT (probed_at) DO NOTHING",
            (datetime.fromtimestamp(probe["at"], tz=UTC), json.dumps(probe)),
        )
    return {"status": "ok"}


@app.get("/v1/houses", dependencies=[Authed])
def list_houses(request: Request) -> list[dict[str, Any]]:
    with request.app.state.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            """
            SELECT h.key, h.region, h.ruleset, h.faction,
                   count(DISTINCT s.id) AS legacy_scans,
                   count(DISTINCT ms.id) AS sweeps,
                   count(DISTINCT s.id) + count(DISTINCT ms.id) AS scans,
                   greatest(max(s.scanned_at), max(ms.finished_at)) AS last_scan_at,
                   (SELECT num_listings FROM scans
                     WHERE house_id = h.id ORDER BY scanned_at DESC LIMIT 1) AS last_scan_listings
            FROM houses h LEFT JOIN scans s ON s.house_id = h.id
              LEFT JOIN market_sweeps ms ON ms.house_id = h.id
            GROUP BY h.id ORDER BY h.key
            """
        ).fetchall()


@app.get("/v1/houses/{key}/latest", dependencies=[Authed])
def latest_prices(
    key: str,
    request: Request,
    search: str | None = None,
    limit: int = Query(default=100, le=5000),
) -> dict[str, Any]:
    """Latest market observations plus a separate legacy full-scan section."""
    with request.app.state.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        house_id = _house_id(conn, key)
        scan = cur.execute(
            "SELECT id, scan_uid, scanned_at, num_listings FROM scans"
            " WHERE house_id = %s ORDER BY scanned_at DESC LIMIT 1",
            (house_id,),
        ).fetchone()
        legacy_rows = cur.execute(
            """
            SELECT st.item_key, st.item_id, i.name, i.quality, st.num_auctions, st.total_quantity,
                   st.min_unit, st.p25_unit, st.median_unit, st.market_value
            FROM item_stats st JOIN items i USING (item_key)
            WHERE st.scan_id = %s AND st.scanned_at = %s
              AND (%s::text IS NULL OR i.name ILIKE '%%' || %s || '%%')
            ORDER BY st.total_quantity DESC
            LIMIT %s
            """,
            (scan["id"], scan["scanned_at"], search, search, limit)
            if scan
            else (None, None, search, search, limit),
        ).fetchall()
        market_rows = cur.execute(
            """
            SELECT ms.sweep_uid, ms.started_at, ms.finished_at, mo.ordinal, mo.item_id,
                   mo.item_key, mo.kind, mo.coverage, mo.source_complete, mo.cutoff,
                   mo.higher_price_witness, mo.reason_code, mo.row_count, mo.observation
            FROM market_observations mo JOIN market_sweeps ms ON ms.id = mo.sweep_id
            WHERE ms.house_id = %s
              AND ms.id = (SELECT id FROM market_sweeps WHERE house_id = %s
                           ORDER BY finished_at DESC LIMIT 1)
              AND (%s::text IS NULL OR mo.item_key ILIKE '%%' || %s || '%%')
            ORDER BY ms.finished_at DESC, mo.ordinal
            LIMIT %s
            """,
            (house_id, house_id, search, search, limit),
        ).fetchall()
        latest_market = cur.execute(
            """
            SELECT sweep_uid, started_at, finished_at, plan_hash,
                   num_observations, num_rows
            FROM market_sweeps
            WHERE house_id = %s
            ORDER BY finished_at DESC LIMIT 1
            """,
            (house_id,),
        ).fetchone()
    if not scan and not latest_market:
        raise HTTPException(status_code=404, detail="house has no scans")
    return {
        "house": key,
        "scan": scan,
        "items": legacy_rows,
        "legacy_full_scan": {"scan": scan, "items": legacy_rows} if scan else None,
        "legacyPoints": legacy_rows,
        "sweep": latest_market,
        "observations": market_rows,
    }


@app.get("/v1/houses/{key}/items/{item_key}/history", dependencies=[Authed])
def item_history(
    key: str, item_key: str, request: Request, days: int = Query(default=7, le=365)
) -> dict[str, Any]:
    since = datetime.now(UTC) - timedelta(days=days)
    item_id = _base_item_id(item_key)
    with request.app.state.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        house_id = _house_id(conn, key)
        item = cur.execute(
            "SELECT item_key, item_id, name, quality, level FROM items WHERE item_key = %s",
            (item_key,),
        ).fetchone()
        points = cur.execute(
            """
            SELECT scanned_at, num_auctions, total_quantity, min_unit, p25_unit, median_unit,
                   market_value
            FROM item_stats
            WHERE house_id = %s AND item_key = %s AND scanned_at >= %s
            ORDER BY scanned_at
            """,
            (house_id, item_key, since),
        ).fetchall()
        market_rows = cur.execute(
            """
            SELECT ms.sweep_uid, ms.started_at, ms.finished_at, mo.ordinal, mo.item_id,
                   mo.item_key, mo.kind, mo.coverage, mo.source_complete, mo.cutoff,
                   mo.reason_code, mo.row_count, mo.observation
            FROM market_observations mo JOIN market_sweeps ms ON ms.id = mo.sweep_id
            WHERE mo.house_id = %s AND mo.item_id = %s AND ms.finished_at >= %s
            ORDER BY ms.started_at, mo.ordinal, ms.sweep_uid
            """,
            (house_id, item_id, since),
        ).fetchall()
    market = []
    for row in market_rows:
        projected = project_observation_variant(row["observation"], item_key)
        market.append({**row, "observation": projected, "row_count": projected["rowCount"]})
    return {
        "house": key,
        "item": item,
        "legacy_full_scan": {"points": points} if points else None,
        "legacyPoints": points,
        "observations": market,
    }


@app.get("/v1/houses/{key}/items/{item_key}/volume", dependencies=[Authed])
def item_volume(
    key: str,
    item_key: str,
    request: Request,
    hours: int = Query(default=24, ge=1, le=168),
) -> dict[str, Any]:
    since = datetime.now(UTC) - timedelta(hours=hours)
    item_id = _base_item_id(item_key)
    with request.app.state.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        house_id = _house_id(conn, key)
        rows = cur.execute(
            """
            SELECT ms.sweep_uid, ms.house_id, ms.started_at, ms.finished_at,
                   mo.item_key, ms.context, ms.plan_hash, mo.observation
            FROM market_observations mo JOIN market_sweeps ms ON ms.id = mo.sweep_id
            WHERE ms.house_id = %s AND mo.item_id = %s
            ORDER BY ms.started_at, (mo.observation->>'ordinal')::int, ms.sweep_uid
            """,
            (house_id, item_id),
        ).fetchall()
        own_sales = cur.execute(
            """
            SELECT auction_id, character, first_seen_sold_at, quantity, listed_buyout,
                   item_id, item_key, raw_item_key, observation_window, inconsistent
            FROM own_sale_evidence
            WHERE house_id = %s AND item_id = %s AND first_seen_sold_at >= %s
            ORDER BY first_seen_sold_at
            """,
            (house_id, item_id, since),
        ).fetchall()
    records = []
    for row in rows:
        # Keep the complete base-item scope for grouping and persistent-ID
        # checks.  volume_report applies the exact variant filter while it
        # still sees grouped rows and variants outside the requested prefix.
        observation = row["observation"]
        records.append(
            {
                "observation": observation,
                "envelope": {
                    "house": {"key": key},
                    "itemKey": item_key,
                    "context": row["context"],
                    "planHash": row["plan_hash"],
                    "startedAt": int(row["started_at"].timestamp()),
                    "finishedAt": int(row["finished_at"].timestamp()),
                    "sweepStart": int(row["started_at"].timestamp()),
                    "ordinal": observation["ordinal"],
                    "sweep_uid": row["sweep_uid"],
                },
            }
        )
    own_sales = [row for row in own_sales if row["item_key"] == item_key]
    report = volume_report(records, hours=hours, end=int(time.time()), item_key=item_key)
    report["house"] = key
    report["itemKey"] = item_key
    report["normalizationPolicy"] = "format2-whole-buyout-quantity-reduced-rational"
    report["ownConfirmed"] = {
        "units": sum(row["quantity"] for row in own_sales if not row["inconsistent"]),
        "evidence": own_sales,
        "executionTimeKnown": False,
    }
    return report


class AddonDataRequest(BaseModel):
    # Scan ids currently sitting in the player's SavedVariables.
    scan_ids: list[str] = []


@app.get("/v1/scan-plan", dependencies=[Authed])
def scan_plan() -> dict[str, Any]:
    return load_catalog().scan_plan()


@app.post("/v1/addon-data", dependencies=[Authed])
def addon_data(body: AddonDataRequest, request: Request) -> dict[str, Any]:
    """Everything the companion writes into Crowley_Data/Data.lua."""
    acked: list[str] = []
    if body.scan_ids:
        with request.app.state.pool.connection() as conn:
            acked = [
                row[0]
                for row in conn.execute(
                    """
                    SELECT scan_uid FROM scans WHERE scan_uid = ANY(%s)
                    UNION
                    SELECT sweep_uid FROM market_sweeps WHERE sweep_uid = ANY(%s)
                    """,
                    (body.scan_ids, body.scan_ids),
                )
            ]
    return {
        "generatedAt": int(time.time()),
        "ackedScans": sorted(acked),
        "scanPlan": load_catalog().scan_plan(),
        # Filled by the strategy engine in a later phase.
        "shoppingLists": [],
    }
