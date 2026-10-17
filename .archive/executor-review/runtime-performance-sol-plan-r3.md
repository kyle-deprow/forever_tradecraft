# Sol plan review: deterministic runtime performance R3

Reviewed plan SHA-256: `55f680dc1683c53dfddc5543384621875b7d1e8a4aa5280f7a921c427bef5f07`.

R3 closes the sole R2 contradiction. Phase 1 may now truthfully finish with `plan_prototype`, `defer_rewrite`, or `insufficient_evidence`; insufficient evidence requires the exact missing paired stages/runs and a bounded reviewed evidence proposal rather than a forced Rust decision.

Evidence and source hashes inspected:

- `.archive/executor-review/offline-decoder-computation-baseline-20261017.json`: `306d334c752a2522488a5b92310ad8cca58797e2f02c1891f716f09589edf520`
- `.archive/executor-review/gnome-no-flash-next-cost-parent-live-verification.json`: `9927ab1150384c6ab34be261b4224b7c382283608edf4851aebb36eca7a4218c`
- `.archive/executor-review/build-70450-fifth-scan-parent-verification.json`: `6070e10a60fdd7b09cfae330315b13f005a1584ea6ef6aaf3fc04f810e6dabe7`
- `src/crowley/session/decoder.py`: `badd6c3f469f0f13503d3aa8851e7d0dac416629f3974841593d6b42d2199739`
- `src/crowley/session/protocol.py`: `cf13dedd7a37e553ac799b87dd5429cc29b5910483661f994ffdec3b38a74d2f`

The decoder and protocol hashes still match the offline replay record. The new fifth-sweep baseline is accurately separated from CPU attribution: its receipt records 81.673676 seconds from sweep completion to Return dispatch and 4.958056 seconds from dispatch to server receipt at `.archive/executor-review/build-70450-fifth-scan-parent-verification.json:41`. `.archive/PLAN-deterministic-runtime-performance.md:60` uses it only to prioritize deterministic completion/readback/dispatch analysis and explicitly refuses to label the pre-dispatch interval as Python computation or unmeasured model time.

The prior decision gate remains intact: matched region binding, paired same-sample CPU/wall intervals, 120 completed observations across at least 15 eight-sample runs, exact Q95, pooled plus 80% per-run trigger, bounded counterfactual screening, and missing evidence returning `insufficient_evidence`. The model-boundary audit still records both AH anchor calls and prohibits a whole-cycle zero-Luna claim without an accepted fresh semantic-anchor provider.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
