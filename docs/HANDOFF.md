# Forever Tradecraft handoff

Updated 2026-10-19, 02:49 UTC. Repo `/home/dev/repos/pegasus`.
Origin https://github.com/kyle-deprow/forever_tradecraft . Existing Crowley names
remain intentional. User revoked AGENTS.md rules; ongoing fixes/install/recovery/
commits/pushes are authorized. Do not re-ask routine permission.

## Objective

Private WoW Forever market research/trading platform, ready to collect data and
build profession/flipping/investment strategies at launch. First-run catalog:
**428 targeted items**, multiple professions/trade goods/recipes/containers and
selected equipment; see [WATCHLIST.md](WATCHLIST.md). No scan of every AH item.
Capture cheapest **20 distinct unit-price levels plus boundary ties**; explicit
full/bounded/incomplete coverage. Missing/timeouts are unknown, never zero supply.
Disappearance is an uncalibrated activity proxy, not confirmed sales.

Required **15-minute** repeat includes the entire save/upload/ACK/reopen loop.
SavedVariables persist only on reload/logout/exit; written ACKs load on reload.
Completion means **three autonomous15-minute cycles**, not merely addon timers.
Later work: verified Forever recipe economics, strategies and launch monitoring.

## Live game/data

Only `/root/luna_live_continuation` operates actual GUI/game. Root may read retained
screenshots, run isolated Xvfb and coordinate source/service work. Arthur remains
stationary at Ironforge AH; no movement or trading. Sunshine/Moonlight disabled.
WoW PID644491/procstart15495385/XID0x02e00001; fingerprint
`e84a459bda54c891092f049af9c523eb171588ce566a44123723d733baf6918a`.

Canonical crowley-session.service verified active PID3581203 after native source
installation/restart, **PAUSED/gen24/nativefalse/inputfalse/operationidle**.
Seven accepted native files are installed; helper remains uninstalled.
See native-paused-install-parent-verification.json for hashes/pins/process proof.
Collection is still **operator-assisted**; GUI Luna keeps it flowing.

Latest parent independently verified **72**, UID
`beta-normal-alliance-1792377110-Arthur-7645`, start02:31:50UTC:
428obs/2205rows/409full/19bounded/0incomplete, exact900s start interval.
Original SHA `f3f527ae84418a6824d2e16b176cff3248b7076f5dc88af9fd31b2349e2f29d1`;
DB logical digest and exact loaded ACK independently checked with production PNG
decoder, boot1792377635-848394/pending0/ordinarynormal0/inactivefence.
Finish→server36.462403s. Scan73 started naturally02:46:50UTC while GUI input
was idle during source promotion. Starts64–73 were900s; #73 closeout pending.
Read-only totals02:43: **80sweeps/34240observations/191023rows**, latest receipt
2026-10-19T02:40:23.462403UTC. Historical sweeps included.

Private receipts/images/original payloads:
`~/.local/state/crowley/executor-evidence/runtime-relink`.
Parent verifier `.archive/executor-review/verify_preserved_sweep.py` is private,
not committed. Public exact evidence records are build-70450-<ordinal>-scan-parent-
verification.json. For73 verifier prior_start1792377110, ordinalseventythird.

Earlier GNOME keyring modal blocked AH reopen/dimmed HUD. One owned installed
uinput ESC cleared it00:13, no credentials/settings changes; AFK logout cleared
the earlier typed-but-unsubmitted chat. Scan63 interval4257s was a real missed
cadence, never reclassify as900s. Recovery receipts preserved. Xvfb does not
isolate system-wide uinput or per-user GNOME screenshot locks.

## Native executor: final offline review, no production defect found

Luna worker `/root/luna_profiler_schema_fix` completed native R10d and is now
assigned the HELPER correction below; do not ask it to edit frozen native trees.
Final native WT:
`/home/dev/.cache/crowley/worktrees/native-terminal-final-r10d-20261019`,
basec5e5772. Freeze/closure: native-terminal-final-r10d-{freeze.json,closure.md}
in .archive/executor-review. Plan: PLAN-native-guardian-generation-r10.md plus
PLAN-native-guardian-proof-r10b.md and PLAN-native-terminal-proof-r10c.md including
FINAL arbitration and minimalR10d appendix.

R10 daemon SHA
`5c55f9b3080649cebf7bb57fbdcd14f69ddcbac83f5172500ba045c745d9ea58`.
Original Guardian generation is immutable in owners/capabilities/tickets/context,
validated against current state and inside real Guardian-locked pre-Popen start.
Lock order controller→construction→Guardian. Both Sol and actual Opus found no
production defect. Legacy capability-less stock capture remains explicitly
deferred; strong fencing claims concern the configured producer qualification path.

