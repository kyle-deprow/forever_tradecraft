# Stage B closure amendment

Status: releases three sequential **offline-only** implementation slices after
review of this amendment. It authorizes no game input, capture, daemon restart,
deployment, service change, or native retry.

This amends the frozen Stage B R3 plan, SHA-256
`cc3892cff429d49ab48398926cf2351cecb20a9460fd5bbcfc23d222fed45784`.
R3 remains immutable. Every R3 rule not changed below still applies; this file
does not restate its architecture.

## Closed decisions

### Durable preparation and one reservation vocabulary

`native-construction-prepare` captures and decodes a fresh strict ordinary
`normal/0` frame in the daemon. Its boot is `B0`; the daemon alone derives
`native-construction:<B0>`. The helper receives that value and may only echo it
back with the reservation. It never decodes or invents a boot.

The controller journal gains one bounded internal `nativeConstruction` record:

```text
{ schema: 1, B0, expectedConstructorBoot, ownerGeneration,
  kind: "measure"|"preflight", phase: "prepared"|"recovery_required" }
```

It is not addon SavedVariables, a public frame field, or calibration evidence.
The controller owns it so ordinary `_save` calls cannot erase it. Once a
reservation is returned to the helper, `B0` remains durable through expiry,
helper/daemon death, terminal error, Finalize, and restart. It is cleared only
after recovery completion proves a genuinely new ordinary unarmed boot. A
failure before the first input therefore takes the same recovery path rather
than guessing whether a command reached the client.

Every private prepare, reservation, ticket, and recheck response uses these
canonical fields and no aliases:

```text
reservationId, reservationKind, reservationState, controllerGeneration,
desktopLeaseHeld, guardianGeneration, guardianArmed,
ownerPid, ownerProcessStart, profileFingerprint, identityFingerprint,
B0, expectedConstructorBoot, expiresMonotonic
```

`desktopLeaseHeld` is the daemon's process-lifetime `InputLease`; the two
Guardian fields describe its current input generation. The helper requires the
exact returned values at every pre-input boundary. The service remains unarmed
for construction control, so `guardianArmed` must be false.

Measure prepare admits only exact `NATIVE_CALIBRATION`, non-interaction mode,
an idle/unarmed owner, a fresh ordinary frame with an unarmed projected schedule
fence, no calibration operation ever started for that controller generation,
no pending legacy bootstrap, reservation, recovery ticket, Guardian calibration
ticket, or other input operation, and no earlier durable construction checkpoint.
Control preflight has the same exclusions but requires exact `PAUSED` and can
never expose `construction_released`.

There is one process-local reservation at a time:

- measure prepare is consumed atomically by the deferred bootstrap;
- control preflight is converted atomically, under the same daemon lock, into
  its recovery ticket; there is no release/reacquire gap;
- expiry, helper cancel, generation/identity/profile/lease drift, operation
  failure, or daemon shutdown revokes the reservation and any Guardian
  calibration ticket before clearing process-local admission;
- a daemon restart has no live reservation, but retains the journaled `B0` and
  permits a new recovery ticket after all recovery admission checks;
- a second actor is refused while any reservation, ticket, bootstrap, native
  operation, or helper-owned input is live.

### Complete handshake and deferred-load proof

The private deferred handshake has one expected-previous-state table shared by
daemon tests and the helper:

| State | Exact predecessor / event |
|---|---|
| `construction_prepared` | prepare created the durable checkpoint and reservation |
| `running` | deferred bootstrap consumed that reservation |
| `construction_reset_archived` | construction reset archive committed |
| `baseline_bound` | reset baseline and sealed absence metadata bound |
| `construction_released` | release flag and native bootstrap readiness published together |
| `hold_required` | Construct produced the strict `normal/0` prefixed frame |
| `updates_reset_archived` | update reset archive committed |
| `measure_ready` | update window bound at `updates/0` |
| `resume_required` | sealed `held/100` boundary accepted |
| `resume_ready` | fresh resumed `normal/0` observation accepted |
| `finalize_required` | finalize admission consumed the resume hook |
| `finalized` | newer prefixed `normal/0`, native fence unarmed, accepted |

Repeated, skipped, regressed, wrong-generation, or wrong-reservation states
revoke the operation. The legacy branch and `bootstrap_ready` remain unchanged.

After typing `/reload`, and before deferred bootstrap or the memory baseline,
the helper requires one fresh image with separate positive Construct and Restore
template matches. Missing, ambiguous, overlapping, or stale matches fail and
leave the durable checkpoint recoverable. The daemon's following entry capture
still supplies the strict Agent-absence proof.

### Recovery, pause, and boot rebind

