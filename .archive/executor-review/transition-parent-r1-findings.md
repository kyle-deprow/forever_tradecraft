# Parent inspection of first transition implementation freeze

Baseline reviewed: source-freeze-transition-r1.json and transition-implementation.diff (2118 lines). Existing affected tests reported passing by Luna; no fresh Sol/Opus review or native input released. Returned to the same Luna worker for one bounded completion outcome under PLAN-xtest-motion-transition.md.

Accepted concrete defects/gaps:

1. Calibration `_validate_sequence` compares the second native origin with the current raw endpoint instead of tracking the last accepted endpoint.
2. Helper `_seed_only` and `_positive` wait predicates still match native root origin against destination; final seed postquery omits owned-window validation. Audit every wait/path/duration/echo consumer.
3. `_controlled_echo_proof` searches older primary candidates and compares their native origins with echo endpoints. Guardian stores native origins in pending echoes and overwrites unfinished prior evidence. Normalize endpoints and enforce only the latest primary/full signature.
4. `_verify_current_xtest_profile` silently accepts absent evidence for legacy fixtures. Remove the production bypass and model complete evidence in fixtures. Per-action hierarchy must be freshly queried rather than copied from evidence.
5. Click implementation removed the precommit exact pointer endpoint/owned-window query required by the plan. Preserve it as well as postquery; the prohibition applies to profile subprocesses at that boundary.
6. Native xwininfo argv gate tests a list against a set of tuples and raises TypeError. Exercise `_run` itself with only the external process boundary doubled.
7. Profile parser counts class origins without validating measured source/class roles. Enforce complete measured structural identity.
8. Inspect normalized expected-event coordinate tuple shape and the native synthetic emitter's actual origin/requested/postquery records.
9. Required new regressions were absent from the first delta: decoder negatives, strict-next/origin progression, native driver entrypoints/postqueries, outside-origin refusal, profile drift, and actual echo producer -> evidence builder -> verify_seal -> DesktopDriver.arm -> Guardian.begin_action with unchanged MAX-to-zero proof. Existing fixtures and direct fake-evidence Guardian tests do not replace them.

Worker must update helper documentation and report exact new test names, strict hermetic results/private lease and scoped checks. Parent reproduces meaningful tests on a new unchanged freeze before independent Sol and actual Opus implementation review. Keep original failed native receipts unchanged.
10. A legitimate same-point click has no positioning/motion trace. Canonical action setup must permit that case with exact queried origin, press/release and endpoint ownership, without inserting fake motion or selecting a weaker evidence path.
11. During correction, parent parsed the exact retained native profile command stdout. The parser rejected it because the new expected class list invented XIScrollClass. Actual capture reports XIButtonClass followed by TWO XIValuatorClass entries (one per axis). Required captured-output parser regression remains part of acceptance.
12. Seal verification must reject missing/empty canonical motion transitions and require retained native origin/requested/result evidence; iterating an empty tuple is not validation. Existing direct-Guardian MAX-to-zero tests do not exercise the full required handoff.
