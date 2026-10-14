# Architecture

## Constraints that shape everything

- **No official data feed.** Blizzard's Game Data API has no Forever auction endpoint, so
  every price we have comes from our own in-game scans. Data is only as fresh as our scans
  (one full scan per 15 minutes, while a character stands at an auctioneer).
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
| `C_AuctionHouse.ReplicateItems` full scan, 0-based indices, buyout per auction | `Scanner.lua` | Lua error on `/crowley scan` |
| `GetRealmName()` returns the ruleset (e.g. "PvP") | `Context.lua` | Server rejects the house as unknown |
| English zone names identify neutral houses | `Context.lua` | Use `/crowley set faction neutral` |
| `C_EncodingUtil.CompressString(s, Enum.CompressionMethod.Deflate)` is raw deflate | `Scanner.lua`, `scanformat.py` | Server can't decompress rows |
| Auctionator is installed (hard dependency) | `Crowley.toc` | Addon doesn't load |

`/crowley probe` saves the client's API surface for checking these.

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

The addon keeps at most 6 un-acknowledged scans. The companion acknowledges uploaded scans
through Data.lua, and the addon prunes them on the next load. Uploads are idempotent on
the addon-generated scan id.

## Scan format (v1)

`CrowleyDB.scans[id]` holds the house, raw client context (realm string, zone, build), and
`rows`: raw-deflated, base64-encoded, newline-separated
`itemId,itemKey,quantity,buyout,minBid,bid,timeLeft,owner`. `buyout` is for the whole
auction in copper (0 = bid only), `timeLeft` is 1 (short) to 4 (very long), and `owner` is
empty when the seller is hidden. Rows are only saved once the client has the item's data.

`itemKey` identifies what is being sold: the item ID, plus `:s<suffix>` for random-suffix
gear and `:b<bonus.ids>` for bonus IDs. Items are never keyed by name; names are stored
separately per item key.

## Storage (TimescaleDB)

| Table | Contents |
|---|---|
| `houses` | one row per region/ruleset/faction |
| `scans` | one row per upload, with client context and the raw-archive path |
| `listings` | hypertable, every auction in every scan; compressed after 3 days |
| `item_stats` | hypertable, one row per item key per scan: min, p10, p25, median, market value, quantity |
| `items` | latest name, quality and level per item key |
| `client_probes` | `/crowley probe` reports |

Raw payloads are also archived as gzip JSON under `data_dir/raw/<house>/<day>/` so stats and
models can be recomputed from source. Market value is the quantity-weighted mean of the
cheapest 15% of units, similar to TSM's approach.

## Roadmap

1. **Beta (until Oct 21):** run `/crowley probe` and real scans, confirm the API surface,
   field layout, throttle and compression, and keep real scans as test fixtures.
2. **Pre-launch:** inferred sales (listings that disappear before expiring), the strategy
   engine (vendor flips, deals below market, faction-vs-neutral arbitrage, crafting
   margins), and strategy output in Data.lua and Auctionator lists.
3. **Launch week:** continuous scanning, a "next action" executor button (one protected
   call per click, within strategy limits), and a dashboard.
4. **Weeks 2–4:** demand ranking, anomaly detection, price forecasting once there is
   history, alerts.
