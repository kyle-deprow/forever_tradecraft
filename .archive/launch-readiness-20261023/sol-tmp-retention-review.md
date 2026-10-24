# Sol pytest temporary-retention review — READY

Scope reviewed: frozen `pyproject.toml`, the suite-stability plan, the temporary-
retention policy note, and the installed pytest 9.1.1 implementation at
`.venv/lib/python3.12/site-packages/_pytest/tmpdir.py`. No pytest command was run
and no temporary directory, evidence, user data or unrelated resource was
deleted.

Frozen `pyproject.toml` SHA-256 before and after review:

`b160b637640dfef4bccd5939d922461159b929e3d7e9eda3f4b85d09e47f7921`

The one-file manifest agrees with that hash. Device, inode, size, mtime, ctime
and mode also remained unchanged across the read.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

## Review conclusions

- The only new retention setting is
  `tmp_path_retention_policy = "failed"`. Existing `testpaths`, bounded
  `-n 16`, `--dist worksteal`, and all-case collection remain unchanged. No
  retention-count override is present.
- Installed pytest is version 9.1.1. Its `TempPathFactory.from_config` reads the
  count independently from the policy, accepts only `all`, `failed` or `none`,
  and the registered default count remains `3`. Policy `failed` does not force
  the count to zero.
- The function-scoped `tmp_path` fixture creates a new path, yields it, and
  performs best-effort cleanup only in its post-yield teardown. Pytest fixture
  dependency teardown therefore finishes before the dependency path is removed.
  The exact installed condition is a passed call report
  (`result_dict.get("call", True)`); a failed call retains its path. This is the
  precise installed semantics and does not overclaim retention for every
  possible setup/teardown failure shape.
- At session finish, pytest removes the newly created basetemp only when the
  overall exit status is successful, policy is `failed`, and the user did not
  supply `--basetemp`. A failed session retains that basetemp. The configuration
  adds no project cleanup hook and does not name, traverse or manually delete
  existing beta data, raw evidence, SavedVariables, backups or unrelated paths.
- No HOME, TMPDIR, environment, stdlib, subprocess, production-source, marker,
  timeout, fallback or test-selection behavior was changed. The setting reduces
  successful test-generated `tmp_path` accumulation; it does not skip proofs.

Status: **READY** for the frozen temporary-retention configuration slice.
