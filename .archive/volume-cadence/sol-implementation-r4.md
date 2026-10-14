## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

All accepted round 3 findings are resolved in the current implementation:

- Pre-owned global sweep timeouts now retain `unqueried/not_started`.
- Cumulative duplicate rows compare owner names, counts, grouping flags, and identity kind while allowing time-left changes.
- Invalid house-setting values leave active sweeps and settings untouched.
- History and volume projections share numeric `row:<n>` ordering and contiguous projected ordinals.

The added strict Lua-envelope, pure projection, and database route regressions cover these behaviors. I found no concrete regression in the seven-file final fix set. Documented live-client event and identity assumptions remain beta assumptions rather than implementation defects.

STATUS: READY
