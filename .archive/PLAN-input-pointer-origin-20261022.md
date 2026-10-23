# Input calibration pointer ownership and failure evidence

The user returned for calibration after scan274. Native73 passed, recovery74
passed, and input75 refused before human readiness because the pointer origin
failed ownership or client bounds. The failure lacks the actual query tuple.
Do not claim either conjunct as the historical cause.

## Scope and order

Implement offline in `/home/dev/.cache/crowley/worktrees/input-pointer-origin-20261022`.
Own only:

- `src/crowley/session/driver.py`
- `src/crowley/session/calibration.py`
- `tests/test_session_native_regressions.py`
- `tests/test_session_input_diagnostics.py`

1. Align synthetic calibration origin and endpoint hit-window checks with the
   exact CalibrationTicket certified XID set. Preserve measured client bounds,
   requested endpoint equality, ticket identity/focus/revalidation, nonzero
   displacement, Guardian, curved pointer execution and fixed click cadence.
   A frame hit outside client bounds, unrelated window, sibling and root refuse.
2. Retain bounded actual origin query and each rejected predicate before input,
   and the post query before a failed postcondition. Keep the existing successful
   motion-query proof contract intact. Carry facts into pre-human diagnostic,
   including driver/backend producer boundary, without raw environment/secrets.
3. Cover exact target and certified descendant success, certified frame in/out
   of client bounds, unrelated in-bounds/root refusal before input, zero move,
   postcondition failure before click, and persisted actual failure facts.
   Verify real producer-to-workflow diagnostic composition rather than a made-up
   diagnostic dictionary alone. Preserve existing source pins and ownership gates.

No GTK placement changes without direct origin evidence; no GUI, IPC, service,
input, deployment, commit, trading, or unrelated source edits by implementer.

## Verification and completion

Run repository virtualenv pytest on native regression and input diagnostic files,
plus relevant direct synthetic calibration tests in test_session_native.py.
Run Ruff check/format for changed files and git diff --check.
Record exact commands, totals, failures, final diff and file hashes privately.
Sol independently reviews code and regressions read-only; fix findings then
repeat review as needed. Root reproduces focused checks and integrates only
reviewed bytes at a safe scan boundary. No live retry before accepted review.
The current live GUI owner continues assisted collection while work proceeds.

Success proves the bounded code contract and diagnostic evidence, not a successful
human calibration or autonomous collection. Live acceptance remains pending.
