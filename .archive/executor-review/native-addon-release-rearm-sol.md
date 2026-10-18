# Native addon release rearm — Sol closure review

Reviewed the frozen candidate in `/home/dev/.cache/crowley/worktrees/native-addon-release-rearm-20261018` against the prior frozen final candidate, the bounded release-rearm plan, the freeze, the closure note, and the previously accepted final review. I reviewed only the two-function scheduling repair and its focused tests. I ran no tests, game actions, builds, or source mutations.

All eight candidate SHA-256 values match `native-addon-release-rearm-freeze.json`. The plan, prior final freeze, and prior Sol review also match their pinned hashes. Relative to the prior final candidate, the only production changes are the two declared calls in `addon/Crowley/Agent.lua`; the remaining test-only delta covers those calls. The other six fenced files are byte-identical to the prior frozen final candidate. I accept the parent's independent `244 passed in 31.55s` result as provenance.

The repair closes the accepted Must-fix at the correct transaction boundaries. Finalize retains the prepublication inactive-fence proof and rollback, then clears the marker, commits `finalized`, refreshes commands, and invokes `SetNativeConstructionFence(false)` again (`addon/Crowley/Agent.lua:648-659`). Restore likewise retains both checked publications and its failure cleanup/rearm, then clears the marker and in-flight flag before invoking the setter after the successful `ordinary` commit (`Agent.lua:791-809`). Neither failure path can reach the new call.

The repeated setter is safe under the existing scheduler contract. It schedules only when the logout fence is clear, the auction house is open, and no scan is active (`addon/Crowley/Scanner.lua:67-71`); `Scanner.Schedule` then applies the lifecycle/native fence, storage, plan, and cadence checks and advances the timer token (`Scanner.lua:983-999`). A prior release timer therefore becomes stale, and a live scan cannot overlap the new request. The focused tests exercise the real Finalize and restore-load paths with a canonical plan and an open auction house, require the postcommit `native_construction_release` timer, retain the strict inactive-fence frame assertion, and establish that checked-publication failure does not rearm (`tests/test_addon.py:721-751,866-910`).

## Must-fix

None.

## Should-fix

None.

## Nits

None.

STATUS: READY
