# Identity latency barrier schema closure

The isolated worktree `/home/dev/.cache/crowley/worktrees/identity-latency-schema-20261018` is based at `3f43d8f40aa17035409a87c4718e1f34a888ff65`. It applies the single Sol final finding from `identity-latency-sol-final.md`: every persisted barrier object is now required to have exactly `barrier`, `start_monotonic_ns`, `end_monotonic_ns`, `duration_ns`, and `outcome` before any field is indexed. `IdentityLatencyError` is raised for unknown or missing fields, and `read_response_profile`/`build_report` classify those persisted artifacts as `artifact_invalid` without exposing raw `path` or `error` values.

The exact candidate SHA-256 values are:

- `src/crowley/session/driver.py`: `ca0ca123d0fa09d8361c8632d9cc1c2c501d87adf99cb3cc268688dd4291a166`
- `src/crowley/session/daemon.py`: `972c74057003bb13931cf257fffeaf6b77a802689814c4aa7c35b46c01bb23ae`
- `tests/test_session_native.py`: `f787057139cfaeacad1756ac1799c8fbfbb3f2e06fba31456ee810caf734b9ae`
- `tools/gnome-telemetry-region/identity_latency_sidecar.py`: `e14233b0309a3b872dee0e7ff1eef82ace96865a3c0b4065455afbd56602056e`

The read-only baseline remains pinned at these SHA-256 values:

- `docs/RUNTIME_PERFORMANCE.md`: `54237c344ef0faa3392cca6fe82b75f1f986bbf697c81d3f34493b2f00e1caca`
- `src/crowley/session/calibration.py`: `e87e844bc0428f76f2d2c8053e58017651e5ea7e285164bac56ba33bbb39630c`
- `tests/test_session_native_regressions.py`: `07d0dbcc66c78554d3b378208e6e1b7be68bd64617a1ac898f3a5f05b7245945`
- `tests/test_session_performance.py`: `c998aa4a9ff67ba67ddeab05a0e5a0cfa5273a296909e0b07cb79a3d06dd313a`
- `tools/gnome-telemetry-region/offline_harness.py`: `f682d85636b0073a8fd7e8330a6ae06ba7542d2cb9b7ccc74a1304ea856d7716`
- `tools/session_performance.py`: `c46cae849058005e9b7387ef95c34f40f376afb5477739efaf6f40f6a36ebd8c`

The scoped checks passed:

- `uv run pytest -q tests/test_session_native.py -k identity_latency --maxfail=1`: `10 passed, 138 deselected in 1.24s`.
- Scoped Ruff check: `All checks passed!`.
- Scoped Ruff format check: `4 files already formatted`.
- `git diff --check`: passed.

The new regression writes real persisted complete and partial artifacts, confirms both remain accepted, then tests arbitrary `path` and `error` barrier fields plus each of the five missing required fields through `validate_artifact`, `read_response_profile`, and `build_report`. No live action, deployment, restart, commit, or Rust decision was made. The complete machine-readable record is [identity-latency-schema-freeze.json](/home/dev/repos/pegasus/.archive/executor-review/identity-latency-schema-freeze.json).
