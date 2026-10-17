# Sol source review: addon schedule observability and early-callback correction R1

Reviewed the released canonical plan at SHA-256
`5852febd27ccf42a9576f2ea39aae42b461f1fef8f86fd58bfef995a2e143763`
and the isolated-worktree diff from `f2d3f2b`. The candidate is limited to the
two authorized files, with these reviewed hashes:

- `addon/Crowley/Scanner.lua`: `b14d2d67d3ee3e1fac0d127e743d444fae0ec160fc75be44149451cbaf74bbde`
- `tests/test_addon.py`: `08cadca84f0cc15fa3f4f3f79a371e9ade392f00321b3fbaa5a156e430906ebd`

The preserved failing-before artifact has SHA-256
`4e306739452f777c9a78e81243eef13802fae8cfb04722270ec7c66e4eef66fa`.
It demonstrates only the controlled early wall-clock callback: the callback at
wall due-minus-one consumed the prior timer. It does not establish the cause of
the live missed sixth scan, and neither the candidate nor this review claims
otherwise. The parent independently ran 165 tests in 12.84 seconds. This was a
read-only source review; I did not run tests, Lua, the addon, the GUI, or game
input, and did not mutate Git or the candidate worktree.

## Must-Fix

1. **`addon/Crowley/Scanner.lua:979-987` turns repeated early callbacks into repeated chat output.** Every timer callback that is still one or more seconds early calls `ns.Print("scan due in ...")` after re-arming. The new regression at `tests/test_addon.py:1194-1237` deliberately exercises three consecutive early callbacks, so the candidate produces three user-facing cooldown messages in that bounded case; a sustained wall/timer mismatch can continue doing so once per callback. This violates the plan's no-chat-spam requirement and changes a background recovery mechanism into visible repeated output. Keep the diagnostic `due_refusal` event and the single remaining-cooldown re-arm, but suppress the cooldown print when `source == "timer_callback"`; retain it for an operator's manual `/scan`. Extend the repeated-early regression to assert that internal callbacks add no cooldown chat messages.

## Should-Fix

1. **`addon/Crowley/Scanner.lua:952-955` records `timer_create` before calling `C_Timer.After`.** If the timer API raises, the retained trace says a timer was created even though the call did not complete. This weakens the central distinction between a schedule request and actual timer creation that this diagnostic slice is meant to establish. Build the callback first, call `C_Timer.After`, and append `timer_create` only after that call returns successfully; alternatively use distinct fixed `timer_request` and post-call `timer_create` events. Add a focused error-path assertion so a failed timer API call cannot leave false creation evidence.

## Nits

None.

Apart from those points, the correction is appropriately small. It preserves the
900-second wall-time cadence, consumes each callback before creating one remaining-
cooldown timer, keeps token invalidation and AH/lifecycle/fence cancellation,
rechecks plan and storage admission through `Schedule`, prevents overlapping
sweeps, and leaves the Agent/status and scan-wire schemas unchanged. The separate
SavedVariables trace uses fixed event fields, bounded strings, a rolling 64-event
cap with overflow count, wall and uptime clocks, and a per-load correlation key.
The focused tests cover timer-only start, persisted reload scheduling, lifecycle
and fence invalidation, plan/storage refusal, active-sweep exclusion, bounded
trace shape, the failing-before clock split, repeated re-arms, cancellation, and
single eventual start.

STATUS: NEEDS WORK
