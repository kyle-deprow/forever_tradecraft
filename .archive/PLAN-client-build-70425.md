# Refresh the installed Forever beta build

The existing client could no longer reconnect. A normal quit, verified zero
clients and one Play through authenticated Battle.net triggered its automatic
update from 1.60.1.70374 to 1.60.1.70425. Luna verified the new client and character
select. This is an installed-client change, not permission to accept multiple
builds or weaken the strict wire/plan contract. Controller remains inactive.

## Scope and order

Wait until the main engine review finishes before editing its frozen config/tests.
One Luna implementation worker then owns only:

- src/crowley/data/first_run.json
- src/crowley/session/config.py
- addon/Crowley/Scanner.lua
- deploy/crowley-session.example.toml
- tests/wow_harness.py
- tests/test_addon.py
- tests/test_session.py
- tests/test_session_evidence.py
- tests/test_session_runtime.py
- tests/test_session_regressions.py

Refresh the catalog target build only; preserve all 544 entries, exact 428 active
IDs, pools, depth20, cadence900 and cap600. Generate the new canonical plan bytes
and SHA-256 through the existing catalog code. Update the scanner's exact canonical
build/hash binding and current-client test fixtures; never edit historical scan
archives, stored sweeps, SavedVariables or their recorded build/hash. Session build
defaults and strict comparisons should derive the one expected short build from
the source catalog, avoiding another independent stale literal. Keep version1.60.1
and interface16001 only after actual new-client verification. Reject70374 under
the new runtime profile; retain generic historical format-2 validation unchanged.

No native driver/controller/protocol changes in this batch. If live evidence shows
an API/wire change, stop this scoped implementation and report the exact contract
for a separate reviewed fix. No fallback to old builds or alternative formats.

## Checks and deployment

Test canonical JSON/hash/body binding, exact new build acceptance and old/malformed
runtime build rejection. Run addon, session, evidence, runtime, and independent
regressions with strict thread/unraisable/fork warning errors; Ruff/format/diff.
Parent reproduces and Sol reviews the frozen change. No database schema changes.

After review, the sole deployment operator rebuilds/restarts only the API server
using the existing authorized compose env-file, verifies health, and lets the
companion publish the new canonical Data.lua. Update the private session profile
atomically with new short build and generated exact plan JSON/hash; preserve0600.
Restage the final user unit while it remains inactive until calibration. Verify
all three catalog/API/Data/profile plan identities agree before enabling Crowley
in a measured fresh boot. Existing eight accepted historical sweeps remain intact.

Manual setup may proceed independently using normal menus, with Crowley disabled,
Arthur stationary in Ironforge and AH closed. Then measured construction/update,
actual human calibration, three new cadence/latency-qualified sweeps and durable
repeat-mode acceptance remain required. Nothing in this build refresh counts as
live performance or scanning proof.

## Review correction

Sol verdict NEEDS WORK: the canonical plan target is checked, but the scanner
does not compare it with actual GetBuildInfo() before scheduling/starting. The
real harness can run the70425 plan on an actual70374 runtime and dispatch a query.
Add one exact runtime version/build (and pinned interface) admission check through
the common validated-plan path. Test unchanged canonical plan with old/unknown
runtime values; assert no timer/start/query. No accepting old builds or weakening
the plan-body/hash checks. Only Scanner.lua and test_addon.py need change.

## Final review and independent check

Sol final verdict READY, no findings. Actual GetBuildInfo admission rejects old
build, unknown version/build and wrong interface before timer/start/query. The
manual diagnostic client_invalid maps to the existing wire-valid plan_invalid
blocked reason; real Agent publication bytes decode correctly in all4 cases.
Sol addon107 and focused4 passed; parent addon/session/evidence130 passed in
20.39s with strict warning filters. Canonical plan remains5063bytes, hash
25b596810724d79e702fc4e6bd9ff5fb6d1238f2254b066d00f95625f1c88e56.
Reviewed Scanner SHA256 b247f89272b64e3aaef75c4d493ac32a02a8833c932f81cf201a365dcbe976ae.
Build refresh may now be staged while controller remains inactive. This does
not clear native/controller corrections or establish actual interface telemetry.

## Staged deployment verified

Only the API server was rebuilt/recreated with the authorized compose env-file
and --no-deps. Health is ok and authenticated /v1/scan-plan exactly matches the
source catalog. The companion was restarted normally and published matching
Data.lua with zero acknowledgements; its8historical uploaded UIDs remain.
The private profile was atomically replaced/fsynced at0600 with only client_build,
plan_hash and plan_json changed, and successfully reloaded by production config.
The user unit was restaged/daemon-reloaded. Source/API/Data/profile agree on
build70425 and the reviewed plan hash. Controller stays inactive and disabled.
Crowley remains disabled in the running game; no reload, input, calibration or
new scan occurred as part of this deployment.
