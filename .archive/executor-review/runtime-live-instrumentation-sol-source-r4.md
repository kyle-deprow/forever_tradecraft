# Runtime live instrumentation: Sol R4 closure review

This was a read-only review of the R3-test-closure to R4 delta in
`/home/dev/.cache/crowley/worktrees/runtime-instrumentation-r4-20261017`. I
reviewed only the changed daemon, harness, and focused tests. I did not edit the
candidate, run tests, use Git, or access any runtime, game, GUI, network,
configuration, or model service. The only file I wrote is this report.

## Identity and scope

- R4 freeze:
  `0d2fbfe43079d58a0216aded1895209831083f238e0bc8759678c81f1c2dcad7`
- Closure delta:
  `625074838a0071ef34a32e7ae774572485b89a837746cc4450fce7c826bfdbb5`
- Review prompt:
  `a36ed7f91b10b877c48120ff25bdd88026c82c8006f4d1917ca67cb76e34b972`

The four frozen candidate hashes match the freeze:

- `src/crowley/session/driver.py`:
  `fb907096007e10ed59f67dceb52dd20a3e54c37ff02e011d21c61f292806938d`
- `src/crowley/session/daemon.py`:
  `69678fdcd4963ffeb38dd31441cf0074713baf5b95747da3383e90892636073f`
- `tools/gnome-telemetry-region/offline_harness.py`:
  `f682d85636b0073a8fd7e8330a6ae06ba7542d2cb9b7ccc74a1304ea856d7716`
- `tests/test_session_native.py`:
  `c47d2bdeebcb2079f24fb901caeb6c54c568fdf607c33eed217ebf20721dd846`

The driver and all three accepted evaluator files are unchanged. The evaluator
pins remain `c46cae849058...`, `c998aa4a9ff6...`, and `54237c344ef0...`.
Parent reports 66 focused checks passing in 62.58 seconds plus Ruff, formatting,
and diff checks; I did not rerun them.

## Closure assessment

- `offline_harness.py:1918-1961` persists the bounded refusal before validating
  its optional owner metadata, accepts the genuine simple `ok:false,error`
  SessionIPC shape without inventing owner evidence, and checks a valid durable
  refusal's IPC return deadline before validating or publishing its returned
  sample. A late refusal therefore retains its original private record while
  schema 2 truthfully records `deadline/sample_deadline_missed`.
- `offline_harness.py:1086-1090` classifies a malformed producer API/branch/
  rectangle object as `producer_binding`, rather than misreporting runtime source
  drift that would poison the whole collection.
- `daemon.py:3976-3992` performs the final source rehash before taking the final
  model-counter snapshot. A model call overlapping that verification remains in
  the sample delta. The subsequent response clock retains its documented
  content-ready-before-fsync meaning.
- The focused composed test uses the harness-local forwarding clock only. It
  now proves the late-refusal boundary, exact identity reasons and whole-report
  outcome, delayed and thrown final-status behavior through the public evaluator,
  all four real model wrapper transitions, and a genuine concurrent model call
  persisted by the owner and rejected by the independent-binding public report.
  No receipt counters are rewritten by that concurrency regression.

The delta preserves the original one-second targets/deadlines, nullable
completion semantics, private failure evidence, cleanup behavior, and unchanged
accepted evaluator. I found no causal regression or remaining closure defect.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

This review qualifies the frozen R4 source closure only. It does not qualify a
live schema-2 collection, the performance decision gates, or a Rust rewrite.

STATUS: READY
