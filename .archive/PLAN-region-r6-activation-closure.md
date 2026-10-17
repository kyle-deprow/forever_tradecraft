# Native region R6 activation/action closure

Parent adjudicates actual Opus R5 Must-Fix1, Should-Fix2 and the alreadyclosed
forwarding test gap as reachable, and accepts the narrow comment/failure-stage
corrections below. SolR5R2's early test cleanup gap is also concrete. This is a
new bounded closure, not another broad exploratory review of all prior work.
Read the full R5 plan/freeze, actual OpusR5 output and SolR5R2 report from main.
Existing R3/R5 binaries, source freezes and failures remain immutable.

## Isolation and ownership

Work ONLY /home/dev/.cache/crowley/worktrees/region-r6-20261017, based at2a8d73e
with12hash-verified R5 source overlays including forwarded-testhash47ac2cef.
Primary `gnome-telemetry-region-r6-isolation-baseline.json` binds that baseline.
Own exactly:
- tools/gnome-telemetry-region/0001-typed-telemetry-area.patch
- tools/gnome-telemetry-region/build-private.sh: EXPECTED_PATCH_SHA line ONLY
- tools/gnome-telemetry-region/README.md and manifest.example.json
- tools/gnome-telemetry-region/offline_harness.py
- src/crowley/session/daemon.py: exact profile comparison comment/fields and
  explicit not-started producer failure evidence only
- tests/test_session_native.py
- deploy/crowley-session.example.toml: actual R6 producer path/hash only
- R6-only metadata under main .archive/executor-review/gnome-telemetry-region-r6-*
No driver/CLI/Guardian/controller/model/config/addon/input-tool/backup/market
edits, real GUI/display/game/profile/services/DB operations or Git mutations.
Do not commit/reset/stash/revert others. All default-off/soleowner/identity/
strict decoder/admission/reap/one-second/absolute IPC deadline guards remain.

## Required changes

1. In the TELEMETRY process, reject/ignore GApplication activate and EVERY
app-action handler before modifying shared options or starting other capture/UI.
Use telemetry_region_arg (set before registration) rather than relying only on
active flag set after ACK. Preserve the original own command-line handshake and
capture; preserve normal nontelemetry invocation behavior. The existing foreign
command-line guard and runtime flock stay intact.
2. Compiled private-bus evidence must invoke genuine valid D-Bus Activate,
ActivateAction and org.gtk.Actions.Activate routes for both screen-shot/window-shot
actions while the actual Shell capture is blocked. Handle synchronous main-loop
queueing with staged real child RPCs and release, not invented handlercalls or
waiting for return while holdinggate. Prove those actual routes reached their
telemetry guards, no extra area OR stock Shell request/output/dialog capture,
and the original capture completes. Keep the separate-runtime forwarded-command
proof with exact primary stderr plus same-runtime flock refusal. Cleanup must
cover the ENTIRE post-capture-thread-start interval: any assertion/setup/dispatch
failure releases markers, joins capturethread and reaps every started child.
No fakePopen, stubguard, weakened deadline or global desktop owner substitutes.
3. Fix actual fake RecordingBackend native-provider regression identified by
Opus: assert production X11-only native refusal/no regioncapture and retain stock
model half; real positive route is the compiled test. Do not restore fake-backend
acceptance in production to satisfy this stale test.
4. Driver no longer writes runtime anchors into profile.anchor_fingerprints.
Remove stale explanatory comment/exclusion in `_driver_profile_matches_config`
so independently copied profile compares every real configured field. Measured
anchors remain in separate runtime state. Preserve actual anchor IPC success,
config/profile drift refusal and default profile deep copy.
5. Represent producer-not-entered failures explicitly, e.g. stage not_started
with null request_started/lock_acquired/ack_sent. Owner identity failure before
producer must retain original phase/error and durable ownerfailure; harness must
accept this typed unavailable state rather than remask as malformed attempt.
Never fabricate clock values, claimcapturestarted, clear revocation or accept
unknown evidence as a completed sample. Add meaningful actual externalidentity
failure regression through ownerIPC/runner where feasible; no fakeconstructor.

## Build, checks and freeze

Build genuine C changes once validated to NEW cache
/home/dev/.cache/crowley/gnome-telemetry-region-r6 using exact pinned recipe/image/
archives/dependency/argv rules; only expectedpatch digest changes. Prepare private
0700 XDG runtime in the container invocation as documented in R5. Preserve every
failed build/fixture log and earlier binaries; never overwrite R3/R5 caches.
Bind tests and example to actual R6 producer/manifest/patch hashes, not renamedR5.

Run focused compiled defaultdaemon and paused8sample native nodes, changed
fakebackend regression, scoped Ruff/format/py_compile/source diffcheck plus actual
harness self-test/self-check. No broad reruns now: parent's frozenR5 affectedbatch
is still collecting other regressions. Root independently reproduces finalchecks,
Sol and actual Opus review final R5->R6 delta/integratedsource, then appropriate
broad verification on finalsource. Retain prior concurrent3process PNG-readiness
failure as unresolvednegativeevidence; no blanket live-reliability claim.

Return exact changedfiles/hashes, actual commands/results, new source/binary freeze,
R5->R6 delta and all unresolved findings. DONE only whencomplete; no deployment.

## Parent scope amendment: observed PNG publication race

R6 serial composition logs `focused-composition-r6.log` and
`focused-composition-r6-retry.log` reproduced the earlier concurrent PNG failure:
the decoder observed an incomplete image, then process.poll observed exit0.
Parent and independent Sol source diagnosis confirmed `_wait_for_complete_png`
fails using that stale pre-exit read. Completion can occur between those two
operations. This does not establish that every prior PNG failure has this cause.

Extend ownership by exactly two paths (ten total):
- `src/crowley/session/driver.py`: `_wait_for_complete_png` only;
- `tests/test_session_capture.py`: deterministic regression for that helper only.
The earlier prohibition on all driver edits is superseded only for this helper.

After an incomplete read, retain poll's result. A nonzero exit remains terminal.
For exit0, perform one final validation bracketed by the existing epoch check.
A valid final PNG may return; an incomplete final PNG fails immediately with its
fresh diagnostic, and invalid output remains terminal. No sleep, new retry loop,
deadline extension, source fallback or weakened protocol/identity guard. The
caller still verifies authenticated completion, nonce/branch/rectangle/path,
exact byte count/digest, image dimensions, zero exit and original deadline before
publication. A final read cannot bypass those checks.

Use a deterministic helper regression where initially truncated output becomes
complete inside poll before it returns0. Also cover clean exit with still
truncated output and revocation winning before the final read. A small fake
process is appropriate for this exact unit interleaving; compiled composition
and the real eight-sample runner remain the end-to-end evidence. Preserve all
failed logs and recheck the final source/binary rather than rerunning unchanged
failures until one passes. Sol and actual Opus review the added delta.
