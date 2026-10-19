# Expose actual native restoration failure

Live operator-assisted preflight reached Restore handler: SavedVariables wrote
restore_pending at03:00:37UTC, but new load has no Agent pixels and Restore stays
visible. Public recovery-complete expires. Installed addon hashes match main.
Exact allocation/publication error is currently discarded in Agent initializeLoad
restore_pending branch. Root model reproduced permanent failed/surfaceless state
when UnitPosition is unavailable at ADDON_LOADED; this is a hypothesis, NOT a
confirmed live cause. Don't change lifecycle timing based solely on that model.

First bounded implementation owns addon/Crowley/Agent.lua and tests/test_addon.py
ONLY. Add compact diagnostic chat at the three existing restore startup failure
branches: createSurface allocation, first checked publication, second checked
publication. Capture pcall failure reason and print phase+exact causal error.
Do not change acceptance, retries, markers, timers, fences, construction, normal
startup, dimensions, decoder or native protocol. Retain failure cleanup first;
diagnostic errors must not replace causal state/cleanup or make input admissible.
Test real Lua failure injection at each branch asserts correct phase/reason and
existing failed/surfaceless/recoverable marker/fence behavior. Distinguish second
publication failures by exact count. Preserve compact style, no new framework.

Read full plan before editing. Don't commit/reset/stash/revert anyone's edits.
No GUI/service/hostaddon installation. Parent owns installation and git after
parent reproduction + Sol review. Actual Opus checks final executor changes
when behavioral correction is made; this initial diagnostic has no executor
behavior change. Run scoped addon tests, scoped ruff and diff check; full logs
private0600/evidence0700. Report actual commands/results/exact hashes/fence.
DONE only diagnostics implemented and checks green.

Then sole GUI owner can deploy exact reviewed diagnostic source and perform
one bounded source-approved Restore with fresh public recovery ticket while
capturing the earliest post-reload chat. Root arbitrates a separate behavioral
fix against that actual error. No repeated blind Restore attempts.

## Diagnostic retention correction after live attempt

Three diagnostic chat messages alone were not observable after reload/trade
scroll. Root authorizes retaining plain-string `ns.db.agentRestoreFailure` with
exact phase+cause in the same three failure branches AFTER cleanup BEFOREprint.
Clear it when a fresh restore_pending initialization begins, preventing stale
error after successful restoration. Do not alter other startup paths, native
marker, fence, retry/timing/admission or scan payload. This is optional private
SavedVariables diagnostic metadata, not a success flag. Tests retain all3phase
failure guarantees and successful fresh restoration clears stale diagnostic.
Then soleGUI may issue short local `/run print(CrowleyDB.agentRestoreFailure)`
to expose exact error without a fragile startup-chat capture/long history query.
Same two owned files, checks and scope fence. Parent + Sol review before install.
