# Market backup source review R2

Reviewed the bounded three-file candidate against canonical plan SHA-256
`a2df7c21dfe4b20a620084264743c1b62d2014e2b5f660e61caa5f912e969b8f`, the R1
source review, and the Luna R1 fix report. The reviewed source hashes are:

- `tools/market_backup.py`: `56f4a37bc981ab3379d364b00c29e57fe030bd6e0c8850e22fc81d72c413b939`
- `tests/test_market_backup.py`: `8334fb5b7bdae9f53641b5718fa35a35b9fc951b7d36f9823a6006b96fb1b5b3`
- `docs/MARKET_RECOVERY.md`: `ae096f23fea26d9f14960bc61c5bc9d6e38b857032aa3e295ec0401be1483509`

The R1 review SHA-256 was
`7050ffdcd66aee704af4ce5b5677d191651fc3d67460f3d5441fbd1cd5e1c77b`; the
Luna fix report SHA-256 was
`7c397c3f74dd8fadd4abe68ed314959e95378b3f2de76651c61a2090220fc915`.
I did not run tests, Docker, a restore, the application, the network, or Git, and
did not reread or modify the preserved private receipt.

The four R1 must-fixes are closed:

1. `tools/market_backup.py:1654-1668` limits compatibility to Compose,
   migrations, versions, image identities, and pinned-image migrations, while
   `tools/market_backup.py:2692-2729` retains historical resource identities as
   a separate collision deny set. `tests/test_market_backup.py:365-389` and
   `tests/test_market_backup.py:511-545` cover historical-ID drift and collisions
   with both current and historical sets.
2. `tools/market_backup.py:992-1037` validates the resolved Compose images and
   complete mount definitions, and `tools/market_backup.py:1298-1410` checks the
   inspected images, exact one-mount-per-service inventory, distinct volume
   roles, and exact network membership. The wrong-image, shared-volume,
   additional-volume, extra-bind, and swapped-role regressions are covered at
   `tests/test_market_backup.py:548-574`.
3. `tools/market_backup.py:2522-2554` records the creation attempt before Compose
   runs and refuses verified cleanup without a captured target. Cleanup at
   `tools/market_backup.py:2557-2682` proves all ownership before removal,
   re-inventories after each removal, verifies final project absence, and retains
   only confirmed removals. `tests/test_market_backup.py:580-675` and
   `tests/test_market_backup.py:714-754` cover complete, partial, stuck,
   create-failure, and discovery-failure outcomes.
4. The nested receipt validators at `tools/market_backup.py:2039-2487` reject
   malformed target, count, migration, reference, API, operation, and cleanup
   evidence. `restore_verified` requires all operations passed, exact versions
   and migrations, restored-dump counts, complete references and target
   inventory, both probes, and exact verified cleanup. The complete receipt and
   mutation regressions at `tests/test_market_backup.py:1001-1225` exercise those
   gates.

`docs/MARKET_RECOVERY.md:31-49` now describes the intended compatibility/deny-set
split and exact actual-target checks; `docs/MARKET_RECOVERY.md:67-80` describes
the fail-closed partial-creation cleanup and strict success receipt semantics.
The source is ready for the separately required new disposable drill. The prior
receipt remains historical evidence and does not need to validate under the new
stricter schema implementation.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
