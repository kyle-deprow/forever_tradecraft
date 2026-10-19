# Native helper release corrections — final offline evidence

Status: **implementation and real fixture evidence complete; parent independent review pending**.

This report covers only the two owned files in `/home/dev/.cache/crowley/worktrees/native-helper-final-integration-20261019`. It records the final source/test bytes and retained evidence; it does not claim live GUI, addon, deployment, or native promotion acceptance.

## Scope and hash pins

- Base commit: `c5e577200adadb8c158b1009643aa0f746d98753`
- Worktree: `/home/dev/.cache/crowley/worktrees/native-helper-final-integration-20261019`
- Owned implementation: `tools/native_calibration_operator.py` SHA-256 `6f8f87efad4e818d3c401d600d7fabe34d8ba48c405832ff20e53924bb5ddbac`
- Owned tests: `tests/test_native_calibration_operator.py` SHA-256 `39f7c5c769e9769561f44d45b9cd6b759ae329fec45ef9aa6ba4a0ae45503bee`
- The seven R10d native dependencies were read-only in this task and remain pinned:

  - `src/crowley/session/cli.py` — `df59d15c05fc1ae723b99927ce3cecefacd418442ffd08f8e4b75ee349041220`
  - `src/crowley/session/controller.py` — `dcdc7387e9c0f39bec3473e1bcfaa9a8c108987fd03c67a7029f84fa876b82e4`
  - `src/crowley/session/daemon.py` — `5c55f9b3080649cebf7bb57fbdcd14f69ddcbac83f5172500ba045c745d9ea58`
  - `tests/test_session_native.py` — `bd719bb26e25ae23583658680d26a14fcf45defbd03f1887f4a4fa7e9b55f1ef`
  - `tests/test_session_native_regressions.py` — `12ed6f14abbb7dae5bb68f12f1fac904badfcfc32a87eeb765a47553fbd0ef2a`
  - `tests/test_session_runtime.py` — `d762163925d61d5a42d40123fa9815fabe7bb24a2f0382726fd8bc33ca3f616f`
  - `tests/test_session_transitions.py` — `6b0bc711eedad30c4bc400584fb4357ce7e53784542be5e39aaa45959cc08293`

No native, driver, Guardian, addon, config, service, GUI, deployment, or Git mutation was made by this helper task. The worktree status showing the seven copied R10d inputs as modified relative to the base is expected; their hashes above are unchanged task inputs.

## Implemented contract corrections

- Pause handling now validates the immediate controller response for `PAUSED`, a newer controller generation, and a higher lease generation. It then fetches aggregate status to require the native operation to be nonrunning and the Guardian unarmed. Recovery input requires the new canonical binding with a higher Guardian generation and `guardianArmed == false`. The original exception and failed receipt are retained after recovery.
- `_record_operation_deadline` keeps the minimum existing deadline, so a later report cannot extend an operation.
- Owned emitter startup aborts and reaps on invalid process-group/readiness failure. Watchdog startup rejects missing or malformed exact owner-start identity. Cancellation actor startup closes inherited descriptors outside its protocol whitelist.
- The composed fixture uses the real compiled private `gnome-screenshot`, private X11/Shell compositor, real daemon AF_UNIX IPC, Lua-rendered PNGs, real `X11Screen`, `FixedInput`, `OwnedEmitter`, and `Watchdog`. Screen and input share one sealed artifact. Controls are ACK-dispatched only after the real client state changes.
- Receipt assertions pin the helper source, profile, construct/restore templates, producer manifest, pinned input tool, and native dependency hashes through `_source_bindings` and the actual receipt.

## Real workflow coverage

The parameterized `test_actual_operator_measure_composes_x11_screen_daemon_and_agent` exercises these actual modes through `NativeCalibrationOperator.run`:

| Case | Resulting proof |
| --- | --- |
| `success` | Construct, held-0, updates 1 through 99, held-100, resume, finalize; finalized Lua client; controller `INPUT_CALIBRATION`; native calibrated true; input calibrated false; receipt provenance hashes. The same case then pauses publicly and runs a fresh real `MODE_RECOVER` owner through ordinary SavedVariables reload, consuming the checkpoint and leaving `PAUSED`, native true, input false, checkpoint `None`, Guardian unarmed, and a newer ordinary boot. |
| `measurement-failure` | Real provider-side failure preserves the original exception, transitions to a newer PAUSED generation, performs empty-ID recovery through a fresh ordinary client, and preserves a failure receipt with terminal/recovery events. |
| `control-preflight` | Real configured control-preflight admission followed by ACK-dispatched Restore and fresh ordinary publication. |
| `recover-ordinary` | Real paused checkpoint and empty-ID ordinary recovery through the compiled producer and daemon IPC. |
| `recover-restore` | Real paused checkpoint and Restore control path through the compiled producer, then fresh ordinary publication. |
| `watchdog-readiness` | Real Watchdog closed before run; refusal is bounded and receipt is terminal. |
| `pressed-budget` | Real input path has a deadline that cannot fit; refusal occurs before physical action and cleanup remains empty. |
| `post-handoff-cancel` | Real provider sends SIGINT after handoff; `OperatorInterrupted`, cancellation receipt, and disarmed Guardian are asserted. |

