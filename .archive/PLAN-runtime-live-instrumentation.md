# Runtime live instrumentation after native R5

Status: proposed bounded Phase 2 evidence slice. This plan authorizes no source
change, build, test, service restart, desktop capture, input, deployment, or Rust
work. Implementation starts only after the final R5 source/binary freeze passes
parent verification plus Sol and actual Opus review and is accepted into main.

## Fixed basis and sequencing

- The decision contract and migration thresholds remain exactly those in
  `.archive/PLAN-deterministic-runtime-performance.md` at SHA-256
  `08479c262c6b36e152f6b6ceee8f714aa360633f83c9020ae5b4a5354447de80`.
- Accepted Phase 1 inputs are `tools/session_performance.py` SHA-256
  `23c0294b9037ef8edb39fd49d6af61a43216f4997298f590a6d92a838eb774fe`,
  `docs/RUNTIME_PERFORMANCE.md` SHA-256
  `becbcbe0c6b9bf1154e1254661f5cc39f99dba87ae73f1c0c3d2ed38c3b62c5c`,
  and the static audit SHA-256
  `a188d3012403797a352537e37bb7766652bd64f4776ba777fd275bd87398ebd5`.
  The R4 audit is historical source analysis, not observed model-call evidence.
- R5 plan SHA-256 is
  `87396c942452b4c6293c15d589faa58039d08319c967ae2814247c489fef7142`.
  The inspected R5 worktree is still mutable and supplies interface names only.
  Do not copy its current hashes into an accepted performance binding.
- After R5 acceptance, root records its final hashes and binary digest. Luna then
  implements this slice in a new isolated worktree. Because it touches production
  executor source, parent checks, Sol review, and actual Opus review must all be
  READY before integration. Live collection then requires parent technical release
  and sole-operator scheduling under the user's existing authorization.
- Ordinary beta collection remains the priority. Never pause or restart its owner
  automatically to gather performance evidence.

## Exact implementation ownership

Luna owns only these existing files:

- `src/crowley/session/driver.py`
- `src/crowley/session/daemon.py`
- `tools/gnome-telemetry-region/offline_harness.py`
- `tools/session_performance.py`
- `tests/test_session_native.py`
- `tests/test_session_performance.py`
- `docs/RUNTIME_PERFORMANCE.md`

No C patch, native build recipe, `cli.py`, controller, Guardian, model adapter,
configuration, service, addon, market, or deployment file changes. Reuse R5's
existing `paused_region_sample` IPC, sole owner, one-second sample deadline,
fixed eight-sample run, capture admission, cancellation, and cleanup semantics.

Root alone creates a reviewed, private accepted-binding JSON after source review.
It contains the exact accepted hashes of `daemon.py`, `driver.py`, `cli.py`,
`decoder.py`, `protocol.py`, `offline_harness.py`, and
`session_performance.py`; the accepted R5 producer digest and protocol branch;
and the reviewed raw-file and semantic config digests. Its SHA-256 is retained in
the public decision report. It contains no config values, paths, or identities.

## Instrumentation contract

`driver.py` extends the existing immutable region receipt and failure-attempt
snapshot only with timestamps the parent really observes. Preserve
`request_started`, `lock_acquired`, `ack_sent`, producer `capture_started`, and
parent `capture_returned`; make every not-yet-reached value `null` on failure.
Update the failure snapshot whenever a boundary is crossed so late failures do
not lose earlier evidence. Do not add a producer timestamp, child CPU value, or
Shell interval that the parent did not observe. Do not change deadlines, waits,
capture behavior, or producer protocol.

`daemon.py` snapshots a fixed source-hash map at owner construction and verifies
the same descriptor-bound, capped bytes before and after every diagnostic sample.
Read only the fixed package files above that belong to the owner; reject symlinks,
replacement, size drift, or digest drift. Return digests and logical source names,
never filesystem paths. Keep the loaded semantic config snapshot and existing
producer seal/hash checks as the config and producer authority.

All four daemon model entry points (`observe`, `observe_route`,
`observe_viewport`, and `decide`) increment thread-safe monotonically increasing
started/succeeded/failed counters immediately around the real adapter call. The
paused sample records before/after snapshots and exact deltas. A missing counter
is `null`; it is never inferred from the static audit. Any nonzero delta is
retained and makes that run ineligible for the pure paused capture path. These
counts say nothing about an ordinary full scan or AH reopen cycle.

The owner adds `source_binding`, `model_calls_before`, `model_calls_after`,
`model_call_delta`, and a final `response_ready_monotonic` to both success and
bounded failure evidence. Keep the existing finalizer timestamp with its current
meaning; do not relabel it as socket return. Failure before a boundary preserves
the original request target/deadline and uses `null` for unavailable fields.

`offline_harness.py` publishes live receipt schema 2. Before each status request,
create an attempt record containing index, original target, outer start, and
`deadline = target + 1.0`. Finalize that record in `finally`, including the
failure phase and a fixed reason code. The top-level receipt always retains all
eight original targets, all attempts actually begun, and the terminal run state.
It does not retry a sample or continue after a qualification failure.

Record client `status_returned`, owner-IPC request start/return, PNG publication
end, PNG-load start/end, strict-decode start/end, and sample completion. Measure
`PixelDecoder.decode` in that same attempt with `time.process_time_ns()` and
monotonic wall time, excluding `Image.open/load`, file writes, capture, IPC, and
planners. Only a successfully returned strict decode supplies
`application_compute_cpu_seconds`; a thrown decode may retain a separately named
partial diagnostic interval but cannot become a completed pair.

