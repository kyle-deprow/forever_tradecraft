# Native observation budget and failure-evidence plan

Status: DIAGNOSTIC-ONLY IMPLEMENTATION VERIFIED AND INSTALLED after
Sol and actual Opus5.5 R3 READY, parent focused14 and independent135.08s actual
configured-producer composition PASS. No identity optimization is installed.
Parent scope decision: the first release is DIAGNOSTICS ONLY. No identity
resolve is removed until actual instrumented native timing is available and
a separate exact optimization delta is reviewed. Phase 2 is future work after
that evidence, not a prerequisite to the diagnostic-only release. This plan is for
Sol and parent review before any source or test edit. No live qualification is
claimed. The current MAIN source and installed service remain unchanged.

## Problem and bounded conclusion

Gen30 reached the native measurement phase, then failed at requested update 4
with `native updates/4 returned 'updates'/5`. The retained intervention record
is private and its exact reason is preserved below. It does not contain the
per-update producer receipt, decoded frame, or timing spans, so the historical
failure does not prove whether capture, publication, or identity work caused
the skipped observation.

The current path has five full identity resolutions for each accepted update,
before accounting for producer, decode, and cell validation work:

1. `calibration.py:4710` resolves before the provider call.
2. `daemon.py:4011` resolves in `_check_native_poll_identity`.
3. `driver.py:2864` resolves in the backend pre-capture fence.
4. `driver.py:3165` resolves in the backend post-capture fence.
5. `calibration.py:4608` resolves after capture during observation validation.

The identity-latency report measured individual full resolves at approximately
193--223 ms, including proc matching and X11 queries. Thus five resolves alone
can consume roughly 0.97--1.12 seconds. This is a measured budget pressure and
the leading explanation for update 4 observing update 5, but it is not a direct
reconstruction of Gen30.

The retained ordinary timing profile measured direct producer receipt spans at
26.8--34.7 ms and strict decode at 54.7--60.1 ms. It bypassed the full
DesktopDriver/Guardian/native-ordinal path and is qualified only as a timing
profile. It shows that the producer is not intrinsically a one-second stage;
it does not establish native-100 timing or explain the historical failure.

## Evidence and source pins

Gen30 intervention receipt:
`~/.local/state/crowley/native-calibration-operator/native-calibration-measure-deferred-20261019T090417229480Z-2302400-b25f4d31/receipt.json`
SHA-256 `e7891db61295f6e15474d3b286670e5fb8c7c5a63e369c5ee366175d570f14b6`.

The retained intervention archive is
`.session.json.archives/interventions/00000000000000000016.json`, SHA-256
`5d2f3a14ec86e506a1b07fb4cfbdeb0b7ddd5a891d7e0e4c1e9ed9d5b11a0431`, with
reason `native update 4 measurement failed: native updates/4 returned 'updates'/5`.
The retained native memory summaries are private and do not contain raw
per-update frames: construction archive SHA-256
`2cada4bd642649b9cb3423f759affb7dd5648f3bb509fc3c51d342204084fcdd`; updates
archive SHA-256 `eca46c50a21ea997357d8ed99e9f0a1807e274e606bea30cccc06461dadf93ee`.

Current source pins, confirmed before this plan, are:

* `src/crowley/session/daemon.py`
  `5c55f9b3080649cebf7bb57fbdcd14f69ddcbac83f5172500ba045c745d9ea58`;
* `src/crowley/session/calibration.py`
  `20fe37ca1bc8b69cae1aa8f3ce559ac08f822bd666243e303f249f4857a4a3ae`;
* `src/crowley/session/driver.py`
  `ca0ca123d0fa09d8361c8632d9cc1c2c501d87adf99cb3cc268688dd4291a166`.

The ordinary timing-only profile is
`~/.local/state/crowley/executor-evidence/native-publication-cadence-20261019/profile-r2.json`,
SHA-256 `b71253f0b6afb30bc0b155209f7b5fa4945e74c5cb48856799bfdba21d9d2817`.
The identity-latency report is
`~/.local/state/crowley/executor-evidence/runtime-relink/identity-latency-parent-binding-20261018/report.json`,
SHA-256 `5108a15568d243da2bcb777a6951014733ecf0f1e426ba5659b9ef3292d81a01`.

## Mandatory phase 1: bounded private diagnostics

Before another native attempt, add bounded diagnostics with no behavior change.
The trace must be in private failure evidence, not the public session journal.
It must be mode 0700 for its directory and 0600 for its JSON and any image.
It must never contain a raw path that is exposed as public state.

Keep a bounded ring of the most recent 16 attempts per run, so failures after
update16 retain useful context. Record and at most one offending 256x256 PNG. The
metadata for each attempt should include requested stage/ordinal, returned
phase/ordinal, boot, sequence, update count, publisher uptime, capture start,
source digest, candidate digest, and release outcome.

Keep the trace buffered in memory. Compute source/binary/protocol pins once
per run, outside the hot loop. Persist on failure/terminal boundaries rather
than synchronously writing JSON on every sample. Diagnostic overhead itself
must be measured/bounded. Fields for stages not reached must be null or
`not_reached`, never fabricated zero durations.

Record existing receipt timestamps when available: request start, lock,
acknowledgement, producer capture start/return, attempt retirement, and process
reap. Add spans for identity resolution, capture, hashing, strict decode,
copy, observation validation, and cleanup. Use monotonic finite values and
bounded JSON serialization. A trace failure must never mask calibration failure
or cleanup failure.

On an exact phase/ordinal mismatch, copy one private offending crop before
normal release, then execute the existing release and unlink behavior. On all
other failures, retain metadata only. Successful runs retain no new raw
artifacts. Existing normal ownership, cleanup, privacy, and public error
behavior remain unchanged.

