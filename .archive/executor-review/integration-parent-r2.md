# Parent check of first D1 correction

Luna reported30 strict tests passing and DONE. Parent rejected completeness
before spending another independent review. Source inspection found:

- Calibration still30s despite five probes, camera and real1Hz barriers.
- Unknown-role precommit remaining-distance guard was weakened to checking
  cumulative distance alone; a final1-unit probe could be emitted with0.6 left.
- Forward max speed retained, but inconsistent repeated measurements not rejected.
- Excessive camera expected angle rejected only after physical drag.
- No installed IPC calibration or waypoint requests added to integration tests.
- Alternating FRESH/NO_CHANGE every other capture is roughly50ms, not1Hz.
- Cumulative test assertion counted three displacements despite five probes.

The same bounded Luna received all concrete findings together, preserving its
existing file fence. Require meaningful installed-path tests, practical shared
budgets with completion margin, restored conservative precommit bounds and
coherent technical default before final source review. No native acceptance
claim follows from the first correction report.
