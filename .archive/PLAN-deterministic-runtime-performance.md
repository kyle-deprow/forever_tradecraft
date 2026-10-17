# Deterministic runtime performance and conditional Rust migration

Status: proposed performance plan, not an approved rewrite or deployment.
User direction (Oct 17): continue collection and qualification, minimize Luna in
routine execution, and plan a Rust rewrite if computation proves a bottleneck.
This work must not delay useful beta collection or overwrite the ongoing native
region and recovery tasks. The user has resumed those tasks.

## Evidence and decision

The existing compiled C capture diagnostic measured one full-screen path at
1.674s overall, including 357ms inside the Shell request and 347ms encoding and
writing the output PNG. These are individual diagnostic intervals, not current
region-capture distributions or a complete additive attribution of all latency.
See `gnome-no-flash-next-cost-parent-live-verification.json` in executor-review.

Parent offline replay of one preserved genuine 256x256 frame, 100 measured
iterations after five warmups, measured strict Python decode at 54.54ms median /
60.65ms p95 and PNG loading at 0.64ms median / 0.72ms p95. CPU median closely
matched wall median. This is real computation but currently insufficient to
establish it as the end-to-end bottleneck. Replay uses a fresh decoder for each
iteration; it establishes neither live freshness nor real sequence transitions.
See `offline-decoder-computation-baseline-20261017.json`.

Do not claim a Rust speedup from language choice or compare region capture to
full-screen capture as if language were the only variable. The existing capture
producer is already native C. First complete accepted region integration and
timing evidence, then attribute the remaining costs.

## Phase 1: bounded measurement and deterministic-boundary audit

After the active native closure has frozen and passed review, propose a Luna
implementation owning only:

- `tools/session_performance.py` (offline, explicit input artifacts only);
- `tests/test_session_performance.py`;
- `docs/RUNTIME_PERFORMANCE.md`.

No production source, addon, private profile, native producer, Compose, service,
market data, global tools or Git changes. Do not add live screenshot/input modes
to this benchmark. No overlap with native worker ownership. Sol reviews this
plan before implementation; actual Opus reviews any later executor changes.

The offline command must accept explicit preserved lossless status PNGs and
captured timing receipts. It never captures the desktop or sends input. Measure
PNG load, strict pixel extraction/2x2 validation, cell unpack, frame inflation /
JSON/schema validation, full strict decode, and pure pointer/click/key/camera
planning separately. Instrument at existing public boundaries without replacing
the production algorithms. Where substeps have no public boundary, report an
honest combined interval rather than modifying production for attribution.

Record warmups, N, input hash/size/dimensions, relevant source hashes, Python /
Pillow versions, OS/CPU metadata, process CPU and monotonic wall p50/p95/p99/max,
and exact quantile definition. Exclude startup only when labeled. Default 100
samples; cap counts and input sizes. Distinguish cold imports, warm-file replay,
live capture and end-to-end measurements. Never sum overlapping intervals or
silently mix source versions. Missing live stage evidence remains unknown.
No payloads, character identity, screenshots or credentials in committed reports.

The fifth ordinary sweep provides a separate orchestration baseline (see
`build-70450-fifth-scan-parent-verification.json`): completion to Return dispatch
81.67s, then dispatch to server receipt4.96s. A preserved completed HUD existed
about44s before dispatch. This misses the60s upload gate primarily before
dispatch; it is not evidence of slow Python computation. Audit deterministic
completion/readback/dispatch handling separately from CPU and server transport.
Do not attribute all pre-dispatch time to model inference without per-stage logs.

Include real valid fixture sequences and malformed/CRC/pixel-disagreement cases
from shared Lua/CRS1 boundaries. Preserve production strict refusal behavior.
Benchmark success says nothing about live-frame freshness qualification.

Audit the actual controller's stable-session scan start, monitor, reload-buffer
verification, upload/ACK reconciliation and closeout path. Build a concrete table
of deterministic vs model-assisted boundaries and count actual model calls from
existing test/journal evidence. Missing counters are unknown, not zero. Routine
telemetry checks, deadlines, timing, retries, command text verification and input
release belong in code. Luna remains limited to bounded visual uncertainty such
as an unrecognized screen or a freshly measured target. Do not replace expired
visual evidence with remembered coordinates just to achieve zero model calls.
Propose a separate reviewed slice for any discovered model call that can safely
be removed; the performance tool itself must not change controller behavior.
The audit must separately cover already-open scanning, AH reopen/start, reload
buffer verification, upload/loaded-ACK reconciliation, and closeout/recovery.
Record both `_measure_pointer_anchor`'s Luna call and the post-movement
`_refresh_pointer_anchor` call with their actual evidence source. A zero-call
whole-cycle claim requires an accepted fresh semantic-anchor provider replacing
both; deterministic telemetry monitoring alone is insufficient.

Verification: `uv run pytest -q tests/test_session_performance.py`, scoped
`uv run ruff check tools/session_performance.py tests/test_session_performance.py`,
`uv run ruff format --check tools/session_performance.py tests/test_session_performance.py`,
`uv run python -m py_compile tools/session_performance.py`, `git diff --check`,
and actual offline CLI output against explicit retained or shared fixture input.
No flaky wall-time thresholds in unit tests; verify statistics and refusal logic.

## Phase 2: conditional Rust design review

