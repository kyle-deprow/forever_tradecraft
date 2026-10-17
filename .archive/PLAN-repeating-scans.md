# Repeating Crowley scan system

## Status and bounded objective

**IMPLEMENTATION RELEASED — parent incorporated Sol's final contract findings.**
This revision is the pinned implementation contract. Luna owns implementation within the
exact fence below; deployment and live operation follow implementation review.

The objective is a deterministic local session that keeps the existing native format-2
scanner running at its existing cadence, saves and uploads each completed sweep promptly,
loads the exact acknowledgement, reopens the AH before the next due start, and closes out
with a persisted empty queue. It must sustain three consecutive full 428-ID sweeps as a
native acceptance test and remain capable of continuing without an LLM turn for every
poll, timer, scan, or acknowledgement wait.

The user's authority covers the one local Forever beta client, normal Arthur login or
reconnect, the established AH, `/reload`, safe logout, installation, and the scan/upload
workflow. It excludes credentials, trading, public chat, anti-AFK input, arbitrary travel,
unrelated services, production database tests, commits, and pushes. A user pause or human
takeover revokes all input immediately, including cleanup. A planned collection cutoff may
finish cleanup for already-existing work. The six-pending safeguard, 900-second start
cadence, 600-second sweep cap, 20 retained levels, exact variant identity, strict format 2,
and incomplete/unqueried evidence semantics remain unchanged.

## Pinned host, profile, and evidence

The measured profile is WoW Forever beta 1.60.1 build 70374/interface 16001, Classic Beta
PvE 2, character Arthur, house `beta-normal-alliance`, on this Linux host through Lutris,
Wine, GNOME/Xwayland. The active watchlist contains 428 IDs from the 544-entry catalog.
Accepted native evidence proves full sweeps of 428/428 in 480–488 seconds, with real
commodity, recipe, container, and equipment rows. The 2026-10-15 pilot proved two useful
sweeps and zero-pending closeout but missed the cadence: starts were 1,256 seconds apart;
finish-to-accepted-upload was about 312 and 217 seconds. The journal showed that
acknowledgement publication followed HTTP 200 immediately; waiting for the companion's
periodic refresh caused the avoidable delay. The implementation therefore observes exact
UIDs as soon as the stable SavedVariables/Data.lua handshake permits and budgets the
save/reload/reopen sequence against the next due time.

The independent `.archive/PLAN-desktop-agent-harness.md` remains background architecture
only. Its provider/navigation scope, alternate client assumptions, and proposed
`Crowley_AgentTelemetry` addon are not part of this implementation.

## Native telemetry contract

`addon/Crowley/Agent.lua` adds a read-only snapshot function and an always-visible,
non-interactive telemetry frame. The frame never writes files, calls the network, changes
scanner state, or reads mutable state through a command. `ns.Agent.Snapshot()` returns a
fresh deep copy of only scalar status and copied arrays; it has no side effects and tests
must prove that mutating the returned value cannot mutate the scanner or SavedVariables.

The snapshot JSON has exactly these top-level fields and meanings:

```text
schema: 1
boot: fresh addon-load identity; changes on every reload or new client process
sequence: strictly increasing within boot, beginning at 1
wallTime: time() seconds at publication
uptimeMs: floor(GetTime()*1000) modulo 2^32, for wrap-safe freshness across wall-clock changes
context: { addonVersion, interface, clientBuild, character, realm }
house: { key, source }
plan: { hash, count, cadenceSeconds: 900, sweepCapSeconds: 600, initialPriceLevels: 20 }
ahOpen: boolean
scanner: {
  phase: ready|scheduled|item|owned|blocked,
  activeSweepId: "" sentinel while no saved UID exists (native Lua nil is forbidden),
  startedAt: integer or 0,
  dueAt: integer or 0,
  ordinal: integer or 0,
  planned: integer,
  cursorItemID: integer or 0
}
lastSaved: {
  memoryUid: string or "", finishedAt: integer or 0,
  planned: integer, attempted: integer, failures: integer, rows: integer,
  persistence: "unknown"
}
pending: { ids: sorted exact UID strings, count: integer, cap: 6, blocked: boolean, reason: string or "" }
loaded: { ackedIds: sorted exact UID strings, generatedAt: integer or 0 }
chatEdit: { active: boolean, focused: boolean, text: bounded string }
```

`pending.ids` is the exact union of current format-2 SavedVariables scan IDs and the
existing v2 sweep queue, deduplicated and sorted; it is never inferred from counts.
`loaded.ackedIds` is the exact sorted `CROWLEY_DATA.ackedScans` array loaded by this addon
session. Acknowledged does not
mean pruned: the controller separately verifies the next reload's in-memory queue and the
following normal flush's on-disk queue. `activeSweepId` is always the representable empty
string until a future scanner state has an actual saved UID; no native `nil` is serialized.
`lastSaved.memoryUid` is the UID that the current Lua session has placed in
`CrowleyDB.scans`; `persistence` is always the literal `"unknown"` in the addon snapshot.
The addon never claims that its in-memory table has reached disk. Only the controller's
stable SavedVariables parse after a save/reload may record a separate
`stableSavedVarsUid`, and only the exact stable file can prove it. `phase=blocked`
means the addon itself has stopped starting work because the six-item queue is full or the
plan is invalid; controller pause/lease state lives in the session journal and is not
fabricated as addon state.

`chatEdit` is a read-only command-preparation readback. The addon obtains the active edit
box from the verified Forever `ChatFrameUtil.GetActiveWindow()` path and reports its
active/shown status, `HasFocus()`, and exact `GetText()` value; it does not read the
clipboard. The text is bounded, transient telemetry and is never written to SavedVariables,
the journal, or model prompts. A prepared command is admissible only when the active edit
box is focused and its exact text equals the one allowlisted command requested by the
controller. An intended clipboard string alone is not proof that the game buffer contains
the command.

The wire surface is a fixed 128x128 grid of 2x2 physical pixels, anchored inside the game
client at the pinned profile origin `(80,48)` relative to the 1920x1080 child area. This
256x256 interior crop is below the confirmed GNOME top panel and right of the left dock;
the exact profile crop is `(x=80,y=48,width=256,height=256)`. It is never placed at the
desktop/game origin `(0,0)`, and desktop or display settings are never changed. The
frame scale is 1, alpha 1, high frame strata, non-input, and has no animation, font, OCR,
or text. The addon calls the documented `SetIgnoreParentScale(true)` before layout, reads
the resulting effective scale, and derives `cellUi = 2 / effectiveScale`; it also derives
a deterministic fractional anchor offset so the frame's physical top-left is exactly the
profile origin. The executor's calibration must prove that this inverse-scale layout really
yields one stable 2x2 physical grid at that exact crop; a mismatch blocks the session and
does not relocate the frame automatically. `SetSnapToPixelGrid(true)` and
`SetTexelSnappingBias(0.5)` are pinned. Each cell is an opaque black or white texture set with
`SetColorTexture(0,0,0,1)` for bit 0 or `SetColorTexture(1,1,1,1)` for bit 1.

