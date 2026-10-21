# Architecture

## Constraints that shape everything

- **No official data feed.** Blizzard's Game Data API has no Forever auction endpoint, so
  every price we have comes from our own in-game observations. Starts are 900 seconds apart
  while a character stands at an auctioneer; all 428 active watchlist IDs may not finish every sweep. Each item
  has a 30-second query budget, each sweep has a 600-second budget, and the client permits at
  most 100 throttled sends in any rolling 60 seconds.
- **Addons cannot do I/O.** The only way out is SavedVariables, written on `/reload`,
  logout or exit. The only way in is an addon file loaded at login or `/reload`. The
  companion bridges both directions; this is the same pattern as the TSM desktop app.
- **Realmless houses.** A house is `(region, ruleset, faction)`, where faction includes the
  goblin `neutral` houses (15% cut instead of 5%). The house key `us-normal-horde` is
  decided **at scan time** in game (auto-detected, overridable with `/crowley set`) and
  stored with every scan. The server never mixes data across houses.
- **One click per protected action.** Buying, posting and cancelling need a hardware event.
  We automate analysis and queue-building, never the clicks.
- **One assumed path, no fallbacks.** Each unknown about the Forever client has one assumed
  answer, written below. If an assumption is wrong, the code fails loudly and we fix that
  one path rather than carrying alternatives.

## Client facts and remaining assumptions

| Assumption | Where | If wrong |
|---|---|---|
| Interface 16001; a plain `Crowley.toc` loads | `addon/*/*.toc` | Addon missing from the list |
| Commodities and non-equipment use native `MakeItemKey` + `SendSearchQuery`; equipment uses an explicitly zeroed comparison key + `SendSellSearchQuery` | `Scanner.lua` | Native full-sweep verification includes recipe 2555, containers 4238/4240/4241/4245/5765, and equipment 873 |
| Item-search and commodity-search events follow the observed paths; freshness barriers reject stale, unrelated and foreign results | `Scanner.lua` | Full sweep `beta-normal-alliance-1792040351-Arthur-6643` verified 428 active IDs and native recipe, container, equipment and commodity results; item identity and freshness barriers remain required because result events have no request ID |
| **Live observed:** `GetCurrentRegion()` returns 110 and `GetCurrentRegionName()` is empty. **Code mapping:** 1=us, 2=kr, 3=eu, 4=tw, 5=cn, 110=beta | `Context.lua`, `house.py` | Unknown numeric IDs fail |
| **Live observed:** realm is `Classic Beta PvE 2`; `/crowley status` reports `beta-normal-alliance(auto)` after the correction. **Code behavior:** beta auto-attribution maps only that exact realm to normal and rejects other beta realms | `Context.lua`, `house.py` | Avoids merging unverified beta realms |
| **Assumption:** launch realm labels Normal, PvP, RP and Hardcore identify rulesets | `Context.lua` | Unknown names fail |
| English zone names identify neutral houses | `Context.lua` | Use `/crowley set faction neutral` |
| Probe observed `C_AuctionHouse`, `C_EncodingUtil`, and `C_Item`; `C_RealmInfo` absent and `C_GameRules` present | `Probe.lua` | Presence only; behavior remains to verify |
| **Live observed and fixed:** empty Lua tables serialize as `[]`; the native contract accepts that only for empty collections, requires objects for nonempty keyed collections, normalizes them to dictionaries, and rejects `{}` empty / nonempty arrays | `Scanner.lua`, `scanformat.py` | The earlier 422 row/count mismatch is historical; the original scans now POST 200. No archive payload format changed |
| Native commodity `SendSearchQuery` and class-aware item search dispatch produce matching result events | `Scanner.lua` | Verified with retained commodity, recipe, container and equipment prices in full sweep `beta-normal-alliance-1792040351-Arthur-6643` |
| Full source-complete coverage at exactly N retained levels uses an unbounded cutoff and unknown witness; bounded coverage needs a strictly higher N+1 witness | `Scanner.lua` | The earlier producer defect was rejected with HTTP 422; the correction is accepted by strict validation in sweep 4 |
| Non-commodity search results group identical one-unit auctions; `buyoutAmount` is one auction's buyout and `quantity` is units available in that result | `Scanner.lua`, `scanformat.py` | Item unit prices use the per-auction buyout; grouped quantity is retained as availability |
| Exact `timeLeftSeconds` in the uint32 window `2^32-300..2^32-1` decodes as `seconds - 2^32`; format 3 exact seconds are `[-300,172800]` | `Scanner.lua`, `scanformat.py` | Values outside the understood window fail through the existing incomplete/numeric-range path |
| Auctionator is installed (hard dependency) | `Crowley.toc` | Addon doesn't load |

