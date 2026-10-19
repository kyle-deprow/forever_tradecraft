# Native publication cadence correction plan

Status: implemented, reviewed and installed; live qualification pending. The
full native file passed 159 tests, parent focused and compiled helper checks
passed, and Sol plus actual Opus R2 returned READY. Opus R1's stalled-capture
and held/100 negative test requests were implemented without another production
change. The parent promoted the three files and restarted the paused service
after assisted scan #88. See the release verification in executor-review.

## Evidence and conclusion

The private timing profile is retained at
`/home/dev/.local/state/crowley/executor-evidence/native-publication-cadence-20261019/profile-r2.json`
(SHA-256
`b71253f0b6afb30bc0b155209f7b5fa4945e74c5cb48856799bfdba21d9d2817`). Its
sampler source is pinned at
`504089f68ddeff6ae3cf9b2cdfdcbea409261888b5a788e29a6fb3b49cafee77`.

The run contains one warmup and twelve actual captures from generation 26. All
actual decoded frames were ordinary, `nativePhase=normal`,
`nativeOrdinal=0`, and marked `FRESH`. They have one stable boot, sequences
39 through 51 with no gaps, and update counts 38 through 50. The producer and
configuration are pinned in the private report; the producer executable is
`gnome-screenshot` with SHA-256
`cb938cab1bd99dc088d05f6f55c8a0443401320755e2037633e7f9ac6dbe2396`.
Source pins before and after the run are identical, including the sampler and
the session CLI, config, decoder, driver, and protocol modules.

For the twelve advancing pairs, publisher `uptimeMs` deltas are 1000--1012
ms, while consumer capture-start deltas are 0.567253 s for the warmup-to-first
sample pair and 0.964056--1.006839 s thereafter. Receipt capture spans are
about 26.8--34.7 ms; strict decode spans are about 54.7--60.1 ms. This
distinguishes the publisher clock from the consumer capture clock under the
current producer. The profile is explicitly timing-only: it used ordinary
normal/0 frames without native ordinal claims and did not establish native
100 qualification.

This evidence does not reconstruct the original failed native update 1/2
frames. The retained earlier failure remains evidence of the old behavior,
not proof of which clock caused that run's failure. The implementation and
tests must preserve that limitation in their reports.

## Exact source and test fence

The implementation round may modify only:

* `src/crowley/session/calibration.py`
* `tests/test_session_native.py`
* `tests/test_session_native_regressions.py` (only the two native-runner decoded-frame
  stubs and directly necessary clock regressions; they currently omit uptime_ms)

No addon, daemon, driver, decoder, protocol, config, GUI, service, Rust, or
serialized-schema changes are in scope. `NativeRenderObservation` must keep
its current API. The existing `.protocol.unsigned_delta` helper is the source
of truth; do not duplicate or alter its wrap semantics.

## Correction contract

Keep the current validation and cleanup order for identity, phase, ordinal,
update count, capture artifact/hash/path, strict decode, boot, sequence,
metrics, binding, and artifact release. Keep `_validate_capture_time`
unchanged: capture monotonic values remain finite, non-negative, strictly
increasing, and no more than five seconds old at validation. Capture timing
continues to be checked independently of publication cadence.

The publication check must run only after the observation has been decoded and
all decoded binding, boot/sequence, phase/ordinal, update-count, identity,
metrics, and capture-freshness checks have passed. Track the last accepted
decoded `Frame.uptime_ms` alongside the existing accepted sequence and capture
anchors. The construction frame and update 1 establish that publisher-time
anchor; every accepted frame advances it only after validation succeeds.

For an update frame with `expected_phase == "updates"` and ordinal at least 2,
and for the held ordinal-100 check, compute:

```
publisher_delta_ms = unsigned_delta(current_frame.uptime_ms, previous_uptime_ms)
```

Require the inclusive integer range `750 <= publisher_delta_ms <= 1250`.
Zero, an out-of-range delta, and an ambiguous/backward uint32 delta are
publication-cadence failures. Preserve the existing bounded error/cleanup
behavior; do not restamp, infer, fall back to capture time, or widen the
range. A valid uint32 wrap with a small forward `unsigned_delta` must remain
accepted. The capture monotonic anchor must still be updated and checked
independently for every accepted frame, including the existing freshness and
ordering guarantees.

