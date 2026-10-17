# Engine review round 8

Sol verdict: MAJOR ISSUES despite 64 scoped/independent tests. Conservative
dispatch uncertainty, exact normal UID checks, native receipts/full records,
phase errors and fresh fence dispatch are corrected. Four production gaps remain.

## Controller and transaction owner

Own only src/crowley/session/controller.py, src/crowley/session/journal.py and
tests/test_session_transitions.py, plus CONTRACT-session-recovery.md for the
implemented public API. Main ownership is now split explicitly; do not
edit daemon/config/protocol/evidence or other tests. The parent additionally
assigns tests/test_session_regressions.py solely to update the one stale
test_restart_reconciliation_keeps_unresolved_intent_until_complete_facts fixture
with actual full evidence required by the new API; preserve its assertions and
all independent negatives. Its previous owner is inactive and build owner released
this file. Also update test_ack_reload_waits_for_data_publication_and_retains_loaded_ack_after_refresh
with real full SavedVariables evidence before completing acknowledgement; retain
its original publication/loaded-ack assertions. A separate build-refresh
owner changes current-client fixtures/config for the installed70425 client.

1. Define honest restart resolution for EVERY ActionKind, including positive
   scan completion, open_ah, dismiss_disconnect, reconnect_game, select_arthur and
   enter_world. Test a fresh owner for every kind and actual matching postcondition.
   Remove unused kinds rather than persist unresolvable actions. Missing proof
   must remain blocked; no generic absence rule to abandon save/upload/ack without
   a complete rejected outcome. Completed logout must resolve from read-only
   character-select plus stable empty-file proof without invented Agent phase/boot.
2. Recovered acknowledgement must persist exact UID/load time/boot/sequence,
   reconstruct complete stable format-2 evidence and perform qualification once.
   Do not set REOPEN and skip qualification. Bind companion-uploaded UID, Data ack
   UID, loaded UID and qualified evidence UID explicitly. If the evidence cannot
   be proved, publish a truthful rejected outcome rather than count or drop it.
3. Fix outcome transaction recovery. Replaying historical manifests in hash order
   currently rolls newer state/counters back to an older outcome. Use a monotonic
   commit identity/order or applied/pending markers; repair artifacts idempotently
   and apply only the correct latest committed controller state. Manifest creation
   failure must retain a DURABLE path to retry qualification/outcome publication.
   Cover failure at every write, including the first manifest/pending commit, with
   a fresh owner, plus multiple chronological outcomes with reversed hash order.
   Counters and complete accepted/rejected records must occur exactly once.

Publish concrete controller reconciliation/qualification interfaces to the daemon
owner before it edits consumers. Preserve canonical intents/deadlines and pause/
stop no-input behavior. Tests must exercise public production restart paths, not
only simulated reload transitions. The existing one-outcome archive test is not
adequate. Complete this bounded outcome, strict tests/Ruff/format/diff then freeze.

## Daemon and operator handshake owner

Own only src/crowley/session/daemon.py and docs/REPEATING_SCANS.md. Runtime test
ownership is now released explicitly to a fresh bounded fixture worker below.

4. Implement real bounded waits after operator readiness. After bootstrap-ready,
   wait for the actual newly constructed Agent; after hold-required, release
   intervening normal frames until actual fresh held/0; after measure-ready,
   wait for exact update1 then enforce all100 sequential publications; after
   resume-required, wait through held/100 until actual fresh same-boot normal/0.
   Immediate one-shot captures cannot let an operator respond. Keep original
   timestamps, generation/identity checks, strict ordinal/cadence/boot validation,
   durable history before reset and complete artifact cleanup on every poll/failure.
   Publish actual status and exact manual commands in documentation.
5. Before login recovery in RECONCILE with no Agent, detect a completed logout at
   character select using read-only scene and stable empty queues. Never relog to
   discover an already completed logout. Use the controller owner's new intent-
   specific/recovered qualification route; do not skip it on REOPEN.

Replace runtime capture-count fabrication with a callback/operator-driven REAL
Agent fixture using hold/measure/resume. Allow delayed operator reactions with
normal/held frames, genuine absence until bootstrap, and timeout/cancellation
cases. Native driver owner keeps its six files and fixed native10 contract.
Rehydrate durable restoration/receipt status after daemon restart if applicable.

## Shared completion

Workers may lack the parent's collaboration namespace. Exchange actual task IDs
once and verify routing; the app may reject peer task messages. Use the shared
CONTRACT-session-recovery.md for the actual API when routing is unavailable.
The parent supervises whole outcomes.
No cross-owner edits, GUI/game input, live resets, services, persistent data,
credentials or git mutations. All strict warning checks, parent combined suite
and consolidated read-only Sol re-review remain required. Native performance,
human input and three new qualifying live sweeps have not started.

## Consolidated frozen-producer review correction