R10b corrected four ACTUAL compiled producer/public owner cases: PAUSEDpreflight
and NATIVEprepare+bootstrap, each revoke-first/admission-first. Exact new Guardian
error with callback blocked/owner unchanged and zero starts; actual child/reap
when admitted first. R10c corrected real controller-mutex contention after real
flush, refusal-before-capture counter and direct owner/epoch assertions. R10d
finally adds later public CANCELLED terminal recheck in actual cancelled branch
and corrects supplementary sleep-test wording. Inspect branch, not only green count.

Separate results, never invent a combined invocation:
- WorkerR10 native3suites367pass/532.50s +separate14 postformat and namedruntime.
- ParentR10 core25pass/201.87s, R10b4pass/5.20s, R10c8pass/49.12s.
- WorkerR10d2pass/43.30s; parent2pass/43.45s, sourcebranch/fence/sixreadonly/
  hashes/logs/statics independently verified. Parent native-r10d-parent-verification.json.
- Final SolR10d **READY/no findings**. Actual final Opus exited0 on
  claude-opus-5-5, NEEDS WORK solely for a misleading test comment, no functional
  findings. Root corrected the exact comment and verified the entire module AST
  unchanged; six other files exact R10d. No test rerun for comment-only edit.

Root accepted offline native source in
`/home/dev/.cache/crowley/worktrees/native-release-final-20261019`, exact seven
hashes in native-final-offline-acceptance.json. All Opus/test sessions are CLOSED;
no active root exec. No live native100/input/autonomous qualification inferred.

Main c5e5772 was pushed before promotion (use git log for current HEAD). Recovery
SOURCE branch checkpoint/executor-20261018 commitc83b6ca remains pushed and
unmerged: frozen R10 plus old failed helper pair; do not install that helper.
Root copied accepted seven native files to main and restarted PAUSED service
with GUI input quiet. Independent verification confirms PID3581203/gen24,
unchanged authentic CLI/producer/config pins and unchanged WoW process.
Initial immediate post-restart assertion failed before its report; subsequent
independent verification passed without repeating the restart. Public receipt:
`native-paused-install-parent-verification.json`.

## Active helper correction: real failure recovery/all modes/provenance

Worker **`/root/luna_profiler_schema_fix`**, NEW task in
`/home/dev/.cache/crowley/worktrees/native-helper-final-integration-20261019`,
basec5e5772. Root copied seven exact nativeR10d files plus helperffc8/testd483.
Own TWO files only: tools/native_calibration_operator.py and its test. Seven native
files/driver/Guardian/addon/config/service/GUI/git are forbidden/read-only.
Read **PLAN-native-helper-release-corrections.md** IN FULL; it supersedes earlier
metadata-only freeze instructions. Reference PLAN-native-helper-final-integration.md.
Main writes ONLY native-helper-release-corrections-{closure.md,freeze.json}.

Final Sol helper review NEEDS WORK, accepted concrete findings in
native-helper-causal-final-sol-review.md:
1. REAL BUG: pause mutation response has controller fields/state/generation/
   leaseGeneration, no calibrationOperation or guardian. Current helper wrongly
   requires them, so actual Operator.run failure recovery always fails. Validate
   immediate newPAUSED/higherlease; fetch aggregate status for nonrunning native
   op; require new binding higherGuardian/unarmed BEFORE recovery input. Preserve
   original error and failed receipt through actual successful recovery.
2. Reuse actual causal compiled fixture for ALL modes: measure, preflight,
   ordinary_reload recovery, restore recovery, failure/newPAUSED/emptyID,
   post-handoff cancel, real readiness and READY/watchdog/GO/PRESSED budget
   negatives. Old other-mode tests use FakeScreen/FakeInput/rawobs/directclient.
3. Share actual sealed input artifact for screen/input factory; real helper SHA
   and _source_bindings; receipt assertions bind config/templates/producer/input/
   native dependencies. Current causal receipt omits/mismatches these.
4. Monotone _record_operation_deadline must min(existing,new), not silently extend.
5. Allocation matrix: invalid OwnedEmitter pgid abort/reap actual spawned child;
   Watchdog missing owner-start refuses; cancellation child closes inherited
   nonprotocol descriptors; preserve causal errors/cleanup/no unpressed releases.
6. Actual successful measure→publicpause→fresh MODE_RECOVER→ordinary Lua
   SavedVariables reload: checkpointNone, PAUSED/nativeCalTRUE/inputFALSE,
   unarmed/clean. Needed before human GTK gate; no fake human calibration.

