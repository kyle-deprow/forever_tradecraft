# Forever Tradecraft handoff

Updated 2026-10-19, 07:05 UTC. Repo `/home/dev/repos/pegasus`.
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
Seven accepted native files and the final Rust-backed calibration helper are installed.
See native-paused-install-parent-verification.json for hashes/pins/process proof.
Collection is still **operator-assisted**; GUI Luna keeps it flowing.

Historical parent independently verified **80**, UID
`beta-normal-alliance-1792388863-Arthur-6955`:428obs/2060rows/412full/16bounded/
0incomplete, duration479s, exact900s after79. Original/DB/ACK/AH independently
verified; finish→server43.468876s. AHboot1792389401-501896/seq13, pending0, normal0,
inactivefence/stationary/released. Public build-70450-eightieth-{scan,ah-reopen}-
parent-verification.json.81due1792389763 (06:02:43), soleGUI owns fullnextcycles.

Previously parent independently verified **79**, UID
`beta-normal-alliance-1792387963-Arthur-1707`:428obs/2045rows/411full/17bounded/
0incomplete, duration478s, exact900s after78. Original/DB/ACK/AH independently
verified by private deterministicrunner; finish→server40.631092s. AHboot
1792388498-512859/seq13, pending0/normal0/inactivefence/stationary/released.
Public build-70450-seventyninth-{scan,ah-reopen}-parent-verification.json.
80nextdue1792388863 (05:47:43). 77/78/79 are three complete on-time assisted
cycles, NOT autonomousengine qualification. SoleGUIcontinues untilrelease.

Previously parent independently verified **78**, UID
`beta-normal-alliance-1792387063-Arthur-1589`:428obs/2016rows/412full/16bounded/
0incomplete, duration480s, exact900s after77. Original/DB/ACK/finalAH independently
verified; finish→server31.733305s, boot1792387591-257771/seq14, pending0, normal0/
fenceinactive/stationary/buttonreleased. Public build-70450-seventyeighth-{scan,
ah-reopen}-parent-verification.json. Fullassistedcycle;79due1792387963 (05:32:43).
Reusable private parentverification runner verify-assisted-cycle.py consumes
number/ordinalword/priorstart/rawreceiptREL; does retained productiondecode +DB
verifier+exactoriginal. No GUIinput. 79prior_start1792387063 ordinalseventyninth.

Previously parent independently verified **77**, UID
`beta-normal-alliance-1792386163-Arthur-8643`:428obs/2003rows/413full/15bounded/
0incomplete, duration477s, exact900s after76. Original SHA
9911126e8bf9f7c1026c2d2b8db0bfc9fd43fc81007cfdcc54cc97a12fbe1179; DBdigest
match, finish→server54.838502s. Parent decoded actualACK and final AH-open PNG
a02b08f9583c17980c6eb5af2d6d233c4ed3dcae9ffbbce2c1de3c1e980e8c93, boot
1792386710-567444/seq14, normal0/fenceinactive/pending0/buttonsreleased/stationary.
Public build-70450-seventyseventh-{scan,ah-reopen}-parent-verification.json.
Full assistedcycle complete. 78start1792387063 (05:17:43) exact900s after77,
confirmed soleGUI freshreceipt...T051757775548Z:AHopen/ordinal13/planned428/noinput.
78 completedandfullyverifiedabove. SoleGUI owns next
full cycles. No autonomous engine qualification.

Previously parent independently verified **76**
UID `beta-normal-alliance-1792385263-Arthur-2687`, start04:47:43UTC,
finish04:55:42UTC (479s):428obs/2057rows/412full/16bounded/0incomplete.
Parent original SHA2ce5b4d2f5b38a6676565783550cb4291195cdc1ef8739670affa769b1004adb
and DBlogicaldigest match; exact76ACK loaded in boot1792385864-340613, pending0,
normal0/inactivefence. finish→server105.968071s, interval1329s after75 (429s late).
Public build-70450-seventysixth-scan-parent-verification.json. Raw receipt ends
failed at later tooltip-OCR; ACK stage succeeded and independent normalization
preserves that distinction. Parent independently verified subsequent AH-open PNG
dc967cbd... in boot1792385864-340613/seq132; scheduled77due1792386163,
all buttons released, stationary. Public build-70450-seventysixth-ah-reopen-parent-
verification.json. Full76 assisted cycle complete; no autonomous qualification.
77 started1792386163 (05:02:43), exact900s after76 and completed above.
Parent verified activeframe308 at start, then full saved/DB/ACK/AH cycle.

