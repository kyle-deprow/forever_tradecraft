# Live trading test runbook

Who: the game driver (sole GUI owner) runs the in-game steps; the data agent runs server-side steps and checks.
Mode: **paper only** unless the user explicitly authorizes a specific armed test (step 5). Every executor click is a dry run
unless the published queue is armed **and** `/crowley arm <queueId>` was typed in the current session
([contract](EXECUTOR_CONTRACT.md)).

## 0. Launch deployment and identity

The beta is over. These are launch-day instructions; no game input, service restart,
migration or deployment is authorized by this document alone. Review the active
[HANDOFF](HANDOFF.md) and [launch target procedure](LAUNCH_TARGET.md) first.
The addon is a symlink into this checkout, so a later game reload consumes local source.

1. Record the actual launch build/interface, native region/realm/house, executable,
   installation roots and client facts. Edit the packaged launch target and regenerate
   the coordinated artifacts and staged configuration. Review drift checks and the
   complete staged diff before installing it. Preserve beta data and route provenance.
2. At an authorized quiet boundary, take a market backup and deploy the reviewed server.
   Production currently has migrations 001–008; migration 009 adds immutable paper-run
   capability metadata. Verify health and retained beta rows. Create a new launch-house
   paper run with observed capabilities; do not relabel or rewrite a beta run.
3. Install the coordinated addon/data/session source and reviewed staged configuration.
   Configure the companion's exact launch house and character. With no queue configured,
   it writes `CROWLEY_QUEUE = false`; queue data stays in Queue.lua, outside CROWLEY_DATA.
4. Reload the addon and start the matching daemon only at the authorized boundary.
   Require exact telemetry schema and target identity. Confirm no Lua errors and no
   active queue. Complete passive readiness/takeover/native input qualification before
   any automated executor or route input. Preserve original frames and receipts privately.

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
launch paper run: `uv run python -m crowley.trading queue from-paper --run <launch-paper-run> --character <name>`
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
Pause the daemon and disarm the session; clear the published queue through the ordinary
queue workflow. Restore a reviewed coordinated source/config version at an authorized quiet
boundary. Preserve all original execution results, uncertain intents and receipts for audit;
never reset a journal to manufacture permission to retry an unknown effect.

## Route qualification and mailbox trips

The retained routes were measured on beta build70450. A changed target refuses them;
remeasure on the actual launch client before allowing automated walking. Qualify native
input, focus/identity, camera, human pointer behavior and the actual executor button bounds.
Keep the real one-second click cap and full curved press/release path.

A supervised route test enters interaction mode with the current generation, walks
`auctioneer_to_mailbox`, then uses the existing hover-confirmed `world-click` with
`expect=mailOpen`. Its hint comes from current measured visual evidence. The mailbox's
actual `MailFrame:IsShown()` state is authoritative; the missing beta MAIL_CLOSED event
must not be treated as a close witness. Collect only a reviewed mail_collect queue,
starting unarmed. Walk `mailbox_to_auctioneer`, require fresh mailOpen=false after the
walk, and reopen the AH through the guarded Auctioneer Jaxon/SoftTargetInteract/CTRL-F12
path. `world-click --expect ahOpen` is invalid. Exit interaction using the current
generation and complete normal re-arm/reconciliation before collection resumes.

The guarded executor and mail-loop runtime passed offline implementation, independent
composition/control/recovery proofs and Sol review. Scheduling remains disabled for
live use until launch qualification is complete. The request shapes are fixed below.

Start from a repeat-mode daemon with a current generation, the exact current
`mail_collect` queue/sequence, a loaded scan ACK, no unresolved work and enough
remaining time before the next sweep. Capture the generation and IDs from current
status; the shell variables below represent those observed values:

```sh
crowley-session mail-loop-start --generation "$generation" --queue-id "$queue_id" --seq "$seq"
crowley-session mail-loop-status
```

Start sends an empty queue confirmation. It never arms the addon or authorizes a
protected click. The opt-in is local to this daemon process and covers one admitted
mail sequence, once per exact acknowledged sweep. A successor needs a fresh start;
a restart leaves scheduling disabled and uncertain work blocked.

Qualify the whole route with both queue/session arms false first. After opening the
mailbox, the scheduler performs one real guarded executor-button dry run, returns,
proves the mailbox closed and AH open, then uses ordinary re-arm/reconciliation to
resume repeat collection. Require its original frame bytes, receipt and durable
mail-cycle outcome; do not infer success solely from a visible button or route.

For a separately authorized armed queue, each ready mail message waits for a fresh
explicit request. Read the current generation and cycle ID from status, then:

```sh
crowley-session executor-click --generation "$generation" --queue-id "$queue_id" --seq "$seq" --confirm-queue-id "$queue_id" --cycle-id "$cycle_id"
```

An unarmed standalone request uses `--confirm-queue-id ''` and `--cycle-id ''`.
`mail_wait` permits observation only. A later `mail_items` boundary needs a new
confirmation; an asynchronous terminal result needs no extra click. These commands
never set either addon arm. Failed, refused, uncertain or expired work blocks the
cycle and preserves its evidence; it grants no automatic retry or return walking.

```sh
crowley-session mail-loop-stop --generation "$generation"
```

Stop disables scheduling immediately and fences an active cycle. Use the current
generation after any control transition. Preserve blocked journals and receipts
when diagnosing or rolling back; do not clear them to obtain a retry.

No rendered-button coordinates, native OnClick delivery, route validity, protected
API behavior or autonomous mail cycle is established by offline tests.