Recovery is allowed only from a verified `PAUSED`, unarmed, idle owner. When a
native run ends with `calibrationOperation.state == "error"` while the controller
is still `NATIVE_CALIBRATION`, the helper first sends the existing
generation-bound `pause` request with the fixed reason
`native construction recovery`. It requires the returned newer generation,
`PAUSED`, revoked/unarmed Guardian, terminal operation, and no active worker
before recovery-begin. A failed pause or failed proof permits no chat command or
click. Already-PAUSED recovery skips this transition; other states are refused.

Recovery-begin accepts exactly one fresh capture case:

1. no Agent surface;
2. strict boot `native-construction:<B0>`; or
3. the pre-reload armed case: strict ordinary `normal/0`, boot exactly `B0`,
   and projected schedule fence armed.

It also requires non-interaction mode, the durable checkpoint, current canonical
lease/identity fields, no active operation/ticket, and the atomic preflight
handoff when applicable. The ticket records the begin boot, sequence, capture
identity/time, current generation, lease fields, and `B0`.

The typed command is fixed: `/crowley agent recover`. It has no token argument.
Commands generates the existing 24-lowercase-hex `recovery:` nonce locally and
keeps it out of public frames. Before that command, every Restore click prints
`recovery not admitted` and changes no marker, nonce, control state, fence, or
reload state. After admission, the first Restore click writes exact
`restore_pending` with the addon-owned nonce and follows R3's ReloadUI path.

Recovery-complete independently captures and decodes a frame newer than the
begin observation. It requires ordinary `normal/0`, a boot different from both
the begin boot and `B0`, and an unarmed projected schedule fence. Merely seeing
an ordinary frame cannot complete recovery. Failure/expiry leaves the controller
paused and `B0` durable.

`src/crowley/session/controller.py` gains one non-IPC method that durably rebinds
`frameBoot`, sequence, and CRC without changing generation or controller state.
It accepts only the closed reasons `native_construction_finalize` in exact
`NATIVE_CALIBRATION` and `native_construction_recovery` in exact `PAUSED`, with
the expected current generation/state. The daemon validates the ticket/frame
contract before calling it. Finalize rebinds to the accepted prefixed frame
immediately before `native_calibrated`; recovery-complete rebinds to the new
ordinary frame immediately before explicit owner resume. No generic/public boot
rewrite is added. Tests pass both paths through `observe_frame`; unrelated boot
changes must still block.

### Panel, click ownership, and evidence wording

`Commands.lua` solely owns `CrowleyNativeConstructionPanel`. It is 220 by 84 UI
units, anchored `TOPRIGHT` on `UIParent` at `(-24,-24)`. Agent never creates or
owns it. The harness pins that owner, size, anchor, visibility, and callback
lifecycle. Live qualification must additionally prove its measured native box
does not intersect the Agent crop `[80,48,256,256]` or the reviewed chat OCR box
`[30,938,460,37]` before templates are accepted.

The constructor click deadline is
`providerDeadline - (5.0 second construction reserve + 2.0 second capture margin)`.
It is also bounded by the unchanged addon ten-second release window. Admission
at or after either deadline is refused; neither deadline is extended.

The helper reuses the existing independent watchdog entrypoint in
`guardian.py` with a sealed `NativeReleaseSpec` from `input_tool.py`. It publishes
only owned button 1 through the acknowledged watchdog pipe before opening the
gated press, and clears it only after the matching release. Normal `finally`
release remains. `SIGTERM`, `SIGHUP`, and `SIGINT` handlers enter the same cancel
and release path; SIGKILL/owner loss is handled by the independent watchdog.
No `keyup --all`, unrelated mouseup, second emitter, or alternate input image is
allowed. Offline subprocess tests kill the helper during the admitted hold and
prove exactly `mouseup 1`, ownership-record cleanup, child reaping, and ticket
revocation.

The absence capture file is deleted after its seal is checked. Durable/private
records retain only its path string, SHA-256, capture identity, and completed
monotonic time, plus a successful deletion/clear result. Receipts must not claim
that the PNG itself was retained. Tests prove the metadata survives while the
path no longer exists.

## Sequential offline slices

Slices may not overlap and are implemented/reviewed in this order.

### 1. Addon slice — released first

Source fence:

- `addon/Crowley/Core.lua`
- `addon/Crowley/Scanner.lua`
- `addon/Crowley/Agent.lua`
- `addon/Crowley/Commands.lua`

Test/fixture fence:

- `tests/wow_harness.py`
- `tests/test_addon.py`
- `tests/test_companion.py`
- `tests/fixtures/native-construction-unknown-savedvars.lua` (new, owned here)

Focused acceptance covers file execution versus `ADDON_LOADED`; the full strict
marker matrix; ordinary construction/publication; every scan entry while the
decision is unknown; once-only Construct; fixed recover grammar and addon-owned
nonce; visible inert Construct/Restore refusals; constructor cleanup; independent
native/logout fences; panel ownership/anchor; and Finalize/Restore lifecycle.
The static fixture contains an unknown/malformed construction SavedVariables
record plus a known legacy format-2 scan. Companion parsing must preserve the
scan envelope/payload bytes exactly and must not leak the unrelated key into a
decoded Agent frame or scan wire. No companion source is owned.

