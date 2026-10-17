# Native motion capability wire amendment

Parent has reviewed and adopted this concrete amendment for Sol plan review. It grants no GUI, game, input, service, or deployment authority. No
source or test implementation starts until this plan is adopted and reviewed.

## Verified 70425 facts

The installed client is WoW 1.60.1 build 70425. The read-only parent receipt is
`.archive/executor-review/native-api-parent-verification.json`; provenance is
`.archive/executor-review/native-motion-api-provenance.md`.

- `pcall(C_CVar.GetCVarBool, "autointeract")` succeeded and returned the
  boolean `false`. This is the only observed Click-to-Move result.
- `GetUnitSpeed("player")` returned
  `0, 7, 7, 4.7222218513489`. The pinned community UI-source revision
  `b401e0332adfbf0460d319b06d8ea29279a941f1` names these positions
  `currentSpeed`, `runSpeed`, `flightSpeed`, and `swimSpeed`; it does not
  establish units or a universal upper bound.
- `IsFlying`, `IsFalling`, `IsSwimming`, `IsSubmerged`, `IsMounted`, and
  `UnitOnTaxi` were present as functions and each returned boolean `false` in
  the stationary observation.
- The observed frame rate was 71.153266906738. It is diagnostic only; it does
  not alter the existing publication freshness or operation deadlines.
- No movement, camera drag, Click-to-Move change, or calibration was performed.

The source revision is matching community provenance, not an independently
verified Blizzard or installed CASC source digest. The source labels establish
the tuple order only. They cannot turn `7` into a speed ceiling or establish
that the value is in the same units as `UnitPosition`. Model `ground_clear` and
`units_clear` remain visual corridor evidence and cannot substitute for native
state.

## Contract to implement

Keep CRS1 framing version, 128x128-cell grid/256x256-pixel crop, 2x2 physical cells, 2048-byte
capacity, 2000-byte payload limit, render/resource budgets, protected actions,
historical data, existing deadlines, and the shared two-unit movement ledger
unchanged.

The live snapshot schema moves from schema 2 to schema 3 in one migration. The
runtime decoder accepts only schema 3 after the producer migration; it has no
dual decoder or compatibility fallback. Existing schema-2 artifacts remain
immutable historical records. Update current test fixtures directly; never convert or rewrite historical
archives, original failed receipts, or scan-format-2 data.

Retain the existing `motion.speed` field as the current-speed scalar for the
stationary telemetry contract. Add one required strict `motion.native` object:

```text
native = {
  ctm = {
    accessor: "C_CVar.GetCVarBool",
    cvar: "autointeract",
    state: "disabled" | "enabled" | "unknown",
    reason: "" | "call_error" | "missing" | "wrong_type" | "nil_result",
  },
  ground = {
    state: "grounded" | "not_grounded" | "unknown",
    falling: "false" | "true" | "unknown",
    flying: "false" | "true" | "unknown",
    swimming: "false" | "true" | "unknown",
    submerged: "false" | "true" | "unknown",
    mounted: "false" | "true" | "unknown",
    taxi: "false" | "true" | "unknown",
    reason: "" | "call_error" | "missing" | "wrong_type" | "nil_result",
  },
  speedTuple = {
    current: finite number in [0,1000],
    run: finite number in [0,1000],
    flight: finite number in [0,1000],
    swim: finite number in [0,1000],
    unitStatus: "unverified",
  },
}
```

The exact six ground calls and their call signatures come from the pinned
70425 parent receipt; do not add another accessor. `ctm.state="disabled"`
requires a successful call, a boolean result, and `false`. Any call error,
missing function, nil, wrong type, or `true` is represented explicitly and
blocks affected motion. `ground.state="grounded"` is produced only when all
six predicates are observed as boolean false in the same sample. Any true or
unknown predicate blocks affected motion. The numeric tuple is named
diagnostic telemetry with unverified units; it is never used as an upper bound,
world-unit conversion, or replacement for measured role displacement.