Sol found two remaining production defects despite60strict producer/regression
passes. Controller owner keeps its existing five-file fence (controller,
journal, transitions, the one regression fixture and shared contract). Daemon
owner remains separate. Complete this batch, not isolated patch approvals.

1. Qualification stages full durable proof, then exposes terminal mutation in
   memory before the first immutable outcome marker. A marker failure leaves
   memory REOPEN/streak1 while disk is QUALIFY_PENDING/total0. The ordinary
   daemon block/save then persists partial counters and destroys retryability.
   Make every accepted, rejected and cadence outcome publication failure leave
   exactly the staged state in memory and disk. Error handling must preserve
   that durable retry path; do not duplicate writers. Test real public methods,
   keep the failing owner alive, exercise its normal block/error handler, then
   destroy it and retry from files alone exactly once; also continued-owner
   retry and later publication failures must not double-mutate or conflict.
2. Read-only restart qualification currently returns REOPEN/cleanup although
   fresh owner invalidated live gates. After repair, keep terminal work in
   resumeState and enter durable PAUSED or fresh calibration gate; require
   explicit resume and new native/input proof before any reopen/logout input.
   Cover both disk-only pending retry and recovered acknowledgement, accepted
   and rejected outcomes. Ordinary same-owner successful scan qualification
   retains its existing authorized flow. Do not add defaults masking missing
   evidence or resurrect serialized calibration flags.
3. A dispatched scan has no new UID until Finish. Its checkpoint carries an
   empty or previous accepted UID, while restart observation finds a new stable
   lastSaved UID. Bind positive scan completion from the new complete stable
   evidence, exact persisted startedAt/house/plan and new-vs-prior identity;
   only then set last UID. Do not require the pre-dispatch UID to equal a UID
   that did not exist yet. Test first scan, later scan, wrong start and old UID
   through actual fresh-owner public recovery.

Correct the shared contract's blanket fresh Agent boot requirement: menu actions
have no Agent, metadata/openAH normally use the same boot. They require actual
fresh identity/intent/capture-bound positive observations from the daemon's
existing named visual producer. Save/ack reload still require changed boots;
enter-world must bind actual fresh Agent/world observation after menu transition.
Coordinate only concrete consumer/API fields through the shared contract.

Resolve the dispatched-scan/ready-empty no-op policy explicitly: retain a
truthful durable rejected scan attempt (no fabricated sweep/evidence/UID or
accepted count) rather than silently treating it as a completed data cycle.
Fresh-owner test must retain the attempted action and exact reason, and no
input may be replayed. Keep unknown/incomplete observations unresolved.

Verification: owned transitions plus session/evidence/independent regressions
with the three strict filters, Ruff check/format, compileall, diff check.
Actual complete tests and immutable producer freeze before Sol re-review.
No game, live resets, services, deployed state, git or other owners' files.

## Runtime fixture owner split

Fresh Luna owns tests/test_session_runtime.py and ONE exact driver.py expression:
in DesktopDriver.decode_native_capture, use self._clock() instead of
time.monotonic() for the ORIGINAL decoder.decode monotonic argument. No other
driver source changes. Production default clock stays actual monotonic; decoded
sample timestamps must never be rebound/restamped later. Parent must review
this delta against the already-cleared native source and reproduce checks.

Replace count-based native fabrication with real WowClient AgentFrameBytes and
production decode, operator callbacks using actual hold/measure/resume. Prove
absence until load, delayed normal frames before held0, held0 before update1,
exact100publications, held100 before resumednormal0, timeout/revocation and
capture cleanup. Separate this native handshake fixture from existing simulated
scan/upload/ack lifecycle if useful; rewriting the entire Lua Scanner lifecycle
is outside scope. Keep existing three-cycle/socket/closeout/restart assertions.
No global stdlib time monkeypatches: inject consistent clocks only at the changed
boundary, leave real watchdog/socket/background timing intact. Realtime100sec
is acceptable if deterministic virtual time cannot stay correct; avoid hours
of unrelated fixture work to save seconds. Other source/docs/test files belong
to active workers and are read-only. Whole bounded batch, exact strict runtime
tests/Ruff/format/compile/diff, final DONE/freeze and Sol integration review.

## Consolidated frozen-consumer review correction

Sol consumer verdict NEEDS WORK. Daemon owner reopens daemon.py/docs only;
runtime owner supplies focused regressions separately. Preserve reviewed actual
native waits/receipts/timestamps/cleanup and honest menu visual observations.

1. scanner_idle for restart must depend on ready/scheduled phase and absence of
   an active query/sweep, not pending.ids being empty. The completed saved UID
   legitimately remains pending before acknowledgement. Pass pending IDs as
   separate proof. Test complete scheduled/ready scanner with one pending UID.
