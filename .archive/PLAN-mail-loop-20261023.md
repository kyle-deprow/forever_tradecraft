# Plan: ACK-bounded mailbox loop between sweeps

Status: offline runtime Round2 corrections active after Sol MAJOR ISSUES in the
first runtime slice. Telemetry, guarded-click and pure-policy phases are READY;
native deadline producer and whole-cycle composition have disjoint workers.
This plan does not authorize game input now.

## Outcome

After a fully acknowledged sweep, optionally route from the AH to the mailbox,
collect only the current `mail_collect` action(s) through the guarded executor
click operation, return to the AH, and resume repeat scheduling. The scheduler
must remain dry-run by default and must never type `/crowley arm`.

## Reserved source and sequencing

The active target worker currently reserves `controller.py`, `daemon.py`,
`protocol.py`, `config.py`, and target files. Do not edit those files until that
worker’s review is complete. Then implement in this order:

1. Land and verify schema 6 and the executor-click operation.
2. Add the durable mail-cycle phase and ACK marker in
   `src/crowley/session/controller.py` and
   `src/crowley/session/journal.py`.
3. Add the scheduler and route ownership in
   `src/crowley/session/daemon.py`.
4. Add the public opt-in/default-dry-run IPC/CLI surface in
   `src/crowley/session/cli.py`.
5. Add lifecycle/route/real-byte tests, then update handoff documentation only
   after implementation review.

No change is needed to `deploy/config/routes/stormwind.json`; use its existing
`auctioneer_to_mailbox` and `mailbox_to_auctioneer` routes.

## Durable phase and admission

Persist a bounded `mailCycle` object in the journal current evidence and an
append-only `mail_cycle` archive:

```text
{
  "phase": "none | preparing | to_mailbox | mailbox_open |
             executing | to_auctioneer | opening_ah | complete | blocked",
  "ackUid": "<exact loaded ACK UID>",
  "queueId": "<exact queue ID>",
  "generation": <controller generation>,
  "lastExecutorSeq": <last observed sequence>,
  "reason": ""
}
```

Entry is allowed only from repeat `WAIT_DUE`, after the existing ACK/reopen
boundary has been completed:

- the controller evidence has `ackLoadedUID == status.last_uid`;
- `pending.ids` is empty and scanner telemetry is `ready` or `scheduled`;
- the current queue identity/house/character is exact and its current action is
  `mail_collect`;
- the ACK UID is not already marked complete or blocked in the durable archive;
- no scan, reload, upload, executor, or other action intent is unresolved;
- the existing effective due time is far enough away for both routes, mailbox
  click/postcondition waits, all current mail units, AH reopening, and a safety
  margin.

Use the scheduler’s existing effective due calculation (`max(addon due,
controller anchored due)`). Do not invent a cadence timestamp. If the bounded
mail-cycle budget cannot fit before that due time, leave `WAIT_DUE` untouched and
defer; do not start a route that may collide with the next sweep.

The durable marker is written before entering interaction. A crash during a
route or mailbox transition therefore cannot be mistaken for a completed cycle.
A fresh owner must reconcile the phase and current CRS frame; it must not resume
the route or click automatically from a stale position.

## Interaction ownership and sequence

The controller transition is:

```text
repeat WAIT_DUE + current lease
  -> enter interaction / READY / same generation and lease
  -> route_to_mailbox
  -> mailbox_open
  -> executing
  -> route_to_auctioneer
  -> opening_ah
  -> complete
  -> exit interaction / revoke old lease / generation advances
  -> normal resume/reconcile / repeat WAIT_DUE
```

The existing interaction guard remains authoritative. Every route operation
must use `execute_route_walk()` and therefore retain fresh settled motion,
instance/zone, camera/native gate, combat/death, generation, and Guardian
checks. The repeat scheduler must not scan while mode is `interaction`; the
interaction `_advance` branch remains quiescent except for the explicit mail
cycle step.

