# Native helper final integration — evidence supplement

Status: **integration evidence incomplete; source/test pair frozen**.

This supplement records only retained evidence. It does not claim the required
post-measure public pause, fresh empty-ID recovery, ordinary reload, or full
R10d helper-suite result. The frozen owned pair was not edited in this stage.

## Frozen scope

- Worktree: `/home/dev/.cache/crowley/worktrees/native-helper-final-integration-20261019`
- Base commit: `c5e577200adadb8c158b1009643aa0f746d98753`
- Owned files:
  - `tools/native_calibration_operator.py`
    SHA-256 `ffc8ae4f2e338d36d521002e7de5d894c3876a06f621aca5166361055fa9b2e5`
  - `tests/test_native_calibration_operator.py`
    SHA-256 `d4834f543333a66e9bc9d31e150ef9e085195a27cc93656df5c8d81683fd8b48`
- The seven native files were treated as read-only R10d dependencies. Their
  current hashes are in the companion freeze JSON.
- No GUI, service, configuration, input, native-source, or Git mutation was
  made by this metadata-only supplement.

## Retained commands and results

### Prior causal helper suite (not the requested R10d integration run)

The only retained 66-test helper log is:

`/home/dev/.local/state/crowley/executor-evidence/helper-causal-parent-final-20261019/test.log`

- mode: `0600`
- SHA-256: `3c026e3f41c5881edfa0bafa83e6400fefd7a39471f2a40384b26443631effea`
- command: `/home/dev/repos/pegasus/.venv/bin/python -m pytest -vv tests/test_native_calibration_operator.py`
- result: `66 passed, 2 warnings in 188.77s`
- return code: `0`
- result record: `/home/dev/.local/state/crowley/executor-evidence/helper-causal-parent-final-20261019/result.json`, mode `0600`, SHA-256 `6dd76092bca5f48a92cd3db1da43f7079abcab0d966ae67e6727dd08c4a42fbc`

That run used the prior causal dependency set (for example controller
`81d377c4…` and daemon `b727b4df…`), not the current R10d set. It is retained
as historical helper evidence and cannot serve as the exact R10d integration
result.

The two warnings are both Python 3.12 `DeprecationWarning` messages from
`multiprocessing/popen_fork.py:66` about forking a multithreaded process. They
occurred in `test_owned_emitter_gate_and_release_subprocess` and
`test_owned_emitter_gate_eof_is_bounded`; both tests passed.

### Current R10d native smoke artifact

The retained current-dependency artifact is:

`/home/dev/.local/state/crowley/executor-evidence/native-r10d-parent-final-20261019/test.log`

- mode: `0600`
- SHA-256: `80bdb2857970389fe25cd01273bf7b0a1d689bf54f5b893e210e6d87165141a2`
- command wrapper: `/home/dev/.local/state/crowley/executor-evidence/native-r10d-parent-final-20261019/run.py`
- the wrapper selected two native regression nodes and opened the log with mode
  `0600`; no `result.json` or terminal return code was retained
- this is not evidence of a passing integration suite and is not reported as
  one

No retained focused integration command exists for the requested extension.
The existing actual composition test ends after the successful measure state;
it does not continue through public pause, fresh recovery owners, Restore,
ordinary reload, and fresh normal publication.

## Requirement map

| Requirement | Retained test/evidence | State in this stage |
| --- | --- | --- |
| Actual construct/held/updates 1..99/held100/resume/finalized sequence | `test_actual_operator_measure_composes_x11_screen_daemon_and_agent` in prior 66-log | historical prior-dependency evidence |
| Actual INPUT_CALIBRATION and native calibration outcome | same test in prior 66-log | historical prior-dependency evidence |
| Public pause to a newer PAUSED/Guardian generation | no test in current frozen pair | not run |
| Fresh production X11Screen/FixedInput/Watchdog/OwnedEmitter recovery owners | no test in current frozen pair | not run |
| Empty-ID public MODE_RECOVER through actor | standalone recovery tests exist, but no continuation from the actual composed success | not the requested integration proof |
| ACK-dispatched Restore and ordinary SavedVariables lifecycle | no post-success continuation in current composed test | not run |
| Role from actual pointer target and available control | current composed test still uses its pre-integration role path | not demonstrated |
| Newly rendered ordinary boot PNG and normal0/fence inactive | no post-success ordinary reload in current composed test | not run |
| Checkpoint consumed, native calibration true, input calibration false, Guardian unarmed, no leaks | no post-success integration assertion set | not run |
| Full exact R10d helper suite with retained raw log | no retained result/log for this worktree | not run / unavailable |

The prior causal suite did retain cleanup assertions for its own measure and
reply-loss cases. Those assertions do not establish the missing post-success
recovery lifecycle.

## Provenance and limitations

The helper and test import from the frozen worktree; `crowley.session.*` would
resolve through that worktree's `src` when invoked with its explicit `PYTHONPATH`.
The prior causal run used private per-test temporary roots. No XDG override,
current R10d integration log, post-success receipt, or full cleanup receipt was
retained for this stage. The absence is recorded rather than inferred.

The pair remains offline development evidence only. It does not qualify live
UI geometry, addon behavior, native dependency promotion, or deployment.
