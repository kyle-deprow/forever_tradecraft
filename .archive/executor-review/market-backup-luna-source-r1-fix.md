# Market backup source R1 fixes

Candidate checked against canonical plan SHA-256
`a2df7c21dfe4b20a620084264743c1b62d2014e2b5f660e61caa5f912e969b8f` and source
review SHA-256
`7050ffdcd66aee704af4ce5b5677d191651fc3d67460f3d5441fbd1cd5e1c77b`.

## Changes

- Snapshot container, volume, and network identities remain provenance and
  collision deny sets. Restore compatibility still checks Compose and migration
  digests, image IDs/digests, PostgreSQL and TimescaleDB versions, and pinned
  server-image migrations. Current source identities remain frozen and rechecked
  during the drill.
- Resolved Compose configuration and inspected targets require the recorded
  database/server images, exactly one expected mount per service, two distinct
  project volumes assigned to database/raw roles, and one private project
  network. Extra mounts and collisions with current or historical source
  identities fail closed.
- The create-attempt state is set before Compose runs. If creation or discovery
  fails before a complete target inventory is captured, cleanup remains blocked
  and leaves uncertain resources untouched. Cleanup of a captured target checks
  ownership before writes, verifies each removal by re-inventory, and records
  only the confirmed removed subset.
- Receipt validation now checks nested target, count, migration, API, and logical
  reference fields. `restore_verified` requires all 15 operations to pass,
  restored-dump counts and complete migration/reference evidence, exact target
  and helper inventory, both API probes, and verified cleanup of every recorded
  resource.
- Recovery documentation describes compatibility IDs, target mount/image
  checks, and blocked cleanup after partial creation.

## Validation

- `uv run pytest -q tests/test_market_backup.py`: **88 passed**.
- Scoped Ruff check and format check: **passed**.
- `uv run python -m compileall -q tools/market_backup.py tests/test_market_backup.py`:
  **passed**.
- No Docker operation, snapshot, restore, or live-source write was run in this
  correction round. The prior private success receipt was not modified; its SHA-256
  remains `158f36e0e71aaa54b156b62d70d90f56dd949e88f8add9116e6154507be77864`.

Updated file SHA-256 values:

- `tools/market_backup.py`: `56f4a37bc981ab3379d364b00c29e57fe030bd6e0c8850e22fc81d72c413b939`
- `tests/test_market_backup.py`: `8334fb5b7bdae9f53641b5718fa35a35b9fc951b7d36f9823a6006b96fb1b5b3`
- `docs/MARKET_RECOVERY.md`: `ae096f23fea26d9f14960bc61c5bc9d6e38b857032aa3e295ec0401be1483509`

## Review gate and known limits

This is a source candidate, not new restore qualification. The canonical plan
requires parent reproduction and Sol source re-review before another disposable
drill. The older private receipt remains byte-for-byte unchanged; the stricter
receipt validator is not used to rewrite or relabel that historical evidence.
When Compose fails after partial creation or target discovery is ambiguous,
resources may remain for a later, positively identified cleanup; the receipt
reports cleanup blocked instead of claiming absence.

STATUS: READY FOR SOL R2 SOURCE REVIEW
