# Anchor and motion deadline closure

Root owns this API contract. Actual stack traces in composition Round8 show
unbounded motion identity lookups and anchor measurement/sealing. Preserve all
existing native/Guardian/freshness/receipt guards and two-argument anchor providers.
No provider signature introspection, TypeError compatibility retry or new fallback.

Driver producer (Luna suite_implement):
- Own only driver.py and test_session_driver_actions.py for this round.
- Expose read-only DesktopDriver.anchor_observation_deadline -> float | None.
  It is a thread-local inherited absolute bound during each measured-anchor
  provider invocation, both initial measure_pointer_anchor and refresh.
  Nested scopes intersect with the prior bound; restore it on return/exception.
- build_measured_anchor accepts optional deadline_monotonic and intersects it
  with the active anchor-observation bound before its identity lookup/sealing.
  Reuse that same absolute bound, validate expiry before/after blocking work,
  and pass it explicitly to resolve_identity. Never renew it.
- Legacy calls outside an active bounded operation retain optional-None behavior.
  Real bounded provider invocations and their builders inherit the original bound.
- Keep provider(identity, action) unchanged. No pointer_execution.py edits.

Daemon/motion consumer (Luna mail_design):
- Own daemon.py, motion.py and existing owned runtime tests; additionally release
  test_session_executor_movement.py and test_session_motion_integration.py ONLY
  for strict motion identity callback API updates and targeted deadline oracles.
- NativeMotionProvider identity callback now accepts keyword deadline; observe
  supplies its own fixed absolute deadline, checks after identity and capture,
  and rejects expiry before any following operation. Update every constructor
  callback, including daemon's lambda and the narrow test fixtures. No no-arg
  compatibility fallback. Existing capture_with_deadline API remains unchanged.
- Daemon initial executor measure_pointer_anchor passes the actual current
  serialized operation deadline explicitly.
- Builtin _measure_pointer_anchor intersects its own five-second bound with
  driver.anchor_observation_deadline before its FIRST identity lookup; all
  identity/capture/model/sealing work uses that same intersection. Pass it to
  build_measured_anchor. Configured provider callbacks remain unchanged.

Verify bounded initial/refreshed provider and builder queries, nested/exception
scope restoration, expired identity preventing capture, and actual composition
all nested calls. Keep standalone legacy None tests. All pytest holds shared
flock/pinned CARGO with unique full exit/count/time logs; no direct native test
execution around the lock. Static checks then freeze actual final candidates.

Producer readiness (driver worker may update ONLY these lines):
- API implemented: complete (driver Round8 final SHA 56e0f89a3b508b041165574903337b49b7d8a0d728e5ad59027fed895e9944ba)
- Static checks: complete (scoped Ruff, format, compile, diff-check; final64 focused tests pass in3.18s)
