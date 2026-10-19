Model ID: `claude-opus-5-5`

# Source review: native identity budget and pre-ACK alignment (Opus R1)

**What I checked:** I confirmed the worktree and all six source pins and three plan pins in `review-input.json` against `sha256sum`. HEAD is `1cbaadf`, and I reviewed the working-tree delta against it. I read all three plans plus the alignment amendment, and the accepted Sol R1 JSON. I did not edit, run tests, capture or touch services, and I did not create a plan file.

**Confirmed correct:**
- **Lock order:** the final admission takes controller → construction → Guardian, then `dispatch_ack_once` takes the backend `_process_lock`. That matches the existing `admit_observer` → `observer_dispatch_admission` → `spawn_gated` order, and I found no path that takes the process lock first and then the Guardian lock.
- **Wait loop:** it sleeps in chunks of at most 50 ms with no authority lock held.
- **Health check:** `admission_gate_ready()` is nonblocking and raises; `_watchdog_state()` is not called.
- **One-shot ACK:** the one-shot flag is set before `sendall`. No dispatch or a failure before dispatch raises with zero ACK. A double dispatch or a failure after dispatch gives at most one ACK and publishes no receipt.
- **Eligibility is closed:** both the runner and the daemon read `driver.native_measurement_provider`. A wrapped or custom provider therefore keeps the outer resolve, the deferred-owner validation and the poll resolve.
- **Checks kept:** `_native_update_capability_matches_locked` covers everything `_native_construction_validate_snapshot` checked except the removed full resolve. The backend-pre, backend-post and runner-post resolves are unchanged.
- **Timing origin:** S1 comes from the eligible update-1 receipt's `capture_started`; deltas use decoded uptime and `unsigned_delta`; the anchor is cleared on exit, close and refusal.
- **Generic callers:** the new `_pre_ack_admission` keyword is only passed when it is present.

## Must-Fix

1. **`src/crowley/session/calibration.py:4892-4905` — Sol R1 M1 is not closed: the held/100 notification fires before the resume-required checks.**
   - **Defect:** `diagnostic.mark_release(final_path)` runs at line 4898. That is before the `notify_native_resume_required` callable check and before `resume_required(identity, boundary)` at line 4905. That call is where the daemon actually checks the controller state, re-verifies the sealed boundary and its identity/phase binding, and checks deferred `measure_ready` ordering.
   - **Reachable failure:** a stop or pause, or an out-of-order deferred callback, between held/100 acceptance and that callback. The observer and the persisted failure payload have already recorded held/100 as an accepted `retained` terminal. The runner then fails, and its `finally` deletes `final_path`. The later `release_native_capture` → `mark_release` call is ignored because `_current` is already `None`. The diagnostic keeps reporting `retained` for evidence that was rejected and deleted.
   - **Missing test:** Stage A.1 required a "subsequent failure cleanup" test, and no new test covers it. The compiled-100 test only proves the success ordering.
   - **Correction:**
     - Move the `mark_release` call to immediately after `resume_required(identity, boundary)` returns and before `provider(identity, "resume", 0)`.
     - Add a test where resume-required rejects: there must be no `retained` notification, and the attempt must end `released`.
     - Add a test where the resume provider fails after notification: the image must be removed, the notified path/hash kept, and owned captures cleaned.

## Should-Fix

1. **`tests/test_session_runtime.py:3421` with `src/crowley/session/daemon.py:2246` — the reduced-mode baseline fails because of the test stub, not naturally.**
   - **Defect:** `daemon._native_update_alignment_wait = lambda **_: None` never sets `anchor["waitingOrdinal"]`. The final admission therefore always raises "native pre-ACK alignment anchor was replaced" at update 2, with zero ACK.
   - **Effect:** `reduced["error"] is not None` passes trivially. The parent's "old/reduced/aligned characterization passed" is not evidence of the natural duplicate or overrun the plan requires.
   - **Correction:** disable alignment through a seam that keeps the production binding intact. For example, run the real wait with the target forced to now, or skip only the sleep. Then report the duplicate or budget outcome that actually results.

2. **`tests/test_session_runtime.py:2915, 3435-3447` — the timing model drops a measured cost and does not simulate retry sleeps.**
   - **Dropped cost:** the named `poll_backend_glue` (0.167 ms) is never charged in any mode. Its only charge site is the `elif charging:` branch of `virtual_sleep`, which is unreachable because `_native_alignment_sleep` is only called inside the tracked alignment wait.
   - **Retry sleeps:** the provider's retry sleeps (`time.sleep(_NATIVE_POLL_INTERVAL_SECONDS)`) bypass the virtual clock entirely. Retry timelines in the negative and old cases are compressed by 50 ms per retry.
   - **Impact:** no outcome flips (the positive maxima become about 889.08 ms). But this is the dropped-residual defect the earlier candidate was rejected for.
   - **Correction:** charge `poll_backend_glue` at the provider-to-backend-pre edge. Advance the virtual clock for the provider poll sleep without counting it as active work. Delete the dead branch.