`/crowley probe` saves the client's API surface for checking these. The scanner uses the
client's `hooksecurefunc` callbacks to flag an Auctionator or user search that overlaps an
active Crowley request. The Auction House result events have no request identifier, so a
foreign same-key query is conservatively recorded as incomplete rather than attributed to
Crowley; this correlation limit remains a live-client beta assumption.

## Data flow

```
WoW (Wine) ── /crowley scan ──▶ CrowleyDB.scans (SavedVariables, compressed rows)
     │                                │ /reload or logout
     │                                ▼
     │                     crowley-companion (poll, parse, POST /v1/scans)
     │                                │                     ▲
     │  Crowley_Data/Data.lua ◀───────┘ POST /v1/addon-data │ HTTP over Tailscale
     │  (acked scan ids, shopping lists)                    │
     └─ next /reload: prune acked scans, sync lists ──▶ crowley-server ──▶ TimescaleDB
```

The addon keeps at most 6 unacknowledged sweeps. The companion acknowledges uploaded sweeps
through Data.lua, and the addon prunes them on the next load. At capacity it pauses and never
evicts evidence. Uploads are idempotent on the addon-generated sweep ID.

## Scan format (v2 and v3)

`CrowleyDB.scans[id]` holds an envelope with `format=3`, integer sweep bounds, house/context,
row and observation counts, and one raw-deflated/base64 JSON payload. The payload has exactly
`planHash`, canonical string `planJSON`, object-keyed `observations`, and object-keyed `owned`.
The server also accepts historical format-2 envelopes. Each planned item has a query window,
kind, coverage (`full`, `bounded`, `incomplete` or `unqueried`), source completeness, rational
cutoff/witness and retained `row:<n>` objects.
Commodity price is unit copper. A non-commodity result groups identical one-unit auctions: its
`price.copper`/`buyoutAmount` is the buyout of one auction, while `quantity` is the number of
units available in that result, so format 3 stores `unitPrice` as `{copper, 1}`. Historical
format-2 rows retain their old reduced `copper / quantity` wire value for validation and are
normalized to the corrected unit price before storage. Format-3 exact time-left values may be
negative: a client uint32 value from `2^32-300` through `2^32-1` is decoded by subtracting
`2^32`; all other exact values must be in `[-300,172800]`. Format-2 wrapped values are likewise
decoded during storage normalization. Stored observations and captured rows always use corrected
semantics; `market_sweeps.payload`, its content digest, and the raw archive keep the received
envelope/payload unchanged. Unsafe cross-products produce `numeric_range`; bid-only rows do
not become zero-price listings. Noncommodity keys preserve parsed link bonuses plus raw level,
suffix and pet identity. Successful full/bounded scopes prove every retained rational pair and
the higher witness; incomplete captures retain safe partial rows, sort them when comparisons are
safe, and leave the cutoff unknown otherwise. Unknown links/owners are tagged unknown rather
than guessed. Owned collection remains `unqueried` until its own query is sent; a house change
before completion makes that batch incomplete and prevents cross-house evidence.

## Storage (TimescaleDB)

| Table | Contents |
|---|---|
| `houses` | one row per region/ruleset/faction |
| `scans` | one row per upload, with client context and the raw-archive path |
| `listings` | hypertable, every auction in every scan; compressed after 3 days |
| `item_stats` | hypertable, one row per item key per scan: min, p10, p25, median, market value, quantity |
| `items` | latest name, quality and level per item key |
| `client_probes` | `/crowley probe` reports |

Migration 002 adds `market_plans`, `market_sweeps`, `market_observations`,
`market_captured_rows`, `owned_observations` and deduplicated `own_sale_evidence`. Legacy
scans/listings/item_stats stay separate and are returned under `legacy_full_scan` sections;
the volume endpoint reads only the new observation tables. Public churn is an uncalibrated
proxy. A disappearing listing is never a confirmed sale, and own Sold evidence is reported
separately only after a full owned result.

`GET /v1/houses/{house}/items/{item_key}/volume?hours=24` accepts 1–168 hours and compares
only new observations whose end windows fall inside the request. It reports actual compared
seconds, common proved price scope, excluded intervals, commodity depletion/replenishment,
individual candidate units per observed hour labelled `UNCALIBRATED`, and a separate own-Sold
evidence section. Market actual-sales estimates and confidence intervals remain null.

Accepted envelopes are archived as gzip JSON under the retained content-addressed
`data_dir/raw/format2/<digest-prefix>/<digest>.json.gz` so observations can be replayed without
trusting a UID path. Legacy archives remain where they were written. New depth and volume
reports never use legacy whole-market statistics.