At completion, persist `complete` and the exact ACK UID before revoking the
lease. Resume through the ordinary controller re-arm/reconcile path, not by
mutating state directly to `WAIT_DUE`. If re-arm or reconciliation fails, block
without rerouting or clicking.

## Mailbox and AH facts

- Keep `world-click` limited to `expect=mailOpen`. It already proves the
  `Mailbox` hover and post-click `mailOpen` state.
- Treat `Agent.mailOpen`, sourced from `MailFrame:IsShown()`, as the mailbox
  truth. Do not wait for or infer correctness from `MAIL_CLOSED`; that event was
  observed missing.
- After walking back and before opening the AH, require a fresh frame with
  mailOpen=false and clear blocking UI. Walking away may close the frame without
  an event; requiring closure before starting that walk would deadlock.
- Reopen the AH through a new interaction-mode wrapper around the existing
  guarded `open_ah` path in `daemon.py`: `_prepare_auctioneer_open`, exact
  Auctioneer Jaxon target/range evidence, SoftTargetInteract, conditional
  CTRL-F12 binding, Guardian keyboard receipt, and a fresh `ahOpen=true`
  postcondition.
- Do not add `ahOpen` to the world-click allowlist. The old runbook’s
  `world-click --expect ahOpen` example is stale and current CLI/tests reject
  it.

## Executor scheduling rules

The loop may click only `mail_collect`. It must validate the schema-6 executor
object before every click:

- exact cycle queueId and current seq/kind;
- `availability=valid`, matching house/character, visible button;
- `clickReady=true`, no ambiguous/blocked/latched state;
- fresh generation/lease/native/camera/identity/blocking-UI proof;
- the public executor request’s exact `queueId` and `confirmQueueId`.

Default mode is dry-run-only: if both addon arms are observed, the scheduler
stops and requires a separate explicit daemon request with the exact full queue
confirmation before any protected click. The scheduler never sets either arm
and never sends `/crowley arm`. An armed click remains subject to both addon
arms on every protected call.

For `mail_collect`, `started + mail_wait` is a wait boundary, not permission for
another click. After a fresh frame proves `mail_items`, `clickReady`, and the
per-mail postcondition progress, one more rate-gated button click is allowed
while the overall action remains in flight. Any missing/uncertain/started state
at restart blocks the queue; it is never retried, even if the unsaved result
record is gone from the reloaded game memory.

## Asynchronous owned mail completion

A witnessed physical click may be archived as started/mail_wait before the addon
later completes that message without another click. Add a controller-owned
observation transition for this case: require the same private process-local
mail owner plus exact queue/seq/generation/lease, and a fresh actual decoded CRS
witness bound to the last archived physical attempt (same boot/identity/ordinal,
unchanged result count, exact prior action's terminal result and valid terminal
successor). Durably archive that terminal observation with its own stable outcome
identity and clear only the matching overall-action owner atomically. It is an
observation, never a fabricated second physical attempt. Unknown/blocked/failed
states remain fenced. Do not directly clear private controller fields from the
scheduler. A fresh owner cannot reconstruct this permission from archive bytes.
Wire this read-only completion observation for both an active mail cycle and a
standalone same-process mail owner in interaction mode. Neither path may emit an
extra executor click to discover completion. Reuse the last owned physical
attempt's real pre/post evidence when validating the later terminal frame.

Test started/mail_wait -> later real Lua terminal success for one message with
exactly one physical click, no extra confirmation/input, then return-route
admission. Also retain the multi-message case requiring a fresh request per
mail_items boundary. Completion during mail_wait must not deadlock behind the
standalone overall-action fence.

## Tests and default entrypoints

Add focused lifecycle tests in `tests/test_session_mail_loop.py` (or the
reviewed transition file), with narrow updates to:

- `tests/test_session_transitions.py`: exact ACK-only once-per-UID admission,
  due-time budget refusal, interaction lease/generation transition, completion
  marker, resume/reconcile, and restart block.
- `tests/test_session_route_walk.py`: existing mailbox `world-click` only,
  rejection of `ahOpen`, route ownership, and `MailFrame:IsShown` close proof.
