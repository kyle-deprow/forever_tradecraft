# Sol bounded closure review: transition r12 final r2

Reviewer role requested: Sol. Reliable serving-model and serving-effort metadata are not exposed to this worker, so I do not claim either.

I reviewed the five numbered requirements in `executors-r11-arbitration.md`, the prior Sol r2 report, the actual Opus r11 report, and only the 731-line/8-path final correction delta plus the implicated functions and tests. I made no source change, ran no test or application command, sent no game input, and performed no git operation. The 418 affected passes, duplicate-transition and final label/count/seal checks, parent 32 focused passes, parent final two passes, global Ruff/format/diff checks, and running full strict DB regression are supplied evidence. The running full suite is not treated as a pass.

Requirements 1, 2, 3, and 5 close at the intended boundaries. `LifecycleBackend` now refuses every unmodeled command in its own override; the successful click test records motion through postquery including the second consumed-seal check; the helper enters through `_begin_motion_phase`, rejects a missing phase origin and orphan primary, and reaches both real positive and mid-hold pre-button ownership checks; captured parser mutations cover parent, axis indices, label, and class count, while click/camera drift and the defensive empty-trace path assert zero dispatched input.

Requirement 4's production changes are also coherent: builder and seal reject zero displacement, the common evidence fixture is nonzero, producer refusal occurs before F13/move/click, transition modifiers/effective state are tied to the matching primary, caller substitution/query/extra raw/extra primary/duplicate transition/forwarded-echo mutations are re-fingerprinted, and the exact canonical-seal assertion is restored. One required negative does not isolate the new check, as detailed below.

## Must-Fix

None.

## Should-Fix

1. `tests/test_session_native.py:421-423` does not exercise the required transition-versus-event-proof root/event binding at `src/crowley/session/calibration.py:589-599`. It changes the transition root XID from the sealed profile root, so the older profile-root ancestry check at `calibration.py:551-565` rejects first. The test therefore still passes if the newly added root/event fields are removed from `motion_facts` membership, leaving a regression able to accept validly re-fingerprinted evidence whose primary Motion root/event XIDs disagree with its transition. Keep the transition and profile unchanged; parametrically mutate the baseline primary row's root XID and event XID in `event_proof`, recompute fingerprint/hash with the existing `resign` helper, and assert rejection as absent from the event proof. This is the only unclosed numbered acceptance boundary I found.

## Nits

None.

The frozen source otherwise appears ready for the later operational proof. This review does not claim native/GUI input, owned GTK seed, game, human, camera, movement, or cadence acceptance, and it does not claim the still-running full DB regression.

STATUS: NEEDS WORK
