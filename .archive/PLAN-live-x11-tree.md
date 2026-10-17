# Live X11 tree parsing correction

Actual native bootstrap rejects the verified sole game client before measuring:
`expected one verified game client, found 0`. Captured production command:

```
xwininfo: Window id: 0x1800001 "World of Warcraft"

  Root window id: 0x374 (the root window) (has no name)
  Parent window id: 0x374 (the root window) (has no name)
     1 child:
     0x1600011 (has no name): ()  1920x1080+0+0  +0+0
```

The common parser currently ignores the queried-window header and treats the
first child as the queried root. WM_NAME, WM_CLASS, PID, executable/prefix and
1928x1092 outer/1920x1080 direct child dimensions independently match profile.

Luna owns only `src/crowley/session/driver.py`,
`src/crowley/session/calibration.py`, `tests/test_session_native.py`.
Read AGENTS/CLAUDE, local-game-control and client-contract skills. All other
source/tests/docs and deployed data/config/services/game/git are read-only.

1. Encode the actual xwininfo tree contract in the common parser: queried root
   comes from its unique header; structural child rows and indentation prove
   ancestry. Root/Parent diagnostic lines, titles and unrelated hex tokens
   must not manufacture descendants. Reject missing/ambiguous/mismatched roots,
   duplicate/cyclic structure or invalid ancestry rather than guessing.
2. Remove the GTK caller's manual synthetic root-prefix construction; use the
   same actual-header parser for game descendants and owned GTK ancestry.
   Preserve exact managed-frame/client/PID checks and sibling/root rejection.
3. Add regression using the captured game output and production child geometry
   path; update artificial headerless tree fixtures to the real format. Include
   no-children output and foreign/root/sibling/ambiguous negative cases. Do not
   invent a second legacy/headerless parser or relax identity gates.
4. Run focused new tests and complete native/independent-native suites with a
   private CROWLEY_DESKTOP_LEASE and all three strict warning filters, then
   Ruff check/format, compile and git diff --check. Freeze and report DONE.

Sol independently reviews only this concrete live-contract correction and its
regressions; retain previously reviewed memory-window, timing, clock and guardian
logic unchanged. Parent reproduces tests and read-only real resolve_identity
before the sole Luna game operator restarts the unarmed daemon and retries native
bootstrap. No SavedVariables edits or fake evidence; existing process remains.

Parent inspection after first implementation found native named rows were still
ignored by a parenthesis-only row recognizer. Actual filtered root-tree output:

```
xwininfo: Window id: 0x374 (the root window) (has no name)
     0x1800001 "World of Warcraft": ("wowb.exe" "wowb.exe")  1928x1092+0+0  +0+0
        0x1600011 (has no name): ()  1920x1080+0+0  +0+0
```

The same bounded fix must parse genuine quoted-name/class rows and unnamed
rows, including actual GTK title syntax. Replace invented parenthesized title
fixtures with real output shapes; retain strict diagnostic rejection. No Sol
review or live clearance was issued for the incomplete first implementation.
