Must-Fix

1. **Persisted coverage and query completeness are conflated.**
   Plan lines 30–37, 83–85, 109–117, and 154–157 say to retain only 20 price levels, but also allow a completed query to be marked `full`, which downstream means “no price ceiling.” A complete query containing more than 20 levels is still bounded after higher rows are discarded. Labeling it `full` would let comparisons treat omitted rows as absent.

   Concrete fix: store query completeness separately from persisted coverage. `coverage=full` only when every eligible result is retained and there are at most 20 levels. If any eligible rows are dropped, use `coverage=bounded` with a proved cutoff and higher-price witness, even if `HasFull*SearchResults` was true. Apply this equally to commodities and noncommodities.

2. **The noncommodity identity algorithm is not safe as written.**
   Plan lines 56–61 and 159–164 permit identity inference for all item-result rows and count quantity reductions under a persistent ID as removals. The extracted `ItemSearchResultInfo` contains `owners` and `totalNumberOfOwners`, so grouping exists outside the commodity structure too. The query also sets `separateOwnerItems=false`. For a truly individual noncommodity auction, purchase is by auction ID and the whole listing disappears; a quantity or price change under the same ID is an identity inconsistency, not a partial sale.

   Concrete fix:
   - Make identity comparison eligible only when grouping indicators establish a single auction/result owner and a nonzero auction ID.
   - Exclude grouped item rows from sale-candidate inference or report them as unknown aggregate movement.
   - Treat any quantity, variant, or price change under a persistent auction ID as inconsistent/unknown.
   - A missing eligible prior ID contributes the full prior quantity as an observed removal; a new ID is an addition.
   - Record auction-ID persistence as a beta assumption because the generated source documents the field, not stability across scans.

3. **“Full itemKey” cannot come from the documented `ItemKey` alone.**
   Plan lines 29 and 87 require full equipment identity, but the generated `ItemKey` structure only has item ID, item level, suffix, and battle-pet species. It has no bonus IDs. The current canonical key logic parses bonus IDs from `itemLink` in `addon/Crowley/Scanner.lua:22-37`, while `ItemSearchResultInfo.itemLink` is documented as nilable.

   Concrete fix: define the canonical wire identity as the current parsed item-link key plus the raw structured API item key. Verify item ID/suffix agreement. If a noncommodity row lacks a usable link and its complete identity cannot be established, mark that observation incomplete with an explicit reason; never collapse it to the cleared query key.

4. **Owned-auction status is overstated relative to the API.**
   Plan lines 181–188 say the owned-query/status API includes listed, sold, and expired observations. The extracted `AuctionStatus` enum contains only `Active` and `Sold`. Expiry and cancellation are separate ID-bearing events: `AUCTION_HOUSE_AUCTIONS_EXPIRED` and `AUCTION_CANCELED`. `QueryOwnedAuctions` also needs completion through `OWNED_AUCTIONS_UPDATED` plus `HasFullOwnedAuctionResults`.

   Concrete fix: specify these as separate evidence streams. The owned snapshot contains Active/Sold rows only and is valid only after full completion. Persist canceled/expired events with their observation timestamp and auction ID until attached to an upload that is acknowledged. If that lifecycle is too large for this release, limit v1 of owned evidence to Active/Sold and explicitly defer cancellation/expiry rather than representing them as query statuses.

5. **The v2 wire contract is not exact enough to implement or review.**
   Plan lines 72–91 defer the schema to “docs and code together,” despite calling this document the implementation specification. Several unresolved details change correctness:
   - An `unqueried` item cannot truthfully have the required query start/end timestamps.
   - Lua `nil` cannot serve as an explicit JSON null field without a defined tagged representation.
   - Empty Lua tables may not reliably distinguish empty arrays from objects.
   - A noncommodity whole-stack buyout divided by quantity can be fractional copper. Float division cannot safely define exact price levels, cutoffs, or persistent price identity.
   - The owned batch, grouping fields, count declarations, and reason enums have no defined nullability or shape.

   Concrete fix: add the full format-2 schema to the plan before implementation. Give every item a sweep ordinal and status; make query timestamps nullable for `unqueried`; order comparisons by sweep start/ordinal while retaining query windows for exposure. Represent time-left absence with a tagged value such as `exact`, `band`, or `unknown`. Represent normalized noncommodity unit prices as reduced numerator/denominator pairs, retaining whole-stack buyout and quantity; commodity prices use denominator 1. Define exact enums and count invariants.

6. **Plan identity does not cover cadence and cannot validate delayed historical plans.**
   Plan lines 67–70 add `cadenceSeconds`, while `src/crowley/core/watchlist.py:99-118` computes `catalogHash` from the catalog model before constructing the exported plan. Therefore cadence is outside the canonical hash. Lines 137–150 require out-of-order acceptance, membership validation, and plan-identity matching, but a delayed upload from an older future plan cannot be validated after the packaged catalog changes.

   Concrete fix: retain `catalogHash` for catalog provenance and add `planHash = SHA-256(canonical exported plan excluding planHash)`, covering cadence, depth, target build, item IDs, and pools. Embed that exact plan snapshot in each compressed payload and persist it once per hash in a plan table; validate observations against the embedded canonical snapshot. An alternative is moving cadence into the canonical catalog and revising it, but it still needs a historical-plan strategy.

