# Native calibration operator preparation R2

Status: **UNQUALIFIED OFFLINE R2 CANDIDATE**. This isolated correction is
not native acceptance and authorizes no desktop input, service restart, live
collection, integration, or promotion. Accepted native composition and the
parent/Sol/Opus gates remain required.

## Scope and provenance

Worktree: `/home/dev/.cache/crowley/worktrees/native-calibration-operator-preparation-r2-20261018`

Base: `cf4b6cc8cd3553273bf65bff47405208c810e091`

Owned files and final SHA-256:

- `tools/native_calibration_operator.py` — `8958a8efa9f9d531566b37a8a03b25b3a80e8dea97d948bb0488e9b02d8f589e`
- `tests/test_native_calibration_operator.py` — `3d8d0a3a42fd30ca9bfffb702c59bfcc7cb42bcefc964d09fd3423ef751b5b09`

The copied native dependencies are read-only for this candidate. Their observed
SHA-256 pins are:

- `guardian.py` `e73128de1e6fdf38beda8256b11f77d66b2b666eb8b1499018c70781217a2efa`
- `input_tool.py` `7d4edcc9094a813a2d8d87d0e94257493c11f5740f297eb0aefa7798b22a9ed6`
- `config.py` `976717d23d18d6c37d7a3a280d532ba0cdc15e6d086896fc4781b6efdf6b94cb`
- `driver.py` `ca0ca123d0fa09d8361c8632d9cc1c2c501d87adf99cb3cc268688dd4291a166`
- `decoder.py` `badd6c3f469f0f13503d3aa8851e7d0dac416629f3974841593d6b42d2199739`
- `cli.py` `f3156eb78a6cf20f88275b08b7fb105cd7466c59bde77097e949690bafcee8ab`
- `daemon.py` `6dfb65acea2d91096c8b37a5292a28dcc40e14782960277f3c94f32206df88d9`
- `controller.py` `f40ee4d3c4c7682a6d361eb90fc4e7cc54245ff4753f81ce8eeaa19af3b21839`

## R2 corrections

- Chat actions now verify the pre-action state, submit the fixed command, and
  only then await the causally newer requested state. The measure path starts
  the existing `native_calibrate` operation exactly once after bootstrap,
  polls `calibration_status` under the daemon-provided absolute deadline,
  aggregates unchanged polls, and retains terminal failure.
- The helper validates bounded private `stateHistory` records (maximum 16
  exact-field entries, finite nondecreasing native clocks, complete ordered
  construction/recovery prefixes, immutable prior prefix). Missed transient
  daemon states are accepted only when the published history proves the
  contiguous chain; skipped, regressed, missing, or conflicting history
  refuses before input.
- Recovery requires an actual terminal `recovered` or `cancelled`
  reservation record. Terminal native errors use the existing status/pause
  path with the fixed recovery reason, then preserve the first causal error
  and perform bounded cancellation cleanup.
- Chat OCR is restricted to the reviewed fixed crop. Template matching is
  exact-resolution and bounded; a positive role is checked against its rival
  at the same candidate box, allowing the legitimate other panel button
  elsewhere. Post-reload Construct/Restore positives must be distinct.
- Repositioned clicks recheck identity, focus, binding, pointer coordinates,
  and target XID immediately before the owned emitter press. The emitter,
  watchdog ACKs, status/EOF reads, release, and close paths use finite
  bounds; no production `_test_run` bypass remains.
- Capture and receipt clocks remain separate. Private atomic receipts retain
  source/producer/template bindings and bounded poll summaries without
  exposing raw paths or command output.

## Checks

Commands ran in the isolated worktree; no native suite, live desktop, service,
or network was used:

- `uv run pytest -q tests/test_native_calibration_operator.py --maxfail=1`
  — **13 passed, 2 warnings, 2.62s**. Warnings are Python's
  fork-in-multithreaded-process deprecation from the offline gated-emitter
  tests.
- `uv run ruff check tools/native_calibration_operator.py tests/test_native_calibration_operator.py`
  — **passed**.
- `uv run ruff format --check tools/native_calibration_operator.py tests/test_native_calibration_operator.py`
  — **2 files already formatted**.
- `python3 -m compileall -q tools/native_calibration_operator.py tests/test_native_calibration_operator.py`
  — **passed**.
- `git diff --no-index --check /dev/null tools/native_calibration_operator.py`
  — **passed with the expected exit status for an untracked added file and no
  whitespace diagnostics**.

Private retained logs and hashes:

`/home/dev/.local/state/crowley/executor-evidence/native-calibration-operator-preparation-r2-20261018/`

## Remaining qualification boundaries

1. This candidate still imports the copied rejected native dependencies. Native
   IPC parser behavior, daemon state-history publication, reservation ownership,
   Guardian/lease lifecycle, cancellation/recovery handoff, and terminal
   response shapes require composition tests against the accepted native
   implementation.
2. No real X11 image, addon reload lifecycle, OCR engine, XTEST callback,
   pinned producer, native terminal error, or service was exercised. Templates
   and geometry remain fixtures.
3. The process-loss, signal, ACK-loss, and watchdog behavior here is covered by
   bounded offline emitter tests only; parent must run the complete accepted
   native composition matrix and independent external reviews.
4. This work does not establish a CPU bottleneck or a Rust migration trigger.