Hash the observer's `offline_harness.py`, `decoder.py`, and `protocol.py` through
bounded descriptors before and after the run and refuse drift. Preserve boot,
sequence, identity fingerprint consistency, PNG digest, owner receipt nonce,
config digests, producer digest, cleanup, generation, targets, and deadlines.
Raw schema-2 receipts and PNGs stay private. Public reports omit paths, image
bytes, raw errors, character/realm, XIDs/PIDs, nonces, and identity fingerprints.

## Honest intervals

Each attempt retains original boundaries plus these directly derived intervals:

- outer end-to-end wall: outer start through strict decode completion;
- status wall: outer start through status return;
- owner IPC round-trip wall: request start through client response return;
- owner wall: owner entry through owner response-ready;
- pre-capture owner wall: owner entry through driver request start;
- capture-lock wait: driver request start through lock acquisition;
- admitted setup/protocol wall: lock acquisition through owner ACK;
- external capture plus parent validation wall: producer capture start through
  parent capture return;
- response/materialization wall: owner response-ready through PNG publication;
- PNG-load wall and strict-decode wall;
- strict-decode process CPU from the observer process.

These intervals overlap and must never be summed. Request-to-ACK includes setup,
admission, scheduling, and IPC; capture-start-to-parent-return includes GNOME
Shell, the C child, PNG encoding/I/O, validation, and process exit. GNOME Shell
CPU, producer-child CPU, kernel/filesystem CPU, and server-side external CPU are
`null` with reason `external_process_cpu_unavailable`. No residual subtraction is
reported as a stage. Failed attempts retain every reached timestamp and `null`
for each unreached interval.

## Binding validation and decision report

`tools/session_performance.py` adds a separate bounded schema-2 live-receipt mode;
the Phase 1 PNG replay remains offline and unchanged. Accept at most 64 live run
receipts so failures are never discarded to fit the 15-run minimum. Use stable
descriptor reads, strict duplicate/nonfinite JSON refusal, a fixed schema, unique
receipt digests/run IDs, and exact source/config/producer equality with the
reviewed binding file and its separately supplied expected SHA-256. Caller fields
such as `accepted=true` remain meaningless.

Emit the already specified top-level schema
`crowley.runtime-performance-decision` version 1 with
`accepted_source_hashes`, `producer_binding`, `config_binding`, `runs`,
`statistics`, `decision`, `reason_codes`, and `limitations`. Each run contains
its receipt digest/state, eight targets, begun attempts, completed pairs, failed
phases/reason codes, model-call deltas, and interval availability. Preserve failed
and ineligible runs in `runs`; statistics select eligibility without deleting
them. Apply the existing Q95, 120-completion/15-run, 80% repeatability, 100 ms,
ratio, and counterfactual failure rules verbatim. Current and partial collections
return `insufficient_evidence`; do not create a Rust plan from them.

## Verification and later acceptance

Tests use injected local clocks/counters, never global time replacement. Cover
success and failure at every timestamp boundary; model started/succeeded/failed
deltas; source/config/producer drift; missing/null intervals; decode exceptions;
duplicate/nonfinite/oversized receipts; 14 versus 15 runs; 119 versus 120 pairs;
duplicate runs; exact quantiles; all three decisions; and public-report privacy.
Exercise the real R5 IPC/strict decoder in the focused native test. No wall-time
performance assertion belongs in unit tests. Name the two new native regressions
`test_paused_region_performance_receipt_preserves_all_boundaries_and_model_counts`
and `test_paused_region_performance_failure_preserves_reached_boundaries` so the
focused command below cannot silently omit them.

Implementation checks after R5 acceptance:

```bash
uv run pytest -q tests/test_session_performance.py
uv run pytest -q \
  tests/test_session_native.py::test_paused_diagnostic_uses_actual_config_ipc_driver_and_eight_compiled_samples \
  tests/test_session_native.py::test_compiled_region_composes_through_default_daemon_and_stock_model \
  tests/test_session_native.py::test_paused_region_performance_receipt_preserves_all_boundaries_and_model_counts \
  tests/test_session_native.py::test_paused_region_performance_failure_preserves_reached_boundaries
uv run ruff check src/crowley/session/driver.py src/crowley/session/daemon.py tools/gnome-telemetry-region/offline_harness.py tools/session_performance.py tests/test_session_native.py tests/test_session_performance.py
uv run ruff format --check src/crowley/session/driver.py src/crowley/session/daemon.py tools/gnome-telemetry-region/offline_harness.py tools/session_performance.py tests/test_session_native.py tests/test_session_performance.py
uv run python -m py_compile src/crowley/session/driver.py src/crowley/session/daemon.py tools/gnome-telemetry-region/offline_harness.py tools/session_performance.py
git diff --check
```

After review, integration, a fresh owner using the accepted hashes, parent
technical release, and sole-operator scheduling, invoke the existing
`--paused-diagnostic` command once per new private evidence directory. Keep every
failed receipt and collect at least 15 distinct passed runs of eight samples
without changing the fixed runner. Then run `tools/session_performance.py` with
every receipt, the reviewed private binding file, and its parent-recorded
SHA-256. Parent independently checks the raw receipts, binding digest, decision
output, owner cleanup, and unchanged one-second deadlines before any migration
verdict. The user's authorization already covers ongoing implementation and live
collection; this plan still requires the accepted source and qualification gates,
preserves the R5/Guardian/human-proof fences, and never restarts the owner
automatically or releases unreviewed work.
