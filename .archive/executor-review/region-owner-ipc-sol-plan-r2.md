# Sol plan review: region owner IPC closure R2

Reviewed plan SHA-256: `6b2fe53800cf889e937f5bf504009f9dcb077cc2be0f42ae0f0ab471d2ed4182`.

R2 closes the R1 findings without widening the task. The diagnostic remains on the existing owning daemon and canonical desktop lease. The added driver scope is limited to region producer admission/cancellation and retains the real producer, decoder, identity checks, original parent timestamp, and eight fixed samples.

Source hashes inspected:

- `tools/gnome-telemetry-region/offline_harness.py`: `74e0f5012bc1c99606bf2866350be496ff4d0d168a177e7683d00e2e35a2c9f9`
- `src/crowley/session/daemon.py`: `23aef76fecbc82178bd25e51e2a39901b091eed26705361da35d7ad27cc0cf13`
- `src/crowley/session/cli.py`: `b861c28bd0ae821306c8f01aa65f6a25924aff8893c940c7562f5a5a486047f1`
- `src/crowley/session/driver.py`: `3d37abf8df6e0594e1d9205dba185313c8f92894b87956eda5389eaf6901af05`
- `src/crowley/session/guardian.py`: `e73128de1e6fdf38beda8256b11f77d66b2b666eb8b1499018c70781217a2efa`
- `tests/test_session_native.py`: `e5d9fe51619d4339aed5f2d8d4098073952a672af8e89fc8ae7a108e6ed8e70a`
- `tests/test_session_cli_motion.py`: `e21870f80c448da7fe145a4bc5d82ce6e01f322e14727efdea8193291edc53fb`
- `tests/test_session_capture.py`: `49f48b601a2e6600b71d6a994f23f038140cb18ceca7ce0f02355215064289da`

R1 closure checked:

- `.archive/PLAN-region-owner-ipc-closure.md:56` now requires registration in the existing guardian observer ledger before exec-gate release, continued registration through termination/reaping, actual PAUSED/generation admission, capture-epoch cancellation, and a consistent controller-to-guardian/backend lock order. This supplies the ownership and cancellation mechanism absent in R1. It is compatible with `InputGuardian.observer_dispatch_admission()` at `src/crowley/session/guardian.py:781` and with pause/stop calling `guardian.revoke()` at `src/crowley/session/controller.py:1911` and `src/crowley/session/controller.py:2402`.
- `.archive/PLAN-region-owner-ipc-closure.md:112` defines bounded request, response, and PNG sizes, bounded newline framing before parsing, duplicate/non-finite rejection in both directions, and socket-level regressions while preserving sequential request semantics.
- `.archive/PLAN-region-owner-ipc-closure.md:76` now distinguishes published evidence that can be retained from pre-publication failure metadata where no PNG or `TelemetryRegionReceipt` exists.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
