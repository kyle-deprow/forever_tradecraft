# Plan: preserve failed construction measurements and isolate Agent allocation

Status: proposed, plan only. This document authorizes no source, service, game,
configuration, live-capture, or frozen-worktree change.

## Verified boundary and evidence gap

- The target is the private `native-handshake-20261017T173946672064Z-pid1439046`
  receipt. It reports `native construction memory growth exceeds its limit`; its
  nested prior terminal observation also reports that no fresh `normal/0` frame
  arrived. The construction reset archive is ordinal 0 with record SHA
  `035cf83d617288ffb391e629b23fcedd21462aab03255442ee35e12e4a7c9ffa`.
- The supplied pre-reset HWM/RSS was 2,667,470,848 bytes. The fixed construction
  limit is 134,217,728 bytes. The receipt and `session.json` do not contain the
  completed measurement's post-reset HWM, final HWM/RSS, or growth; the latter
  retains only archive counters. Missing values remain unknown until the durable
  archive is found. No retry or qualification may reconstruct them.
- `Agent.lua` calls `createSurface()` while the file is loaded. That allocates the
  frame and 2,048 textures before the update script is installed. `ns.On` can
  register events, but Agent has no current deferred lifecycle or world-stability
  carrier.
- Reset5 begins only after the real absent-surface proof, historical archive,
  `clear_refs=5`, post-reset read, and baseline-ready publication. It ends after
  the first bound fresh `normal/0` capture and final HWM/RSS read. World/terrain
  loading is therefore eligible for the interval, but this receipt cannot prove
  that it occurred or attribute growth to it.

## Stage A: retain the exact completed failed measurement

`LinuxProcStatusVmHwmReset5.finish_window` already reads final HWM/RSS, constructs
`NativeMemoryMeasurement`, and calls `verify()` before applying the limit. Add an
owned completion callback at that boundary in a future isolated worktree:

- `src/crowley/session/calibration.py`: define a typed
  `NativeMemoryMeasurementArchiveReceipt` separate from the existing
  `NativeMemoryArchiveReceipt` (which covers only the pre-reset record). After
  `NativeMemoryMeasurement.verify()` and only when `growth_bytes > limit_bytes`,
  invoke the production callback before raising the existing exact limit error.
  The callback receives the complete measurement and returns the typed receipt.
  A callback failure is private diagnostic state and the original over-limit
  exception remains the caller-visible causal error; no successful qualification
  may result. Direct meter tests without a production callback retain the current
  exception behavior.
- `src/crowley/session/daemon.py`: implement the production callback using the
  existing `controller.journal.append_archive` mode-0600 append-only path, with
  archive kind `native_memory_failures`. The exact application payload is:
  `schema: 1`, `outcomeId`, `phase`, `ordinal`, `decision: "rejected_over_limit"`,
  `qualifies: false`, `failure: "native <phase> memory growth exceeds its limit"`,
  `measurement: NativeMemoryMeasurement.to_dict()`. `outcomeId` is the SHA-256
  of canonical JSON containing the kind, identity-bound measurement, and failure
  string. Journal-owned `archiveOrdinal`/`archivedAt` remain its only additions.
  The typed receipt covers `outcomeId`, measurement digest, durable archive
  ordinal, and `durable: true`; it is verified against the exact measurement.
  Do not add this private artifact to the IPC handshake, public calibration
  evidence, schema-2 receipt, or qualification counters.
- The private measurement includes every existing dataclass field, including
  historical/post-reset/final values, timestamps, identity binding, limit, and
  derived growth. Do not redact fields needed to verify accounting, and do not
  copy them into status output. A failed archive is logged privately without
  replacing the original failure or changing the 128 MiB decision.
- No consumer migration is required: successful native evidence and all current
  public response shapes remain byte-compatible. The new archive kind is an
  audit artifact only.

Stage A tests, in `tests/test_session_native.py` and
`tests/test_session_native_regressions.py`, must prove: exact completed
measurement is archived before an over-limit exception; digest/outcome replay is
idempotent; archive-write failure preserves the original causal error and leaves
qualification false; under-limit measurements still return unchanged; final
read/identity failure creates no fabricated measurement; and the archive is
0600/private. Run:

    uv run pytest -q tests/test_session_native.py tests/test_session_native_regressions.py
    uv run ruff check src/crowley/session/calibration.py src/crowley/session/daemon.py tests/test_session_native.py tests/test_session_native_regressions.py
    uv run ruff format --check src/crowley/session/calibration.py src/crowley/session/daemon.py tests/test_session_native.py tests/test_session_native_regressions.py

## Stage B: concrete deferred-Agent construction path

Future ownership is exactly `addon/Crowley/Agent.lua`,
`addon/Crowley/Commands.lua`, `src/crowley/session/daemon.py`,
`src/crowley/session/calibration.py`, and the focused native/addon tests. The
normal path remains unchanged when no one-shot marker is present.

1. Add `/crowley agent defer` as an explicit opt-in. It refuses while
   `ns.Scanner.InProgress()` or a pending scanner/queue action exists, writes one
   ephemeral `CrowleyDB.nativeConstructionMode = "deferred"`, and requires
   `/reload`. On the next addon load Agent consumes and clears that marker before
   creating any surface; its in-memory state is `unconstructed`. A later reload
   without a new marker returns to normal construction. Scanner scheduling,
   SavedVariables scan records, and queue ownership are untouched.
2. While deferred, the authorized operator reaches the build-pinned in-world
   steady boundary and runs the existing `native-bootstrap` then
   `native-calibrate` sequence while the Agent surface is still absent. The
   operator's accepted visual proof must be explicit and build-bound; no fixed
   sleep, nonempty zone guess, or ordinary crop alone may claim world stability.
   If that proof is unavailable, this mode remains test-only and ineligible.
3. After the daemon publishes baseline-ready, the operator issues exactly one
   finite game-local `/crowley agent construct`. Agent checks deferred state and
   scanner idleness, calls the existing `createSurface()` once, publishes the
   first fresh `normal/0`, clears the one-shot state on success, and refuses
   duplicate, stale, or failed requests. The daemon accepts only a fresh frame
   whose capture time is after the reset-release boundary; an early, late,
   identity-changed, boot-changed, or duplicate frame is a terminal restoration
   failure, with no second construction attempt.
4. The exact measured order is: absent proof → one reset5 baseline → one
   construct trigger → fresh bound `normal/0` → final accounting → existing
   restoration/cleanup. The 128 MiB limit, reset method, process identity,
   cancellation, and watchdog guards remain unchanged. Deferral alone is not
   claimed to isolate terrain unless the reviewed steady-world proof establishes
   the boundary immediately before reset.

Stage B tests must use the real Lua harness and compiled native fixture to cover
normal eager construction, deferred addon-load absence, scanner-busy refusal,
accepted one-shot construction, duplicate/early/late trigger refusal, stale
identity/boot, constructor error, reset failure, and cleanup. Run:

    uv run pytest -q tests/test_addon.py tests/test_session_native.py tests/test_session_native_regressions.py
    uv run pytest -q tests/test_session_native.py tests/test_session_performance.py

Run the focused native/addon tests plus the full native/performance suites before
any live restart or qualification. No Rust decision follows from this plan; a
separate CPU bottleneck profile would be required.
