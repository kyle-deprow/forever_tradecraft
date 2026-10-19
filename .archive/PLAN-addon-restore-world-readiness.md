# Restore only after world telemetry is ready

Actual evidence: executor-review/addon-restore-invalid-facing-live-evidence.json.
Fresh Sourceb46e679f restore reload first checked publication rejected invalid
facing during ADDON_LOADED, permanently cleared HUD and markedfailed. Root
preserved original SavedVariables bytes/hash. The exact invalid facing value
is unknown; don't assert nil as the native observation. Model reproduction
with unavailable facing covers the same guard. No schema/value fallback.

Goal: a normal Restore reload waits for actual world entry and valid movement
telemetry, then performs the existing strict two-publication restoration commit.
Keep native construction, measurement deadlines, metrics, frame schema and
Guardian/controller admission unchanged. Restore readiness is not calibration.

## Ownership and scope

Fresh isolated WT at main c8498ce. Worker owns addon/Crowley/Agent.lua,
tests/test_addon.py, and tests/wow_harness.py ONLY. No main/installed addon edits,
GUI/services/config/daemon/Guardian/helper source/git operations or reset/stash/
reverts. Parent controls integration. Read this plan and relevant clientcontracts
skill fully. Root asks Sol plan review before implementation. Actual Opus reviews
behavioral change after parent checks, alongside Sol.

## Implementation order / behavior

1. Preserve a fresh restore_pending initialization's boot/token, diagnostic clear,
   armed fence and nonce/load ownership; enter explicit pending restore with
   Restore disabled. Do NOT construct/publish the restoration surface before
   PLAYER_ENTERING_WORLD. Ordinary/deferred/measurement startup unchanged.
2. On actual PLAYER_ENTERING_WORLD, check native movementTelemetry through its
   existing validators before entering the original restoration transaction.
   Readiness means EXACTLY pcall(movementTelemetry) succeeds: preserve structured
   schema-valid unknown CTM/ground values; add no new native readiness validator.
   If transiently unavailable, poll at <=10Hz via bounded timers; never normalize
   unknown values into accepted motion. No Agent.Publish/JSON serialization in
   this readiness probe, so publication errors still reach their exact commit.
   Keep surface absent, scanner fenced and marker pending while waiting.
3. Bound startup waiting to30s from restore initialization, including missing world
   event; stop retries after that deadline. Use existing GetTime/C_Timer facilities
   and owned load/token guards, not global time monkeypatching. Refuse when
   GetTime() >= deadline BEFORE probing at the exact boundary. Terminal readiness
   failure stores exact last native reason (or missing world entry), leaves failed/
   surfaceless/fenced/recoverable state, reenables Restore through existing actor.
   No callback may complete a replaced/failed/ordinary/newer nonce. Multiple world
   events cannot allocate/publish/commit twice. No callback may mutate state or reschedule after terminal state; already
   queued C_Timer.After callbacks may remain bounded and inert.
4. Once ready, run existing createSurface plus first fenced publication then
   lifecycle ordinary/unarmed publication/marker-clear in the same ordering.
   Keep allocation/first/second publication failures terminal and causal diagnostics
   intact. Existing successful scanner rearm only after actual commit unchanged.
   Do not loosen facing range, timing of constructor click, native100 cadence,
   memory/render metrics, decoder, permission/lease or accepted native evidence.
5. Model native login sequence honestly: WowClient.login normally fires ADDON_LOADED
   then PLAYER_ENTERING_WORLD. Tests needing pre-world states fire events directly.
   Do not globally make native APIs alwaysready or advance wall clocks. Inspect
   other handlers triggered by event before changing harness; adjust only assumptions
   invalidated by real sequence, no unrelated fixture redesign.

## Meaningful regression and checks

- Reproduce old failure with facing unavailable during ADDON_LOADED. At this boundary
  new code remains pending/surfaceless/fenced/no ordinary marker commit.
- Facing becomes valid at world entry: restored ordinary fresh boot normal0,
  inactive fence, marker nil, no retained failure; real frame roundtrip decoder.
- World entry initially lacks valid facing, later valid: bounded retry succeeds;
  readiness never publishes invalid value and no early scanner query starts.
- Missing world event/permanently invalid facing: bounded terminal failure with
  exact reason, cleanup/no leaked repeated timers and existing recovery route.
- Duplicate world events, stale timer after nonce/retry/load change, exact deadline
  boundary refusal; no late success or duplicate texture construction.
- All existing allocation/first/second publication failure tests remain meaningful
  at their actual boundaries, correct error phase and retained diagnostic.
- Successful restore with AH open rearms only after strict ordinary commit.
- Normal startup/deferred construct/native100 lifecycle remains unchanged.

First run focused restore/readiness tests; full tests/test_addon.py ONCE after
focused green and source stable. Scoped ruff check/format on changed Pythonfiles,
git diff --check. Fullprivate0600logs/evidence0700 beforecommands, exact argv/rc/
sourcehashes and no out-of-scope changes. Parent independently reproduces relevant
cases and inspects diff. Sol+actualOpus review then root installs exact accepted
source, sole GUI owner performs source-approved recovery and actual ordinary
normal0/inactivefence/checkpointclear/AH reopen proof. No autonomous success claim
until three full900s cycles; don't relax checks merely to restore screenshots.

DONE only implementation + relevant tests/ fulladdon checks green, exact scope,
no unresolved real failures. A plan/report alone is not completion.

## Sol plan arbitration

Root accepts both concrete initial Musts. Readiness is exactly successful pcall
of current movementTelemetry, preserving its schema-valid CTM/ground unknown
results. Regression covers unknown states accepted with otherwise valid movement.
Use only verified existing C_Timer.After. At most the bounded timeout and one
next poll remain outstanding for an owner; invalidating owner on terminal makes
all queued callbacks inert. Tests drain stale timeout/poll after early success,
failure and nonce change, asserting no state mutation/reschedule/new allocation/
publication. No new cancellation API or harness-only fake cancellation. Exact
GetTime()>=deadline refuses before probe. This supersedes literal timer removal.
