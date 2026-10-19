# Native helper proof closure — final scoped handoff

Status: **focused corrected causal proofs pass; parent combined helper/runtime verification and independent review pending**.

Worktree: `/home/dev/.cache/crowley/worktrees/native-helper-proof-closure-20261019`, base `59046b1`.

Owned final bytes:

- `tools/native_calibration_operator.py`: `47afeda449fb9eab695c33c239c1909ea45e2c05d5d16df36b95dd63df3d5cce`
- `tests/test_native_calibration_operator.py`: `a38bd17d8d55386697f3de5ecc6b3588cd31ffaca2eb6f9d5bf1535d0ec259b6`

The helper change is the narrow phase-deadline correction: `_record_operation_deadline` retains the minimum observed value for operation, constructor, provider, finalize-hook, and finalize deadlines. The test covers every deadline key, a lower subsequent report, and constructor-bound refusal. The native seven-file inputs and all other native/helper dependencies stayed read-only.

The final test fixture corrections closed three real causality defects found during execution:

1. Reload updates keep compositor payload files base64 encoded; only the producer’s requested output path receives raw PNG bytes. This fixed recovery-complete producer failures after a real Restore/reload boundary.
2. The actual ordinary Lua VM remains unarmed until the helper dispatches `/agent defer`. The test now asserts the live action changes the marker to `armed`, preserves the ordinary lifecycle and boot, arms `NativeConstructionFence`, and does not reload. Static construction images use a separate seed VM.
3. Construct, Hold, update, Resume, and Finalize payloads are rewritten from the live reloaded VM and checked against its actual rendered PNG. The first measurement reload expects a real deferred VM; recovery reloads expect ordinary. No RNG or production deadline was changed to mask token differences.

Final corrected focused outputs, all from the final test hash and mode `0600`:

- `success-causal-r3.log` — SHA256 `e9afa77eb2edbf7cfe91067809e231c0efc0fa1fa6175e8f36a865c2cb5102ed`; `success` passed in 147.16 s, including real 100-update cadence and public pause/fresh recovery.
- `control-preflight-causal-r2.log` — SHA256 `787cc0c1c562283132685188973eb67d2131a2686586166cb42beaff408c018c`; control-preflight passed in 27.73 s.
- `measurement-failure-causal-r3.log` — SHA256 `1fda8e04a1975e3d9ee591925e617a6e3c00fe5c89fd618c00f8594673adc04f`; measurement-failure recovery passed in 42.51 s.

A prior eight-mode run (`full-helper-final-r3.log`, SHA256 `9520186ae2f1f842d8b704ba31f03ca46e1479b722ec7b773a91cbeb70a6aed0`) passed 8 cases on the superseded test hash `6abbea8664ef6a3edc17e0884b02e45470a3508e31abadf32b592a92c265ca07`; it is retained as historical evidence and is not claimed for final bytes. The final full module command was intentionally stopped after 61 passed when the parent combined final suite began; its log is `full-helper-77-final-r2.log`, SHA256 `2351351de58b3a5ecb9d863adcdfeeed6e13052484f6fc52dbf3d9a4aeb2c452`. The parent combined run is the authoritative final verification for recovery modes and the remaining helper tests.

Final static checks passed on the final bytes: Ruff format check (`2 files already formatted`), Ruff check (`All checks passed!`), Python `compileall`, and `git diff --check`. The evidence directory is `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-helper-proof-closure-20261019` with mode `0700`; retained logs are mode `0600`.

No GUI, live input, addon, service, deployment, native promotion, configuration, or Git mutation was performed. Parent must independently verify the final two hashes in the combined helper/runtime suite before acceptance.
