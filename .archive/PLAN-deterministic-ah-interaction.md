# Deterministic Auction-House Interaction Proposal

Status: **blocked pending a build-specific capability receipt**. This document
authorizes no implementation, binding change, or live input. Parent review and
sole-operator technical scheduling precede any later passive probe.

## Objective

Replace the pointer portion of `open_ah` when the character is already stationary
at the auction house and the intended auctioneer is already selected. A qualifying
path would use one freshly observed `INTERACTTARGET` binding, the existing admitted
keyboard executor, and a fresh action-specific auction-house-open postcondition.
Unknown, contradictory, or stale facts leave the action undispatched and retain the
existing observation/recovery path.

This is useful even before all visual observations become native: removing the
pointer path removes the initial pointer-anchor model call and the additional anchor
refresh call after movement. It does not by itself remove the existing pre-state or
two post-state model observations. Zero routine model calls is defensible only after
the complete native precondition and postcondition below are qualified.

## Facts established without input

- The exact Forever 1.60.1.70450 extracted interface source defines the
  `INTERACTTARGET` binding and the `softTargetInteract` CVar. The setting defaults
  off in source, but the live value is not established:
  <https://github.com/Gethe/wow-ui-source/blob/172a387e3ab85b26e6640d3058d5ec1e6ccd4c63/Interface/AddOns/Blizzard_SettingsDefinitions_Frame/Controls.lua#L66-L90>.
- The same build exposes `IsPlayerInWorld`, `IsPlayerMoving`, and
  `CheckInteractDistance`:
  <https://github.com/Gethe/wow-ui-source/blob/172a387e3ab85b26e6640d3058d5ec1e6ccd4c63/Interface/AddOns/Blizzard_APIDocumentationGenerated/PlayerScriptDocumentation.lua>.
  It also exposes `UnitGUID`, `UnitName`, and `UnitIsInteractable`:
  <https://github.com/Gethe/wow-ui-source/blob/172a387e3ab85b26e6640d3058d5ec1e6ccd4c63/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua>.
- Build-matched unit-token documentation includes `target`, `softinteract`, and
  `anyinteract` tokens:
  <https://github.com/Gethe/wow-ui-source/blob/172a387e3ab85b26e6640d3058d5ec1e6ccd4c63/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitSharedDocumentation.lua>.
- `AuctionHouseFrame` is a managed panel. Its show path sets the portrait from
  `npc`; its hide path closes the auction house; it has a dialog overlay and a
  bounded list of auction-house static popups:
  <https://github.com/Gethe/wow-ui-source/blob/172a387e3ab85b26e6640d3058d5ec1e6ccd4c63/Interface/AddOns/Blizzard_AuctionHouseUI/Shared/Blizzard_AuctionHouseFrame.lua>.
- `Agent.lua` already reads bindings with `GetBindingKey`, but publishes only the
  movement bindings. Its `ahOpen` field is an event-maintained bit and is not enough
  to prove the required scene, modal, control, and idle facts.
- The inspected persisted binding cache contains no explicit `INTERACTTARGET`
  assignment. A default key must not be inferred from that absence. The runtime
  binding remains unknown.
- The current driver admits keyboard work through the Guardian, focus and window
  identity, sealed XKB/keycode evidence, XTEST provenance, and delivered raw-event
  proof. Its generic action list does not currently contain an interact operation.

## Facts that block implementation

The first capability receipt must be passive and must preserve typed unknowns and
API-call failures. It must establish all of the following on the exact accepted
client/addon build before any key action is eligible:

1. `GetBindingKey("INTERACTTARGET")` returns one unmodified keyboard binding. Nil,
   multiple bindings, chords, mouse inputs, or a key outside a small predeclared
   driver allowlist fail closed. No code may call `SetBinding`, `SaveBindings`, or
   modify a cache/config file.
2. The fresh runtime value of `softTargetInteract` is known and disabled. The source
   default and an absent config entry do not establish the runtime value. An enabled
   or unreadable value blocks this first implementation because `INTERACTTARGET`
   may then select a soft target instead of acting on the explicit `target` token.
3. The selected `target` has an exact operator-approved auctioneer identity:
   `UnitName("target")`, `UnitGUID("target")`, and a stable NPC identifier. GUID
   parsing is allowed only after its format is verified for this build. Name alone
   does not establish identity. `PLAYER_TARGET_CHANGED` must advance a target epoch.
4. An interaction-range predicate is proven. `UnitIsInteractable("target")` is a
   candidate. A `CheckInteractDistance` index may be added only if its meaning for
   this auctioneer is demonstrated; the generated API declaration does not identify
   an auction-specific index. Unknown or false range state blocks input.
5. Snapshot-time auction UI facts are available and stable on this load-on-demand
   UI: `AuctionHouseFrame:IsShown()`, its dialog overlay state, and visibility of the
   known auction-house static popups. The capability receipt must show how absent
   globals and Lua errors become typed unknowns rather than false success.

