# Plan: guarded daemon executor-button click

Status: offline implementation reviewed READY after Round4. Parent146 click/policy
cases and114 schema cases passed with frozen hashes unchanged. The accepted
phase freeze is launch-readiness-20261023/executor-click-round4-sha256.json;
subsequent mail-loop edits have separate review. This plan authorizes no live click
or armed operation.

## Outcome

Add one public daemon/IPC operation that clicks the rendered Crowley executor
button with the existing measured-anchor, Guardian, human-pointer, rate-limit,
native gate, camera/identity, generation, and fresh-CRS postcondition seams.
The operation is dry-run by default. A protected operation additionally requires
an exact full `confirmQueueId` in the daemon request and both observed addon arm
bits. No code path may type `/crowley arm`.

## Reserved ownership and order

The current launch-target/session worker owns the following until review is
complete; do not overlap its edits:

- `src/crowley/session/controller.py`
- `src/crowley/session/daemon.py`
- `src/crowley/session/protocol.py`
- `src/crowley/session/config.py`
- `src/crowley/core/game_target.py`

Implementation order after that review:

1. Finish and review schema 6 source from
   `.archive/PLAN-executor-telemetry-20261023.md`.
2. Add the strict executor-mailbox visual state to
   `src/crowley/session/model.py` and its model tests. The state must use a
   fresh measured anchor, not a configured center coordinate:

   ```text
   state: executor_mailbox
   facts: scene=world, modal=mailbox, control=crowley_executor_button,
          character=<configured>, realm=<configured>, code="", idle=true
   ```

   The model returns bounds; the daemon converts them into the existing sealed
   `MeasuredAnchor`. No UI scale or button pixel mapping may be guessed.

3. Extend `src/crowley/session/driver.py` with the internal allowlisted action
   `executor_click`, using left button, the existing curved/timed
   `HumanPointerPlan`, `ClickRatePermit`, `Guardian.begin_action`, exact raw and
   delivered press/release events, and the existing pointer receipt machinery.
   Add:

   ```text
   ANCHOR_CONTROLS["executor_click"] = "crowley_executor_button"
   ANCHOR_SCENES["executor_click"] = "executor_mailbox"
   POINTER_BUTTONS["executor_click"] = 1
   ```

   A fresh anchor must be re-observed immediately before dispatch and consumed
   once. The receipt must include the action name, generation, anchor evidence
   hash/capture ID, endpoint, rate precommit/press record, and Guardian event
   completion. Do not call backend `_run()` directly from the daemon.

4. Add `execute_executor_click()` in `src/crowley/session/daemon.py`.

   Pre-dispatch, in this order:

   - Require interaction mode, `READY`, current generation and current armed
     lease; reject repeat `WAIT_DUE` callers.
   - Capture a fresh CRS frame and a fresh motion frame. Require the existing
     native gate (CTM disabled, grounded, no combat/death, current zone/instance,
     stable identity/camera evidence, no chat or blocking UI).
   - Validate `executor.availability=valid`, exact queueId, exact current seq,
     `currentKind=mail_collect`, visible button, `clickReady=true`, matching
     house/character, and no ambiguous/blocked state.
   - An empty confirmQueueId is the canonical dry-run-only default. A nonempty
     value must equal queueId. If both observed arms are true, exact nonempty
     confirmation is mandatory; otherwise execution stays dry run. Recheck
     this at final admission; the daemon never mutates either addon arm.
   - Persist the executor click intent before pointer motion/button dispatch.

5. Extend `src/crowley/session/controller.py` and
   `src/crowley/session/journal.py` with a distinct durable executor intent.
   It must retain queueId, seq, generation, lease generation, pre-click CRS
   `(boot, sequence, crc32)`, pre-click ordinal, arm observations, and sealed
   anchor identity. Archive the dispatch and terminal witness under an
   append-only `executor` archive. Do not force `/reload`; that clears the
   session arm and can invalidate motion evidence. SavedVariables execution
   upload remains the normal companion cycle after the current sweep.

