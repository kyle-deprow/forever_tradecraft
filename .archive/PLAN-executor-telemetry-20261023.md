# Plan: executor telemetry schema 6

Status: bounded design only. This plan is launch-pending and must be sequenced
after the current launch-target/session worker is reviewed. It owns no current
target-worker source while that work is active.

## Outcome

Publish a strict, bounded `executor` object in every Agent frame so the daemon
can distinguish no queue, invalid queue, valid queue, button visibility, actual
button callbacks, mail per-message readiness, and terminal/nonterminal results.
The exact object is frozen in
`.archive/launch-readiness-20261023/EXECUTOR-TELEMETRY-CONTRACT.md`.

Schema 6 is a coordinated producer/consumer cutover. CRS1 framing remains
unchanged; schema 5 and schema 6 are never accepted interchangeably.

## Reserved ownership

Do not edit these files until the current target worker's review is complete:

- `src/crowley/core/game_target.py`
- `src/crowley/session/config.py`
- `src/crowley/session/controller.py`
- `src/crowley/session/daemon.py`
- `src/crowley/session/protocol.py`
- `addon/Crowley/GeneratedTarget.lua`

After that review, this slice owns only the telemetry portions of the addon and
protocol consumers. Click dispatch and mail scheduling are separate plans.

## Implementation order and exact files

1. Add the producer projection in `addon/Crowley/Executor.lua`.

   - Add a bounded `clickOrdinal` initialized per loaded queue/session.
   - Change the real button callback to identify `source == button`, increment
     only for that callback, and set `lastClickSource = "button"`.
   - Keep the existing direct `Executor.Click()` harness seam, but mark it
     `directAPI` without incrementing the causal button ordinal.
   - Project the actual action kinds from `ACTION_FIELDS`, the actual phase
     names, `state.inFlight/blocked/latched/ambiguous`, result count/latest
     status, and mail `mailProcessed/mailCount`.
   - Derive `clickReady` from the same branches accepted by `click()`. Do not
     create a second readiness policy.
   - For `mail_collect`, use `MailFrame:IsShown()` in `isFrameOpen`; retain
     event flags only as supplemental state. This addresses the observed
     missing `MAIL_CLOSED` event.

2. Add `executorTelemetry()` in `addon/Crowley/Agent.lua` and publish it from
   `Agent.Snapshot()` with `schema = 6`.

   - Implement the exact `none`, `invalid`, and `valid` semantics in the shared
     contract.
   - Copy only bounded primitive fields. Never copy result detail tables into a
     frame.
   - Publish actual valid queue identity independently from Agent context.
     Mismatches are executor refusal cases; daemon operation admission refuses
     them before input without corrupting unrelated collection telemetry.

3. Update strict consumers together:

   - `src/crowley/session/protocol.py`: exact top-level schema-6 keys and
     executor validator, including all enums, integer/string limits, and
     cross-field invariants.
   - `src/crowley/session/motion.py`: require schema 6 and preserve existing
     native/camera/identity checks.
   - `src/crowley/session/decoder.py`: no semantic change is expected, but
     verify its public `decode()` path consumes the schema-6 `Frame` without a
     compatibility branch.

4. Update real-byte fixtures and producer harnesses only:

   - `tests/wow_harness.py`
   - `tests/test_executor.py`
   - `tests/test_addon.py`
   - `tests/test_session.py`
   - `tests/test_session_native.py`
   - `tests/test_session_runtime.py`
   - `tests/test_session_motion_integration.py`
   - `tests/test_session_executor_movement.py`
   - `tests/test_session_regressions.py`
   - `tests/test_session_performance.py`

   Preserve existing schema-5 rejection tests by changing them to reject schema
   5 after the cutover and add explicit schema-7/unknown-key rejection.

## Meaningful tests and entrypoints

The proof must use actual Lua publication and actual bytes, not a Python dict
standing in for the producer:

- Load no `Queue.lua` and assert `Agent.Snapshot()` publishes `availability=none`,
  no button, no arm, and no result.
- Load malformed queue data and assert `availability=invalid` with only the
  bounded queue-refusal witness.
- Load a valid unarmed queue and assert exact queue identity, current action,
  `publishedArmed=false`, `sessionArmed=false`, and `clickReady=true` only when
  the matching frame is shown.
- Call the harness’s real `button.Click(button)` path and assert the ordinal
  increments and source is `button`; call the existing direct API seam and
  assert source is `directAPI` while the causal ordinal does not increment.
- Render `Agent.FrameBytes()` through `WowClient.render_agent_capture()`, feed
  it through `PixelDecoder.decode()` and the public `decode_frame()` path, and
  assert the executor object survives the CRS1 byte round trip.
- Assert payload compression remains below `MAX_PAYLOAD` with the full schema-6
  snapshot.
- Run the default `SessionIPC`/daemon fixture path with a valid unarmed queue;
  no protected call may be inferred from telemetry alone.

No direct `Executor.State()`-only Python fixture is sufficient as the primary
proof. Direct state inspection may remain as a narrow Lua behavior assertion.

## Verification and acceptance

