# Sol plan closure review: GNOME telemetry region

This review was limited to closure of the prior five Must-Fix and two Should-Fix findings. I reviewed the revised plan only and did not inspect source, run tests, build the private binary, capture pixels, or query D-Bus.

The revised plan closes the prior findings:

- It removes the compression-only binary, comparison branch, and extra full-screen captures, leaving one source-controlled GNOME 41.0 no-flash `ScreenshotArea` implementation.
- Its routing matrix selects region capture for native bootstrap, `_capture_native_frame_with_capture` and native calibration/named-addon observations, and `capture_status` with all of its callers. It keeps model artifacts, route/viewport captures, input calibration, and other full-scene/model consumers on stock full-desktop capture.
- The private executable is no longer admitted through generic PATH resolution or a writable retained inode. The plan requires a verified immutable sealed-memory image, the existing positive admission/process-group lifecycle, exact typed argv, a per-request nonce and capability channel, live PID/process/executable/PPID/PGID verification, a primary non-remote GApplication proof, and a positive parent ACK before `ScreenshotArea` can run. This is feasible without the former owner-monitor quiet delay or an impossible post-exit `/proc` check.
- `capture_started` binds the output-path digest before an image exists, while `capture_complete` binds the resulting image digest and byte count. The original parent capture-start remains the decoder/admission timestamp; the child Shell-call timestamp is additional in-request evidence and cannot restamp freshness.
- The coordinate formula remains the sole candidate and is accepted only by the first live exact-rectangle, exact-256x256, strict-schema-3 decode. Scaling guesses, tolerance, alternate offsets, and fallback crops remain forbidden.
- The live gate now uses the configured `DesktopDriver` region operation and `PixelDecoder` while paused, with no invented daemon command or calibration phase. It predeclares at most eight one-second targets, measures the entire identity-to-decode path, records every attempt, requires sub-second completion and 0.75..1.25-second actual intervals, and stops on `NO_CHANGE` or any failure. It requires one boot and increasing sequences without claiming contiguous or unskipped normal publications; the formal runner remains the later 100-update proof.
- The implementation fence names the production, example-config, test, tool, review, cache, and evidence paths, with `process_admission.py` conditional only on where retained-FD execution is implemented. The focused tests require the compiled parser, owned child/PGID/nonce/ACK ordering, real decoder/admission/provider bindings, cleanup failures, and stock model/full-screen exclusion rather than gate booleans.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
