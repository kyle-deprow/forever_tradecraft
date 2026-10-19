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

## Sol plan arbitration: exact integration contract

Parent accepts all three concrete plan findings; these details supersede earlier
ambiguity. Source implementation waits for final component and helper-proof gates.

- Add `deadline_monotonic` to match, require_exclusive, _match_at and
  require_dual_positive. Thread the existing _capture absolute deadline through
  every scoring call for the proof. SEARCH and SCORE_AT share it; never reset a
  timeout between subprocesses. Refuse before spawn if expired/remaining work
  cannot fit; kill and reap on actual expiry, including cancellation.
- Canonical default artifact root is Path.home()/'.cache/crowley/template-matcher/v1'.
  Production CLI `--matcher-artifact-root` wires it to the adapter injected into
  TemplateMatcher and NativeCalibrationOperator. Parent installs the adjacent
  runtime adapter and accepted artifact before live use. No Python fallback.
- Code-owned immutable executable SHA256 is
  75b18bd04cc3a9248f99ecdca3a1cdebe6e0d89c4d33eaebd600788177bcd80c.
  Reviewed Rust source pins are Cargo.toml3307fd9c7503479a443bbd23554958cda94343596985f9772ceba4187aeb7cd8,
  Cargo.lockea23646a59c8a3956ede087e8fea60643cbd016771f435fe84c24c467861a9b2,
  src/main.rsbb3647dc12804670d391170563284799fce7b931a07f663726767e95402b47a3.
  Adjacent manifest is corroborating metadata only. Validate source pins, artifact
  identity/private ownership/mode, and protocol; retain a verified no-follow
  regular-file descriptor and execute that descriptor via /proc/self/fd with
  pass_fds so a path replacement cannot swap the executable after verification.
  Close every retained FD on all setup/runtime/cleanup paths.
- _source_bindings binds actual runtime adapter source and the independently
  pinned binary/three Rust sources to helper receipts. Tests compare these
  values to independently read known artifacts and reviewed constants.
- Start from FINAL helper proof corrections, not superseded test39f7: actual
  DaemonClient/SessionIPC public post-success pause, actual READY/watchdog ACK
  then expired pre-GO first-key budget with zero action records, and exact
  independently calculated receipt source/artifact hashes. Preserve these
  assertions in the actual compiled causal full helper run with final addon79.
- Retain and rerun actual-frame benchmark THROUGH the new Python adapter and
  TemplateMatcher exclusive/dual call shapes, including PNG preparation,
  source/artifact verification, serialization, process startup/IPC/parse. Pin
  runner/argv/fixture hashes and assert reference decisions. Component timings
  alone do not prove integration latency. A focused test command with supplied
  private fixture paths may serve as the reproducible runner; no private images
  enter git. Parent independently reproduces final integration evidence.

## Independent preparation stage

To avoid idle time while final component reviews and helper test-proof closure
finish, stage A may implement ONLY new tools/template_matcher_runtime.py and
tests/test_template_matcher_runtime.py in rust-matcher-runtime-integration-20261019.
The seven frozen scorer files and the old helper pair are read-only contract
inputs. Use parent independently built release for isolated tests. No helper
integration, promotion or live use before component acceptance and final helper
proofs. Stage B later owns the remaining helper/test edits using the finalized
proof baseline. This changes ordering only; reviewed trust/deadline/proof
requirements and all deployment gates remain in force.

## Parallel helper wiring preparation

Component is now final Sol+Opus READY, parent31checks/reference benchmark green;
standalone adapter final Sol READY and parent16checks green. While the independent
helper-proof fixture correction finishes, the integration worker may wire the
helper production source in its isolated integration worktree and run focused
matching checks. Leave _record_operation_deadline unchanged there; the parent
will bring in the narrow finalized deadline-method correction with the corrected
helper test baseline. Do not edit the older helper test file before that handoff.
No full-helper claim, final review, deployment or live use until the exact final
proof tests and deadline method are incorporated and run. The two worktrees do
not share editable source files. This preparation changes ordering only.

## Frozen review may overlap validation

After parent inspected the combined delta and independently passed22 focused
checks on exact frozen helper877642/testa9625/runtimeedc524/test302f74, the
read-only Sol review may overlap the unchanged full94-test run. This saves idle
time without changing acceptance: the full combined run, parent actual workflow
reproduction and final Opus review must all pass before installation. Any source
change invalidates its previous frozen review until the changed delta is reviewed.
No live qualification is inferred from this scheduling change.

## Actual Opus R1 deadline follow-up

The actual review completed0/NEEDS WORK with no Must and one accepted Should.
In the same four-file worktree, remove TemplateMatcher's silent fresh-five-second
deadline default, require the absolute deadline at each matching API, and test
actual Operator._capture propagation to SEARCH/SCORE_AT and both dual searches.
Inject runtime error/timeout/rejection through actual _click and assert no emitter
allocation or recorded input. Clarify the existing minimum-test comment only;
other review nits are nonblocking and deferred. No native/runtime architecture,
GUI, matcher-algorithm or deferred-nit changes in this round.

Run focused new boundary tests and runtime17, then full combined suite once stable.
If only those two new test functions receive stronger assertions after that full
run, preserve its original exact test hash and verify all other module AST is
unchanged; rerun every revised test/parameter on the final hash instead of another
unchanged hundred-second native measurement. Record the mixed-version evidence
truthfully, never as a full run of the later test file. Production hashes must be
identical across both checks. Parent independently reproduces those new boundaries;
Sol and actual Opus review only the small delta against exact prior877/314e source
copies. Baseline hashes are independently verified in private deadline-delta review
directory. All review/validation gates still precede installation and live input.
