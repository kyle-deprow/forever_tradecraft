# Autonomous startup and persistent takeover drill

User authorized implementation with a Luna/Sol loop and resumed Luna collection.
This replaces routine calibration gates per the independent Opus audit in
`REVIEW-calibration-architecture-opus-20261022.md`. It reuses the current executor;
there is no runtime or Rust rewrite. Assisted collection continues until a reviewed
cutover at a fully saved, uploaded, and loaded-ACKed scan boundary.

## Ownership and scope

Root coordinates, integrates, verifies, documents, commits and deploys. The
existing Luna scanner exclusively owns GUI input/capture. Core Luna implements
in a new isolated worktree from current main, without GUI or service mutations.
Sol reviews read-only. No peer API relay is needed: one core worker owns both
producer and consumer changes. The core worker may change only:

- `src/crowley/session/startup.py` (new cohesive startup/drill definitions)
- `src/crowley/session/controller.py`
- `src/crowley/session/driver.py`
- `src/crowley/session/daemon.py`
- `src/crowley/session/cli.py`
- `src/crowley/session/config.py`
- `src/crowley/session/model.py`
- `src/crowley/session/motion.py` (strict schema4 consumer validation only)
- `src/crowley/session/calibration.py`
- `src/crowley/session/input_events.py`
- `src/crowley/session/input_tool.py` (explicit guarded keyboard-step argv)
- `src/crowley/session/guardian.py`
- `src/crowley/session/protocol.py`
- `addon/Crowley/Agent.lua`
- `tests/test_session_startup.py` (new)
- `tests/test_session_takeover.py` (new)
- `tests/test_session.py`
- `tests/test_session_cli_motion.py` (public takeover lifecycle timeout only)
- `tests/test_session_runtime.py`
- `tests/test_session_transitions.py`
- `tests/test_session_regressions.py`
- `tests/test_session_dispatch.py`
- `tests/test_session_driver_actions.py`
- `tests/test_session_executor_dispatch.py`
- `tests/test_session_input_tool.py`
- `tests/test_session_native.py`
- `tests/test_session_native_regressions.py`
- `tests/test_session_motion_integration.py` (schema4 fixtures only)
- `tests/test_session_executor_movement.py` (schema4 fixtures only)
- `tests/test_session_performance.py` (schema4 assertion only)
- `tests/test_addon.py`
- `tests/wow_harness.py`

If a necessary file is outside this list, report the concrete dependency to root
before editing it. No other addon, server, database, unrelated motion feature, credentials,
desktop configuration, existing audit, plan, or main-tree runtime edits. Do not
commit or install. Do not carry the large frozen GTK rehearsal harness into this
implementation. Retain optional diagnostics without making them startup gates.

## Implement in this order

1. Define the small runtime startup result, durable drill record, and explicit
   invalidation causes. Wire the real default daemon/controller/driver path.
2. Replace mandatory native memory/GTK/typed-keyboard/human-per-process gates with
   an automatic passive startup check and one environment-bound drill.
3. Add the public takeover-drill operation/status, cancellation and persistence.
4. Port exact Stormwind auctioneer targeting and session-only interaction through
   the deterministic runtime executor, with actual HUD AH-open confirmation.
5. Run focused tests and lint, deliver a frozen diff and verification report.

## Required behavior

Automatic startup must not type, click, move, reload, construct/reset the addon,
or launch GTK. It verifies the actual game identity/focus, current display/input
environment, unique measured XTEST keyboard/pointer and hierarchy, native tool
identity/keymap, healthy registered XI2 observer, and at least three consecutive
valid advancing ordinary CRS1 frames. Reuse existing capture/parser/ownership
interfaces. Derive key expectations from the measured native keymap and actual
runtime vocabulary; do not require an unused Ctrl+A or synthesize a typed stream.
Reject unknown/malformed frames, ambiguous devices and unhealthy observers with
one concrete BLOCKED reason. No permissive branch on a failed proof.
Mint a fresh process-local sealed runtime input object only after these checks;
it supplies the real arm/Guardian/runtime consumers with their needed measured
hierarchy/profile, identity/geometry, keymap, modifier and event expectations.
Read the actual current native modifier/held-input state as well as the keymap;
the keymap alone cannot establish a modifier baseline. Refuse pre-existing held
keys/buttons rather than claiming or releasing another controller's controls.
Do not replace those interfaces with readiness booleans or fabricate a successful
old synthetic calibration stream. Observer forwarding must remain explicitly
attributed and paired at runtime, with an observed representation for its inputs.

Separate ephemeral readiness from durable human takeover evidence. Existing old
journal calibration booleans and process-local seals are not new drill evidence.
Preserve scan journal/no-replay/reconciliation data during migration. New process
startup recollects passive readiness automatically; it does not ask for another
human when a valid persisted drill still matches the relevant environment.

