# Sol source review: R6 identity-before-capture test closure

I reviewed only the one-file successor test in
`/home/dev/.cache/crowley/worktrees/region-r6-identity-test-20261017` against
the frozen R6 candidate. I did not run tests, use Git, inspect live state, or
make source/runtime changes.

## Identity and scope

- Baseline manifest
  `.archive/executor-review/gnome-telemetry-region-r6-identity-test-baseline.json`:
  `0285c2179d222910ad9ea500945faf6b8678b95a89db6d6b814b6a4384d63cb4`
- Frozen R6 `tests/test_session_native.py`:
  `131b491df437dc52cdd48a6ab96a0f1b5f6129ee9b6f52980a7359d8399f10d3`
- Successor `tests/test_session_native.py`:
  `b8e582ec555c787ff3e8d0df886e1b1df47360eeffc54d373a32ff05baad395b`
- Parent-provided final focused log:
  `4ef7b5c935fd553536f2d22f2b344099345d56179135d77e82006d07b0acc22a`
  (`1 passed in 37.89s`)

I independently checked the other eleven baseline paths in the successor
worktree; every hash matches the baseline manifest. The delta is confined to
the new block at `tests/test_session_native.py:1991-2067`. No production,
harness, native patch, build, configuration, or other test file changed.

## Closure assessment

The test closes the prior Should-Fix meaningfully:

- It keeps the constructed production `SessionDaemon`, real `X11Backend`,
  real `SessionIPC` socket handler, and actual `run_paused_diagnostic` runner.
  The only injected fault replaces that backend instance's external identity
  lookup with a deterministic `DriverError`; it does not construct a synthetic
  IPC response or bypass the owner/harness validation path
  (`tests/test_session_native.py:1999-2019`).
- The public receipt must retain the outer
  `sample_0_owner_capture_ipc` failure and the bounded owner response. The
  nested owner response must retain the exact original error and
  `identity_before_capture` phase (`:2021-2034`).
- The producer attempt is compared as an exact object with stage
  `not_started` and null `request_started`, `lock_acquired`, and `ack_sent`;
  both the returned owner evidence and separately read durable owner receipt
  must preserve it (`:2035-2057`). A stale prior attempt or fabricated clock
  therefore fails the regression.
- The test proves the owner request directory/receipt exists, no client PNG was
  published, owner cleanup is empty, the canonical lease remains held and
  unarmed, and no Shell call or Guardian/backend admission/process ledger
  changes (`:2043-2067`). Its request-count assertion correctly accounts for
  the runner's status request plus owner IPC; the retained initial failure and
  corrected `+2` expectation demonstrate that this assertion follows the real
  route rather than an assumed shortcut.
- The original identity resolver is restored in `finally`, so a failure in the
  diagnostic cannot contaminate the later compiled-owner cases (`:2015-2019`).

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