## Natural interaction executors

The addon publishes a read-only256x256pixel status surface once per second.
`session/decoder.py` turns it into strict CRS1 frames with checksum, boot,
sequence and window-identity checks. Scan state, command-buffer readback and
movement feedback use this deterministic path. A larger screenshot feeds Luna
when semantic visual evidence is required. AH reopening currently measures its
target with Luna, then refreshes that measurement after pointer movement; a
deterministic scan monitor does not imply a whole cycle without model calls.

The accepted capture path obtains a desktop image before cropping it. The
default-off region producer under `tools/gnome-telemetry-region/` is native C,
requests only the status rectangle, and is still undergoing integration review.
Its diagnostic must use the already leased daemon through IPC, with no second
desktop owner. Original observation timestamps and absolute deadlines include
capture and identity work. Compiled isolated tests are not live timing evidence.
An offline replay measured strict Python decode at about55ms median; the prior
full-screen path measured1.67s overall. See
[the conditional runtime performance plan](../.archive/PLAN-deterministic-runtime-performance.md)
for attribution and the evidence required before a Rust migration plan.

`session/executor.py` plans deterministic pointer curves, click dwell, key holds,
camera drags and waits. `driver.py` dispatches finite XTEST command chains under
the existing Guardian admission fence; the Guardian owns process groups and the
exact held-input set. Clicks reobserve the target after movement and verify its
safe interior before pressing. Camera motion occurs while the right button is
held. Cancellation revokes the generation and releases owned inputs.

`session/input_tool.py` verifies Crowley's fixed private xdotool publication
against its vendored upstream source and executable manifest. The backend pins
the ELF bytes in a sealed Linux memfd before acquiring input ownership. Normal
dispatch, ordinary release and the independent spawned watchdog use that image;
the watchdog acknowledges FD readiness before input can be admitted. Disk
publication drift invalidates calibration while the pinned image remains
available for releases. XI2 RawMotion is explicit metadata: shared forward-only
one-to-one pairing requires a following primary Motion at the same server time;
raw records alone cannot prove a target or endpoint. Complete raw records reach
the takeover monitor at the native delimiter even when the stream goes idle.
Window fingerprints and sealed driver versions include
the tool digest. The supported default X screen is zero. Build instructions are
in [REPEATING_SCANS.md](REPEATING_SCANS.md).

Native motion qualification requires completing and reviewing the attached-XTEST
coordinate contract. The captured slave Motion contains the prior pointer in root/event
coordinates and the endpoint in delivered valuators. Matching upstream DIX source
explains that order; the current failed seed remains unqualified. The reviewed
correction plan is [PLAN-xtest-motion-transition.md](../.archive/PLAN-xtest-motion-transition.md):
preserve both coordinates, verify an exact origin-to-endpoint transition, seal the
measured two-axis device mapping, and recheck the actual final pointer. Its source
and regression implementation is undergoing final verification; no fresh native
qualification is claimed. Human relative motion keeps its separate interpretation.

`session/motion.py` consumes decoded schema-3 native position, facing, speed,
combat/death and primary bindings. This status-body version is distinct from
CRS1 framing and scan format 2. Movement pulses are capped at 0.35 seconds;
waypoints are local, capped at two world units and a finite 20-second budget.
Waypoint admission supports one translation pulse whose full 2D endpoint
uncertainty fits the arrival tolerance, minimum duration, profile ceiling and
remaining travel budget. It includes speed uncertainty, the named heading
allowance, and the full position/facing drift allowed at final confirmation.
Requests outside that supported region are rejected before camera or key input;
being inside the two-unit outer cap alone does not imply reachability. The
minimum pulse creates a lower gap above the no-input arrival tolerance. At
speed7/minimum0.08, examples are roughly0.413–1.292 units straight ahead and
0.442–0.83 at the0.20-radian translation limit; exact admission is computed.
Movement calibration supports handedness+1; a reflected basis is refused before
additional role probes or sealing. Native capture-start uses the driver's clock;
settling validates each observation at receipt and the latest at decision time.
Waypoint execution requires measured camera response and a movement basis,
fresh visual route evidence and current native feedback. Interaction mode uses
the existing native/input calibration gates and leaves scan scheduling idle.
The engine and interaction producers share one capture/action fence; stop
revokes without waiting for it. Calibration measures repeated forward movement
at two headings, backward and both strafe directions within the cumulative
two-unit bound. Its technical default is 0.03 seconds, independent of human
preference minimums. Each physical commitment reserves two later 1 Hz native
publications plus jitter/cleanup time. Server budgets are 30 seconds for key and
camera intents, 90 seconds for movement calibration and 20 seconds for a waypoint;
CLI timeouts add 5 seconds for response delivery.

