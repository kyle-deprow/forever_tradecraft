# D1 integration review

Actual model gpt-5.6-sol, xhigh; source-only, no tests run. Status MAJOR ISSUES.
Parent accepted the following reachable findings as one scoped correction.

1. daemon.py:87-123 and3485-3549: engine capture/decoder and interaction intents
   lack shared serialization. _advance snapshots repeat mode; entering interaction
   preserves generation, so later engine dispatch can race interaction ownership.
2. daemon.py:105-112 versus cli.py:700-710: 30s server versus key5/camera15/
   calibration30 client budgets. Share budgets with transport/cleanup margin.
3. daemon.py:2139-2157,2346-2349,2450-2460,2629-2632,2727-2730: model can spend
   feedback reserve; physical admission reserves hold only despite two required
   postrelease publications. Calibration30s is impractical for actual1Hz telemetry.
4. daemon.py:1984-2001,2491-2564: repeated forward measurements unchecked and
   first speed retained; backward/right strafe are inferred without measurement.
   Measure all roles, consistent repeats and conservative travel before commitment.
5. daemon.py:2432-2467,2633-2662: original route may expire while awaiting native
   confirmation; capture timestamps assigned after capture falsely freshen evidence.
6. daemon.py:2748-2751: fixed absolute camera response error accepts zero or
   opposite small responses. Waypoint shares turn/translation stall counter.
7. Installed IPC tests omit actual calibration/waypoint and produce fresh sequence
   every capture instead of1Hz publications/NO_CHANGE. Add boundary-level paths,
   no production ownership/route/driver gate stubs.

Also accepted: bound angular camera response to avoid normalized multi-turn
aliases; circular fit repeated heading offsets; native W forward fixture;
NativeMotionProvider compare separately resolved and captured identity; expose
complete actual calibration basis/measurements in IPC response.

The installed xdotool absolute XWarpPointer mismatch is a separate native emitter
defect; it neither excuses nor changes these source findings.
