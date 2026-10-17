# Sol plan review: deterministic runtime performance R1

Reviewed plan SHA-256: `5bac0e1d345e7e4e0288b4620874c339c19aeea7f605688bdde837d292bf22b0`.

The phase ordering and source fence preserve the current beta priority: Phase 1 is offline and starts only after the active native closure freezes, and Phase 2 authorizes a new plan rather than a Rust implementation. The plan also correctly preserves strict decoding, identity, deadline, cleanup, watchdog, and sole-owner behavior. Its migration trigger needs a reproducible definition before it can safely authorize the Rust plan.

Evidence and source hashes inspected:

- `.archive/executor-review/offline-decoder-computation-baseline-20261017.json`: `306d334c752a2522488a5b92310ad8cca58797e2f02c1891f716f09589edf520`
- `.archive/executor-review/gnome-no-flash-next-cost-parent-live-verification.json`: `9927ab1150384c6ab34be261b4224b7c382283608edf4851aebb36eca7a4218c`
- `src/crowley/session/decoder.py`: `badd6c3f469f0f13503d3aa8851e7d0dac416629f3974841593d6b42d2199739`
- `src/crowley/session/protocol.py`: `cf13dedd7a37e553ac799b87dd5429cc29b5910483661f994ffdec3b38a74d2f`

The current source hashes match those recorded in the offline baseline. That baseline measures one genuine preserved frame over 100 warm iterations: strict decode p95 is 60.650805997 ms and PNG-load p95 is 0.723975001 ms. The other receipt contains one full-screen native-C diagnostic sample, not a matched region-path distribution, so the two records do not establish a Rust trigger.

## Must-Fix

1. `.archive/PLAN-deterministic-runtime-performance.md:84` defines three disjunctive migration triggers without defining the numerator, denominator, eligible sample set, or minimum repeatability needed to evaluate them. “Application computation,” “same-path p95 observation budget,” and “after capture/I/O overhead has been addressed” can produce different decisions depending on whether PNG file loading, schema inflation, overlapping substeps, or unrelated planner timings are included. The existing single full-screen receipt at `.archive/executor-review/gnome-no-flash-next-cost-parent-live-verification.json:4` cannot be combined as a same-path denominator with the preserved region replay, and the current 60.65 ms decoder p95 does not satisfy the plan's explicit 100 ms condition. Before Phase 1 implementation, define one frozen decision record schema with: eligible accepted region-path artifact/receipt identities and source hashes; a predeclared sample/run minimum and quantile rule; one non-overlapping `application_compute` interval; a same-sample original-parent-start to strict-decode-completion interval; process-CPU and wall values kept separate; an exact formula for the 20% test; an exact CPU or wall interpretation for the 100 ms test; and a numeric repeatability rule for computation-attributed deadline failures. Unmatched full-screen and region evidence must remain separate and must yield `insufficient evidence`, not migrate or defer.

## Should-Fix

1. `.archive/PLAN-deterministic-runtime-performance.md:64` asks for a deterministic/model boundary audit, but the acceptance criteria should name the known routine-cycle boundary that can otherwise be missed. With no configured native semantic anchor producer, `SessionDaemon._measure_pointer_anchor()` captures a fresh image and calls Luna at `src/crowley/session/daemon.py:1288`. A pointer movement then invokes the same provider again through `DesktopDriver._refresh_pointer_anchor()` at `src/crowley/session/driver.py:4734`. Thus an AH reopen can require two model calls even when routine telemetry monitoring itself is deterministic. Require the audit table to cover at least the already-open scan path, AH reopen/start, reload-buffer verification, upload/loaded-ACK reconciliation, and closeout/recovery, and to list both anchor calls separately with their evidence source. Permit a zero-call full-cycle claim only when an accepted fresh native semantic-anchor provider replaces both boundaries; the existing prohibition on remembered coordinates at `.archive/PLAN-deterministic-runtime-performance.md:70` must remain.

## Nits

None.

STATUS: NEEDS WORK