The session config selects `pointer_profile`, `camera_profile` and `move_profile`
as `"baseline"` (also the policy when omitted) or an absolute profile-file path.
Selected files must validate and match their role. `motion-profile build/show/reset`
manage bounded summaries from explicitly supplied demonstrations; importing numbers
does not establish live human calibration. Raw demonstrations are not retained.
Profile documents use strict schema 2. Pointer/camera duration uses a bounded
intercept plus slope times `log2(1 + distance / safe_target_width)`; supplied
summaries fit these coefficients across difficulties. Curvature describes the
peak lateral deviation. MOVE summaries learn a 0.05–0.35-second pulse ceiling,
which combines with measured displacement when choosing a movement pulse.
Older profile schemas require an explicit rebuild.

Source tests and reviews do not establish native acceptance. Current live proof,
remaining calibration requirements and the paused deployment are recorded at the
top of [HANDOFF.md](HANDOFF.md).

## Installed deployment status (2026-10-15)

Game, companion, API and database run on Linux host `3080servermach`; the repository is at
`/home/dev/repos/pegasus`. WoW 1.60.1 build 70374/interface 16001 runs locally through
Lutris/Wine. Auctionator 341 is installed with full autoscan disabled. `Crowley` is a repo
symlink and generated `Crowley_Data` has the curated 428-active-ID, 900-second, 20-level plan.
The house is `beta-normal-alliance`; Sunshine and the fullscreen watcher are disabled. The
companion is active. Compose needs `--env-file deploy/.env` from the repo root.

The database contains six accepted sweeps, 2,568 observations and 5,726 captured price rows.
Full native verification sweep `beta-normal-alliance-1792040351-Arthur-6643` ran from
2026-10-15 04:59:11 to 05:07:15 UTC (484 seconds), queried all 428 active IDs with zero
incomplete or unqueried items, and captured 2,889 rows across 271 row-bearing IDs and
125,395 units. That includes 306 full commodity observations (1,328 rows), 23 bounded
commodity observations (460 rows), and 99 full item observations (1,101 rows), all under
`beta-normal-alliance`. Native item examples include equipment 873 (`873:l40`), recipe 2555
(`2555:l15`), and containers 4238, 4240, 4241, 4245 and 5765.

A later scheduled sweep, `beta-normal-alliance-1792041251-Arthur-0169`, ran 05:14:11–05:19:36
UTC and stored 1,599 rows. It attempted 293 items (292 successful; one active query was
interrupted by AH closure) and left 135 unqueried when the AH closed after 325 seconds. It is
the latest scan by time; the preceding 428-active-ID sweep is the full verification result.
After the second reload,
the addon reported two uploaded scans cleared and loaded plan `0712de248d42` with 428 active
IDs. A further normal reload persisted the cleared queue; the parent independently verified
zero pending scans on disk. Arthur is parked at Buckler with the AH closed. The malformed
961-row sweep remains intact in private quarantine and was never ingested. The class-aware
query correction is now verified natively. Sol approved the change; 118 addon/core tests and
the 149-pass/15-DB-skip normal suite passed. Full DB testing used a disposable
TimescaleDB container. See the [live validation record](../.archive/live-client/real-validation.md)
for query traces, exact coverage, chronology and preserved payload hashes. The 544-entry
catalog has 428 active IDs in the scan plan; this curated watchlist is not a full-market
claim. Each sweep has a 600-second cap and may leave tail items unqueried. A scan begins every
900 seconds while AH-open. SavedVariables upload after `/reload` or logout, and a subsequent
reload loads the companion acknowledgement.

## Roadmap

The [first-run item catalog](WATCHLIST.md) defines the selective-scanning universe. It is
packaged on the server and delivered as `scanPlan` through addon data. The scanner uses
targeted queries, bounded depth, plan identity and per-item coverage. Partial depth is not
ingested as legacy whole-market statistics.

1. **Beta (until Oct 21):** continue targeted real scans, verify the remaining native
   recipe/container/equipment query paths, confirm event ordering and field layout, and
   keep real scans as test fixtures. Commodity retained-price ingestion is verified.
2. **Pre-launch:** inferred sales (listings that disappear before expiring), the strategy
   engine (vendor flips, deals below market, faction-vs-neutral arbitrage, crafting
   margins), and strategy output in Data.lua and Auctionator lists.
3. **Launch week:** continuous scanning, a "next action" executor button (one protected
   call per click, within strategy limits), and a dashboard.
4. **Weeks 2–4:** demand ranking, anomaly detection, price forecasting once there is
   history, alerts.
