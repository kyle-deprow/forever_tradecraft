# Sol GTK startup final r1 review

Serving model ID: not exposed to this worker. The session identifies the agent only as Codex based on GPT-6, so I cannot accurately claim a more specific serving ID.

## Scope and evidence

I reviewed the six-path `gtk-startup-final-r3.diff` against `gtk-startup-source-snapshot`, the 43-path freeze manifest, `PLAN-gtk-startup-readiness.md`, `gtk-startup-diagnosis-r1.md`, and `gtk-startup-parent-r1-findings.md`. I did not run tests, issue GUI/native input, inspect private files, or modify source. The parent-reported 44 focused GTK/workflow passes, unchanged 25 helper passes, and global Ruff/format/diff checks are supporting evidence rather than results I independently reproduced.

The delta stays inside the authorized GTK startup, passive recorder, same-window proof-target, affected-test, and parent-document fence. It preserves the previously approved emitter, evidence, Guardian, driver admission, runtime, and service implementation. The absolute create deadline begins before process/admission work, is reused for identity publication and every verifier command, rejects late certificate completion, and keeps one admitted child until reap/unregister. The nonblocking identity pipe, fresh whole verifier attempts, strict post-ready mode, toolkit-boundary MOUSE placement test, direct-root/tiny-frame regression, and present-property/frame-child hard-failure tests address most of the eight required boundaries.

## Must-Fix

1. **A conflicting same-process/title `wmctrl` identity is still startup-pending when the published XID is absent.** [`src/crowley/session/calibration.py:2647`](/home/dev/repos/crowley/src/crowley/session/calibration.py:2647) adds every other row with the admitted PID/title to `client_matches`, but [`:2649-2652`](/home/dev/repos/crowley/src/crowley/session/calibration.py:2649) calls `pending_or_hard()` whenever `xid_rows` is empty, without first rejecting those conflicting matches. Thus a listing containing only `0xOTHER ... <pid> ... CROWLEY INPUT CALIBRATION ONLY` for a helper-published `xid` consumes the readiness deadline as absence. This is a present contradictory identity, not an allowed “not in wmctrl yet” state. Permit pending only when both the exact-XID rows and same-PID/title matches are absent; otherwise fail immediately. Add the missing alternate-only case alongside the existing same-XID-wrong-PID and exact-plus-second-window cases.

2. **Missing frame readiness can still mask an unavailable admitted-client process identity.** The first pending frame-property exit is at [`src/crowley/session/calibration.py:2761`](/home/dev/repos/crowley/src/crowley/session/calibration.py:2761), while `_process_identity(pid)` for the owned client is deferred until [`:2817-2820`](/home/dev/repos/crowley/src/crowley/session/calibration.py:2817). A live process whose published PID/XID properties are established but whose `/proc` identity is unavailable can therefore be retried for the full startup budget whenever a frame property or helper child is also missing. This leaves the client half of the parent’s explicit “published client/frame process identity errors are hard” correction incomplete. Validate and retain the client identity immediately after its exact XID/PID properties, before any later readiness-pending branch; add an unavailable-client-identity plus missing-frame-companion regression that proves one attempt and cleanup.

## Should-Fix

1. **The passive recorder can change production behavior on a malformed matching `wmctrl` row.** [`owned-gesture-proof.py:109-121`](/home/dev/repos/crowley/.archive/executor-review/owned-gesture-proof.py:109) applies `int(fields[0], 16)` after checking PID/title but without validating the XID token. A malformed matching row raises `ValueError` inside the recorder after the production command succeeds, so the wrapper does not return that command's exact stdout to the verifier. Keep diagnostic parsing inert by validating/catching the token and emitting a scoped parse-error record; test that the recorder returns the original stdout and adds no commands for this case.

2. **The same-window target regression does not cover the three proof-mode call sites it is meant to protect.** [`test_owned_gesture_proof.py:433-477`](/home/dev/repos/crowley/.archive/executor-review/test_owned_gesture_proof.py:433) calls `_distinct_target_point`, `_target_plan`, `_trajectory`, and the click planner directly. It proves the helper composition for two near-center origins, but it would still pass if `_positive`, `_cancel_midpath`, or `_cancel_midbuttonhold` later recomputed or failed to pass that plan. The current production call sites are wired correctly. Parameterize external doubles over all three modes and capture their production planner inputs, asserting a meaningful distinct endpoint and the same pinned target wherever motion and click coexist.

## Nits

None.

## Readiness boundary

The MOUSE call remains an initial GTK placement request only; the certified native rectangle/window and later pointer query remain authoritative. No unit or review evidence here constitutes the unreleased GTK seed, native gesture, game, physical-human, camera, movement, or cadence proof. The two hard-vs-pending identity gaps should be closed before the source is released for that seed.

STATUS: NEEDS WORK
