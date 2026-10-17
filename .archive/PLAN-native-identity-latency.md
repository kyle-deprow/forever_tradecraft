# Plan: measure repeated native identity latency

Status: proposed, plan-only. Sol review is required before implementation. This plan
releases Stage 1 measurement only. It addresses the unattended 15-minute blocker by
making the two identity-heavy owner intervals measurable; it does not qualify
unattended scans, remove Luna observations, or change the schema-2 evaluator.

## Accepted boundary and invariants
Use the corrected audit
.archive/executor-review/runtime-owner-latency-code-audit.md at SHA-256
566fa2da6c494d0c4842a5f9bd4645e4d0c3da1706485a370dde72725d6ed870.
Its accepted 26-pair batch reports owner-entry to producer-request p50/p95
392.082/424.574 ms and producer capture-return to owner response-ready
395.297/420.772 ms. These are wall intervals, not causal attribution; owner and
external-child CPU are unmeasured.
Four independent fresh identity barriers remain mandatory:
1. daemon pre-capture, daemon.py:3852;
2. backend pre-capture, driver.py:2800;
3. backend post-capture, driver.py:3094;
4. daemon post-capture, daemon.py:3947-3949.
Guardian admission, one lease, cancellation/deadlines, sealed producer/object hashes,
process verification, source/config checks, cleanup/retirement, original failures,
the one-second sample deadline, and repeating-scan cadence/ack gates remain unchanged.
No cache, fallback identity, deadline relaxation, optimization, or Rust rewrite is authorized here.

## Exact Stage 1 ownership
Stage 1 may change only:
- src/crowley/session/driver.py, for the owner-local timing sink around existing
  resolve_identity, _run, seal, protocol, producer, and cleanup boundaries;
- src/crowley/session/daemon.py, for collector lifecycle and artifact persistence
  inside capture_paused_region_sample;
- tests/test_session_native.py, for actual daemon/driver boundary and failure tests;
- tools/gnome-telemetry-region/identity_latency_sidecar.py, for descriptor-safe
  artifact reading, private fixture/live diagnostics, and sanitized aggregates.
No offline_harness.py, evaluator, protocol schema, addon, controller, CLI dispatch,
config, service, producer, game/input path, or model loop changes are included. The
collector stays local to daemon.py/driver.py; no additional module, helper binary,
batching change, or persistent native process is implied by this plan.

## Activation and transport
At capture_paused_region_sample function entry, before request-directory creation,
create an in-memory collector and capture local monotonic, owner-thread CPU, and
owner-process CPU entry clocks. It has no path yet. After the existing request
directory is safely created and chmodded, bind that collector to the directory and
continue it through source binding, all four barriers, producer work, cleanup, and
the existing finally path. If no request directory is created, discard the
in-memory collector and write no artifact. The sink is bound to this owner thread
and exactly one invocation; no global clock replacement, process-wide hook,
background thread, or cross-request state is allowed.
The owner writes identity-latency.json beside receipt.json in the existing request
directory. It is a regular, non-symlink file, mode 0600, bounded in size, and
atomically written without adding an IPC field. It is attempted whenever the
directory was created, including identity/capture failures. A profiler write
failure produces only a fixed-token private log and an absent diagnostic profile;
it never replaces a causal capture, identity, deadline, or cleanup failure and never
changes existing owner/private response key sets, model counters, controller loop,
or receipt shape.
The parent/sidecar locates the candidate only through unchanged response keys:
on success, response.sample.artifact_directory; on failure,
response.failure.receipt_path, using its parent directory. It opens the candidate
descriptor with no-follow and close-on-exec flags, checks regular-file type, mode,
bounded size, and descriptor identity before and after a bounded read, then computes
a SHA-256 for provenance. That digest is not authentication: the unchanged IPC
contains no trusted artifact digest, and a digest of the bytes being parsed cannot
detect self-consistent tampering. No hash-mismatch refusal or acceptance claim is
made from that digest.
The sidecar has fixture and explicit live modes; it never starts/restarts/arms an
owner, modifies config, sends game input, or accepts arbitrary commands. Live mode
requires a separate parent-reviewed expected-binding manifest and a SHA supplied by
the parent before any sample. The manifest is private, descriptor-bound, mode 0600,
and contains exactly the seven logical source names and their SHA-256 values
(daemon.py, driver.py, cli.py, decoder.py, protocol.py, offline_harness.py, and
session_performance.py), config-file SHA-256, config-semantic SHA-256, and pinned
producer SHA-256. The sidecar verifies the manifest bytes against the supplied SHA
before reading mutable runtime files; it never derives an expected binding from the
current checkout; artifact/request/response hashes are compared with the manifest
only for consistency, never as artifact authentication. Missing, unreadable, or
mismatched manifest input aborts live diagnostics before the first request.
Using the existing owner IPC client, live mode sends three sequential
paused_region_sample requests. Each has exactly the original six keys: command,
generation, parent_started, deadline, config_file_sha256, and
config_semantic_sha256. Each deadline is parent_started + 1.0 seconds and the
existing 0.25-second failure-evidence grace is preserved. It saves every returned
success or failure once, reads the artifact through the existing response path, and
does not invoke the eight-sample runner, add an IPC command, add a request field,
change config, or make qualification claims. Normal generation/status preflight uses
the existing client path and is not counted as a sample command.
## Private artifact contract
identity-latency.json has this closed shape; it contains no raw identifiers, config
values, paths, executable names, argv contents, image bytes, or arbitrary errors:
{
  "schema": "identity-latency-v1",
  "status": "complete|partial",
  "source_binding_sha256": "64 lowercase hex",
  "producer_sha256": "64 lowercase hex",
  "config_file_sha256": "64 lowercase hex",
  "config_semantic_sha256": "64 lowercase hex",
  "owner_entry_monotonic_ns": "integer",
  "owner_bound_monotonic_ns": "integer or null",
  "owner_return_monotonic_ns": "integer or null",
  "intervals_non_additive": "boolean true",
  "intervals": [
    {
      "name": "owner_to_request_started|capture_return_to_response_ready",
      "start_monotonic_ns": "integer or null",
      "end_monotonic_ns": "integer or null",
      "duration_ns": "integer or null",
      "outcome": "ok|failed|cancelled|deadline|not_reached"
    }
  ],
  "barriers": [
    {
      "barrier": "daemon_pre|backend_pre|backend_post|daemon_post",
      "start_monotonic_ns": "integer or null",
      "end_monotonic_ns": "integer or null",
      "duration_ns": "integer or null",
      "outcome": "ok|failed|cancelled|deadline|not_reached"
    }
  ],
  "event_count": "integer 0..256",
  "events_truncated": "boolean",
  "events": [
    {
      "name": "bounded enum",
      "barrier": "daemon_pre|backend_pre|backend_post|daemon_post|none",
      "ordinal": "integer 0..31",
      "start_monotonic_ns": "integer or null",
      "end_monotonic_ns": "integer or null",
      "duration_ns": "integer or null",
      "owner_thread_cpu_ns": "integer or null",
      "owner_process_cpu_ns": "integer or null",
      "child_cpu_ns": null,
      "child_cpu_reason": "external_child_cpu_unmeasured",
      "outcome": "ok|failed|cancelled|deadline|not_reached"
    }
  ]
}
Barrier records are the only authority for the four identity resolutions. Their
start/end/duration values come from the same local clock pair; unreached values are
null. Events may be nested inside a barrier and intervals may overlap, so no barrier,
event, or interval durations are summed. Owner CPU fields are elapsed deltas from
the same local thread/process clock pair. External child CPU is null unless genuinely
per-child accounting is available; RUSAGE_CHILDREN aggregates are forbidden, and
wait/reaping must not change to obtain CPU. The event list is capped at 256.
Allowed event names are exactly:
sample_enter, source_binding_before, proc_match, identity_x11_query,
identity_return, seal_open, seal_hash, lock_acquired, protocol_wait,
protocol_record, capture_started, capture_returned, png_publication,
identity_after_backend, identity_after_daemon, config_check, source_binding_after,
cleanup, response_ready, artifact_write. Unknown names, fields, enums, and bounds
are rejected. Repeated identity_x11_query events use only the bounded ordinal;
command text is never stored. If final artifact publication fails, no artifact
status is published; the fixed private write-failure log is the only record.

