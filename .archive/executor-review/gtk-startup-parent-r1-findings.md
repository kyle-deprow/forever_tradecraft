# Parent completion audit: gtk-startup-final-r1

Parent reproduced33GTK/owned-workflow tests1.58s/exit0 and25helper tests0.39s/
exit0; global Ruff/format231files/diffcheck pass. Source scope is six paths,
including parent helper documentation,1434delta lines. Runtime/emitter/seal
outside the released regions remain unchanged. The startup boundary still has
these concrete gaps; close together within the existing five-file fence before
formal Sol/actual Opus review or native input.

## 1. Preserve one actual finite create deadline

create() currently establishes its deadline only after process launch/admission.
_verify(timeout=remaining) then computes a NEW now+remaining, which extends the
original deadline if time passes between caller and callee. The publication
select is followed by blocking stdout.readline(): a readable partial line can
block past the deadline. No final deadline check guards certificate return.

Validate a finite positive timeout before acquiring resources, establish the
absolute deadline once at create entry, carry it unchanged through publication,
each verification/read and completion, and bound partial identity reads too.
Use the existing cleanup/ownership path exactly once. Add meaningful fake-clock
coverage for time consumed by startup admission and between attempts, plus an
owned harmless partial identity pipe/process that never completes its line.
Prove no new budget and timely cleanup; do not dispatch GTK or desktop input.

## 2. Pending must not swallow facts already known to be invalid

Current early returns / broad catches turn contradictory evidence into a ten-
second retry rather than the required immediate failure:
- wmctrl exact XID with wrong PID/title is filtered away, then treated as absent;
- missing one client property masks a wrong/duplicate other property;
- missing map state masks already captured malformed frame extents;
- frame property parsing catches ANY error and returns pending if ANY other
  property is missing, hiding wrong/malformed/duplicate present frame facts;
- missing expected helper is tested before unexpected frame children;
- unavailable exact published client/frame process identity is treated pending.

Validate present identity/properties independently before deciding which facts
are merely missing. Reject explicit wrong/duplicate/malformed facts immediately;
check unexpected children before allowing missing expected children to wait.
Known published process identity errors are hard failures, not a new startup
state. Preserve only the closed recognized genuine initial pending states.
Add regressions with a malformed/wrong present fact AND a missing companion,
and extra-child-plus-missing-helper; require ONE attempt and exact cleanup.
Keep the successful initial-unmapped→fresh-ready lifecycle test.

## 3. Separate readiness validation from startup permission

show_human_prompt currently passes startup_readiness=True solely because map/
frame validation is conditional on that flag; direct _verify defaults skip those
fields. Make map/frame validity part of every certificate attempt. Only create
may interpret recognized incompleteness as pending and loop; post-ready checks
must fail immediately. Keep the actual existing post-ready drift regression.
No fallback certificate or second permissive verification mode.

Run focused new boundary cases, then affected GTK selection and whole helper;
scoped checks. Report exact results and requirement mapping, freeze afterward.
Do not rerun unrelated resource/DB/motion tests. Parent will reproduce final
boundaries and run focused independent Sol/actual Opus review. No GUI authority.