Previously parent independently verified **75**, UID
`beta-normal-alliance-1792383934-Arthur-2146`, start04:25:34UTC:
428obs/2113rows/414full/14bounded/0incomplete; exact900s after74;
duration477s, finish→server41.017916s. Actual post-save-beforeACK original
SHA6da236d697d8ed7cb8b09b98fc297fc4a186fd2c58a5799a595af048568bd781;
DBlogicaldigest matches; exact loadedACK PNG independently production-decoded.
Public build-70450-seventyfifth-scan-parent-verification.json. Data saved/ACKed.
AH reopened at04:47:43 after final reposition immediately before click. Scan76
started1792385263, due1792386163 (05:02:43): gap1329s after75, 429s late.
The 04:40:34 start was missed. Collection remains operator-assisted.

**Pointer issue diagnosed:** repeated post75 AH clicks failed because capture
can reset the pointer. Parent independently checked motion-only probe rawXI2,
core+sealedtool queries:284,177→1400,100, held beforecapture→284,177 duringcapture;
source4 injected move worked, later source7 motion reset endpoint. No button/key
probe inputs. Receipt raw_motion_events0 is a counting error: actual rawtrace has
RawMotion. Successful AH reopen04:47 preceded the04:50 diagnostic; do not invert
causality. Final collector order: scene/focus capture→final explicit reposition→
fresh endpoint/window guard→immediate button pair, no intervening capture/focus.
Parent production-decoded retained AH-open PNG860ca642...: exact75ACK/pending0,
normal0/inactivefence, scan76 active, character stationary. Public
capture-pointer-reset-and-scan76-parent-verification.json pins rawreceipt/PNG.
Candidate production FixedInput already has this order; no native/inputtool or
new desktop workaround needed. SoleGUI continues76 completion/save/ACK/reopen.

74 previously verified428/2144rows/410full16bounded2query_timeout; actualstartgap
5024s after73, finish→server70.117346s. Its complete save/ACK/AHcycle succeeded;
75startedexact900s later. Sources/partials remain hash-bound and preserved.
GUIprivatehelper first75save failed KeyError(savedvars_before) AFTERactualsave+
upload; continuation preservedactualnewpayloadandloadedACK, don'tduplicateupload.
#74oldpreflushbaseline3e498 isnotnewpayload; rootpreservedactualACKreloadbytes3ac503.

**Recovery now succeeded in the live client (04:09 UTC).** Parent independently
production-decoded actual retained PNG: boot1792382956-926241, normal/0,
valid facing1.4647572040557861, speed0, inactive scanner fence. Public recovery
complete returned recovered for fresh exact reservation; Guardian unarmed,
checkpoint cleared, controller remains PAUSEDgen24/nativefalse/inputfalse.
Separate AH-reopen receipt independently decoded AHopen true, phaseitem and
nextdue1792383934. Recovery scan74 completed and was independentlyverified above;75activecollection
followed exactly900s later. UID is empty during active collection.
Actual start gap from73 is5024s; #74 due03:01:50 and subsequent intervals were
MISSED during fenced recovery. SoleGUI continues fullsave/upload/ACK/reopen;
never midscanreload or claim autonomous900s. Public recovery/AH proof reports.

**Historical startup failure, fixed below:**
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

Diagnostic retention Agentb46e679f/testaf761acb was installed+loaded and committed
c8498ce (pushed). Worker9/parent9(1.84s)/SolREADY. It retains optional private
CrowleyDB.agentRestoreFailure after existing failurecleanup, clears only fresh
restore_pending initialization, no lifecycle/admission change. New soleGUI Luna
finished normal /reload flush (no moreRestore needed), GameMenu closed, Arthur
stationary/world/identity unchanged, allinputsclosed. Old actor is inactive.
That diagnostic-only version is superseded by the accepted behavioral fix below.

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
Actual recovery/AH reopen independently verified above. No native100/input
qualification or autonomous cycles yet.

| Client assumption | Required handling / evidence |
| --- | --- |
| Native movement can be invalid at ADDON_LOADED during reload. | Restore waits for actual PLAYER_ENTERING_WORLD and exact valid movementTelemetry; may retry after world entry for at most30s. This bound is a refusal, not an assumption that world entry guarantees readiness. Actual correction passed live04:09; telemetry facing valid in independently decoded frame. |