## Required tests and checks
The fixture must enter real daemon dispatch and capture_paused_region_sample with the
actual X11Backend and producer boundary. It must prove entry clocks exist before
directory creation, successful artifact mode 0600 and closed shape, all four barrier
records, explicit timestamps/durations, non-additive interval reporting, no
cross-thread/request mixing, and unchanged success response key sets. Failure tests
must prove:
- pre-admission identity refusal after directory creation preserves original
  phase/error and cleanup/lease evidence while retaining its separate profile;
- post-capture identity drift, source/config drift, cancellation, and deadline keep
  completion null and retain the original failure;
- forced artifact-write failure leaves the causal failure unchanged and the profile
  absent;
- descriptor replacement, symlink, wrong mode, size bound, and before/after fstat
  changes are rejected by the reader; a computed digest alone never authenticates;
- missing/mismatched supplied manifest blocks live mode before the first request;
- child CPU remains null with its fixed reason, no argv/path/identifier leaks occur,
  and a second owner thread cannot append to the first collector.
After Stage 1 implementation, run the full native and 65-check evaluator suites:

~~~
uv run pytest -q tests/test_session_native.py tests/test_session_performance.py
uv run ruff check src/crowley/session/driver.py src/crowley/session/daemon.py tools/gnome-telemetry-region/identity_latency_sidecar.py tests/test_session_native.py
uv run ruff format --check src/crowley/session/driver.py src/crowley/session/daemon.py tools/gnome-telemetry-region/identity_latency_sidecar.py tests/test_session_native.py
python -m compileall -q src/crowley/session tools/gnome-telemetry-region/identity_latency_sidecar.py
git diff --check
~~~

The performance file and evaluator contract remain byte-identical. Profiling overhead
must be reported and never used as schema-2 qualification or uninstrumented timing.
No live command runs until Sol reviews the Stage 1 diff, artifact contract, tests,
and expected-binding manifest. Implementation remains isolated in
/home/dev/.cache/crowley/worktrees/identity-latency-20261017; do not integrate,
restart, or alter the live service while native100 qualification is in progress.

## Stop, rollback, and later work
Keep the current identity path unchanged except for best-effort local timing.
Disable/remove the collector if it changes response bytes, deadline rules, cleanup,
or source/config/error preservation. Rollback never means using stale identity.
Stage 1 stops after fixture/static checks and three diagnostic responses are retained.
Any batching of same-observation X11 queries, persistent helper, direct native X11
implementation, or Rust consideration requires a separate plan naming future files,
interface, proof thresholds, tests, binding, and rollback. It cannot be inferred
from this four-file fence. The next decision is only whether measured identity wall
and owner CPU warrant that separate proposal; no computation bottleneck or
unattended scan qualification is claimed here.