- `tests/test_session_runtime.py`: public `SessionIPC`/CLI mail-loop request,
  strict queue confirmation, dry-run default, no arm command, and no scan while
  interaction owns the lease.
- `tests/test_session_native.py`: fresh CRS bytes across route/mail/AH steps,
  identity/boot/generation fences, and guarded `open_ah` postcondition.
- `tests/test_executor.py`: one click per mail message, `mail_wait` versus
  `mail_items`, and no protected calls in the default queue.

The minimum offline proof must run through:

```text
WowClient.publish_agent/render_agent_capture
  -> PixelDecoder.decode/decode_frame
  -> installed crowley-session SessionIPC entrypoint
  -> route/mail/executor public methods
```

It must assert no protected API calls, no `/crowley arm`, exact ACK UID
admission, and zero click retries after simulated restart uncertainty. It must
not force a reload merely to obtain an execution upload; SavedVariables upload
may occur during the normal subsequent save cycle.

## Verification and acceptance

- One cycle per exact ACK UID, never once per polling tick.
- No route or executor click begins from `ACK_RELOAD_WAIT`, `REOPEN`, scanning,
  pending uploads, or an insufficient due-time window.
- Interaction mode owns the GUI exclusively; repeat scheduling is paused.
- Return to repeat mode uses lease revocation and normal re-arm/reconcile.
- Mailbox state uses `MailFrame:IsShown()`; AH reopening uses guarded
  `open_ah`, not world-click broadening.
- Queue/session/published arms and daemon `confirmQueueId` remain separate.
- Unknown, started, blocked, boot-changed, identity-changed, or lost-result
  clicks remain blocked across restart.

## Buildable work versus live blockers

Buildable offline: durable phase transitions, ACK/due-time admission, public IPC,
schema-6 byte plumbing, dry-run no-protected-call proof, route ownership, and
restart no-retry behavior.

Opt-in configuration may be added only in `src/crowley/session/config.py`;
it defaults disabled and dry-run-only. Do not change live deploy/config files.
An empty confirmQueueId means dry-run-only; nonempty confirmation is valid only
for that exact queue and cannot survive restart as real authority.

Focused checks use pinned CARGO and the machine lock:
`flock /home/dev/.cache/r-pg.lock uv run pytest -q tests/test_session_mail_loop.py tests/test_session_transitions.py tests/test_session_route_walk.py`.
Use scoped Ruff/checkformat; parent requires the full default <180 seconds.
No game/service/deployment, commits or evidence deletion. Keep one composed
lifecycle proof and small failures; avoid giant repeated process fixtures.

Live blockers: launch queue identity and ACK timing, actual route validity on the
launch client, actual mailbox frame close behavior, rendered executor-button
anchor/scale, XTEST callback delivery, and real protected API behavior. These
must be observed at launch; no native facts or coordinates should be guessed.


## Parent amendment after independent Sol design review

Sequence after reviewed telemetry+click phases, which replace the former active
target reservations above. One cycle handles exactly the admitted current
mail_collect seq; never budget or execute unseen successor actions. Preserve that
seq in durablecycle state even if addon currentSeq advances after terminal.

Use atomic Controller.begin_mail_cycle: validates exact WAIT_DUE/ACK/budget/lease,
persists full durablecycle and entersinteraction in ONE checkpoint. Ordinary
enter_interaction must not clear/hide this owner. Add cycleId, admittedSeq,
admittedEffectiveDueAt, fixed deadlineAt and awaiting_confirmation phase to the
bounded durable object. Type a private process-local capability bound to
cycleID/generation/lease for internal route/worldclick/executor/AHopen calls.
Reject unrelated IPC/motion requests across the ENTIRE cycle, including waits
between serialized calls. Exact externally confirmed executor requests may join
only awaiting_confirmation for one click, via daemon-owned capability, never by
trusting caller-supplied IDs as authority. Stop/pause/Guardian revoke remains
immediate; persist blocked/uncertain cycle before ordinary reconciliation. Any
fresh owner with any nonterminal cycle must block, even if generic actionIntent
is empty. Completion uses transactional archivebundle+checkpoint with stable
outcomeID, tested at actual durablewrite boundaries with a fresh owner.

