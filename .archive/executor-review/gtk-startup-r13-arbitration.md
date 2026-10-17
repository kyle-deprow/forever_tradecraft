# GTK review r13 arbitration

Actual Opus claude-opus-5-5 exited0/NEEDS WORK; Sol final-r1 NEEDS WORK.
Both reviewed unchanged gtk-startup-final-r3. No native input released.

Accept and batch in the existing five-file startup/helper fence:

1. Alternate-only same-PID/title wmctrl identity must be hard, not pending (both M1).
2. Validate/retain published admitted-client process identity before later startup
   pending branches (Sol M2). Do not introduce new process identity policy.
3. Real create/verifier lifecycle with external command/clock doubles must traverse
   unmapped/noextents, viewable/directroot/tiny unrelated sibling, then ready;
   observe every command's decreasing remaining timeout. Include never-ready
   exact-once unregister/reap and late-final-certificate cleanup (Opus M2).
4. Reject >1 non-client frame children before missing helper/property pending;
   when helper XID is published, reject already-known unexpected children before
   missing companions. Preserve one possible not-yet-published helper as pending.
5. Helper's _distinct_target_point chooses farthest safely inset quarter endpoint
   from the actual local start. Do not modify _seed_endpoint or production planners.
   Cover near-left/right-quarter origins as well as center.
6. Drive all three proof modes using external doubles and real planners. Capture
   same-window start, meaningful endpoint, pinned motion/click PointerTarget;
   post-motion pointer must not cause replanning. Existing utility tests remain.
7. Recorder handles malformed matching wmctrl XID without changing returned stdout
   or issuing queries; retain a scoped parse diagnostic. No unrelated metadata.
8. Extend structural tests over startup/strict modes; real unmapped post-ready
   fails hard. Strengthen partial-identity cleanup assertions. These are tests.

Minor cleanup directly in already-touched regions is allowed: remove redundant
create timeout argument when passing deadline (adapt tests to assert real command
budget); describe post-ready verify budget/error clearly; identity EOF while
child lives is a hard channel failure with cleanup, not a busy-spin. Preserve
single finite deadline and exact startup ownership. Do not refactor unrelated code.
No general stdout protocol redesign or extra diagnostics/query policy expansion.
Existing exact-XID/wrong-PID proof retains final error but is deliberately not
broadened into recorder enumeration of unrelated rows. Nits are not permission
for additional source scope. Parent fixes docs/assumptions separately.

After one implementation batch, parent reproduces affected checks and freezes;
Sol and Opus r14 review correction closure on that unchanged delta. Full prior
transition subsystem is approved/frozen; no unrelated full DB rerun.
