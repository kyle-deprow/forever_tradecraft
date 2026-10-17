# D1 rereview

Actual gpt-5.6-sol xhigh; read-only, no tests/code executed. STATUS NEEDS WORK.
Parent accepted the following concrete findings after its37-pass hermetic run.

Must fix:
1. Initial camera calibration accepts16–120pixels with declared maximum0.25rad/px,
   so even16 permits4radians. Endpoint normalization can alias a multi-turn drag
   into a valid small mapping. Require coherent pre-input sub-pi envelope.
2. Both calibration/runtime yaw subtract the visual evidence frame rather than
   the confirmed dispatch frame; accepted0.019rad pre-input drift can manufacture
   apparent progress for a zero-response drag.
3. Waypoint rejects a reachable0.5unit target at7units/s/default0.08s pulse:
   desired0.057s is below minimum, while a safe0.08s pulse ends0.06units away.
4. Waypoint stall accounting compares pre-pulse distance one pulse late, allowing
   an additional ineffective pulse before the nominal stall budget is exhausted.
5. No actual IPC motion_camera_calibrate test; fixture preinstalls CameraMapping.

Also accepted: require stationarity before every role probe; close model cancel
versus event.clear admission race; bound cancellation/reaping within absolute
model deadline; tighten/justify a repeated-forward limit permitting2x speed;
include camera generation/boot in calibration response.

Ownership, route freshness, four-role measurement, deadlines/reserves, postrelease
barrier and actual installed movement/waypoint tests are substantially improved.
This report does not establish native game input acceptance.
