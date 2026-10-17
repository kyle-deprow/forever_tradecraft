# Sol source review: recipe foundation R1

The three-file implementation follows the approved recipe-foundation plan. The packaged loader uses `importlib.resources`, validates the embedded normalized-manifest digest, enforces strict models and exact known-path claim coverage, and has no `.archive` or network dependency (`src/crowley/core/recipes.py:142-158,443-546,688-703`). Raw-byte hashes, exact HTML locators, normalized-manifest projection, and locator-to-record values remain in the explicit review helper (`tests/test_recipes.py:208-251`).

The two packaged records retain only supported facts: known item and recipe IDs, known reagent quantities, four displayed skill thresholds, client-file-only learnability, and the forge/fire conditions. Output quantities, cooldowns, tradeability, and server learnability remain unknown and deterministically block readiness. Coverage reports all eight crafting professions plus Mining and treats first-run overlap as diagnostic only (`src/crowley/core/recipes.py:627-685,710-812`).

The focused tests exercise the installed-resource boundary, exact pilot facts and blockers, nine-row coverage, stable unresolved identity, client-data learnability refusal, build mismatch refusal, malformed schema and manifest bindings, raw evidence verification, detached source values, and absence of market/margin behavior (`tests/test_recipes.py:266-433`). Parent verification independently reports 17 recipe tests and six watchlist tests passing, scoped Ruff passing, and a disposable-wheel load without `.archive`.

## Must Fix

None.

## Should Fix

None.

## Nits

None.

STATUS: READY
