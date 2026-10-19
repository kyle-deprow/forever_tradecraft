Model ID: **claude-opus-5-5**

The delta is ready: every finding from the previous review is resolved and I found no regressions. I compared the current files against the previously reviewed bytes, whose hashes match your references (`d8f181d5`, `e2f2de9f`, `d58ea219`). `tests/wow_harness.py` hasn't changed at all. I made no edits and ran no tests.

## Production change (`Agent.lua`)
- **Only change:** the `if GetTime() < restoreReadinessDeadline then return end` line is removed from the timeout callback, so the owner can no longer be silently stranded. This resolves the prior nit.
- **Timeout callback now:** if the owner is still active, it always reaches `failRestoreReadiness`, which invalidates the owner. Any poll still queued then returns without effect.
- **Poll path:** it still checks the deadline before each probe (`Agent.lua:852`), so `restoreReadinessDeadline` is still in use.
- **Unchanged:** the readiness probe is still `pcall(movementTelemetry)`. The transaction, fence and 30-second bound are as before.

## Prior findings
| Prior finding | Status |
|---|---|
| **Should #1:** test from the `ADDON_LOADED` boundary | **Resolved** (`test_addon.py:666`). Fires `ADDON_LOADED` directly with `facing=None`. Asserts: pending, no surface or frame, marker `restore_pending`, fence armed, Restore shown but disabled, exactly one timer (no probe or poll). Then sets a valid facing and fires a single `PLAYER_ENTERING_WORLD`, which commits. After `advance_with_timers(30)`: same frame and texture count, marker nil, zero timers. |
| **Should #1:** duplicate world events and stale-poll drain | **Resolved** (`test_addon.py:696`). After a second world event and `advance_with_timers(30)`: same frame and texture count, `ordinary`, marker nil, zero timers. |
| **Should #2:** no query during the retry wait | **Resolved** (`test_addon.py:739-772`). Fires `AUCTION_HOUSE_SHOW` while pending and asserts a `native_construction_fence` refusal from `ah_show` and `queryCalls == 0`. After the poll commits, the last trace event is a `native_construction_release` `timer_create`, and the release timer drains to zero after the auction house closes. |
| **Nit:** early `GetTime` return in the timeout | **Resolved** (the production change above). |
| **Nit:** recovery route after the missing-world timeout | **Resolved** (`test_addon.py:795-800`). Runs `agent recover` and the Restore click, logs in on a fresh client and asserts `ordinary` with marker nil. |
| **Nit:** comment on the artificial token replacement | **Resolved** (`test_addon.py:868`). |

On Should #2: the test sets `lastSweepStart` so the cooldown is still active. That means `queryCalls == 0` on its own wouldn't prove anything. The fence-reason refusal assertion is what actually proves the fence is checked, and it would fail if the fence weren't armed. The cooldown also keeps the release timer around long enough to observe. This is sound.

## Must-Fix
None.

## Should-Fix
None.

## Nits
- **`tests/test_addon.py:798-800`:** the recovered client's final assertions (`ordinary`, marker nil) prove the route works, but not that the fresh client went through `restore_pending` and then committed.
  - **Fix:** also assert `recovered.lua.globals().CrowleyDB.agentRestoreFailure is None`. `Agent.lua:910` clears it only on a `restore_pending` load, and ordinary loads keep it (per commit c8498ce), so this pins the path taken.
  - **Optionally:** assert `client.reload_calls == 1` before handing the saved variables to the fresh client.
- **Outside these three files:** the earlier note still stands for you as parent. Record the assumption that movement telemetry is valid at or after `PLAYER_ENTERING_WORLD` on reload in the HANDOFF §6 table. It isn't part of this delta.

This is still offline evidence only; the live recovery remains pending. The review is also saved at `/home/dev/.claude/plans/read-only-delta-follow-up-review-moonlit-gizmo.md`.

STATUS: READY
