"""Persist decoded scans: archive the raw payload, then listings, stats and item names."""

from __future__ import annotations

import gzip
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg

from crowley.core.house import House
from crowley.core.scanformat import Scan, compute_stats, parse_scan

log = logging.getLogger(__name__)


@dataclass
class IngestResult:
    scan_uid: str
    house: str
    status: str  # created | duplicate
    listings: int
    items: int


def _ts(epoch: int) -> datetime:
    return datetime.fromtimestamp(epoch, tz=UTC)


def archive_raw(data_dir: Path, raw: dict[str, Any], scan: Scan) -> Path:
    day = _ts(scan.finished_at).strftime("%Y-%m-%d")
    path = data_dir / "raw" / scan.house.key / day / f"{scan.scan_uid}.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(raw, handle)
    return path


def ensure_house(conn: psycopg.Connection, house: House) -> int:
    row = conn.execute(
        "INSERT INTO houses (key, region, ruleset, faction) VALUES (%s, %s, %s, %s)"
        " ON CONFLICT (key) DO UPDATE SET key = EXCLUDED.key RETURNING id",
        (house.key, house.region, house.ruleset, house.faction),
    ).fetchone()
    return row[0]


def ingest_scan(conn: psycopg.Connection, raw: dict[str, Any], data_dir: Path) -> IngestResult:
    scan = parse_scan(raw)

    if conn.execute("SELECT 1 FROM scans WHERE scan_uid = %s", (scan.scan_uid,)).fetchone():
        return IngestResult(scan.scan_uid, scan.house.key, "duplicate", len(scan.listings), 0)

    stats = compute_stats(scan.listings)
    raw_path = archive_raw(data_dir, raw, scan)
    scanned_at = _ts(scan.finished_at)
    ctx = scan.context

    with conn.transaction():
        house_id = ensure_house(conn, scan.house)
        (scan_id,) = conn.execute(
            """
            INSERT INTO scans (scan_uid, house_id, house_source, started_at, scanned_at, character,
                               client_build, interface, num_listings, num_items, skipped, context,
                               raw_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                scan.scan_uid,
                house_id,
                scan.house_source,
                _ts(scan.started_at),
                scanned_at,
                ctx["character"],
                ctx["clientBuild"],
                ctx["interface"],
                len(scan.listings),
                len(stats),
                scan.skipped,
                json.dumps(ctx),
                str(raw_path),
            ),
        ).fetchone()

        with conn.cursor() as cur:
            with cur.copy(
                "COPY listings (scanned_at, house_id, scan_id, item_id, item_key, quantity,"
                " buyout, min_bid, bid, time_left, owner) FROM STDIN"
            ) as copy:
                for lst in scan.listings:
                    copy.write_row(
                        (
                            scanned_at,
                            house_id,
                            scan_id,
                            lst.item_id,
                            lst.item_key,
                            lst.quantity,
                            lst.buyout,
                            lst.min_bid,
                            lst.bid,
                            lst.time_left,
                            lst.owner,
                        )
                    )
            with cur.copy(
                "COPY item_stats (scanned_at, house_id, scan_id, item_id, item_key, num_auctions,"
                " total_quantity, buyout_quantity, min_unit, p10_unit, p25_unit, median_unit,"
                " market_value) FROM STDIN"
            ) as copy:
                for st in stats:
                    copy.write_row(
                        (
                            scanned_at,
                            house_id,
                            scan_id,
                            st.item_id,
                            st.item_key,
                            st.num_auctions,
                            st.total_quantity,
                            st.buyout_quantity,
                            st.min_unit,
                            st.p10_unit,
                            st.p25_unit,
                            st.median_unit,
                            st.market_value,
                        )
                    )

            item_ids = {lst.item_key: lst.item_id for lst in scan.listings}
            cur.executemany(
                """
                INSERT INTO items (item_key, item_id, name, quality, level, first_seen, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (item_key) DO UPDATE SET
                    name = EXCLUDED.name,
                    quality = EXCLUDED.quality,
                    level = EXCLUDED.level,
                    last_seen = GREATEST(items.last_seen, EXCLUDED.last_seen)
                """,
                [
                    (key, item_ids[key], info.name, info.quality, info.level, scanned_at, scanned_at)
                    for key, info in scan.items.items()
                ],
            )

    log.info(
        "ingested %s: %d listings, %d items into %s",
        scan.scan_uid,
        len(scan.listings),
        len(stats),
        scan.house.key,
    )
    return IngestResult(scan.scan_uid, scan.house.key, "created", len(scan.listings), len(stats))
