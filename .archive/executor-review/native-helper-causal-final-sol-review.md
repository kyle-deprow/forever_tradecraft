# Final helper causal-composition Sol review

Read-only /root/sol_helper_causal_final, frozen helperffc8ae4f/testd4834f54.
No edits/tests/builds.

## Must-Fix

1. Helper3715–3733 assumes pause mutating response includes calibrationOperation
   and guardian; production response has controller fields/state/generation/
   leaseGeneration only. Mandatory operation check always fails, preventing
   actual Operator.run error→new-PAUSED→empty-ID recovery. Direct-client error
   test masks this. Validate immediate PAUSED/new generation/higher lease, fetch
   aggregate status for nonrunning native op, require new canonical recovery
   binding higher guardianGeneration and guardianArmedfalse before input. Prove
   whole run preserves original exception/failure receipt through recovered.
2. Only measure mode has real causal X11Screen/FixedInput/compiled fixture. Other
   modes/error tests use FakeScreen/FakeInput/raw observations/direct client.
   Reuse real fixture for control preflight, ordinary and restore recovery,
   failure/newPAUSED/emptyID, post-handoff cancel, actual readiness/physical
   READY/watchdog/GO/PRESSED budget negatives with ACK-caused scenes.
3. Receipt provenance mismatches: screen tool differs from FixedInput sealed
   artifact; no helper_source_sha256 and only producer dependency. Patch allowed
   real tool factory for shared sealed artifact, use real source bindings,
   assert receipt helper/config/templates/producer/input/native hashes.

## Should-Fix

1. _record_operation_deadline3014–3019 assigns new reported value in both branches,
   allowing later extension. Keep minimum or refuse increase; test actual method.
2. Allocation cleanup: OwnedEmitter1253–1259 invalid processgroup raises without
   aborting child; Watchdog1569–1571 accepts missing owner-start identity;
   cancellation child1164–1167 leaves inherited nonprotocol FDs. Complete assigned
   X11Screen/OwnedEmitter/Watchdog/CancellationActor failure matrix.

No nits.

STATUS: NEEDS WORK

Root accepts all concrete Musts and Shoulds. Correct in exact-native integration
WT under bounded helper2file scope before source acceptance or live use.
