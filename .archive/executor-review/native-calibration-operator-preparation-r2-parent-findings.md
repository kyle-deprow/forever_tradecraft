# Parent observations pending independent reviews

Parent independently reproduced13 helper tests passing4.06s, verified both owned
hashes and the six frozen read-only dependency hashes. The candidate remains
UNQUALIFIED. Sol and actual CLI Opus review it independently; these observations
were not supplied as an expected verdict.

- _control_region (line1589) treats the panel's220x84 UI units and24 inset as
  native pixels and computes y=height-108. Commands anchors TOPRIGHT, while
  capture pixels start at the top; the real scale is also not1. The64x64 fixtures
  take a None-region fallback, concealing the live-size geometry error.
- _chat (line1592) no longer rechecks daemon binding/current focus immediately
  before final Return after capture/OCR. Revocation during readback can therefore
  submit stale input. The pre-input guard must apply at that actual boundary.
- _record_operation_deadline (line1385) permanently takes the minimum of overall
  and phase-specific constructor/finalize bounds, including expired historical
  fields retained in the handshake. Constructor admission and total measurement
  waits need distinct lifetime accounting; realistic published deadlines must be
  exercised, not only a huge fixture expiry.
- Recovery invokes completion immediately after its one reload/click. Native R4
  takes one immediate capture, before ReloadUI may finish. Root sent native R5
  the concrete bounded readiness-poll correction under the existing45s/expiry cap.
  No helper action retry or new IPC is permitted.

Thirteen unit fixtures do not cover the required actual spawned sealed watchdog
composition, helper death during hold, signal/ACK-loss matrix, full-size rendering
or production main lifecycle. Accepted native integration is a separate gate;
independent offline ownership coverage is still required before qualification.
