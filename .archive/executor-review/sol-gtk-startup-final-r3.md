# Sol GTK startup final r3 test-closure review

Serving model ID: not exposed to this worker. The session identifies the agent only as Codex based on GPT-6, so I cannot accurately claim a more specific serving ID.

## Scope and evidence

I reviewed only the 153-line `gtk-test-closure-r1.diff`, its 43-path freeze manifest, `gtk-startup-r14-arbitration.md`, and the actual Opus r14 report. I did not rerun tests, inspect production implementation, issue GUI/native input, inspect private files, or modify anything except this report. The preservation artifact establishes that the other 41 paths remain byte-identical to the Opus-approved r14 freeze. The parent-reported nine focused passes and global Ruff/format/diff checks are supporting evidence rather than checks I independently ran.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

## Closure assessment

The parameterized partial-identity regression now exercises both authorized boundaries through `OwnedGtkCalibrationWindow.create()`:

- an unterminated partial line with its writer still open reaches the finite deadline and requires the exact `identity was incomplete` error;
- the same partial line followed by EOF while the fake child remains live requires the exact `identity channel closed before identity` error.

Both variants assert the exact `terminate` then `wait` lifecycle, a reaped process, and exactly one registration cleanup. File descriptors are closed once according to whether the writer remains owned by the fixture. This closes the remaining Sol r2 and Opus r14 test requirement at [`tests/test_session_native_regressions.py:1535`](/home/dev/repos/crowley/tests/test_session_native_regressions.py:1535).

The all-mode helper regression now uses `4_194_304` and `4_194_305` for its modeled process groups at [`test_owned_gesture_proof.py:530`](/home/dev/repos/crowley/.archive/executor-review/test_owned_gesture_proof.py:530), avoiding collisions with live Linux PIDs while preserving distinct motion and button identities. The lifecycle fixture's added one-line, same-title, direct-root sibling matches the observed unmapped startup shape and remains non-certifying.

The test-only delta introduces no production or acceptance-contract change. Source readiness remains separate from the forthcoming owned seed: GTK/Mutter placement, live mapped/reparented certification, queried initial pointer ownership, native gestures, game, physical-human, camera, movement, and cadence remain unproven until their respective authorized live gates run.

STATUS: READY
