# Process matching cost: authorized offline implementation

Root reviewed the proposed PLAN-process-matching-cost.md (SHA
6556e5255e247d0989a90dc4c8892a63c97147873876d42c3e82100760a90520).
This releases only its two-file offline implementation at fe43924. No live
comparison or restart is released until source reviews pass. Its invariants,
acceptance commands, manifest/comparison requirements and Rust boundary apply.

Own only src/crowley/session/driver.py and tests/test_session_driver_actions.py
in an isolated worktree. Move the existing exact cmdline basename/cardinality
rejection before unrelated proc I/O; matching candidates retain identical full
checks/order/results. Preserve four fresh scans and window-PID checks.

Clarifications to avoid expanding a small optimization:
- Noncandidate error precedence can be observed by a direct caller; explicitly
  accept the earlier exact-executable DriverError while keeping its identity
  refusal phase. No error text for actual matching candidates changes.
- Compare controlled exit/exec snapshots with baseline semantics. Do not promise
  stronger atomicity than baseline or add new reads/identity behavior to obtain
  it. Proc snapshots already span reads; retain fresh-call revalidation.
- Malformed-stat injection tests validate existing failures only, without adding
  new stat grammar or changing start-time parsing.
- Test helpers are harmless non-GUI subprocesses using a unique configured test
  executable name and temporary Wine prefix. They MUST NOT identify as WowB.exe
  or interfere with the real operator's matching set. Reap every owned child.
- Real proc fixtures may set their own comm/argv/loader/prefix. Read hooks record
  actual reads or synchronize child events; do not fake the matcher/resolver.

Run the proposed focused and full driver-action checks and scoped static checks.
Parent inspects the exact delta and repeats relevant checks; Sol and actual Opus
review before integration. Existing native core/limits/producer/config/public
schema/IPC/addon files are read-only. No Rust code, caching, fallback, deadline
change, game input, deployment, main-source edit, commit/reset/stash is allowed.
Freeze exact two-file hashes and actual output in new executor-review records.
