# Crowley handoff

Written 2026-10-14 by the agent that started the project, for the agent taking over on the
server. Read this fully before changing anything. `docs/ARCHITECTURE.md` is the shorter
technical reference; this document adds requirements, history, research and next steps.

### Continuation on the server

The companion now retries stable SavedVariables after transport failures; successful
uploads are not repeated. The first-run item catalog and server delivery are implemented;
see [WATCHLIST.md](WATCHLIST.md) for the canonical data, coverage and management commands.
The scan plan is delivered in addon data and the Lua scanner now performs targeted,
bounded-depth format-2 sweeps with explicit per-item coverage and plan identity. The earlier
assumption that ForeverWowCraft has no backend history is not
established; only its public current plans were inspected. Recipe data must be verified
against Forever's build rather than copied from Classic.

### Format-2 cutover

Before deploying this format-2 addon and server together, run the old addon against the old
server until its SavedVariables have been uploaded and acknowledged. Reload once to write the
old pending scans, let the companion write acknowledgements, then reload a second time and
confirm the old addon's pending queue is empty. Only after that acknowledgement check should
the addon and server be upgraded as one coordinated change. The new server accepts format 2
only; it preserves the already-flushed legacy rows and archives but has no legacy decoder or
full-scan fallback. If the old queue cannot be emptied, stop the cutover and fix that upload
path before collecting new sweeps.

---

## 1. What we are building and why

The user (Kyle) wants a private gold-making platform for the auction house in
**World of Warcraft: Forever**, plus an addon to act on it in game:

1. **Pull live AH data** and store retained observation history with explicit coverage.
2. **Make gold from it** using:
   - arbitrage, including faction houses vs neutral houses and vendor flips
   - high-demand items
   - ML prediction of price increases
   - anomaly detection
3. **Execute in game seamlessly** through the **Auctionator** addon: buy and sell lists the
   backend computes, ready to use the next time the user is at the AH.

The first milestone was the foundation: targeted scanning, retained observations, and the round
trip between game and server. Strategies come next.

### Explicit user requirements (from the conversation)
- **Private tool, single user.** No accounts or multi-tenancy, and no protection against
  poisoned crowdsourced data. Design so it *could* open up later, but don't build for that.
- **Tailscale** connects the game machine to the server that runs the calculations and
  hosts the data. During the first session the game and server were the same machine. **The
  user is now deploying the backend to a dedicated server**, so expect them to become
  separate machines.
- **The game runs on Linux under Wine.**
- **Region, ruleset and faction are chosen at scan time.** The user must be able to switch
  between houses freely. The database keeps each house separate and never mixes them.
- **No fallbacks** (strong preference, stated explicitly). Keep the codebase clean: assume
  one way things work, encode only that, let it fail loudly, and fix it if wrong. No
  "try A then B", no optional-dependency checks, no defaults that hide missing data, no
  multi-format decoders. Write every assumption down (see §6).
- The user is **in the Forever beta** and can test in game.
- Use subagents for investigation-heavy work.
- Commit or push only when the user asks.

---

## 2. Timeline (critical)

| Date | Event |
|---|---|
| 2026-09-12 | WoW Forever announced at BlizzCon |
| 2026-09-17 → **2026-10-21** | Beta. **The only chance to test the addon against a live AH before launch** |
| 2026-10-27 → 11-03 | Name reservation (no AH) |
| **2026-11-04, 3pm PT** | Launch. The user first thought it was "in two weeks"; the real date is Nov 4 |

Launch week is when prices are highest and most volatile (fresh economy, no WoW Token), so
the pipeline must be reliable before then and the first strategies ready.

---

## 3. Research findings (2026-10-14)

Three research agents covered the game, foreverwowcraft.com, and Auctionator plus the
addon data flow. Below, "confirmed" means from official or primary sources; the rest is
reported by fans or the press.

### 3.1 WoW Forever
- A third permanent WoW version alongside Modern and Classic. It's a reimagined original
  Azeroth: level 60 cap, new zones, a new Skyborne race. PC and Mac, included with the
  subscription. Confirmed.
