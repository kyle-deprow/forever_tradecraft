# Native operator final closure plan

Status: root-approved for implementation; final Opus arbitration below supersedes
conflicting phase descriptions in the original plan. This is
an offline two-file repair and proof stage. It authorizes changes only to the
frozen `tools/native_calibration_operator.py` and
`tests/test_native_calibration_operator.py` from
`native-operator-production-proofs-20261018`. Do not edit native source,
Guardian, driver, input tool, addon, protocol, config, services, GUI, or a third
source file; do not commit, reset, stash, revert, promote, or use the live
desktop.

The current six R7 native files are rejected development inputs. They can expose
interfaces during the offline edit but supply no acceptance evidence. Final
acceptance requires a clean verification tree containing the exact final helper
pair and the separately accepted seven-file R8 native freeze, followed by the
same composed cases and final helper suite. No R7 test result may be relabeled as
R8 acceptance.

## Patch order

### 1. Fix the four bounded source paths

1. In the actor's indeterminate known-ID bootstrap branch, replace the current
   cleanup horizon `max(old_expiry, now + grace)` with a bound strictly after the
   old expiry: `max(old_expiry, now) + KNOWN_ADMISSION_CLEANUP_GRACE`. Apply this
   only as exact-ID cleanup protection. Do not retry bootstrap, claim the unseen
   canonical expiry, admit input, or guess a new ID. Owner EOF/death must still
   produce at most the existing exact cancellation operation and bounded exit.

2. In `_await_calibration_terminal`, validate `calibration_status` identity and
   recognize operation `error` before calling construction recheck. Set the
   terminal-error flag and raise the original daemon error immediately; keep
   recheck as the completion/finalization proof for `complete`. During cleanup,
   require `status` to show the old generation in `NATIVE_CALIBRATION`, the same
   native operation in explicit `error`, then require `pause` to return a
   strictly newer `PAUSED` generation, an explicit non-running native operation,
   and `guardian.armed is False`. Clear the closed measure operation/reservation
   and phase deadline values used for request budgeting, while leaving the actor
   armed on the old known ID. Give empty-ID `recovery_begin` one fresh bounded
   client request deadline. Only its validated canonical reply may atomically
   replace the actor generation, ID, and expiry before recovery input. Preserve
   the original measurement failure as the raised result and receipt failure
   even when recovery succeeds.

3. Give each chat action its actual phase bound. The original Sol prescription
   to map all four provider commands to providerDeadline is superseded below:
   that deadline belongs only to initial construction. Map finalize to
   `finalizeDeadline`; defer,
   reload, and recovery use the minimum reservation/operation bound. Select one
   absolute deadline before the first gate and use it for recheck, identity,
   capture/readback, preflight budget, `FixedInput`, emitter READY/GO/PRESSED,
   and the watchdog ownership publication that precedes GO. Keep the existing
   authentic 130-ms character duration and existing action margins; add no time.
   A sequence that cannot fit refuses before the first Return or pointer move.
   Once a press may have occurred, exact watchdog release and child reap remain
   independently bounded rather than being cut off by the expired phase.

4. Make receipt failure fail closed during active work. An event publication
   error becomes the first causal error and prevents the next physical gate.
   Set protected cleanup before publishing terminal/cleanup events so subsequent
   receipt errors cannot replace an earlier operation failure or interrupt
   release, reservation cancellation, actor retention/reap, and signal cleanup.
   Keep the existing receipt schema, source hashes, dependency hashes, modes,
   public request fields, and first-error exit behavior.

After this source patch, add only focused regressions for these paths and run
them before adding the composed fixture:

- **Known-ID horizon:** configure the real daemon with a valid six-second
  prepare expiry (longer than the five-second grace). Prepare through the actor,
  let bootstrap commit its same-ID 3130-second extension, and withhold its reply
  past the recorded old expiry. The actor call becomes indeterminate quickly;
  keep the owner alive until `oldExpiry + epsilon`, assert the actor is still
  alive and has emitted no cancellation, then close owner control. Require one
  actual AF_UNIX exact-ID cancellation, canonical cancellation, and bounded actor
  exit. This is a roughly six-second proof, not the current immediate-EOF test
  and not a 45-second wait.
