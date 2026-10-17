# Sol source review: production runtime instrumentation R1

I reviewed the frozen four-file candidate in
`/home/dev/.cache/crowley/worktrees/runtime-instrumentation-20261017` against
the released live-instrumentation plan and the accepted read-only schema-2
evaluator. I inspected source and metadata only. I did not run tests, execute a
receipt, use Git, or operate the game, GUI, network, database, or any runtime.

## Identity and scope verification

The supplied freeze and delta match the handoff:

- `.archive/executor-review/runtime-live-instrumentation-r1-freeze.json`:
  `3182baafd4b72ad02e377dd102f379d0ea23a1423f9ad07d2fc7569e8a5b2af6`
- `.archive/executor-review/runtime-live-instrumentation-r1-parent-delta.diff`:
  `70b5f486002e2bbd41585b10d9ba5f938591acb11c126e6a02a49cbabbe661f9`
- `.archive/PLAN-runtime-live-instrumentation.md`:
  `a563e4df1450eaac3cb44b87fb3143a823bbed5b23f4209d168703a010a0bb62`

The four frozen candidate hashes also match exactly:

- `src/crowley/session/driver.py`:
  `cdcb5d030c7c11bd9eee0c24d839650652384ad30bc68ae1b3ba8576721eeea0`
- `src/crowley/session/daemon.py`:
  `19f7573aa1447171303b29ecbdc4d0d5c41117eb374f617213f256426129e6e8`
- `tools/gnome-telemetry-region/offline_harness.py`:
  `3effff49ec55052cbf5dc45112f086da2e094a3dd5d240b6b24dbd2abf438a97`
- `tests/test_session_native.py`:
  `60ce82d886412de099562461a3b48ff6a1a499f3718c33be7affbe6b5278a195`

The four main-tree baselines match the isolation manifest, and the accepted
evaluator, evaluator tests, and performance documentation remain unchanged at
`c46cae849058005e9b7387ef95c34f40f376afb5477739efaf6f40f6a36ebd8c`,
`c998aa4a9ff67ba67ddeab05a0e5a0cfa5273a296909e0b07cb79a3d06dd313a`,
and `54237c344ef0faa3392cca6fe82b75f1f986bbf697c81d3f34493b2f00e1caca`.
Scope is confined to the authorized four paths. The worker reports four
focused native tests and 65 evaluator tests passing; parent reproduction was
still underway at handoff, and I did not independently execute those checks.
The separate eight-sample schema-1 run is not schema-2 CPU evidence and does
not affect this review.

## Must-Fix

1. **Do not reset the per-sample model counter baseline after admission and
   source hashing.**

   - File: `src/crowley/session/daemon.py:3702-3704,3799-3801`
   - The owner takes the correct entry snapshot at line 3704, then overwrites
     it at line 3801 after request validation, admission, directory creation,
     and the seven-file source check. A model call that starts and finishes in
     that interval is absorbed into the replacement `before` snapshot. This is
     especially consequential for attempt 0 because there is no preceding
     attempt whose `after` snapshot can expose the increase. The receipt can
     therefore claim a zero per-attempt and zero inter-sample delta despite
     real adapter activity during that owner request.
   - Correction: retain the line-3704 snapshot as the sole
     `model_calls_before` value for the request. If a narrower capture-only
     diagnostic is also useful, give it a different non-qualification field in
     a separately reviewed schema; do not replace the normative owner-entry
     baseline. Add a concurrent first-attempt regression that increments one of
     the four real adapter counters before the source gate finishes and proves
     the emitted run is ineligible.

2. **A successful decoder return followed by frame/identity validation failure
   emits a receipt the accepted evaluator must refuse.**

   - File: `tools/gnome-telemetry-region/offline_harness.py:1573-1606,1625-1629`
   - After `PixelDecoder.decode` returns, lines 1586-1589 correctly retain the
     full CPU value and `strict_decode_finished_monotonic`. The phase remains
     `strict_decode` while freshness, frame presence, boot, identity, and
     sequence are checked. Any of those later checks therefore becomes
     `strict_decode_failed` with a non-null full CPU value. The accepted
     evaluator explicitly refuses that combination as an invalid lifecycle;
     it reserves `strict_decode_failed` for a thrown decode with only partial
     diagnostics. The genuine boot-change and no-change paths reach this case,
     and `tests/test_session_native.py:1593-1601` currently locks in the
     incompatible phase.
   - Correction: distinguish a thrown decoder call from validation after a
     returned decode. Preserve full CPU and decode-finish for the latter, then
     use a truthful accepted post-decode failure classification. If the finite
     contract has no semantically correct classification, use its explicit
     unknown-required-stage outcome rather than claiming the decoder threw;
     any enum expansion needs a separate evaluator-contract slice. Update the
     boot-change/no-change regressions and pass those receipts through the
     unchanged evaluator.

