# Sol source review: addon schedule observability R2

Reviewed the full isolated-worktree candidate against `f2d3f2b`, canonical plan
SHA-256 `5852febd27ccf42a9576f2ea39aae42b461f1fef8f86fd58bfef995a2e143763`,
and the R1 source-review findings. The diff remains limited to the two authorized
files. Reviewed hashes:

- `addon/Crowley/Scanner.lua`: `75a8ca368ce1659d1c4a0e338770b11c2d0285161fb99478b2fdff23e98fee9e`
- `tests/test_addon.py`: `f3fe07faaba496437c67289b5f2f711ad3f716f26ceb435c1f1a9b1f8de14583`

The parent independently reports 166 tests passing in 14.57 seconds plus scoped
Ruff, format, and diff checks. This was a read-only review; I did not run tests,
Lua, the addon, the GUI, or game input, and did not mutate Git or the candidate.

## Must-Fix

None.

The R1 chat-noise blocker is closed at `addon/Crowley/Scanner.lua:980-989`:
an early internal timer callback records `due_refusal`, creates exactly one
remaining-cooldown timer through `Schedule`, and returns without printing. Manual
`/scan` during cooldown still prints the existing notice. The repeated-early test
at `tests/test_addon.py:1194-1239` now proves three internal callbacks create no
chat, no query, no start, and only one current re-arm each before lifecycle
cancellation invalidates the final callback.

## Should-Fix

None.

The R1 creation-evidence issue is closed at `addon/Crowley/Scanner.lua:952-968`:
the callback is constructed first, `C_Timer.After` must return successfully, and
only then is `timer_create` retained. The error-path regression at
`tests/test_addon.py:1242-1251` proves a throwing timer API leaves the request
evidence but no false creation event.

## Nits

None.

The full candidate preserves the 900-second wall-time cadence, timer-token
invalidation, AH-close/logout/fence cancellation, plan and queue admission,
single-sweep exclusion, persisted `lastSweepStart`, catalog and query ordering,
and the existing Agent/status and scan-wire schemas. The separate SavedVariables
trace remains bounded to 64 fixed-schema events with bounded strings, overflow,
wall/uptime timestamps, and per-load correlation. The controlled early-callback
case is fixed; the cause of the observed live missed scan remains explicitly
unknown pending retained live diagnostics.

STATUS: READY
