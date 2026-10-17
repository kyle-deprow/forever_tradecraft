# Passive AH capability publication plan

Status: proposed, revised after Sol plan review. This is a passive evidence
slice. It authorizes no AH action, `/run` typing, arbitrary Lua, key dispatch,
binding/CVar/config mutation, new network route, or Rust work.

## Decision and ownership

Use the existing Agent CRS1 status frames as the evidence source. Do not put
interaction identity in `CrowleyDB.probe`: the existing companion uploads that
object wholesale on `/reload`. Do not change `Probe.lua` or the companion.
The runtime owner will retain a bounded ordered bundle of decoded strict frames
in its existing private evidence path; the bundle is not a SavedVariables or
server/companion payload. The existing `/crowley probe` remains unchanged and
continues to report only its current diagnostic surface.

The future implementation owns exactly:

* `addon/Crowley/Agent.lua`: passive API reads, event epochs, and optional
  `interaction` frame member;
* `src/crowley/session/protocol.py`: strict validation of that member;
* `tests/wow_harness.py`, `tests/test_addon.py`, `tests/test_session.py`, and
  `tests/test_session_runtime.py`: producer, decoder, consumer, and reload
  coverage; and
* `tests/test_companion.py`: a regression proving the ordinary probe upload
  still contains no interaction receipt or identity.

`Probe.lua`, `Commands.lua`, `Scanner.lua`, `Core.lua`, `decoder.py`,
`companion/sync.py`, daemon/driver/controller, owner/config, server, model, and
input code remain unchanged. The parent may select the already existing private
status-frame collector for the ordered bundle; this plan adds no new uploader.

## Consumer-first rollout

The current validator requires an exact schema-3 root and therefore rejects a
new optional member. First deploy and test the validator/consumer that accepts
the optional member while still accepting legacy schema-3 frames. Keep the
producer at its old shape until that consumer is the stopped-owner version;
then release the addon producer and restart the owner. No extended frame may
be exposed to an old decoder, so this is a decoder-first cutover rather than a
claim that old binaries are forward compatible. `decoder.py` production code
does not need a change because it delegates snapshot validation.

## Exact frame schema

The root remains schema `3` with one optional `interaction` key. If present,
its exact keys are `schema`, `eventEpoch`, `binding`, `softTarget`, `target`,
and `ui`; `schema` is integer `1`. No other interaction keys are accepted.
`eventEpoch` has exactly `show`, `close`, and `target`, each unsigned integer
`0..4294967295`, scoped to the root `boot`. The Agent increments only for the
corresponding real event; counters never reset within a boot or decrease.

Each measured leaf is a closed `Fact` union with these exact variants:

* known: `{state:"known",value:<declared type>}`;
* unknown: `{state:"unknown",reason:<Reason>}`; or
* error: `{state:"error",reason:<Reason>}`.

Variant keys are exact: known has only `state,value`; unknown/error have only
`state,reason`. `Reason` is exactly one of `api_missing`, `call_threw`,
`nil_result`, `wrong_type`, `not_loaded`, `not_selected`,
`multiple_returns`, `invalid_shape`, `contract_unverified`, `unsupported`,
or `stale_epoch`. No raw error text is serialized. Known false is evidence of
false; unknown/error never becomes false. The validator applies UTF-8 byte
limits (strings max 96), unsigned integer bounds above, and rejects booleans as
integers.

Optional API results use a separate closed `OptionalFact<T>` union: known
present is `{state:"known",present:true,value:<T>}`, known absent is
`{state:"known",present:false}`, and unknown/error use the same two-key
variants as `Fact`. Thus a documented nil absence is distinguishable from an
API failure without encoding Lua nil as a guessed value.

The exact nested objects are:

```text
binding = {
  accessor: "GetBindingKey", action: "INTERACTTARGET",
  returnCount: uint 0..255, primary: OptionalFact<string>,
  secondary: OptionalFact<string>
}
softTarget = {accessor: Fact<string>, cvar:"softTargetInteract", value:Fact<bool>}
target = {
  unit:"target", exists:Fact<bool>, name:OptionalFact<string>,
  guid:OptionalFact<string>, npcId:OptionalFact<uint>,
  interactable:Fact<bool>, range:Fact<bool>, rangeAccessor:Fact<string>
}
ui = {
  frameLoaded:Fact<bool>, frameShown:Fact<bool>, overlay:Fact<bool>,
  popups:Fact<[{id:string<=64, visible:Fact<bool>}]>
}
```

The known `popups` array has exactly the ordered source-pinned IDs (zero to
eight, no duplicates); the exact allowlist and overlay member path are
build-pinned constants, not runtime-discovered names. `softTarget.accessor`
and `target.rangeAccessor` are known only when their source-pinned literal and relevant semantics are
verified; otherwise their fact is `contract_unverified`. All object
key sets, array bounds, and literal values are strict.

