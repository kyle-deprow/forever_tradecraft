# Native terminal proof R10c closure

R10c completed the two remaining test proofs against the frozen R10b production bytes. The worktree was `/home/dev/.cache/crowley/worktrees/native-terminal-proof-r10c-20261019` at base `c5e577200adadb8c158b1009643aa0f746d98753`. Production files, helper/driver/Guardian files, configuration, services, GUI state, and Git state were unchanged.

The finalize/cancel test now gates cancellation after the real `_native_construction_flush_expiry` returns, forwards the real controller lock through a thin observing facade, records the cancel thread's failed nonblocking acquire while the real final transaction owns the controller mutex, then lets the public cancellation finish. Both terminal orders retain their public `native_construction_recheck` assertions: finalized for final-wins and cancelled for cancel-wins, with the existing rebind/observe/native-calibrated and checkpoint assertions. This is covered by `test_native_construction_composes_real_png_runner_and_finalize[False-None]` and `[True-None]`.

The restart proof counts the actual observation provider. Public control preflight made exactly one provider call. Public recovery restart refused the live reservation with the exact live-reservation error, made no additional observation call, left the reservation owner unchanged, and left no inflight owner. This is covered by `test_native_recovery_restart_refuses_live_reservation`.

The final arbitration's two small test assertions were also applied. The four compiled Guardian-order cases directly assert that the reservation owner and construction epoch remain unchanged after Guardian generation advances while the callback is blocked, and the vacuous nonnegative epoch assertion was removed. The public inflight capability proof now asserts its `guardianGeneration` equals the second driver's actual Guardian generation. The four compiled cases use the authentic pinned Codex CLI, real private Shell compositor/X11 backend/compiled producer/decoder path, and private 0700 runtime/bus isolation.

The final focused invocation covered all eight required case IDs and passed:

- `8 passed in 49.75s; exit_code=0`
- Log: `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-terminal-proof-r10c-20261019/focused-r10c-eight.log`
- Log SHA256: `44b50c75cb10d7ac63baeb58197ffc3a3a7263d58f7970dccaf9ca6c9f33fa83`

The eight cases were the two finalize/cancel orders, restart refusal, inflight capability generation, and compiled `paused-revoke-first`, `paused-admission-first`, `native-revoke-first`, and `native-admission-first`. Earlier retained three-case evidence also passed (`3 passed in 44.35s`; SHA256 `ef1b0b1206097d45a83142cd38e3c3c6cd6044073a7cc326fef869d827e86988` for the final three-case rerun).

Scoped checks passed on all seven fenced files: Ruff format check, Ruff lint, Python compileall, and `git diff --check`. The final static log is `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-terminal-proof-r10c-20261019/static-r10c-final2.log` (SHA256 `d33d34cd061da999b07e64da244733b25bf6ece71b753f0efa54162040d68c97`). The AST fence log is `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-terminal-proof-r10c-20261019/ast-fence-r10c.log` (SHA256 `bd17c01738867cce0aee572cfcb8931465aa68bb4f09fa3ee7e8dfd59699fd49`); it reports only the named compiled test and the three named regression functions changed against the R10b baseline. All private evidence logs are mode 0600 in a mode 0700 directory, and no stale pytest, producer, Xvfb, or dbus-run-session processes remained.

The final seven hashes are recorded in `native-terminal-proof-r10c-freeze.json`. The five readonly files retain their R10b hashes. The two writable test files have only the named proof changes. The prior R10b broad result is preserved; R10c intentionally did not repeat a broad suite.

For traceability, the already-arbitrated R9 same-kind starting-record adoption remains the public input-start fix, and malformed legacy resume facts remain intended early fail-closed behavior. The supplementary `/bin/sleep` test is unit-only outer capability-refusal coverage and is not counted as the compiled Guardian-generation proof; the four compiled cases above are the required producer proof. Parent verification and focused Sol review remain pending; no deployment, live claim, or acceptance promotion is asserted here.
