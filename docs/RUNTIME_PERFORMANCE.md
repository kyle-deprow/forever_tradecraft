# Session runtime performance

`tools/session_performance.py` is an offline measurement tool. It reads only
explicit PNG paths and bounded JSON receipt files. It never captures the
desktop, sends input, invokes Luna, contacts the server, or changes the session
controller.

Run it with an explicit lossless 256x256 status crop:

```bash
uv run python tools/session_performance.py \
  --input /private/preserved/status.png \
  --receipt /private/preserved/timing.json \
  --samples 100 \
  --warmups 5 \
  --output /tmp/runtime-performance.json
```

The command reads each input through a bounded file handle, checks the PNG
format and 256x256 header before pixel allocation, and refuses file-size or
byte-digest drift between preflight and every warmup/sample. Receipt metadata
is read through a descriptor with identity/size checks and a capped
1 MiB-plus-one-byte read, so a growing or replaced file cannot turn an initial
stat result into an unbounded read. Inputs are capped at 16 files and 1 MiB
per PNG; receipts are capped at 16 files and 1 MiB per receipt; samples are
capped at 1,000. Warmups are excluded from the reported statistics and labeled
as excluded startup cost. Reports contain input digests, dimensions, measured
local source hashes, Python/Pillow/host metadata, process CPU and monotonic
wall p50/p95/p99/max, and no image payload, input path, character identity, or
receipt path.

`full_strict_decode` calls the existing public `PixelDecoder.decode` boundary
with a fresh decoder for every sample. The production decoder does not expose
public physical-pixel, cell-unpack, or frame/schema substep boundaries, so
those stages are explicitly `null`/`unmeasured` and included only in the
combined strict interval. The pure pointer, click, key, and camera stages call
the existing planner APIs with bounded synthetic inputs. Stage quantiles are
not additive; CPU and elapsed wall values remain separate. Quantiles use
`sorted_samples[ceil(N*q)-1]`.

The decoder retains strict CRS1 behavior for valid Lua-rendered fixtures,
non-binary and physical-pixel disagreement, malformed cells, CRC failure,
advancing sequence, one-time boot acceptance and unexpected boot refusal, and
schema refusal. Fresh decoder instances intentionally exclude sequence/boot
transition cost from timing samples; the public-boundary tests exercise those
transitions separately. A valid PNG whose CRS1 payload is refused remains a
measured decode failure. Missing intervals are `null`, never zero.

Receipt files are read only for bounded diagnostics. The current artifacts do
not define an accepted matching live instrumentation contract, so even a
fabricated `accepted=true` object cannot qualify source/config/producer
bindings, paired CPU/end-to-end intervals, or eight-sample runs. Reports
therefore return `insufficient_evidence`, keep top-level accepted bindings
empty, and preserve only safe receipt digest, size, known-field, and unknown
field-count metadata. Local decoder hashes are measured-source identities, not
accepted region-runtime evidence. A separately reviewed matching live
instrumentation contract is required before the Phase 2 gate can be evaluated.

The decision cannot qualify live capture freshness, native producer binding,
controller timing, upload transport, model calls, or a Rust speedup. Those
remain a separate reviewed evidence-collection slice.
