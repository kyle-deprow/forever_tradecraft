The accepted round 2 fixes are otherwise present: documented API signatures, paging, depth/witness handling, numeric safety, strict validation, owned abort states, variant transitions, hidden owners, and documentation now match revision 4.

## Must-Fix

1. **The global sweep timeout still claims an owned query that never began.**
   `addon/Crowley/Scanner.lua:625-632` calls `failCurrent`, then unconditionally creates `state.owned` as `queried/incomplete/sweep_timeout` when the 600-second timer expires. During a market-item or metadata wait, `beginOwned` has never run, so revision 4 requires `unqueried/not_started`. This preserves the residual round 2 owned-state defect despite the corrected `Abort` path. Only create an incomplete owned batch when owned collection was entered; otherwise let `Scanner.Finish` supply its unqueried default. Extend `tests/test_addon.py:475-492` to strictly assert the owned object for a pre-owned global timeout.

2. **Cumulative paging can discard contrary owner/grouping evidence and emit unsafe individual identity.**
   `addon/Crowley/Scanner.lua:343-352` captures owner names, count, grouping flags, and `identityKind`, but `sameRow` at `:356-363` ignores all of them. Consequently, `collectResults` at `:365-381` accepts an earlier individual row when a later cumulative page exposes that result ID as grouped or unknown. The final observation can remain `full/ok` and later support a false disappearance candidate, violating the rule that any contrary grouping evidence excludes individual inference. Compare the complete owner/grouping identity for repeated result IDs and classify conflicts as `identity_mismatch` incomplete; do not compare naturally decreasing time-left values. Add cumulative-page regressions for individual-to-grouped and grouped-to-individual changes under one stable result ID.

## Should-Fix

1. **Invalid house-setting commands abort active sweeps before validation.**
   `addon/Crowley/Commands.lua:34-49` calls `Scanner.Abort("house_changed")` before checking whether the supplied value is valid. `/crowley set faction goblins` therefore saves a partial sweep labeled `house_changed` even though no setting changed. Normalize and validate the value first, then finalize an active sweep immediately before applying an accepted override. Add a delayed-query regression proving an invalid value leaves the sweep running and settings unchanged.

2. **History projection still relies on JSON object iteration order.**
   `src/crowley/server/app.py:90-102` filters `observation["rows"].values()` and assigns new ordinals in that iteration order. Revision 4 requires numeric `row:<n>` interpretation, and arbitrary decoded/JSONB mapping order can reorder the projected price ladder. Reuse `project_observation_variant` or explicitly sort original keys by numeric ordinal. Add a projection regression with at least `row:1`, `row:2`, and `row:10` inserted out of order.

## Nits

None.

STATUS: MAJOR ISSUES
