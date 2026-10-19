# Native identity budget plan

Status: proposed for Sol/parent review. This is a plan only; no production or test changes are authorized by this file.

## Objective and measured boundary

Make the configured native producer complete all 100 updates with exact contiguous boot, sequence, ordinal, update-count, CRC, publisher-uptime and capture-freshness checks while preserving identity, foreground, owner, generation, lease, source, recovery, cleanup and timing guards. Keep the inclusive 750--1250 ms publisher cadence rule unchanged. Do not restamp publisher time, skip a frame, retry a mismatch, or cache a stale identity.

The gen37 diagnostic is the measured trigger: source drift was false, generation was 37, and the exact failure was requested `updates/2`, observed `updates/3`. The trace and bindings are preserved by digest in the parent review; use the [gen37 parent verification](executor-review/native-live-budget-failure-gen37-parent-verification.json) as the public evidence link. Installed source pins are daemon `4259e4de58b3b3d79f2fc595978907090a7f74666656a4af0c311a33602b0dad`, calibration `3a91f4fe690cd820329fe2536fc03e5c7de24e4c20649efdf1a705b8c147c8fc`, and driver `ca0ca123d0fa09d8361c8632d9cc1c2c501d87adf99cb3cc268688dd4291a166`.

The failed producer took 28.957 ms from telemetry capture start to return and provider decode took 57.159 ms. Backend lock-to-capture-start setup/admission was 117.511 ms. Identity spans were 140--178 ms and accepted post-capture identity was 224.612 ms. This is orchestration/process/I/O latency; Rust pixel or scoring work is not implicated.

The accepted ordinal-1 capture started at 218360.582279 and the next capture started at 218361.966850, a 1,384.571 ms consumer gap. Publisher uptime moved from 218359557 to 218361571, a 2,014 ms delta. The exact publication instant of ordinal 2 is unknown, but the consumer path demonstrably had insufficient margin for a 1 Hz stream.

## Exact current call graph

For each update, `NativeCalibrationRunner.run` currently resolves identity in `calibration.py` before calling the provider (`identity_pre_provider`). `SessionDaemon._native_measurement_provider` then performs `_check_native_poll_identity`.

In the deferred construction path, `_check_native_poll_identity` first checks shutdown, construction context, reservation id/epoch and operation deadline. `_native_construction_validate_snapshot` then checks controller generation, Guardian generation, desktop lease, Guardian armed state, process owner/start, profile fingerprint, identity fingerprint, B0 and expiry, but also performs a full `driver.resolve_identity`; this was the uninstrumented 142.073 ms gap before the failed attempt's recorded `identity_poll` span.

The recorded `identity_poll` performs another full resolve and rechecks controller state/generation. `_capture_native_region_for_identity` admits current controller state/generation and the configured X11 backend. The driver backend performs fresh full resolves at `backend_pre` and `backend_post`, binds the exact rectangle and producer executable, proves the admitted owner process, and verifies output identity/digest. After acceptance, `capture_observation` performs independent `identity_post_capture`, then cells, runner decode, CRC/sequence/metrics and timing validation.

Thus an accepted deferred update currently has outer pre-provider, deferred owner-validation, provider poll, backend pre/post, and runner post-capture resolves. The first three are before the producer. Backend pre/post and runner post are the fresh pixel-bound proof sites. The update-1 pre-provider span occurred several seconds before accepted attempt 14 and must not be summed into it; update 2's outer span ended immediately before attempt 15.

## Candidate reduction and preserved proof

The first candidate is NATIVE-only and keeps the existing driver backend and runner post-capture fences unchanged. It is eligible only for the configured X11 telemetry-region provider in the deferred construction path; normal movement, legacy/fallback providers, and generic recovery revalidation retain their existing fresh checks.

1. Remove only the updates-loop full resolve immediately before the configured deferred provider. Construct, held, resume, normal movement, and fallback paths are unchanged. The backend-pre resolve is fresher and rejects identity change before producer admission; backend-post and runner-post independently reject changes during/after capture.
2. In that eligible deferred provider path, retain all cheap construction owner, controller, Guardian, lease, expiry, profile, B0, process-start and epoch checks, but replace owner-validation's full X11 resolve with a comparison of the reservation identity fingerprint to the caller's originally verified identity fingerprint. This is not a vacuous self-comparison: backend-pre must then resolve the live client and compare its fresh fingerprint to that original before spawning the actual producer. The fast path is separate from generic recovery revalidation; existing `_native_construction_validate_snapshot` behavior remains intact elsewhere.
3. Remove the separate provider `identity_poll` full resolve only in that configured deferred path. Keep shutdown, context/epoch/reservation, controller state/generation and cheap owner checks. Backend-pre immediately follows and is the live identity/foreground/geometry admission fence for the exact producer.

