# GNOME ScreenshotArea telemetry-region plan

Status: **planning only.** This document authorizes no source edit, private build,
desktop/D-Bus operation, input, profile mutation, service change, or runtime
capture. It is the bounded design for one reviewed implementation, followed by
an eight-sample gate. Stock full-desktop capture and full-size model capture
remain the default until implementation, Sol review, Opus review, and parent
release are complete.

## Evidence and decision

The released timing receipt is
`/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark-20261017T042825821377Z-1280000/receipt.json`
(SHA-256 `bfc3f7093c306ff7e2db451401dfa9c75a632d5b3efac2be9ebaafcab8cf95a7`),
with parent validation in
`.archive/executor-review/gnome-no-flash-next-cost-parent-live-verification.json`.
It used the private GNOME Screenshot 41.0 no-flash binary (SHA-256
`b988bc4c49251c7951805b0af6ad942dd82d50052feffd338f5f6b72d43b025c`,
`-Dx11=disabled`) and production driver SHA-256
`14ae6be4a901a17e396e68ac4501238db3d1cc0118c8c34ad6f7107fbcfacfa7`.

One complete 28-marker sample measured command time `0.8208475 s` and the
identity-to-decode outer path `1.6741884 s`:

| boundary | seconds |
| --- | ---: |
| Shell D-Bus `Screenshot` call, including Shell-side work seen by client | 0.3571508 |
| Shell-produced PNG read/decode | 0.0289703 |
| final output PNG encode/write | 0.3467185 |
| recent in-memory entry | 0.0038828 |
| GTK/libhandy startup | 0.0548379 |
| command start through `run_return`, excluding post-marker tail | 0.8166375 |
| `run_return` to command end | 0.0042101 |

The outer value includes identity and crop/decode. Parent verification records
identity resolutions at `0.13147`, `0.12560`, and `0.12344` seconds; the
previous `outer - backend` value therefore cannot be attributed to crop/decode
alone. The after-backend crop/protocol/decode residual is approximately
`0.10440 s`. These values do not qualify a one-Hz run.

The accepted decision is one implementation: a source-controlled private
GNOME 41.0 binary that uses the existing typed `ScreenshotArea` backend path for
an exact 256x256 telemetry rectangle, with `flash=FALSE` and X11 disabled.
The requested pixel reduction is the causal reason to test this path. A
compression-only binary, a comparison branch, and extra full-desktop samples
are out of scope; no encoding change may be used to claim feasibility.

## Existing bindings and invariants

The accepted source hashes before implementation are:

| path | SHA-256 |
| --- | --- |
| `src/crowley/session/daemon.py` | `8d2a04aafe0672da80434e2b2c2981ccf2b5a9b7766a2c78a6dad119b1a0fcb0` |
| `src/crowley/session/driver.py` | `14ae6be4a901a17e396e68ac4501238db3d1cc0118c8c34ad6f7107fbcfacfa7` |
| `src/crowley/session/motion.py` | `ba3a6681ae66852db2d7abbdf8947bb6034fb9259779b473e211699105545d79` |
| `src/crowley/session/calibration.py` | `bb60a3449a20bd013c84973b672f528e658721b83481b0e8c0b6d6ca0bc1d6f1` |

The native calibration runner accepts 103 observations: construct, held/0,
updates 1..99, held/100, and resume. A successful observation has at least four
identity resolutions: the native poll check, backend before/after, and runner
capture check. The runner adds 99 update-boundary checks, runner entry, hold
boundary, and memory-meter checks: `103*4 + 99 + 1 + 1 + 1 = 514`, plus one
bootstrap check, excluding retries. A successful `NativeMotionProvider.observe`
has at least six identity resolutions; `observe_after_release` has at least 12;
route and viewport observations have at least five; `_confirm_motion_pose` has
at least six. Region capture may reduce pixels and crop/encode work only. It
must preserve every identity, process, generation, sequence, boot, timestamp,
admission, freshness, deadline, revocation, native-gate, and cleanup check.

