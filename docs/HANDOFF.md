# Forever Tradecraft handoff

Updated 2026-10-19, 04:05 UTC. Repo `/home/dev/repos/pegasus`.
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

Only `/root/luna_live_recovery` operates actual GUI/game. Previous operator
`/root/luna_live_continuation` confirmed all inputs/tools closed and is inactive.
Root may read retained
screenshots, run isolated Xvfb and coordinate source/service work. Arthur remains
stationary at Ironforge AH; no movement or trading. Sunshine/Moonlight disabled.
WoW PID644491/procstart15495385/XID0x02e00001; fingerprint
`e84a459bda54c891092f049af9c523eb171588ce566a44123723d733baf6918a`.

Canonical crowley-session.service verified active PID3581203 after native source
installation/restart, **PAUSED/gen24/nativefalse/inputfalse/operationidle**.
Seven accepted native files are installed; helper remains uninstalled.
See native-paused-install-parent-verification.json for hashes/pins/process proof.
Collection is still **operator-assisted**; GUI Luna keeps it flowing.

Latest parent independently verified **73**, UID
`beta-normal-alliance-1792378010-Arthur-5824`, start02:46:50UTC:
428obs/2156rows/408full/20bounded/0incomplete, exact900s start interval.
Original SavedVariables/DB logical digest/production-decoded exact loaded ACK
verified in build-70450-seventythird-scan-parent-verification.json.
Finish→server14.394454s. Starts64–73 were900s.

**Current live blocker after actual panel preflight:** generation24 preflight
succeeded; agent defer produced actual visible Construct/Restore controls. The
handoff expired during operator proof. Fresh empty-ID recovery admitted; one
fresh exclusive-template-verified Restore click at03:00:37UTC reached the Lua
handler and saved restore_pending. New load has no telemetry surface and Restore
remains visible; completion expired. #74 due03:01:50 was MISSED while fenced.
Do not report continuous cadence or a decoded ordinary boot.
Installed Agent/Commands/Core/Scanner were exact main before this diagnostic.

**LIVE CAUSE CONFIRMED by flushed original bytes:**
`first publication: Interface/AddOns/Crowley/Agent.lua:501:
Interface/AddOns/Crowley/Agent.lua:158: Crowley movement telemetry has invalid facing`.
Marker failed/attempts1; savedmtime1792380928.9356596, original SHA
8ba82cd2acc729248dfa0fef84eb1438c3af51695e983a8245bc8110d883a342.
Root preserved original bytes in a0600 file under private native-restore-facing-failure-
20261019 evidence; public addon-restore-invalid-facing-live-evidence.json.
Exact invalid native value unknown, don't assert nil. Parent model unavailable
facing reproduces guard/permanent failure after later validworldevent too.
Actual savedmarker is valid and modeled ready-load restores ordinary normally.

Diagnostic retention Agentb46e679f/testaf761acb is installed+loaded and committed
c8498ce (pushed). Worker9/parent9(1.84s)/SolREADY. It retains optional private
CrowleyDB.agentRestoreFailure after existing failurecleanup, clears only fresh
restore_pending initialization, no lifecycle/admission change. New soleGUI Luna
finished normal /reload flush (no moreRestore needed), GameMenu closed, Arthur
stationary/world/identity unchanged, allinputsclosed. Old actor is inactive.
No more live inputs until reviewed behavioralfix is installed.

BEHAVIORAL FIX accepted and installed at04:04UTC. Final Agent SHA
79aa0d6853d4122d0a968cc7b1cd8cead8cccff349afb8c698e5aee983ed9edb;
test189fd6368503458ea43940fe8eff38172142b95d256d108661359edb36a0fa70;
harnessd58ea219de6c5d723e8fc152aeb9ed40d521d27fc9d7216b4a47561c7fe1f206.
Existing installed Crowley directory symlink resolves to repository addon, same
inode; copy into main installs next-reload bytes. No service restart/SavedVars edits.
Initial Sol READY; actual Opus r1 noMusts/sourcecorrect, accepted2testShoulds plus
small early-timeout fix. Final full249pass; parent17pass2.30s; actual
claude-opus-5-5 DELTA r2 READY/rc0, unchanged frozen sources. Optional extra
recovery-path test nit is nonblocking. Public parent/install/review reports retained.
SoleGUI luna_live_recovery received CODE-INSTALLED signal and owns full live
reload→publicrecovery→Restore→ordinary/checkpointclear→AHreopen outcome.
No live success inferred until actual receipts. No native100/input qualification
or autonomous cycles yet.

| Client assumption | Required handling / evidence |
| --- | --- |
| Native movement can be invalid at ADDON_LOADED during reload. | Restore waits for actual PLAYER_ENTERING_WORLD and exact valid movementTelemetry; may retry after world entry for at most30s. This bound is a refusal, not an assumption that world entry guarantees readiness. Live correction validation pending. |

