# Close operator/helper composition gaps

Root found concrete production-path omissions in the first two-file offline
helper. Its eleven tests pass independently (2.74s) but do not establish a working
helper. The first candidate stays frozen and UNQUALIFIED. This amendment resolves
two contract gaps and specifies the focused correction before external review.

## Shared native/private handshake amendment

A polling helper cannot observe every transient daemon state: reset archive,
baseline bind and verified deletion/release may all occur between two IPC polls.
The exact twelve-state table still applies to daemon events. Add a bounded private
stateHistory to construction replies/terminal records: at most16 entries, each
exactly {state, nativeClock}. The active reservation/run supplies ID/generation
binding. Preserve the exact ordered twelve-state chain for a successful run;
clocks are finite/nondecreasing and use _native_clock. Every actual state
publication appends once; repeated polls never append. Terminal failure/cancel
may end the chain. Recovery handoff begins its own two-state chain. No public
status/frame/evidence schema, canonical fourteen-field reservation or IPC request
shape changes. Legacy behavior stays unchanged. Keep history with immutable
run context through cleanup and in bounded terminal replies.

The helper validates this complete bound prefix (including its immutable prior
prefix), then accepts the newest actionable state even if polling missed
intermediate states. Missing/skipped/regressed/conflicting history refuses before
input. It must not demand RPC scheduling between consecutive daemon callbacks.
Native worker owns this daemon/test change inside the existing R4 six-file fence.
Helper worker owns validation/tests in its two-file fence; neither edits the other.

## Closed existing control operations

Eight construction commands remain unchanged. The helper additionally needs only
these existing fixed requests, already part of the reviewed lifecycle:

- native_calibrate: exactly command+generation, once immediately after consumed
  bootstrap, within its existing10s entry window;
- calibration_status and status: exactly command, read only;
- pause: exactly command+generation+reason, reason is the literal
  'native construction recovery', only after a terminal native error while still
  NATIVE_CALIBRATION. Verify newer PAUSED/unarmed/idle/no-worker facts before any
  recovery chat. Never add start/resume/input calibration or generic requests.

This resolves a plan omission: bootstrap consumes admission but does not start
the existing calibration worker. Do not change daemon bootstrap to start it or
invent new IPC. Helper uses the existing native_calibrate path and exact response.

## Concrete helper correction (new R2 preparation tree)

Own only tools/native_calibration_operator.py and its same-named test file in
native-calibration-operator-preparation-r2-20261018. Root copied exact first
candidate bytes and frozen R3 dependencies, all dependencies remain read only.
Keep all original helper/parallel preparation constraints and no live input.

1. _chat currently demands post_state BEFORE Return dispatch (Hold/Measure/
   Resume/Finalize), so real clients fail before causing the action. Verify the
   current pre-action state, exact fresh cropped chat/OCR/readback and guards,
   then Return, then separately wait for the causally newer expected state.
   A test client may advance only after the injected actual dispatch boundary;
   the current FakeClient iterator advances too early and conceals the bug.
2. Invoke existing native_calibrate immediately after consumed bootstrap. Observe
   actual private stateHistory, phase deadlines and terminal operation. Polling
   must use published finite bounds, not an arbitrary200*50ms ten-second ceiling
   across101 measurements. Aggregate unchanged polls in receipts; do not exhaust
   the256-event bound with one event per poll. Keep exact input ledger unchanged.
3. Recovery must accept ONLY the actual recovered terminal record, not the fake
   recovery_required reply used by the passing test. Validate finalized/recovered/
   cancelled non-admitting terminal states and their actual reservation shape.
   Do not report success on chat dispatch alone. Preserve fixed pause-on-error,
   ticket cancellation/cleanup, first failure, no auto retry/resume.
4. OCR currently runs psm7 on the entire1920x1080 capture, and template matching
   scans every fourth pixel with Python/Pillow over the entire image. Use the
   reviewed chat box and measured panel/template geometry/source pattern, keep
   pixel transforms explicit, and establish bounded exact-resolution matching
   with no missed non-four-aligned target. Check true overlap/ambiguity. Source
   artifacts may be fixtures until live qualification; a synthetic64x64 pass is
   not evidence of live-size effectiveness. No new runtime dependency or relaxed
   match threshold, arbitrary coordinates/commands/template roles.
   Negative-role proof applies at the candidate button's location, not globally
   across the image: Commands.updatePanel deliberately shows both buttons while
   armed/deferred. Require the positive role and reject the rival role at that
   same target crop; a separate legitimate rival button elsewhere is permitted.
   Post-reload dual positives must occupy distinct non-overlapping target boxes.
   Cover both-visible actual panel layouts, not only one-button fake scenes.
5. Pointer/focus/identity/binding/freshness must be rechecked AFTER reposition,
   BEFORE press, with no stale match allowed. Current pointer check occurs only
   after click. Retain separate capture/receipt times and the unchanged7s reserve
   and addon10s window. Helper deadlines also constrain every subprocess and ACK
   wait; no blocking os.read without a finite owner/deadline/EOF check.
6. Remove the special _test_run production-path bypass. Tests must traverse the
   same owned emitter and actual acknowledged _watchdog_entry with sealed fixture
   artifacts. Add real subprocess helper death during hold, SIGTERM/HUP/INT,
   SIGKILL/EOF, ACK loss, late emitter, exact release/reaping/registry cleanup and
   signal/setup/receipt-write failure. Owner-death gates must close after spawn:
   multiprocessing.DupFd resource-sharer descriptors can keep a writer alive;
   exercise EOF at every gate, not only normal press/release. Never kill the
   watchdog before confirmed exact physical release/reaping. Keyboard dispatch
   needs equivalent exact owned-key/emitter cleanup. No unowned key release.
7. Verify production main setup/teardown using fake external captures/transport,
   not fake orchestration/Guardian. Ensure profile-bound display/authority reach
   input and release children, and all setup failures close screen/tool/watchdog.
   Include actual source/producer/template bindings and precise input ledger in
   private receipts. Keep independent test-only actions out of runtime branches.

Complete independent negatives now. Do not fabricate R3 backend success; actual
accepted native integration remains a later gate. Run exact helper test command,
scoped statics/hash/fence and retain complete private logs/import paths. Send a
short milestone before tests, then write a new R2 preparation report in MAIN
.archive/executor-review/native-calibration-operator-preparation-r2.md. No git or
promotion. Report unresolved integration boundaries honestly; no DONE until full
accepted-native composition/parent/Sol/actual Opus acceptance is complete.
