# Identity latency barrier schema closure

The broad profiler work is frozen. This is a narrowed repair of the sole Sol
final finding, not another profiler rewrite. Existing Stage 1 contracts and
limits remain fixed; prior final candidate hashes are the starting point.

Own only `tools/gnome-telemetry-region/identity_latency_sidecar.py` and
`tests/test_session_native.py` in the schema worktree. Driver/daemon and prior
worktrees are read-only. No live actions, deployment, commits, or config changes.

Require each barrier dictionary to contain exactly `barrier`,
`start_monotonic_ns`, `end_monotonic_ns`, `duration_ns`, `outcome` before indexing
it. Unknown or missing fields must raise IdentityLatencyError, and the public
report reader must return artifact_invalid without propagating raw fields or
KeyError. Existing valid artifacts and report values remain unchanged.

Test real persisted artifacts through read_response_profile/build_report for
unknown path/error fields and each missing required field, with otherwise valid
bindings. Check original valid complete and partial artifacts still work.

Run `uv run pytest -q tests/test_session_native.py -k identity_latency --maxfail=1`,
scoped Ruff/format and git diff --check. Parent repeats focused checks and reviews
the exact delta, then Sol closes this finding and actual Opus reviews final
closure. Full prior 297 checks remain separate evidence for unchanged core code.
New frozen hashes and reports supersede only the sidecar/test entries; previous
freezes stay immutable. No live claim or Rust decision is made.
