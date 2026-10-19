# Native capture ACK alignment correction

Status: APPROVED by Sol R2 and parent on 2026-10-19. Source implementation
and release qualification remain pending.

## Reason and precedence

Retain the [identity-budget plan](PLAN-native-identity-budget.md) and the
[alignment amendment](PLAN-native-identity-budget-alignment.md), except the
pre-backend rolling target and the source fence explicitly revised here.
Sol's diagnosis of snapshot125916Z found a genuine failure: alternating setup
is301.617ms before update1's shot and295.617ms before update2's. Admissions1s
apart therefore yield shots994ms apart and a duplicate. The reported1492.444ms
active value is not qualification evidence: the fixture measured provider
acceptance, misplaced producer/glue charges, and omitted the old deferred owner
validation. Preserve the rejected sources and reported result; do not tune
publisher phase, numeric vectors, cadence, ordinal acceptance or the900ms budget.

## Exact source/test fence

Allow only these six files; parent owns plans, evidence and Git:

- `src/crowley/session/daemon.py`: capability and run-local phase origin,
  bounded pre-ACK wait and synchronized continuation admission;
- `src/crowley/session/calibration.py`: exact provider/witness contract and
  runner lifecycle cleanup already in progress;
- `src/crowley/session/driver.py`: one private optional pre-ACK admission hook,
  threaded through `DesktopDriver.capture_native_region_for_identity` to
  `X11Backend.capture_native_region`;
- `tests/test_session_runtime.py`: actual-run model and semantic matrix;
- `tests/test_native_calibration_operator.py`: exact compiled-producer100
  composition and complete real diagnostic/observer collector;
- `tests/test_session_native.py`: directly necessary compiled-producer pre-ACK
  protocol, revocation, deadline and cleanup regressions.

No Guardian, lease, producer binary/protocol, addon, Rust, helper, service,
configuration, public command or receipt-schema changes. Generic/default calls
keep their existing behavior. The private optional hook is passed only on the
eligible native update path; do not break custom backends by passing a new
keyword when it is absent. No identity fence is removed beyond the originally
approved three duplicate resolves.

## Actual capture alignment

Remove the pre-backend admission wait. After update1 is provider-accepted,
retain its verified producer receipt's `capture_started` as immutable host
origin S1 and its exact decoded uint32 publisher `uptime_ms` as U1. Require a fresh receipt for this exact capture: output digest,
nonce/request, owner, binary, rectangle, retirement and original identity/run
bindings must agree. A diagnostic or caller-supplied timestamp is insufficient.
Keep this origin separate from existing admission-based `captureMonotonic` used
for freshness; do not restamp either field or convert publisher uptime.

The origin is provider-provisional until the same exact runner subsequently
requests N+1 after validating/releasing N. Keep boot, generation, run id, epoch,
reservation, original identity, source/backend and ordinal bindings. Clear it
on construction, replacement, failure and completion. Runner-post rejection
must prevent any later eligible use. Missing, malformed, future or mismatched
origin refuses. Never replace the origin with a later capture or retry.

Agent.lua recursively schedules `C_Timer.After(1)` after publication; the live
trace's2,014ms over two ticks demonstrates cumulative callback delay. For
eligible updates N=2..99 compute once:
`S1 + unsigned_delta(U_previous, U1) / 1000 + 1.000s + 0.050s`.
U_previous is the exact prior decoded publication, usable only after the same
runner validates/releases it and requests N. Use existing wrap-safe uint32
delta semantics, rejecting malformed, ambiguous/backwards or ordinal-inconsistent
values; preserve existing750..1250ms inter-publication validation. Bind every
uptime to its original retained frame/CRC/boot/sequence and run capability.
The50ms phase guard is constant, never multiplied by ordinal or accumulated.
This uses elapsed publisher deltas, cancelling its unknown clock offset without
restamping any timestamp. It does not assert a common host/game clock origin.
Qualification covers the pinned0..14ms callback-excess and update1 phase-age
envelope below, not every cadence allowed by the rejection contract.
Late setup must remain late; never roll the schedule forward, skip an ordinal,
retry a mismatch or hide an over-budget transition.

