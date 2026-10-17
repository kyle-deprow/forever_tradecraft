# Sol review: GNOME no-flash next-cost R4 canonical closure

Scope was limited to the R3-to-final-R4 private harness and documentation delta. I reviewed the canonical harness at SHA-256 `29b9ebf15705b68cbb43756b266e076700d2f845ab7ef405959264387d4ef0c6`, the R4 freeze and delta, the prior Opus findings, and the accepted R2 arbitration. I did not run tests, binaries, captures, builds, D-Bus queries, or runtime operations.

The functional closures are sound. `derive_intervals()` requires a complete ordered stream, contains the first and last child markers within the parent command interval, emits `pre_main`, every adjacent marker bucket, and `post_run_return_tail`, rejects negative/overlapping intervals, and verifies that their sum equals the observed elapsed time. The three sampled empty-pair rows are non-overlapping named pairs, and their total/max fields are accurately scoped as samples rather than a bound on all instrumentation. The default parser still requires the complete live stream; `allow_incomplete` is used only by the offline real-binary `--version` emitter test, which also checks the exact two-event prefix. Unknown events, changed PIDs, malformed/mid-line records, token changes, order/cardinality changes, and non-increasing timestamps remain fail-closed.

The completed-process path retains driver-decoded stderr text, while a backend exception records that stderr is unavailable and preserves the original failure without manufacturing an empty artifact or stage attribution. The canonical receipt kind/path, process-local PATH and token changes, production-vs-private boundary, null unrecorded creation time, unretained Docker invocation, and build-network description are truthful. The accepted shutdown minimum is represented by the `app_release` to `run_return` shutdown bucket and the documentation that recent markers cover only lookup/parse/in-memory work and that the bucket is not removable startup cost.

## Must-Fix

None.

## Should-Fix

None.

## Nits

- `.archive/executor-review/gnome-no-flash-next-cost-plan.md:34` and `:46` retain the historical labels “Strict PNG completion wait” and “completion of the driver's staged PNG.” The accepted R4 interpretation is that this approximately 0.05-second measurement is PIL `verify()`/`load()` after the screenshot child has exited. Rename those two labels accordingly so later cost analysis does not mistake decode work for waiting on an asynchronous writer. This is documentation-only and does not affect benchmark execution or evidence admission.

STATUS: READY
