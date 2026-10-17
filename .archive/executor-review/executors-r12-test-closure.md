# Final test-only closure after actual Opus r12 / Sol final-r3

Actual claude-opus-5-5 CLIexit0 STATUS READY; no production defect, all five
accepted requirements closed. Sol final-r3 has no Must-Fix and one remaining
required negative isolation issue. This release strengthens only tests, with
no change to the production/helper implementation reviewed by Opus. Preserve
source-freeze-transition-r12-final-r2.json and both complete reports.

Same Luna owns ONLY these three files for this final closure:
- tests/test_session_native.py
- .archive/executor-review/test_owned_gesture_proof.py
- tests/test_session_driver_actions.py (only forged-plan explanatory comment)

Complete together, no other edits:
1. In the re-fingerprinted seal negatives, keep transition/profile valid and
   mutate primary Motion event_proof root XID and event XID separately; expect
   exactly the absent-from-event-proof rejection. Also cover transition event
   XID and forwarded echo event XID, independently from existing root cases.
2. Both real helper button-flow refusal cases must record backend._run as well
   as _run_chain, assert no button backend call, no synthetic-button phase or
   phase-synthetic-button stage. This must catch moving the ownership check
   after phase entry or worker launch, not only removing it accidentally.
3. Split transition modifier tuple/effective-state mutations so each binding
   is independently verified. Add a zero-displacement PREFIX builder negative
   (query remains nonzero) to exercise that guard independently of zero query.
   Narrow the caller-substitution regex to its actual error. Add the one-line
   comment explaining the camera plan intentionally bypasses its constructor
   to exercise defensive driver validation.

Do not remove redundant source guards, change runtime messages, expand parser
messages, alter producer endpoint selection or make any production/helper edits.
No GUI/game/service/settings/profile/tool/git work. Parent owns this document,
plans/freezes/reports. Use strict hermetic runner, unset DB URL, unique private
lease. Run all changed negative functions + helper file + defensive camera case,
scoped Ruff/format/compile. Report actual results and freeze. No repeat full
affected batch is needed solely for these assertion refinements.

Parent will independently reproduce these cases and Sol will verify closure of
its specific finding and the Opus test-strength findings. Opus r12's runtime
implementation approval remains applicable because those source bytes must stay
identical; a further Opus implementation round is required for a meaningful
runtime change, not this test-only refinement. The currently running full strict
DB suite validates unchanged runtime source and the r12 suite; the added isolated
assertions receive their own focused verification. Do not restart that full run
only for these test assertions. This follows the requirement to repeat checks
only where new changes justify them. Final native release still awaits full
suite success, focused closure and exact runtime source hashes.
