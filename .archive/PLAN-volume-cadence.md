# Fifteen minute market observations and volume estimates

## Objective and review gate

Revision 4 incorporates the Sol plan reviews and code-review clarifications. Replace full-AH replication with the
reviewed first-run watchlist, start sweeps every 900 seconds while the AH is open and
storage is available, and publish price depth and turnover evidence by house/item.
Cadence means sweep starts; all 428 items cannot be guaranteed to finish every sweep.
Report actual per-item observation cadence. Rotate after capped/partial sweeps to prevent
starvation; a fully completed wrap can keep its normal start order.

Build collection, storage, comparison and API support, with our confirmed sales separate
from an uncalibrated public-market proxy. Trading, forecasting, statistical calibration,
mailbox parsing and a dashboard are out of scope. No invented sales probabilities.

Sol reviews this plan read-only before Luna implementation. Parent resolves findings until
STATUS: READY. Luna then implements/fixes; a separate read-only Sol worker reviews the
resulting implementation; parent independently verifies. Existing retry/watchlist work is
authorized and must survive. Baseline files/diff are in .archive/volume-cadence/baseline/,
baseline-files.json and baseline.diff. No commit, push, stash, reset or data removal.

## Nonnegotiable semantics

- Collection is not live networking. SavedVariables leave only on user /reload, logout or
  exit. Data.lua is loaded only at login/reload. No automatic ReloadUI or injected input.
- No full-scan fallback, alternate format decoder, guessed IDs or missing-data substitution.
  Missing required client APIs fail loudly. Document every client assumption for beta tests.
- Query active IDs only, both core/discovery pools initially. Names are labels; preserve
  item variants. Never mix houses. Query caps produce missing coverage, not zero supply.
- Initially retain the cheapest 20 distinct unit-price levels and all quantity at the last
  level. Keep row identity/grouping and quantity inside retained depth.
- sourceComplete is distinct from persisted coverage. Even a complete query is bounded if
  eligible results above level 20 are discarded. Full retained coverage has no discarded
  eligible rows. Full empty means zero eligible buyout supply; bid-only auctions may exist.
- Disappearance, expiry, cancellation and leaving covered depth are different. Nothing
  inferred from a public listing is a confirmed sale. No 24-hour extrapolation from brief
  exposure; unknown rates are null, not zero. Coverage quality is not sale probability.
- Do not write truncated supply/medians/cheapest-15%-of-all-units into legacy item_stats.
  Preserve legacy rows and archives. New observation series have explicit scoped meaning.

## Verified API surface and beta assumptions

Primary extracted client documentation:
https://github.com/Gethe/wow-ui-source/tree/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated
AuctionHouseDocumentation.lua, AuctionHouseEnumsDocumentation.lua, EncodingUtilDocumentation.lua.
Read exact signatures/events before coding; these are not successful live-client tests.

Use MakeItemKey and SendSellSearchQuery by item ID with cleared level/suffix and the
required separateOwnerItems=false argument (the conservative grouping model). Await
GetItemKeyInfo/ITEM_KEY_ITEM_INFO_RECEIVED if metadata is not available, choosing Price
ascending for commodities and Buyout ascending for items. Verify result kind matches
metadata. Serialize queries, accept only matching active-key events after a fresh response
barrier, and never finish from a stale cached result. COMMODITY_SEARCH_RESULTS_RECEIVED has
no item payload, so cannot by itself identify the active query. Use matching updated/added
result events with their documented payload, completion predicates and pagination.
Guard stale sessions, late replies and unrelated Auctionator/user queries; ambiguity means
incomplete, not attribution to the current item. Document limits of event freshness testing.

Respect IsThrottledMessageSystemReady and <=100 sends in ANY rolling 60-second window,
including owned/page requests. Use events/timers, never a blocking Lua sleep loop.

Both commodity and item result structures have owners/grouping indicators. Commodity IDs
are result identities, not a stable individual-auction contract. All commodities use
aggregate price-bucket churn. Only noncommodity rows with positive ID, exactly one reported
owner/name, no contrary grouping evidence and stable price/quantity/variant qualify for
individual disappearance inference. Persistence across scans remains a beta assumption.
A quantity change under an individual item ID is inconsistent, never a partial purchase.
If either observation contains ANY grouped/unknown item row within the comparable prefix,
exclude individual removal/addition inference for the entire queried item scope with
`grouped_scope`: grouped rows can conceal previously individual IDs. This conservative
rule covers individual-to-grouped and grouped-to-individual transitions.

