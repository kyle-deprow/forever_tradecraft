# Sol review: GNOME capture completion r1

The review was limited to the frozen `src/crowley/session/driver.py` and new
`tests/test_session_capture.py` change. I inspected the plan, retained real
concurrency diagnosis, freeze metadata, patch, production call paths, and the
reported parent verification. I did not run tests, operate the GUI, or change
source, configuration, or services.

## Must-Fix

1. **A capture can survive revocation once the short-lived GNOME client has
   exited, and a later arm can let that revoked capture publish.**
   [`src/crowley/session/driver.py:2298`](../../src/crowley/session/driver.py#L2298)
   waits for the cross-process lock and
   [`src/crowley/session/driver.py:2307`](../../src/crowley/session/driver.py#L2307)
   waits for the asynchronous PNG without consulting the backend cancellation
   state; the last check before
   [`os.replace` at line 2318](../../src/crowley/session/driver.py#L2318) is only
   identity and time. `_run()` observes `_cancel_active` while the CLI process
   is alive, but the retained diagnosis establishes that this process can exit
   before the service writes the image. `release_held_input()` then sets that
   event, while `activate_generation()` clears it for a successor. Consequently,
   revocation followed by a new arm during the new completion wait can leave no
   cancellation state for the final identity commands to observe, and the old
   capture can be atomically published. This is reachable through the normal
   `DesktopDriver` capture methods, which do not bind `X11Backend.capture()` to
   a generation and rely on the backend cancellation behavior.

   Add a monotonic backend cancellation/revocation epoch that is incremented by
   `release_held_input()`, snapshot it at capture admission, and require the
   exact epoch during lock acquisition, completion polling, final identity
   verification, and immediately before publication. Do not use only the
   clearable event as the retained proof. Add a delayed-writer test that revokes
   after `_run()` returns, reactivates a successor generation, and proves that
   the old request cannot publish; cover cancellation while waiting for the
   capture lock as well.

## Should-Fix

1. **The staging path is neither intrinsically private nor reliably cleaned
   when an asynchronous writer creates it after the deadline.**
   [`src/crowley/session/driver.py:2295`](../../src/crowley/session/driver.py#L2295)
   accepts an existing destination parent without checking or tightening its
   mode, and line 2296 places the GNOME output directly in that parent. The
   stage is chmodded only on the successful path at line 2317. More directly
   for this diagnosed failure mode, the `finally` at lines 2321-2325 performs
   one unlink: if the service has not created the file yet, the unlink sees
   `FileNotFoundError`, after which the service can create the stage and leave
   it behind. A unique name prevents that file from satisfying another request,
   but it does not support the freeze's claim that staging evidence is removed
   on every failure and can expose a partial capture when the supplied parent
   is not private.

   Create each stage inside a fresh mode-`0700` per-attempt directory on the
   destination filesystem, so `os.replace()` remains atomic, and retire that
   directory on every exit in a way that prevents a not-yet-opened late writer
   from recreating the pathname. Add a writer whose creation is delayed beyond
   the capture deadline and assert that the destination is unchanged, the
   successor still succeeds, and no late stage becomes visible; also assert the
   staging directory/file privacy while the writer is active.

## Nits

None.

The remaining reviewed behavior matches the bounded plan: all Crowley
processes contend on one nonblocking `flock`, lock/subprocess/completion/final
identity work consumes one absolute deadline, complete images receive both
Pillow verification and full decoding, publication is atomic, and the existing
destination cannot satisfy a new request. The focused tests meaningfully cover
early exit, partial and truncated PNGs, contention without screenshot dispatch,
identity drift, and ordinary successor cleanup. Parent reports 36 focused tests
passing in 7.93 seconds with scoped Ruff and formatting checks passing; no real
GNOME capture has yet validated this repair.

STATUS: NEEDS WORK
