# Owned GTK startup diagnosis r1

## Scope and evidence

This is a bounded startup diagnosis, not a new review of the native emitter, seal, Guardian, driver, or runtime. I inspected only the authorized receipt and diagnostic log, `OwnedGtkCalibrationWindow` and `_GTK_SCRIPT` in `src/crowley/session/calibration.py`, the proof helper's command recorder/startup path, and their directly relevant tests. I sent no GUI or native input, ran no tests, and changed no source.

The supplied artifact digests match:

- receipt: `b8a41e519e02501e7014a0d04ce88a5f8d7e94b358bb904f86cd105dba23e572`
- diagnostic: `35b4f1f2613bc0892b596f6a1a36605b64f1f6f4773d97c86466939159861519`

The receipt is `seed-only`, `FAIL`, with `CalibrationError: owned GTK target ancestry includes the X11 root`. This happened during target construction, before observer startup or input dispatch. The parent-supplied process/lease checks establish that the failed helper PIDs are gone and the desktop lease is free.

## Diagnosis

The GTK child publishes its XID too early for the current parent-side certificate. `_GTK_SCRIPT` calls `show_all()`, performs one nonblocking `Gtk.main_iteration_do(False)`, then prints the XID (`calibration.py:232-249`). `create()` reads that identity and immediately calls `_verify()` once (`:2400-2429`). X11 mapping and Mutter reparenting are asynchronous, so one GTK iteration does not establish a viewable, managed window.

The relevant retained records show one lifecycle transition, all stamped within the same UTC second:

- Record 4 queried client `0x3400003`: `IsUnMapped`, absolute and relative position `(66,32)`, size `480x240`.
- Record 5's root tree had client `0x3400003` directly under root `0x374`. A separate same-title Mutter frame `0x6001d4` was also a direct root child and still `1x1`.
- `_verify()` assigned `parents[client]` to `managed_frame_xid`; that value was the root, so the refusal at `calibration.py:2550-2552` was correct for that snapshot. The root must never be certified or treated as a fallback frame.
- Record 7, queried later by the diagnostic recorder, showed the same client `IsViewable` at absolute `(753,456)`, relative `(61,94)`, still `480x240`. Record 8 now included `_NET_FRAME_EXTENTS`. Records 41-42 later found frame `0x6001d4` viewable at `(692,362)` with size `602x401` and `_MUTTER_FRAME_FOR=0x3400003`.

The later per-window records strongly establish that Mutter completed more of the lifecycle after the production tree snapshot. They do not establish final structural ancestry because the recorder never obtained a fresh root tree. The correct response is a fresh bounded certification attempt, not combining the old tree with later properties.

The proof recorder amplified and obscured the race. At `owned-gesture-proof.py:117-137`, it interpreted the client's immediate parent as a frame even when that parent was root. It then treated every direct root child as an immediate frame child and queried stats/properties for all of them. The retained log contains 160 records: 79 `xwininfo`, 78 `xprop`, one `wmctrl`, and two metadata records. Those synchronous queries happened after the stale root tree was captured but before `_verify()` consumed it, adding latency and mixing unrelated desktop state into the diagnostic. They did not make the stale tree valid.

A readiness-only fix will expose the next deterministic blocker. The fresh pointer was `(1524,542)`, while the eventual client rectangle was `x=[753,1233)`, `y=[456,696)`. The pointer was outside both the client and its observed frame. The existing seed origin check must continue to refuse this without input; no bootstrap warp is allowed.

## Minimal implementation plan

### 1. Request one owned initial placement

