# Private native handshake helper r2

The private helper is frozen at
`dd4778b38802d2e68dacfd3b9f6453f03280cdaed3d6e79fef8084ca2d4349e4` (354
lines):
`/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-handshake-once.py`.
The r1 source hash `eaa14f0ab6766502f1cccca95fb5ca3a0875bf92b4b46aadc2f27136084c7ac9`
and its receipts remain preserved. Every attempt uses a unique `0700` directory;
receipts and captures are `0600`.

The operator path binds the dynamically observed controller generation to the
native calibration operation's exact `kind: native`, operation generation, and
running `NATIVE_CALIBRATION` state. Polling accepts only the exact ordered
handshake phase and its readiness flag. Sticky flags from an earlier phase,
generation, operation, or restart fail before input. The final `resume_ready`
proof accepts the documented same-generation race into `INPUT_CALIBRATION` only
when the native operation is complete. Each mouse move, click, chat open/type,
OCR cancellation Escape, and chat submit rechecks identity and the bound phase
immediately before the physical input. A stale OCR cancellation is abandoned
without sending Escape. Status observations record expected phase, observed
generation/state/operation, acceptance, and order in the private receipt.

`--preflight-only` remains read-only: it derives current Xwayland variables
before backend construction, verifies the measured 1920x1080 client and
1928x1092 outer geometry, binds the live identity, and performs one fresh GNOME
capture plus positive/negative Enter World matching. It never starts bootstrap
or calibration, sends input, or resets memory. The r2 receipt is
`.archive/executor-review/native-handshake-read-only-preflight-receipt-r2.json`.
The r2 attempt passed with positive MAE 0.0, negative MAE 37.8541, and
`input: 0`, `native-bootstrap: 0`, `native-calibrate: 0`, and `kernel-reset: 0`.

The dry guard suite is
`.archive/executor-review/test_private_helper_guards.py` with output in
`private-helper-guards-r2.log` and exit marker `private-helper-guards-r2.exit`.
It uses fake status payloads only and covers stale generation, sticky old-phase
flags, completed and wrong-kind operations, wrong phase/flag, and the allowed
final transition. It also enters the production `handshake()` through the
first fake `native-bootstrap --generation 42` call, proving initial receipt
recording and dynamic generation binding without a real backend, CLI, capture,
or physical input. Scoped `py_compile`, AST parsing, and Ruff `E9,F` checks
pass. The live operator handshake and real GUI preflight were not rerun for
this startup-only correction.
