# Sol plan review: deterministic runtime performance R2

Reviewed plan SHA-256: `de6f10c9979fffe79051ad33ab3d5bf97d7f3bb7103b4d3905c315236ff0c454`.

R2 closes the substantive R1 measurement and model-boundary findings. It defines a matched region-path decision record, exact CPU numerator and end-to-end wall denominator, source/config/producer binding, sample and run eligibility, one quantile rule, per-run repeatability, a bounded counterfactual failure screen, and `insufficient_evidence` behavior. The audit now explicitly includes both Luna calls used by an AH pointer action and forbids a whole-cycle zero-call claim without a fresh semantic-anchor replacement.

Evidence and source hashes inspected:

- `.archive/executor-review/offline-decoder-computation-baseline-20261017.json`: `306d334c752a2522488a5b92310ad8cca58797e2f02c1891f716f09589edf520`
- `.archive/executor-review/gnome-no-flash-next-cost-parent-live-verification.json`: `9927ab1150384c6ab34be261b4224b7c382283608edf4851aebb36eca7a4218c`
- `src/crowley/session/decoder.py`: `badd6c3f469f0f13503d3aa8851e7d0dac416629f3974841593d6b42d2199739`
- `src/crowley/session/protocol.py`: `cf13dedd7a37e553ac799b87dd5429cc29b5910483661f994ffdec3b38a74d2f`

The source hashes still match the offline baseline. The existing 100-iteration one-frame replay and single full-screen receipt remain correctly classified as insufficient, not as a migration or defer decision.

## Must-Fix

1. `.archive/PLAN-deterministic-runtime-performance.md:181` says Phase 1 ends with an explicit migrate/defer decision, but `.archive/PLAN-deterministic-runtime-performance.md:138` correctly requires `insufficient_evidence` when matched CPU/stage evidence or the 15 complete runs are absent, and `.archive/PLAN-deterministic-runtime-performance.md:142` explicitly classifies the current evidence that way. Phase 1 itself cannot acquire the missing live evidence because `.archive/PLAN-deterministic-runtime-performance.md:40` prohibits live screenshot modes and `.archive/PLAN-deterministic-runtime-performance.md:107` reserves acquisition for a separate reviewed operation. As written, an implementer must either violate the evidence rule by returning `defer_rewrite` or leave Phase 1 unable to satisfy its completion condition. Change line 181 to require an explicit `plan_prototype`, `defer_rewrite`, or `insufficient_evidence` decision. When evidence is insufficient, require a bounded next-evidence slice rather than a Rust plan; retain migrate/defer as the terminal outcomes only after the eligibility gate is met.

## Should-Fix

None.

## Nits

None.

STATUS: NEEDS WORK
