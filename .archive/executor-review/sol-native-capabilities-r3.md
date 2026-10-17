# Sol source review r3

Reviewed the final r2 correction delta against the archived reviewed-r2 source and the adopted review-fix plan. I did not run tests or operate the game. The supplied validation evidence reports 141 focused tests passing, with the full strict run at 514 passing and 23 pre-existing global Codex CLI version failures; I do not treat that as a green full-suite result or as live qualification.

## Must-Fix

1. **Post-admission deadline expiry can still return while retaining both native proofs.** In `src/crowley/session/daemon.py:2263-2271` and `src/crowley/session/daemon.py:2316-2324`, route/viewport observation can establish a deadline, spend the remaining budget in capture/model work, and then raise when `_remaining_motion_budget()` is non-positive without calling `_invalidate_motion_admission()`. The same gap is reachable in the post-observation, pre-commit reserve/freshness checks in camera calibration at `src/crowley/session/daemon.py:2486-2491` and camera execution at `src/crowley/session/daemon.py:3174-3183`. Because `_serialized_motion` correctly no longer has catch-all invalidation, these branches leave the exact pre-existing `camera_mapping` and `movement_basis` objects installed. A slow route/viewport provider or a deterministic clock advance after the first native observation reaches these paths without any static request infeasibility. That violates the adopted narrow rule that inability to maintain the operation deadline after native admission/observation clears both proofs, and it permits a later request to reuse proofs after the current operation could not complete its required observation or pre-commit checks.

   Add explicit invalidation immediately before these post-admission deadline/reserve/freshness raises, or route them through a narrowly scoped helper that invalidates only after native admission. Do not restore blanket decorator invalidation or move static request validation behind the gate. Add deterministic-clock tests that seed the two exact proof objects, advance time during route/viewport work and during the camera pre-commit window, and assert zero physical commit input plus both fields cleared. Keep the existing exact-object-retention assertions for invalid requests rejected before native observation.

## Should-Fix

None.

## Nits

None.

The other requested r2 closures are present in the reviewed delta: the decorator releases its lock when initial clock setup throws; static invalid requests retain the exact proof objects; interaction, lease, generation, native observation, and exercised successor failures use narrow invalidation; real Lua/pixels/default-provider/public-entrypoint coverage includes all CTM and ground result classes; an allowed successor followed by another public command does not revive cleared proofs; ground stubs accept varargs; CTM failure priority and reasons are distinct; and the full-precision payload test uses the real codec and the supplied evidence records 1,735 bytes with 265 bytes of headroom.

STATUS: NEEDS WORK
