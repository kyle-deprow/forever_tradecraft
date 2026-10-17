# Native review round 9

Sol verdict: MAJOR ISSUES. PID directory pinning, reset-receipt ordering and actual
executable identity checks are improved. Preserve all confirmed XI2/GTK/ticket/
scene/freshness/reaping behavior. Correct these remaining production defects in
the existing six-file native fence, coordinating actual callback changes directly
with the main engine owner.

1. Match the real Agent lifecycle. updateCount counts every publication and never
   resets on hold or resume. Capture the held/0 count as a baseline; measured
   ordinal N must have baseline+N. Measure publishes ordinal1 immediately, so
   enforce 1Hz intervals only from update1→2 through update99→held100. Normal
   frames may occur while the operator responds to hold-required: construction
   to held/0 must be newer, not exactly consecutive. Require continuity from
   held/0 through the 100 measurement frames. Post-resume normal/0 has a later
   publication count, not zero. Fix the sealed evidence validator too.
2. Emit resume-required BEFORE requesting the resumed frame. The callback cannot
   require final evidence that itself requires the resumed frame. Agree one
   concrete pre-resume callback carrying the validated held boundary; publish
   operator status, then capture fresh normal/0, seal proof and emit resume-ready.
3. Register each returned capture artifact before stage/ordinal/count/cadence/
   freshness validation. Put construction path handling and all reset/provider
   operations inside cleanup protection. On any failure abort pending windows,
   release artifacts, preserve history and allow safe retry after restoration.
4. Replace the Boolean-only restoration claim with either a verified fresh
   same-identity/boot normal/0 observation or the engine's durable explicit
   restoration-required record/receipt. Never certify normal without observing it.
   A durable restoration-required state may keep the failed gate unarmed until
   the operator restores normal publication and a fresh frame proves it.
5. Implement the missing negative and real producer-consumer tests below. The
   previous happy provider invented updateCount/phase behavior and hid the bugs.

Seal the actual baseline-ready/bootstrap-release timestamp as construction work
start. Enforce exact phase limits of 128 MiB and 16 MiB in sealed revalidation,
not merely positive limits and growth caps. Keep the fixed memory method.

## Required tests

Build a runner provider fixture from the REAL WowClient/Agent publication bytes
and production decode, not a parallel handcrafted render lifecycle. Drive test
operator hold/measure/resume commands from the corresponding readiness callbacks;
providers observe results and must not silently manufacture requested states.
Use a harmless owned child for the process-memory portion. Include normal frames
before operator hold, immediate update1 and relative counts through resume.

Run legal-but-wrong normal/0 at each measurement stage; skipped/old ordinals;
noncontiguous measured frames; bad cadence; missing resume; invalid/stale artifact
cleanup and retry through the runner using the same meter; archive callback failure
before any clear_refs write; PID-path replacement with pinned FD; stalled wrapper
and wrong executable rejection through actual XI2Observer.start admission; and
sealed limit/boundary tampering. Preserve genuine negative failures.

Same six native files only; engine owner handles actual status/callback/receipt
integration and its fixtures. Independent regression owner retains its files.
Publish agreed interfaces early. Strict scoped tests, Ruff/format/compile/diff,
parent reproduction and independent Sol re-review. No GUI/live reset/service/
production data/SavedVariables/git mutations. DONE only after full owned outcome.
