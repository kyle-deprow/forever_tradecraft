# Process matching cost Sol R1 source review

Review scope: frozen candidate
`/home/dev/.cache/crowley/worktrees/process-matching-cost-20261018` at base
`fe439243afdb7e2fd0ba8244819eac2fa9086761`, reviewed against
`.archive/PLAN-process-matching-cost-implementation.md`,
`.archive/PLAN-process-matching-cost.md`, the R1 freeze/closure records, and the
three-single diagnostic summary. This was a read-only source review. I did not
run tests, builds, live GUI operations, captures, restarts, or git mutations.

## Findings

Must: none.

Should: none.

Nits: none.

## Freeze and fence

The candidate HEAD is the declared base. Its only changed paths are
`src/crowley/session/driver.py` and `tests/test_session_driver_actions.py`.
The current hashes are respectively
`965c4b3f20842f3e065469077358b6886d8260d24aab5fe7ed3933beca0d13f6`
and `7bf8538bdb804cd4e5d275d7c311b86171ce7ec9f650999371c6169abca956a6`;
the base blobs hash to the recorded
`ca0ca123d0fa09d8361c8632d9cc1c2c501d87adf99cb3cc268688dd4291a166`
and `6d5b21dd11a3af45d20f494ce7950ea18f676e40f47c5d01aae8a30e655f2413`.
The two plan hashes and diagnostic-summary hash also match the freeze record.

## Source acceptance

At `src/crowley/session/driver.py:2198-2234`, the production delta only splits
the former inspection `try` around the existing exact cmdline basename and
cardinality check. A zero-match or duplicate-match process now receives the
accepted configured-executable refusal after `cmdline` and before `stat`,
`status`, `exe`, or `environ`. An exact candidate retains the prior sequence and
behavior: `stat` start field, `status`/`Name`, resolved `exe` basename
`wine-preloader`, configured real `WINEPREFIX`, then the same `(matches[0],
start)` result. Candidate exception classes and error text are unchanged.

At `src/crowley/session/driver.py:2236-2248`, numeric `/proc` enumeration,
per-call set construction, caught error classes, and PID-set semantics are
unchanged. At `src/crowley/session/driver.py:2310-2344`, each resolver call still
builds a fresh matching set and re-runs `_process_executable` for the selected
window PID. The diagnostic path still makes independent `daemon_pre`,
`backend_pre`, `backend_post`, and `daemon_post` resolver calls at
`src/crowley/session/daemon.py:4234-4238`,
`src/crowley/session/driver.py:2864-2868`,
`src/crowley/session/driver.py:3167-3168`, and
`src/crowley/session/daemon.py:4331-4335`. No result is cached across those
barriers. The two-file fence leaves profiler schema, IPC/public evidence,
cancellation, deadlines, and producer/config behavior unchanged.

The transition expectations match the implementation plan's clarified baseline
semantics. A cmdline noncandidate remains rejected for that invocation even if
it execs immediately afterward. A candidate that exits or changes after the
cmdline read proceeds through the existing later reads and fails closed on the
first inconsistent or unavailable predicate. The following call scans the PID
fresh. This preserves the baseline's non-atomic `/proc` snapshots without
claiming stronger PID/exec atomicity.

## Test review

`tests/test_session_driver_actions.py:203-314` creates owned, non-GUI processes
with the unique configured name `CrowleyTest.exe`, a temporary copied interpreter
named `wine-preloader`, and temporary Wine prefixes; its `finally` path
terminates/kills and waits for every child. The matcher and resolver remain the
production methods. Read hooks at lines 317-342 record actual `/proc` operations
rather than supplying identity values.

The tests cover cmdline-only zero/duplicate rejection and matched-set omission
(lines 345-378); exact candidate read order plus `Name`, loader, prefix, and
malformed-stat refusals (381-452); exit after cmdline (455-501); both synchronized
exec directions with a fresh follow-up call (504-583); duplicate valid PID-set
cardinality refusal (586-609); and production resolver/window-PID binding against
a real matching process (612-675). These checks exercise the specified behavior
without identifying a fixture as `WowB.exe` or touching the live game.

The recorded worker and parent checks support source acceptance, but this review
makes no live performance, native qualification, or Rust-gate claim. The planned
three-single diagnostic comparison remains separate and requires its own
authorization and evidence.

STATUS: READY
