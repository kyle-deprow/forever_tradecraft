---
name: crowley-client-contracts
description: Diagnose or change Crowley's native WoW API, serialized scan format, and Lua test harness when validating addon-to-server behavior. Use for client contract fixes and live scan evidence, not ordinary watchlist edits.
---

# Crowley client contracts

Read `docs/HANDOFF.md` for verified facts and remaining assumptions, and the current
plan in `.archive/` for the active scope. Preserve the project's no-fallback rule:
encode the observed native contract and reject alternatives instead of hiding a
bad assumption behind a second decoder or guessed default.

Validate the installed entrypoint and real backend together. Manually calling mock
controller transitions or supplying calibration booleans does not prove an autonomous
session. Exercise captured native file/event fixtures before requesting live input.
Cover default service construction and its public calibration entrypoint.
When replacing a backend, compose the new pinned binary through that default
path. A separate component pass plus a legacy composed test that mocks identity
proves two separate paths. Bind the new binary/source pins and its actual fresh
invocations to the composed evidence before claiming integration.
Required meters and providers must be wired without manual fixture assignment.
For helper composition, drive the actual SessionDaemon/SessionIPC handlers;
scripted client replies cannot establish that the three production modes compose.
Pinned development dependencies permit offline composition before live acceptance;
finish assigned composition tests instead of deferring them as parent verification.
Before claiming completion, map each assigned race/deadline requirement to its
actual regression and result; a broad green total does not cover an omitted case.
In composed Lua/desktop fixtures, derive every served frame from the current
client, including initial captures. Change clients only after the actual accepted
reload action, using its written SavedVariables; assert deliberate inactive-control
refusals separately. Fixed frame indexes or uncaused scene swaps can hide broken modes.
Keep static-image seed clients separate from the active ordinary client; the
helper's emitted defer must perform the real unarmed-to-armed transition.
Bind recovery checkpoints to the active client's persisted marker token.
Retain accepted/refused command and control actions with actual boot and reload
changes. Compare their exact order at each phase boundary: post-pause recovery
cannot appear in a pre-pause expectation, and an empty expectation must prove
an empty history rather than skip assertions.
Derive phase deadlines and terminal controller states from the real producer's
lifecycle, not field names or scripted replies that preserve an earlier state.
Trace integration failures to the actual guard before blaming development inputs;
verify the exact constructor call before claiming an unavailable-resource blocker.
When a fixture tails an action log, consume only complete newline records and
validate PID/argument count before dispatch or ACK; retain an incomplete fragment
at its original offset. A missing ACK locates the boundary, not the cause.
Distinguish a reproduced interleaving from proof of the historical byte sequence.
For restart checks, create a fresh driver and owner without process-local evidence.
For owner-death tests, signal the actual helper owner PID, not its emitter child.
Prove independent release and reservation cancellation while that owner is dead;
a surviving test parent calling cleanup only proves child-failure handling.
SIGKILL bypasses Python finalizers, so it cannot prove bounded normal cleanup.
Exercise real owner return/exception through main while failed release stays pending.
Reconstructing only the controller around the same driver cannot establish which
calibration proof survives an actual process restart.
Start restart tests from the actual daemon dispatch/observation order. A journal
seeded with the desired result can hide overwritten attempts or impossible proof
flags that the real producer never emits.
Persist the pre-effect boot at dispatch; reconstructing it from a later frame
can turn a valid reload into an apparent mismatch and admit a second boot.
Native bootstrap and calibration startup cross a short freshness window. Prepare
a bounded helper that sends the public bootstrap/start calls back-to-back. Stage
the actual load action before bootstrap, then dispatch it through fresh guards as
soon as baseline readiness appears; a model-turn gap can expire the constructor
wait before the first frame. Keep observation timestamps and age limits intact.
For a staged handshake, compare each actual observation with the requested phase
and ordinal and verify the final resumed state. A valid schema or callback that
only checks arguments does not prove the production side effect.
Bind rolling metrics to the exact measurement window: a later valid frame may
have dropped measured samples. Verify boundary sequence and update count too.
Derive a native run's outer bound from actual provider invocations, including
per-update calls and finalization; four phase labels do not imply four waits.
Test archive recovery at every durable write boundary with a fresh owner; the same outcome ID
must retain the exact complete payload and resulting controller state.
Include a later pause/stop checkpoint in replay tests. Repairing an old outcome
must preserve newer operator state, even when its outcome commit number matches.
Inject real write failures at the first durable boundary; a duplicate writer that
bypasses the failed helper does not prove crash recovery.
Capture proof must carry the finalized per-call receipt through cleanup; a
callback that rereads a mutable last-receipt field still permits substitution.
Test that seam before consumption with identical pixels and different nonce/time.
Exercise terminal callback failures through the real runner and cleanup, not only
a newly extracted helper; successful notification does not prove failure ordering.

