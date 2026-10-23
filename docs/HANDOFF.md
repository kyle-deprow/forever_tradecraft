# Forever Tradecraft handoff

Updated 2026-10-23. This is the active handoff: current state, rules, and what remains before launch.
The beta-era handoff (1,837 lines of chronology and proofs) is preserved verbatim in git
(`git show 7fd2e1d:docs/HANDOFF.md`) and in `.archive/handoff-history-before-launch-prep-20261023.md`.
Technical reference: [ARCHITECTURE.md](ARCHITECTURE.md) (including the client assumptions table).

## Status: between beta and launch

- **The beta has ended.** WoW Forever launches **2026-11-04** with a fresh economy. Nothing touches the game
  until launch: no collection, reconnects, calibration or trading.
- **Off-season service state** (all user systemd units are symlinks into `deploy/`):
  - `crowley-session.service` stopped and disabled.
  - `crowley-paper-trading.timer`, `crowley-health.timer`, `crowley-market-backup.timer` disabled.
  - `crowley-companion.service` running and idle (no game); it writes `Queue.lua` with no queue.
  - Docker `crowley-db` and `crowley-server` up; migrations 001–008 applied.
- **Beta data retained:** 298 sweeps / 127,544 observations for house `beta-normal-alliance`
  (builds 1.60.1.70374 and 1.60.1.70450, 2026-10-15 → 2026-10-23). Backups: 7 daily snapshots plus 14
  restore-drill receipts in `~/.local/state/crowley/market-backups` (final snapshot
  `beta-20261023T215111Z-8dd827fad91d`).
- **Code:** MAIN is pushed to origin. Every worktree and side branch was audited and removed on 2026-10-23;
  their uncommitted state is archived in `~/.local/state/crowley/worktree-archive-20261023/`.

## Objective

Make gold on the WoW Forever auction house with several concurrent, independently profitable strategies:

1. **Collect** the market: a 428-item scan plan every 900 s, cheapest 20 distinct unit-price levels per item,
   never mixing houses or item identities (`itemKey`).
2. **Model** it: demand, time-to-sale, price metrics, recipe economics from the client's own data.
3. **Decide** with the trading engine (backtest → paper trading → queues).
4. **Execute** through the guarded addon executor (dry run unless doubly armed), with automated input at human
   speed and human motion (see Rules), plus route walking between the AH and the mailbox.

## Rules

- `CLAUDE.md` rules apply (no fallbacks, `itemKey` only, new migrations only, ≤1 automated click/s, full simulated
  human pointer motion, ask before committing/pushing/destroying data).
- **Real gold:** nothing is armed without the user's explicit authorization for that specific queue
  ([executor contract](EXECUTOR_CONTRACT.md), [runbook](LIVE_TRADING_TEST.md)).
- **One GUI owner at a time.** Before any automated input, confirm the game window has focus and nobody is using
  the desktop; verify each action through addon telemetry (XTEST keys go to the Wayland-focused window, not
  necessarily the X "active" window).
- **Ownership:** the data agent (Claude) owns code and worktree status (user grant 2026-10-23). Implementation
  goes through the Luna (implement) / Sol (review) loop; the parent verifies and commits. Origin:
  https://github.com/p-kjdeprow/forever_tradecraft.
- **Privacy:** raw frames, receipts, SavedVariables, recordings and backups stay private under
  `~/.local/state/crowley` (dirs 0700, files 0600). Never edit game SavedVariables. Secrets live only in the
  untracked `deploy/.env`. Stage explicit files only; never `git add .`.

## Components

| Component | Code | Docs |
|---|---|---|
| Addon (scanner, telemetry HUD schema 5, account capture, executor, reference) | `addon/Crowley`, `addon/Crowley_Data` | [ARCHITECTURE](ARCHITECTURE.md), [EXECUTOR_CONTRACT](EXECUTOR_CONTRACT.md) |
| Companion (SavedVariables ↔ server, Queue.lua) | `src/crowley/companion` | — |
| Server + TimescaleDB | `src/crowley/server`, `deploy/docker-compose.yml` | [MARKET_RECOVERY](MARKET_RECOVERY.md) |
| Session daemon (collection driver, guarded input, route walking) | `src/crowley/session` | [REPEATING_SCANS](REPEATING_SCANS.md), [RUNTIME_PERFORMANCE](RUNTIME_PERFORMANCE.md) |
| Analysis and client data | `src/crowley/analysis`, `src/crowley/core/client_data.py`, `tools/client_data*` | [ANALYSIS](ANALYSIS.md) |
| Trading engine, paper trading, queues | `src/crowley/trading`, `src/crowley/core/queue.py` | [TRADING](TRADING.md), [LIVE_TRADING_TEST](LIVE_TRADING_TEST.md) |
| Live configuration and routes | `deploy/config/` (linked from `~/.config/crowley`) | [deploy/config/README](../deploy/config/README.md) |
| Game setup | — | [GAME_SETUP](GAME_SETUP.md), [WATCHLIST](WATCHLIST.md) |

