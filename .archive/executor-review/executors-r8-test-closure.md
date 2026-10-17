# Final test-only acceptance closure

Read AGENTS.md, CLAUDE.md and local-game-control skill. This plan grants no edits until root explicitly releases after frozen r11 full run and actual Opus review finish. Source has no accepted defect; preserve all production/helper implementation, including metadata nit (proofScope already explicit). No GUI, services/data/artifacts/profiles or git operations. Sole separate operator may run seed diagnostics while you edit tests only; your tests always use a private lease. Do not commit/reset/stash/revert others.

Owned files exactly:
.archive/executor-review/test_owned_gesture_proof.py
tests/test_session_native.py
tests/test_session_dispatch.py

Implement one small batch:
1. Direct actual _run_seed_chain success/error tests using backend._run external double, real admission-monitor thread and active_process_groups. Assert actual process result fields/error and schema/argv identity, registeredPID/timing evidence. No-op-before-dispatch counter must be0.
2. Prepare-context actual observer callback receives exact malformed raw diagnostic and stores cause/text/revokes; main _write_private captured output must contain same text/cause with FAIL and observer error. Keep doubles at process/observer/native-window boundaries and preserve production callback/main sequencing, not handwritten expected-state substitutes.
3. Real Guardian and calibration _validate_sequence: ordinary lag raw11/raw12/primary11/primary12 accepted; wrap lag rawMAX/raw0/primaryMAX/primary0 accepted; after raw12/primary11 a nonpending otherwise allowed event at11 must reject, preserving arrival clock.
4. Restore production open_ah test motion-before-click order with RawMotion before primary+echo. Upgrade camera entrypoint test to wrap real begin_action and real dispatch/check/finish; backend._run external double feeds press/raw/primary/echo/release under the ACTUAL captured camera contract (trace, coordinates, modifiers, echo). No Guardian replacement, no invented native claim.
5. Real Guardian and InputCalibrationWorkflow._controlled_echo_proof consumer matrix primaryMAX→echo0 accepted; 100→350 accepted;100→351 and100→50 rejected, using exact source/target/coordinate/modifier/sealed echo metadata. No fake native claim.

Verification: env -u CROWLEY_TEST_DATABASE_URL CROWLEY_DESKTOP_LEASE=/tmp/crowley-luna-test-closure.lock uv run python .archive/executor-review/run_hermetic_tests.py tests/test_session_native.py tests/test_session_dispatch.py .archive/executor-review/test_owned_gesture_proof.py -k 'seed or observer_diagnostic or receipt or echo or card32 or raw_motion or production_camera or production_pointer'
Run scoped Ruff/format/compile. Report exact files/checks/output and no unresolved issues, DONE only complete. Freeze after. Parent reproduces and obtains focused Sol test rereview; existing actual Opus review applies unchanged production code. Do not broaden into another source review/implementation cycle for tests alone.

## Final focused correction after Sol test rereview
Root releases the following coherent closure; prior tests-only fence expands ONLY src/crowley/session/guardian.py begin_action echo-proof validation. Snapshot before edit retained separately. Real zero echo proof cannot be replaced by1. Validate timestamp tuple indexes1 and7 with shared strict CARD32 helper (0valid, bool/negative/out-of-domaininvalid); device/target indexes2,3,4,8,9 remain strictpositiveintegers. Preserve all other proof/dispatch constraints. Reproduce actual _controlled_echo_proof result withMAX→0 directly into real Guardian begin_action before fix, then verify accepts; negative typed/domain cases reject. No coordinate/native matcher changes.

Close both remaining test-fidelity gaps in the same existing3testfiles: run main with actual_prepare_context (external driver/window/observer doubles only), trigger captured real observer callback during proof dispatch and let proof return; its observer error must itself produceFAIL in captured_write_private. Do not independently seed diagnostic/state or make proof throw. Camera wrapreal dispatch/check/finish with orderedcall assertions, verifyactionclearedBEFOREclose, and capturedexpectedtraceequals independently derived tuple(trace). No newprodmethods/refactors/helperedits.

Run original focused command and scopedchecks, plus full affected4file suite includingnative_regressions using private hermeticlease. Freeze exactsource/tests. Parent reproduces and focusedSol+actualOpus review validator delta, not whole subsystem. No GUI/services/data/git.
