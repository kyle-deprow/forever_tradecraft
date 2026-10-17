# Sol review: private native handshake helper r3

This review was limited to the R3 Enter World pulse delta in the frozen private
helper and its dry tests. The helper hash matches
`bf79d703cc9b98fc7e0842d119e69cbbfa5539f02456f8d5083d4629bdeee2d0`
and its mode is `0700`. I did not run the helper or tests, capture the game,
dispatch input, call native operations, or change source, configuration, or
services.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

The new pulse preserves the accepted R2 phase contract. Before movement it
requires the bound identity and the same-generation running native operation at
`bootstrap_ready/nativeBootstrapReady`. After movement it repeats both checks,
reads the actual root pointer coordinates and reported X11 target, and rejects a
coordinate mismatch or a target outside the sealed client event-XID set. It
then repeats identity and phase validation immediately before admitting the
press. The original and refreshed identity fingerprints include geometry and
the exact event-target set, so using the retained identity for the membership
check does not weaken the fresh proof.

At
[`native-handshake-once.py:356`](</home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-handshake-once.py:356>),
the helper marks button 1 as owned before invoking `mousedown`. The `finally`
path then attempts the matching `mouseup` without a generation or phase check,
including when press dispatch, the 150 ms hold, or the native operation fails or
is revoked. Operation and release failures are retained separately, both
monotonic release timings are recorded, and an operation failure remains the
raised primary error while a release-only failure is also surfaced. This is the
required cleanup ordering for an input item the helper may have emitted.

The handshake replaces only the prior instantaneous Enter World click with this
guarded pulse. Later hold, measure, 100-update, and resume behavior remains
unchanged. The dry tests exercise the complete successful ordering, refusal
after movement and before press for wrong coordinates and a foreign target, and
an injected hold failure followed by the owned release. The retained status and
handshake-entry tests continue to cover dynamic generation binding and exact
phase/flag admission. Parent reports the combined dry suite passing in 0.1
seconds. No live preflight or native attempt was made, and the change does not
claim that zero dwell was the sole cause of the earlier failed click.

STATUS: READY