Actual private controls manifest:
`~/.local/state/crowley/executor-evidence/native-live-controls-20261019/templates.json`.
Retained actual WoW panel source SHA bfe7fb9ce7c7169fbf52e714e140c0e1f1e560c0077dc8ba4e46c5fe1e2b42c2.
98x27 templates; actual fresh Restore match score0.00063. Fixed Python matcher
on retained real frame costs2.5531s Construct/2.5208s Restore in region220x84.
Standalone Rust scorer final fixes complete, sevenfiles frozen in
rust-template-matcher-20261019. Parent28testsPASS5.62s + two independently
reproduced byte-identical release builds SHA75b18bd04cc3a9248f99ecdca3a1cdebe6e0d89c4d33eaebd600788177bcd80c.
Hermetic build env/config, stable private source snapshot, EXACT official versions,
source-bound artifact test fixture, stronger tie/ambiguity and public benchmark
runner implemented. Parent actual retained-frame publicrunner/reference parity
PASS9.87s; full invocation/hash/log proof rust-template-matcher-parent-r2-20261019.
Final standalone Rust COMPONENT ACCEPTED: parent31PASS7.01s, two independent
reproducible builds75b18..., final actualpublicrunner/referenceparity9.86s;
Sol finaldeltaREADY and actualclaude-opus-5-5 finaldeltaREADY0 on exact7hashes.
NoMust/Shouldremaining. Optionalverbose-log/cache-symlink/extra-fixture nits
nonblocking onverifiedhost; rawverdict preserved. Source7copiedMAIN and canonical
artifact independently rebuilt fromMAIN into~/.cache/crowley/template-matcher/v1,
SHA75b18bd04cc3a9248f99ecdca3a1cdebe6e0d89c4d33eaebd600788177bcd80c.
Helper notinstalled, scorerdoesnotemitinput/acquirelease. No live qualification.

Standalone runtime StageA FINAL SolREADY/parent16PASS0.68s, source
edc5242e9eaf864e98b78b9904b28f8fac51927cc90a6001047a32ab8d36700d,
teste2775104d0974b158f8bff8838a8a64bda80007bf1347ab2df61edf6de1151ca.
OnlyclosedenvLC_ALL=C/cwd=/, verifiedFD/codeownedpins, strictprotocol, deadline/
actualkillreap+FDtests. In private rust-matcher-runtime-integration-20261019.
Lunaworkerrust_matcher completedpreliminarymatching/CLI/sourcebindings wiring there,
helperSHAe0b8c04eeae1e212c47ee34454d4e665b834a9007bbff1fa62dc54a12f43e545;
runtimetestSHA302f74f2098dbd8a2eb6f1d3f417e8fd757b89bf66a6d854e921008661dbfa69.
Parent18focusedPASS1.11s andactualretainedframevsoriginalPythonreference: exclusive
206.79/207.32ms,dual240.53ms, setup0.868ms, includesPNG/hash/process/rolelogic.
AllactualOperatorreceiptsmergeverifiedruntimepins, deterministicimport/script+module
help green. Leaves _record_operation_deadline andoldhelpertestfileuntouched. Parentwillmerge
finalproofworker's phase-minmethod+actualcausaltestbaseline beforefullintegration
checks/review/deploy. Parent now provisionally composed exact47af phase-minmethod
plus test6abbea8664ef6a3edc17e0884b02e45470a3508e31abadf32b592a92c265ca07:
composed helper8776425736b81d0c130380f96f673a0010b79d1382c36e9681cbbfb1b02b1169.
Rustworker resumed finalactualintegration in separate WT; no promotion yet.
Parent fourfocusednewbranch tests PASS2.36s/sourceunchanged, public
native-helper-phase-min-focused-parent-verification.json. Proofworker eightcausalmodes PASS328.08s, full77 running; prior emitterPRESSED
failures retained. Parent then found6abb STILL prearms actualordinary before
helperdefer, causing realdefer refusalalready_set ignored by handler. Workerfix
uses independent constructionseed and asserts actualNone→armed/token/fence/noReload
transition at emitteddefer. Provisional6abb NOT accepted; Rustworker informed
to rebase finalproofdelta, no broadfullcausal run until correction. Narrow
phase-minproduction47af unchanged. New genuineunarmedpreflight passed27.67s;
success failed42s at update1 unexpectedbootchange. Parent pureactualLuaexperiment
confirmed staticseedtoken454944 differs actual856168; Construct/Hold payload4/5
were still static while update6 becameactual. Worker now binds actual4/5 at
accepted actions +exactpublicationasserts; no boot-guard/RNG relaxation.
Genuinecorrected success-causal-r3 PASS147.16s with proof test a38bd17d8d553866
97f3de5ecc6b3588cd31ffaca2eb6f9d5bf1535d0ec259b6. Rustworker resumed exact
baseline rebase and actualcompiledreceipt runtime/binary/3Rust independentpins,
then ONE final full composed suite. Proofworker askedfreeze/report vsredundant
concurrent100-fixture run. No finalSol/Opus orpromotion yet.
See proofplan follow-up. Runtimeworker completed bounded17runtime+7helper+1pin
checks/CLI/Ruff on interim039454test, fullcausal interrupted130 perparentpending
finalproofbaseline. Logs rust-matcher-helper-final-20261019; no fullgreen claim. ReviewedPLAN-rust-matcher-helper-integration.md includes
parallelpreparation. FinalintegrationOpus reviewsallcombinedchanges once; no early
helperpromotion. PriorstageA10/15passes historical, final16authoritative.
Private official Rust/Cargo1.85.1+rustfmt installed under
~/.cache/crowley/rust-toolchain-1.85.1/toolchain; global PATH/game/services unchanged.