For a post-side-effect failure test, assert the side effect and pending ownership
exist at the injection point. A guessed callback count may fail before the reset
or dispatch and leave the intended cleanup branch untested.
For transaction-expiry tests, observe actual transaction entry; an identical
deadline error from an earlier outer check does not establish the inner guard.
An absent entry marker proves nothing if the fixture never enabled it. Arm the
entry barrier and prove a successful control creates that marker before using
its absence as a zero-side-effect oracle.
Fixture-barrier timeouts must fail the test, never satisfy an expected production
refusal. Bind lock barriers to the intended call site; the first nested acquisition
can block earlier while holding a lock the test itself then needs.
Keep the failing owner alive through its normal error handler before recreating
it from disk. Immediate owner destruction can hide a catch path that persists
partly mutated counters over the recoverable checkpoint.
After pause/retry, assert actual guardian ownership with a real driver. A
correct controller state alone cannot prove the next input action is armed.
Inject virtual time only into the simulated provider/runner. Globally replacing
stdlib time functions also changes guardian, socket and background-thread timing
and can conceal or manufacture lifecycle failures.
Round-trip blocked states and diagnostic metrics from actual Agent publication
bytes through the real frame decoder into the persisted artifact. Direct mock
snapshots or a black PNG beside copied metrics do not validate that path. For
nested decoded metrics, mutate the source after recording and verify the saved
values remain unchanged. Producer tables alone also miss unsupported reason enums.
For multi-observation admission, validate every consumed publication, including
an intermediate post-release barrier. A later allowed frame cannot erase an
observed failure. Test through the default provider and public daemon entrypoint;
calling the private gate alone misses ordering and invalidation defects. Combine
native-state failure with pose/chat drift so an earlier check cannot conceal it,
and assert both refusal-before-input and permanent clearing of retained proofs.
Lua API stubs must forward varargs to argument counters; fixed signatures discard
unexpected arguments before the counter can detect them. Assert exact failure
reasons and use distinct simultaneous failures when testing precedence.
Decide SavedVariables-dependent startup in `ADDON_LOADED`, with initialization
order covered by the harness: load files, inject saved values, then emit the event.
File execution alone does not establish that saved values have been restored.
When fence release also rearms a scheduler, test the real lifecycle through its
publication and commit, with the triggering event present. A setter-only test in
an already-ordinary load misses a release refused before lifecycle commit. Keep
failure cases free of live timers; label simulated event order separately from
client-reachable behavior.
For reviewed-source hashing, compare descriptor identity and metadata before and
after the entire read as well as the final path. Two matching late snapshots miss
an in-place change after bytes were read; test a real same-size mutation at EOF.

- Treat the Lua harness as a model to verify, not proof of native behavior. Check
  real payloads before declaring serialization correct. Native empty Lua tables
  become JSON arrays; nested empty collections matter as much as top-level ones.
  Fixture builders must reproduce that behavior. Keep negative wire fixtures
  malformed so an encoder helper cannot silently make a rejection test pass.
  Model search and sell-search separately; aliasing distinct native methods in a
  mock hid ignored commodity requests. Test API selection with mixed item kinds.
  Inspect returned query keys: zero arguments do not guarantee zero fields, and
  cache warming can change native item levels. Equipment comparison keys and
  ordinary recipe/container search keys follow different native contracts.
- Preserve original failed payload bytes. Validate any internal normalization
  separately from the wire contract and ingestion identity. Never edit a game's
  SavedVariables file to make an upload pass.
- Record actual query event order before changing freshness barriers. Installed
  Auctionator source can establish its call signatures and readiness checks;
  its implementation alone does not establish which events our live query saw.
  Use bounded diagnostics with sequence, item/attempt identity, dispatch, result
  and throttle events, readiness, quantity, and completion state. Diagnostics
  must not send extra queries or change scanner outcomes.
- An observation record does not prove an item was queried. Report attempted,
  unqueried, incomplete, and priced counts distinctly. Count attempts from query
  provenance, not reason codes alone: a sweep stop can mark both the active queried
  item and the unqueried tail with the same reason. Failure counters may include
  that tail and exceed attempted counts; validate them against planned counts.
  A timeout with zero rows
  does not establish an empty market. Inspect diagnostics before repeating a
  long sweep that has already produced only timeouts.
