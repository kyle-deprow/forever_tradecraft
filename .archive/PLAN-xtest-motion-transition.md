# Canonical attached-XTEST motion transitions

Status: SOURCE READY and frozen after actual Opus r12 (claude-opus-5-5/CLIexit0) and Sol final-r4 READY/no findings. Parent full strict DB754passed plus final25focused checks and global checks pass. Final43-path freeze source-freeze-transition-r12-test-closure-final-r1.json; all hashes match, and implementation bytes remain identical to Opus approval after the final test-only closure. Earlier arbitration/review reports remain preserved. No coding worker has further source authority. This document grants no GUI/input authority; root separately released exactly ONE owned-GTK seed-only outcome. Preserve the contract and fence below; do not reopen unrelated design.

## Evidence and intended behavior
Actual one-seed failed under old endpoint interpretation: source4 Motion root/event873,576 (prior origin), deliveredaxes1113,576 (new endpoint), pairedRawdetail0/time303971237; actualpostpointer1113,576. Currentreceipt remainsFAIL. Officialmatching Xserver and XI2 source establishes slave-before-master processing, xinput prints deviceid(sourceid). Source/profile references are retained under executor-review/xwayland-24.1.6-source and xinput-1.6.4-source with provenance/SHA. This is genericDIX; no desktop switch.

One canonical interpretation for the pinned absolute-XTEST command: delivered axes prove endpoint; native root/event prove transition origin; raw proves same-time ancestry. Require every part, existing target/window/modifier/ownership checks, and post-query result. The slave child is the window at the ORIGIN, never endpoint ownership. Initialorigin must already be inside the ownedtarget and query-confirmed; refuse beforedispatch ifoutside. Endpoint ownership comes from exactpostquerywindow and buttonpress/releasechild. Remove helper outside-seed movement; it must refusewithoutinput. No OR root/axes, no raw-only endpoint, no guessed axes or ignored unknown records. Human/non-XTEST relative Motion keeps its own existing semantics. Current native profile: source4 attachedtomaster2, XTESTDevice1/Enabled1/CTMidentity, exactly2 axes0RelX/1RelY ModeRelative range-1..-1 resolution0,3classes/10buttons, root/screen0=1920x1080at0,0. Never hardcode actual sourceID/PID/XID. Absolute endpoint semantics come from pinned absolute command/server source, NOT an advertised absoluteaxisrange.

## Implementation order / exact contract
1. Parser/shared representation in input_events.py. Retain the existing device_id property (fix misleading docstring; it is actualdeviceid, not alwaysparent/source). Append immutable parsed valuators `(axis, value, raw_value|None)` to XI2Event. Retain native root/event/rawlines unchanged; firstdevicefield isdeviceid, existing master_device name may remain with explicitdevice_id alias to avoid unrelatedrename. Strictly reject duplicate/nonfinite/malformed valuator rows; preserve streaming completeness and failure text/cause. Do not assign endpoint meaning in generic parsing.

Provide one immutable XTestMotionTransition and shared decoder for a profile-proven attached XTEST source under a canonical absolute command. Require Motion/deviceid==sourceid==expectedsource/detail0, exactfiniteaxes{0,1}, expectedroot/eventXIDs, nativeoriginroot/event. The observer selects --root: requireeventXID==rootXID and nativeeventXY==rootXY. Endpointroot=deliveredaxes; endpointevent==endpointroot. Rejectnonzero root-eventoffset ratherthanaddingunusedcoordinate mode. Preserve actualnativefloats; canonicalabsolute rootaxes must befiniteinteger-equivalent andexactlyequalplannedintegers, with no rounding. Current gamewindow is pinnedat0,0; GTKoffset must use root/root traces, notclient-relativeeventhalves. Decoder never acceptsRawMotion. All consumers use this helper, not independently reimplemented coordinate math.

