# Native ACK source-review closure

Status: APPROVED by parent to implement the accepted Sol source-review R1
findings. This is a closure checklist for existing approved requirements, not
source approval or a separate claim of Sol plan review.

This breaks implementation into smaller verification stages. It retains the
approved [identity budget](PLAN-native-identity-budget.md) and
[pre-ACK correction](PLAN-native-capture-ack-alignment.md) requirements, exact
six-file fence, numeric vectors, deadlines and release gates. It introduces no
new producer protocol, Guardian, addon, Rust, helper or public schema changes.
Parent owns this document, skills, evidence and Git; Luna owns the same six
source/test files in the isolated worktree.

## Stage A: close production correctness before expensive replay

1. Complete terminal diagnostics at the actual retained-evidence boundary.
   After held100 frame, memory, metrics, hash, resume-boundary verification and
   `resume_required` validation,
   notify the real diagnostic observer once before resume replaces its current
   attempt. Preserve the final image; report `retained`, never a false release.
   Existing `mark_release` already supports retained paths. All other released
   accepted attempts retain their actual release proofs. Test exact terminal
   notification, image/digest preservation and subsequent failure cleanup.
2. Carry the exact fresh receipt validated at the capture seam to the update
   anchor. Do not later reread mutable `backend.last_region_receipt`. Preserve
   existing callers' behavior and binding to the exact original attempt. Use
   a deterministic receipt-substitution barrier with identical output digest
   and different nonce/timestamps; the substitute must not become the origin.
3. Thread the provider's original absolute frame deadline through capture,
   real driver and pre-ACK wait/admission. Never mint `now + timeout` at a later
   boundary. Apply the earliest existing frame, producer, operation, reservation
   and capability limits. Under controller -> construction -> Guardian, repeat
   shutdown and all expiry checks immediately before ACK dispatch. Contention
   for the final lock must not carry stale admission past expiry. Test the
   exact deadline reaching the real driver and
   a producer already waiting for ACK when the earliest limit expires.

Run named focused correctness tests and scoped checks. Give parent a concise
completed/remaining checkpoint if a requirement needs a plan change. Do not
spend another full compiled100 run on a known incomplete candidate.

## Stage B: make performance evidence match the actual call graph

- Restore the old deferred owner's actual 142.073ms validation charge when
  eligibility alone is disabled; do not change deferred context/reservation.
- Charge every actual capability validation once at 0.500ms. Charge final
  synchronized ACK admission separately at 0.500ms at its actual boundary,
  excluding the separately charged capability check.
- Split the existing 117.511ms lock-to-shot total into before-wait and actual
  ACK tail; keep its total unchanged for both 1ms and 5ms tails. Do not count
  the existing ACK/process proof twice.
- Keep publisher ticks independent from actual Measure publication. Retain
  exact pinned first-shot phases and all seven already-approved vectors.
  Every virtual advance needs named work or an actual production wait; scope
  virtual sleep to the simulated path. No global stdlib clock patching.
- Require real refusal or visible budget overrun for negatives. Preserve
  retries, all physical shots and terminal100 proof. No exception for an input
  merely being outside the declared passing envelope. The pinned phase951 case
  specifically requires actual no-skip/protocol refusal; budget overrun alone
  is insufficient.

Retain per-case command, full private output, source pins, actual cost counts,
publisher and physical-shot timelines. Parent reproduces the final model,
including old-mode characterization, before source approval.

## Stage C: finish actual producer pre-ACK protocol coverage

Use the existing compiled producer and compositor. Bind a typed ordinal2
attempt to a real ordinal1 receipt and its decoded publication; do not label a
gradient capture and caller-chosen uptime as an observed Agent publication.
Use barriers outside authority locks for wait tests and a separate barrier at
the final synchronized admission boundary for the ACK race.

Map each approved requirement to a named case, reusing existing tests only
when they actually traverse the new eligible path:

- Successful eligible pre-ACK capture and unchanged generic fallback.
- Owner/reservation revoke, controller stop or generation change while waiting.
- Original frame/producer deadline and operation/reservation expiry.
- Unhealthy watchdog, lost lease and unresolved release/input ownership.
- Wrong admitted PID, dead/replaced process and capture-epoch replacement.
- Final ACK transaction race: revoke-first prevents ACK; dispatch-first permits
  at most one capture and later rejection/cleanup as appropriate.
- Callback no-dispatch, pre-dispatch failure, double dispatch and failure after
  dispatch; during/after-capture revocation still rejects evidence.

Before observer admission, refusal starts zero producers. After producer spawn
but before ACK, refusal means zero ACK, zero ScreenshotArea entry, kill/reap,
empty Guardian/backend registries and retired attempt artifacts. Enable the
compositor's entry-marker/block fixture so absence is meaningful; an unarmed
marker cannot prove zero entry. Check unchanged completed-call log too.
After dispatch, permit at most one actual ACK/call, require rejected evidence
on failure and complete cleanup. Always release the fixture's own blocking
gate in cleanup. Do not confuse a completed-call log with method-entry proof.

## Final milestone and review

Provide a requirement-to-test/result table covering A, B and C. Run scoped Ruff,
format, compile and diff checks, then freeze all six hashes. Parent inspects and
reproduces relevant checks. Run exactly this long node once on that candidate:

`tests/test_native_calibration_operator.py::test_actual_operator_measure_composes_x11_screen_daemon_and_agent[success]`

The short region compositor test is additional evidence, not this native100
gate. Keep construct0, held0, updates1..99, retained held100 and resume0 in the
real observer's exact accepted sequence. No fixture-manual spans/finish calls.

Sol re-reviews the resulting frozen source; actual CLI Opus reviews the same
accepted candidate. Parent reproduces compiled100. Only then quiescent install,
restart, live native100/recovery, genuine human input calibration and three
autonomous900s full cycles. Ordinary assisted collection continues meanwhile.