Private receipts/images/original payloads:
`~/.local/state/crowley/executor-evidence/runtime-relink`.
Parent verifier `.archive/executor-review/verify_preserved_sweep.py` is private,
not committed. Public exact evidence records are build-70450-<ordinal>-scan-parent-
verification.json. For next completed sweep75 verifier prior_start1792383034; record actual missed
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
Sol final helper review NEEDSWORK on TEST PROOF ONLY: directcontrollerpause
bypasses required publicAF_UNIX; budgetnegative fails beforeREADY and afteran
openingReturn; focusednewbranches/provenance assertions missing. Parent accepts
these concrete gaps; productionhelpercoherent. ActualOpus priorcandidate review completed0/NEEDSWORK onimmutableoldWT.
Additional accepted realproductionbug: phase deadline recheck widensrelease+10s
constructor bound; NEWworker ownshelperonlythatmethod tokeepminallphasekeys.
FixtureMusts: initialpayloads falselyselectordinary forrecover-restore; wrong
clickrole/controlpreflight swaps despiteLua refusal; post-success uncausedordinary
swap; recoverypre-deferSavedVars. MustservetrueLua state/fromactualaccepted
action/reload andpersistedSavedVars, including finalizedclient→restorekind.
ReadactualOpusreport+planappendix, no claimsold73provedthesebranches. Test-onlyfixNOW in NEW native-helper-proof-closure-
20261019 at59046b1, samehelper6f8 +canonicalnative7+FINALaddon79. Worker
luna_profiler_schema_fix owns testfile plus narrowlyhelperdeadline method,
MAIN plan-native-helper-proof-closure.md.
Must actualpublicpause→freshrecovery; firstkeyREADY→watchdogACK→expirybeforeGO
withzeroactualactions/reap/emptyownership; narrowdeadline/allocation/inheritedFD
branches; exact independently knownbytes vsallreceiptdependencydigests. Fullonce
stable, parent changedbranches+successcase meaningfulrepro, deltaSol/actualOpus.
Actualrecover-restore r2/r3/debug repeatedly61s AdmissionIndeterminate. Independent
Sol diagnosis found compositor .b64 payloadfiles overwrittenwithRAWPng afterreal
Restore; GJSreadBase64cannotpublishnextScreenshotArea, secondaryactortimeout.
Lunaappliesbase64encodedatomic600payloadupdates; rawPNGonlyrequestedoutputfile.
No native/deadline/ownershiprelaxation. Sourcehelperphase-minfixremainsnarrow;
finalcausaltests/hashhandoffpending. Diagnosticrawlogs private runtime-relink/
native-helper-proof-closure-20261019. Separatewiringworktree untouchedbyproofworker.
Helper NOT main/installed; never run rejected old candidates. R8/66pass historical.

## Final combined integration checkpoint (05:37 UTC)

Frozen final integration in private `rust-matcher-runtime-integration-20261019`:
helper8776425736b81d0c130380f96f673a0010b79d1382c36e9681cbbfb1b02b1169;
helpertest314e118b497f9814d371553c33706063b6b6bef32da0e472657aa6e73041ed38;
runtimeedc5242e9eaf864e98b78b9904b28f8fac51927cc90a6001047a32ab8d36700d;
runtimetest302f74f2098dbd8a2eb6f1d3f417e8fd757b89bf66a6d854e921008661dbfa69.
Proofhelper47af/testa38 scopedfocusedfreeze is separatelycommitted; final314e
adds actualrestorecheckpointtoken and exact acceptedcommand/control/boot/reload
histories. Prior a962/20f/b8/ee0b are superseded test-only revisions, neverpromoted.
Historical full94r2:86PASS then badfixturecheckpoint ordinary856168 vsactualseed
454944; focusedcheckpointfixPASS19.74s. Historyassertions fixedphaseorder/exact
empty/prefixvscompletedhistory and actualcontrolacceptance. No native/production
changes for these test fixes. Priorlogsretained, not relabeledfinal.

FinalSol **READY**, noMust/Should/Nits onexactfourfinalhashes; public
native-helper-rust-final-sol-review.md. Parent ACTUAL finalpositive100updates +
publicpause/freshRestore→ordinaryrecovery PASS137.10s, sourcepre/postunchanged;
public native-helper-rust-final-actual-parent-verification.json. Private run
rust-matcher-final-actual-parent-20261019/{input.json,run.py,tests.log,result.json};
root exec61766 completed0. Parent22focusedPASS3.22s and finalproductionwrapper
~207ms exclusive/~239msdual referenceparity remain separatelyhash-bound (tests
werea962 in thosefocused/benchmark records; productionthreefilesunchanged).

