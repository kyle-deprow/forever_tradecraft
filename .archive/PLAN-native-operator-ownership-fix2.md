# Ownership fix2: accepted closed-actor design and combined review closure

Root APPROVES the complete Sol proposal in PLAN-native-operator-ownership-fix2-proposal.md.
Read it and both full R4fix1 source reviews (Sol + actualOpus) before editing.
Root accepts Sol5Must/2Should and Opus5Must/3Should as concrete reachable issues;
merge duplicates. Fix the complete bounded ownership stage, not unrelated workflow.
R4fix1 remains frozen; parent38passes are real but required cases are absent.

Root creates native-operator-ownership-fix2-20261018 from2fcdedd, exacttwoR4fix1
helperfiles + exactsixR5developmentdeps. ONLY tools/native_calibration_operator.py
and tests/test_native_calibration_operator.py may change. All other source/native/
Guardian/driver/inputtool/addon/config/services/GUI/gitmutations forbidden. Root
owns commits. No real desktop/game input; harmless isolated fixtures only. No
new public mode/requestkeyset/schema/Guardian/lease/releasefallback. NativeR5 is
knownunaccepted; finalnativeintegration/livegates remainlater.

## Required implementation

- One closed independent ownership actor performs fixed existing admissions/
  bootstrap/recoveryhandoff/terminal operations. It stores canonical binding and
  expiry BEFORE ACK to helper, including bootstrap's3130s expiry. Fixed pause
  for terminal-error recovery may be proxied as the already-approved literal
  existing command; no arbitrary router. Finalize-admit is NOT terminal; only
  actual exact finalized/cancelled/recovered (or coordinated native closed-failure
  evidence) disarms. Independent actor performs no physical input. Unknown-ID
  lostreply is honestly indeterminate, no guessedcancel or retry; preserve known
  capability and serverboundedexpiry, prohibit dependent input. See Solproposal.
- Protected cleanup starts BEFORE failure recovery/cancel. Keep actor armed
  until exact canonical terminal ACK; failed sync cancel/recovery must leave
  independent EOF cancellation active. First causal error survives secondary
  cleanup errors/repeated signals. Unconfirmed mandatory cleanup makes receipt
  and exit failure, and records retained actor/secondary release failure.
- Watchdog and ownership actor entry wrappers call setsid before READY and
  dispatch existing _watchdog_entry/_cancellation body. They must survive whole
  HELPER process-group TERM/HUP/INT. Detach standard fds so a retained child cannot
  keep captured caller stdout/stderr pipes open indefinitely. A child exit !=0
  is NOT physical release confirmation. Keep unresolved live release actor alive.
- Owned typing must WORK with authentic pinned xdotool timing. Existing2s inner
  subprocess/PRESSED bounds are shorter than fixed /crowley commands. Derive
  action/ACK bounds from fixed text length and actual vendored timing plus margin,
  capped by applicable remaining phase deadline. Publish exact fixed-text keysyms
  potentially held before gate (or genuine owned per-character dispatch); empty
  type keyset is forbidden. No unowned modifier clearing. On every failure,
  emitter.abort/reap/fdclose runs in finally even if release_now raises; retain
  first error and unconfirmed cleanup audit. Verify actual typing on an isolated
  Xvfb with real pinned tool or equally faithful bounded transport fixture; never
  the user's display. Instant recorder alone cannot prove real type deadlines.
- Staged idempotent rollback for X11Screen/OwnedEmitter/Watchdog/ownershipactor:
  every allocated pipe end/spec/transferredfd and started child is tracked before
  next fallible step, closed/reaped on failure. Require positivePID/nonemptysealed
  process-start identity before actor spawn. No silent _children API failure or
  missing socket bypass in production; explicit injected test doubles may only
  supplement proof. No unrelated dead-code or portability refactor.

## Required actual proof, then freeze

Run real production-lifetime key AND button owner hold cases, helperPID death and
wholehelperPG TERM/HUP/INT plus repeated signal DURING cancellation/cleanup; show
exactrelease/reap/cancel/receiptfirsterror. Test actor owned admissions with death
before/during/after prepare/bootstrapnewexpiry/recoverygen-ID ACK and cancellation
transport failures/failed recovered ticket. Test real NORMAL main nonzero return /
SystemExit / atexit while release remains unavailable (NOT owner.kill), actor
survives, caller communicate returns within bound, later exact release completes.
Test each staged allocation/start/readiness failure with actualdescriptor/spec
closure assertions. Test type duration/deadline and killmidtyping exactkeyup.

Keep complete private logs/importorigins/source/dephashes. Focused groups first;
send concise literal actual results, then fullhelperfile ONCE finalsource + scoped
Ruff/format/compile/diff. No unrelated native/performance suite. MAIN report only
executor-review/native-operator-ownership-fix2.md with literal covered/uncovered
cases. DONE only when this stage actuallycomplete. Parent independentlytests,
then Sol+actualOpus rereview. No nativeintegration/live acceptance claim.

Known later integration check: after terminal MEASURE error and confirmednewPAUSED
(no live reservation), native recovery_begin expects EMPTY reservationId for a
fresh recovery; old measureID is not a preflight handoff. Preserve current public
native semantics, verify actual SessionIPC composition later, do not make stale
measureIDs admissible just to match helper fakes.
