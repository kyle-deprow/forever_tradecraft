# Forever Tradecraft handoff

Updated 2026-10-23 01:43 UTC. This is the active handoff. The exact preceding640-line
handoff is preserved in [review-closure history](../.archive/executor-review/handoff-history-before-ack-review-closure-20261019T1439Z.md).
Earlier chronology is linked there. Historical pending statements are superseded
by the current state below.

## Current collection and calibration state

**USER DIRECTION: ASSUME THE BETA IS OVER.** End live collection, reconnects,
recovery and calibration appointments. The game operator has been told to stop;
`crowley-session.service` is stopped and disabled (independently verified
inactive/disabled). Do not re-enable or resume scans without a new user update.
Keep existing data/evidence and focus on offline launch readiness. Scan290 is
the last fully verified complete/uploaded/loaded-ACK sweep. Partial291 is not
yet durable or uploaded. The separately scoped
motion-correlation fix continues offline, with native eventual-echo delivery
explicitly unqualified; no live acceptance is authorized by these code changes.

**HUD visibility implemented and promoted to source.** `/crowley hud` toggles;
`/crowley hud hide`, `show`, `status` make/check an explicit choice. Preference
persists across reloads. Hidden HUD has no periodic updates or stale frame bytes;
show publishes fresh bytes at original geometry. Native diagnostic ownership
is protected in both command orders. This is display-only, not a controller
pause or scanner mode change. The installed addon symlinks MAIN; commands become
available at the next user-owned addon load/reload. No live reload was sent.
Luna265PASS22.25s; parent265PASS21.82s/Ruff/format/diff; Sol READY/no Must or
Should. Read [the plan](../.archive/PLAN-hud-visibility-20261023.md).
Private R2 `executor-evidence/hud-visibility-20261023-r2/`, cumulative patch
3165f785af01b282b66329a2b71336c31afca98fbade4568361a67d9fdb9ce5b;
Sol review6c28576bba3198ff93575270674d8f0a34d28e26cdd89033b91c8c9790d7f6e4.
Agent.lua source now05ddf75815b322e2e925cacda7d588bead223d3f9bbe162c82061886982ec4ea.
Earlier live runtime manifests below describe the pre-HUD baseline, not current
source; do not reuse them as current dispatch pins. Service stays disabled.

**NEW LIVE BLOCKER: ARTHUR DIED BESIDE JAXON.** At01:17:07UTC the retained
scan291 watcher image shows the Release Spirit dialog and Arthur's corpse.
No input had been sent since the scan-start click at01:11:11. Death cause is
unknown; the adjacent protected/secret-value telemetry error does not establish
causation. User has been notified; all game input is held pending recovery
preference. Do not release spirit, navigate or run the ordinary reload helper
through the modal. Scan291 terminated early: UID
`beta-normal-alliance-1792717871-Arthur-6563`, finished1792718223,
254attempts/177failures/370rows/428planned, pending1 in retainedHUD.
**This partial is still memory/HUD-only:** preserved pre-reload SavedVariables
does not contain its UID; no upload or loadedACK exists. Preserve evidence under
`scan291-partial-preserve-20261023T0118Z/preservation.json` in assisted-collection
evidence. Screenshot `scan291-watch-prestage-20261023T0106Z/029-full.png` also
shows Agent.lua165/586 failing on a secret number. Offline motion-correlation
work continues in its isolated worktree; earlier active291 statements below
are superseded by this death/hold.

**Last live collection state (superseded by beta cutoff above).**
Exclusive GUI owner `/root/luna_assisted_scanner` is explicitly authorized to
collect. Arthur remains in Stormwind next to Jaxon; no navigation/trades.
**Active assisted scan291:** actual start01:11:11UTC (1792717871), due01:26:11UTC
(1792718771),51seconds after prior nominaldue01:10:20. Fresh native frames show
AHopen/itemphase/advancingordinal/428planned/pending0/speed0. One released curved
right-click; no keyboard command. Start sidecar:
`scan291-jaxon-curved-click-prestage-20261023T0106Z/scan291-start-proof.json`.
Watcher/postprocess use the current24-file diagnostic manifest. Do not deploy
mid-sweep or mistake intentionallyblank activeSweepId for idle.

**Latest completed scan290:** UID`beta-normal-alliance-1792716920-Arthur-5985`,
started00:55:20UTC, finished01:03:25UTC,428attempts/0failures/724rows.
Parent independently parsed exact originalDBUID and SHA
f585281dcb43a8c6d82a09c00c3f7db7295f416723851c0110f6262db3ae09d2;
companion/strictDataACK timestamp01:04:25 (60safterfinish); loadedHUD exactUID
boot1792717487-523401/seq5/CRC724215353/pending0/AHclosed. Proof:
`scan290-postprocess-stage-20261023T0055Z/scan288-save-upload-ack-20261023T010404944167Z/parent-loaded-ack-verification.json`
under assisted-collection-luna-20261021. Scan289 also fully independentlyACKed,
728rows/zero failures; its artifacts remain preserved. The earliergap and late290
start remain real; do not claim an autonomous or proven15-minute cadence.

**Simplification installed and code-reviewed.** R2 is committed/pushed asb769d57;
23 reviewed files include strict schema4, passive startup, durable genuine drill,
typed invalidation, deterministic Jaxon opener and actual-start900s scheduling.
Parent753PASS/562.59s, Ruff22/format/diff clean; Sol READY/no Must or Should.
Addon-first one-shot reload was separately CRC-verified before Python promotion.
Private R2 artifacts: `executor-evidence/autonomous-startup-takeover-20261022-r2/`.

**Configured capture admission FIXED live:** the old PAUSED recovery-capability
refusal is corrected by the isolated three-file passive-region patch. Sol READY,
parent149PASS/287.49s, Ruff3/format/diff clean. Promoted/restarted00:40:24UTC.
Public repeat start generation95 now succeeds with three advancing ordinary
frames, no input and startup takeover_needed. Driver/Agent/protocol unchanged.
Read [the narrow plan](../.archive/PLAN-passive-region-admission-20261023.md).
Private artifacts: `executor-evidence/passive-region-admission-20261023/`.
Canonical installed24-file pin manifest is `installed-runtime-manifest.json`,
SHA2cfa592341b33f88352906e7456c6433d6ad43f9bbd64771c6a322cf82f4374d.
ConfigSHA89580ebd... already pins private Codex0.162.1 and was unchanged.

**Hover evidence instrumentation installed; exact native failure captured.**
Evidence-only patch passes SolREADY and parent75PASS/12.10s/Ruff3/format/diff.
Installed/restarted01:09:23, newownerPAUSED96. Actual drill then failed before the
human window: Guardian reports unattributed Motion source4/target62914563. No
click, keyboard action, human sample or PASS; controls/processgroups cleared.
Timestamped actual JSON:
`scan291-takeover-drill-failure-20261023T0109Z/latest-hover-failure.json`, SHA
d383992b7855feb2f868bd2390e3730b133c43b7733d0e6597204e4ef932d322.
It retains complete rawblocks plus the rejected partialtail: first primarymotion
accepted, expected motionIndex1/pendingEchoCount1, second primary rejected before
a relative-pointer echo appears. This proves the mandatory ordering assumption
fails on the recorded stream; it does not prove no echo ever occurs. Replay this
exact stream/context before changing correlation; preserve primary/raw pairing,
plan order/identity/endpoint checks and immediate human/UNKNOWN revoke. No filters,
blanket device acceptance, fabricated echo, native-profile/cadence change or new
calibration framework. Continue assisted collection while correcting this seam.
Private reviewed R2 instrumentation bundle:
`executor-evidence/takeover-hover-evidence-20261023-r2/`; current installed manifest
`installed-runtime-manifest.json` SHA
0b79d94c7876615f42511199ba56265a948c8a1107f2b38463819919a458b4d0.
Actual native input cause correction is next; do not ask the human to calibrate
until actual hover reaches awaiting_input. Genuine drill and full autonomous
save/upload/loadedACK/reopen/takeover-resume remain acceptance work.

### Historical work notes (superseded by the installed state above)

**Sol assisted-helper review NEEDS WORK:** Separate read-only review of the past
2245/2257 helper snapshots found first-frame polling errors, receipt labels that
hid four taps instead of a held Ctrl-F12 chord, and success exit on an unobserved
start. Luna repaired those in the private helper, including actual-argv/cleanup
replays and a private-Xvfb Xlib held-state query. No interaction was dispatched
by the affected attempts. Review artifact is private under
`autonomous-startup-takeover-20261022/assisted-helper-review/sol-review.md`.
This is not the final core review. The source-controlled game-control skill now
records the concise modifier/raw-first lessons; its validator passes.

**CURRENT: USER HANDED CONTROL BACK; ASSISTED COLLECTION RECOVERING.** User explicitly
answered "Luna can resume collection" and authorized the simplification with a
Luna/Sol loop. `/root/luna_assisted_scanner` is running and exclusively owns GUI
input/capture. Its fresh 21:01 UTC scene verified the same WoW process, Arthur
stationary in Stormwind AH, advancing ordinary frames, empty closed editor and
no held controls. The foreign `/run F=C` buffer is absent; no cleanup was sent.
Scan288's loaded ACK is complete. Repeated WOW51900319 disconnects and verified
interaction refusals have delayed the next sweep; no scan289 start is confirmed.
Luna recovered the cached Arthur login and is using one pre-staged curved
hover/auctioneer-tooltip/right-click chain. The latest hover found an intervening
player rather than Fitch and correctly refused the click; Jaxon is being verified.
Continue curated 428-item scans at 900 seconds anchored to actual starts. All earlier takeover
holds below are superseded by this explicit handback.

**Recovery COMPLETE / scan288 loaded ACK confirmed:** The first ACK-only helper observed a fresh
WOW51900319 disconnect and sent no input. Luna dismissed it and followed the
cached Normal ruleset/Arthur path with guarded curved clicks. Arthur is entering
the world in the earlier record; the later world frame now confirms Arthur
stationary in Stormwind, ordinary HUD boot1792704247-503409/seq17, exact scan288
loaded ACK and pending0. Root independently CRC-decoded that retained full image
and parsed the exact original `CrowleyDB.scans[uid]` key. Proof:
`handback-world-entry-observation-20261022T2124Z/parent-loaded-ack-verification.json`.
Luna is reopening the AH; a new scan start remains unconfirmed.
Root also independently decoded retained 21:01 HUD PNGs and
verified scan288's preserved original SHA. Comparing parsed current SavedVariables
to that original showed only `scheduleTrace` changed. Proof is
`handback-window-20261022T2101Z/parent-retained-handback-verification.json` under
the assisted-collection evidence directory. Do not call this an autonomous cycle.

**SIMPLIFICATION IMPLEMENTATION RUNNING OFFLINE.** Core Luna owns the complete
startup/drill/AH-open vertical path in an isolated worktree; Sol independently
reviews the design then frozen code. Read the concrete
[implementation plan](../.archive/PLAN-autonomous-startup-takeover-20261022.md).
Replace routine native/GTK/human-per-restart gates with passive automatic startup
and one durable environment-bound human takeover drill; retain runtime safety,
strict ACK/no-replay and the curved executor. Port the proven Stormwind opener.
The isolated worktree is
`~/.cache/crowley/worktrees/autonomous-startup-takeover-20261022`, base644dc14.
Sol's plan review identified two integration seams now explicit in the plan:
fresh process-local measured input evidence and a complete guarded Stormwind
command/binding path. Ownership includes minimal Agent.lua auctioneer telemetry
and its strict schema4 protocol/harness. The new parser rejects schema3, so the
later live promotion requires an explicit staged addon reload/source transition.
The current implementation covers passive evidence, durable drill/status, typed
invalidation, schema4 auctioneer facts, guarded keyboard dispatch, actual-start
cadence and active-repeat restart recovery. Verification is still running:
the native shifted-key trace exposed extra RawKeyRelease events and the complete
restart-to-admitted-action path needs a passing composed test. These are release
blockers. Final scoped tests, frozen source hashes and Sol code review remain
pending. Private Xvfb results do not qualify the live Mutter/Xwayland environment.
No production runtime change or service restart has occurred. Cutover requires
code review and parent checks, then a safe fully ACKed scan boundary. Do not run
another old calibration attempt. Actual autonomous cycles remain unqualified.

**Opus audit COMPLETE: MAJOR ISSUES / SIMPLIFY BEFORE CONTINUING.**
Read [the preserved independent audit](../.archive/REVIEW-calibration-architecture-opus-20261022.md).
Actual model claude-opus-5-5, read-only Read/Grep/Glob, no MCP/fallback; CLIexit0.
Root independently verified restart clears both calibration gates and runtime
AH-open still hardcodes Ironforge Buckler. Do not deploy the isolated patch or
run another calibration attempt under the existing design. Preserve that small
correct patch for the simplification. No runtime rewrite is proposed by the audit.
Next design should decouple routine startup/telemetry checks from native memory
benchmarking and per-restart human sampling, retain Guardian/watchdog/identity/
focus/curvedclickcap/decoder/journal/ACK, use a persistent takeover drill with real
input-environment invalidation, and port the proven Stormwind interaction path.
The user approved the simplification; implementation/code review and human
acceptance remain in progress. Any new user takeover takes priority.
Private original CLI prompt/raw/process/result: calibration-audit-opus-20261022/.

**Latest scan288:** Started20:35:05 UTC (`1792701305`), finished20:43:13
(`1792701793`), UID`beta-normal-alliance-1792701305-Arthur-3046`,428attempts/
zero failures/645rows. Preserved original SHA
`6a2a8f6a536618df45d160342d700b9d6f7b7a58e3165165e8379da8c2e02a6b`.
Companion uploaded/Data.lua strictACK observed timestamp1792701846=20:44:06,
53safterfinish. Exact loadedHUD ACK was subsequently independently verified at
21:24 UTC (proof above); AH reopen and the next scan remain unconfirmed. The earlier helper's first
chat-open Return exposed the foreign controller's `/run F=C` text and refused
typing/submission. No command was typed after that Return; no cleanup was sent.
Receipt `scan288-postprocess-stage-20261022T204327Z/scan288-save-upload-ack-20261022T204346728505Z/receipt.json`
under assisted-collection-luna-20261021. No active sweep at takeover; collection
is recovering rather than actively sweeping. Nominal next due20:50:05 does not
erase the actual collection gap or override user control.

**Isolated candidate FROZEN, NOT DEPLOYED:** Luna completed the minimal12-line
unused select_chat_all profile deletion in input92-keyboard-rehearsal worktree.
Private native workflow reaches real strict keyboard+pointer readiness and
no-input wait:8runtimeoperations/134steps/272keyboardrecords plus8pointerrecords;
observer staysopen/idle afterfinalrelease, then target/observer reaped and Guardian
registriesclear. Private fixture preconditions XTEST sources before observing to
avoid fresh-Xvfb DeviceChanged metadata; no production filtering/parser changes.
Scoped78PASS/1known-baseline test deselected, native9PASS/176deselected, Ruff/diffclean.
Unfiltered78PASS/1FAIL reproduced exactsame pointer gesture-plan assertion onclean
base1130c81. Report/manifest/native proof under input92-xi2-implementation; diffSHA
13a1e8345c4b950dfeab9a0db4ffc663fb83e638663b34855b9270760c11dcfb.
No productionpromotion, restart, code review or live qualification is claimed.