The diagnostic record must include source pins, binary/protocol pins, run
identity, and an explicit `trace_schema` version. It must distinguish a
publisher observation from a consumer capture attempt and must preserve the
capture timestamp independently from publisher uptime.

## Mandatory phase 2: deterministic budget fixture

Add a self-contained fixture that publishes 100 frames at exact 1,000 ms
publisher intervals with contiguous boot, sequence, ordinal, and update count.
Inject measured 193--223 ms identity delays and the retained producer/decode
budgets with deterministic jitter. The fixture must show the current five-fence
path missing a publication at a bounded point, while the candidate path reaches
all 100 updates. This test must fail on the old path for the timing reason, not
because it simply asserts a new helper's return value.

The fixture must independently assert publisher uptime deltas of 750--1250 ms,
strictly increasing fresh capture timestamps, exact contiguous sequences, and
artifact cleanup. It must include identity mutation before backend capture and
a mutation after capture; each must still refuse. Wrong phase, skipped ordinal,
wrong boot, bad metrics, and stale capture must retain their existing failures.

The fixture may use a deterministic clock and producer, but it must not replace
the actual native protocol, serialized schema, or production cleanup assertions.
Existing exact skipped-ordinal coverage in
`tests/test_session_runtime.py:2232-2261` remains required and must continue
checking that owned paths and native-evidence PNGs are gone.

## Candidate optimization after diagnostics

Keep the backend pre-capture and post-capture identity fences at
`driver.py:2864` and `driver.py:3165`; they bind the produced pixels to the
current client and are not removed by timing pressure. Keep the independent
post-capture observation identity check initially.

The first candidate is to stop the daemon poll loop from doing a redundant full
identity resolve in `_check_native_poll_identity` after context, generation,
capability, and admission checks have passed. Backend pre/post fences and
observation validation remain the replacement safeguards. Implement this only
if the phase-1 trace confirms the budget and the fixture proves both identity
mutation cases still refuse.

Do not remove the calibration update-loop identity resolve at `4710` or the
post-capture resolve at `4608` in the first candidate. If measured totals still
exceed the budget, propose a second separately reviewed removal with an explicit
replacement invariant and failure test. Do not remove safeguards by inference.

No producer protocol, addon, GUI, service, Rust matcher, decoder schema,
configuration, lease, Guardian, or public receipt changes are in scope.
Do not restamp capture time, infer publisher time from capture time, retry
blindly, widen cadence bounds, or fall back to ordinary frames.

## Small source/test fence for implementation

The implementation round may modify only:

* `src/crowley/session/daemon.py` for bounded private trace; any later
  poll-loop identity optimization needs the phase2 review gate;
* `src/crowley/session/calibration.py` only if a directly measured observation
  span requires a narrow trace hook;
* `tests/test_session_runtime.py` for the deterministic budget/cleanup fixture;
* `tests/test_session_native.py` or
  `tests/test_session_native_regressions.py` only for directly necessary native
  timing, trace, and identity-drift regressions.

No other source, test, helper, addon, driver, decoder, protocol, service, GUI,
config, Rust, or schema file may change without a new reviewed plan.

## Verification and live gates

For the first diagnostic-only release run focused trace, failure retention,
identity-drift, cleanup and existing wrong/skipped-ordinal tests. The phase2
budget fixture is required only for the later optimization. Preserve exact
existing assertions for normal capture deletion; the isolated diagnostic copy
is separate from owned transient/native-evidence files. Run the directly
affected native/provider tests, Ruff, format check, Python compilation and
`git diff --check`. Legacy runtime tests have known stale stub/default desktop
lease failures already reproduced on the baseline; do not run unrelated
full files or weaken the live lease to force them green. If a relevant known
failure blocks focused verification, isolate the fixture within reviewed scope
and prove its original failure on the unchanged baseline.
Record commands, exit codes, source hashes, private trace hashes, and cleanup
results in 0600 logs before and after each run.

Parent must reproduce the focused and scoped checks. Sol reviews the exact
source/test delta; actual Opus performs an independent bounded review. Only
after both reviews and a stable source freeze may one fresh native attempt run.
That attempt must preserve the old Gen30 failure evidence and retain per-update
trace metadata before cleanup. It must prove all 100 exact contiguous updates,
750--1250 ms publisher deltas, independent capture freshness/identity, and
terminal cleanup. No native-100 claim may use the ordinary timing profile.

The release report must state whether the observed mismatch was directly timed
or remains a budget hypothesis. It must identify any retained offending frame,
all source/binary pins, and the exact cleanup result. This plan is complete only
after parent verification and the Sol/Opus review gates; writing the plan does
not authorize implementation or a live retry.

## Approved R3 test-only scope exception

Sol and parent approve extending only
`tests/test_native_calibration_operator.py` in the existing actual composed
operator success test. This already runs the real NativeCalibrationRunner,
daemon provider, configured X11Backend and compiled region producer for100
updates. Assert same-attempt ordered finite five identity spans, correct fresh
receipt digest/nonce/retirement, release outcome and same-thread latency-sink
restoration. This exception adds only the fifth test file; the original four-file
scope still permits the accepted narrow diagnostic correctness fixes from R2.
No application-helper change or identity optimization is authorized.
The four R2 source/test pins remain frozen while this independent fifth-file
test edit and check run. R3 reviews cover the assertion delta, its actual success-case result, and the
accepted narrow R2 diagnostic correctness fixes before installation. Do not duplicate the fixture
or replace the production configured-producer path with a stock fallback.
