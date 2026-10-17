# Recipe foundation plan

**Status:** plan only; no production implementation or data population in this change
**Reviewed:** 2026-10-17
**Target:** Forever client build `1.60.1.70450`
**Owner fence:** proposed implementation files are `src/crowley/core/recipes.py`, `src/crowley/data/recipe_foundation.json`, and `tests/test_recipes.py`. Frozen public source snapshots and the raw review manifest are evidence under `.archive/executor-review/recipe-foundation-*`; the packaged JSON embeds its normalized manifest and has no runtime dependency on `.archive`. No other source, runtime, database, addon, profile, service, or deployment file is in scope.

## Why this slice exists

The current `first_run.json` catalog contains a selected set of 544 item entries, with positive historical row evidence for 274 entries, plus profession memberships. It is an observation universe, not a recipe graph. Membership in a profession, a leveling-route purchase, or a name match must never be promoted into a recipe, quantity, learnability, or cost. `docs/WATCHLIST.md` also records that ForeverWowCraft plans are candidate-discovery evidence and that client-file presence does not prove a recipe is learnable.

This slice establishes a small strict recipe model, source binding, coverage report, and static readiness blockers. It does not add a crafting strategy, shopping list, auction forecast, recursive intermediate resolver, or numeric margin. A later strategy slice must own compatible market quotes, freshness, recursive graph behavior, cycle handling, and margin calculation. The generic schema and validator must be useful before any population is trusted. The population is deliberately small and may remain blocked when source coverage is not current enough.

Observed source-build drift is a first-class constraint: the frozen Mining and Cooking pages and item pages expose build `1.60.1.70450`, while the separately reviewed First Aid page is `1.60.1.70374` and several other profession pages are `1.60.1.70425`. `Classic` values are never a fallback for Forever. A source-build mismatch blocks a record; it is not silently normalized.

## Proposed files and boundaries

The implementation, when released, owns exactly these new files:

1. `src/crowley/core/recipes.py` — typed records, strict JSON validation, nine-row coverage reporting, and recipe-side readiness/refusal metadata. It must not make network requests, read market storage, calculate a margin, or modify the existing item catalog.
2. `src/crowley/data/recipe_foundation.json` — a source-controlled normalized artifact. It contains the two bounded blocked candidates and any explicitly retained blocked records; it is not an importer cache and does not replace `first_run.json`.
3. `tests/test_recipes.py` — focused schema, manifest binding, coverage, deterministic readiness, and refusal tests. Tests load pinned review snapshots and do not call a live site.

`validate_normalized_artifact()` in `recipes.py` is the installed validator: it checks the embedded digest, schema, and claim bindings from packaged JSON alone. `validate_review_snapshot_evidence()` is a review-only helper in `tests/test_recipes.py`: it reads the pinned local HTML and archive manifest to check byte hashes, metadata, exact locators, and the normalized projection. Production code never imports or calls the review helper. Neither validator makes a network request. Do not edit `watchlist.py`, the strategy engine, market storage, migrations, deploy files, addon code, native-motion files, or profile/service configuration in this slice.

## Canonical JSON contract

The artifact is strict JSON with no extra keys. Its top-level keys are `schema_version`, `catalog_id`, `revision`, `target_client_build`, `reviewed_on`, `source_manifest`, and `recipes`. The full `source_manifest` shape is specified after the record example. A blocked Mining record inside `recipes` has this shape; Cooking uses the same fields with its own IDs, locators, claims, and record ID.