- **Terminal ordering:** make the real daemon worker fail, run the complete
  operator, and assert status error is observed before any error-terminal
  recheck can intercept it. Require newer PAUSED, empty-ID fresh recovery, new-ID
  actor ACK, recovered cleanup, original exception/receipt failure, and no old-ID
  recovery request. A variant fails after new-ID handoff and requires exact
  cancellation of that new ID.
- **Phase budgets:** for provider and finalize typing, set the applicable phase
  deadline one tick below the computed fixed sequence budget and assert no GO,
  recorder entry, or physical dispatch. Allow a press, expire the phase, and
  assert exact release and reap. Also assert every readiness/gate/press wait uses
  no deadline later than the selected phase.
- **Receipt/PAUSED/rollback:** fail an active receipt event before first input and
  assert zero dispatch plus cancellation and causal receipt error. Parameterize
  missing/malformed/running paused-operation and Guardian shapes. Add targeted
  allocation/start/READY failures for X11Screen, OwnedEmitter, Watchdog, and
  CancellationActor, asserting all acquired descriptors/specs close and no
  child survives; do not duplicate already-proved normal lifetime cases.

### 2. Add one reusable causal composition fixture in the test file

Build a private `ComposedOperatorFixture` in
`tests/test_native_calibration_operator.py`; it is test support inside the owned
file, not a new module.

- Reuse the private mode-0700 shell compositor, frozen compiled telemetry-region
  executable, `WowClient`/stock `PixelDecoder`, profile dimensions/crops, stable
  `WindowIdentity`, and authentic Codex `0.162.1` path from
  `tests/test_session_native.py:962-1197`. Write a real private config file whose
  producer path and SHA-256 match that executable. Keep the daemon's production
  image/capture observation path; do not install a raw-dict successful
  observation provider.
- Create a real `SessionDaemon` and `SessionIPC`, and serve bounded records over
  an actual mode-0600 AF_UNIX socket. `DaemonClient` and the independent actor
  use that socket unchanged. Every generation, reservation, expiry, history,
  reply, and terminal record must originate in daemon dispatch.
- Construct the real `X11Screen`; do not override
  `wait_reload_boundary`. Its external device boundary receives full-size,
  identity-bound PNGs from a synchronized scene producer. Absence frames,
  dual-control frames, role-exclusive construct/restore frames, construction
  telemetry, and fresh ordinary telemetry all retain the configured crop and
  dimensions. Identity-before/capture/identity-after and pointer queries use the
  same stable external-device state. This uses the production crop, strict
  absence classifier, stock decoder, ordinary boot/phase/ordinal/fence checks,
  template matcher, and freshness logic.
- Load a real `PinnedInputTool` from a sealed test artifact and use actual
  `Watchdog`, `FixedInput`, and spawned `OwnedEmitter`. Its recorder transport
  writes the complete argv, not merely the first two tokens, and waits for a
  test-device ACK. A bridge accepts only the existing fixed key/type/move/button
  argv. It updates pointer/chat/game state and ACKs only after the actual emitter
  has registered ownership and dispatched the record. For chat, recognize the
  exact Return/type/Return sequence; only after the submitting Return may it
  call the real Lua harness slash command or advance the reload scene. For a
  click, update the pointer only after `mousemove` and advance the external
  scene only after `mousedown`; `mouseup` remains independently observable.
- Inject OCR only as an external sensor: it reports the bridge's current chat
  edit-box value. It must not return the next expected command from a canned
  iterator. Advance capture pixels only from acknowledged bridge events or the
  real native worker's requested stage. Precomputed compiled frames are allowed
  only behind those barriers; they cannot be consumed early.
