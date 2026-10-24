# Mail-loop control and admission negative proofs

Independent unit-test slice to finish the existing Runtime Round4 acceptance
requirements while the runtime producer diagnoses the composed AH boundary.
Luna owns only new tests/test_session_mail_loop_controls.py and
.archive/mail-loop-controls-20261024/. Existing production and tests are read-only.
Read CLAUDE.md, docs/HANDOFF.md, PLAN-mail-loop-20261023.md in full and the shared
terminal/driver contracts. Import existing explicitly synthetic fixtures where
useful; do not claim native or physical coverage from unit doubles.

Acceptance: focused fast unit tests must distinguish:
- Actual daemon _advance stops on admission checkpoint errors before and after
  replacement, including throwing revoke: no fallthrough scan/reload/input.
- Public start rejects stale generation and active owner before capture; stop
  during capture and replacement start during capture invalidate prior commit;
  status reflects a coherent binding/cycle snapshot; completion cannot erase a
  newer binding. Use deterministic barriers/hooks, no timing sleeps.
- Ordinary Controller.resume refuses unresolved/staged/restart mail ownership
  before generation mutation or arm; original journals/unknown input survive.
- Public malformed surrogate queue identity and executor house/character mismatch
  return controlled errors with unchanged binding and no input.
- Per-message asynchronous postcondition wait expires from the first physical
  attempt rather than resetting each poll; all remaining work is still reserved.
- Failed/refused direct and async owned executor outcomes archive exact audit but
  block cycle before any return route or AH action. No forged return proof.

Use actual Controller, Journal, SessionDaemon/SessionIPC methods for the boundary
under test, not a replacement implementation of the method. Narrow model/driver
unit doubles are fine; retain real policy admission/protocol-valid evidence.
Do not modify production to satisfy the test or mutate private state to bypass
terminal proof. Keep tests small/fast and avoid duplicate broad native cases.

Run Ruff check/format and compile. All pytest acquires
flock /home/dev/.cache/r-pg.lock with pinned CARGO. Runtime source is active: report
actual failures separately, freeze test hash at DONE, then read-only Sol review
and parent reproduce after production freeze. No game/services/DB/commits/deletion.