```json
{
      "record_id": "rfs-20261017-mining-2840-0",
      "recipe_id": 2657,
      "profession": "mining",
      "profession_kind": "processing",
      "output": {"item_id": 2840, "quantity": null, "quantity_status": "unknown"},
      "reagents": [
        {"item_id": 2770, "quantity": 1, "quantity_status": "known", "optional": false}
      ],
      "skill_gate": {
        "minimum": {"value": 1, "status": "known"},
        "yellow": {"value": 25, "status": "known"},
        "green": {"value": 47, "status": "known"},
        "gray": {"value": 70, "status": "known"}
      },
      "learnability": {
        "status": "client_file_only",
        "evidence_kind": "displayed_client_data"
      },
      "cooldown": {"status": "unknown", "seconds": null, "shared_group": null},
      "acquisition": {
        "kind": "profession_window",
        "status": "client_data_only",
        "requirement_ids": [],
        "conditions": ["Needs a forge"]
      },
      "vendor_components": [],
      "binding_and_tradeability": {
        "output_status": "unknown",
        "reagent_restrictions": []
      },
      "source_build": "1.60.1.70450",
      "provenance_claims": [
        {
          "claim_id": "claim-mining-profession",
          "manifest_entry_id": "bof-mining-profession-20261017",
          "locator_id": "mining.profession",
          "field_paths": ["/profession"],
          "reviewer": "foundation-review",
          "reviewed_on": "2026-10-17"
        },
        {
          "claim_id": "claim-mining-source-build",
          "manifest_entry_id": "bof-mining-profession-20261017",
          "locator_id": "mining.page-build",
          "field_paths": ["/source_build"],
          "reviewer": "foundation-review",
          "reviewed_on": "2026-10-17"
        },
        {
          "claim_id": "claim-mining-copper-recipe-row",
          "manifest_entry_id": "bof-mining-profession-20261017",
          "locator_id": "mining.recipe-id",
          "field_paths": ["/recipe_id"],
          "reviewer": "foundation-review",
          "reviewed_on": "2026-10-17"
        },
        {
          "claim_id": "claim-mining-copper-output-item",
          "manifest_entry_id": "bof-mining-profession-20261017",
          "locator_id": "mining.output-item-id",
          "field_paths": ["/output/item_id"],
          "reviewer": "foundation-review",
          "reviewed_on": "2026-10-17"
        },
        {
          "claim_id": "claim-mining-copper-reagent-item",
          "manifest_entry_id": "bof-mining-profession-20261017",
          "locator_id": "mining.reagent-item-id",
          "field_paths": ["/reagents/0/item_id"],
          "reviewer": "foundation-review",
          "reviewed_on": "2026-10-17"
        },
        {
          "claim_id": "claim-mining-copper-reagent-quantity",
          "manifest_entry_id": "bof-mining-profession-20261017",
          "locator_id": "mining.reagent-quantity",
          "field_paths": ["/reagents/0/optional", "/reagents/0/quantity"],
          "reviewer": "foundation-review",
          "reviewed_on": "2026-10-17"
        },
        {
          "claim_id": "claim-mining-copper-skill-gate",
          "manifest_entry_id": "bof-mining-profession-20261017",
          "locator_id": "mining.skill-label",
          "field_paths": ["/skill_gate/gray", "/skill_gate/green", "/skill_gate/minimum", "/skill_gate/yellow"],
          "reviewer": "foundation-review",
          "reviewed_on": "2026-10-17"
        },
        {
          "claim_id": "claim-mining-copper-learnability-evidence",
          "manifest_entry_id": "bof-mining-profession-20261017",
          "locator_id": "mining.apprentice-text",
          "field_paths": ["/learnability/evidence_kind", "/learnability/status"],
          "reviewer": "foundation-review",
          "reviewed_on": "2026-10-17"
        },
        {
          "claim_id": "claim-mining-copper-forge-condition",
          "manifest_entry_id": "bof-mining-profession-20261017",
          "locator_id": "mining.forge-condition",
          "field_paths": ["/acquisition/conditions/0"],
          "reviewer": "foundation-review",
          "reviewed_on": "2026-10-17"
        }
      ],
      "unknowns": [
        "cooldown",
        "item_binding",
        "learnability_server_gate",
        "output_quantity"
      ],
      "readiness": {
        "status": "blocked",
        "codes": [
          "OUTPUT_QUANTITY_UNKNOWN",
          "LEARNABILITY_NOT_CONFIRMED",
          "COOLDOWN_UNKNOWN",
          "TRADEABILITY_UNKNOWN"
        ]
      },
      "review_status": "blocked",
      "superseded_by": null
}
```

The top-level `source_manifest` has exactly `{sha256, manifest}`. Its `manifest` value is the complete v2 normalized object in `.archive/executor-review/recipe-foundation-source-manifest-20261017.json` with only each archive-local `snapshot_path` removed. It contains all six entries, their raw-byte hashes, retrieval times, titles, claimed builds, and locator maps. `source_manifest.sha256` is the SHA-256 of UTF-8 canonical JSON for that normalized object: recursively sorted object keys, array order as stored, no insignificant whitespace, no trailing newline, and `ensure_ascii=false`. The digest field is outside the object it hashes. This makes the digest non-self-referential. It is `7da0a957d6d04a5e351a9cba7c54ef622d816fa519c0682501c481a114187378` for the frozen v2 manifest.

Each locator has a collection-unique `locator_id`, a CSS selector, `value_kind` (`text` or `attribute`), an attribute name only for the latter, an exact `expected_value`, and an array of permitted record JSON field paths. Text comparison decodes HTML entities, strips nested tags, and collapses whitespace; attributes compare exactly. A locator with no field paths may verify manifest metadata but cannot be used by a recipe claim. The archive manifest retains `snapshot_path` only for review-time verification; no packaged loader opens it.