6. After the physical release, poll the public capture/decoder path for a fresh
   CRS frame. Accept delivery only when boot/identity are unchanged and:

   ```text
   post.clickOrdinal == pre.clickOrdinal + 1
   post.lastClickSource == "button"
   post.queueId == requested queueId
   post.currentSeq/currentKind still identify the requested action or a valid
   terminal successor
   ```

   A directAPI source, ordinal jump, missing frame, changed boot/identity,
   stale generation, or timeout leaves the intent uncertain and blocks; it never
   retries the click.

7. Interpret the post-frame result. `dry_run` is a terminal result for this
   click but not durable queue completion across a reload. `started` and
   `blocked` are nonterminal; for mail, a `mail_items`/`clickReady` frame permits
   the next per-message click while the overall action remains in flight.
   `succeeded`, `failed`, `refused`, and `skipped` are terminal according to the
   executor contract. Clear the live intent only after the archive and exact
   fresh-frame witness are durable.

## Public entrypoint

Add an exact `executor_click` IPC/CLI request in `src/crowley/session/cli.py`:

```json
{
  "command": "executor_click",
  "generation": 12,
  "queueId": "<full queue id>",
  "seq": 7,
  "confirmQueueId": "<same full queue id>"
}
```

No extra fields, queue-arm command, item names, or inferred queue selection are
allowed. The installed `crowley-session executor-click` entrypoint must reach
the same `SessionIPC.dispatch()` validation and daemon method used by the
mail-loop scheduler.

## Meaningful tests

Add focused tests in `tests/test_session_executor_click.py` (or the reviewed
existing dispatch file), plus narrow updates to:

- `tests/test_session_driver_actions.py`: sealed mailbox/executor anchor,
  fresh-anchor refresh, one left-click Guardian/XTEST receipt, rate gate,
  pointer endpoint, and source/control mismatch rejection.
- `tests/test_session_native.py`: exact CRS bytes before and after the click,
  same boot/identity, ordinal increment, and rejection of stale/forged frames.
- `tests/test_session_runtime.py`: public `SessionIPC`/CLI field validation,
  generation fencing, durable pre-click intent, terminal archive, and restart
  reconciliation with no second dispatch.
- `tests/test_executor.py`: actual harness `button.Click(button)` versus
  direct `Executor.Click()`, dry-run protected-call count zero, and mail
  `mail_items` progress.

The end-to-end offline proof must use `WowClient.render_agent_capture()` →
`PixelDecoder.decode()` → default IPC dispatch. A Python dictionary pretending
to be an addon post-frame is not sufficient. Native X11 physical acceptance
remains a launch-day check.

## Verification and acceptance

- `confirmQueueId` is exact and separate from both addon arm observations.
- A daemon request cannot arm, publish, replace, or reload a queue.
- The measured anchor is fresh, named, visually bounded, tied to client identity
  and generation, and consumed once.
- Pointer receipts prove curved/timed motion and one physical press/release;
  CRS telemetry proves that the addon button callback ran.
- Every uncertainty path persists before dispatch and never retries an unknown
  or started effect after restart.
- The first acceptance queue is published unarmed and produces no protected
  calls. Armed acceptance is explicitly deferred until launch authorization.

## True blockers versus buildable work

Buildable offline: schema/IPC validation, journal semantics, model state schema,
Guardian receipt plumbing, byte-level causal proof, and Lua dry-run behavior.

Focused checks use pinned CARGO and the machine lock:
`flock /home/dev/.cache/r-pg.lock uv run pytest -q tests/test_session_executor_click.py tests/test_session_driver_actions.py tests/test_executor.py`.
Use scoped Ruff/checkformat; parent requires the integrated default <180 seconds.
No live deploy/game/service changes or commits. Reuse fixtures for one small
causal real-byte/default-entrypoint proof and focused negative cases.

