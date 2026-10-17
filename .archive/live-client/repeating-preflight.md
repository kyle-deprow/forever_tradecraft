# Repeating controller host preflight

Preflight date: 2026-10-15. This was observation-only: no game key, mouse click, slash command, character entry, movement, scan, or service/configuration change was performed. Window activation was used only to inspect the already-running game and existing launcher.

## Host, window, and capture

- One `WowB.exe` process and one mapped WoW window were present (`0x01800001`); the window maps to `WowB.exe`. One existing Battle.net main window (`0x01a00011`) maps to a Chromium renderer process. No second game client was found. The launcher profile showed Online; its game tile remained on the normal Play page. No launcher control was clicked.
- Desktop is GNOME Shell with one Xwayland server. The game process has `DISPLAY=:0`, `WAYLAND_DISPLAY=wayland-0`, `XDG_RUNTIME_DIR=/run/user/1000`; its inherited `XDG_SESSION_TYPE=tty` conflicts with the observed Wayland socket and running GNOME Shell/Xwayland processes, so that variable alone is not a reliable backend indicator. The X display identifies as X.Org Foundation under Xwayland.
- `xrandr` reports primary `HDMI-1`, 1920x1080 at 74.91 Hz. The visible WoW X window is at (0,0), outer size 1928x1092; its game child is 1920x1080. `gnome-screenshot` successfully captures the complete 1920x1080 desktop, including GNOME panel/dock. A representative game capture is `/tmp/crowley-preflight-game.png` (shows the current disconnect dialog); the launcher observation is `/tmp/crowley-launcher-preflight.png`.
- Current WoW screen: login/disconnect modal `WOW51900319`; no character is in the world. Battle.net separately showed its profile Online. The immediately preceding post-logout character-select screenshot showed Arthur Aguafuerte selected and available in the list. No reconnect, login, or character entry was attempted in this preflight. The launcher-online state does not establish an active WoW server session or exclusive account use.

## Input devices and source distinction

`xinput --list --short` reports these relevant devices:

| ID | Device | Role |
|---:|---|---|
| 4 | Virtual core XTEST pointer | Synthetic pointer source |
| 5 | Virtual core XTEST keyboard | Synthetic keyboard source |
| 6 | xwayland-pointer:17 | Wayland-compositor-forwarded pointer |
| 7 | xwayland-relative-pointer:17 | Wayland-compositor-forwarded relative pointer |
| 8 | xwayland-pointer-gestures:17 | Wayland-compositor-forwarded gestures |
| 9 | xwayland-keyboard:17 | Wayland-compositor-forwarded keyboard |

Touch and tablet forwarding devices are also present (IDs 10–13). No individual physical keyboard or mouse names appear in XInput; physical devices are presented to Xwayland through the compositor's aggregated pointer/keyboard devices. The XTEST devices are separate synthetic sources. The existing `/tmp/crowley-game-control.py` uses `xdotool` for key/click operations; the installed xdotool description identifies it as fake keyboard/mouse input. No test event was injected, so this report does not claim an observed event-level `sourceid` trace.

## Capture/controller implications and open assumptions

The current display can produce full-screen captures, and XTEST and compositor-forwarded device classes are distinct in the XInput hierarchy. A repeating controller can potentially filter its own XTEST events from user input, but an Xwayland client sees compositor-forwarded devices rather than named physical keyboards/mice. Event-level behavior, GNOME-level takeover detection, and whether all human pointer paths reach the same Xwayland source remain unverified; the preflight intentionally avoided test input. A safe controller should use an explicit closed-by-default session lease and a separate passive human-activity signal, not infer user takeover from the game screenshot, Battle.net Online status, or its own XTEST activity. The controller/telemetry design and its human-takeover criterion remain implementation-review questions.

## Bounded XI2 event-source test (2026-10-15)

An ephemeral GTK3/X11 window titled `CROWLEY INPUT PREFLIGHT ONLY` was created with a separate helper process (PID 3046622, top-level XID `0x03c00003`). Before input, the exact title and PID matched in `wmctrl`, `_NET_WM_PID` and `WM_NAME` matched via `xprop`, and `xdotool getactivewindow` resolved to that same XID and title. Only after that check, xdotool sent F13 and one left click to the test target; no WoW or launcher key/button command was sent. The window process exited with code 0, and a later window listing showed only the pre-existing WoW and Battle.net windows. The bounded `xinput test-xi2 --root` observer was stopped with SIGINT; no observer or test-window process remained.

Observed XI2 source IDs matched the device list:

- F13 `RawKeyPress`/`KeyPress` and release: master keyboard device 3, source/device ID 5 (`Virtual core XTEST keyboard`). The key event was at test coordinates (987,595) and its child XID was `0x600119`, within the focused temporary GTK target; the active target was still the verified test window immediately before input.
- Left-button press/release: master pointer device 2, source/device ID 4 (`Virtual core XTEST pointer`), at the same test coordinates and child XID `0x600119`.
- The trace also contained a `Motion` from relative forwarded Xwayland device/source ID 7 with child XID `0x01a00011` (the existing Battle.net window) while the cursor was being positioned. It contained no key or button event for that child. The motion's origin is unresolved (compositor/warp behavior versus another source); this run therefore does not establish that pointer positioning is invisible to other windows. Do not interpret this event as proof of human activity.

No human key or click was intentionally generated during this test, so it provides no direct sample of human input attribution. The key event reported no latched or base modifier state; xdotool was invoked with `--clearmodifiers`, but XI2 showed no modifier key events. Logs are in `/tmp/crowley-input-preflight-xi2.txt`; the ephemeral window script and driver are `/tmp/crowley-input-preflight-window.py` and `/tmp/crowley-input-preflight-run.py`. This validates source IDs for the tested xdotool key and click calls only. It does not validate GNOME-level takeover detection, real human device attribution, or all pointer-movement paths.


## Parent read-only identity check during implementation review

The sole WoW window's actual WM_CLASS is `"wowb.exe", "wowb.exe"`, with title
`World of Warcraft`; `_NET_WM_PID` matches the sole `WowB.exe` process. Its Linux
`/proc/<pid>/exe` is the Lutris Wine runner's `wine-preloader`, so verification must
also identify the Windows executable and Wine prefix rather than compare the
Linux executable basename with `WowB.exe`. The observed XID/PID are runtime facts,
not configuration constants. No input, focus change, launch, or service change
was performed for this check.

A second read-only check confirmed the title window is 1928x1092 at (0,0),
with exactly one unnamed 1920x1080 child at relative and absolute (0,0).
The initial example's inferred `(4,12)` client offset is unsupported by this
hierarchy; derive and verify the actual child origin instead.