The exact field rules are:

- `schema_version`, `revision`, and all IDs are positive integers where present. `record_id` is a required immutable lowercase internal identifier matching `[a-z0-9][a-z0-9._-]*`; it is the review identity even when `recipe_id` is null. A record ID is derived from the source collection entry, profession kind, output item ID, and source ordinal, never from a fuzzy display-name join. `recipe_id` is a positive integer or JSON `null`; `null` requires `RECIPE_ID_UNRESOLVED` and `review_status` `draft` or `blocked`.
- `profession` is one of the eight crafting professions `alchemy`, `blacksmithing`, `cooking`, `enchanting`, `engineering`, `first-aid`, `leatherworking`, or `tailoring`, or the separate processing profession `mining`. `profession_kind` is `crafting` for the first eight and `processing` for Mining. Coverage is nine rows, not eight with Mining substituted.
- `output.quantity` and every reagent/vendor `quantity` are positive integers when their status is `known`; they are JSON `null` when their status is `unknown`. `quantity_status` is exactly `known` or `unknown`. Reagent item IDs are positive, unique within a record, and optionality is an explicit boolean; optional does not mean free or ignorable.
- `skill_gate` has exactly `minimum`, `yellow`, `green`, and `gray`. Each is `{value, status}` with `status` `known` or `unknown`; a known value is a nonnegative integer and an unknown value is JSON `null`. Known thresholds must be monotonic in that order. `minimum` is the value following `Learn`; it is not an `orange` threshold. No threshold is interpolated when another threshold is missing.
- `learnability.status` is `confirmed_learnable`, `client_file_only`, `server_gated`, `unknown`, or `not_learnable`. `evidence_kind` is `server_observation`, `displayed_client_data`, `source_item`, or `unknown`. Displayed “every apprentice knows it” text remains `client_file_only` until an exact current-client observation proves actual learnability.
- `cooldown.status` is `none`, `known`, or `unknown`. `none` requires `seconds=null` and `shared_group=null`; `known` requires a positive integer `seconds` and permits a string or null `shared_group`; `unknown` requires both null. Missing cooldown data never becomes zero.
- `acquisition.kind` is `trainer`, `recipe_item`, `vendor`, `drop`, `quest`, `profession_window`, or `unknown`; `status` is `confirmed`, `client_data_only`, `unknown`, or `not_applicable`; `requirement_ids` contains only positive integers; and `conditions` contains explicit strings for faction, reputation, quest, or other gates. A client-only row cannot have `confirmed` acquisition.
- Each `vendor_components` entry has `{item_id, quantity, quantity_status, price_amount, price_status, currency, vendor_id, stock_status, conditions, provenance_claim_ids}`. `price_amount` is a positive integer only when `price_status=known`, otherwise null. `currency` is `copper`, `silver`, `gold`, `token`, or `unknown`. `vendor_id` is a positive integer or null. `stock_status` is `known_limited`, `known_unlimited`, or `unknown`; unlimited supply is never inferred.
- `binding_and_tradeability.output_status` is `tradeable`, `bind_on_pickup`, `bind_on_equip`, or `unknown`. Restrictions are explicit strings. Unknown output binding blocks readiness.
- `provenance_claims` are nonempty for every factual field and contain only manifest entry IDs from the embedded manifest, a `locator_id`, JSON-pointer-like `field_paths`, a reviewer string, and an ISO review date. Every locator ID must resolve within that entry and each claimed path must be in that locator's `field_paths`. Every known factual record path must be covered by at least one claim. Derived fields exempt from direct claims are `/record_id` (stable identity algorithm), `/profession_kind` (fixed profession map), `/acquisition/kind`, `/acquisition/status`, and `/acquisition/requirement_ids` (classification and empty-as-unrecorded policy), `/unknowns`, `/readiness`, `/review_status`, and `/superseded_by` (validator/workflow outputs). Known `/learnability` fields and `/acquisition/conditions/*` are source claims and are not exempt. Unknown/null values and their status markers express missing evidence and do not claim a source fact. Empty `vendor_components`, `requirement_ids`, or `reagent_restrictions` means “no value recorded in this seed,” not evidence that none exist.
- `unknowns` is a sorted unique list from the fixed reasons `recipe_id_unresolved`, `output_quantity`, `reagent_quantity`, `skill_gate`, `learnability_server_gate`, `acquisition`, `cooldown`, `vendor_price`, `vendor_stock`, `item_binding`, `source_build_mismatch`, `provenance_unbound`, and `intermediate_recipe`. Every unknown status has its matching reason; no unknown reason is silently omitted.
- `readiness.status` is `ready_for_recipe_review` or `blocked`. `readiness.codes` is a sorted-by-contract ordered unique list from `RECIPE_ID_UNRESOLVED`, `SOURCE_BUILD_MISMATCH`, `OUTPUT_QUANTITY_UNKNOWN`, `REAGENT_QUANTITY_UNKNOWN`, `SKILL_GATE_UNKNOWN`, `LEARNABILITY_NOT_CONFIRMED`, `ACQUISITION_UNKNOWN`, `COOLDOWN_UNKNOWN`, `VENDOR_PRICE_UNKNOWN`, `VENDOR_STOCK_UNKNOWN`, `TRADEABILITY_UNKNOWN`, and `PROVENANCE_UNBOUND`. A blocked record has at least one code; a ready record has an empty list. `review_status=verified` additionally requires a non-null recipe ID, target build, confirmed learnability, complete known quantities, complete provenance, no unknowns, and readiness ready. `review_status=blocked` requires readiness blocked. `superseded_by` is null unless `review_status=superseded`, in which case it is another record ID.

