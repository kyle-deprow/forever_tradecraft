# Market backup and restore drill

Status: proposed offline launch-readiness slice, not implemented or released.
Source root: `/home/dev/repos/pegasus`; canonical origin is forever_tradecraft.
Live collection and the native/recipe implementation fences are independent.

## Owned files and outcome

Proposed ownership: `tools/market_backup.py`, `tests/test_market_backup.py`, and
`docs/MARKET_RECOVERY.md` only. Run artifacts belong in private local state;
only sanitized summaries may be committed. No migrations, scanner, session,
recipe, companion, existing deployment-unit or compose changes. A Sol plan
review precedes implementation. No source-control operations by workers.

Deliver a local snapshot command and a disposable restore-drill command. Never
restore into the live database or volume. No offsite upload is in this slice.

## Snapshot contract

- Resolve the actual Compose project/container/volume identity using the checked-in
  deployment and private env file without printing its values or container Env.
  Record source commit plus dirty-source fingerprint, image IDs/digests, migration
  files, schema/build/house/plan counts and archive references in a sanitized manifest.
- Create a new owner-only destination; refuse existing paths, unsafe permissions
  and symlinks. Use `pg_dump` custom format inside the existing database container,
  without passing passwords in command arguments or output.
- Dump the database FIRST, then copy the immutable raw archive volume. Ingestion
  writes the immutable archive before committing its DB reference; this order
  permits concurrent collection while ensuring snapshot DB references predate the
  later raw copy. Preserve original compressed envelope bytes. Exclude unfinished
  temporary files, and do not assume every copied archive is DB-referenced.
- Publish a complete snapshot only after dump/raw checksums and manifest are
  durable. Retain failed evidence under an explicit incomplete marker, never
  advertise partial files as a valid backup. No live ingestion pause or deletion.
- Archive references must be checked against the restored snapshot, not a later
  query of the live changing database. Verify referenced raw files exist and
  decompress/validate, recompute their logical content digests using the existing
  ingestion definition, and compare identity and plan. Report extra/orphan raw
  objects separately; never delete them. Any missing referenced object fails.
- Credentials/private profiles are not part of the public manifest. The runbook
  separately identifies companion config/state, Data.lua, SavedVariables, session
  journal/archive and executable/plan fingerprints needed for machine recovery.
  Do not imply a market snapshot alone restores game control or calibration.

## Disposable drill contract

- Require an explicit snapshot path and a fresh unique drill project. Use new
  containers and new volumes with positive label/ID verification; refuse any ID
  matching the live database/server/raw volumes. Do not alter or attach live
  volumes writable. Use compatible pinned Timescale/Postgres and server images.
- No conflicting host ports: use a private internal network and, if API probing
  requires it, an ephemeral port bound only to127.0.0.1. Generate drill-only
  credentials in a private temporary file; never print or persist them in Git.
- Reject unsafe tar members, symlinks and path traversal before extraction. Restore
  DB/raw only into proven disposable targets. Check dump/manifest/archive hashes,
  schema and row counts by table and regime, plan hashes, all DB-to-raw references,
  health and one authenticated read API. Compare against the dump's own snapshot,
  allowing documented extra immutable raw objects.
- Record exact receipt and cleanup. Terminate/remove only identity-verified drill
  resources. Keep the backup; retain failed restore evidence and do not broaden
  cleanup to unrelated Compose projects or volumes.

## Verification

Use meaningful tests for incomplete snapshots, checksum changes, missing references,
orphans, unsafe archive paths and mistaken live-target selection. Run a real
disposable restore once from a read-only production snapshot after unit checks.
The live DB is read-only to this operation; all restore writes are disposable.
Acceptance is a successful restore receipt, not merely a successful pg_dump.

Keep launch history partitioned by exact house/build/interface/plan. A restored
beta database must retain beta labels; it must never be rewritten into launch
history. Controller/input gates remain disabled until fresh launch qualification.
