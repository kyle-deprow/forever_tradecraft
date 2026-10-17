# C integration review

Reviewer: gpt-5.6-sol, xhigh, read-only. STATUS: MAJOR ISSUES.

Accepted Must-Fix:

1. Camera positioning and held-drag motion share one trace, while button press
   requires that entire trace already complete. Encode explicit positioning,
   press-at-start, motion-while-held and release-at-end phases and coordinates.
2. Game target certification does not pin its managed-frame relationship.
   Parent native-tree evidence shows the current fullscreen outer is directly
   under root, with its one Wine client child. Pin that observed relationship
   and fail unknown reparenting; do not add guessed generic WM acceptance.
3. Keymap parsing flattens shift levels; motion re-reads a live map instead of
   proving the binding against sealed unmodified level-zero detail.
4. begin_action publishes planned held inputs before process/emission admission.
   Separate planned action expectations from actually admitted physical holds.
5. Two-trajectory camera, backend, Guardian and CLI budgets disagree. Propagate
   one absolute operation deadline through dispatch, completion and cleanup;
   the client wait must exceed the server bound. Capture/model work must also
   obey the same deadline, rather than checking only before and after a fixed
   fifteen-second screenshot call.
6. Tests omit production run_camera_drag/run_motion_key_hold and the required
   IPC/controller/lease/driver path. Add real entrypoint tests with only true
   external-boundary doubles; cover malformed phases, coordinates, keymaps,
   missing/late/wrong-target events, cancellation and deadline behavior.

No separate Should/Nit findings. Controller/lease separation, reconciliation,
interaction exit and incomplete-finish revocation were observed correct.
Mutable daemon/motion/model paths await later integration review.

Parent reproduces the native-tree assertion from private unchanged-production
GTK receipt diagnostics1792141559. Game event targets must never include root,
advertised WM metadata helpers, unrelated siblings or arbitrary ancestors.
Current owned-GTK certificate PASS is independent of this game certificate.
