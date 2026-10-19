Model ID: `claude-opus-5-5`

# Opus R2 source review: native ACK correction (R7 → final)

The production source in this correction is correct: no Must-Fix. One new test fault can feed a fake process-group ID into the real watchdog's SIGKILL list, and that should be fixed before this candidate is accepted.

**What I checked**
- **Pins:** all six final source hashes and all six R7 hashes match `review-input.json`. The R7 pins match the `native-identity-budget-20261019` worktree. The MAIN plan hashes match their pins.
- **Diff:** applying `correction.diff` to copies of the R7 files reproduces all six final hashes exactly.
- **Inputs read:** Opus R1 review, R1 arbitration, Sol R2 JSON, and the closure plan's "Source review R2", "Actual Opus R1" and "Final verification scope clarification" sections.
- **Read-only:** I made no edits, ran no tests, touched no services or GUI, and created no plan file.

**Evidence status**
- **Parent-reproduced:** focused tests (9 passed, then 2 passed) and the static checks.
- **Still pending per `review-input.json`:** parent reproduction of the matrix, the seven-case model, the baseline and exact compiled100.
- **Worker-reported only:** model PASS (1085/98/98/99 charges), baseline (old refuses at update 4; reduced accepts 99 with a 1435.161 ms maximum), compiled100 PASS (log sha `7a3e65c7…`).
- None of this is live qualification. The receipt tests replace the capture seam with a model; compiled100 covers the real producer separately; neither is a concurrent real-C-producer race.

## Confirmed in source

**Per-call receipt**
- The driver keeps a local `finalized_receipt` and replaces it with the post-retirement value in `finally` (`driver.py:3291-3294`).
- It hands that receipt to the sink only after the cleanup snapshot, with no lock held (`driver.py:3309-3310`).
- On the eligible path the daemon consumes only the single receipt handed off by that call. A missing or duplicate handoff is refused (`daemon.py:4985-5008`).
- The provider passes that receipt by value to the record step, which still requires `attempt_retired is True` (`daemon.py:2320`, `:5410-5420`).
- A same-digest global replacement cannot become the origin.
- `_receipt_sink` is forwarded only when `native_capability` is set (`daemon.py:4974`, `:6226`; `driver.py:6671`). Eligibility requires an exact `X11Backend` and the daemon's own provider (`daemon.py:1875`, `:1884`), the same gate `_pre_ack_admission` already uses.
- The generic and other callers never forward `_receipt_sink`, and every fenced override accepts `**kwargs`.

**held/100 ordering**
- `_publish_resume_required_boundary` (`calibration.py:4282-4297`) keeps base's callable guards, order and messages.
- It calls `resume_required` before `mark_release`, and the resume provider follows immediately (`:4913-4915`).
- `notify_native_resume_required` never touches the diagnostic, so the still-current held/100 attempt is the one marked.
- If the callback rejects: the original error propagates and the `finally` releases the capture as `released`.
- If the resume provider fails after notification: the error is wrapped `from exc`, and the notified `retained` path/hash stay recorded.
- The missing-callable path is source-validated, as the parent clarification asks.

**DriverError handling**
- Only `now >= frame_deadline` maps to the canonical no-fresh-frame refusal; anything else re-raises (`daemon.py:5285-5293`).
- The error-text retry and the `construct` retry are gone.

**Timing model**
- **Glue charge:** the `poll_backend_glue` span is a production no-op: the name is not in `_SPAN_NAMES`, and `begin_attempt` always runs first. The model charges it once per capture call at span entry.
- **Retry sleeps:** provider retries go through the daemon-local hook and only advance the virtual clock. `charge_total` is the only measure of active work, and `time.sleep` is checked unchanged.
- **Reduced mode:** only the target value is swapped. The capability, anchor/`waitingOrdinal` and final-ACK checks all still run, with no fake exception.
- **First-shot phases:** the startup sum now includes the glue charge, so pinned first-shot phases stay exact and the vectors are unchanged.

**Other items**
- **Restored regression:** `test_runtime_native_observation_couples_provider_and_runner_spans` is equivalent to base; only the lease filename and the assertion form differ.
- **Typed refusal cases:** the three new cases reach the final admission refusal at `daemon.py:2281-2290`. `_release_failed` only changes in `revoke`/`close`, so the case is deterministic.
- **Sol R2 M3:** retirement and artifact-removal checks now cover every spawned refusal and post-dispatch rejection (`test_session_native.py:1777`, `:1813`, `:2510`, `:2534`).
- **Lock order:** no new nesting. The sink, the sleep hook and `mark_release` all run outside authority locks.

## Must-Fix

None.

## Should-Fix

1. **`tests/test_session_native.py:2439-2441` with `:2571-2576` — the `active-groups` fault puts a made-up process group into the real watchdog's kill list.**
   - **How it gets there:**
     - The test adds `999999` to `driver.guardian._active_process_groups`. This test's `DesktopDriver` runs a real non-daemon watchdog process.
     - When the refused producer is reaped, `observer_reaped` calls `unregister_observer_process` (`daemon.py:6195-6196`). That calls `_watchdog_state()` (`guardian.py:822-825`), which publishes `[999999]` to the watchdog (`guardian.py:1949`).
     - The restore is plain code, not in a `finally`, and does not republish.
   - **What can happen:**
     - **On a failed assertion or Ctrl-C in this case:** the restore is skipped. `close()` cannot prove release, raises (`guardian.py:2035-2041`) and leaves the watchdog running. At pytest exit, owner death triggers `cleanup()` (`:414`), which runs `terminate_groups()` (`:261-275`) and sends SIGTERM then SIGKILL to process group 999999.
     - **In a passing run:** the same kill happens if the process crashes before the next observer admission republishes the list.
     - **Why it is reachable:** `pid_max` here is 4194304 and the PID counter is already at 927905. Any same-user process-group leader that holds PID 999999 at that moment would be killed, which could be the game client or the session daemon. If another user owns that group, the watchdog loops on EPERM indefinitely.
   - **Fix:**
     - Use a test-owned live group, for example `Popen(["/bin/sleep", "30"], start_new_session=True)` and its PID.
     - In a `finally`, restore `_held`, `_active_process_groups` and `_release_failed` under `guardian._lock`, call `_watchdog_state()`, then kill and reap the holder.
     - The refusal under test stays identical.
     - Only the three new typed cases need re-running.

## Nits

1. **`tests/test_session_runtime.py:3997-4002` — the baseline guard can never fire, and the marker list is loose.**
   - `"anchor replaced"` never matches R7's artifact message, `"native pre-ACK alignment anchor was replaced"`. The marker list still excludes that message, so no false pass results.
   - The `"publisher"` marker would accept binding refusals as a natural outcome.
   - The model is deterministic, so pin the observed outcomes instead: old raises with `returned`; reduced has no error and a maximum above 900 ms.
2. **`tests/test_session_runtime.py:3963-3967` — the comment misattributes the count.**
   - Charging starts at memory-ready, so `owner_validation == 2` comes from held/100 and resume/0, not from "construction and held phases".
   - The assertion itself is correct.

STATUS: NEEDS WORK
