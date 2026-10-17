# Sol plan review: addon schedule observability R1

Reviewed plan SHA-256: `f04790c3fb9b2d23b8dc6bfd36cbd4d17c2735e819d96976df620df87f6b686f`.

The plan is correctly limited to diagnosis and timer-path regression coverage. It preserves the unknown live cause, does not infer timer ownership from the HUD cooldown projection, and does not authorize a scheduling fix before root inspects a reproduction. The detached worktree exists and its owned files match the reviewed primary sources.

Source hashes inspected in both `/home/dev/repos/pegasus` and `/home/dev/.cache/crowley/worktrees/addon-schedule-20261017`:

- `addon/Crowley/Scanner.lua`: `b2843e42d1edf4d9ed4df1b6214928cf12baadde03108b65fd10912fdfc0b218`
- `tests/test_addon.py`: `b29fe821fb81303b586b08c9e4be0317b71611378477dfab2cb283d1c58394ed`
- read-only shared `tests/wow_harness.py`: `7228357e7a1f24703195169db3879f0d64da8d8a0e16a56787786e4c8f3037d9`

Interface checks:

- `Scanner.Schedule()` at `addon/Crowley/Scanner.lua:865` currently performs silent early refusals, increments a private token, and creates `C_Timer.After` without retaining observable timer evidence. The requested bounded SavedVariables trace can record each decision and callback without changing the existing scheduling outcome.
- `Scanner.Status()` at `addon/Crowley/Scanner.lua:984` derives `scheduled` only from AH-open plus positive wall-clock cooldown at `addon/Crowley/Scanner.lua:1006`; the plan correctly keeps this projection separate from timer creation and callback evidence and leaves the status wire schema unchanged.
- `test_start_cadence_and_no_overlap()` at `tests/test_addon.py:989` advances to due and fires `AUCTION_HOUSE_SHOW` at `tests/test_addon.py:1000`, which calls `Scanner.Schedule()` again. It does not prove that the timer created after the prior sweep starts the next sweep by itself. The requested timer-only regression closes that gap.
- The existing harness timer queue uses `_now` at `tests/wow_harness.py:240` and exposes bounded timer advancement at `tests/wow_harness.py:1260`. `tests/test_addon.py` can override the Lua `time()`/`GetTime()` globals locally to model separate wall, uptime, and timer clocks without editing the shared harness.
- Token increments already occur on AH close, logout, scan start, and the pre-logout fence. Recording logical cancellation and later stale-token callback discard is compatible with the existing `C_Timer.After` API and does not require a timer handle or fallback ticker.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