The relevant source boundaries are `daemon.py:302-313` for the provider binding,
`daemon.py:473-483` for native bootstrap, `daemon.py:975-1012` for native frame
capture and retention, `daemon.py:1043-1174` for the measurement provider,
`daemon.py:1184-1192` for poll identity, `daemon.py:1881-1909` for
`capture_status`, `motion.py:383-467` for motion observations,
`calibration.py:4280-4610` for the native runner, and
`driver.py:2342-2405`, `driver.py:5639-5739` for secure full capture, crop, and
strict decoding.

## One genuine area producer

The implementation must be reproducible from these source-controlled files:

- `tools/gnome-telemetry-region/README.md` — pinned archive, patch, build,
  private prefix, explicit opt-in, and stock-default binding;
- `tools/gnome-telemetry-region/0001-typed-telemetry-area.patch` — the small
  GNOME 41.0 patch;
- `tools/gnome-telemetry-region/build-private.sh` — archive/patch/container
  hash checks, `-Dx11=disabled`, isolated private prefix, and ELF/version/help
  evidence; and
- `tools/gnome-telemetry-region/manifest.example.json` — archive, patch,
  container, option, binary, and build hashes; and
- `tools/gnome-telemetry-region/offline_harness.py` — compiled-option,
  receipt, process-admission, and exact-pixel self-tests.

The patch changes only the private noninteractive option/config path and the
telemetry branch; existing stock `Screenshot` full-screen, window, and
interactive branches remain unchanged. It must:

1. Require four typed integer coordinates and a private telemetry mode; reject
   missing, duplicate, conflicting, window, interactive, delay, pointer, and
   malformed options. Accept only positive `width=height=256`.
2. Pass a validated `GdkRectangle` through the ordinary application/backend
   interfaces. The existing `screenshot-backend-shell.c` `ScreenshotArea`
   call receives `(x,y,width,height,flash,filename)` with `flash=FALSE`.
   Interactive area selection, a delay, direct client D-Bus, synthetic output,
   and X11 fallback are forbidden. A Shell request failure is terminal.
3. Keep the output path lossless and exact. The parent checks the PNG format,
   dimensions, pixels, digest, and completion; no output setting may turn a
   failed or late area request into a success.
4. Emit the branch/owner receipt described below from the genuine canonical
   primary GApplication. `g_application_get_is_remote()` or the equivalent
   canonical owner result must prove that this process is the primary local
   owner; a forwarded/remote invocation is a failure.

The current source files and hashes for the private GNOME inputs are:

| source | SHA-256 |
| --- | --- |
| `screenshot-backend-shell.c` | `2abbdede110a4e01a0a7846db67551463210ddcae1d581b6cdce2d72403f22f4` |
| `screenshot-application.c` | `8af9588631633ff978696a1bf9a9fde5cc7025720239a70c544d1edd94246649` |
| `screenshot-config.c` | `401f7d44c4cd740f35001d865af3b0900b1e245eb12329fea555cdd86d4480d7` |
| `screenshot-utils.c` | `5bb40b7be34f1008a303bd04a31d90f896c59405f4e3018fa5d64fd2865fa7a6` |
| `screenshot-backend-x11.c` | `e94c412263789fa1d587b25665b5386171327e99aa9f0828ab2dba25ed79d029` |

The verified archive SHA-256 is
`4adb7dec926428f74263d5796673cf142e4720b6e768f5468a8d0933f98c9597`.
The binary belongs under a new private prefix such as
`/home/dev/.cache/crowley/gnome-telemetry-region-r1/prefix/bin/gnome-screenshot`;
no host package, system service, global PATH, or desktop setting changes.

## Retained executable and live-owner protocol

The region capability is dedicated; generic `_resolve_wrapped_executable` must
not be widened. The parent process opens the configured absolute binary with
no symlink following and close-on-exec semantics, verifies regular-file type,
owner, mode, and SHA-256, and retains that exact descriptor. It passes the
retained executable capability through the existing positive process-admission
and process-group mechanism (if that mechanism requires a helper edit, the only
additional production file permitted is `src/crowley/session/process_admission.py`).
A path lookup after validation is not sufficient.
The executed capability must be an immutable sealed memory image of those
verified bytes, following the existing input-image pattern; retaining a writable
on-disk inode alone does not prevent in-place replacement. Keep the input tool
module protected and place the narrow capture-image helper in `driver.py`.

