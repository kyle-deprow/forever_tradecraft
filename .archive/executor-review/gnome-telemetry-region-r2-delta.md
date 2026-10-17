# GNOME telemetry region R2 delta

R2 preserves the byte-for-byte R1 source tree under `gnome-telemetry-region-r1-source/` and applies the reviewed correction set. The private R2 ELF is `b69e949197d64551ec1ade481db541137310d5dda0eeb9ceb5431db1ace1c3cb` and was built from the pinned GNOME 41.0 archives, Debian series, patch `0a135ab39ca57e168602cc2ea0a1e403ae69268f6593c1ad41e8d0972c231b9e`, and `-Dx11=disabled` in the pinned container. The successful recipe used only the new R2 cache mount; the recorded Docker command retained network bridge access for apt dependency retrieval.

## Production boundary

- `driver.py` keeps the capture epoch fence through lock admission, spawn/registration, owner-record waits, live kernel proof, ACK, start/completion waits, and final publication. It verifies `/proc/PID/fd/exec_fd` and `/proc/PID/exe` device/inode and SHA-256 against the sealed memfd, PPID/PGID/process-group membership, strict bool/int protocol types, and capture-start interval.
- The private producer uses strict typed option parsing and the ordinary `ScreenshotArea` path with `flash=false`; stock full-desktop/model/input paths remain unchanged and the capability is default-off.
- `daemon.py` routes actual `SessionDaemon -> NativeMotionProvider -> capture_status` through the opt-in producer while preserving a fixture-safe stock fallback when a minimal non-production daemon object has no profile. The fallback only prevents a test fixture from dereferencing an absent profile; production config always supplies one.

## Regression mapping

| Requirement | Evidence |
| --- | --- |
| sealed executable and exact kernel owner proof | `test_session_capture.py::test_capture_native_region_uses_sealed_producer_and_exact_png`; wrong nonce/digest/path/PGID/bool protocol/EOF parametrized cases |
| revocation epoch before ACK leaves no output or registry entries | `test_session_capture.py::test_capture_native_region_revoke_before_owner_ack_publishes_nothing` |
| compiled parser rejects missing, duplicate, conflicting, wrong-size, relative, and malformed option forms | R2 `offline_harness.py --self-test --self-check` against rebuilt ELF |
| real producer branch and D-Bus `ScreenshotArea`/flash=false | same harness private `dbus-run-session` + Xvfb/GJS compositor fixture; exact decoded 256x256 pixels, plus rebuilt-C wrong-ACK and owner-EOF refusal checks |
| default-off config and trusted opt-in path/hash | `test_session_native.py` config/profile cases |
| real daemon/provider/decoder binding and model/full-scene stock exclusion | `test_session_native.py::test_real_session_daemon_native_provider_route_and_stock_model_capture` |
| broad motion/runtime/evidence regression coverage | final recorded batch log below |

## Verification outcome

- Targeted post-fix checks: 13 passed in 2.04s, including native capture, revocation, configuration, and the real daemon/provider/decoder route.
- Complete affected batch: 301 passed, 13 failed, exit 1, in `.archive/executor-review/gnome-telemetry-region-r2-fix.log`. The 13 failures start with the host's global Codex `0.163.0` versus the pinned `0.162.1` model startup boundary and then cascade through the runner's desktop lease; no native-region assertion failed. The prior complete batch is retained in `.archive/executor-review/gnome-telemetry-region-r2.log` (300 passed, 14 failed) and records the profile-fixture defect fixed before the final run.
- Explicit scoped Ruff check, Ruff format check, Python compilation, and `git diff --check` passed. Build and harness evidence is in `gnome-telemetry-region-r2-build-receipt.json`.