Before delegation, review the exact contract file against current
`Executor.lua` action/phase/status names. After implementation, verify:

- schema-6 addon and Python source hashes are deployed together;
- no schema-5 frame reaches the schema-6 decoder;
- every enum has a producer path or an explicit sentinel path;
- no queue, invalid queue, and valid queue each have deterministic frames;
- directAPI cannot satisfy a causal click proof;
- no arm command is emitted by the daemon or test harness;
- frame bytes remain private and bounded.

Focused checks use pinned CARGO and the machine lock:
`flock /home/dev/.cache/r-pg.lock uv run pytest -q tests/test_executor.py tests/test_addon.py tests/test_session.py`.
Use scoped Ruff/checkformat, never a repository-wide formatter. Parent verifies
the full default remains <180 seconds. Reuse fixtures for one real-byte
composition plus small guard cases; avoid giant redundant native matrices.
No game/services/deployment, commits, pushes, resets or private-data changes.

Live acceptance remains pending launch: actual button rendering, UI scale,
position, XTEST `OnClick` delivery, and protected API behavior are not
established by offline Lua tests.


## Round2 actual source matrix correction

Real post_commodity/cancel_auction set inFlight=true with nil state.phase until
native terminal events. Keep literal wirephase ready for these two kinds only,
with clickReady=false and exact currentseq/kind lastResult: started with latched=false, or blocked with latched=true after an actual refused second click; top-level blocked/ambiguous remain false. Do not reject
actual producer states or invent guessed native phases. Add actual Lua bytes
paused before each success event and decoded again after terminal success.
Deliberate fixture operator arming may simulate sourcebehavior; no daemon path
or default composition may arm or infer protectedcall success.

Sol also requires clickReady implies !blocked/!ambiguous and complete actual
payload proof with valid executor at accepted maxima, not only none sentinel.
If maxsize breaks fixed2000bytes, root must approve coordinated explicit bounds
amendment from measured evidence before completion; never raise framecapacity,
truncate identity, fallback or silently shrink the negative fixture.

## Round2 producer/server queue-bound alignment

Additional exactownership src/crowley/core/queue.py queue validation/build bounds
ONLY, tests/test_trade_queue.py focusedboundparitytests ONLY. Mirror the addon
schema6 queueId/house/character UTF8byte bounds and maxMessages uint32 ceiling in
Python queue validation before server/companion can bless/render an impossible
queue. Preserve historical execution record parsing and all queueconfirmation,
IDcomposition, itemidentity andhouseisolation rules. No migration/servicechanges.
Use actual render->Lua validator boundary tests at bound/bound+1; no plaintext
name keys or truncation. Any changed wirebound requires root contract amendment
from measuredpayload evidence, coordinated producer/consumer validators.

Add actual stale-open mailbox direction: eventflagtrue fromMAIL_SHOW but native
MailFrame:IsShown false =>clickReadyfalse and noprotectedcall. Add one explicit
operator-armed partialmail Lua snapshot/bytes with real workDone/workTotal,
mail_wait versusmail_items, inFlight and one-second readiness. No daemonarming.
Focused tests add test_trade_queue.py to existing affectedtelemetry command.

## Aggregate wire limit clarification (parent + independent Sol design)

Individual field maxima do not guarantee their Cartesian product fits the
fixed deflated2000byte aggregate cap. That preexisting independent cap remains
strict; all-max high-entropy actualLua publication must fail without truncation,
fallback or a new frame. No arbitrary nativecharacter limit or capacitygrowth.

Separate honest proofs: maxexecutoridentity fields (prefer variedstrings with
native-format pendingUIDs), production-representative canonicaltargethouse /
queueID={house}-{character}-{generatedAt}-4hex / six Scanner-format pendingIDs
{house}-{startedAt}-{character}-4decimal through realLuaFrameBytes/PixelDecoder/
decode_frame, and allmaxhighentropy aggregate rejection. Measure exactcompressed
size/margin for positivecases. Negative must prove valid snapshotsemanticstate,
>2000computedpayload, exact Agent.Publish failure and originalpublishedframe
unchanged. Never label compressiblepadding 'realistic worst'. Preserve exact
oldcapacityboundtests. Queuefieldbounds remainsharedbytepolicy, not claims of
native UI/name limits. Historical executionrecords retain old parsing semantics.

## Round5 consecutive mail and actual partial-failure progress

Clear mailCount/mailProcessed/mailIndex/beforeMailCount on advance so the next
mail_collect action publishes 0/its ownmaxMessages. Preserve partial progress of
the SAME failed/blocked action (finishStartedfailed clearsphase butdoesnotadvance).
Exact decoder matrix: active mail total>=1 and done<total; ready+!blocked means
done0; ready+done>0 means blockedtrue/ambiguousfalse/latchedfalse/clickReadyfalse
and latestsame-seq/kind failed or blocked. mail_items/mail_wait requireinFlight.
RealLua bytes must prove success->secondmailready0/newmax and partialmailUIerror
->blockedreadyretainedprogress. No generic phase-name inference or progressreset
on failure. Parent finalverification was cancelled before its child started
because this newfinding invalidated the earlierfreeze; newmanifest required.
