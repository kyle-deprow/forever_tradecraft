# Sol schema closure review — identity latency barriers

Candidate reviewed: `/home/dev/.cache/crowley/worktrees/identity-latency-schema-20261018`

## Identity and scope

- Closure plan SHA-256 verified: `2c5c3e3ae50529e7ab1c37943ee5a9121e82f8e5d5df9590e2634c399e19187f`.
- Prior Sol finding input SHA-256 verified: `056d57442335c47a57f2845d836628991e39307dc6518bef8f590d127759a403`.
- All four candidate hashes and all six read-only baseline hashes match `identity-latency-schema-freeze.json` exactly.
- `src/crowley/session/driver.py` and `src/crowley/session/daemon.py` are byte-identical to the prior frozen final tree. The repair delta against that tree is confined to `tools/gnome-telemetry-region/identity_latency_sidecar.py` and `tests/test_session_native.py`; the worktree has no additional repair-owned change or untracked path.
- The existing parent expected-binding manifest remains valid: its source binding does not include the changed sidecar or test, and its frozen driver/daemon plus five `f213e1f` read-only source hashes are unchanged.
- I reviewed only this repair delta and did not rerun tests, builds, or live actions. The frozen evidence records 10 focused identity-latency tests passing, and the worker's scoped Ruff, format, and diff checks passing.

The repair closes the sole accepted finding. At `tools/gnome-telemetry-region/identity_latency_sidecar.py:401-412`, the validator now requires the original barrier dictionary to contain exactly `barrier`, `start_monotonic_ns`, `end_monotonic_ns`, `duration_ns`, and `outcome` before any field is indexed. Unknown fields therefore cannot survive validation into the sanitized report, and every missing required field raises `IdentityLatencyError` rather than `KeyError`.

The regression at `tests/test_session_native.py:232-317` writes real complete and partial artifacts and confirms both still pass through `read_response_profile` and `build_report`. It then persists barriers containing `path` and `error`, plus separate artifacts missing each required key, and verifies direct typed rejection, `artifact_invalid` through both report paths, null sanitized barriers, and absence of the raw injected values.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
