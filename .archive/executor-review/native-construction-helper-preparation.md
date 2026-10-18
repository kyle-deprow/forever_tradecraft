# Native construction helper preparation

Status: dependency preparation only. This note does not release the helper, authorize
input, start a daemon, change configuration, or claim live qualification. The helper
slice starts only after the accepted native construction slice and its source review.

## Provenance

The private retained source pair was checked byte-for-byte without invoking either
script:

- reviewed snapshot: 447 lines, SHA-256
  `bf79d703cc9b98fc7e0842d119e69cbbfa5539f02456f8d5083d4629bdeee2d0`;
- current snapshot: 461 lines, SHA-256
  `d5530fbd7085478c481e6004608f7d3068e48b5da0c67f05cec9db9376a13466`;
- exact 27-line delta SHA-256
  `7b2f59ca6e5059942897af041c986bd713686c1064e572cab21e490553650cb5`.

The delta changes only `handshake()` admission to require a prior terminal
`construct/0` failure and then retry legacy bootstrap/calibration. It is explicitly
excluded from the future helper: no terminal retry, automatic retry, deadline
extension, or retry-specific error admission is carried forward. The reviewed
fixed-action guards are the only source pattern retained.

## Future ownership and transport

The future source/test fence is exactly:

- `tools/native_calibration_operator.py`;
- `tests/test_native_calibration_operator.py`.

Read-only production dependencies are `src/crowley/session/guardian.py`,
`input_tool.py`, the config loader, `X11Backend`, the protocol decoder, and the
session CLI. The native implementation plan fixes closed IPC request shapes and
transport: `SessionIPC.dispatch(request)` validates exact keys and types, while
`crowley.session.cli._socket_request` is the transport. The helper may use only
these fixed CLI/IPC operations:

- `native-construction-prepare`;
- `native-construction-control-preflight`;
- `native-construction-bootstrap`;
- `native-construction-recheck`;
- `native-construction-finalize-admit`;
- `native-construction-recovery-begin`, `-complete`, and `-cancel`.

Generation and reservation identifiers are closed, bounded values. The helper must
only echo the daemon-derived `expectedConstructorBoot` value, exactly
`native-construction:<B0>`; it must never substitute the ordinary `B0`, decode a
boot, or invent one. The closure amendment supersedes the older token-bearing
recovery command: the exact chat command is `/crowley agent recover`, with no token
argument; the addon owns the private recovery nonce.

## Guard/API map

The reviewed focus and identity boundary maps to
`X11Backend.resolve_identity(require_foreground=True, deadline_monotonic=...)`,
`X11Backend._focus(identity, generation=...)`, `X11Backend.pointer_position(...)`,
and the returned `WindowIdentity` fingerprint, PID/process start, XID/child XID,
geometry, foreground XID, and `target_event_xids`. Every input edge needs a fresh
identity/focus/phase/lease/generation recheck; stale identity, foreground drift,
window ancestry/geometry drift, pointer target drift, or expired evidence refuses
before input.

The reviewed chat/OCR pattern consists of a fresh captured image, the fixed chat
EditBox readback, and exact normalized OCR of the submitted command.
`DesktopDriver.prepare_command(...)` is a baseline contract/reference only: its
allowlist excludes the Agent commands, and a deferred load has no Agent chatEdit
frame. The future helper must therefore use its independent fresh-image/OCR path,
with a daemon recheck immediately before each command; it must not call
`prepare_command`, widen that allowlist, or require Agent pixels while Agent is
absent. The helper has no arbitrary command, text, coordinate, template, or generic
automation API. Construct/Restore templates remain exactly two closed roles in a
private manifest, with fresh positive and negative matches and no
ambiguous/overlapping/stale match accepted.

Pinned input is obtained only through `PinnedInputTool.load()` (or its explicit test
root), with its `proc_path` and sealed image descriptor. A release capability is
created by `PinnedInputTool.duplicate_release_spec()` and verified by
`NativeReleaseSpec.verify_image()` (sealed memfd, descriptor identity, digest, and
version). No PATH fallback or alternate executable is permitted.

Guardian ownership uses the existing methods `begin_calibration_operation`,
`issue_calibration_ticket`, `calibration_ticket_current`,
`calibration_dispatch_admission`, `publish_calibration_holds`,
`admission_gate_ready`, `cancel_calibration_operation`, `revoke`, and `close`.
The independent entry point is `_watchdog_entry(..., release_spec=..., ack_fd=...)`.
Its acknowledged `T` state carries only tracked process groups, keys, and buttons;
owner EOF/death and handled signals enter the same cleanup. With a
`NativeReleaseSpec`, release emits only the exact owned `keyup`/`mouseup` items
through the sealed image. `keyup --all`, unrelated mouse-up, a second emitter, and
clearing ownership before physical release are forbidden.

## Helper-specific fixture and review obligations

Offline tests must exercise all three closed modes (`control-preflight`,
`measure-deferred`, `recover`), the complete predecessor/handshake table, daemon
boot echo, fixed chat commands, fresh positive/negative template checks, and every
pre-input revocation boundary: phase, generation, identity, focus, lease, profile,
reservation/ticket, and each unchanged deadline. They must use production IPC
parsing and the actual Guardian/PinnedInputTool composition, while replacing only
local clocks, captures, OCR, and pinned fixture artifacts.

Failure fixtures must cover terminal native error followed by generation-bound pause,
reservation expiry/cancel/handoff, helper SIGTERM/SIGHUP/SIGINT, owner death/SIGKILL,
watchdog ACK loss, button held during helper death, stale recovery boot, malformed or
ambiguous templates, chat readback mismatch, capture/receipt write failure, and
second-actor overlap. Assertions retain the first causal error and prove exact
release, process reaping, ticket revocation, private 0600/0700 receipt cleanup, and
no public credential/config/environment leakage. No fixture may qualify a native
measurement or imply that a retry path is safe.

The addon/native live gates remain future work: installed source hashes, measured
panel/template pixels, real ReloadUI/handler order, a fresh ordinary boot, and a
separate native generation. This preparation note makes no live or Rust claim.