2. After any read-only no-Agent uncertain-intent resolution attempt, remain
   without input while RECONCILE+restartUncertain holds. A logout with queues
   still settling must never fall through to _recover_login. OSError/absence
   during other pending effects also must not dispatch a new action. Expected
   enter-world loading can temporarily have no Agent; wait under the existing
   durable deadline instead of immediately misclassifying absence as corruption.
   Never weaken rejection of invalid frames into permission to act.
3. Reconstruct and strictly validate complete stable SweepEvidence BEFORE
   ack_reload_complete clears the intent/moves state. Missing full proof must
   leave ACK_RELOAD_WAIT unresolved/blocked or publish truthful rejection; remove
   the skip branch that assumes a future sweep can qualify this UID. Every
   acknowledged UID needs exactly one complete qualification outcome.
4. A JournalError during disk-only qualification retry must not call block or
   issue a second journal mutation. Leave the exact QUALIFY_PENDING checkpoint
   intact or terminate the owner so systemd can restart/read-only-recover. Ensure
   outer error handlers also preserve it; no partial counters/overwrite/replay.

Runtime owner tests actual daemon consumers for these cases, not just controller
calls. Daemon owner reports exact API/behavior changes through parent/shared
contract without editing runtime source. Freeze after Ruff/format/compile and
available focused checks; final combined strict runtime/full suite and one Sol
integration re-review required. Same source fences/no game/services/data/git.

Final integration finding: daemon _command('/crowley scan') persists SCAN
attempt1/dispatched, then begin_scan creates attempt2/pending. Preserve the
existing just-dispatched canonical SCAN intent/result rather than minting a new
attempt. Add actual daemon/public-flow regression through restart ready/empty:
one attempted input, durable truthful UID-empty rejected outcome exactly once,
no replay/loop. Cover observed automatic scan admission separately where needed;
do not falsely claim a second input was dispatched. Controller/transitions owner
only; runtime owner refrozen and native timing patch remains disjoint.

Final boot-reference refinement (same root correction): reference must be the
actual pre-effect B0 persisted at expect_boot/dispatch, before observe_frame
can replace frameBoot with B1 and clear expectedBoot. Capturing at constructor
or pause is too late after an effect has settled. Retain B0 through WAIT, pause
and crash; B0->expectB0->observeB1->freshowner->B1 must resolve, B2 must block.
Same-process pause/resume uses existing B0, never overwrites it with B1.
Enter-world legitimately has no prior Agent: a fresh first nonempty B1 is valid
when prior boot was empty; where B0 exists a change is required. Preserve the
first observed post-effect identity so churn is rejected even across restart.
Correct synthetic tests that skipped the actual B0 frame then incorrectly
authorized a second new boot. Controller/transitions/shared contract only,
focused real public ordering tests and final Sol review before live readiness.

Final qualification pause correction: preserve the durable staged outcome
through pause/resume, but use the normal live input calibration/re-arm path
before retry may expose REOPEN or cleanup. A real DesktopDriver/RecordingBackend
regression asserts guardian revocation, direct paused-retry rejection, explicit
resume/re-arm, read-only reconciliation and exactly-once repair to armed REOPEN.
Parent focused9tests pass. Final Sol re-review is active. The broad snapshot
had400passes and one stale restart fixture lacking canonical pre-effect B0;
fix the fixture rather than infer missing B0 from frameBoot on restart.

## Final frozen engine verdict: READY (2026-10-16 04:42 UTC)

Sol reports no Must-Fix, Should-Fix or Nits. The exact corrected restart
regression passed independently with all three strict warning filters and a
private desktop lease. Luna full transition/regression84passed; parent final
qualification9passed. Runtime12previously passed independent Sol.

Final hashes:
- controller.py: f50b2bea14ea6f5fc2ed7f74731428e952871002e4e740268ce3908150789b05
- journal.py: fdc246c4f6e1df9fadfc0000e213bf57c6e8d10753ba153f7d110e44f9052756
- daemon.py: 65d9314c825fee4877c544c962ffbe227e6099492c64d700b711f80c54b3d9b0
- test_session_runtime.py: c7551ba76d994d945865ecb7287b698713dd1c9140af741590d1d3d9650835b9
- test_session_transitions.py: a0f9525644046a057533acbc84ea2958ad771fadba1e7f34d054077f91d7b718
- test_session_regressions.py: dfb0e40c57d7473d5e91247326ef5108ffa156862b6c7629d26d64095b3adef9

The final parent full strict suite remains running. All source is frozen. The
sole Luna operator is cleared for unarmed live native/input calibration; this
READY verdict does not establish physical input proof or scan acceptance.

Parent final frozen full suite completed **402passed/15DBskipped**,
17knownwarnings,389.41s, exit0 under all3strict filters/private lease. The15DB
tests were separately verified on the removed disposable container. Live
native measurements begin only after this test load ended.
