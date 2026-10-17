# Proposal: bounded Crowley scan sessions and login windows

## Recommendation

Use explicitly released play windows with Arthur already in the game, and keep the game session resident only while the user has authorized that window. Do not log in every 15 minutes. The 15-minute value is the addon's minimum interval between sweep **starts**, not a wall-clock schedule; the next start is based on the preceding `lastSweepStart`. Opening the Auction House (AH) schedules a scan if it is due, so an otherwise ordinary AH visit can start collection automatically.

For the initial pilot, reserve about 60 minutes for three consecutive scheduled sweeps in one resident game session, with the AH open during each sweep. A clean sweep has taken 484 seconds, so starts approximately at the beginning and 15 and 30 minutes later would finish the third around 38 minutes after the first start if each run remains near that result. Treat this as a planning estimate: each sweep has a 600-second cap, and actual login, game interaction, SavedVariables flush and acknowledgement work takes additional time. Save each completed sweep and reopen the AH between starts; measure whether this fits the available gap. Keep the window open long enough to finish the active scan and the closeout sequence. Never force a scan just to meet a clock target.

After the pilot, use a small number of user-selected recurring windows that preserve adjacent sweeps for comparison. A session window should normally gather three to five scans, saving each completed scan for timely server updates and completing acknowledgement cleanup before another session. The addon holds at most six unacknowledged sweeps; at six it pauses rather than evicting evidence. Leave capacity for an interrupted or delayed flush. Between windows, log out normally or leave the AH closed; do not keep a worker signed into Arthur around the clock.

## What the live runs establish

The current plan has 428 active IDs from a 544-entry catalog, a 900-second start cadence and 20 initial distinct price levels. Sweep time is capped at 600 seconds. The client has now completed a full sweep in 484 seconds: all 428 active IDs were queried, with no incomplete or unqueried observations. It retained 2,889 rows across 271 item IDs and 125,395 units, including full and bounded commodities and full item observations. Real commodity, recipe, container and equipment prices are present in the accepted database. This is good evidence that an open, resident session can finish a targeted sweep in less than the 600-second cap.

The next scheduled sweep started 900 seconds after the prior start, saved 325 seconds later when the AH closed, and left 135 IDs unqueried. That shows why closing or reloading during a sweep defeats full coverage. It does not show that 15-minute polling is intrinsically unreliable. Native login and multi-day session reliability have not yet been measured over a long run, and the observed 484 seconds is scanner time rather than a guarantee for the entire GUI workflow.

If the AH remains open, [`Scanner.Schedule()`](../addon/Crowley/Scanner.lua) targets `lastSweepStart + 900`; when that time is already due, opening the AH can start the scan promptly. A scan completing in 484 seconds leaves about 416 seconds until the next scheduled start. That interval is the only natural gap for a flush/reload sequence before the next scan becomes due. Do not assume the closeout, user interaction and AH reopen will fit that gap until pilot timings show it. A reload closes the AH; the AH must be opened again to resume scheduled scans.

## Session and operator controls

The automation policy should have a persistent **closed-by-default play lock**. A user explicitly opens a bounded session window before Luna may interact with Arthur; user activity or inactivity never opens or releases that lock. Give one worker the lease for that window. The lease has an expiry that prevents starting new work after the window, but expiry does not silently authorize a new session or erase the user's lock. Do not run overlapping login workers or issue catch-up scans after a missed window.

Luna should wake at the user-released session start, upload/acknowledgement checkpoints, the final queue flush, or a blocker. An external watcher has no completion signal for an in-memory sweep before SavedVariables are written. A read-only watchdog may check files, companion/server state, and database rows after a flush, but it cannot establish that the AH is open or that an unflushed sweep has finished. Until a read-only addon completion/status hook exists, Luna must use bounded visual checks and `/crowley status` at explicit checkpoints: confirm the session and plan at start, inspect near the expected sweep end, and confirm completion or cap outcome before changing state. The current status command reports whether a scan is running and last-sweep counts, but has no external event stream. A proposed addon status hook should expose read-only in-progress/completed state and counts without changing query timing or results. Avoid frequent root polling, repeated screenshots, and repeated full process/window inventories. Inspect the target game state at session start and after an action that changes it; inspect again only at a planned checkpoint or when recovery is needed. At a quiet boundary, wait until the next relevant checkpoint.

