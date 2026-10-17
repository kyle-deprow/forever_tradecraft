# Complete and serialize the production GNOME capture

User authorizes restoring WoW, realistic executors and repeating scans with Luna
implementation, Sol and actual Opus reviews. AGENTS.md is revoked. No git changes
such as commit/reset/stash/push are authorized. Preserve all unrelated edits.

Actual diagnosis: `native-capture-concurrency-diagnosis-r1.json` proves that the
single-instance GNOME Screenshot D-Bus application can exit0 before its requested
PNG exists or finishes writing. One capture never materialized. The helper failed
at the construction-ready edge before any input. Pure preflight was insufficient.

## Scope and order

Implementer owns only `src/crowley/session/driver.py`, new
`tests/test_session_capture.py` and scoped test adjustments in
`tests/test_session_driver_actions.py` if existing capture fixtures need actual
valid PNG output. Record original/current hashes and exact diff under
`.archive/executor-review/gnome-capture-*`. Other source, native ABI/thresholds,
private helper/profile, services, game, database and configuration are read-only.
No GUI input, native calibration or kernel reset. Do not commit/reset/stash/revert.

1. Read actual capture and subprocess deadline paths before editing. Keep the
   exact GNOME backend/argv and all identity checks. No alternate backend.
2. Serialize Crowley's requests across independent backend instances/processes
   using one private user capture lock, separate from the desktop input lease.
   Lock wait, subprocess, output completion and final identity verification must
   consume the existing supplied deadline (or existing15s bounded capture budget).
   Use nonblocking bounded acquisition and reliable release on every failure.
   Protect the shared lock path from symlink/owner/unsafe-mode mistakes using
   existing local conventions. Never unlink a held shared lock inode.
3. Success requires the newly requested complete PNG, validated with strict image
   verification and full decoding. Avoid accepting stale preexisting output.
   Prefer a unique private staging output and publish it atomically only after
   completion, if compatible with existing argv/identity/schema behavior. Keep
   failed evidence private; don't leave stale images available as new success.
4. Preserve capture-start timestamps and freshness semantics: waiting consumes
   time and never restamps an old observation. Missing/partial/invalid PNG and
   expired lock/completion/identity checks must fail with a useful DriverError.
   Do not widen runtime freshness/resource/travel budgets or retry native runs.

## Verification

Use meaningful tests at production X11Backend.capture boundary. Include real
owned writer subprocess behavior: exit0 before creation/partial PNG completion;
never-created/truncated output refuses by deadline; old valid destination cannot
count as this request; cross-process serialization rather than only one-thread
mutex; contention consumes caller deadline without invoking screenshot; final
identity change refuses; cleanup releases lock for a successor after failure.
No real input or compositor needed for tests. Do not fake the gate under test.

Run `uv run pytest -q tests/test_session_capture.py tests/test_session_driver_actions.py`
plus scoped Ruff check/format and compile checks. Record real results. If other
existing tests genuinely need fixture updates, report exact paths before editing.
Parent independently reproduces tests and inspects delta. Sol then actual CLI
Opus read-only review. After accepted source only, parent restarts unarmed daemon;
sole operator may run read-only concurrent production captures to verify complete
outputs before one further native attempt. Never claim native acceptance from
the read-only capture test. All earlier resource failures remain retained.

## Accepted r1 review corrections

Sol found a reachable revocation/rearm race: the GNOME client can exit before
completion, and the backend's clearable cancellation event cannot retain old
revocation across a successor activation. Bind admission to a monotonic backend
revocation epoch. Check the exact epoch during lock wait, image wait, after final
identity work and immediately before publication. Test real delayed output with
revocation then rearm, plus revocation while contending for the lock.

The single finally-unlink also misses a writer that creates the stage after the
deadline. Put staging inside a fresh0700 per-attempt directory on the destination
filesystem, and retire the directory on exit so a late not-yet-opened writer
cannot recreate the file. Test delayed creation after timeout, private active
directory, unchanged destination and a succeeding next request. Do not claim
success-path unlink alone proves late-writer cleanup.

Actual Opus r1 (`claude-opus-5-5`, exit0) independently confirmed cancellation
and late-writer cleanup, and found a geometry regression. GNOME captures the
desktop; existing cropping permits a desktop larger than the origin0 child.
Preserve that behavior. A complete image with wrong format/insufficient size is
a terminal refusal rather than a partial-image retry. Test larger desktops and
prompt invalid-geometry/format refusal. Give real child-process refusal tests
at least1s startup budget so they test completion rather than startup load; do
not change any production deadlines for this test correction.