- **Realmless** (confirmed by Wowhead from a Blizzard announcement). Players pick a region
  and a ruleset: Normal, PvP, RP, and Hardcore after launch. Factions can't group with each
  other.
- **AH structure** (reported): one house per (region, ruleset, faction), plus neutral goblin
  houses in Booty Bay, Gadgetzan and Everlook. Faction houses take a 5% cut, neutral 15%
  (Classic Era rules). Deposits are based on vendor price and lost if the item doesn't sell.
  Listing durations are reported inconsistently.
- **Client:** retail-derived. Blizzard said it shares "the vast majority of APIs available
  in 12.1.5". Beta interface 16001, build 1.60.x. The TOC suffix is currently `_Camelot`,
  which Blizzard says will be renamed. Some old globals such as `GetItemInfo` are gone; use
  `C_Item.*`. Midnight-style combat addon restrictions apply.
- **AH API:** retail-style (commodities bought by quantity), so `C_AuctionHouse` targeted
  item-key queries are used. Result event freshness, metadata and pagination behavior remain
  beta assumptions until a live client test.
- **No Blizzard Game Data API for Forever auctions.** Nothing documents one, and the client
  "exposes no API". All data has to come from in-game scans. The classic API was also
  unreliable (frequent 404s), and a realmless game doesn't fit its "connected-realm" model.
- **No WoW Token, no boosts.** Gold supply comes only from farming, so prices should start
  high and fall over the first weeks.
- **Temporary Economy Hold:** Blizzard freezes trade, mail and AH access for accounts with
  suspected real-money-trading gold flows, and warns of false positives. Very large or odd
  gold movements carry account risk. About 3,700 beta accounts were banned for RMT.
- **Reported economy notes:**
  - A vendor next to the Black Market AH sells Black Lotus and Arcane Crystal at 50g, which
    caps their price.
  - Black Market AH is bid-only, 100g–3,000g.
  - In beta, Dungeon Set 1 pieces sold around 100g, low-level blues 10–25g, raw materials
    for silver.
  - Beta gold and characters are wiped at launch.
- **Automation rules:** buying, bidding, posting and cancelling need a hardware event
  (a real click or key press), one protected call per click. Input injection, memory
  reading and unattended buying get accounts banned. Reading SavedVariables and writing
  addon data files from outside the game is the accepted pattern (TSM's desktop app does
  it).
- Sources include Wowhead, Blizzard news, Icy Veins, PC Gamer, warcraft.wiki.gg TOC_format,
  and the Blizzard forums.

### 3.2 foreverwowcraft.com (reference site)
- **Narrow product:** the cheapest route to level each profession from 1 to 300 per
  realm/faction, using player-uploaded AH scans. No price history, flipping or alerts.
- **Data:** players scan in game with their addon, and a small Windows "helper" program
  uploads the SavedVariables and writes computed routes back into the addon. The same
  pattern as ours.
- **Backend:** no API at all. An offline optimizer writes static JSON files
  (`/data/houses.json`, `/data/<house>/manifest.json`, `/data/<house>/plans/*.json`,
  `/data/names/<locale>.json`) and Cloudflare serves them. Plain ES5 single-page app, with
  AdSense and Patreon.
- **Weaknesses:**
  - Keys items by **English name** (no item IDs).
  - Keeps only a single snapshot, so no history.
  - Depends on volunteers; 2 of its 3 houses were about 14 hours stale.
  - No defense against poisoned data.
- **Ideas worth copying:**
  - Static JSON on a CDN, if we ever publish a site.
  - Costing that walks up the price ladder, so buying more units costs more.
  - Sell-probability weights: reagents 0.9, consumables 0.8, green gear 0.35, blue gear 0.5.
  - Auctionator import strings.
  - A 15-minute snapshot cooldown and a 5% AH cut.
- Its downloaded files are on the old machine only; don't rely on them.
- **Other Forever AH tools:** Hammerprice, Grimlight Auctions, AHledger (web plus sync app;
  counts 18 houses across US/EU/CN), auxForever, Forever Guide, bootybaybroker.com/forever.
  All rely on in-game scans because addons can't reach the network.

