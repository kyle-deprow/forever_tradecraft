# Launch readiness execution

User authorization (2026-10-23): refactor default tests below three minutes using
parallelization and deletion of less important tests/functions, then continue the
remaining launch preparation through Luna implementation / Sol review.

## Order and acceptance

1. Suite refactor: reuse justified repairs from suite-green without merging its
   global HOME/Popen patches. Default `uv run pytest` must pass in <180 seconds,
   measured externally after dependency installation. Use bounded pytest-xdist
   parallelism. Remove redundant/low-value tests and helpers with a recorded
   coverage rationale. Do not achieve the target merely by deselecting existing
   native tests. Keep meaningful data-integrity, financial execution, rate-limit,
   process cleanup, takeover and input-fencing checks. Avoid production behavior
   changes solely for speed. No game or live service interaction.
2. Central launch target and reproducible generation with drift checks. Preserve
   strict version/identity rejection, itemKey identity, separate houses and all
   beta history. Regenerate beta outputs without pretending launch facts are known.
3. Station/tool-aware crafting, then reassess two-profession strategy evidence
   against retained beta data and document limits for the fresh launch economy.
4. Guarded mailbox/executor orchestration between sweeps, dry-run by default.
5. Update active handoff and launch checklist. Live collection qualification,
   route validation and armed tests await launch and user authorization.

Each implementation phase receives a bounded prompt, read-only Sol review,
concrete Luna fix rounds if required, and parent verification. No commits,
pushes, worktree removal, SavedVariables edits, secrets, destructive data actions,
or deployment changes. Keep current evidence archives intact.

## Phase 1 ownership

Luna may edit `tests/**/*.py`, `pyproject.toml`, `uv.lock`, README.md Tests section,
`docs/HANDOFF.md` test status/commands only, and may create
`docs/TESTING.md` and `.archive/test-suite-refactor-20261023/` artifacts.
The existing suite-green worktree is read-only reference. No production source,
addon, native source, deploy, other docs, skills, or other archives edits.
Read CLAUDE.md, docs/HANDOFF.md, archived Claude handoff, and this plan first.
Read client-contracts skill if touching Lua harness or serialization tests.

## Phase 1 verification

All pytest invocations hold the machine lock:
`flock /home/dev/.cache/r-pg.lock ...` (one suite coordinator; xdist children are
the authorized parallelization inside that invocation). Set CARGO to
`/home/dev/.cache/crowley/rust-toolchain-1.85.1/toolchain/bin/cargo` for Rust builds.
Do not set or repurpose HOME globally. Scope any display environment fixtures.
Use a timeout for exploratory runs; do not repeat a 35-minute baseline.

Run default pytest with external wall time and durations report, appropriate
isolated DB tests only if a test database is available, and scoped Ruff checks.
Parent independently reproduces the final default command and inspects removed
test names versus retained coverage. Sol reviews correctness, lost coverage,
parallel isolation, cleanup, test integrity and scope. Report counts, wall time,
worker count, deleted behavior coverage, skipped tests, and unresolved concerns.

Later phases receive supplementary plans with exact file ownership before edits.