For each request, the parent creates a private inherited pipe or socketpair,
seals a nonce, exact rectangle, output path, executable object digest, and
expected argv, and records the existing lease, revocation epoch, deadline,
identity fingerprint, process start, display, child XID, and profile-derived
rectangle. The child receives only this capability channel and exact typed
arguments. Its fixed protocol is:

1. After registration, the genuine binary emits a versioned `owner_ready`
   record containing nonce, child PID, child process-start value, parent PID,
   PGID, executable-object digest, canonical primary-owner/remote result,
   branch name, rectangle, and output-path digest. It writes this record while
   the admitted PID and active process group are alive.
2. The parent verifies the record against the actual admitted PID/process start,
   retained executable object, PPID/PGID and active process group, nonce,
   rectangle, identity, and exact argv. It sends a positive `ACK` only after all
   checks pass. The child must wait for that ACK before invoking
   `ScreenshotArea`; EOF, cancellation, deadline, a remote/forwarded owner, or
   any mismatch is terminal and must prevent capture.
3. The child emits a versioned `capture_started` record with the same nonce,
   rectangle, branch, output-path digest and monotonic capture-start timestamp, then
   invokes the ordinary `ScreenshotArea` call. It emits `capture_complete` only
   after the exact output is complete, carrying the output-file digest and
   byte count. The parent accepts the result only when all records, the
   capture-start timestamp, epoch/lease record, live-owner proof, and final
   PNG agree.

The existing parent capture-start timestamp remains the decoder/admission
timestamp. The child's later Shell-call timestamp is additional producer evidence,
must lie inside the request interval, and must never restamp or rejuvenate the
parent observation.

The parent records the proof while the child is alive; it never relies on a
post-exit `/proc/<pid>` lookup. Existing lease, cancellation, deadline,
termination, process-group, revocation, unique-attempt-directory, delayed
writer retirement, and final identity checks remain in force. The epoch is
checked before lock wait, before spawn, during owner/PNG waits, before
publication, and at replacement. There is no observer quiet sleep or hidden
retry. Every failure retires the attempt directory and exposes the original
failure; no late writer may recreate a published path.

## Driver contract, rectangle basis, and routing

The optional profile/session capability is explicit and default-off:
`telemetry_region_executable` is an absolute path paired with a required
`telemetry_region_executable_sha256`. Startup rejects a non-absolute,
non-regular, wrong-owner, wrong-mode, non-executable, or hash-mismatched file.
Stock `gnome-screenshot` remains selected when the capability is absent. No
process-wide environment or unreviewed PATH selection is allowed.

Add a typed, identity-bound region operation (the implementation may choose the
private method name) rather than changing generic
`capture_client_crop_for_identity`. It derives the sole candidate rectangle
from fresh identity and profile values:
`(child_x + crop_x, child_y + crop_y, 256, 256)`. Values must be finite,
integer, exact-size, contained by the verified client and desktop geometry, and
bound to the same fingerprint, process start, executable, display, and child
XID. No `(80,48)` constant, scaling guess, rounding, tolerance, alternate
offset, or post-capture crop is allowed.

The first region sample is a coordinate-basis gate: fresh identity, typed
rectangle in the owner/branch receipt, exact 256x256 lossless PNG, and strict
schema-3 HUD decode must all agree. Any mismatch stops the diagnostic.

The opt-in routing matrix is exact:

| path | region capability | stock full-desktop path |
| --- | --- | --- |
| native bootstrap absence/status artifact | yes | no |
| `_capture_native_frame_with_capture` and all native calibration/named-addon observations | yes | no |
| `capture_status`, including motion, transition, command-buffer, and closeout callers | yes | no |
| `NativeMotionProvider` through its actual daemon binding | reaches the rows above | no separate bypass |
| `_capture_model`, `_capture_model_artifact`, route/viewport model captures | no | yes |
| input calibration and unrelated full-scene/model consumers | no | yes |

The region rows preserve existing decoder, generation, deadline, boot, sequence,
freshness, native gate, retention, and public-entrypoint behavior. Tests must
traverse the real `SessionDaemon -> NativeMotionProvider -> capture_status`
binding, the actual native measurement provider, and one public daemon path.
No model or full-scene caller may select the region operation.