### 2. Native slice

Source fence:

- `src/crowley/session/controller.py`
- `src/crowley/session/daemon.py`
- `src/crowley/session/cli.py`

Test fence:

- `tests/test_session_native.py`
- `tests/test_session_native_regressions.py`
- `tests/test_session_transitions.py`

Focused acceptance covers public CLI field strictness; daemon-derived `B0`;
prepare/preflight exclusions; every handshake edge; the
`updates_reset_archived` ordering race; reservation consume/handoff/expiry and
all revocations; daemon restart with durable `B0`; terminal-error pause; all
three recovery-begin capture cases; refusal while a reservation/ticket is live;
new ordinary boot and unarmed-fence completion; retained seal metadata with
deleted capture; seven-second constructor reserve; and reason/state/generation
guards on controller boot rebind. Both rebind paths are exercised through real
`observe_frame` and a fresh reconstructed controller.

### 3. Helper slice

Source/test fence:

- `tools/native_calibration_operator.py` (new)
- `tests/test_native_calibration_operator.py` (new)

`guardian.py`, `input_tool.py`, the config loader, `X11Backend`, protocol decoder,
and session CLI are read-only dependencies. The helper retains exactly the R3
three closed modes and fixed commands. Tests cover the full predecessor table,
daemon-supplied boot echo, dual positive post-reload controls before bootstrap,
canonical lease fields at every input edge, template ambiguity, all deadlines,
terminal-error pause, reservation-to-ticket handoff, fixed recover command,
atomic/private receipts, each handled signal, and independent owner-death release.
No test opens the real desktop or game.

Each slice receives Sol source review and actual Opus executor review before the
next slice starts. The helper's accepted source then receives a full SHA-256 pin
in the qualification handoff and every receipt.

## Finding closure

| Remaining finding | Closure |
|---|---|
| terminal native error cannot recover | generation-bound pause and PAUSED proof before recovery |
| armed ordinary load was unreachable | durable `B0` plus the exact ordinary/armed begin case |
| recovery could accept the old boot | newer ordinary boot, different from begin and `B0`, fence unarmed |
| reservation lifecycle/overlap undefined | one canonical record; atomic consume/handoff; explicit expiry/revocation |
| handshake omitted real states | complete 12-state predecessor table |
| prepare had no guarded state | `construction_prepared` with strict no-attempt/no-ticket/non-interaction admission |
| expected boot had two sources | daemon decodes `B0`; helper only echoes the derived value |
| reload completion was not proven | fresh positive Construct and Restore matches before bootstrap/baseline |
| controller rejects legitimate boot change | closed, durable finalize/recovery rebind method and transition tests |
| helper death can leave button held | existing sealed-image owner-death watchdog plus signal handling |
| recovery token was unreadable | fixed command; nonce is addon-owned and private |
| Restore before admission undefined | visible inert refusal with zero mutation |
| click left less than construction budget | fixed 5-second construction plus 2-second capture reserve |
| capture retention was overstated | retain hash/identity/time/path string; assert PNG deletion |
| interaction mode could race old calibration | prepare/bootstrap/recovery all refuse interaction mode |
| panel owner/location ambiguous | Commands-owned fixed top-right panel; native nonintersection live gate |
| unknown SavedVariables wire proof unowned | addon-owned static fixture and companion byte-identity test |

## Fixed invariants and later qualification

Offline implementation keeps the 128 MiB construction limit, 100-update
measurement, existing five-second freshness checks, 30-second provider windows,
public evidence schema, sole-operator rule, and strict no-fallback behavior.
It adds no Rust, automatic retry, deadline extension, limit increase, manual
SavedVariables edit, or new live claim.

All implementation decisions needed by the addon slice are settled above.
Later live qualification still supplies only environment evidence: real
SavedVariables availability/handler order, measured panel pixels and reviewed
templates, pinned XTEST callback delivery, ReloadUI behavior, installed hashes,
the genuinely new ordinary boot observation, and the separate fresh native
generation. Those facts do not block the three offline slices.

| Boundary | Required decision or evidence |
|---|---|
| before addon implementation | none open: marker grammar, fixed recover command, nonce owner, refusals, panel owner/location, fences, and fixture path are fixed here |
| before native implementation | accepted addon slice; reservation/checkpoint, pause, handshake, recovery, and boot-rebind contracts are fixed here |
| before helper implementation | accepted native slice; helper modes, commands, lease fields, watchdog, signals, templates, and deadlines are fixed here |
| later live qualification | measured handler order, panel/template pixels, real callbacks/ReloadUI, installed hashes, new ordinary boot, and a separate fresh generation |

There is no unresolved design question in this amendment. Helper source
provenance review and live templates remain review/qualification work, not design
choices.
