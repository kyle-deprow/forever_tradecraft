# Integrate reviewed deterministic matching into the calibration helper

Goal: use the accepted Rust scorer for the existing template matcher without
changing matching decisions, desktop ownership, input, scan cadence or recovery.
This round starts only after final helper and scorer component acceptance.

Scope: tools/native_calibration_operator.py, its existing test module,
new tools/template_matcher_runtime.py, and tests/test_template_matcher_runtime.py.
No Rust/builder source, addon, driver, Guardian, daemon, controller, service,
profile, credentials or GUI changes. Parent owns integration/deployment/git.
No reset/stash/revert of others' work. Read component plans and exact freezes.

1. A small Python adapter verifies the exact reviewed release executable and
   manifest/source pins, private regular-file ownership/modes, and fixed protocol.
   Bind executable and reviewed Rust source digests separately from mutable
   adjacent metadata. Never trust a manifest to authenticate its own binary.
   Do not build at runtime, silently fall back to Python, or invoke a shell.
   Use one explicit private artifact root (CLI argument with canonical default)
   and fail clearly if unavailable. Parent publishes accepted artifact before
   any live invocation. Preserve pure Python reference only in differential tests.
2. Replace SEARCH and candidate SCORE_AT computation in TemplateMatcher while
   retaining manifest/template verification, exact role validation, RGB image
   conversion, captured-file digest, absolute box/center, threshold, ambiguity
   exception, role exclusivity and dual-positive overlap validation. Exact
   SAD/count determine score; validate closed response schema/types/geometry,
   count, range, status and decision consistency. Malformed output refuses.
3. Bound execution, input/output and cleanup using explicit process deadlines;
   honor any narrower remaining caller deadline rather than extending it.
   No runtime actor may survive cancellation/timeout/error. This scorer never
   emits desktop input or obtains an input lease. Record matcher binary/source
   digests in actual helper dependency receipts and production entrypoint.
4. Tests use the actual reviewed release artifact; fresh-build/current-source
   verification belongs to the component builder. Independent Python reference
   proves identical positive/negative/ambiguous/tie/edge/threshold results,
   exclusive candidate and dual-positive behavior. Exercise actual adapter
   invocation, malformed output, timeout/reaping, artifact/manifest/source
   tampering and refusal before GUI input. Keep small component tests meaningful.
5. Run helper actual compiled causal cases against accepted native and final
   world-readiness addon, including all100 updates and post-success ordinary
   recovery. Keep the original helper failure/recovery/provenance assertions.
   Full helper once after focused integration checks are green and source stable.
   Scoped Ruff/diff checks; retained private logs opened before commands,
   source hashes before/after, imports, artifact pin and actual exit status.
6. Parent independently inspects diff and reproduces relevant runtime parity
   plus actual helper composition. Sol and actual CLI Opus review the integration
   delta; do not reopen accepted component internals without a concrete issue.
   Parent then installs exact accepted helper/adapter/artifact, sole GUI owner
   runs live preflight and native100. This is not human input calibration.

Acceptance: unchanged visual and ownership semantics, real release invoked,
retained-frame whole-call benchmark improvement, actual helper lifecycle green,
no unresolved concrete review finding. No live or autonomous qualification is
inferred from offline tests. User physical GTK key/click only after native100
and ordinary recovery complete; then three autonomous 900-second scan loops.
