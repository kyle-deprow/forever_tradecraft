# Native region production lifecycle closure R5

Status: parent releases corrections required by Sol source R4. Preserve all R3/R4
freezes and negative receipts. This is a bounded rewrite of the remaining scope,
not another broad exploratory round. No deployment is authorized by this plan.
Keep primary R4 source frozen for the already-running actual Opus review. Root
releases implementation only in the isolated worktree
`/home/dev/.cache/crowley/worktrees/region-r5-20261017`, detached at8c98469 with
the verified R4/R3 source overlay recorded in `gnome-telemetry-region-r5-isolation-baseline.json`.
Compare edits against that hash baseline, not only Git HEAD. Read plans/reviews
from primary, write owned source only in the worktree and R5-only review metadata
under primary executor-review. Root integrates after reviews and checks.

## Requirements and ownership

Read original region contract, R3/R4 plans/freezes, Sol source R4 and actual Opus
R4 output. Own only:

- tools/gnome-telemetry-region/0001-typed-telemetry-area.patch
- tools/gnome-telemetry-region/offline_harness.py
- tools/gnome-telemetry-region/README.md and manifest.example.json
- tools/gnome-telemetry-region/build-private.sh: only update EXPECTED_PATCH_SHA
  to the actual R5 patch digest; retain every other build/cache/image/argv rule.
- src/crowley/session/daemon.py and driver.py
- tests/test_session_native.py and tests/test_session_capture.py
- src/crowley/session/cli.py and tests/test_session_cli_motion.py: absolute
  bounded socket response deadline and capture-only late-failure evidence tests.
- deploy/crowley-session.example.toml: commented/example producer path/hash
  updated to the actual R5 build; no real profile or service edits.
- R5-only metadata/review artifacts in .archive/executor-review/gnome-telemetry-region-r5-*

No Guardian/controller/model/config/input_tool/motion/calibration/addon/market/
backup/globaltool/profile/service edits or actual desktop/game/DB operations.
No Git mutations. Keep sole canonical owner, default-off config, stock model route,
strict capture/decoder, one-second diagnostic deadline and all cancellation gates.

1. Enable the C active-primary guard after successful canonical owner ACK and
before asynchronous capture starts. Keep it active through terminal one-shot
completion/failure. A foreign ordinary command must be rejected before shared
capture options are touched. Compiled private-bus test: hold actual first Shell
capture, invoke ordinary non-telemetry command on the same canonical application,
assert nonzero refusal/no second Shell request/no second output, then release and
complete the original request. A second telemetry invocation alone is insufficient.

Private compiled fixtures must isolate the screenshot serialization file from the
actual desktop: patch only test `GNOME_CAPTURE_LOCK_PATH` to an owned private
fixture path while exercising real `_capture_lock`/flock checks. Current broad
parent run317pass/1fail shows lock deadline expiry at sample0 of the no-change
case; the tests currently share the real desktop's global lock with the live
operator. This is an isolation gap, not proof of the competing lock holder or
live computational latency. Preserve that failure and the actual lock-security
and cross-process serialization tests. Never substitute a production desktop
lease or disable locking to obtain a pass.

## Actual Opus R4 adjudication

Actual claude-opus-5-5 completed exit0/NEEDS WORK. Read its complete retained
`gnome-telemetry-region-opus-r4.txt`; parent accepts these reachable corrections:

- The semantic hash must describe loaded configuration, not runtime anchors.
  Snapshot canonical loaded configuration at daemon construction and separate
  runtime-measured profile/anchor state. Compare live driver configuration against
  that immutable snapshot while explicitly excluding only documented runtime
  fields. Preserve every real configured field; no crop/producer-only shortcut.
  Prove a real installed measured anchor does not break later owner IPC, while
  changed actual configured fields still refuse before admission.
- A capture-cancelled backend must refuse up front with a specific reason before
  directory creation/capture. Do not clear input revocation to enable diagnostics.
  Test actual armed-then-paused ownership. For this slice a fresh unarmed owner is
  required after retained capture cancellation; document that limitation.
