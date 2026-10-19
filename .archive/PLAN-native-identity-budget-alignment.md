# Native update capture alignment amendment

Status: APPROVED by Sol R2 and parent. Implementation remains isolated; no installation before the source and verification gates.

## Objective and retained requirements

Amend [the approved identity-budget plan](PLAN-native-identity-budget.md), not
replace its identity, owner, source, CRC, ordinal, cadence, cleanup or review
requirements. The exact four-file source/test fence remains unchanged. Keep all
three fresh backend-pre/backend-post/runner-post identity checks. No driver,
Rust, addon, helper, protocol, Guardian, lease, public API or deadline changes.

The first candidate's isolated configured-producer100 test passed, but parent
rejected its timing replay. The replay manually implemented the runner loop,
inserted a wait absent from production, dropped residual glue and temporarily
added a non-evidence capture delay. That pass is not budget qualification.
Sol independently confirmed these defects and supplied an actual-run fixture
design. Luna must preserve its genuine outcome before alignment is enabled.

The measured gen37 vector remains 1,384.569ms, with only the three full resolves
(226.079 + 142.073 + 140.391ms) removed: 876.026ms active work. Preserve the
0.040ms outer-gap residual. An unaligned 876ms path can capture a duplicate before
the next 1,000ms publication, then pay for another full attempt. All retry work
is active work; it cannot be renamed alignment wait or ignored.

## Production change

Align only exact eligible deferred `updates/2..99` captures. Update1 retains its
real readiness polling. Construct, held0, held100, resume, ordinary operation,
custom/wrapped providers and nondeferred contexts retain their current paths.

Use the previous accepted update's existing host `captureMonotonic` (admission
before backend-pre, already used for freshness), plus the nominal 1.000-second
publisher interval, as the earliest admission time for the next eligible
capture. Anchor in the host monotonic domain. Do not convert publisher uptime
to host time or restamp any publication, capture or receipt timestamp. Since
backend-pre and producer setup follow admission on both samples, stable setup
cost gives approximately one second between actual screenshots as well.

The daemon stores a provisional provider-accepted anchor before the runner
finishes validating that observation. Do not label it runner-accepted at that
point. It is consumable only when the same live exact runner subsequently calls
the next ordinal: `run()` validates/releases N before requesting N+1, and any
runner hash/identity/cell/decode/cadence rejection terminates that run. Retain
private anchor bindings for ordinal N, generation, identity, boot and deferred
run/epoch/reservation. Construction, run/stage replacement, completion or failure
clears it. Prove with a runner-post rejection that no later eligible provider
call or anchor consumption occurs. Never derive an anchor from held0, a
rejected/duplicate attempt, a prior run, an arbitrary caller or a later ordinal.
Missing/malformed anchor state after eligible update1 refuses rather than
silently waiving alignment. Future/nonfinite timestamps and inconsistent
ordinals refuse.

At provider entry retain the existing frame deadline. Wait, when needed, before
the next capture admission and outside controller/construction/Guardian locks.
Use bounded chunks of at most50ms in the same monotonic clock domain; between
chunks recheck shutdown, controller generation/state/stop request, the immutable
capability and operation/reservation expiry through existing cheap guards.
Never extend any deadline. Refuse if a target cannot be reached before either
deadline, and revalidate immediately after waiting before capture. A revoke or
shutdown while waiting must start zero producers. Keep actual observer-admission
validation under the existing lock order and all fresh identity fences.
Every capability-validation invocation performs active process/profile/Guardian/
lease/deadline work, including invocations made between wait chunks. Count and
charge each actual invocation at its real production site. Only the duration in
the sleep primitive is intentional wait; target calculation and guard execution
are active. Retain their call counts and durations in the timing evidence.

Apply alignment at the real per-attempt boundary, with a valid prior accepted
update anchor. A duplicate still follows the actual existing rejection/poll
path. Do not move the anchor forward to disguise retries, skip a requested
ordinal, slow the publisher, relax cadence, or accept stale evidence. If timing
jitter still causes cumulative active work to exceed the budget, preserve that
failure and stop for a separately reviewed resolver/performance change.

## Actual-run timing fixture

Replace the manual replay with `_runtime_daemon` + `_NativeProviderBackend` and
the exact daemon-installed provider, executing `NativeCalibrationRunner.run()`.
Reuse existing sealed preconstruction, archive, memory-reset and real Agent
command callbacks. Inject the fixture meter clock so reset completion and runner
timestamps share a domain. Use a genuine configured private executable/digest
profile; never force `_native_region_enabled=True` for this proof.

