# Native R5: consolidated implementation and review contract

This consolidates root's R5 handoff/messages; it adds no new behavior beyond
those instructions. Worktree native-construction-native-r5-20261018 starts from
the exact six frozen R4 files, base e6e17bb. The same three production and three
native test files are the entire write fence. All addon/driver/calibration/
Guardian/inputtool/protocol/config/helper/GUI/service and git mutations remain
forbidden. Earlier freezes stay immutable; no live or acceptance claim.

Retain all original native R3/R4 correction requirements and operation bounds.
Read the R4 closure plan, original native-review-fix plan, ordinary-recovery
amendment and shared helper composition closure. R5 specifically finishes:

1. A bound private stateHistory with at most16 exact {state,nativeClock}
   entries, full twelve-state contiguous prefix for successful construction,
   nondecreasing _native_clock timestamps, no poll append, immutable owner
   association and terminal/recovery records. No public schema, canonical14
   reservation, request-shape or legacy behavior changes.
2. Extract the corrected image-only absence implementation into private pure
   _strict_native_absence_image(path, *, expected_size); keep the instance
   method as compatible configured wrapper. Preserve semantics and actual PNG
   malformed/corrupt/ordinary cases. The helper can prove same-image controls +
   absence after reload without boot decoding or fake daemon construction.
3. Recovery-begin refuses an existing provisional inflight slot before another
   capture. Completion owner/ticket validation and durable checkpoint/frame
   commit are linearized against same-generation cancel, using consistent
   controller-first ordering or a closed capability. Expiry is handled before
   dereferencing a cleared ticket; no uncaught AttributeError escapes IPC.
4. Recovery-complete bounded-polls through expected old/absent/loading frames
   after the single reload/Restore action, until genuinely newer ordinary /
   inactive-fence proof. Revalidate ticket/epoch/generation/state/identity/lease
   at every boundary. Preserve existing45s/config/expiry cap; decoder failure
   is never accepted absence proof or permission to input. No helper action
   retry or new IPC.
5. Real configured compiled PAUSED adapter/provisional capture tests, actual
   thread-barrier pause/recovery/competing-admission races and private IPC/parser
   coverage. Include atomic journal failure/fresh-owner retry with the failing
   owner alive through its handler. Raw observation dictionaries/manual private
   callback sequences alone cannot establish production acceptance.
6. Fix the OWNED diagnostic fixture's actual cadence instability without
   weakening production or harness limits/assertions. Parent R4 starts were
   1.000055196s apart and both samples met1s, but completions0.645715499s apart
   violated the0.75 lower bound. Retain this trace; use real fixture scheduling/
   warmup with exact payload accounting and distinguish it from live performance.

Run focused cases first, then the full three native suites once after final
source changes, with authentic private0.162.1 CLI configured explicitly and
private0700 XDG_RUNTIME_DIR. Scope Ruff/format/compile/diff to the six files.
Retain complete private logs/import origins/invocations and programmatic six
hashes/base hashes in MAIN R5 freeze.json and closure.md only. Send an actual
implementation/test milestone. Root independently verifies final source before
Sol and actual Opus review; accepted native source is still required before
final helper integration, live native100 or genuine human input.