Previous helper baseline is IMMUTABLE in
`native-operator-causal-composition-20261018`: helper
`ffc8ae4f2e338d36d521002e7de5d894c3876a06f621aca5166361055fa9b2e5`, test
`d4834f543333a66e9bc9d31e150ef9e085195a27cc93656df5c8d81683fd8b48`.
Worker66pass/189.07s, parent independently66pass/188.77s with private0700XDG,
full0600log SHA3c026e3f41c5881edfa0bafa83e6400fefd7a39471f2a40384b26443631effea.
Two warnings are explicit subprocess fixture fork DeprecationWarnings, no hidden
thread failures. These green tests DO NOT cover the real pause bug/allmodes.
Seven baseline dependencies were frozenR8, not accepted native; new correction
uses exactR10d. Parent native-operator-causal-parent-verification.json records it.

Old helper agent `/root/luna_runtime_instrumentation` ended integration task at
metadata only (NO implementation/source changes); its integration closure/freeze
explicitly mark missing proof. Native worker is now implementing actual code.
Do not accept another metadata-only final/redDONE. Complete focused cases then
fullhelper once, exact7readonly/imports/authenticCLI/private0700XDG/capturelock/
bus/complete0600logs opened before commands/cleanup. Parent meaningful repro,
Sol and actual Opus review, then eventual helper promotion.

The real one-Hz external Lua publication ticker is now correct; no delays in
provider/admission wrappers or restamped captures. Earlier parent diagnostic
failed update2 cadence and is retained separately. Original failed helper3cb57/
c0221 reports61pass3fail remain history. Do not resurrect them.

## Remaining live gates

- Actual WoW Construct/Restore controls physical bounds are UNKNOWN. Retained
  full-frame template image is synthetic, GTK certificates have screenCapturedfalse.
  Construct/Restore are WoW Frames in Commands.lua, NOT the later human GTK window.
  Panel220x84 UIParent units TOPRIGHT(-24,-24), buttons100x28 offsets(8,-8)/(112,-8).
  UIParent1365.33x768 vs physical1920x1080 is not a measured button transform.
  No guessed coordinates/templates. GUI Luna has read-only prepared source facts.
- Native source is installed. Sole GUI Luna is authorized, AFTER #73 closeout,
  to source-check and perform bounded operator-assisted control preflight/template
  acquisition: exact PAUSED generation → public preflight reservation → agent
  defer/no reload → actual panel screenshot/bounds → public recovery handoff →
  agent recover/verified Restore → public recovery-complete → ordinary boot/
  cleared checkpoint/PAUSED/unarmed → AH reopen. No rejected helper/native100.
  Do not start if source/readiness/timing cannot support safe recovery.
- Accepted helper/native exact integration and ordinary recovery contract, then
  real inactive control preflight +fresh native100. Measure live template matching;
  synthetic2.6/5.05s benchmark does not establish a Rust bottleneck.
- Only when actually ready request genuine human GTK physical key+click gate.
  No user action needed now. Never fake human success.
- Then three autonomous900s save/upload/ACK/reopen cycles. Only then complete.

## Preservation and working rules

Latest hourly backup `beta-20261019T021427Z-40cef19170e3`, parentvalidate PASS,
manifest SHA552a2eeb7a8c627251e3cf6438d200f003da7b039d8fbd51b69db38eb2f6d0fe,
0700 directory, data through70. Next hourly03:14UTC. Run
`uv run python tools/market_backup.py snapshot`; independentlyvalidate_snapshot.
Prior isolated restore drill passed; no repeat without reason. Raw/private files
stay out of git. Historical handoff: handoff-history-before-consolidation-
20261018T2330Z.md in executor-review, and git history.

Authentic CLI0.162.1 SHA628e35487d888a28f0427fc37501da529dd3d81fcbad7a2c3421c1e8670d92e1;
producer SHAcb938cab1bd99dc088d05f6f55c8a0443401320755e2037633e7f9ac6dbe2396
matches config/user1000/mode0700. Last config rawSHA0dde50b95ad0e992a53d3cfa86e02cbba7e60af2d6d722db86804bb77c12c3a1.
Recheck before promotion. No runtime requalification inferred from offline pins.

Use compact existing .agents/skills/local-game-control and crowley-client-contracts,
not a skill per incident. Lua/model/hardware evidence are distinct. Maintain
full logs/hash/fence and inspect exact claimed branch before completion. User
prefers Luna implements/GUI, Sol reviews, actual Opus executor review; no model
fallback. Main agent owns arbitration/git. **Never git add .** Explicit curated
paths only; many private untracked files. No resets/stash/reverting others.
Continue authorized work; do not end coordination with a status-only final.
