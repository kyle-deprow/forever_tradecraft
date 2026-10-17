# Future sole Luna native API observation outcome

NOT RELEASED. Root may release only after owned-target seed/positive/cancellation evidence and independent source review. Read AGENTS.md, CLAUDE.md, docs/HANDOFF.md, .agents/skills/local-game-control/SKILL.md and .archive/PLAN-motion-live-prerequisites.md. No service arming, camera/movement, trades, credentials, unrelated settings/streaming/display changes, or source edits. Stop on user takeover. Use sole existing verified client, no duplicate Play. Normal cached login/reconnect authorized; leave Arthur stationary and AHclosed. If account conflict recurs or credentials required, stop and report.

Verify foreground/scene via GNOME capture and current exact process/window identity. Use already established bounded slash-command path; confirm edit buffer and never send ordinary chat. Each statement fits client edit length. Capture original actual responses privately; no config-file inference.

1. /run local ok,v=pcall(function() return C_CVar.GetCVarBool("autointeract") end);print("CR_CTM",ok,type(v),tostring(v))
2. /run local a,b,c,d=GetUnitSpeed("player");print("CR_SPEED",a,b,c,d,GetFramerate())
3. /run print("CR_TYPES",type(IsFlying),type(IsFalling),type(IsSwimming),type(IsSubmerged),type(IsMounted),type(UnitOnTaxi))
4. Only if exact native functions above exist: /run print("CR_GROUND",IsFlying(),IsFalling(),IsSwimming(),IsSubmerged(),IsMounted(),UnitOnTaxi("player"))

These are diagnostics; nil/errors remain explicit facts, no accessor fallback. Do not change Click-to-Move or encode capability from source knowledge alone. Report exact all-four speed values, CTM bool vs nil/error, actual framerate, ground predicates, build/character/location/current screenshot state, retained private paths and cleanup. No camera/motion calibration is authorized by this outcome. No commit/reset/stash/revert.
