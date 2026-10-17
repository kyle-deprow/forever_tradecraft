# 70450 scan plateau diagnosis

## Live conclusion

The observed `148/428` plateau is **not a confirmed permanent scan stall**. The same run later printed `sweep saved: 428 observations, 0 failed` at 05:52:34. A scan that had actually taken either the 30-second item-timeout path or the 600-second sweep-timeout path could not truthfully produce that zero-failure result. Fresh CRS1 frames with the same boot and sequence advancing from 824 to 827 rule out whole-frame compositor staleness for those frames, but they do not by themselves establish that the displayed `148/428` came from the freshly decoded `scanner.ordinal` field. Preserve the frame receipts and uploaded payload before assigning a cause.

The run's successful completion does expose one separate, reachable source defect worth fixing preventively: an exception during item setup can leave a live item with no item timer. There is no evidence yet that this defect fired in this run.

## Reachable source fault

`beginItem` calls `C_AuctionHouse.MakeItemKey`, `GetItemKeyInfo`, `C_Item.RequestLoadItemDataByID`, and, for warm metadata, the entire `startSearch`/native-send path before it schedules the 30-second timer (`addon/Crowley/Scanner.lua:816-838`). `startSearch` and `sendMessage` also call readiness and query APIs without protection (`Scanner.lua:412-426,698-730`). Any synchronous Lua/native error in that interval aborts the callback after `state.item` may have been installed but before `s.timer` exists. `Scanner.InProgress()` then remains true and the ordinal can remain fixed until the independent sweep callback.

The 600-second callback is registered before the first item starts (`Scanner.lua:893-915`), so the setup defect alone is not an unlimited stall. Its callback is also unprotected, however: an error in `failCurrent`, `markTail`, or `Scanner.Finish` can abort finalization (`Scanner.lua:905-913`). `Scanner.Finish` clears private state before serialization (`Scanner.lua:951-961`), so a serialization error would cause a missing saved sweep rather than a continuing `item` phase.

Result-event callbacks run without an error boundary because the central dispatcher directly invokes handlers (`addon/Crowley/Core.lua:104-108`), and result collection contains many native calls (`Scanner.lua:602-652,654-684`). An asynchronous result-handler exception alone should not cause the reported permanent item stall: the timer has already been armed by then and should recover in 30 seconds. It remains a diagnostic and latency defect because the original error is lost and recovery is delayed; a second exception in the timer callback could prevent recovery.

`internalSendDepth` is incremented immediately before native search/page calls and restored only on the successful return (`Scanner.lua:646-650,722-728`). A thrown native call leaves it elevated, suppressing later foreign-search attribution. This is a concrete secondary cleanup defect.

The current query trace cannot diagnose ordinal 148. It retains the first 256 events and drops every later event (`Scanner.lua:44-67`); normal scans consume several events per item. `/crowley status` prints the active ordinal but its `cursor:` value is the last persisted sweep cursor, not the active item's cursor (`addon/Crowley/Commands.lua:24-34`). The Agent frame's `scanner.cursorItemID` is the current source (`addon/Crowley/Agent.lua:278-296`; `Scanner.lua:984-1038`). Because the plan rotates after the persisted cursor (`Scanner.lua:883-899`), canonical plan index 148 must not be assumed to be this run's ordinal-148 item.

## Evidence that resolves the live observation

Preserve these without starting another scan:

1. The two fresh decoded CRS1 receipts, including `boot`, `sequence`, `wallTime`, `uptimeMs`, and the complete scanner tuple (`phase`, `startedAt`, `ordinal`, `planned`, `cursorItemID`). If wall time and uptime advanced by more than 30 seconds while that exact tuple stayed fixed, that is timer/presentation evidence; advancing sequence alone is insufficient.
2. The submitted `/crowley status` output after completion and a fresh Agent frame showing `phase=ready`, changed `lastSaved`, and pending UID. The command's `agent: ... ordinal ...` line is authoritative for live ordinal; its separate `cursor:` field is historical.
3. After the ordinary `/reload` persistence step, the exact raw sweep plus strict decoder result. Its `startedAt`, `finishedAt`, `attempted`, failure count, every observation's `ordinal`, and reason histogram determine whether any item/sweep timeout occurred and recover the identity assigned ordinal 148. Do not infer a market result from the chat counter.
4. Any Lua error dialog/stack or client error log already produced by the run. The addon currently exposes no runtime error through `Scanner.Status`, Agent telemetry, or `/crowley probe`; `activeQueryTrace`/`lastQueryTrace` in SavedVariables is the only existing addon trace and its prefix cap likely excludes ordinal 148. Absence of a trace entry is therefore not evidence that no native error occurred.

The completed zero-failure sweep currently favors an apparent-progress/presentation ambiguity or a transient scheduling pause over the pre-timer exception defect. If the strict payload confirms all 428 observations are successful and its total duration is below 600 seconds, this incident should be recorded as an unconfirmed plateau, not a scanner failure.

## Minimal robust source-fix plan

Do not patch around this run before its payload is preserved. The bounded preventive fix should cover the real exception window without treating an error as an empty market:

1. In `Scanner.lua`, construct and install the item owner first, then arm its identity-checked 30-second timer before any item, metadata, readiness, or query call. Keep stale timers harmless through the existing `state.item == s` check; completion must advance an ordinal exactly once.
2. Route synchronous setup/send stages and asynchronous metadata/result callbacks through one item-owner error boundary. On an actual exception, preserve the stage and original error text/stack in a bounded diagnostic, report it through the normal Lua error surface/chat, disconnect owned handlers, write exactly one **incomplete** observation, and advance. Never synthesize zero rows with `full` coverage or `reasonCode=ok`.
3. Add a strict `native_error` reason (producer and `src/crowley/core/scanformat.py`) rather than mislabeling an exception as `query_timeout` or `metadata_unavailable`. Keep dynamic error text out of the strict market observation; retain it in the bounded scanner diagnostic/trace. Make late errors observable rather than relying on the existing first-256-event prefix.
4. Restore `internalSendDepth` on both success and failure around every native send. Guard recovery itself so a reporting/error-handler failure cannot prevent item cleanup, while still surfacing the original error. Protect the sweep-timeout finalizer with the same fail-closed principle so it always produces incomplete current/tail observations or an explicit durable finalization error.
5. Extend the real Lua harness with injected throws at `MakeItemKey`, `GetItemKeyInfo`, `RequestLoadItemDataByID`, readiness, and the initial native send before the old timer position; assert one incomplete `native_error`, later ordinals processed, strict payload admission, and no duplicate advance when the stale timer fires. Add an asynchronous result-callback throw (for example result count/info or source-complete) with the same assertions. Also assert the exact diagnostic stage/error, `internalSendDepth` restoration through subsequent foreign-query attribution, and that neither path becomes an empty successful market.

The existing timeout test delays metadata but does not inject a synchronous native exception (`tests/test_addon.py:1325-1348`), and the harness invokes timer callbacks directly without a protective runtime boundary (`tests/wow_harness.py:240-264`). Those tests do not cover this defect.

## Assessment

- Live 70450 run: completed; no confirmed scanner stall pending payload verification.
- Source: reachable timer-registration and exception-containment defect, independent of this incident.
- Priority: preserve and ingest the new beta sweep first, then implement the bounded preventive fix before relying on unattended collection.
