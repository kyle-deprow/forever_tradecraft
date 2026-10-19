Model ID: **claude-opus-5-5**

All four accepted Should issues are fixed, and I found no regressions. I only reviewed the four changed files, comparing them with `rust-matcher-runtime-integration-20261019`. The three Rust files are identical in both worktrees, and all seven hashes match the parent-final `result.json`. I made no edits and ran no builds or tests.

## The four fixes
1. **Build workspace and ancestor refusal: fixed.**
   - **Location:** the build workspace is now under `~/.cache/crowley/template-matcher/build-v1`, not `TMPDIR`. That directory is checked to be owned by you and mode 0700.
   - **Refusal:** `_refuse_ancestor_build_inputs` (`tools/build_template_matcher.py:104`) refuses any `Cargo.toml`, `.cargo/config` or `.cargo/config.toml` in any parent directory. It starts from both the snapshot's parent directory and the neutral working directory, walks up to `/`, and runs before any toolchain command.
   - **Refusal test:** `tests/test_template_matcher.py:697` plants a `linker` setting, `opt-level = 0`, and a `[workspace]` `Cargo.toml`. Nothing else overrides these. If either check were deleted, the test would fail, because cargo would error on the workspace or run the planted linker.
   - **Republication test:** the test at `:613` builds clean, then rebuilds into the same output with poisoned settings, and requires the artifact and manifest to be byte-identical.
   - **This host:** there is no `~/.cargo/config*`, and no directory on the cache path is a symlink.
2. **Exact stderr: fixed.** `invoke_error` now requires the stderr to equal the full message, not just its prefix. Each of the 14 expected messages appears exactly once in `main.rs`, and the 31-test run passing shows each check fires before the truncation check.
3. **Benchmark: fixed.**
   - **Binary path:** the path given to `--binary` is made absolute without following symlinks.
   - **Images:** each PNG is decoded from the same bytes that were hashed.
   - **Hashes:** the binary is hashed before and after timing, and the run fails if they differ. In the parent-final `benchmark.json` both hashes are `75b18…`.
   - **Report:** it records argv, the Python and Pillow versions, and the runner's own SHA.
   - **Timing fields:** renamed to `startup_ipc_native_scoring_ms`.
   - **Symlink test:** the test would catch a switch to `resolve()`.
4. **Doc: fixed.** The numbers match the r2 `benchmark.json` medians exactly (63.30, 40.55/40.58, 7.53/7.56, 8.33/7.39, 49.39, 81.89). The doc also gives samples=3, warmups=1, the binary hash, and labels which SCORE_AT calls are the own-box ones and which are the rival checks.

**Regression check:** `tools/template_matcher_runtime.py` in the integration worktree doesn't look at the toolchain keys. The new `rustc_verbose` manifest key therefore doesn't affect it, and the binary and source pins are unchanged.

## Must
None.

## Should
None.

## Nits (none of these block acceptance)
- **The cargo verbose output isn't kept.** `--verbose` is passed, but `_command_output` (`tools/build_template_matcher.py:223-236`) keeps only stdout when the build succeeds. The parent-final `build.log` contains no cargo ``Running `…` `` lines. So the in-scope "cargo verbose retained output" nit is only half done: the extra detail appears only in error messages when a build fails.
- **The cache path isn't checked for symlinks.** The ancestor check walks the path as written, while cargo walks the real directory path. If any directory on the cache path were a symlink, cargo would check config locations the builder never looked at. This can't happen on this host. The fix is one line: refuse when `BUILD_CACHE_ROOT.resolve() != BUILD_CACHE_ROOT`.
- **The relative-path test only covers the hashing step.** `tests/test_template_matcher.py:786` only exercises `_source_binding`. If both calls that make the path absolute in `tools/benchmark_template_matcher.py` (lines 242 and 516) were removed, the original bug (timing a different file than the one hashed) would come back and this test would still pass.
- **One in-scope nit wasn't done.** The test for two acceptable candidates that each overlap the best box but not each other was not added.

I also wrote this review to the plan file `/home/dev/.claude/plans/read-only-delta-follow-up-state-twinkly-teacup.md`.

STATUS: READY
