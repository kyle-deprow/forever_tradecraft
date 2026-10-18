# Native calibration operator ownership R4 fix1

Status: **UNQUALIFIED OFFLINE OWNERSHIP CLOSURE**. This report records the
bounded fix1 evidence only. It is not native acceptance, live desktop
evidence, or a release claim.

## Scope and provenance

Worktree:
`/home/dev/.cache/crowley/worktrees/native-calibration-operator-ownership-r4-fix1-20261018`

Only these two files are owned by this slice:

| file | SHA-256 |
| --- | --- |
| `tools/native_calibration_operator.py` | `94d1ad216e5bd4a7a8abf2883f623015b434ee31ae425f208542e5ab4ba48ae9` |
| `tests/test_native_calibration_operator.py` | `164db34cb3c44b63e41f6ca01e45cbf28f8012da40af4edf61818382592cd5d8` |

The six native R5 files remain copied read-only development dependencies:

| file | SHA-256 |
| --- | --- |
| `src/crowley/session/cli.py` | `df59d15c05fc1ae723b99927ce3cecefacd418442ffd08f8e4b75ee349041220` |
| `src/crowley/session/controller.py` | `f40ee4d3c4c7682a6d361eb90fc4e7cc54245ff4753f81ce8eeaa19af3b21839` |
| `src/crowley/session/daemon.py` | `7a3f100aee45b6f6358b7529bae2e31b7fe7c5a4685291567e27576f3cb5a0ed` |
| `tests/test_session_native.py` | `7994ab963b8bd8073a22ea16f45fe62f294afda5598568de51300fac345d1b7b` |
| `tests/test_session_native_regressions.py` | `e82e8e295614f4c7942fd6655303cec0772abb2110ec65b24a90e7a76f6a9b21` |
| `tests/test_session_transitions.py` | `cdb4384f3408bb5b21a18445a2c5df8a74dcd271c812ba9b39f9eb171dfce331` |

## Fixes

Cancellation actor EOF is now treated as an abrupt owner/control failure even
when a killed owner remains a zombie with the same `/proc` start identity.
Only an explicit stop frame disarms the actor. The actor accepts a bounded,
validated, acknowledged internal handoff frame for generation, reservation ID,
and deadline; operator handoff updates the existing actor in place and refuses
socket replacement, so no stop-then-start admission window can send a stale
cancellation.

Watchdog and cancellation setup continue to close descriptors on readiness
failure. The real failed-release owner test now launches a distinct owner
process, confirms nonzero bounded owner termination while the watchdog actor
remains alive, then enables the exact sealed release and confirms the retained
actor exits. PID/start waits are monotonic and identity-aware, avoiding the
parent's prior immediate-final-exit race.

Run signal handlers remain installed through cleanup and ignore repeated
handled signals after cleanup starts; restoration occurs after input, actor,
and receipt cleanup. The production-main composition test invokes the actual
`main` lifetime with a sealed compiled input artifact, real Watchdog and
OwnedEmitter paths, an acknowledged button hold, exact `mouseup 1` release,
and the exact admitted recovery-cancel IPC. Existing separate owner fixtures
retain key and button SIGKILL coverage.

## Verification

Focused ownership command:

`uv run pytest -q tests/test_native_calibration_operator.py -k 'spawned or actual_helper_owner or production_main_lifetime or cancellation_actor or unconfirmed_release or real_owner_exit or handled_signal_handlers' -o faulthandler_timeout=20`

Result: **20 passed, 18 deselected**, 17.92s.

Final helper command:

`uv run pytest -q tests/test_native_calibration_operator.py -o faulthandler_timeout=20`

Result: **38 passed**, 2 existing multiprocessing fork deprecation warnings,
22.23s.

Scoped checks passed:

- `uv run ruff format --check tools/native_calibration_operator.py tests/test_native_calibration_operator.py`
- `uv run ruff check tools/native_calibration_operator.py tests/test_native_calibration_operator.py`
- `uv run python -m compileall -q tools/native_calibration_operator.py tests/test_native_calibration_operator.py`
- `git diff --check`

The final suite includes sealed input ACK/release, ACK loss, EOF, late child,
readiness rollback, signal-group termination, receipt publication and cleanup
failure, actual helper-owner key/button SIGKILL, zombie-owner cancellation EOF,
canonical handoff, persistent release failure with bounded owner exit,
production-main release/cancel composition, and repeated handled-signal
cleanup.

## Limits

No live GUI, game, service restart, input, configuration, network, database,
deployment, or Rust work was performed. The production-main composition uses
harmless compiled sealed fixtures and a local test UNIX socket; it is not live
native qualification. Native R5 composition remains outside this slice.
