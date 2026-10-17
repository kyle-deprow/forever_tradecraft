# Auxiliary engine review

Sol verdict: MAJOR ISSUES. Stable scope: CLI/model adapter, addon Agent/Scanner/
Commands/TOC, addon harness/tests, service/example. No source or live state changed.

## Must fix

1. No atomic pre-logout schedule fence. At cadence+900 another scan starts before
   normal logout; PLAYER_LOGOUT then saves that fourth scan incomplete/logout.
   Preserve ordinary user logout partial-save behavior, but controller closeout
   must first fence future starts atomically, refusing the fence while active.
   Daemon must accept only genuinely idle ready/scheduled phases, not item/owned
   with empty activeSweepId (active scans ALWAYS have that field empty). Coordinate
   an exact reserved fence command and telemetry proof with main/native owners.
2. SessionIPC.status holds controller.lock then owner.status_dict, while calibration
   completion holds calibration-state lock then requests controller.lock. A real
   two-thread repro leaves both alive. One consistent lock order, no outer
   controller lock around owner status; concurrent status/pause/calibration/shutdown
   regression must finish and surface errors.
3. Model parser accepts free text, unknown events with output, diagnostic substrings,
   and multiple answers (last wins). Exact known JSON lifecycle, exactly one
   structured answer, exact allowed diagnostic equality/count. Reject free text,
   unknown result-bearing events, duplicate answers, extra candidate shapes.
   Preserve model/prompt/tool restrictions, absolute executable/version startup,
   deadline and process-group TERM/KILL.
4. Agent claims publish_high_water verified at zero with a constant counter. Samples
   around C calls plus a Lua string witness cannot establish transient C allocation
   peak. Must not label a net/retained metric true peak. Constant/non-sensitive
   counters reject; true peak requires an actual peak-capable method and controlled
   transient C witness plus native measurement. Prior GC state restoration is sound.
   Measurement contract clarification is pending parent decision; do not invent
   unsupported APIs or silently claim a peak.
5. Scanner accepts wrong build, wrong retained depth and arbitrary count while Agent
   hardcodes900/600/20. Enforce the actual pinned canonical plan before scheduling/
   starting:428IDs,20levels,900cadence,600cap,fulltarget1.60.1.70374, matching plan
   identity. Project actual loaded values into telemetry; invalid plan must block
   with plan_invalid. Current harness falsebuild1.60.1.1 hides errors. Preserve
   meaningful depth/API/pagination tests using complete canonical fixtures, no
   test-only production bypasses.

## Also fix / integration

- Agent activeEdit requires actual methods and <=128UTF8 bytes; missing IsShown
  must not mean shown. No user chat persisted, malformed/unbounded text blocks
  safely without sending Enter or poisoning the whole telemetry surface.
- Stable harness tests for closeout deadline race, canonical-plan rejection,
  unavailable/non-sensitive/positive measurement and prior stopped-GC restoration.
- Daemon chat-readback path stamps captured_at AFTER _capture_model; preserve
  original timestamp returned by capture and recheck identity/state after inference.
- Service/example entry point, Restart policy and secrets are correct; live setup
  must verify inherited XAUTHORITY. Actual staged environment was verified earlier.

Sol checks: addon87pass6.95s strict warnings; Ruff/format/diff/help/installedentrypoint/
exactCodex0.162.1 pass. Four adversarial repro groups exit0 proved defects. No
GUI/input/model turn/services/privateconfig/database/auth/source mutations.
