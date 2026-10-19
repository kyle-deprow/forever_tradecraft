# Native Guardian-generation R10 closure

This bounded R10 candidate is frozen in
`/home/dev/.cache/crowley/worktrees/native-guardian-generation-r10-20261019`
at base `6dade3ea22c70f97d52fa768d4199440dda6e275`. The writable fence was
`src/crowley/session/daemon.py`, `tests/test_session_native_regressions.py`,
and the required existing-fixture additions in `tests/test_session_native.py`.
Controller, CLI, transitions, and runtime files remained read-only; their exact
base and final bytes are recorded in `native-guardian-generation-r10-freeze.json`.

The daemon now records the original Guardian generation when a provisional or
recovery owner is created, carries that fact through private capabilities and
recovery tickets, and compares it to the live Guardian generation under the
actual Guardian lock immediately before producer admission. Snapshot validation
also performs an independent live-generation comparison; an existing owner
without an original generation fails closed, while only a truly ownerless legacy
context may sample the current generation.

The regression fence now asserts that an old complete/error worker cannot alter
a successor record after the old worker joins, including while the successor is
still `starting`. It exercises the public input start through its own `running`
record to a controlled worker error, keeps cross-kind `starting` refusal, rejects
recovery restart over a live reservation, and covers live Guardian-generation
drift. The existing real-daemon route test again proves configured NATIVE state
refuses a non-X11 backend before the PAUSED/STOPPED checks.

The required compiled proof is
`tests/test_session_native.py::test_compiled_private_owner_guardian_generation_revoke_orders`.
Both parameter cases use the authentic pinned Codex 0.162.1 fixture, private
Shell/Xvfb/D-Bus, real `X11Backend`, real configured producer and Guardian
process admission, and the public `SessionDaemon` owner/preflight path. The
fixture first executes a real configured `NATIVE_CALIBRATION` producer capture,
then exercises revoke-before-admission and admission-before-revoke in PAUSED.
The `/bin/sleep` Guardian test remains supplemental unit coverage and is not
used as the compiled producer proof.

The final production-source three-suite command was:

```
XDG_RUNTIME_DIR=<private-0700> PYTHONPATH=src \
  /home/dev/repos/pegasus/.venv/bin/pytest -q \
  tests/test_session_native.py tests/test_session_native_regressions.py \
  tests/test_session_transitions.py --disable-warnings
```

It produced `367 passed in 532.50s (0:08:52)` with exit code 0. The retained
0600 log is
`/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-guardian-generation-r10-20261019/full-native-three-suites-r10-final2.log`,
SHA-256 `7b7159af509e1f4677fcd2ea45159feee052771fa94ea73343e67e21c2a2aa9b`.
The named runtime command produced `1 passed, 14 deselected in 0.49s`; its
0600 log is
`/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-guardian-generation-r10-20261019/named-runtime-meter-r10-final.log`,
SHA-256 `98adba2037388c345f62033bab6d5b12884b5b088a9249481e4491d0c767e284`.

After the final suite, formatting changed only layout in the regression test;
no production byte changed. The mapped final-byte focused command then
produced `14 passed in 72.11s`; its 0600 log is
`/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-guardian-generation-r10-20261019/focused-r10-postformat.log`,
SHA-256 `c9d0f58c908c500bfd5d0b4d1941a21fdaac83656a6c2927ea7a44ae18bea66e`.
Final scoped Ruff format, Ruff lint, compileall, and `git diff --check` all
passed; the 0600 log is
`/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-guardian-generation-r10-20261019/static-r10-final2.log`,
SHA-256 `1d05080bb10c2a4ba07d816f65aba3a504f17239e50190eafed94cfefbb889c0`.

The earlier candidate run is retained as superseded evidence: `362 passed,
3 failed in 558.78s`. Its failures were the two durable-write cases and the
composed Guardian-drift case under the pre-correction source/test bytes. Both
durable cases pass independently (`2 passed in 43.52s`), and the composed
Guardian case passes independently after preserving the established
`binding changed` error contract (`1 passed in 21.74s`). The final2 run is the
authoritative broad result.

The authentic private CLI was
`/home/dev/.cache/crowley/codex/0.162.1/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex`,
version `0.162.1`, SHA-256
`628e35487d888a28f0427fc37501da529dd3d81fcbad7a2c3421c1e8670d92e1`. No live
capture, deployment, promotion, native100 qualification, or GUI input was
performed. Parent verification and independent Sol/actual-Opus review remain
required.