Canonical serialization sorts records by `record_id`, reagents and vendor components by item ID and optionality, provenance claims by `claim_id`, manifest entries by `entry_id`, locators by `locator_id`, each locator's field paths lexicographically, unknowns lexicographically, and readiness codes by the fixed order above. `validate_normalized_artifact()` verifies the embedded manifest digest, manifest structure, unique entry/locator IDs, and each claim-to-locator/field-path binding. It does not read snapshots or `.archive`. `validate_review_snapshot_evidence()` verifies each raw SHA-256, page title/build, locator selection and expected value against the frozen HTML, and equality between the normalized manifest projection and the packaged embedded manifest. It is a test/review operation, never part of an installed load. The installed validator rejects extra keys, wrong JSON types, duplicate IDs, invalid nulls, invalid status combinations, non-monotonic known thresholds, mismatched embedded manifest hashes, and unbound field claims.

## Frozen evidence and ingestion

The reviewed seed evidence is frozen in `.archive/executor-review/recipe-foundation-source-manifest-20261017.json`, archive file SHA-256 `d461bb66faa941a8c5340ce719b71e833003d8d7f4c311a616bdcd68dd79115b`, with six raw HTML snapshots under `.archive/executor-review/recipe-foundation-snapshots-20261017/`. The normalized v2 manifest digest embedded in the package is `7da0a957d6d04a5e351a9cba7c54ef622d816fa519c0682501c481a114187378`. Each entry preserves the existing raw-byte SHA-256, retrieval timestamp, exact title, claimed build, and machine-checkable locator-to-field-path map. The runtime binds the normalized digest; only the review-time raw validator reads snapshot paths. Changing a raw snapshot requires updating its raw hash and producing a new normalized digest and catalog revision.

The importer is offline and deterministic. A future capture records URL, retrieval timestamp, raw-content SHA-256, page/build stamp, parser version, and exact locator before emitting a draft. Normalization may use only numeric IDs and source links from the snapshot; names are display evidence. A reviewer promotes individual field claims, not an entire page, and every promoted field points to a manifest entry and locator. The validator never calls a live site.

Bind on Forever is suitable for client-data candidates, exact IDs, displayed reagent quantities, and displayed skill thresholds. The frozen profession pages do not display output quantities, so both pilot outputs have unknown quantity. Its apprentice text maps to `client_file_only` or `unknown`, never `confirmed_learnable`; client data does not prove server learnability. A later exact-build client capture may upgrade learnability only when its build, profession, character state, and observation evidence are recorded.

ForeverWowCraft remains route and market-context evidence. Its route page describes a cheapest path from a live AH snapshot, so it may later supply a candidate price/route observation with realm, faction, scan time, and hash. It is not recipe truth. The reviewed direct manifest URL was not retrievable, so no manifest facts are imported or asserted. No route quantity, aggregate purchase, or Classic value can populate a recipe field.

## Coverage and conservative readiness

The coverage report includes all eight crafting professions and the separate processing row for Mining, even when a row has zero verified records. For each row it reports total records and `verified`, `blocked`, and `draft` counts; target-build compatibility; known output and reagent quantities; skill-gate, learnability, cooldown, acquisition, vendor-price, and tradeability coverage; unresolved IDs; and every blocking reason. It reports overlap with `first_run.json` only as a diagnostic. An item overlap does not create a recipe edge. Bind’s recipe-window index count is not a count of learnable recipes.

