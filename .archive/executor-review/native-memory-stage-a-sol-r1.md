# Sol source review R1 — native memory failure archive Stage A

Candidate reviewed: `/home/dev/.cache/crowley/worktrees/native-memory-failure-20261017` at base `8d06cd0`

Verified inputs:

- plan `.archive/PLAN-native-construction-isolation.md`: `8b9fd740a252cf7319a8414d9557644936a199e618116befa77c2c2c089d2286`
- Sol plan review `.archive/executor-review/native-construction-isolation-sol-plan-r1.md`: `e612224cf44c4b00f18f35faecb9df4cfe9ee6a383286c3d93e7d33bcb624181`
- freeze `.archive/executor-review/native-memory-stage-a-r1-freeze.json`: `55e86f1b4c87c84aad6650683fd016a623ed77bc51542728696a9cbd42054d1c`
- `src/crowley/session/calibration.py`: `e87e844bc0428f76f2d2c8053e58017651e5ea7e285164bac56ba33bbb39630c`
- `src/crowley/session/daemon.py`: `47702e23606ec9f42a4ce3a54b1be400f64f715f617fa48dc0507782ce189929`
- `tests/test_session_native.py`: `5519aa12759042935fbab00108673452f3cc4a5b8e46a2f4054e712843026e35`
- `tests/test_session_native_regressions.py`: `967123b09c1544aba93aac74ffe1625eb271d00910c55dcbe9d7edbdc8a915be`

The implementation satisfies the bounded Stage A contract:

- `src/crowley/session/calibration.py:1632-1696` constructs and verifies the complete final measurement before entering the over-limit branch. Final status or identity failure cannot call the archive callback. The pending token remains one-use, and the completing token exists only for the synchronous callback lifetime.
- `src/crowley/session/daemon.py:975-1017` injects the optional callback only into the daemon-created production meter. Direct meters preserve their previous behavior. Callback or receipt failures set only a fixed private token and are suppressed before the exact original `CalibrationError`, without exception chaining.
- `src/crowley/session/daemon.py:1019-1088` verifies the measurement, over-limit decision, current `NATIVE_CALIBRATION` state, exact meter ownership, fresh client/process identity, and the meter's completing token before publication. The closed payload has `qualifies: false` and does not enter handshake, status, calibration evidence, or qualification counters.
- The canonical measurement digest and outcome identity at `src/crowley/session/calibration.py:1230-1289` bind the full measurement and exact failure. The receipt is built from the journal-returned positive ordinal; the journal's existing `outcomeId` replay gives one immutable record and the same ordinal on an identical retry.
- The focused tests cover ordering, exact complete values, final-read/identity refusal, invalid callback admission before proc ownership, production binding, replay idempotence, 0600 publication, invalid receipt, append failure, original error preservation, privacy, and nonqualification. The reported transient accessibility-bus warning is in an unchanged compiled-GJS fixture and reproduced cleanly on both the unchanged baseline and candidate, so it does not identify a Stage A defect.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
