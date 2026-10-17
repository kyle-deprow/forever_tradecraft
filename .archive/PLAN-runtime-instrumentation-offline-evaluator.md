# Offline live-receipt evaluator isolation slice

Root releases this independent offline consumer while frozen native R5 undergoes
Sol/actual Opus review. This supersedes only the implementation sequencing for
the three offline files below in PLAN-runtime-live-instrumentation.md; production
instrumentation still waits for accepted R5. The full data/measurement/privacy
contract and thresholds in that plan and PLAN-deterministic-runtime-performance.md
remain required. No accepted live instrumentation or bindings exist yet.

## Ownership and fence

Work only in /home/dev/.cache/crowley/worktrees/runtime-evaluator-20261017,
detached at5ed3fcb. Own exactly tools/session_performance.py,
tests/test_session_performance.py, docs/RUNTIME_PERFORMANCE.md. Read the two
canonical plans and current accepted Phase1 implementation in full first.
No production session source, native harness/C/build, addon, profiles, config,
services, GUI/input/capture, network/Docker/database, main-tree edits or Rust.
Do not commit/reset/stash/revert. Root owns integration. Source stays frozen in
this WT once handed over; report exact hashes. Native reviews keep their own
frozen WT unchanged and take precedence if a substantive fix is later assigned.

## Requirements

Implement only the schema2 offline evaluator/CLI and meaningful tests described
in the live instrumentation plan: strict bounded descriptor reads; separately
supplied accepted-binding file and parent-recorded expectedSHA; exact fixed
logical source map/config/producer matches; original8targets/all begun attempts,
completed paired intervals, failures, counter deltas and availability preserved;
all canonical quantile/120pairs/15runs/80percent/deadline-failure decision rules.
Keep Phase1 PNG replay and current unqualified receipt diagnostic behavior.
Live mode must be explicit, mutually exclusive with PNG replay, and must never
capture, invoke a model, contact services or create an accepted binding itself.
At most64 distinct live receipts; capped file sizes and strict duplicate/nonfinite
JSON/depth rejection. No raw paths/nonces/identities/run IDs/errors in public output.
No overlapping interval addition or absent-to-zero conversion. A paired measurement requires a successfully returned strict decode and trusted
same-attempt binding/schema/model/identity evidence; action timing qualification
is a SEPARATE field. Late successful decode still has a real CPU/wall pair and
must remain available to the canonical failed-run/counterfactual gate. It never
qualifies a late native sample as successful. Failed/ineligible records stay visible.

Make the schema2 receipt/binding interface concrete in the owned doc, faithfully
expressing all fields in the canonical plan. Require exact types, finite clocks,
ordered same-attempt boundaries, immutable target/index/deadline, correct reached
vs unavailable intervals and lifecycle state, exact8target/no duplicate records,
source/config/producer binding and counter consistency. Missing provenance or
unknown required stages yields insufficient_evidence, never a forged accepted run.
The evaluator verifies supplied evidence and expected parent binding digest; it
does not independently prove that a human reviewed the source or that supplied
JSON was captured live. State that practical limit plainly. There is currently
no qualifying real schema2 input: fixture decisions are test evidence only.
Use explicit null/reason for external CPU and private decoder substages. Keep
known actual public decoder CPU separate from PNG/capture/IPC; elapsed wall is
not CPU. Failures can trigger only the unchanged canonical counterfactual gate.

Meaningful tests include real existing Phase1 tests, binding/hash/size/file-drift
refusals; malformed/duplicate/nonfinite/deep/schema/privacy cases; missing/unknown
stages/counters; all failures retained; 14vs15runs and119vs120pairs; exact ceil
quantiles; pooled ratio vs ratio-per-sample distinction;80percent repeatability;
all3decisions; exact threshold equalities; distinct-runs failure trigger and
capture/I/O availability; and unchanged offline real public decoder behavior.
Do not add runtime timing assertions or mirror implementation with identical
copied algorithms in test oracles.

## Verification and completion

Run uv run pytest -q tests/test_session_performance.py;
uv run ruff check tools/session_performance.py tests/test_session_performance.py;
uv run ruff format --check on those exact2files;
uv run python -m py_compile on those exact2files; git diff --check.
Report actual results, schema choices, changed paths/hashes and unresolved issues.
DONE only when complete. Root reproduces and Sol reviews before integration;
no Opus required for these offline files alone. Actual Opus remains required for
later production instrumentation. No claim of a measured live bottleneck or Rust
migration follows from this slice.

## Parent correction before source review

Parent reproduced36tests/Ruff, then found the first offline contract had wrongly
coupled pairing to the1second qualification. The canonical plan takes precedence:
successful strict decode supplies paired computation/end-to-end even when timing
fails. Separate timing qualification from measuredpair provenance. Apply identity/
boot/sequence/nonce/cleanup/source checks consistently to ALL decoded paired data,
including failedlateattempts; preserve null/partial diagnostics for thrown decode.
Original scheduled targets are exactly1second apart;0.75–1.25 applies to ACTUAL
start/completion cadence, not declared targets. Passed-run declarations must meet
actual cadence/deadline; failedruns may truthfully retain timingviolations and
remain eligible by evidence/provenance. Record violations without silently
changing declared run state. Minimum/80percent/alternative gate follows canonical
plan verbatim; the failed outcome alone must not erase measured pairs.
A malformed/unknown-stage receipt in an otherwise full collection must return
insufficient_evidence as promised, not disappear from the decision denominator.
Preserve its digest/refusal and mark unrecoverable attempt counts unknown/null,
not falsely0. Add realistic mixed valid+invalid and late-decode/identity-drift
regressions. This is a correction of parentcontract, not runtime release.

Gate interpretation for this correction: the baseline remains120valid decoded
pairs across15independent fixed-eight-target runs (failed runs may stop early).
The primary pooled CPU/ratio route additionally needs15full eight-decoded-pair
runs for its80percent repeatability calculation. The alternate three-distinct-
eligible-failure route needs the baseline plus its explicit counterfactual
conditions, without adding a15timing-passed/full-run condition not in that route.
If baseline is adequate but primary repeatability lacks15full decodedruns and
the alternative does not trigger, verdict remains insufficient_evidence.
