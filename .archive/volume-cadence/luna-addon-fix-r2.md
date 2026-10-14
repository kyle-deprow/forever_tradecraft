DONE

Fixround2 ownership A is complete.

Implemented:

- Strict `QueryOwnedAuctions(sorts)` API call and harness validation.
- Correct `{kind:"known"}` higher-price witnesses.
- Exact commodity level-20 cutoff/witness handling, including 21-level incomplete-source early completion.
- Whole-buyout item source ordering with exact normalized unit-price sorting.
- All-pair rational safety checks before sorting; unsafe partials preserve rows with `numeric_range`.
- Missing advertised results become incomplete identity mismatches.
- Owned snapshots remain unqueried until owned collection begins.
- Owned house-change guards and command house-override finalization.
- Hidden owners classify as `unknown`, not grouped.
- Updated architecture and handoff documentation for variant keys and partial/owned semantics.
- `decoded_payload()` now strictly validates every addon-produced envelope.

Verification:

- `31 passed` — `tests/test_addon.py`
- `63 passed` — non-DB suite excluding server/volume tests
- `uv run ruff check .` passed
- `uv run ruff format --check .` passed
- `git diff --check` passed

No DB tests or out-of-scope files were touched.
