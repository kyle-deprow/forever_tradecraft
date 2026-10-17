# Region composition and diagnostic closure

This rewrites the remaining task after R3, rather than repeating the broad
implementation rounds. R3 source/binary are frozen, not accepted or deployed.
Parent reproduced19focused tests and the actual compiled producer harness.
The remaining demonstrable gaps are in composition and diagnostic evidence.
Read original contract, R3 closure plan, R3 freeze and both R2 source reviews.

## Exact scope

Own `tools/gnome-telemetry-region/offline_harness.py` and
`tests/test_session_native.py`. `tests/test_session_capture.py` and
`src/crowley/session/driver.py` may change only to test/fix truthful capture
retirement evidence, without changing the capture protocol or unrelated paths.
No C patch, rebuild, config, daemon, model, input_tool, motion, calibration,
addon, game/profile/service/DB or Git operations. Preserve the R3 binary/cache
and source freeze. Review artifacts may use `region-composition-r4-*`.
Work only in `/home/dev/repos/pegasus`, never the old isolated checkout.

## 1. Close one real composed path

R3 harness lines330-393 stop at X11Backend and compare a static PNG. Its
separate daemon test still substitutes RecordingBackend.capture_native_region.
Do not call those two disconnected tests the complete path.

Extend the private D-Bus/Xvfb compositor fixture so one test captures a valid
schema3 CRS1 surface from the ACTUAL compiled R3 GNOME producer through:

`SessionDaemon.motion_provider.observe -> capture_status -> DesktopDriver ->
X11Backend -> sealed image/admission -> GNOME ScreenshotArea -> complete PNG ->
PixelDecoder -> MotionFrame`.

Construct a real region-enabled SessionDaemon through its real constructor and
default provider binding. Preserve the actual DesktopDriver and X11Backend;
do not replace their capture methods, the decoder, MotionFrame, protocol checks,
freshness gates or admission proofs. Simulate only external game/window/Shell
boundaries on the private display/bus. A faithful recorded window resolver or
low-level external query fixture is acceptable; counters and identity checks
must still execute. Never touch the real desktop or WoW process.

Use an actual WindowIdentity and a non-default supported canvas origin. Render
valid pixels from the shared real Lua/CRS1 test harness, with advancing sequences
for subsequent observations. Do not invent booleans saying a native gate passed.
Use the authentic private Codex0.162.1 binary via explicit fixture config if the
constructor needs CLI startup; no fake version or installed-global modification.
Exercise actual bootstrap/native-frame capture and `_capture_model()` on that
SAME opted-in daemon, proving the latter selects stock full capture. A model
call is unnecessary; test its image-capture boundary with an external compositor
response. Assert actual frame contents, rectangle, live receipt, strict decoder
and cleanup. The private compositor may serve both native and desktop PNGs;
the real producer and parent remain intact.

## 2. Make the eight-sample diagnostic real and runnable

Replace R3's unbound object callback facade. It currently guesses status.boot,
stamps decoder time after capture, substitutes clock() for missing evidence,
sets retired=True without proof, and never enforces the subsecond/interval gates.

Provide an explicit opt-in mode on the EXISTING offline harness CLI, requiring
the real config path and a new private evidence directory. No extra standalone
helper or new project CLI. Default remains offline self-check/self-test.

- Load actual SessionConfig. Require the reviewed producer path/hash already
  configured in its profile; do not modify the profile or bind an alternate
  in-memory provider. Use actual DesktopDriver/X11Backend and strict PixelDecoder.
- Read the actual controller IPC status via the existing socket request path.
  Current response shape is `{'ok':true,'status':{...}}`, status is a DICT with
  `state`, `generation`, `boot`, `nativeBootstrapPending`, `calibrationOperation`
  etc. Require PAUSED, no in-flight operation and unchanged generation before
  every sample and after the run. Do not fake status/config/boot objects. A paused
  controller can retain an OLD boot: bind expected boot to the first actual
  decoded sample, require all eight fresh frames match, and record both values.
- Predeclare eight one-second targets before sampling. Use no ninth bootstrap
  capture or retry. Resolve identity through the actual driver; require unchanged
  PID/start/window fingerprint and source/config/producer binding throughout.
- Start the outer monotonic interval BEFORE status/identity/capture work. Pass
  that original parent timestamp to PixelDecoder. Read actual backend
  TelemetryRegionReceipt: request_started, ack_sent, capture_started,
  capture_returned, epoch, output digest and retirement. Never restamp or use
  clock() defaults for absent fields. Preserve the child timestamp separately.
- Give each capture an absolute deadline at target+1second. Require entire
  sample path duration<1second and adjacent actual starts AND completion
  intervals within0.75–1.25seconds. Require finite timing values, exact target
  spacing, same identity/boot, strictly increasing sequences and valid digests.
  Late/missing/NO_CHANGE/invalid samples fail immediately and stop further work;
  do not collect seven more samples before deciding the first missed its budget.
- Retirement must come from actual receipt and observable empty owned process
  registries/no attempt directories. R3 driver currently sets attempt_retired
  unconditionally after ignore_errors cleanup: fix that flag if necessary, never
  manufacture success in the diagnostic. Use actual available cleanup APIs;
  DesktopDriver has no release_native_capture interface. Do not invoke input
  actions or clear held-state/calibration just to clean a read-only diagnostic.
- Keep failures and complete PNG evidence in the new private directory; write an
  atomic JSON receipt with failure phase and cleanup state. Do not delete failed
  sample files in finally. This is a diagnostic, not native100 qualification.

Offline tests must execute runner stop/timing/cleanup logic at external I/O
boundaries, rather than test only eight manufactured record dictionaries.
There must be no real display/status request during self-test/self-check.

## Completion

No live run. Actual R3 binary private composed fixture and new negative tests
first, then affected host batch if production driver/native tests changed;
scoped Ruff/format/compile and explicit file hashes. No bubblewrap executable
memfd environment (known EACCES). Complete implementation, tests and freeze;
do not stop after a plan or candidate. Preserve a concise R3-to-R4 delta and
map both requirements to actual regression tests. Parent checks before Sol and
actual Opus source review. Any opt-in live binding remains a later root step.
