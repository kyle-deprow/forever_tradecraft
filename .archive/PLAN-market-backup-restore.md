# Market backup and restore drill

Status: proposed offline launch-readiness slice; not implemented or released.
Source root: `/home/dev/repos/pegasus`; canonical origin is forever_tradecraft.
Live collection and the native/recipe implementation fences are independent.

## Owned files and outcome

Proposed ownership: `tools/market_backup.py`, `tests/test_market_backup.py`, and
`docs/MARKET_RECOVERY.md` only. Run artifacts stay in private local state; only
sanitized summaries may be committed. No migrations, scanner, session, recipe,
companion, deployment-unit or Compose changes. A Sol plan review precedes
implementation. No source-control operations by workers.

Deliver a local snapshot command and one disposable restore-drill command. Never
restore into the live database or attach a live volume writable. No offsite
upload, backup scheduler, whole-machine clone, strategy validation, game input,
or market-quote/recursive-recipe/cycle/margin work is in this slice.

The existing private manual snapshot at
`/home/dev/.local/state/crowley/market-backups/beta-20261017T061327Z` is preserved
unchanged. It is a legacy/manual custom-dump plus raw-tar artifact, has no v1
`COMPLETE` contract, and has no restore qualification. The new v1 commands must
not relabel or silently accept it as a canonical snapshot; recovery from it stays
manual and outside this implementation.

## Snapshot command and v1 layout

Resolve the actual Compose project, services, containers, mounts and volumes from
the checked-in deployment and private env file. Do not print env values,
`Config.Env`, DSNs or credentials. Record source commit and a deterministic
dirty-source fingerprint, exact database/server image IDs and digests, Compose
file digest, migration file digests, PostgreSQL server version and TimescaleDB
extension version. The source database is queried only for dump/version metadata;
no source row counts are acceptance expectations.

Create a new owner-only destination directory (mode `0700`); reject existing
destinations, symlinked path components and unsafe permissions. Snapshot files
and markers are mode `0600`. Create an empty `INCOMPLETE` marker before writing
snapshot data, then fsync the marker and directory. While `INCOMPLETE` exists,
partial files may coexist but the directory is never valid. The completed
canonical v1 directory contains exactly:

```text
database.dump              # PostgreSQL custom-format dump
raw.tar                    # preserved final raw archive objects
manifest.json              # canonical v1 manifest bytes
COMPLETE                   # published only after all prior files are durable
```

Use custom-format `pg_dump` against the existing database container, with
credentials supplied without password arguments or secret output. Dump the
database first. Then copy the immutable raw volume through a read-only mount;
ingestion atomically archives an object before its database reference can commit,
so a later copy may include extra final objects but cannot omit objects
referenced by the dump. Do not pause ingestion or delete source data. Preserve
compressed object bytes exactly. Include only final regular files, exclude
dot-temporary ingest files, do not follow symlinks, and emit no tar directory,
link, device or special-file members. Fail on any encountered symlink or special
file instead of following or silently skipping it.

The versioned manifest is a sanitized, local-only machine-readable record with
these exact required fields and no credentials or raw payloads:

- Top-level `schema="crowley.market-backup-manifest"`, `schema_version=1`,
  generated `backup_id`, and `created_at_utc` (RFC 3339 UTC with `Z`).
- `source`: `compose_file_sha256`, `compose_project`, `services` with `database`
  and `server` names, `containers` with `database` and `server` objects holding
  `id`, `image_id`, and `repo_digests`, `volumes` with `database` and
  `raw_archive` objects holding `name` and inspected `mountpoint`, `networks`
  sorted by name with `name` and `id`, `source_commit`, `dirty_tree_sha256`,
  `migrations` sorted by path with repository-relative `path` and `sha256`,
  `postgres_server_version`, and `timescaledb_extension_version`.
- `database_dump`: `path="database.dump"`, `format="postgres-custom"`,
  `size_bytes`, and lowercase SHA-256 of its exact bytes.
- `raw_archive`: `path="raw.tar"`, `format="tar"`, `size_bytes`, lowercase
  SHA-256 of its exact bytes, and `members`, sorted by UTF-8 path bytes. Each
  member has `path`, `size_bytes`, and lowercase SHA-256 of the original file
  bytes. Member paths are nonempty UTF-8 relative POSIX paths with no NUL,
  backslash, empty, `.` or `..` component; reject absolute, duplicate or
  non-regular members.

Serialize `manifest.json` as UTF-8 JSON with object keys sorted, compact comma
and colon separators, `ensure_ascii=false`, and no trailing newline. Hash the
exact serialized manifest bytes with SHA-256. `COMPLETE` is exactly
`crowley.market-backup-complete-v1 <manifest-sha256>\n`. The manifest does not
contain its own digest or the `COMPLETE` contents, so this binding is not
self-referential. `INCOMPLETE` is an empty sentinel. Fsync the dump, raw archive,
manifest and directory before preparing the marker. Fsync a temporary `COMPLETE`,
atomically rename it to `COMPLETE`, fsync the directory, remove `INCOMPLETE`, and
fsync the directory again. A snapshot is **complete backup bytes** only when the
manifest, every outer hash, every listed member, and the marker digest validate,
and `INCOMPLETE` is absent. Interrupted finalization (including both markers
remaining) is incomplete evidence, never a valid backup.

