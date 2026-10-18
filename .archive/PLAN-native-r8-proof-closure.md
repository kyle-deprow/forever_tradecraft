# R8 proof closure

Root received R8 freeze (334 native passes plus named runtime pass) but the worker
confirmed three explicitly assigned regressions are absent. Production source is
not yet accepted. Preserve original native-final-commit-r8-20261018 and reports.
New native-final-commit-r8-proof-20261018 is based on a74297c with all seven exact
frozen R8 files copied and hash-verified. Own ONLY
tests/test_session_native_regressions.py. Six other files are read-only, especially
the three production modules. No helper, GUI, config, service, protocol, Git,
driver, Guardian, journal module or additional file edits. Do not commit, reset,
stash or revert another agent. Root owns final acceptance and git.

Read PLAN-native-final-commit-r8.md and R7 Opus review. Add these three focused
regressions at actual production boundaries, preserving current tests:

1. Worker completion/prepare/pause three-way barrier: orchestrate actual worker
   completion status snapshot, pause's controller-to-construction callback and
   prepare's construction-to-calibration access. Require bounded thread completion
   and cleanup. It must detect the old calibration-lock/status inversion, not
   merely assert a mocked method ran. Barriers may observe real locks/calls; never
   replace the relevant ownership gate or fake successful state transitions.
2. A genuine live deferred owner passes the outer finalization precheck, then
   waits for controller lock while its tighter final/hook/operation bound expires.
   Release the lock and prove the final transaction refuses the named deadline
   BEFORE rebind/observe/native_calibrated and cannot publish finalized. All other
   owner/context/generation/boot facts must remain valid. Use a real publicly
   prepared/bootstrap owner and the existing PNG runner fixture as appropriate.
   Cover each applicable tighter bound if a compact parameterization is possible.
3. Deferred resume callback receives missing/nonfinite sequence/capture facts
   with otherwise valid same-boot/newer-boundary metrics and a real resume_required
   owner. Require the named fact refusal before resume_ready/history publication,
   no INPUT_CALIBRATION and normal owner error/checkpoint cleanup. Avoid an earlier
   unrelated stale-frame guard masking the intended fact check.

Run only these new cases first, main .venv Python, explicit worktree PYTHONPATH,
private0700 XDG and authentic CLI config0.162.1. Preserve full private0600 logs,
exact source/dependency/base hashes, import origins and scoped Ruff/format/compile/
diff checks. No broad native rerun if all six read-only bytes remain unchanged:
retain the exact original334-pass log plus final added-case results, explicitly
distinguishing their test-file hashes. This is sufficient incremental evidence,
not a claim that the final combined test file ran in one334/337-test invocation.
If a test exposes an actual production bug, report exact reproduction before
changing production bytes; root will arbitrate the narrow repair and required
rechecks. Continue other independent proof work while awaiting that arbitration.

MAIN report writes only native-r8-proof-closure-{closure.md,freeze.json} under
.archive/executor-review. Include existing success semantics: native finalization
retains prepared checkpoint; a fresh ordinary recovery clears it. Parent source
inspection/tests and Sol + actual Opus full review still precede promotion. DONE
only when all three missing proofs actually pass, not when merely planned.
