# Forever Tradecraft handoff

Updated 2026-10-19, 00:16 UTC. Repository: `/home/dev/repos/pegasus`.
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

- WoW runs locally through Wine; Sunshine/Moonlight is disabled. Arthur was left
  stationary at the Ironforge AH. No trading or movement is authorized here.
- Canonical daemon is **PAUSED/gen23/unqualified**, neither candidate promoted.
  Collection has been **operator-assisted**; repeated900s starts do not qualify
  autonomous save/upload/ACK/reopen.
- Latest independently verified sweep **62**:
  `beta-normal-alliance-1792364753-Arthur-8911`, start23:05:53UTC,
  428 observations/2640rows/404full/23bounded/one incomplete(item12692 timeout).
  Parent checked source hash, logical DB digest and production-decoded exact ACK.
  Server receipt20.782144s after finish.
- Read-only totals:70 sweeps/29960 observations/167498rows, latest receipt
  2026-10-18T23:14:45.782144UTC. Historical sweeps included.
- GNOME login-keyring modal blocked AH reopen and dimmed the binary HUD. A typed
  targetexact command was NOT submitted; receipt records open_chat and typing, so
  do not repeat the worker's inaccurate no-input claim. One Xwayland Cancel click
  had no effect. AFK logout later cleared that buffer. Scan63's23:20:53 due time
  was missed; record its actual delayed start when collection resumes.
- At00:13 one owned installed `ydotool key ESC` invoked the verified GNOME Cancel
  binding. Child exited/reaped0; root viewed retained after.png and confirms modal
  gone/Arthur selected at character select. No password/settings/service changes.
  Native pointer-click attempt refused BEFORE dispatch when Cancel became blank.
  Uinput is system-wide and not isolated by Xvfb DISPLAY. User dismissal is no
  longer needed; the earlier asynchronous question is obsolete.
- At00:14:52 sole GUI Luna matched the actual EnterWorld control(MAE0), clicked
  [960,1002] with150ms release and verified loading screen. Await settled world
  HUD/plan/queue, exact target-frame+tooltip and AH reopen. Do not reuse old chat
  or infer world readiness from the loading screen. No native workflow started.

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
resume facts before publication. Other6 files are read-only. Worker6pass65.92s and
parent6pass65.43s now complete; all pre-existing named test/helper ASTs unchanged,
six exact read-only hashes/log permissions verified. Sol focused review found a
false-positive: deadline cases expire at a fourth outer revalidation before entering
the transaction; they do NOT establish its inner guard. R9 now includes correcting
the barrier to actual transaction entry and asserting calibration-worker termination
in the three-way case. Malformed-resume cases passed focused review. No combined
340-test invocation is claimed.

Sol full R8 source review found a capability/Guardian-dispatch race with
non-controller-serialized replay/recheck/expiry revocation, plus None-ID wildcard
and ignored kind. Root accepted. Active native worker is in
`native-capability-transaction-r9-20261018`, base2d63777, exact7R8-proof files copied.
Read [R9 plan](../.archive/PLAN-native-capability-transaction-r9.md), INCLUDING final
Opus arbitration. Writable fence: daemon.py; controller.py ONLY native_calibrated
rollback; native_regressions tests; test_session_native.py ONLY compiled-default
STOPPED fixture correction. Other3read-only. Final R8 Opus completed NEEDS WORK;
no review hold remains. Accepted additions: final identity/lease/Guardian binding,
transient durable-write rollback before error-handler save, actual transaction
cancel-wins/deterministic final-wins, strict STOPPED refusal, resume type ordering,
async old-worker operation identity, corrected transaction-expiry/worker-completion
proofs and named remaining guard cases. Legacy stock-capture dispatch residual is
explicitly deferred. Focused proof then final suites once; no source acceptance,
native100 or live qualification.

**Helper causal composition:** worker `/root/luna_runtime_instrumentation`, worktree
`/home/dev/.cache/crowley/worktrees/native-operator-causal-composition-20261018`,
base2d63777. Owns ONLY tools/native_calibration_operator.py and its test file.
Read [the current plan](../.archive/PLAN-native-operator-causal-composition.md),
[Sol's concrete repair prescription](../.archive/executor-review/native-operator-final-closure-failure-triage-sol.md),
[the preceding plan](../.archive/PLAN-native-operator-final-closure.md) and
[Sol's findings](../.archive/executor-review/native-operator-production-proofs-sol-review.md).
Seven exact frozen R8 native files are read-only development inputs, not accepted code.
Actual helper Opus completed exit0/claude-opus-5-5, STATUS: MAJOR ISSUES.
Final root arbitration is appended to the closure plan; no review hold remains.
It supersedes the original Sol prescription: providerDeadline belongs ONLY to
initial construction, not later hold/measure/resume phases. Additional accepted
fixes include actual INPUT_CALIBRATION success, error detection at any wait,
genuine Guardian-generation increase on new PAUSED handoff, private pipe reply
correlation, no unpressed release input, and complete GO-time action budgets.

Previous helper3cb57dad/testc0221bde froze RED:61 pass/3 fail, no required causal
fixture. Root rejected the completion claim and independently reproduced two
failures. Normal recovery is misclassified by the helper actor itself, not an
R7 compatibility failure. Reply-loss tests conflate incomplete private reply
(valid early exact cancellation) with a complete server-indeterminate private
reply (RPC unusable, owner retained through cleanup horizon). Sol triage provides
the exact repairs and allowed external-device factory seam. Neither X11Screen
nor X11Backend constructor discovers a game window; no live WoW interface blocker
exists for this offline composition. Keep the failed tree/reports as evidence.

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

No active root exec. Native R8 actual Opus28192 CLOSED0/claude-opus-5-5/NEEDS WORK;
final arbitration is in R9 plan. Sol full R8 source review and added-proof review
also NEEDS WORK, accepted corrections above. Earlier six passing cases do not
establish transaction proof. Helper Opus22003 CLOSED0/MAJOR ISSUES; R7Opus2839
CLOSED0/NEEDS WORK. Parent3947/42539/42012/76434/6947/41048 and backups30667/73320,
checkpoint push53971 all CLOSED0. New actual CLI review sessions must remain
attached/polled <=30s, no fallback; rawJSONL0600 stays private.
Checkpoint **2d63777** contains the consolidated handoff; use git log for latest HEAD.
Frozen candidate SOURCE is also pushed as `checkpoint/executor-20261018` commit
`dacefb9`: exact seven R8-proof files plus failed helper pair, nine curated files
only. It is an UNACCEPTED recovery checkpoint with the native race/helper red suite
explicit in its commit message; canonical main source/runtime is not promoted.

Read-only live pin precheck23:40: configured authentic CLI0.162.1 SHA628e3548,
producer SHAcb938cab matches config/user1000/mode0700; live daemonPAUSED/gen23,
nativeCalibration=false/inputCalibration=false, calibration operationidle.
No service/config/input mutation was needed or performed.

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

Hourly snapshot `beta-20261019T001252Z-099a6adfaad4` independently validates;
manifest SHA256 `01bb962b4846077935d8eb8532e69e89e824f61e5ea2c13d86525f1d08b9ceb9`.
It includes scan62. Next hourly due01:13UTC. Use
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
