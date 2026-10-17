# Repeating scans: first implementation review

Sol verdict: MAJOR ISSUES. Parent reproduced normal checks: 161 passed, 15 DB
skipped; Ruff/check/format (92 files)/whitespace pass. These tests omit the real
daemon lifecycle. No native inputs or deployment have occurred.

Required correction outcomes:

1. Parse the captured native XI2 records (`device: master (source)`, event blocks,
   actual child/target, detail, timestamps), not synthetic `sourceid` fixtures.
   Match actual event classes and ancestry to declared generation/action/target.
   Own a temporary non-game GTK target and live synthetic plus deliberate human
   key/click sampling; prove queued input cancellation. No caller boolean/source
   sets, copied traces, or magic calibration token may arm the production path.
2. Real guardian cancellation must produce durable generation-incrementing PAUSED,
   interrupt capture/model/multi-step input, and release held input. Use one
   process-lifetime lease before journal/socket ownership; no second daemon may
   unlink the live socket. Parent-death monitoring must observe another process.
   Do not hold the controller mutex during blocking model/capture/input work.
3. Bind screenshots and actions to the exact one-client PID/executable, XID/child
   geometry and foreground. A 1920x1080 desktop screenshot is not itself proof of
   game pixels. Decode exact boot/sequence/CRC; allow only expected reload boots,
   tolerate bounded loading-screen absence, enforce freshness deadlines.
4. Restore current UID/phase/evidence/action/retry/deadlines before reconciliation.
   A start cannot erase pending work. Fence all mutating IPC requests, including
   start/closeout/calibration, make status read-only, use TOML paths in clients,
   and persist action intent before dispatch. Persist reopen intent/deadline.
5. Match actual Data.lua fields (`generatedAt`, ackedScans, scanPlan, shoppingLists;
   repository placeholder also declares ackedSweeps). Wait for stable exact UID
   in both companion uploaded timestamps and Data.lua before ack reload. Evaluate
   finish-to-upload from the durable timestamp, not later observation time.
   Externally pin canonical plan hash/JSON and exact character/realm/build.
   Wire kinds commodity/item cannot classify recipe/container/equipment: use
   verified item metadata and persist per-item coverage/source/priced/category
   evidence. Reset streak for every nonqualifier and retain diagnostic history.
6. Enforce actual state-specific visual/telemetry pre/postconditions for login,
   selection, AH, reload, reopen and logout, with bounded retry/deadline records.
   Reject nested model tool/command events and catch recovery errors as BLOCKED.
   Queue emptiness does not prove logout: require actual character-select evidence.
   Never persist chatEdit.text in a journal or model prompt.
7. Test the integrated daemon/CLI runtime with fake clocks and realistic captured
   fixtures: three cycles, every wait/restart boundary, automatic scan adoption,
   reload/Data publication races, stale/foreign frames, takeover/cancellation,
   calibration and strict negatives. Manually calling qualify() three times is
   not an integrated test. Document a real install command and session environment.

Parent probes independently confirmed: reload loading-screen error becomes BLOCKED;
assertion-only calibration reaches ARMED; driver revocation leaves journal SCANNING;
actual Data.lua parser rejects generatedAt; preserved XI2 trace parses no events.

Use the approved plan plus its correction-round addendum for exact ownership and
measurement interfaces. Fix the production paths, not just these reproductions.
