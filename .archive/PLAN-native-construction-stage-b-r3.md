# Plan: native construction isolation, Stage B R3

Status: proposed rescope for independent review. This plan does not release
implementation or live input. It replaces the invalid pre-file-execution
SavedVariables premise in R1/R2; those plans remain frozen evidence.

## Objective and invariant

Defer the normal Agent surface across one `/reload`, take the existing whole-process
memory baseline while it is absent, construct it once after a guarded operator click,
and run the unchanged native measurement window. The result remains conservative
whole-process growth: any remaining world loading is counted. This does not claim a
pure Agent allocation, terrain isolation, a higher 128 MiB limit, a longer freshness
window, or native qualification.

Ordinary addon behavior remains externally the same after `ADDON_LOADED`. The timing
of normal Agent construction deliberately moves from file execution into Agent's own
`ADDON_LOADED` handler so the handler can use loaded SavedVariables.

## Correct lifecycle foundation

Local primary evidence is decisive:

- Core initializes `CrowleyDB` in its first matching `ADDON_LOADED` handler
  (`addon/Crowley/Core.lua:110-116`).
- The harness executes every addon file before firing `ADDON_LOADED`
  (`tests/wow_harness.py:760,810-815`), and existing tests can inject the SavedVariables
  table after file loading and before that event.
- Therefore no file-execution path may read the marker or choose ordinary/deferred
  construction.

Before `ADDON_LOADED`, Core exposes only an in-memory `unknown` decision. Scanner is
blocked in that state, and every timer, event, manual start, resume, queued start, and
rearm entry point rechecks the decision before scanning or scheduling. It does not
publish a new protocol phase: public status stays within `ready|scheduled`, while the
bounded schedule trace may record `native_construction_unknown`.

Core's first matching `ADDON_LOADED` handler initializes/defaults `CrowleyDB`, strictly
validates the marker, and publishes one immutable boot decision plus a separate
in-memory lifecycle state. Agent's separately
registered matching handler runs afterward and is the only handler that selects the
boot token and constructs or withholds the surface. Registration order is pinned in
the harness. Agent fails closed without constructing if the decision is still
`unknown`; qualification must catch any real-client ordering difference.

The boot decision never changes within that load. The lifecycle may advance only
through `deferred -> constructing -> constructed -> finalized` or to restore-only.
Scanner gates on both: it remains blocked until an ordinary decision or `finalized`
lifecycle, so clearing the marker cannot accidentally leave it blocked or release it
early.

All Agent methods that can otherwise create or mutate the surface (`safePublish`,
`Publish`, `Hold`, `Measure`, and `Resume`) return a typed `agent_unconstructed`
failure without changing the marker, counters, boot, scan state, or UI when no surface
exists. Construction occurs only in the ordinary `ADDON_LOADED` branch or the guarded
Construct callback.

## Persistent marker and boot rules

The only new SavedVariables member is `CrowleyDB.nativeConstruction` with exactly:

```text
{ schema = 1, state = <enum>, token = <bounded opaque boot>, attempts = 0|1 }
```

Allowed forms are:

- `armed`, `deferred`: `attempts=0`;
- `constructing`, `constructed`, `failed`: `attempts=1`;
- `restore_pending`: `attempts=0`, with `token="recovery:"` plus exactly 24 lowercase
  hex characters supplied by the daemon recovery ticket.

An active attempt token uses the existing boot grammar and is at most 64 UTF-8 bytes,
so `native-construction:<token>` remains within the existing 96-byte boot limit.

Unknown keys, wrong types, missing keys, invalid tokens, or invalid state/attempt pairs
are malformed. They never admit construction. Core maps them to restore-only behavior
without partially repairing the original table.

`/crowley agent defer` is accepted only from an ordinary constructed boot, with no
scan queued/running, no native or logout scheduling fence, and no prior marker. It
atomically writes `armed/attempts=0` using the current fresh decoded boot as `token`,
arms only the native-construction schedule fence, and creates the controls immediately
in the still-ordinary load. On the following `ADDON_LOADED`, Core canonicalizes exact
`armed` to `deferred`; Agent chooses
`native-construction:<token>` but does not construct the surface.

That prefixed boot remains unchanged through Construct, Hold, Measure, Resume, and
Finalize. Finalize does not synthesize a boot transition. It publishes a newer
`normal/0` frame with the same prefixed boot, clears the marker and only the native
fence, and leaves Restore visible until the next ordinary reload. The next ordinary
reload generates the normal opaque boot by the existing rule.

The new marker is persistent by design, but it is not part of the scan wire. Strict
decoder/companion fixtures must prove byte-for-byte legacy scan serialization and
that an unrelated SavedVariables key cannot appear in public frames.

## Separate scheduling fences