- Save bounded owner failure response before validating any optional sample.
  Preserve phase/error/artifact metadata even when the sample fails validation.
  Include active and retired attempt-directory patterns in cleanup evidence, and
  take the failure cleanup snapshot while the motion fence is still held.
- Make lock nesting controller -> Guardian -> backend consistent. Move admission
  health checks out of backend process-lock sections; preserve health checking
  before exec release. Close admission-gate write descriptors on every rejection
  after spawn. Test rejection/reaping/descriptor ownership at the actual boundary.
- Preserve strict one-second sample qualification. A capture-response read may
  have an explicitly bounded evidence-only grace of at most250ms after that
  deadline solely to retain a late failure response; it never qualifies a late
  sample, retries capture, or extends the producer deadline. Generic socket reads
  must use an absolute response deadline, not reset the full timeout per chunk.
  Label unavailable late evidence unknown and retain actual owner receipt.
  Record nonsecret pending protocol stage/lock-acquired/ACK timing where available;
  never dump arbitrary producer stderr or private payloads into public evidence.
- Test late-response/changed-identity fault injections actually follow a successful
  owner capture, and add one real supervised serve positive/paused-collision case
  instead of claiming the custom fault-injection socket loop is that production
  composition. Keep fail-closed busy behavior and no additional desktop owner.
- The generic producer exit0/output race may re-check the same strictly bounded
  fresh attempt PNG once after confirmed exit0; never relax owner proof, accept
  old output, or make this a fallback capture route.

The active-primary C guard, private fixture lock and complete success-receipt
publication are already required above. Set the C guard before asynchronous
capture can accept a foreign command; the synchronous owner handshake must not
leave a forwarded command able to reparse shared state.

Defer Opus's duplicate-identity optimization: it is a measured-cost proposal,
not a correctness blocker, and needs its own matched performance evidence and
typed after-identity receipt contract. Preserve existing identity guards here.
Generic permissive-getattr style comments are not independent production defects
when actual constructor invariants are mandatory; still refuse missing required
owner state rather than inventing evidence in any modified production path.

2. Cover the actual default daemon/native-motion production route with Guardian
observer admission and confirmed-reap unregister, not only paused diagnostic IPC.
Bind current controller generation/state at actual admission under the existing
controller-to-Guardian lock order. Every production X11 region producer must be
registered before exec release; do not leave an accidental callback-free route.
An explicit low-level offline fixture boundary may remain. No locks held over
capture waits; pause/stop remain able to revoke while unarmed. Compiled default-
daemon blocked-Shell races must prove stop-before-admission prevents exec, and
admission-before-pause/stop revokes epoch, prevents publication, reaps/unregisters
producer and retains healthy canonical lease/watchdog. Do not merely repeat the
already-covered paused diagnostic route. Preserve bootstrap and stock model capture.

3. Publish one complete final success receipt after final timestamps/schema/size
validation; never write preliminary ok:true. Failure publication remains bounded
and preserves any actual PNG. Test every attempted publication and missing-final-
field/write-failure cases without inventing a successful receipt.

## Build and verification

Use existing reproducible build-private.sh without global installs or overwriting
R3 cache. Build once to /home/dev/.cache/crowley/gnome-telemetry-region-r5. Preserve
source/archive/image/package/patch/binary digests and real build logs. Bind fixtures
explicitly to the new authentic binary. Do not edit old freezes to match new code.
Parent authorizes the required expected-patch digest update in the isolated
build script. Other recipe changes still require a concrete scoped report.

Run new focused regressions through real compiled C / private D-Bus and Xvfb /
production default daemon / strict PixelDecoder, plus existing owner IPC runner,
capture and CLI tests where affected. Run scoped Ruff/format/py_compile/diff and
actual harness self-check/self-test. No fake constructors or status gates, weaker
deadlines, swallowed thread errors or private lease substitutions. Retain timing
failures as negative evidence; a later pass does not erase them.

Return exact changed files/hashes, actual command output/exit statuses, source-
binary freeze and all unresolved findings. Root reproduces focused checks, then
Sol and actual Opus review the final integrated source before live opt-in. Run
one appropriate broad batch after focused/source closure, avoiding blind repeats.
