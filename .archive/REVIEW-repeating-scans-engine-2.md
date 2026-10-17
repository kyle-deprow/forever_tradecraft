# Engine/addon component review 2

Sol verdict: MAJOR ISSUES (component only; native review is separate).
Frozen milestone has improved but these production outcomes remain required.

1. evidence.py requires ackedSweeps although real companion Data.lua has exactly
   generatedAt, ackedScans, scanPlan, shoppingLists. Accept the actual strict schema.
   Before ack reload require stable companion uploaded UID and stable Data UID;
   persist both stages. After reload use fresh loaded/pending telemetry, not a
   subsequent mutable Data refresh that may have dropped the UID.
2. Valid bounded commodity coverage may have sourceComplete=false when strict
   cutoff/witness rules prove retained depth. Let strict format-2 validation enforce
   coverage-specific completeness; do not require full-source semantics everywhere.
3. IPC generation validation and mutation must be one atomic nonblocking locked
   transition. closeout increments generation. Serialize all journal writes, including
   sanitized telemetry/model updates, so they cannot overwrite concurrent durable pause.
4. Acquire process lifetime ownership before Controller/journal/socket construction.
   Failure of capture or socket loop must fail the service, not leave a healthy-looking
   daemon thread server alive. No second daemon may mutate state before lease failure.
5. Duplicate tuple includes boot,sequence,CRC. Enforce ordinary boot stability, expected
   single reload boot, freshness deadline, and boot-churn rejection; persist frame evidence.
6. Validate available configured context/build/interface/house/plan before any recovery
   input. Corrupt/mismatched telemetry is not a login surface. Require an actual verified
   scene before model action, and catch recovery exceptions into durable BLOCKED.
7. Persist structured action intent before dispatch (scan, save/ack reload, reopen,
   model actions, logout), with result/retry/deadline. Reconcile uncertain actions without
   replay. Closeout stays orthogonal until fresh idle evidence, including auto-scan/IPC
   race. Clear closeoutRequested only after proven closeout; retain reload evidence.
8. Reject nested Codex tool/command events, not only top-level types. Support four-step
   disconnect/reconnect/selectArthur/enterWorld with state-specific one-attempt budgets.
   Model process group must terminate on generation revocation/cancellation.
9. Agent.lua luaTransientKiB starts measurement after encoding; move measurement across
   snapshot/JSON/compression/frame construction/render, with meaningful harness regression.
10. Existing happy-path fixture hides schema/publication defects by always including
    ackedSweeps and creating Data during ack reload. Add actual captured-shape positive
    and negative lifecycle tests: restart/action-wait matrix, automatic adoption, Data race,
    boot churn, closeout scan race, concurrent IPC, bounded qualifiers, nested tools,
    cancellation. Do not weaken tests to mirror current implementation.

Also fix: non-daemon --config must determine socket/journal paths; failed CLI requests
exit nonzero. Document actual CLI install -> unarmed daemon -> real gates -> explicit
start/resume sequence, measured display authority, and accurate stop semantics.

No native inputs or installation happened. Parent and Sol agree that passing isolated
unit/happy-path tests cannot clear these remaining production defects.