2. Seal/recheck exact profile in calibration.py/driver.py. Parse native xinput list --long <positiveid> and list-props <positiveid> output with exactmeasured classes/axes/mode/range/resolution/Enabled/XTESTDevice/identityCTM, hierarchy source/parent/name. Add only these exactread-onlyargv shapes and existingrootstats ifneeded; no genericxinputcommandallowance. RequirepointerquerySCREEN0 and bound actualrootXID/geometry/profile. Record fresh actual pre-move origin, requestedendpoint and postqueryendpoint/window. Exclude mutable Button state from the structural profile. Profile/parsedvaluators/origin/result are included in evidence fingerprint/seal and replay; old evidence fails loudly, bump DRIVER_VERSION. Preservepointer_position three-valueAPI, but nativeoutputmustcontainSCREEN0 orraise. Atarmandonceperpointeraction, re-read/compareprofile/hierarchy/root BEFORE originquery andbegin_action, within existinggeneration/actionownershipfence; recheckgeneration/profileepoch atfinaladmission. Do not runprofilequery subprocesses inside dispatch-admissioncallback or between motion and clickcommit; never waitforobserver whileholdingGuardianlock. Anyprofile/mappingdrift invalidates. No new account/config/settings/session/tool-artifact changes.

3. Guardian.begin_action/ActionCorrelation keep existing4tupleendpoint traces. Add explicit initialorigin4tuples for positioning and held/clickmotion and expectedroot/eventXIDs. For every canonicalprimary require FIFOraw same CARD32timestamp/detail/source/parent; deliveredendpoint must match STRICT NEXT traceindex, and nativeorigin must equal the last ACCEPTED endpoint (explicitinitialorigin for firststep; certifiedpresspoint forheldmotion). Remove forward-skippinglookup forcanonicalmotions: rawbetweenmotions preventsservercoalescing, onecommandgivesoneslaveMotion. Never roll back retainedarrivalclock. Do not skiptracepoints or guessmissingevents. No weaker compatibilitytrace mode for nativeinput.

Mastercopy support is DEFERRED: nativecaptureobservednone; keep revoking Motiondevice=parent ratherthanaddingunprovedoptionalacceptance. Retain such a futurefailedrecord forsourceanalysis. No master whitelist, decoder orstate isadded inthisbatch.

Controlled forwarded echoes match ONLY the LATEST acceptedprimary normalizedendpoint root/event plus exactroot/event/childXIDs/modifiers/effective/source relationship and existing250msCARD32bound. Atmostone primary can have pendingechoevidence; all requiredcurrent echoes mustcomplete before nextprimary; stale/late/nonlatest echoes revoke. Do not retain an older-primary queue. No echoes were observed with correctedcanonicalXTEST; DRIVER_VERSIONbumpforcesfreshlearning, neverinheritoldwarppath echoevidence. Fix inaccuratecalibrationforwardedmotion comment. Primary nativeorigin remains audited. Calibration _controlled_echo_proof and evidence verification use identical semantics; physicalhuman validation never calls syntheticdecoder. Fix InputCalibrationEvidence.verify_seal itself: MotionEcho timestampsindexes1/7 use shared strictCARD32validity, elapsed(primary7,echo1) must be0..250; IDs/XIDsstaypositive. Auditserver-event proof domain/order through actualseal/replay, neverusewalltime/receiptagesasCARD32. Preserve proof0valid timestamps andpositiveIDs. Tests MUST run actual _controlled_echo_proof -> _build_evidence -> verify_seal -> DesktopDriver.arm -> begin_action unchangedMAX→0; directGuardian evidencefakealoneisnotacceptance.

4. Producers. Driver click captures actualcurrentpointerorigin and passes it before motion; existing pre-clickcommit query plus postclickquery must exactlymatch endpoint/ownedwindow. Camera positioning starts at actualpointer; drag starts at certifiedpresspoint; verify exactpostdrag pointer/ownedtarget beforefinish. Requiredcalibrationprofilechecks must fit existingfinite deadlines/evidenceages, not relax them. Preserve heldstate/process/ticket/watchdog/admission/cancel contracts and all budgets.

