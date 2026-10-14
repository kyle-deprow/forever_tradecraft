Round 3 complete.

Changed only:

- `src/crowley/server/app.py`
- `tests/test_server.py`

The history API now reuses `project_observation_variant`, preserving numeric `row:<n>` ordering and exact variant filtering. Added a 12-row JSONB reorder regression covering history and volume projections.

Checks:

- Required DB test command: `15 passed`
- Scoped `ruff check`: passed
- Scoped `ruff format --check`: passed

No unresolved issues.

DONE.
