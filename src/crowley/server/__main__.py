"""crowley-server: run the API (default) or apply migrations."""

from __future__ import annotations

import argparse
import logging

import psycopg
import uvicorn

from .config import get_settings
from .db import migrate


def main() -> None:
    parser = argparse.ArgumentParser(prog="crowley-server")
    parser.add_argument("command", nargs="?", default="serve", choices=["serve", "migrate"])
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = get_settings()

    if args.command == "migrate":
        with psycopg.connect(settings.database_url, autocommit=True) as conn:
            applied = migrate(conn)
        print("applied:", ", ".join(applied) if applied else "nothing (up to date)")
        return

    uvicorn.run("crowley.server.app:app", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
