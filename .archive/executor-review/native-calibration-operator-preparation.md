# Native calibration operator preparation

Status: **UNQUALIFIED OFFLINE CANDIDATE**. This report records an isolated helper
candidate only. It does not authorize native integration, desktop input, service
restart, live collection, or promotion. Acceptance of the native controller,
daemon, CLI, addon/template geometry, and parent/Sol/Opus composition remains a
separate gate.

## Scope and provenance

Worktree: `/home/dev/.cache/crowley/worktrees/native-calibration-operator-preparation-20261018`

Base: `cf4b6cc8cd3553273bf65bff47405208c810e091`

Owned files and final SHA-256:

- `tools/native_calibration_operator.py` — `06b858d614facda8eb91a2b535359a8c7a8b3be42457a1b2f4ec0b97f2eb6e55`
- `tests/test_native_calibration_operator.py` — `fe1275249c1c2f55b44b3dee573baf4c061d45a9335c73797bd12f47ccde035f`

The copied read-only development dependencies were not modified. Their observed
SHA-256 pins are:

- `guardian.py` `e73128de1e6fdf38beda8256b11f77d66b2b666eb8b1499018c70781217a2efa`
- `input_tool.py` `7d4edcc9094a813a2d8d87d0e94257493c11f5740f297eb0aefa7798b22a9ed6`
- `config.py` `976717d23d18d6c37d7a3a280d532ba0cdc15e6d086896fc4781b6efdf6b94cb`
- `driver.py` `ca0ca123d0fa09d8361c8632d9cc1c2c501d87adf99cb3cc268688dd4291a166`
- `decoder.py` `badd6c3f469f0f13503d3aa8851e7d0dac416629f3974841593d6b42d2199739`
- `cli.py` `f3156eb78a6cf20f88275b08b7fb105cd7466c59bde77097e949690bafcee8ab`
- `daemon.py` `6dfb65acea2d91096c8b37a5292a28dcc40e14782960277f3c94f32206df88d9`
- `controller.py` `f40ee4d3c4c7682a6d361eb90fc4e7cc54245ff4753f81ce8eeaa19af3b21839`

The source tree had unrelated pre-existing modified read-only files; this
candidate touched only its two owned paths.

## Candidate behavior

The helper exposes exactly `control-preflight`, `measure-deferred`, and `recover`.
It uses the closed eight-command native IPC vocabulary and exact request keysets,
validates all fourteen canonical reservation fields, preserves daemon-provided
`expectedConstructorBoot` verbatim, rejects reservation/handshake drift and
skipped predecessor states, and uses absolute operation deadlines without retry
or deadline extension.

The production adapter uses `X11Backend` and `PinnedInputTool` directly. Identity,
capture, and pointer calls carry the daemon's remaining absolute deadline. Chat
input is limited to the fixed reviewed commands and exact normalized OCR
readback. Construct and Restore are the only private template roles; each click
requires a fresh unambiguous positive/negative match, fresh identity/focus and
pointer-target checks, and post-reload measurement requires both controls to be
positive. The ordinary recovery branch emits only `/reload`; the restore branch
uses `/crowley agent recover` and one Restore click.

Physical input is bounded to the pinned tool, button 1, and an owned gated
emitter process group. The existing `_watchdog_entry` and sealed
`NativeReleaseSpec` are reused; ownership is ACKed before press, exact release
is attempted on failure/owner loss, children are reaped, and ownership is
cleared after release. Signal handlers share the same abort path. Receipts use
private 0700 attempt directories and atomic 0600 `receipt.json` publication,
retain source/producer/template pins and bounded event data, and reject raw
paths, argv, environment, config, and secret fields.

## Checks

Commands were run in the isolated worktree; no native suite or live desktop was
run:

- `uv run pytest -q tests/test_native_calibration_operator.py --maxfail=1` — **11 passed, 1 warning, 4.71s**. The only warning is Python's fork-in-multithreaded-process deprecation in the offline gated-emitter test.
- `uv run ruff check tools/native_calibration_operator.py tests/test_native_calibration_operator.py` — **passed**.
- `uv run ruff format --check tools/native_calibration_operator.py tests/test_native_calibration_operator.py` — **2 files already formatted**.
- `python3 -m compileall -q tools/native_calibration_operator.py tests/test_native_calibration_operator.py` — **passed**.
- `git diff --check -- tools/native_calibration_operator.py tests/test_native_calibration_operator.py` — **passed**.

Private retained outputs:

- `/home/dev/.local/state/crowley/executor-evidence/native-calibration-operator-preparation-20261018/pytest-final.log`
- `/home/dev/.local/state/crowley/executor-evidence/native-calibration-operator-preparation-20261018/ruff-check-final.log`
- `/home/dev/.local/state/crowley/executor-evidence/native-calibration-operator-preparation-20261018/ruff-format-final.log`
- `/home/dev/.local/state/crowley/executor-evidence/native-calibration-operator-preparation-20261018/compile-final.log`
- `/home/dev/.local/state/crowley/executor-evidence/native-calibration-operator-preparation-20261018/diff-check-final.log`

## Concrete blockers before qualification

1. The candidate was tested against the copied rejected R3 native dependency
   files, not the accepted native implementation. The native IPC parser,
   daemon reservations, Guardian/lease lifecycle, cancellation/recovery
   handoff, and actual production response shapes still require composition
   testing against accepted source.
2. No real X11 image, panel/chat intersection, addon `ADDON_LOADED`/ReloadUI
   lifecycle, OCR engine, XTEST callback, or pinned producer was exercised.
   Template hashes and click geometry are fixture-only until parent supplies
   reviewed live artifacts.
3. No real desktop input, process-loss watchdog event, native terminal error,
   or service was run. The emitter/watchdog path is covered only by offline
   injected/fork tests and must be checked at the accepted native boundary.
4. Parent must rerun the helper's complete composed test matrix, native tests,
   and independent Sol/actual Opus review after replacing the read-only
   development dependencies. Until then, this candidate is not a live or Rust
   qualification result.
