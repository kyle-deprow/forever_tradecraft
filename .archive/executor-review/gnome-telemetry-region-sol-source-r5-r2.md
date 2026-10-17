# Sol source review: GNOME telemetry region R5 forwarding-test closure

I reviewed the one-file forwarding-test candidate in
`/home/dev/.cache/crowley/worktrees/region-r5-forwarding-test-20261017`
against the exact frozen R5 source and the bounded closure plan. I compared the
test directly with frozen R5 rather than with the worktree's Git baseline. I did
not run tests or builds, use Git, or operate any live desktop, game, service,
network, Docker, or database path.

## Identity verification

- Closure plan `.archive/PLAN-region-r5-forwarding-test-closure.md`:
  `b4e90ec9404f061f3b09c2098ed6c8a609fab532888456d336280c4d058389ed`
- Frozen R5 manifest
  `.archive/executor-review/gnome-telemetry-region-r5-freeze.json`:
  `307c6ef69ba4c8b7376af4307852b12fcb55a57da3c1df84c3ef1fc4ddda2bf2`
- Prior Sol R5 review
  `.archive/executor-review/gnome-telemetry-region-sol-source-r5.md`:
  `92aa145392c10b304a023efa96ea9905f02708c1990f8b8f3f7eb4eb6b36b7fb`
- Updated `tests/test_session_native.py`:
  `47ac2cef30d234983609db3c08ad17c24487126abaf3d2b48dc4aeaa4ee15f9b`
  (frozen R5 base:
  `169d0d3b6068d3ae42e762b7f3059348b42b5d988f012c8c520603da0978e764`)

The other eleven files in the twelve-file R5 freeze match their frozen hashes
exactly. The inspected delta is therefore confined to the authorized test file;
no production source, patch, build input, configuration, harness, or other test
changed.

## R1 closure

The R1 Must-Fix is causally closed. At
`tests/test_session_native.py:682`, the new invocation receives a distinct,
owned mode-0700 `XDG_RUNTIME_DIR`, so it does not encounter the private
producer's same-runtime flock. It retains the fixture's explicit private D-Bus
address, display, and X11 backend, then launches the real compiled producer
asynchronously at line 703 while the original capture is blocked inside the
real Shell boundary.

The assertions distinguish the repaired active-primary guard from the earlier
flock-only evidence. The primary producer's cached stderr must contain exactly
one `A foreign command line arrived while telemetry capture was active.`
diagnostic at lines 743-746, while the remote invocation exits 1 with no local
stdout or stderr, creates no output, and causes no second Shell call. The
original capture is then required to complete successfully, and the owner
process and Guardian ledgers must be empty while the canonical lease and
watchdog remain healthy. Removing or bypassing the R5 active-primary guard
would now fail this case.

The retained same-runtime ordinary and malformed-telemetry cases continue to
test the earlier flock boundary separately. The reported parent execution of
the exact composition node passed once in 4.68 seconds, with scoped Ruff and
format checks also passing; I did not independently execute them.

The earlier three-process parallel stress run's PNG-readiness failure remains
unresolved negative evidence. This serial forwarding test neither explains nor
erases that failure, and its one-file scope makes no broader concurrency claim.

## Must-Fix

None.

## Should-Fix

1. **The blocked fixture is not released in `finally` for all assertion and
   setup failures.** `tests/test_session_native.py:618-701` creates the block
   marker and starts the capture thread, then performs the gate-entry checks,
   process/Guardian assertions, both preserved same-runtime subprocess checks,
   and alternate-runtime setup before entering the cleanup `try` at line 702.
   A failure or exception in that interval skips the gate release and thread
   join at lines 716-730. The outer test cleanup can revoke and terminate the
   registered producer, but it does not satisfy the closure plan's explicit
   requirement to release the test gate and reap/join every started operation
   on assertion failure; it can also leave the daemon capture thread running
   while fixture teardown begins. Initialize the optional ordinary child and
   captured outputs before starting the blocked capture, and place the entire
   interval from `capture_thread.start()` through both preserved checks and the
   new forwarding launch inside a `try/finally` that always removes the block,
   publishes the release marker, joins the capture thread, and kills/collects
   the ordinary child if it was started. Keep the post-cleanup behavioral
   assertions after that `finally`.

## Nits

None.

STATUS: NEEDS WORK
