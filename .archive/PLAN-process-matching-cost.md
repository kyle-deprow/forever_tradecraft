# Plan: remove noncandidate process-matching I/O

Status: proposed, plan-only. Implementation, integration, restart, live comparison, and any Rust work require separate authorization after root review of this plan. This document releases no optimization.

## Evidence and decision boundary

The reviewed diagnostic summary at `.archive/executor-review/identity-latency-live-20261018-summary.json` is SHA-256 `ee1e53b16ed6dfde83fd32399405fb97248007ffc3cc07fdcac0367538601a77`. Its three manifest-bound single requests each reached four fresh `proc_match` spans. The twelve owner-thread CPU intervals were 91.588–115.394 ms and closely tracked wall time; every request ended at `owner_post_capture_check` under the unchanged one-second deadline. The observed host snapshot had 745 numeric `/proc` entries.

This is useful diagnostic evidence, not the formal Rust gate. All three artifacts were partial, their event lists were truncated, and three singles are neither schema-2 qualification nor the required 15 independent fixed-eight runs and 120 decoded pairs. No Rust trigger, native qualification, or deadline change follows from these observations.

The code supplies a narrower actionable cause. At commit `fe439243afdb7e2fd0ba8244819eac2fa9086761`, `X11Backend._process_executable` reads `cmdline`, `stat`, `status`, and the `exe` symlink, resolves the executable path, and only then checks whether the command line contains the configured Windows executable exactly once. `_matching_game_pids` repeats that work for every numeric process entry. Nearly all entries can be rejected from the already-read `cmdline` without the remaining process I/O.

## Exact implementation

Source fence:

- `src/crowley/session/driver.py`
- `tests/test_session_driver_actions.py`