The v1 manifest validator rejects missing or unknown keys, duplicate JSON keys,
wrong field types, noncanonical bytes and non-lowercase/non-64-character SHA-256
values. Member `size_bytes` values are nonnegative integers; paths also reject
backslashes and NUL bytes.

For `dirty_tree_sha256`, hash canonical UTF-8 JSON for a path-byte-sorted list
of changed tracked and non-ignored untracked repository paths, each represented
by its path, `present`/`deleted` state and SHA-256 of current file bytes (`null`
for deleted paths), using the manifest JSON serialization rules above. Do not
store file contents or include private env files or ignored paths.
`manifest.json` is stored only in the owner-only snapshot directory; its
curated non-secret Compose/container/volume/network identifiers are not
credentials and are not part of any committed summary. Local absolute
mountpoints are private manifest/receipt fields and never appear in a sanitized
committed summary.

The manifest is structural: it contains no table/house/build/plan row counts or
reference/orphan claims. Those facts can only be derived from the restored dump
and belong in its bound drill receipt.

## Disposable restore drill

Require an explicit canonical v1 snapshot path. Before creating drill resources,
validate its directory and marker, canonical manifest, exact root entries, dump
and raw-tar outer hashes, and every raw member type/path/hash. Reject absolute or
traversing paths, duplicates, links, devices, FIFOs, unlisted members and missing
members. Do not create a target until this complete preflight passes.

Before any restore write, inspect and record current live Compose container,
network and volume identities, labels and mounts, and the source identities in
the manifest. Generate a fresh unique Compose project name internally; do not
accept a project/container/volume name from an operator or snapshot. Refuse any
existing project/resources for that name. Use an owner-only generated Compose
override (mode `0600`) that removes every host `ports` mapping from both database
and server, disables restart policies, and uses only fresh project-scoped
volumes on a private network. Inspect the resolved Compose configuration and
refuse to create resources unless it proves there are no host port bindings.
Parse that configuration privately and report only the relevant safe/unsafe
result; never echo the resolved config or its interpolated environment values.
Probe the API only from that private network; no ephemeral or fixed host port is
allowed. Generate drill-only credentials in a mode-`0600` temporary file.

Create only stopped disposable resources, then inspect the actual Compose labels,
services, mounts and identities before starting a container or writing restored
data. Require all drill container IDs, network IDs and volume names to be fresh,
correctly project-scoped, and
disjoint from both the current live identities and every source identity recorded
in the snapshot. Require the database target mount and raw target mount to be the
new disposable volumes; never accept destination identities from the snapshot.
Repeat ownership/disjointness checks immediately before starting the disposable
database; creating the drill database/extension; `timescaledb_pre_restore()`,
`pg_restore`, `timescaledb_post_restore()`, `ANALYZE`, raw extraction, server
startup, and cleanup. If identity cannot be proved, stop and do not restore or
broaden cleanup.

