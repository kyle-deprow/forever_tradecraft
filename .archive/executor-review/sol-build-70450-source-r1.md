# Sol source review: build 70450 r1

Reviewed the 13-path frozen release-identity diff against the authoritative plan. I did not run tests, operate the game, inspect private configuration, deploy services, or re-audit scanner/query/runtime behavior outside this release update. The supplied validation result is 241 passing and 23 failing across the planned files; all reported failures are the known global Codex CLI 0.163.0 versus required 0.162.1 startup mismatch and lease cascade. This is not a full green-suite, deployment, or live scanner qualification claim.

## Must-Fix

None.

## Should-Fix

1. **The runtime-gate test no longer independently verifies the client-version component of the exact release tuple.** At `tests/test_addon.py:1693`, the `unknown-version` row supplies `("9.9.9", "70425", 16001)`. Since 70425 is now independently noncanonical, that row still rejects if the production version comparison at `addon/Crowley/Scanner.lua:233-234` is accidentally removed. The preceding `previous-client-build` row already covers 70425. Change the unknown-version row's build to `70450`, leaving version as `9.9.9` and interface as 16001, so each dimension of the exact `1.60.1` / `70450` / `16001` tuple is tested in isolation. The production gate is correct today; this is a reachable regression hole in the release-identity test matrix.

## Nits

None.

The remaining bounded release update matches the plan. `src/crowley/data/first_run.json:4-6` changes only revision, client build, and review date, while the supplied comparison confirms all 544 item objects are identical. `addon/Crowley/Scanner.lua:16-25` carries the reviewed plan/catalog hashes and revision 2 build identity, and `addon/Crowley/Scanner.lua:172-182` now serializes `CANONICAL_REVISION`, producing the same revision used by the strict plan checks. The encoded 428-entry plan remains unchanged, and the supplied exports match catalog hash `90918db5cc912e889553b5ddd422b829f3c6cb3773ab6da56a2e79a5a8db04f3` and plan hash `f1745d85c071b350ebea242add2a7b38e3f53df5bcc8a6df1f19002f995a31d4`.

The prior-build row at `tests/test_addon.py:1692` rejects 70425 before scheduling or querying, current session fixtures use 70450, and the historical 70425 format-2 envelope in `tests/test_session_regressions.py:713-807` remains intentionally preserved. The shipped-plan test pins revision, build, hashes, and all release counts. The README labels the 70374 deployment as historical, and the WATCHLIST adoption note explicitly limits its claim to reviewed release identity pending coordinated publication and live qualification. The example profile and repeating-scan documentation carry the new build without claiming that private cutover, deployment, or scanner qualification has occurred.

STATUS: NEEDS WORK