At admission compute an explicit worst-case bound for both actual route bounds,
worldclick, every possible current-action mailmessage click+postconditionwait,
AHreopen and margin. Persist effective due and a fixed nonextendable absolute
cycle deadline. All nested operations receive min(own deadline,remainingcycle),
never reset the budget. Recheck before every new physical effect and after any
confirmation wait. If it cannot fit, defer without state/input changes. A known
expireddeadline blocks; do not begin returnroute that no longer fits.

Default scheduler remains disabled and dryrun-only. When both addon arms true,
enter awaiting_confirmation without input. A separate exact request authorizes
one physical protected click only; no implicit remaining-action authority and no
persisted confirmation across restart. Continue observing mail_wait without
clicking; new mail_items boundary needs a new confirmed request. Never allow a
stale waiting request to extend cycledeadline or change queue/seq authority.

The exact opt-in public request/CLI must expose queueId and current seq, with
empty confirmQueueId and disabled scheduling default. Match one exact strict
request shape for start/configure/status; do not create loose arbitrary kwargs.
Update this plan/contract with final field names before implementation completion.
No coordinates/UI scale may be invented: mailbox probing uses current measured
visual hint evidence and retained hover-confirmed worldclick; executor uses sealed
fresh buttonanchor. Configured route poses are provenance-bound beta facts only.

The existing model has no mailbox-object visual hint contract. After phase B
releases model.py, C may additionally change src/crowley/session/model.py and
tests/test_session_model.py ONLY to add strict mailbox-world observation:
state=mailbox_world, scene=world, modal=none, control=mailbox_object, configured
character/realm, code empty, idle=true, measured bounds inside the verified crop.
Use actual retained capture, identity/generation/lease and existing freshness
checks to derive a bounded client-relative hint. The world-click still requires
fresh native hover name Mailbox and expect=mailOpen. A generic viewport clear
point, configured center, fixed coordinate, or synthetic production provider
cannot substitute for this measured object evidence.

