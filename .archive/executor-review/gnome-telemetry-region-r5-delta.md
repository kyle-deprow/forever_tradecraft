# GNOME telemetry region R5 lifecycle closure

R5 closes the three accepted R4 lifecycle issues in the isolated worktree and
keeps the original default-off profile capability. Production native region
captures now enter Guardian observer admission under the controller-generation
fence, register the producer before exec release, and remove the registration
only after confirmed reap. Controller/Guardian/backend lock ordering is
consistent; health checks occur before gate release, capture waits hold no owner
locks, and rejection paths close the admission-gate descriptor. A private
compiled default-daemon fixture proves both stop-before-admission refusal and
admission-before-stop cancellation while the external Shell call is blocked.
The producer is reaped, no PNG is published, and the canonical owner lease and
watchdog remain healthy. The same fixture confirms the foreign ordinary
screenshot command is refused while the actual telemetry capture is primary,
before a second Shell call, output file, or shared-option reparse.

The compiled composition test carries the authenticated R5 producer through the
actual X11 backend, DesktopDriver, Guardian observer ledger, SessionDaemon
native bootstrap/provider, strict PixelDecoder, and MotionFrame. The captured
native data advances by sequence, and _capture_model() remains on the stock
full-desktop screenshot path. Only game-window identity discovery and the
external Shell/Xvfb boundary are simulated. The private test sets its capture
flock path beneath its owned fixture root and still exercises production
_capture_lock and flock checks; it does not touch the user's desktop lock.

The eight-sample runner remains opt-in and uses the existing daemon owner IPC.
It binds every loaded SessionConfig field through canonical semantic hashing,
keeps the raw TOML hash as provenance, and checks the independently copied
runtime driver profile against that immutable config. The real default
constructor path installs a sealed measured anchor and succeeds on later owner
IPC; changed configured driver fields and changed config values refuse before
admission or Shell capture. The runner preserves the original parent start
monotonic time, actual owner receipt and PNG, enforces a strict sub-one-second
sample deadline and 0.75–1.25 second sample intervals, stops on the first
failure, and records durable failure evidence and cleanup. It creates no second
DesktopDriver, Guardian, or input lease.

The retained-capture revocation proof uses a real armed Guardian epoch and
registered read-only XI2 observer, then pause/reap and a specific
capture-revoked refusal. That owner cannot be reused. To exercise the subsequent
capture race without clearing revocation or forging state, the fixture resolves
the persisted STOPPED intent with a real fresh-owner start() then pause(),
closes that transition owner, and reconstructs the final owner from its
legitimate PAUSED journal. The final owner is asserted PAUSED, intent-free,
unarmed, unheld, lease-owning, and backed by a fresh uncancelled X11 backend
before its capture enters the blocked Shell call.

The final focused runs passed:

- Compiled default-daemon/native route and stop races: 1 passed in 4.30s.
- Actual owner-IPC eight-sample runner and negative cases: 1 passed in 38.35s.
- Capture suite: 32 passed in 10.25s.
- CLI-motion suite: 16 passed in 1.32s.
- Ruff, format, compileall, py_compile, private harness self-test/self-check,
  and source-path git diff --check passed. The complete unfiltered diff check
  reports the single required blank context marker at line 119 of the unified C
  patch artifact; the patch was successfully applied in build attempt 04 and
  its exact digest is bound by the binary manifest.

Focused failures are retained without being relabeled: attempt 14 was
interrupted during an invalid same-owner lifecycle path; attempt 15 caught an
incorrect assertion that Guardian revoke must set the backend cancel event even
when no backend epoch was active; attempt 16 reached the compiled producer but
exhausted a 25-frame fixture table on the 26th real call; and attempt 17 caught
an indentation error at collection. Those causes were corrected and the exact
final runner rerun passed. The earlier R4 owner protocol deadline expiry before
Shell capture remains a separate open review item recorded in the R4 freeze; a
passing private fixture does not erase it or establish live timing reliability.

Performance evidence remains limited. Existing preserved-frame replay measured
strict PixelDecoder at 54.54ms median / 60.65ms p95 and PNG loading at 0.64ms
median. R5 records per-sample PNG load, decoder, and duration fields in the
private runner, but it does not produce an aggregate benchmark. Real desktop
owner IPC, Shell capture, transfer, and end-to-end cost remain unmeasured; no
Rust implementation or new benchmark was added.

Build attempt 04 is bound to the R5 patch digest and produces private binary
7f7080c82f0c403373480ac24e0f5ec22587c04716e9dc081a897751e2db46b3 with manifest 6f2a9f1752ff2b5ae3d3fe350fad044cf9867ac1d4af5785bb7c7be4bea9cf01. The R5 build script differs from
the exact frozen R4 script only in the authorized EXPECTED_PATCH_SHA line.
R3's cache was not overwritten and no further binary was built. There was no
live desktop run, profile opt-in, deployment, service change, or Git operation.

The canonical review freeze is
.archive/executor-review/gnome-telemetry-region-r5-freeze.json
(SHA-256 307c6ef69ba4c8b7376af4307852b12fcb55a57da3c1df84c3ef1fc4ddda2bf2). It lists all twelve source hashes, the R4/R5 baseline,
build provenance, test/log hashes, and retained failure history. The source is
ready for parent reproduction and Sol/actual Opus review; live opt-in remains
outside this closure.