3. **Post-run observer source drift creates an internally invalid schema-2
   lifecycle instead of a retained source-binding failure.**

   - File: `tools/gnome-telemetry-region/offline_harness.py:1631-1648`
   - When all eight attempts have completed, the harness first declares the
     run `passed`. If the final observer map differs, it changes only
     `run_state` to `failed`; all eight attempts remain `completed` with null
     failures. The accepted evaluator requires a failed run to contain a
     failed attempt, so the receipt is refused as `attempt_lifecycle_invalid`
     before its source-drift evidence can be retained. If the after-read itself
     fails, the receipt also leaves the copied before-map in the field named
     `observer_source_hashes_after`, which is not an observed after snapshot.
   - Correction: finalize observer binding before declaring the terminal
     attempt complete, or convert the last begun attempt to a truthful
     `source_binding/source_binding_drift` failure while preserving its reached
     decode/CPU boundaries and the actually observed differing map. An
     unreadable after-map must remain visibly nonqualifying/refused; do not copy
     the before-map and label it an after observation. Add evaluator-backed
     regressions for both a differing map and an unreadable final source.

4. **The required producer-to-evaluator compatibility test is absent, allowing
   the incompatible failure receipts above to pass both suites independently.**

   - File: `tests/test_session_native.py:1488-1536,2292-2406`
   - The actual composition test checks selected schema-2 fields but never
     submits its persisted receipt to `tools/session_performance.py`. The two
     new focused tests call only `_live_owner_evidence` and
     `_validate_producer_attempt`; neither constructs a complete receipt nor
     invokes the unchanged evaluator. Running the 65 existing evaluator tests
     separately validates synthetic evaluator fixtures, not this producer.
     This misses the plan's explicit final-real-schema compatibility pass and
     explains why `strict_decode_failed` plus full CPU is currently asserted as
     valid producer behavior.
   - Correction: with a clearly test-only exact binding, evaluate the genuine
     persisted success receipt and representative reached-boundary failures
     through the unchanged accepted evaluator. Assert structural acceptance,
     eight eligible pairs for the zero-model-call success fixture, and retained
     but ineligible/refused-as-designed results for source, cleanup, counter,
     decode, and post-decode failures. Keep threshold and malformed-input cases
     in the existing evaluator suite.

## Should-Fix

1. **Close the pathname-replacement race in both seven-source readers.**

   - Files: `src/crowley/session/daemon.py:163-200` and
     `tools/gnome-telemetry-region/offline_harness.py:756-786`
   - Both helpers compare the initial pathname stat with the opened descriptor
     and compare two descriptor stats, but neither stats the pathname again
     after reading. An atomic replacement after `open()` leaves the descriptor
     unchanged, so the helper returns the digest of the unlinked inode while
     the fixed logical path names different bytes. That contradicts the
     released requirement to reject replacement and is weaker than the pinned
     evaluator's descriptor-bound read.
   - Correction: after the bounded read, `lstat` the path again and require its
     regular-file identity to match the descriptor, including device, inode,
     mode/link count, size, and mutation timestamps as appropriate. Convert
     disappearance or replacement to the bounded source-binding failure.

2. **Project every owner cleanup component instead of allowing an ignored
   Guardian group to look clean.**

   - Files: `src/crowley/session/daemon.py:4089-4121` and
     `tools/gnome-telemetry-region/offline_harness.py:1315-1327,1376-1388`
   - The daemon's authoritative `empty` value includes
     `guardian_active_groups`, but the schema projection ignores that list and
     computes `capture_process_reaped` from backend processes, backend groups,
     and observer groups only. If a Guardian active group remains while the
     producer attempt itself retired, the projected cleanup can show every
     boolean true and every exported count zero even though the daemon's final
     snapshot says it is not empty. The projection also defaults a missing
     lease observation to `true`, which is invented evidence even though other
     missing fields usually make the record ineligible.
   - Correction: include Guardian active groups in the exported active-group
     count (deduplicating IDs if needed), derive cleanup booleans only from the
     complete actual snapshot, and treat a missing boolean as malformed rather
     than supplying a favorable value. Add a failure fixture with a retained
     Guardian group and verify the evaluator reports cleanup failure.

## Nits

None.

The driver boundary capture itself preserves the existing deadlines, producer
protocol, identity/epoch checks, admission, reap, and retirement order. The
daemon wrappers cover the four requested adapter entry points without changing
ordinary call arguments. The success receipt has the accepted exact root,
attempt, owner, binding, CPU-method, and nullable-field shapes. Those positive
properties do not close the false-zero counter window or the incompatible and
misstated failure evidence above. No schema-2 collection or Rust decision is
qualified by this review.

STATUS: NEEDS WORK
