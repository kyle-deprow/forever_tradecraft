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