Live blockers requiring observation rather than guesses: rendered button bounds
and movable position, UI-scale mapping, XTEST delivery to `OnClick`, whether the
mail frame/button stays synchronized after walking away, and actual protected
API behavior on the launch client.


## Parent amendment after independent Sol design review

PhaseA telemetry is now the active source owner, target phase is READY. Begin this
phase only after telemetry's reviewed freeze; previous target reservations above
are historical sequencing notes, not current overlapping ownership.

Each physical click has a stable attempt ID and full pre-state: resultCount,
lastResult, phase, workDone/workTotal, ordinal, boot/sequence/CRC, queue/seq,
identity, generation/lease, arm observations and sealed anchor. Persist intent
before any pointer movement. Keep a separate durable overall mail-action marker
for an action still started after the individual click has been witnessed.
A causally witnessed started+mail_wait archives the physical click as delivered
and atomically clears only that physical click intent; it does not mark the mail
action complete. Later mail_items clicks create new IDs and pre-ordinals. Any
fresh owner encountering an unfinished action blocks without replay even if the
individual click intent was cleared.

Add a one-use final admission callback through DesktopDriver.run/X11Backend's
pointer action. Invoke it after actual pointer movement, refreshed anchor and
endpoint check, immediately before ClickRatePermit.precommit and physicalpress.
Re-capture strict fresh CRS and verify exact durableattemptID, generation/lease,
queue/seq, boot/identity, unchanged pre-ordinal/phase/work/result state, both arm
bits and request-local confirmation. Invalidate if any changed; never reinterpret
an unconfirmed earlier dryrun request after arms become true. Barrier tests at
this exact seam change queue/arms/generation and prove zero precommit/press.
Do not weaken Guardian, native gate, freshness, rate, endpoint or identity guards.

Return an immutable finalized *per-call* physical receipt through Guardian
cleanup. Do not look it up from mutable last_pointer_execution or history after
the call. Controller outcome/checkpoint clearing uses append_archive_bundle with
one stable outcomeId and exact immutable payload. Add focused fresh-owner write
failure cases at pendingmarker, manifest, archiveartifact, checkpoint boundaries,
asserting exact payload/no second physical dispatch. Keep proof bounded.

For current mail action, interpret resultCount precisely: first ready click adds
exactly1 result (dryrun/started/terminal refusal/success); a later mail_items click
retains the started result count and may mutate that exact result to terminal.
Bind lastResult exact preseq/kind. Terminal current successor is either unchanged
seq/kind with terminal refusal/failure and blocked state, next contiguous seq, or
0/empty/complete; reject arbitrary jumps. Causal callback delivery and protected
operation success remain separate facts. Refused/failed/blocked paths cannot
permit an automatic retry. Source directAPI never supplies the causal proof.

IPC/CLI includes required cycleId, empty string for ordinary standalone manual
interaction or the exact active cycle ID. No activecycle caller can acquire a
cycle capability just by supplying its ID: only the daemon scheduler owns the
typed process-local capability. During awaiting_confirmation, an exact explicit
executor_click request may authorize ONE protected click of that admitted cycle,
queue and seq. Each later protected click needs a fresh request. Empty
confirmQueueId always means dry-run-only; authority is never durable/reusable.
No request arms either addon bit. Deadline/generation/lease/queue/seq/restart
invalidates authority. Required fields/noextrafields remain strict.

Additional exact verification ownership: tests/test_session_pointer_execution.py
(final callback/immutable percallreceipt tests only), tests/test_session_model.py
(executor_mailbox observation schema only), plus all files listed in this plan.
No production config changes until mailphase requires opt-in settings. Root owns
docsHANDOFF/runbook integration. Keep full default<180s.

## Parent continuation fence

An in-flight mail_items continuation is never a dry-run action: that Lua branch
calls protected() directly. Require both observed arms plus the exact fresh
one-click confirmation for any in-flight continuation; missing/disarmed state
blocks before input. The initial ready action may be a dry run when either arm
is false. Repeat every check at finalprepress admission.