Cross-field rules are mandatory: `binding.returnCount` equals the protected
call's actual return count; a one-return valid binding has primary known
present and secondary known absent; any duplicate/extra return is retained as a
count and cannot qualify. `target.npcId` may be known only when the pinned GUID
grammar accepts the same known GUID; a name alone never qualifies. If target
existence is known false, name/GUID/NPC ID are known absent; if existence is
known true, a nil name/GUID is unknown `nil_result`. `frameShown` known
true requires `frameLoaded` known true. If the frame lookup returns nil under
the pinned load-on-demand contract, `frameLoaded` and `frameShown` are known
false; API absence/throw/wrong shape is error. `overlay` and each named popup
are known false only when their pinned accessor returns its documented absent
value (normally nil/false); missing/throw/wrong shape is error. A popup list
must use exactly the pinned IDs in their pinned order. This slice permits only one protected `UnitIsInteractable("target")` call
per publication. Its returned boolean supplies `interactable`. Only when the
source-pinned contract proves the required auctioneer-range meaning may the
same call also supply `range` (equal to `interactable`) and known literal
`rangeAccessor="UnitIsInteractable"`. Otherwise `range` and `rangeAccessor`
are unknown `contract_unverified`, even if `interactable` is known. No indexed
predicate or encoded accessor/index string is permitted in schema1; adding one
requires a reviewed protocol revision. A measured range false remains false.

The new object does not duplicate readiness facts. The consumer reads existing
strict root fields by name: `context` identity, `motion.speed == 0`,
`motion.combat == false`, `motion.deadOrGhost == false`, and
`chatEdit.active == false`. Scanner phase, cached `ahOpen`, and an opaque
"ready" aggregate are not promoted to stationary or action readiness.

## Build-pinned API table and five facts

Implementation is blocked until a reviewed table in the producer/tests pins,
for the installed build, each accessor's literal name, arguments, return arity,
return types, documented absence, and exception behavior:

1. `GetBindingKey("INTERACTTARGET")` is called once with Lua-5.1-safe vararg
   packing. A nonempty observed string of at most96UTF-8 bytes and no secondary
   return proves only the observed one-return fact. Preserve that exact raw
   string in private frames; this slice does not assert keyboard support or
   authorize a key. Fact1 remains incomplete until a later reviewed driver
   plan accepts that exact unmodified value in its explicit finite allowlist
   and seals its measured XKB/keycode mapping. Chords/mouse/unsupported values
   cannot qualify via string shape alone. Nil primary is exactly known absent
   `{state:"known",present:false}` without a reason; a second return is retained
   and disqualifies one-binding evidence. A count over255 is an invalid producer shape and
   prevents publication rather than truncating evidence.
2. The table pins the exact accessor for CVar `softTargetInteract`; only a
   returned boolean is known, `nil_result` is unknown, and missing/throw/type
   failure is error. A default or absent config is not evidence. The value must
   be known false for qualification.
3. `UnitExists`, `UnitName`, and `UnitGUID` are called for literal unit
   `target`. `UnitExists=false` is known absence; name/GUID nil without that
   absence is unknown. Stable NPC extraction requires the reviewed build GUID
   grammar; malformed grammar is `contract_unverified`.
4. The table pins only `UnitIsInteractable("target")`, called once as above.
   False is a real negative; nil/throw/type failure is unknown/error. Its
   auctioneer-range meaning must be source-proven before `range` can be known;
   indexed distance predicates are excluded from this schema.
5. The table pins `_G.AuctionHouseFrame`, its exact `IsShown`/overlay member
   path, and the fixed popup IDs/accessor. Load-on-demand nil is known unloaded;
   absent methods, throw, and wrong types are errors. Show/close/target epochs
   must advance on actual events only.

If any table row is not source-pinned on the actual build, the producer may
publish a typed `contract_unverified` fact for diagnostics, but the receipt is
ineligible and no deterministic AH action follows. The existing historical
source notes identify candidates but do not establish the installed runtime;
no placeholder popup ID, overlay path, GUID grammar, range index, or accessor
literal may be introduced to make the row appear known.

## Private ordered evidence and proof

The private qualification artifact is exactly:

```text
bundle = {schema:1, source:"agent-strict-frame", frames:[full decoded frames]}
```

`frames` contains 2..16 complete strict frames, in capture order, all from one
owner run. Every frame's root boot/sequence/wallTime and interaction object are
retained; no frame is overwritten and no identity is uploaded. Within one boot,
sequence and wallTime strictly increase. The target-change pair must show one
`target` epoch increment with no intervening boot; the AH lifecycle must show
the expected `show` and `close` increments in separate adjacent observations.
After `/reload`, a new bundle frame must have a different boot and a fresh
sequence/receipt; epochs are never compared across boots. If ordinary passive
operator activity does not produce the complete ordered bundle, the fact stays
unknown and the deterministic plan remains blocked.

## Tests and release gate

`tests/test_session.py` must construct exact legal/illegal snapshots and test
all union variants, reasons, bounds, key rejection, cross-field invariants,
legacy schema-3 acceptance, and the real CRS1 maximum legal snapshot through
Lua publisher plus Python decoder under the 2000-byte compressed limit. Addon
tests cover missing/throw/nil/wrong-type APIs, duplicate returns, known false
and known absence, source-pinned popup/overlay/GUID/range contracts, event-only
epochs, and unchanged scan/action state. Runtime tests cover consumer-first
cutover, two ordered same-boot frames, target/show/close transitions, and
post-reload different-boot regeneration. Companion tests prove the existing
probe upload omits the private interaction receipt. No test uses `/run`, fake
input, or a new network path.

Only after Sol accepts the plan and a current five-fact bundle is complete may
the parent plan a deterministic AH action. That later action still requires
fresh post-action frames, same identity/generation, new show epoch, no close,
no overlay/popup, and unchanged world/stationary/combat/chat conditions. Rust
requires separate accepted evaluator CPU evidence proving an actual bottleneck;
this passive publication cannot justify it.