7. **The stated per-item cadence is not feasible under the stated worst-case limits, and static ordering can starve items.**
   Plan lines 5–6 imply every selected item is observed every 900 seconds. There are 428 active IDs. The minimum 428 initial sends consume 4.28 minutes at 100/minute before response latency; the allowed ten pages per item permit a 4,280-send worst case, far beyond the 600-second sweep cap. Explicit incomplete coverage preserves truth, but a fixed query order can leave the same tail permanently unqueried.

   Concrete fix: change the objective to a sweep-start cadence with per-item observed cadence reported separately, unless the watchlist is reduced enough to guarantee completion. Persist a rotating start cursor/fair queue across sweeps so capped scans do not starve later IDs. Define whether the initial query is page one and include owned-query time in the 600-second budget. Add a budget/fairness acceptance test covering repeated capped sweeps.

8. **Six saved sweeps retain only 90 minutes of a 15-minute collection stream.**
   Plan lines 22–25 correctly distinguish collection from delivery, but lines 124–125 still require evicting unacknowledged history after six sweeps. A player remaining at the AH longer than 90 minutes without `/reload` loses the very cadence history being collected; a warning does not preserve it.

   Concrete fix: define a retention objective and measure a representative worst-case compressed v2 size. Size the count/byte budget to the intended unattended window. Never evict unacknowledged sweeps silently; when the safe limit is reached, stop starting new sweeps and report storage-blocked missing coverage, or require and document a reload interval that satisfies the chosen retention window.

9. **Reload during a sweep needs an explicit finalization path.**
   Lines 85–86 and 102–107 preserve partial work for AH closure and query failures, but `/reload` is the normal delivery mechanism and may terminate Lua timers without a reliable AH-close callback. The in-progress sweep can disappear without its completed observations or explicit unfinished statuses.

   Concrete fix: handle `PLAYER_LOGOUT` synchronously, converting the active sweep into a saved partial record before SavedVariables are written. Add a harness test that reloads during metadata wait, initial query wait, and pagination.

10. **Acceptance tests omit several contracts that currently gate correctness.**
    Plan lines 232–246 do not explicitly test concurrent idempotency despite line 137, traversal-resistant archive paths despite line 139, owned-query completion/events, grouped item exclusion, exact fractional unit ordering, full-query-but-bounded-storage semantics, in-progress reload finalization, rotating fairness, or delayed uploads from a prior plan snapshot.

    Concrete fix: add those cases to the acceptance list. The concurrent test must send same-UID/same-payload and same-UID/different-payload requests through separate connections and assert one committed sweep, deterministic duplicate/conflict responses, and one immutable archive.

Should-Fix

1. **Specify the exact search handshake and sorts.**
   Plan lines 49–54 and 109–117 should state the preflight and event contract: wait for `GetItemKeyInfo` when metadata is absent; choose `Price` ascending for commodities and `Buyout` ascending for items; verify that the received result kind agrees with metadata; accept only the matching active key after the fresh response barrier; use `*_RESULTS_ADDED` for pagination and `HasFull*SearchResults` for completion. The source documents `COMMODITY_SEARCH_RESULTS_RECEIVED` with no item payload, so it cannot identify an active request by itself.

2. **Define conservative expiration timing.**
   For plan line 163, compare prior minimum remaining life against `current_query_finished_at - prior_query_started_at`, the maximum possible elapsed time between the two observations. Prefer exact `timeLeftSeconds`; otherwise derive the documented band minimum with `GetTimeLeftBandInfo`. Separate “expiry possible” from other unknown removals in the response.

3. **Resolve observed versus target build naming.**
   The catalog plan currently carries a full value such as `1.60.1.70374`, while `addon/Crowley/Context.lua:48-60` stores `clientVersion` and build number separately. Define `targetClientBuild` and the canonical observed full build comparison rather than overloading `clientBuild`.

4. **Choose the parent-table and route migration explicitly.**
   Current `/latest` selects the newest row in legacy `scans` and then legacy `item_stats` (`src/crowley/server/app.py:111-140`). If v2 sweeps enter `scans` without route changes, the newest response can become empty or mislabel captured counts as full-market counts. State whether migration 002 extends `scans` with format/hash/plan fields or creates a separate sweep table, how acknowledgements cover both, and whether latest/history return separate `legacy_full_scan` and `bounded_observation` series.

5. **Preserve the companion’s upload response contract.**
   Production companion code is outside Luna’s scope and reads `status`, `house`, and `listings` from every `/v1/scans` response at `src/crowley/companion/sync.py:113-121`. Require v2 ingest to retain those keys, with `listings` explicitly meaning captured rows, or widen Luna’s scope to update the companion.

6. **Make duplicate identity canonical and archive writes atomic.**
   Define the conflict digest over canonical parsed payload content rather than raw HTTP byte ordering. Insert or lock the UID/hash transactionally, compare on conflict, write through a temporary content-addressed path, and expose duplicate only after both DB and archive state are valid. This gives concrete implementation guidance for plan lines 137–140.

7. **Spell out the no-dual-decoder upgrade sequence.**
   The user must flush v1 scans to the old server, reload to receive acknowledgements, verify `CrowleyDB.scans` is empty, then update the server/addon together. Merely saying to upload old scans before replacing the addon leaves room to deploy the v2-only server too early.

Nits

- Plan line 147 should constrain `hours` to a bounded positive range and state whether the window is based on query finish time or sweep time.
- Give coverage/error reasons stable machine-readable codes plus display text; API consumers should not parse prose.
- Record the rolling send-budget timestamps in the harness so the test proves no 60-second window exceeds 100 sends, including page requests.
- Retain `sourceComplete` or equivalent diagnostic metadata even when persisted coverage is `bounded`; it is useful for distinguishing a deliberate cutoff from a page/time cap.

STATUS: NEEDS WORK