**Latest collection boundary:**287 completed20:26:57 UTC, UID
`beta-normal-alliance-1792700329-Arthur-5720`,428 attempts/zero failures/691 rows.
Original224404B SHA`da34f9f7fad98ad43fbf682486cffc44fa33ae26ee7ab5c51b921370f3505fd5`.
Companion upload1792700867=20:27:47 UTC,50s after finish. Exact loaded ACK/pending0
verified; parent independently decoded boot1792700890-960915 seq5 and parsed the
original SavedVariables queue key (not a UID substring). Parent proof:
`scan287-postprocess-stage-20261022T202108Z/scan287-save-upload-ack-20261022T202727179496Z/parent-loaded-ack-verification.json`.
This is historical evidence; see the current scanner state above.
Do not start early solely because post-reload scanner dueAt=0. Main runtime source
unchanged; latest pushedc252a3f contains only documentation/plan/skill updates.

**Offline repair RUNNING20:28 UTC:** Luna is implementing the minimal input92
fix in isolated worktree `~/.cache/crowley/worktrees/input92-keyboard-rehearsal-20261022`,
base1130c81, under [keyboard rehearsal plan](../.archive/PLAN-input92-keyboard-rehearsal-20261022.md).
Sol design review READY; exact runtime-vocabulary equality/sealed operation coverage
and real private-Xvfb open-idle final-release/workflow-readiness proof are required.
Production runtime bytes remain unchanged; GUI owner keeps scanning. No live retry
until frozen implementation, independent Sol code review and parent verification,
then promotion/restart/source rebinding at an exact ACK boundary and fresh native proof.
Plan ownership now explicitly includes tests/test_session_input_tool.py to retain
its generic left/right modifier-hold admission/refusal tests with explicit fixtures.

Completed exact diagnostic replay:281 source5 key records vs280 expected; first
mismatch is unused select_chat_all, then all256 suffix records align after one
extra raw Control release. Exact raw+partial bytes yield289 parsed events including
final KeyRelease40; finish()None. Missing final blank delimiter makes diagnostic
replayable=false but did not withhold the semantic event. Pinned xinput uses line
buffering; no parser/observer change is justified. Private diagnosis/report and
Sol design review: `calibration-resume-20261021/input92-xi2-implementation/`.
The existing game-control skill now records these two reusable lessons; validation
passes. No new skill folder or incident dump is added.

**Current collection20:18:49 UTC:** Assisted287 started at Jaxon,
`startedAt=1792700329`, due20:33:49 (`1792701229`), AHopen/item2/speed0/pending0,
interaction keys released. Receipt:
`assisted-collection-luna-20261021/scan287-interaction-20261022T201757Z/receipt.json`.
Actual286->287 start gap1660s(27m40),760s late against20:06:09 nominaldue.
Keep watching287, preserve/save/upload/exactACK and repeat900s assisted cycles;
no extra calibration attempt until reviewed fix promoted at a safe boundary.

**Input92 diagnosis underway:** Actual first keyboard divergence occurs in
calibration-only `select_chat_all`: expected release(a) before release(Control_L),
but pinned xdotool releases Control_L before a and emits duplicate raw Control_L
release due modifier compensation. All later256 class/detail records align after
that one extra record; final deliveredrelease remains partial. Runtime ACTIONS
explicitly exclude select_chat_all; public typing uses per-character allowlisted
keys. Luna is finishing exact parser/validator replay and producer-tail flushing
audit before root defines smallest fix. Preserve strict validation; don't filter
extra records, reorder contract to hide mismatches, or invent missing native fields.
Report under `calibration-resume-20261021/input92-xi2-implementation/`.

**Current blocker20:13 UTC:** Readiness-only input92 FAILED before human readiness:
`XI2 calibration event deadline expired`, operation started1792699794 and
finished1792699807 (20:10:07 UTC). No genuine/fakehuman input and no unchanged retry.
GTK root-child certificate and synthetic pointer pre/post predicates DID pass;
failure stage synthetic, keyboard predicate "extra or missing key transitions"
twice. Observer retained289/290 blocks/63,195bytes, no parserfailure/truncation;
final delivered KeyRelease is partial, replayable=false. Do not infer its cause
or invent missing native fields from that incomplete record. Immutable bundle:
`assisted-collection-luna-20261021/input-calibration-failure-92-20261022T201139Z/failure-index.json`,
original diagnostic SHA3e3cad097d297bbb86afcbb04f0f2916c2107a7b4e3b38a8c734eb9358ef903e.

Publicpause92 advanced PAUSED93/native=true/input=false; exact target PID549304
and title are gone, observer reaped, checkpoint keyABSENT, controlsUP and two advancing
ordinary stationary frames verified. GUI owner `/root/luna_assisted_scanner` is
restoring287 via the established Jaxon interaction chain. Next nominal due20:06:09
was missed for calibration; actual287 start is not yet confirmed. Keep collecting
while repairing, no further calibration attempt before reviewed fix and fresh gates.

Offline READ-ONLY Luna diagnosis is RUNNING in `/root/luna_calibration_diagnosis`,
bound to canonical1130c81 source (not its stale previous worktree). It compares
actual keyboard operations/keymap and raw/primary stream at parser/validator
boundaries, distinguishes incomplete evidence from replay, and proposes smallest
source/test fix. Report under `calibration-resume-20261021/input92-xi2-implementation/`.
Root will define an implementation plan after that diagnosis; Luna implements,
Sol independently reviews, root verifies/promotes. No host GUI/input/capture/IPC,
deployment or daemon restart by coding/review workers. Sole GUI owner remains Luna
scanner. User remains AWAY; human calibration has NEVER reached readiness.

**Successful native boundary20:09 UTC:** Mandatory control-preflight89 PASSED;
resume90/full100-update103-call measure-deferred PASSED with native proof valid.
Public pause advanced91; durable journal retained a valid measure90 checkpoint
although aggregate status omitted it. Canonical recover91 then SUCCEEDED;
parent independently verified journal PAUSED91/native=true/input=false,
`nativeConstruction` keyABSENT and lastAction native_construction_recovery_commit.
Receipt: `native-calibration-operator/native-calibration-recover-20261022T200732651521Z-481965-9e546958/receipt.json`;
parent proof: `closed-chat-world-implementation/parent-recovery91-verification.json`.
Resource assessment remains target_exceeded: construction12,779,520B within128MiB,
updates73,740,288B exceeds16MiB. Native validity is not a performance-target pass.

Two fresh post-recovery ordinary frames boot1792699669-261365 seq77->79 verify
stationary Arthur/Stormwind build70450/validmovementbindings/AHclosed/noactive/
pending0/native-normal/controlsUP/currentidentity+pins. GUI owner is proceeding
with the reviewed readiness-only input rehearsal, staged before public resume;
reuse matching auto-started input op, don't duplicate it. Do not rerun mutating
native preflight or restart with native proof already valid. No live input readiness
or human acceptance has yet been established. After calibration flow the current
loaded ACK list is empty; separately retained exact286 upload/ACK proof remains
valid. Next nominal due20:06:09 is already passed; retain actual overrun and restore
assisted collection after operation terminal and cleanup. User remains AWAY.

**Previous scan boundary20:02 UTC:** Assisted286 is completed, saved, uploaded and
exact-loaded ACK/pending0 verified. Actual start19:51:09 (`1792698669`), finish
19:59:13 (`1792699153`),428 attempts/zero failures/727 rows, UID
`beta-normal-alliance-1792698669-Arthur-7290`. Original226875-byte SavedVariables
SHA`4064f8f402ce0920718058c7f98365fd8c1333f4d7103ccbc2abf55fb9943843`.
Companion timestamp1792699216=20:00:16 UTC,63s after finish. Loaded ACK verified
20:00:47; parent independently decoded original PNG boot1792699238-294888 seq7
and checked original bytes. Proof:
`scan286-postprocess-stage/scan285-save-upload-ack-20261022T195955811091Z/parent-loaded-ack-verification.json`
under assisted-collection-luna-20261021; the reused folder name does not identify
the scan. Actual285->286 start gap3294s(54m54); neither900s cadence nor60s upload
qualification is claimed. Zero autonomous cycles qualify.

Two fresh post-ACK frames verify ordinary state/complete movement bindings
(moveForward=W)/speed0/pending0/exact286loaded/controlsUP/current identity+pins,
public PAUSED89/native=false/input=false/opidle/checkpoint keyABSENT.
The Agent.lua invalid moveForward message visible in earlier post-save chat is
historical; actual fresh native snapshots are valid. Do not change user bindings
or weaken the publisher based on that retained log line. Proof:
`scan286-postack-readonly-gate-20261022T2001Z/receipt.json`.

GUI owner now owns the staged mandatory mutating control-preflight89, actual
resume/full100-update103-call native measurement, pause/canonical recovery if valid
checkpoint present, ordinary/checkpoint keyABSENT, then ONE reviewed readiness-only
input rehearsal. User AWAY: no human/fakehuman events. At actual matching ready+
visible owned GTK use one public pause and wait for actual same input-operation
terminal plus window/process cleanup before restoring collection. Poller is
`scan285-calibration-rehearsal-stage-20261022T1900Z/readiness_rehearsal_poller.py`,
SHA959fbbcb0cbd6e4e72175d3d937cb9a01edb7ad57fc95982507b5e727d5ae374,
Sol READY. Next nominal scan due20:06:09; record actual proof overrun rather than
interrupting a running owned proof or claiming cadence. Native/input/live readiness
remain unproven at this boundary. Do not restart the daemon gratuitously.

**Pre-scan recovery chronology (19:39 UTC):** Canonical recover89 SUCCEEDED with the
reviewed helper585b005b. It verified exact `/reload` before Return, crossed an
ordinary reload boundary and committed recovery. Parent independently checked its
receipt and durable journal: PAUSED89/native=false/input=false/opidle,
`nativeConstruction` keyABSENT, lastAction native_construction_recovery_commit.
Receipt: `native-calibration-operator/native-calibration-recover-20261022T193913274925Z-3877195-ecb63434/receipt.json`;
parent proof: `calibration-resume-20261021/closed-chat-world-implementation/parent-recovery89-verification.json`.
Do not repeat recovery or restart the daemon. GUI owner is restoring286 first;
no start confirmed19:46. Fresh stationary Stormwind scene/pending0/loaded285 ACK
verified, Jaxon reselected via exact guarded `/targetexact Auctioneer Jaxon`.
One adapted range helper refused before input on obsolete hardcoded pins; corrected
helper then succeeded19:45:45: literal interaction flags1/2/3/4 all true,
Jaxon target visible, chat/AHclosed/speed0/pending0. Game displayed "World refresh
in 5 Minutes"; preserve interrupted partial data if maintenance cuts the new sweep
short, then normal cached reconnect/re-entry is authorized. Conditional binding and
one interaction are next. Update remaining helper dependencies from accepted pin
receipts offline before dispatch rather than discovering one stale pin per action.

**Last completed sweep:**285 finished19:05:02 UTC, UID
`beta-normal-alliance-1792695375-Arthur-9733`,428 attempts/zero failures/793 rows.
Original230873-byte SavedVariables SHA
`20193ccfc3c0743093f817b9382a64589860fb71c1f21cb1f74d450f9b33a6a2`.
Companion upload timestamp1792695987=19:06:27 UTC,85s after finish; later observation
time is separate. Exact loaded ACK/pending0 verified independently from retained
PNG and original bytes. Proof in
`scan285-postprocess-stage/scan285-save-upload-ack-20261022T190607790164Z/`.
Cadence is interrupted; zero autonomous cycles qualified.

**Closed-editor repair installed and pushed9df2091:** Sol READY, helper SHA
`585b005baa608ec01c2ba4e8a548854ef998da090383302ba13b8f10fbbeba0a`, installed19:26.
Transparent editor chrome contrast replaces absolute world-background luminance;
active-state refusal and exact typed-command OCR/Return ordering remain. Both actual
failed crops replay through guarded `_chat`. Full module:126 PASS/1 FAIL in848.40s,
sole failure the pre-existing RGB-versus-L assertion collected before correction.
Final focused21 PASS/106 deselected includes that corrected assertion and actual OCR;
Ruff/diff checks PASS. No second full run for the test-only correction.
Private exact review/report and source/test/fixture hashes are in
`calibration-resume-20261021/closed-chat-world-implementation/`. Helper pin is
receipt-only; promotion preserved daemon PID1812097 and valid checkpoint89 without
restart. Plan: [closed-editor repair](../.archive/PLAN-closed-chat-world-background-20261022.md).

**Resolved UI obstruction:** Fresh19:27 scene showed in-game Game Menu plus empty
focused Say editor. Raw XTEST Escape19:30 had no immediate observed effect; later
fresh frame showed chat inactive but menu remained. Exact XGetInputFocus and
_NET_ACTIVE_WINDOW agreed with the verified game. One owned FixedInput.key_escape
with production graphical environment19:38 dismissed the menu, with two advancing
frames and controls UP verified. Receipt:
`closed-chat-world-implementation/recover89-owned-escape-20261022T193809Z/receipt.json`.
Do not infer the earlier cause solely from an unset worker shell environment.
An offline audit found full-module tests use private Xvfb/D-Bus and recorder tools;
no actual host-game XTEST/uinput path was found.

After286 scan/save/upload/exact ACK, native/readiness rehearsal follows in an
interscan window. Final poller/actual-entry fixture audit is Sol READY at
poller959fbbcb, harness48a93bf6, receipt3e251590 using retained input87
stats/tree/xprop and actual daemon readiness serialization. No live readiness or
human qualification is claimed; user remains AWAY.

**Current collection (2026-10-22 18:59 UTC):** Assisted285 actually started
18:56:15 UTC (`startedAt=1792695375`), due19:11:15 (`dueAt=1792696275`).
Parent independently decoded its retained start PNG: AHopen/item phase/ordinal1,
speed0/pending0 and exact284 loaded ACK. All interaction keys released. Evidence:
`assisted-collection-luna-20261021/scan285-interaction-20261022T1852Z/`, including
`parent-start-verification.json`. Actual284->285 start gap3187s (53m7); this is
not900s cadence qualification. Zero autonomous cycles qualify. Sole GUI owner
`/root/luna_assisted_scanner` is watching285; do not interrupt the active sweep
or run binding cleanup during it. Keep the authorized session-only CTRL-F12
binding for assisted interaction; no SaveBindings.

**Latest user instruction:** User confirmed intervening Arthur movement was
intentional, then said: "nvm Im stepping away, just make sure the calibration
works when I get back, keep scanning". User is AWAY. Do not request genuine
human samples until they return. GUI owner owns complete scan/save/upload/exact
ACK/native/readiness/collection outcome; root must not capture/input concurrently.
Keep repeating assisted900s collection; do not stop after one/three cycles.
Honor new user takeover immediately.

