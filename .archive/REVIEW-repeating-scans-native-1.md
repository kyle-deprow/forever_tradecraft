# Native boundary component review 1

Sol verdict: MAJOR ISSUES. Owned non-game calibration NOT READY TO EXECUTE.
No live window/input/sample request is authorized until a passing focused review.
16 native tests pass but use trimmed/fake streams and miss production failures.

Critical corrections:

1. synthetic_calibration sends xdotool mousemove 10 10 in absolute desktop
   coordinates, not relative to owned GTK geometry. This clicks outside the
   test window. Verify owned PID/XID/ancestry/focus and convert exact target
   geometry before consistent active-window XTEST; never touch game/launcher.
2. First human revoke correctly pauses controller and increments generation,
   but daemon then rejects completed evidence for generation change, losing
   it and requiring endless repeated calibration. Retain proven evidence while
   staying durably paused; explicit resume may reconcile it, never auto-arm.
   Clear stopped monitor references and start a live runtime observer on arm.
3. External input outside GTK records an error but fails to revoke immediately,
   so delayed action may fire. Every human/unclassified event revokes input,
   releases and invalidates queue regardless target. A 5-second scheduled action
   conflicts with a 120-second human wait; use a real bounded cancellation test
   that accommodates deliberate response and proves a due action was suppressed.
4. begin_action generation check and state install are not atomic. Blocking
   subprocess.run cannot cancel active type/click/key commands. Backend has no
   actual release_held_input. Independent watchdog uses unsupported xdotool
   'keyup --all', never releases buttons, and clears held state before failed
   release can use fallback. Track owned held keys/buttons, cancel process groups,
   use supported release arguments, retain fallback until release succeeds.
   Do not hold guardian lock during blocking X11 ancestry lookup. Exercise real
   owner exit with fake release process; daemonized multiprocessing watchdog must
   survive long enough to perform release.
5. Full preserved XI2 trace has 12 records incl releases, DeviceChanged, Enter,
   Leave and unresolved source7 Motion. Runtime only awaits press and may clear
   correlation before release; pointer allowlist omits transition records. Key
   detail/order/multiplicity are unchecked. Correlate complete expected operation
   sequences and device/source/target ancestry/time fields. Keep unknown source7
   closed, never accept solely because its target is owned. Use full captured
   fixture positive valid subsequences and negative foreign motion, not trimmed
   press-only test streams.
6. Input evidence lacks F13/button1 details, raw/delivered pairs/releases/order/
   timestamps/master-source hierarchy/modifiers/target retention. Fingerprint omits
   event proof. Store complete exact evidence and only proven bounded pointer echoes;
   ancestry alone is not deterministic echo provenance.
7. Verify actual Linux Wine loader via /proc/pid/exe in addition to Windows cmdline,
   exact status Name and prefix. Count matching game processes (including starting/
   windowless), not only title windows. Enforce outer/child origin0,0. focus_game
   cannot require already-foreground as precondition; separate verified focus
   recovery from foreground-required capture/input. No speculative fallback.
8. RSS construction baseline is sampled after textures already exist. Observe before
   authorized external operator bootstrap, then new addon construction; use VmHWM
   peak and proper intervals, not only current RSS. Native runner must enforce one
   process/identity/boot itself through 101 frames. Prove all four physical pixels
   per 2x2 cell, boundaries and all-cell black/white colors, not center-only plus
   addon self-report. Pin exact canvas origin/crop80,48,256,256.
9. Actual pointer actions require runtime fingerprint anchors but no owned anchor
   calibration/installation path exists; example has none. Provide a measured,
   reviewable live producer for reconnect/select/enter/AH actions, not fake
   fingerprints/manual assertion. Coordinate with lead's real visual observer.
10. Persist and enforce full native/input fingerprints and observations, not booleans,
    and invalidate on owner/game/display/geometry/XInput/driver changes.

Also: one reader owns each observer stdout pipe (avoid communicate race); use parsed
incremental records instead of reparsing incomplete blocks; clean intermediate101
capture dirs retaining only final evidence; remove unused synthetic-parser state.

Actual host: lowercase WM_CLASS wowb.exe; comm/status Name WowB.exe; Linux exe Wine
wine-preloader. One outer1928x1092 at0,0, one unnamed child1920x1080 at0,0. Never
hardcode PID/XID. Focused review will recheck executable calibration before user sample.