State/field consistency is part of strict validation, not merely an admission
check: CTM known states require empty reason; unknown requires one failure code.
Ground is unknown if any predicate is unknown, with reason from the first failed
predicate in fixed falling/flying/swimming/submerged/mounted/taxi order. Otherwise
reason is empty and state is not_grounded iff any predicate is true, else grounded.
Reject every contradictory summary/value/reason combination. Sample all four
GetUnitSpeed returns ONCE per publication and derive both speedTuple.current and
motion.speed from that same result; require their exact numeric equality. The
existing finite serialization bound is not a physical speed ceiling.

Unknown capability state must not invalidate an otherwise valid stationary
snapshot. It must invalidate camera and movement admission. A missing or
malformed speed tuple continues to fail the existing native telemetry frame;
the producer must not invent numeric sentinels.

## Producer and consumer ordering

`Agent.lua` samples the native capability object in the same publication as
position/facing/speed. The producer validates the exact accessor identity and
return types, records failure state without selecting another accessor, and
publishes schema 3. `Probe.lua` remains diagnostic-only and cannot authorize
motion.

`protocol.py` owns the schema-3 exact-key validator, tagged state values,
bounded failure codes, finite tuple checks, and the unchanged CRS1 payload
boundary. `decoder.py` keeps the existing crop/identity/boot/sequence/freshness
behavior and hands the validated native object through unchanged; it must not
reinterpret or default capability fields. `MotionFrame` receives a typed native
capability value bound to its boot, sequence, capture time, and window identity.

Before camera calibration, camera dispatch, direct execute_motion_key /
_execute_motion_key_with_frame, movement-basis calibration, or waypoint dispatch, the daemon requires a fresh frame whose CTM state is
`disabled` and ground state is `grounded`. It must recheck the same capability
conditions immediately before the physical hold/drag/key admission. The
post-release frame must retain matching identity, boot, generation, and
capability state. Any CTM/ground drift invalidates the affected mapping or
basis and clears the retained admission evidence. The existing visual viewport
and route evidence, measured role basis, response checks, and post-release
feedback remain required.

Invalidation matrix: for any affected motion operation, a disallowed CTM or
ground state at initial admission, immediate precommit or post-release clears
BOTH camera_mapping and movement_basis before raising; later allowed values
never restore them. A failure to obtain/validate a required successor frame
also clears both, because the previous native admission cannot be established.
Do not clear these fields merely for an infeasible target rejected before native
observation. Test the actual stored fields, including successor exceptions.
Every direct key action obtains a newly observed successor frame before
run_motion_key_hold; require newer sequence/capture and preserved pose, identity,
boot, generation and native gate. Post-release checks remain mandatory.

Exact producer calls are IsFlying(), IsFalling(), IsSwimming(), IsSubmerged(),
IsMounted(), UnitOnTaxi("player"); no arguments for the first five. Parent
verified both staged beginning/tail screenshots and the actual result; ordered
expressions/arguments/digests are now in native-api-parent-verification.json.
Harness functions assert those arguments and exactly one call per publication.

The speed tuple is retained for diagnosis and future qualification only. No
calibration flag, synthetic speed, guessed unit conversion, or new speed limit
is introduced. Existing per-role displacement, direction, uncertainty, and
two-unit ledger checks remain authoritative.

## Exclusive implementation fence

Only these regions may change after adoption:

- `addon/Crowley/Agent.lua`: snapshot schema declaration and
  `movementTelemetry()` only.
- `src/crowley/session/protocol.py`: schema-3 version check,
  `_validate_motion` and native capability validators only. Existing payload/
  framing handling and MAX_PAYLOAD/CAPACITY are read-only.
- `src/crowley/session/decoder.py`: only the strict schema-3 sample handoff if
  required; no crop, threshold, identity, or freshness redesign.
- `src/crowley/session/motion.py`: `MotionFrame` native capability type,
  `from_sample`, capability freshness/binding, and affected admission helpers
  only.
- `src/crowley/session/daemon.py`: camera calibration/dispatch, movement-basis
  calibration, execute_motion_key/_execute_motion_key_with_frame, waypoint
  pre-admission and post-release capability checks, and related retained-field
  initialization/clearing only.
