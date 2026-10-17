# Runtime live instrumentation: Sol source review R2

This was a read-only source review of the frozen successor at
`/home/dev/.cache/crowley/worktrees/runtime-instrumentation-r2-20261017`.
I did not edit the candidate, run tests, execute the harness, use Git, or access
the game, GUI, network, database, or any live runtime. The only file I wrote is
this report.

## Identity and scope verification

The supplied review artifacts match exactly:

- `.archive/executor-review/runtime-live-instrumentation-r2-freeze.json`:
  `2b05273751940da904fcde48e08ebdd922ba198e8254b0ce18c907bad77cb773`
- `.archive/executor-review/runtime-live-instrumentation-r2-parent-delta.diff`:
  `379f7d22f16bbb033bc7401567a571d4fba5dbcc72bb8c79bb31ad35bcc88a40`
- `.archive/PLAN-runtime-live-instrumentation.md`:
  `a563e4df1450eaac3cb44b87fb3143a823bbed5b23f4209d168703a010a0bb62`
- prior Sol R1 report:
  `43462d2c35921b16d3580c1242ae139bd85c5c730a5e430f523f7c2704a24257`
- actual Opus R1 report:
  `2c7e53cff23da0dc30e7ee374b099c810e450c4128e2bf23a7d8df4c81219e80`

The four frozen candidate hashes match the freeze:

- `src/crowley/session/driver.py`:
  `fc257a6dbe579a350aa4a774a5fdee65bf6e0878c7c6d01c6f22ab055b56cd30`
- `src/crowley/session/daemon.py`:
  `52779e13442bab071a320141377be1ad80547983d7213476a0f571fd82753942`
- `tools/gnome-telemetry-region/offline_harness.py`:
  `e2fb79049c46b1784a1dfb9e4db0df03c3e30756c49a3c5b2a987787953ef6f2`
- `tests/test_session_native.py`:
  `879061130591a916c09d72d86d95c6608154faa7a4819c27571d6b210508f465`

The accepted evaluator remains byte-identical at
`c46cae849058005e9b7387ef95c34f40f376afb5477739efaf6f40f6a36ebd8c`,
its tests at
`c998aa4a9ff67ba67ddeab05a0e5a0cfa5273a296909e0b07cb79a3d06dd313a`,
and its documentation at
`54237c344ef0faa3392cca6fe82b75f1f986bbf697c81d3f34493b2f00e1caca`.
The inspected change remains inside the authorized four-file fence. Parent
reports 71 focused checks passing in 29.70 seconds, plus the harness self-test,
self-check, Ruff, formatting, compile, and diff checks; I did not rerun them.

R2 closes the R1 counter-baseline overwrite, post-decode CPU lifecycle, final
source-read failure, descriptor replacement, Guardian cleanup projection,
request-clock placement, module-origin, and ordinary success-to-evaluator gaps.
It also preserves the adjudicated full CPU interval when strict decode returns
successfully but a later required validation fails. The following remaining
paths still violate the frozen contract.

## Must-Fix

1. **A pre-sample config mismatch still reports the requested semantic hash as
   the owner's actual loaded config.**

   - Files: `tools/gnome-telemetry-region/offline_harness.py:1467-1475,1503-1511`
     and `src/crowley/session/daemon.py:3997-4018,4053-4073`
   - The daemon failure record truthfully exports top-level
     `owner_config_semantic_sha256`. The harness fallback copies only
     `config_file_sha256` and `config_semantic_sha256`, then falls back from the
     absent owner field to the request semantic hash. The real config-mismatch
     path can therefore claim the owner was bound to the changed request even
     though the owner rejected precisely because its loaded config differed.
     The real mismatch regression at `tests/test_session_native.py:2312-2325`
     checks only digest lengths and does not expose the false owner binding.
   - Correction: copy the daemon's actual owner semantic hash into the failure
     projection and never substitute the requested semantic hash for a missing
     owner observation. Treat a missing actual owner hash as null/malformed.
     Feed the genuine mismatch receipt through the unchanged evaluator and
     assert binding mismatch rather than favorable echoed binding.

