# Close the final helper proof gaps

Production helper corrections are coherent; parent full73 passed. Sol found
specific claims not reached by the assertions. This is a test correction round,
not another native/Guardian redesign. Read release-corrections plan and reports.

Scope: tests/test_native_calibration_operator.py ONLY in existing final-integration
worktree `native-helper-proof-closure-20261019` at main59046b1. Production helper6f8f87ef and seven native dependencies remain immutable.
No GUI/config/services/addon/deployment/git/main edits. Parent owns promotion.
Parent created a fresh isolated worktree so the older final-integration candidate
can stay immutable for its ongoing Opus review. Edits in this NEW worktree are
authorized now; never edit the older final-integration tree.

1. Actual successful100 fixture must pause through existing DaemonClient.pause
   and AF_UNIX SessionIPC, not direct controller.pause. Validate immediate PAUSED,
   newer generation and higher lease; use returned generation for fresh recovery.
2. Actual budget-negative must reach emitted READY, real watchdog ownership ACK,
   then exhaust deadline before GO on FIRST key action. Do not patch type_command
   after opening Return or fail before emitter startup. Use an owned scheduling
   seam to consume budget, not fake emitter/watchdog. Assert actual sealed action
   log empty, emitter reaped, descriptors/ownership empty, failure receipt terminal.
   Readiness refusal must independently assert zero recorded actions.
3. Narrow allocation/deadline regressions: min deadline cannot extend; actual
   spawned emitter with invalid process-group result is reaped/FDs closed; missing
   owner-start refuses before Watchdog child allocation; cancellation-child closes
   inherited nonprotocol FD while its actual protocol still operates. Exercise
   corrected source branch, not a neighboring generic exception.
4. Compare receipt pins against independently read known profile/template/producer/
   sealed input bytes and all eight imported native module sources. A digest-shaped
   string is not provenance proof. Keep actual helper hash assertion and current
   same sealed input artifact for screen/FixedInput. No facts copied only from
   receipt to expected object.
5. Focus new cases first; then full helper once stable. Retain private0700 evidence
   and complete0600 logs opened before commands, exact source pre/post hashes,
   actual commands/exit/count, import origins, cleanup. Parent reproduces focused
   changed branches plus public-success/recovery, not unchanged entire suite again.
   Sol/actual Opus review only correction delta after parent green.

No DONE until actual corrected coverage passes. If a purported source bug is
found, stop that edit and report concrete cause; do not widen scope unilaterally.

## Actual Opus review arbitration (final prior candidate)

Actual claude-opus-5-5 completed0, prior two source hashes unchanged, verdict
NEEDS WORK. Parent accepts the concrete following findings after source inspection.
Read private native-helper-release-opus-20261019/review.txt in full.

Scope widened ONLY to tools/native_calibration_operator.py in the NEW proof-closure
worktree for the single _record_operation_deadline correction: phase-specific
constructor/provider/finalize_hook/finalize deadlines must use min(existing,new),
just like operationDeadline. A recheck must not widen the release+10s constructor
bound to provider+23s. Add direct minimum tests for every key and one constructor
recheck/click refusal path proving the original bound stays effective. No other
production refactor/native/GUI scope expansion. Helper source pin will change.

The fixture must also be genuinely causal in ALL modes:
- recover-restore must serve the real fenced restore frame to FIRST recovery_begin
  capture and assert the returned recoveryKind; ordinary case must assert its own.
  Fixed payload0/1/2 overrides cannot conceal the current client state.
- control-preflight dispatches actual Construct or Restore according to the real
  emitted pointer position. Run the actual Lua click handler for that role and
  change scenes only after its accepted reload/publication. agent defer must
  not swap in a new post-reload VM until the helper really submits /reload.
- post-success recovery starts from the ACTUAL finalized native-construction:B0
  client/checkpoint, not an uncaused swap to an ordinary VM. Public pause, fresh
  actual recovery_begin must choose restore, dispatch actual agent recover and
  Restore on that finalized client, and observe the resulting committed fresh boot.
- Every recovery reload uses the SavedVariables actually written by the dispatched
  Restore/Finalize. No pre-defer SavedVariables substitution. The final addon79
  restore_pending/world-entry/strict two-publication path must really execute.
- Validate each served initial/capture image against actual current Lua state,
  including first three captures; synthetic sequence numbers must not dictate
  scene transitions before real input. Retain accepted-action/reload history and
  assert Lua accepted each expected handler; a dispatched but refused action is
  not a successful causal proof. Use fresh_screen for fresh-operator bindings.

Retain prior tests/evidence truthfully: old73 passed but did not establish these
boundaries. Do not rewrite old logs or label them final. Final suite/reference
must start from the corrected source and exact actual SavedVariables transitions.

## Parent causal inspection follow-up

The 6abb test snapshot still prearmed the actual `ordinary` VM during fixture
setup in every mode except ordinary recovery. Its later dispatched agent defer
therefore refused `native_construction_already_set`, hidden by ignoring that
handler result. Eight workflow tests passed but did not establish this transition.
Always use a separate construction seed for static/future deferred images and
leave the actual ordinary client unarmed until the emitted helper command. At
that dispatch assert no marker before, armed marker with actual boot token after,
construction fence true and no reload yet. Preserve the same VM until the actual
reload action. Recover-restore still starts the separate actual fenced client.
Run affected success/preflight cases first. Rebase provisional Rust integration
test baseline without discarding its independent matcher-provenance assertions.
No production, native, deadline or GUI scope expansion.
