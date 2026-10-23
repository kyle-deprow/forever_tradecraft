# Actual native hover motion correlation

Base: 0b1fd2b. Luna implements in the isolated takeover-motion-correlation-20261023
worktree; Sol reviews frozen bytes read-only. Main and live game remain untouched
until parent checks and a fully saved/uploaded/loaded-ACK scan boundary.

## Objective and order

1. Replay the exact retained native trace and original action context through the
   production parser and Guardian. Preserve the complete rejected partial tail.
   Establish which assertion fails; distinguish hierarchy capability from events
   actually delivered. Do not infer that absent early echoes never occur later.
2. Implement the smallest supported motion correlation correction. Preserve exact
   raw/primary timestamp and endpoint pairing, origin continuity, planned order,
   source/master/target identity, modifiers, bounded correlation and immediate
   physical/UNKNOWN takeover. No filters, blanket source allowance, fabricated
   events, relaxed profile proofs, extra calibration framework or fallback path.
3. Cover the observed trace, actual completion and adversarial unsolicited,
   duplicate, reordered, wrong-source/target/endpoint/modifier and late events;
   retain existing native/human/drill/cleanup behavior. If the trace cannot justify
   a safe completed-action contract, report the specific extra observation needed
   rather than inventing it. Keep assisted scans running independently.
4. Freeze source hashes, complete patch, exact commands/results and remaining
   acceptance limits for independent Sol review. Parent reproduces verification.

Evidence: /home/dev/.local/state/crowley/executor-evidence/assisted-collection-luna-20261021/scan291-takeover-drill-failure-20261023T0109Z/latest-hover-failure.json
SHA256: d383992b7855feb2f868bd2390e3730b133c43b7733d0e6597204e4ef932d322

## Exact ownership

Allowed source: src/crowley/session/guardian.py, driver.py, startup.py (under the
same session directory). Allowed tests: tests/test_session_startup.py,
tests/test_session_dispatch.py, tests/test_session_native_regressions.py,
tests/test_session_native.py. Add one focused test file
tests/test_session_motion_correlation.py if needed. Ask before expanding scope.
No daemon/protocol/addon/config/dependency/docs/skills changes. No main edits,
host GUI/capture/input, live services, git commit/push or data changes.

## Verification and completion

Run uv run pytest over every changed test module and the existing startup,
dispatch and native regression modules. Use authentic private pinned CLI via the
existing fixture adapter if required; no version fabrication or pin relaxation.
Run uv run ruff check and uv run ruff format --check on changed Python paths;
git diff --check. Relevant native coverage cannot be skipped without stating why.
Freeze manifest/report/patch in a new private executor-evidence directory. DONE
only for a complete bounded implementation, not a live autonomy claim. Human
drill, real native hover and full autonomous cadence remain separate acceptance.

Verification correction: the first broad run passed321/failed1 because the
existing reload-stream fixture still drops the required native keymap and
expects obsolete named-key emissions. Within its already-owned native regression
test, forward the actual keymap and record/assert current numeric keydown/up
emissions while preserving per-character native correlation and partial-tail
coverage. Keep the original failure log. Rerun that node, its full module and
the focused correlation suite; no production typing changes or assertion bypass.
The user has ended beta collection; all further verification is offline and
live eventual-echo/hover/drill acceptance remains explicitly unqualified.

## Exact fixture correction R2

Keep the final R1 bundle immutable (patch807e19b0...). Sol found the complete
raw blocks match but partial-tail fixture omits the receipt's last newline:
363versus364bytes. R2 in the sibling takeover-motion-correlation-20261023-r2
worktree owns only tests/test_session_motion_correlation.py for this correction.
Preserve exact receipt bytes and assert their pinned SHA/length in the test,
without adding private filesystem dependencies. Do not edit production or other
tests. Run the full focused module plus existing four Guardian cases, Ruff/format
and diff checks, freeze cumulative patch/hash manifest/report in new R2 directory.
Sol verifies final bytes; parent reproduces focused checks. Existing broad run
on identical production bytes remains applicable, with honest fixture provenance.
