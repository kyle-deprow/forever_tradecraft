# Region diagnostic through the existing desktop owner

Status: proposed R4 correction; Sol plan review precedes implementation.
Read `PLAN-region-composition-diagnostic-closure.md`, original region/R3 plans,
R3 freeze and R2 Sol/Opus reviews. This addendum supersedes only the diagnostic's
ownership/transport design and expands its exact source fence. Preserve the real
default-daemon composed test and truthful retirement changes already made.

## Problem and scope

The current diagnostic constructs a second DesktopDriver with a private lease
while the paused daemon owns canonical desktop.lock. This violates the live-proof
ownership contract. There is no existing owner IPC read-only capture operation.
Do not run that version live or spend the broad batch on it.

Own these files only:

- `tools/gnome-telemetry-region/offline_harness.py`;
- `src/crowley/session/daemon.py`;
- `src/crowley/session/cli.py`;
- `tests/test_session_native.py`;
- `tests/test_session_cli_motion.py` (existing IPC request tests);
- `src/crowley/session/driver.py` / `tests/test_session_capture.py`: existing
  truthful retirement fix plus narrow region admission/cancellation integration.

No new C/build/config/controller/model/input_tool/motion/calibration/addon/market/
service/profile changes, no live game/desktop/DB operations and no Git. No second
desktop owner, alternate production lease, temporary arming or broad fallback.

## Owner-side read-only sample

Add one explicitly named local IPC operation for a paused telemetry-region sample,
with an exact request field set, positive non-bool expected generation, finite
original parent monotonic start and absolute deadline. Restrict deadline to at
most one second after parent start; reject future/expired start/deadline values
against the owner's actual same-host monotonic clock. Enforce a strict overall
request budget including lock/identity/capture/evidence serialization work.
Unknown fields, bad types, absent owner and stale generation fail before capture.

Implement the operation on the already constructed SessionDaemon, using its
existing self.driver and configured native region producer. Require PAUSED,
unchanged generation, no active/bootstrap/calibration/interaction operation,
actual held canonical lease and unarmed state. Claim the existing shared motion/
capture intent fence nonblocking, rejecting busy rather than queueing. Do not
hold controller/state locks across desktop I/O; reread state at each admission
and after capture. Lifecycle pause/stop must remain able to revoke concurrently.

Use actual identity resolution and native region capture with the caller's
absolute deadline, verify the same identity before/after and original producer
binding. Return the actual TelemetryRegionReceipt, verified identity, source /
config / producer binding, exact PNG bytes as bounded base64, and truthful owned
capture cleanup state. Include owner-entry/capture-return times separately from
the original parent timestamp. No fake capture callbacks or post-capture
freshness restamping. Reject oversized images/metadata and nonfinite evidence.

Region producer spawn/registration/exec-gate release must participate in the
existing Guardian read-only observer fence. Register before releasing the exec
gate and unregister only after confirmed termination/reaping; a live backend
registry alone is insufficient for watchdog/revoke ownership. Bind the owner
PAUSED/generation predicate at actual admission, then check cancellation through
PNG publication. Reuse `observer_dispatch_admission` and existing observer ledger
rather than adding an alternate Guardian or modifying its implementation. Make
pause/stop revoke the backend capture epoch even while unarmed, preventing a
late producer from publishing. Keep lock acquisition consistent with lifecycle
operations (controller before Guardian/backend, no reverse nested acquisition),
and hold state locks only for bounded nonblocking admission, never capture waits.
Other input/observer/stock capture contracts retain their existing behavior.

Keep the operation read-only: no model call, native100/bootstrap measurement,
input emission, calibration/gate changes, controller tick/start or new driver.
The helper must never close/revoke the owning driver's lease or its watchdog.
Only the current capture's artifacts/processes may be retired. Serialize owner
operations through the existing capture fence, so empty capture registries can
be attributed to this capture rather than clearing another operation's state.

Artifacts must live in new owner-only per-request directories beneath the
configured private capture root, with no caller-supplied arbitrary path. Preserve
the owner-side published PNG and bounded atomic receipt on success and on later
state/decode/response/transport failure; no delivery acknowledgement protocol or
automatic pruning is in scope. For pre-publication producer failures there may
be no PNG or TelemetryRegionReceipt: preserve exact bounded error, failure phase
and truthful cleanup state without claiming absent artifacts. Backend failed
attempt archival is not required. Bound individual output size.

