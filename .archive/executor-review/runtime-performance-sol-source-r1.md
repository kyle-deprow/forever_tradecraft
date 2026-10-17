# Runtime performance Phase 1 source review R1

Reviewed only the isolated-worktree candidate at
`/home/dev/.cache/crowley/worktrees/addon-schedule-20261017` against canonical
plan SHA-256
`08479c262c6b36e152f6b6ceee8f714aa360633f83c9020ae5b4a5354447de80`.
The reviewed candidate hashes are:

- `tools/session_performance.py`: `8496268abe2bd6e6fa4574e6d99ff5f453af6d9fb40da0b9a9f8272168297e3d`
- `tests/test_session_performance.py`: `60eff55d51183417a8e4b9090a01b38b7b015ad4eb635f79d1958e41e092ab68`
- `docs/RUNTIME_PERFORMANCE.md`: `f4038bad1aa3f15c16057f350cffc0ec29a0c39849b67783fd5f5cf447b356d5`
- `.archive/executor-review/runtime-model-boundary-luna-audit.md`:
  `c81c27c9000ef12c6e29f764fa8010ab02325215f0eee7985fff364f846f6f92`

I also inspected the primary candidate summary at SHA-256
`c805979968893858102a8cc27549a39189410f965779d96f18005cde838b684e`,
its replay summary at SHA-256
`6124d32ac34ad8d78e4ff2a649b95e0e70485e7f6fedbd9593904c5cc57de9c8`,
and the parent replay at the supplied SHA-256
`17df74e9da169cdec2f73894749a58837fb1ed1538c793dfadc8d5ba278c83b8`.
The measured production boundaries in the worktree match the report:
`decoder.py` `badd6c3f469f0f13503d3aa8851e7d0dac416629f3974841593d6b42d2199739`,
`protocol.py` `cf13dedd7a37e553ac799b87dd5429cc29b5910483661f994ffdec3b38a74d2f`,
and `executor.py` `642744e4695abebebcebd51d1f481754753a5da1b8e4fba5eee7260d99ea0573`.

The public `PixelDecoder.decode` interval, separate PNG interval, process-CPU
and monotonic-wall samples, exact ceil quantiles, null private substeps, pure
planner timings, and `insufficient_evidence` decision are otherwise coherent.
The parent replay honestly reports 100 successful strict decodes with p95 wall
63.647683 ms and p95 CPU 63.396576 ms while leaving accepted source/config/
producer bindings, paired live intervals, eligible runs, trigger ratios, and
failure attribution empty. It does not support a Rust decision. The static
audit also correctly keeps runtime counts unknown, includes the current visual
AH observations and both pointer-anchor boundaries, and proposes a bounded
semantic-provider and instrumentation slice without removing current checks.

This was a read-only source review. I did not run tests, the CLI, the game,
Docker, a database, the network, or Git, and did not edit the candidate.

## Must-Fix

1. **`tools/session_performance.py:395-410` does not enforce the promised receipt-byte bound during the read, and `tools/session_performance.py:90-99` lets bounded but deeply nested JSON escape the diagnostic refusal path.** `_receipt_diagnostic()` first accepts a `stat()` size at or below 1 MiB and then calls unbounded `Path.read_bytes()`. A file that grows or is replaced after the `stat()` can therefore make the process allocate and read arbitrarily more than `MAX_RECEIPT_BYTES`; checking `len(raw)` afterward is too late. This contradicts `docs/RUNTIME_PERFORMANCE.md:22-23` and the Phase 1 bounded-input contract. Separately, Python's JSON decoder can raise `RecursionError` for a deeply nested receipt well below 1 MiB, but `_strict_json()` does not translate it to a fixed `PerformanceInputError`, so the CLI crashes instead of returning a sanitized refused diagnostic. Open the receipt once, compare the opened descriptor with the preflight metadata, read at most `MAX_RECEIPT_BYTES + 1`, and reject size/identity drift before parsing. Map excessive JSON nesting to a fixed refusal reason without retaining input text. Add regressions that simulate growth between preflight and read and supply deeply nested JSON; both must remain bounded, sanitized, and `insufficient_evidence`.

2. **`tests/test_session_performance.py:79-146` does not cover the plan's required valid sequence, malformed/schema, and physical-pixel-disagreement boundaries, while `docs/RUNTIME_PERFORMANCE.md:38-41` says those strict behaviors are retained.** The test named `test_pixel_disagreement_is_refused_by_public_decoder` changes one pixel to gray `(127,127,127)`, so it raises “neither black nor white” before reaching the distinct “physical pixels disagree” check. The suite has a CRC case, but no valid multi-frame sequence/boot case and no validly framed payload that reaches schema or malformed-frame refusal. The benchmark intentionally constructs a fresh decoder at `tools/session_performance.py:290-296`, so repeated timing samples cannot establish sequence/boot behavior by themselves. Keep that fresh-decoder timing boundary, but add focused public-boundary regressions: invert one physical pixel to the opposite valid black/white value, exercise a malformed or schema-invalid frame with valid framing/CRC, and pass a real ordered Lua fixture sequence through one decoder to verify the sequence/boot contract. Update the documentation to distinguish those strictness regressions from the fresh-decoder timing replay.

## Should-Fix

1. **`.archive/executor-review/runtime-model-boundary-luna-audit.md:39-78` cites line locations that do not match the exact source hashes recorded in the same audit.** For example, `_measure_pointer_anchor` begins at `daemon.py:1197` and calls `_observe_model` at `daemon.py:1288`, rather than at the cited `1327`; `_observe_addon_state` begins at `daemon.py:1574` and calls the model at `daemon.py:1620`, rather than `1659`; pointer-anchor measurement occurs at `driver.py:5852-5857` and the refresh callback is installed at `driver.py:6154-6157`, rather than the cited `5976-5982` and `6271-6282`. Several stable-session citations are beyond the current `daemon.py` line count. Correct every source/test citation against the recorded hashes so the static call minima and deterministic-boundary claims are directly reviewable. The substantive current-source conclusion remains supported: ordinary deterministic monitoring can use zero model calls, while current AH reopening still uses named visual observations and the visual anchor provider, including a second anchor observation when pointer movement occurs.

## Nits

None.

STATUS: NEEDS WORK