This foundation does not define a market quote type, freshness cutoff, recursive producer resolution, optional-reagent pricing, cycle handling, or numeric margin. `recipes.py` only returns the deterministic recipe-side readiness status and ordered refusal codes above. A later strategy slice must fail closed on any blocked record and separately define compatible house/realm, client version/build, interface/source revision, plan hash, observation time, maximum age, item-keyed quotes, producer ambiguity, recursion, and cycles. Until that slice exists, no recipe record is margin-eligible and no price or margin is emitted. This explicit boundary prevents an incomplete recipe foundation from becoming an investment recommendation.

## Small reviewed pilot

The pilot is a source-fact seed, not a learnability or investment approval. Both records remain blocked with `learnability.status=client_file_only` until an exact current-client observation proves actual learnability. Their displayed item IDs, reagent quantities, four skill thresholds, apprentice text, forge/fire conditions, and target-build claims are bound to exact locators in the frozen manifest above. Neither profession page displays output quantity, so each output quantity is unknown and blocks readiness.

| Profession | Source-fact candidate | Frozen evidence |
| --- | --- | --- |
| Mining (processing) | `Smelt Copper`: Copper Bar item `2840` (output quantity unknown) from Copper Ore item `2770` ×1; `Learn 1`, yellow 25, green 47, grey 70; client-only apprentice text and `Needs a forge` condition | `bof-mining-profession-20261017`, `bof-item-2840-20261017`, and `bof-item-2770-20261017` |
| Cooking | `Charred Wolf Meat`: item `2679` (output quantity unknown) from Stringy Wolf Meat item `2672` ×1; `Learn 1`, yellow 45, green 65, grey 85; client-only apprentice text and `Needs a cooking fire` condition | `bof-cooking-profession-20261017`, `bof-item-2679-20261017`, and `bof-item-2672-20261017` |

`Spiced Wolf Meat` remains blocked because its learnability is shown as unknown. First Aid Linen Bandage remains a holdout because its profession page is `1.60.1.70374`, even though its item page is current. Alchemy, Blacksmithing, Engineering, Leatherworking, Tailoring, and Enchanting pages observed at `1.60.1.70425` remain candidates only until matching `1.60.1.70450` evidence is reviewed. No ForeverWowCraft-only record belongs in this pilot.

## Focused acceptance tests

`tests/test_recipes.py` should cover the implementation without network access:

1. The installed validator parses the artifact and its embedded normalized manifest, validates its canonical digest and every claim binding, and verifies deterministic serialization. A separate review-time check verifies all six raw snapshot hashes, page metadata, exact locator values, and equality with the package's normalized manifest; the installed validator has no archive-path dependency.
2. Validate exact null/status cross-fields: known quantities and thresholds are positive/nonnegative values, unknown values are null, cooldown variants are exclusive, and malformed extra/duplicate/negative fields fail.
3. Prove unresolved recipe IDs retain stable `record_id` values and are blocked with `RECIPE_ID_UNRESOLVED`; prove client-file-only learnability never becomes confirmed.
4. Validate the two pilot records’ numeric IDs, known reagent quantities, unknown output quantities, four displayed thresholds, forge/fire conditions, build, and frozen locators while asserting blocked readiness and ordered refusal codes.
5. Reject 70425/70374 source mismatches, missing provenance, changed manifest digests, Classic fallback values, and route or item-membership edges.
6. Assert nine coverage rows with explicit zero/blocked counts and source-build mismatch reasons.
7. Assert that the foundation exposes no market quote or recursive-margin computation; a blocked record returns only the named recipe-side refusal codes and no numeric margin.
8. Verify no test performs a network request and that the existing item catalog is read-only.

## Open questions and explicit unknowns

- Is there an authoritative current `1.60.1.70450` source for every profession, or must some rows remain blocked?
- How can server-side learnability, trainer/recipe-item acquisition, faction, and reputation requirements be observed without mistaking client-file presence for learnability?
- What exact cooldown and shared-group facts apply to each recipe, including variable or proc yields?
- Which vendor prices, currencies, stock limits, and reputation discounts are valid at launch?
- What launch auction-house evidence and tradeability rules should the separately reviewed strategy slice require?
- What is the authoritative recipe/spell ID for each displayed recipe when a page exposes only an item link?
- Can output quantity vary by proc, failure, or profession state? Until answered, only directly displayed base quantity is stored.
- The reviewed ForeverWowCraft manifest endpoint was inaccessible; no facts from it are assumed.

The next implementation review should approve this strict JSON/refusal contract first, then the two blocked pilot records and nine-row coverage report. It should not expand the graph from the selected item-membership catalog or import market quotes into this foundation.
