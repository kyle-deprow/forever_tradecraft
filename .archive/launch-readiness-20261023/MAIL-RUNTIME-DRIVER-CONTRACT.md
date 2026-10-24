# Mail runtime / driver absolute deadline contract

Root owns this API contract. Runtime Luna owns daemon/controller/CLI/model and
mail tests. Deadline Luna owns driver.py plus narrow driver_actions and
pointer_execution deadline regressions after explicit source release. Preserve
the existing partial driver edits and all reviewed guarded-click behavior.
Workers use this file instead of depending on peer messaging availability.

Required additive keyword-only API:

```python
DesktopDriver.run(name, generation, *, precondition=None, postcondition=None,
                  deadline_monotonic=None, **kwargs)
DesktopDriver.prepare_command(generation, command, telemetry, *, readback=None,
                              precondition=None, postcondition=None,
                              deadline_monotonic=None)
```

Runtime passes the exact fixed cycle completion deadline intersected with each
operation's own bound. Driver validates finite future absolute monotonic values
and never derives a new relative deadline for nested calls. None preserves the
existing behavior of callers outside a cycle. Runtime does not pass private
capability objects into native driver code; it retains semantic ownership and
final prepress checks in the daemon.

Receipt generation is the Guardian INPUT LEASE generation passed to driver.run;
it is distinct from the controller/IPC generation. Runtime receipt validation
compares it with intent.leaseGeneration, while semantic ownership separately
checks controller generation. Never assume the two counters are equal.
Every physical driver.run/prepare_command call, including the internal
_prepare_auctioneer_open generation argument, receives the input lease counter.
Public daemon/IPC route/executor generation arguments remain controller epochs.

Propagate the bound through canonical click-rate admission, identity, focus,
keymap/profile observation, anchor refresh/native callback, pointer position,
Guardian event waits and every X11Backend.action subprocess, including pointer
motion/press-release and allowlisted keyboard command preparation/submission.
Each blocking provider must receive the remaining bound; a check after return
alone is insufficient. Generic callback/native model producers use the runtime's
already bounded motion context for their capture/model timeout. Driver must
check the supplied deadline before and after invoking callbacks.

The runtime worker owns clamping _prepare_auctioneer_open, fresh-status/readback
and model helpers to this same bound, and supplies it to run/prepare_command.
The driver worker may add internal optional deadline parameters/context to
existing helpers without changing unrelated public APIs or legacy returns.
No wire/addon/config/API-fallback/Guardian/rate/input-event relaxation.

Cancellation still completes emergency release and cleanup even after the
deadline; never abandon held keys/buttons to satisfy a timing assertion. Keep
the complete call-local executor receipt through success and cleanup failure.

Focused proof must traverse actual DesktopDriver.run/prepare_command and
X11Backend.action, retaining actual runner-admission checks. Assert exact bound
at nested native calls and zero input after a deadline that expires inside an
earlier blocking step. Do not prove this only with a mocked driver.run or a
private deadline arithmetic helper. Keep tests short and independent of a game.

All pytest holds flock /home/dev/.cache/r-pg.lock with pinned CARGO. No live
input/deployment/DB/commits. Final source freeze and parent reproduction precede
independent Sol acceptance. Runtime whole-cycle integration is separately
reviewed after both producer and consumer finish.