## CLI-side eight-sample runner

The existing offline harness --paused-diagnostic remains the sole opt-in command.
It loads the actual config, creates a new private evidence directory, uses the
real existing socket status operation and requests eight owner-side captures.
It must not instantiate DesktopDriver, X11Backend or an input Guardian. It never
copies a producer binding into an alternate in-memory profile. Unknown operation
from an old daemon fails before any sample; do not deploy/restart that daemon in
this implementation round.

Preserve the previous eight predeclared one-second targets, outer start before
status/IPC/identity/capture, strict target+1 deadline and full path under one
second, .75..1.25 adjacent start and completion intervals, exactly eight and no
retry/ninth bootstrap, fresh strict schema3 decoding, increasing sequences, one
boot bound from first fresh frame, exact producer/config/source/identity binding,
unchanged PAUSED generation before each and after run, and immediate fail-stop.

The owner capture response is evidence, not authority to skip decoder checks.
Validate exact base64/image size/dimensions/digest/receipt identity and times,
write each PNG privately and durably, and decode with the ORIGINAL parent outer
timestamp. Keep child capture times separately. Bound IPC response size before
JSON parsing; socket timeout is the remaining absolute sample budget. Validate
success/error response shapes and reject truncated, duplicate-key, oversized or
wrong-generation responses. Preserve failed evidence and atomically persist the
runner receipt including owner and client cleanup. Client cleanup never claims
the daemon was closed or its lease released.

For both IPC directions use one UTF-8 newline-terminated JSON record with fixed
limits: request at most4096encoded bytes including newline, response at
most524288bytes including newline; PNG at most131072bytes before base64, decoded
dimensions exactly256x256. These limits cover lossless RGBA output for the binary
telemetry surface and bounded proof metadata; reject overflow, never truncate
into acceptance. Bound reads BEFORE parsing or waiting for an unbounded
unterminated line. Use duplicate-key and NaN/Infinity rejection on both sides.
Existing newline request/reply connection semantics may remain, but each record
is complete, independently bounded and schema-checked; trailing data within one
record is malformed. Enforce the server request limit at the shared socket
framing boundary so malformed diagnostic input cannot bypass it before dispatch.
The harness uses the same strict bounded response parsing; no general streaming
protocol or unrelated request schema refactor is needed.

## Verification and completion

Offline fixtures may use a unique isolated lease because they own a private
Xvfb/D-Bus desktop. Make that distinction explicit in the fixture, never embed
it as a live runner option. Extend the real compiled fixture so the runner uses
actual SessionIPC + the owning real SessionDaemon and default driver/producer,
with only external window/Shell boundaries simulated. No replacing the native
capture method, decoder or protocol checks. Prove a single desktop owner.

Test stale/malformed generation, state/busy/armed refusal before capture,
pause/stop or generation change during capture, absolute budget expiry,
transport/malformed/oversized response, incomplete PNG/digest mismatch,
non-retirement, NO_CHANGE, identity/boot/sequence changes, late sample immediate
stop, preserved failed PNG/receipt, and continued owner lease/watchdog health.
Prove no input/model methods are invoked and status/stop remain responsive while
sample I/O is blocked. Retain the same-daemon stock model capture regression.
Specifically block a real gated producer before exec and prove concurrent stop
prevents execution/publication while retaining canonical lease/watchdog health.
Use socket-level tests for oversized unterminated requests/responses, duplicate
fields, NaN/Infinity and truncated/trailing records, plus normal existing
status/lifecycle compatibility. Distinguish post-publication preserved PNGs from
pre-publication failure metadata in tests.

Run targeted tests, actual compiled harness --self-test/--self-check, then the
affected host batch for capture/native/motion integration/preferences/driver
actions plus CLI tests. Confirm actual test filenames first; no known-bad memfd
bubblewrap namespace. Run scoped Ruff/format/compile and git diff --check. Freeze
all changed sources and write an explicit R3-to-final delta, real outputs and
remaining limitations. Parent reproduces before Sol and actual Opus source
reviews. No live profile opt-in or deployment is authorized by this plan alone.