No full identity result is cached across captures. Backend-pre still executes for every capture, backend-post proves the client did not change while the producer ran, and runner-post proves the retained PNG belongs to the same identity after decode. Owner process, executable digest, rectangle, lease, Guardian/generation, B0, source and cleanup checks remain at current boundaries. Identity changes before backend-pre, during capture, after backend-post, or during runner-post must still refuse.

The measured arithmetic predicts a capture-start gap near `1384.571 - 226.079 - 142.073 - 140.391 = 876.028 ms`, before ordinary jitter. The 750--1250 ms rule validates publisher-uptime deltas; it is not available consumer work budget. Repeated 1,100 ms consumer intervals miss 1 Hz slots, so the deterministic measured worst-case candidate path must be <=900 ms, leaving approximately 100 ms to the ideal 1,000 ms slot. The live 100-update gate remains final. If worst-case timing fails, stop and propose a separately reviewed faster resolver; do not alter cadence tolerance or remove another guard by inference.

## Exact implementation and test fence

Implementation may touch only:

- `src/crowley/session/daemon.py`: deferred-provider cheap owner-validation path and removal of redundant provider poll resolve;
- `src/crowley/session/calibration.py`: removal of update-loop pre-provider resolve, with all observation/cadence validation unchanged;
- `tests/test_session_runtime.py`: deterministic native-only budget and negative identity/owner-handover regressions;
- `tests/test_native_calibration_operator.py`: the existing exact configured-producer composition test `test_actual_operator_measure_composes_x11_screen_daemon_and_agent[success]` and directly necessary call-order assertions. It must retain the real fixture, producer, and 100 contiguous frames; no mocked spans or stock fallback may qualify it.

Do not change driver, decoder, protocol/schema, addon, GUI, Guardian, lease, service, config, helper, Rust or public receipt behavior in this round.

Before editing, add a self-contained deterministic publisher fixture using measured identity/admission/decode delays and exact 1,000 ms publisher uptime. It must fail on the old call graph because an ordinal is skipped, not because a return value is hardcoded. The candidate must reach all 100 frames while asserting publisher deltas 750--1250 ms, strictly increasing capture times, contiguous sequences/ordinals/update counts, CRC, identity and cleanup.

Focused regressions must cover identity mutation before backend-pre, during producer/backend-post, and after capture/runner-post; generation, lease, Guardian armed state, reservation epoch/id, profile, B0, process-start and executable-owner handover; wrong boot/phase, stale capture, bad metrics and noncontiguous sequence. A pre-admission fault must admit no producer. A fault during or after capture may have admitted/captured, but must reject the evidence, release and clean it, and never accept it. Add a call-count assertion proving no pre-provider or provider-poll full resolve remains in the eligible path while backend pre/post and runner post do.

The existing real configured X11/daemon/runner composition in `tests/test_native_calibration_operator.py::test_actual_operator_measure_composes_x11_screen_daemon_and_agent[success]` must then execute one exact 100-update success case. It must use the compiled producer, retain fresh receipt/digest/nonce/retirement proof, and assert existing lifecycle, identity, cadence, sequence, ordinal, CRC and cleanup outcomes. No stock fallback, mocked span, or synthetic frame source can qualify this gate.

## Verification and review gates

Run focused native/runtime tests, Python compile, scoped Ruff/format and `git diff --check` after the final edit. Preserve the old gen37 failure and all source/binary pins. Freeze source before Sol and actual Opus review. Parent must independently reproduce focused negatives, the deterministic 100-frame fixture and the exact configured-producer composition. Run the long native composition once after final freeze; do not rerun unrelated suites.

Any remaining diagnosis must be reported as measured or unknown. The plan is complete only when the candidate passes the focused semantic matrix, real configured-producer 100-update case, parent reproduction and both reviews.