Exact geometry decision: model bounds use physical pixels relative to the
verified model_crop, as in existing _measure_pointer_anchor. Validate bounds
inside that crop, then hint=(crop_x+x+width//2,crop_y+y+height//2), also inside
the verified client child. Use radius=0 for this measured center; the retained
world-click performs one hover-confirmed probe and refuses if it is not Mailbox.
No UI-scale transform or guessed search geometry is needed. Retain crop/hash,
bounds, client identity, generation and capture timestamp in private evidence.

Runtime tests may additionally use tests/test_session_executor_click.py for a
small shared fixture extraction after B review; preserve every existing safety
oracle. Reuse real Lua/decoder/driver composition rather than duplicating a giant
native fixture. Root retains documentation ownership.

After B release, C additionally owns src/crowley/session/driver.py ONLY for
absolute-deadline propagation through DesktopDriver.run/prepare_command and
X11Backend action/identity/focus/keyboard/pointer helpers. Current generic run and
prepare_command do not carry that deadline to every native subprocess, so a
daemon-only timer would not satisfy the fixed bound. Preserve all admission,
Guardian, event, receipt, rate and legacy-caller behavior; no native API or wire
changes. Narrow deadline regressions may extend tests/test_session_driver_actions.py
and tests/test_session_pointer_execution.py. Every blocking provider/subprocess
gets the remaining bound; checking only after it returns is insufficient.
Emergency release/cleanup must still run after cancellation to free held input.

Tests must prove competing IPC refusal during route gaps/mail_wait/confirmation,
immediate stop/pause, nonzero effective due/max composition, propagation of one
absolute deadline through nested real entrypoints, one-seqbudget/onceperACK,
exact per-click confirmation consumption, fresh-owner uncertainty, and ordinary
resume/reconcile ownership after complete. Preserve one meaningful real-Lua/
PixelDecoder/defaultIPC lifecycle composition, not many redundant expensive ones.

## Exact public request contract (root design)

Use process-local opt-in, disabled after every daemon construction/restart. No
live deploy config changes or persisted enable/armed authority. The journal
retains cycle audit/uncertainty, not future permission to start new cycles.

- `mail_loop_start`: exactly command,generation,queueId,seq,confirmQueueId.
  queueId/seq must be explicit, current and valid; confirmQueueId must be empty
  (scheduling itself cannot grant protected-click authority). It enables this
  process's scheduling for that exact queue+admittedseq only. Normal WAIT_DUE
  observation performs atomic admission; no forced startup cycle/input.
- `mail_loop_status`: exactly command. Read-only enabled binding/currentcycle,
  no identity bypass and no hidden side effect.
- `mail_loop_stop`: exactly command,generation. Disable opt-in; an active cycle
  is marked blocked and paused/revoked through normal control immediately,
  preserving unfinished ownership, not auto-walking back or clearing uncertainty.

CLI names mail-loop-start/--queue-id/--seq/--generation (empty confirmation
implicit), mail-loop-status, mail-loop-stop/--generation. Armed awaitingphase
uses the separately reviewed executor-click --cycle-id --queue-id --seq
--confirm-queue-id exact one-click request. No start flag may authorize all later
messages. A nonempty confirmation on mail_loop_start is rejected.

After admitted current seq ends, disable this binding; a successor action/queue
requires a fresh explicit start, not inferred selection. Once-per-ACK archive
prevents repeat scheduling even if the same binding is re-enabled. Budget may
defer large maxMessages bounds even when the actual inbox is smaller: use small
reviewed queue maxMessages for launch dry-run qualification; do not guess unseen
workload or claim the loop will always fit within900seconds.

## Parallel pure-policy slice (before B source release)

To use independent work while click fixes/review run, a Luna worker may implement
ONLY new src/crowley/session/mail_loop.py, new tests/test_session_mail_loop_policy.py,
.archive/mail-loop-20261023/ evidence, and
.archive/launch-readiness-20261023/MAIL-LOOP-POLICY-CONTRACT.md. No existing source
or test file, no B source edits/import churn, no journal/IPC/runtime side effects.
This is preparation, not completed scheduling. Runtime wiring waits for B READY.

Build a small immutable policy API for exact binding, collection ACK boundary,
operation-budget bounds, and admitted/deferred result. It consumes already
validated schema6 Snapshot plus controller-boundary values and durable seen ACK
IDs supplied by the caller. It never mints lease/continuation authority or
substitutes for atomic runtime admission. Freeze/publicize the small API contract
so final wiring uses those exact interfaces without parent field relays.

Pure admission must enforce disabled-by-default/process-generation binding,
repeat WAIT_DUE, current exact loaded ACK/status UID (including actual loaded
ackedIds), empty pending IDs/no unresolved action/reconciliation/stop/closeout,
ready or scheduled scanner, exact queue/seq/house/character, initial ready
non-inflight/nonblocked/nonlatched/nonambiguous mail, positive workTotal with0done,
and once-per-ACK. It must NOT require executor button visible/clickReady at the
AH; those only become true after the mailbox opens. No capability inference.

Effective due is exactly max(addon dueAt,last actual start+900). Compute an
explicit worst-case total from supplied finite positive operation limits:
both route bounds + worldclick + each admitted maxMessages unit's click and
postcondition wait + guarded AH reopen + safety margin. Return fixed effective
wall due / nonextendable deadline and detailed budget, or defer when it cannot
fit. No now+cadence invented schedule, unseen successor work, fractional/boolean
work count or nonfinite/negative durations. Runtime later binds this to one
monotonic deadline and repeats admission atomically before any effects.

Focused unit tests cover identity/ACK/pending/once/budget/phase differences and
max(addon,anchored) boundary using independent expected arithmetic. Include a
small actual Lua Snapshot positive as data-shape proof, explicitly not default
runtime composition. No sleeps/process matrices. Allpytest shared flock and
pinnedCARGO, scopedRuff/format. Sol review and parent reproduction before wiring.

Armed awaiting_confirmation occurs after guarded route/mailbox-open admission
and before an executor press. The explicit start authorizes those reversible
route/open steps; it never grants a protected click. While awaiting, no new
physical effect occurs absent its fresh exact one-click confirmation, and the
original cycle deadline keeps running. This clarifies earlier 'without input'
wording: no unconfirmed executor press, not a requirement to confirm a button
before the mailbox has been reached.

## Pure-policy Round2 review correction

Round1 Sol NEEDS WORK despite21green. Actual Snapshot is authoritative for loaded
ackedIds, pending IDs, scanner phase and addon dueAt; remove duplicated caller
wire fields or enforce exact equality. Match both executor identity and the
current top-level house/context character to the binding. Require consistent
current time (>= snapshot.wallTime) and a positive actual prior start; missing
ACK/start or other normal ineligible mode/state is a bounded deferral, not a
malformed-input exception. Add an explicit session-mode boundary value and defer
unless repeat. Require the actual Snapshot class, not arbitrary .value objects.

Separate latest_start_at = effective_due - total_budget from the fixed cycle
COMPLETION deadline, e.g. effective_due - safety_margin. Fit is now+total<=due.
At exact lateststart boundary, remaining completion time must equal the complete
operational budget (excluding reserved margin), not0. Runtime later propagates
that completion deadline unchanged; no dynamic extension.

Collection input types must be exact immutable tuple/frozenset/tuple (or remove
wire duplicates entirely and trust validated Snapshot arrays). Reject mutable or
string substitutes without coercion, wrap float overflow as MailLoopPolicyError.
Tests use a real Lua-loaded Data.lua ACK and derive wire/epoch facts from its
frame, plus independent addon-wins/anchored-wins/equality arithmetic, a larger
successor ignored, scheduled scanner, every unresolved flag, real session identity
mismatch, malformed types, missingstart and wire/boundary disagreement. Negative
pure tests remain advisory proof, not a claim of runtime ownership/authority.
Only the4 original pure-slice files may change. No B source or runtime wiring.

## Pure-policy Round4 review correction

Round3 parent42 policy tests passed; Sol found disabled falsey malformed fields
could pass zero/empty comparisons. Validate exact integer/string types first,
including disabled bindings, then compare canonical zero/empty defaults. Include
generation=False, seq=0.0 and queue_id=None regressions, a codec-valid admitted
ready scanner frame, and a malformed nonstring controller ACK proof. Keep the
policy advisory and source-disjoint until both policy and phase B are READY.

## Parallel runtime ownership override

Both B and pure policy are now reviewed READY. Root split C into disjoint Luna
assignments: runtime worker /root/mail_design owns controller/journal/daemon/CLI/
model and its listed runtime tests; deadline worker /root/launch_design exclusively
owns driver.py, test_session_driver_actions.py and test_session_pointer_execution.py.
This overrides the earlier combined C driver ownership until explicit handback.
The shared MAIL-RUNTIME-DRIVER-CONTRACT.md in launch-readiness-20261023 is the exact
producer/consumer API; workers do not depend on peer task routing. Existing partial
driver changes remain in place. Each slice requires Sol acceptance and parent
verification, followed by integrated plain default <180s. Root owns docs/checks.

Runtime integration also corrects receipt epoch binding: physical
receipt.generation is the Guardian input lease supplied to driver.run, while
intent.generation is the controller/IPC generation. Daemon/controller validators
must compare receipt.generation to intent.leaseGeneration, retaining independent
semantic generation guards. Add a real public driver/IPC case with unequal
current controller and lease counters, plus wrong-lease refusal. The existing
executor_click test file is released for this narrow regression/helper update.

## Runtime Round2 acceptance corrections

Sol found MAJOR ISSUES despite parent379 passing focused cases (77.777s external,
14 hashes unchanged). The new composition worker exclusively owns NEW
tests/test_session_mail_loop_composition.py per PLAN-mail-loop-composition-20261024.md;
runtime producer may read/run it but may not edit or weaken it. Driver producer
additionally owns pointer_execution.py only for deadline-aware precommit. Root
retains shared contracts; exact public IPC shapes remain unchanged.

- Admission requires actual Snapshot and exact immutable policy types, rechecks
  the complete policy under the controller lock from current controller and wire
  facts/current time, and cannot leave a live capability after uncertain save
  either before or after atomic replacement. No input on any admission failure.
- Persist full immutable staged logical complete/blocked outcomes before bundle
  publication. Fresh constructor replay at pending/manifest/artifact/checkpoint
  needs no old-owner arguments; preserve later operator holds. Stage failure
  blocks and never emits input. Do not replace a reserved outcome's payload.
- Archive blocked ACKs durably on every pause/stop/revoke/error and prevent new
  admission until failed publication is repaired. Block A, admit B, then A must
  remain refused across restart; a current marker alone loses history.
- Failed/refused/blocked/lost executor outcomes retain their exact audit but
  block/revoke the cycle. They never start a return route or AH-complete path.
- Enforce a one-way phase graph, rejecting skip/backtrack. Complete only from
  opening_ah after fresh AH-open/mail-closed proof. Use normal re-arm/reconcile.
- Store admitted units/expanded bounds and check ALL remaining worst-case work
  before every effect and after waits/confirmation, including return/AH reserve.
  An expired awaiting_confirmation cycle must block immediately when observed.
  Pass the unchanged intersected deadline into executor driver.run/postcapture
  and the initial AH identity lookup as well as all other nested operations.
- Completion observers must use valid MotionFrame/native evidence; protocol.Frame
  from capture_status has no identity_fingerprint. Unarmed default scheduling
  actually performs its one dry-run click; armed mail_items requests a new exact
  confirmation. Async terminal observation and standalone completion never click.
- Focused tests must distinguish exact public CLI/IPC shapes, ownership during
  gaps/waits, stop/pause/revoke, fresh per-message confirmation, budgets/deadlines,
  retained visual facts, return/AH/rearm, blocked UID history and fresh-owner real
  write-boundary recovery. Separate button proof and fake Owner status are not a
  whole-cycle proof. Correct progress claims to match actual evidence.

## Runtime Round4 acceptance corrections

Independent Sol review of Round3 found MAJOR ISSUES despite the green core slice.
The runtime worker retains only its existing source/test ownership; independent
composition/recovery files and accepted driver Round6 remain read-only.

1. Implement `Controller.accept_mail_terminal(*, capability, outcome_id)` exactly
   as MAIL-TERMINAL-PROOF-CONTRACT.md. Generic phase transitions cannot authorize
   return. Validate an already-durable causal physical/asynchronous terminal
   outcome against exact queue/admitted sequence/original controller and lease
   epochs/cycle/raw evidence and successful status. Completion requires the
   privately accepted proof plus fresh AH-open/mail-closed evidence. Preserve
   maxMessages as an upper bound: dry-run collects zero and a real inbox can be
   smaller; terminal advancement can reset native counters. Separate budget
   settlement from observed native progress without inventing collected counts.
2. One absolute operation deadline covers each whole pipeline: model/world click/
   postcondition, return route/postcondition, and AH preparation/identity/input/
   postcondition. Per-message async wait starts once and is never reset by polls.
   Recheck all remaining reserved work before/after waits. Sample wall/monotonic
   clocks coherently so rollback cannot extend authority.
3. Admission checkpoint errors before and after atomic replacement fence/revoke/
   block the candidate and terminate daemon advance without scan fallthrough.
   Revoke errors must not skip durable blocked publication; synchronize actual
   Guardian epoch, attempt persistence/publication, then surface errors.
4. Linearize start/stop/replacement/completion/status with a control epoch reserved
   under lock before capture. Reject stale generation/active ownership before
   capture; compare epoch at commit. Completion clears only its exact owned binding.
5. Ordinary `Controller.resume` must reject unresolved live/staged/restart mail
   ownership before changing generation/arming, as runtime-evidence resume does.
   Preserve pending block history and unknown-input fences.
6. Add negative oracles for actual daemon advance fallthrough, direct/asynchronous
   failed/refused no motion, control races, exhausted operation budgets and public
   CLI shapes. Forged terminal authority must leave state unchanged.
7. Reject non-UTF8/lone-surrogate queue IDs with controlled errors, and compare
   executor house/character as well as top-level identity before public start.
8. Keep progress claims tied to actual proofs. Both real default and armed cycles
   must pass before readiness. `run_once` must capture/advance exact live owned
   cycles and same-process standalone completion despite ordinary interaction
   READY quiescence; do not weaken fresh FRAME gates or act on NO_CHANGE.

## Runtime Round5 review corrections

Round4 parent core/recovery128 passed/5.087s with15 frozen hashes; Sol nevertheless
found four production defects (sol-mail-runtime-round4-review.md). Runtime source
is released only to its existing Luna owner for this correction; driver and new
composition/recovery/control files stay read-only.

- Persist/derive validated mail_wait versus mail_items ownership. An immediate
  first callback may already advance workDone and expose mail_items: that next
  message still needs a reserved click and new confirmation. Executing/lastSeq
  alone cannot subtract a click from remaining work.
- Reserve fixed current-operation deadline remainder plus all future operations,
  instead of adding the full world/route/wait bound again after partial/completed
  work. Exact-fit admission must survive valid bounded progress without extension.
- Bound initial run_once captures by the live cycle/per-attempt deadline. Retain
  the actual started standalone attempt's deadline across polls; reject expiry
  before/after captures including NO_CHANGE, with no missing-record fallback.
- The terminal proof gate independently checks raw-valid pre/post boot, identity,
  advancing sequence and queue/house/character continuity against original admitted
  evidence before granting return authority. Test foreign/stale valid frames and
  preserve state/capability on rejection.

Add distinguishing focused regressions, then freeze producer for Sol re-review
and parent reproduction. No broad serial matrix required before handback.

## Narrow driver producer correction from composed AH evidence

Parent inspection found that the new composition fixture injected a missing
submit_command precondition inside its observed DesktopDriver.run wrapper. That
changes production admission and is forbidden in a composition proof. Remove it.
Actual DesktopDriver.prepare_command passes its caller precondition for typing
but omits it for submit, while real X11 run rejects any action without one.

Luna /root/launch_design (accepted driver owner, currently controls-test owner)
is additionally released ONLY driver.py and test_session_driver_actions.py for
this narrow correction: carry the actual caller's precondition into submit under
the same unchanged absolute deadline; preserve fresh exact EditBox readback and
all Guardian/native guards. Add positive propagation and changed-guard refusal
oracles. Do not loosen driver.run or supply a fabricated guard in tests. Other
driver/pointer files stay frozen. Static and locked focused driver checks, Sol
re-review and parent reproduction are required; Round6 manifest becomes historical
only after this explicit source edit, and a new driver freeze follows DONE.

## Runtime Round6 corrections and durable regression coverage

Sol source Round5 found3 remaining defects: cycle-owned started results do not
copy the controller's private continuation token into the daemon; current-work
remainder and fit mix two clock samples and reject exact-fit progress; terminal
proof revalidates raw post evidence but not archived raw pre evidence. Existing
runtime owner is released for these scoped corrections only. Keep all prior
ownership/deadline/recovery guards and accepted driver/new test files read-only.

Persist distinguishing runnable cases, including daemon immediate mail_items
reserve/new confirmation, current-operation exact-fit remainder with ticking
clock, fixed standalone/outer NO_CHANGE expiry, raw-valid foreign boot/sequence/
identity/queue-house-character terminal rejection, and invalid raw pre evidence.
Source owner's shared _accept_seeded_terminal fixture must reach legal mail phases
before begin/finalize; no test may bypass terminal proof. Ephemeral probes and
pytest cache are not a substitute for exact logged results and regression cases.
