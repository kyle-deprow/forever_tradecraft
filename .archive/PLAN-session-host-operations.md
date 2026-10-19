# Host scheduling for backups and collection health

Status: authorized within the user's20:07UTC instruction to proceed to unattended
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
Retain bounded private operation receipts and fixed error categories; do not
retain raw child stderr/database output. Emit only bounded success/failure metadata.
Retain the current0700directories/0600files. Atomically record latest valid
snapshot name, manifest digest and completion timestamp after an explicit second
validate_snapshot call on the returned path. Snapshot itself already validates. A
failed/incomplete snapshot must not replace last-known-good backup metadata.
Do not prune, restore, delete backups or change the server. Failure returns a
nonzero code to systemd with an actionable fixed category; no secret/raw dump.

The service is oneshot with restrictive umask and no automatic concurrent retry.
The timer is hourly at minute12 with Persistent=true. Root will stop duplicate
manual hourly scheduling when the timer is enabled and independently validate
one real service invocation plus the next computed trigger. Existing restore
drill is accepted; do not run a restore drill for this scheduler change.

## Health operation

Use crowley.session.config.load_config, evidence.read_uploads and bounded
cli._socket_request(config.socket, {"command":"status"}, timeout=5.0). Require
ok is True and a bounded typed status. Inspect only the two Crowley user services
in one allowlisted systemctl --user show call with fixed LoadState, ActiveState,
SubState, Result and ExecMainStatus fields and a5s subprocess timeout. No captures,
input, recovery/restart, model calls or Docker writes. Unit TimeoutStartSec=30s,
below the120s timer interval. Avoid retaining arbitrary daemon/config data.

Use fixed classification operational | gated | attention and operational:boolean.
Valid PAUSED/STOPPED/NATIVE_CALIBRATION/INPUT_CALIBRATION are gated, exit0,
operational:false and summary GATED. Initial idle calibration awaiting an operator
is legitimate; do not flag it solely for idle (daemon initializes it that way).
Starting/running calibration is gated. Validate operation kind/state/error shape;
a reported error, impossible operation/controller combination, BLOCKED,
LOGIN_REQUIRED, invalid/unreachable services/inputs or an expired active deadline
is attention/nonzero. Active scan/save/reload/upload operations require a valid
unexpired deadline where the controller defines one. WAIT_DUE requires a valid
dueAt; allow a bounded240s overdue transition grace, then attention. Operational
requires current nativeCalibration/inputCalibration flags. This classification
states controller progress, never substitutes for the three-cycle acceptance test.

Read uploads strictly. Reject future timestamps; missing history is unknown,
never fresh. Expose most-recent upload age for visibility but bind cycle freshness
to exact status.lastUid. During SCANNING/save/reload/UPLOAD_WAIT before its valid
deadline, the current UID can legitimately be absent. After upload/ACK/qualification/
reopen/cleanup/WAIT_DUE a nonempty lastUid must exist in uploads; unrelated recent
uploads cannot cover its absence. Apply the1800s stale threshold only when the
controller would otherwise be operational; first-cycle unknown remains explicit.
Include bounded pending/deadline/calibration facts and concrete issues.

Health validates the last-good backup record schema, safe snapshot basename,
private directory/file modes, snapshot existence and COMPLETE marker digest
matching its manifest before using completion age. Missing/invalid/old backups
are independent attention issues even while gated. Maximum age75minutes covers
hourly cadence plus15minutes completion grace; document this constant. Never
read a forged future timestamp as fresh. Health does not perform a full DB restore
or recurring full archive validation.

Write an atomic private latest-health JSON and bounded journal summary. The
health service is read-only apart from its own state files. Timer every two
minutes. These are local health records/failed-unit visibility, not a claim that
an email/mobile alert exists. Overages in nativeResourceAssessment, if present,
are displayed truthfully without redefining current native qualification.

## Verification and release

Meaningful tests cover stale/fresh/future/malformed/missing timestamps, expected
pause versus operational stall, unavailable services/IPC, current-UID binding, initial idle calibration,
missing/altered COMPLETE or manifest, service-query timeout, atomic last-good backup
preservation and real process flock exclusion. No live DB or GUI in tests.
Run `uv run pytest -q tests/test_crowley_ops.py`, scoped Ruff/format/compile/diff,
and systemd-analyze verify/calendar on the new units (no activation).
Freeze six hashes/diff/private logs. Parent reproduces before Sol/actual Opus
source approval. Then root copies exact files/units, enables timers, runs a real
backup oneshot and health oneshot, independently validates the backup, checks
private modes, last-good state and installed timer deadlines. No restart of
crowley-session or companion is needed for this host-only release.
