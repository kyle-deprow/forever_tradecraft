# Process matching cost R1 closure

The isolated worktree `/home/dev/.cache/crowley/worktrees/process-matching-cost-20261018` is based at `fe439243afdb7e2fd0ba8244819eac2fa9086761`. The implementation moves the existing exact cmdline basename/cardinality refusal ahead of `stat`, `status`, `/proc/<pid>/exe`, and configured-prefix reads. A process with exactly one configured basename continues through the unchanged checks and order, including start time, Linux `Name`, `wine-preloader`, and `WINEPREFIX`; `_matching_game_pids` and resolver call structure are unchanged.

The exact two-file hashes are:

- `src/crowley/session/driver.py`: before `ca0ca123d0fa09d8361c8632d9cc1c2c501d87adf99cb3cc268688dd4291a166`, after `965c4b3f20842f3e065469077358b6886d8260d24aab5fe7ed3933beca0d13f6`.
- `tests/test_session_driver_actions.py`: before `6d5b21dd11a3af45d20f494ce7950ea18f676e40f47c5d01aae8a30e655f2413`, after `7bf8538bdb804cd4e5d275d7c311b86171ce7ec9f650999371c6169abca956a6`.

The focused acceptance command passed:

`uv run pytest -q tests/test_session_driver_actions.py -k 'process_executable or matching_game_pids or native_resolver'` → `9 passed, 24 deselected in 1.62s`.

The full action suite passed:

`uv run pytest -q tests/test_session_driver_actions.py` → `33 passed in 11.20s`.

Scoped Ruff passed, the format check reported `2 files already formatted`, compileall passed through `uv run python -m compileall -q ...`, and `git diff --check` passed. The literal plan command `python -m compileall` was unavailable because this environment has no `python` executable; the repository `uv` interpreter ran the same check successfully.

The regressions use real short-lived Linux `/proc` fixtures. They cover zero-match and duplicate-basename early rejection with only `cmdline` read, valid-candidate read order, wrong `Name`/loader/prefix, malformed `stat`, candidate exit after `cmdline`, synchronized nonmatch↔candidate `exec` transitions, multiple valid candidates, and production resolver binding to a real matched PID. Fixtures use unique `CrowleyTest.exe`, temporary copied `/usr/bin/python3` images named `wine-preloader`, temporary prefixes, and no matcher or resolver replacement. All owned children were reaped and no fixture processes remain.

This is offline source/test evidence only. No live game, capture, input, restart, deployment, commit, or Rust qualification action was performed. The machine-readable record is [process-matching-cost-r1-freeze.json](/home/dev/repos/pegasus/.archive/executor-review/process-matching-cost-r1-freeze.json).
