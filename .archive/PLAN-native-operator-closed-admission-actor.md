# Closed admission actor component

Fix2 remains frozen and unaccepted. Its cancellation actor only receives updates
after the helper performs admissions; this does not implement the approved fix2
architecture. This component implements that exact missing architecture before
another full source review. Read PLAN-native-operator-ownership-fix2.md and its
Sol proposal as the contract; retain the other fix2 changes.

## Ownership and order

Root creates native-operator-closed-admission-actor-20261018 from 2fcdedd with the
exact frozen fix2 helper and tests plus the same six read-only native R5 development
dependencies. Only tools/native_calibration_operator.py and
tests/test_native_calibration_operator.py may change. Root owns git. No commit,
reset, stash, revert, GUI, live input, service/config/native/Guardian changes.
Do not add a generic RPC forwarder, public schema, mode, or input capability.

1. Make the independent ownership actor perform fixed existing prepare/preflight,
   bootstrap, recovery begin, cancel, recovery complete, finalize admission and
   the necessary canonical terminal recheck. Fixed private enum and exact fields;
   construct existing public request bodies inside the actor. The helper must not
   issue ownership admissions and then merely publish the returned binding.
2. Actor validates and stores canonical generation, ID and expiry BEFORE ACK to
   helper. Bootstrap replaces short prepare expiry with canonical long expiry.
   Recovery retains known binding while request pending and adopts new binding
   before ACK. No physical input before ACK; actor performs no physical input.
3. Keep protection until exact canonical terminal proof. Finalize admission is
   not terminal. Failed transport/recovery/cancel remains armed. Owner death while
   admission reply is pending must still consume the canonical reply and cancel
   its known ID. Lost reply is honestly indeterminate: no guessed ID/retry/input;
   preserve known binding and record unknown admission's existing bounded expiry.
4. Preserve fix2 signal/session/stdio/typing/rollback changes. Do not expand this
   component into another unrelated workflow rewrite.

## Decisive verification

Use an actual local AF_UNIX server with SO_PEERCRED to prove the peer sending each
ownership admission is the independent actor PID, NOT the helper owner PID. Hold
server reply at a barrier; kill helper before ACK; return canonical admission and
assert actor cancels that exact generation and ID. Cover prepare, bootstrap's
3130-second expiry and recovery's new generation/ID. Include no-input-before-ACK,
lost reply indeterminate, failed terminal operation retaining protection, and
finalize-admit requiring actual terminal recheck. Instant fake clients and actor
update tests cannot substitute for peer-PID proof. Send literal focused results
and peer/owner/actor IDs before the full suite.

Then run the complete helper suite once on final source with main .venv/bin/python,
PYTHONPATH=<worktree>/src and a fresh private 0700 XDG_RUNTIME_DIR, scoped Ruff
check/format, compile and git diff --check. Preserve private complete logs, source
and dependency hashes and import origins. No unrelated native suite. Write only
the extra main report .archive/executor-review/native-operator-closed-admission-actor.md.
Report actual covered/uncovered cases. DONE only when this architecture and its
real process proofs are complete. Parent verifies before Sol and actual Opus.