Use the existing local-game-control procedures for any future authorized UI work: verify the actual client before input, avoid duplicate launcher starts, verify slash-command text before submitting, and confirm visible results. Check `/crowley status` and the house/plan before relying on the AH open event. Opening the AH may auto-start a due scan. Do not force a second scan if one is already running.

Stop the session on a credential prompt, account conflict, unexpected character or house, unrecognized window/state, active user interaction that would be disrupted, storage block, or rejected/failed upload. Do not handle or print credentials. Preserve any rejected payload and its trace, report attempted/incomplete/unqueried counts separately, and diagnose before another scan. Allow at most one bounded recovery for a clearly understood transient UI failure after re-establishing the intended client; otherwise end the window with the exact blocker. Never trade, post, bid, cancel, send public chat, or change services/configuration as part of a scan session.

## Flush, upload and acknowledgement closeout

For timely updates, verify a sweep has completed, then `/reload` so the client writes SavedVariables. Let the [companion](../src/crowley/companion/sync.py) observe a stable file and verify that the original UID was accepted with HTTP 200; it deduplicates accepted IDs and retries stable files after transport errors. Reopen the AH in time for the next scheduled start. This is one login per session with save/reopen cycles, not a new login every 15 minutes. Under the observed duration there are 416 seconds between finish and the next start; at the 600-second cap there are 300 seconds. If the GUI cycle exceeds that margin, record the delayed start rather than forcing overlapping work or claiming the cadence was maintained.

An acknowledgement does not have to load immediately after each successful upload. To reduce GUI work, the next normal post-sweep reload can consume the preceding upload's acknowledgement while writing the newly completed sweep. Check actual posted UIDs rather than assuming an acknowledgement is ready. This proposed sequence must be piloted; it is not yet an unattended timing guarantee. At the end of the session, wait for the final upload acknowledgement, load it with another normal reload, then perform a normal reload or logout to persist the pruned queue. Verify the saved queue is empty before closing the session lease. Scan acceptance, acknowledgement load, and persisted cleanup remain separate checkpoints. External file/HTTP observations become possible after the write; neither is an event emitted when an in-game sweep finishes.

An optional archival mode can leave the AH open for three to five scans and save the batch at the end. It reduces GUI interactions and preserves captured query timestamps, but server freshness can lag by tens of minutes. It does not meet a goal of timely updates every 15 minutes and is unsuitable for immediate flipping alerts. Keep that tradeoff explicit rather than silently substituting batch uploads for the requested cadence.

After any reload, the AH is closed. Reopen it only if the explicitly released session still has time and the user wants collection to continue. Since the cadence is anchored to the last start, a scan may be due immediately; check status before waiting or asking for another manual scan. Do not let a scheduled start surprise an actively playing user.

## Schedule design and data collection

Do not choose a purportedly optimal auction time from the current evidence. The sample demonstrates scanning mechanics and yields only a few accepted scans on one beta house. It cannot establish weekday, hour-of-day, or market-liquidity patterns.

Use a pilot first: obtain at least three consecutive full sweeps with successful upload, loaded acknowledgements, and a verified flushed queue. Record per sweep the planned, attempted, successful full/bounded, incomplete, unqueried, priced and row-bearing counts; query start/end times; captured quantities; total sweep duration; upload latency; time spent on login/verification/reload; and any AH interruption. This validates the session procedure and estimates its actual wall-clock cost.

