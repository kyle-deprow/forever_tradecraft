# Market backup and restore plan R2 — Sol review

Reviewed the canonical plan at SHA-256 `113504002b81c877e5dc65bfa97c94806dd7ab57258fad1270b06942d7d2e924` against the four R1 must-fix findings and the receipt-privacy should-fix. This was a bounded, read-only plan review; no backup, restore, database, runtime, game, test, or source-control operation was performed.

## Must Fix

None.

The four prior blockers are closed:

1. Restored-state facts are no longer inferred from a changing live database or embedded as manifest claims. The manifest is explicitly structural (`PLAN-market-backup-restore.md:112-114`), while every application-table count, the migration set, legacy/format-2 split, and build/interface/house/plan grouping are derived from the disposable restored database and bound to the private receipt (`:166-177`, `:250-265`).
2. The restore lifecycle now creates the database and extension, invokes `timescaledb_pre_restore()`, runs single-job `pg_restore --no-owner`, invokes `timescaledb_post_restore()`, and runs `ANALYZE` before validation and server startup (`:151-177`). The migration set is rechecked after server startup and before the authenticated read probe (`:206-211`).
3. The target is positively isolated: a non-operator-selected fresh Compose project, a private generated override with no host ports or restart policy, fresh project-scoped volumes/network, resolved-configuration inspection before creation, and repeated identity/disjointness checks before every mutating phase and cleanup (`:118-149`, `:246-250`). The plan does not use fixed or ephemeral host ports.
4. The v1 snapshot now has one canonical layout and publication protocol, canonical manifest and marker bytes, outer and member digests, strict archive-member/path validation, exact `/data/` mapping, format-2 identity checks, explicit orphan handling, and fail-closed legacy-reference handling (`:37-99`, `:179-205`). The pre-existing manual snapshot remains preserved and explicitly cannot qualify this path (`:20-25`, `:262-264`).

## Should Fix

None.

The private receipt has a fixed typed scope, stores exact operational identities and restored evidence only in owner-only local state, forbids secrets and interpolated command lines, deletes drill credentials on every exit, and defines a separate sanitized committed summary that excludes local paths, resource IDs, group keys, member paths, plan hashes, credentials, and payloads (`:213-244`).

## Nits

None.

STATUS: READY
