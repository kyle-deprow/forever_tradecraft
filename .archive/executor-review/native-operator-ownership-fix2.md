# Native operator ownership fix2

Status: implementation complete in the isolated fix2 worktree; no native-R5,
live desktop, game, deployment, or qualification claim.

## Frozen source

Worktree: `/home/dev/.cache/crowley/worktrees/native-operator-ownership-fix2-20261018`

Owned files:

- `tools/native_calibration_operator.py`
  SHA-256 `d589ac388aab6869d5a16f2bea037a3f08bc2ec502265a22c568adab264d9bfc`
- `tests/test_native_calibration_operator.py`
  SHA-256 `455e97b67f7c545032af6c1b0730b9fc1a1b26860d0016e1c69d563c5cbf7391`

The six copied R5 development dependencies were not edited by this fix2 pass:

```text
src/crowley/session/cli.py                         df59d15c05fc1ae723b99927ce3cecefacd418442ffd08f8e4b75ee349041220
src/crowley/session/controller.py                   f40ee4d3c4c7682a6d361eb90fc4e7cc54245ff4753f81ce8eeaa19af3b21839
src/crowley/session/daemon.py                       7a3f100aee45b6f6358b7529bae2e31b7fe7c5a4685291567e27576f3cb5a0ed
tests/test_session_native.py                        7994ab963b8bd8073a22ea16f45fe62f294afda5598568de51300fac345d1b7b
tests/test_session_native_regressions.py            e82e8e295614f4c7942fd6655303cec0772abb2110ec65b24a90e7a76f6a9b21
tests/test_session_transitions.py                   cdb4384f3408bb5b21a18445a2c5df8a74dcd271c812ba9b39f9eb171dfce331
```

## Implemented closure

- Admission and handoff install the independent cancellation actor before the
  helper exposes a new binding; every acknowledged binding update carries its
  canonical generation, reservation ID, and expiry, including bootstrap's
  long expiry. Production clients refuse a missing socket; test-only clients
  must opt into the explicit bypass.
- Canonical terminal cancellation is acknowledged before the actor is closed.
  Failed synchronous cancellation retains EOF cancellation, protected cleanup
  starts before recovery/cancel, and cleanup failures change a provisional
  success receipt to failure while preserving the first causal exception.
- Watchdog and cancellation entry wrappers use independent sessions and detach
  standard descriptors. Retained watchdog children are removed from the
  multiprocessing implicit join set without a silent registry fallback, and
  nonzero child exit is never treated as release confirmation.
- Fixed text actions use a bounded delay-derived timeout and publish a nonempty
  exact fixed-text keysym set. Emitter, screen, watchdog, and actor setup paths
  track and close descriptors/specs on staged failure; emitter abort is always
  attempted after release failures.

## Verification

Commands and results:

```text
PYTHONPATH=src uv run pytest -q tests/test_native_calibration_operator.py --maxfail=1
42 passed, 2 warnings in 30.90s

uv run ruff check tools/native_calibration_operator.py tests/test_native_calibration_operator.py
All checks passed

uv run ruff format --check tools/native_calibration_operator.py tests/test_native_calibration_operator.py
2 files already formatted

python3 -m py_compile tools/native_calibration_operator.py tests/test_native_calibration_operator.py
passed

git diff --check
passed
```

The focused cases include actual sealed compiled input fixtures, key and button
owner death, independent sessions, bootstrap expiry/handoff rebinding, local
socket cancellation, normal `SystemExit(2)` with a retained release actor,
handled TERM with repeated cleanup signals, fixed typing ownership/timing, and
staged readiness rollback. The tests use isolated fixtures and do not send
input to a real desktop.

Remaining boundary: the copied R5 files are development dependencies and were
not accepted or integrated here. Full native session composition, live X11,
and native qualification remain parent-owned follow-up work.
