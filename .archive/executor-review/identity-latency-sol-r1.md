# Sol source review R1 — native identity latency Stage 1

Candidate reviewed: `/home/dev/.cache/crowley/worktrees/identity-latency-20261017`

Verified inputs:

- plan `.archive/PLAN-native-identity-latency.md`: `397bccaa859a7e39c31eef7555aa5f10764dd63329f118478e4004ac5ca2d685`
- freeze `.archive/executor-review/identity-latency-r1-freeze.json`: `4d4fb627c17b5abb488f2b4129a3a515dfe57fda827c3a86c4323d0bb3645922`
- full four-file delta `.archive/executor-review/identity-latency-r1.diff`: `8c0ca9118f1366719da55e9a04c38911e560bd0338bb07d151b5fc0df598b76f`
- `src/crowley/session/driver.py`: `a216d009ba3ee5a0cf0a9e9d731c6e79dcc311fa4e328743446ab9b342f0b59e`
- `src/crowley/session/daemon.py`: `3fc24b08010f2823cf1efa127a832c625e6a22b185263f08140d119a8972fe60`
- `tests/test_session_native.py`: `8ee0efa006539d3a09c674de8fb0a39a318a9c50a10d7c9864d549c118805058`
- `tools/gnome-telemetry-region/identity_latency_sidecar.py`: `b994f363ea5aefcda99fd8d0cc5a91c592bd5d7ae76d6e6cd37dd63e9281488d`

The owner-side implementation has the right basic shape. The collector starts before request-directory creation, is request-local through a `ContextVar`, records the four unchanged identity barriers, leaves child CPU explicitly unknown, bounds its event list and private artifact, and writes only after the existing cleanup and receipt paths have preserved the causal result. The production response shapes and capture/Guardian guards remain intact. The descriptor-bound artifact and expected-manifest readers also enforce type, mode, link count, size, and before/after identity checks.

## Must-Fix

1. **Live mode does not enforce its accepted binding and owner-state preflight before the first sample.** `tools/gnome-telemetry-region/identity_latency_sidecar.py:514-535` authenticates the expected manifest, but it never compares `args.config_file_sha256` or `args.config_semantic_sha256` with that manifest before copying those values into the requests. It also never sends the required status preflight. A caller can therefore supply a valid reviewed manifest plus different request hashes and the tool will create the raw directory and issue all three sample commands; `_binding_consistent` at lines 391-403 detects this only after capture/refusal. Before creating evidence or sending a sample, compare both supplied config hashes with the manifest, query status through the existing IPC client, and require an `ok` PAUSED status with the exact generation and no stop, closeout, action, reconciliation, bootstrap, or calibration operation in progress. Guardian admission remains authoritative for the unexposed physical armed/held state. Refuse the run on any malformed or mismatched preflight.

2. **The sidecar weakens the established IPC deadline and record-framing contract.** `tools/gnome-telemetry-region/identity_latency_sidecar.py:480-494,521-533` implements a second socket client with a relative 1.25-second timeout on each blocking operation. It does not bind transport time to the request's absolute one-second deadline plus the 250 ms evidence grace, does not half-close the request, and accepts bytes after the first newline without proving EOF. A slow or multi-record peer can therefore extend the bounded run or be accepted where `src/crowley/session/cli.py:550-630` refuses it. Use the existing client with `response_deadline=request["deadline"]` and `failure_evidence_grace=0.25` for each sample, and use the same bounded client for status without the paused-sample grace. Add transport tests for a delayed response and trailing data.

3. **The emitted diagnostic drops the only owner-CPU and substage measurements.** `tools/gnome-telemetry-region/identity_latency_sidecar.py:406-455` validates the artifact's events and then emits only wall-time barriers and the two broad intervals. All `owner_thread_cpu_ns`, `owner_process_cpu_ns`, per-query timings, and the explicit unknown-child-CPU reason are discarded. The resulting CLI report cannot support Stage 1's stated decision about identity wall time versus owner CPU. Include the bounded, validated event records in each sanitized sample or emit a closed per-event/per-barrier summary that retains wall/thread/process CPU separately. Do not sum nested `identity_return`, query, or protocol events.

4. **The tests do not exercise the required live or failure boundaries.** `tests/test_session_native.py:147-206` checks a partial artifact and a bad manifest digest, while `tests/test_session_native.py:1688-1741` checks successful artifacts produced incidentally by the existing eight-sample composition test. No test invokes `_run_live`, proves a manifest/request-binding or status mismatch sends zero sample requests, covers the absolute deadline/grace and strict framing, forces artifact publication failure, inspects profiles from identity/source/config/cancellation/deadline failures, or proves request/thread isolation. The descriptor-race monkeypatch also fails at the first comparison rather than proving the final fstat/path check. Add focused tests for those accepted-plan cases and assert the original response phase/error/cleanup remains unchanged. These tests should also prove that the repaired report retains the useful CPU fields without identifiers or paths.

## Should-Fix

1. **Raw response storage accepts an existing or symlinked directory.** `tools/gnome-telemetry-region/identity_latency_sidecar.py:517-519` uses `mkdir(..., exist_ok=True)` followed by path-based `chmod`; this follows a caller-supplied symlink and permits an old/nonempty directory. Since the files contain full private owner responses, require a fresh, owned, non-symlink 0700 leaf (or descriptor-bind and verify an explicitly reusable empty directory) before any sample. Keep the exclusive 0600 response-file creation at lines 459-477.

## Nits

None.

STATUS: NEEDS WORK
