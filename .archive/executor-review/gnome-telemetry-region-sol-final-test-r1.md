# Sol source review: final R6 test-only closure

I reviewed only the final `tests/test_session_native.py` delta in
`/home/dev/.cache/crowley/worktrees/region-r6-identity-test-20261017` against
the original frozen R6 test. I did not rerun tests, use Git, inspect runtime
state, operate the desktop, or reopen the accepted production implementation.

## Identity and scope

- Final test: `a1780bbdad1a8c50a352ab36c303d04a52f05226c81bb423c74c6293f01ac354`
- Original frozen R6 test:
  `131b491df437dc52cdd48a6ab96a0f1b5f6129ee9b6f52980a7359d8399f10d3`
- Test-only baseline manifest:
  `0285c2179d222910ad9ea500945faf6b8678b95a89db6d6b814b6a4384d63cb4`
- Final R6 freeze used by the test:
  `61166a2a12adf1ad5861a7051f65f926791aeb004246ccdfd52b022877a8ef79`
- Actual Opus R6 review:
  `d303f0bddbb23b5d14854f604da0241fe2423b5639d61f3002ac3e500c953cf5`
- Worker-reported focused compiled result: `1 passed in 4.97s`; I did not
  reproduce it. Parent's final forwarding-node reproduction was still pending
  in the supplied handoff and is not represented as complete here.

I independently checked all other eleven baseline paths in the successor
worktree. They match the baseline exactly, including frozen production source,
native patch/build inputs, harness, and the two other tests. The candidate
changes only `tests/test_session_native.py`.

## Closure assessment

- **Final producer provenance is correct.** Both compiled tests now read
  `.archive/executor-review/gnome-telemetry-region-r6-final-freeze.json` and use
  its actual nested `build.private_binary_sha256` field
  (`tests/test_session_native.py:333-344`, `:1071-1081`). The copied executable
  remains the final frozen R6 binary; no production or build input changed.
- **All five RPC calls are genuine and correctly typed.** The table at
  `tests/test_session_native.py:726-756` uses the D-Bus signatures required by
  `org.freedesktop.Application.Activate` (`a{sv}`), both
  `ActivateAction` calls (`sava{sv}`), and both
  `org.gtk.Actions.Activate` calls (`sava{sv}`). Empty dictionaries and variant
  arrays are encoded with zero entries, so these are valid method calls rather
  than parser-failure probes.
- **The RPCs cannot activate a host service.** Every call is made with
  `busctl --address=<private bus> --auto-start=no`
  (`tests/test_session_native.py:757-779`). The address is explicit and does
  not depend on a host session-bus environment. The synchronous
  `GetNameOwner` call at `:780-801` proves `org.gnome.Screenshot` is genuinely
  owned on that private bus while the primary capture is blocked.
- **Delivery remains proved by production behavior.** After the gate is
  released, every RPC child must return successfully, and the primary stderr
  still contains exactly four action guards and one activation guard in
  addition to the existing forwarded-command guard (`:834-858`). Thus fixed
  sleeps are not treated as proof of delivery: missing or late calls reduce the
  exact guard count and fail the test.
- **The negative no-autostart proof is semantic.** After the original primary
  has exited, another valid `Activate` with `--auto-start=no` must fail, and a
  direct `org.freedesktop.DBus.GetNameOwner` must report that the well-known
  name has no owner (`tests/test_session_native.py:859-903`). The area and stock
  Shell logs are then required to remain unchanged at `:904-905`. This covers
  both absence of the primary and absence of a replacement capture, rather
  than relying on an unsupported helper command or generic nonzero exit.
- **Cleanup and prior closure evidence are preserved.** All asynchronously
  started ordinary and RPC children remain in the existing `rpc_children`
  cleanup at `:802-821`; synchronous ownership probes are bounded
  `subprocess.run` calls. The exact primary guard counts, successful original
  capture, Guardian cleanup, held lease, and watchdog assertions remain. The
  ineffective local PNG assertions identified by Opus were removed without
  weakening the real Shell-log proof. The previously reviewed
  identity-before-capture block at `:2066-2143` is unchanged in substance and
  still exercises actual runner/owner IPC with exact `not_started` evidence.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