The 16,384 texture objects are created once at addon load/calibration and never created or
destroyed during an active query. Snapshot copies, native JSON, raw-deflate, and pixel
buffers necessarily allocate bounded transient memory at the one-Hz publication tick;
the implementation must cap those buffers, measure their native time/peak size, and report
the cost. It must not claim zero allocation. The calibration/performance gate is pinned to
an initial canvas construction of at most 5 seconds, a one-frame all-cell update p99 of at
most 250 ms over 100 updates, no more than 128 MiB process-RSS high-water growth for the
initial 16,384-texture construction, and no more than 16 MiB additional high-water growth
over those 100 updates. It records Lua transient memory separately from process RSS and
requires the one-Hz snapshot/encoding tick to stay within the 600-second sweep budget. A
telemetry-free baseline is accepted UID
`beta-normal-alliance-1792040351-Arthur-6643` (database sweep 6), with 428 queried
observations and a median `query.finishedAt-query.startedAt` of 1 second (range 0–2).
The telemetry-enabled 428-ID runs must show no more than 5% increase in that median.
The preserved native format-2 timestamps resolve integer seconds; report that practical
measurement limit rather than claiming millisecond precision. These are measured native gates, separate from unit-test timing. A
failed mapping or budget is an implementation blocker, not a request to change the user's
display/UI scale or a runtime fallback.

The exact frame bytes are little-endian and are packed row-major into the cell grid. Within
each byte, bit 0 is emitted first (least-significant-bit first); bit 0 is black and bit 1
is white. The
first 26 bytes are:

```text
offset  size  field
0       4     ASCII magic "CRS1"
4       1     protocol version 1
5       1     encoding 1 (native SerializeJSON bytes, raw Deflate)
6       1     canvas width 128
7       1     canvas height 128
8       2     compressed payload length, 1..2000
10      4     sequence, unsigned 32-bit
14      4     wallTime, unsigned 32-bit
18      4     uptimeMs modulo 2^32, unsigned 32-bit
22      4     CRC-32/IEEE of bytes 0..21 followed by payload bytes
26      N     compressed snapshot JSON, exactly payload length bytes
```

`uptimeMs` is `floor(GetTime()*1000) mod 2^32` in both the JSON and header. The decoder
compares it with unsigned modular subtraction within one boot, so a wrap after roughly
49.7 days is valid; it never compares the modulo value as an ordinary unbounded integer.
Sequence, boot identity, and the controller's monotonic capture clock remain the primary
freshness proof. A gap at or above the half-range (`2^31` ms), a stale controller deadline,
or a boot change makes the sample non-progress until a fresh boot reconciliation rather
than guessing across an ambiguous wrap.

The payload is the exact byte string returned by native
`C_EncodingUtil.SerializeJSON(snapshot)`, compressed with native
`C_EncodingUtil.CompressString(..., Enum.CompressionMethod.Deflate)`; it is raw Deflate,
not zlib or gzip. It is followed by zero padding to the 2,048-byte canvas capacity. The
Python decoder inflates with a raw-Deflate window (`wbits=-15`) and an absolute inflated
limit of 16,384 bytes before JSON parsing. It requires the magic, version, encoding,
dimensions, payload length in 1..2000, zero padding, header sequence/time agreement with
the JSON, and CRC before accepting any field. It samples the center of each calibrated
cell, accepts only black/white values with a strict luminance threshold, rejects partial
crops, and classifies an exact repeated `(boot, sequence, CRC)` sample as `NO_CHANGE`.
`NO_CHANGE` is never progress, but is admitted while waiting for the one expected fresh
boot after reload. A new sequence on the old boot is also not a fresh boot. The decoder
rejects a stale/foreign boot, boot churn, malformed or out-of-range JSON, and duplicate
progress after the wait deadline, and records monotonic capture time, screenshot
dimensions, crop, cell size, target window identity, and CRC. No hash or OCR is used as a
status transport.

The JSON validator is strict: required keys are exactly the documented keys, unknown keys
are rejected, all strings have bounded UTF-8 lengths and valid UTF-8, integers are integral
and within their declared unsigned ranges, booleans are not accepted as integers, phases
are the five enumerated values, `activeSweepId` and empty UID fields must be `""`, counts
equal their arrays' lengths, UID arrays are unique and byte-sorted, `pending.count <= 6`,
and the plan cadence/cap/levels are exactly 900/600/20. `schema`, sequence, wall time,
and uptime are unsigned 32-bit values; `boot`, context, house, and UIDs use the existing
format-2 bounded string rules; `chatEdit.text` is valid UTF-8 of at most 128 bytes; all
required nested objects, booleans, arrays, and array element types are checked explicitly.
Context, house, plan, scanner, lastSaved, pending, loaded, chatEdit, `boot`, sequence, wall
time, and uptime are all required and validated recursively before the snapshot reaches the
controller. The decoder requires payload bytes in the inclusive range 1..2000 and refuses
inflated JSON above 16,384 bytes before parsing.

Cross-field validation is also strict. `ready` has no active UID or start time;
`scheduled` has no active UID or start time and has a nonzero due time;
`item`/`owned` retain `activeSweepId=""` because the existing scanner creates its UID only
at finish; they have `startedAt > 0`, `dueAt = startedAt + 900`,
and an ordinal in `1..planned`; `blocked` has no active run and a nonempty enumerated
reason. Active cursor IDs are either zero or members of the exact plan, `planned` equals
the configured 428 count, and `startedAt <= wallTime <= dueAt` is required while an
active run is within its cadence interval. `lastSaved.memoryUid` is empty exactly when
`finishedAt=0` and all its counters are zero; otherwise `finishedAt>0`,
`planned=428`, `0 <= attempted <= planned`, `planned-attempted <= failures <= planned`, and
`rows >= 0` hold.
`pending.count` equals the sorted unique UID array length and is at most six;
`pending.blocked` requires a reason from `queue_full|plan_invalid` and a full queue or
invalid plan, while an unblocked queue has an empty reason. `phase=blocked` requires
`pending.blocked=true`, and `pending.blocked=true` requires `phase=blocked`. The house key,
plan hash,
client build, interface, cadence, cap, and watchlist count must match the journal before
any input. An empty character/realm is admissible only in `LOGIN_REQUIRED` or a verified
character-select precondition; before `enter_world`, `/reload`, AH, or scan input the
context must be exactly Arthur, Classic Beta PvE 2, and the configured realm. A
contradiction blocks before an action is considered; it is never repaired from a
screenshot or a model decision.

