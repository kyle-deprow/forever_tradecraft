# Sol review: private native handshake helper r2

Reviewed only the r2 generation/phase guard delta, the dry guard suite, the frozen helper/specification, and the parent read-only preflight receipt. I did not execute tests, operate the GUI, change services/configuration, or reopen the accepted read-only shim and matcher scope. The reviewed helper SHA-256 is `dd4778b38802d2e68dacfd3b9f6453f03280cdaed3d6e79fef8084ca2d4349e4`. No full helper run or native resource qualification has occurred.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

The r1 stale-input finding is closed. `native-handshake-once.py:217-251` requires the originally observed generation, native operation kind, matching operation generation, and the permitted controller/operation boundary. `native-handshake-once.py:264-283` accepts only the next exact handshake state and its own readiness flag; a sticky earlier flag, skipped phase, changed generation, completed/wrong-kind operation, or missing phase flag fails before input. The final `resume_ready` path permits only the same-generation documented combinations: running native calibration before transition, or completed native operation in `INPUT_CALIBRATION`.

The action paths revalidate immediately before physical effects. The Enter World flow at `native-handshake-once.py:333` checks identity and exact `bootstrap_ready` status before both mouse movement and click. The command flow at `native-handshake-once.py:296-310` rechecks identity and phase before chat open, typing, OCR-mismatch Escape, and submit. If the operation is revoked during OCR, it abandons the buffer without sending Escape. These checks prevent a previously published sticky flag from authorizing input after pause, restart, generation change, cancellation, or phase advance.

The initial receipt-indexing defect is also closed. `status_observations` is initialized at `native-handshake-once.py:26`, and `handshake()` records the dynamically read boundary before invoking bootstrap at `native-handshake-once.py:321-327`. The dry production-entry test reaches exactly `native-bootstrap --generation 42`, records generation 42, and has an input sentinel. The other dry cases cover stale generation, sticky old-phase flags, completed and wrong-kind operations, missing exact flags, and the permitted final transition. The supplied parent guard run passes.

The parent read-only preflight receipt is consistent with the bounded preflight contract: it records the verified identity and geometry, real positive and synthetic negative matcher results, private artifact modes, and zero input/bootstrap/calibration/reset attempts. It does not establish the live pinned-tool dispatch path, phase sequence, 100-frame measurement, or completed calibration. The helper will read the current generation at execution time; no fixed historical generation is embedded.

STATUS: READY
