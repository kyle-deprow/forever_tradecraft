# Sol plan review: region owner IPC closure R1

Reviewed plan SHA-256: `ea17e461f4de493f7f25c58dfa5b0c104b64ab0714fc2a110d805d520cd212d6`.

The replacement architecture is correct: the paused diagnostic must ask the existing daemon to use its already-owned `DesktopDriver`, canonical desktop lease, configured native producer, and capture fence. The original parent monotonic timestamp can cross the same-host Unix socket without restamping, and the proposed one-second absolute deadline can flow through the existing identity and native-region APIs. The following gaps need closure before implementation.

Source hashes inspected:

- `tools/gnome-telemetry-region/offline_harness.py`: `74e0f5012bc1c99606bf2866350be496ff4d0d168a177e7683d00e2e35a2c9f9`
- `src/crowley/session/daemon.py`: `23aef76fecbc82178bd25e51e2a39901b091eed26705361da35d7ad27cc0cf13`
- `src/crowley/session/cli.py`: `b861c28bd0ae821306c8f01aa65f6a25924aff8893c940c7562f5a5a486047f1`
- `src/crowley/session/driver.py`: `3d37abf8df6e0594e1d9205dba185313c8f92894b87956eda5389eaf6901af05`
- `tests/test_session_native.py`: `e5d9fe51619d4339aed5f2d8d4098073952a672af8e89fc8ae7a108e6ed8e70a`
- `tests/test_session_cli_motion.py`: `e21870f80c448da7fe145a4bc5d82ce6e01f322e14727efdea8193291edc53fb`
- `tests/test_session_capture.py`: `49f48b601a2e6600b71d6a994f23f038140cb18ceca7ce0f02355215064289da`

## Must-Fix

1. `.archive/PLAN-region-owner-ipc-closure.md:45` requires pause/stop or a generation change to revoke a sample concurrently, but the allowed implementation fence cannot currently provide that guarantee. The native producer is placed only in `X11Backend._active_processes` and `_active_process_groups` at `src/crowley/session/driver.py:2833`; it is not registered in the guardian's read-only observer ledger. `InputGuardian.revoke()` invokes the backend release callback only when input is held or a guardian process/observer group is active at `src/crowley/session/guardian.py:1906`. A stop of an already-paused, unarmed controller can therefore change controller state while leaving the producer alive until its deadline. The daemon also cannot repeat the PAUSED/generation predicate at the actual exec gate, because that gate is released internally at `src/crowley/session/driver.py:2841`. The scope at `.archive/PLAN-region-owner-ipc-closure.md:23` limits `driver.py` to the prior retirement fix, so it excludes the change needed to meet the stated cancellation/admission contract. Correct the plan by allowing one narrow driver integration that registers this read-only region producer with the existing guardian observer ownership fence before releasing its exec gate, unregisters it only after termination/reaping, and makes pause/stop revoke the backend capture epoch. Require a regression that blocks the producer at the gate and proves a concurrent stop both remains responsive and prevents PNG publication, while the canonical lease and watchdog stay owned by the daemon.

## Should-Fix

1. `.archive/PLAN-region-owner-ipc-closure.md:32` promises an exact, finite, bounded request and `.archive/PLAN-region-owner-ipc-closure.md:90` promises a bounded response before JSON parsing, but the existing transport reads arbitrary-length lines and calls permissive `json.loads` at `src/crowley/session/cli.py:416`, while the client reads an arbitrary-length response before parsing at `src/crowley/session/cli.py:513`. The plan names malformed/oversized response tests but omits the symmetric request framing and duplicate/non-finite JSON cases. Define fixed encoded request and response limits, require each frame to be newline terminated within its bound, and use duplicate-key and non-finite rejection on both sides before dispatch. Add socket-level tests for an over-limit unterminated request, duplicate request fields, `NaN`, an over-limit response, duplicate response fields, and trailing bytes after a response frame. Keep the constants sized for the exact 256x256 PNG/base64 envelope and preserve the server's existing ability to process sequential bounded request frames rather than introducing a new streaming protocol.

2. `.archive/PLAN-region-owner-ipc-closure.md:64` requires failed PNG and receipt preservation, but `X11Backend.capture_native_region()` creates `last_region_receipt` only after a fully successful publication at `src/crowley/session/driver.py:3001` and retires the attempt directory unconditionally at `src/crowley/session/driver.py:3055`. That requirement cannot be met for failures before publication under the plan's retirement-only driver scope. Narrow the contract: preserve the owner PNG and receipt when capture publication succeeded and a later state, decode, response, or transport check fails; for pre-publication producer failures, retain the exact bounded error, failure phase, and truthful cleanup state without claiming a PNG or receipt exists. Reflect that distinction in the preservation tests at `.archive/PLAN-region-owner-ipc-closure.md:110`. Expanding the backend into a new failed-attempt archive is unnecessary for this closure.

## Nits

None.

STATUS: NEEDS WORK