Then collect a seven-day coverage sample using a few recurring windows chosen by the user. Keep each window's scans contiguous and aim for starts 900 seconds apart, preserving comparable neighboring observations. To compare candidate times, repeat windows at the same America/Chicago local times on multiple days and include both weekdays and weekend days; the slots should be user-selected rather than guessed here. Compare the same house, active plan and client build. Hold cadence and per-sweep behavior constant so the observed difference comes from sampling time, not a changed scan method.

[`volume.py`](../src/crowley/core/volume.py) pairs consecutive item observations only when their query windows are valid and non-overlapping, and `current query end - previous query start` is at most 1,800 seconds. Comparisons also require compatible house, client build, plan, item kind/variant and price coverage. An incomplete/unqueried observation, long break, changed plan/build or incompatible bounded scope excludes that interval. Contiguous 900-second starts are therefore the useful default for price/volume evidence; widely separated daily logins remain useful for snapshots but cannot supply eligible movement pairs across those gaps. Commodity depletion/replenishment is an uncalibrated churn proxy, not confirmed sales. Gear disappearance is not a sale unless the stricter own-sale evidence supports it.

Read-only production volume checks support this distinction: commodity item 7078 had an eligible 900-second comparison but measured zero depletion and replenishment, with actual sales left null. Recipe variant `6211:l30` had an eligible 899-second pair, but `grouped_scope` made individual sale candidates unavailable. Item 2447 was unqueried after AH closure and had no eligible comparison; it is not a zero-supply observation. The checks show that contiguous pairs can be produced by the session design, not that the current evidence predicts sales accurately or identifies a profitable time.

Evaluate candidate windows on capture completion, comparable price coverage and scan freshness first. Evaluate market movement only after enough repeated, valid observation pairs exist. Keep price-history and churn comparisons within the same verified house; do not combine beta data with launch-region prices. After the seven-day sample, choose the smallest set of windows that achieves useful coverage within the user's stated play-time budget. This proposal creates no schedule or timer and does not assume a particular scheduler is installed.

## Alternatives and tradeoffs

| Pattern | Benefit | Cost and evidence fit |
|---|---|---|
| Fresh login every 15 minutes | Attempts to follow every cadence slot | Highest GUI and login overhead; the cadence is not wall-clock based; reloads close the AH and break contiguous windows. Not recommended. |
| One resident session, saving and reopening the AH between completed sweeps | Avoids repeated logins and can provide adjacent volume pairs plus timely server updates | The save/reopen step must fit between sweep starts; unattended operation is unproven and user play takes priority. Continuous AH-open batching instead delays server freshness. |
| Several bounded user-released windows | Limits login/worker time while retaining adjacent scan pairs within each window and clear pause points | Creates gaps between windows, so cross-gap volume intervals may be excluded; snapshot comparisons still work. Recommended starting policy. |
| Very short visits for isolated snapshots | Low session time and straightforward upload | Does not establish cadence/volume pairs and is weaker for diagnosing item coverage or price change. Use only for a specific snapshot need. |

## Acceptance and boundaries

The pilot succeeds when three consecutive sweeps complete with all 428 active IDs queried, native commodity/item prices retained, each original payload accepted under `beta-normal-alliance`, acknowledgements loaded, and the saved queue verified empty after its flush. Keep a sweep that misses any of these criteria as partial evidence; do not silently repeat it or report unqueried/incomplete items as empty.

The next phase succeeds when seven days of user-approved windows produce enough adjacent, compatible observations to report actual coverage, valid interval counts, elapsed wall-clock cost and gaps. It may then support a recommendation about a practical collection window. It still cannot establish the economically optimal trading time without a longer representative price history and a defined strategy outcome.

This file is a proposal only. It does not authorize logging into the active user's game, changing a schedule, waking a worker, modifying the addon/companion/server, or creating an external timer. Obtain an explicit user-released play window before any future game input, and preserve the established no-automation rule for protected trading actions.