Scanner tracks native-construction and logout/reload causes separately. The effective
legacy `scheduleFence` projection is armed if either cause is armed. Clearing the
native cause recomputes the projection and never clears or rewrites the logout cause.
Native release rearms the existing schedule only when the effective fence becomes
unarmed and the auction house remained open; it preserves the 900-second cadence,
queue/token rules, and no-overlap behavior.

The workflow requires the logout/reload cause to be unarmed before defer and through
Finalize. This makes a fresh prefixed `normal/0` frame whose projected schedule fence
changed from armed to unarmed a truthful Finalize proof, without adding a wire field.

## Controls and recovery semantics

Commands/Agent create a small transient Construct/Restore panel outside the Agent crop
whenever defer succeeds in the current ordinary load and on every deferred,
constructing, failed, restore-only, or recovery load. Creating the panel does not
construct Agent.

- Construct is clickable in pre-reload `armed` state solely to exercise its actual
  callback. The handler visibly reports `not released` and makes no persistent or
  Agent mutation. It becomes effective only for exact `deferred/attempts=0` after the
  helper OCR-verifies `/crowley agent release`. Commands stores that admission only in
  memory and opens a ten-second `GetTime()` window. The reviewed helper cannot dispatch
  release until the daemon exposes `construction_released`; out-of-band commands remain
  outside the accepted sole-operator assumption. The helper also enforces the earlier
  external click deadline. The addon window is a local UI refusal only; it is never
  compared with or substituted for the daemon's native-clock evidence.
- The first effective Construct transition atomically writes
  `constructing/attempts=1`, disables itself, invokes the constructor once, then writes
  `constructed` or `failed`. Construction uses local references until complete; an
  error unregisters timers/scripts, hides every owned partial frame/texture, publishes
  no Agent frame, and preserves Restore. Duplicate, early, late, stale-boot, and
  post-error clicks never invoke the constructor.
- Restore is available in every nonordinary and malformed state, including the
  pre-reload `armed` state and after successful Finalize until an ordinary reload.
  It never admits construction. After a daemon recovery ticket, the helper types
  `/crowley agent recover <recovery-token>`; Commands switches to restore-only UI,
  hides Construct, and binds Restore to that token. This command is valid even when
  the Agent surface is absent because Commands remains loaded.

Restore first replaces the marker with exact `restore_pending/attempts=0` and a fresh
recovery token, keeps the native fence armed, disables both controls, and calls
`ReloadUI`. It never interprets a normal return as failure. A two-second token-bound
timer re-enables Restore only if the same `restore_pending` marker and same load still
exist. On the next matching `ADDON_LOADED`, Agent constructs an ordinary boot. Only a
successful fresh `normal/0` publication clears `restore_pending` and the native fence;
constructor failure preserves the fence and Restore path. In the post-Finalize
in-memory state, Restore may recreate this exact marker from its admitted recovery
token even though Finalize already cleared the old attempt marker.

Hold, Measure, and Resume preserve their current phase/ordinal rules. A private
`measurementCompleted` bit is set only by successful Resume from `held/100`.
Finalize requires exact `constructed/attempts=1`, that bit, the unchanged prefixed
boot, `normal/0`, and an idle scanner; otherwise it is inert and leaves recovery
intact.

Direct UI input is not an automatic service action. Live Construct and Restore clicks
are made only by the reviewed versioned operator tool after the daemon admissions
below. An inactive preflight may exercise the real pre-reload Construct callback and
Restore callback before any Agentless measurement attempt.

## Native admission and sealed absence evidence

The existing `native-bootstrap` request and response remain byte-compatible and keep
their ordinary behavior. `native-construction-prepare --generation` binds the exact
expected prefixed boot and a bounded input reservation to a new native generation.
The PAUSED control-only rehearsal uses the separate
`native-construction-control-preflight --generation`; it issues only a bounded input
reservation and can never expose release or admit construction.
Deferred mode is explicit through a new bootstrap request/method that requires
`expected_constructor_boot`; old clients are never required to send it.

The deferred native handshake has this exact order:

```text
running
construction_reset_archived
baseline_bound        (nativeBootstrapReady=false)
construction_released (release flag and nativeBootstrapReady become true together)
hold_required
resume_ready
finalize_required
finalized
```

It never emits the legacy `bootstrap_ready` label for the deferred branch. Repeated,
skipped, or regressed states fail closed.

The first provider capture is only entry evidence and remains subject to the existing
10-second provider-entry limit. After the one unchanged reset and baseline binding, a
second capture is the actual absence evidence. The daemon retains its exact private
path, SHA-256, capture identity, and completed monotonic timestamp before setting
`construction_released`. Capture completion, release, freshness comparisons, click
deadlines, and receipt times all use `self._native_clock`.

