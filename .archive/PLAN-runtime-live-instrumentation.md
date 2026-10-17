# Runtime live instrumentation after accepted native closure

Status: proposed bounded Phase 2 evidence slice. This plan authorizes no source
change, build, test, service restart, desktop capture, input, deployment, or Rust
work. Production instrumentation starts only after the final native successor
(currently R6) source/binary freeze passes
parent verification plus Sol and actual Opus review and is accepted into main.

The independent offline evaluator is already accepted in main at0e2ef72 after
SolsourceR3READY and parent65checks. It is a read-only compatibility authority
for this production slice, not part of the implementation scope.

## Fixed basis and sequencing

- The decision contract and migration thresholds remain exactly those in
  `.archive/PLAN-deterministic-runtime-performance.md` at SHA-256
  `08479c262c6b36e152f6b6ceee8f714aa360633f83c9020ae5b4a5354447de80`.
- Accepted evaluator inputs are `tools/session_performance.py` SHA-256
  `c46cae849058005e9b7387ef95c34f40f376afb5477739efaf6f40f6a36ebd8c`,
  `tests/test_session_performance.py` SHA-256
  `c998aa4a9ff67ba67ddeab05a0e5a0cfa5273a296909e0b07cb79a3d06dd313a`,
  `docs/RUNTIME_PERFORMANCE.md` SHA-256
  `54237c344ef0faa3392cca6fe82b75f1f986bbf697c81d3f34493b2f00e1caca`,
  and the static audit SHA-256
  `a188d3012403797a352537e37bb7766652bd64f4776ba777fd275bd87398ebd5`.
  The R4 audit is historical source analysis, not observed model-call evidence.
- R6 closure is scoped in `.archive/PLAN-region-r6-activation-closure.md`,
  including the observed PNG publication race amendment. R5 is not accepted;
  historical R5 hashes cannot qualify this new live path. Until R6 acceptance,
  its artifacts supply interface names only, never an accepted binding.
- After native acceptance, root records its final hashes and binary digest. Luna then
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
- `tests/test_session_native.py`

No C patch, native build recipe, `cli.py`, controller, Guardian, model adapter,
configuration, service, addon, market, or deployment file changes. The three
accepted evaluator files above remain read-only; any necessary evaluator change
needs a separate reviewed slice. Reuse the accepted native successor's
existing `paused_region_sample` IPC, sole owner, one-second sample deadline,
fixed eight-sample run, capture admission, cancellation, and cleanup semantics.

Root alone creates a reviewed, private accepted-binding JSON after source review.
It contains the exact accepted hashes of `daemon.py`, `driver.py`, `cli.py`,
`decoder.py`, `protocol.py`, `offline_harness.py`, and
`session_performance.py`; the accepted native producer digest and protocol branch;
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

The exact schema in the pinned accepted `docs/RUNTIME_PERFORMANCE.md` and
`tools/session_performance.py` is normative, including all root, attempt, owner,
identity, counter, cleanup and failure keys/types/enums. Missing and extra keys
are refused. This slice must emit that schema rather than invent a compatible
extension of an old receipt. Every unreached nullable field is present as JSON
null. No extra private diagnostic keys are added to schema2 objects.

Both owner and observer use this fixed trusted-root path map:

| logical key | repository-relative source |
| --- | --- |
| daemon.py | src/crowley/session/daemon.py |
| driver.py | src/crowley/session/driver.py |
| cli.py | src/crowley/session/cli.py |
| decoder.py | src/crowley/session/decoder.py |
| protocol.py | src/crowley/session/protocol.py |
| offline_harness.py | tools/gnome-telemetry-region/offline_harness.py |
| session_performance.py | tools/session_performance.py |

Derive the trusted root from the actual installed project source, never a request
path. An installation lacking any required file cannot qualify this diagnostic.
Each map contains exactly all seven logical keys and lowercase SHA256 values.

`daemon.py` snapshots this whole source-hash map at owner construction and verifies
the same descriptor-bound, capped bytes before and after every diagnostic sample.
Read all seven fixed files above, including tooling; reject symlinks,
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
Counter objects contain exactly started/succeeded/failed with nonnegative integer
or null values; known deltas equal after minus before. Cumulative values never
decrease, succeeded+failed never exceeds started, and inter-sample increases are
retained as model activity, never reset to zero. The exact cleanup object is
captured after process reap and attempt retirement: booleans capture_process_reaped,
attempt_retired, lease_held, watchdog_healthy; nonnegative counts active_process_count,
active_process_group_count, observer_process_group_count. Do not snapshot provisional
cleanup and call it final. Eligible pairs require all four true and all counts0;
well-formed failures retain their actual snapshot and become ineligible. Identity
is exactly fingerprint/boot/sequence; owner entry absent means owner:null. Every
failure is exactly phase/reason_code using the accepted documentation's finite
enums. Preserve original failures without raw errors or invented classifications.

