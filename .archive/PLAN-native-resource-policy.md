# Separate native correctness from whole-client resource targets

Status: USER AUTHORIZED 2026-10-19 20:07UTC: proceed with the recommended
resource-policy separation and qualification steps. Sol plan review READY,
no Must-Fix. Assisted collection continues while implementation/review runs.

## Decision

Separate resource performance from protocol qualification. Keep construction128MiB
and updates16MiB as exact recorded whole-WoW targets. An overage is always
`target_exceeded`, never a resource pass. Operation with that unresolved
performance overage is permitted only after all independent correctness and
input gates pass. Do not choose a larger limit, substitute netRSS, or subtract
the unmatched ordinary sample.

Evidence: live40 and43 reached accepted held100, then failed update peaks of
48,644,096 and20,414,464 bytes against16,777,216. FinalRSS fell in both runs.
Ordinary passive RSS varied91,168,768 bytes over109s. Those facts do not prove
addon attribution, a persistent leak, or an acceptable resource peak. Diagnostic
late16 texture counts were2048; late p99 about23ms; metrics cannot rule out an
earlier transient. See native-memory-failure-gen40/gen43-parent-verification.json
and ordinary-scan123-passive-memory-parent-verification.json.

## Authorized implementation fence

Only production calibration.py, controller.py, daemon.py under src/crowley/session;
only tests/test_session_native.py, tests/test_session_runtime.py and
tests/test_session_native_regressions.py. No driver, helper, addon, protocol
command, lease, Guardian, input, configuration or service-definition changes.
Work in a new isolated worktree from8277ec1 or a descendant with exact source pins.
Root owns Git and live promotion. Luna implements; Sol and actual CLI Opus review.

1. Preserve NativeMemoryMeasurement.verify: exact reset5 method, PID/start/UID/
   executable identity, phases, timestamps, ordinal1..100, growth formula and
   exact128/16MiB targets remain mandatory. Missing/invalid measurement fails.
   Add a frozen resource assessment derived only from both verified measurements:
   within_targets or target_exceeded, exact growth/target bytes, recomputed result.
2. Change only the over-target branch in LinuxProcStatusVmHwmReset5.finish_window.
   Before returning an exceeded measurement, require an owned, durable, typed
   archive receipt with exact measurement/identity/assessment binding. Missing
   callback, archive failure, wrong receipt or identity drift remains a hard error.
   Use assessment-specific receipt/hash semantics and a new private
   native_memory_assessments archive kind; do not call a new overage rejected or
   reuse native_memory_failures outcome IDs. Canonical receipt domain includes
   {kind:native_memory_assessments,schema:1,classification:target_exceeded,
   measurement:exact_to_dict}; verify its outcome hash and measurement digest.
   Sol confirmed Journal.append_archive accepts this safe kind without edits.
3. Remove only threshold-overage rejection from NativeCalibrationEvidence.verify.
   Retain measurement validity, limits, phase ordering, seal/hash and identity
   bindings. Derive resource_assessment from the hash-covered measurements; never
   accept a caller-supplied classification. Runner still completes100publications,
   held100, normal0 resume, cadence/CRC/boot/sequence/P99/construction-time/artifact
   and cleanup guards. Unavailable reset or archive failure still recovers/fails.
4. Controller records the verified assessment atomically with native evidence in
   the existing transaction; failed writes roll back. Native correctness success
   advances only to INPUT_CALIBRATION. Guardian/input stay unarmed until genuine
   physical-input calibration and the ordinary operational gates pass.
5. Add bounded public nativeResourceAssessment with classification
   within_targets/target_exceeded/not_measured, method, evidence hash and both
   phase growth/target/withinTarget facts. Derive current from valid current
   native evidence, invalidation and replacement-operation state. Restart or
   invalidation leaves historical evidence current:false and requires fresh
   native calibration. Missing/malformed legacy data is not_measured, never pass.

## History and compatibility

Do not rewrite, delete or relabel old native_memory_failures, especially40/43.
Those were real failures under the installed old contract. Preserve their raw
bytes/hashes. Do not backfill either failed run into a new qualification. Require
fresh full native evidence after reviewed promotion. Bind changed evidence and
assessment semantics so old stored assertions cannot silently rearm a session.
Old structurally complete measurements may support a historical assessment;
that does not make old/invalid calibration current. Existing RPC commands stay.

## Verification and live acceptance

- Exact target and target+1 classification for both phases; alternate limits,
  malformed measurement/receipt and forged classification hard-fail.
- Actual meter/runner overage continues only after the exact durable assessment
  receipt, then completes held100/resume0/seal/artifact cleanup. Archive/reset/
  capture/identity/cadence/P99/construction-time negatives retain causal errors.
- Controller atomic persistence, native-to-input transition and Guardian-unarmed
  behavior; invalidation/restart cannot rearm from historical assessment.
- Existing failure archives remain readable and unchanged; legacy status is
  derived or not_measured. Status cannot mislabel target_exceeded as resource pass.
- Focused tests plus relevant native/runtime/regression suites, scoped static
  checks and one exact compiled100 integration. Parent reproduces decisive gates.
  Do not repeat the unchanged seven-case timing model absent changed timing paths.

After Sol/actual Opus approval and parent verification, finish the active ordinary
scan/ACK/reopen, obtain fresh quiescence, promote exact pins and restart. Run one
fresh native100 under the selected explicit policy. Verify native correctness,
resource classification and canonical ordinary recovery separately. Only then
request human input calibration, followed by three autonomous900s full cycles.
A target_exceeded result remains visibly over target even if correctness passes.

## Exact implementation checks

Create an isolated worktree from current HEAD948ff2c (or descendant with identical
source) and a private editable environment; prove imports resolve to that worktree.
Run focused resource/memory/assessment tests first. Then run:

```text
uv run pytest -q tests/test_session_native.py tests/test_session_runtime.py tests/test_session_native_regressions.py -k 'not native_update_fast_trace_replay' --tb=short
uv run pytest -q 'tests/test_native_calibration_operator.py::test_actual_operator_measure_composes_x11_screen_daemon_and_agent[success]' --tb=short
uv run ruff check src/crowley/session/calibration.py src/crowley/session/controller.py src/crowley/session/daemon.py tests/test_session_native.py tests/test_session_runtime.py tests/test_session_native_regressions.py
uv run ruff format --check src/crowley/session/calibration.py src/crowley/session/controller.py src/crowley/session/daemon.py tests/test_session_native.py tests/test_session_runtime.py tests/test_session_native_regressions.py
git diff --check
```

Keep full private0600 logs and0700 evidence directory, exact six-file hashes,
unchanged driver/helper/operator-test hashes, and retained fixture receipts.
No live kernel accounting writes, desktop input/captures, services, configuration,
DB mutation, Git commits/resets/stashes, or edits outside the six-file fence.
Owned harmless-process fixtures and private compositors are permitted.
No new native live run until parent verification plus Sol/actual Opus approval.
