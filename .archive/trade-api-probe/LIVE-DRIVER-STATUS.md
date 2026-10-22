# Live driver coordination

Updated 2026-10-22 04:02 UTC by the main game-driver session.

- `/root/luna_assisted_scanner` is running after an explicit follow-up task on the
  user resume. It is the sole GUI owner. Root/other agents must not capture/input.
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
- Exact scan237 ACK is present in Data.lua and strictly verified; loaded ACK is
  pending its next ordinary save reload. The reader rejected referenceItemIDs;
  Luna/Sol fix d78510b and fixture closure e58d8f8 are committed/pushed. Fresh
  helpers load it. Restart paused daemon before future autonomous use.
- Scan238 began03:54:27 UTC; nextdue04:09:27 UTC. Actual interval1095s (195s late).
  It retains scan237 as one uploaded pending UID belowcap6. Never interrupt an
  active sweep to load an ACK; its normal save reload can load that prior ACK.
- Native calibration is independently held for an offline shared human-click
  implementation. Design READY does not approve code. Native/input remain false,
  no human prompt active, zero autonomous cycles qualified. Keep collecting.