In `_process_executable`, keep the existing `cmdline` read, UTF-8 replacement decoding, NUL split, `/` and `\` basename extraction, case-sensitive comparison, and exactly-one-match rule. Move that rule immediately after the `cmdline` read. A zero-match or duplicate-match process raises the same typed `DriverError` rejection before reading `stat`, `status`, `exe`, or `environ`.

For an exact single-basename candidate, keep every current check and its order: read start time from `stat`, read `Name` from `status`, resolve the `/proc/<pid>/exe` link and require basename `wine-preloader`, then, when configured, read `environ` and compare the real expanded `WINEPREFIX`. Return the same `(configured executable, start time)` tuple. `_matching_game_pids`, its numeric enumeration, set semantics, and its swallowed `DriverError`/`OSError`/`ValueError` classes remain unchanged.

Do not add a process cache, candidate cache, PID memo, background watcher, batch helper, fallback identity, relaxed match, or deadline/cancellation special case. `resolve_identity` must still call `_matching_game_pids` at each of the four existing barriers and must still re-run `_process_executable` for the selected window PID. Duplicate executable arguments remain a refusal. Actual Wine `cmdline`, `Name`, loader, prefix, start time, window PID membership, and final identity checks remain mandatory.

For a stable `/proc` snapshot, the matched PID set is byte-for-byte identical: only processes with exactly one configured basename reach the unchanged remaining predicates. Under exit, PID reuse, or `exec`, the current `cmdline` bytes remain the decision for that invocation. A nonmatch stays rejected even if it changes immediately afterward; the next barrier scans it fresh. A candidate that exits or changes after the read reaches the unchanged remaining reads and fails closed on missing or inconsistent `stat`, `Name`, loader, or prefix. No read result crosses calls or barriers.

Early rejection deliberately changes only an unobservable internal precedence: a nonmatching process whose later proc files are unreadable now raises the configured-executable `DriverError` before the generic inspection error. `_matching_game_pids` already catches both and returns the same set. Candidate read failures and all errors reachable through a selected matching window retain their present messages and behavior.

## Tests

Use real short-lived subprocesses and their real `/proc/<pid>` files. A temporary copied interpreter named `wine-preloader` can set its Linux comm name, argv, and `WINEPREFIX` to model a valid Wine candidate without touching the running game. Instrument filesystem methods only to record or synchronize actual reads; do not replace `_matching_game_pids` or `_process_executable` with a fake.

Tests must prove:

- a zero-match process and a duplicate-basename process read `cmdline` but never read their `stat`, `status`, `exe`, or `environ`, and remain absent from the matched set;
- one valid candidate performs the full checks in the existing order and is returned once, while wrong `Name`, loader, prefix, and malformed start-time fixtures remain rejected;
- a candidate exit after `cmdline` yields the existing inspection failure and is omitted;
- synchronized nonmatch-to-candidate and candidate-to-nonmatch `exec` transitions cannot create a mixed-generation acceptance, and the following fresh call observes only the new stable state;
- multiple valid candidates retain both PIDs so the existing exactly-one-game-process refusal is unchanged;
- the production resolver integration still binds the window PID to the actual matched set and rechecks the candidate; no matcher method is monkeypatched in this integration case.

## Acceptance and parent verification

The implementer records the base commit, exact two-file diff, before/after hashes, and outputs from:

```text
uv run pytest -q tests/test_session_driver_actions.py -k 'process_executable or matching_game_pids or native_resolver'
uv run pytest -q tests/test_session_driver_actions.py
uv run ruff check src/crowley/session/driver.py tests/test_session_driver_actions.py
uv run ruff format --check src/crowley/session/driver.py tests/test_session_driver_actions.py
python -m compileall -q src/crowley/session/driver.py tests/test_session_driver_actions.py
git diff --check
```

Parent verification must inspect the real source diff and read-order assertions, confirm the exact fence and clean worktree, compare stable and transition fixture PID sets, and verify that the four identity call sites, profiler schema, IPC/public evidence, cancellation, deadlines, and failure text for actual candidates are unchanged. A Sol source review is required before integration.

Any later live comparison needs separate approval. After accepted integration, the parent creates a new private mode-0600 manifest under a mode-0700 directory, binds the new `driver.py` hash and the still-accepted hashes for every other named source, and independently rechecks unchanged config raw/semantic and producer hashes. After the separately authorized sole quiet restart, run exactly three sequential instrumented `paused_region_sample` singles in the same PAUSED generation with the existing 1.0-second deadline and 0.25-second failure-evidence grace. Retain all responses and profiles, require binding consistency and all four fresh spans per request, and compare owner-thread CPU by barrier with the prior medians: daemon-pre 105.278 ms, backend-pre 105.034 ms, backend-post 102.840 ms, daemon-post 102.949 ms. Diagnostic acceptance requires all four new medians to decrease, the pooled median to decrease by at least 50%, no new identity/error phase, and no changed matched identity. These three singles remain diagnostic and cannot satisfy or substitute for the formal Rust gate.

## Rollback and later Rust boundary

If source tests, review, or the separately approved live comparison fail, stop further samples and restore the previously reviewed `driver.py`; do not compensate with a cache, stale PID, or longer deadline. Re-run the two-file checks, bind the restored hash in a fresh parent manifest, and use the same separately authorized restart/paused identity verification before any further live work.

Rust is considered only if a later schema-2 evidence set satisfies the existing `RUNTIME_PERFORMANCE.md` baseline and returns `plan_prototype` through its repeatable CPU/ratio or counterfactual deadline gate after this Python change. The next plan may then prototype only a fresh one-shot process matcher with the same exact basename cardinality, start/comm/loader/prefix predicates, closed PID/start result, error mapping, four independent calls, and no cache or persistent helper. It must compare the optimized Python matcher before expanding the fence. Removing unnecessary proc reads comes first because a Rust rewrite that preserves those reads keeps the avoidable kernel/filesystem work while adding a new binary and interface.

## Known unknowns

The diagnostics do not attribute CPU among directory enumeration, proc reads, decoding, regex splitting, or kernel path resolution; external child CPU remains unavailable. Numeric process count and procfs cache state vary between runs. The expected reduction and the 50% diagnostic threshold are therefore hypotheses to test, not released performance claims. The exact stable matched set and failure behavior are release invariants; measured speed is not permission to weaken them.