**Installed repair:** GTK root-child fix is committed/pushed as7788c4b and Sol
READY at scoped diffSHA
`a2e697d7308f2ffa2950aef0c7567bbda0cdf0532b1e14636407ea35903ffd0c`.
Root restarted crowley-session once18:25 UTC: PID3787948->1812097; fresh initialized
PAUSED89/native=false/input=false/operationidle/journal `nativeConstruction`
keyABSENT. No native89 measurement or new input attempt has started. Installed
calibration.py=`31d421b232ef4b84378fcc43f9856e59c8391f6782f0b69432984ea70ec98ebf`;
driver.py=`0600af7a484fac896a16fdcef034f1731fed7c7d386bbb3d67f233d1893440cd`.
Private `calibration-resume-20261021/gtk-unframed-implementation/` contains exact
installation/restart proofs, Sol review, parent checks and real private-Xvfb proof.
Final-source suite243 PASS316.34s; parent20 focused+54 diagnostic/driver checks
PASS; implementer21 focused PASS; Ruff check/format/diff check PASS. No human
readiness or completed input calibration has ever occurred.

**Authorized next chain:** After285 terminal/original save/upload/exact loaded ACK,
use interscan time for fresh identity/scene/held/source gates, mandatory mutating
control-preflight, resume/full100-update/103-call native measurement, pause/
canonical recovery and checkpoint keyABSENT. While user is away run ONE explicitly
readiness-only input rehearsal: stage public-status polling before input-calibrate,
retain matching running input readiness plus visibly mapped owned GTK, then
public-pause/revoke without genuine input and wait for actual terminal cleanup
(human wait may retain its existing120s bound). Never claim that rehearsal as
input qualification. On pre-readiness failure retain exact diagnostic, no unchanged
retry. Restore ordinary assisted collection and record any actual overrun of
nextdue; do not interrupt proof or fabricate cadence. Sol is reviewing this small
public API/cancellation sequence offline; GUI owner supplies staged helper paths.

**284 preserved and acknowledged:** UID
`beta-normal-alliance-1792692188-Arthur-8390`, start18:03:08, finish18:12:43 UTC,
428 attempts/2 failures/1195 rows. Original251877-byte SavedVariables SHA
`076942bc871c587f18f6d937e1168eb61592be45653971506876465bdb4a7433` is preserved.
Companion uploaded18:13:20; loaded-HUD exact ACK/pending0 verified18:34:30 at
boot`1792694066-508586`,seq3, AHclosed/noactive. Parent independently decoded
retained PNG and verified original bytes. Private receipt and parent proof:
`assisted-collection-luna-20261021/scan284-ack-continuation-20261022T183416955877Z/`.
The repaired ACK helper passed14 offline cases and Sol review (parent independently
reproduced13 before its final diagnostic-only identity correction). Actual live
continuation typed exact `/reload` and Return from observed focused empty chat.
Reuse these proven helpers; private wrapper defects caused a real collection gap.

**Repaired assumption:** Input87 failed17:40:41 before readiness. Alive-window
observations showed owned focused/viewable480x240 GTK at1440,32, direct parent
root0x374, no frame extents, Motif decorations0 and one advertised1x1 InputOnly
helper. Old code required a reparented frame. Production now explicitly pins
root-child layout and advertised helper identity; only the client is an event
target. Root/helper/siblings remain excluded. Missing helper publication is
startup-pending within10s; present-invalid facts and post-ready loss fail hard.
Private Xvfb proof exercises real GTK/verifier/ticket/focus with unchanged pointer,
but does not establish live target-hit/human acceptance. Plan:
[GTK repair](../.archive/PLAN-gtk-unframed-calibration-20261022.md). Retained live
facts: `calibration-retry-20261022/input87-observed-failure-20261022T1740Z/`.

The following paragraphs retain earlier chronology; the current state above
supersedes their generations, availability holds, deployment and pending statements.

**Latest live handover (2026-10-22 17:29 UTC):** User moved Arthur to Stormwind
and explicitly returned control with "i am in stormwind, lets calibrate".
That supersedes the availability hold and movement takeover below. Sole GUI
owner `/root/luna_assisted_scanner` was woken by follow-up and verified running.
Fresh scene verifies stationary Arthur in Trade District, build70450, unchanged
process/window identity, all keys/buttons released, AH/chat closed, pending0,
scan283 exact ACK loaded. Native83 remains valid; do not restart gratuitously.

The prior fresh connection attempt85 failed before readiness at17:19:41 UTC:
final client xprop timed out with2.9ms left of the shared10s GTK startup deadline.
It does not establish why earlier readiness polls remained pending. Diagnostic
and post-cleanup observation are preserved under
`calibration-retry-20261022/input-calibration-ready-20261022T1717Z-3/`.
Public pause returned PAUSED86/native=true/input=false, checkpoint keyABSENT.
W was held intentionally during the user's movement; never release user-owned
keys or misclassify that movement as a stuck input.

Scan283 completed428 attempts/zero failures/1546 rows and exact loaded ACK;
no284 began. User is currently connected/available. Owner is authorized for ONE
observed input attempt with a bounded read-only sampler staged BEFORE startup
to retain owned GTK properties/geometry while alive, using actual generations.
No source/config/deadline changes or blind retries. Alert user only at matching
running input readiness AND visible owned prompt. Preserve failure facts if it
fails; do not infer startup cause from post-cleanup BadWindow. The state below
is earlier chronology and is superseded by this handover.

**Latest user instruction:** The user returned and requested calibration after the
next scan. That supersedes the previous AWAY hold. Luna remains the sole GUI
owner; root must not capture or input concurrently. Human calibration has not
reached readiness. Never ask for human events before actual readiness.

**Current cutover (14:32 UTC):** Placement repair passed final Sol review at scoped
diffSHA`0bc394c624c431e7101aeaaf9f4f0e0cf88be9e137c2dbe9963167275c866d67`.
An undecorated GTK client now has a private actual-constructor/guarded-focus proof
for unchanged(1809,43) inside measured[1440,0,480,240]; placement-disabled negative
and historical out-of-client refusal remain covered. Private Xvfb geometry proof
does not establish live Mutter/certified-hit acceptance. Production preflight
requires actual certified hit AND measured client bounds before synthetic probes.
Read-only keyboard/device profiles may precede this guard; input dispatch may not.
Parent independently passed11 GTK/workflow/producer tests and9 diagnostic tests.
The installed full native-regression/diagnostic/real-producer run subsequently
passed181 tests in285.44s; Ruff check/format and diff-check also passed.
Sol READY, no findings. Reviewed calibration.py is now
`281ddffcb34ac928e5d144788a87652afe11d644c91d59ab8eb8377e8e115069`;
driver35677b remains unchanged. Exact reviewed three-file promotion and restart
proofs are in `calibration-resume-20261021/input-pointer-origin-implementation/`
(`sol-placement-review.md`, `parent-placement-installation.json`,
`parent-placement-service-restart.json`).

Scan275 is preserved/uploaded/exact-loaded-ACK verified: UID
`beta-normal-alliance-1792678774-Arthur-9084`,428/428,zero failures,1517 rows,
finished14:27:33,received14:28:08.397681 UTC (35.40s). Parent read-only DB counts
and independently decoded retained loaded-ACK PNG agree; private proof:
`assisted-collection-luna-20261021/848-scan275-postprocess/scan275-save-upload-ack-20261022T142749711585Z/parent-scan275-loaded-ack-verification.json`.
No276 started. GUI owner completed its scan task and was explicitly woken with a
follow-up task after deployment; verified running. Service restart14:32:34:
PID2931936->3787948, fresh public PAUSED82/nativefalse/inputfalse/opidle,
journal checkpoint keyABSENT. Mandatory preflight82 and full native83 subsequently
passed; public pause84/canonical recovery84 succeeded. Fresh journal independently
verified14:43:29 UTC is PAUSED84/native=true/input=false/checkpoint keyABSENT,
lastAction native_construction_recovery_commit. Native83 resource growth was
1,159,168B construction (within128MiB),61,980,672B updates (exceeds16MiB);
this is not a performance-target or autonomous qualification pass.
Native proof:
`native-calibration-operator/native-calibration-measure-deferred-20261022T143902649049Z-3967959-680997c0/receipt.json`
under the private Crowley state root. Reviewed placement repair is committed and
pushed as8e858ce; prior origin repair aa8b43b. Fresh user-availability question
is PENDING; **do not launch input-calibrate/timed human window until answered**.
GUI owner is restoring assisted276, then must keep repeating900s assisted cycles
until explicit new user update or real blocker; do not stop after one/three cycles.
Actual276 start has not yet been reported. Keep the human question pending and
retain native83 evidence without gratuitous restart. Later human input admission
must use fresh actual state/generation after a completed scan. Zero autonomous
cycles qualified; live Mutter/certified-hit placement remains pending that stage.

The following paragraphs retain the two earlier attempts and repair evidence;
the current cutover above supersedes their state/generation/hold statements.

Scan274 completed13:38:05 UTC: UID`beta-normal-alliance-1792675804-Arthur-7101`,
428/428 attempted, zero failures,1471 rows. Read-only DB confirms428 observations/
1471 rows received13:38:37.077966 UTC (32.08s after finish). Luna preserved original
SavedVariables and verified exact loaded ACK/pending0/AHclosed. Parent independently
decoded the retained screenshot and matched the DB counts; private proof:
`assisted-collection-luna-20261021/832-scan274-postprocess/scan274-save-upload-ack-20261022T133820858870Z/parent-scan274-loaded-ack-verification.json`.

Fresh Sol compatibility review accepted MAIN82857ee. Mandatory control-preflight
at PAUSED72 succeeded and recovered ordinarily. Resume73/full native measurement
succeeded13:44:07 UTC, native=true/input=false. Construction growth14,422,016B
met128MiB target; update growth57,204,736B exceeded16MiB target. This is a recorded
resource-target failure, not a waived calibration guard. Pause74/canonical recovery
succeeded; journal `nativeConstruction` key was ABSENT before input admission.

Resume75/input-calibrate failed before readiness at13:45:47 UTC:
`calibration pointer origin is outside the owned target`, stage=synthetic,
readinessPublished=false. User input was never requested. Bounded private diagnostic:
`~/.local/state/crowley/input-calibration-diagnostics/latest-pre-human-failure.json`
(SHA256`ddd9cfe7420cd81cc678e812810214b1a0118629ce5bae0585b7a3a3dc0391f1`).
It records target geometry[1440,71,480,240] and certified owned ancestry, but lacks
the actual rejected pointer-query tuple; do not invent it. Immutable copy:
`calibration-resume-20261021/input75-origin-failure/pre-human-failure.json`.
The exact historical failing conjunct remains unknown.

**Reviewed origin repair installed; one fresh retry authorized.** The producer
incorrectly required an exact top-level hit XID while its ticket/seal permits
the certified target, descendants and managed frame. It now uses the ticket's
exact set while retaining measured client bounds, endpoint equality, nonzero
motion, ownership/focus/Guardian/cadence. Failure evidence retains actual queried
origin/post coordinates, hit XID and each predicate through daemon JSON persistence.
No GTK placement assumption was changed. Luna178 tests passed before a test-only
persistence correction; corrected diagnostics9 passed. Parent independently
reproduced8 producer regressions,9 diagnostics and1 real producer/Guardian test;
installed MAIN8+9 tests also passed. Ruff/format/diff checks passed. Sol READY,
no outstanding findings, reviewed diffSHA
`45532ff721eedf40212b813417e4ba7eba00a7df2c6a575ef8f9d9086ed07bf8`.
Private review/install/restart proofs:
`calibration-resume-20261021/input-pointer-origin-implementation/`.

At the safe boundary no scan275 had started: AHclosed/noactive/pending0,
ordinary native phase; temporary CTRL-F12 was set session-only, never saved.
Root promoted the four exact reviewed files and restarted the service once;
PID2931936, fresh public PAUSED77/nativefalse/inputfalse/operationidle,
checkpoint keyABSENT verified14:02:03 UTC. User freshly confirmed connected and
available. GUI owner is authorized to repeat the full guarded preflight/native/
recovery/input sequence using actual generations, immediately alert root at
matching readiness plus visible GTK. Never fabricate human input. On failure
preserve the new diagnostic, restore ordinary collection, and report the exact
new tuple/predicate before further repair. Do not blindly repeat.

**Retry result: native78 PASS, input80 refused on proven geometry.** Mandatory
preflight77 and full native78 passed; canonical pause79/recovery79 restored
ordinary state/keyABSENT. Input80 failed before readiness14:10:08 UTC. Actual
origin(1809,43), hitXID73400323 was certified, but GTK client was
[1440,71,480,240]: `certifiedHitWindow=true`, `insideTargetGeometry=false`,
`nonzeroDisplacement=true`. The origin repair worked; the pointer sat above
the client area and the bounds guard correctly refused. No human prompt occurred.
Immutable diagnostic and independent parent predicate verification:
`calibration-retry-20261022-1402/input80-origin-failure/`.

Public pause returned PAUSED81/native=true/input=false, checkpoint keyABSENT;
fresh14:11:46 scene was ordinary, AHclosed/noactive/pending0/speed0 and GTKgone.
No scan275 had begun at that failure boundary. Root subsequently resumed assisted
collection during placement repair/review under
`../.archive/PLAN-input-target-placement-20261022.md`. Scan275 started14:19:34 UTC
(1792678774),due14:34:34 UTC (1792679674),428 planned,AHopen/pending0/speed0.
The274→275 start interval is2970s (49m30s), including the calibration hold and
repairs; this is not900s cadence qualification. GUI owner must finish/save/upload/
exact-ACK275 before closing AH for deployment; never interrupt it.
Luna owns offline implementation; Sol reviews. No further live retry is approved
until that review passes. Current user is connected/available. Input and autonomous
qualification remain pending. Native78 resource update growth60,243,968B also
exceeded16MiB target.

The following scan237–241 details describe the earlier collection restart;
Luna continued assisted scans overnight through274. These are not autonomous
qualification: three new unattended900s cycles remain unproven.

The user resumed game operation at 02:46 UTC on 2026-10-22 and confirmed RDP
availability then. `/root/luna_assisted_scanner` was woken with a follow-up task
and verified running. It is the sole GUI owner; root must not capture or input
concurrently. The user has now returned for calibration; reconfirm availability
if the repair outlasts this session before starting a new timed human prompt.

**Collection continues under Luna supervision.** Scan241 began04:41:18 UTC
(startedAt1792644078),nextdue04:56:18 UTC (1792644978),pending0 and prior exact
scan240 ACK loaded. It started19s late; the preceding scan240 started13s late.
These remain assisted cycles, not autonomous qualification.

Four resumed sweeps237–240 are stored in DB:1712 attempted items,4201 rows total.
Rows per sweep:1046/1039/1047/1069. Only scan238 had a failure: one queried item6361
with query_timeout; all other attempts were ok. All four uploads arrived within
60s of actual finish. Parent independently verified original format3/digest/plan/
counts and retained HUD loaded ACKs for237–239; Luna verified scan240's original
save/upload/exact loaded ACK and parent confirmed its DB428 observations/1069 rows.
Last stored UID`beta-normal-alliance-1792643159-Arthur-5376` ran04:25:59–04:34:01 UTC,
received04:34:50.391049 UTC. Its ACK receipt is
`assisted-collection-luna-20261021/569-scan240-postprocess/scan240-save-upload-ack-20261022T043431968606Z/receipt.json`.
The initial recovery intervals were1095s/979s; subsequent intervals improved to
913s/919s. Carry actual startedAt+900 through reload even if addon dueAt resets.

