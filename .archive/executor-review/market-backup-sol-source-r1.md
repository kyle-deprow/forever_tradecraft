# Market backup source review R1

Reviewed the implementation against canonical plan SHA-256
`113504002b81c877e5dc65bfa97c94806dd7ab57258fad1270b06942d7d2e924`
and the prior READY plan review. The reviewed source hashes are:

- `tools/market_backup.py`: `0b63d82f55facbbd5783c900e2a4fd5a02ac2302f789d34db04c443bff081b87`
- `tests/test_market_backup.py`: `102ef606df722ff25b8292149f2930fe3138f0f93202f8329995a856c9f6f377`
- `docs/MARKET_RECOVERY.md`: `4281408a819ba0d64526f7ad345c17bc3b1a1a640e3bdee070aad42b7b840ea9`

I also checked the permitted private receipt at SHA-256
`158f36e0e71aaa54b156b62d70d90f56dd949e88f8add9116e6154507be77864`.
It is owner-only (`0700` directory, `0600` file), says `restore_verified`,
records all 15 operations as passed, matches PostgreSQL 16.6 and TimescaleDB
2.17.2, binds 12 format-2 references with no orphans, passes both API probes,
and records cleanup of four containers, two volumes, and one network. That is
valid happy-path evidence. The parent separately reproduced 53 unit tests; this
review did not run tests, Docker, a restore, the application, or Git.

## Must Fix

1. **`tools/market_backup.py:2210-2222` makes historical Docker resource IDs an unintended compatibility requirement.** The drill rejects a snapshot whenever the current source containers or network have been recreated, even when the current Compose digest, migrations, image IDs/digests, PostgreSQL version, and TimescaleDB version all match. Container and network IDs normally change across a Compose recreation, so this can make a sound recovery snapshot undrillable after exactly the kind of lifecycle event a recovery tool must tolerate. It also contradicts the plan's distinction between “current live identities” and “every source identity recorded in the snapshot” (`PLAN-market-backup-restore.md:124-143`) and the documented compatibility list (`docs/MARKET_RECOVERY.md:31-35`). Remove ID/name equality from compatibility. Continue to freeze and recheck the current live source identities during one drill, and retain the recorded snapshot IDs/names as a second deny set so every disposable resource must be disjoint from both sets. Add a test near `tests/test_market_backup.py:362-381` proving that changed container/network IDs with otherwise exact compatibility are accepted, while a target collision with either the current or recorded set is rejected.

2. **`tools/market_backup.py:1003-1027` and `tools/market_backup.py:1287-1355` do not prove the actual target uses only the recorded images and the two intended disposable mounts.** The resolved-config check pins image strings, but the initial actual-container guard never compares `container["image_id"]` with the recorded database/server image ID. Its mount check selects one expected destination while ignoring additional bind, volume, or other mounts, and it does not require the database and server to use distinct members of the exact two-volume target set. A target can therefore be frozen as the expected identity and later pass every repeated guard while carrying an unrecorded image or an extra/live mount. Require each inspected target container's actual image ID to equal the corresponding recorded image, require its complete mount inventory to be exactly the one expected project volume at the expected destination, require the database/raw volume names to be distinct and equal the two recorded target-volume names, and reject every extra mount. Extend `tests/test_market_backup.py:384-430` with valid-target, wrong-image, shared-volume, extra-volume, and extra-bind cases.

3. **`tools/market_backup.py:2260-2285` and `tools/market_backup.py:2511-2528` can report cleanup as passed after a partial `docker compose create` leaves resources behind.** `target` remains the empty placeholder if Compose creates some resources and then returns failure, or if `_target_ids()` fails while discovering the created set. The `finally` block skips `_guard_current()` when `target["containers"]` is empty; `_remove_owned()` then receives empty lists, returns `True`, and the receipt records `cleanup_owned_resources=passed` with `cleanup.verified=true`. Track whether creation was attempted. After such a failure, either discover and positively verify the exact newly project-labelled resources against the pre-create inventory before removing them, or leave them untouched and record cleanup as blocked. Never treat an empty captured inventory as verified cleanup after creation began. Also verify absence after successful removals and retain the exact confirmed removed subset on partial cleanup failure. Add orchestration tests that simulate command failure after partial resource creation and discovery failure after successful creation.

4. **`tools/market_backup.py:1956-2096` validates receipt shape but not the meaning of `restore_verified`, and several nested values are not type-checked.** A receipt with `result="restore_verified"` is currently accepted with every operation `not_run`, version/migration/API/cleanup checks false, empty counts, and an empty target. Target IDs, labels, mounts and networks, grouping rows, migration-list elements, and logical-reference fields can also have arbitrary nested types. This is weaker than the promised wrong-type rejection and allows the final publication gate to bless internally inconsistent recovery evidence. Enforce success invariants: all 15 operations passed; version and migration matches true; expected/applied migrations equal; restored-dump counts present; both API probes true; cleanup verified; the exact target resource inventory present; and every reference logically typed and valid. Validate nested identity and evidence fields for all results while allowing explicitly partial fields for `failed`/`blocked`. Replace the shallow test at `tests/test_market_backup.py:677-688` with positive complete-receipt coverage and mutations for each success invariant and representative nested wrong types.

## Should Fix

None beyond the bounded corrections and regression tests above.

## Nits

None.

The snapshot publication order, strict manifest/tar validation, Timescale restore sequence, restored-database count provenance, format-2 identity checks, legacy fail-closed behavior, fixed failure categorization, credential removal on the exercised path, and private successful receipt are otherwise consistent with the reviewed contract.

STATUS: NEEDS WORK