Synthetic calibration emitter requires already-owned query-confirmed origin and captures it immediatelybeforedispatch, exactpostrequestedendpoint/window, retains deliveredaxes/transition and binds seal. Runtime inputprofile revalidation is mandatory on native/default path. Fixtures model fullcurrentprofile; do not add production defaults for incomplete testEvidence.

Proof helper uses shareddecoder for seed/wait/path/duration/echo; actualseedstart is explicitorigin and mustalreadybeinsidecertifiedownedtarget; outsideinitialpointerrefusesbeforeanydispatch, actualpostquery is required. Receipt records nativeorigin, parsedvaluators and normalizedendpoint separately. Positive/cancel evidence unchanged in scope. No GUI until reviewedfrozen source and rootrelease.

## Owned file fence
Production ONLY:
src/crowley/session/input_events.py
src/crowley/session/calibration.py
src/crowley/session/guardian.py
src/crowley/session/driver.py

Helper ONLY:
.archive/executor-review/owned-gesture-proof.py
.archive/executor-review/test_owned_gesture_proof.py
.archive/executor-review/owned-gesture-proof.md

Tests ONLY:
tests/test_session_native.py
tests/test_session_native_regressions.py
tests/test_session_dispatch.py
tests/test_session_driver_actions.py
tests/test_session_executor_dispatch.py
tests/test_session_motion_integration.py
tests/test_session.py (only complete native input evidence fixtures/seal expectations)
tests/test_session_regressions.py (only native/default-path evidence/observer fixtures)
tests/test_session_executor_movement.py (ONLY shared native input profile/observation fixtures affected by this contract; no D1 geometry/calibration travel/planner behavior or assertion relaxation)

tests/test_session_runtime.py (ONLY affected native command/query/evidence lifecycle fixtures; no controller/lifecycle assertion relaxation)

Parent owns this plan/reviews/docs/skills/freezes/git. No daemon/executor/motion/model/controller/addon/protocol/profile/service/schema/data edits. If anotherboundarymustchange, report exact need beforeediting. No globalformatting, no commit/reset/stash/revert others.

## Acceptance / verification
- Actual retainedRaw+slaveMotion fields decode preservingoldorigin andnewendpoint. Missing/extra/duplicate/nonfiniteaxes, wrongorigin/axis/root/eventXID/source/parent, nonzero root-event delta rejection, noRaw/partialRaw/wrongtimestamp are covered.
- RealGuardian acceptedtrajectory and right-heldcamera entrypoints use oldorigin+deliveredaxes, actualbegin/dispatch/check/finish and independentexpectedtrace; correctpostqueries required, mismatchrefuses. MasterMotioncopy remainsunsupportedandrevokes; do not fabricateacceptance. Echoendpoint accepted; origin/wrongXID/modifiers/reverse/>250ms rejected; actualcalibrationproducer→seal→driverarm→Guardianhandoff including0 isrequired. Outsideorigin refusesbeforeinput; finalendpointoutsideownedtargetfails exactpostquery evenifsourcechildisowned.
- Calibration producer/seal/replay and profile drift (CTM/source/parent/axes/mode/range/rootscreen/geometry) fail closed. Humanrelativeproof semantics remainunchanged. InstalledIPC externaldoubles emitcaptured nativecontract and updateactualsimulatedpointer; do not stubownership/calibration gates.
- Helperactualseed success/error/receipt diagnostics/noop remainscovered; wait/proofusesnewendpointandoldorigin. No nativeclaim from fixtures.

Worker runs strict hermetic affectedfiles with privatelease, scoped Ruff/format/compile. Parent independently reproduces meaningfulconsumerchecks, inspectsdiff, obtains focusedSol+actualOpusimplementationreviews on unchangedfreeze. Fullregression afterintegration uses disposableDBonly; no productionDB. AfterREADYrootreleases ONE actualownedGTKseed; success thenpositive/cancel-midpath/cancel-midhold. Preserveallfailedreceipts and exactprocess/globalleasecleanup. ActualWoW/human/motion/cadenceacceptance remains separate.
