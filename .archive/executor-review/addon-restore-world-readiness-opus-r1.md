Model ID: **claude-opus-5-5**

I reviewed `git diff c8498ce` for `addon/Crowley/Agent.lua`, `tests/test_addon.py` and `tests/wow_harness.py`. I also read the plan in full including the Sol arbitration, the live-evidence record and the crowley-client-contracts skill. I made no edits and ran no tests or game actions. The one exception: a short Python arithmetic check, plus a temporary block comparison in `/tmp` that I deleted afterwards.

## Source verdict
The `Agent.lua` change is correct against the accepted plan:
- **Commit block unchanged:** `restoreCommit` (`Agent.lua:775-836`) is byte-identical to the base block apart from the owner bump at line 776. Allocation and first/second publication failures keep their phase-specific diagnostics, and the scanner is still rearmed only after a real commit.
- **Startup pending:** `ADDON_LOADED` builds no surface and does not probe. Startup sets `restoreInFlight=true`, so Restore is disabled, the fence stays armed and the marker stays `restore_pending`.
- **Readiness probe:** it is exactly `pcall(movementTelemetry)`, with no serialization or publish. Unknown CTM/ground results are still accepted.
- **Deadline:** `GetTime() >= deadline` is checked before every probe (line 852).
- **Timers:** at most one timeout and one 10 Hz poll exist at a time. Committing, failing or reloading invalidates the owner, so queued callbacks return without changing state or rescheduling.
- **Duplicate world events:** extra `PLAYER_ENTERING_WORLD` events can't commit twice, because the handler requires `lifecycle == "restore_pending"`.
- **Terminal failure:** `failRestoreReadiness` leaves the boot failed, surfaceless and fenced, sets the marker to failed/1, re-enables Restore and stores the exact reason.
- **Facing diagnostic:** limited to facing and capped at 32 characters.
- **Harness:** only Agent listens for `PLAYER_ENTERING_WORLD`, so the `login()` change affects nothing else.

## Must-Fix
None.

## Should-Fix
These are regressions the accepted plan explicitly requires that the current tests don't actually exercise.

1. **`tests/test_addon.py:668`: the old-failure reproduction never reaches the `ADDON_LOADED` boundary.**
   - **Issue:** `login()` now fires `PLAYER_ENTERING_WORLD` too. The first assertions therefore run after a failed probe with a poll queued, and the commit comes from a second world event. The live sequence — facing missing at `ADDON_LOADED`, valid at a single world entry — is never tested. The plan's "drain stale poll after early success" case is also missing: this test leaves its poll undrained.
   - **Fix:** add a test that fires `ADDON_LOADED` directly with `facing=None` and asserts:
     - pending, no surface, fence armed, marker `restore_pending`
     - Restore disabled, exactly one queued timer (the timeout only)
     - then set a valid facing, fire one `PLAYER_ENTERING_WORLD` and assert the commit
     - then `advance_with_timers(30)` and assert nothing changed and no timers remain.

     Keep the current flow as the duplicate-world-event test, and add `advance_with_timers(30)` asserting the same `agent_frame`, the same `texture_count`, `ordinary`, a nil marker and zero timers.
2. **`tests/test_addon.py:690`: no test checks that a scanner query can't start during the retry wait.**
   - **Issue:** the behaviour is safe today: `nativeBlocked()` sees `restore_pending` and the fence is armed. But the plan and the skill's rule on fence release rearming a scheduler both require a test with the triggering event present.
   - **Fix:** in the transient-retry test:
     - while pending, call `set_canonical_plan()` and fire `AUCTION_HOUSE_SHOW`
     - assert a `native_construction_fence` refusal in `schedule_trace` and `state.queryCalls == 0`
     - after the poll commits, assert the last event is a `native_construction_release` `timer_create`.

## Nits
- **`Agent.lua:920`:** the `GetTime() < restoreReadinessDeadline` check in the timeout callback does nothing useful, because the owner guard already rejects stale callbacks.
  - **Risk:** if C_Timer ever fires before `GetTime()` reaches the deadline, the callback returns silently. With no world event and no poll queued, the restore then stays pending with no bound. My arithmetic check found about 0.3% of millisecond start times round adversely; it also needs an exact-millisecond fire and a missing world event, so it's unlikely.
  - **Fix:** delete the line.
- **`tests/test_addon.py:716`:** prove the recovery route end to end. Run `slash("agent recover")` and `click_native("restore")`, then log in on a fresh client and assert `ordinary`.
- **`tests/test_addon.py:797`:** add a comment that replacing the token during the wait can't happen in the real client, because Restore and BeginRecovery both refuse while pending. The test only proves the guard is inert.
- **Outside the worker's file scope:** the parent should record in the HANDOFF §6 table the client assumption that movement telemetry is valid at or after `PLAYER_ENTERING_WORLD` on reload.

This is offline evidence only; the live recovery is still pending. The review is also saved at `/home/dev/.claude/plans/you-are-a-read-only-zany-candle.md`.

STATUS: NEEDS WORK