The durable drill binds actual stable display/input hierarchy/source attribution,
keymap, tool identity, and the takeover implementation version. Device names alone
are insufficient. Exclude incidental process ID, controller generation, ordinary
addon boot/reload, and unrelated source edits from the durable environment key.
Actual display/device/keymap/tool or takeover-contract changes require a new drill.
Use existing journal atomic persistence and validate record structure/fingerprint.
An arbitrary loaded flag must never grant readiness.

The explicit one-time drill uses the production curved pointer executor for a
small slow hover inside the freshly verified game, no click. It waits for genuine
non-XTEST input and proves Guardian pause/release; preserve detection latency and
the environment identity. UNKNOWN/observer loss must stop input but cannot count
as a successful human sample. Handle timeout, cancellation, process death, and
generation races; release/reap owned input and observer resources. A successful
drill leaves the session paused; explicit resume rechecks current state and
reconciles without replay. Never silently authorize unattended input before the
drill. Public CLI/status must make startup, drill-needed/running/passed and the
next action clear, without the old calibration sequence.

Use typed causes for readiness invalidation at real producer/consumer boundaries;
remove the current substring search over human-readable reasons. Ordinary reload,
CRC/decode errors and boot churn can block current telemetry, but must not erase
a still-valid environment-bound human drill. Observer death or game-process change
requires fresh passive readiness; an actual input environment change requires a
new drill. Unknown errors fail closed. Preserve ordinary human takeover pause and
the existing explicit handback behavior.

Keep Guardian independent watchdog and exact releases, generation admission,
process ownership/reaping, input provenance/forwarded-echo pairing, click interval
>=1s, curved Fitts motion, target rechecks, source/identity/focus guards, decoder
CRC, durable action intent/no-replay, original SavedVariables retention, strict
upload ACK and loaded-HUD ACK. Do not lower guards to make fixtures pass. Keep
native memory measurement and the GTK keyboard benchmark explicitly optional
diagnostics, off ordinary resume/startup. Do not run clear_refs at startup.

AH opening must support Arthur's verified Stormwind setup: exact target Auctioneer
Jaxon and the proven session-only CTRL-F12 INTERACTTARGET binding, verified empty
or already identical before setting. No SaveBindings or overwriting another
binding. Use the bounded executor command path and fresh target/range/scene facts;
the assisted helper is a behavior reference, not a runtime shell escape hatch.
Do not navigate. Stop with concrete evidence if target is absent or out of range.
Confirm HUD ahOpen before scanning. Remove the mandatory Ironforge Buckler anchor
from this configured default path rather than silently trying alternate NPCs.
Normal AH reopening must use these native pre/postconditions without calling the
model-based generic world/AH named-scene observer. This follows the approved
audit's deterministic routine/Luna-for-exceptions requirement. Keep model-based
scene recovery for actual exceptions; do not fabricate visual modal facts from
telemetry. Publish minimal native popup/menu visibility with explicit API
availability so an unknown dialog cannot consume Return before the empty-chat
postcondition. Refuse blocked/unavailable UI before input. Test the default
composed reopen path with model invocation refused and popup refusal before input.
The existing addon lacks exact target/range/interaction-binding telemetry. Add
only the native facts needed for this fixed route to Agent.lua and the strict
protocol, with the real Lua harness and decoder tests updated together. Read
`.agents/skills/crowley-client-contracts/SKILL.md` before this producer change.
Represent an absent target explicitly, and require fresh exact target identity,
literal range results and the binding action before dispatch. Do not infer those
facts from an empty field or from the successful submission of a query command.
The fixed conditional binding command may set only an empty/already-identical
CTRL-F12 action and must be verified afterward in native telemetry.
Live diagnostics also established that SoftTargetInteract=1 is gamepad-only;
Forever's normal Enable Interact Key checkbox selects Any=3 (Kbm=2 also supports
the keyboard). Publish the native mode with explicit unavailable representation
and refuse unsupported mode before chord dispatch. Runtime does not mutate this
setting; initial setup is a separately verified, reversible operator action.
Cover the complete command/key route: allowlisted fixed commands, keymap-derived
shifted letters and binding punctuation, the CTRL-F12 chord, semantic action
dispatch and named-state facts. Native private-fixture coverage should traverse
the actual guarded emitter for those new emissions; planner-only tests are
insufficient after the observed earlier modifier mismatch.

The scheduler remains anchored to actual scan starts at 900 seconds, including
across reload/restart; addon dueAt=0 alone must not cause early starts. Retain
current saved/upload/loaded-ACK/reopen stages and never replay an unresolved scan.

## Verification and completion