### 3.3 Auctionator (integration target)
The GitHub repo `github.com/Auctionator/Auctionator` returned 404 when we checked. We read
v321 (May 2026) from a downloaded copy. Key facts:
- **API** `Auctionator.API.v1.*`: the first argument is always a caller ID string (we use
  `"Crowley"`), and errors are raised as Lua errors. Functions we use or will use:
  - `ConvertToSearchString(caller, {searchString, isExact, maxPrice(copper), quantity, ...})`
  - `CreateShoppingList(caller, name, searchStrings)`: replaces any list with the same name.
  - Also available: `GetAuctionPriceByItemID` / `GetAuctionPriceByItemLink`,
    `MultiSearch` / `MultiSearchExact` (AH must be open), `RegisterForDBUpdate`, and
    `GetShoppingListItems` / `AlterShoppingListItem` / `DeleteShoppingListItem`.
- **Search string:** 14 fields separated by `;`:
  `"Name";category;minIlvl;maxIlvl;minLvl;maxLvl;minCLvl;maxCLvl;minPrice;maxPrice;quality;tier;expansion;quantity`.
  Prices here are in **gold** (copper / 10000, decimals allowed). Quotes around the name
  mean an exact match.
- **Import format** (paste into Auctionator's import box): one list per line,
  `ListName^item1^item2...`.
- Its own price database is thin: one minimum price and maximum quantity per day, partly
  stored as compressed binary (CBOR). **Don't use it as a data source**; Crowley stores targeted retained observations.
---

## 4. Design decisions (and why)

| Decision | Reason |
|---|---|
| In-game addon scan → SavedVariables → companion → server | Addons have no network or file I/O, and there's no official API. SavedVariables are written only on `/reload`, logout or exit |
| Server → companion → `Crowley_Data/Data.lua` → game | The only way to get data into the game. Addon files are read only at login or `/reload` |
| Companion **polls** file mtime and size, and waits until they hold still for one interval | Wine prefixes and network mounts make inotify unreliable, and we must never read a half-written file |
| Upload acknowledgement through `Data.lua` (`ackedScans`); the addon prunes acked scans on load and keeps at most 6 unacked | Keeps SavedVariables small without the companion ever writing to the game's own file |
| House = `(region, ruleset, faction)` with faction in alliance/horde/neutral. The key looks like `us-normal-horde`, is decided **in game at scan time** (auto-detected, overridable with `/crowley set`), and is stored on every scan | Realmless game, plus the user's requirement to switch houses freely. Raw client context is stored too so attribution can be audited |
| Items keyed by `itemKey` = item ID, plus `:s<suffix>` for random-suffix gear, `:b<sorted bonus ids>`, `:l<itemLevel>`, and `:p<battlePetSpeciesID>` when nonzero. Never by name | Names are locale-dependent and ambiguous (foreverwowcraft's weakness); raw key fields remain alongside the canonical key |
| Store the cheapest 20 distinct unit-price levels plus every row at the retained boundary | Preserves explicit bounded coverage and row identity without claiming whole-market supply |
| Public listing churn is a separate uncalibrated proxy; own Sold evidence is separate | A disappearance is not a confirmed sale and no sale probability is inferred |
| Rows are raw-deflated and base64-encoded in SavedVariables | Payload size depends on retained rows, variants, links and owners; the representative 428-item sample is documented in WATCHLIST.md |
| Python 3.12, FastAPI, psycopg3, **PostgreSQL 16 + TimescaleDB 2.17.2** | Python suits ML. Timescale gives time-partitioned tables plus compression for listing data |
| Docker Compose for db + server; the companion runs on the game machine under systemd | The companion must sit next to the Wine game folder |
| Single bearer token, compared in constant time | Single user over Tailscale |
| Database bound to localhost only; the API binds to `CROWLEY_BIND` (localhost or the Tailscale IP) | The only network surface is the API |
| SavedVariables parser written in pure Python, never executing Lua | The files come from the game folder |
| Raw scans archived as gzip JSON under `data_dir/raw/<house>/<day>/` | Stats and models can be recomputed from source |
| `Crowley` addon is symlinked from the repo; `Crowley_Data` is a real copied folder | Repo edits show up after `/reload`; companion writes must not dirty the repo |
| Auctionator and Crowley_Data are **hard** TOC dependencies | The no-fallback rule |
| Only the generic `Crowley.toc` (no `_Camelot`/`_Forever` copies) | The client loads the generic TOC when no flavor-specific one exists |

---

## 5. Current state

### Built and tested
```
addon/Crowley/          Core.lua (events, SavedVariables, prune), Context.lua (house detection),
                        Scanner.lua (targeted watchlist scan), Bridge.lua (Auctionator lists),
                        Probe.lua (/crowley probe), Commands.lua (/crowley ...)
addon/Crowley_Data/     Data.lua placeholder; the companion overwrites it
src/crowley/core/       savedvars.py (parser), scanformat.py (strict format-2 validation), volume.py, house.py, luawriter.py
src/crowley/server/     app.py (FastAPI), ingest.py, db.py (migration runner), migrations/001_init.sql
src/crowley/companion/  sync.py (poll/upload/write Data.lua), config.py, __main__.py (CLI)
deploy/                 docker-compose.yml, Dockerfile, .env.example, crowley-companion.service
tests/                  wow_harness.py runs the REAL addon Lua under Lua 5.1 (lupa) with a fake WoW API
```

- **In-game commands:** `/crowley scan [force]`, `status`, `set <region|ruleset|faction> <value|auto>`,
  `lists`, `probe`.
- **API** (every endpoint except `/healthz` needs `Authorization: Bearer <token>`):
  - `GET /healthz`
  - `POST /v1/scans`: upload a scan; idempotent on scan id.
  - `POST /v1/probes`
  - `GET /v1/houses`
  - `GET /v1/houses/{key}/latest?search=&limit=`
  - `GET /v1/houses/{key}/items/{item_key}/history?days=`
  - `GET /v1/houses/{key}/items/{item_key}/volume?hours=`
  - `POST /v1/addon-data`: returns `{generatedAt, ackedScans, scanPlan, shoppingLists}`.
    `shoppingLists` is always empty until the strategy engine exists.
- **Companion CLI:** `crowley-companion run|once|doctor|install-addon`.
  - Config is in `~/.config/crowley/companion.toml`, or the file named by
    `CROWLEY_COMPANION_CONFIG`. Fields: `wow_dir`, `server_url`, `api_token`,
    `poll_seconds`, `refresh_minutes`.
  - State is in `~/.local/state/crowley/companion-state.json`.
- **Tests:** the real Lua addon harness covers structured API calls, fresh result barriers,
  depth boundaries, paging, throttle/cap behavior, logout/closure, owned completion and
  SavedVariables lifecycle. Run `uv run pytest`; database tests require
  `CROWLEY_TEST_DATABASE_URL` as described in the README. A live Forever client capture is
  still required before treating client event ordering as verified.

### Not yet verified against the real client
Nothing has run in the real game yet. See §6.

### Not built yet
- Inferring sales from listings that disappear.
- The strategy engine and real shopping lists.
- The "next action" executor button.
- A dashboard.
- ML forecasting, anomaly detection, alerts.
- Backups and monitoring.

---

## 6. Client assumptions to verify on the beta (before 2026-10-21)

Each one is encoded as the single path in the code. If one is wrong, fix that path; don't
add a second one.

| Assumption | Code | Symptom if wrong |
|---|---|---|
| Interface 16001; the plain `Crowley.toc` loads | `addon/*/*.toc` | Addon missing or marked out of date |
| `MakeItemKey`, `GetItemKeyInfo`, `SendSellSearchQuery`, matching result events and owned-query APIs exist | `Scanner.lua` | Lua error or explicitly incomplete observations |
| Search result events carry the active item key; stale, unrelated or no-payload events are ignored | `Scanner.lua` | The item remains incomplete until a matching response arrives or its timer expires |
| `GetCurrentRegionName()` returns e.g. "US" | `Context.lua` | Server rejects the house |
| `GetRealmName()` returns the ruleset, e.g. "PvP" or "Normal" (lowercased, letters only) | `Context.lua` | Server rejects the house (`unknown ruleset`). Fix the detection; meanwhile `/crowley set ruleset ...` |
| English zone or subzone text identifies the neutral houses | `Context.lua` | Neutral scans saved under a faction house |
| `C_EncodingUtil.SerializeJSON`, raw-deflate `CompressString` and standard `EncodeBase64` work | `Scanner.lua`, `scanformat.py` | Server returns 422 and the companion stops on that sweep |
| The client JSON codec preserves empty keyed collections as JSON objects | `Scanner.lua` | The strict server rejects an empty rows/observations/owned collection encoded as an array |
| SavedVariables strings use `\n` or backslash-newline and `\ddd` escapes | `savedvars.py` | Companion stops with a parse error and line number |
| Auctionator v1 API as described in §3.3 | `Bridge.lua` | Lua error when the AH opens and lists exist |

**Beta checklist for the user:**
1. Install and configure the companion (§7).
2. In game, run `/crowley probe`, then `/reload`. The probe lands in the `client_probes`
   table. Inspect `probe->'namespaces'` and `probe->'context'`, including the realm string.
3. At an auctioneer, run `/crowley status`, check the house key and loaded plan, then
   `/crowley scan`. Wait for "sweep saved", then `/reload`.
4. Check the companion log and `GET /v1/houses`.
5. Repeat at a neutral house and on the other faction.
6. Keep one or two real raw format-2 sweeps from `data_dir/raw` as **test fixtures** (copy
   them into `tests/fixtures/`), and add a test that validates exact coverage and identity.

---

## 7. Deployment (server + separate game machine)

**On the server (database + API):**
```sh
git clone <repo> ~/repos/crowley && cd ~/repos/crowley
cp deploy/.env.example deploy/.env
# Fill in CROWLEY_API_TOKEN and CROWLEY_DB_PASSWORD:
#   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Set CROWLEY_BIND to the server's Tailscale IP: tailscale ip -4
chmod 600 deploy/.env
docker compose -f deploy/docker-compose.yml up -d --build
curl http://<tailscale-ip>:8080/healthz
```
The first start logs a few "connection refused" errors while TimescaleDB restarts after
initializing. The pool retries, then applies migrations. That's normal.

**On the game machine (Linux + Wine):**
```sh
git clone <repo> ~/repos/crowley && cd ~/repos/crowley && uv sync
mkdir -p ~/.config/crowley && cat > ~/.config/crowley/companion.toml <<'TOML'
wow_dir    = "/home/<user>/.wine/drive_c/Program Files (x86)/World of Warcraft/<flavor folder, e.g. _forever_>"
server_url = "http://<server tailnet name or 100.x IP>:8080"
api_token  = "<same CROWLEY_API_TOKEN>"
TOML
uv run crowley-companion install-addon
uv run crowley-companion doctor
cp deploy/crowley-companion.service ~/.config/systemd/user/
systemctl --user daemon-reload && systemctl --user enable --now crowley-companion
```
- The game machine needs the repo because `install-addon` symlinks `addon/Crowley` from it
  (`REPO_ADDON_DIR` resolves relative to the editable install).
- The systemd unit assumes the repo is at `~/repos/crowley` and `uv` is at
  `~/.local/bin/uv`.
- Auctionator must be installed in the game.

**Operations:**
```sh
docker compose -f deploy/docker-compose.yml logs -f server
docker compose -f deploy/docker-compose.yml exec db psql -U crowley
docker compose -f deploy/docker-compose.yml up -d --build    # redeploy after pulling code
docker compose -f deploy/docker-compose.yml down -v          # DESTROYS ALL DATA
```

---

## 8. Gotchas

- **Schema changes are now new migrations.** `001_init.sql` was edited in place during
  development because there was no real data. From the moment the server holds real data,
  add `002_*.sql` and so on. The runner applies files in name order and records them in
  `schema_migrations`.
- **Timing:**
  - SavedVariables are written only on `/reload`, logout or exit, so a scan reaches the
    server only after one of those.
  - `Data.lua` reaches the game only on the next login or `/reload`.
- **Cadence and caps:** starts are 15 minutes apart while the AH is open. A force scan starts
  the same serialized pipeline immediately but still respects the 100-message rolling throttle,
  30-second per-item budget, 10-page cap and 600-second sweep cap. Capped, timed-out, logout and
  closure work is retained as incomplete or unqueried coverage and the rotating cursor advances.
- **The companion is strict by design:** a parse error or a rejected upload (4xx/5xx) stops
  it, and systemd restarts it. Only connection failures are retried quietly. Fix the root
  cause rather than adding tolerance.
- **Test harness:** the lupa runtime uses `encoding="latin-1"` so Lua byte strings
  round-trip. Python callables cross the boundary as latin-1 `str`.
- `/v1/houses/{key}/items/{item_key}/history` defaults to the last 7 days.
- **Auctionator search strings** take max price in gold, not copper.
- **Neutral houses** cost 15%, not 5%. Every arbitrage calculation must use `House.ah_cut`.
- **Market reports:** new volume reports expose explicit coverage, bounded depth and null
  rates where grouping or evidence is unknown. Legacy `item_stats` rows remain historical and
  are not used for new observation comparisons.

---

## 9. Roadmap / future goals

Priority order:

1. **Beta verification (until 10-21):** run the §6 checklist, fix any wrong assumptions,
   and save real fixtures.
2. **Backups:** nightly `pg_dump` of the database plus a copy of the `crowley-raw` volume.
   Also alert or log loudly when no scan arrives for a house within N hours.
3. **Inferred sales:** compare consecutive scans of a house. An auction that disappears
   before its time-left band could have expired counts as a probable sale; one that
   expires doesn't. This gives sell-through rate and sales per day per item, which is the
   demand signal. Needs stable captured result IDs plus owner, quantity, price and variant
   identity across scans; Crowley currently reports this as an uncalibrated public-market
   proxy and never calls it confirmed sales.
4. **Strategy engine (server), each producing shopping lists in `/v1/addon-data`:**
   - **Vendor flip:** buyout per unit below the vendor sell price. Needs vendor prices;
     add a reviewed vendor-price table; client result fields do not provide vendor prices.
   - **Deals:** listings well below the house market value or a rolling median.
     Robust z-score / MAD.
   - **Faction vs neutral arbitrage:** buy in one house, sell in another, net of 5%/15% cuts
     and deposit risk. The neutral house is shared across factions, which makes it the
     natural bridge.
   - **Crafting margin:** needs recipe data.
   - **Depth-aware costing:** price up the ladder for multi-unit buys (foreverwowcraft's
     idea).
   - **Launch dynamics:** prices start high and fall as gold enters the economy. Sell into
     early demand and buy after it eases.
5. **Executor in game:** a "next action" button. One protected call per click, and each
   click checked against the strategy limits (max price, quantity) before it calls
   Auctionator or `C_AuctionHouse`. No automation of the clicks themselves; that's a ToS
   red line.
6. **Dashboard:** a minimal view of houses, deals and item history. Could be static JSON
   plus a small page, foreverwowcraft-style.
7. **ML and anomaly detection** once there are 1–2 weeks of history: price-direction
   forecasting (e.g. gradient boosting on lagged stats, quantity, sell-through, time of
   day / day of week), anomaly alerts, and alert delivery (push or mail).
8. **Account safety:** keep gold flows looking normal given the Economy Hold. Avoid huge
   single trades in launch week.

---

## 10. Working agreements

- No fallbacks (see §1). Write every new assumption into §6 / ARCHITECTURE.md.
- Match existing style: compact, commented where non-obvious, no speculative abstractions.
- Run `uv run ruff check . && uv run ruff format --check . && uv run pytest` before
  declaring work done. Run the database tests against a throwaway `crowley_test` database.
- Ask before committing or pushing, and before destructive operations
  (`down -v`, `TRUNCATE`, dropping data).
