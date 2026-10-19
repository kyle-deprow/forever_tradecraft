# Host scheduling for backups and collection health

Status: proposed within the user's20:07UTC instruction to proceed to unattended
operation. Parallel scope, independent of the native resource-policy correction.
Current game scans remain on the addon900s clock; no cron-driven game input.

## Outcome and ownership

Install persistent systemd user timers for hourly validated market backups and
read-only collection health checks every two minutes. Routine host maintenance
must not require Luna. No external messages or desktop notification/input.
Root owns installation, documentation, Git and live validation. Luna implements,
Sol and actual CLI Opus review. Do not change the main session controller.

Only these six files may be created/changed by the implementer:

- tools/crowley_ops.py
- tests/test_crowley_ops.py
- deploy/crowley-market-backup.service
- deploy/crowley-market-backup.timer
- deploy/crowley-health.service
- deploy/crowley-health.timer

Use an isolated worktree based on current source. Existing market_backup.py,
core/session/addon/helper/config/compose files are read-only. No live services,
Docker/DB/game operations, installation, commits, resets, stashes or source edits
outside this fence from the implementation worker. Tests use private fixtures.

## Backup operation

CLI takes explicit repo/config/state paths, suitable for systemd WorkingDirectory
and the repository's .venv Python. Reuse tools.market_backup.snapshot and
validate_snapshot without changing their implementation. Hold a nonblocking
process-lifetime flock for this task to prevent overlapping scheduled/manual ops
runs. A busy lock skips safely, preserving the previous successful record.
Capture full backup output privately; emit only bounded success/failure metadata.
Retain the current0700directories/0600files. Atomically record latest valid
snapshot name, manifest digest and completion timestamp after validation. A
failed/incomplete snapshot must not replace last-known-good backup metadata.
Do not prune, restore, delete backups or change the server. Failure returns a
nonzero code to systemd with an actionable fixed category; no secret/raw dump.

The service is oneshot with restrictive umask and no automatic concurrent retry.
The timer is hourly at minute12 with Persistent=true. Root will stop duplicate
manual hourly scheduling when the timer is enabled and independently validate
one real service invocation plus the next computed trigger. Existing restore
drill is accepted; do not run a restore drill for this scheduler change.

## Health operation

Read existing session config, request read-only daemon status via bounded IPC,
read companion-state uploaded timestamps, and inspect only the two Crowley user
service states. No captures, input, recovery/restart, model calls or Docker writes.
Use a fixed bounded schema with observation time, service/controller state,
calibration flags, most recent upload age, pending/deadline facts when present,
last backup age and concrete local issues. Keep full raw status private if retained;
public stdout/journal must not dump arbitrary daemon fields or configuration.

Distinguish deliberately PAUSED/STOPPED/calibration states from an operational
stall: report their facts without marking an expected scan pause as a failure.
Inactive/unreachable required services, invalid/unreadable input, BLOCKED state,
expired active operation deadline or uploads stale by more than two900s periods
while the controller expects operational progress produce an attention result
and nonzero exit. No upload history is explicitly unknown, never fresh. Future or
malformed timestamps cannot be treated as fresh success. A missing/old backup is
reported independently; threshold should cover hourly cadence plus a modest
completion grace, documented in code/docs rather than hidden magic.

Write an atomic private latest-health JSON and bounded journal summary. The
health service is read-only apart from its own state files. Timer every two
minutes. These are local health records/failed-unit visibility, not a claim that
an email/mobile alert exists. Overages in nativeResourceAssessment, if present,
are displayed truthfully without redefining current native qualification.

## Verification and release

Meaningful tests cover stale/fresh/future/malformed/missing timestamps, expected
pause versus operational stall, unavailable services/IPC, atomic last-good backup
preservation and real process flock exclusion. No live DB or GUI in tests.
Run `uv run pytest -q tests/test_crowley_ops.py`, scoped Ruff/format/compile/diff,
and systemd-analyze verify/calendar on the new units (no activation).
Freeze six hashes/diff/private logs. Parent reproduces before Sol/actual Opus
source approval. Then root copies exact files/units, enables timers, runs a real
backup oneshot and health oneshot, independently validates the backup, checks
private modes, last-good state and installed timer deadlines. No restart of
crowley-session or companion is needed for this host-only release.
