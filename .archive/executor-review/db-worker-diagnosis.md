# DB-enabled test setup race (2026-10-16)

Sol read-only diagnosis identified Timescale scheduler/telemetry vs per-test DROP SCHEMA public CASCADE. Failure occurred before TestClient lifespan. Container logs correlate locked OID63760 and scheduler/telemetry processes; current activity contains no leaked Crowley application backend. App lifespan closes its pool. No production source/fixture change warranted.

Dedicated final ephemeral container crowley-executor-tests-final-20261016 uses timescale/timescaledb:2.17.2-pg16, tmpfs data, loopback15434, postgres -c timescaledb.telemetry_level=off -c timescaledb.max_background_workers=0. This preserves synchronous extension/hypertable/policy registration/inserts/queries exercised by the suite, while disabling scheduled job execution (not verified by these tests). Production data/settings untouched. Container must be removed after final testing; original disposable port15433 retained until cleanup too.

Sources inspected by Sol: https://docs.timescale.com/self-hosted/latest/configuration/timescaledb-config/ and https://docs.timescale.com/self-hosted/latest/configuration/telemetry/ . Requested gpt-5.6-sol; independent runtime ID not established.
