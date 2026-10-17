# Sol build-70450 plan review r1

The proposed in-memory release identity reproduces exactly from the current catalog with only `revision=2`, `client_build=1.60.1.70450`, and `reviewed_on=2026-10-16`: catalog hash `90918db5cc912e889553b5ddd422b829f3c6cb3773ab6da56a2e79a5a8db04f3`, plan hash `f1745d85c071b350ebea242add2a7b38e3f53df5bcc8a6df1f19002f995a31d4`, and counts 544/428/74/42 with 352 core and 76 discovery. The named watchlist, probe, scan, companion, and authenticated plan-endpoint commands exist. The strict exact-build gate, historical plan retention, existing targeted-sweep qualification, and no-runtime-parity-claim boundaries are otherwise coherent.

## Must-Fix

1. **The cutover says to restart the server, but the deployed server packages the catalog into a Docker image.**

   `.archive/PLAN-build-70450.md:46` requires a server restart to clear `load_catalog()`'s cache. A restart alone reuses the existing image. `deploy/Dockerfile:5-8` copies `src/` into the image at build time, and `deploy/docker-compose.yml:21-24` builds that image without a source bind mount. Therefore a plain restart can start a fresh process whose packaged `first_run.json` is still revision 1/70425. The authenticated `/v1/scan-plan` endpoint at `src/crowley/server/app.py:342-344` would continue returning the old plan, and the companion would write that old plan into `Data.lua`, preventing an atomic matching 70450 cutover.

   Change the delivery step to rebuild and redeploy the reviewed server image, for example the repository's existing non-destructive command `docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d --build server`, wait for health, and only then verify authenticated `/v1/scan-plan` returns the exact revision-2 build/hash/JSON. This new process also clears the `load_catalog()` LRU cache at `src/crowley/core/watchlist.py:128-131`. Do not use `down -v` or otherwise touch the database volume.

2. **The exclusive file fence omits the shipped session profile example, which will become invalid under the catalog-derived build.**

   `deploy/crowley-session.example.toml:11` still pins `client_build = "70425"`, and `docs/REPEATING_SCANS.md:67-73` directs operators to copy that file. After `first_run.json` moves to 70450, `src/crowley/session/config.py:17` derives 70450 as canonical and `src/crowley/session/config.py:113-119` rejects the copied example's 70425 value. The current owned-file list at `.archive/PLAN-build-70450.md:27-36` does not permit correcting it.

   Add `deploy/crowley-session.example.toml` to the fence for the single `client_build` literal change from 70425 to 70450. Keep interface, version, plan count, timing, paths, and commented plan fields unchanged. Include this literal in the source diff review; the private installed profile remains a separate cutover edit populated with the exact exported hash and compact `planJSON`.

## Should-Fix

1. **The README's “Current local deployment” statement would remain a conflicting current-build claim.**

   `README.md:71-79` labels the deployment current but says the live client is build 70374. The documentation fence updates `REPEATING_SCANS.md`, `WATCHLIST.md`, and `HANDOFF.md` only. Once the cutover and qualification evidence exist, either add `README.md` to the documentation fence for the verified 70450 state or relabel the dated 70374 section as historical. Do not rewrite it as a successful 70450 deployment before the real sweep, strict ingestion/ACK, and later cadence evidence have passed.

## Nits

None.

STATUS: NEEDS WORK
