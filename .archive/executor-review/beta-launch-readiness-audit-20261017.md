# Beta-to-launch readiness audit — 2026-10-17

## Assessment

Crowley's collection path is close to beta qualification, but Crowley is not yet a
launch-ready strategy product. The current release is pinned correctly to client
`1.60.1.70450`, yet the database contains no observation from that build or current
plan. The server has conservative churn and own-sale evidence machinery, but
`/v1/addon-data` still returns `shoppingLists: []` unconditionally and there is no
recipe graph or strategy module.

The four remaining beta days should be used for facts that cannot be reconstructed
offline: current-build native sweeps, consecutive same-regime intervals, and exact
launch identity during the production-hardware stress test. Strategy, recipe schema,
backup/recovery, and deployment cutover work can proceed without consuming game time.

## Evidence behind that assessment

- The user reports four beta days remain. The audit initially cited the
  [official product page](https://worldofwarcraft.blizzard.com/en-us/forever/) for
  October 21 beta closure and November 4 launch; parent verification received
  HTTP403, so those product-page dates remain unverified in this checkpoint.
  More urgently, Blizzard's October 21 stress test will run on the regional hardware
  intended for launch for only a few hours, then be wiped and return to beta
  ([official blue post](https://us.forums.blizzard.com/en/wow/t/wow-forever-stress-test-october-21/2383617)).
  Parent verified the updated blue post directly: Americas/Oceania starts
  October21 at14:00PDT (16:00America/Chicago). The old October19 URL redirects
  to October21; do not use its stale slug or embedded article preview as the schedule.
  That is the best pre-launch opportunity to verify region, ruleset/realm, build, and
  interface identity. A general end-of-beta character/economy wipe is not stated in
  the official sources reviewed here; treat it as expected but unconfirmed.
- A read-only database transaction found one house, `beta-normal-alliance`, with
  8 sweeps, 3,424 observations, and 11,139 captured rows. Every sweep is build
  `70374` under old plan hash `0712de…53a7c`; there are **zero** build-70450/current
  plan `f1745…31d4` sweeps. Three older sweeps completed all 428 observations, but
  only the last pair is close enough to contribute a consecutive interval under the
  1,800-second comparison limit. There are 8 owned observations, 3 full, and zero
  owned rows or `own_sale_evidence` rows.
- The release gate is intentionally strict: the addon hard-codes build 70450,
  interface 16001, revision 2, and the reviewed plan/catalog hashes
  (`addon/Crowley/Scanner.lua:16-25`). `docs/HANDOFF.md:43-45` accurately says no
  qualified 70450 scan has run.
- House, build, and plan separation already have good foundations. Sweeps persist
  `client_version`, `client_build`, `interface`, and `plan_hash`
  (`src/crowley/server/migrations/002_market_observations.sql:10-31`), and volume
  comparisons reject house, build, and plan changes
  (`src/crowley/core/volume.py:244-277`). Launch data will use a non-beta house key,
  so beta rows can remain as history without becoming launch priors.
- Launch attribution remains an assumption. `Context.lua` accepts only literal
  launch realm names `Normal`, `PvP`, `RP`, and `Hardcore`
  (`addon/Crowley/Context.lua:28-35,51-63`); the only live-verified identity is
  `Classic Beta PvE 2`/region 110 (`docs/HANDOFF.md:801-805,835-837`). Blizzard calls
  the roleplaying ruleset “Roleplaying,” so the native `GetRealmName()` spelling must
  be observed rather than inferred.
- The catalog is broad as a scan universe, not a recipe or trade model. It has 544
  items: 428 active (352 core, 76 discovery), 74 research, and 42 excluded. Active
  membership spans all listed professions, but all 428 active items still have
  `auction_eligibility: unverified`. Historical scans have produced at least one row
  for 274 active IDs: 40/46 components, 39/67 consumables, 11/16 containers, 11/25
  enhancements, 3/4 equipment, 34/74 recipe items, and 136/196 trade goods. A row is
  evidence that the item was offered, not that it sold or has stable liquidity.
- Profession memberships overlap and do not encode recipes
  (`src/crowley/core/watchlist.py:51-64`). The repository explicitly lacks ingredient
  quantities, output yields, cooldowns, skill gates, and acquisition requirements
  (`docs/WATCHLIST.md:81-91`). ForeverWowCraft publishes profession plans and prices,
  but those are candidate inputs rather than proof of a complete or learnable recipe
  graph ([direct source](https://foreverwowcraft.com/)).
- Public-market turnover is deliberately conservative. Commodity changes are called
  depletion/replenishment, individual disappearance is labelled `UNCALIBRATED`, and
  actual-sales estimates remain null (`src/crowley/core/volume.py:339-373,427-465,535-570`).
  Own `sold` rows are separately deduplicated on ingestion
  (`src/crowley/server/ingest.py:122-210`). Do not convert captured quantity,
  row count, disappearance, or beta price into sales volume.
- Strategy delivery plumbing exists but has no producer. The companion refreshes
  `Data.lua` (`src/crowley/companion/sync.py:123-157`) and the addon can create
  house-filtered Auctionator lists (`addon/Crowley/Bridge.lua:9-29`), while the server
  hard-codes an empty list (`src/crowley/server/app.py:347-370`). There is no positive
  end-to-end shopping-list test. The installed Auctionator API accepts `term.maxPrice`
  in copper and serializes it to gold by dividing by 10,000; the repository note at
  `docs/HANDOFF.md:925` saying the API takes gold is misleading and must not drive
  strategy output.
- Deployment has named database and raw-data volumes
  (`deploy/docker-compose.yml:4-44`) but no backup/restore implementation; the only
  backup text is a roadmap item (`docs/HANDOFF.md:937-940`). The example session
  profile is beta-specific (`deploy/crowley-session.example.toml:11-33`), and the
  checked-in companion unit still uses `%h/repos/crowley`
  (`deploy/crowley-companion.service:8-10`) while the accepted live checkout is
  `/home/dev/repos/pegasus` (`docs/HANDOFF.md:56-60`).

## Work that must use the remaining beta window

### P0 — October 21 production-hardware identity capture

During the official stress-test window, run the existing `/crowley probe` path before
any scan and preserve the uploaded probe plus raw SavedVariables fixture. Record exact
`GetCurrentRegion()`, `GetCurrentRegionName()`, `GetRealmName()`, faction, zone/subzone,
client version/build/interface, portal, locale, and relevant namespace availability.
Exercise `Context.House()` without overrides. If the launch auction house is reachable,
run one bounded current-plan sweep and retain its upload/ACK; do not make AH access a
condition for completing the identity probe. Acceptance is an exact observed launch
mapping or an explicit fail-closed attribution error, followed by reviewed fixture tests.

### P0 — qualify the current 70450 release

Complete the already-defined three 428-item sweeps at seed/+900/+1800 seconds, each
under plan `f1745…31d4`, with upload within 60 seconds and loaded acknowledgements;
verify no unintended fourth sweep. Preserve at least one complete raw envelope as a
strict fixture. Report full/bounded/incomplete/unqueried counts, row-bearing IDs,
captured units, query failures, exact house/build/interface/plan, and ACK timestamps.
Price totals are observations, not a launch forecast.

### P1 — collect consecutive evidence, not isolated totals

After the three-sweep gate, use remaining ordinary beta AH time for uninterrupted
same-house/build/plan 15-minute sequences. A useful minimum is eight completed sweeps
in one block, yielding seven adjacent intervals for coverage/exclusion analysis. Record
actual starts, query windows, cursor rotation, failures, and the volume report's valid
and excluded intervals. Never describe depletion or disappearance as sales. Favor
continuity over adding more one-off snapshots.

### P1 — close live catalog and owned-path evidence gaps

Generate a reproducible qualification report from the retained sweeps: positive
row-bearing IDs by category/profession, never-seen IDs, query kind, coverage, and
current build. Promote an item's auction eligibility only from positive live evidence;
an empty result proves absence within that observation, not non-tradeability.

If a normal user-owned auction is naturally available, capture one full owned query
and subsequent `sold` evidence to validate the existing ingestion path. Do not create a
risky or economically meaningful trade solely to make this row nonzero. Neutral/Horde
collection is useful for future arbitrage only if those houses are actually reachable;
otherwise record them as unqualified rather than synthesizing cross-house data.

## Work that should run offline in parallel

### Slice A — smallest end-to-end strategy: conservative commodity deals

Own: new `src/crowley/core/strategy.py` and `tests/test_strategy.py`; bounded changes to
`src/crowley/server/app.py`, `tests/test_server.py`, `tests/test_companion.py`, and
`tests/test_addon.py`. Touch `addon/Crowley/Bridge.lua` only if strict payload validation
is needed. This slice should deliberately exclude crafting, vendor flips, arbitrage,
forecasting, and public-sales estimates.

The engine should:

1. Partition inputs by exact `(house, client_version, client_build, interface, plan_hash)`
   and require at least three compatible completed sweeps. A launch house must return no
   candidate from beta history.
2. Admit only current commodity observations with proved full/bounded coverage; bounded
   candidates and their reference price must remain inside the proved cutoff. Failed,
   unqueried, stale, mixed-plan, mixed-build, and variant-ambiguous inputs fail closed.
3. Use an explicitly reviewed policy for discount threshold, per-item quantity, and
   spend ceiling. Do not derive quantity from captured supply or churn. Start at a hard
   quantity cap of one unless the reviewed policy says otherwise.
4. Emit a deterministic house-filtered Auctionator list with integer-copper `maxPrice`.
   Keep the computed reference, source sweep IDs, regime identity, coverage, and reason
   in a server-side candidate response/receipt so a list is auditable.
5. Prove the real chain in tests: market envelopes -> strict ingestion -> candidate ->
   `/v1/addon-data` -> companion `Data.lua` -> real Lua bridge contract, including exact
   gold-string serialization by Auctionator's `maxPrice / 10000`, empty output on every
   insufficient-evidence case, and house filtering.

This produces a useful launch capability as soon as three launch sweeps exist without
pretending to know demand. The latest/history API should also expose the stored build,
interface, and plan identity, or the strategy query must retain that identity internally;
the current latest response selects `plan_hash` but omits client build/interface
(`src/crowley/server/app.py:202-211`).

### Slice B — recipe catalog foundation, not premature crafting recommendations

Own: new `src/crowley/core/recipes.py`, a source-controlled recipe-data artifact, and
focused validation/coverage tests. Store output item and quantity, each reagent ID and
quantity, profession, skill gates, cooldown, acquisition/learnability status, vendor
components/prices with provenance, source build, review date, and explicit unknowns.
Reject incomplete records from margin calculation. Produce a coverage report across the
eight crafting professions and resolve a small reviewed cross-profession set first; do
not claim the 428-item membership list is a recipe graph. A crafting candidate may be
added only when every input/output quote has current compatible launch coverage and all
recipe quantities/costs are verified.

### Slice C — launch cutover and recovery

Own deployment/runbook files only, outside the active telemetry-region freeze.

- Add a repeatable, secret-free `pg_dump` plus raw-volume backup command and a restore
  drill into disposable volumes. Validate row counts, plan hashes, raw archive digests,
  and authenticated health after restore. Preserve the companion config/state,
  `Data.lua`, SavedVariables, session journal, and journal archive too. Ingestion can
  intentionally leave an unreferenced immutable archive after a DB rollback
  (`src/crowley/server/ingest.py:260-263`), so the receipt must report orphans rather
  than assume DB and raw volume have identical membership. A backup without a restore
  receipt is not a launch gate.
- Create a launch profile from the October 21/launch probe: exact game flavor path,
  build/interface/version, character, launch house, SavedVariables/Data.lua paths, plan
  hash, executable hashes, and fresh window/capture calibration. Keep the beta profile
  as historical evidence; do not edit its rows into launch identity.
- If the observed launch build/interface differs, cut a new canonical catalog revision
  and update the scanner constants/hashes, TOC, profile, and exact tests as one reviewed
  release. Keep strict matching and keep old plans/raw rows ingestible; do not bypass
  the build gate to make launch start.
- Bind or reset persisted controller state at the release boundary. The session journal
  schema does not contain house/build/interface/plan identity
  (`src/crowley/session/journal.py:16-46`), so archive the beta journal and its archive
  directory before a fresh launch journal, or add an exact release fingerprint with
  explicit mismatch refusal. Keep the controller disabled until fresh launch
  calibration and identity checks pass.
- Make checked-in systemd paths match the real installation method, document a clean
  server image rebuild/redeploy, and verify companion upload/ACK after restart. Record
  the source tree/snapshot, built server image ID, base/database image digests,
  migrations, addon hashes, plan/catalog hashes, sanitized config fingerprints, and
  prior image ID in a rollback manifest.
- Add a read-only staleness check for last accepted sweep per expected house, queue
  backlog, raw-archive presence, DB health, and disk space. Alerting must distinguish
  “no scan,” “scan incomplete,” “upload pending,” and “wrong regime.”

### Slice D — companion failure recovery

Own `src/crowley/companion/sync.py`, companion CLI code, and
`tests/test_companion.py`. Add versioned validation for the persisted upload/probe
state, durable file-and-directory sync, and a doctor/quarantine workflow for corrupt
state or a permanently rejected scan. It must diagnose the exact file/scan and retain
the queue; it must not silently discard evidence. This is finishable offline and keeps
a malformed launch artifact from becoming a systemd restart loop.

## Launch gates

Before launch (exact date to verify), require: a reviewed launch identity mapping; current build/plan
qualification fixtures; a successful database/raw restore drill; one positive deals-list
round trip using fixtures; explicit empty-list behavior without three compatible sweeps;
and a cutover checklist that preserves beta history while selecting a fresh launch
profile. At launch, collect three compatible launch sweeps before producing any list.
Treat beta prices, captured quantities, commodity depletion, and individual
disappearance only as pipeline/calibration evidence. Crafting and arbitrage remain
disabled until their recipe or multi-house evidence gates are satisfied.
