# Native capability transaction R9

Root independently inspected and accepts the concrete Must in
executor-review/native-final-commit-r8-sol-review.md. R8 source and proof trees
stay frozen. R8 actual Opus review remains active; final arbitration will arrive
before final freeze/broad checks. Do not wait to implement this accepted race fix.

Root-created worktree native-capability-transaction-r9-20261018, base2d63777,
contains all seven exact R8 proof-closure files. Final-arbitration writable fence:
src/crowley/session/daemon.py, controller.py (ONLY native_calibrated rollback),
tests/test_session_native_regressions.py, and test_session_native.py (ONLY the
compiled-default capture fixture's STOPPED correction). Other three copied files
are read-only. Keep every R8/R7 regression and all six
new R8 proof cases. No helper/driver/Guardian/inputtool/journal/addon/config/
protocol/service/GUI edits, new public schema/mode/deadline or unrelated refactor.
No git/reset/stash/revert/commit or live input. Parent owns git and promotion.

Required source change:

- In native producer admit_observer, existing controller lock stays outermost.
  Hold construction lock from the exact capability comparison THROUGH
  guardian.observer_dispatch_admission(start). Owner revocation/expiry under only
  construction lock cannot linearize between check and process release. Preserve
  controller -> construction -> Guardian order; independent Guardian revoke still
  changes driver capture epoch and prevents escaped gated process admission.
- Compare exact immutable epoch, generation, kind and reservationId. None equals
  only None; it is never a wildcard for a later owner. Audit all matcher call sites
  for the documented construction-lock requirement. Replace the incorrect
  lock-free atomic-assignment justification with the actual transaction contract.

Focused proof BEFORE broad checks:

1. Use a real publicly created provisional/recovery/deferred owner and a configured
   PNG producer path. Pause admission immediately after capability validation.
   A same-ID replayed bootstrap or failed public recheck/finalize validation must
   attempt the real construction-owner revocation. Show owner clear/epoch change
   cannot complete before the admitted process starts, OR revocation wins first
   and zero process dispatch follows. Observe the actual owner-clear boundary,
   not merely the revocation method return (which later waits for controller).
   Prove both linearization orders and bounded thread/process cleanup. Do not
   replace Guardian admission or use a fake Owner raising its own expected error.
2. Exact capability negatives: same-generation wrong kind, None-ID versus an
   installed real ID, stale epoch and replaced owner cannot borrow admission;
   legitimate same-owner inflight None-ID still works. Use real created owner
   data; no made-up successful reservations. Assert zero producer process release
   after a named refusal, not just a generic exception.
3. Retain exact-cancel-before-dispatch, both finalization/cancel interleavings,
   configured PAUSED capture, strict absent/no-producer behavior, and the six
   R8 proof cases. Run focused new cases first and send literal outcomes; continue
   independent source/proof work while final Opus arbitration is pending.

After root final arbitration, run final native three suites plus the one named
runtime meter test ONCE on final bytes, scoped Ruff/format/compile/diff checks.
Use main .venv Python, explicit worktree PYTHONPATH, private0700XDG and authentic
CLI0.162.1 configured explicitly. Preserve complete private0600 logs, exact
commands/return codes/import origins/base/seven final and three-readonly hashes.
Map every assigned requirement to actual regression/result before reporting DONE.
Do not substitute a broad passing total for a missing race case.

MAIN report writes only executor-review/native-capability-transaction-r9-
{closure.md,freeze.json}. Parent independently verifies and obtains final review;
no source acceptance/native100/service restart/live qualification claim here.

## Accepted R8 proof-review corrections (root, 00:03 UTC)

Read native-r8-proof-closure-sol-review.md. Root accepts its Must and Should.
The three deadline cases in test file6447c6 currently stop the third outer
revalidation, but a fourth outer revalidation refuses before the transaction;
the six-case passing totals therefore do NOT establish transaction deadline proof.
In this same authorized R9 regression file, replace callback-count gating with a
thin observer/wrapper on ACTUAL _native_construction_finalize_transaction entry.
Signal entry, wait while main holds controller lock and expires only named bound,
delegate to original transaction, and assert entry once plus exact after-lock
refusal/zero rebind/observe/native_calibrated. No production change is required
for this test correction. In the three-way barrier explicitly assert the joined
calibration worker is no longer alive; keep finally cleanup. The two malformed
resume cases passed focused review. Run corrected focused cases with R9 proofs
before any final broad suite. Earlier R8 source/proof trees remain preserved.

## Final actual Opus arbitration (root, 00:12 UTC)

R8 actual Opus completed exit0, resolved claude-opus-5-5, NEEDS WORK. Read full
native-final-commit-r8-opus-review.txt. Root inspected the relevant methods and
accepts these concrete corrections in this same R9 scope:

- Must1: finalization lost the last full reservation binding validation. After
  selecting the final candidate, outside the locks call the existing
  _native_construction_validate_snapshot on an exact reservation snapshot. Require
  candidate identityFingerprint == captureIdentity == reservation identity.
  Inside the controller-first transaction recheck exact candidate/reservation
  identity and pure Guardian generation/disarmed predicates alongside existing
  owner/deadline predicates. Keep external identity acquisition OUTSIDE locks.
  Do not restore the old finalization race or drop final terminal serialization.
  Add actual final-capture-to-commit identity drift and Guardian-generation drift
  barriers, zero rebind/observe/native_calibrated. Preserve lease/profile/owner
  PID/start/B0 binding checks through the existing snapshot validator.
- Should1: narrow controller.py exception ONLY native_calibrated. Snapshot and
  restore its in-memory native flag/evidence/history/invalidated reason/state and
  write-affected history if _archive or _save fails. Do not delete a committed
  audit archive or rewrite general Journal behavior. Inject actual journal.write
  at each finalize durable boundary; retain the same owner through its normal
  error handler, require native=false/no INPUT state/no false finalized, then a
  fresh driver/owner sees required recovery. No live calibration evidence may be
  resurrected by the later recovery checkpoint save. Test transient failure where
  that later save succeeds; failing every write would mask the defect.
- Should2: commit cancel-wins proof must stop at actual transaction entry AFTER
  last outer revalidation, cancel exact public owner first, then enter original
  transaction and require its exact owner-revoked guard, zero mutations, immutable
  cancelled on later public recheck. Finalization-wins barrier must observe the
  cancel thread actually attempting/blocking on the real controller mutex;
  replace the scheduling sleep with deterministic events, retain real lock/gates.
- Nit2: restore explicit BLOCKED/STOPPED producer admission refusal. Narrow
  test_session_native.py exception only the compiled-default capture fixture:
  enter a legitimate calibration state through actual public controller lifecycle
  instead of loosening production STOPPED to satisfy a fresh test fixture. Preserve
  actual SessionDaemon.default/configured compiled producer/stock decoder proof;
  do not replace it with a fake daemon or guessed state assignment.
- Nit3: validate actual resume sequence/capture types before comparisons can
  mask them with TypeError/earlier freshness errors. Keep legacy versus deferred
  contracts explicit; extend negatives to missing/None sequence as appropriate.
- Nit4: async worker result/error/finally writes must target the ORIGINAL operation
  object. A next gate can replace _calibration_operation after _finish_calibration
  releases its operation lock. Capture the original record and, under state lock,
  write only if it is still current; old worker must never mark the new operation
  error. Preserve status_dict acquisition outside state lock. Add a real bounded
  worker-completion/next-operation barrier, not manually fabricated terminal replies.
- Nit5: close the small named remaining regressions within this existing test
  file: real recovery restart overlapping a live reservation; deferred callback
  ordering beyond hold; PAUSED no-producer recovery begin. The accepted R9 public
  execution-gate barrier must actually traverse the NATIVE configured producer
  path too; raw injected capture methods cannot prove that branch.

Nit1 legacy stock-capture path is explicitly deferred: no generic fallback API or
driver rewrite. The strong no-revoked-producer-dispatch claim applies to the
configured producer used for qualification. Legacy read-only stock capture may
finish and be discarded at the next owner recheck; record that limit, not universal
process fencing. No additional classifier rewrite, public schema/mode/timeout,
Guardian/driver/journal module change, or broad pause/restart refactor.

This is FINAL arbitration; no Opus hold remains. Finish these bounded corrections
and actual focused proofs, map each to real test/result, then final native three
suites plus named runtime ONCE on final bytes and scoped checks. Root independently
verifies and obtains focused Sol + actual Opus review of the final R8-to-R9 delta.

## Test-only proof completion after the full suite (root, 00:46 UTC)

The actual finalize/error-handler transient-write proof remains required; a direct
controller.native_calibrated test cannot replace it. If the current full-suite
run passes and this last proof is added without changing production source or
any existing test/helper AST, do not repeat the whole suite merely to count the
new test. Preserve the full run's exact seven hashes, add the regression in the
owned file, run its real cases and scoped checks, then freeze final hashes and
map the incremental evidence explicitly. Parent checks unchanged production
hashes and existing ASTs; do not claim a combined single invocation. A production
change, changed existing test/helper, failure, or genuine new concern requires
the relevant tests again. This narrow incremental option supersedes the earlier
final-file-byte wording only for a strictly additive proof.