The durable overall-action marker also fences unrelated standalone interaction
requests between physical clicks, not only restart. Only matching same-process
mail-action continuation can acquire its typed capability. A witnessed terminal
outcome releases that owner atomically; unknown/blocked/lost results do not.
Preserve existing DesktopDriver.run return behavior for other actions. New
receipt plumbing must not silently change unrelated backend/caller contracts.

## Disjoint implementation scheduling amendment

Telemetry Round3's source contract is now frozen; final checks await the shared
machine lock and its Sol reviewer has inspected the corrected state matrix and
payload design. Root releases the DISJOINT production slice for implementation
while PhaseA finishes verification. This does not waive PhaseA READY or final
integrated checks before click-phase acceptance.

Exact production ownership: src/crowley/session/{model,driver,daemon,controller,
journal,cli}.py. Exact newtests: tests/test_session_executor_click.py and
 tests/test_session_model.py. Additional existingtests allowed: pointer_execution
and driver_actions (observer fixture fix independently READY). Do not edit any
PhaseA-owned tests/protocol/motion/decoder/addon/harness, config/core/target or
trading source while telemetry is active. Read those consumers as needed and use
shared EXECUTOR-TELEMETRY-CONTRACT.md rather than relaying every field through root.
The final composed acceptance test belongs in the new executor_click test file.
Other fixturefiles require root source release first. No deploy/docsHANDOFF.

Scope is mail_collect only. Nonempty cycleId is rejected until a reviewed active
mail cycle exists; the later phase will supply a private typed cycle capability.
No caller-provided ID itself conveys ownership. Empty confirmation is dryrun-only;
inflight continuation requires both arms+exactfreshconfirmation before effect.
No source outside this fence, no fullsuite, no live actions. All pytest under
shared flock/pinnedCARGO. Default behavior remains unchanged without explicit
new IPC request. Source finalfreeze and independentSol review remain required.

## Review clarification: durable source evidence

Persist the complete bounded pre executor projection and the decoded post
projection along with their exact CRS tuples and physical receipt. Retain actual
validated frame bytes or a private immutable capture artifact that re-decodes to
those exact tuples; do not re-encode a Python dictionary and label it nativebytes.
Missing CRC/frame binding must fail, never default to0. Require these witnesses
through admission/finalization, not optional metadata at only one call site.

If raw-frame retention requires it, additional exact ownership is
src/crowley/session/protocol.py Frame decoded-evidence field and decode_frame
return construction ONLY, and src/crowley/session/decoder.py Sample/raw-evidence
plumbing ONLY. No wire format/schema/semantic-validation change; addon stays
unchanged. Decoder production path always supplies actual bytes; a manually
constructed fixture without evidence cannot authorize an executor click.
Alternatively capture the exact private source raster before normal cleanup,
with immutable hash/path binding and a round-trip assertion. Root must reverify
PhaseA112+ cases if its decoder/protocol source changes. Archive evidence stays
private and live checkpoints remain bounded, with append-only outcome history.

A started mail action needs a matching same-process standalone continuation even
with empty cycleId; cycleId is not itself that authority. Full pre-state includes
phase/inFlight/latched/progress/resultCount/lastResult/ordinal/source/arms/identity.
Initialready adds1 result; per-message mail_items preserves the started record
count and may mutate that exact result terminal. Next contiguous seq can be any
validated action kind; unchanged failed/refused currentseq requires actualblocked
state. No change to native addon semantics. Real two-message/mixed-successor Lua
frames must drive the public daemon/IPC regression, not manually constructed
transition dictionaries alone.

## Round2 review corrections and required proof

Sol Round1 NEEDS WORK despite64green; parent inspection agrees. Apply all grouped
findings before refreeze, not only the happy-path transition. No PhaseC edits yet.

- Initial/final click scene admission requires native motion safety plus exact
  chat and blockingUI refusal; after the final blocking capture repeat current
  generation/lease/Guardian/durableattempt checks before returning to precommit.