## What the beta established

- **Collection** worked operator-assisted (last fully verified sweep: scan 290). Autonomous qualification was
  never reached: native eventual-echo delivery remains unqualified, and the driver moved to passive startup with
  takeover qualification (`.archive/PLAN-autonomous-startup-takeover-20261022.md`). Zero autonomous cycles counted.
- **Strategies** (20 g start, demand share 0.5, see [TRADING](TRADING.md)): crafting dominates — alchemy and
  blacksmithing (≈148 g of ≈218 g closed-trade profit over the beta), then engineering and leatherworking;
  Coarse Grinding Stone alone was ~¼ of profit (concentration risk). Scalping lost money in-model. 58 % of listed
  units expired (deposit losses). A character has only **two** primary professions, so the launch portfolio must
  be cut to two. Some recipes need stations (Bronze Tube: anvil + Blacksmith Hammer); the engine does not yet
  model stations.
- **Live trial facts** (build 70450, 2026-10-22): keyboard turning is π rad/s, run 7 yd/s; XTEST input lands up to
  ~1 s late, so open-loop walking drifted 13 yd while closed-loop stepping worked. JUMP=SPACE, TURNLEFT=Q,
  TURNRIGHT=E. The mailbox and auctioneers open with a left click; object hover shows in a UIParent-owned
  GameTooltip ("Mailbox"); `MAIL_SHOW` fires but `MAIL_CLOSED` did not, so `MailFrame:IsShown()` is the signal.
  These are recorded in the ARCHITECTURE assumptions table.

## Built but never exercised live

- **Executor and queue pipeline:** account capture, `/crowley arm`, dry-run queues, execution uploads, queue
  reconciliation (migrations 007/008). Test plan: [LIVE_TRADING_TEST](LIVE_TRADING_TEST.md).
- **Route walker:** `crowley-session route-walk` (closed-loop, Guardian-checked key timelines, holds ≤0.45 s below
  autorepeat) and `world-click` (hover-confirmed, rate-gated mailbox click). Routes in
  `deploy/config/routes/stormwind.json` (Stormwind AH ↔ mailbox, from hand-walked laps).
- **Telemetry schema 5** (union of the driver's auctioneer/blockingUI fields and the walker's hover/mailOpen fields).
  The addon and session daemon must always deploy together.

## Before launch (open work)

1. **Green test suite** on MAIN with the pinned Rust toolchain (in progress, 2026-10-23).
2. **Launch parametrization:** client version/build, interface, executable, game folder, realm/house and the scan
   plan are hard-coded for the beta in ~15 files (protocol checks included). Move them into one launch target
   configuration so launch day is a config change plus regenerated data.
3. **Strategy selection** for one character's two professions; station-aware recipes; time-on-AH and expiry
   handling (smaller posts, cancel/repost).
4. **Mail loop scheduling** between sweeps and the daemon clicking the addon executor button (not built).
5. **Collection qualification at launch:** native and human input calibration, takeover qualification, then three
   autonomous 900 s cycles before claiming autonomy.

## Launch-day checklist (draft; finalize with item 2)

1. Install/patch the launch client; record its version/build, interface, executable and game folder.
2. Update the launch target configuration; regenerate client data (`tools/client_data_export.py`) and the item
   reference; rebuild the scan plan for the new build.
3. Create the launch house in the DB on first upload (new house key); start a new paper run at the first sweep.
4. Re-enable `crowley-market-backup.timer` and `crowley-health.timer`; start the session daemon only after the
   addon reload so both run telemetry schema 5.
5. Collection qualification (item 5 above); then the executor dry run and, with explicit authorization, the armed
   micro-test ([LIVE_TRADING_TEST](LIVE_TRADING_TEST.md)).
6. Re-verify the Stormwind route with one supervised walk before trusting `route-walk`.

## Entrypoints

- Python: `/home/dev/repos/pegasus/.venv/bin/python`; session CLI `~/.local/bin/crowley-session` (editable install
  of this checkout); config `deploy/config/session.toml` (linked from `~/.config/crowley/session.toml`).
- Tests: `CARGO=~/.cache/crowley/rust-toolchain-1.85.1/toolchain/bin/cargo uv run pytest` (add
  `CROWLEY_TEST_DATABASE_URL` for DB tests).
- Backups: `systemctl --user start crowley-market-backup.service`; restore drills via `tools.market_backup`.
- Pinned binaries: `~/.cache/crowley/{xdotool,x11-identity-observer,template-matcher,gnome-telemetry-region-r6,
  codex,rust-toolchain-1.85.1}`. Parts of `gnome-telemetry-region-r3/r5` are root-owned stale builds
  (remove with sudo).
