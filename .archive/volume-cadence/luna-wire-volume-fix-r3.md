Round 3 ownership C is complete.

Changed only:

- `src/crowley/core/volume.py`
- `tests/test_volume.py`

`project_observation_variant` now validates and sorts original `row:<n>` keys numerically before filtering, deep-copies rows, and emits contiguous projected ordinals. Added the shuffled 12-row variant regression.

Checks:

- Scoped Ruff format/check/format-check: passed
- `uv run pytest tests/test_volume.py`: **21 passed**
- No DB or full-suite tests run.

Projection helper contract for server reuse: `project_observation_variant(observation, requested_item_key, raw_identity=None)`.

DONE
