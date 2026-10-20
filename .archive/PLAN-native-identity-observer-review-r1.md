# Native identity observer — formal review R1 correction

Approved for bounded Luna implementation by root under existing user authorization.
Work ONLY in /home/dev/.cache/crowley/worktrees/native-identity-observer-fix-r1-20261020.
The original worktree remains frozen for actual CLI Opus R1; do not modify it.
Read the original .archive/PLAN-native-identity-observer.md in full. Same exact
13-file implementation fence, including its accepted narrow daemon recheck seam.
Parent owns this plan and copied current skill; those pre-existing changes are not
worker edits. No additional source files or dependency downloads.

## Accepted corrections

1. Sol S1: prevent mixed process lifetimes. Revalidate full PID/start/command,
   status/loader/prefix after complete X11 observation and reread exact title/class
   and PID/window binding. Refuse any relevant change. Preserve reference semantics,
   including canonical prefix handling. Exercise deterministic process replacement
   and real window mutations; no mocked facts or cached identity fallback.
2. Sol S2: synchronize observer invoke/close and sealed FD ownership. Duplicate or
   retain the verified image safely under a lifecycle lock; own active invocations,
   cancel/kill/reap them on shutdown; prevent new work after close. Preserve caller
   cancellation/deadline and bounded cleanup, causal errors and no FD leaks. Close
   backend on failed Guardian/lease construction, including partial failures.
   Add barrier-controlled close/invoke and failed-lease FD-count regressions.
3. Sol S3 + independent parent reproduction: fix retained pending bytes plus
   rewind/reopen duplication in action_bridge. Choose one clear owner for bytes.
   Regression must exercise actual close/reopen/offset path between fragments;
   no action/ACK before complete record, exactly one afterward, malformed and next
   valid records handled. Preserve atomic writer and production acknowledgements.
4. Sol S4: force real finalize between recheck snapshot validation and second lock,
   send the reply through a real CancellationActor using AF_UNIX SessionIPC, assert
   actual actor acceptance of canonical finalized binding/history, committed native
   state, exact generation, deep copies and different-ID/wrong-generation negatives.
   Do not extract or fake the actual validator or seed desired controller outcomes.
5. Sol S5: implement original plan's actual owned Xvfb/process mutation matrix:
   accepted full reference WindowIdentity/fingerprint parity; title/both WM_CLASS
   values/PID/process replacement and uniqueness/geometry/tree/reparent/root/focus/
   active changes as applicable. Mutate real observations rather than request values.
   Fault separately at backend-pre/backend-post/runner-post with actual fresh Rust
   observations; prove producer non-dispatch or owned capture rejection/release at
   correct boundary; restore and prove fresh reread. No return-dictionary mocks.
6. Sol S6: hermetic builder accepts only exact three source files and expected
   directory structure; reject build.rs, .cargo/config, extra modules/symlinks, with
   meaningful rejection tests. Preserve stable snapshot, static/linker hashes and
   byte-identical offline double build.
7. Sol S7: verify executable-mode contract before sealing an executable memfd;
   test unsafe modes and no input/lease acquisition on factory refusal.
8. Keep permanent private test-only common IPC receipts; serialize complete JSONL
   records across concurrent handlers if needed, with no IPC behavior change.
   Original isolated actor_admission_invalid remains unexplained; do not relabel a
   later passing run as historical causal closure. Preserve diagnostic evidence.

Reference/test-only prefilter optimization (Sol nit S8) is deferred: mandatory
production always uses Rust. Do not expand this fix to an unused performance path.
Root will arbitrate any additional actual CLI Opus R1 findings when it finishes.
Routine in-scope implementation choices are yours; keep going on independent work.

## Verification and completion

Run new decisive regressions first. Then exact owned Xvfb component, driver actions,
full tests/test_session_native.py (lifecycle/source changes justify fresh broad run),
real compiled operator/daemon/Agent composition success with independent 1Hz clock,
three fresh boundary nonces, contiguous1..99/held100/resume0 and maximum active<900ms,
actual-actor forced race and relevant runtime/input-constructor checks. Source hashes
must match final composition. Preserve numerical per-attempt/boundary measurements,
source snapshots, binary/static/linker manifest and all commands/results privately.
Run Cargo offline/locked, rustfmt, scoped Ruff/format/compile and git diff --check.
Do not repeat unrelated broad suites after passing unless changes justify it.
Final report includes precise coverage map, all13 final hashes, binary/log hashes,
actual outcomes, unresolved limits and DONE only if implementation is complete.

No live GUI/capture/input/IPC/services/config installation, game movement/trading,
DB/kernel writes, external messages, Git commit/reset/stash/revert/push, global
formatting, calibration/decoder/Guardian/addon/public schema/admission weakening,
consumer-driven publisher clocks, alternate decoders or production fallback.
Keep artifacts dirs0700/files0600/executables0700. Root owns Git and promotion.