Parent verification for scan238 and both237/238 loaded ACKs:
`assisted-collection-luna-20261021/553-scan238-postprocess/scan238-save-upload-ack-20261022T040332496592Z/parent-two-sweeps-loaded-ack-verification.json`.
Scan239's zero-failure original and exact loaded ACK:
`assisted-collection-luna-20261021/562-scan239-postprocess/scan239-save-upload-ack-20261022T041901912534Z/parent-third-sweep-verification.json`.
Never interrupt an active sweep for ACK or calibration. Continue collecting until
explicit user takeover/stop or a real blocker; completing three cycles is no stop rule.

Scan237, UID `beta-normal-alliance-1792640172-Arthur-4663`, ran 03:36:12–03:44:22
UTC: 428 attempted, zero failures, 1046 rows, 423 full/5 bounded, all428 reasons ok.
Server receipt was 03:44:57.060933 UTC (35.06s after finish). Parent validated the
original format3 envelope, matched logical digest/plan/counts to read-only DB,
and compared all428 stored observation JSON records plus1046 captured-row
JSON/quantity/unit-price columns: exactly equal, including26 stacked-item rows.
Original SavedVariables SHA256:
`0b54f4af1a83821ebc420a21177f4d7db3ec6845da2e7393f3bbd10dac00c31a`.
Private proofs are under `assisted-collection-luna-20261021/543-scan237-exact-ack-diagnostic/`:
`parent-format3-upload-verification.json` and `parent-stored-prices-verification.json`.

The exact237/238 server ACKs were independently proven loaded as described above.
Do not reload an active sweep for ACK. Never claim a completed cycle from upload
or Data.lua publication alone; the client must consume the exact UID.
The old session reader rejected the producer's new `referenceItemIDs` field;
Luna fix d78510b requires the current five-field schema and canonical full-catalog
reference IDs, preserving strict unknown-field/ACK/plan validation. Sol READY;
parent4 focused tests and retained actual Data.lua acceptance passed. Fixture
closure e58d8f8 is also Sol READY; Luna5 targeted lifecycle/ACK/reconcile tests
passed (80.13s), parent2 targeted integration tests passed. Both commits pushed.

**Expanded API probe completed.** P2 merged at05392bf (parent9 focused tests passed).
Luna loaded it with a guarded preparatory reload, submitted `/crowley probe` once,
then saved with a verified reload. Probe1792639338 (03:22:18 UTC) is in client_probes.
Parent compared the complete saved JSON against DB: exactly equal, including40
boolean globals, six boolean frame checks and namespace function inventories.
Private proof: `assisted-collection-luna-20261021/530-saving-reload-probe-check/parent-probe-verification.json`.
Presence does not prove usable return contracts; absent load-on-demand frames do
not establish unavailable APIs. No trade actions were performed.

**Service and live identity.** Before any new sweep, root restarted
`crowley-session.service` at02:54:19 UTC, PID3087152 ->1821334. It initialized
PAUSED generation71, native/input false, operation idle, nativeConstruction key
ABSENT. Read actual generations/checkpoint membership before acting. This loaded
format3 support347ab56 (parent10 focused format2/3 tests passed). Running server
also explicitly reports accepted formats[2,3]. After the reviewed gesture
integration, root restarted again: PID1821334 ->676938,
PAUSED **generation72**, native/input false, operation idle, nativeConstruction key
ABSENT, lastAction restart_invalidate_calibration. This process loads the strict
ACK reader and reviewed gesture code. Read fresh actual generations before commands.
The addon symlinks to MAIN's `addon/Crowley`. Current client is PID1532084,
start44691603, Arthur/Ironforge, build70450/version1.60.1/interface16001. Re-resolve
identity before input; do not reuse old PID2792826 or earlier fingerprint evidence.

**Gesture repair installed; current live retry described above.** Shared
seeded curved Fitts-timed movement, submovements, endpoint scatter/receipts and a
fixed crash-safe >=1.0s click gate now cover native bootstrap/parking and runtime
X11 actions. Raw click branches refuse before input. Existing Guardian, one-use
anchors, five-second click evidence, ten-second constructor, owned cleanup and
native103 protocol remain enforced. Rate timestamps are conservative post-click
ACK times, not hardware-down timestamps.

Luna's original gesture implementation in
`~/.cache/crowley/worktrees/native-human-click-20261022` passed final Sol code review
and was promoted byte-for-byte. The origin repair above supersedes its driver
and calibration pins. Current production SHA:

- driver.py: `35677b166b153f2349fb7abbce7c482d7537cad874cdae5b903abaa99b99a9a5`
- calibration.py: `281ddffcb34ac928e5d144788a87652afe11d644c91d59ab8eb8377e8e115069`
- pointer_execution.py: `a116142fcd04c319681c957df9891f83bcda126a9ee338047444d1b5da408b30`
- native_calibration_operator.py: `807d7d80614a9410b372674abc311706bbfe3b5d907e1ecd8ed7df42136bad30`

Verification: worker full scoped175 passed/one pre-existing RGB-vs-L retained-crop
assertion failure independently reproduced on clean2e48728. After the final X11
adapter planning fix, pointer/driver51 passed, strict-current-ACK three-cycle real
socket lifecycle passed (68.54s), actual native103 success passed (148.30s).
Parent independently passed30 executor/shared-pointer tests and45 driver tests;
installed MAIN51 focused driver/ACK/reconciliation tests passed (9.91s), Ruff/check
format and diff-check passed. All seven installed files match Sol's final hashes.
Private closure: `calibration-resume-20261021/parent-human-gesture-installation-closure.json`
(SHA`d221ebe57b2bb4f62c172f5f51cef5623982cac1e3aa5ba1a385baddb4ce21e6`).
Final review: `calibration-resume-20261021/sol-native-human-click-final-code-review.md`.
Plan: `../.archive/PLAN-native-human-click-20261022.md`, including runtime test-state
isolation addendum. The prior provisional driver020950a4 approval is superseded.

No live native attempt or human prompt was started during the user's absence.
The user-return attempts and current generations are recorded above;
**zero autonomous cycles are qualified**. Require actual matching input readiness
and visible owned prompt before asking for human events. Final acceptance is three
consecutive unattended900s full save/upload/exact loaded-ACK/reopen cycles.

Shared data-agent coordination: `../.archive/trade-api-probe/LIVE-DRIVER-STATUS.md`.
Everything below this point is historical and must not override the current state.

**HISTORICAL USER HOLD (superseded by the resume above):** User reported the game was
still not playable and will tell us when it is ready. Stop reconnect attempts,
screen polling, game input and calibration until that update. The attempted
stale-modal dismissal refused at its PID/start guard before capture or input;
the current game identity is unconfirmed. `/root/luna_assisted_scanner` is now
interrupted. Resume only on a new user update with a follow-up task and fresh
identity/scene checks; the older21:00 UTC not-before time is no longer a trigger.

User connected through RDP for the planned 11:30 AM Chicago (16:30 UTC)
calibration, which could not finish before the realm outage. The user now thinks
the realm will remain down until **4 PM Chicago today (21:00 UTC)**; this is a
tentative user estimate, not verified server availability. At17:07 UTC Luna
stopped all reconnect input and screen polling, reaped helpers and released input.
`/root/luna_assisted_scanner` completed its outage-watch task; no GUI worker is
currently operating. Do not keep polling during this hold. At/after21:00 UTC or
an earlier user update, wake that worker with a follow-up task and verify it is
running before expecting recovery. First check actual realm/scene availability,
then restore authorized Normal/Arthur assisted900-second collection. Reconfirm
human availability before a new expiring calibration prompt.
Appointment plan committed at `abc4278`:
[runbook](../.archive/PLAN-calibration-run-20261021-1130.md), reviewed READY by Sol
at SHA91bc4852c66c2674e19732e4dbc910410182f777877f31800fd77659abacd945.
The private exact command sequence is `calibration-resume-20261021/sol-appointment-review.md`.

Assisted collection continued through cycle235 (428 attempted, zero failures,
1768 rows, original upload/exact loaded ACK/AH reopen). Cycle236 started16:23:03Z
and ended early16:27:01Z because AH closed. UID
`beta-normal-alliance-1792599783-Arthur-8176`: 215 attempted,1093 rows; actual
coverage201full/13bounded/1incomplete/213unqueried. Reasons214ok/214ah_closed;
this is one interrupted query and213 unqueried entries, not214 query timeouts.
Original payload was preserved/uploaded and exact loaded ACK verified. AH was
held closed for the authorized dedicated calibration window.

Fresh preflight at16:32:54Z refused before any game input because the empty-chat
classifier returned unknown. Actual closed crop medians96/63/92/96 exceeded two
inactive background bands by3/2; no slash OCR or synthetic XI2 step was reached.
A single bounded D pulse returned the character toward a known working pose;
after settling at(-4949.6,-901.0), the actual production classifier accepted the
new crop (medians67/34/62/67). Input was explicitly released and speed0 verified.
No source, OCR rule, admission guard, config or validator was changed.

That refused preflight created a valid generation70 preflight/recovery_required
checkpoint. Canonical public recovery subsequently SUCCEEDED at16:38 UTC:
private receipt `native-calibration-operator/native-calibration-recover-20261021T163759848559Z-1598579-c0eb6488/receipt.json`.
Root independently read its success receipt and journal at16:38:32Z: PAUSED70,
lastAction native_construction_recovery_commit, **nativeConstruction key ABSENT**.
Explicit JSON null is malformed; always check key membership, not `.get()`.
The separate prior owner64 checkpoint already cleared at10:08 UTC. Never recover
either checkpoint again from an older handoff. Re-read actual state before acting.

At a fresh16:37:02Z scene the game showed live SERVER shutdown2:00/1:45 countdown
messages. The normal native measurement historically takes157–161seconds, so root
held the native100 attempt rather than start it across that imminent shutdown.
**Native and input calibration remain false; no human prompt was started and no
autonomous cycle is qualified.** Finish ordinary recovery and retain original data;
when the server is actually available, restore normal cached connection/assisted
collection and coordinate the existing reviewed calibration sequence with the user.
The game actually disconnected at16:39–16:40 UTC (WOW51900319). Cached reconnect
advanced through the authorized Normal ruleset; the16:46:46Z receipt
`assisted-collection-luna-20261021/505-confirm-normal/receipt.json` then confirmed
**No realms are currently available (WOW51900309)**. This is the current external
blocker. Do not infer a server return time. The latest17:07 UTC read-only frame
still showed the same error; current GUI hold supersedes earlier reconnect loops.
Resume normal cached recovery and assisted collection after that hold. Reconfirm
user availability before opening an expiring human-input window; do not launch it
while the parent/user is away. Root must not capture/input concurrently.

Private current operation notes, appointment and progress are under
`executor-evidence/assisted-collection-luna-20261021/`; raw receipts outrank stale
sidecar fields. Offline closed-editor analysis is
`calibration-resume-20261021/closed-editor-preflight-diagnosis.md`.
Its candidate future classifier change is diagnosis only, not installed code.

## Objective and completion criteria

Build the launch-ready Crowley auction-house workflow for WoW Forever build70450.
The [watchlist](WATCHLIST.md) requires428 observations. Retain the cheapest20
**distinct unit-price levels**, all ties at each selected level, and explicit
missing/unknown values. Exactly20 levels without a higher witness is full;
never mix houses or item identities. Disappearance remains an uncalibrated
activity proxy, not confirmed sales. Buying, posting and cancelling are outside
this task. Recipe economics and trading/investment strategies follow collection.

A full cycle saves the original game payload, uploads it, receives the exact
server ACK, reloads it and verifies the reopened AH. Operational qualification
requires native calibration/recovery, genuine human input calibration and three
**autonomous900-second** full cycles. Current cycles are operator-assisted;
**zero autonomous qualification cycles are counted**.

## Authority and ownership

- Origin: https://github.com/p-kjdeprow/forever_tradecraft . Routine recovery,
  installation, fixes, commits and pushes remain authorized. The user revoked
  AGENTS.md rules. Keep progressing until requirements are met.
- User now requires OpenAI Luna implementation/game control and Sol review;
  Anthropic quota is offline. Opus is no longer a gate for new work. Preserve
  historical actual Opus evidence without claiming any new review occurred.
- Sole live GUI owner: `/root/luna_assisted_scanner`. Root may inspect retained
  artifacts but must not operate/capture/input the GUI concurrently.
- Arthur is at Ironforge AH. User now authorizes Luna-assisted scanning; a bounded
  safe approach to the auctioneer is allowed when fresh scene evidence requires it.
  No trading or general navigation. Standard Wine desktop; Sunshine disabled.
- Implementation worker: `/root/luna_rust_matcher`; latest hover candidate in
  `/home/dev/.cache/crowley/worktrees/native-control-hover-20261020` is frozen and
  installed at its final two-file hashes. Earlier Rust observer worktrees remain
  frozen historical evidence; R4 passed parent/Sol/actual Opus review before
  installation. Do not confuse those approvals with the new Luna/Sol hover fix.
  Root owns docs, skills, final verification, installation and Git. Review worker:
  `/root/sol_final_composition_plan`.
- Communication: explain the overall autonomy objective, current milestone and
  remaining gates. User asked for clearer progress and less per-probe/tool noise.
- Never reset/stash/revert others or use `git add .`. Many untracked files are
  private. Stage only explicit reviewed files. No messages to outside parties.

## Live state and collection

**Current priority: Luna-assisted collection every900seconds while the unattended
controller is repaired.** User explicitly said not to pause scanning and authorized
Luna to direct the scanner until the fix. This supersedes the previous GUI hold
and calibration-first handoff. Sole GUI owner `/root/luna_assisted_scanner` is active with fresh task context;
root must not capture or dispatch input concurrently. Start a fresh428-observation
scan, preserve its original SavedVariables, upload, verify exact loaded ACK and
reopen AH; continue on the addon900-second schedule.

**ASSISTED COLLECTION RESTORED: full scan180 verified; scan181 started900seconds later.**
Luna must continue900-second assisted cycles until explicit user/parent handoff or
an actual blocker; three cycles are a minimum validation target, not a stop rule.

Scan180 UID `beta-normal-alliance-1792547461-Arthur-9410`, actual start01:51:01Z,
finish01:59:05Z, all428 attempted, zero failures,1667 raw rows. Parent validated
original SavedVariablesSHA a95a53fb7c09adb2a9922368748c71285a48e1dca82e4ff9ab48bc6cb4836c5f,
logical digest against actual database row, and real loaded-ACK pixels:
[scan proof](../.archive/executor-review/build-70450-onehundredeighty-scan-parent-verification.json).
Coverage413full/15bounded; all428 reasonok. Server received02:01:16.400972Z,
**131.400972seconds after finish**, missing the60-second target. The private helper
first refused a wrong nested lastSaved path; it now uses observed top-level
lastSaved. Preserve actual lateness. Existing prior-start gap66433seconds is
recorded, not backfilled. No autonomous qualification cycle is counted.