2. **The harness no longer enforces the existing exact owner-IPC response and
   request-binding protocol before trusting the response as owner evidence.**

   - File: `tools/gnome-telemetry-region/offline_harness.py:1701-1742`
   - `response.get("ok") not in {True, False}` admits integers `0` and `1` as
     booleans. A success may include any combination of `error` and `failure`;
     a failure need not include a string error or an exact field set. The
     failure object is projected before its exact schema, generation, request
     config, and actual owner-config binding are checked. Only an optional
     producer-attempt subobject and optional sample are validated. This is
     weaker than the accepted R6 input fence and lets malformed or cross-request
     failure metadata become a normal schema-2 owner record.
   - Correction: require `ok is True` or `ok is False`; require exact success
     and failure outer shapes; validate the complete current failure shape and
     generation/config/owner-config request binding before `_live_owner_evidence`
     consumes it. A malformed response must remain an owner-IPC protocol
     failure, with no trusted owner projection. Add focused wrong-type,
     extra-field, and cross-request failure regressions.

3. **Clean failures before producer admission emit `attempt_retired: null`, so
   the unchanged evaluator refuses the receipt instead of retaining a
   well-formed ineligible failure.**

   - Files: `src/crowley/session/daemon.py:3739-3748,3835-3845`,
     `tools/gnome-telemetry-region/offline_harness.py:1522-1548`, and
     `tests/test_session_native.py:2139-2185`
   - The daemon initializes a not-started attempt with null retirement and
     retains that value after an identity or config rejection, even when its
     final cleanup snapshot proves there is no process, group, or attempt
     directory. The harness passes the null through. The accepted evaluator
     requires each of the four cleanup fields to be an observed boolean, so the
     actual identity-before-capture receipt asserted at test line 2177 is
     structurally refused as `cleanup_invalid`. This misses the plan's exact
     cleanup schema and well-formed failure retention.
   - Correction: define the no-producer-start terminal case from the daemon's
     final cleanup evidence and export a truthful boolean for the condition
     that no attempt remains; do not make the observer guess. Evaluate the
     genuine identity and config rejections through the unchanged evaluator and
     assert retained, ineligible outcomes rather than schema refusal.

4. **Interruption while waiting for a fixed target bypasses the run finalizer
   and writes an invalid failed lifecycle.**

   - File: `tools/gnome-telemetry-region/offline_harness.py:1624-1638`
   - The target sleep is outside the attempt `try/finally`. On
     `KeyboardInterrupt`, `SystemExit`, or another `BaseException`, this branch
     writes `run_state: failed` and raises immediately, without an attempt for
     that target and without the final observer source snapshot. With no failed
     attempt (zero attempts or only earlier completed attempts), the unchanged
     evaluator refuses the run as `attempt_lifecycle_invalid`. This is the
     remaining reachable case behind the R1 run-level-finalization finding.
   - Correction: route target-wait termination through the common source-hash
     and receipt finalizer. Because the next attempt has not begun, preserve the
     shorter run as `incomplete`; create a failed attempt only after its actual
     start boundary exists. Add a target-wait interruption regression that
     validates the resulting receipt with the unchanged evaluator.

5. **Attempt 7 stamps sample completion before its required final status check
   and never reapplies the one-second completion deadline afterward.**

   - File: `tools/gnome-telemetry-region/offline_harness.py:1828-1850`
   - `sample_completed_monotonic`, its deadline test, and completion cadence are
     recorded before the final same-generation paused-status request. A slow
     final status may cross `target + 1.0` while the persisted completion clock
     remains inside the deadline; a final-status failure also leaves a
     completion timestamp even though the later required sample boundary was
     not reached. This conflicts with the plan's rule that completion is
     stamped only at the later actual completion boundary and makes attempt 7's
     timing unlike the work required to complete it.
   - Correction: perform and validate final status first, under the original
     target deadline; then stamp sample completion and apply the same deadline
     and cadence checks. A final-status failure must leave completion null. Add
     a delayed final-status regression that crosses the fixed deadline without
     rebasing the target.

## Should-Fix

1. **A client-side PNG publication failure is still mislabeled as owner IPC.**

   - File: `tools/gnome-telemetry-region/offline_harness.py:1682,1746-1760,1851-1855`
   - The phase remains `owner_ipc` after a valid owner sample has been checked
     and while `_atomic_private_png` publishes the client copy. A filesystem
     failure in that call therefore emits `owner_ipc_failed`, despite the
     accepted finite schema containing the exact
     `png_publication/png_publication_failed` outcome. This was an explicit R1
     failure-classification gap and remains reachable.
   - Correction: set `phase = "png_publication"` immediately before the atomic
     client write, and retain a regression that forces that write to fail after
     a valid owner response and verifies the exact persisted phase/reason.

## Nits

None.

No schema-2 collection, performance threshold, or Rust decision is qualified
by this review. The candidate should remain unreleased until the failure
evidence and final timing boundary above are corrected and reviewed.

STATUS: NEEDS WORK
