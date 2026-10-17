# Unified engine correction, round 6

Sol verdict MAJOR ISSUES on stable controller5 despite30ownedtests passing.
Controller/daemon must now be corrected under ONE owner and shared typed contract.

## Must fix

1. reconcile() ignores restartUncertain after fresh gates, restores old dispatched
   SAVE_RELOAD_SENT and permits replay. Characterselect/noAgent logout_wait goes
   LOGIN_REQUIRED, bootstrap returnsworld, then restores DISK_CLEANUP_WAIT forever.
   Build executable per-intent observation-only recovery across external scenes;
   uncertainty must resolve from honest action-specific proof before any replayable
   state. Completed logout at characterselect must remain completed, not relogin.
2. Realdaemon setsliteral /reload intent withoutdeadline; reload_sent renamesit
   save_reload and incrementsattempt. Preparedtest usessemanticnameandzerodeadline,
   concealingactualcaller. Define ONE canonical typed intent identity/deadline
   across preparation/dispatch/observation/controller states. Stop during actual
   QUIET_SAVE dispatched /reload currently becomesSTOPPED with uncertaintyfalse;
   freshowner neverreconciles. Preserve allinflightuncertainty acrossstop/pause/
   restart in EVERY state, no newinput afterstop, no replay onresume.
3. GenericUIDabsence cannotresolve any arbitraryintent. scanner_phase=None plus
   assertedidle abandonsunknown effects; open_ah dispatched + unrelatedoldUIDabsent
   isalsoabandoned. Requireactualper-intent scene/boot/scanner/stablefile witnesses.
   Positiveack_reload recovery currentlyjumpsREOPEN pendingtrue/streak0/noarchives,
   silentlylosingqualification. Complete normalexactUIDqualification onrecovery.
4. qualify acceptsUIDb aftersave/upload/ackUIDa and doesn'tbindstableevidenceor
   actualupload/publication/loadwitnesses. uploaded acceptsfinish+9898latency.
   Bindallqualification to EXACTone persisted savedUID/format2proof/house/build/
   plan plus <=60s actualupload and publication/load witnesses; no publicalternate
   path around proof. Globalcadence3new428qualifiers/no4thcloseout unchanged.
5. Outcome archive multiappend isnotfailureatomic/idempotent. outcomeArchivedset
   BEFOREappends suppressesretry afterfirstfailure, producing0proof; partial
   run/evidencepublication then cadencefailure+restart createsduplicates andwrong
   counters. Use stableoutcomeidentity and atomicdurablebundle/transaction or
   equivalent; crash atEVERY publication/checkpointboundary mustrecoverEXACTLYone
   logicaloutcome withcompleteproof andconsistentboundedcheckpoint/counters.
6. Invalidqualification discards existingupload/publication/loadtimestamps before
   archive andresetsstreakbeforeacceptedBefore. Preserveallpriorevidenceandstreak
   inaccepted/rejectedrun/cadence/ackarchives regardlessreason/retry.
7. Protocol _keys sortsheterogeneousunknownkeys ->TypeError; method=[] setmembership
   ->TypeError. Allmalformedvalues mustyieldProtocolError. Activecursor999999999
   outsidepinnedplanaccepted; enforceactualconfiguredplanmembership atproduction
   validationboundary (schemaalone lacksIDlist), no thinfixture/globalbypass.
8. Buildtypedmismatch: telemetry.clientBuild='70374'; canonicalscanPlan.targetClientBuild
   is'1.60.1.70374'. evidencepinscorrectfullbuild; daemonpassesconfig.client_build
   shortbuildandallrealDatareads fail. Distinguishcorrecttypes andpinfullcanonical
   planidentity withoutlooseningvalidation oracceptingaliases.

## Also fix

- Remove/unifyunusedalternate reload_observed/acknowledged/ack_reload_sent,
  STOP_REQUESTED/CLOSEOUT_REQUESTED pseudostates andsaved(stable=True) route.
  Oneproductionlifecyclewithstrictlegalstates andpostIOfences, testsuseactualpath.
- Encoded428positivequalifier test needs nonemptyVALIDownedrows andexactperitem
  row/pricedcounts, ownedcounts andnormalization, notonlyemptyownedsection.
- Fsyncarchiveparentdirectoryentries whencreating .archives/kind directories.
- Remove duplicateackstatecheck, ignoredarchivekindparameter, misleadingtests.

## Required verification

Actualdaemon-style /reload and/logout preparation/dispatch withnonzerodeadline;
stop/pause/crash atallrelevantstates; unresolved/freshgates/reconcile cannotreplay;
characterselectcompletedlogoutneverrelogs; ackrecovery exactqualification;
mismatchedUID andlateuploadrejected; archivefailureinjection everywriteboundary
acrossfreshowner restart/retry no missing/duplicatelogicaloutcomes; rejectedproof
keepsalltimestampsandpriorstreak; malformedprotocolcanonicalerrors+cursorcontext;
actualstagedprofileplan/telemetrybuild types viaread-onlyconfiguration fixtures.

Parent/workerchecks: stableowned30pass, independentengine25pass(parent5.33s),
runtime88pass1nativeecho-retentionfailure. Solreprosaboveallactualexit0, Ruff/
formatpass, noedits/GUI/services/privateconfig/DB. Native7 separateowner fixes4native
modules/2ownedtests. Unifiedengineowner exactfence recorded inplan; independent
testfiles remainexclusive testowner. NoGUI/services/config/DB/commits duringcoding.