The existing five-second release/freshness checks remain unchanged. Tests cover just
under and just over five seconds. The absence classifier, identity, epoch, digest,
profile, and crop checks remain strict. Archive or capture write failure preserves the
original phase/error and prevents release.

On entry to the existing 30-second construction measurement provider, the daemon
publishes `constructorClickDeadline = provider_deadline - 2.0` in the private
handshake. It must be finite, later than release, and bound to the active generation,
expected boot, capture identity, and attempt. The helper then OCR-verifies the exact
release command, confirms the positive ready control, repeats admission immediately
before clicking, and refuses at or after either the daemon deadline or the addon's
ten-second window. No timeout is extended.

After Resume produces the existing fresh `normal/0` observation, the daemon sets
`resume_ready` and enters a 30-second deferred-finalize hook before calling
`controller.native_calibrated`. The helper observes that exact state and calls
`native-construction-finalize-admit --generation`; the daemon atomically advances to
`finalize_required` and publishes `min(hook_deadline, now + 10s)` as its native-clock
deadline. The helper then
OCR-verifies Finalize while the same native operation/generation remains active. The
hook accepts only a newer strict frame with the exact prefixed boot, `normal/0`, and
projected schedule fence unarmed, then publishes `finalized`. Timeout, interruption,
drift, or a remaining fence fails the native operation and never advances to input
calibration. This removes the current `resume_ready` transition race.

## Recovery admission and crash matrix

Recovery does not depend on the canceled native generation. The bounded private IPCs
are `native-construction-recovery-begin`, `-complete`, and `-cancel`. Begin is available
only while the current controller is `PAUSED`, its service unit is unarmed, it is idle,
and it has no active native/input operation. The addon's native schedule fence may
remain armed. Begin verifies the canonical desktop lease,
Guardian/human-proof state, exact current PID/start/profile identity, and a fresh
capture that shows either no Agent surface or the exact
`native-construction:` boot.

Admission issues one process-local, single-use recovery ticket bound to the current
paused generation, lease generation, identity, capture epoch, fresh recovery token,
and existing bounded reload deadline. It blocks competing daemon input admission until
complete/cancel, but does not transfer or duplicate the desktop lease. The helper
OCR-verifies the exact recover command, then requires a positive Restore template and
negative Construct template. It rechecks the ticket immediately before its single
Restore click. A daemon completion call independently
captures and decodes the resulting ordinary boot; only then does the helper invoke the
existing explicit owner resume for that still-current paused generation.

This same path covers:

- `armed` before the first reload;
- deferred, constructing, constructor-error, and malformed marker loads;
- pause or generation change during the attempt;
- service/helper restart with no active operation;
- crash after construction, Resume, or Finalize but before durable daemon completion;
- a completed native operation whose prefixed load still exposes Restore, after the
  owner deliberately returns the controller to PAUSED.

The recovery path cannot construct Agent from deferred state. Ticket expiry, identity
change, absent/ambiguous templates, active work, or failed ordinary-boot proof leaves
the controller paused and the native fence intact. It never types a blind command.

## Versioned input actor

The only new input actor is the versioned repository tool
`tools/native_calibration_operator.py`, with focused tests in
`tests/test_native_calibration_operator.py`. It has exactly three closed modes:
`control-preflight`, `measure-deferred`, and `recover`. It exposes no arbitrary command,
key, text, coordinate, template, or generic game-automation interface.

Its only runtime selectors are the closed mode, expected generation, existing Crowley
config path, and a private template manifest. The manifest schema has exactly the
`construct` and `restore` roles with reviewed SHA-256 values and fixed thresholds; the
tool derives coordinates only from a fresh accepted match and rejects extra roles or
fields.

The implementation must first preserve and reconcile two read-only provenance inputs:

- current private `native-handshake-once.py`, SHA-256
  `d5530fbd7085478c481e6004608f7d3068e48b5da0c67f05cec9db9376a13466`;
- the distinct last-reviewed `bf79d703...` variant.

Their exact delta and the subset carried into the repo tool are recorded in the helper
review. Neither frozen private script is edited or invoked as the new implementation.
The repo tool itself receives Sol and actual Opus source review and is pinned by full
SHA-256 before use.

The tool may depend only on the existing Crowley config loader, `X11Backend`, pinned
input-tool verification, Pillow, the production session CLI, and the already reviewed
OCR/template process pattern. It preserves fresh input-image, PID/start/window/profile,
focus, canonical lease, generation/phase, pointer-target, press ownership, and
unconditional release guards. Runtime templates, screenshots, receipts, and selected
environment evidence remain in a new private 0700 attempt directory under
`~/.local/state/crowley`; files are 0600. It never copies credentials, Xauthority
contents, raw process environments, or config contents into the repo or receipt.