The user's available play windows are not yet known; until provided, use a fresh explicit handover for every session and create no recurring schedule. The official [scheduled tasks documentation](https://learn.chatgpt.com/docs/automations?surface=app) describes local project tasks that require the computer and app to be running and an explicit model selection. Whether that local scheduler and the needed runner are available in this installation is unverified and is a setup preflight. A cloud task cannot directly access this local workspace. This plan does not claim that any scheduled task or Luna runner has been installed.

## First pilot authorization

On 2026-10-15 the user explicitly handed control back after playing. One pilot window is
authorized from 06:54:52 to 07:54:52 UTC (01:54:52–02:54:52 America/Chicago). The sole Luna
game operator owns three new scan/upload cycles and final acknowledgement, persisted queue
cleanup and normal logout. The existing user pause is lifted for this window only; a new
user takeover stops input immediately. No recurring schedule or unattended-login service is
enabled. Actual results belong in [scan-session-pilot.md](live-client/scan-session-pilot.md).

The initial screen has a pre-existing logged-in-elsewhere dialog with exactly one local
game client. The user's explicit handover authorizes one ordinary reconnect through the
existing authenticated launcher/client, without credential entry, to establish Arthur's
session. This is a bounded exception to the general conflict-stop rule above, not a retry
loop. If the conflict recurs after that attempt, a credential prompt appears, or another
active session cannot be distinguished, stop and report the actual state. Keep the same
pilot deadline and report fewer than three cycles honestly if setup consumes the window.

The collection cutoff prevents new scans and AH reopening. It must not strand existing
uploads during closeout: the user's handover still permits completing the already-required
acknowledgement load, normal queue flush and logout after the cutoff, provided the user has
not taken control back. This is cleanup of the same pilot, not another scan window. No new
login, scan, recurring timer or unrelated recovery is authorized during closeout.

## First pilot measurements

Two complete new sweeps were independently verified in the deployed database. Both queried
all 428 IDs with zero incomplete or unqueried observations in `beta-normal-alliance`.

| Sweep UID suffix | Start UTC | Finish UTC | Scan time | Rows | Accepted HTTP 200 UTC |
|---|---|---|---|---|---|
| `1792048509-Arthur-7339` | 07:15:09 | 07:23:17 | 488s | 2,725 | 07:28:29 |
| `1792049765-Arthur-6163` | 07:36:05 | 07:44:05 | 480s | 2,688 | 07:47:42 |

The actual start interval was 1,256 seconds (20m56s), missing the 900-second target by
356 seconds. Finish-to-accepted-upload latency was 312 and 217 seconds. These wall-clock
figures include operator work and are not companion transport latency measurements. The
production volume API produced a valid 1,255-second commodity comparison for item 7078;
actual sales remain unknown. The initial account recovery and setup consumed about 20 minutes.

The pilot did not meet its three-cycle/15-minute-cadence acceptance criterion. Native
collection remains successful; the login/save/reopen procedure needs improvement before
recurring wakeups are enabled. The next implementation should make command preparation and
completion detection observable, reduce repeated GUI checks, and budget save/reopen work
against the actual next start. Validate the revised procedure with three complete adjacent
cycles and measured per-item comparison intervals; do not change cadence to conceal delays.
No recurring wakeup has been configured. Final closeout state is recorded in the linked
pilot evidence after normal acknowledgement/flush/logout completion.

Closeout completed: normal acknowledgement reload followed by logout left Arthur at
character select and zero pending scans on disk, both independently verified by the parent.
Journal evidence also corrects an operator timing assumption: the first acknowledgement
was written at 07:28:29 immediately after HTTP200, not when the operator observed a later
07:33:29 refresh. Future runs should check the exact acknowledged UID promptly, avoid
waiting for the periodic refresh, and consume an earlier acknowledgement on the next
post-sweep reload where possible. No further game input or recurring task is active.
