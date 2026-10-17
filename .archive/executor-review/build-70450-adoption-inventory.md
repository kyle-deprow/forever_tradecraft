# Build 70450 adoption inventory

Read-only Luna inventory, 2026-10-16. No build gate was relaxed. Live game reports 1.60.1/70450; Scanner CANONICAL_CLIENT_BUILD remains 1.60.1.70425, and runtimeMatchesCanonical rejects this client. Status folds client_invalid into plan_invalid. Native auction API parity has not yet been qualified.

After contract qualification, perform one reviewed canonical release update:
- first_run.json top-level client_build/revision/reviewed_on; retain item evidence/active428 membership unless actual evidence requires changes.
- Scanner canonical build/catalogHash/planHash/revision; retain count/pools/compressed entries if unchanged. Derive hashes with Catalog.scan_plan(), never invent them.
- Current canonical test fixtures only; retain explicit older-build rejection and historical fixtures.
- Private profile client_build/plan_hash/plan_json through existing export/config validation.
- Reload server catalog cache, authenticated addon-data/companion delivery, normal addon reload. Do not hand-edit generated game Data.lua or SavedVariables.
- Update current-release docs, leaving original evidence historical.

watchlist.py owns compact sorted planJSON/hash. Server addon-data endpoint delivers it; companion sync.py atomically writes live Crowley_Data. Lua independently reconstructs exact canonical JSON. scanformat validation is generic. Ingestion stores new immutable market_plans rows keyed by hash and associates future sweeps with that release; old plans and sweeps stay unchanged.

This is an inventory, not source implementation or live scan acceptance. Existing motion worker owns its fourteen files; do not overlap harness/addon test edits. Source review and parent integration precede another bounded release task.