3. **`tests/test_session_runtime.py:1208-1278` — the M2 substitution test cannot catch the regression it is meant to guard.**
   - **Defect:** it calls `_native_update_alignment_record` directly and only substitutes `backend.last_region_receipt` afterwards, with the same timestamp. A reintroduced reread of `last_region_receipt` inside the provider would still pass.
   - **Status:** the M2 source fix is correct. The receipt is read once in `_capture_native_frame_with_capture` and passed by value into the record at `daemon.py:5387-5397`.
   - **Correction:** drive the real `_native_measurement_provider` for an eligible update. Substitute a receipt with the same digest but a different nonce and timestamps at a barrier after the capture seam (for example in `provider_decode` or `copy`). Assert the anchor keeps the original nonce and `capture_started`.

4. **An existing regression test was deleted with no replacement.**
   - **What was lost:** `test_runtime_native_observation_couples_provider_and_runner_spans` (base `tests/test_session_runtime.py:2335`). Its body was overwritten in the hunk that is now around line 3706. It covered provider/runner span attribution, `release_outcome == "released"`, clearing `_current`, and run-span attribution of `identity_pre_provider`.
   - **Why it matters:** this delta changes `mark_release` and `finish_attempt`, so this is exactly the coverage to keep. The plans do not authorise removing it.
   - **Correction:** restore it, adjusted only if a contract genuinely changed.

5. **`tests/test_session_native.py:1965-1988` — the typed compiled matrix is missing a named Stage C case.**
   - **Defect:** there is no case for "unresolved release/input ownership". The final admission's `guardian.held`, `active_process_groups` and `_release_failed` refusals at `daemon.py:2272-2280` are never exercised with a producer waiting for ACK.
   - **Correction:** add a typed case that sets one of these at the pre-ACK barrier. It should assert zero ACK, no ScreenshotArea entry under the armed marker, and empty registries.

6. **`src/crowley/session/daemon.py:5252-5270` — the new `DriverError` retry branch changes behaviour on paths that were meant to stay unchanged.**
   - **Defect:** for `construct`, any `DriverError` once `now >= capture_deadline` now becomes a `no_change` retry. For every other stage the same happens if the message contains `"deadline"`.
   - **Effect:** construct, held, resume and nondeferred callers previously failed when a capture attempt hit its 15 s producer bound (for example under GNOME capture-lock contention). They now retry silently until 30 s. Retryability is decided by matching error text, which conflicts with the no-fallbacks rule. Unrelated errors are also recorded as `no_change` in the diagnostic.
   - **Correction:** keep only the mapping that is needed: if `now >= frame_deadline`, break to the canonical "did not produce the requested fresh frame" refusal. Otherwise re-raise.

## Nits

1. **`tests/test_session_native.py:2237-2245, 2355` — expiry clauses are not tested independently.**
   - All five final-lock cases pass `typed_deadline == final_lock_expiry`, so the `deadline` check always fires first. The operation, reservation and capability expiry clauses are never the deciding check.
   - `cap-expiry` is set up identically to `reservation-expiry`.
   - To test the operation-deadline clause on its own, give it a later `typed_deadline` and shorten only the operation deadline while the final lock is contended.

2. **`tests/test_native_calibration_operator.py:5334-5353` — the compiled-100 gate wraps a production method.**
   - The success gate replaces `_native_update_alignment_pre_ack` with a pass-through recorder that reads the mutable `last_region_receipt`.
   - It would be better to use the per-attempt `ack_admission` / `alignment_target` spans the diagnostic already records, and to assert the anchor's `originCaptureStarted` equals update 1's receipt `capture_started`.

3. **`tests/test_session_runtime.py:3657` — count assertions are weak.**
   - The model asserts `capability_match_calls >= 4 * 99`, and nothing about `ack_admission` or `alignment_target` counts.
   - Exact per-transition counts are only kept in the timeline JSON. Asserting one of each per eligible update-2..99 attempt, and one `owner_validation` per old-mode attempt, would pin M4.

4. **No test exercises the wait loop mid-sleep.**
   - Nothing revokes or expires between real sleep chunks, or checks that the authority locks can be acquired during a sleep.
   - The faults are injected at the pre-wait barrier instead. The source is correct by inspection, so this only affects test coverage.

## Sol R1 closure

| Finding | Status | Notes |
|---|---|---|
| M1 | Open | Notification is placed before the resume-required checks, and the failure-cleanup test is missing (Must-Fix 1). |
| M2 | Source closed | The test does not exercise it (Should-Fix 3). |
| M3 | Closed | One per-attempt deadline, `min(frame, attempt+15 s, operation, reservation, capability)`, reaches the driver and the pre-ACK step unchanged. The shutdown/expiry recheck runs under the Guardian lock after contention, and the driver rechecks under its process lock. The new retry branch is a separate regression (Should-Fix 6). |
| M4 | Mostly closed | Old-owner 142.073 ms charge and separate 0.500 ms final-ACK admission are in place, and phase951 refuses naturally with "returned". Model fidelity gaps remain (Should-Fix 1–2). |
| M5 | Mostly closed | Entry marker is armed, the origin comes from decoded Agent bytes, and the matrix and cleanup are exact. The release/input-ownership case is missing (Should-Fix 5). |

STATUS: NEEDS WORK
