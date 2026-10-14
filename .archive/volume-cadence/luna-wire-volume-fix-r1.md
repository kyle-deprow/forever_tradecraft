Implemented and verified wire/volume fixes in the owned files:

- Strict format-2 validation with duplicate-key outer JSON helpers (`decode_json_envelope`, aliases).
- Safe rational validation, canonical variants, ownership consistency, depth/cutoff/witness checks, malformed-type handling, timestamp storability, abort-tail reasons, and numeric-range partial preservation.
- Volume comparison now uses sweep start/ordinal ordering, exact variant filtering after whole-scope grouping and persistent-ID checks, correct exposure versus expiry gap, whole-window intervals, latest-independent freshness, null grouped/commodity individual rates, and aggregate evidence.
- Added regression coverage for duplicate keys, logout tails, depth overflow, malformed types, variant grouping, persistent repricing, timing, and projection.

Changed only:

- `src/crowley/core/scanformat.py`
- `src/crowley/core/volume.py`
- `tests/test_core.py`
- `tests/test_volume.py`

Checks:

- Scoped Ruff format/check: passed.
- `uv run pytest tests/test_core.py tests/test_volume.py`: **25 passed**.
- Full non-DB suite: **43 passed, 8 skipped**.

No unresolved issues in the owned scope.

Root follow-up: current disk report still filtered records before pairing, used sweep-end freshness, omitted top-level commodity rates. Asked worker to correct them and add regressions before completion.

Completed the second wire/volume fix round.

Changes remain limited to:

- `src/crowley/core/scanformat.py`
- `src/crowley/core/volume.py`
- `tests/test_core.py`
- `tests/test_volume.py`

Fixed report windowing so comparisons use the complete sweep ordered sequence before endpoint filtering, preserving failed/intervening observations and preventing continuity bridges. Added actual query-end freshness, commodity-only exposure/rates, mixed grouped interval handling, safe enum/type rejection, and numeric-range fractional boundary coverage.

Verification:

- Scoped Ruff format/check: passed.
- `uv run pytest tests/test_core.py tests/test_volume.py`: **32 passed**.

Final checks passed:

- Scoped Ruff format/check: passed.
- `uv run pytest tests/test_core.py tests/test_volume.py`: **32 passed**.
- Owned files only changed.
- No DB or full-suite checks run in this final round.

DONE

Parent independent verification: 32 passed on same targeted test command.
