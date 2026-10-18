# Identity latency final closure

The isolated final worktree `/home/dev/.cache/crowley/worktrees/identity-latency-final-20261017` is based on `f213e1f`. The final sidecar closure compares the complete descriptor tuple (device, inode, mode, link count, size, mtime, and ctime) at open, after the full read, and at the final path check. A real same-size mutation of the config bytes at EOF is detected during the read and refuses before the first IPC/sample request.

Checks completed in the final worktree:

- `uv run pytest -q tests/test_session_native.py -k identity_latency --maxfail=1`: 9 passed, 138 deselected.
- Actual compiled owner composition: 1 passed in 57.59s.
- Ruff, format, compileall, and `git diff --check`: passed.
- The immutable R3 worktree had already passed the full native/regression/performance suite: 297 passed in 246.58s.

See `identity-latency-final-freeze.json` for exact file hashes, immutable references, commands, and limitations.
