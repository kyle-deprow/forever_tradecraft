# Sol plan review R2 — native identity latency Stage 1

Plan reviewed: `.archive/PLAN-native-identity-latency.md`

Verified SHA-256: `397bccaa859a7e39c31eef7555aa5f10764dd63329f118478e4004ac5ca2d685`

The R1 findings are closed without expanding Stage 1:

- The collector now captures monotonic, thread CPU, and process CPU clocks at
  `capture_paused_region_sample` entry, then binds to the request directory or is
  discarded if no directory exists (`.archive/PLAN-native-identity-latency.md:40-49`).
  This covers the actual interval from `src/crowley/session/daemon.py:3720` through the
  directory creation at `src/crowley/session/daemon.py:3829-3834`.
- The artifact now separates two non-additive wall intervals, four closed-enum identity
  barriers, and bounded nested events. Start/end/duration semantics and same-pair
  thread/process CPU deltas are explicit; unreached values remain null
  (`.archive/PLAN-native-identity-latency.md:88-151`). The four barriers still correspond
  to `src/crowley/session/daemon.py:3852,3947` and
  `src/crowley/session/driver.py:2800,3094`; none is removed or cached.
- Artifact reading is descriptor-bound and race checked. Its computed SHA-256 is only
  provenance, and the former impossible self-authentication/hash-mismatch claim is gone
  (`.archive/PLAN-native-identity-latency.md:58-66,168-169`).
- Live mode now requires a separate parent-reviewed, descriptor-bound 0600 manifest and
  independently supplied SHA before the first request. It carries the exact seven-source
  map plus raw/semantic config and producer digests; mutable runtime files cannot assert
  their own acceptance (`.archive/PLAN-native-identity-latency.md:67-78,170-172`).
- Atomic profile publication failure now leaves the profile absent and records only a
  fixed private token; published status is limited to `complete|partial`, and the causal
  capture failure/response schema remains unchanged
  (`.archive/PLAN-native-identity-latency.md:50-57,89-97,152-153,166-167`).

The existing six request keys, one-second deadline and 250 ms failure-evidence grace are
preserved (`.archive/PLAN-native-identity-latency.md:79-87`). The implementation remains
isolated to the four named files and is explicitly barred from integration or service
restart during native-100 qualification (`.archive/PLAN-native-identity-latency.md:26-38,183-188`).

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
