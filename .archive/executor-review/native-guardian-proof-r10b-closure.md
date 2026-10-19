# Native Guardian generation proof R10b closure

R10b is a proof-only test correction in `/home/dev/.cache/crowley/worktrees/native-guardian-proof-r10b-20261019`. The R10 production files and the six readonly companion files are unchanged. The only changed file is `tests/test_session_native.py`; the candidate hashes are recorded in `native-guardian-proof-r10b-freeze.json`.

The former R10 test created a bare NATIVE capture without a native owner and, in the PAUSED case, waited for owner deletion before the capture reached the Guardian admission boundary. That could only prove an outer capability refusal. R10b now creates the owner through the public configured paths: `native_construction_control_preflight` for PAUSED and public `native_construction_prepare` followed by `native_construction_bootstrap` for NATIVE. Each case then calls the real configured compiled producer through the real X11 backend and private Shell compositor.

The four focused case IDs and result are:

- `paused-revoke-first`: pass
- `paused-admission-first`: pass
- `native-revoke-first`: pass
- `native-admission-first`: pass

The combined command was:

```text
pytest -q tests/test_session_native.py::test_compiled_private_owner_guardian_generation_revoke_orders --maxfail=1
```

It produced `4 passed in 5.71s`. The complete log is private at `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-guardian-proof-r10b-20261019/focused-r10b-four-final2.log` with SHA-256 `b23184cf6c564260cbfd8c0be820afb962971188546a1c43e54d93cdc4f7c4ff`.

Each race installs a thin forwarding wrapper on the actual `Guardian.observer_dispatch_admission`. The wrapper pauses after the daemon has acquired the controller and native-construction locks, records the real owner and construction epoch, and forwards into the original Guardian method. In the revoke-first cases, a second thread calls the real Guardian revoke while the forwarding barrier is held. The test observes Guardian generation advancement, verifies the construction lock is still held and the owner/epoch remain unchanged, and then releases into production admission. The immutable capability reaches the final Guardian-generation check and returns exactly `native region capture Guardian generation is stale`; no producer process, Shell call, observer registration, or output is published. The capture epoch remains the pre-revoke snapshot because no producer was admitted.

In the admission-first cases, the forwarding barrier is released into the real Guardian method. The compiled child registers, reaches the private Shell `ScreenshotArea` gate, and is present in the real Guardian observer registry. A real revoke then increments the capture epoch and reaps the child while it remains blocked. The compositor gate is not released after revocation, so no late area receipt is written; the capture fails with a revocation error and all backend/Guardian process registries are empty. The captured epoch is the pre-revoke value.

Scoped checks passed: Ruff format check, Ruff lint check, Python compileall, and `git diff --check`. The static log is private at `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-guardian-proof-r10b-20261019/static-r10b-final2.log` with SHA-256 `f71e6944cf9d785a46e42d702dabec79b8a331c75d0c955c313ccbdab6ceca7d`.

The focused fixtures used the authentic private Codex `0.162.1` binary, private `XDG_RUNTIME_DIR`, a private no-autostart D-Bus session, the genuine X11 backend, real compiled producer, real Guardian, real owner protocol, and real decoder. Evidence logs are mode `0600` under a mode `0700` private directory. No GUI input, live capture, service/config mutation, deployment, or Git mutation was performed. No broad suite was rerun; the accepted R10 `367 passed` result remains preserved separately. Parent verification and external review remain pending, so this report is a candidate freeze rather than a promotion claim.