The runner must continue enforcing contiguous sequence/update behavior through
all 100 native updates, held-100 behavior, resume behavior, boot binding,
metrics binding, and terminal cleanup. Moving the cadence check must not allow
an observation with a bad phase, ordinal, sequence, boot, metric, capture, or
artifact to reach the uptime comparison.

## Required regression coverage

Add focused cases to `tests/test_session_native.py` using the existing Lua
client/runner harness and real encoded/published frames:

1. A positive capture-clock-skew case must make the consumer capture clock
   advance by a short but positive skew while the actual Lua publisher advances
   `uptimeMs` by about one second. The complete relevant runner path must
   succeed, proving that a capture-start interval is not used as the 1 Hz
   publisher guard.
2. A delayed (or otherwise too-fast) publisher case must keep capture timing
   finite, increasing, and fresh while the actual Lua frame's `uptimeMs` delta
   is below 750 ms or above 1250 ms. The runner must reject with the publication
   cadence error and release pending meter/artifact state. This must exercise
   the real Lua publication path, rather than changing only an observation
   metadata field.
3. Cover a valid uint32 uptime wrap, an ambiguous/backward delta, zero, and an
   out-of-range delta. The wrap is accepted only when `unsigned_delta` is a
   small forward value; ambiguous/backward and stale/zero values are rejected.
4. Retain or extend the existing lifecycle matrix for capture freshness,
   sequence gaps, boot changes, phase/ordinal mismatches, metrics/update-count
   failures, held ordinal 100, resume, and cleanup. Include assertions that a
   rejected cadence leaves no pending measurement and no unreleased capture
   artifact.

The positive and negative cases must assert the distinction between the two
clocks directly. Do not weaken the existing all-100 lifecycle assertions or
replace actual Lua frames with fabricated observations merely to exercise the
numeric helper.

## Verification and review gates

After implementation, the worker must run the focused new cases first, then the
relevant native test file, using the clean implementation worktree
`/home/dev/.cache/crowley/worktrees/native-publication-cadence-20261019`.
The scoped checks are:

```
uv run pytest -q tests/test_session_native.py
uv run pytest -q tests/test_session_native_regressions.py -k native_runner
uv run ruff check src/crowley/session/calibration.py tests/test_session_native.py tests/test_session_native_regressions.py
uv run ruff format --check src/crowley/session/calibration.py tests/test_session_native.py tests/test_session_native_regressions.py
uv run python -m py_compile src/crowley/session/calibration.py tests/test_session_native.py tests/test_session_native_regressions.py
git diff --check -- src/crowley/session/calibration.py tests/test_session_native.py tests/test_session_native_regressions.py
```

The worker must preserve the old failure log and all source pins, record the
new test/source hashes, and report the exact focused and full results. The
parent must reproduce the scoped checks and the live native run. Sol reviews
the source/test contract first; actual Opus performs the independent bounded
review after Sol. Only after both reviews and parent reproduction may the live
100 gate run, with fresh production evidence preserving decoded publisher
uptime deltas, boot, contiguous sequence/ordinal/update-count checks, capture
freshness, and cleanup. The final report must continue to distinguish the new
clock semantics from the unreconstructed original update 1/2 failure.

## Non-goals and risks

This is a measured clock-semantics correction, not a Rust rewrite or a capture
performance claim. Do not change the 0.75--1.25 second bounds, relax the
five-second capture age, alter serialized data, add a fallback, or claim native
100 qualification from the ordinary normal/0 timing profile. The main risk is
accidentally allowing an invalid observation to become the uptime anchor;
decoded validation must precede both the comparison and anchor advancement.

## Parent arbitration before Sol plan review

The two decoded-frame stubs in test_session_native_regressions.py around lines
8350/8411 also need valid publisher uptime so their existing HWM and boot-churn
contracts remain exercised. The file is added to the explicit fence for that
purpose, and its native_runner cases must run. No unrelated regressions change.
A stale/zero/backward uptime may already be refused by the unchanged decoder;
retain that earlier refusal instead of bypassing it to force a cadence message.
The new too-fast/late publisher tests must use forward but out-of-range uptime
(e.g.500ms/1500ms), so they reach the intended cadence guard. Preserve the original
failure cause uncertainty; source semantics plus current ordinary profile justify
the correct clock binding without claiming lost historical native frames.
