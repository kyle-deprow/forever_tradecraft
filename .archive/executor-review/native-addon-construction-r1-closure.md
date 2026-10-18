# Native construction addon slice closure

The addon slice is frozen in `/home/dev/.cache/crowley/worktrees/native-addon-construction-20261018`, based on `3f43d8f`. It implements the strict `nativeConstruction` marker matrix and first-event decision, deferred Agent surface construction, transactional constructor failure cleanup, independent native/logout fences, Commands-owned recovery panel, fixed command grammar, and the unknown SavedVariables fixture without changing scan wire serialization.

Validation completed:

- `uv run pytest -q tests/test_addon.py tests/test_companion.py --maxfail=1`: 178 passed in 15.20s.
- Ruff, format, Python compileall, and `git diff --check`: passed.
- Production Lua frame/atlas boundary smoke: 4 passed, 63 deselected.

The implementation remains offline-only. Native daemon/helper ticket integration and live qualification are separate slices and were not attempted. Exact file hashes and plan references are in `native-addon-construction-r1-freeze.json`.
