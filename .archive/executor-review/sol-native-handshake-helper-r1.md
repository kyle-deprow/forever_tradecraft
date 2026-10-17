# Sol review: private native handshake helper r1

Reviewed the frozen 242-line private helper, its specification and plan, the production handshake/status boundaries needed to interpret its flags, and the parent preflight receipt. I did not execute the helper, operate the GUI, change services/configuration, or rerun preflight. The reviewed SHA-256 is `eaa14f0ab6766502f1cccca95fb5ca3a0875bf92b4b46aadc2f27136084c7ac9`; the helper and attempt directory are mode 0700 and the receipt is mode 0600. No full operator run or native resource qualification has occurred.

## Must-Fix

1. **Readiness actions are not bound to the initial controller generation and active calibration phase.** The helper captures a dynamic generation at `native-handshake-once.py:214-215`, but `read_snapshot()` at `native-handshake-once.py:171-175` only rejects operation error or `restoration_required`. `wait_flag()` at `native-handshake-once.py:178-184` accepts any truthy top-level or handshake flag without rechecking `status.generation`, controller state, calibration kind/state, or the exact handshake state. The readiness fields are sticky: production sets `holdRequired`, `measureReady`, and `resumeRequired` true without clearing earlier fields. If the controller is paused, restarted, or otherwise revokes the generation after a readiness flag is published but before the next poll/action, the old true flag can still authorize the Enter World click or a `/crowley agent hold`, `measure`, or `resume` submission even though the original native calibration boundary no longer owns that action.

   Preserve the initial dynamically read generation and require every subsequent status to match it. Before the four actionable readiness edges, require controller state `NATIVE_CALIBRATION`, a running native calibration operation, and the exact expected handshake state (`bootstrap_ready`, `hold_required`, `measure_ready`, or `resume_required`) together with its flag. For final `resumeReady`, require the same generation and exact `resume_ready` handshake while allowing the documented race into the completed `INPUT_CALIBRATION` transition. Record the initial and observed generation/state in the receipt. Any mismatch must abort before GUI input; do not retry or accept another operation's flag.

## Should-Fix

None.

## Nits

None.

The remaining helper behavior matches the bounded specification. It derives graphical variables from the sole session processes before backend construction, verifies exact profile geometry and foreground PID/XID/start/fingerprint, creates a unique private attempt directory, and preserves prior attempts. The bootstrap and calibration calls are consecutive and the elapsed check enforces the ten-second proof lifetime. Readiness polling returns on the first observed match with 30-second bounds, while the update window has a 130-second bound. After submitting `measure`, the helper records the capture count, performs status-only polling until the production `resumeRequired` boundary—which itself verifies held ordinal 100—and rejects any extra helper GUI capture before resume.

The three chat commands are one-shot: each opens chat, types through the live pinned XTEST tool, captures the buffer, requires exact OCR text, and submits only after the match. The Enter World path rechecks identity and pixels before one click. Cleanup closes the backend's input-tool handle in `finally`, and failed receipts/captures are retained.

Preflight is narrower than a live qualification. Its explicit `ReadOnlyInputTool` uses system `xdotool` only for X11 queries while separately verifying the real pinned artifact metadata; `input_tool_mode: read-only-stub` discloses that distinction. It performs a real GNOME capture and identity/control match but no GUI input, bootstrap, calibration, reset5, or DesktopDriver lease work. The positive match is real current pixels; the black case is only a synthetic negative for this template threshold. Those results validate read-only setup and matcher discrimination, not native calibration, live pinned-tool dispatch, the 100-frame measurement, or completion of the full handshake.

STATUS: NEEDS WORK