Worker ONE final full94 **PASS350.13s/5warnings**, private rust-matcher-helper-final-
20261019/full-combined-final-r4.log, exactfinal314e pre/postunchanged. Workercompleted
scopedCLI/compile/Ruff/diffchecks too; no further implementationneeded. Parent
independently verifiedfull94log/mode/sourcepins, public native-helper-rust-full94-
parent-verification.json.
No furtherfull/native367/sourcearchitecture re-review withoutnewconcretefailure.
ActualOpus R1 completed0 **NEEDS WORK**, resolvedclaude-opus-5-5, sourceunchanged,
rawSHA b9e77e9cc33be31898be8b265f7c6d8dd1ade5bf980be3cba67bbf9521c61a81,
1013.23s. Private native-helper-rust-final-review-20261019/{review.txt,process.json,
opus-stream.jsonl,review-input.json}. Root91918/CELL3168 CLOSED, no runningexec.
NoMust, ONEacceptedShould: requireexplicitTemplateMatcher deadline/removefresh5s
fallback, test exactsame capturedeadline through allcalls +actual_click/_postreload
refusal beforeFixedInputemitter/allactualinput. Currentprodcalls alreadypassit;
proofgap/futuremissingargumenthardening, notnewconfirmedlivefailure. Parentaccepted
commentnitclarification was considered but did NOT land; deferred. Other4nitsnonblocking/deferred
(servedframeselfcheck,copyoptimization,receiptclassification,recheckFDmetadata under
hypotheticalinplaceupgrade). Public native-helper-rust-opus-r1-arbitration.json.
LunaRustworker resumed bounded SAME4files forShould+commentonly, runtimeedcshould
stayunchanged; no native/GUI/main/git. Focusnewboundarytests/runtime17 thenfullonce
stable, newfreeze. Parentrepro meaningfulnewboundary tests; Sol+ACTUALOpus NARROW
DELTA against frozen877/314e baseline, no 17minwholearchitecture repeat. Exactold877/314e sourcebaselines recoveredandhash-verified frompreservedsource
fragments in private native-helper-deadline-delta-review-20261019/baseline-*.py.
Also preserved candidate4c3c/d52 before finaltestchainchanges; worker informed.
Newhelper4c3c2aa399cc36b52f42b0af6ef0f1dbe5038fe42d7825c31911d132f17fbb60,
interimhelpertestd52d074ae9904b9d1ac7ee96c63965a1e1bd2242e14e8c2be15b030fc3c843bc.
Newfocused5PASS0.93s andruntime17PASS0.85s; fullcombined98 running in
rust-matcher-helper-final-20261019/full-combined-deadline-r1.log (89dotsat06:02).
ParentcaughtpositiveforwardingtestonlycalledMatcher directly; workeraskedstrengthen
samefunction via ACTUAL Operator._capture and fixedONEdeadline allscreen/runtime
calls. Negative deadlinegetteralsoprecomputedconstant. TESTONLYfinalstrengthening
canfollowfull98 withfocused4andASTcomparison ofallothermodulecode instead of
redundantfullnative100. Planappendixauthorizes truthfulversion-specificevidence.
No R2reviewstarted untilnewboundarytests build; runtimeedc/test-runtime302 unchanged. Previous94/parent137 remainhonest
oldhashproof, not relabelednewsource. No installbefore new acceptedreviews.
Reviewrunner add-dir includes MAIN andownprivate reviewdir. IfREADY, parent copies
exactfourfiles toMAIN, verifies CLI/source/artifact/config pins, commits/pushes;
no service restartneeded for unchangednative7. SoleGUIthenpreflight/native100/
publicpause→freshordinaryrecovery/clearedcheckpoint/AH between completed scans.
GUIalreadyaskedread-only prepareactualargs/profile/templatepins, no calinputuntil
parent announces actualreviewrelease. Controllerfreshreadonly status05:35:
PAUSEDgen24, moderepeat, leaseGeneration1. No mode-migrationneeded.
Then realuserphysicalGTKkey/clickgate, then3autonomous900s cycles. No livehelper,
native100/human/autonomousqualification claimed byofflinechecks.

Latest81 independently verified: beta-normal-alliance-1792389763-Arthur-0881,
428/2094rows/413full15bounded0incomplete,900s after80,finish→server45.35329s.
ExactACK/pending0/AHtrue/ordinary0/inactive/stationary/released; boot1792390300-186600
seq14. Nextdue1792390663 (06:17:43); soleGUI released livecal after81flush.
Backup beta-20261019T061211Z-fc30b9ff6d72 independentlyvalidate PASS/0700,
manifest 3239b52eb82de2008d29e244b1a7f9f3cd203700b80ed8696fefa99a7d57694f. Nextbackup07:12UTC.

## Current release — supersedes historical review status above

