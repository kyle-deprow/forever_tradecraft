from __future__ import annotations

import hmac
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from psycopg.rows import dict_row
from pydantic import BaseModel

from crowley.core.house import House
from crowley.core.scanformat import ScanFormatError

from .config import ServerSettings, get_settings
from .db import create_pool, migrate
from .ingest import ingest_scan

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
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
def upload_scan(raw: dict[str, Any], request: Request, settings: Settings) -> dict[str, Any]:
    """Body: one CrowleyDB.scans entry, as the companion parsed it from SavedVariables."""
    with request.app.state.pool.connection() as conn:
        try:
            result = ingest_scan(conn, raw, settings.data_dir)
        except ScanFormatError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
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
                   count(s.id) AS scans, max(s.scanned_at) AS last_scan_at,
                   (SELECT num_listings FROM scans
                     WHERE house_id = h.id ORDER BY scanned_at DESC LIMIT 1) AS last_scan_listings
            FROM houses h LEFT JOIN scans s ON s.house_id = h.id
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
    """Item stats from the most recent scan of a house."""
    with request.app.state.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        house_id = _house_id(conn, key)
        scan = cur.execute(
            "SELECT id, scan_uid, scanned_at, num_listings FROM scans"
            " WHERE house_id = %s ORDER BY scanned_at DESC LIMIT 1",
            (house_id,),
        ).fetchone()
        if not scan:
            raise HTTPException(status_code=404, detail="house has no scans")
        rows = cur.execute(
            """
            SELECT st.item_key, st.item_id, i.name, i.quality, st.num_auctions, st.total_quantity,
                   st.min_unit, st.p25_unit, st.median_unit, st.market_value
            FROM item_stats st JOIN items i USING (item_key)
            WHERE st.scan_id = %s AND st.scanned_at = %s
              AND (%s::text IS NULL OR i.name ILIKE '%%' || %s || '%%')
            ORDER BY st.total_quantity DESC
            LIMIT %s
            """,
            (scan["id"], scan["scanned_at"], search, search, limit),
        ).fetchall()
    return {"house": key, "scan": scan, "items": rows}


@app.get("/v1/houses/{key}/items/{item_key}/history", dependencies=[Authed])
def item_history(
    key: str, item_key: str, request: Request, days: int = Query(default=7, le=365)
) -> dict[str, Any]:
    since = datetime.now(UTC) - timedelta(days=days)
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
    return {"house": key, "item": item, "points": points}


class AddonDataRequest(BaseModel):
    # Scan ids currently sitting in the player's SavedVariables.
    scan_ids: list[str] = []


@app.post("/v1/addon-data", dependencies=[Authed])
def addon_data(body: AddonDataRequest, request: Request) -> dict[str, Any]:
    """Everything the companion writes into Crowley_Data/Data.lua."""
    acked: list[str] = []
    if body.scan_ids:
        with request.app.state.pool.connection() as conn:
            acked = [
                row[0]
                for row in conn.execute(
                    "SELECT scan_uid FROM scans WHERE scan_uid = ANY(%s)", (body.scan_ids,)
                )
            ]
    return {
        "generatedAt": int(time.time()),
        "ackedScans": sorted(acked),
        # Filled by the strategy engine in a later phase.
        "shoppingLists": [],
    }