Invoke the private hook after the real driver has verified `owner_ready` and
the admitted executable/process, immediately before its existing ACK send.
The producer is already Guardian-registered and blocked awaiting ACK. This
absorbs backend-pre and lock/setup jitter before alignment. All three fresh
backend-pre/backend-post/runner-post resolves remain at their current boundaries;
post-capture evidence still refuses any intervening identity change.

Wait in chunks<=50ms outside controller, construction, Guardian and backend
process locks. Recheck shutdown, stop, controller state/generation, immutable
capability, run/epoch/reservation, lease, Guardian and expiry/deadlines between
chunks and after the wait. Use the same host clock and existing earliest frame,
operation, reservation and producer deadlines; never extend them. Reject a target
that cannot fit those deadlines. Count every guard and target calculation as
active work, with only actual sleep excluded.

The final ACK send must be synchronized, not a validate-then-send race. The
private callback contract is `(actual_producer_pid, dispatch_ack_once) -> None`.
The backend supplies the PID of its admitted Popen and a closure bound to that
exact process/nonce/socket/epoch. The daemon also captures the PID from the
existing observer-admission result and requires exact equality; it must not
trust a caller-chosen or merely registered PID. Immediately
before invoking it, acquire controller -> construction -> Guardian in the existing
order, validate the exact capability and unchanged observer-admission invariants,
require the exact producer PID in Guardian's observer registry and live watchdog,
held lease, unarmed Guardian, no unresolved held input/active input groups and no
release failure. Require nonblocking `Guardian.admission_gate_ready()` under
the Guardian lock. Do not call `_watchdog_state()` or wait for watchdog ACK
there. Use existing locks/health guards; do not register a second
observer or release its exec gate again. The dispatch closure then takes the
existing backend process lock, rechecks capture epoch, deadline, process liveness
and admitted executable/process proof, and sends the unchanged ACK once. No
sleep or readiness wait occurs under these authority locks. No-dispatch and
pre-dispatch exception must fail with zero ACK/capture. Reject second dispatch
before sending a second ACK. A second call or exception after the first dispatch
can have started capture: require at most one ACK, no accepted evidence and
complete cleanup, rather than falsely claiming zero capture.

Pre-observer revocation still requires zero producer starts. For a revoke after
spawn/before ACK, require zero ACK, zero ScreenshotArea call/capture, kill/reap,
empty Guardian/backend registries and retired attempt artifacts. Amend only
this later boundary's prior zero-producer wording. During/after-capture faults
still reject evidence and clean up. No new actual game input is introduced.

## Correct fixture before production changes

Correct the existing real-run fixture against the preserved current source first
and retain its genuine failing outcome with exact command, output, six-file
pins and first-shot timeline. Do not run another unlogged multi-run shell loop.
Parameterize the timing cases so one failing case can be reproduced alone.

Keep the real `NativeCalibrationRunner.run`, exact provider, deferred context
and reservation in every mode. Old mode disables only eligibility, restoring
outer, deferred-owner and poll resolves; it must not set `deferred=False`.
Publisher ticks are independent events driven by the selected pinned interval
vector and armed by the actual measure command. Every virtual-clock advance must be named active work or a real
production wait; remove hidden capture advances during the stream.

Add a test-only pixel-sampling callback immediately after actual Agent command
service and before reading `agent_frame`. Record every shot there, with ordinal,
sequence, boot, CRC, publisher uptime, host time and cumulative active/wait work.
Derive accepted shot boundaries from those records, not provider finish/decode.
Charge lock-to-shot before sampling, producer32.323ms immediately after it,
backend-post afterward and accepted glue after actual release/cleanup. Fabricated
model receipts must use that exact sampling timestamp as `capture_started`.
Retain screenshot attempts, including duplicates, and all actual guard counts.

