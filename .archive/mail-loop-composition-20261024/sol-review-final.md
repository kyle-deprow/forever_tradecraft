# Sol review — mail-loop composition test final — READY

Reviewed frozen test:

- `tests/test_session_mail_loop_composition.py`
- SHA-256: `d58b6198df27971ce29c6409919e4bc61606057e8a8af123dedf64b150149fe8`
- Manifest: `.archive/launch-readiness-20261023/mail-composition-final-sha256.json`

The file and its device/inode, size, timestamps, mode, owner, and SHA-256 were
unchanged while inspected.  I did not run pytest during the parent full-suite
hash guard.  The saved final locked result is **2 passed in 97.65s**, external
**97.94s**, with both full lifecycle cases green.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

## Round8 oracle finding closure

- The executor operation is now correctly modeled as the production
  serialized 60-second physical owner; the separate fixed 30-second
  postcondition remains traced and reserved rather than being folded into a
  synthetic 90-second physical deadline.
- The observational native-clock wrapper records the first actual source
  sample used after the executor operation scope is installed and returns that
  exact value unchanged.  The `_require_motion_interaction` wrapper observes
  the already-created `_motion_deadline_local.deadline` and forwards the
  original args/kwargs untouched.  It injects no precondition or guard result.
- Expected and observed values remain separate: the test independently
  calculates `min(serialized_owner_start + 60, caller_deadline,
  cycle_deadline)` and requires the recorded production owner deadline to equal
  it.  It does not infer the owner from a first nested helper, widen it to 90
  seconds, restamp a clock, or allow an arbitrary shorter outer bound.
- Each postcondition reads the daemon's existing per-attempt deadline from
  `_mail_cycle_wait_deadlines` before forwarding the real observer call.  It
  never derives a new poll-start-plus-30 deadline.  All scoped driver, native,
  and action records still require a non-null finite deadline no later than the
  exact operation owner and fixed cycle cap; legitimate nested intersections
  may only shorten that already-proved outer bound.
- All prior real Lua/Data.lua/PixelDecoder, public IPC, route/motion/hover,
  lower keyboard, Guardian/X11 action, physical receipt, asynchronous terminal,
  no-third-click, unchanged successor, once-per-ACK, and ordinary rearm oracles
  remain intact.

This test verdict does not replace parent full-suite verification or live
qualification.

Status: **READY**.
