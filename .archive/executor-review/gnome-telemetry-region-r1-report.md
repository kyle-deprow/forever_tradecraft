# GNOME telemetry-region offline implementation freeze

This is the completed offline implementation for accepted plan
`ac1c8cbec750844c71c3eaade3f349ffc638d6d427e01c88d602d019e4a00b95`. The
parent pre-edit receipt is `gnome-telemetry-region-parent-before.json`; exact
owned-file hashes are in `gnome-telemetry-region-r1-owned-sha256.txt` and the
machine-readable freeze is `gnome-telemetry-region-r1-freeze.json`.

## Implemented boundary

`SessionConfig` and `DriverProfile` accept a default-off absolute executable
and lowercase SHA-256 pair. Validation rejects missing, relative, malformed,
unowned, writable, or digest-mismatched files.

The production X11 path opens that executable by verified path, copies its
exact bytes into an immutable sealed memfd, and starts only the pinned private
producer. The nonce-bound admission protocol validates the live child
PID/start/executable FD/PPID/PGID/primary-owner/non-remote proof and typed
rectangle before acknowledging the child. The producer then calls typed
`ScreenshotArea` with the profile-derived global rectangle, flash disabled,
and an exact 256x256 PNG. Parent epoch/deadline/identity/lock checks,
completion digest/byte checks, secure staging, retirement, and cleanup remain
enforced.

Native bootstrap, native frame capture, native calibration/status, and the
native motion route select this producer only for explicit profile opt-in.
Model/full-scene capture and ordinary input calibration retain the stock
desktop path. No live binding was performed.

The private GNOME 41.0 build is source-controlled by the exact patch and
reproducible script in `tools/gnome-telemetry-region`. The build verifies the
upstream archive, Debian archive, and patch hashes; uses `-Dx11=disabled` in
the recorded Debian container; and records full source hashes, compiler logs,
version/help, file/ldd output, and the binary hash. The resulting binary is
`248a445fbe4c382f71db37b480bb671759368595ca1cf91d6e78c4dc0e3c3bab`.

## Requirement-to-check mapping

| Requirement | Evidence |
|---|---|
| Typed `ScreenshotArea`, exact rectangle/size, no flash, X11 disabled | Patched GNOME source, private manifest, compiled binary, and offline parser/producer checks |
| Immutable executable/image ownership | Sealed executable test, production `X11Backend.capture_native_region` test, and sealed protocol fixture |
| Nonce-bound owner receipt and positive ACK before capture | Offline harness and production capture test validate owner fields, rectangle, output-path digest, ACK, and start/completion ordering |
| Exact PNG bytes and producer completion | Production capture test writes/decodes an exact 256x256 PNG and checks the receipt |
| Default-off and profile-pinned daemon routing | `test_native_region_profile_is_default_off_and_hash_pinned` and `test_daemon_native_region_route_is_opt_in_and_identity_bound` |
| Native protocol/decoder and motion admission | Existing native integration tests plus the focused real producer/decoder test; malformed native states remain rejected |
| Static/reproducibility checks | Offline self-test/self-check, Ruff check/format, explicit-file `py_compile`, and private build metadata |
| Framing/model/input safety | Model/full-scene and input calibration paths were not changed; no live capture, input, bus activation, service restart, or profile binding occurred |

## Verification

The complete affected batch ran once after implementation:

```text
env -u CROWLEY_TEST_DATABASE_URL PYTHONPATH=src uv run pytest -q \
  tests/test_session_capture.py tests/test_session_native.py \
  tests/test_session_motion_integration.py tests/test_session_preferences.py \
  tests/test_session_driver_actions.py --disable-warnings --maxfail=0
284 passed in 346.83s (0:05:46)
```

The source-controlled harness reported `self_test=true, self_check=true`.
Scoped Ruff check, Ruff format check, explicit-file `py_compile`, and manifest
JSON validation passed. The private binary `--version`, `--help`, `file`, and
`ldd` checks passed without activation. Global host-Codex version differences
and live-game qualification remain outside this offline freeze.

## Fence

The six baseline paths changed are:

- `deploy/crowley-session.example.toml`
- `src/crowley/session/config.py`
- `src/crowley/session/daemon.py`
- `src/crowley/session/driver.py`
- `tests/test_session_capture.py`
- `tests/test_session_native.py`

The three existing owned test paths that remained byte-identical are
`tests/test_session_driver_actions.py`, `tests/test_session_motion_integration.py`,
and `tests/test_session_preferences.py`. The five new tool paths are under
`tools/gnome-telemetry-region/`. The freeze records zero out-of-fence paths
relative to the parent's pre-edit receipt; review artifacts and private cache
outputs are explicitly excluded from that source comparison.
