# Sol implementation prescription: final helper composition

**Decision: ready to implement; no interface blocker.** Freeze inputs are helper
`44acb08dd44f3974819937b3874abf6809381cbc18505a9fa02b3ec728a5e6b8` and tests
`9c1c5043dceab6b0f18a4620c60e2b1e31bb904f2b01a0945c9c8c8dee784575`. The six R5/R6
native files remain development dependencies until the separate absence repair and parent acceptance.
Only `tools/native_calibration_operator.py` and its test file change; add no public mode, request field,
schema, router, Guardian, lease, or timing allowance.

## Exact implementation

1. **Production reload readiness.** Replace the unconditional stub at frozen helper
`tools/native_calibration_operator.py:816-819`. Extend only the private `ScreenAdapter`/helper call with a
closed proof selector (`absence` or `ordinary`). On each poll, use `X11Backend.capture` through the
configured profile, with the same absolute deadline on identity-before, capture, and identity-after;
require one unchanged profile/binding fingerprint. Crop exactly `profile.canvas_crop` into an attempt-local
0600 PNG. `absence` accepts only the final native `_strict_native_absence_image` result for that exact size.
`ordinary` decodes that crop with the stock `PixelDecoder` and accepts only `FRESH`, nonempty boot not
prefixed `native-construction:`, `render.nativePhase == "normal"`, `nativeOrdinal == 0`, and inactive
`scanner.scheduleFence`. Delete every temporary crop. Use `absence` at the measure `/reload` boundary
(`:3269-3271`) and `ordinary` after either recovery action (`:3226-3232`). Keep
`_post_reload_controls` (`:2811-2852`) as the independent dual-button plus strict-absence proof; keep
`SessionDaemon.native_construction_recovery_complete` as the authoritative genuinely-new-boot proof
(R6 `daemon.py:2297-2422`). A same/old ordinary boot may satisfy only helper readiness and must still be
rejected by that daemon comparison.

2. **Deadline reaches physical dispatch.** Add `deadline_monotonic` to the private `InputAdapter` methods
(`:193-206`), `FixedInput` methods (`:1180-1266`), and `OwnedEmitter` construction (`:1018-1033`). Make
`_deadline()` (`:2353-2361`) always take the minimum of reservation, operation, and named phase rather
than dropping reservation when another bound exists. `_chat` (`:2861-2902`) selects the bound for its
current/causal state and passes the same absolute timestamp to open/type/submit (or Escape); before the
first Return, prove the fixed emitter sequence can fit using the authentic 130 ms/character contract.
`_click` passes the constructor phase bound for Construct and the reservation bound for Restore
(`:2913-2946`) and preflights the complete move + press/release sequence before moving. `_new_emitter`
must call `_action_timeout(action, deadline=...)`; change `_action_timeout` (`:956-970`) so insufficient
remaining time refuses instead of shortening the required action budget. In both parent and
`_emitter_entry` (`:839-890`), cap readiness, gate writes, subprocess press/release, acknowledgements and
joins to the current remaining absolute time. Once a press may have occurred, phase expiry still invokes
the existing independent watchdog release; do not cap that safety release to the expired phase. Preserve
the daemon's 30 s provider, helper's 5 s capture freshness, 7 s constructor/click reserve, 10 s addon
window, and existing independent cleanup windows.

3. **Terminal measurement recovery is a fresh admission.** After terminal native error, require `pause`
to return a strictly newer generation (not equal), PAUSED, idle/non-running and unarmed (`:3167-3201`).
Retain the old binding only to validate immutable owner/profile/identity handoff, clear history, and call
`_recover("")` at `:3333-3342`; never send the old measure ID. In `CancellationActor.call`
(`:2023-2085`), allow an empty ID only for `recovery_begin`, matching actor execution already present at
`:1742-1762`. The actual recovery reply must install/ACK its new canonical ID and expiry before any input;
every later failure cancels that new ID through the actor and retains the actor if cancellation is not
canonical. The separately reproduced bootstrap-lost-reply known-ID/old-expiry defect is a required
dependency of the final two-file candidate; do not duplicate or broaden that correction here.

## Decisive test mapping

Build one shared actual-composition fixture around the private compiled producer/X11 compositor from R6
`tests/test_session_native.py:962-1197`, the actual `SessionDaemon`, and an AF_UNIX handler that forwards
each record to actual `SessionIPC.dispatch` (reuse `:2000-2144`). Reuse the real PNG runner/capture state
machine from `tests/test_session_native_regressions.py:5121-5303`, but advance its external scene only
after the real `FixedInput -> OwnedEmitter -> watchdog publish -> GO/PRESSED` order. Inject only external
pixels, OCR text, clocks, and an explicitly sealed input fixture; daemon reservations, histories,
deadlines and replies must be created by public calls. Do **not** copy the manually manufactured inflight
capability at `test_session_native.py:1222-1252`, canned `_admission_reply`, `FakeClient`, or override
`wait_reload_boundary`.

| Test | Required proof |
|---|---|
| production readiness | Actual `X11Screen.wait_reload_boundary`: loading/damaged/wrong-identity/prefixed-or-fenced frames refuse; strict absence satisfies only measure; fresh ordinary normal/0 satisfies recovery; deadline is bounded. Preserve the separate pure-absence suite. |
| `control-preflight` | Actual public preflight creates its ID; fixed Defer + Construct dispatch precedes actual preflight-ID recovery handoff; parameterize daemon capture to cover Restore and ordinary-reload classification; require actual recovered terminal reply. |
| `recover` | Start from a real durable checkpoint with no live reservation; actor request has exactly empty `reservationId`; ordinary branch emits only `/reload`, restore emits Recover + one Restore click; actual daemon creates a new ID and completion proves a newer ordinary boot. |
| `measure-deferred` | Actual prepare/bootstrap/native-calibrate/status/finalize flow, all 12 real history states, bootstrap's long expiry ACKed before input, and `finalize_required` is not success until real `finalized`. A terminal-error variant proves newer PAUSED, empty-ID fresh recovery, new-ID handoff, and exact-ID cancellation after an injected post-handoff failure. |
| budget/refusal | One tick below required type and complete-click budgets yields no GO, tool log, or physical dispatch; admitted cases show every wait <= remaining phase time. Expiry after possible press proves independent exact release. Canonical IPC refusal, identity drift and timeout each occur before the next physical dispatch and leave an actual cancellation terminal. |

Keep all existing new-boot, identity, control, absence and ownership proofs. Run only focused readiness,
composition and budget groups first, then the complete helper suite once on final bytes; final accepted
native copy and parent full composition remain acceptance prerequisites.
