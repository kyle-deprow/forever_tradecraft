# Sol mail-loop recovery test final review — READY

Scope reviewed: the complete frozen `tests/test_session_mail_loop_recovery.py`,
current recovery progress and the prior Round4 Sol review. Production source was
not reviewed, and no pytest was run.

Frozen SHA-256 before and after review:

`b57f6253612a451be4d5ff620940db85f686b8a168ad235627ae32c03c2cfea0`

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

## Narrow correction verification

- Both normal admission-failure expectations and the throwing-revoke expectation
  now require the exact original cause `admission checkpoint write failed`.
  They no longer depend on the stale prefixed reason.
- Exact ordered revoke effects and effective lease-generation assertions remain
  intact, including unchanged lease generation when revoke itself raises.
- The Round4 READY proof is otherwise preserved: exact logical payload plus the
  strict three-field Journal envelope, all four publication boundaries, fresh
  owner replay, later stop-state preservation, independent original epochs,
  causal begin/finalize/terminal acceptance, forged-ID/phase negatives,
  stage-write uncertainty and A-to-B-to-A blocked-ACK history.
- Synthetic frame, receipt and AH evidence remain honestly labeled, with no
  native or daemon-fallthrough claim.

Status: **READY** for the frozen recovery test implementation. This is not a
production-source verdict.
