# Engine review, round 4

Sol verdict MAJOR ISSUES; no GUI/user sample or controller activation. Two real
IPC runtime tests pass, but production counterexamples remain.

## Must fix

1. Observational transitions overwrite pause: daemon stale SCANNING status then
   saved() produced QUIET_SAVE gen1 after pause. All I/O outside lock, then atomic
   expected-generation AND expected-state compare/transition under Controller.lock
   for saved/stable/upload/ack/reopen/adopt/cleanup and metadata writes. No stale
   transition may erase pause/stop/block or cross a resume epoch.
2. restartUncertain is permanent: resume blocks, pending prevents start, no clear
   path. Fresh telemetry/files must reconcile actual outcome and abandon/complete
   uncertain intent without replay, then new generation can advance. Do not simply
   clear uncertainty or replay possibly-dispatched effects.
3. uploaded() changes intent to ack_reload but keeps previous dispatched result;
   stop then stays ACK_RELOAD_SENT forever. Bind attempt/result/deadline to each
   unique intent and reset atomically on new intent.
4. Closeout misreads blocked-backpressure as active scan, fabricates startedAt.
   Two valid blocked frames changed DISK_CLEANUP_SENT to SCANNING. Adopt only real
   active scanner phase/start/ordinal. Final logout reuses old scan/queue snapshot;
   chat-readback discards fresh scanner state. Require final fresh evidence and
   prevent scheduled auto-start race with a proved addon schedule fence or safe
   equivalent; exactly one logout and no abort of an intervening active scan.
5. Model inference can take45s then evidence timestamps are reset to NOW, bypassing
   freshness. Preserve ORIGINAL capture monotonic/identity/boot/sequence, bound
   inference by freshness, reread target/telemetry after inference and reject stale.
   Require expected boot+sequence relation, not sequence only. Recovery graph
   still asks reconnect from disconnect_dialog after dismiss led to game_client.
   Match actual controls on four-scene graph.
6. Per-item proof omits rowCount/pricedRowCount/owned rows. Preserve complete
   structured proof. start(validation) erases prior accepted run. Rejections/
   cadence/ack metadata overwritten, block doesn'tmark rejection, mixed history
   evicts intervention/restart/pause. Accepted evidence unbounded duplicated in
   1Hz journal. Use bounded live checkpoint plus durable immutable run/evidence/
   intervention archive without deleting prior proof. Full calibration serialization
   must include NEW mandatory managed-frame/modifier/echo/keymap/profile fields;
   persist anchor/model capture/timing/use evidence too.
7. Lua peak fallback notproved: with debug=nil and inside-serializer1000KiB witness,
   output said0. Hook cannot see alloc/free insideC; discretebefore/after sampling
   silentlyunderreports. Implement actual peak-capable mechanism with verified
   live API semantics and controlled transient witness, restore priorGC/hookstate.
   If unavailable publish unverified capability and FAILnativegate, never report
   net-retained bytes as truepeak. PinnedWoWAPIavailability remains unproven; no
   claim that stop/restart/isrunning/debug are unsupported until native evidence.
8. Startup accepts nonexistentSavedVars/companion/Data when parents exist. Require
   canonical existing expected files and schemas/plan. Model acceptsrelativecodex
   and defersversion untilfirstcall. Requirecanonicalabsoluteexecutable/exactversion
   beforearming/startup. Actualstagedpaths/bin arevalid, enforcecontractanyprofile.
9. IPCshutdownjoin5s doesn'tverifyownerexit, releaseslease/socketwhileowner/handlers
   maystillalive. request_shutdown swallowclosefailure. Cancel/track/joinowner+
   handlers toconfirmedtermination beforeleasing/unlink, surfaceclosefailure;
   retainownership onincompleteclose.
10. Native bootstrap checksgenbeforecaptureonly/storesnone; pause/resumecanconsume
    oldproofwithin10s. Bindadmittedcontroller/nativeepoch, recheckaftercaptureand
    consumption/baselineready, neverreuseacrossepoch.

## Known native/lead integration

Default modelanchorproducerstillconstructsunsealedMeasuredAnchor. Mustretainactual
captureandcall driver.build_measured_anchor withcapture_path/fullscene/bounds/
generation/ancestry, recordmodeltiming andaccepted/rejectedproof. Native5 builder
signatureisnowpublished. No injected-only provider proof.

## Should fix

Strictnon-boolschema/count/coordinateints; exactshoppingLists shape/pinnedbuild;
exactmodeloutput/eventschemasrejectunrelated/extraobjects; removedeadmanualanchor
parsing; canonicalabsoluteconfiguration/servicepaths.

## Corrections / ownership

Controller owner: controller/journal/protocol/evidence andtest_session/test_evidence/
newtest_session_transitions. Daemon owner: daemon/CLI/config/model/addon/harness/
deploy/docs/runtime/addon tests withinpriorleadfence. Nativeownersretainfourfiles;
independentowneralonechangesits2regressions. Coordinateexpected-generation/state
observationAPI, intent resolver andpeakmetricsschema. No GUI/services/privateconfig/
DB/commitsduringcoding. Add meaningful concurrency/restart/closeout/schema/peak/
shutdown real-path checks andrunrequiredchecks thenSolreview.