Schedule independent1,000ms publisher callbacks from the actual measure command.
Advancing virtual time at any real boundary fires every due tick. The fixture
may replace the external device process/pixels and wall-clock wait, but must keep
the real runner, provider, eligibility, capture/admission, decode, validation and
cleanup lifecycle. The real Agent supplies pixels/CRC/sequence/metrics. Charge
named gen37 costs at actual diagnostic or identity/capture calls, not in a
parallel ordinal loop. Preserve fresh backend pre/post barriers and process
admission/reaping in the external device seam. Use a trace state machine for
the small residual edges; do not invent delays or drop them.

Exercise three modes through that same fixture: old full-resolve graph;
reduced graph with production alignment disabled through a private test seam;
and the accepted reduction plus actual production alignment. The first two
must report their naturally observed failures/budget overruns, never hardcoded
ordinal pairs. Only the third may qualify. Assert 100 exact publications
(updates1..99 then held100), runner evidence/seal, contiguous sequence/ordinal/
update count, boot/CRC, unchanged publisher cadence, increasing capture times,
three fresh eligible identity fences and automatic resource cleanup.

From each accepted updates/1..98 screenshot boundary to the next accepted
updates/2..99 screenshot, accumulate all active named charges, including every
duplicate/retry. Require <=900ms per transition; report actual deliberate wait
separately. Do not impose <=900ms on update99->held100: held100 intentionally
retains the full identity path and the publisher stops advancing in that held
phase. Report that terminal transition separately while retaining exact held100
sequence, cadence, identity, memory-window and cleanup requirements.

Pin these numeric model cases before implementation. All retain the full exact
gen37 vector, charging0.500ms for every actual fast capability-validation call
and0.050ms for every actual alignment-target calculation. Those new-work costs
are explicit model assumptions, not measurements from gen37; report real
diagnostic durations separately. Do not reduce the assumptions to obtain a pass.

- Reference: unchanged named vector plus these counted new-work charges; expect
  aligned exact100 and active<=900ms for each streaming transition.
- Slower backend/setup: add2ms each to backend-pre, backend-post and lock-to-shot
  on every attempt; same expected pass.
- Alternating: on odd screenshot attempts add3ms backend-pre,1ms backend-post
  and3ms lock-to-shot; on even attempts add only1ms backend-post. Same expected
  pass; count retries and apply the vector by actual attempt, not requested ordinal.
- Over-budget: add40ms each to backend-pre and backend-post on every attempt.
  Expect a visible active-budget failure; retain the actual protocol outcome
  rather than forcing a particular skipped ordinal.

If a proposed passing case fails, report that failure for review instead of
changing its clock phase or numeric vector. Report the tested envelope, not an
arbitrary-jitter guarantee. The aligned fixture replaces only the private sleep
primitive for waiting; actual production target calculation and rechecks execute.
No fixture-only pre-provider wait is permitted. The qualification must fail when
production alignment is disabled or deleted.

## Negatives, real composition and release

Retain the original plan's complete eligible semantic matrix and ineligible
actual resolve counts. Add alignment negatives for stale/malformed anchors,
owner/generation/run/boot replacement, shutdown/revoke during a real wait,
deadline/expiry during wait, no locks held across sleep, and fresh identity
change after waiting. Pre-admission faults start zero producers; later faults
reject evidence and clean up. Do not replace the whole capture or admission
function with a recorder to establish those claims.

Complete all focused negatives and actual-run timing cases, scoped Ruff/format,
compile and diff checks first. Parent inspects and independently reproduces them.
Freeze exactly the four source/test hashes; send the milestone before running
the exact configured-producer success integration once. Its observer/diagnostic
collector must retain all attempts and all accepted lifecycle stages before ring
pruning, including per-update fences, receipt/digest/retirement and timing proof.
Sol and actual CLI Opus review the same frozen sources. Parent independently
reproduces the real configured-producer100 integration. Corrected source/tests
require new pins and justified reruns, not reuse of the rejected candidate's pass.

Only after all gates pass may root promote and restart the quiescent daemon.
The sole GUI owner continues assisted scans until the concrete release boundary.
Live native100 plus ordinary recovery, genuine physical input calibration and
three autonomous900s full cycles remain required. No offline pass establishes
live qualification.
