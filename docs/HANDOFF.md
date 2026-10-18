# Forever Tradecraft handoff

Updated 2026-10-18, 23:38 UTC. Repository: `/home/dev/repos/pegasus`.
Origin: https://github.com/kyle-deprow/forever_tradecraft . Existing Crowley
package, addon and configuration names remain intentional.

Read this for current status. The complete preceding handoff is preserved in
[the historical archive](../.archive/executor-review/handoff-history-before-consolidation-20261018T2330Z.md).
Its dated status entries, test counts, deadlines and old approval rules are history.
User instructions take precedence; the user revoked `AGENTS.md` instructions.

## Objective and requirements

Build a private WoW Forever market research and trading platform. Collect useful
price history and estimated market activity so launch can begin with data and
strategies already prepared. Prioritize profitable profession combinations,
short-term supply/demand shocks and longer-term crafted/material investments.
Keep different region/ruleset/faction houses separate. Do not scan every AH item.

The first-run catalog has **428 active items**, including multiple professions,
trade goods, recipes, containers and selected equipment. Management and rationale:
[WATCHLIST.md](WATCHLIST.md). Capture the cheapest **20 distinct unit-price levels**
and every row at the retained boundary, with explicit full/bounded/incomplete
coverage. Missing or timed-out observations are unknown, never zero supply.

Target a **15-minute** repeating collection cadence. SavedVariables only persist
on reload/logout/exit; the companion uploads stable files, writes addon data and
ACKs, and the game loads those files on reload. Completion requires this entire
save/upload/ACK/reopen loop to run autonomously, not just an addon scan timer.

Listing disappearance is an **uncalibrated activity proxy**, not confirmed sales.
Keep actual own-sale evidence separate. Strategy generation, verified Forever
recipe economics, useful shopping lists and launch monitoring remain later work.

## Live status and immediate blocker

- WoW runs locally through Wine. Sunshine/Moonlight is disabled. Arthur is
  stationary at the Ironforge AH; no trading or movement is authorized here.
- Canonical runtime daemon remains **PAUSED, generation23, unqualified**. Neither
  current native/helper candidate has been promoted or installed into that service.
- Collection has been **operator-assisted** by the sole GUI Luna worker. Many
  consecutive starts were exactly900s apart; that is not autonomous qualification.
- Latest independently verified sweep is **62**:
  `beta-normal-alliance-1792364753-Arthur-8911`, started23:05:53UTC,
  428 observations /2640 rows /404 full /23 bounded /one incomplete.
  Item12692 timed out. Receipt arrived20.782144s after finish. Parent verified
  SavedVariables hash, logical DB digest and exact loaded ACK using production
  PixelDecoder on the retained PNG.
- Fresh read-only DB totals: **70 sweeps,29960 observations,167498 captured rows**;
  latest receipt2026-10-18T23:14:45.782144UTC. Historical sweeps are included.
- Reopening the AH is now blocked by GNOME's **login-keyring authentication
  modal**. It dims the whole display and invalidates the strict binary HUD.
  `/targetexact Auctioneer Buckler` is typed behind it; Return was not sent.
  The failed receipt records open_chat and typing, so do not claim zero input.
- One guarded Cancel click through the game/Xwayland input path had no effect on
  the compositor-owned dialog. Available accessibility/D-Bus paths cannot cancel
  it; no requester can be attributed to our own process. No credentials, keyring
  service changes or repeated clicks. User was asked asynchronously to click
  **Cancel**; no reply yet. Scan63's23:20:53 due time has therefore been missed.
  After dismissal require fresh exact identity/HUD/chat-buffer proof before Return.

Only `/root/luna_live_continuation` operates the actual game/desktop. Root may
inspect retained screenshots and run isolated Xvfb tests. Preserve that ownership.

## Active implementation and reviews

Requested workflow: Luna implements/operates, Sol reviews, actual Claude CLI Opus
reviews executor changes. Workers have bounded tasks and may continue without
per-action approvals. Root owns arbitration, final verification and git.

**Native R8:** original frozen worktree
`/home/dev/.cache/crowley/worktrees/native-final-commit-r8-20261018`, base7ac5c85.
Read [the authoritative R8 plan](../.archive/PLAN-native-final-commit-r8.md),
including final Opus arbitration. Seven-file fence: session/controller.py,
daemon.py, cli.py; native/native_regressions/transitions tests; ONLY the named
runtime-meter test-double correction in test_session_runtime.py. Do not expand it.

R7 independently passed330 tests but was rejected by Sol and actual Opus. R8 fixes
finalize/cancel/expiry ownership serialization, admission before PAUSED capture,
a three-lock liveness cycle, unsafe guessed observation/admission fallbacks, and
real predecessor/journal-write coverage. Root additionally identified deadlines
expiring while waiting for the final lock: every applicable deadline must be
rechecked inside the final transaction, plus before/after capture and sleep.
Worker334 native passes443.09s plus named runtime pass are independently hash-bound.
Parent scoped checks and10 targeted tests passed58.53s, including both actual PNG
runner cancel/finalize interleavings and compiled configured capture. Three assigned
proofs were missing despite the initial closure claim. Worker
`/root/luna_profiler_schema_fix` now owns ONLY native_regressions tests in separate
`native-final-commit-r8-proof-20261018` (basea74297c, all7 exactR8files copied).
Read [the proof-closure plan](../.archive/PLAN-native-r8-proof-closure.md): actual
three-way lock barrier, deadline expiry while waiting for final lock, and malformed
resume facts before publication. Other6 files are read-only. No duplicate broad
rerun if production bytes remain identical. No source acceptance/native100/live gate.

