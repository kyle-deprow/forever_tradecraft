# Native final commit R8 closure

The bounded R8 source correction is frozen in the isolated worktree
`/home/dev/.cache/crowley/worktrees/native-final-commit-r8-20261018` at base
`7ac5c853928bd7fb8dc29492a2059007457a807c`. The six original files plus the
one explicitly authorized runtime fixture test are the only changed files.

The daemon now revalidates deferred finalization ownership and all applicable
final, hook, operation, and reservation deadlines at every capture/sleep edge
and again inside a controller-first final transaction. Final frame rebind,
observation, admitted native calibration, terminal receipt, owner clear, and
context close remain one controller→construction lock transaction. Producer
capture carries the exact owner capability through its execution gate, so
PAUSED no-producer capture fails closed and cancellation cannot dispatch a
revoked process. The worker completion snapshot is computed before taking the
calibration-state lock. Deferred resume readiness requires finite, newer
sequence and capture facts from the actual observation; the unfenced
`native_calibrated` retry and guessed resume values are removed.

Regression coverage includes real PNG runner cancellation in both finalization
interleavings, configured compiled PAUSED capture, no-producer refusal, public
cancel-before-producer admission with zero process dispatch, live-ID
predecessor guards, overlap/cancel recovery, durable journal-write rollback,
expiry, and all existing R7 classifier/IPC/transition cases. The named runtime
meter fixture uses the authentic private Codex 0.162.1 binary and accepts the
real generation/state admission keywords, returning an INPUT_CALIBRATION
status.

Final evidence is private mode 0700 with mode 0600 logs:

- `full-native-three-suites-final.log` — 334 passed in 443.09s,
  SHA-256 `729f127604cd9fbc13b9c20d53aa2f5a2f8cdc126b9e67ea582a8cfe287df35f`.
- `named-runtime-meter-final.log` — 1 passed, 14 deselected in 0.58s,
  SHA-256 `17e27749bdbc49b9a6cebd270f230b266ebaad4868cb8493074b89f85c7b3548`.
- `final-statics.log` — Ruff, format, compile, and diff checks passed,
  SHA-256 `9a53adb6e001e329dda013bc4e725b45247e5c7257b85e8c1ee2dfc4e5e9c5a6`.

The exact base and final SHA-256 values, source fence, authentic CLI pin, and
invocations are recorded in `native-final-commit-r8-freeze.json`. This is a
bounded offline source proof only; parent verification and independent Sol and
Opus rereview remain required before any promotion, deployment, live capture,
or native100 qualification claim.
