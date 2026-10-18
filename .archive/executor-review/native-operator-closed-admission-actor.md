# Closed admission actor closure

Status: bounded actor-admission component complete in the isolated worktree;
native daemon integration and live qualification remain parent-owned.

The helper now starts the independent non-daemon actor before production
admission. For a real `DaemonClient`, the actor constructs the existing public
`native_construction_*` requests for prepare/preflight, bootstrap, recovery
begin/complete, cancel, finalize admission, and terminal recheck. It validates
the canonical reservation, sealed immutable fields, state history, generation,
and expiry before returning the response to the helper. Bootstrap expiry is
adopted from the server (the focused fixture used the required 3130-second
extension). Recovery explicitly permits one advancing generation with a new
canonical reservation ID while retaining the sealed owner/profile/identity
fields. Lost responses remain `AdmissionIndeterminate`; no guessed ID or retry
is performed. The existing fake-client path remains test-only direct behavior.

The local AF_UNIX proof used Linux `SO_PEERCRED` on every admission connection.
The final focused run recorded:

* actor `2178217`, helper `2177989`: prepare/bootstrap/finalize/recheck/cancel,
  all five peers actor `2178217`;
* actor `2178228`, helper `2177989`: preflight/recovery-begin/recovery-complete,
  all three peers actor `2178228`, with recovery generation 31 -> 32 and a new
  reservation ID;
* real `DaemonClient` operator prepare actor `2178246`, helper `2177989`;
* held prepare reply: actor `2178334`, killed owner `2178286`, both prepare and
  exact-generation/reservation cancel peers `2178334`.

The held-reply fixture releases the canonical prepare response only after the
owner is SIGKILLed. The actor consumes that response, records the canonical ID,
and performs the exact cancellation request. Refusal and transport-loss tests
assert the actor remains armed; the operator route asserts no input calls before
the actor acknowledgement. Finalize is followed by an independent recheck in
the peer-credential fixture.

Validation from the isolated worktree:

```
PYTHONPATH=src XDG_RUNTIME_DIR=/tmp/crowley-actor-xdg-20261018 \
  /home/dev/repos/pegasus/.venv/bin/pytest -q tests/test_native_calibration_operator.py --maxfail=1
48 passed, 2 warnings, 35.09s

PYTHONPATH=src XDG_RUNTIME_DIR=/tmp/crowley-actor-xdg-20261018 \
  /home/dev/repos/pegasus/.venv/bin/pytest -q tests/test_native_calibration_operator.py \
  -k 'actor_owns_prepare or actor_owns_recovery or actor_admission_survives_owner or routes_real_daemon or refusal_keeps or lost_admission' -s
6 passed, 42 deselected, 2.98s
```

Scoped Ruff check/format, Python compileall, and `git diff --check` all pass.
The owned source hashes are:

```
tools/native_calibration_operator.py       44acb08dd44f3974819937b3874abf6809381cbc18505a9fa02b3ec728a5e6b8
tests/test_native_calibration_operator.py  9c1c5043dceab6b0f18a4620c60e2b1e31bb904f2b01a0945c9c8c8dee784575
```

The six copied R5 dependency files remain read-only development inputs. The
peer proof uses a local deterministic AF_UNIX server and canonical fixtures; a
fresh composed run against the accepted daemon/R5 dependency set is still
required before integration or live use. Existing original fix2 typing and
input ownership behavior is retained; this component does not claim a second
live desktop run.
