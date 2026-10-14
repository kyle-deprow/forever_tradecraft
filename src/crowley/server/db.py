from __future__ import annotations

import logging
from importlib import resources

import psycopg
from psycopg_pool import ConnectionPool

log = logging.getLogger(__name__)


def create_pool(database_url: str) -> ConnectionPool:
    pool = ConnectionPool(database_url, min_size=1, max_size=8, open=False)
    pool.open(wait=True, timeout=30)
    return pool


def migrate(conn: psycopg.Connection) -> list[str]:
    """Apply pending migrations/*.sql in filename order. Returns the names applied."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        " name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
    )
    applied = {row[0] for row in conn.execute("SELECT name FROM schema_migrations")}
    files = sorted(
        (f for f in resources.files("crowley.server.migrations").iterdir() if f.name.endswith(".sql")),
        key=lambda f: f.name,
    )
    newly = []
    for file in files:
        if file.name in applied:
            continue
        log.info("applying migration %s", file.name)
        with conn.transaction():
            conn.execute(file.read_text())
            conn.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (file.name,))
        newly.append(file.name)
    return newly