Use a versioned decision record with exactly these top-level fields:
`schema="crowley.runtime-performance-decision"`, `schema_version=1`,
`accepted_source_hashes`, `producer_binding`, `config_binding`, `runs`,
`statistics`, `decision`, `reason_codes` and `limitations`. Each run records
original structurally validated receipt digest, source/input hashes, original sample targets,
the paired end-to-end wall intervals, separately measured non-overlapping
computation CPU intervals, failure phases, and capture/I/O interval availability.
An absent interval is null, never zero. Use process/thread CPU from the executing
process, not parent CPU to represent work in a child. Never add overlapping
whole-decode and pixel/unpack/schema substeps.

Eligibility requires the SAME reviewed region path/config/source/producer binding
and at least120paired completed observations across at least15independent
eight-sample runs, with all attempts and failures retained. A run may have a
failed outcome; eligibility means the reviewed binding/evidence is valid, not
that its timing passed. Only samples reaching strict decode completion have a
paired end-to-end/CPU interval; earlier failures remain counted separately.
Live acquisition is a separate
reviewed operation, not part of the offline tool. Normal native100 evidence can
only contribute through a separately reviewed matching instrumentation contract;
do not alter the eight-sample runner's fixed count. Existing warm replay and
single full-screen capture do not meet this eligibility requirement.

For each sample, `end_to_end_wall` is original parent outer start (before status
and identity) through strict decode completion, in seconds. `application_compute`
is the sum of CPU time for strict region pixel/cell/frame/schema decoding in the
actual observer process, measured within that same sample. Exclude filesystem
reads, PNG loading, capture/identity/IPC waiting, child process work and all
gesture planners from this numerator; record their costs separately. It is one
combined non-overlapping decode interval, not the sum of nested substeps. Both
CPU and elapsed wall values are retained with method and units.

Quantile Q95(x) is sorted(x)[ceil(.95*N)-1]. For the pooled eligible sample set,
compute `ratio=Q95(application_compute_cpu)/Q95(end_to_end_wall)`; do not describe
this ratio of quantiles as a per-sample CPU fraction. The proposed migration-plan
trigger is ratio>=0.20 OR Q95(application_compute_cpu)>=0.100seconds, provided
the relevant condition also holds in at least80%of eligible runs with all eight
completed samples (at least15such runs), using each run's same
quantile rule. Trigger means draft a scoped Rust plan, never deploy code.

Alternatively, computation-attributed deadline failure triggers a plan only if
at least3failures occur across3distinct eligible runs, measured end-to-end>1s,
measured application CPU>=0.100s, and end-to-end minus that same CPU interval<1s
for every such failure. This is a screening counterfactual for a prototype, not
proof Rust would remove that CPU time or guarantee deadline compliance. Required
stage evidence must be present; unexplained/missing capture or I/O measurements
cannot be called computation-attributed failures.

Return `insufficient_evidence` for mismatched sources/paths, absent paired CPU
measurements, missing required stages or inadequate runs. Return `plan_prototype`
only when an eligible trigger passes, otherwise `defer_rewrite`. Never infer a
defer/migrate verdict from unmatched full-screen and replay measurements. Current
evidence is `insufficient_evidence`; prioritize accepted capture/IPC measurements.

If triggered, write `.archive/PLAN-rust-session-runtime.md` with measured target,
exact file ownership, public interface and rollout criteria before code. Start
with a pure offline decoder behind a versioned boundary, retaining Python as
the reference. Proposed crate location is `native/session-runtime/`; creating it
is NOT authorized by this performance plan alone. Select dependencies only after
checking official documentation and the actual host requirements.

Stage the migration: strict pixel decoder first; capture broker second only if
profiling warrants it; input/executor ownership last. Keep Lua publication and
Python market/strategy/server orchestration. Persistent connections, batching and
fewer image copies are separate architectural variables that must be measured
independently of Rust. Preserve GNOME's actual admission/identity restrictions;
a new binary or direct D-Bus call is not automatically an admitted producer.

For a Rust prototype, differential tests must reproduce valid decoded values and
malformed-input refusals, resource/size bounds, sequence/boot/window identity
checks, integer and boolean distinctions, CRC/inflate semantics and timestamps.
No live fallback after an admitted native path fails. An offline prototype is
default-off, has no input privilege and cannot replace the runtime by accident.

A later persistent runtime proposal must specify typed local IPC, original
monotonic timestamps, exact ownership of every connection/process/held input,
deadlines, bounded queues/backpressure, cancellation generations, human takeover,
parent-death release, binary/source binding and crash reconciliation. Rust's
ownership types do not replace behavioral proofs. Keep the independent watchdog
and sole canonical desktop owner. No evidence-scoped alternate input lease can
qualify the production path.

Accept migration only after matched workloads show material p95/p99 improvement,
behavioral parity and adversarial cleanup/takeover tests, then Sol and actual
Opus READY reviews and a bounded live qualification. Gesture durations remain
deliberate: faster internal processing must not shorten calibrated dwell or
movement beyond existing limits. No higher publication frequency is implied;
the addon remains at one Hz unless separately measured and reviewed.

## Completion

Phase 1 ends with reproducible stage measurements, deterministic-boundary audit,
an explicit `plan_prototype`, `defer_rewrite` or `insufficient_evidence` decision,
and a reviewed next slice. Insufficient evidence is a valid Phase1 outcome: name
the exact missing paired stages/runs and propose a bounded reviewed evidence
collection slice instead of forcing a Rust decision. This work does not claim
launch readiness or authorize a broad rewrite. Root owns integration and Git.
