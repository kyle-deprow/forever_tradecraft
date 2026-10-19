Model ID: **claude-opus-5-5**

The component needs work: four "Should" findings, none of them "Must" level. I made no edits and ran no builds or tests. The only file I wrote is the plan file `/home/dev/.claude/plans/read-only-final-rust-component-generic-quokka.md`.

## What checks out
- **Hashes:** all 7 in-scope files hash exactly as listed in the parent r2 `input.json`, and nothing outside those 7 paths changed.
- **Reproducible build:** r1 and r2 ran the builder in separate temporary workspaces and both produced `75b18bd0…bcd80c`, which also matches the manifest.
- **Tests:** r2 ran 28 tests, all passed, none skipped. They ran against the published binary (`CROWLEY_TEMPLATE_MATCHER_BIN` was set). Because `CARGO` was also set, the contaminated-config builder test actually ran.
- **Matches the old helper:** on the same retained frame (sha `bfe7fb…`) and region 1676,24,220,84, the Rust results match the original Python helper: Construct at [1685,33,98,27] and Restore at [1789,33,98,27], both with score 0. The rival check scores 78466/7938 ≈ 9.885, above the 5.0 threshold, so it is correctly rejected.
- **Fixes:**
  - The builder now builds from a clean, minimal environment.
  - It checks exact toolchain versions.
  - It copies the 3 source files into a private snapshot (read from a stable file descriptor) and builds that snapshot twice.
  - Republication is checked against a fresh rebuild, not against the existing manifest.
  - The test that relies on x winning ties over y now really depends on that order.
  - The later-disjoint ambiguity test would catch a regression to comparing only the second-best candidate.

## Should
1. **The builder still reads Cargo config through the inherited `TMPDIR`** (`tools/build_template_matcher.py:420`, `:273`). The build workspace is created under the caller's `TMPDIR` (`/tmp` by default, which any local user can write to). Cargo reads `.cargo/config.toml` from every parent directory of its working directory, so `$TMPDIR/.cargo/config.toml` is loaded.
   - The test at `tests/test_template_matcher.py:588-622` sets up exactly this case. It only passes because the one key it plants, `rustc-wrapper`, is overridden by the `CARGO_BUILD_RUSTC_WRAPPER=""` environment variable.
   - Two keys that nothing overrides would work:
     - `[target.x86_64-unknown-linux-gnu] linker = "<script>"` would run that script during the build.
     - `[profile.release] opt-level = 0` would produce a different binary, and the manifest would not show it.
   - A parent `Cargo.toml` with `[workspace]` can also take over the build.
   - Fix: fail if any parent of the working directory or snapshot contains `.cargo/config`, `.cargo/config.toml` or `Cargo.toml`, and add an empty `[workspace]` to the package `Cargo.toml`.
   - Test fix: plant `linker` and `profile` keys in the config. Also run a clean build into the same output directory first. Then the contaminated build must pass the rebuild comparison, which also proves the planted `CARGO_ENCODED_RUSTFLAGS`/`RUSTFLAGS` were ignored. Today the test only checks that the wrapper's marker file is absent.
2. **The malformed-input tests prove nothing about the specific checks** (`tests/test_template_matcher.py:486-514`). Every parametrized case, plus the unknown-operation, reserved-field and bad-magic cases, sends an empty or short body. So each one also fails the truncation check, and all would still pass if the dimension, region, size-limit, operation, reserved or magic checks were deleted. Fix: assert the exact stderr message (each check has its own message in `main.rs`) or send correctly sized bodies. The `0xFFFFFFFF` case actually reports "search region is outside the frame".
3. **A relative `--binary` path in the benchmark runs a different file than the one it hashes** (`tools/benchmark_template_matcher.py:504-506`, `:196-205`). The path is never made absolute, and `subprocess.run(..., cwd="/")` looks up a relative program from `/`. I confirmed this behaviour with `./true`. The result is either a crash or timing a binary other than the one hashed. Fix: use `args.binary.absolute()` (not `resolve()`, so symlinks are still rejected), and re-hash the binary after the timed runs. The parent's run used an absolute path, so its evidence is still valid.
4. **The doc's timings don't come from the public runner** (`docs/RUNTIME_PERFORMANCE.md:292-300`). The figures 62.74 / 43.55 / 42.61 / 9.45 / 8.64 / 52.38 / 86.45 come from r1's ad-hoc script, whose timings include building each request. The doc presents them as if preparation were measured separately. The public runner in r2 measured:

   | Measurement | r2 public runner (ms) |
   |---|---|
   | Preparation | 63.30 |
   | SEARCH (Construct / Restore) | 40.55 / 40.58 |
   | SCORE_AT on own box | 7.53 / 7.56 |
   | SCORE_AT rival check | 8.33 / 7.39 |
   | Exclusive shape | 49.39 |
   | Dual-positive shape | 81.89 |

   Fix: use the r2 numbers, cite samples=3, warmups=1 and the binary hash, and label which SCORE_AT is the own-box call and which is the rival check.

## Nits
- **Republish path untested:** reusing, refusing a tampered artifact or manifest, and refusing a partial publication in `_publish` have no direct tests. The test fix in item 1 covers part of this.
- **Mislabelled field:** `startup_ipc_ms` includes the native scoring time (SEARCH shows 40.53 ms under that name). Rename it, or measure a real startup-only baseline.
- **Fixture hash can drift:** `_load_rgb` hashes the file, then opens it again by path to decode, so the hash and the decoded pixels can come from different contents. Decode from the bytes already read instead (`Image.open(io.BytesIO(raw))`).
- **Report lacks provenance:** the benchmark report has no argv, Python version or Pillow version, which plan item 5 asks for. Only the parent's private wrapper kept the command.
- **Builder tidy-ups:**
  - rustfmt is version-pinned but never run.
  - Tool lookup falls back to `PATH` when no toolchain directory is given, which goes against the no-fallbacks rule.
  - The manifest records `rustc -V` rather than the plan's `rustc -vV`.
  - The manifest stores the same source hash twice.
  - Environment variables are set twice.
  - cargo's output is thrown away on success, so the build log doesn't show the actual compiler commands; `cargo build -v` would fix that.
- **Test gaps:**
  - The seeded random tests almost never produce an accepted match (average pixel difference is about 85 against a threshold of 5).
  - No case has two acceptable candidates that each overlap the best box but not each other, which should report "matched".
- **Temp dirs leak:** `_fresh_build_binary` leaves a `mkdtemp` directory behind on every test run.
- **Not gitignored:** `native/template_matcher/target/` isn't in `.gitignore`. That file is outside this review's scope, so it's a follow-up.

STATUS: NEEDS WORK
