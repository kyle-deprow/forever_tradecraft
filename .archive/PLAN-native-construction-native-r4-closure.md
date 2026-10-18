# Native R4: finish the rejected R3 correction round

R3 is frozen and rejected before external review. Its final report acknowledges
an unresolved Must (construction/controller lock inversion). This was explicitly
inside the authorized six-file fence; fixing it is required, not scope expansion.
R3 also left several concrete required corrections unimplemented. Do not rerun
the broad suite or request review until the focused proofs below pass.

Use native-construction-native-r4-20261018, base e6e17bb, exact six frozen R3
files already copied and hash-verified. Own only the same three production files
(controller.py, daemon.py, cli.py) and three native test files. All other source,
addon, services, GUI, config, dependencies and git mutations remain forbidden.
Read PLAN-native-construction-native-review-fix.md and the ordinary recovery
amendment again as the acceptance criteria, not optional review suggestions.

## Concrete unfinished source requirements

1. Recovery-begin and complete still hold constructionlock across controller
   calls, captures and controller commit (R3 daemon lines1634-1830). Expiry still
   invokes Guardian cancellation inside that lock. Remove every reverse nested
   lock/callback edge; capture outside owner/controller locks, retain a provisional
   epoch-bound admission, revalidate under an explicit safe order before commit.
   Prove real public pause/recovery races with thread barriers and bounded joins.
2. The ordinary_reload branch is unreachable: begin rejects every boot other
   than B0/prefixed, then requires B0 fence armed, leaving the later ordinary
   branch impossible. Implement the amendment literally: ordinary normal0 /
   inactive fence includes BOTH unchanged unarmed B0 and later ordinary C.
   Preserve armed-B0 restore, prefixed restore and strict absence restore.
   Cover all five concrete variants through IPC; reject same/old/prefixed/fenced
   completion and prove fresh-controller atomic recovery after write failures.
3. start_calibration still checks construction admission then independently
   publishes starting (R3 lines918-938). The competing-entry helper ignores
   provisional inflight and expiry. Legacy native_bootstrap is still bypassable.
   Establish the promised single linearization point for those admissions,
   diagnostic/interaction, prepare and recovery. Test genuine competing threads.
4. Deferred callbacks still decide legacy versus deferred from the mutable live
   reservation; worker except still clears arbitrary current reservation/ticket
   (R3 lines6425-6435). Retain immutable per-run ID/epoch/context through cleanup;
   cancellation must fail that run, never switch its callbacks to legacy or clear
   a later recovery ticket. Every wrong predecessor, including early/late finalize,
   must revoke the matching owner; preserve the first causal failure.
5. _capture_native_region_for_identity now allows PAUSED generically whenever
   no expected_state is supplied. Restore closed default NATIVE admission and
   admit PAUSED only with the exact live generation-bound provisional/recovery
   capability. A test-only observation provider or overridden capture method is
   not proof. Exercise the actual configured compiled producer adapter for prepare,
   preflight, recovery begin/complete and generic PAUSED refusal.
6. _strict_native_absence_capture treats a single non-flat/non-BW pixel as
   absence, including a damaged otherwise encoded grid. Preserve/reuse the strict
   legacy classification rather than widening it: malformed header/CRC/schema,
   stale encoded surface and one-cell/pixel corruption must refuse. Test actual
   PNGs through the production decoder path, not only uniform BW fake images.
7. Finish the original R3 acceptance coverage and actual constraints: two real
   distinct captures around reset, verified deletion before release with durable
   clear metadata; all eight parser/IPC commands and terminal receipts; all twelve
   predecessor edges, real bound clocks and finalize fast-admission race; total
   malformed checkpoint/frame counter validation. Address actual reachable gaps,
   without adding unrelated hardening or changing any production deadline.

## Fix the fixtures before full-suite verification

The R3 transition test claims to inject a private pin but hardcodes the HOST path
/home/dev/.local/share/pnpm/nodejs/22.23.1/bin/codex. That is exactly 0.163.0.
Use the already verified AUTHENTIC private binary:
/home/dev/.cache/crowley/codex/0.162.1/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex
SHA256 628e35487d888a28f0427fc37501da529dd3d81fcbad7a2c3421c1e8670d92e1.
Inject that explicit configured path in the test, and use private0700
XDG_RUNTIME_DIR for all fake desktop fixture leases. Never fake version output,
change the host/default production pin, or rely on PATH overriding an explicit path.

Diagnose the paused one-second sample failure from the actual trace. Repair owned
test scheduling/proof if needed; do not label host load causal without evidence,
weaken assertions or increase the production deadline. Focused failures must be
resolved or precisely proven pre-existing with actual traces before broad reruns.

## Completion

Send one short implementation milestone before tests. Run focused new tests first,
then full three suites once, scoped Ruff/format/compile/diff and programmatic six
hashes. Preserve full private logs and exact invocation/environment bindings.
Write R4 freeze.json and closure.md in MAIN .archive/executor-review only when
ready; keep R3 freeze/closure immutable. Explicitly list any unresolved plan item;
do not call an acknowledged Must outside scope. DONE only if the entire slice
is complete. Parent independently inspects/tests, then Sol and actual Opus review.
No promotion, service change, helper implementation or live input is authorized.