- A foreign already-inflight mail action with no process-local authority must
  refuse before anchor/intent/input. Implement the planned private same-process
  continuation capability now for this phase's standalone action; do not merely
  defer all continuations to C. Initial ready creates its owner only after a
  witnessed own started click; each continuation still needs both arms and fresh
  exact confirmation. Fresh owner never reconstructs authority from the journal.
- Complete physical receipts include actual refreshed anchor hash/capture ID,
  action/generation/identity/endpoint/rateprecommit/press/release/Guardian completion.
  Validate receipts before accepting/clearing a result. Preserve a known immutable
  receipt if post-frame acquisition fails; a missing/malformed receipt cannot
  authorize a successful terminal archive.
- Exact persisted executor checkpoint schema; malformed nested intent/overall
  never silently becomes absence. No changing a reserved logical outcome to a
  different blocked payload after archive publication fails. Separate dispatch/
  observation errors from archive/finalization errors; stage/replay the same
  immutable outcome through all actual Journal bundle write boundaries.
- Require the executor final callback (legacy actions stay unchanged); require
  actual CRC binding instead of0fallback. Native-construction competing-owner
  gate must match other IPC physical operations; installed CLI main must emit
  exact validated IPC fields.

Acceptance maps every finding to its actual regression: unowned in-flight reject;
owned two-message continuation; initial/continuation counter matrices; mixed-kind
successor; UI state at initial and final frames; pause/lease/attempt changes DURING
final capture (not only before callback); receipt missing/malformed/substitution/
cleanup and post-capture failure; malformed nested checkpoint; fresh-owner crash
at pending marker, manifest, archiveartifact and checkpoint writes; later pause/
stop preserved; exact CLI main/native-construction expiry/refusal. Keep one real
Lua/PixelDecoder/actual driver/defaultIPC composition and focused lightweight
cases; no giant duplicated native process matrices. Parent runs integrated tests
and schema6 regression slice after final sourcefreeze. Allpytest sharedlock.

Create phase evidence under .archive/executor-click-20261023/ (new ownership),
not the old launch-target artifact directory. Preserve earlier attempts.

## Round3 review correction

Round2 parent124 click/policy tests and114 schema cases passed with exact hashes,
but Sol found omitted authorization, witness and recovery distinctions. Initial
admission is ready/not-inFlight only; mail_items/inFlight always requires private
same-process ownership bound to queue/seq/generation/lease before anchor or intent.
Receipt identifies actual refreshed prepress anchor separately from the initial
admitted anchor. Guardian cleanup failure propagates its known sealed receipt to
blocked archival with guardianCompleted=false via call-local data, not history.
Stage the complete immutable outcome durably before archive publication. Fresh
constructor recovery must need no dead-owner finalization arguments. Test actual
staged-checkpoint plus pending/manifest/artifact/checkpoint boundaries, preserving
later pause/stop and never re-dispatching. A staging failure itself leaves unknown
ownership blocked. Required two-message/mixed-successor and foreign-inflight
proofs run real Lua bytes through public IPC/daemon, not private validators alone.

## Round4 exact closure

Round3 parent132+114passed, but overall schema still lacks seq and its stored
generation/lease are not checked. Add seq to every creation/validation site and
compare queue/seq/cycleId/generation/lease at daemon pre-capture and controller
admission, with one distinguishing drift regression per dimension.
Persist full actual rawFrameHex in the pre-input intent, validate actual decode,
hash/length/CRC and CRS/projection binding, and prove fresh-owner recovery after
physical dispatch but before outcome staging retains those bytes without retry.
The public armed two-message queue must itself contain a contiguous craft
successor, with public archived response/resultCount assertions. A separate
private validator proof is insufficient. Also test actual mail_items against an
empty owner (both capabilities and overall absent), with the intended initial-
state refusal before anchor/intent/input. Retain the existing owned continuation.
Add pause, lease and durable-attempt mutations during the final blocking capture;
all must prevent rate precommit/press. Map all five corrections to exact tests
and actual verification before DONE/sourcefreeze.
