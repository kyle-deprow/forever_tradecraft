# Live driver coordination

Updated 2026-10-22 03:10 UTC by the main game-driver session.

- `/root/luna_assisted_scanner` was resumed by follow-up task on the user's latest
  instruction and is running. The old user hold in HANDOFF is superseded.
- Before any new sweep, `crowley-session.service` was restarted at02:54:19 UTC:
  PID3087152 ->1821334. Runtime is PAUSED generation71, native/input false, idle.
  MAIN includes format3 validator commit347ab56; focused format2/3 tests passed10.
  Companion was left alone. First new format3 sweep is not yet verified.
- Live addon is a symlink to `/home/dev/repos/pegasus/addon/Crowley` on MAIN.
- P2 merged at05392bf; parent probe tests passed9/244deselected. Arthur's world boot
  predates the merge, so the live driver is loading the addon with a guarded
  reload before `/crowley probe` and the saving `/reload`. Actual capture/upload
  remains pending; source merge alone is not live API evidence.
- Arthur is in Ironforge on build70450, AHclosed/pending0/speed0, PAUSED71 with
  checkpoint absent. Do not independently capture or operate the game. Luna is
  the sole GUI owner for keyboard-only probe and assisted scanning.
- Native calibration is held for a concrete current-policy click-helper fix,
  implemented offline in the isolated native-human-click worktree. This does not
  block the keyboard-only collection path.

P2 merge owner: record the resulting MAIN commit below (or relay it to this
session) once ready. The driver will then verify current source/loaded addon,
execute the probe/reload, and retain the actual probe upload evidence.

P2 merged MAIN commit: 05392bf
Live expanded-probe capture: pending
