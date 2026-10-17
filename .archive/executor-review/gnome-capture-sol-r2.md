# Sol review: GNOME capture completion r2

This rereview was limited to the accepted R1 corrections in the frozen
`src/crowley/session/driver.py` and `tests/test_session_capture.py` delta. The
reviewed hashes match `gnome-capture-freeze-r2.json`: driver
`14ae6be4a901a17e396e68ac4501238db3d1cc0118c8c34ad6f7107fbcfacfa7`,
capture tests `9aa1555f22d3c781253092a0903aec1919c7435f32ea78cdbb7b27a81f66c9d7`,
and the existing driver-actions tests remain unchanged. I did not run tests,
operate the GUI, or change source, configuration, or services.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

The retained revocation epoch at
[`driver.py:787`](../../src/crowley/session/driver.py#L787) is incremented under
the same process lock used for the final publication boundary. Capture checks
the exact epoch before and after initial identity work, while waiting for the
cross-process lock, while waiting for the asynchronous image, after final
identity work, and again while holding the process lock immediately before
`os.replace`. A revoke therefore orders either before publication and rejects
the old capture, or after publication; clearing the cancellation event for a
successor cannot revive an earlier epoch. The delayed-writer/rearm and
lock-contention/rearm tests exercise both formerly reachable gaps.

Each request now creates its GNOME output inside a fresh mode-`0700` directory
on the destination filesystem. The exit path first atomically renames that
directory, which removes the original pathname before recursive cleanup. A
writer that has not opened its destination can no longer recreate the retired
path; a writer that already opened it remains confined to the private renamed
directory and cannot affect the destination or a successor. The delayed
creation test waits beyond the child delay, proves the old destination remains
unchanged and no attempt path reappears, then proves a successor succeeds.

The image validator preserves the existing desktop-crop contract by accepting
a complete PNG at least as large as the verified client. A complete non-PNG or
undersized PNG is rejected immediately, while absent, short, or not-yet-
decodable PNG data remains eligible to complete within the unchanged absolute
deadline. Tests cover the larger-desktop path and both terminal refusals. The
real child-process refusal budgets were raised to one second without changing
production bounds.

Parent reports 42 focused tests passing in 12.40 seconds and scoped Ruff and
format checks passing. As recorded in the freeze, no real compositor capture or
native calibration was run in this source-verification phase.

STATUS: READY