The tool gets the boot from a fresh strict ordinary frame, then uses its OCR-confirmed
chat path with a fixed `measure-deferred` sequence: defer, `/reload`, release, Hold,
Measure, Resume, the private finalize-admit IPC, then Finalize. Defer and `/reload`
happen after the daemon creates the new native generation but before deferred
bootstrap. `control-preflight` is limited to
defer, the inert Construct click, admitted recover, and one Restore click while PAUSED.
`recover` is limited to admitted recover and one Restore click. Construct and Restore
always use reviewed fresh positive and negative templates. The ordinary scan-reload
path and the production driver's command allowlist are unchanged and are not used for
the Agentless reload.

Every attempt receipt records the exact repo-tool SHA-256, addon/native source map,
producer manifest and binary hashes, private template hashes, expected/current boot,
generation, PID/start/profile identity, every admission result, handshake states and
clocks, click deadline, input count, terminal controller state, and cleanup result.
The tool records every command and click in an exact input ledger, sends each action at
most once, refuses unknown states/commands, and has no automatic retry.

## Three offline implementation slices

### 1. Addon slice

Owned files:

- `addon/Crowley/Core.lua`
- `addon/Crowley/Scanner.lua`
- `addon/Crowley/Agent.lua`
- `addon/Crowley/Commands.lua`
- `tests/wow_harness.py`
- `tests/test_addon.py`
- `docs/HANDOFF.md` only to record the verified load/event order

Acceptance tests pin file-execution then `ADDON_LOADED` ordering, cover SavedVariables
injection both before and after file execution but before the event, preserve ordinary
initial publication, and prove unknown-state scan blocking at every entry. They cover
the full marker matrix; no implicit construction by publish/lifecycle methods; exact
once-only construction; early/late/duplicate refusal; the real pre-reload Construct
callback; Restore timer/reload behavior; constructor errors; native/logout fence
independence; AH-open schedule rearm; and unchanged strict wire bytes.

### 2. Native slice

Owned files:

- `src/crowley/session/daemon.py`
- `src/crowley/session/cli.py`
- `tests/test_session_native.py`
- `tests/test_session_native_regressions.py`

This slice adds only the explicit deferred bootstrap/admissions, private handshake,
sealed post-reset evidence, finalize hook, and recovery ticket. Tests use real public
CLI parsing and the production callback path. They cover legacy bootstrap unchanged;
the exact state machine; reset/archive/capture failures; the five-second boundary;
single native clock; 30-second provider and click-deadline boundaries; interruption;
generation/identity/epoch drift; Finalize-before-transition; restart/pause recovery;
ticket expiry; original-error preservation; and cleanup of tickets, callbacks,
processes, and private artifacts.

### 3. Helper slice

Owned files:

- `tools/native_calibration_operator.py`
- `tests/test_native_calibration_operator.py`

The d553/bf79 provenance delta is reviewed first. Pure offline fixtures then cover all
three modes, every allowed handshake transition and fixed chat command, positive and
negative template checks, phase/focus/lease/identity revocation at every pre-input
boundary, owned button release after injected failure, deadlines, tickets, receipt
privacy and atomic publication, and cleanup. No test invokes the real desktop or game.
The exact source hash is pinned in the native qualification handoff and every receipt.

The slices are implemented and reviewed in that order. Addon/native/helper source and
tests may be completed offline before future live templates or callbacks exist. No
slice authorizes game input, daemon restart, deployment, or a measurement retry.

## Live qualification gates after accepted code

1. Sole-operator release verifies installed addon/native/helper hashes, the real
   SavedVariables-at-`ADDON_LOADED` behavior, and current lease/Guardian/identity.
2. A disposable inactive preflight runs while the controller is PAUSED, unarmed, and
   idle. It runs defer in the ordinary load, captures positive controls and negative
   outside-Agent-crop templates, clicks Construct to prove the real inert callback,
   then obtains a recovery ticket, enters restore-only mode, clicks Restore, and proves
   a fresh ordinary boot. The attempt ends; its templates and complete receipt receive
   review.
3. Only a later fresh native generation may perform the Agentless reload and
   measurement.
   Qualification requires the complete strict handshake, retained pre/post-reset
   evidence, one Construct input, unchanged memory limits, Finalize proof before the
   controller transition, and clean terminal state.
4. Any failure uses the admitted Restore path and stays paused until ordinary-boot
   proof. No limit increase, manual marker edit, blind typing, synthetic input
   qualification, or automatic retry is allowed.

## Review checkpoint

This R3 plan needs independent root review and actual Opus closure before any slice is
released. The main unresolved dependency is source-reviewing and pinning the private
helper delta; live control templates and callbacks are qualification evidence that can
exist only after accepted implementation. Stage A diagnostics remain independently
usable, and Stage B remains unreleased.