Final helper/Rust composition ACCEPTED AND INSTALLED in main at 06:12 UTC.
Exact hashes: helper4c3c2aa399cc36b52f42b0af6ef0f1dbe5038fe42d7825c31911d132f17fbb60,
helpertest6f8ddc4b2091f7928004e9f9d3fab2bdb0077cf88f71afb1367db6404875b21c,
runtimeedc5242e9eaf864e98b78b9904b28f8fac51927cc90a6001047a32ab8d36700d,
runtimetest302f74f2098dbd8a2eb6f1d3f417e8fd757b89bf66a6d854e921008661dbfa69.
Final full98 PASS349.41s/5warnings on these exact hashes (pre/post unchanged),
parent22 PASS1.32s, Sol READY/noMustShould, actual claude-opus-5-5 R2 READY/noMustShould,
rawSHAf0a8f5bdb80b9c171c06bd8cfb4b6c4e45ca93e0621f98825c382a29aa54546d.
Private native-helper-deadline-delta-review-20261019/{review.txt,process.json}.
Public native-helper-rust-final-release-parent-verification.json binds final evidence.
All original comment/performance nits deferred; constructor-test comment NOT fixed.
Unused action-log assertion is not input proof; actual forbidden emitter factory is.
Canonical artifact75b/config0dde independently unchanged; actual MAIN CLI help0.
No service restart: accepted native7 unchanged. Sole GUI released to complete81
save/upload/ACK then actual preflight/native100/publicpause/freshrecover/Restore/
ordinary cleared checkpoint. No physical user gate or autonomous success yet.
Do not rerun architecture reviews or suites without concrete failure.

## New live blocker after promotion

Actual control-preflight06:12 refused BEFORE any key/mouse at closed-chatOCR.
Private native-calibration-operator/native-calibration-control-preflight-
20261019T061245160385Z-2199488-df1ec3be/receipt.json,
SHA6c6959963a93e2e7f9928a72a1bcd4b033ed61d94477ca51fec13da075aaa114.
Parent retainedcrop actualtesseract--psm7 returns `i`; GUIfreshchatEdit inactive/
unfocused/empty proves rightborderfalsepositive, notopenchat. Reservationcancelled;
publicPAUSEDgen24. New .archive/PLAN-native-chat-ocr-border.md, sameLunaRustworker
owns ONLYhelper/test inprivateWT; actual measured current stagedfixedslashcommand
fullframe/crop comingfromsoleGUI, thenEscape/noReturn. No guardwhitelisting/bypass.
Solboundedplanreview; actualOCR+focusedparenttests thenSol/actualOpusdelta before
promotionretry. GUIkeeps82assistedcycle ifpatchnotreadyat06:17:43.

## Chat OCR fix accepted and installed — current helper supersedes 4c3c

Helper e6cde9058a3b8318599824ca6168cd5c3f60a60cb30f28ed1b4a13180d10340f,
helpertest7aae4d94e3b7e436950f519ed1603f2ebbc5b43f3a7c007151ce6b54e620db25.
Actual fullframes closed1d4c34...9340 / stageda53ecd...6458 independently hashed,
production_capture(crop=True)->actualOCR/normalize->_chat PASS closedempty,
typedexact `say: /crowley agent recover`, nonemptyclosedguardnoinput. Parent3PASS0.85s,
worker4PASS/Ruff/compile. Smalltwofilegeometry/preprocessingdelta only; unchanged
98-testrelease evidence remainsversionbound, notrelabelednewsource.
SolREADYnofindings; actualclaude-opus-5-5 READY/noMustShould,
rawSHAb68352a3362e11f284c051a65dcfd53355656826fd0da0231ace45c44683b09d.
Fivecomment/testnits nonblocking/deferred; no sourcechurn. Originalruntimeedc,
artifact75/native7/addon79 unchanged. MainCLIhelp0. Public
native-chat-ocr-final-parent-verification.json; private native-chat-ocr-review-
20261019/{review.txt,process.json}, native-chat-ocr-parent-20261019/result.json.
SoleGUIreleased actualcanonicalpreflight/native100/recovery AFTER83saved+ACKed;
83started1792391563 (06:32:43), no midscaninput. No actualnative100success yet.
Latestcompleted82 independent428/2095rows/411full17bounded/0incomplete,
900s after81,finish→server42.222884s, exactACK/pending0/AHtrue/ordinary0/inactive/
stationary/released. Publicbuild-70450-eightysecond-{scan,ah-reopen}-parent-verification.
Compactlocal-game-control skilladdsfullframeOCRborderlesson; skillvalidatePASS.
Solread-onlyderivingpublichumanGTKsequence afterpause/recover; awaitingreport.
No activeOpusprocess (10716closed0), no ownedoldOCRexperimentleft.

## R2 live command readback blocker — supersedes R1 OCR success scope

