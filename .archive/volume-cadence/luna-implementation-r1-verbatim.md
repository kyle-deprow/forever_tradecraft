Implemented the approved Luna scope.

- Strict format-2-only schema and historical plan validation.
- Targeted 900-second Lua sweeps with bounded depth, rational pricing, commodity handling, fair cursor rotation, throttling, owned evidence, and safe six-sweep backpressure.
- Additive market schema, atomic/content-addressed ingest, market-only volume API, conservative churn inference, and sold-evidence deduplication.
- Updated harness, tests, README, WATCHLIST, ARCHITECTURE, and HANDOFF, including the coordinated legacy flush/cutover procedure and payload-size measurement.
- Removed the retained v1 decoder.

Verification:

- Ruff check and format check passed.
- Exact DB test command: `36 passed, 1 warning`.
- Wheel build passed; packaged `volume.py` and `first_run.json` verified.
- No unresolved contract blockers or forbidden edits.

DONE