Exact ACK loaded in a real new boot with pending0. Parent decoded the actual AH
reopen PNG at02:05:42 published wall time: normal0, inactivefence, speed0,
AHopen/scheduled and original dueAt1792548361:
[reopen proof](../.archive/executor-review/build-70450-onehundredeighty-ah-reopen-parent-verification.json).

Scan181 actual published startedAt1792548361 (02:06:01Z), exactly900seconds after
scan180; nextdue1792549261 (02:21:01Z). New sweep advanced ordinal19→34→140;
latest worker capture02:08:36Z reported AHopen/speed0/pending0/exact prior ACK.
[Retained PNG cadence proof](../.archive/executor-review/assisted-scan181-cadence-parent-verification.json)
validates CRC/payload and published start interval. The watcher omitted host
capture monotonic, so this proof explicitly makes no independent capture-freshness
attestation and substitutes no client uptime. Add actual capture start/return to
future watcher receipts without interrupting this sweep. `activeSweepId` remains
literally blank during real sweeps; completion requires a new saved UID.

Previous owner `/root/luna_live_recovery` is interrupted/held; no concurrent GUI
work. Root retained-image review found prior clicks hit names/posts/players.
Interact-With-Target was unbound; CTRL-F12 was measured empty, temporarily set to
INTERACTTARGET without SaveBindings, and read back. Current owner must restore
CTRL-F12 to empty before handback/exit. Owned reloads actually clear this temporary
binding; measure empty, reapply and verify before keyboard reopen as needed. Physical Control_L/F12 hold/release was
verified. The actual successful interaction required returning near the known
working Buckler pose: position(-4951.3003,-902.4000,0), fresh exact Buckler target,
literal range flags1/2/3/4 alltrue, then one physical chord. Earlier flags were
1true/2false/3false/4true; initial pose and forward movement remained out of reach.
Do not assign undocumented yard values to those flags. Use fresh observed safe
movement toward a reference world pose; old NPC pixel coordinates are stale.

Private action receipts and progress are under
`executor-evidence/assisted-collection-luna-20261021/` in private state. The owner
is running the scan181 watcher and staging its corrected save/upload/loadedACK/
reopen flow during the active sweep. Direct worker messages and hash-bound
receipts are authoritative; progress.json now carries actual observed capture UTC
and sequence. It previously lagged and must not replace raw evidence. Use unique per-action dirs/script hashes.

Literal command staging now uses bounded effect polling on advancing HUD frames;
initial frames after input could still report a partial/old editor state. Chat
text over128bytes deliberately publishes inactive/empty and must never be
submitted without exact proof. Prefer short bounded read-only queries.
Wayland clipboard providers need selection-readiness polling and must survive
multiple Wine/XWayland requests; installed manual warns --paste-once can fail.
Default wl-paste appends a newline, invalidating earlier byte-exact clipboard
claims; current corrected --no-newline reads and provider restoration are verified
in private receipts. No addon/decoder/ownership guard was relaxed for assistance.


Game and persistent Wine launcher are restored; Arthur is logged in at Ironforge
AH. ControllerPAUSED70/nativefalse/inputfalse remains appropriate for its
unqualified unattended path; it does not forbid explicitly authorized assisted
scans. Last handoff position(-4939.8003,-908.4000,0), speed/current0 on advancing
frames1009/1012/1014/1017/1019, normal0, AHclosed/pending0/fenceinactive and released
controls. Current GUI owner must revalidate identity/scene and actual NPC range;
old coordinates are not proof of present interaction range.
[Prior restoration proof](../.archive/executor-review/wow-restoration-handoff-parent-verification.json).

**OCR recognition repair installed:**
[Parent release proof](../.archive/executor-review/native-chat-ocr-release-parent-verification.json),
[bounded plan](../.archive/PLAN-native-chat-ocr-20261021.md).
The actual retained crop reproducibly read `lreload` with the old cursor probe45;
probe60 preserves `/reload` while removing the insertion cursor. Production uses
one preprocessing pipeline; exact command comparison and editor/ownership guards
remain unchanged. Luna implementation, parent22focused tests, Sol R1 READY/no
findings, then promoted-MAIN22tests passed at identical reviewed hashes. No daemon
restart, game reload, native/input attempt or durable-checkpoint change occurred.
Do not interrupt assisted collection to test recovery. Synthetic diagnostics are
installed but still await a fresh post-install attempt after canonical recovery.

[Checkpoint correction](../.archive/executor-review/native-checkpoint-status-correction-20261020.json):
public status DOES NOT expose nativeConstruction. Earlier post-native64
clear-checkpoint claims based on `.get(...)=None` were unproven. The durable
journal retains ownerGeneration64/phase recovery_required. Normal0 HUD proves
visible ordinary operation, not durable checkpoint completion. Preserve this
checkpoint and eventually finish canonical public recovery after reviewed repair.
The previous native57→canonical58 proof remains separate historical evidence.
Underlying synthetic event timeout68 needs a later instrumented attempt.
Zero autonomous cycles counted.

**Completed restoration and diagnostic installation:**
[Recovery proof](../.archive/executor-review/wow-runtime-restoration-parent-verification.json),
[installed diagnostic proof](../.archive/executor-review/input-calibration-diagnostics-release-parent-verification.json),
[local game setup](GAME_SETUP.md).
User confirmed another agent deleted Lutris/Wine files and authorized restoration.
Luna restored matching Wine11.16 staging plus DXVK2.6.2/vkd3d2.14/NVAPI0.9.0;
parent verified Wine archive against upstream SHA, current mapped preloader bytes,
and zero dangling DLL links in both system32/syswow64. Registry, addon and saved
variable backups are private. Existing game/prefix/account data were preserved;
cached Battle.net login worked. Arthur is back beside Auctioneer Buckler.

GamePID2792826/start34949911, fingerprint
`bf242eeac260a077173e9a0107c2646be9d07b1d78c54d2198a8bb196f9d2808`,
outerXID67108865/child60817450, measured1928x1092/1920x1080. Parent decoded five
ordinary frames96/101/105/109/114 and fresh pre-promotion419/423/428/432/436:
speed/current0, AHclosed, pending0, inactive fence and released controls. Prior
chat startup movement error is historical; fresh telemetry passed.

Desktop World of Warcraft entry now invokes `~/.local/bin/crowley-world-of-warcraft`
directly, using the recovered Wine runtime and existing cached Battle.net. It
checks exact process comm/Windowsargv0/UID/prefix before refusing duplicate clients.
Parent inspected exact real PID guard and launcher bytes; sh-n and desktop-file
validation passed, gtk-launch guard preserved process count1. Sol launcher review
READY, no findings, reportSHA
`3c26b5afd984ab148489b2fd4b9d5ae570759a1f2d50d460f83a797ffcf7b731`.
The deleted Lutris game database is bypassed by this persistent shortcut; do not
claim that database was recovered. Runtime files under Lutris directories remain
required dependencies even when using Wine directly; preserve them.

Input diagnostics candidatec26a844 was reviewed Luna/Sol R2 READY and parent89
checks passed; exact four reviewed files are now promoted to MAIN6f53cc5.
[Plan](../.archive/PLAN-input-calibration-failure-diagnostics.md). Sol R1's owned-temp
cleanup and actual reader/parser→workflow→daemon proof were fixed. Input/admission/
qualification/readiness validators are unchanged. Bounded private pre-human raw
XI2 and first/last rejection reasons will survive cleanup, latest-only1MiBraw/
2MiBartifact; no human-stage or public IPC trace. Live artifact path is
`~/.local/state/crowley/input-calibration-diagnostics/latest-pre-human-failure.json`.
Parent stopped only sessiondaemon2274001, promoted exact reviewed code, and
restarted NEWdaemon3087152: PAUSED70/nativefalse/inputfalse. Config and five
protected sources unchanged; the restored game was not restarted by promotion.
Historical native64 private seal belongs to exited game1033131 and was invalidated.
Luna owns fresh preflight→native100→public pause/recovery if checkpoint→ordinary5→
instrumented input attempt. If actual pointer is at a top edge after setup, ask
user to center it BEFORE GTK creation; no synthetic origin warp or blind retry.
Notify user only real human readiness; preserve fresh actual nativeXI2 artifact
on refusal and replay existing validators offline. No autonomous cycles counted.

**Input68 passed the cursor/argv boundary, then timed out before readiness:**
[Current parent verification](../.archive/executor-review/input68-timeout-parent-verification.json).
User connected RDP/centered pointer and said ready. Arthur was at character
selection; authorized pinned Return entered world. Parent decoded five fresh
normal0 frames57/61/66/70/74: speed/current0, controls up, AHclosed/pending0/
fenceinactive. Actual cursor stayed near center933,498; exact coordinate equality
with the user's earlier center was unnecessary. One monitored input68 attempt
failed `XI2 calibration event deadline expired` before READY/human sample.
The monitor's startup/window/command logs are retained, but do not establish
retention of the real XI2 stream. Do not infer a missing device/event/root cause
from that timeout alone. Workflow/driver cleanup appears to discard observer
text. The reviewed diagnostic candidate above addresses lost failure evidence; the
underlying rejected synthetic event is still unknown until the instrumented attempt.
Public PAUSED69/native=true/input=false, checkpoint clear, daemon2274001/game1033131
unchanged. User controls were released and then user requested continue; offline
work proceeds first. Notify user for the next actual live calibration handoff.
Zero autonomous cycles counted.

**Native64 protocol passed; input66 refused before human readiness:**
[Current parent verification](../.archive/executor-review/native64-ordinary65-input66-parent-verification.json).
Same gamePID1033131/start33665951 and newdaemon2274001. Parent independently
recomputed native64 evidence/content hashes and decoded retained held100 sequence110,
CRC3330663465. Production runner accepted the full strict protocol; parent did not
re-decode99 released intermediate crops or raw resume0. Memory assessment separately
classified target_exceeded: construction36,864 bytes≤128MiB; updates90,767,360
bytes>16MiB. This diagnostic does not block the input gate and needs investigation.
Public pause64→65 left no checkpoint/reconciliation, so no empty recovery was issued;
parent decoded five normal0 ordinary frames152/156/160/164/169, speed/current0,
AHclosed/pending0/fenceinactive and inputs released.

Input66 failed `calibration pointer origin is outside the owned target` before
readiness. Its persistent monitor survived, but missed the short GTK lifetime;
geometry/placement cause is unproven. Public pause→67 native=true/input=false,
no checkpoint/reconciliation. User was asked to place the actual pointer at the
center of the desktop before a fresh owned GTK creation; wait for their response,
then one monitored changed-precondition startup. No synthetic origin warp or fake
human samples. Luna holds GUI pending this response; native64 gate remains live.

**Keyboard ownership fix installed:**
[Parent verification](../.archive/executor-review/input-key-ownership-release-parent-verification.json).
Input61 reached its owned GTK target but refused before human readiness with
`desktop argv holds do not match its sealed input plan`. The raw monitor does
not serialize action argv/holds; offline production-path reproduction establishes
that Control_L+a was emitted as ambiguous ctrl+a while owning Control_L+a.
Synthetic baseline actions could execute before that refusal; no human sample
was accepted. Public cleanup paused62 with checkpoint clear.

Luna fixed only synthetic keyboard-profile serialization to retain physical
Control_L/Control_R keysyms. Strict validator, admission, Guardian and watchdog
are unchanged. Parent independently passed56 relevant tests plus scoped static
checks; the new real-admission/harmless-producer regression fails against old
MAIN with the exact original refusal. Sol R1 READY, no findings. Exact reviewed
source/test pins are installed. Parent decoded five fresh ordinary frames
1142/1146/1151/1155/1159: speed/current0, AHclosed, pending0, inactive fence and
released controls. Only sessiondaemon restarted3174693→2274001, PAUSED63 with
both live calibration gates false. Config and seven protected sources unchanged.
Luna owns fresh preflight/native100→public pause/canonical ordinary recovery→
five ordinary frames→monitored genuine human-input calibration. Notify the user
only when actual owned GTK readiness is published; no fabricated human input.

Historical native57 and ordinary58 passed on gamePID1033131/start33665951,
fingerprint899bf01093de178de122655c436fa6163f7584b74e0294035bf8c6282b9c6439:
[Native57 verification](../.archive/executor-review/native57-ordinary58-input59-parent-verification.json).
Parent recomputed hashes/held100 and ordinary5 frames; construction memory growth0
and updates7,172,096 bytes met targets. Those private live seals were intentionally
invalidated by the new driver reload; do not carry them forward. Input59 refused
pointer origin; its old monitor died before invocation and cannot prove the cause.
Normal reconnect preceded input61 and its corrected persistent target monitor.
Zero autonomous qualification cycles counted; last verified assisted scan is179.

**Installed correction:** pointer parking clears button hover before unchanged
control recognition. Exact matcher replay identified the original Restore hover
failure; no template/threshold/protocol/Guardian relaxation was needed.
[Release verification](../.archive/executor-review/native-control-hover-release-parent-verification.json).
Luna implemented the [bounded plan](../.archive/PLAN-native-control-unhover.md);
Sol R1 found a final-admission race, which was fixed and covered by actual owned
process tests. Sol R2 is READY with no findings. Parent independently passed the
full119-test operator module at final source pins (688.81s, four existing fork
warnings),22 focused checks and scoped static checks. The full module includes
actual composed success/refusals, unchanged matcher discrimination, watchdog
ownership/cleanup and late revocation/geometry/deadline no-dispatch regressions.
The exact reviewed helper/test files are installed in MAIN. Runtime/config and
daemon process remain unchanged; installed imports and helper CLI verified.
Actual CLI Opus was rejected429 before any review; user explicitly switched to
OpenAI Luna/Sol only. No new Opus approval is claimed or required.
No live input/capture occurred during installation. At that boundary the daemon
was PAUSED56/nativefalse/inputfalse with deferred recovery required. Subsequent
live results are above. Zero autonomous cycles are counted. Continue already
authorized work; a status request does not pause it.


**Historical blocker (resolved by the installed hover fix):** new-process preflight54 passed; measure-deferred55 refused
at post-reload-controls BEFORE bootstrap/native measurement, then canonical
recover56 refused its restore-control template. PAUSED56/nativefalse/inputfalse;
no human prompt appeared. [Visual refusal evidence](../.archive/executor-review/native55-visual-startup-refusal.json).
Actual images show Construct+Restore, then onlyRestore; the ordinary HUD is still
absent, so later crop failures do not prove a new movement fault. No current speed
claim. All agent input/capture is stopped; user can use RDP while Luna performs an
offline exact matcher/template comparison against successful preflight54. Do not
retry/restart/loosen guards or take desktop control until root coordinates it.
Autonomous qualification is still zero; the human-input step has never begun.


