# Live driver coordination

Updated 2026-10-22 after the live 03:22 UTC probe by the main game-driver session.

- `/root/luna_assisted_scanner` was resumed by follow-up task on the user's latest
  instruction and is running. The old user hold in HANDOFF is superseded.
- Before any new sweep, `crowley-session.service` was restarted at02:54:19 UTC:
  PID3087152 ->1821334. Runtime is PAUSED generation71, native/input false, idle.
  MAIN includes format3 validator commit347ab56; focused format2/3 tests passed10.
  Companion was left alone. First new format3 sweep is not yet verified.
- Live addon is a symlink to `/home/dev/repos/pegasus/addon/Crowley` on MAIN.
- P2 merged at05392bf; parent probe tests passed9/244deselected. Luna loaded it
  with a guarded reload, submitted `/crowley probe` once, then saved with a second
  verified reload. Probe1792639338 (2026-10-22 03:22:18 UTC) is in client_probes.
  Parent independently compared the entire database probe JSON against the
  immutable saved CrowleyDB.probe: exactly equal, including40 boolean globals,
  six boolean frame checks and expanded namespace function inventories.
  SavedVariables SHA256:
  `b3e9a362d06f6813b29b5c3d62323b9e6547706cc33e5b757f587e88066fa0b7`.
  Private proof: `assisted-collection-luna-20261021/530-saving-reload-probe-check/parent-probe-verification.json`.
  Presence does not prove usable return contracts; absent load-on-demand frames
  do not establish unavailable APIs. No trade actions were performed.
- Arthur is in Ironforge on build70450, AHclosed/pending0/speed0, PAUSED71 with
  checkpoint absent. Do not independently capture or operate the game. Luna is
  the sole GUI owner for keyboard-only probe and assisted scanning.
- Native calibration is held for a concrete current-policy click-helper fix,
  implemented offline in the isolated native-human-click worktree. This does not
  block the keyboard-only collection path.

P2 merged MAIN commit: 05392bf
Live expanded-probe capture: saved and uploaded; independently verified against DB.
First resumed sweep: UID`beta-normal-alliance-1792640172-Arthur-4663`,
03:36:12–03:44:22 UTC,428 attempted/zero failures/1046 rows. Parent validated
original format3 and matched complete logical digest/plan/counts to DB:
423 full/5 bounded,428ok. Server receipt03:44:57.060933 UTC (35.06s after finish).
Next due03:51:12 UTC. Original SavedVariables/Data.lua retained. Exact ACK exists
in Data.lua; loaded-ACK proof is pending because the session reader rejects the
producer's newly added `referenceItemIDs` field. Narrow Luna consumer-contract
fix is promoted after Sol READY and parent4tests/retainedactualData.lua acceptance.
Fresh helpers load it; paused daemon restart is pending before autonomous use.
GUI owner is restoring AH with one uploaded pending UID
below cap6 to keep collection moving. No active-sweep ACK reloads.
Private proof: `assisted-collection-luna-20261021/543-scan237-exact-ack-diagnostic/parent-format3-upload-verification.json`.
