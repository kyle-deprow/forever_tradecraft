# Native readiness review, round 3

Sol verdict: MAJOR ISSUES. Human sample and game input remain withheld.
38 focused native tests pass; actual native workflow remains unsafe/unexecutable.
Native sources stayed unchanged during review. Lifecycle clarification at the
end of PLAN-repeating-scans.md applies: lazy controls and pre-Agent handshake.

## Must fix

1. Generation check and dispatch still race. Driver calls backend.action after
   begin_action without atomic admission; release_held_input clears cancellation.
   Injected revoke immediately after begin_action still dispatched focus_game
   and open_chat with guardian unarmed. Popen->registration gap also permits
   revoke to see no process, clear cancel, then process starts. Fix centrally:
   generation admission and nonblocking spawn/registration share one fence,
   blocking wait stays outside it, canceled generation never revives on release.
2. Delayed calibration action executes after 0.25s but human can respond in120s;
   ordinary wait executes it and guarantees rejection. Already-running timer
   holds calibration lock through blocking focus, delaying revoke and completing
   after takeover. Use genuine due-action cancellation proof without blocking
   revocation or requiring subsecond human response. Bound counters per run.
3. Synthetic readiness still checks only delivered presses then validates
   complete releases. Await all complete raw/delivered press/release records on
   actual open stream before readiness, not batch fixtures.
4. All-six controls in one5s batch is impossible; backend measure_pointer_anchor
   is undefined. Follow lazy actual-scene lifecycle, implement real producer.
   MeasuredAnchor accepts empty facts/unsealed caller assertions; runtime trusts
   only coords+identity. Bind full named control/scene/capture/target evidence and
   validate it immediately before action, retaining reviewable proof.
5. Untyped callback before HWM doesn't prove Agent absent; current bootstrap
   already observes rendered frame. Implement actual absence/baseline->visible
   operator bootstrap-ready->authorized load->101samebootframes handshake.
   Render observation metrics must bind runner's decoded boot/seq/CRC/capture.
6. Native fingerprint omits process start/boot/CRC/render/HWM/capture facts.
   verify_seal doesn't recompute either fingerprint; dataclasses.replace with
   synthetic_key_source=999,event_proof=() retains a passing seal. Canonically
   hash every evidence fact and recompute during verification/durable validation.
7. Runtime accepts arbitrary first modifiers/detail rather than expected state.
   Nonzero delivered modifiers=(1,0,0) were accepted. --clearmodifiers emits
   release/restore events not modeled or tracked. Pin actual expected key detail,
   modifier state and physical stream; reject unowned modifier effects. Delivered
   Enter/Leave require actual owned-target proof, not missing target allowances.
8. GTK stays 'verifying' forever; transition actual UI to human-input prompt only
   after full synthetic proof, synchronized with observable ready status.
9. Close silently returns after three failed releases with held/lease/watchdog
   alive. Preserve independent release fallback but report/block incomplete
   close. Empty focus marks held with zero keys/buttons, watchdog then cannot
   release and loops forever. Distinguish active process from held keys/buttons.

## Should fix / API

- Snapshot/reset calibration execution/due counters per operation; failures must
  not poison future explicit retries.
- Implement published verify_named_action(..., observation=None) keyword.
- Add actual barriers for begin->dispatch and spawn->registration revoke;
  already-running due callback; press-before-release; modifiers; tampered seals;
  failed close; and fingerprint fact changes. Do not fake immediate full traces.

## Ownership / checks

Native owner: four native source files and tests/test_session_native.py only.
Lead: actual CLI/status/singleflight, preconstruction handshake, scene producer,
complete durable evidence and engine3 fixes. Independent test owner alone owns
two independent regression files. Coordinate APIs directly, no GUI/services/
private config/prodDB/commits. Re-run meaningful tests/lint/format/diff and
Sol review. Existing passes do not authorize physical test.