`offline_harness.py` publishes live receipt schema 2. Before each status request,
create an attempt record containing index, original target, outer start, and
`deadline = target + 1.0`. Finalize that record in `finally`, including the
failure phase and a fixed reason code. The top-level receipt always retains all
eight original targets, all attempts actually begun, and the terminal run state.
It does not retry a sample or continue after a qualification failure.
Targets are exactly t0+i*1.0 for i=0..7, each deadline is target+1.0. Late starts
and completions never rebase later targets.

Record client `status_returned`, owner-IPC request start/return, PNG publication
end, PNG-load start/end, strict-decode start/end, and sample completion. Measure
`PixelDecoder.decode` in that same attempt with `time.process_time_ns()` and
monotonic wall time, excluding `Image.open/load`, file writes, capture, IPC, and
planners. Only a successfully returned strict decode supplies
`application_compute_cpu_seconds`; a thrown decode may retain a separately named
partial diagnostic interval but cannot become a completed pair.
Emit application_compute_cpu_method exactly `time.process_time_ns` when full
CPU is present, otherwise null. Stamp strict_decode_finished_monotonic when
the public strict decoder actually returns. Separately stamp
sample_completed_monotonic only when the later sample completion boundary is
actually reached. An interrupted post-decode attempt keeps its real CPU/wall
pair and nullable completion marker. Finally preserves the record; it never
manufactures a completion timestamp. Declared completed attempts require both.

Hash all seven fixed sources independently in the observer through
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

The accepted read-only `tools/session_performance.py` already supplies the bounded
schema2 live-receipt evaluation mode; do not change it in this slice. It accepts at most64 live run
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

Production tests use injected local clocks/counters, never global time replacement.
Cover emitted schema, success/failure at every timestamp boundary, model counters
and deltas, source/config/producer drift, missing/null intervals, decode exceptions,
and final lifecycle/cleanup evidence, plus the compatibility pass below.
The accepted evaluator's existing tests already cover threshold math, malformed
inputs and privacy; do not duplicate them or modify their fixtures to accept an
incompatible producer. Exercise final real schema2 output through that unmodified
evaluator, with a clearly test-only exact binding. Exercise the accepted native
IPC/strict decoder in the focused native test. No wall-time
performance assertion belongs in unit tests. Name the two new native regressions
`test_paused_region_performance_receipt_preserves_all_boundaries_and_model_counts`
and `test_paused_region_performance_failure_preserves_reached_boundaries` so the
focused command below cannot silently omit them.

Implementation checks after native acceptance:

```bash
uv run pytest -q tests/test_session_performance.py
uv run pytest -q \
  tests/test_session_native.py::test_paused_diagnostic_uses_actual_config_ipc_driver_and_eight_compiled_samples \
  tests/test_session_native.py::test_compiled_region_composes_through_default_daemon_and_stock_model \
  tests/test_session_native.py::test_paused_region_performance_receipt_preserves_all_boundaries_and_model_counts \
  tests/test_session_native.py::test_paused_region_performance_failure_preserves_reached_boundaries
uv run ruff check src/crowley/session/driver.py src/crowley/session/daemon.py tools/gnome-telemetry-region/offline_harness.py tests/test_session_native.py
uv run ruff format --check src/crowley/session/driver.py src/crowley/session/daemon.py tools/gnome-telemetry-region/offline_harness.py tests/test_session_native.py
uv run python -m py_compile src/crowley/session/driver.py src/crowley/session/daemon.py tools/gnome-telemetry-region/offline_harness.py
git diff --check
```

After review, integration, a fresh owner using the accepted hashes, parent
technical release, and sole-operator scheduling, invoke the existing
`--paused-diagnostic` command once per new private evidence directory. Before the
first live run, predeclare one bounded collection of16runs, below the64receipt cap;
retain every begun outcome and report any early technical stop. Never extend the
batch selectively until enough successes occur. Each run retains eight fixed
targets; failed runs may end early. Evaluate the complete declared batch with
the baseline of120valid decoded pairs across15independent eligible runs. The
primary pooled CPU/ratio route additionally needs15full eight-pair runs and its
80percent repeatability condition. The alternative needs that baseline plus
three fully measured counterfactual failures across three distinct eligible
runs, without adding a15passed/full-run requirement. Insufficient data remains
insufficient_evidence; any later batch needs its own predeclared scope.
Then run `tools/session_performance.py` with
every receipt, the reviewed private binding file, and its parent-recorded
SHA-256. Parent independently checks the raw receipts, binding digest, decision
output, owner cleanup, and unchanged one-second deadlines before any migration
verdict. The user's authorization already covers ongoing implementation and live
collection; this plan still requires the accepted source and qualification gates,
preserves the accepted native/Guardian/human-proof fences, and never restarts the owner
automatically or releases unreviewed work.
