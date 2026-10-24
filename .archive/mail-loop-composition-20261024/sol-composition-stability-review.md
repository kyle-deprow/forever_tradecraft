# Sol review — composition fixture stability — READY

Scope reviewed: `.archive/PLAN-suite-stability-20261024.md`, the updated
composition and suite-refactor progress, the prior final composition/runtime
and suite-tuning reviews, and the sole frozen test in
`composition-stability-sha256.json`. Production source was unchanged and was
not re-reviewed. I did not run pytest, the game, services, or a database.

The reviewed test matched its manifest before and after inspection:

```text
5002473689a5a2bd2c42a8f855527afa7966d6c4423cc4499a57d5e49108deaf  tests/test_session_mail_loop_composition.py
```

Its device/inode, size, timestamps, mode, owner, and SHA-256 were unchanged
while inspected.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

## Stability and coverage findings

- The optimization is limited to character-only HUD cadence. Every character
  still enters through the real `X11Backend.action` lower boundary, emits its
  measured raw and delivered XI2 key sequence with the sealed modifiers, and
  mutates the focused command buffer (`tests/test_session_mail_loop_composition.py:420-494`,
  `:635-638`, `:665-680`). Open-chat, submit, Escape, and CTRL-F12 retain
  immediate semantic publication.
- A deferred batch is flushed only by the existing publication path. That path
  synchronizes current state into the real Lua client, calls `publish_agent`,
  renders the actual Agent frame, requires a fresh `PixelDecoder` result, and
  records the decoded snapshot (`:251-278`). The inherited real capture path
  also invokes this override before readback. There is no canned frame,
  `NO_CHANGE` admission, timestamp rewrite, production-method replacement, or
  timeout/deadline increase.
- The new independent oracle reconstructs each submitted command from the
  actual `type_character` effects and requires an empty trailing character
  stream plus a flushed batch for both submissions (`:1336-1353`). This
  complements the immediate lower-boundary comparison between the physically
  emitted command buffer and the production action's requested command
  (`:675-680`); it does not synthesize submission or state.
- The accepted causal proofs remain present: real Data.lua/Lua/pixel flow,
  canonical queue and route identity, nonzero route motion, retained model
  capture bytes/crop/hover evidence, actual Guardian/X11 actions, exact native
  deadlines, dry-run no-protected-call/no-arm/no-reload behavior, two fresh
  armed confirmations, one-second rate gate, competing-input refusal, two
  physical receipts, receipt-free asynchronous terminal observation, no third
  click, unchanged craft successor, and ordinary Guardian rearm to `WAIT_DUE`.
  The transplanted continuation-token assertions remain at first confirmation,
  second confirmation, asynchronous terminal, and final `WAIT_DUE`
  (`:1775-1777`, `:1830`, `:1847-1849`, `:1872-1875`).
- The saved locked configured-default result is **2 passed in 28.00s**, external
  **28.22s**, with 16 bounded work-stealing workers and no skips, versus the
  prior external 55.04 seconds. Static checks are recorded green. This is a
  fixture CPU/cadence correction; the parent final bare default run and source
  hash guard remain separate acceptance gates.

Status: **READY**.
