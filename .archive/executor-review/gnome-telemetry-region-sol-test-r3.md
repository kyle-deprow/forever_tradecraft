# Sol source review: R6 test closure R3

I reviewed only the two-assertion delta in
`/home/dev/.cache/crowley/worktrees/region-r6-test-r3-20261017` against the
prior test-only candidate. I did not execute tests, use Git, inspect runtime
state, or reopen production R6 source.

## Identity and scope

- R3 `tests/test_session_native.py`:
  `ade91281df21869fdf7bdb2b7ccfcde4e92e3333467788811395988427437cb8`
- Prior test-only candidate:
  `a1780bbdad1a8c50a352ab36c303d04a52f05226c81bb423c74c6293f01ac354`
- Exact parent delta:
  `b275e9114263a6bcfd42bf5693739d11dd3384b319d00700ab756644ced93b2b`
- Actual Opus R2 report:
  `385bd03c2850584a031f0af6f1c94b5ff35c2491111375ba9cd74ec6a17b9df0`

The supplied delta contains exactly two added assertions. I independently
checked the other eleven native paths; all match the frozen R6 baseline hashes.
There is no production, harness, native patch, build, configuration, or other
test change.

## Closure assessment

- **Harness acceptance is now distinguished from saved owner evidence.** At
  `tests/test_session_native.py:2101-2106`, the test requires the runner's
  terminal error to be exactly the original owner refusal. The harness first
  saves `owner_failure`, then validates its producer attempt at
  `tools/gnome-telemetry-region/offline_harness.py:1282-1334`, and only after
  successful validation raises the owner refusal at `:1363-1364`. The outer
  receipt records that exception at `:1511-1515`. Removing `not_started` from
  the accepted stages, breaking its all-null rule, or otherwise remasking the
  owner failure produces a different schema/timing error and now fails this
  assertion. The existing exact owner/durable-receipt assertions remain
  unchanged.
- **The late no-autostart proof is strict.** At
  `tests/test_session_native.py:879-881`, the valid late `Activate` must have
  empty stdout and the private bus's precise `Name "org.gnome.Screenshot" does
  not exist` error. If `--auto-start=no` is removed and service activation is
  attempted, the process-start failure text cannot satisfy this assertion.
  The subsequent real `GetNameOwner` no-owner check and unchanged Shell logs
  remain in place.

The worker-reported focused results cover both affected compiled nodes; the
parent reproduction was still in progress in the supplied handoff, so I do not
represent it as complete.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
