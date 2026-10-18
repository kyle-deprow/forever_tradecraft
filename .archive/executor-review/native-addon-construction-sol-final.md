# Native addon construction — Sol final closure review

Reviewed the frozen candidate in `/home/dev/.cache/crowley/worktrees/native-addon-construction-final-20261018` against frozen R3, R4, both closure plans, the prior Sol R3 report, actual Opus R3 report, and parent adjudication. I inspected the R3-to-R4 publication changes, the two-function R4-to-final source delta, and the directly affected Scanner/Commands paths. I ran no tests, builds, game actions, or source mutations.

All eight candidate SHA-256 values match `native-addon-construction-final-freeze.json`. Relative to frozen R4, only `addon/Crowley/Agent.lua` and `tests/test_addon.py` differ. The overall base fence contains exactly the seven modified owned files plus the one owned fixture. The final plan hash, actual Opus R3 hash, and R4-freeze hash match the pins in the final freeze. I accept the parent's independent `242 passed in 29.48s` result as provenance.

The named R4 and final repairs otherwise close cleanly. Restore retains its marker through both checked publications and rolls second-publication failure back to a hidden, cleared, fenced, recoverable state. Finalize checks its inactive-fence publication before commit and restores the constructed marker/fence on failure. `BeginRecovery` now distinguishes real in-load pending state from malformed raw `restore_pending` data, arms the private fence on acceptance, and leaves raw malformed data untouched until the Restore callback canonicalizes it. Ordinary construction again retains its surface and periodic retry after a transient first publication failure. The expanded tests cover the required marker pairs, nonce boundaries, opaque 64-byte token, pre-load entry points, direct unconstructed calls, strict boots, held/0 refusal, publication failures, and the fixed slash/button recovery path.

## Must-fix

1. **Successful Finalize and successful restore do not actually rearm automatic scanning while the auction house remains open.** `Scanner.SetNativeConstructionFence(false)` attempts `Scanner.Schedule("native_construction_release")` immediately (`addon/Crowley/Scanner.lua:67-71`), but Schedule refuses whenever `nativeBlocked()` is true (`Scanner.lua:47-53,983-990`). Both callers clear the fence before committing the lifecycle that makes `nativeBlocked()` false: Finalize clears it while lifecycle is still `constructed`, then publishes and only afterward sets `finalized` (`addon/Crowley/Agent.lua:648-657`); restore clears it while lifecycle is still `restore_pending`, then sets `ordinary`, publishes, and commits (`Agent.lua:790-795`). Thus the only release-triggered schedule request is refused, and no request is made after the successful lifecycle commit. If the prior timer fired while construction was fenced, the repeating scan remains unscheduled until another external event. This violates the closed R3 rule that native release rearms the existing schedule when the effective fence becomes unarmed and the auction house remains open. After each successful transaction commits `finalized`/`ordinary`, invoke the release scheduling boundary again (without weakening the checked publication or failure rollback). Test the real Finalize and restore-load paths with AH open and a canonical plan, asserting a `timer_create` from `native_construction_release`; the current test at `tests/test_addon.py:845-857` directly toggles the fence in an already-ordinary lifecycle and cannot expose this ordering defect.

## Should-fix

None.

## Nits

None.

STATUS: NEEDS WORK