83fullyparentverified428/2121rows/412full16bounded0incomplete,900s after82,
finish→server27.143005s, exactACK/pending0/AHtrue/ordinary0/inactive/released.
Original/DB/ACK/AH publicbuild-70450-eightythird-{scan,ah-reopen}-parent-verification.
Then canonicalrecovergen24 ordinary_reload FAILED typed `/reload` readback:
productionOCR `Say {reload`, mismatch→Escape, no submitReturn. Receipt private
native-calibration-operator/native-calibration-recover-20261019T064156080979Z-
2947204-483521d6/receipt.json,
SHA4f5d5d29635098c628baaaee1c7634a0223d669304d78c229f8216db12924787.
PublicPAUSEDgen24/recovery_required; no native100 proof. TypedcropSHA2bfe86436b66f20596833222200cc123001763f622a36b3b37ca8123d61a8666.
R1 had onlyactualrecovercommandproof; do notclaimallcommandsfixed.
SameLunaRustworker R2 twofilesprivateWT; readplanR2appendix. SoleGUIcapturing ALL
FIXED_COMMANDS originalfullframes+independentexactchatEdit, noSubmit, closesaftereach.
Needone deterministic measuredpreproc (or explicitbody-onlyOCRcontract withupdated
tests), allactualfixedcommands+empty/nonempty throughproductionpath before new
Sol/actualOpus narrowreview/install/retry. No unchangedOCRretry. Keep84assisted
at1792392463 (06:47:43)ifpatchpending, no midscaninput.

Solpublichumansequence: failedprepare cancellation leavescheckpointrecovery_required;
FIRSThelperrecover24 ->preflight24 ->publicresume24 returnsNATIVE_CALIBRATION25 ->
measure-deferred25 ->verifyINPUT_CALIBRATION/nativeTRUE/opcomplete/finalized ->
publicpause25 returnsPAUSED26 ->freshhelperrecover26(expectedrestore) ->verify
PAUSED26/nativeTRUE/inputFALSE/invalidatedblank/recovered ordinarycheckpointcleared.
Nativeproofsurvivesplannedpause/recover. Actualreturnedgenerationsauthoritative.
SoleGUIauthorizedwholepublicCLIchain; rootwon'tmutatecontrollerconcurrently.
Stopbeforehuman gate foruseravailability. Laterresume26 ->INPUT_CALIBRATION27,
input-calibrate27 async ->readinessrunning/kindinput/readytrue +visibleownedGTKprompt.
Ask realphysicalpointermotion+keypress/release+click/releaseinsideownedwindow ONLY
whenready. FirsthumaneventPAUSED/gen28 isNOTcomplete; wait~120.5s staleaction rejection
and operationcomplete+nativeTRUE/inputTRUE/evidencefingerprint. Thenresume28 should
RECONCILE. Never resume early whileoperationrunning. No humanfake/no autonomyclaim.

## Current R2 candidate/review handles (06:54 UTC)

Frozen PRIVATE helper0dda3012e14ac8665fbd5bef02e665fbf875419056479cb06a5c9f347c54a3a2,
test56a5c50e6ebf071e7cb77defcf0ca28a6bcba01802386f192112ad5fa23d3314.
MAINstill9db5d47/e6+7aae; do NOT retrymainuntilR2accepted/promoted.
R2 reads only measured command body, preserves grayscale, exacttypedslashcommand;
closedguardnowrequiresstrictEMPTY (oldSay/aliasesremoved). No fuzzyfix/whitelist.
All8GUIstage/noSubmit suite originalreceiptSHA84646abcb14d86c8141c3f08e9ac0b31ab117ecf78cfa5cb0bae09d15d2a081c,
private runtime-relink/chat-fixed-command-suite-20261019T064358713755Z/receipt.json.
Parent FINALALL8 productionX11Screen.chat_crop->originalfullframes->_capture/OCR/
normalize/_chat acceptedexactbody andALL8nonemptyclosedrefusal/noinput PASS,
private native-chat-ocr-parent-r2-final-20261019/{verify.py,result.json}.
Parentfocused4PASS0.92s exact0dda/56a5 sourcepre/postunchanged, private
native-chat-ocr-parent-r2-20261019/{focused.log,focused-result.json}.
Earlierfullframeproof294/b3 preformat retainedseparately; NOTfinalevidence.
WorkerfullhelperpytestPID3175315 running~06:50:47; outputownedanonymousfile, workerwill
preservecompletedlog. Source0dda/56a5 stable. FullaffectedhelpergateBEFOREinstall.
SolnarrowR2reviewrunning; ACTUALOpusR2 CLI session63095/PID3248122 running,
private native-chat-ocr-review-r2-20261019/{run.py,review-input.json,opus-stream.jsonl,
process.json}; review.txtcreatedonexit. Pollattachedsession<=30s, inspectactualverdict,
sourcepre/post,resolvedmodel/no fallback. Runtimeedc/artifact75/native7 unchanged.
Onlysource2filespromotionafterreviewsREADY+fullhelpergreen, no unrelatedsuite reruns.
GUIowns84wholeassistedscheduled06:47:43 (do not inputmidscan); thenacceptedR2recoverfirst
checkpoint->preflight->resume/measure100->pause->freshrecoverordinary. No humanyet.
SolfeasibilityNOallbinarychatEdit: release hasabsentAgentpreConstruct; measure/resume
areheldwithpausedpublisher; recovermayrestore_onlynosurface. Exactvisualreadback
needed; nohybridfallback/redesign. No physicalGTK/autonomousproofyet.