**Latest boundary:** user manually repositioned Arthur after saved/new frames
reported real speed7 at constant coordinates with all controls released. Root
refused quiescence before daemon mutation; no S stop key was dispatched. After
user correction, root independently decoded five advancing frames476..492 at
speed/current0, stableposition/AHclosed/pending0/normal0/inactive/chatinactive and
all controls up (receiptSHA `769d9b306d5401172cf973e697874df5b5be082b374cb96b0909130fc4cba4c9`).
Only sessiondaemon was restarted to discard private live seals from the exited
game: new PID3174693, PAUSED54/nativefalse/inputfalse, no checkpoint/action/reconcile.
GamePID2800399, RDP1822704, companion21909, profile and all approved runtime source
pins are unchanged. [Reset proof](../.archive/executor-review/replacement-game-native-reset-20261020.json).
Luna now owns one fresh preflight/native100/ordinary recovery, then one monitored
GTK input startup. User remains connected, Arthur still; notify immediately when
the actual human prompt is ready. No physical-input evidence or autonomous cycle
has passed. Native50 is historical for the exited game, not the current binding.


**Current live correction after remote connection:** input calibration52 failed
before human readiness on `xdotool windowactivate --sync 0x3400003` timeout.
A subsequent instrumented startup found the original game PID644491 gone and
refused identity admission. No human sample was accepted. Its window-focus
failure cause and the game exit cause remain unproven; nearby Docker `/tmp`
ENOSPC records are correlation only. [Preserved failure](../.archive/executor-review/input-calibration52-startup-and-game-exit.json).
Luna recovered the cached launcher once: new PID2800399/start32181443,
outer0x03200001/child0x02c00011, client1920x1080; Arthur selected, entering world.
Native50 below is historical for the old process; original held100/archive copies
are preserved privately. Root authorized one fresh native100/recovery on the new
binding, then an instrumented owned-GTK startup and prompt notification for real
RDP user input. No stale evidence carry, daemon restart or source edit. User is
connected through RDP and awaiting the ready prompt; no autonomous cycle counts.


Remote input calibration can be attempted through Windows RDP. GNOME existing
Desktop Sharing is active in mirror-primary mode, reachable over Tailscale at
`100.93.67.120:3389`; UFW allows3389 only on tailscale0 forIPv4/IPv6.
[Setup proof](../.archive/executor-review/rdp-desktop-sharing-setup-20261020.json).
Temporary credentials are in the private session keyring and private RDP evidence
handoff; never put the password in source control. They need reconfiguration after
logout/reboot. Protocol negotiation passed; remote Windows authentication and
non-XTEST user-input attribution still need the user's connection. Leave the game
paused and do not launch input calibration until the user can see the desktop.


Historical pre-exit game identity (superseded above): PID644491/start15495385, xid0x02e00001,
child0x2000011, fingerprint
`e84a459bda54c891092f049af9c523eb171588ce566a44123723d733baf6918a`.
1920x1080 client, telemetry crop80,48,256,256. DISPLAY:0; obtain fresh authority
and controller generation before mutation. Latest canonical recovery is PAUSED51,
nativetrue/inputfalse after the successful generation50 native calibration.
Obtain fresh state before any mutation; no physical calibration has started.

The following daemon/resource-policy history predates the installed Rust observer.
Daemon `crowley-session` restarted after accepted resource-policy R2 installation
at21:28UTC, PID184662, PAUSED45/nativefalse/inputfalse. All six accepted files and
three unchanged boundaries match final pins; MAIN imports verified; copy occurred
while stopped. [Release proof](../.archive/executor-review/native-resource-policy-release-parent-verification.json).
Parent decoded fresh closedAH normal0/inactive/pending0/speed0/released boundary
before install: [quiescence](../.archive/executor-review/native-resource-policy-quiescence-parent-verification.json).
Original gen40/43 failure archives remain byte-exact. One fresh native attempt in
generation46 failed exact ordinal validation: updates/4 observed updates/5,
sequence18. Parent independently decoded the offending original PNG. Updates1..3
were accepted; one Measure command, no source drift and all captures released.
[Failure proof](../.archive/executor-review/native-resource-policy-live46-failure-parent-verification.json).
Canonical public pause/recovery succeeded to PAUSED47/nativefalse/inputfalse. No
unchanged retry, genuine input calibration or autonomous cycle occurred. The
trace shows1.2..1.4s host processing per1Hz update; repeated identity checks
dominate while ScreenshotArea itself takes about44ms. Luna investigates the
smallest deterministic correction without relaxing exact ordinals. Assisted140 resumed with an actual1512s gap after139;141 returned to exact900s.
No claim of900s through the calibration pause.

Latest fully parent-verified cycle **#179**:

- UID `beta-normal-alliance-1792481028-Arthur-6729`;
- start1792481028, finish1792481567:539s;428 observations/1,720 rows;
- 408 full/18 bounded/2 incomplete; 426 `ok`, 2 `query_timeout`; 2 incomplete/unqueried observations;
- exact900s after178;33.130976s finish-to-server receipt;
- original saved/server digest agreement, exact loaded ACK, pending0, reopened
  AH, normal0/inactive fence, zero speed and released controls;
- [scan proof](../.archive/executor-review/build-70450-onehundredseventyninth-scan-parent-verification.json)
  and [reopen proof](../.archive/executor-review/build-70450-onehundredseventyninth-ah-reopen-parent-verification.json).

Assisted180 nominal due1792481928 (07:38:48UTC) is held for the approved
installation/native qualification window; do not claim cadence through this pause. The legacy watcher had a hardcoded
nominal start; its original receipt remains intact alongside an explicit correction.
Parent instead verified the original SavedVariables/server start and actual gap.

Scan144's exact ACK loaded on its first owned save reload before the strict
pending observation, so the assisted watcher timed out while observing a valid
already-ACKed state. Parent decoded the retained closed-AH/loaded exact ACK and
the later independent AH-open frame, verified the original saved/server payload,
and composed evidence with all three original receipt hashes. The initial
predicate timeout and stale immediate reopen sample are preserved. No separate
ACK reload or autonomous cycle is claimed. Sole operator may repair only the
private assisted predicate/read-only postclick polling for these observed states.

Scan159 retained one real incomplete observation: item12361 timed out after30s,
queried1792463305..1792463335, zero rows, unknown cutoff/witness. Counts are427ok/
1query_timeout,400full/27bounded/1incomplete. Parent verified the original payload,
server digest, exact ACK and reopened AH; finish-to-server66.948579s. No retry or
price/empty-market inference was made. This assisted cycle is not qualification.
[Original outcome proof](../.archive/executor-review/build-70450-onehundredfiftyninth-scan-parent-verification.json).

Scan161's first save helper stopped before actions on a5s OCR timeout. Original
receiptSHA `e49b9b9a5519df590f0135220fee2a450d21801fd45dddde544253e99e2c7d59`
is preserved. A fresh ordinary recovery receipt passed parent full-chain checks:
428ok,399full/29bounded,65.749333s finish-to-server; assisted only. Sole-owner
retained-image OCR comparison produced identical text in5.87s default versus2.06s
with per-call OMP_THREAD_LIMIT=1. Apply that private assisted-helper environment;
keep bounded OCR, fresh-frame and identity/input guards. Host load27.20 on16CPUs
was a contention lead; no unrelated process was killed and no global env changed.
[Recovery proof](../.archive/executor-review/build-70450-onehundredsixtyfirst-scan-parent-verification.json).

Scan177's initial helper stopped before its ACK reload on buffer MAE14.449>12;
its cause remains unproven. A later owned reload was rejected by a stale decoder;
rebind at that verified reload boundary observed exact loadedACK/pending0. Fresh
same-boot AH reopening completed. Parent independently composed the original
saved/server payload with those ACK/reopen frames, retaining all three recovery
receipts and both failures unchanged. CompositeSHA
`80644b07c3e115cd4d47a94f5b0212c22616ad4d66ab0412a856d1c6692b1d6a`;
[verified outcome](../.archive/executor-review/build-70450-onehundredseventyseventh-ah-reopen-parent-verification.json).
This remains assisted; no guard threshold changed or historical cause inferred.

Native throughput correction is scoped in the
[approved Rust observer plan](../.archive/PLAN-native-identity-observer.md).
Replace CLI fanout with one fresh pinned Rust observer at each of the existing
three identity boundaries, preserving all calibration guards. The approved R4c
source is now installed; its isolated fix worktree remains frozen.

**Current milestone: live native calibration PASS; ordinary recovery independently verified.**
[Generation50 parent proof](../.archive/executor-review/native-observer-live50-parent-verification.json):
one canonical measure attempt completed construction/held0, exact updates1..99,
held100, contiguous resume0 and finalization through the unchanged reviewed
production runner. Parent recomputed the archived evidence hash/fingerprint and
independently decoded the retained held100 PNG and recovered ordinary full-frame
PNG. Successful intermediate crops are released by production; no independent
raw re-decode of all99 updates is claimed. EvidenceHash
`8afd1e0e50d8f27835fcf521a5bd1cfa571235e8136966230c4a95f4bb52bf1a`.
Public pause50→51 and canonical recovery succeeded: PAUSED51/native true/input
false, normal0/inactive, scanner ready, AHclosed, pending0, speed0, chat inactive,
construction checkpoint absent. All source/protected pins and old40/43 archives
remain unchanged. Helpers/input are stopped and GUI held at this boundary.
Resource result is separately `target_exceeded`: update whole-process HWM growth
45,514,752bytes (43.40625MiB) against16MiB; construction growth0 against128MiB.
This is a retained resource follow-up, not a transport/render calibration failure.
The gen49 raw admission refusal was `game client is not foreground`. One guarded
pinned-tool activation restored verified foreground; preflight then passed and
recovered. Earlier gen48 cause is not inferred from that later diagnostic.
[Original refusal evidence](../.archive/executor-review/native-observer-r4-live-preflight-refusal.json)
retains all refused probes, the child-only raw logger and operating correction.
Next: ask availability for genuine physical input, then prove three NEW
unattended900s full cycles. No human input or autonomous cycle is counted yet.

[Release proof](../.archive/executor-review/native-observer-r4-release-parent-verification.json):
exact13 approved files promoted while the daemon was stopped. The reviewed
hermetic double-build produced the exact approved binary at the stable path;
the newly path-bound manifest SHA is
`bca822007b51ffc1fb25789129a31618772015dbccd43473e95a23278a823ae2`.
Only the paired observer path/hash fields were added to the private profile.
Installed uv-tool imports resolve to MAIN; daemon PID1134848 remains stable
beyond its restart interval, PAUSED48/nativefalse/inputfalse. CompanionPID21909
and protected input/decoder/calibration/controller sources remain unchanged;
original gen40/43 archives are byte-exact. Sole GUI owner held all actions during
promotion after root independently decoded its AH-closed normal0 boundary.
[Sol R4 READY](../.archive/executor-review/native-observer-sol-r4-review-verification.json)
and [actual CLI Opus R4 READY](../.archive/executor-review/native-observer-opus-r4-review-verification.json)
(exit0, claude-opus-5-5) approve these exact pins with no blocking findings.
Three nonblocking Opus follow-ups remain separately recorded.
Installation prerequisites and native100/recovery above are now complete. Genuine
human input and three new unattended900s cycles remain; qualification is zero.

[Final R4 parent verification](../.archive/executor-review/native-observer-r4-final-parent-verification.json):
284 aggregate covered cases at byte-identical source across both phases: full13
composition and251 components before the parent-only path failure, then affected
diagnostic1/fragment4/finalize5/runtime7/constructor3 fresh with short paths.
Independent rustfmt, Ruff, format, compile and diff checks pass. No source/test/
deadline changed for the path fix; no uninterrupted full-group rerun is claimed.
The fresh full13 phase accepted99updates/max438.741355ms with exact1Hz/held100/
resume0 guards; its numeric evidence carries at identical source. Actual query
receipts prove preserved R3 acceptance versus current typed X11 refusal under the
same forced uncertainty, before normal restoration. Source remains frozen; no
observer installed, new native attempt, physical input or autonomous cycle yet.

The following describes the already-closed parent test-environment failure:
[Parent environment diagnosis](../.archive/executor-review/native-observer-r4-parent-path-failure.json):
actual supervised socket path110bytes; direct host bind refuses AF_UNIX path too
long before owner startup. Root caused the long per-command basetemp. New run
`native-identity-observer-parent-r4-path-closure-20261020` freshly checks that
same diagnostic and remaining groups with short paths; ALL13source bytes and
production/test deadlines are unchanged. Prior same-source13+251passes and
numerical/X11 receipts link explicitly; no uninterrupted full-group rerun claim.
Private final manifest `native-identity-observer-r4-20261020/final-manifest-r4c.json`,
SHA `e2cd9b22d2e9651d7af69b5c88f7f937df571d443c0184a37bb2fa99052ef0ba`.
BinarySHA `5f4cb94ba23d079885ac9aaf7034619f60cf59f33dd91ae2f91174631c675b58`.
Rust/test are the only two changed paths versus R3d; other11 stay byte-identical.
None focus refuses; matching-candidate query errors propagate. Actual X11 shim
proof distinguishes preserved R3 acceptance from current exact error, records
ordered request/destroy events and restores real identity. Historical binary is
optional when absent; the required current regression always executes.
Root preserved an owned untracked Cargo cache after the initial scope guard
refused before tests, then confirmed all13pins unchanged. The clean run is
`native-identity-observer-parent-r4-clean-final-20261020`: fresh all13 composition,
fresh broad/runtime/static and independent rustfmt (11checks), no prior case/
performance carry after changed Rust. Per-command private basetemps and retained
X11 query/error receipts prevent pytest evidence rotation. Luna monitors then
launches root-prepared actualCLI OpusR4 only on fullPASS; root triggers SolR4.
No observer installed, new live native/input calibration or autonomous cycle.

The following R3 review/result is historical at its unchanged original pins:
[Sol R3](../.archive/executor-review/native-observer-sol-r3-review-verification.json)
requires query uncertainty on an already matching candidate to propagate rather
than be dropped; [actual CLI Opus R3](../.archive/executor-review/native-observer-opus-r3-review-verification.json)
(exit0/claude-opus-5-5) requires None/zero focus to refuse, matching the real tool.
Root rewrote the next phase as the [two-file rejection-state plan](../.archive/PLAN-native-observer-r4-rejection-states.md):
only Rust main and its component test may change; other11source files stay at
R3d. Actual deterministic X11 error and None-focus regressions are required.
Complete geometry before counting remains intentional; the old reference's
outer-size-after-count behavior can differ and is not universal parity. The
close-race FD-baseline coverage nit is deferred with existing lifecycle proofs.
No new native attempt or source installation. The following R3 result is the
historical pre-R4 validation, not approval of future changed Rust bytes:
[Final R3 parent verification](../.archive/executor-review/native-observer-r3-final-parent-verification.json)
records272 fresh tests plus12 carried unchanged composition cases (284 aggregate).
The corrected cancellation branch passed independently39.49s; observer/driver/
native252, fragment4, actual actor/finalize5, runtime7, constructor3 and scoped
static checks passed fresh. All other12source files are byte-identical to R3b;
whole-module AST outside the single corrected branch is identical. The prior12
passing composition cases/full99updates/max496.03336ms carry explicitly; no fresh
whole13run is claimed. Exact final manifest:
`native-identity-observer-posthandoff-r3d-20261020/final-manifest-r3d.json`, SHA
`dff988fe51c5180be9f570c6d5ede1a378f15612e0337a134d1f4fd7a6f6fdc9`.
Source remains frozen through reviews. No observer installed or new live native,
physical input calibration or autonomous cycle attempted.

