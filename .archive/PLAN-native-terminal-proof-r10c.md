# R10c: two remaining test proofs only

Sol finalR10b review finds no production defect and accepts four actualproducer
races. Two already-arbitrated test proof obligations remain. Source is frozen
and no production rewrite/full-suite rerun is assigned. Actual Opus review of
frozen R10b remains running; preserve that candidate and its reports unchanged.

Fresh WT /home/dev/.cache/crowley/worktrees/native-terminal-proof-r10c-20261019,
base c5e5772; seven exact R10b files copied. Own ONLY
tests/test_session_native_regressions.py, ONLY two named tests and tiny forwarding
helper if needed. Six files readonly including final four-case native test.
No production/helper/driver/Guardian/config/service/GUI/git/reset/stash/revert.

1. test_native_construction_composes_real_png_runner_and_finalize: existing
finalize-wins barrier currently sets cancel_attempted before public dispatch and
not cancel_done.wait(0.2), which only proves it may block in flush_expiry on
construction. Gate cancel immediately AFTER its REAL flush_expiry completes;
then permit final transaction to acquire controller+construction locks, observe
a nonblocking acquire of REAL daemon.controller.lock fails from the cancel
thread before its blocking acquire. A thin forwarding lock facade preserving
real lock and public method behavior is allowed. No fake mutex, no sleeps as
proof. Release final transaction and finish normal public cancellation. For
BOTH terminal orders, later public native_construction_recheck must preserve
exact final finalized/cancelled terminal and all existing mutation assertions.
2. test_native_recovery_restart_refuses_live_reservation: count actual
observation-provider calls. Public preflight uses exactly one; public recovery
restart must raise exact live reservation error while count remains unchanged,
owner unchanged, no inflight owner. Keep real public paths.

Run affected composed normal-finalize and cancel-wins cases plus recovery-restart
case (three cases) on final bytes, then scoped Ruff/compile/diff/AST and six readonly
hashes. No broad suite repeat, no other test behavior changes. Retain complete
0600 logs, exact commands/results/hash/fence/cleanup. Main reports ONLY
executor-review/native-terminal-proof-r10c-{closure.md,freeze.json}.

Continue these two accepted corrections while Opus finishes; do not final-freeze
until root sends FINAL arbitration of Opus findings. Send milestone via message
when focused proofs pass; keep production/other six bytes unchanged.

## FINAL Opus arbitration (root)

Actual R10b Opus completed exit0/claude-opus-5-5/NEEDS WORK. Both reviewers
find no production defect and accept actual four-case Guardian proof. Final
arbitration has arrived; no hold remains. Finish the two Shoulds above plus:

- Accept Nit1 and2: in test_session_native.py ONLY the new four-case
  test_compiled_private_owner_guardian_generation_revoke_orders, directly
  assert current reservation==owner_before and current construction epoch==
  construction_epoch_before AFTER actual Guardian generation advances, while
  callback remains blocked. Remove final vacuous nonnegative captured_epochs
  assertion after exact epoch checks. This is the sole native-test exception.
- Accept Nit3 as documentation only: in supplementary /bin/sleep regression
  correct docstring/comment to say revoke-first exercises OUTER capability
  refusal, not the Guardian-generation fence; exact compiled cases prove that.
  No need add a new surrogate race or test a comment edit.
- Accept Nit6: in existing public recovery-begin inflight capability proof
  add exact original guardianGeneration==second_driver.guardian.generation.
  Include that affected case in focused verification.
- Accept Nit7 in NEW closure: document existing R9 same-kind starting-record
  adoption as public input-start fix, and intended early fail-closed malformed
  resume facts on legacy path. No extra production edit.
- Defer Nits4/5: source comment placement and unused optional private parameters
  are nonblocking cleanup. Current source is correct and frozen; do not move
  validation or alter parameter signatures for this proof-only task.

Writable fence now TWO TEST FILES ONLY, limited to the exact functions above;
five production/companion files remain read-only. Source hashes unchanged.
Run three original assigned regression cases, the one affected recovery-inflight
case, and four compiled cases (eight total), scoped statics/AST/five readonly/
private0600logs/cleanup. No full-suite or unaffected25-core repeat. Finalize
R10c closure/freeze after green proof; parent independently verifies exact delta
and obtains focused Sol/actual Opus review of test-only fixes. No extra scope.

## Minimal R10d closure of omitted branch assertion

Final Sol accepts real mutex and other test corrections, but cancelled branch
STILL only checks initial response; closure overstates the later recheck. Fresh
WT native-terminal-final-r10d-20261019/base c5e5772 copies exact seven R10c files.
ONLY regressions.py writable: after capture_index==105 in cancel-wins branch
of composed_real_png_runner_and_finalize call public native_construction_recheck
with expected_generation7 and exact reservation ID, then assert handshake.state
and reservation.reservationState BOTH cancelled. Preserve all prior checks.
Also revise supplementary sleep test docstring to say outer-capability refusal
and child cleanup; four compiled cases establish generation fence. No production
or other test change; six files readonly. Run only two composed normal/cancel
cases (comment edit needs no surrogate rerun), scoped statics/AST/six hashes/
private logs/cleanup. Main reports only native-terminal-final-r10d-{closure.md,
freeze.json}. Parent must inspect the actual cancelled branch before review;
green totals alone do not show this assertion exists.