Run in the isolated worktree using `PYTHONPATH=src uv run pytest` for every changed
test module. Add focused tests through default daemon/public command routing and
real producer/consumer boundaries for: valid passive readiness; no-input startup;
three genuinely advancing frames; observer/resource cleanup and loss; durable
drill matching across controller restart; environment mismatch/corrupt/legacy
record refusal; real takeover versus UNKNOWN; exact release before persistence;
pause/generation races; normal reload versus device change; no-replay migration;
and deterministic Stormwind AH-open and refusal before input. Exercise actual
curved pointer dispatch/forwarded-echo handling, not only a plan builder.

Reuse retained native traces where suitable and document which are synthetic
versus real. Address or clearly isolate the independently reproduced existing
`test_production_pointer_dispatch_pairs_current_motion_with_forwarded_echo`
failure; the runtime cannot be declared qualified while that concern is unresolved.
Do not add another large calibration certification harness.

Run `uv run ruff check` and `uv run ruff format --check` on changed Python files,
and `git diff --check`. Report exact counts and any failures; no blanket baseline
waivers. Sol independently reviews the frozen diff; Luna fixes concrete findings;
root reruns checks before integration. Only after reviewed installation at a safe
scan boundary does scanner run startup, then arrange the user drill when available,
then a supervised complete autonomous cycle and takeover/resume test. Fixtures
do not prove live Mutter/Xwayland qualification. Report observed 900s cadence and
real ACK evidence; do not invent a 24h percentage gate or claim autonomy early.

Core completion report: worktree/base, changed paths, concise design/API summary,
exact verification output, remaining live acceptance steps, and immutable diff
and source hashes. Reply DONE only when the implemented scope is complete.

## Verified deployment constraints (root)

The installed Agent.lua resolves to the repository file through its addon
directory, and the installed crowley-session command imports this repository's
editable Python source. Neither is an independent installation copy. Freeze and
verify the complete bundle before any main-tree source promotion. At the fully
ACKed boundary, the GUI owner must stage an explicit schema3-to-schema4 reload:
verify the old loaded HUD with old code, admit only the reviewed addon-file
transition, send one owned reload, then validate the resulting schema4 HUD with
the reviewed parser before starting the updated daemon. Preserve the original
scan, transition receipts, releases and previous pins. Do not accidentally apply
new strict parsing to the old HUD before the reload command can be sent.

The mutable global Codex executable now reports0.163.0 but the project pins
0.162.1. The existing private 0.162.1 executable was actually verified; use its
explicit configured path without relaxing version validation. Root updates the
live profile path and accepted configuration digest only at cutover, so current
assisted helpers retain their matching pins until then. Active-repeat owner
restart must automatically recollect passive readiness and reconcile with the
stored drill; persisted PAUSED/STOPPED/stop-requested holds must stay held.

## Review corrections

R1 is frozen in `final-manifest.json` with complete diff SHA42f34d46203ffbdf33fa9e914bc9cd57bf735354fb1f7dab36c610c0dfd0c938.
Sol reviews that immutable worktree while parent independently tests it. Concrete
fixes use sibling worktree `autonomous-startup-takeover-20261022-r2`, initialized
from the same base plus the exact R1 diff. First correction owns only daemon.py
and test_session_startup.py: observer cleanup failure must always release drill
single-flight ownership, retain both failure diagnostics and unreaped resources,
and never save false PASS. Additional corrections require explicit bounded scope.
The second confirmed correction additionally owns driver.py and, if needed,
test_session_dispatch.py: runtime modifier event expectations must match actual
pre-transition XI2 states. Compare retained native records against the generated
runtime profile and exercise that new evidence through real guarded emission.
Retain exact Guardian validation and distinguish this from old measured-profile
native proofs.

Sol's final R1 report adds two bounded corrections: driver.py plus startup tests
must bind takeover hover to actual positive passive capture provenance (never a
fabricated zero or relaxed BindingMetadata), and controller.py/daemon.py plus
runtime tests must persist a concrete recoverable BLOCKED state when automatic
restart passive startup fails. Invoke the actual production hover planner/guarded
executor in regression coverage rather than stubbing the method under test.
The addon index1 comment may be corrected without changing behavior. R2 remains
offline until a complete frozen diff passes parent checks and independent review.
The positive-capture correction may also minimally change startup.py to carry
actual final passive-frame provenance in sealed runtime evidence. Preserve its
semantic validation and seal; do not substitute an unrelated local counter.

## Integration outcome (2026-10-23)

Frozen R2 complete diff4a56f4bd... passes Sol READY with no Must/Should and
parent independent753PASS/562.59s, Ruff22/format/diff clean. Root installed the
addon first; Luna sent one guarded reload; root independently decoded schema4
boot1792714266-396905/seq6 before promoting all23 files and restarting the owner.
Live passive startup, actual clickless hover/human drill and complete autonomous
cycle remain acceptance work; no live qualification follows from isolated tests.
