# Independent bounded mail recovery tests

Luna owns only NEW tests/test_session_mail_loop_recovery.py and evidence under
.archive/mail-loop-recovery-20261024/. No production or existing-test edits.
Read main PLAN-mail-loop-20261023.md and shared contracts. Runtime producer owns
controller/journal/daemon and their tests; whole-cycle tester owns its separate
composition file. This is an independent failure oracle, not native qualification.

Use the real Controller/Journal methods and fresh actual Snapshot/policy values.
Keep fixture setup small and explicit: a prior verified WAIT_DUE/ACK boundary is
a precondition, not a claim to replay three earlier collection cycles. Use
controlled fake input control only to prove no new route/command/press; do not
claim full DesktopDriver/Guardian composition from these unit cases.

Required groups:

1. Admission write failure before replacement and delegate-real-write-then-raise.
   Prove no live capability/GUI effect or ordinary scan fallthrough in the same
   owner, including another observation/admission attempt. Fresh owner must not
   reconstruct input authority from a possibly written cycle marker.
2. Full complete and blocked logical outcomes: inject failure at the ACTUAL
   pending marker, immutable manifest, archive artifact and final checkpoint
   boundaries AFTER a complete immutable staged outcome exists durably. Assert
   the intended boundary was reached. Keep the failing owner alive through its
   normal catch; recreate a fresh Journal/Controller/driver and recover without
   passing dead-owner finalization arguments. Exact payload/outcomeId, one
   archive, no input replay; preserve later actual pause/stop holds.
3. Stage-write failure itself leaves uncertainty and cannot fabricate completion.
   Distinguish it from pending-marker failure after durable staging.
4. Block ACK A, later cycle B, then A remains refused across fresh owners. Preserve
   the archive while establishing subsequent explicit verified-repeat fixture
   preconditions; do not wipe history or seed the expected terminal outcome.

Use legal phase transitions and real producer proof methods to establish AH-open
completion prerequisites; do not manually manufacture a staged result. Staged
expected evidence may be read from the actual durable file before replay, never
handed into the fresh constructor as permission. Check immutable record identity
and original admitted epochs independently from later operator/current epochs.

No giant process fixtures or global time monkeypatch. If APIs are mid-correction,
read the producer's latest code/plan and record exact failing behavior instead
of weakening the test. A complete source-frozen test can report honest SUT
failures; overall acceptance requires green production and independent Sol review.

All pytest uses pinned CARGO and flock /home/dev/.cache/r-pg.lock. Run only the
new file, scoped Ruff/format/compile/diff check. No game/services/DB/deploy/commits/
secrets or existing evidence removal. Full default remains under180s.
