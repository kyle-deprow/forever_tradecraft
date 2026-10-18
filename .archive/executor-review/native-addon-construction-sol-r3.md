# Native addon construction R3 — Sol final closure review

Reviewed the frozen candidate in `/home/dev/.cache/crowley/worktrees/native-addon-construction-r3-20261018` against base `3f43d8f40aa17035409a87c4718e1f34a888ff65`, the R3 closure plan, the parent adjudication, and the prior Sol and actual Opus reports. I inspected the R2-to-R3 critical delta and the resulting reachable source paths. I did not run tests, operate the game, or modify the candidate.

The worktree contains exactly the seven modified fenced files and the one new fenced fixture. All eight SHA-256 values match `native-addon-construction-r3-freeze.json`; the closure plan hash is `e03a2d32558d4da8c85ace8dff1eb938131e9d29d7e4c3085a6bd5b416766854`, and the freeze pins the prior Sol/Opus report hashes correctly. I accept the reported parent 215-test result, four compiled frame/atlas smoke checks, Ruff/format/compile checks, and worker statics as provenance.

The R1/R2 blocking paths are materially corrected: native fencing now retains the strict public schema, the exact recover command is a reachable actor, post-Finalize recovery works, callbacks are attached, construction and first restore publication failures clean the surface, controls are explicitly enabled and templated, malformed scalar markers do not crash, and fallback timers bind nonce/load/attempt.

## Must-fix

1. **A failure in the required post-fence restore publication clears the only recoverable state and produces a boot that recovery-begin cannot admit.** In `addon/Crowley/Agent.lua:762-768`, restore load first publishes a new ordinary boot while the native fence is still armed, then irrevocably clears `nativeConstruction`, sets lifecycle `ordinary`, clears the fence, and calls the error-swallowing `safePublish()`. If native telemetry or serialization succeeds for the first call but fails for this second call, the last visible frame has a new random ordinary boot with an armed fence, while the marker is gone, the panel is hidden, and the in-memory fence is unarmed. Recovery-complete cannot accept that frame because it lacks the required unarmed projection, and a subsequent recovery-begin accepts only no surface, the expected prefixed boot, or the original `B0` armed case—not this new ordinary boot. A persistent failure therefore leaves the paused durable checkpoint without an admissible Restore route. Make the post-clear unarmed publication part of the restore transaction: retain the recovery token until it succeeds; on failure, re-arm the native fence, persist a valid failed/restore state, detach and hide the surface, clear frame bytes, expose Restore, and return a nonordinary lifecycle. Add a serializer/native-telemetry fixture that succeeds on the first restore publication and fails on the second, then assert no surface, a durable recoverable marker, armed fence, visible/enabled Restore, and no ordinary completion.

## Should-fix

1. **Finalize still reports success and deletes the attempt before it knows the required inactive-fence frame was published.** `addon/Crowley/Agent.lua:639-644` clears the marker and fence, refreshes the panel, calls `safePublish()`, and returns true regardless of publication failure. The daemon's later strict proof prevents false native acceptance and post-Finalize Restore remains reachable, so this is not the dead-end above, but the addon command does not itself satisfy the frozen statement that Finalize publishes the newer strict frame. Tentatively release the native fence, perform a checked publication, and only then clear the marker/enter `finalized`; on failure restore the constructed marker/fence and return `publication_error`. Cover a failure injected specifically at the Finalize publication.

2. **The claimed closed marker/entry-point matrix remains incomplete.** `tests/test_addon.py:367-460` covers useful malformed and valid representatives, but it does not cover every state/attempt pair, a valid 64-byte token, numeric/wrong-type state and token fields, short/long/non-hex recovery nonces, or the full pre-`ADDON_LOADED` manual/event/timer/rearm surface required by `.archive/PLAN-native-addon-r3-closure.md:42-49`. The unconstructed checks at `tests/test_addon.py:418-430` also omit direct `Publish`/`Snapshot` behavior. Add the remaining closed cases and assert the same preserved raw marker, no surface/frame, private scan refusal, and no state mutation; do not broaden the marker grammar beyond the parent-adjudicated opaque-token contract.

## Nits

None.

STATUS: NEEDS WORK