- Drive the native worker with the proven production callback/capture state
  machine from `tests/test_session_native_regressions.py:5460-5624`, adapted to
  frames published by the real Lua/compiled producer. Use a monotonic clock
  rooted at real `time.monotonic()` and advance only external capture time; keep
  all reply deadlines numerically comparable to the helper clock. Assert the
  exact 12-state history, rather than mutating daemon handshake state.
- Build the receipt with the real helper SHA-256 and `_source_bindings`; assert
  the config, templates, compiled producer, pinned input tool, helper, and native
  dependency hashes appear in the private receipt.

There is no source-interface blocker. The narrow test seam is limited to the
already external device factories: patch `PinnedInputTool.load` to return the
sealed artifact and construct `X11Backend` against the private compositor/stable
window discovery. Do not object-construct X11Screen, replace its readiness
method, replace DaemonClient, intercept actor replies, or substitute
FixedInput/OwnedEmitter. If those two external factory substitutions cannot be
made without replacing production methods, stop and report the exact constructor
call; do not introduce a fake test labeled production.

### 3. Decisive composed cases

Run these against the shared fixture:

1. `measure-deferred` **success**: actual prepare, absence reload readiness,
   dual-control proof, bootstrap and canonical long-expiry ACK before input,
   native-calibrate, all 12 ordered history states, phase-bounded fixed commands
   and construct click, finalize admission that remains `finalize_required`,
   actual finalize command, worker completion, real `finalized`, actor disarm,
   release/reap, and successful pinned receipt.
2. `measure-deferred` **error/recovery**: actual worker error through the complete
   operator, strict status/pause to a newer generation, empty-ID recovery, new
   canonical ID before reload/restore input, recovery terminalization, and the
   original measurement exception and failure receipt after successful cleanup.
   Parameterize a post-handoff readiness failure to prove new-ID cancellation.
3. `control-preflight`: real preflight reservation, owned defer and construct
   dispatch, actual preflight-ID recovery handoff, ordinary readiness, real
   recovery completion, and terminal actor cleanup.
4. `recover`, parameterized for `ordinary_reload` and `restore`: start from a
   real durable checkpoint with no live reservation; require an exactly empty
   request ID, daemon-created recovery ID, only reload for ordinary, Recover plus
   exactly one role-exclusive restore click for restore, genuinely newer
   ordinary boot, recovered terminal, and cleared checkpoint.
5. Production readiness refusal table: loading/damaged fragment, identity drift,
   construction-prefixed boot, active fence, wrong native phase/ordinal, stale or
   non-profile capture, and deadline exhaustion. Assert refusal occurs before
   the next recorder dispatch. Retain the existing independent pure-absence,
   new-boot, identity, control, owner-death, signal, and release proofs.

### 4. Verification and R8 integration

Run focused source regressions first, then the composed cases. Once those are
green, run the complete helper suite exactly once on the final two bytes, followed
by scoped Ruff check/format check, compile, diff check, import origins, exact
two-file hashes, descriptor/child fence, private-XDG permissions, and full log
SHA-256. Do not repeat broad rounds without a source change.

After R8 is independently accepted, create a clean final verification tree with
the exact helper pair and all seven exact R8 files. Re-run the composed cases and
one final helper suite there; record both dependency and helper hashes. Root then
arbitrates this plan with the parallel Opus review and owns promotion. Native100,
human takeover, live game input, service changes, and unattended cycles remain
later gates and are not claims of this offline closure.

## Final Opus arbitration (root, 23:32 UTC)

Actual review completed exit0, resolved claude-opus-5-5, STATUS: MAJOR ISSUES.
Read native-operator-production-proofs-opus-review.txt in full. Root independently
inspected the relevant helper/daemon paths and accepts these reachable findings:

- M1: completed measurement must require the real same-generation
  INPUT_CALIBRATION state after canonical finalized, not NATIVE_CALIBRATION.
  Do not relax state checks generally. Error remains a failure before finalized.
