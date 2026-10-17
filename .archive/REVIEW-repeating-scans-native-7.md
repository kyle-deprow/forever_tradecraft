# Native re-review, round 7

Sol verdict MAJOR ISSUES. Native6 corrections are present but incomplete; no
native/bootstrap/non-game GTK input is source-cleared. Native owned44tests pass.
Independent native33tests:27pass6fail; runtime lifecycle also fails echo sealing.

## Complete fix batch

1. OwnedGtkCalibrationWindow._verify parses wmctrl-lp wrong: actual five fields
   XID, desktop, PID, client-machine, title; currentfixtures omit desktop. Parse
   split(maxsplit=4), allow desktop-1, exactPID/title. Use real-format fixtures.
2. Seal a synthetic/human phase boundary. HumanMotion is required in realX11 path
   but combined proof runs every nonXTESTMotion through synthetic echo validation,
   so genuine human takeover motion is rejected. Echo correlation must use ONLY
   synthetic prefix; human suffix retains actual deliberate takeover events.
   Emptyhumanmotion must not fakeproof; genuinehumanmotion must not beecho.
3. Echo seal verification reconstructs syntheticMotion using forwardeddevice as
   master, making(7,4) instead of correct deliveredsource4(4). Correct class-specific
   facts consistently across measurement, verification, evidence retention/resume.
4. Runtime still compares events to old calibration target/coords/timestamps rather
   than recording current source4 Motion then its source7 echo. Implement action-local
   pair state: exact measured current anchor target/coords/modifiers/timestamp,
   calibrated relationship and bounded measured delta, at most matching echo.
   Source7 before current pair or foreigntarget revokes. Generic device_by_class
   Motion=4 must not reject already-proved7(7) echo; positive test must use actual
   production DesktopDriver dispatch, not patch that map to7. RecordedBattle.net
   source7 withno4pair remainsclosed and supplies NOpositiveproof.
5. Helper ownership stillbroken: direct observer.stop clearsprocess beforedriver
   unregister canfindPID; staleobserver PGID retained. GTKregisteredonlyatticket
   longafterPopen, GTKcloseconfirmedexitneverunregisters, preventingresume.arm.
   observer registration occursafter monitor.start spawn/startupwait. Implement
   actualgatedexecutable startup for GTK+XI2: spawnwrapper -> registerPGID with
   watchdogunderfence -> releasepostexecpipe -> readinesswaitOUTSIDEfence.
   No blockingpreexec. Retain PID/process untilconfirmedwait; unregisterexactly
   afterreap; retainretryhandleonfailure. End-to-end workflow must end withno
   stalehelpergroup and actualsameprocess resume.arm succeeds.
6. Nativecapturetimes onlynonnegative/increasing acceptsancient101frames.
   Enforcefinite originalcapturetime, futuretolerance, <=5sage againstinjected
   runnerclock EACHcaptureconsumption independentlyprovider. AnchorNaNpassesseal
   andagecomparisons; requirefiniteoriginaltime beforesealing+verify+oneuseadmission.

## Also fix

- Remove unused install_measured_anchors compatibilitybatch or validate per-action
  mappingincludinggame_client. Correctreconnectbatchcurrentlyrejected.
- Guardian anchorcoordinates mustbind ButtonPress/Release and currentMotion,
  notonlyEnter/Leave. Clickelsewhereinsideownedwindowmustreject.
- Schedulecapability-boundfullhumantimeouttimer BEFORE externallyvisiblereadiness.
- Remove duplicatepointermodifiercomparison, unusedexecution_gate plumbingleftover,
  obsoleteforkcommentsaftersafespawn.

## Tests and integration

Add meaningful production-path regressions for each finding, including full valid
syntheticprefix+humanmotion suffix -> sealedproof -> retainedproof -> resume.arm;
realhelperprocess gatedstartup/ownerdeath/reap/emptyregistry; temporalruntimeecho
through actualdispatch withunchangeddevice map and differentruntimecoords/times;
ancient/future/NaNcapturecases; validrealwmctrl rows anddesktop-1. Do notweaken
negativecasesor invent simplifiedtrace formats. Independenttestowner alone owns
its two files; nativeowner retains samefourproduction/twoownedtest fence.

Verifiedcorrect: positiveargvschemas/explicitauthority, processcommandexecwrapper,
release-failurecalibrationboundary, exact12event incrementalparsercrossingfields,
GTKchildACK/recertify, postprep timer placement, sameartifactrender equality,
originaltimeplumbing, newerpostconditions, safespawn, strictpeakgate/profileints,
livegame_client reconnectmapping, consumedcapturecleanup. Preserve these fixes.

Solchecks:44ownedtests8.40s strictthread/unraisable/forkwarnings; focusedindependent
seal2fail andbatchreconnect1fail/1pass; freshnessreproancient/NaNadmitted; Ruff/
formatpass; noownedhelperorphans; noGUI/input/source/service/config/DB mutation.
