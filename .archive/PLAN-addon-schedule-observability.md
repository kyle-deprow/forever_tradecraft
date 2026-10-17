# Addon timer evidence and cadence regression

Status: proposed, Sol plan review before implementation. Main objective remains
reliable900s scans. Preserve ordinary beta collection while the cause is unknown.

## Evidence and scope

Fifth sweep started1792220223 exactly900s after fourth. After its loadedACK and
AH reopen, same-boot HUD at07:11:35UTC reported AHopen/scheduled/due1792221123.
At07:12:42and07:17:26 it reported AHopen/ready/due0/no active query/pending0,
with lastSaved still fifth. One safe close/reopen auto-started sixth1792221571.
Installed Scanner.lua SHA b2843e42d1edf4d9ed4df1b6214928cf12baadde03108b65fd10912fdfc0b218
matches this checkout. Cause is NOT established. `Status.phase=scheduled` is a
cooldown projection, not a timer-handle observation. Existing cadence test fires
AUCTION_HOUSE_SHOW atdue and cannot prove the timer-alone path.

Own only `addon/Crowley/Scanner.lua` and `tests/test_addon.py`. Keep separately
controlled external clocks in the test fixture; do not edit the shared
`tests/wow_harness.py` used by the concurrent native work. No Agent/protocol/status wire-schema, catalog/plan, build policy,
server/companion/session/executor, config, game input, deployment or Git changes.
Implement and test ONLY in the detached worktree
`/home/dev/.cache/crowley/worktrees/addon-schedule-20261017` based on `f2d3f2b`.
The live addon symlinks the primary checkout and normal scan flushes reload it;
editing its Scanner.lua would load an unreviewed candidate. Read this plan from
the primary checkout, but never write primary addon/tests. Parent integrates the
reviewed candidate only after coordinating a safe reload boundary. Worker does
not commit or manipulate worktrees. Review artifacts use the primary
`.archive/executor-review/addon-schedule-*` namespace only.

## Requirements

Add bounded read-only scheduling diagnostics in a separate SavedVariables field,
outside format2 scan envelopes and existing queryTrace. Record schedule request,
refusal reason, actual timer creation, intended due/delay/token, callback entry,
stale-token/AHclosed discard, due refusal, start commitment and cancellation on
AHclose/logout/fence. Include actual wall time and GetTime uptime and a per-load
correlation key; never pretend these events are proof of executed queries.
Keep the latest at most64small fixed-schema events and an overflow count, with
bounded strings and no chat/input/market payloads. No per-frame polling, extra
AH queries or chat spam; preserve event and query ordering.

First add meaningful tests proving timer-alone start at900s without reopening,
manual /scan or duplicate start; AHclose/logout/fence cancel stale callbacks;
active sweep cannot overlap; queue/plan blocks remain enforced; reload/newowner
scheduling uses persisted lastSweepStart. Reproduce forward/backward clock
changes or an early callback with separate wall and timer clocks ONLY at the
external harness boundary. State clearly which case is experimentally
reproduced and which actual live cause remains unknown.

Do not silently change scheduling while adding diagnostics. If a concrete
early-callback case reproduces a lost due start, propose the smallest fix and
exact regression in the completion report; root can release that focused fix
after inspecting the reproduction. No force scan, shortened cadence, duplicate
timer recovery loop, broad ticker or fallback. Fixes to unrelated callbacks or
new runtime observability endpoints require a separate scope decision.

## Verification and completion

Run `uv run pytest -q tests/test_addon.py` and any affected existing direct
harness consumers, scoped Ruff/format for changed Python, Lua through actual
shared harness, and `git diff --check`. Preserve failing-before/passing-after
evidence, changed-file hashes, bounded-trace tests and actual output. No live
rollout: parent and Sol source review precede any reload/deployment, coordinated
with the GUI operator after an in-flight sweep has been saved/ACKed.
Return a completed diagnostics/test slice, plus an evidence-based fix proposal
or explicit still-unknown cause; do not claim the live miss fixed without proof.

## Parent release: bounded early-callback correction

Parent independently reproduced all164diagnostic tests on Oct17. The separate
clock regression demonstrates a callback at wall due-1 consumes the only timer.
Release the smallest correction in the same isolated two-file scope: a current,
AH-open callback that is still cooling down re-arms through Schedule for the
remaining delay, preserving token invalidation, all admission checks and the
original900s wall-time cadence. Never force Start or busy-loop; no additional
ticker or overlapping recovery chain. Turn the reproduction into a passing
recovery regression, include cancellation of the re-armed callback and repeated
early callbacks without duplicate starts. Preserve the failing-before proof.
Actual cause of the observed live miss remains unproven until retained runtime
diagnostics establish it. Sol source review and parent integration still precede
loading this candidate in the real client.
