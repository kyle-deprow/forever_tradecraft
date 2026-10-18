# Native calibration operator preparation R3

Status: **UNQUALIFIED OFFLINE CANDIDATE**. This report records the bounded R3
helper and its independent ownership evidence. It is not native acceptance, live
desktop evidence, or a release claim.

## Scope and provenance

The candidate was implemented in
`/home/dev/.cache/crowley/worktrees/native-calibration-operator-preparation-r3-20261018`
from the R2 candidate and the approved R3 plan
`PLAN-native-calibration-operator-review-fix-r3.md` (R2 report SHA
`ef761213c459cb19577562bc5fa71f24f59137e1f74b0460e9b362986919dc9f`). Only
these two owned files were changed:

| file | SHA-256 |
| --- | --- |
| `tools/native_calibration_operator.py` | `09987bec7daa2d587d06fe0dfc3be03725bf82ef5da5ec48323b0913e76ebe4c` |
| `tests/test_native_calibration_operator.py` | `a5dd6c9d5fc232ec5869f613987b72d2e6ce211e2338d2d0150860ca2f158020` |

The six R5 development files remain copied read-only dependencies for this
candidate; they are not owned by this slice. Their current R3 worktree hashes
are `cli.py` `f3156eb78a6cf20f88275b08b7fb105cd7466c59bde77097e949690bafcee8ab`,
`controller.py` `f40ee4d3c4c7682a6d361eb90fc4e7cc54245ff4753f81ce8eeaa19af3b21839`,
`daemon.py` `6dfb65acea2d91096c8b37a5292a28dcc40e14782960277f3c94f32206df88d9`,
`tests/test_session_native.py` `f787057139cfaeacad1756ac1799c8fbfbb3f2e06fba31456ee810caf734b9ae`,
`tests/test_session_native_regressions.py` `fbe07b6ac65e448514a68ee9c0ce99191b2de4daff61401747ef6371c558e178`, and
`tests/test_session_transitions.py` `99e15af5eed69c1cc58b77cdc255f92e961c4c1b20b4d6684e94ef6100d07742`.

## Implemented bounded behavior

The helper retains the closed three-mode vocabulary and the existing daemon
IPC/parser. It validates the complete reservation/state history prefix,
measure-finalized and recovery-terminal records, operation kind/generation,
phase-specific deadlines, release-dispatch bounds, five-second capture age,
identity/focus and pointer target at every physical gate, and post-dispatch
state causality. It uses measured client geometry for the TOPRIGHT control
region, exact immutable template bytes/sizes, local ambiguity/intersection
rejection, closed chat readback, and the same fresh dual-control plus Agent
absence boundary after reload. The pure absence classifier is lazy and refuses
when the accepted R5 function is unavailable.

All keyboard, fixed command text, pointer motion, and buttons use the pinned
sealed-image owned emitter. The independent watchdog receives exact ownership
sets and acknowledged empty-state clears. Setup/readiness, ACK, EOF, signal,
late-child, receipt, and cleanup errors preserve the first causal error and do
not silently claim release. Receipt writes use short-write loops, file and
directory fsyncs, private permissions, and the outer run lifetime owns begin,
execution, cleanup, and finish.

The test fixture advances state only from the injected input dispatch boundary.
It covers control-preflight, ordinary reload recovery, restore recovery, and
the deferred measurement workflow without asserting native qualification.

## Verification

The ownership-first command

`uv run pytest -q tests/test_native_calibration_operator.py`

passed **29 tests** in 6.50s. The real spawned cases include:

* sealed pinned emitter ACK/press/release;
* actual `_watchdog_entry` ACK and acknowledged empty clear;
* ACK-loss retention, gate EOF, late-child reaping, and readiness rollback;
* SIGTERM, SIGHUP, SIGINT, and SIGKILL emitter-group death;
* a compiled private sealed fixture where `keydown Return` is confirmed,
  the emitter group is SIGKILLed, and the independent watchdog logs the exact
  `keyup Return` release before reaping;
* receipt publication failure and run cleanup preserving the causal error.

The current composition command

`uv run pytest -q tests/test_native_calibration_operator.py tests/test_session_native_regressions.py tests/test_session_performance.py`

passed **186 tests** in 52.29s. A broader 334-test command including
`tests/test_session_native.py` passed in 264.34s before the final compiled
fixture test replacement; the current 186-test run includes that replacement.
Scoped checks passed:

* `uv run ruff format --check tools/native_calibration_operator.py tests/test_native_calibration_operator.py`
* `uv run ruff check tools/native_calibration_operator.py tests/test_native_calibration_operator.py`
* `uv run python -m py_compile tools/native_calibration_operator.py tests/test_native_calibration_operator.py`
* `git diff --check` on the copied native dependency files.

## Explicit limits

The R3 dependency copy does not contain the accepted R5 reload readiness
boundary or pure image-only Agent classifier, so no R3 test claims that native
composition. No live GUI, game, service restart, input, configuration, network,
database, deployment, or Rust work was performed. The helper remains an
unqualified offline candidate pending the parent’s exact R5 dependency transfer,
independent native composition, and Sol/Opus review.
