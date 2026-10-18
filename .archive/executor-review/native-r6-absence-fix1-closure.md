# Native R6 absence fix1 closure

This is a candidate freeze from base `2fcdedd595b3349f4fdb3e3b23ef0153a9b72203` in `/home/dev/.cache/crowley/worktrees/native-r6-absence-fix1-20261018`. The six-file source fence and exact base/candidate SHA-256 values are recorded in `native-r6-absence-fix1-freeze.json`. No helper, driver, Guardian, addon, calibration, input-tool, protocol, configuration, service, deployment, GUI, or git mutation was made.

The absence classifier now uses the pure `_strict_native_absence_image(path, *, expected_size)` path. It rejects malformed size/mode, fully binary loading/ambiguous surfaces, encoded payload damage, the retained combined header/payload counterexample, and a second retained image with all four `CRS1` magic bytes plus payload occluded. It recognizes surviving fixed protocol geometry/version bytes after header erasure rather than substituting an arbitrary intact-cell percentage. Ordinary retained grayscale and colorful crops remain accepted. Direct candidate checks returned `False` for all three retained production `PixelDecoder` `ProtocolError` images:

- `black-loading.png`, SHA-256 `3b93f26267630963185ee67d8020972faee108a7bca80db725817e4680c9955c`.
- `encoded-header-and-payload-occlusion.png`, SHA-256 `d28917c2061dfb5f28ac28275d1e3a05c2f318e252e9d121d264c233408054ed`.
- `encoded-entire-magic-and-payload-occlusion.png`, SHA-256 `f28413cf71925638edda9f45ab2f775b84a94a8c33210af0bcd47f8af5e01e06`.

The construction operation envelope remains `3130.0` seconds, derived as `10 + (103 * 30) + 30`: 103 actual provider invocations, plus the existing entry and finalize bounds. Individual provider deadlines and the seven-second constructor reserve remain unchanged.

The real-daemon predecessor group passed `1 passed, 114 deselected in 3.40s`; it drives the same SessionIPC owner through missing reservation/checkpoint, wrong state, invalid handoff, cancelled/completed ticket, and cleanup cases. The exhaustive twelve-case SessionIPC predecessor matrix additionally verifies each public predecessor error is returned as a typed IPC failure.

The named barrier coverage is retained in `test_native_construction_composes_real_png_runner_and_finalize`, `test_deferred_start_seals_owner_before_pause_and_never_falls_back_to_legacy`, `test_native_recovery_begin_refuses_competing_capture_before_second_observation`, `test_native_recovery_cancel_revokes_inflight_capture_epoch`, `test_native_recovery_complete_cancel_barrier_preserves_checkpoint`, and `test_native_recovery_durable_commit_failure_keeps_checkpoint_for_fresh_owner`.

Coverage includes all eight native SessionIPC request shapes with unknown-field rejection and exact routing, all eight native CLI argparse roundtrips, the twelve predecessor error cases through SessionIPC, and the real daemon regressions for missing reservations/checkpoints, wrong state/kind, expiry, cancelled/completed tickets, and competing capture admission. Real barriers cover construction poll/pause lock release, deferred start/pause sealing and slot cleanup, recovery competing admission, in-flight cancellation with epoch revocation, completion/cancel commit linearization, fast finalize admission, and the fresh-owner durable checkpoint failure path. The existing configured compiled PAUSED producer/PNG decoder public composition is exercised in the final native suites.

Final-source verification used the authentic private Codex `0.162.1` binary at `/home/dev/.cache/crowley/codex/0.162.1/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex`, SHA-256 `628e35487d888a28f0427fc37501da529dd3d81fcbad7a2c3421c1e8670d92e1`, and private mode-0700 runtime directories. The final native suites passed `329 passed in 411.78s (0:06:51)`, exit code 0. The retained mode-0600 log is `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-r6-absence-fix1-final-20261018/native-three-suites-final-source-plus-real-predecessors.log`, SHA-256 `49edc41140ce5e97cef44efa0aef8e9a38ed6ffb3a1910c5c140b58f8f3351cf`.

Scoped Ruff format, Ruff lint, Python compilation, and `git diff --check` all passed. The retained mode-0600 static log is `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-r6-absence-fix1-final-20261018/scoped-statics-final.log`, SHA-256 `ef52491033e141c3155544a71cb5d144d629277dadeb632909fbdd17ec1cbde8`.

Parent independent verification, complete source review, Sol review, and actual Opus review remain pending. This closure makes no deployment, live qualification, promotion, or helper-integration claim.
