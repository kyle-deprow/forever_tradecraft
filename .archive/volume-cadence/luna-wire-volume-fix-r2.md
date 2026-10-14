Round 2 ownership B is complete.

Changed only:

- `src/crowley/core/scanformat.py`
- `src/crowley/core/volume.py`
- `tests/test_core.py`
- `tests/test_volume.py`

Implemented strict successful-scope pairwise safety/depth proofs, partial-scope tolerance, numeric ordinal/tie handling, owned `house_changed` validation, bidirectional unqueried tags, requested-variant persistent-ID transition accounting, numeric row ordering, and deep-copy projection.

Checks:

- Scoped Ruff format: passed
- Scoped Ruff check: passed
- Scoped Ruff format check: passed
- `uv run pytest tests/test_core.py tests/test_volume.py`: **42 passed**
- No DB or full-suite tests run.

DONE
