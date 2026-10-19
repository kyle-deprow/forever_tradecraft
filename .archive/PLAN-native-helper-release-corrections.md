# Helper release corrections on exact nativeR10d

Root accepts all final Sol findings in
executor-review/native-helper-causal-final-sol-review.md. Parent66green on oldR8
proves only tested paths; publicpause response mismatch is real production bug.
Prior integration task stopped at metadata without implementation and its
reports honestly mark post-success recovery missing. Do the actual code now.

WT /home/dev/.cache/crowley/worktrees/native-helper-final-integration-20261019,
base c5e5772, seven exact nativeR10d files + helperffc8/testd483. Own TWO files:
tools/native_calibration_operator.py and tests/test_native_calibration_operator.py.
All7native/driver/Guardian/addon/config/services/GUI/git are READONLY/noactions.
No resets/stashes/reverts. This supersedes old metadata-only freeze instruction.

Order:
1. Fix real response contract: pause response is immediate controller status,
   not aggregate status. Validate PAUSED/new controller generation and higher
   leaseGeneration. Fetch actual aggregate status to confirm exact nonrunning
   native operation. Before recovery input require the NEW canonical binding's
   higher guardianGeneration and guardianArmedfalse. Preserve original error
   and failed receipt even after successful recovery. Test actual Operator.run
   after real measurement-sideeffect/error, not directclientonly.
2. Fix monotonic _record_operation_deadline directly: min(existing,new) or
   rejectincrease; no clock/timeout allowances. Cover actual method.
3. Finish allocation hardening: invalid OwnedEmitter processgroup must abort/
   reap actual spawnedchild/close stagedfds; Watchdog requires available exact
   owner-start identity before spawn; cancellation actor child closes inherited
   nonprotocol descriptors using real watchdog-style whitelist. Preserve private
   channel/owner identity and no unpressed physical releases before GO. Real
   failure matrix for X11Screen/OwnedEmitter/Watchdog/CancellationActor staged
   allocations, causalexception/receipt and cleanup proof.
4. Refactor EXISTING real compiled fixture into reusable causal device within
   testfile; no newframework/module. NormalX11Screen/readiness/backend/decoder/
   actualdaemon+AF_UNIXIPC+FixedInput/OwnedEmitter/Watchdog remain. All scene
   changes ONLY after owneddispatchACK and realLua behavior. No FakeScreen/
   FakeInput/rawsuccessfulobs/pacingprovider/admission for successful cases.
   Share actual sealed input artifact via allowed tool factory for screen and
   input; supply real helper_source_sha256 and _source_bindings; assert resulting
   receipt helper/config/templates/producer/input/native dependency hashes.
5. Use this actualfixture through Operator.run for measureSUCCESS/all12 states,
   control-preflight, recoverordinary_reload, recoverrestore, actualmeasurement
   failure→newPAUSED/emptyID recovery preserving ORIGINALerror, post-handoff
   cancellation, real readiness refusals, and actual READY/watchdog/GO/PRESSED
   budget refusal before physical action. Do not claim FakeScreen/directclient
   tests prove these. Existing focused simpler tests stay as supplementary.
6. Complete PREVIOUS integrationplan actualsuccess→publicpause→freshrecover
   ordinaryrestoration on actualSavedVariablesLua reload; checkpointNone, PAUSED,
   nativeCalibrationTRUE/inputFALSE/unarmed. Fresh actual helperowners after
   previousrun closes them; no fake human gate. Original plan remains reference.

Use exact R10d native files, no R8compatibility claims. If a real nativecontract
failure arises quote exact call/guard; don'teditnative/weakentiming. Complete
focused real modes/negatives then FULLhelper suite ONCE on finalcode. Parent
independently reproduces meaningful cases then Sol+actualOpus review. No source
promotion/live100/GUI yet. No another metadata-only final or redDONE.

Private0700XDG/evidencedir/capturelock/bus, complete0600logs BEFOREcommands start,
exact argv/rc/imports/authenticCLI/base/9hashes/7readonly/cleanup. Keep failures.
MAIN writeONLY executor-review/native-helper-release-corrections-{closure.md,
freeze.json}. DONE only actualimplementation/proofs/fullgreen complete.