The supplemental standalone causal tests retain public prepare/bootstrap/status/pause/recovery and allocation-failure checks. The focused post-success case was separately retained at `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-helper-final-integration-20261019/logs/success-postsuccess-recovery-3.log`.

## Retained commands and outputs

Authoritative final helper run:

```text
XDG_RUNTIME_DIR=/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-helper-final-integration-20261019/xdg-runtime PYTHONPATH=/home/dev/.cache/crowley/worktrees/native-helper-final-integration-20261019/src:/home/dev/repos/pegasus /home/dev/repos/pegasus/.venv/bin/pytest -q tests/test_native_calibration_operator.py --disable-warnings
```

- return code: `0`
- result: `73 passed, 3 warnings in 364.98s (0:06:04)`
- log: `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-helper-final-integration-20261019/full-helper-final-r2.log`
- log mode: `0600`
- log SHA-256: `3160c921594945e6f29120d08af45b75fe54cf27a9d06f96d5ed4355aaed761e`
- result record: `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-helper-final-integration-20261019/full-helper-final-r2-result.json`
- result-record mode: `0600`
- result-record SHA-256: `cbb2e76171dba5c8ef64c5781edbf9a0070e55cb9089c2ea1de2279b1efc8fbc`

The final success/public-pause/fresh-recovery run was retained at `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-helper-final-integration-20261019/logs/success-postsuccess-recovery-3.log` with SHA-256 `ce55cfc2ae7f350055e804707d1be628f618966ff384bffa992a0192a855ee0a` and result `1 passed in 141.64s`. The focused negative matrix was retained at `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-helper-final-integration-20261019/logs/actual-negatives-current.log` with SHA-256 `39d5558836036fec0e0bf9e24499ea737db46eee3781491c45f5d75bcb2fe8bd` and result `3 passed, 70 deselected in 66.80s`; the final full run is authoritative for the final source/test pair.

Supporting focused logs (all mode `0600`) are retained in `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-helper-final-integration-20261019`:

- control-preflight: `logs/control-current-2.log`, SHA-256 `a6c686d70d8cd82624103d995dca6ddc9ef54e5f094bf24e33155dc8fc27360d`, `1 passed in 26.51s`;
- ordinary recovery: `logs/recover-ordinary-current.log`, SHA-256 `0ac31443f4273adce9fa98b1c085e59800670eaa86a2c8df54c3bda39c25390c`, `1 passed in 18.50s`;
- restore recovery: `logs/recover-restore-current.log`, SHA-256 `265cdb98eddd498664cf77bbc34e079d9172974363b6416535d5d0d45a3bb6d8`, `1 passed in 18.37s`.

Static checks on the final bytes passed: Ruff check (`All checks passed!`), Ruff format check (`2 files already formatted`), Python `compileall`, and `git diff --check`. Import-origin verification resolved the helper and `crowley.session.cli`, `crowley.session.controller`, and `crowley.session.daemon` from the worktree paths listed in the companion freeze JSON.

## Cleanup, provenance, and limits

The final fixture `finally` paths close actor/listener/bridge/gate threads, FixedInput/watchdog, X11Screen, producer input tools, driver, and producer child. The suite passed its cleanup assertions. The private evidence directory `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-helper-final-integration-20261019` is mode `0700`; retained logs and result records are mode `0600`.

The real fixture uses the existing offline WoW Lua harness/addon bytes. A separate live `restore_pending` addon initialization defect is outside this two-file fence and remains separately owned; this report does not convert that live issue into helper evidence. No live GUI, addon, deployment, native promotion, or service acceptance is claimed. Three Python 3.12 multiprocessing fork deprecation warnings remain in existing OwnedEmitter tests and did not affect the zero return code.

This pair is ready for parent independent review and downstream Sol/Opus review.
