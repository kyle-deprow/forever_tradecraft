# Narrow Rust template matching acceleration

Objective: remove deterministic template-scoring latency from the calibration
helper without changing visual acceptance, input ownership or scan cadence.
User authorized a Rust rewrite if computation is a measured bottleneck.
Parent actual retained WoW frame measured 2.5531s Construct + 2.5208s Restore
using the current pure Python matcher on the 220x84 region and 98x27 templates.
See executor-review/real-wow-control-matching-benchmark.json. Two sequential
role matches consume about five seconds; measure live boundaries separately.

This is independent preparation while helper recovery is corrected. No helper
source modification or live installation until both changes are accepted.
No new service, agent runtime, input API, screenshot API or trading behavior.

## First implementation scope

New native/template_matcher/Cargo.toml, native/template_matcher/Cargo.lock,
native/template_matcher/src/main.rs, tools/build_template_matcher.py,
tests/test_template_matcher.py, plus an update to docs/RUNTIME_PERFORMANCE.md.
No modifications to tools/native_calibration_operator.py, its tests, daemon,
Guardian, driver, addon, profile or running services. No GUI/game input.
Parent owns git. No resets/stashes/reverts. Read full plan before editing.

1. Inspect exact current TemplateMatcher/_mae/_candidate_score and matching
   contracts in frozen helper native-operator-causal-composition-20261018.
   Rust std-only bounded command-line executable; no third-party crates needed.
   Preserve RGB absolute-difference sum/mean, all allowed coordinates, threshold
   <=5.0, best tie ordering (score,x,y), and ambiguity relative to BEST box,
   not merely the second-best candidate. Preserve accepted/rejected score,
   dimensions, edge-inclusive scan bounds and role exclusivity behavior.
2. Fixed, versioned raw-RGB stdin protocol with checked dimensions/lengths,
   bounded bytes/coordinate arithmetic, no arbitrary files/commands or network.
   Return a small structured numeric result on stdout, explicit nonzero on
   malformed input. Document protocol precisely. User paths never executable.
   Rust binary handles scoring/ambiguity only; Python retains artifact hashing,
   manifest verification, identity, receipt and all input ownership.
3. Reproducible release builder verifies/builds exact source, creates private
   versioned executable artifact + manifest with source and executable digests.
   Verify existing artifact against its manifest before reuse; reject mismatch.
   Keep actual host paths and raw screenshot/template artifacts out of git.
4. Independent Python reference differential cases: actual retained frame,
   seeded images, both roles, equal-score ties with x/y priority, multiple
   overlapping acceptable boxes, disjoint ambiguity, absent template, region
   edges, malformed/truncated/oversized protocol/overflow. Compare exact scores
   to reference within float representation precision; no timing relaxation.
   Preserve complete private build/test logs and before/after hashes.
5. Benchmark same actual retained frame/region/templates after release compile
   with captured argv/imports/binary digest, report startup+IPC+matching cost
   separately from compile. Aim <100ms per role on host; if not, report actual
   numbers and cause. No unmeasured claims about fresh input/scan performance.
6. Parent meaningfully reproduces parity + benchmark, Sol and actual Opus review.
   Then a separately approved integration round may add bounded invocation to
   the corrected helper and bind binary/source digests in receipts. Until that
   round, the current helper remains the canonical implementation.

## Acceptance

Full scoped parity/negative checks pass, no out-of-scope edits, clean scoped
format/lint, exact source/artifact proofs, measured improvement on retained
actual frame, review findings arbitrated. No live qualification inferred.

## Sol plan arbitration: exact implementation contract

Root accepts all initial Sol plan findings. The following details supersede
ambiguous earlier prose. This remains a plan, no production helper integration.

- Two operations: SEARCH (bounded global search) and SCORE_AT (only the exact
  positive candidate box). require_exclusive uses SEARCH positive + SCORE_AT
  rival; require_dual_positive uses SEARCH twice and Python overlap validation.
- Stdin header exactly48 bytes: ASCII magic CRWTM001 (8bytes), then ten unsigned
  little-endian32 integers: operation(1SEARCH/2SCORE_AT), reserved(0), frameW,
  frameH, templateW, templateH, regionX, regionY, regionW, regionH. Follow full
  frame row-major RGB8 bytes, then template row-major RGB8 bytes, then EOF.
  Positions/boxes remain absolute full-frame coordinates. SCORE_AT requires
  regionW/H exactly templateW/H. Reject truncation/trailing bytes/unknown op,
  nonzero reserved, zero/out-of-bounds dimensions or checked-arithmetic overflow.
- Limits: frameW/H<=4096, templateW/H<=512, total input<=64MiB; checked proposed
  comparison count<=2^31 bytes per invocation. Invalid requests exit nonzero
  with concise stderr, no result JSON. Validate caps before allocation/work.
- Result one JSON object: status matched/rejected/ambiguous, sad integer sum,
  count integer template byte count, box[x,y,w,h]. All scores computed as exact
  RGB absolute differences. Accept SAD<=5*count. SEARCH best=min(SAD,x,y).
  Ambiguous iff another acceptable candidate is disjoint from best box under
  existing rectangle semantics. A valid absent match returns rejected with
  best SAD/count/box and exit0. Ambiguous is semantic exit0; Python later maps
  it to the existing ambiguity exception. SCORE_AT cannot be ambiguous.
- Tests compare exact SAD/count/box/status, including threshold exactly5 and
  one total absolute-difference unit above5*count. Float conversion remains
  Python SAD/count. No score tolerances used to accept changed decisions.
- Pinned std-only toolchain Rust/Cargo1.85.1, x86_64-unknown-linux-gnu. Official
  release: https://blog.rust-lang.org/2025/03/18/Rust-1.85.1/ . Parent found no
  rustc/cargo on PATH; private verified installation is a separate prerequisite.
  Build --release --locked --offline, no target-cpu=native, fixed CARGO_INCREMENTAL=0,
  debuginfo0, strip, single codegen unit, remap build paths; record exact rustc-vV,
  cargo version, target, flags and source hashes. Byte-identical reproducibility
  is claimed only after two independent target-directory builds actually match.
  Rebuild from reviewed source/toolchain to revalidate existing publication;
  an adjacent mutable manifest never authenticates its own binary. Publish
  privately/atomically; exact binary digest is pinned separately at later helper
  integration. Do not install/change system toolchain or GUI during worker scope.
- Benchmark preparation/serialization, process startup+IPC+parse, SEARCH,
  SCORE_AT, and both composed exclusivity and dual-positive call shapes. Count
  actual data conversion/transfer and binary startup, never compile in matching
  timing. Retained real frame proves computation only, not live input readiness.
