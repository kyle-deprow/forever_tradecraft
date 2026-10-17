# GNOME telemetry region R3 to R4 owner-IPC delta

R3's default-daemon composition and eight-sample diagnostic were separate: the
composition test stopped at a static capture, and the diagnostic created a
second DesktopDriver with a private desktop lease. R4 keeps the real compiled
R3 producer and routes diagnostic samples through the already-running
SessionDaemon and its existing DesktopDriver, X11Backend, Guardian observer
ledger, and canonical lease. The runner's config binding now covers the whole
loaded SessionConfig, not just fields echoed by the caller.

The default-daemon test now exercises the compiled producer through native
bootstrap, native-frame capture, strict PixelDecoder and MotionFrame creation,
then checks that `_capture_model()` on that same region-enabled daemon still
uses stock full-desktop capture. Its private fixture simulates only the game
window and Shell compositor boundaries. The eight-sample runner loads the
actual config, uses existing status and `paused_region_sample` IPC, preserves
the original parent timestamp, and enforces generation, PAUSED state, producer,
config, identity, receipt, PNG, sequence, boot, retirement, deadline, interval,
and immediate fail-stop checks. The runner creates no driver or Guardian and
does not release or close the owner.

Owner capture IPC uses strict bounded newline records in both directions
(4096-byte requests, 524288-byte responses), rejects duplicate JSON keys and
non-finite numbers, and returns actual producer receipts plus owner and client
artifact evidence. Published PNGs and bounded receipts remain available after
post-publication failures; pre-publication failures retain error phase and
cleanup evidence without inventing a PNG. Producer retirement now reflects
observed reaping and attempt-directory cleanup. Pause/stop revocation is tested
while the real Shell call is blocked, with the owner lease and watchdog kept
healthy.

The owner and client independently hash `dataclasses.asdict(SessionConfig)` as
sorted compact JSON after normalizing every `Path` with `os.fspath`. The raw
TOML file SHA remains separate client provenance. Before capture admission the
owner requires the semantic hash to match its loaded config and confirms the
active driver's profile matches that config; it repeats both checks at actual
producer admission and after capture. The real socket fixture changes only
`capture_dir`, leaving crop and producer unchanged, and proves the owner refuses
before Guardian admission or Shell capture.

The race tests record both actual linearization orders. In the first, stop
completes while identity resolution is held at a barrier outside controller
and Guardian locks; the request then rechecks state and never enters Guardian
admission or Shell capture. In the second, the Guardian admission wrapper
returns after the real gate release, Shell records its monotonic capture entry,
then stop revokes the observer and the producer is reaped before publication.
No test blocks inside Popen, the admission gate release, or the authority
locks.

Verification completed:

- `test_compiled_region_composes_through_default_daemon_and_stock_model` passed.
- After adding owner-validated semantic config binding and making the IPC fixture preserve actual owner refusal responses, `test_paused_diagnostic_uses_actual_config_ipc_driver_and_eight_compiled_samples` passed in 33.56 seconds. It included the changed-`capture_dir` same-crop/producer refusal before admission/capture and the malformed, oversized, truncated, late, wrong-generation, wrong-digest, incomplete-image, identity-change, `NO_CHANGE`, boot-change, generation-change, and stop-race cases.
- The compiled default-daemon composition test passed in 3.84 seconds. The full CLI-motion file passed 14 tests in 0.96 seconds.
- The existing private compiled binary passed offline `--self-check --self-test`. Scoped Ruff, format, compile, and `git diff --check` passed.
- The parent-run hermetic batch recorded 316 passed and 2 failed in 368.60 seconds. Both failures were fixture setup failures because `PRIVATE_TOOL_ROOT` was absent when `X11Backend` loaded the authentic private xdotool artifact; the exact output is retained in `gnome-telemetry-region-parent-r4-host.log` (exit 1). Before this semantic-config correction, the parent separately reported 16 actual-host compiled integration/runner/CLI tests passed in 35.29 seconds from tool session `99382`; that tool output was not retained as a file. Neither result is represented as an all-passing hermetic batch.

The Sol R2 plan review marked SHA
`6b2fe53800cf889e937f5bf504009f9dcb077cc2be0f42ae0f0ab471d2ed4182` READY.
The current plan file SHA is recorded in the R4 freeze. Subsequent parent
clarifications cover the two atomic-admission race cases and bind the complete
semantic SessionConfig; implementation and tests follow both requirements.

No live desktop run, profile opt-in, deployment, or new binary build occurred.
The runner records PNG-load, PixelDecoder, and total sample timing values in
the private fixture, but those are not real desktop performance measurements.
Existing preserved-frame replay evidence in the handoff measured strict decode
at 54.54 ms median / 60.65 ms p95 and PNG loading at 0.64 ms median. Real
owner-IPC, Shell capture, transfer, and end-to-end desktop cost remain
unmeasured; no benchmark or Rust implementation was added.

The earlier evidence-scoped read-only lease question is resolved by the
single-owner IPC design: R4 uses the existing daemon and canonical lease and
provides no alternate live lease. No live diagnostic run is authorized. The
seven frozen source hashes and verification record are in
`gnome-telemetry-region-r4-owner-ipc-freeze.json`.

One earlier parent-focused run failed closed during the first mutated-response
case: the existing daemon's producer IPC returned `DriverError: telemetry owner
protocol deadline expired` in `region_capture`, just over one second after owner
entry, before Shell capture and without publishing a PNG. Its actual owner
response and client/owner receipts are retained in the executor-review
artifacts. The old test fixture then assumed a successful sample, raised a
`KeyError`, and missed the expected compositor event, so that run did not
complete the intended mutation assertion. The fixture now records `ok`, sample
presence, and any owner failure from the real dispatch; it mutates only a real
successful sample and explicitly fails with the observed dispatch if the owner
refuses. An intermediate instrumented run completed the cases but failed at
teardown because the late-response client had already disconnected; the fixture
now records that expected transport error and does not retry a write on that
socket. The single fresh targeted rerun passed in 33.56 seconds. The earlier
owner deadline refusal remains retained and unresolved; the passing rerun does
not erase it or establish live timing reliability, and no deadline was widened.