- M2 supersedes the conflicting Sol phase mapping above. providerDeadline is set
  ONLY for initial construct-frame acceptance and is not refreshed for subsequent
  held/updates/resume. Apply it only to the initial applicable release/construct
  actions and wait for hold_required; discard it after canonical hold_required.
  Later replies retain the old field, so never reinstall it for later stages.
  Hold/measure/resume and later waits use the real reservation/operation bounds;
  daemon keeps enforcing its own existing per-frame deadlines. Constructor click
  still uses its existing release+10/constructor bound. Finalize chat uses the
  canonical finalizeDeadline, which already includes the hook bound. Do not add
  new public deadlines or extend any timing allowance. Add a real-shaped phase
  test that runs beyond the old construct deadline and still completes.
- M3 extends the accepted terminal-error fix to failures at ANY wait/recheck,
  not only _await_calibration_terminal. Recognize only validated exact-ID,
  same-generation canonical terminal failure records (error/restoration_required/
  recovery_required as actually returned) without treating them as successful
  terminal/disarm permission. Wait within a bounded cleanup budget for actual
  native operation error/idle before pause. Fresh recovery must allow the genuine
  STRICT increase in guardianGeneration across the newer PAUSED generation;
  preserve all other sealed owner/profile/identity/B0/boot/lease invariants and
  explicit guardian disarmed. Same-generation handoffs retain exact immutability.
  Preserve old actor protection until the new canonical admission is ACKed;
  use a fresh bounded request deadline. Prove run() fails with original error
  while cleanup reaches recovered under the new exact ID.
- S1: private actor replies need correlation after incomplete/interrupted calls.
  Prefer poisoning the private channel after any incomplete call and relying on
  actor EOF cleanup, rather than adding public protocol fields or retries. Include
  SIGTERM/late-reply ordering and prove no stale reply is consumed as cancel ACK.
- S2: if GO was never attempted, a pre-press refusal clears watchdog ownership
  and aborts the emitter without sending keyup/mouseup. Once GO may have been
  written, exact release remains mandatory. A before_press callback runs after
  pointer reposition: that test may contain the admitted mousemove, but MUST have
  zero button press/release events. Whole-sequence budget refusal must have zero
  GO and zero recorder events of any kind. Do not claim the former proves zero
  pointer movement.
- S3: phase bounds must reach watchdog publication ACK and READY/GO/PRESSED waits;
  immediately before GO require the FULL remaining fixed action budget after
  emitter spawn, do not silently shorten it. This duplicates/clarifies Sol Must3.
- S4: preserve active receipt fail-close and first causal failure. Record named
  mandatory_cleanup_failed stages for input.close/release/abort failures; cleanup
  audit failures cannot interrupt other mandatory cleanup. Set cleanup protection
  BEFORE the terminal receipt event, so repeated signals cannot escape that edge.
- S5a-d duplicate required real composition/readiness/horizon/budget proof. S5e:
  main lifetime tests must use private state directories and the real actor path
  where the test claims actor lifetime. S5f: measure production-size templates
  against existing freshness/click windows, retain timings; tiny4x4 fixtures do
  not establish production latency. No matcher rewrite in this repair stage;
  report a measured blocking result for separate root arbitration if necessary.

Accept reachable cleanup nits: abort OwnedEmitter.start on invalid process-group
identity, require valid owner_start for Watchdog, and close non-protocol inherited
actor descriptors as the existing watchdog does. Cover their actual allocation
boundaries. Correct the inaccurate late-reply comment. Do not spend this round on
duplicate branches, duck-typing style refactors or 50ms poll optimization: no
demonstrated correctness defect there beyond the accepted deadline/identity gates.

Root has created native-operator-final-closure-20261018 from a74297c with exact
frozen helper pair and six R7 read-only dependencies. Continue source fixes and
focused proof, then causal composition. This is final arbitration; no review hold
remains. R8 exact-byte integration still awaits separate native acceptance.