The Forever primary sources support this design: the beta branch's generated
[`SimpleFrameAPI`](https://raw.githubusercontent.com/Gethe/wow-ui-source/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/SimpleFrameAPIDocumentation.lua)
documents `CreateTexture`, `GetScale`, `GetEffectiveScale`, `SetScale`,
`SetIgnoreParentScale`, `SetAlpha`, `Show`, and frame/window access;
[`SimpleTextureBaseAPI`](https://raw.githubusercontent.com/Gethe/wow-ui-source/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/SimpleTextureBaseAPIDocumentation.lua)
documents `SetColorTexture`, `SetSnapToPixelGrid`, `SetTexelSnappingBias`, and texture
layout. Those APIs establish logical UI units and
rendering controls, not the GNOME/Xwayland
physical pixel mapping. The mapping is an explicit live calibration acceptance step using
the actual configured window and lossless PNG capture. The production decoder uses this
single calibrated interior crop for every status frame; model images use a separately
verified game/launcher client-area crop and never the full desktop. The harness models the
APIs and the pixel packer but cannot prove native filtering or compositor behavior.
The active-chat source is the Forever
[`ChatFrameUtil.lua`](https://raw.githubusercontent.com/Gethe/wow-ui-source/forever/Interface/AddOns/Blizzard_ChatFrameBase/Shared/ChatFrameUtil.lua);
the harness must exercise the same active-window and EditBox readback path rather than
inventing a clipboard or screenshot round trip.

## Scanner and addon changes after release

Keep `Core.lua` entirely unchanged. `Scanner.lua` initializes its additive
`ns.db.agentLastSaved` mapping if absent and records the in-memory UID, finished time,
planned/attempted/failure/row counters before it schedules the next run. Those fields are
SavedVariables only because the existing scanner already writes `CrowleyDB`; the agent
does not add a second global or claim persistence. `Scanner.lua` gains a pure status
projection and exposes the actual item/owned phase, start time, due time, cursor, and
six-pending block without returning private mutable tables. No scan query, throttle, result
event, or depth/coverage decision may be changed for telemetry.

`Commands.lua` keeps the existing user commands and status text, and may add only a
read-only agent status line useful for manual diagnosis. It must validate any new session
control input before changing state. No unrestricted Lua, generated command, `/crowley
scan force`, trading action, or hidden command is added. `Crowley.toc` loads Agent.lua
after the scanner and before commands; if the live client rejects the declared frame or
texture APIs, the addon fails visibly and the session does not proceed.

The Lua harness must model native empty/nonempty tables, frame/texture scale and color,
`GetTime`, reload boot changes, frame updates, `ChatFrameUtil.GetActiveWindow()` with an
EditBox `HasFocus()`/`GetText()` readback, and screenshot cell extraction closely enough
to test the serializer. It must preserve existing native query tests and add
Lua-to-pixel-to-Python fixtures whose bytes are decoded by the production protocol code.

## Deterministic controller and durable session package

The new `src/crowley/session/` package owns only local session orchestration. The planned
modules are `protocol.py` (strict frame and snapshot decoder), `clock.py` or equivalent
injected clock interfaces, `driver.py` (narrow desktop actions and guardian), `model.py`
(selected Luna decision boundary), `controller.py` (state machine), `journal.py` (atomic
durable state), and `cli.py` (status/start/resume/pause/stop/closeout). The package reads
the existing companion's stable files and HTTP/journal evidence but never writes
SavedVariables or `Crowley_Data`, never uploads scans itself, and never tests against the
deployed database.

The controller states and legal transitions are:

```text
STOPPED -> NATIVE_CALIBRATION -> INPUT_CALIBRATION -> ARMED -> RECONCILE
RECONCILE -> LOGIN_REQUIRED|READY
READY -> WAIT_DUE -> SCANNING -> QUIET_SAVE -> SAVE_RELOAD_SENT -> SAVE_RELOAD_WAIT
SAVE_RELOAD_WAIT -> UPLOAD_WAIT -> ACK_RELOAD_SENT -> ACK_RELOAD_WAIT
ACK_RELOAD_WAIT -> REOPEN -> WAIT_DUE (repeat mode or validation needing another interval)
ACK_RELOAD_WAIT -> DISK_CLEANUP_SENT -> DISK_CLEANUP_WAIT -> STOPPED
closeoutRequested is orthogonal to the current phase; SCANNING waits for a natural saved
  outcome, then follows QUIET_SAVE and the exact save/upload/ack/cleanup path
any active state -> PAUSED on explicit pause, lease loss, or human input
explicit stop sets stopRequested=true and revokes input without replacing the recorded
  in-flight phase or uncertain action intent
explicit closeout or validation completion sets closeoutRequested=true without replacing
  the current phase or replaying an already-issued action
any active state -> BLOCKED on stale/foreign frame, identity mismatch, credential or
                     repeated conflict, rejected/missing acknowledgement, companion failure,
                     malformed/mismatched payload, or timeout
stopRequested -> STOPPED once the current natural scan/reload outcome is observed;
  all input stays revoked and no cleanup or new scan starts
PAUSED -> RECONCILE only on explicit resume and a fresh identity/telemetry reconciliation
          (or NATIVE_CALIBRATION -> INPUT_CALIBRATION when profile/source evidence changed)
BLOCKED -> RECONCILE only on explicit resume after the blocker is reconciled; no auto-retry
```

On startup or restart, the controller first releases guardian input, reads the journal,
and captures a fresh frame. A restart always enters durable `PAUSED` with
`restartRequiresResume=true`, even if `closeoutRequested` was already set; it never
continues closeout, replays an uncertain click, slash command, reload, login, or scan
until an explicit resume performs reconciliation. A single `fcntl.flock` lease covers the
controller and its guardian;
the lease has a generation. Pause, human takeover, process cancellation, and guardian
failure increment the generation, release held input, and reject every queued action from
the old generation. The durable journal records profile, lease generation, controller
state, frame boot/sequence/CRC, observed sweep UID, expected acknowledgement IDs, action
intent/result, deadline, retry count, `stopRequested`, `closeoutRequested`, and blocker
without recording credentials or image secrets. `closeoutRequested` is durable and is
carried unchanged through save, upload, acknowledgement reload, and disk-cleanup states;
it is cleared only after stable empty-queue closeout. Reload evidence is structured as
`expectedBoot`, `newBootLoaded`,
`stableSavedVarsUid`, `atomicCompanionUploadedUid`, `dataAckUid`, and
`diskCleanupPendingCount`; these fields replace free-form log claims.
The durable calibration record includes the game child geometry, interior crop, XTEST and
human-source observations, driver version, and native performance results. A geometry,
display, XInput hierarchy, or driver-version change invalidates it and forces both
calibration states before the next input.

The daemon exposes an explicit local Unix-socket IPC endpoint, mode 0600, for `status`,
`pause`, `resume`, `stop`, and `closeout`. Each request includes the caller's observed
journal generation; the daemon persists a pause/stop/closeout transition and increments
the generation before replying, so an old client cannot enqueue cleanup after revocation.
`pause` immediately releases the guardian and drains/rejects old-generation actions;
`stop` does the same while preserving the pending queue, recorded in-flight phase, and
uncertain action intent until the natural current scan/reload outcome is observed; it
then enters `STOPPED` and never starts cleanup. `closeout` sets
`closeoutRequested`, forbids new scans, and may finish an already-running authorized scan
and its exact upload/ack/cleanup sequence. `resume` is the only operation that can arm
work again and always starts with fresh reconciliation; after a rejected/missing ack it
must reconcile the exact stable files before leaving `BLOCKED`. IPC replies include the
durable state and generation, not free-form log text. A restart reads these records and
never auto-resumes. A stop does not silently clear an already durable
`closeoutRequested`; an explicit later resume either continues that closeout after
reconciliation or, when no closeout was requested, remains stopped. A closeout request
received during `SAVE_RELOAD_*`, `UPLOAD_WAIT`, or `ACK_RELOAD_*` sets the durable flag but
lets that in-flight state finish exactly once; it never cancels and replays an uncertain
reload or upload.

Steady-state waiting is local and model-free. The controller adopts an automatically
started scan from telemetry and never starts a second one. It considers a sweep finished
only when the scanner is idle, the saved UID is present, and the saved counters are
available. It then enters `SAVE_RELOAD_SENT` and issues exactly one prepared `/reload`
after the fresh-idle and quiet-margin checks. `SAVE_RELOAD_WAIT` admits exactly one fresh
boot identity; exact repeated `(boot, sequence, CRC)` samples are `NO_CHANGE`, and new
sequences from the old boot do not satisfy the wait. Boot churn, a stale deadline, or an
unexpected identity blocks. The controller separately parses a stable SavedVariables file
and records `stableSavedVarsUid`; the in-memory `lastSaved.memoryUid` never proves disk.

`UPLOAD_WAIT` uses only stable, atomically written evidence. The existing
`~/.local/state/crowley/companion-state.json` must be unchanged across two polls and
contain the exact sweep UID with a post-finish upload record. The existing generated
`Crowley_Data/Data.lua` must likewise be unchanged across two polls and contain that exact
UID in its `ackedScans` set. The parsers accept only the known JSON/Lua keys,
types, and UID arrays; they do not consume free-form logs. HTTP 200, database acceptance,
ack publication, and ack loading remain separate evidence stages. Finish-to-accepted-upload
must be at most 60 seconds. The
controller then enters `ACK_RELOAD_SENT` and issues one further reload, with the same
one-fresh-boot wait and `NO_CHANGE` allowance. Only `ACK_RELOAD_WAIT` may declare the UID
loaded when the new boot's `loaded.ackedIds` contains it and its `pending.ids` no longer
contains it. This prevents a prior boot's loaded ack from winning a reload race.

Before a sweep can qualify, the controller reads the exact stable
`WTF/Account/*/SavedVariables/Crowley.lua` payload and `CrowleyDB.scans[uid]` entry
through the existing pure `crowley.core.savedvars` parser and existing strict
`crowley.core.scanformat.validate_v2_envelope` format-2 validator. It must match the
observed UID, configured `beta-normal-alliance` house, character/realm/context, plan hash
and canonical plan JSON, `format=2`, envelope start/finish, `numObservations=428`, and
`numRows` exactly. From that decoded payload it records a durable `format2Evidence`
object containing per-item query start/finish times, `kind`, `coverage` (`full`,
`bounded`, `incomplete`, or `unqueried`), source completeness, row count, and priced-row
count, plus total full/bounded/incomplete/unqueried counts and commodity/item/owned row
counts. Telemetry counters can locate a candidate sweep but cannot prove qualification.
A malformed payload, UID/house/plan/envelope/counter mismatch, missing item, invalid
query window, or disagreement with the strict parser rejects the candidate and preserves
the evidence for diagnosis.
If `closeoutRequested=true` at this point, the controller goes directly to
`DISK_CLEANUP_SENT`; it does not reopen the AH or schedule another sweep. Whenever another interval is required (repeat mode, or validation below three consecutive
qualifiers, including after a reset), it performs `REOPEN` and records the next due start.

For final closeout, `DISK_CLEANUP_SENT` performs exactly one normal `/logout` after all
acknowledgements are loaded, then verifies character select and stable on-disk empty queues. `DISK_CLEANUP_WAIT` requires stable SavedVariables and the
exact on-disk pending queue to be empty before entering `STOPPED`. The controller uses
atomic companion-state and Data.lua parsers with strict schemas and stable mtime/size
observations; free-form logs, a single in-memory frame, or a presumed reload completion
are never acceptance evidence. The next regular cycle may write a new scan while loading
the prior ack, but the exact UID lists and explicit wait states govern that race. It
reopens the AH from the verified stationary auctioneer location before the next due time,
and records a late start instead of forcing a catch-up scan if the margin was missed.

The journal has a durable `mode` of `validation` or `repeat` and a qualification record:
`{streak, totalAccepted, cadenceSeedStart, lastAcceptedUid, lastStart, lastFinish,
lastReason, format2Evidence}`. A
validation session continues until three consecutive qualifying accepted sweeps, then
enters closeout; it is not a one-sweep mode. A qualifier requires all 428 IDs, zero
incomplete/unqueried items, real retained price rows, upload at most 60 seconds after
finish, exact ack loaded after the fresh boot, and AH reopened before the next due time
when another interval is required. The first qualifying sweep is the cadence seed:
it records `cadenceSeedStart` and does not need a preceding interval. The second must start
at `cadenceSeedStart + 900 ± 5` seconds, and the third at
`cadenceSeedStart + 1800 ± 5` seconds; the third's acknowledgement then sets
`closeoutRequested=true` and closes out without requiring a fourth AH reopen. Every completed nonqualifying sweep resets `streak` to zero and clears `cadenceSeedStart`
with a durable reason, including partial coverage, late cadence, missing priced categories,
zero-price evidence, and upload latency over 60 seconds. Validation then continues unless
a separate blocker requires explicit reconciliation. A rejected or missing acknowledgement resets the
streak and clears the cadence seed, records the exact UID/blocker, and enters `BLOCKED`; it
cannot continue or restart until explicit resume
performs reconciliation of the stable SavedVariables, companion state, and Data.lua.
Repeat mode continues indefinitely until an explicit pause, stop, or closeout command.
Qualification records are atomically persisted before the next interval and are reconciled
on restart.

At closeout the controller stops new collection, lets an already-running scan reach its
natural saved outcome if the session is still authorized, performs the exact final upload
and acknowledgement reload, then the normal disk-cleanup `/logout` and stable-file
parse. A pause at any point stops all input and leaves the pending queue for explicit
resume; it does not issue a logout, reload, upload, or cleanup action after revocation.

## Desktop driver, lease, and human takeover

The source-controlled driver replaces the pilot's `/tmp` helpers and is a narrow Xwayland
profile for this measured GNOME/Wine host. It resolves the game window and PID from fresh
`xprop`/`xwininfo` evidence, checks
the configured title/class, geometry, foreground focus, and one-client invariant before
each input sequence, and uses lossless `gnome-screenshot` PNG capture plus Pillow for
pixel decoding. Pillow is an actual dependency because it is absent from the current
environment and the driver must decode PNG without OCR or an external image fallback.
`DISPLAY=:0`, Xauthority, capture command, and target window identity are explicit config;
the service must propagate them from the measured GNOME/Xwayland session and must not guess
them from a cloud or shell session. `XDG_SESSION_TYPE=tty` is not used as a backend
detector because the observed game inherits a GNOME/Xwayland display with
`WAYLAND_DISPLAY=wayland-0` and `XDG_RUNTIME_DIR=/run/user/1000`.

The supported profile adopts the existing one-client game and its reconnect control. The
executor exposes named, state-bound actions only:
`dismiss_disconnect`, `reconnect_game`, `select_arthur`,
`enter_world`, `focus_game`, `open_chat`, `type_allowlisted_command`,
`submit_command`, `reload`, `open_ah`, and `logout`. The model can return only one of
these names plus the fixed target identity; it cannot emit coordinates, text, shell, Lua,
or an action sequence. Executor-owned calibration resolves the configured game window and
known controls from fresh geometry and visual anchors; it may inspect the launcher only for
the observation-only diagnostic crop. It does not become a generic desktop framework.

Each action has an exact precondition, postcondition, and retry budget. A disconnect
`dismiss_disconnect` starts only on the known `WOW51900319` modal and ends with that
modal absent (one attempt). `reconnect_game` starts on the known in-game reconnect
control while the one existing WoW client is still present and ends at character select
or a declared blocker (one attempt). `select_arthur` starts at the pinned Classic
Beta PvE 2 character list and selects the exact Arthur Aguafuerte row (one attempt).
`enter_world` starts with that identity selected and the Enter World control visible, and
ends on a fresh world-ready telemetry identity (one attempt). Any credential, MFA, realm,
or account conflict stops immediately; the driver never enters credentials.

`open_ah` starts world-ready at the configured stationary Auctioneer Buckler location and
ends only when the expected auction house is visually open and `ahOpen=true`; it has one
bounded attempt and no movement or arbitrary travel. `reload` starts only when the frame
is fresh and idle with the configured quiet margin and ends only through the explicit
one-fresh-boot wait. `logout` starts only in an idle closeout state and ends at character
select. No arbitrary shell, Lua, movement hold, client launch argument, buy/post/bid/
cancel action, or generated script is accepted.

Launcher reconnect and launcher Play are outside this supported profile. If the game
process disappears or a launch is required, the controller blocks for explicit operator
handling; it does not click Play. A future launcher path would require a freshly verified
zero-game-client precondition and an exact one-client postcondition, but that path is not
implemented in this contract. An Online Battle.net profile alone never authorizes it.

For a slash command, the executor first focuses the verified game window, presses Enter to
open an empty chat box, and requires `chatEdit.active=true`, `focused=true`, and
`text=""`. It then types exactly one of `/crowley status`, `/crowley scan` (never
`force`), `/reload`, or `/logout`, reads back the exact active EditBox text from the
telemetry frame, and presses Enter once. If a nonempty/unexpected buffer is observed, it
presses Escape once and blocks on any mismatch; it never trusts clipboard intent or asks
the model for a screenshot round trip. Command submission is followed by a fresh visual
and telemetry postcondition; dispatch success is never treated as in-game success.
Every action is bounded by a retry budget and monotonic deadline, and any postcondition
failure enters `BLOCKED` rather than retrying indefinitely.

`INPUT_CALIBRATION` is closed by default: the controller has no permission to send game
or launcher input until this live gate passes. After the implementation exists, it creates
an ephemeral non-game GTK/X11 calibration window, verifies its title, PID, XID, geometry,
and focus, and observes XI2 events on the root display. It repeats the harmless F13 and
left-click test from the canonical preflight, recording the proven XTEST keyboard/pointer
sources and target-child events. This proves only those synthetic driver calls; it is not
human-input evidence.

With that same temporary window focused, the operator then deliberately supplies one real
key sample and one real pointer click while the observer is running. The resulting source
IDs, target XID, modifiers, and event classes are recorded as the host's human activity
signal. No root permission, synthetic event, or source-ID substitution may be used to call
this a human sample. The test also queues a harmless delayed action for the temporary
window; the operator's pause/human takeover must increment the lease generation, release
the guardian, and discard the queued action before it fires. The test asserts that no
post-pause action reaches the game or launcher. Its temporary process/window then closes
cleanly and the controller remains unarmed until the evidence is durable.

The runtime policy is conservative. XTEST sources are accepted only when the exact event,
generation, target XID, and deadline match the executor's currently declared action.
Compositor-forwarded sources, including relative pointer source 7, are never ignored by
device ID alone. A forwarded motion is admissible only if calibration proves it is the
deterministic echo of the current bounded pointer operation with the expected target and
no concurrent human sample; an unclassified motion, key, button, touch, or gesture revokes
the lease. Pointer moves are limited to the verified client-area target, and a button is
sent only after a fresh focus/window check. If the source cannot be correlated safely, the
driver blocks arming rather than guessing. Any human sample or explicit pause revokes all
input immediately, including cleanup, and only an explicit resume can reconcile and arm
again.

`NATIVE_CALIBRATION` performs the interior-crop rendering and performance measurements
without sending game or launcher input: it verifies the physical origin, all-cell colors,
lossless decode, initial/update limits, transient allocation bounds, and scanner baseline.
Only a passing native result permits `INPUT_CALIBRATION`; either failure leaves the durable
controller unarmed.

Deployment bootstrap is an explicitly authorized operator step outside the unarmed
controller: after code review the sole Luna game operator may adopt/reconnect the existing
client and load the installed addon normally under the repository game-control skill.
This makes world telemetry available for the read-only native gate. The controller itself
sends no game input until both calibration gates pass; operator bootstrap does not count
as proof that those gates passed.

The guardian is an independent process/thread with a monotonic deadline for every held
key/button. It releases on deadline, cancellation, focus loss, frame staleness, lease
loss, human input, model timeout, or parent death. XInput event monitoring is configured
for the same display; an event not attributed to the current action generation triggers
human takeover, revokes the lease, releases input, and prevents queued cleanup. The
explicit CLI pause is the authoritative takeover mechanism when the user is at the
keyboard; input monitoring is an additional stop signal, not permission to resume.

## Selected Luna adapter and model-only boundary

The only model adapter is the configured `gpt-6-luna` login/recovery adapter using the
existing local Codex CLI authentication. It wakes only in `LOGIN_REQUIRED` or a bounded
recovery state and receives the fresh structured screenshot/image plus a fixed prompt.
Before invocation, the driver verifies the one-client window identity and supplies only
the verified game client-area crop (or the exact launcher client-area crop for an
observation-only diagnostic; launcher actions remain outside this profile). The model
never receives the 1920x1080 full desktop with the
GNOME panel, dock, or unrelated windows. A missing, stale, or contradictory crop blocks
the turn.
It returns one schema-validated enum decision and target identity; the executor maps that
decision to the narrow allowlist (`dismiss_disconnect`, `reconnect_game`, `select_arthur`,
or `enter_world`). The model never receives desktop
tools and never emits shell, Lua, input, command text, or arbitrary coordinates. A state
not eligible for one of those actions, an identity mismatch, or an ambiguous image is a
blocker, not a request for a broader navigation decision.

The actual supported CLI boundary, verified in the parent preflight, is equivalent to this
clean invocation from a freshly created neutral directory:

```text
codex exec --model gpt-6-luna --ignore-user-config --ignore-rules
  --skip-git-repo-check -C /tmp/crowley-model-preflight-neutral
  --sandbox read-only --ephemeral --json
  --output-schema <decision-schema> -i <fresh-image>
  -c model_reasoning_effort="low"
  --disable hooks
  --disable shell_tool --disable unified_exec --disable code_mode_host
  --disable computer_use --disable apps --disable plugins --disable multi_agent
  --disable image_generation --disable browser_use --disable browser_use_external
  --disable in_app_browser --disable view_image
  -c mcp_servers.openaiDeveloperDocs.enabled=false
```

The pinned executable is `codex-cli 0.162.1`; startup hard-fails if the installed version
differs. `--ignore-user-config` and `--ignore-rules` are required so no user config,
project instructions, AGENTS/CLAUDE rules, hooks, or inherited MCP is loaded from the
neutral directory; the tested existing saved authentication remains available and is not
rewritten. Every switch in this command is an installed CLI option or feature/config key
observed by `codex features list`; there is no invented `--no-tools` flag. Images are
fresh files mode 0600 and are deleted after the bounded turn. The adapter must reject any
tool/function event or schema mismatch, enforce a subprocess deadline and cancellation,
send TERM then KILL to the whole `start_new_session` process group, and kill the child
before releasing the desktop lease.
The parent preflight emitted one known `item.error` saying Code Mode is unavailable
because its host was disabled, then completed with a valid structured decision and no
tool/command event. The adapter records that specific diagnostic and accepts the result
only when the schema is valid and no tool event occurred; any other error is a blocker.
It must verify that the exact model ID is available under the existing login; an
unavailable model, credential prompt, billing profile change, or unsupported image/schema
capability is a hard blocker. There is no model substitution, API-key provisioning, or
billing/auth change. Normal sweep waiting, completion detection, upload polling, and
acknowledgement polling never invoke the adapter.

## Service and configuration lifecycle

`deploy/crowley-session.service` is a user systemd unit running the installed local
controller with `Restart=on-failure`; a restart always comes up paused/stopped according
to the durable journal and requires explicit resume. `deploy/crowley-session.example.toml`
contains the measured profile, game window identity, display/capture settings, cell
geometry, `canvas_origin=(80,48)`, `canvas_crop=(80,48,256,256)`, model client-area crop,
quiet/reload/upload deadlines, configured character/realm/house/plan, session log/journal
paths outside git, exact model ID, and no secrets. The CLI provides
`status`, explicit `start`/`resume`, `pause`, `stop`, and `closeout`; no future calendar
window is guessed, silently armed, or cloud-scheduled. Installation and service enablement
are parent/operator work after implementation review.

## Ownership and exact implementation fence

After the plan gate, Luna owns the complete bounded implementation and fixes only these
paths: `addon/Crowley/Agent.lua`, `addon/Crowley/Crowley.toc`,
`addon/Crowley/Scanner.lua`, `addon/Crowley/Commands.lua`, `tests/wow_harness.py`,
`tests/test_addon.py`, a new `src/crowley/session/` package, `tests/test_session*.py`,
`pyproject.toml`, `uv.lock`, `deploy/crowley-session.service`,
`deploy/crowley-session.example.toml`, and `docs/REPEATING_SCANS.md`. No companion,
server, codec, schema, watchlist, migration, shared skill, unrelated proposal, or
production configuration changes are allowed. Parent owns deployment, live operation,
review integration, shared documentation, skills, commits, and git history.

## Automated verification and native acceptance

The implementation must add meaningful tests for:

- pure snapshot copies and Lua frame construction without scanner mutation;
- exact Lua snapshot JSON -> deflate -> black/white pixels -> Python decode;
- wrong magic/version/encoding, bad length/CRC, truncated/padded frames, stale and
  duplicate sequence, foreign boot, wrong window/crop/scale, and malformed JSON;
- strict key/type/range/array/count/phase validation, exact chat EditBox focus/text
  readback, cross-field identity/time/ordinal/pending invariants, uptime modulo wrap,
  and no clipboard-only command acceptance;
- frame-only native calibration/performance budgets, 16,384 texture reuse, inverse-scale
  anchoring, exact interior crop, model client-area cropping, and transient encoding
  allocation bounds before a soak;
- three fake-clock cycles with immediate exact-UID HTTP acceptance, upload deadline,
  one-fresh-boot save-reload and ack-reload waits, duplicate `NO_CHANGE` handling, and
  persisted queue cleanup;
- strict stable format-2 SavedVariables qualification, UID/house/plan/envelope/counter
  mismatches, malformed payloads, per-item timing and coverage evidence, and priced/kind
  row accounting;
- automatic scheduled-scan adoption and reload race prevention;
- incomplete/rejected upload, six-pending block, no retry storm, and preserved evidence;
- durable validation cadence seed, second/third start comparison, rejected-ack blocking,
  stop/closeout transitions, restart pause, three-consecutive closeout without a fourth
  reopen, and normal indefinite repeat mode;
- process restart, one lease, guardian cancellation/deadline, explicit pause/resume,
  human takeover, IPC generation fencing, and no queued input after revocation;
- closed-by-default non-game XI2 input calibration, synthetic-source evidence, deliberate
  human key/click sampling, safe pointer handling, unresolved forwarded-source blocking,
  and queued-action revocation without root permissions;
- model deadline/cancellation, wrong schema, tool-event rejection, exact model/flags,
  and zero model turns during ordinary scanning.

Before Sol's implementation review and again before handoff, run exactly:

```text
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
```

Database tests remain skipped unless a separately provisioned disposable database is
explicitly supplied. No deployed database, schema drop, service rebuild, or destructive
operation is needed for this feature.

Native acceptance first requires the measured frame-only rendering/performance gate and
the closed-by-default `INPUT_CALIBRATION` gate before controller arming or any soak. It
then requires three consecutive **new** 428-ID sweeps. The first qualifying sweep is the
cadence seed; the second start must be seed+900±5 seconds and the third seed+1800±5
seconds. The AH must reopen before the next due time after the seed and second sweeps.
The third's exact acknowledgement is followed directly by disk cleanup, with no fourth
sweep or AH reopen required. Every qualifying sweep must be proven from the exact
stable SavedVariables payload through the existing strict format-2 parser: full/bounded
coverage for every planned ID, zero incomplete/unqueried items, real retained commodity,
recipe, container, and equipment rows, matching UID/house/plan/envelope/counters, and
per-item query times. No telemetry-only or zero-row-only proof counts. Each finish-to-
accepted-upload latency must be ≤60 seconds, and exact acknowledgements must load with
zero pending after normal closeout. Demonstrate explicit pause stopping all input and
surviving restart, explicit resume, one configured game reconnect path, one-client
identity, durable status, no credentials, and autonomous continuation beyond a single
model task. Report per-sweep start/finish, attempted/full/bounded/incomplete/unqueried/
priced/row/kind counts, per-item timing gaps, upload and ack latencies, interventions,
pause/restart events, calibration evidence, and practical limits. Do not mark DONE until
the measured native requirements and all required checks pass.

## Concrete unresolved assumptions and read-only preflight

1. The primary Forever UI sources pin the Lua rendering calls, `SetIgnoreParentScale`, and
   logical scale controls, but the physical screenshot mapping, texture filtering, cell
   size at the current UI scale, and whether the high-strata canvas is visible above the
   game must be measured with the actual client. The configured interior canvas profile is
   `(80,48,256,256)` relative to the 1920x1080 game child, below the GNOME top panel and
   right of the left dock; calibration must verify that exact crop and may not change the
   user's display or game UI scale. The harness is not evidence of native pixels.
2. The observation-only host preflight established one GNOME/Xwayland display at `:0`,
   `WAYLAND_DISPLAY=wayland-0`, and `XDG_RUNTIME_DIR=/run/user/1000`. Lossless capture is
   1920x1080; the WoW outer window is 1928x1092 and the child game area is 1920x1080 at
   (0,0), with panel/dock visible in the full desktop capture. The actual configured
   service must carry this environment explicitly. `xdotool`, `xinput`, `xwininfo`,
   `xprop`, `gnome-screenshot`, `tesseract`, `codex`, and `uv` are installed; Pillow and
   Xlib Python packages are absent. No game input, reconnect, scan, or service/configuration
   change was performed.
3. The canonical evidence is `.archive/live-client/repeating-preflight.md` and its appended
   XI2 trace; exactly one WoW client and one Battle.net process stack were observed. The
   game showed
   the `WOW51900319` disconnected dialog; the authenticated Battle.net profile was Online,
   and Arthur Aguafuerte had been selected on the preceding character-select screen. No
   reconnect or game input was performed. The appended bounded XI2 test used only a
   temporary non-game GTK target: its F13 and left click were traced to XTEST sources 5
   and 4, respectively. A compositor-forwarded relative motion from source 7 also
   appeared over the existing Battle.net window during cursor positioning; its origin is
   unresolved. No human key or click was sampled, so source attribution is not complete.
   The later `INPUT_CALIBRATION` gate must perform the deliberate real sample and stop on
   a duplicate, conflict, credential, unexpected identity, or uncorrelatable event.
4. The clean model-only preflight used Codex CLI `0.162.1`, the neutral directory,
   `--ignore-user-config`, `--ignore-rules`, `--skip-git-repo-check`, and the exact
   boundary above. It preserved saved authentication, returned valid structured JSON for
   the disconnected dialog with no tool or command event, and made no config, auth, or
   billing change. It emitted one known Code Mode unavailable diagnostic because the host
   was disabled; the adapter must preserve and classify that diagnostic rather than hide
   it. Any other startup/turn error, tool event, unsupported schema/image, credential
   prompt, or model mismatch is a blocker. Cancellation under the configured deadline and
   live executor reconciliation remain implementation/native checks.
5. The harness currently lacks frame/texture and `GetTime` stubs, and the addon has no
   `Agent.lua`; those are implementation tasks after the gate. The observed scanner's
   private state and SavedVariables names are known, but the additive last-saved fields,
   stable file parsers, exact native render cost, and event-source attribution must be
   measured before live acceptance.

Sol's review should either approve this exact contract or identify a concrete field,
transition, or capability that cannot be implemented on the pinned profile. After the
parent releases the plan, Luna owns implementation, fixes, checks, and a final changed-
files/results/open-issues report.


## Correction round after first implementation review (authoritative)

The initial implementation failed final Sol review. Apply
[REVIEW-repeating-scans-1.md](REVIEW-repeating-scans-1.md) as a complete correction
outcome. This addendum supersedes conflicting initial implementation signatures
or measurement details; it does not loosen scanner, identity, input, or evidence
requirements. No new proposal gate is needed.

The lead Luna worker owns integrated controller/daemon/CLI/config/model/protocol/
evidence/addon/harness work and tests except the native worker's files. A separate
Luna native worker owns `src/crowley/session/driver.py`, new
`src/crowley/session/calibration.py`, `src/crowley/session/input_events.py`,
`src/crowley/session/guardian.py` if needed, and
`tests/test_session_native.py`. Workers coordinate their interface directly and
must not edit each other's files. Existing outer scope exclusions still apply.

Native calibration must be an owned live operation, not a public assertion API.
It may add fixed, strictly validated read-only `render` metrics to the snapshot:
construction time, update count and p99 over at least 100 actual updates, texture
count, effective scale/cell size, and transient Lua memory. Measure using a native
high-resolution clock; do not infer sub-frame CPU cost from frame-cached GetTime.
The lead owns the addon/protocol metric schema and communicates it to the native
worker. The native worker owns lossless pixel/identity proof and process RSS
sampling tied to the same process/boot, including observation before operator
bootstrap where construction baseline requires it. No invented values or copied
capture can produce a calibration result. Real renderer performance and 2x2
physical mapping must pass before the controller sends game input.

Scanner timing regression is evaluated from each actual strict format-2 native
qualifier against the pinned telemetry-free baseline; it is a final acceptance
gate, not an operator-supplied number required before any scan can run. This
separates pre-input rendering calibration from scan timing evidence without an
extra manually driven sweep.

The native worker's milestone is a fully executable non-game calibration and
cancellation workflow ready for focused review and the promised real human sample.
The lead's milestone is an integrated three-cycle daemon/CLI test and all required
checks. Both remain responsible for complete fixes and integration, with no GUI,
service/private config changes, or fabricated native evidence during coding.
Only the sole Luna game operator performs authorized live validation after review.


A further engine component review is recorded in
[REVIEW-repeating-scans-engine-2.md](REVIEW-repeating-scans-engine-2.md).
A separate Luna regression worker owns only `tests/test_session_regressions.py`;
the lead must not edit that file. Its assertions encode the reviewed production
contract independently while the lead fixes the implementation. Native component
review and final integrated verification remain required before any live arming.

The independent regression worker also owns
`tests/test_session_native_regressions.py`. The native implementation worker must
not change that file to make its implementation pass. Any genuine test defect is
resolved by the regression owner against the production contract.

The next full correction contracts are
[REVIEW-repeating-scans-native-2.md](REVIEW-repeating-scans-native-2.md) and
[REVIEW-repeating-scans-engine-3.md](REVIEW-repeating-scans-engine-3.md).
They preserve the original live acceptance and measurement requirements; green
batch tests are insufficient. In particular, do not substitute a post-load
memory baseline, operator-entered control coordinates, or boolean calibration
for actual preconstruction measurement, control-specific visual evidence, and
bound retained proof. Whole engine/native fix batches and re-review precede
physical input or installation.

### Executable measurement lifecycle clarification

The six named controls live in mutually exclusive scenes. Do not require all
six anchors to be visible, captured within one freshness window, or installed
in a batch during input calibration. Native rendering/input gates do not require
future login controls to exist in the current world scene. Instead, immediately
before each authorized named action, the production visual provider locates
that control on a fresh owned-client capture, measures coordinates, and seals
the identity, scene/control facts, capture reference, and timestamp. The driver
verifies that evidence and current scene before dispatch. Retain it for review;
do not substitute configured coordinates or a generic world frame. This
supersedes any earlier all-six-anchor prerequisite without weakening per-action
identity, freshness, cancellation, or control verification.

Construction measurement is a two-stage live handshake: establish the verified
client and observe/capture that the new Agent surface has not been constructed,
sample HWM, and publish an operator-visible bootstrap-ready signal. The sole
authorized Luna operator may then perform the normal login/reload that loads
the addon while the controller stays unarmed. Await construction and 100 new
updates on one boot/identity and enforce the original memory/render budgets.
An already-rendered surface cannot serve as a preconstruction baseline. If a
fresh load is needed, arrange the actual external bootstrap before measurement;
never replace missing evidence with a callback assertion or a post-load sample.

The lead owns the actual semantic visual producer through the selected bounded
Luna adapter; the native owner owns capture identity, sealed evidence admission,
one-use anchor dispatch, and cancellation. Neither may defer the producer to an
undefined backend method. To make fresh control measurement executable, the
selected low-reasoning Luna observer may identify a named control and its bounds
for an actual pending UI transition, including AH reopening. This supersedes the
earlier restriction of all model calls to login/recovery only. Polling, cadence,
scan progress, upload, acknowledgement, and ordinary waiting stay deterministic;
never invoke a model on every telemetry tick. Bound each visual observation by
deadline, exact schema, fresh owned capture and named action, without tools or
free-form input. Record actual model use and timing in acceptance evidence.

Native round-4 findings and the narrower correction ownership are in
[REVIEW-repeating-scans-native-4.md](REVIEW-repeating-scans-native-4.md).
No live compatibility mode is allowed for tests: mandatory fields and canonical
seals must be checked unconditionally. Update complete test fixtures to the
production contract. Baseline sampling must occur before the bootstrap-ready
signal, not merely before the first measurement capture after addon load.

Round-5 correction is in
[REVIEW-repeating-scans-native-5.md](REVIEW-repeating-scans-native-5.md).
One guardian fence must govern both game and calibration authority. Read-only
verification cannot mutate focus. Every input-producing backend operation must
carry explicit authority; only exact tracked release has post-revoke authority.
Pin actual stable modifier state from owned calibration rather than assuming
zero. Unknown forwarded events remain closed unless exact controlled echo
correlation is measured and sealed. No broad source allowlist is authorized.

A fresh controller process cannot treat a persisted native/input boolean as a
live gate, including when the persisted state was already PAUSED, BLOCKED, or
STOPPED. Archived calibration is audit evidence. Require fresh native and input
gates before arming a new owner; same-process pause/resume can retain its sealed
process-local evidence. Restart tests must construct a fresh driver and complete
the attempted arm path, including changed game identity.

### Engine round-4 correction ownership

The complete correction contract is
[REVIEW-repeating-scans-engine-4.md](REVIEW-repeating-scans-engine-4.md).
The controller worker owns only `src/crowley/session/{controller,journal,protocol,evidence}.py`,
`tests/test_session.py`, `tests/test_session_evidence.py`, and new
`tests/test_session_transitions.py`. The daemon worker owns
`src/crowley/session/{daemon,cli,config,model}.py`, `addon/Crowley/{Agent,Scanner,Commands}.lua`,
`addon/Crowley/Crowley.toc`, `tests/{test_session_runtime,test_addon,wow_harness}.py`,
`deploy/crowley-session.service`, `deploy/crowley-session.example.toml`, and
`docs/REPEATING_SCANS.md`. Coordinate transition and peak-metric interfaces before
editing shared contracts. Existing native and independent regression ownership
remains exclusive. No GUI, service activation, private configuration, deployed
database changes, or commits during these coding rounds. Require focused production
regressions, full integration checks, and independent Sol re-review before live gates.

Native round 6 is recorded in
[REVIEW-repeating-scans-native-6.md](REVIEW-repeating-scans-native-6.md).
For this correction batch, one native owner exclusively owns
`src/crowley/session/{driver,guardian,calibration,input_events}.py` and
`tests/{test_session_dispatch,test_session_native}.py`; this supersedes the earlier
split native ownership for the batch. Independent regression ownership remains
separate. Complete the entire review batch and coordinate original capture-time
provider changes with the daemon owner before final integration and Sol re-review.

Controller/evidence round 5 findings are in
[REVIEW-repeating-scans-controller-5.md](REVIEW-repeating-scans-controller-5.md).
The controller owner's existing seven-file fence remains in force. Complete all
restart uncertainty, per-intent lifecycle, evidence archive, strict queue/schema
and malformed protocol corrections as one batch, coordinating typed APIs with
the daemon owner. Tests must cover the reported production counterexamples.

Native round-7 findings are in
[REVIEW-repeating-scans-native-7.md](REVIEW-repeating-scans-native-7.md).
The consolidated native six-file fence remains exclusive. Complete the actual
positive synthetic/human/retention/resume path, helper lifetime, current-operation
echo correlation, and finite fresh capture admission before another review.

### Unified engine round-6 ownership

[REVIEW-repeating-scans-engine-6.md](REVIEW-repeating-scans-engine-6.md) consolidates
the remaining controller/daemon contract failures. One fresh Luna owner exclusively
owns `src/crowley/session/{controller,journal,protocol,evidence,daemon,config}.py`,
`tests/{test_session,test_session_evidence,test_session_transitions,test_session_runtime}.py`,
and `docs/REPEATING_SCANS.md`. This supersedes the split controller/daemon ownership
for this batch. All other engine/native files and both independent regression files
remain outside its fence. Correct and exercise one shared intent, recovery,
qualification and archive lifecycle before independent Sol re-review.

### Auxiliary correction ownership

[REVIEW-repeating-scans-auxiliary-1.md](REVIEW-repeating-scans-auxiliary-1.md)
is a separate stable-component correction. Its Luna owner exclusively owns
`src/crowley/session/{cli,model}.py`, `addon/Crowley/{Agent,Scanner,Commands}.lua`,
`addon/Crowley/Crowley.toc`, `tests/{test_addon,wow_harness}.py`,
`deploy/crowley-session.service`, and `deploy/crowley-session.example.toml`.
Coordinate the pre-logout fence command/telemetry with the main and native owners;
no overlapping files. The parent will resolve the measurement semantics before
changing the strict peak contract. No fabricated peak or unsupported API claim.

### Authoritative memory measurement refinement

[PLAN-native-memory-measurement.md](PLAN-native-memory-measurement.md) now
supersedes the earlier Lua peak and lifetime-HWM arithmetic requirements. The
host's reset5 capability was actually verified with preserved historical evidence.
Use two controlled reset HWM windows for the same128/16MiB limits and label Lua
heap samples as optional net diagnostics. Native, main-engine and auxiliary owners
must implement the explicit hold/measure/resume handshake and one strict schema
within their existing exclusive fences. No scan/input/cadence requirement changes.

The runtime pre-logout command is exactly `/crowley session fence` (lowercase
ASCII; no underscore/Shift injection). Scanner telemetry always includes
`scheduleFence={state,reason,command}`: state inactive/armed/refused, reason empty
except refused scan_active, and the exact command above. No optional legacy frame
shape. Only a fresh armed fence plus genuinely idle scanner/queue proof permits
the separate normal `/logout`. The auxiliary owner implements the handler; the
main owner implements schema/caller proof; the native owner adds the exact command
to its finite measured keyboard vocabulary.