Use the locally available recorded database and server image IDs/digests; do not
pull images or require network access. Require exact PostgreSQL server and
TimescaleDB extension version equality with the manifest, and record target
image/version identities. The official migration guide requires matching major
versions; exact recorded-version equality is this drill's stricter offline pin.
Start only the disposable database first. Create a fresh database and enable
the TimescaleDB extension. Follow the official Timescale logical restore
sequence: run
`timescaledb_pre_restore()`, restore the custom dump with a **single-job**
`pg_restore` (no `-j`) using `--no-owner` so restored objects belong to the drill
role, then run `timescaledb_post_restore()` and `ANALYZE`. Capture PostgreSQL and
TimescaleDB versions from the restored database and compare them to the manifest.
The sequence follows [Timescale logical backup and restore](https://docs.timescale.com/self-hosted/latest/backup-and-restore/logical-backup/)
and [Timescale whole-database migration](https://docs.timescale.com/self-hosted/latest/migration/entire-database/).

Before starting the server, derive all acceptance counts from this restored dump,
never from a query against the changing live database. Record logical row counts
for every application table in the pinned migration set and `schema_migrations`
(not Timescale internal catalogs). Report the legacy `scans` and format-2
`market_sweeps` counts separately; group `scans` by `client_build`, `interface`
and house key, and `market_sweeps` by `client_build`, `interface`, house key and
`plan_hash`. Record the `houses` count/keys and `market_plans` count/full hash
set. Record the exact applied migration-name set and require it to equal the
basenames of manifest migration paths; verify those file digests against the
recorded server image. Store exact counts/group keys and plan hashes in the private
receipt; a committed sanitized summary may contain aggregate counts only. These
values are the restore-drill expectations, not snapshot-manifest claims.

Extract the validated raw tar only into the proven disposable raw volume. Convert
a database `raw_path` only when it starts with the exact container prefix
`/data/`; remove that one prefix and require the result to match one exact
inventory-relative member path. Reject every other prefix/path; never open a
database-provided arbitrary filesystem path. Enumerate references from both
`market_sweeps` and legacy `scans` in the restored database:

- For each format-2 `market_sweeps` row, require the referenced gzip to decode to
  a strict format-2 envelope. Recompute the current ingestion logical digest by
  replacing the envelope's compressed `payload` with its decoded payload, JSON
  encoding with sorted keys, compact separators, `ensure_ascii=false` and UTF-8,
then SHA-256. Require it to match `content_digest`, the digest-addressed filename
  `raw/format2/<first-two-hex>/<digest>.json.gz`, `sweep_uid`/envelope ID,
  house key, plan hash, client build, interface and the exact `/data/`-mapped
  `raw_path`. Require the envelope plan JSON/hash to match the restored
  `market_plans` row. Any missing or mismatched reference fails the drill.
- The legacy `scans.raw_path` format has no checked-in raw decoder/identity
  validator. If the restored dump has any legacy scan reference, fail the drill
  as `unsupported_legacy_reference`; do not validate it as format 2 or infer its
  payload format. Legacy rows remain in the dump and their format support is a
  separate future decision.
- Classify every unreferenced final raw member as an orphan only after all
  references have been resolved. Preserve and inventory it; it must never
  satisfy a missing reference. A valid format-2 orphan may be described as
  independently validated but remains an orphan. An invalid orphan may remain
  as warned evidence, but must not be described as a validated market object.

After base restore checks, start the server with the recorded compatible image
and drill-only configuration. Re-read the applied migration set immediately
after startup; any newly applied/unreviewed migration stops the drill before
the authenticated read probe. Run private-network `GET /healthz` and one
authenticated read-only `GET /v1/houses` request. Do not use upload or mutating
endpoints.

## Receipts, privacy and cleanup

Write a private receipt with `schema` = `crowley.market-backup-drill-receipt`,
`schema_version` = `1`, snapshot `backup_id`, exact manifest SHA-256, result
(`restore_verified`, `failed` or `blocked`), UTC start/end, target versions,
table/group counts, migration comparison, reference/orphan classifications,
API probe result and cleanup outcome. Its target section holds exact drill
project/service/container/network IDs, volume names/mountpoints, labels and
image identities. Each reference result records source table/row identity,
inventory path, member SHA-256 and logical validation result; each orphan records
inventory path, member SHA-256, validation state and warning if invalid. Its
operations list contains only fixed operation names and exit states (never
interpolated command lines): `validate_snapshot`, `create_disposable_resources`,
`start_disposable_database`, `create_database_extension`,
`timescaledb_pre_restore`, `pg_restore_single_job_no_owner`,
`timescaledb_post_restore`, `analyze`, `count_restored_tables`,
`extract_raw_archive`, `validate_raw_references`, `start_server`, `health_probe`,
`authenticated_read`, and `cleanup_owned_resources`. Keep this receipt and
operational logs in mode-`0700` local state with files mode `0600`. Generated
Compose overrides and credential files are mode `0600`; delete the drill
credentials on every exit. The receipt validator also rejects unknown/missing
fields, duplicate JSON keys and wrong types. Never log or persist environment
values, DSNs, bearer tokens, generated passwords, container
`Config.Env`, raw market payloads, or secrets in command arguments.

Any committed summary is separately sanitized with `schema` =
`crowley.market-backup-drill-summary`, `schema_version` = `1`, snapshot ID and
manifest digest, result, aggregate table/regime counts, aggregate
referenced/orphan totals, version-match result, fixed operation statuses and
cleanup result only. Exclude exact local
paths, source/drill container and volume IDs, mountpoints, group keys, member
paths, plan hashes, credentials and market payload content.

Cleanup only the exact drill IDs recorded and positively re-verified as belonging
to the generated project, with expected labels and mounts. If ownership has
changed or is ambiguous, do not remove anything; report the blocker. Preserve the
backup and failed restore evidence. Never delete a live/source resource, raw
object or unrelated Compose project/volume. A receipt is `restore_verified` only
when dump-derived counts, versions, migrations, references, health/API checks and
verified cleanup all pass. Keep beta history partitioned by exact house,
build/interface and plan; never rewrite beta labels into launch history.
Controller/input gates remain disabled until fresh launch qualification.

## Verification

Use meaningful tests for canonical manifest and marker hashes, incomplete or
changed snapshots, unsafe/missing/extra archive members, raw-path prefix checks,
format-2 identity/digest matching, unsupported legacy references, orphan
classification, derived-count provenance, no-host-port isolation and
mistaken-live-target refusal. Run one real disposable drill from a newly created
read-only production snapshot after unit checks. Never use the existing manual
snapshot as proof of the v1 restore path. Acceptance is a successful bound
`restore_verified` receipt, not merely a successful `pg_dump`.