## Current installed R2 — latest state supersedes pending gates above

ALL R2 offline/review gates PASSED. Installed MAIN helper
1cbc51f825fe775847733801354d80ad250201ac0b9e8c5eeb4842980dfad211,
test56a5c50e6ebf071e7cb77defcf0ca28a6bcba01802386f192112ad5fa23d3314.
Parent independently AST-equal to tested/reviewed0dda (only factualcommentsupdated),
exacttestunchanged. Fullhelper84PASS348.83s/5warnings, parentfocused4PASS0.92s,
ALL8originalfullframes throughproductionX11Screen.crop/_capture/OCR/normalize/_chat
PASS exactbody+empty+nonemptyrefusal. Publicnative-chat-ocr-r2-final-parent-verification.
SolREADYnofindings; actualclaude-opus-5-5 R2 READY/noMust,
rawSHA80a8d2b83bd521893cf5a7762df499e90cbbf2ea32c15a4dd530aa90f3ec29af.
OneShouldfactualcommentsfixed (label/body/border/rule/clipping/probemargins), noASTchange.
Specificclosed-alias testcase nit DEFERRED. StickySay/headerlayout is an explicit
measuredclientassumption: labelx17..39/body45/rightborder440, y7ruleretained,
glyphrows20..21clipped. Changedchannel/scale/layout mustrefuseuntilremeasured.
Private native-chat-ocr-review-r2-20261019/{review.txt,process.json,
reviewed-helper-0dda.py}; session63095CLOSED0, noactiveOpusreview.
MainactualCLIhelp0; runtimeedc/testruntime302/artifact75 unchanged. No service restart.
GUI RELEASED wholeactualrecoverfirst/preflight/resume/native100/pause/freshrecover
chain AFTER85saved+ACKed ifactive. Rootwon'tmutatecontrollerconcurrently.
No physicalGTKbeforeactualnative100+ordinaryclearedcheckpointproof/userreadiness.

Latestparentverified84: UIDbeta-normal-alliance-1792392463-Arthur-6323,
428/2089rows/412full16bounded0incomplete,900s after83,finish→server25.055801s,
exactACK/pending0/AHtrue/ordinary0/inactive/stationary/released.
Boot1792392984-179966/seq14. Publicbuild-70450-eightyfourth-{scan,ah-reopen}-parent-verification.
85scheduled1792393363 (07:02:43); soleGUIownscompletion/ACKbeforecalibration.
Latestbackup06:12beta...fc30b9ff6d72 validated; NEXT07:12UTC (after85ingestionifready).
No autonomousqualificationyet: recentcadenceisoperator-assisted.

## Remaining live gates

- Actual WoW Construct/Restore controls have now been captured and measured
  (private actual templates above); earlier full-frame template image was
  synthetic, GTK certificates have screenCapturedfalse.
  Construct/Restore are WoW Frames in Commands.lua, NOT the later human GTK window.
  Panel220x84 UIParent units TOPRIGHT(-24,-24), buttons100x28 offsets(8,-8)/(112,-8).
  UIParent1365.33x768 vs physical1920x1080 is not a measured button transform.
  No guessed coordinates/templates. GUI Luna has read-only prepared source facts.
- Native7 and addon79 are installed. Actual ordinary recovery/cleared checkpoint/
  PAUSED/unarmed/AH reopen succeeded04:09 and subsequent assisted scans74–77
  proceeded; historical startup failure is fixed. Do not run rejected helper.
- Finish exact helper+Rust runtime composition, parent relevant verification and
  final Sol/actualOpus delta review. Then install accepted exact helper+adapter,
  soleGUI runs inactive control preflight and fresh native100 between scans.
  Actual retained-frame integrated matching now measured~207ms exclusive/~241ms
  dual with exact reference parity. This excludes live capture, does not qualify
  native100 and is not a claim of40ms whole-pipeline latency.
- Only when actually ready request genuine human GTK physical key+click gate.
  No user action needed now. Never fake human success.
- Then three autonomous900s save/upload/ACK/reopen cycles. Only then complete.

## Preservation and working rules

Latest hourly backup `beta-20261019T051304Z-a3a4ac88b124`, parentvalidate PASS,
manifest SHA3839cfad5532e6c22d9711b2adf325b7e2b09b1b0b9968f4d7d64477eb29f85b,
0700 directory, after77 ingestion; all new originals retained. Next hourly06:13UTC.
Run `uv run python tools/market_backup.py snapshot`; independentlyvalidate_snapshot.
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
