Implemented server/storage fixes in:

- `src/crowley/server/app.py`
- `src/crowley/server/ingest.py`
- `src/crowley/server/migrations/002_market_observations.sql`
- `tests/test_server.py`

Key coverage includes strict duplicate-key rejection, UID conflict/concurrency handling, atomic content-addressed archives, timestamp validation, exact variant projection, grouping preservation, owned-sale deduplication/inconsistency handling, rollback/path safety, and real Lua addon → API → history/volume integration.

Verification:

- `14 passed` server DB tests using the required temporary PostgreSQL URL
- Scoped `ruff check` passed
- Scoped `ruff format --check` passed

No unresolved server/storage issues.

Server/storage work is complete with no unfinished owned items.

Checks completed:

- DB tests: `14 passed`
- Required temporary PostgreSQL database used
- Scoped `ruff check`: passed
- Scoped `ruff format --check`: passed
- Real Lua addon → API → archive/history/volume integration: passed

DONE. Exclusive DB ownership released to parent.
