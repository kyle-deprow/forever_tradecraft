# Private native handshake helper

The helper is frozen at `eaa14f0ab6766502f1cccca95fb5ca3a0875bf92b4b46aadc2f27136084c7ac9` (242 lines):
`/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-handshake-once.py`. It owns one unique `0700` timestamped attempt directory per process and
writes only a `0600` receipt and private captures. Failed attempts remain intact.

`--preflight-only` derives `DISPLAY` and `XAUTHORITY` from the sole current
Xwayland process before constructing the backend. It takes userbus/XDG values from
that process, consulting the sole GNOME shell only when required. It uses a
read-only input-tool shim backed by the verified artifact metadata, status, live
identity, and GNOME capture. It never calls `native-bootstrap`, `native-calibrate`,
input dispatch, or reset5. The latest preflight passed with zero input, bootstrap,
calibrate, and kernel-reset attempts:

`.archive/executor-review/native-handshake-read-only-preflight-receipt.json`

The measured client is 1920x1080 at root origin inside a 1928x1092 outer window.
The Enter World source is the measured `(842, 977, 236, 51)` client box. The preflight's fresh positive match
was MAE 0.0; a black synthetic negative scored 37.8541 against the 5.0 limit.
The normal helper rechecks identity and fresh pixels before the one pinned XTEST
click. Chat commands are typed and OCR-confirmed one-shot at hold, measure, and
resume readiness. The exact100 update wait performs no GUI captures or input.

Bootstrap and calibration are issued consecutively within the daemon's ten-second
proof window. Readiness edges use 30-second waits; the measured 100-update phase
has a 130-second bound to accommodate one-Hz publications. The normal helper was
not executed by this worker.

Validation and freeze details are in `private-helper-freeze.json`. The previous
failed receipts at 015502Z (missing inherited Xauthority) and 015544Z (stale
control match) are preserved. The pre-edit timestamp pyc is retained as baseline
provenance; a separate pre-edit source SHA was not captured.