The following R2/R3b history remains at its original pins and is superseded by
the current R3 result above:
[Final parent verification](../.archive/executor-review/native-observer-closure-final-parent-verification.json):
280 tests passed:13 actual compiled operator/daemon/Agent composition cases,
248 observer/driver/native,4 fragment/provenance,5 same-actor finalize/recheck
race,7 runtime and3 constructor checks. Scoped Ruff/format/compile/diff pass.
The complete measurement accepted99 updates with worst active550.425186ms,
zero900ms budget violations, and existing exact1Hz/held100/resume0 guards.
Per-case timings, IPC replies, journal and cleanup artifacts are retained
privately outside rotating pytest directories. This is offline fixture evidence.

[Sol R2 READY](../.archive/executor-review/native-observer-sol-r2-review-verification.json)
and [actual CLI Opus R2 NEEDS WORK](../.archive/executor-review/native-observer-opus-r2-review-verification.json)
(exit0, claude-opus-5-5) reviewed identical unchanged13 pins. Opus found actual
Cargo build-cwd ancestor config not checked and window counting before full
verification. Parent/Sol also accepted typed close-race, vendored WM_STATE focus
parity and independent outerParent checks; remaining two nits are deferred with
reasons in the proof. One Luna worker owns seven exact paths under the
[R3 contract-closure plan](../.archive/PLAN-native-observer-r3-contract-closure.md).
No live install or native retry; root independently reruns final relevant matrix
only after the corrected source freezes, followed by both R3 reviews.
R3b is now frozen with all five corrections and decisive regressions complete;
root's independent final matrix FAILED:12passed/1failed at these pins. Private manifest
`native-identity-observer-r3-20261020/final-manifest-r3b.json`, SHA
`4bff2a2a6e5f733986d2b8735c145d031944014f8ff27fbd96f4a8be577ccc33`.
Current binarySHA `ce51b5a0a0ba82f4ac67589610520294d6ccbee860442891575e2e9383c075d7`.
Worker22 observer/12 driver/5 config focused tests and static checks pass;
parent full13 composition and fresh broad/runtime/static checks are separate.
Actual pinned xdotool cases now distinguish descendant-to-client/outer WM_STATE
normalization, no-WM_STATE raw focus and unrelated foreground; invalid and two
valid game-window candidates are also covered. Earlier R3 manifest was superseded
by test-only additions before the parent run; retain it without claiming freeze
stability. Parent run `native-identity-observer-parent-r3-final-20261020` checks
all13pins before/after each group. No live native/input/autonomy claim.
[R3 parent failure](../.archive/executor-review/native-observer-r3-parent-composition-failure.json):
post-handoff-cancel receipt lacked `reservation_cancelled`; the full measurement
accepted99 updates/max496.03336ms/zero budget violations. Broad/runtime/static
groups were not reached. Exact failed-case receipt records interrupted terminal,
reservation_cancel_failed/OperatorError and cancellation_actor_retained; actual
IPC later reports successful cancellation ~123ms after that receipt event.
Root/Luna source diagnosis now confirms intentional late-reply safety: SIGINT
interrupts actor.call, which poisons the channel; helper retains the actor and
EOF cleanup performs exact known-ID cancellation. Product code remains frozen.
Only the post-handoff-cancel test branch is being corrected to verify direct or
retained-actor cancellation through actual matching IPC before fixture teardown.
Root will independently reproduce that branch plus fresh broad/runtime/static;
prior12passing cases/timings may carry only with unchanged other12files and exact
AST equivalence outside this branch. No fresh whole13pass claim at a new hash,
no production deadline change, and no R3 review launched before final checks.

The [accepted closure plan](../.archive/PLAN-native-observer-accepted-closure.md)
keeps the same13 files and disjoint8+5 owners. R3 temporarily supersedes the prior8+5 ownership for its seven exact paths.
Other six candidate files stay frozen. The PRE-R3 final manifest remains:
`native-identity-observer-fix-r1-20261020/resource-retention-r4/final-static/final-manifest-r3.json`,
SHA `f9889c24347bec4e847d0d93176df9c9c3dc03a90edc85fe3b45eed377961956`.
PRE-R3 binarySHA `be2f76f352c311e992611ee111028e9e56515b395e3d9ba57cd1b2b01ea149ea`.

Earlier failed/partial runs and both NEEDS WORK R1 reviews remain preserved in
[the exact preceding handoff](../.archive/executor-review/handoff-history-before-native-observer-final-20261020T0505Z.md).
The earlier925ms row was not persisted and the copied failed-recovery receipt
belonged to a later passing case; neither historical product cause is established.
Test-only corrections now register resources immediately, verify teardown even
on initialization refusal and persist timings/actor receipts before assertions.
No speculative product optimization or relaxed900ms/cadence guard was introduced.
Reference-only prefilter optimization remains deferred.

After both source reviews approve these same pins: coordinate sole-owner fresh
quiescence; stop daemon; promote exact reviewed source; use the reviewed builder
to publish the stable observer path with a newly path-bound private manifest;
verify binary/source/static/linker pins; atomically configure paired path/hash;
restart and verify imports/PAUSED/unarmed. Never blindly copy a manifest whose
`binary` field names the old private output path. Then one fresh native100 and
canonical pause/ordinary recovery. Only after that ask user availability for
real input calibration, followed by three new autonomous900s full cycles.
No new live native attempt, human input calibration or autonomous cycle occurred.

Scans108..122 have full-chain proofs and exact900s starts. Scan123 started
1792429927 after the qualification pause (1216s after122,316s late). Its full
chain is verified;124 also complete at exact900s. Next nominal ordinary
deadline1792431727 (17:42:07UTC) was held for the single diagnostic native run.
Assisted125 began1792431816:989s after124 (89slate). Assisted126..139 and141..179 completed at exact900s intervals;140 has the explicit
1512s calibration gap. Nextdue1792481928 (07:38:48UTC). Full chains125..179 are
parent verified. After122, parent decoded fresh closedAH/pending0/ordinary
normal0/inactive/speed0/released boundary; [quiescence proof](../.archive/executor-review/native-ack-release-quiescence-parent-verification.json).
Exact accepted six files installed while service stopped, imports verified from
MAIN, then service restarted: [release proof](../.archive/executor-review/native-ack-release-parent-verification.json).
After106 a real WOW51900319 disconnect caused107 to start350s late; normal
reconnect succeeded without credentials. The old memory notification said8hours
ago; no new OOM cause is established. See archived links for exact proofs.

Scans115 and118 reopening required separate fresh Auctioneer targets after
stale positions hovered another player. Parent combined the two retained receipts
with their original hashes, decoded both ACK/reopen pixels, and preserved the
failed stale-target attempt unchanged. This remains assisted evidence.

Generic parent verifier, only after the complete retained flow receipt exists:

```text
uv run python /home/dev/.local/state/crowley/executor-evidence/verify-assisted-cycle.py ORDINAL WORD_ORDINAL PRIOR_START RELATIVE_FLOW_RECEIPT
```

It verifies original saved bytes against the server and independently decodes
ACK/reopen pixels. Use a fresh ordinal; its public outputs are exclusive-create.
Private runtime flow receipts live under
`~/.local/state/crowley/executor-evidence/runtime-relink/`.

## Installed release and fixed assumptions

Accepted diagnostic release:
[verification](../.archive/executor-review/native-observation-diagnostics-release-parent-verification.json).
Historical pre-promotion MAIN source SHA256 (superseded below):

- daemon: `4259e4de58b3b3d79f2fc595978907090a7f74666656a4af0c311a33602b0dad`;
- calibration: `3a91f4fe690cd820329fe2536fc03e5c7de24e4c20649efdf1a705b8c147c8fc`;
- driver: `ca0ca123d0fa09d8361c8632d9cc1c2c501d87adf99cb3cc268688dd4291a166`;
- helper: `63fd2b97e84f77b11f12f120dc0300e822611dcedce19213f5b949b40e657462`.

Helper editor-state/contrast correction is installed, reviewed Sol R2 and actual
Opus5.5 R2 READY, with parent reproduction. [Contrast release](../.archive/executor-review/native-chat-contrast-release-parent-verification.json).
Its full96-test result used an earlier test pin; the final test pin adds one
regression with18 focused passes. Do not claim a full97-test run.
The failed gen33 original fullframe was never retained; only its crop exists.

Chat contract remains exact sticky Say/1920x1080 geometry: chat crop30,938,460,37,
body ROI40,7,400,13 within it. Preserve the measured chrome/editor-state guard,
body-only preprocessing, cursor removal and exact typed-command equality.
Unknown/active-empty/inactive nonempty states refuse as specified; no fuzzy
OCR fallback or blanket telemetry replacement. Native bootstrap lacks a surface,
and held publication cannot provide all measure/resume chat checks.

The accepted Rust matcher/runtime and addon79 remain installed. No runtime
build, shell/Python matcher fallback or artifact substitution. Provenance and
release pins remain in the [Rust/helper verification](../.archive/executor-review/native-helper-rust-final-release-parent-verification.json).

## Frozen correction and release status

Livegen37 requested update2 but captured3. Parent decoded the rejected image:
screenshot starts1384.571ms apart, screenshot28.957ms, identity work926.812ms
plus142.073ms deferred-owner validation. This did not establish a Rust compute
bottleneck. [Live timing proof](../.archive/executor-review/native-live-budget-failure-gen37-parent-verification.json).

Approved scope: [identity budget](../.archive/PLAN-native-identity-budget.md),
[pre-ACK alignment](../.archive/PLAN-native-capture-ack-alignment.md), and
[parent closure checklist](../.archive/PLAN-native-ack-review-closure.md).
Only six source/test files. Preserve three fresh backend-pre/backend-post/
runner-post resolves and all identity/owner/lease/Guardian/generation/run/epoch/
B0/CRC/ordinal/cadence/deadline/cleanup guards. Only the three approved duplicate
identity resolves are removed on exact eligible deferred updates. No Guardian,
producer, addon, Rust, helper, service, configuration or public schema changes.

FINAL frozen worktree: `/home/dev/.cache/crowley/worktrees/native-ack-source-r2-20261019`,
base1cbaadf. Private manifest `native-ack-source-r2-20261019/final-freeze-r2.json`
uses key `files`. Original R7 worktree `native-identity-budget-20261019` is frozen
for comparison, not the candidate to install. Final SHA256:

- `src/crowley/session/calibration.py`: `d342224339777e103b47aad008608f56f396711e5aff3999367286319990d26b`;
- `src/crowley/session/daemon.py`: `946e02bd467cecb7d720181e032bb54c2fc280076c884e406f680b51ab085d50`;
- `src/crowley/session/driver.py`: `05e5ed98d0b94019aa29eb0f4bd6ac3174cf45dca93deb9059425eeb815738cc`;
- `tests/test_native_calibration_operator.py`: `275854aca13bd70aff559e10268ed83624046f678a548bd1790de8b9eab0ee62`;
- `tests/test_session_native.py`: `9f0c99e21ade83aba9f74b8f245d2780f7d7a17a5b0d1c1e3e59bd7c74d24d8c`;
- `tests/test_session_runtime.py`: `a6eacc9c699757f0e0870937eec2ae2a320c2ecbd966ee2757003c0395097456`;

The receipt remains local through backend cleanup and is handed to eligible
provider calls once, finalized; generic backend keywords stay unchanged.
Held100 is reported retained only after both callback checks and successful
resume-required publication. Publisher alignment uses immutable first receipt
S1/U1 and prior decoded uptime, constant50ms guard, pre-ACK wait outside locks,
then synchronized controller/construction/Guardian/backend admission. Original
per-attempt/frame/operation/reservation deadlines never extend.

All independent parent offline gates PASSED on unchanged final six hashes:

- receipt/diagnostic/witness9 in1.90s; callback order and real-runner cleanup2
  in13.47s; actual compiled boundary matrix22 in57.33s;
- all seven actual-runner modeled scenarios in130.66s; positive active maxima
  882.576/888.576/889.076/882.576ms, phase951 naturally protocol-refuses;
  negative budgets961.576/1437.161ms; exact positive charge counts
  capability1085, target98, ACK98, glue99;
- genuine baseline56.30s: old refuses update4(received5), accepted3, max
  1384.569ms/glue4; reduced accepts99, max1435.161ms/glue119;
- exact compiled100 in136.20s, real observer103 accepted attempts including
  retained held100 and sealed path/hash; scoped Ruff/format/diff checks passed.

[Final parent proof](../.archive/executor-review/native-ack-final-r2-parent-verification.json).
Private independent source/logs/timelines: `native-ack-parent-r2-final-20261019/`;
verification WT `native-ack-parent-verify-20261019`. Worker exact gate136.22s,
focused runtime21/native23 and actual callback rejection130.80s also passed.
Exact long node (short compositor tests do not substitute):

```text
tests/test_native_calibration_operator.py::test_actual_operator_measure_composes_x11_screen_daemon_and_agent[success]
```

[Sol R3 READY](../.archive/executor-review/native-capture-ack-sol-source-r3-review.json),
all six pins checked before/after; no new Must/Should/Nits. Actual Opus R2
completed exit0 as `claude-opus-5-5`, six pins unchanged. It found production
correct, but returned NEEDS WORK for a test fixture publishing fake PGID999999
to a real watchdog kill list. [Full review](../.archive/executor-review/native-capture-ack-opus-source-r2-review.md).

The [final test safety correction](../.archive/PLAN-native-ack-watchdog-fixture-closure.md)
is frozen. Native test final SHA `dd50b41bad852eeabc01245ca356c153a0b48a51b739b98c73c21e06b5f22ad6`;
runtime test final SHA `d7da65ad2f1704357ef94e15c2acffb93dfdc5481df494fee5a403801723c96e`.
The other four R2 files above remain exact. An owned live group replaces the
fake PGID; finally restores/republishes all three injected fault states before
holder termination/reap, even after failure. Baseline outcomes and comment fixed.
Parent reproduced affected3 in8.69s, baseline in46.10s and scoped static checks.
Production/operator bytes and runtime AST outside baseline are unchanged:
[test-delta proof](../.archive/executor-review/native-ack-test-safety-parent-verification.json).
Earlier full100/seven-model evidence remains bound to original R2 test hashes.
[Sol R4 READY](../.archive/executor-review/native-capture-ack-sol-test-safety-r4-review.json) and [actual Opus R3 READY](../.archive/executor-review/native-capture-ack-opus-test-safety-r3-review.md), exit0 realclaude-opus-5-5, no findings. All offline release gates complete. Exact final six files installed at17:02UTC; see release proof above.
Private final freeze: `native-ack-source-r2-test-safety-r3-20261019/final-test-safety-r3.json`;
parent logs: `native-ack-test-safety-parent-20261019/`;
actual reviews: `native-ack-source-opus-r2-20261019/` and
`native-ack-test-safety-opus-r3-20261019/`.

