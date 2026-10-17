# Standard local gaming restored

Date: 2026-10-14

## Actions

- Disabled and stopped the user `wow-fullscreen-watch.service`; its restart symlink was removed. The watcher script remains on disk, but it is inactive and disabled.
- Backed up `~/.config/systemd/user/sunshine.service` to `~/.config/systemd/user/sunshine.service.pre-local-gaming-20261014.bak`.
- Added `~/.config/systemd/user/sunshine.service.d/10-preserve-local-game.conf` with `KillMode=process` before stopping Sunshine, because Lutris/Wine/WoW were children in Sunshine's cgroup. Sunshine's own shutdown hook still requested its managed app to exit, so the running WoW session closed. The override remains in place; Sunshine is disabled and inactive.
- Disabled and stopped `sunshine.service`; its graphical-session autostart symlink was removed. No Moonlight process was found. Sunshine's shutdown log ran its saved display undo command.
- Clicked the visible Battle.net “Play Now” button once after the old session closed. The parent then reported the user had logged back into the game and directed read-only verification only. Current process inspection confirms `WowB.exe` is alive under Lutris/Wine in a `tmux-spawn` scope, outside Sunshine's cgroup; the user owns all game controls.

## Verification

- `sunshine.service`: inactive, disabled, no Sunshine process.
- `wow-fullscreen-watch.service`: inactive, disabled.
- Physical input devices remain: Logitech USB mouse and Dell USB keyboard. Sunshine's virtual mouse and keyboard passthrough devices disappeared; no streaming controller device is present in `/proc/bus/input/devices`.
- Local display is the Acer KG271 on HDMI-1, primary, 1920x1080 at 74.986 Hz. This matches Sunshine's recorded undo mode.
- `crowley-companion.service` remains active.
- The running game is local Wine/Lutris. The final screenshot shows the game window on the local desktop.
- No GamePad CVar entry is present in the active `Config.wtf`; no input-mode CVar was changed. Current in-game MKB-versus-controller mode was not queried because the user took control and further game input was prohibited. With the virtual controller removed and physical keyboard/mouse present, local MKB input is available; the precise active UI mode remains unverified.

No game navigation, scans, trades, or addon/server changes were made during this setup task. The stopped Sunshine unit's KillMode override and the unit backup are the only external configuration changes beyond disabling the two streaming units.
