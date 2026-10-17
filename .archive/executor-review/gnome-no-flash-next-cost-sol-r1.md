# Sol review: GNOME no-flash next-cost R2 source and harness

This review covered the frozen timing-only GNOME fork, its exact four-C-file plus
header instrumentation diff, private build provenance, and
`/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark.py`
(SHA-256 `86f977d6112e51f6d540c94c26914b6ea9ece33c58d6e28b5cf330fee6c32e38`).
I did not edit, build, execute tests, capture, send input, or query the live bus.

## Must-Fix

1. **A complete first marker stream still triggers the second live capture.**
   `/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark.py:1121-1240`
   iterates over both values in `range(MAX_SAMPLES)`. The only explicit control
   transfer is `continue` for a retryable missing/incomplete first marker stream
   at lines 1232-1238; the successful path at line 1240 also falls through to
   ordinal two. This contradicts the frozen plan and build report, which permit
   the predeclared second ordinal only when ordinal one otherwise succeeds but
   has an absent/incomplete marker stream. A normal run would therefore take an
   unnecessary second screenshot and add a second recent-file side effect.

   Stop the loop after the first capture with a complete valid marker stream.
   Continue to ordinal two only for the existing retryable first-marker case;
   all other failures must still stop. Add offline decision tests covering:
   complete first stream -> one attempt; absent/incomplete first stream -> at
   most one second attempt; malformed/owner/capture/decode failure -> no second
   attempt; incomplete second stream -> failure.

2. **Raw stderr is not retained on a failed screenshot child.**
   At lines 1007-1018, any exception from the unchanged backend leaves
   `completed` as `None`; lines 1033-1039 consequently write an empty stderr
   artifact. The original error is then re-raised at lines 1096-1098. A nonzero
   exit, timeout, or cancellation can therefore discard the partial fixed marker
   stream and ordinary child diagnostics even though the plan, manifest, and
   build report state that raw stderr is retained for every attempted ordinal.
   The receipt keeps only the backend's synthesized exception text, which is not
   equivalent to the raw stream and contains no partial timeout output.

   Preserve raw stdout/stderr for the diagnostic child on both success and
   failure through a private, independently reviewed diagnostic adapter that
   keeps the same one-command admission, argv, executable, process-group,
   deadline, cancellation, termination, and exception-priority behavior. Do not
   change production `_run` or production stderr handling. If raw failure output
   cannot be surfaced without changing those semantics, narrow the frozen claim
   explicitly and do not claim complete failure-stage attribution; the current
   `raw_stderr_retained_per_attempt: true` assertion is false.

## Should-Fix

1. **Live evidence would be stored under the accepted benchmark's generic name.**
   The new harness creates
   `gnome-no-flash-benchmark-<stamp>-<pid>` at lines 864-867, while the amended
   artifact fence and source/build artifacts use `gnome-no-flash-next-cost-*`.
   Use a `gnome-no-flash-next-cost-benchmark-*` directory so diagnostic receipts
   cannot be mistaken for accepted stage-2 benchmark evidence.

## Nits

None.

## Verified closures and behavior

- The instrumented build is isolated under
  `/home/dev/.cache/crowley/gnome-no-flash-next-cost-r1`, retains the accepted
  full-screen `flash=FALSE` behavior and `x11=disabled`, and leaves the accepted
  stage-2 binary and host packages untouched. The manifest correctly records
  deployed production as host-stock.
- The source diff adds only fixed monotonic stderr markers. Its successful event
  order matches the actual synchronous and GLib callback flow: construction and
  startup/configuration, command parsing and idle capture dispatch, Shell call,
  Shell-PNG load/unlink, asynchronous output open/save callbacks, recent-entry
  invocation, application release, and `g_application_run` return. `run_return`
  is correctly treated as preceding final `g_autoptr` cleanup; the parent-side
  command end can retain that residual separately.
- The parser accepts only the literal versioned prefix, exact token and owner
  PID, fixed event sequence/cardinality, and strictly increasing monotonic
  timestamps. It retains nonmarker stderr without treating it as timing evidence
  and classifies only absent or valid-prefix incomplete streams as eligible for
  the predeclared second ordinal.
- The harness keeps the accepted private executable/owner/PPID/PGID proof,
  daemon and capture-lock preflight, production capture/completion/crop/strict
  decode path, original capture timestamp, stationary frame checks, and exact
  cleanup behavior. It no longer requires false CRC or pixel equality across
  changing live HUD publications and makes no native-100 qualification claim.

STATUS: NEEDS WORK
