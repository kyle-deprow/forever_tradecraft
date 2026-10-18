# Native addon R3: source review closure

Preserve immutable R1 and R2. Build a new R3 tree from the exact R2 eight-file
candidate. This is the second fix round; do not expand into native/helper code.
Read frozen Stage B R3 + closure amendment and Sol R1 report in full. Existing
memory, freshness, cadence, wire and sole-operator contracts remain unchanged.
Own only Core.lua, Scanner.lua, Agent.lua, Commands.lua under addon/Crowley;
tests/wow_harness.py, tests/test_addon.py, tests/test_companion.py, and the existing
native-construction-unknown-savedvars fixture. No main source edits, deployment,
GUI, config, daemon/helper changes, commits, reset, stash, or broad formatting.

## Required corrections and real boundary checks

1. Keep native blocking private. Do not invent public scanner/pending reasons.
   Native effective scheduleFence uses existing armed state and EMPTY reason.
   Public status retains the existing ready/scheduled and storage-blocking rules.
   Decode actual publication bytes via decode_frame after defer, Construct,
   Hold/Measure/Resume/Finalize and successful Restore reload. Strict protocol
   source is read-only; never loosen it to accept addon mistakes.
2. Exact no-argument recover command performs addon-local admission and refreshes
   the Commands-owned panel atomically. Extra arguments and pre-command Restore
   clicks are inert. No direct test-only admission call. Recovery remains allowed
   after Finalize clears the marker while its Restore panel remains available.
3. Commands owns explicit shown/enabled control states. Restore click disables
   both controls while reload is pending. Its two-second fallback binds the exact
   nonce AND load, then refreshes the panel only for that same attempt. Test an
   older timer after a newer restore attempt: it cannot enable the newer control.
   Same-token/no-reload fallback re-enables Restore. Next successfully restored
   ordinary load hides the panel despite immutable first-load decision.
4. Construct and restore-load success require first publication to succeed.
   Failed initial serialization/render/publication must detach OnUpdate, hide
   all partial owned frames/textures, clear frame bytes/surface, retain native
   fence and reachable Restore, and mark failed/restore-only appropriately.
   Inject both failure paths at real initial publication after allocation, plus
   a partial texture-construction failure. No acceptance or constructed marker
   may survive a failed Construct publication. Normal periodic callback attaches
   on success and advances after Resume/Finalize without manual Publish calls.
5. Both native Buttons must inherit the existing UIPanelButtonTemplate (or use
   explicitly rendered font/textures with equal certainty). Retain and assert
   that template/visual contract in the harness; merely storing text is not
   evidence of rendered native controls. Keep Commands owner/fixed panel geometry.
6. Add closed marker/lifecycle cases: scalar types; missing/extra/wrong-type
   fields; every state/attempt pair; token empty/64/65 bytes/whitespace/control;
   exact 24-lowercase-hex recovery token; valid armed/deferred/constructing/
   constructed/failed/restore_pending; preserve malformed raw markers, no HUD.
   Cover unknown-decision manual/event/timer/rearm refusal before ADDON_LOADED,
   late Construct refusal, unconstructed methods with no side effects, native
   and logout fence independence, AH-open schedule rearm after native release,
   full Restore save/new-load/strict publication cleanup.

Parent independently reproduced two additional R2 defects via real callbacks:
post-Finalize recover returns recovery_not_required; a second Restore attempt
gets re-admitted by the first attempt's two-second timer. Close both.

Run uv run pytest -q tests/test_addon.py tests/test_companion.py --maxfail=1;
scoped Ruff/format/compileall and git diff --check; repeat existing four native
Lua frame/atlas smoke checks. Report actual commands/results and any remaining
question. Freeze new hashes only after all checks. Sol and actual Opus then
review the combined closure before native slice release. Native live callbacks,
templates and installed evidence remain later live qualification work.