C_EncodingUtil.SerializeJSON(value, options=nil) and DeserializeJSON(source) are documented.
Use their one JSON path plus existing raw-deflate/base64 codecs; do not import a Lua JSON
library or add optional dependency/fallback checks. Empty collections are objects in the
new payload so their Lua representation is unambiguous.

AuctionStatus has Active and Sold only. Owned completion requires OWNED_AUCTIONS_UPDATED
and HasFullOwnedAuctionResults. Expiry/cancellation are separate events; collecting those
and mail evidence is deferred, not invented as owned status values.

## Exact plan and format 2 contract

### Plan identity

Catalog revision/catalogHash remain provenance. Export a plan body with EXACTLY:
schemaVersion=2, id="first-run", positive revision, catalogHash (64 lowercase hex),
targetClientBuild (catalog's full build string), cadenceSeconds=900, positive
initialPriceLevels, sorted unique nonempty itemIDs array, and pools={core:[IDs],discovery:[IDs]}
partitioning itemIDs. Canonical JSON is sorted keys with compact separators. Add planHash
(SHA-256 of canonical body bytes) and planJSON (that exact canonical string) to the exported
object; neither is included in the body digest. API/CLI return this one representation.

Game parsing/queue authority comes from DeserializeJSON(scanPlan.planJSON). Each upload
carries that unchanged string and planHash. Server validates canonical encoding/hash and
membership against the embedded plan, not the current shipped catalog. Store immutable
plan bodies by hash so delayed/out-of-order uploads from historical plans remain valid.
Observed full client build is context.clientVersion + "." + context.clientBuild, separate
from targetClientBuild. Target build is knowledge provenance, not observed client version.
Placeholder Data.lua explicitly has scanPlan=false; no plan means actionable scan refusal.

### Envelope and compressed payload

Format 2 is the SINGLE accepted upload format. Replace old CSV rows with one compressed
JSON payload; do not keep a dual-format decoder. Required envelope fields: id nonempty
string, format=2, startedAt/finishedAt integer epochs, existing house/context attribution
(including character, clientVersion, clientBuild, interface), numRows/numObservations
nonnegative integer counts, payload raw-deflated/base64 JSON.

Payload has EXACTLY planHash, planJSON, observations and owned. observations is an OBJECT
keyed by decimal item-ID strings; owned is the batch below. All payload collections are
objects with string keys, not arrays. The plan remains a canonical STRING supplied by the
server, preserving arrays/empty pools through Lua serialization. Tagged objects represent
absence; nil must not silently stand for JSON null. Reject duplicate JSON keys/extra fields.

### Item observations

Exactly one observation per planned item. Fields:

- itemID; ordinal (1-based position in rotated sweep, unique/contiguous).
- kind: commodity, item, or unknown (unknown only incomplete/unqueried).
- query: {kind:"unqueried"} or {kind:"queried",startedAt,finishedAt}.
- coverage: full, bounded, incomplete or unqueried; sourceComplete boolean.
- cutoff: {kind:"unbounded"}, {kind:"price",numerator,denominator}, or {kind:"unknown"}.
- higherPriceWitness: tagged known reduced rational or unknown.
- reasonCode: ok, metadata_unavailable, query_timeout, page_limit, sweep_timeout,
  ah_closed, logout, house_changed, missing_item_link, identity_mismatch,
  unexpected_order, numeric_range, not_started. Include display text separately if useful.
- rowCount and rows object keyed "row:1", "row:2", etc.

Unqueried: zero rows, unqueried query, unknown kind/cutoff, sourceComplete=false.
Queried windows lie within sweep bounds. Incomplete: unknown cutoff and a stable error code;
retained partial rows are evidence but ineligible for movement. Full: unbounded cutoff,
sourceComplete=true and every eligible buyout row retained, including zero. Bounded:
positive rational cutoff and strictly higher price witness proving that last retained
level is closed; sourceComplete may be true or false for commodities but MUST be true for
noncommodity items. If the boundary cannot be
proved, coverage is incomplete. Full source + >20 retained levels trimmed => bounded.

### Captured rows and exact price identity

Required row fields: resultID positive integer; itemID; canonical itemKey; rawItemKey with
integer itemID/itemLevel/itemSuffix/battlePetSpeciesID; link tagged known string or unknown
(unknown link permitted for commodities only); quantity positive integer; price tagged
unit copper for commodities or auction copper for items; unitPrice reduced positive
numerator/denominator pair. Commodity denominator=1; item rational equals buyout/quantity.
No floating division defines equality, level boundaries or sort order. Use exact rational
Python arithmetic and fraction-aware Lua comparisons; include fractional-copper tests.
Safe numeric domain is 0..9007199254740991 (IEEE-754 MAX_SAFE_INTEGER), with positive
IDs/quantities/rational components where required. Reduce fractions before comparison.
Before cross multiplication require numerator <= floor(MAX_SAFE_INTEGER / the other
denominator) in BOTH directions. A query needing an unsafe comparison is incomplete with
numeric_range, never rounded. Do not emit an unsafe source value as a rounded row: preserve
only safe captured rows with incomplete coverage. Server validates the same numeric domain
and comparison-product safety for successful scopes/cutoffs/witnesses; unsafe wire values
are 422. Test boundary conditions. Format 2 IS the immutable whole-buyout/quantity reduced-
rational normalization policy; a semantic normalization change requires format 3.

Owners are a name:true object; retain totalNumberOfOwners, containsOwnerItem and
containsAccountItem, and identityKind individual/grouped/unknown. Commodities are grouped.
Unknown/hidden owners cannot be guessed. A noncommodity canonical key is the existing
parsed link itemID/suffix/bonus-ID key extended with `:l<itemLevel>` then
`:p<battlePetSpeciesID>` only when those raw fields are nonzero. Also preserve the raw key;
verify ID/suffix agreement. This makes API path keys distinguish level/pet variants. If
link/full identity is unavailable, mark the observation incomplete instead
of collapsing variants to the cleared query key. Reject duplicate result IDs in an item
observation. Variant comparison includes raw item level/pet species and parsed bonus IDs.

Time-left is tagged exact seconds (nonnegative), band with band 0..3 and ordered
minimumSeconds/maximumSeconds from GetTimeLeftBandInfo, or unknown. No fixed Classic bands
or zero substituted for unknown. Prior minimum remaining life must exceed current query
END minus prior query START to exclude expiration conservatively.

All IDs/counts/epochs/copper values are integers. Validate item/row/plan consistency,
nonnegative prices, rational normalization, cutoff/witness relation, level count,
ordered timestamps, owner/group flags and cardinalities. Envelope numObservations equals
plan length; numRows equals summed item rowCounts, excluding owned rows. Observation
keys/IDs agree, ordinals partition 1..plan length. Reject malformed uploads with 422 before
archive writes or DB mutation. Successful scopes contain only eligible positive-buyout rows;
bid-only listings are outside this first release's buyout scope, not zero-price bargains.

### Owned evidence

Batch fields: status full/incomplete/unqueried; query tagged as above; reasonCode ok,
query_timeout, ah_closed, logout, house_changed, sweep_timeout or not_started; rows object keyed decimal
auction ID. Each row: auctionID, itemID, canonical itemKey, rawItemKey, usable itemLink,
quantity, buyout tagged known copper or unknown, and status active/sold. The beta assumption
is that known OwnedAuctionInfo.buyoutAmount is whole-auction copper for either item kind;
it is a listed buyout, not necessarily realized proceeds. Actual proceeds remain unknown
without separate evidence. Only a FULL fresh owned query may
contribute confirmed sold evidence; invalid row/link makes batch incomplete. Actual sale
time is unknown: record first seen sold and observation window, not exact execution time.

## Implementation order

### 1. Wire models, plan export and additive storage

Implement the contract above and migration 002_market_observations.sql. Do NOT edit 001.
Create separate market_plans, market_sweeps, market_observations and captured-row storage
(JSONB per observation is acceptable with suitable house/item/time indexes), plus owned
observation and deduplicated own-sale evidence. Legacy scans/listings/item_stats survive
and are never admitted to new movement comparisons.

Retain companion upload response keys scan_uid/house/status/listings/items; listings now
explicitly means captured rows. Ack lookups cover legacy scans and new sweeps. Preserve
UID uniqueness across both; a v2 UID colliding with legacy data is conflict, not duplicate.
Use the whole canonical logical scan for conflict digest: EVERY validated envelope field
plus the DECODED payload, excluding only transport/compression differences. Changed house,
context, timestamps or counts under one UID are conflicts. Transactionally claim/lock UID:
same-content retries return duplicate only
after committed DB/archive state; different content returns 409. Concurrent connections
must yield one sweep and immutable archive. Archive through temporary file + atomic replace
at content-addressed paths derived from UID/hash, never trust UID as a path component.
DB rollback must not expose half observations; an unreferenced immutable archive is not
committed evidence. No overwriting different payload content for an existing UID.

New latest/history routes expose bounded observations explicitly, alongside separate
legacy_full_scan / legacyPoints sections if historical data exists. Never select a new
sweep then silently fetch legacy stats. /houses counts/freshness include both formats
without implying complete capture. New volume endpoints operate on new tables only.

### 2. Targeted Lua scanner, fairness, cadence and safe retention

Start when AH opens and due; schedule starts 900 seconds apart from LAST START. Persist
last start across reload. Never overlap or replay missed ticks. A long sweep finishes
before another can start; no backlog burst. Manual scan uses this same pipeline; force
can request immediate collection but cannot bypass throttle, overlap or storage protection.
Capture house/context once; a mid-sweep house change finalizes partial work explicitly.

Persist a rotating cursor: next sweep begins after last ATTEMPTED item, wrapping through
current plan. If plan changes and cursor ID remains present, continue after it; otherwise
explicitly reset/log plan change. Every planned item gets an ordinal and status, including
unqueried tail. Capped or failed items cannot hold the cursor fixed across sweeps. Tests
must prove repeated capped sweeps eventually attempt every ID.

Wait for metadata with a query timer. Require fresh matching updated/added events after
sending; guard generation tokens and stale cache. Initial query is page one; maximum 10
pages per item, 30 elapsed seconds per item INCLUDING metadata/paging waits, and 600 elapsed
seconds per sweep INCLUDING owned query. QueryOwnedAuctions consumes budget; do it once
per sweep with full completion and a 30-second timeout. Log all send timestamps in harness.

Commodity prefix must be ascending by unit price; fetch until a higher witness closes
level 20 or the source is complete. Include the whole last level. Contradictory ordering
makes observation incomplete. Item queries fetch all eligible results within caps, then
sort EXACT normalized unit price, preserving variants, and retain level 20 plus witness;
whole-auction sorting cannot prove cheapest unit-price prefix before completion. If any
eligible higher rows are discarded, coverage is bounded even with sourceComplete=true.

AH closure finalizes partial work and invalidates callbacks. PLAYER_LOGOUT synchronously
finalizes an active sweep before SavedVariables writes (including /reload during metadata,
query or paging). Do not assume AH_CLOSED fires on logout. Keep completion notification and
status showing loaded plan, next due time, counts/failures and upload/reload requirement.

Retention objective: preserve all unacknowledged history up to existing six-sweep capacity
(about 90 minutes at ideal cadence), then PAUSE before starting another sweep. Never evict
unacknowledged sweeps. Prune acknowledgements on load and before admission. Storage-blocked
status tells user to flush/reload; collection resumes when acknowledgements are loaded.
The first /reload writes SavedVariables; the companion then uploads and writes new
acknowledgements into Data.lua. A SECOND login/reload is needed to load those acknowledgements
and prune/resume. Never promise immediate resume after a single /reload at capacity.
Force also respects capacity. Measure/report representative full-watchlist compressed size
in tests/docs. No byte-count-based deletion, auto reload or external SavedVariables write.

### 3. Turnover comparison and API

Implement pure volume comparison and authenticated
GET /v1/houses/{key}/items/{item_key}/volume?hours=24 (positive 1..168 hours).
Window uses observation end timestamps; compare only intervals fully contained in it,
not prorated counts whose execution time is unknown. Return latest observation/freshness,
coverage, intervals/exclusions and rates using actual elapsed exposure.

Order each item's records by SWEEP START/ordinal, not arrival or scan UID. Include failed
and unqueried records; do not skip them to manufacture continuity. Out-of-order uploads
recompute consecutive comparisons on read, avoiding permanent gaps/double counting.
Require matching house, canonical variant/raw key, observed client build, planHash and
normalization policy; nonoverlapping queried windows; positive end-to-end elapsed time
<=1800 seconds. Any failure/metadata mismatch/gap gives a stable excluded-interval code.

Common coverage is the intersection of proved prefixes: full including full-empty has no
ceiling; bounded contributes its cutoff. Rows outside common coverage are unknown. Price
ranges and quantities describe retained competitive depth, never whole market totals.

Item rows eligible as individual: only stable positive ID, sole reported owner and owner
name and no contrary grouping evidence. ANY quantity/price/variant change under persistent
ID is inconsistent/unknown. Missing eligible prior IDs inside common scope contribute
full prior quantity as observed removals; new eligible IDs are observed additions. Grouped
or unknown rows in EITHER observation's common prefix disable individual additions/removals
for the queried item scope, including grouping transitions. Separate unexpired removals
(prior minimum life > maximum elapsed gap), expiration-possible and time-left-unknown.
Do not call removals transactions or guess cancellations/reposts with hidden sellers.

Commodity mode: exact-price bucket quantity differences within common coverage produce
positive depletion/replenishment proxies. Offsetting new supply masks purchases;
cancel/reprice can mimic them. Commodity IDs do not enable per-auction identity or expiry
inference. Report aggregate churn distinctly from individual removals.

API: observed individual removed/added units, aggregate commodity depletion/replenishment,
common price scope, compared seconds/hours, excluded intervals/reasons, expiration-possible
and unknown units, and eligible individual sale-candidate units per observed hour labelled
UNCALIBRATED. Market actual-sales estimate/confidence interval remain null/unavailable;
no proxy range is a bound on true market volume. Coverage quality is separate from sale
probability. First sample/no valid comparisons has unknown rate, not zero. No daily
extrapolation or fabricated demand rank. Own-confirmed evidence is a separate section.

### 4. Our sales, docs and upgrade

Store explicit Sold owned snapshots only after full completion, deduplicated by
house/character/auction ID. Preserve first seen sold time, quantity and listed buyout where
known; realized proceeds remain unknown. Repeated sightings do not double-count. Disappearing owned rows are not sales.
Inconsistent repeated sold quantity/price is rejected/flagged, not silently overwritten.
Own-confirmed totals describe first-observed evidence windows, not a complete market or
exact execution clock. Do not add them again to public-market proxies. Expiry/cancel
collection, offline mail evidence and statistical calibration are future work.

Update README, WATCHLIST, ARCHITECTURE and HANDOFF to final state and exact wire schema;
record every API/identity/serialization assumption and beta checklist. Explain limits,
backpressure, fair scheduling, captured vs full-market statistics and no-dual-decoder
upgrade. Explicitly require OLD addon/server flush -> acknowledgements loaded/pending empty
-> coordinated v2 upgrade. Real-client validation remains unperformed until user tests.

## Exact Luna scope fence

May edit/create ONLY these paths:

- addon/Crowley/Core.lua
- addon/Crowley/Scanner.lua
- addon/Crowley/Commands.lua
- addon/Crowley/Probe.lua
- addon/Crowley/Crowley.toc
- addon/Crowley_Data/Data.lua
- src/crowley/core/watchlist.py
- src/crowley/core/scanformat.py
- src/crowley/core/volume.py (new)
- src/crowley/server/app.py
- src/crowley/server/ingest.py
- src/crowley/server/migrations/002_market_observations.sql (new)
- tests/wow_harness.py
- tests/test_addon.py
- tests/test_core.py
- tests/test_server.py
- tests/test_companion.py
- tests/test_watchlist.py
- tests/test_volume.py (new)
- README.md
- docs/WATCHLIST.md
- docs/ARCHITECTURE.md
- docs/HANDOFF.md

Do not edit plan/artifacts, catalog JSON, pyproject/lock, companion production code, deploy,
original migration or unrelated files. No dependencies, external services, full-AH scan
path, protected trade calls, input automation, ML or dashboard. Report precise blockers
before widening scope/substituting behavior. Do not revert earlier authorized edits.

## Acceptance and exact verification

- Real Lua tests: absent plan, start/due at 900, persisted last start, no overlap/catchup,
  AH close/reopen/house change, stale/unrelated events/cache, matching metadata/response,
  true documented no-payload event behavior, zero results, shared-price boundary, source
  full but retained bounded, fractional unit ordering and numeric range/cross-product
  boundaries, grouped item identity exclusion and individual/grouped transitions,
  nil links, bid-only exclusion, per-item/page/sweep caps and timer invalidation.
- Replace drain-all harness timers with due-time scheduling/explicit clock advancement.
  Test reload/PLAYER_LOGOUT in metadata/query/paging wait; safe preservation of partial
  progress. Repeated capped sweeps prove cursor fairness. Six pending sweeps pause without
  eviction; acknowledgements/reload resume. Rolling send timestamps prove <=100 messages
  in every 60 seconds, including owned/page requests. Measure representative compressed size.
- Strict parser tests: v2 only, tagged absence/empty objects, no duplicate/unknown JSON keys,
  hash/historical plan validation, exact fractions, row/membership/count/time invariants,
  grouping and incomplete/zero distinctions, real Lua->SavedVariables->codec round trip.
- Pure volume tests: replacement with equal net supply, missing individual IDs, unchanged
  survivors, inconsistent stable ID quantity/price/variant, grouped/hidden owners and both
  grouping transitions with unchanged supply, raw-level/pet API identity isolation, expiry
  vs unknown time-left with conservative window gap, cutoff displacement, full-query but
  bounded retention, failed/unqueried intervening sample, plan/build/house changes, sparse
  gaps, fractional buckets, commodity churn, first sample unknown and exact exposure.
- DB/API: migration preserves legacy rows; addon-generated snapshots -> archive -> depth
  -> volume, empty observation, house/auth isolation, deterministic chronological results
  after out-of-order uploads, historical plan after current plan changes, partial stats
  never legacy whole-market stats, own full-completion gate, sold dedup/inconsistency.
  Concurrent separate connections test same UID/same payload and conflicting payload:
  exactly one committed sweep, deterministic duplicate/409 and one immutable archive.
  Changed-house/time/context/counts under the same UID are conflicts too.
  Test traversal-resistant UID paths, atomic archive and rollback visibility.
- Parent-provided temporary DB URL ONLY (fixture drops schemas):
  CROWLEY_TEST_DATABASE_URL=postgresql://crowley:crowley-volume-test@127.0.0.1:32904/crowley_test
- Scoped formatter: pass the explicit modified Python file list to uv run ruff format.
  Then uv run ruff check .; uv run ruff format --check .; full pytest with the above DB URL.
  Build wheel and verify packaged catalog remains included. Do not run destructive tests
  against any production DB. No commit/push/reset/stash.
- Luna report changed files, actual command results and unresolved issues; DONE final line
  only when complete. Parent inspects actual diff/scope and independently repeats checks
  before separate Sol review. Fix real findings through Luna, rerun Sol after meaningful
  fixes, and finish only with STATUS: READY and passing parent verification. Preserve
  prompts/reports/round history in .archive/volume-cadence (parent ownership).

## Fix round 1 ownership subdivision (root, after code review)

Sol code review returned MAJOR ISSUES; the same functional contract remains approved.
All findings accepted. To keep corrections bounded, Luna workers have exclusive subsets:

- Original luna_implementation: addon files, tests/wow_harness.py and test_addon.py,
  README.md and three docs files. Owns actual API/scanner/lifecycle/depth and accurate docs.
- luna_wire_volume: src/crowley/core/scanformat.py and volume.py, tests/test_core.py and
  test_volume.py. Owns strict wire/turnover semantics and regression coverage.
- luna_server_storage: src/crowley/server/app.py, ingest.py, migration002, tests/test_server.py.
  Owns variant route projection, storage/owned/concurrency and DB/API regression coverage.

Other original allowed paths remain unchanged unless root explicitly reassigns them.
No worker edits .archive. All workers read full plan and fix prompt; coordinate schema via
root/messages. Original scanner worker and wire worker do not run DB schema-dropping tests;
server worker owns temporary DB until DONE. Root reruns ALL tests after all workers finish,
then independent Sol reviews integrated implementation. No substitutes or scope expansion.

## Revision 4 clarification gate (after second code review)

These clarifications preserve the original objective and format-2 normalization policy:

- Owned collection not entered means unqueried/not_started, including interrupted market
  sweeps. Once owned collection begins, a detected attribution change means incomplete
  house_changed, never confirmed evidence. Add house_changed to the sole owned reason enum.
  Check captured house before accepting owned rows; reject or finalize override changes.
- Initial price-level counts and ordered-prefix proof apply to successful full/bounded
  observations. Incomplete captures may retain more levels and original partial order,
  with unknown cutoff and no movement eligibility. Sort partial rows when all required
  comparisons are safe; otherwise preserve safe rows and classify numeric_range. A cap
  does not force rejection or discard of already captured evidence.
- JSON row objects are interpreted by numeric row ordinals, never object iteration order.
  Equal-price ties may have any row identity order. Successful scopes require safety for
  every reduced-rational pair and exact price ordering; bounded scopes have reason ok and
  exactly initialPriceLevels distinct levels with a closed higher witness.

Root requests Sol read-only review of this narrow clarification before dependent fixes.
Second code-review fixes remain in the original exact scope. No server/storage redesign.