## Tests and staged gate

The implementation must add focused tests before any live release:

- `tests/test_session_capture.py` covers non-default profile-origin rectangle
  arithmetic, typed argv, retained executable/hash binding, owner/PGID/nonce
  pipe and ACK ordering, exact `ScreenshotArea` receipt, exact 256x256 PNG,
  wrong-size/format/full-desktop/stale/malformed output, deadline and epoch
  failures, identity drift, cancellation, delayed writers, and attempt-dir
  retirement. It also proves stock full-capture argv is unchanged.
- `tests/test_session_native.py` and `tests/test_session_motion_integration.py`
  use the actual provider, decoder, admission, and daemon public entrypoint.
  They cover bootstrap, `capture_status`, motion, transition, command-buffer,
  closeout, named-addon/calibration observations, generation/boot/sequence/
  freshness, model/full-scene exclusion, and failure cleanup. External model
  boundaries may be doubled; native producer, decoder, gate, and admission may
  not be replaced by booleans.
- `tests/test_session_preferences.py` covers the default-off profile contract
  and absolute path/hash validation. `tests/test_session_driver_actions.py`
  covers retained executable admission only if the implementation places the
  helper there.
- `tools/gnome-telemetry-region/offline_harness.py` exercises the compiled
  option parser's missing/duplicate/conflicting/
  malformed rejection, typed branch output, exact pixel fixtures, manifest
  hashes, owned-child/process-group admission, nonce pipe, ACK wait, cancellation,
  and delayed-writer cleanup. `--version`/`--help` are harmless parser checks;
  no test may substitute a fake native producer or gate.

The scoped implementation checks are `python3 -m py_compile` over the changed
Python files, the focused pytest files above, and
`python3 tools/gnome-telemetry-region/offline_harness.py --self-test
--self-check`; the private build recipe separately verifies its pinned source,
patch, ELF, version/help, and `-Dx11=disabled` evidence.

After reviews and parent release, the paused diagnostic uses the actual
configured `DesktopDriver` region operation and `PixelDecoder`, not a
phase-specific native calibration provider or CLI bypass. It predeclares no
more than eight monotonic start targets one second apart and waits outside the
measured path. Each sample records target, actual start, capture return, strict
decode end, every underlying attempt, exact rectangle, branch/owner receipt,
identity, boot, sequence, digest, and retirement receipt. It requires the
complete identity-to-region-to-decode path under one second, actual target and
accepted-sample intervals in `0.75..1.25 s`, one fresh boot, and strictly
increasing schema-3 sequence values. It does not assert contiguous or
no-skipped normal frames. A capture error, `NO_CHANGE`, late/wrong output,
identity drift, hidden retry, or cleanup error fails and stops the diagnostic.
No input, D-Bus setup, service, profile mutation, or model/full-scene region
selection occurs. This gate does not qualify the later 100-update run.

The formal native run retains construction, held/99-update/held-100/resume,
phase, publication, identity, freshness, memory, admission, deadline, and
cleanup requirements unchanged. A failed region gate preserves evidence and
leaves the stock producer selected; it does not weaken any native contract.

## Exact ownership fence and review boundary

The implementation fence is exactly these repository paths:

- `src/crowley/session/config.py`, `src/crowley/session/driver.py`, and
  `src/crowley/session/daemon.py`;
- `src/crowley/session/process_admission.py` only if retained-FD execution is
  implemented there, otherwise it remains protected;
- `deploy/crowley-session.example.toml` for a commented, default-off opt-in;
- `tests/test_session_capture.py`, `tests/test_session_native.py`,
  `tests/test_session_motion_integration.py`, `tests/test_session_preferences.py`,
  and `tests/test_session_driver_actions.py` only where the retained-FD helper
  is placed there;
- all five files under `tools/gnome-telemetry-region/` named above; and
- review artifacts named `gnome-telemetry-region-*` under
  `.archive/executor-review/` plus private cache/evidence paths named above.

No other production, test, data, generated, service, profile, renderer, HUD,
framing, model, CLI, or Git path may change. The implementation must report a
zero-out-of-fence diff and source/build hashes. It then requires Sol and actual
Opus review before the parent may release the paused eight-sample gate.
