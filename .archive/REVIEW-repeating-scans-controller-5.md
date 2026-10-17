# Controller/evidence final review, round 5

Sol verdict MAJOR ISSUES. Stable component review after engine4 corrections.
No live activation or physical sample is cleared.

## Must fix

1. Restart uncertainty bypasses fresh gates: resume checks restartUncertain
   before native/input validity and enters RECONCILE. resolve_restart can reach
   WAIT_DUE/SCANNING with both gates false. It accepts in-memory UID/boot change
   as upload evidence or abandons pending work without proving scanner idle and
   exact UID absence from stable format2 files. Unknown outcomes require strictly
   observation-only reconciliation with complete scanner/file facts, then fresh
   gates before any active state. Unproved effects remain unresolved; never replay.
2. saved() starts new save_reload attempt after caller persisted/dispatched reload,
   losing attempt/result (1,/reload,dispatched becomes2,save_reload,pending).
   stop branches replace in-flight intent/result/deadline with stop, violating
   orthogonal stopRequested and leaving dispatched reload without usable intent.
   Pause does not mark dispatched effect uncertain; resume can replay it.
   Preserve per-intent identity/result/deadline across observations and stop/pause;
   reconcile uncertain effects, no replay. Reset only for genuinely NEW action.
3. Upload/block/cadence failures do not archive complete rejected run/cadence/ack
   evidence. Upload reject leaves qualification=pending, no run/cadence/ack records.
   Ack archive omits upload/publication witnesses and latencies, accepted run does
   not copy bounded evidence metadata. totalAccepted uses trimmed accepted length
   (20 vs21 archived). Cadence acceptedBefore captured after zeroing streak;
   cadence rejection leaves pending=True. Preserve complete immutable rejection,
   ack timing/publication/latency proof, monotonic total counters, correct pending
   lifecycle and pre-reset streak.
4. evidence cleanup accepts missing scans/sweeps as empty: CrowleyDB={} returns
   disk_queue_empty=True. Data scanPlan integer0 accepted as False/absent. Require
   both explicit exact queue fields/types and pinned external plan/build; malformed
   schema can never establish empty closeout/startup.
5. Protocol malformed values escape/are accepted: textureCount16384.0, blockedfalse
   with unknown nonemptyreason accepted; phase=[] raisesTypeError instead of
   ProtocolError; decompression exactly16385bytes invokesflush(0), ValueError.
   Strict nonboolean ints, typecheckbeforemembership, exactpendingreason relation,
   bounded inflater canonical ProtocolError for all malformed frames.

## Should fix in batch

- PostIO observation fences must not be optional paths around legal source-state
  admission. saved/stable_saved/uploaded/ack_reload_complete/qualify/cleanup_complete
  reject illegal states independently. Remove unused alternate reload_observed,
  acknowledged, ack_reload_sent paths bypassing production freshboot flow or unify
  them under the one strict path. Tests should exercise real production lifecycle.
- Direct qualify_saved_scan test through encoded 428-item native payload: exact
  house/build/plan, full per-item row/priced counts/owned rows and empty-native
  normalization. Handmade stable_verified SweepEvidence alone is insufficient.
- Meaningful regression coverage for >20 accepted runs, upload/ack rejections,
  pause after dispatch, stop in every reload state, strict restart resolution.
  Existing test expecting unproved abandonment encodes incorrect behavior.
- Journal legacy list migration timestamps must be deterministic/idempotent across
  crash after artifact publication before checkpoint replacement; otherwise retry
  conflicts with immutable artifact and permanently fails. No compatibility paths
  are required for unshipped state; remove unsupported legacy migration if suitable.

## Verification

Sol initial47pass; final strict concurrentnative run43pass4fail (nativefixtures
moving); stablecontroller subset15pass, allactualexit. Ruff/format/diffpass. No
edits/GUI/service/privateconfig/DB mutations. Generation/state/attempt fencing,
new-owner epoch bump, complete item counts, calibration newfields, globalcadence
normal3cyclecleanup were confirmed corrected. Address all remaining findings as
one batch within controller/journal/protocol/evidence and owned3tests only.
