# Human-play HUD visibility

User asks to minimize or disable the upper-left telemetry square during human
play and explicitly says assume beta over. Live collection and game input are
held; session service has been disabled/stopped. This is an offline addon feature,
implemented by Luna and independently reviewed by Sol. No live acceptance claim.

## Behavior and order

1. Read CLAUDE, HANDOFF and crowley-client-contracts skill. Implement
   `/crowley hud hide`, `/crowley hud show`, `/crowley hud status`, and
   `/crowley hud` as a convenient toggle. Explain in command help/messages that
   the telemetry HUD is required for agent operation, and hiding is a display
   preference, not a controller pause or scanner mode change.
2. Persist an explicit boolean preference in CrowleyDB.settings; absent means
   visible, preserving current installations. Hide the entire surface and stop
   its periodic work while hidden; prevent explicit Publish/FrameBytes access
   from presenting stale telemetry as current. Hidden preference survives reload.
3. Show restores the original native geometry/scale without changing schema or
   source identity, attaches exactly one periodic publisher and publishes fresh
   telemetry. Make failure truthful; no success with an old frame. Hide must
   work even when the last publication failed. Never auto-show merely because
   AH opens or a timer fires. Idempotent explicit hide/show and strict arguments.
4. Preserve existing native construction/measurement/recovery lifecycle. Refuse
   visibility mutations while a native diagnostic transaction owns the surface;
   never erase/finalize a marker or run recovery to apply a preference. Cover
   the interaction explicitly. No new calibration, protocol or service framework.
5. Exercise commands and real addon lifecycle using Lua harness, including
   default visible, toggle, persisted hidden boot, fresh show, idempotence,
   no hidden periodic publication/stale bytes, errors and diagnostic ownership.

## Ownership and fence

Isolated worktree: /home/dev/.cache/crowley/worktrees/hud-visibility-20261023
Base0b1fd2b. Allowed: addon/Crowley/Agent.lua, addon/Crowley/Commands.lua,
tests/test_addon.py, tests/wow_harness.py only. Parent owns docs/plan/integration.
No MAIN/other worktree edits, scanner/Core/protocol/Python runtime/config changes,
game input/capture, live services, dependency changes or git commit/push. Do not
fold the separately observed secret-number telemetry bug into this feature.

## Verification and completion

Run PYTHONPATH=src /home/dev/repos/pegasus/.venv/bin/python -m pytest -q tests/test_addon.py
from the worktree, Ruff check/format on changed Python, git diff --check. Freeze
full patch, source hashes, exact command logs/results and report in private
executor-evidence/hud-visibility-20261023. DONE only after completed implementation
and tests. Sol reviews frozen bytes; parent checks/tests before promotion. The
installed addon symlinks MAIN, so promotion requires user reload to load new Lua;
do not operate or reload the live game on the user's behalf.

## Review correction R2

R1 stays frozen. Sol found and parent reproduced the inverse order: hide an
existing ordinary surface, then agent hold/defer. Both native commands still
accept based on surface existence, mutate native ownership and prevent show.
In the sibling hud-visibility-20261023-r2 worktree, guard native entry before
any marker/phase/fence mutation while hidden. Keep same exact file fence and
reject explicitly rather than auto-show. Cover hide-before-native-command and
persisted-hidden boot, unchanged markers/fences/phase, and usable show afterward.
Rerun full addon tests/static checks and freeze a new private R2 bundle for Sol.