Earlier partial/rejected candidates remain historical evidence:
[Sol R1](../.archive/executor-review/native-capture-ack-sol-source-r1-review.json),
[Sol R2](../.archive/executor-review/native-capture-ack-sol-source-r2-review.json),
[Opus R1](../.archive/executor-review/native-capture-ack-opus-source-r1-review.md),
[parent arbitration](../.archive/executor-review/native-capture-ack-opus-source-r1-arbitration.json),
and [failed compiled100](../.archive/executor-review/native-capture-ack-parent-r2-compiled100-failure.json).
Earlier replay omitted0.167ms glue/retry wait and had an invalid reduced-mode
baseline; those outputs are superseded by the corrected parent proof. The
root-added dedicated full-run missing-callable test is explicitly deferred as
redundant with unchanged guard and actual callback-rejection cleanup; accepted
reject/post-notification failure and receipt propagation regressions remain.
Modeled receipt substitution uses the real provider with an external capture
fixture; it is not a concurrent real-C producer race proof.

## Live40 result and current blocker

[Parent failure proof](../.archive/executor-review/native-memory-failure-gen40-parent-verification.json).
Gen39 control preflight succeeded; resume advanced40. Real native measurement
ran133s and reached accepted held100. The diagnostic is intentionally bounded
last16: accepted updates85..99 and held100, no source drift. This resolves the
previous ordinal/capture-timing failure for this run, but native qualification
FAILED at final updates-memory accounting before resume/finalization.

Exact reset5 whole-game process measurement, pinned PID644491/start15495385:
post-reset HWM3,850,637,312 bytes; final HWM3,899,281,408;
growth48,644,096 bytes (46.390625MiB), limit16,777,216 bytes (16MiB).
Final RSS3,808,673,792 is below baseline: a genuine peak breach, not proof of a
persistent addon leak. Bound workload1..100 lasted108.132225155s. Full durable
archive SHAab6df883d2b785e1ee57238bc55c1eec76cec42ff94043a3c4b46bb905790244;
private `.session.json.archives/native_memory_failures/00000000000000000001.json`.
Diagnostic SHA438d682789efbc57fd359c87e7aa1599becaa1de42120c76237085d313d6c99c,
private `native-observation-diagnostics/4bb6255b9ee247cdacc9a8de268e304c/failure.json`.

Original measure helper automatically paused to41, restored/reloaded ordinary
and committed recovery. Standalone recover39/41 subsequently refused before GUI
because no checkpoint remained; coarse actor_admission_invalid wraps the exact
public refusal `native construction recovery checkpoint is missing`. Sol
confirmed no accepted-response mismatch and no recovery source fix is needed.
Do not retry unchanged recover or native measurement. Historical handshake
restored=false is not current-scene proof: parent decoded fresh ordinary state
[ordinary proof](../.archive/executor-review/native-memory-failure-gen40-ordinary-parent-verification.json)
and independently decoded reopenedAH normal0/inactive/pending0/speed0/released.

Current work: sole operator maintains123+assisted900s chains. Parent independently
verified110 passive ordinary samples over109.007s: RSS range91,168,768 bytes,
HWM constant4,086,501,376 bytes; normal/0/AHopen/speed0. No reset/GC/input.
[Passive comparison](../.archive/executor-review/ordinary-scan123-passive-memory-parent-verification.json).
Source audit found2048pooled textures, bounded100sample/timer state, no obvious
unbounded retention; transient copies/serialization/compression remain unprofiled.
Sol approved [bounded diagnostic plan](../.archive/PLAN-native-memory-visibility.md).
Luna owns only daemon.record_candidate and runtime tests in isolated
`native-memory-visibility-20261019`, adding existing Luaheap/texture/updateP99
fields to private last16trace. Root reproduces tests then Sol+actual Opus review.
Frozen candidate daemon22327c5c6c4d772afe515d8c09c4c744214709b55ccc557d33606495676e7c37,
runtime test7bae80b98b08d13b193ea1472e734724ad4b8e275ead206e9fc7d832a6fe9857.
Parent9focusedPASS2.07s plus static; outside2private methods AST unchanged:
[proof](../.archive/executor-review/native-memory-visibility-parent-verification.json).
[Sol READY](../.archive/executor-review/native-memory-visibility-sol-r1-review.json),
[Actual Opus READY](../.archive/executor-review/native-memory-visibility-opus-r1-review.md)
(exit0 claude-opus-5-5). Both source reviews have no Must/Should findings.
Reviewer wrote scratch/plan notes outside repo; parent retained them privately,
source unchanged. Nonblocking nits: P99 also lags and is zero before100updates;
redundant privacy assertion harmless. Do not change frozen source for these.
Private Opus evidence: `native-memory-visibility-opus-r1-20261019/`.
Full124chain and fresh quiescence parent-verified;2-file diagnostic release
installed17:36:54UTC with imports/pins checked and service restarted:
[release proof](../.archive/executor-review/native-memory-visibility-release-parent-verification.json).
The one instrumented chain from42 completed as native43 and failed; separate
canonicalrecover44 succeeded. Details and authorized policy implementation below.
No standalone recovery when checkpoint absent, no unchanged native retry.
Installed16MiB gate and GC behavior remain unchanged pending reviewed release. No user physical input requested yet.

## Instrumented43 result and authorized policy separation

[Parent verified failure](../.archive/executor-review/native-memory-failure-gen43-parent-verification.json).
Fresh42preflight passed; native43 ran135s, source driftfalse, accepted through
held100 again. Updates whole-process reset5 growth20,414,464 bytes (19.46875MiB)
exceeded16,777,216-byte target. FinalRSS3,843,600,384 below reset3,909,410,816.
Late16attempts retained exact2048textures; Luaheapafter123755.455→126370.608KiB;
lastp9923.2616ms. Heap/P99lagonepublication; initialP99zero. This does not
attribute the whole-process peak or rule out earlier transients.

Passive sampler233samples,109inside exactupdatewindow; rawsha and metrics are
in parentproof. Original measure receiptSHA7a3ed8b0bb88bf2e7e24a76d57bff4f0b0cad74fadc22827ca43eeb1ea0dac1f;
newdiagnostic `3443ba6891f14f0782ea89b7bf25e9c0/failure.json`,
SHA46a2acd6be11729168025ffdae571fb4c40dc520ad112ee1bc38d03625efbd74.
Full failurearchive `.session.json.archives/native_memory_failures/00000000000000000002.json`,
SHA48e1aa133e3b0a674cd226ab925e2c4e2ec018c56a3d2730ed57e1fed3f711ab.

Helper ended with reservation_cancel_failed/actor retained. Sole operator made
one publicpause43→44, then canonicalrecover44 SUCCEEDED; parent checked the
separate original receipt and independently decoded fresh ordinary normal0/AH
closed/pending0/inactive/speed0 frame. AH subsequently reopened for assisted125. No further native attempts authorized against this unchanged gate.

User authorized the resource-policy separation with “proceed with these steps”
at20:07UTC. [Implementation plan](../.archive/PLAN-native-resource-policy.md) has
[Sol plan approval](../.archive/executor-review/native-resource-policy-sol-plan-review.json).
Luna completed the first candidate in isolated worktree
`/home/dev/.cache/crowley/worktrees/native-resource-policy-20261019`.
Owned production files: calibration/controller/daemon; three scoped tests.
Exact reset5 memory measurements and128MiB/16MiB targets remain. Verified
resource overages receive separate durable assessments; correctness qualification
still requires a fresh100-update run and all existing identity/cadence/ownership/
recovery guards. Old failure archives remain byte-exact and unqualified.
Policy separation is installed after parent reproduction and Sol/actual Opus
approval. Human input remains a separate genuine-human gate.

First source candidate passed337 native/regression tests,38 runtime tests and
compiled100. Parent reproduced23 focused,6 runtime,5 archive cases and compiled100;
then independently passed one added composed real-runner overage case.
[Parent evidence](../.archive/executor-review/native-resource-policy-r1-parent-verification.json)
keeps exact initial/final test-pin attribution; no full338-test claim.
[Sol R1](../.archive/executor-review/native-resource-policy-sol-r1-review.json) and
[actual Opus5.5 R1](../.archive/executor-review/native-resource-policy-opus-r1-review.json)
both NEEDS WORK. The consolidated R2 fix implements full canonical
persisted fingerprint/hash validation, replacement/historical current semantics,
causal runtime assertion and focused negative coverage. R2 parent independently passed32 focused,6 runtime and real compiled100 plus
static checks: [R2 evidence](../.archive/executor-review/native-resource-policy-r2-parent-verification.json).
[Sol R2 READY](../.archive/executor-review/native-resource-policy-sol-r2-review.json);
[Actual Opus5.5 R2 READY](../.archive/executor-review/native-resource-policy-opus-r2-review.json),
exit0 and all nine hashes unchanged. New private evidence:
`native-resource-policy-source-r2-20261019`. R2 is installed; fresh live gates pending.

Assisted139 is complete. After native46 failure/recovery, assisted140 started
1792445928 (1512s after139), preserving the actual calibration gap. Whole-chain
verification remains pending; do not count it as autonomous qualification.
Scan134 reopened through a separate fresh tooltip-verified Auctioneer target;
the stale-target failure is retained unchanged and its hash plus the recovery
hash appear in the parent reopen proof. The20:12UTC backup is complete and
independently validated. [Host operations plan](../.archive/PLAN-session-host-operations.md)
has [Sol plan approval](../.archive/executor-review/host-operations-sol-plan-review.json)
for hourly backups and two-minute read-only health timers. Luna began that
independent implementation in `/home/dev/.cache/crowley/worktrees/host-operations-20261019`;
R3 candidate passed parent30 tests/static/unit checks;
[Sol R1](../.archive/executor-review/host-operations-sol-r1-review.json) and
[actual Opus R1](../.archive/executor-review/host-operations-opus-r1-review.json)
requested changes. Luna completed consolidated R4 fixes; parent independently
passed all48 tests, scoped static/compile and systemd checks at unchanged six
pins. [Parent R4 evidence](../.archive/executor-review/host-operations-r4-parent-verification.json).
[Sol R2](../.archive/executor-review/host-operations-sol-r2-review.json) and
[actual CLI Opus R2](../.archive/executor-review/host-operations-opus-r2-review.json)
requested bounded manifest headroom and targeted classification/test corrections.
R5 passed parent52 tests and all scoped checks;
[Sol R3](../.archive/executor-review/host-operations-sol-r3-review.json) and
[actual CLI Opus R3](../.archive/executor-review/host-operations-opus-r3-review.json)
are READY, no findings. Exact six files/user units installed without restarting
session or companion; code and proof pushed as513d76b. Real backup service and
independent full validation passed. Health correctly reports ATTENTION/exit2
for preserved native46 error. Both timers are enabled: hourly minute12 backups,
two-minute read-only health. No duplicate manual/Luna hourly scheduling remains.
[Host release proof](../.archive/executor-review/host-operations-release-parent-verification.json).
Core R2 remains installed at23d7f75. These timers do not trigger game scans; the
addon900s timer remains the scan clock. Never synthesize human input.

## Next live gates, in order

1. COMPLETE: pointer-parking correction independently verified (full119 tests),
   Sol R2 approved and exact reviewed helper installed. Runtime/config unchanged;
   no daemon restart or game control during installation.
2. Coordinate desktop handoff with the user, then let the sole Luna GUI owner
   perform canonical recovery from the actual checkpoint/current generation.
   Require ordinary HUD restored and checkpoint clear before fresh calibration.
3. Fresh native preflight/100-update measurement and canonical ordinary recovery
   on the current game process: PAUSED/native true/inputfalse, checkpoint clear,
   no stale operation/action. Prior native50 belongs to the exited game.
4. Resume INPUT_CALIBRATION and start input-calibrate with actual fresh generation.
   Wait kindinput/staterunning/readiness.ready and the separate owned GTK prompt.
   Require real human pointer motion, ordinary key press/release and button
   press/release. Never synthesize. First event intentionally pauses/gen++;
   do not resume early. Wait about120.5s for completion/native+input true.
5. Resume/reconcile and independently verify three autonomous900s full cycles.
   Do not claim launch qualification before every gate passes.

## Entrypoints, backups and preservation

Python `/home/dev/repos/pegasus/.venv/bin/python`; session CLI
`/home/dev/.local/bin/crowley-session`; config `~/.config/crowley/session.toml`.
Helper `tools/native_calibration_operator.py`; templates
`~/.local/state/crowley/executor-evidence/native-live-controls-20261019/templates.json`;
matcher root `~/.cache/crowley/template-matcher/v1`.
Root's private routine verification/publication wrapper is
`~/.local/state/crowley/executor-evidence/complete-assisted-cycle.py`:
arguments NUMBER ORDINAL_WORD PRIOR_START RELATIVE_RECEIPT. It requires clean
tracked MAIN, verifies original/server/ACK/reopen, derives actual coverage/reason
counts, updates the handoff, and commits/pushes exactly the two proofs plus handoff.
Use only after the sole GUI owner seals the full receipt. Logs stay private.
Helper options: `--generation CURRENT --config CONFIG --templates TEMPLATES
--matcher-artifact-root ROOT {recover,control-preflight,measure-deferred}`.
Use exact returned generations and canonical ownership/fence/recovery protocol.

Latest independently validated private backup:
`beta-20261019T221201Z-55a31b91c82d`, after verified141, manifest
`b0c607d275009fb030431e936205e348a5063cbde206ed280ec31ee9b432dcdc`.
The systemd timer actually fired22:12UTC and completed22:12:10; parent independently
fully validated this new snapshot and directory0700/files0600.
[Scheduled backup proof](../.archive/executor-review/market-backup-20261019T2212Z-parent-verification.json).
Next backup23:12UTC via enabled `crowley-market-backup.timer`; no manual/model
invocation. Prepared manual fallback was not launched. Prior isolated restore
drill accepted. Automatic two-minute health recurrence is also
[verified](../.archive/executor-review/host-operations-timer-recurrence-parent-verification.json).

Host maintenance commands:

```sh
systemctl --user list-timers crowley-market-backup.timer crowley-health.timer
systemctl --user start crowley-market-backup.service
cat ~/.local/state/crowley/host-operations/latest-health.json
```

The backup oneshot shares its nonblocking lock with scheduled runs. Health reads
services, IPC status, upload history and validated backup metadata; it performs no
game input/restart. ATTENTION for the known native calibration error is expected
until corrected; it is not an operational qualification. Scans remain on the
addon's900-second start clock, with the deterministic session engine completing
save/reload/upload/ACK/reopen after qualification. No cron drives game input.

API: `tools.market_backup.snapshot` then `validate_snapshot`; retain full
invocation output privately and publish only sanitized hash/coverage/mode proof.

Keep raw frames, receipts, SavedVariables, process/command logs and backup
contents private under existing state directories. Logs/files0600, directories
0700. Never edit game SavedVariables to make an upload pass. Retain original
source/import/process pins and truthful assisted/model/compiled/live labels.
Repository skills stay small and source controlled: client contracts and local
game control contain the demonstrated timing/fixture lessons.

The23:12UTC hourly backup also fired automatically and passed independent full
snapshot/hash/private-mode validation: [recurrence proof](../.archive/executor-review/market-backup-20261019T2312Z-parent-verification.json).