- `tests/wow_harness.py`: exact CVar, six predicate, and four-speed-return
  stubs with explicit success/error/unknown variants; no fallback behavior.
- `tests/test_addon.py`: real Lua producer snapshots and schema-3 serialization.
- `tests/test_session.py`: strict protocol/schema, migration rejection, and
  CRS1 payload boundary cases.
- `tests/test_session_native.py`: pixel decoder, `MotionFrame`, identity/boot/
  sequence/freshness, and capability-state negatives.
- `tests/test_session_motion_integration.py`: actual daemon camera/movement/
  calibration entrypoints with only external capture/model/process boundaries
  doubled.
- `tests/test_session_executor_movement.py`: measured-basis/waypoint gates and
  capability drift while preserving geometry, budgets, and the two-unit ledger.
- `tests/test_session_runtime.py`: default `SessionDaemon` construction and
  public entrypoints without manually injecting a capability provider.
- `tests/test_session_preferences.py` and `tests/test_session_regressions.py`:
  ONLY direct MotionFrame/current-schema fixture migrations required by the new
  mandatory capability. Preserve original assertions and historical negatives.


Do not modify `Probe.lua`, `Commands.lua`, `model.py`, `driver.py`,
`calibration.py`, CLI schemas, CRS1 dimensions, profile defaults, services,
data, or live client state in this amendment.

## Required regressions

The implementation is incomplete until these concrete tests exist and pass:

1. Producer snapshots preserve the four named raw speed values and existing
   scalar stationary telemetry. CTM false and all six ground false produce a
   grounded/disabled capability. Missing function, pcall error, nil, wrong
   type, CTM true, each ground predicate true, and each ground predicate
   unknown produce explicit state and still decode as stationary telemetry.
2. Schema-2 live frames, missing/extra native keys, invalid state strings,
   invalid failure codes, nonfinite/negative speed values, and wrong tuple
   shapes are rejected. The exact 2000-byte payload boundary remains accepted
   and the first oversized payload is rejected.
3. `MotionFrame.from_sample` binds native capability to fresh identity, boot,
   sequence, and capture. Unknown/true CTM or non-grounded/unknown ground
   blocks camera calibration and dispatch before any driver call.
4. Camera calibration and runtime camera dispatch each recheck CTM/ground
   immediately before admission; capability drift, identity drift, boot drift,
   stale sequence, and post-release drift invalidate the result and leave no
   retained mapping admission.
5. Direct key dispatch, movement-basis calibration and waypoint dispatch require the same native
   gate, retain independent measured role displacement and existing ledger
   limits, and never derive a role speed or world-unit bound from `run=7`.
6. Default `SessionDaemon` entrypoints exercise the production construction
   path. Tests must fail if the default path omits native capability validation;
   injected external command/capture/model doubles may not replace the
   producer, decoder, identity, or admission gate.
7. Producer→pixel decoder→MotionFrame→daemon tests cover one complete positive
   stationary capability path and every negative state above, including
   capability change between pre-admission and immediate dispatch.

## Verification and release order

After adoption, run focused addon/protocol/native/runtime/motion integration
tests under a fresh private desktop lease with strict thread, unraisable, and
fork warnings; then run the affected test files once together. Run scoped Ruff,
format, compile, and diff checks for the exclusive fence. Parent reproduces the
frozen result, followed by Sol and Opus source review.

Cutover is quiesced: stop controller admission and all native consumers (session
service remains inactive/paused; any diagnostic consumer must exit), place both
reviewed producer and consumer, reload addon normally, then require the first
fresh identity/boot/sequence-bound schema-3 frame before resuming any daemon
entrypoint. A schema-2 frame during cutover is a refusal, never compatibility.

Only after those checks may the addon owner perform that cutover and
measure installed capture latency, resource use, native frame cadence, human
takeover, and camera response. Those qualifications require fresh evidence and
do not follow from this plan or from the stationary API receipt. No live input,
movement, camera, or calibration acceptance is granted here.
