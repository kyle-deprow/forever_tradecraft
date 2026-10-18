# Native calibration operator ownership R4

Status: **UNQUALIFIED OFFLINE OWNERSHIP CLOSURE**. This report records the
bounded R4 helper evidence only. It is not native acceptance, live desktop
evidence, or a release claim.

## Scope and provenance

Worktree:
`/home/dev/.cache/crowley/worktrees/native-calibration-operator-ownership-r4-20261018`

Only these two files are owned by this slice:

| file | SHA-256 |
| --- | --- |
| `tools/native_calibration_operator.py` | `e7196fb3cc9a0dc62580d18d280bca8a9773d3da8385c6dcb1ba3ca2b169a728` |
| `tests/test_native_calibration_operator.py` | `ccadc93f4e2a928621e0d4dc2bcb2589a19d80b1bfab1aa37b2e3108d9aeaf5b` |

The six native R5 files were copied read-only development dependencies, not
owned by this work:

| file | SHA-256 |
| --- | --- |
| `src/crowley/session/cli.py` | `df59d15c05fc1ae723b99927ce3cecefacd418442ffd08f8e4b75ee349041220` |
| `src/crowley/session/controller.py` | `f40ee4d3c4c7682a6d361eb90fc4e7cc54245ff4753f81ce8eeaa19af3b21839` |
| `src/crowley/session/daemon.py` | `7a3f100aee45b6f6358b7529bae2e31b7fe7c5a4685291567e27576f3cb5a0ed` |
| `tests/test_session_native.py` | `7994ab963b8bd8073a22ea16f45fe62f294afda5598568de51300fac345d1b7b` |
| `tests/test_session_native_regressions.py` | `e82e8e295614f4c7942fd6655303cec0772abb2110ec65b24a90e7a76f6a9b21` |
| `tests/test_session_transitions.py` | `cdb4384f3408bb5b21a18445a2c5df8a74dcd271c812ba9b39f9eb171dfce331` |

## Implemented bounded behavior

The watchdog now accepts and verifies the actual helper owner's PID and
process-start identity, while retaining the existing sealed
`NativeReleaseSpec` and `_watchdog_entry` release path. A bounded owner-side
process wait polls an explicit monotonic deadline, so unrelated child signals
cannot extend cleanup. A failed physical release leaves the non-daemon release
actor alive; the owner receives the bounded failure rather than terminating the
actor to make the test exit cleanly.

The helper arms one independent cancellation actor for an admitted daemon
binding. The actor watches the helper owner's PID/start identity and, after
owner death, sends only the existing
`native_construction_recovery_cancel` request with the bound generation and
reservation ID through the existing bounded UNIX-socket transport. It stops on
normal owner cleanup and is independent of input-release cleanup.

## Actual verification

Focused ownership command:

`uv run pytest -q tests/test_native_calibration_operator.py -k 'spawned or actual_helper_owner or cancellation_actor or unconfirmed_release' -o faulthandler_timeout=20`

Result: **15 passed, 18 deselected**.

The real spawned ownership cases passed for both a confirmed `keydown
Return` and `mousedown 1` hold: the distinct helper owner was SIGKILLed,
the independent watchdog logged exactly `keyup Return` or `mouseup 1`,
and the emitter group and watchdog were reaped. The helper exit code was
`-SIGKILL` within the five-second bound.

The independent cancellation case passed with a distinct spawned owner and a
real bounded AF_UNIX listener. The sole received request was:

```json
{"command":"native_construction_recovery_cancel","generation":17,"reservationId":"reservation-live"}
```

The delayed-release case passed with the first real release subprocess timing
out, the watchdog remaining alive, owner close returning its bounded
`confirm release` error, and a later retry recording the exact `keyup`
after the actor remained independent.

Final helper command:

`uv run pytest -q tests/test_native_calibration_operator.py -o faulthandler_timeout=20`

Result: **33 passed**, 2 existing multiprocessing fork deprecation warnings,
13.51s.

Scoped checks passed:

- `uv run ruff format --check tools/native_calibration_operator.py tests/test_native_calibration_operator.py`
- `uv run ruff check tools/native_calibration_operator.py tests/test_native_calibration_operator.py`
- `uv run python -m compileall -q tools/native_calibration_operator.py tests/test_native_calibration_operator.py`
- `git diff --check` for the owned worktree changes

The existing sealed-emitter tests also retain SIGTERM, SIGHUP, SIGINT, and
SIGKILL group-death coverage, ACK loss, gate EOF, late-child reaping,
readiness rollback, receipt publication failure, and cleanup-on-receipt-error
cases.

## Limits

No live GUI, game, service restart, input, configuration, network, database,
deployment, or Rust work was performed. The cancellation and owner-death
tests use harmless compiled sealed fixtures and no real X input. Native R5
composition and qualification remain outside this slice.
