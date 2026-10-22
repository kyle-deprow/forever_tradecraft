# Live driver coordination

Updated 2026-10-22 04:43 UTC by the main game-driver session.

- `/root/luna_assisted_scanner` is running after an explicit follow-up task on the
  user resume. It is the sole GUI owner. Root/other agents must not capture/input.
- Latest user reply confirms gameidle/userAWAY: keep assisted collection running
  until return; finish offline work and hold the live calibration window.
- Before the first new sweep, root restarted crowley-session at02:54:19 UTC,
  PID3087152 ->1821334, PAUSED71/nativefalse/inputfalse/checkpoint absent. It loads
  format3 support347ab56. Server also reports accepted formats[2,3]. Companion
  was left running. The addon symlinks to MAIN's addon/Crowley.
- P2 merged05392bf. Guarded preparatory reload -> one `/crowley probe` -> verified
  saving reload completed. Probe1792639338 (03:22:18 UTC) is uploaded to
  client_probes. Parent independently matched complete saved JSON against DB,
  including40 boolean globals, six frame checks and namespace inventories.
  SavedVariables SHA256:
  `b3e9a362d06f6813b29b5c3d62323b9e6547706cc33e5b757f587e88066fa0b7`.
  Private proof: assisted-collection-luna-20261021/530-saving-reload-probe-check/parent-probe-verification.json.
  Presence does not establish return contracts; absent load-on-demand frames do
  not establish unavailable APIs. No trade actions performed.
- First new sweep237 UID beta-normal-alliance-1792640172-Arthur-4663 ran
  03:36:12–03:44:22 UTC,428 attempted/zero failures/1046 rows,423full/5bounded.
  Parent matched original format3 logical digest/plan/counts to DB and all stored
  observation/row JSON plus quantity/unit-price columns (including26 stacked
  item rows). Server receipt03:44:57.060933 UTC,35.06s after finish.
  Private proofs: assisted-collection-luna-20261021/543-scan237-exact-ack-diagnostic/
  parent-format3-upload-verification.json and parent-stored-prices-verification.json.
- Both scan237/238 ACKs are independently proven loaded from retained actual HUD
  PNG (boot1792641832-543673/sequence7,pending0,AHclosed,lastSaved238). The reader rejected referenceItemIDs;
  Luna/Sol fix d78510b and fixture closure e58d8f8 are committed/pushed. Fresh
  helpers load it; daemon was restarted after gesture integration, now PAUSED72,
  PID676938, native/input false, operation idle, checkpoint absent.
- Scan238 ran03:54:27–04:03:03 UTC,428 attempted/1039 rows/one query_timeout(item6361),
  received04:03:51.891017 UTC(48.89s). Parent matched originalformat3 digest/plan/counts
  to DB;423full/4bounded/1incomplete. Its next due was04:09:27 UTC.
  Actual preceding interval1095s (195s late). Both ACKs loaded in one ordinary save
  reload. Never interrupt an active sweep to load an ACK.
  Private proof: assisted-collection-luna-20261021/553-scan238-postprocess/
  scan238-save-upload-ack-20261022T040332496592Z/parent-two-sweeps-loaded-ack-verification.json.
- Four resumed sweeps237–240 now have428 observations each and4201 total rows inDB;
  four uploads received within60s of finish, exact client ACKs verified. Latest240
  received04:34:50.391049 UTC; scan241 began04:41:18 UTC,nextdue04:56:18 UTC.
  Last two start intervals913s/919s (13s/19s late); still assisted collection.
- Reviewed shared human-click repair is installed at exact final Sol hashes;
  final native103 case/three-cycle socket composition and parentMAIN51 focused
  tests passed. Broad scoped175pass/one known clean-base retained-crop mode failure
  is recorded, not hidden. Restarted controller is PAUSED72/PID676938 with absent
  checkpoint, native/input false. Live calibration remains held for user return.
  No timed prompt active; zero autonomous cycles qualified. Keep collecting.
