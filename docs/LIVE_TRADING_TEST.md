# Live trading test runbook

Who: the game driver (sole GUI owner) runs the in-game steps; the data agent runs server-side steps and checks.
Mode: **paper only** unless the user explicitly authorizes a specific armed test (step 5). Every executor click is a dry run
unless the published queue is armed **and** `/crowley arm <queueId>` was typed in the current session
([contract](EXECUTOR_CONTRACT.md)).

## 0. Deploy (at a quiet boundary the driver chooses: no active sweep, AH closed)
The live client loads `addon/Crowley` from MAIN on every reload, so merging is deployment.
1. Data agent: fresh market backup (`systemctl --user start crowley-market-backup.service`).
2. Merge the reviewed `live-trading` branch into MAIN (fast-forward).
3. Rebuild the server (`docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d --build --no-deps server`):
   applies migrations 007 (account state) and 008 (trade queue); verify `/healthz`, existing tables unchanged.
4. Install addon data files into the game: `uv run crowley-companion install` (copies the updated `Crowley_Data.toc` and
   the new `Queue.lua`; `Crowley` stays a symlink to MAIN).
5. Configure and restart the companion so it runs the new upload/queue code: add `house_key = "beta-normal-alliance"` and
   `character = "<trading character>"` to `~/.config/crowley/companion.toml` (or `CROWLEY_HOUSE_KEY` / `CROWLEY_CHARACTER`),
   then `systemctl --user restart crowley-companion.service`. Unconfigured, the companion always writes
   `CROWLEY_QUEUE = false`. The session daemon's `Data.lua` reader is unaffected (the queue lives in `Queue.lua`, never in
   `CROWLEY_DATA`).
6. Driver: one ordinary reload. Expected: no Lua errors; scanner state unchanged; `/crowley queue` prints "no queue".

## 1. Account capture
In game: open bags/mailbox/profession window once, then `/crowley account` (prints gold, slots, professions, recipes, mail
state) and an ordinary saving reload. Data agent: `GET /v1/houses/<house>/account-state/latest?character=<name>` returns
the capture; compare gold and a few bag stacks with what the driver sees. No names, senders or subjects are stored.

## 2. Reference capture (deposits)
With the AH open: `/crowley reference`, then a saving reload. Data agent: check `latest_item_reference` and
`item_deposits`; compare real deposits with the engine's assumed rate (D1, 15 % of vendor value per 12 h) and replace the
assumption with measured deposits (code change + new paper run).

## 3. Dry-run queue, every kind
Data agent publishes an **unarmed** test queue covering each action kind for items the character actually has/needs (spec = `house`, `character`, `expiresAt`, `actions` per the
[contract](EXECUTOR_CONTRACT.md); `armed` omitted):
`uv run python -m crowley.trading queue publish --spec dry-run.json` (prints the exact queue, then submits it), or from the
live paper run: `uv run python -m crowley.trading queue from-paper --run live-beta-20261022b --character <name>`
(always unarmed). Within one companion poll the queue reaches `Queue.lua`; `queue status --house <house> --character
<name>` shows the active queue. Driver: reload, open the matching frame (AH / merchant / mailbox / profession window),
click the Crowley executor button once per action. Expected per click: "dry run: would …", a `dry_run` result, no
protected call, nothing traded. Then a saving reload (the companion uploads `CrowleyDB.executions`);
data agent runs `queue reconcile --queue <queueId>` and checks every action has a `dry_run` result with the resolved details (prices, bag slots, merchant index, recipe).

## 4. Refusal checks (still unarmed)
Expired queue, wrong character, AH action during an active sweep, wrong frame open, two clicks < 1 s apart, `/crowley arm`
with a wrong id: each must refuse with its reason code and record it.

## 5. Armed micro-test — ONLY with explicit user authorization for this exact queue
Build the exact armed queue with one cheap action (e.g. buy 1 unit of a cheap commodity with a tight max price; later
queues: post that unit at a high price for 12 h; then cancel it):
`queue preview --spec micro.json --armed --out micro-queue.json` (no network; prints the queue and its full queueId).
The user reviews that preview and authorizes it; then
`queue publish --spec micro-queue.json --armed --confirm-real-trades <full queueId>` submits exactly that file. Driver types
`/crowley arm <queueId>`, clicks once per protected step, `/crowley disarm` afterwards. Data agent reconciles each result
against the account capture and the next sweep (bought unit in bags, listing visible in owned auctions, cancellation).

## Rollback
`/crowley disarm` (session); publish no queue (companion writes `CROWLEY_QUEUE = false`); revert the merge on MAIN and
reload. Execution results already saved remain for audit.

## Route walker (mailbox trips) — branch `route-walker-w3b`
`route-walker-w3b` = `live-trading` + telemetry schema 4 + the route walker. Schema 4 changes the addon telemetry the
session daemon decodes strictly, so the addon and the daemon must switch together:
1. At a driver-chosen boundary (no sweep, AH closed): merge `route-walker-w3b` to MAIN (it contains `live-trading`; do
   the `live-trading` deploy steps above), restart the session daemon, then one ordinary reload. The daemon rejects
   schema 3 frames, so a daemon restarted before the reload blocks until the reload publishes schema 4.
2. `deploy/config/session.toml` (linked from `~/.config/crowley/session.toml`) sets
   `routes_file = "/home/dev/repos/pegasus/deploy/config/routes/stormwind.json"` (built from the 2026-10-22
   hand-walked laps). The daemon refuses world-writable routes files or parents, and group write unless the group is
   the user's private group.
3. With native and input calibration complete: `crowley-session interaction-start --generation N`.
4. Arthur at the AH spot (-8812.7, 662.9): `crowley-session route-walk --generation N --route auctioneer_to_mailbox`.
   Each segment is ≤4 yd, replanned from a settled fix; any bad fix, combat, instance change or budget overrun stops
   the walk with an error and releases keys.
5. `crowley-session world-click --generation N --target Mailbox --hint 1000,430 --radius 300 --expect mailOpen`
   (pointer probes with human gestures until the addon reports "Mailbox" under the pointer; one rate-gated click).
6. Collect mail with the executor's `mail_collect` action (dry run first; armed only with explicit user authorization).
7. `crowley-session route-walk --generation N --route mailbox_to_auctioneer` (walking away closes the mailbox), then
   `crowley-session world-click --generation N --target "Auctioneer Jaxon" --hint 1000,440 --radius 300 --expect ahOpen`.
8. `crowley-session interaction-stop --generation N`.
Not built yet: scheduling these trips between sweeps automatically, and the daemon clicking the addon's executor button.
