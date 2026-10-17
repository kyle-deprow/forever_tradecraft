# Sol source review R2 — native identity latency Stage 1

Candidate reviewed: `/home/dev/.cache/crowley/worktrees/identity-latency-r2-20261017`

## Identity and scope

- Plan SHA-256 verified: `397bccaa859a7e39c31eef7555aa5f10764dd63329f118478e4004ac5ca2d685`.
- Freeze SHA-256 verified: `4e5791989e57fb861b23f52a83f35f94086d318ac2aa83b94d570aada4cd9abd`.
- Owned file hashes verified:
  - `src/crowley/session/driver.py`: `ca0ca123d0fa09d8361c8632d9cc1c2c501d87adf99cb3cc268688dd4291a166`
  - `src/crowley/session/daemon.py`: `e7aa8e0a40cbf527f74632c79e002ef14c47ca268ef63edf986eeb7e2eb3a6c1`
  - `tests/test_session_native.py`: `6616726ce20808b4aa0ccd3baf5a1c433e2b0b993b7bc520ef29f895731d5918`
  - `tools/gnome-telemetry-region/identity_latency_sidecar.py`: `091c754af6450f82677b8145febbfc44b68c446cedbff832e5945505e7d53fd7`
- All four read-only pins match the freeze: `offline_harness.py` `f682d856…`, `session_performance.py` `c46cae84…`, `test_session_performance.py` `c998aa4a…`, and `RUNTIME_PERFORMANCE.md` `54237c34…`.
- I reviewed the R1-to-R2 source delta and relevant callers only. I did not run tests, builds, Git, or runtime actions. Parent reports 204 native/evaluator tests passing in 220.47 seconds plus scoped Ruff, formatting, and diff checks; the worker reports the same 204 tests passing in 214.44 seconds.

R2 closes the R1 IPC, status-preflight, CPU-event, event-capacity, sink-reset, artifact-publication, process-verification, seal-hash, and output-preflight findings in the intended four-file fence. The existing six-key request, one-second sample deadline plus 250 ms evidence grace, PAUSED status schema, response schemas, cleanup, and read-only evaluator contract remain unchanged.

## Must-Fix

1. **The new “current binding” preflight can accept a config revision different from the raw bytes it authenticated.**
   - **Where:** `tools/gnome-telemetry-region/identity_latency_sidecar.py:199-281` and `:751-774`.
   - **Reachable trigger:** `_hash_local_descriptor` compares only device, inode, mode, link count, and size. A same-size in-place write after its read but before the final stat changes `mtime`/`ctime` while passing those comparisons, so the function can return the manifest's old digest after the path already contains new bytes. `_current_config_binding` then reopens the path through `load_config` without rechecking its raw digest. A same-semantic raw change in that gap therefore yields the expected old raw digest, expected semantic digest, and expected producer digest, and `_run_live` proceeds to sample 0. The owner does not independently hash the raw config file, so this drift is not repaired later.
   - **Correction:** compare the full stable descriptor tuple used by the production source reader, including `st_mtime_ns` and `st_ctime_ns`, across lstat/open/read/final-lstat and require the bytes read to equal the opened size. Bind parsing to those bytes if practical; otherwise descriptor-hash the config again after `load_config` and require the same raw digest before status/sample IPC. Add a zero-sample regression for a same-size in-place mutation and for a mutation between the first hash and config load.

2. **The sanitized report silently loses the event-truncation fact.**
   - **Where:** `tools/gnome-telemetry-region/identity_latency_sidecar.py:524-609`; the authoritative fields are emitted by `src/crowley/session/daemon.py:463-465`.
   - **Reachable trigger:** once more than 256 events are attempted, or one name/barrier pair exceeds ordinal 31, the owner publishes `events_truncated: true`. `validate_artifact` accepts that truthful artifact, but `read_response_profile` copies only `events`; it drops both `event_count` and `events_truncated`. The final Stage 1 report then presents an incomplete owner-CPU trace with the same `reason: "ok"` shape as a complete trace. That makes the diagnostic unable to distinguish measured CPU from CPU hidden by its own cap.
   - **Correction:** carry `event_count` and `events_truncated` into every sanitized sample, including explicit nulls for an absent/invalid artifact. Add a 257th-event or ordinal-overflow regression through `build_report` that proves truncation remains visible without increasing the 256-event bound.

## Should-Fix

1. **The derived owner-to-parent tail can be negative without being refused.**
   - **Where:** `tools/gnome-telemetry-region/identity_latency_sidecar.py:494-506` and `:571-602`.
   - **Consequence:** the strict IPC client validates framing, not the response's `owner_returned` clock. Any finite future or otherwise inconsistent value is converted to nanoseconds and subtracted from `response_received_monotonic_ns`, producing a negative field in an otherwise accepted diagnostic report. That is not a truthful transport/serialization interval.
   - **Correction:** require `request_started_monotonic_ns <= owner_returned_monotonic_ns <= response_received_monotonic_ns` before emitting the derived interval. Otherwise keep it null and attach a fixed malformed-clock reason. Cover the bound with a report-only fixture.

## Nits

None.

STATUS: NEEDS WORK
