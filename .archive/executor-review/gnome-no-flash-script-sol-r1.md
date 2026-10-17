# Sol review: runnable GNOME no-flash benchmark script, R1

Review scope was limited to the frozen private script
`/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-benchmark-stage2.py`
(SHA-256 `9a5ec2345974bebfb5fdad6f605190e026004f6962e8e75518784bd67b1b5e9c`),
its R4 freeze record, and the accepted benchmark plan. I did not execute the
script, run tests, perform captures, use the GUI, or change services or source.

## Must-Fix

1. **The live preflight accepts the daemon's real active `starting` calibration state.**
   `/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-benchmark-stage2.py:716-725` normalizes `calibrationOperation.state`, but lines 723-724 reject only `running`, `capturing`, `busy`, and `in_progress`. The production daemon publishes `starting` before its worker enters `running` and treats both `starting` and `running` as active (`src/crowley/session/daemon.py:376-380` and `4037-4040`). A controller can also become `PAUSED` while that worker remains active. The script can therefore pass both its controller-state gate and a momentarily free lock before the calibration worker reaches capture, then begin the benchmark alongside a daemon-owned operation. This violates the accepted requirement that the daemon have no active calibration/capture operation and can contaminate timing or make the two producers contend for the shared capture lock.

   Fix `require_idle_daemon_status` to reject `starting` as active (or, more robustly, admit only the daemon's known terminal operation states), and add an offline test for `PAUSED` plus lowercase `starting`. Preserve the existing rejection of lowercase `running`.

## Should-Fix

None.

## Nits

None.

## Verified behavior

- Live mode remains gated by both the explicit execution flag and exact release token; self-test and self-check modes do not enter `live_run`.
- The script verifies the reviewed binary, one-entry private `bin` directory, disabled X11 build, accepted driver hash, and unchanged production executable resolution before capture. The graphical session values are derived and checked before constructing the backend.
- The monitor uses daemon-only D-Bus queries, proves readiness from an actual `NameAcquired` event, and requires one acquisition and release per request. Acquisition evidence is tied to the private executable hash/path, the actual backend-owned process-group snapshot, benchmark PPID, and `PGID == PID`. Missing, stock, forwarded, reused, late, or ambiguous ownership evidence stops the run.
- Each bounded sample performs one outer identity resolution and one production `backend.capture`, then uses the production crop and strict decoder with the original capture-start timestamp. Starts are scheduled at least 1.1 seconds apart outside the measured path. `NO_CHANGE` is retained as a valid non-fresh observation without retry; `FRESH` observations enforce boot continuity, increasing sequence, fixed position, and zero speed.
- The eight-call cap, one-shot failure behavior, private receipt/capture permissions, XBEL metadata-only accounting, exact-owner SIGTERM cleanup, observer reaping, and final build/config checks match the accepted experiment. No result is labeled native qualification.

STATUS: NEEDS WORK
