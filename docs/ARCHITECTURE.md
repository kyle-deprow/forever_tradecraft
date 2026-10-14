# Architecture

## Constraints that shape everything

- **No official data feed.** Blizzard's Game Data API has no Forever auction endpoint, so
  every price we have comes from our own in-game observations. Starts are 900 seconds apart
  while a character stands at an auctioneer; all 428 items may not finish every sweep. Each item
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

## Client assumptions (verify on the beta)

| Assumption | Where | If wrong |
|---|---|---|
| Interface 16001; a plain `Crowley.toc` loads | `addon/*/*.toc` | Addon missing from the list |
| `MakeItemKey` + `SendSellSearchQuery` and matching result events | `Scanner.lua` | Lua error or incomplete observation on `/crowley scan` |
| `SendSellSearchQuery` uses a structured cleared `ItemKey`, and matching ADDED/UPDATED events arrive after the throttled-message sent and response barriers; `hooksecurefunc` observes `SendSellSearchQuery`, `SendSearchQuery`, and pagination calls so stale, unrelated, foreign same-key and no-payload events are ignored | `Scanner.lua` | The item remains incomplete until its response timeout |
| `GetRealmName()` returns the ruleset (e.g. "PvP") | `Context.lua` | Server rejects the house as unknown |
| English zone names identify neutral houses | `Context.lua` | Use `/crowley set faction neutral` |
| `C_EncodingUtil.SerializeJSON` preserves keyed collections and `CompressString(s, Enum.CompressionMethod.Deflate)` is raw deflate | `Scanner.lua`, `scanformat.py` | Server rejects the strict payload or can't decompress rows |
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

## Scan format (v2)

`CrowleyDB.scans[id]` holds an envelope with `format=2`, integer sweep bounds, house/context,
row and observation counts, and one raw-deflated/base64 JSON payload. The payload has exactly
`planHash`, canonical string `planJSON`, object-keyed `observations`, and object-keyed `owned`.
Each planned item has a query window, kind, coverage (`full`, `bounded`, `incomplete` or
`unqueried`), source completeness, rational cutoff/witness and retained `row:<n>` objects.
Commodity price is unit copper; item price is whole-auction copper and quantity, represented as
a reduced rational unit price. Unsafe cross-products produce `numeric_range`; bid-only rows do
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

Format-2 envelopes are archived as gzip JSON under content-addressed
`data_dir/raw/format2/<digest-prefix>/<digest>.json.gz` so observations can be replayed without
trusting a UID path. Legacy archives remain where they were written. New depth and volume
reports never use legacy whole-market statistics.

## Roadmap

The [first-run item catalog](WATCHLIST.md) defines the selective-scanning universe. It is
packaged on the server and delivered as `scanPlan` through addon data. The scanner uses
targeted queries, bounded depth, plan identity and per-item coverage. Partial depth is not
ingested as legacy whole-market statistics.

1. **Beta (until Oct 21):** run `/crowley probe` and real scans, confirm the API surface,
   field layout, throttle and compression, and keep real scans as test fixtures.
2. **Pre-launch:** inferred sales (listings that disappear before expiring), the strategy
   engine (vendor flips, deals below market, faction-vs-neutral arbitrage, crafting
   margins), and strategy output in Data.lua and Auctionator lists.
3. **Launch week:** continuous scanning, a "next action" executor button (one protected
   call per click, within strategy limits), and a dashboard.
4. **Weeks 2–4:** demand ranking, anomaly detection, price forecasting once there is
   history, alerts.