After implementing the real pre-ACK hook, its external-device fixture invokes
that same callback after modeled verified setup and before sampling. It may
replace only external device/process pixels and actual sleep; production target,
guards, ordering, runner/provider, CRC and cleanup remain real. All capability
validation calls cost0.500ms and all target calculations0.050ms in this declared
model; count actual calls rather than eligibility spans alone. Additionally
charge each actual final synchronized ACK admission0.500ms for its new
registry/watchdog/held/release checks, excluding separately counted inner
capability validation. Report real durations separately. Existing backend
process-lock/process-proof/ACK work stays in the117.511ms gen37 lock-to-shot
total, never double-counted. Declare a model split of1.000ms of that existing
total after the wait and116.511ms before it; these are explicit phase-model
assumptions, not newly measured gen37 components. A boundary case moves5.000ms
of the same total after the wait, keeping the total unchanged. Retain actual
owner_ready/wait/ACK/capture timestamps in compiled-producer proof.

Keep the previously pinned reference, slower(+2/+2/+2ms), alternating
(odd+3/+1/+3, even post+1ms) and over-budget(pre+40/post+40ms) vectors unchanged.
Add publisher interval vectors1000ms,1007ms, and alternating1000/1014ms. They
drive the real Agent timer callbacks and payload uptimes, independently of
captures. The callback excess0..14ms is the qualified model envelope; the
750..1250ms validation contract is unchanged and is not a universal sampling
guarantee. Fix these combined cases before implementation, avoiding a full
Cartesian test explosion:

- Reference costs /1000ms publisher / update1 phase-age0ms /1ms ACK tail: pass.
- Slower costs /1007ms publisher / update1 phase-age500ms /1ms ACK tail: pass.
- Alternating costs /1000,1014ms publisher / phase-age0ms /1ms ACK tail: pass.
- Reference costs /1007ms publisher / phase-age900ms /5ms ACK tail: pass.
- Over-budget costs /1000ms publisher / phase-age0ms /1ms ACK tail: budget fail.
- Reference costs /1000ms publisher / phase-age951ms /1ms ACK tail: expected
  no-skip/protocol failure, not qualification.
- Reference costs /1100ms publisher / phase-age0ms /1ms ACK tail: expected
  retry/budget failure outside the qualified callback-delay envelope.

Initial phase age is the retained difference between actual Measure publication
and first actual shot. The fixture may schedule external Measure/device startup
timing to realize these declared initial scenarios before the stream origin;
record actual times and assert the named phase age. It must not introduce a
consumer wait or move a publisher phase after observing a failure. Passing
cases require phase-age<=900ms and every actual shot before the following
publication (no-skip envelope). Boundary negatives must refuse, not weaken
ordinal/CRC/cadence/freshness validation. Runtime live100 remains the final
qualification outside these declared model assumptions.

Passing cases must reach exact100 and<=900ms active per accepted streaming shot
transition. Include all retry work; report sleep separately.
Over-budget must visibly fail the budget without a fabricated protocol outcome.
Old/reduced-without-hook modes expose natural failure/overrun. Update99->held100
remains outside the streaming-work bound with all exact terminal proofs retained.

## Verification and release

Add actual driver/compiled-producer tests proving hook order, success, pre-spawn
refusal, revoke while waiting, final ACK race, expiry/deadline, unhealthy Guardian,
process/epoch replacement, callback failure/double/no dispatch and cleanup.
Use a real synchronization barrier and actual protocol observations; a recording
capture lambda cannot prove zero ACK or ScreenshotArea. Preserve the existing
eligible owner/identity negatives and actual fallback resolves.

Run corrected parameterized model cases, focused runtime/native negatives and
scoped Ruff/format/compile/diff checks. Capture full logs and source pins before
each long test. Send one honest checkpoint on a failure that needs a plan change;
never phase-tune the fixture or silently repeat multi-minute runs.

Parent inspects and reproduces focused checks before paid source review. Freeze
all six files and send the milestone before running the exact existing compiled
producer100 success node once. Sol and actual CLI Opus review the same final
delta; parent independently reproduces compiled producer100. Live native100,
ordinary recovery, genuine physical input calibration and three autonomous900s
full cycles remain required. Until then, the sole GUI owner performs ordinary
assisted recovery/collection; root owns any later quiescent install/restart.
