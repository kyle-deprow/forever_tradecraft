# Pytest temporary-path retention policy

Date: 2026-10-24

Owned change: `pyproject.toml` only. The standard pytest configuration now sets
`tmp_path_retention_policy = "failed"`; `tmp_path_retention_count` is not set,
so pytest's existing default retention count remains unchanged (`3`). The
existing 16-worker `worksteal` addopts and native test collection are unchanged.

Authoritative installed implementation inspected:

`/home/dev/repos/pegasus/.venv/lib/python3.12/site-packages/_pytest/tmpdir.py`
(pytest 9.1.1).

Verified semantics from that source:

- `TempPathFactory.from_config` reads the configured count and policy, retaining
  the count independently and accepting only `all`, `failed`, or `none`.
- The function-scoped `tmp_path` fixture yields the newly created path, then
  removes only that fixture-owned path after teardown when policy is `failed`
  and the test call report passed (`result_dict["call"]` is true). A failed
  call retains the path for evidence; cleanup is best-effort for leaked files.
- At session finish, a successful run with policy `failed` removes the newly
  created basetemp when the user did not explicitly provide `--basetemp`; a
  failed run retains it. Existing paths are never manually traversed or
  deleted by this change.
- This is pytest's ordinary fixture cleanup, not a project hook: no conftest,
  HOME/TMPDIR, subprocess, marker, worker, or production behavior changes.

Verification:

- `uv run python` TOML parse reports:
  `testpaths=["tests"]`, `addopts=["-n", "16", "--dist", "worksteal"]`,
  and `tmp_path_retention_policy="failed"`; no retention count override.
- The installed pytest source and exact cleanup semantics above were inspected
  with `uv run python`; no pytest suite was duplicated for this configuration-
  only change.
- `git diff --check -- pyproject.toml` passed.
