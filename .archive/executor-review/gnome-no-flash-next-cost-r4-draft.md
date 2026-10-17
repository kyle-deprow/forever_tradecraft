# GNOME no-flash next-cost R4 candidate

Status: **DRAFT_NOT_FROZEN**. This candidate is held for parent, Sol, and Opus
review and has no live release. R2 and R3 artifacts remain preserved. No
screenshot, D-Bus activation, desktop input, profile/configuration change,
production source change, or rebuild occurred.

## Candidate and provenance

The unchanged private instrumented GNOME Screenshot 41.0 binary remains
`/home/dev/.cache/crowley/gnome-no-flash-next-cost-r1/prefix/bin/gnome-screenshot`
(SHA-256 `b988bc4c49251c7951805b0af6ad942dd82d50052feffd338f5f6b72d43b025c`).
The accepted stage2 binary remains `45750c8d…`; the production driver remains
`14ae6be4…`. R4 is a private harness/documentation correction only:

- R3 harness: `gnome-no-flash-next-cost-benchmark-r3-candidate.py`, SHA
  `70743fa2…`.
- R4 harness: `gnome-no-flash-next-cost-benchmark-r4-candidate.py`, SHA
  `913fa3960cc9275ff6920a6a898a8557a70e1b07a5a83780f89da7a0dd6ef463`.
- R4 diff: `gnome-no-flash-next-cost-r4-draft.diff`, SHA recorded in the
  accompanying draft manifest.
- R4 manifest: `gnome-no-flash-next-cost-r4-draft.json`; its `created_utc` is
  explicitly null because no exact creation timestamp was recorded. The
  original Docker invocation was not retained; the script, pinned image digest,
  private mount root, and complete build logs are retained.

The build network was attached through apt update/install, Meson configure,
compile, and install. This was isolated to the private cache root and made no
host package or runtime change.
The candidate self-check binds the R4 manifest, private binary, and current
production driver hash. It does not replace parent release verification against
the preserved R2 freeze: before any live use, the parent must independently
compare the accepted stage2 binary/source/build hashes and all R2 boundary
claims.

## Harness corrections

A complete first marker stream now ends the bounded run. The predeclared second
ordinal is consumed only when the first otherwise-valid attempt has an absent or
incomplete marker stream. Malformed, mid-line, extra, unknown, cross-token,
cross-PID, out-of-order, or non-monotonic markers are nonretryable. Owner,
capture, decode, freshness, and cleanup failures remain stop conditions. The
pure `sample_attempt_decision` function is used by the production loop and table
covered by offline tests.

Successful screenshot commands retain the driver's decoded text `stderr` from
`CompletedProcess`; the record states that it is not raw bytes. When unchanged
production `X11Backend._run` raises, no `CompletedProcess` is available because
the driver has already decoded/discarded the child stream. The receipt records
`diagnostic_stderr_available=false`, the reason, and a nonretryable marker error;
it does not create or hash an empty fake file and does not claim failure-stage
attribution. The process's original exception and precedence are preserved.

Live evidence, if separately released, uses the distinct
`gnome-no-flash-next-cost-benchmark-*` directory and schema 3 receipt kind
`gnome-no-flash-next-cost-diagnostic`. The process-local PATH prepend and
process-local `CROWLEY_NEXT_COST_TOKEN` injection are both recorded; inherited
XDG/GSettings variables remain unchanged.

## Timing derivation

For a complete successful marker stream, `derive_intervals()` converts marker
nanoseconds and Python `time.monotonic()` values on the same Linux
`CLOCK_MONOTONIC` clock. It requires command start <= `main_enter`,
`run_return` <= command end, exact event order, and non-overlapping intervals.
It emits `pre_main`, every adjacent marker interval with a semantic label, and
`post_run_return_tail`; the sum of all emitted durations must equal the parent
command elapsed time. Labels include GApplication registration, GTK/libhandy
startup, config load/parse, dispatch, Shell call, Shell PNG decode, unlink,
output open, PNG encode/write, recent in-memory work, shutdown, and the
post-`run_return` tail. It reports an upper bound made only from explicitly
identified adjacent empty marker pairs and never subtracts an unmeasured pass.

`recent_entry_begin`/`recent_entry_end` cover default-app lookup, recent-file
parse, and the in-memory add. `app_release` to `run_return` is labelled
`shutdown`; it includes GTK deferred recent-file flushing, D-Bus teardown, and
settings synchronization. It is not presented as removable startup cost for a
persistent process. The final `run_return` marker precedes `g_autoptr`
application cleanup; the post-marker tail is reported separately.

The earlier `.05 s` PNG-completion timing is described as the driver's PIL
`verify()`/`load()` decode after the child has exited, not as time waiting for a
writer to finish. No new live timing is claimed by this candidate.

## Verification

The candidate was checked with:

```text
python3 /home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark-r4-candidate.py --self-test
# 32 tests passed
python3 /home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark-r4-candidate.py --self-check
# PASS
python3 -m py_compile /home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark-r4-candidate.py
# PASS
```

The self-tests include the real compiled private `--version` emitter with only
`CROWLEY_NEXT_COST_TOKEN` set and no display/bus environment: it exits cleanly,
emits the valid truncated `main_enter`, `app_constructed` prefix, and does not
claim a complete live stream. They also cover complete-first-stop, incomplete-
first retry, second-incomplete refusal, capture/decode/owner failure precedence,
unknown events, PID changes without an expected PID, prefix placement,
interval containment, interval sums, and semantic labels.

Logs are retained under
`~/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-r4-candidate/`.
This remains a reviewed candidate only; it makes no one-Hz, native-100, or
production qualification claim.