- Scanner completion can transition directly to `scheduled`, not only `ready`.
  Detect a fresh saved UID for the observed run, its pending ownership and terminal
  scanner state; preserve partial results too. Read actual start/finish timestamps
  from the published or saved run; a planned deadline or reused watcher default
  is not an observed start. Use actual finish time for upload latency.
- Verify stages independently: addon loaded, house/plan correct, scan saved,
  original payload accepted, real retained prices stored, acknowledgement loaded.
  A successful probe or zero-row ingestion proves only the stages it exercised.
  A typed `/reload` and logged Enter dispatch do not establish a reload: require
  its actual boot transition and stable SavedVariables containing the exact UID.
  Preserve the new payload after that save flush; a copy made before it contains
  the previous scan. Bind the copy's own hash rather than a later file's hash.
  Rebind decoder boot state only at the verified owned reload boundary, then
  require the new boot, exact identity and expected ordinary state. Retaining the
  old decoder can reject a healthy reload; arbitrary resets can hide boot drift.
  Reload writes the previous session before the new session consumes acknowledgements;
  a cleared in-memory queue can still appear in the saved file. Verify the written
  queue after a subsequent normal flush rather than claiming disk cleanup from chat.
  Separate when an acknowledgement was written from when an operator noticed it.
  Check UID and journal timestamps; a later periodic refresh is not publication latency.
  Parse queued scan/sweep keys rather than searching for a UID substring in metadata.
  The companion requests ACKs only for currently queued IDs; a later empty ACK list
  after pruning does not prove upload failure or retrospectively prove the loaded ACK.
- Test depth limits at N-1, exactly N with ties, and N+1 distinct prices. A complete
  market with exactly N levels is full/unbounded; bounded coverage requires a
  strictly higher witness. Keep the validator strict when producer metadata is wrong.
- Keep regression tests runnable without the deployed database. Use a disposable
  database for schema-changing tests; never point them at persistent Crowley data.
  Restore any companion service deliberately paused during a failed-upload loop
  after deploying the reviewed correction.
- If the host CLI auto-updates past the tested pin, distinguish that startup
  failure from source regressions and subsequent leaked-fixture lease failures.
  Verify an authentic private pinned binary before retrying. A private mount
  namespace may bind it over the default path for tests without changing the host;
  retain its hash, exact command, isolated writable cache/config paths and logs.
  Never fake version output or weaken the pin. Report host and isolated results
  separately, and exercise the real configured production adapter too.
  PATH does not override an explicit configured executable: inject the authentic
  pin through the fixture's configuration. Give fake desktop fixtures a private
  0700 XDG_RUNTIME_DIR so their leases cannot contend with the live daemon.
  Xvfb and a private bus do not isolate per-user screenshot locks. Bind the
  fixture's GNOME_CAPTURE_LOCK_PATH to its private directory before real backend
  creation, preserving the actual lock implementation. Never unlink the live lock
  to clear contention; identify its owner and clean up only the owned fixture.
  Default private session buses can activate desktop portals during GTK startup,
  before producer owner_ready. Give screenshot fixtures an explicit bus config
  with only required service directories; retain real GTK/protocol dispatch and
  scope accessibility environment settings to that fixture. Preserve Popen's
  process type when adapting its argv: driver isinstance checks require a class.
  Check publication cadence against decoded publisher uptime, independently of
  real capture-admission freshness and ordering. Keep the first observation of
  each publication as its timing anchor; repeated captures must not replace it.
  Advancing simulated Lua time does not pace real screenshot timestamps. For
  cadence proofs, publish the external scene on a real monotonic schedule and
  allow repeated captures of the current frame; never restamp captures to pass
  or add timing delays to production provider/admission wrappers in the fixture.
  Once Measure arms a modeled publisher, keep every tick on that independent
  schedule. Never disable or reanchor its next tick from a sampled screenshot.
  Assert actual initial phase age against the pinned case. A boundary negative
  must cause real refusal or visible budget overrun; merely being outside the
  declared input envelope cannot make a successful runner count as failure.

Update the relevant existing skill when live evidence disproves guidance; keep
incident dumps and transient client facts in the handoff/evidence files.

For native telemetry geometry, distinguish logical UI units, frame effective
scale and captured client pixels. Logical screen dimensions differing from the
window are normal when multiplied by effective UI scale; that difference alone
does not prove a render-resolution mismatch. A screen-size API can be stale under Wine;
verify a small temporary marker against the certified client capture before
encoding the transform. Measure scaled-frame anchor offsets too: a harness that
repeats an assumed SetPoint transform does not establish native semantics.
Validate atlas geometry/UV sampling from actual texture records and the asset,
then require native exact pixels/CRC. Texture-pool size is diagnostic rather
than proof of the rendered protocol.