In `_GTK_SCRIPT`, call `window.set_position(Gtk.WindowPosition.MOUSE)` once, before `window.show_all()`. GTK 3 documents `set_position()` as a window position constraint and `GTK_WIN_POS_MOUSE` as placing a window at the current mouse position: [Gtk.Window.set_position](https://docs.gtk.org/gtk3/method.Window.set_position.html), [Gtk.WindowPosition](https://docs.gtk.org/gtk3/enum.WindowPosition.html).

Treat that API as a placement request, not ownership evidence. Keep the normal managed/decorated GTK toplevel. Do not call `xdotool`, move the pointer, retry placement, create an override-redirect window, or relax the frame certificate. The final server-reported client rectangle/window and the existing helper pointer query remain authoritative. If Mutter constrains the placement and the pointer is still outside the certified client, the seed must fail without dispatch.

### 2. Add a bounded startup-readiness state around the existing strict certificate

Refactor the certificate into one fresh attempt that either returns the current exact `OwnedWindow`, reports a narrowly defined internal startup-pending state, or raises the existing hard `CalibrationError`.

Use the single `create(timeout=...)` monotonic deadline for identity publication and every certificate attempt; do not reset the budget after receiving the XID. Bound every external read by the remaining time. Keep the same admitted process, process group, gate ownership, and registration for the whole wait. Do not respawn the target or retry the proof. On exit/deadline, use the existing terminate/reap/unregister path exactly once.

The startup-pending cases should be closed and explicit:

- the exact owned client is still `IsUnMapped` or `IsUnviewable`;
- its exact `_NET_FRAME_EXTENTS` property has not appeared yet;
- a fresh structurally parsed root tree still has the exact owned client absent or directly under root, with no conflicting identity;
- the expected managed relation is not yet complete, while all fields already present remain internally consistent.

Parse `Map State` and `_NET_FRAME_EXTENTS` as exact single values. Missing values may be pending only during the initial bounded wait. Duplicate, malformed, or contradictory values are hard failures. Once the client is viewable, has frame extents, and a fresh tree places it under a non-root frame that is itself directly under root, run the current strict frame/helper/process/geometry/children checks without fallback. Wrong PID/title, duplicate client identity, wrong size/class, malformed tree, unrelated non-root parent, wrong `_MUTTER_FRAME_FOR`, wrong helper, wrong frame process/class, extra frame child, or inconsistent geometry must fail immediately rather than consume the deadline.

After `create()` has returned a certificate, later recertification such as `show_human_prompt()` should remain strict. A previously ready window becoming unmapped, direct-root, or structurally incomplete is certificate drift, not a new startup grace period.

### 3. Make diagnostics passive and branch-scoped

`OwnedGtkCommandRecorder` should forward each production command and return its exact output, but it should not issue additional X11 queries. Remove the root-child enumeration and `_desktop_window_manager_identities()` expansion from `_capture_live_branch`.

For `wmctrl`, retain only the admitted GTK PID/title row plus a digest/count of the original response. For each production root-tree attempt, retain a scoped parsed summary: root XID, client XID, the client's immediate parent if any, the client path/geometry, and only a candidate/verified frame branch relevant to that client. When the client parent is root, record an explicit `startup-unreparented` state; never emit `frameXid=root` or enumerate root children. Once production verification follows the real frame/helper branch, its exact `xprop`/stats commands are already recorded naturally.

This keeps each retry diagnosable without querying unrelated desktop windows or changing the timing between a captured tree and the verifier that consumes it.

## Required regressions

1. **Lifecycle transition:** model the retained sequence: exact client identity, first stats `IsUnMapped` with no frame extents/direct-root tree, then `IsViewable` with frame extents and a fresh exact frame/client/helper tree. Assert one child process, one startup admission, no respawn, and the final exact certificate/target set.
2. **Deadline and ownership:** keep returning an exact startup-pending snapshot until a fake monotonic deadline. Assert query timeouts never exceed remaining budget, the original process remains the only admitted group during the wait, and deadline cleanup terminates/reaps/unregisters it once.
3. **Hard malformed refusal:** parameterize duplicate/wrong client identity, malformed/duplicate map state or frame extents, wrong size/class, ambiguous tree, unrelated parent, wrong frame/helper/process facts, and extra frame children. Assert no retry and complete cleanup.
4. **No root/fallback certificate:** separately prove that direct-root client plus a same-title `1x1` Mutter sibling remains pending and can never produce an `OwnedWindow`; a later certificate must come from a fresh tree with the exact structural relation.
5. **Placement contract:** assert the embedded GTK script requests `Gtk.WindowPosition.MOUSE` before `show_all()` and contains no pointer movement/input operation. Retain the existing helper regressions that refuse an outside queried origin before dispatch.
6. **Passive diagnostic recorder:** feed a tree with a direct-root client and many unrelated root children. Assert the recorder performs only the caller's original production command, records `startup-unreparented`, does not call stats/props for root children, and does not name root as the frame. Repeat with a ready exact branch and assert it records only that branch without adding commands.
7. **Strict post-ready recertification:** after a successful startup certificate, make the prompt-time snapshot unmapped/direct-root or change the exact target set. Assert immediate certificate-drift failure with no startup retry.

## Exact implementation fence

Production/helper changes should be limited to:

- `src/crowley/session/calibration.py` — `_GTK_SCRIPT`, bounded `OwnedGtkCalibrationWindow.create()` readiness, exact map/frame-extents parsing, and the internal single-attempt certificate flow.
- `.archive/executor-review/owned-gesture-proof.py` — passive, client-branch-scoped diagnostic recording only.

Test changes should be limited to:

- `tests/test_session_native_regressions.py` — bounded create/readiness/cleanup/placement lifecycle cases and captured Mutter command sequences.
- `tests/test_session_native.py` — update the existing strict root/parent/sibling certificate fixtures for exact map/frame-extents fields and retain hard structural negatives.
- `.archive/executor-review/test_owned_gesture_proof.py` — passive recorder command-count and scoped-record regressions.

No changes are justified in driver admission, Guardian, input parsing, calibration evidence/sealing, emitter/click/camera paths, runtime/controller/service, profiles, database, or tool artifacts. After this bounded startup fix is reviewed and hermetically tested, run one new owned seed only. Do not advance to positive/cancellation proofs unless that seed returns a valid certificate and the queried initial pointer is already inside the exact certified client.

## Outcome

The observed failure is explained by an unhandled GTK/Mutter startup state, not by the reviewed XTEST transition implementation. The current refusal is safe. The minimal fix is one pre-map GTK mouse-relative placement request, a single-deadline wait for a fresh strict certificate, and passive scoped diagnostics. Root/direct-client or separately titled frame shapes remain non-certifying at every point.

STATUS: NEEDS BOUNDED STARTUP FIX
