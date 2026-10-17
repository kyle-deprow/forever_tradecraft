# Sol GTK startup final r2 correction review

Serving model ID: not exposed to this worker. The session identifies the agent only as Codex based on GPT-6, so I cannot accurately claim a more specific serving ID.

## Scope and evidence

I reviewed `gtk-startup-reviewfix-r2.diff` against the reconstructed `gtk-startup-r3-source-snapshot`, the correction freeze manifest, `gtk-startup-r13-arbitration.md`, both r13 reviews, and the active GTK startup plan. I inspected only the six changed paths and directly implicated context. I did not run tests, issue GUI/native input, inspect private files, or modify source.

The correction remains inside the authorized five worker files plus parent documentation. By inspection, it closes the accepted production findings:

- alternate-only same-PID/title `wmctrl` identity now fails hard;
- admitted-client process identity is captured before later readiness-pending exits;
- one possible unpublished helper may remain pending, while multiple unknown children or a known wrong child fail immediately;
- identity EOF no longer spins, create passes only the absolute deadline, and every verifier command receives its remaining budget;
- malformed recorder XIDs produce a scoped diagnostic without changing stdout or adding commands;
- the helper selects the farthest quarter endpoint and all three proof-mode call sites retain one measured plan.

The real-verifier lifecycle test now traverses missing extents, actual `IsUnMapped`, direct-root, an incomplete candidate frame, and a fresh ready certificate while observing shrinking command timeouts. Separate tests cover a never-ready registration cleanup, late successful verification after the deadline, strict/startup structural behavior, a known helper with a wrong child, and post-ready `IsUnMapped` refusal. The parent-reported 52 GTK and 35 helper passes plus global checks are supporting evidence, not results I independently reproduced.

## Must-Fix

None.

## Should-Fix

1. **The accepted partial-identity cleanup assertion is still missing.** [`tests/test_session_native_regressions.py:1535`](/home/dev/repos/crowley/tests/test_session_native_regressions.py:1535) proves that an unterminated live identity line does not call blocking `readline()`, but its admission returns no cleanup capability and the test never asserts termination, wait/reap, registration cleanup, or final `poll()`. The existing empty-channel timeout and malformed complete-JSON tests exercise neighboring paths, but they would not catch a future change that moved the partial-buffer error ahead of `abort()`. Add a cleanup callback and lifecycle assertions to this exact partial-line case, requiring terminate/wait, one unregister, and a reaped process. This is the remaining explicit item 8 requirement from `gtk-startup-r13-arbitration.md`; the current production path at [`calibration.py:2484-2488`](/home/dev/repos/crowley/src/crowley/session/calibration.py:2484) is correct by inspection.

## Nits

None.

## Readiness boundary

The implementation is source-correct by inspection apart from the required regression assertion above. These tests and reviews do not establish that Mutter honors placement on the live desktop or that the final native pointer starts inside the certified client. They also provide no native gesture, game, physical-human, camera, movement, or cadence acceptance. Those remain separate post-review gates.

STATUS: NEEDS WORK
