# Sol plan review R1 — native identity latency Stage 1

Plan reviewed: `.archive/PLAN-native-identity-latency.md`

Verified SHA-256: `b7594ae97531cc294ba915f4b9044304ec06ab996834695ee69fb95f3d13026a`

The four-file Stage 1 boundary is appropriate. It preserves all four fresh identity
barriers, the existing six-key paused-sample request, the one-second deadline, original
failure/cleanup evidence, and the accepted evaluator. The proposed three-request live
diagnostic is a measurement run, not qualification or permission to optimize.

## Must-Fix

1. **The collector starts after the interval it claims to measure.**
   `.archive/PLAN-native-identity-latency.md:52-57,124-134` starts the collector only
   after the request directory exists but requires a `sample_enter` event and intends to
   measure the complete owner-entry-to-producer interval. In the actual path,
   `owner_entered` is captured at `src/crowley/session/daemon.py:3720`, while the request
   directory is not created until `src/crowley/session/daemon.py:3829-3834`; request
   validation, Guardian/admission checks, and their thread/process CPU occur between
   those points. A collector created at 3834 cannot reconstruct the entry thread/process
   clock values. Create the in-memory request-local collector and capture monotonic,
   `thread_time_ns`, and `process_time_ns` at function entry, bind it to the directory
   only after that directory is safely created, and discard it when no directory exists.
   Alternatively, rename the boundary to `collector_enter` and explicitly give up the
   full first-interval CPU claim.

2. **The event schema cannot unambiguously produce the proposed measurements.**
   `.archive/PLAN-native-identity-latency.md:94-134` does not define whether `wall_ns`,
   `owner_thread_cpu_ns`, and `owner_process_cpu_ns` are absolute clock samples, elapsed
   offsets, or per-operation durations. It also has one repeated `identity_return` name
   and an underspecified `ordinal`, so the four mandatory resolutions at
   `src/crowley/session/daemon.py:3852,3947` and
   `src/crowley/session/driver.py:2800,3094` cannot be attributed independently or paired
   with their X11 queries. Define one interpretation and barrier identity. The smallest
   correction is a duration record with a closed `barrier` enum (`daemon_pre`,
   `backend_pre`, `backend_post`, `daemon_post`, plus non-identity phases), an ordinal
   local to that barrier/name, and wall/thread/process CPU deltas captured from the same
   begin/end pair. Identity-total records may contain query records, but the reporter
   must never sum nested intervals.

3. **“Hash-mismatched artifact” is not a testable refusal under the unchanged transport.**
   `.archive/PLAN-native-identity-latency.md:59-74,148-150` leaves the response schema
   unchanged and locates the artifact by path only. The existing success/failure
   responses expose those paths but no trusted digest
   (`src/crowley/session/daemon.py:4006-4035,4091-4124`). A digest computed from the file
   being parsed cannot detect a mismatch with itself. Keep the no-IPC-change boundary:
   require descriptor-bound `O_NOFOLLOW` open, lstat/fstat identity and size/mode checks,
   bounded read, and unchanged final fstat; compute SHA-256 as reporter provenance, then
   remove the impossible hash-mismatch refusal/test. Binding a trusted expected digest
   into the existing receipt would instead be a receipt-schema change and is outside
   this plan.

4. **The live preflight needs a trusted source for the reviewed expected bindings.**
   `.archive/PLAN-native-identity-latency.md:76-87,116-119` says live mode validates the
   exact accepted source/config/producer hashes but defines neither its required inputs
   nor how “accepted” is distinguished from whatever files happen to be current. This
   matters because Stage 1 itself changes two members of the seven-source map
   (`src/crowley/session/daemon.py:156-255`). Require live mode to receive a
   descriptor-bound, parent-created manifest from the post-review freeze containing the
   exact seven-name map (or its canonical digest), raw/semantic config digests, and
   producer digest. Compare those values with status/request/response/artifact bindings;
   refuse missing or mismatched values. Do not let the sidecar derive acceptance solely
   from the mutable checkout or artifact it is evaluating.

## Should-Fix

1. `.archive/PLAN-native-identity-latency.md:94-122` allows artifact status
   `write_failed`, while an atomic publication failure normally leaves no trusted final
   artifact and the plan already assigns that condition to a fixed-token private log.
   Limit published status to `complete|partial`, or define the narrower recoverable case
   in which a minimal `write_failed` artifact can itself be successfully and atomically
   published. Absence must remain the outcome when final publication fails.

## Nits

None.

STATUS: NEEDS WORK