Actual private controls manifest:
`~/.local/state/crowley/executor-evidence/native-live-controls-20261019/templates.json`.
Retained actual WoW panel source SHA bfe7fb9ce7c7169fbf52e714e140c0e1f1e560c0077dc8ba4e46c5fe1e2b42c2.
98x27 templates; actual fresh Restore match score0.00063. Fixed Python matcher
on retained real frame costs2.5531s Construct/2.5208s Restore in region220x84.
Standalone Rust scorer implementation passes parent21tests and two independently
reproduced byte-identical release builds SHA75b18bd04cc3a9248f99ecdca3a1cdebe6e0d89c4d33eaebd600788177bcd80c.
Parent actual retained-frame benchmark: prep62.74ms, ConstructSEARCH43.55ms,
Restore42.61ms, SCORE9.45/8.64ms, exclusive52.38ms, dual86.45ms. Includes
serialization/startup/IPC/parse per call; not fresh live qualification.
Sol implementation NEEDSWORK: accepted build env/config isolation, private stable
source snapshot, stale binary test binding, stronger tie/ambiguity cases and
retained benchmark runner. Same Luna owns6files + new benchmarktool. Scoring
itself reviewed correct. Unfinished Opus r1 superseded/terminated143 without
verdict BEFORE source edits; preserve record, no acceptance claim. Final review
required after corrections. No helper/runtime integration yet.
Private official Rust/Cargo1.85.1+rustfmt installed under
~/.cache/crowley/rust-toolchain-1.85.1/toolchain; global PATH/game/services unchanged.

Private receipts/images/original payloads:
`~/.local/state/crowley/executor-evidence/runtime-relink`.
Parent verifier `.archive/executor-review/verify_preserved_sweep.py` is private,
not committed. Public exact evidence records are build-70450-<ordinal>-scan-parent-
verification.json. For next completed sweep verifier prior_start1792378010; record actual missed
interval, never invent900s after this recovery.

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

Native milestone committed/pushed12b0646; protocol docs pushed4e405aa
(use git log for current HEAD). Recovery
SOURCE branch checkpoint/executor-20261018 commitc83b6ca remains pushed and
unmerged: frozen R10 plus old failed helper pair; do not install that helper.
Root copied accepted seven native files to main and restarted PAUSED service
with GUI input quiet. Independent verification confirms PID3581203/gen24,
unchanged authentic CLI/producer/config pins and unchanged WoW process.
Initial immediate post-restart assertion failed before its report; subsequent
independent verification passed without repeating the restart. Public receipt:
`native-paused-install-parent-verification.json`.

## Helper release corrections: final offline candidate

Worker final pair in `native-helper-final-integration-20261019`:
helper6f8f87efad4e818d3c401d600d7fabe34d8ba48c405832ff20e53924bb5ddbac,
test39f7c5c769e9769561f44d45b9cd6b759ae329fec45ef9aa6ba4a0ae45503bee.
Full73pass/364.98s, no unresolved real fixture failures. Public
native-helper-release-corrections-{closure.md,freeze.json} pin actual source/logs.
Real modes: success100→publicpause→freshordinaryrecovery/checkpointNone;
measurementfailure→newPAUSED/recovery/originalfailurepreserved; controlpreflight;
ordinary/Restore recovery; readiness/PRESSED budget/posthandoffcancel negatives.
Sameactual sealed input and production _source_bindings provenance. Fixes actual
pause response contract, deadline min, emitter/Watchdog allocation and inheritedFDs.

Parent inspected production delta and final workflow assertions; independent full73
PASSED367.61s (session60695 completed0) in fresh `helper-addon-parent-composition-20261019` with
canonical accepted seven native files plus initial d8addon (exact pins retained).
Private helper-addon-parent-composition-20261019/input.json,tests.log,result.json.
Addon follow-up test changes/timeout nit are separate; do not relabel tested bytes.
Sol+actualOpus final helper review now RUNNING after parent pass, then accepted helper/Rust
integration separate round. Helper is NOT main/installed; never run rejected old
ffc8/d483 or failing3cb57/c0221 candidates. InitialR8 and66pass are historical.

## Remaining live gates

- Actual WoW Construct/Restore controls have now been captured and measured
  (private actual templates above); earlier full-frame template image was
  synthetic, GTK certificates have screenCapturedfalse.
  Construct/Restore are WoW Frames in Commands.lua, NOT the later human GTK window.
  Panel220x84 UIParent units TOPRIGHT(-24,-24), buttons100x28 offsets(8,-8)/(112,-8).
  UIParent1365.33x768 vs physical1920x1080 is not a measured button transform.
  No guessed coordinates/templates. GUI Luna has read-only prepared source facts.
- Native source installed and actual operator-assisted control preflight/template
  acquisition reached restore startup failure above. Finish diagnosis/correction
  and actual ordinary recovery/cleared checkpoint/PAUSED/unarmed/AH reopen before
  further calibration or claiming recovery success. No rejected helper/native100.
- Accepted helper/native exact integration and ordinary recovery contract, then
  real inactive control preflight +fresh native100. Measure live template matching;
  synthetic2.6/5.05s benchmark does not establish a Rust bottleneck.
- Only when actually ready request genuine human GTK physical key+click gate.
  No user action needed now. Never fake human success.
- Then three autonomous900s save/upload/ACK/reopen cycles. Only then complete.

## Preservation and working rules

Latest hourly backup `beta-20261019T031301Z-0fa0a2c4a55c`, parentvalidate PASS,
manifest SHA71025454b869771ea221a9d7bc1e97437dd48736aca05bb7826b1ee3d4eb5bea,
0700 directory, data through73. Next hourly04:13UTC. Run
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