Until these five facts exist, the deterministic route is a candidate only. It must
not press an assumed default key, target by remembered coordinates, treat `ahOpen`
alone as success, or silently fall back from a failed native fact to cached data.

## Proposed native contract

Add a versioned `interaction` object to the existing strict addon snapshot. Each
field is tagged `known`, `unknown`, or `error`; no exception text or player-derived
free text is serialized. A qualifying pre-dispatch snapshot contains:

- the current boot/sequence/time and character/realm identity;
- logged-in, in-world, alive, out-of-combat, stationary, and chat-edit-inactive
  facts;
- `ahOpen == false`;
- `softTargetInteract == false` with its accessor identity;
- exactly one `INTERACTTARGET` binding;
- target epoch, exact approved name, full GUID, verified stable NPC identifier,
  interactable/range booleans, and the exact unit token used.

The daemon obtains this snapshot after intent registration and binds its digest,
boot, sequence, target epoch, binding, and NPC identity into the driver request.
The driver accepts only a presealed, unmodified key operation matching the observed
binding. It retains the existing lease, current-generation, focus, window identity,
Guardian admission/registration-before-exec, capture epoch, XTEST, raw/delivered
event, cancellation, key-release, and child-reaping fences. Any failed check occurs
before key-down. The path emits no pointer event and does not measure or refresh an
anchor.

Success requires two fresh strict snapshots after the admitted key event, separated
by the existing settlement rule, with the same boot, controller identity, intent,
generation, and approved NPC identity. Both must show:

- an `AUCTION_HOUSE_SHOW` epoch newer than the pre-dispatch epoch, with no later
  close epoch, and `ahOpen == true`;
- `AuctionHouseFrame` present and shown;
- no auction-house dialog overlay or known static popup;
- the same world/character/realm, stationary player, and inactive chat edit.

This action-specific evidence proves that the intended selected NPC received one
admitted interact key and produced an unobstructed auction-house surface. It must be
represented explicitly in the named-state result; it must not synthesize the old
visual `idle` or `control` facts. If review concludes those labels cannot accept the
more specific evidence without weakening their meaning, native completion remains
blocked and the existing model postcondition stays authoritative.

Post-dispatch timeout, close, overlay, popup, identity drift, target drift, binding
drift, API error, Guardian revocation, or cancellation preserves the original phase
and causal failure. Key release and executor cleanup still run; a failure does not
retry the key or switch to a pointer click.

## Minimal implementation slice after the gate

Production ownership is limited to:

- `addon/Crowley/Agent.lua`: tagged interaction facts and event epochs;
- `src/crowley/session/protocol.py`: exact closed schema and bounds;
- `src/crowley/session/daemon.py`: eligibility, evidence binding, and two-frame
  action-specific postcondition;
- `src/crowley/session/driver.py`: one binding-derived admitted key operation using
  the existing Guardian executor and proof model.

Test ownership is limited to `tests/wow_harness.py`, `tests/test_addon.py`,
`tests/test_session_runtime.py`, `tests/test_session_dispatch.py`, and the smallest
real composed case in `tests/test_session_native.py`. Scanner wire data, saved
bindings, config files, pointer calibration, movement, navigation, native producer,
and model implementation remain outside this slice.

Executor changes require Luna implementation followed by independent Sol and actual
Opus source review. Under the existing sole-operator authorization, parent may
technically release a bounded read-only console/native capability probe before
implementation; the probe may enter read-only console queries, changes no binding or
config, and dispatches no interact action. Accepted
implementation and focused qualification must precede scheduling any interact-key
action. No probe or live action is released by this plan itself.

## Meaningful acceptance tests

- Lua and protocol tests cover missing/throwing/wrong-type APIs; nil, duplicate,
  modified, mouse, unsupported, and changing bindings; enabled/unknown soft-target
  mode; wrong or changing target identity/epoch; false/unknown range; absent/hidden
  frame; overlay/popup; show-then-close; and bounded privacy-safe serialization.
- Daemon tests prove every unknown or mismatch prevents dispatch, two fresh frames
  are mandatory, `ahOpen` alone fails, and original failure phase/details survive
  timeout, cancellation, and final-state drift.
- Driver tests prove exact sealed level-0 key mapping, one admitted press/release,
  focus/window/generation checks, Guardian external-input revocation, XI2/XTEST event
  proof, and release/reap cleanup. They assert zero pointer events and zero anchor
  observation calls.
- A composed test starts with the approved stationary target and binding, performs
  one real admitted key action, observes the two native post frames, and records no
  model call only when every fact above is known. Unknown-screen fixtures retain the
  existing model/recovery path.

## Open decisions

- Exact live `INTERACTTARGET` binding and whether it fits a safe presealed allowlist.
- Exact live `softTargetInteract` state.
- The auctioneer's stable NPC identifier and verified GUID extraction rule.
- A truthful auction-interaction distance predicate on this build.
- Whether the UI frame/overlay/popup facts are sufficient to replace the existing
  visual named-state labels, or merely supplement the current model postcondition.

