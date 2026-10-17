# Integrated engine review, round 3

Sol verdict: MAJOR ISSUES. Production install/live validation not ready.
Parent verified 221 passed, 15 DB skips, Ruff/102-file format/diff checks pass.
These checks do not establish production calibration/IPC/native acceptance.
Native findings are in REVIEW-repeating-scans-native-2.md and also apply.

## Must fix

1. IPC resume rejects PAUSED/BLOCKED, the only states Controller permits resume.
   Real pause then resume with returned generation yields stale generation.
   Calibration's synchronous five-second socket timeout is also too short.
2. Integrated runtime test directly injects calibration and manually advances
   daemon, bypassing IPC calibration/resume/main daemon supervision. Add a real
   production-shaped control-path test, not provider-registration assertions.
3. Cadence uses previous sweep, accepting starts100,1005,1910. Compare seed+900
   and seed+1800. New validation run must reset streak/accepted evidence and
   require three NEW qualifying cycles, not reuse prior streak.
4. Restored intents ignore uncertain dispatched result, permitting replay of
   reload/logout/scan/openAH/recovery after restart. Reconcile fresh observations
   or block, never replay uncertain effects. Recovery retry budgets must survive
   restart. Increment generation on restart to invalidate stale clients.
5. Addon observation fabricates modal=none/idle=true/world/auctioneer controls.
   Conjoin real fresh visual evidence with telemetry for world/AH facts. CRC or
   protocol errors must block, not trigger login recovery. Four-step recovery
   graph contradicts disconnect dismissal/reconnect preconditions; observe actual
   named controls and scenes, not generic client controls or desired-action facts.
6. Closeout jumps to cleanup despite an intervening Lua auto-start, risking
   logout during scan or completed UID never adopted. Freshly reconcile/adopt
   before cleanup. Empty-run closeout must not wait for emptyUID uploads.
   Rejected sweeps must honor closeout rather than reopen. Stop must prevent new
   save/reload intents and input despite retained observational phase.
7. Retain reviewable evidence: per-item kind/row/priced-row counts; upload and
   publication/loadedack times/boots/latencies; durable rejection/cadence reset/
   intervention/pause/restart history; actual full calibration results, not only
   fingerprints/latest overwritten metadata. Survive pause/restart for report.
8. After acquiring lease remove stale socket safely; supervise owner and socket
   failure together, cancellation/join so input-capable owner cannot outlive IPC.
   Service must use actual verified Codex executable; systemd PATH resolves broken
   /usr/bin/codex, working executable is pnpm installation. Explicit configured
   canonical path, no silent fallback/model substitution.
9. Lua transient allocation metric after-before is not peak; intermediates can
   be freed between samples. Measure actual peak during whole publish pipeline
   with appropriate GC/measurement control, restoring normal GC afterwards.
   Test intermediate peak exceeding final retained memory, not monotonic samples.
10. Actual named anchor producer and preconstruction baseline remain required.
    Manual config coordinates relabeled by generic world telemetry don't prove
    controls. Premeasurement capture after textures exist is not construction.
    Restore correct docs and implement external-bootstrap baseline handshake.

## Should fix / nits

- Validate actual SavedVariables/companion/Data paths at startup before input.
- JSON list/scalar IPC request returns structured error, not AttributeError.
- Enforce exact Data.lua scanPlan/shoppingLists shape, not broad value types.
- Remove or correctly honor CLI --journal/--socket overrides.

## Verified improvements

Actual four-key Data parsing, stable UID publication before reload, fresh
boot/loaded ack, bounded commodity evidence, locked atomic journal writes,
boot/seq/CRC, recursive forbidden-event rejection, group cancellation, and desktop
lease-before-controller are present. They don't resolve remaining findings.

Lead owns its existing controller/daemon/CLI/config/model/journal/protocol/
evidence/addon/harness/deploy/docs fence. Native owner owns four native source
files and tests/test_session_native.py. Independent test owner alone owns the
two independent regression files. Coordinate API integration directly. No GUI,
service install, private config mutation, prodDB changes or commits during fixes.
Complete the entire batch then required tests/lint/format/diff and Sol re-review.