**Helper final closure:** worker `/root/luna_runtime_instrumentation`, worktree
`/home/dev/.cache/crowley/worktrees/native-operator-final-closure-20261018`,
basea74297c. Owns ONLY tools/native_calibration_operator.py and its test file.
Read [the closure plan](../.archive/PLAN-native-operator-final-closure.md) and
[Sol's findings](../.archive/executor-review/native-operator-production-proofs-sol-review.md).
Six copied R7 native files are read-only development inputs, not accepted code.
Actual helper Opus completed exit0/claude-opus-5-5, STATUS: MAJOR ISSUES.
Final root arbitration is appended to the closure plan; no review hold remains.
It supersedes the original Sol prescription: providerDeadline belongs ONLY to
initial construction, not later hold/measure/resume phases. Additional accepted
fixes include actual INPUT_CALIBRATION success, error detection at any wait,
genuine Guardian-generation increase on new PAUSED handoff, private pipe reply
correlation, no unpressed release input, and complete GO-time action budgets.

The preceding helper candidate passed58 parent tests, but full measurement
success/production-screen composition was unproved. Accepted fixes address the
post-old-expiry cancellation horizon, real measurement-error recovery, named
phase deadlines reaching physical dispatch, strict PAUSED proof, active receipt
failure and staged allocation cleanup. Require actual SessionDaemon + AF_UNIX
SessionIPC + production X11Screen readiness + actual FixedInput/OwnedEmitter,
with external scene changes only after owned dispatch ACK. Successful reservations
and all12 history states must come from the daemon; fake successful replies,
direct-client tests accepting errors and a separate compiled test do not prove it.

Actual pinned-tool tests on fresh isolated Xvfb independently proved exact23-key
command typing in3.272824s within3.99s and key release/reap0.562473s after actual
helper SIGKILL while a key was held. These do not establish the full workflow.

No root exec currently running. Helper Opus22003 is CLOSED0/MAJOR ISSUES; native
R7 Opus2839 CLOSED0/NEEDS WORK. Parent native checks3947 and representative-template
benchmark42539 CLOSED0, as are helper tests42012, typing76434, death6947,
backup30667 and push50795. No model fallback. New actual CLI review sessions must
stay attached and be polled at most30s; raw JSONL0600 stays private.
Main last pushed **a74297c** before this consolidation.

Representative offline matcher benchmark on frozen helper715:1920x1080 capture,
220x84 region, synthetic100x28 templates, exclusive2.606132s/dual5.058175s.
This measures real matching loops but not live templates, physical UI transform,
capture or IPC costs. Known UIParent1365.33x768 versus physical1920x1080 raises an
unproved panel-scale assumption; measure actual controls before claiming readiness.
No matcher rewrite is authorized by this benchmark or the unrelated runtime Rust gate.

## Remaining acceptance gates

1. Finish both bounded fixes, focused proof and final scoped suites; parent
   independently checks final bytes/fences, runs meaningful tests, and obtains
   Sol plus actual Opus acceptance. Avoid repeating broad suites without a change.
2. Verify the final helper against the exact accepted seven native R8 files;
   development R7 passes cannot substitute. Confirm the deliberate post-success
   prepared-checkpoint and ordinary recovery contract before live use.
3. Coordinate a quiet GUI window before promotion or PAUSED service restart;
   never mix changed source with a daemon still holding old imports.
4. Run inactive control preflight and a fresh native100. Then request the genuine
   human GTK keyboard/click gate with concrete instructions when it is ready.
5. Prove **three autonomous15-minute save/upload/ACK/reopen cycles**. Preserve
   start times, receipts, fresh ordinary HUD, DB digests and exact loaded ACKs.
6. Only then call the repeating system complete and return to volume/strategy
   validation and launch readiness. No measured compute bottleneck currently
   justifies the proposed Rust rewrite.

## Data preservation and operating references

Hourly snapshot `beta-20261018T231325Z-166c0ce4fbc3` independently validates;
manifest SHA256 `8cb835d02d5c50b1973d2cbb2de42d59c69de0661b6a5c53b85837e7413cf1b5`.
It contains scan61, before62 ingestion. Next hourly due00:13UTC. Use
`uv run python tools/market_backup.py snapshot` and independently validate it.
Keep backups and raw game/private evidence out of git. An earlier isolated
restore drill already passed; no need to repeat without a reason.

- [ARCHITECTURE.md](ARCHITECTURE.md): data path and contracts.
- [REPEATING_SCANS.md](REPEATING_SCANS.md): repeating session operation.
- [RUNTIME_PERFORMANCE.md](RUNTIME_PERFORMANCE.md): measurement/optimization gates.
- [MARKET_RECOVERY.md](MARKET_RECOVERY.md): backup/restore operation.
- `.agents/skills/local-game-control` and `crowley-client-contracts`: compact
  source-controlled lessons. Existing lessons include actual typing timing,
  immutable phase evidence, exact target-frame+tooltip identity, and real composed
  tests. Do not create a skill per mistake.
- Private live evidence: `~/.local/state/crowley/executor-evidence/runtime-relink`.
  Helpers, raw reviews, screenshots and logs there are private artifacts.
- The user has authorized ongoing fixes, installation, recovery, commits and
  pushes. Do not ask again because historical handoff prose says otherwise.
- **Never git add .** Explicit curated paths only; many untracked private files
  exist. Preserve failed evidence, do not reset/stash/revert another worker.
- Continue through independent work while a user action is pending. Do not end
  coordination with a status-only final. Stop dependent live input at real gates.
