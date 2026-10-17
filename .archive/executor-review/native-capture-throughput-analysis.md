# Native capture throughput analysis (live accepted source)

## Scope and authority

This corrected report supersedes the earlier artifact written in the isolated
native-capabilities worktree.  It is based on the live accepted tree
`/home/dev/repos/pegasus`; the earlier report's source line references are not
authoritative.  Verified source hashes at analysis time are:

| File | SHA-256 |
| --- | --- |
| `src/crowley/session/driver.py` | `14ae6be4a901a17e396e68ac4501238db3d1cc0118c8c34ad6f7107fbcfacfa7` |
| `src/crowley/session/daemon.py` | `8d2a04aafe0672da80434e2b2c2981ccf2b5a9b7766a2c78a6dad119b1a0fcb0` |

This is read-only static analysis.  No source, runtime, GUI, capture, profile,
service, CLI, model, or git operation was performed.  Native construction did
not complete because the operator's world-entry click did not enter the world;
there is therefore no honest native 100-publication throughput failure or
qualification result.

The memory-measurement plan requires exactly 100 fresh, same-boot observations
at one Hz: updates 1..99 followed by held/100, with no skipped, old, or
substituted frames.  The provider's 30-second bounded wait and 50-ms retry
interval do not relax that requirement.

## Live production path and static cost

The accepted path is identity-bound and fail-closed:

| Stage | Current work | Live source |
| --- | --- | --- |
| Provider admission | `_native_measurement_provider` checks stage/ordinal, shutdown, controller state/generation, then `_check_native_poll_identity` resolves the live identity before every capture. | `src/crowley/session/daemon.py:1043-1100,1184-1192` |
| Process identity | `_matching_game_pids` scans `/proc`; `_process_executable` checks cmdline, start ticks, status, `/proc/PID/exe`, and Wine-prefix environment for each candidate. | `src/crowley/session/driver.py:1798-1844` |
| Window identity | `resolve_identity` queries search, geometry, window properties, child tree, root tree, focus, and root active-window properties, then seals the fingerprint and foreground/geometry conditions. | `src/crowley/session/driver.py:1895-1992` |
| Capture admission | `X11Backend.capture` snapshots the revocation epoch, resolves identity before the screenshot, serializes through the private GNOME lock, runs `gnome-screenshot -f`, waits for a complete PNG, resolves identity again, and atomically publishes only after final epoch/deadline checks. | `src/crowley/session/driver.py:2342-2405` |
| Desktop subprocess boundary | `_run` starts the positive admission wrapper (`python -I -S -c _EXEC_ADMISSION_WRAPPER`), registers the process group, releases the gate, and waits for the real allowlisted executable. | `src/crowley/session/driver.py:901-902,1277-1310` |
| Crop/decode/evidence | The client crop fully loads and writes a lossless PNG; the daemon hashes, decodes the exact calibrated crop, records capture admission time, copies the crop into private native evidence, and retains it until release. | `src/crowley/session/driver.py:5663-5728`; `src/crowley/session/daemon.py:975-1041` |

For the ordinary single-window case, one `resolve_identity` performs seven
wrapped desktop queries after its `/proc` scan: `xdotool search`, window
geometry, window `xprop`, child `xwininfo`, root `xwininfo`, focus, and root
`xprop`.  One accepted native frame therefore has the provider's poll
resolution plus the capture's before/after resolutions: approximately 3 x 7
wrapped desktop queries, or 21 queries, plus one `gnome-screenshot` process.
This is a static count, not a timing measurement; extra candidates or retries
can add work.  The private lock and complete-PNG wait are part of the live
capture path, so lock contention or asynchronous screenshot output can extend
the critical path before crop/decode/hash/evidence retention completes.

The provider does not accept the latest available frame.  It rejects non-fresh
samples, requires a sequence advance and unchanged boot, and raises when the
observed `(nativePhase, nativeOrdinal)` is not the requested pair.  After update
1 it requests every later ordinal in order.  A frame path materially longer
than one second can therefore miss the requested ordinal and fail the exact
observation contract; accepting an old/latest frame or skipping an ordinal
would be an invalid optimization.

## Measured versus unmeasured

The accepted live observations supplied for this analysis are:

| Observation | Correct interpretation |
| --- | --- |
| 1.853 s backend `capture` latency | Standalone backend capture; already longer than one one-Hz period, but not an end-to-end native publication measurement. |
| 3.406 s backend `capture` latency | Backend capture with lock contention; evidence of serialized-contention risk, not intrinsic single-capture cost. |
| 1.706 s post-error standalone latency | Stronger standalone signal after the construction error; no `strace` decomposition was captured.  Still backend-level evidence. |
| Native construction and 100 updates | Not measured or qualified because construction stopped at world entry. |

The standalone values above make a credible throughput-barrier risk for the
exact 100-update run, especially when lock wait and complete-PNG wait are
included.  They do not prove that the native sequence must fail, and they do
not identify whether identity queries, wrapper startup, GNOME completion,
crop/decode, evidence copy, or lock contention dominates.

## Bounded evidence before any optimization

After construction succeeds, use the real production provider and backend and
retain the existing checks.  For each requested ordinal, record expected and
observed phase/ordinal, sequence and boot, capture admission timestamp, lock
wait, each identity-resolution span, screenshot process return, complete-PNG
wait, crop, hash/decode, evidence copy, and release.  Treat missing, skipped,
stale, wrong-phase, and over-one-second observations as failures; do not
replace any with a latest frame.

One warm-up followed by the actual provider sequence can localize the problem.
If needed, `strace -f -ttT` or existing wrapper timing may measure the same
allowlisted commands with exact argv and the production backend.  That work
must not introduce an alternate screenshot provider, overlap requests, widen
the native deadline, or use provider/model doubles.  Only a complete exact
100-publication run can qualify the one-Hz requirement; a shorter run is
diagnostic only.

## Narrow optimization candidates, subject to review

1. If repeated identity resolution dominates, a reviewed production API could
   carry a newly verified identity certificate through capture while retaining
   before/after fingerprint, foreground, geometry, process, and generation
   checks.  A stale cache or removed boundary check would violate the contract.
2. If wrapper/process startup dominates, a reviewed read-only probe could batch
   the required identity fields while preserving the same fields and freshness
   at every admission boundary.  It must not turn identity into a
   construction-only check.
3. If GNOME completion dominates, optimize only serialization/output readiness
   around the existing `gnome-screenshot -f` backend.  An alternate capture
   backend, concurrent screenshots, or a longer freshness window changes the
   reviewed boundary.
4. If post-capture work dominates, moving hash/copy/decode off the critical
   path is viable only if the returned observation still has the exact crop,
   admission timestamp, identity binding, and sealed evidence semantics.  That
   requires a separately reviewed production change.

Do not widen the 30-second wait, skip ordinals, poll history, accept an old
frame, suppress identity checks, or treat the supplied timings as native
qualification.  The current conclusion is **unqualified but material
throughput risk**: live standalone capture has been observed above one Hz,
while the required exact native sequence remains unmeasured.
