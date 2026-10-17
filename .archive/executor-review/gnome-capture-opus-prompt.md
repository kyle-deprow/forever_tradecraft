State your exact model ID first. This round requires Claude Opus; do not use a
fallback. You are a read-only reviewer in /home/dev/repos/pegasus. The user revoked
AGENTS.md. Do not edit files, commit/reset/stash, execute tests, use GUI/input,
change services or configuration, or make external requests.

Review the completed scoped GNOME screenshot repair against
.archive/PLAN-gnome-capture-completion.md and actual diagnosis
.archive/executor-review/native-capture-concurrency-diagnosis-r1.json.
Production X11Backend.capture previously assumed exit0 meant a completed PNG.
The actual GNOME single-instance D-Bus service can return before creation or PNG
completion under overlapping capture requests. Intent: serialize Crowley requests
and accept only a new complete image within the existing deadline, preserving
identity, freshness, input authority and all native/resource bounds.

Scope: src/crowley/session/driver.py, tests/test_session_capture.py and optional
test fixture edits in tests/test_session_driver_actions.py. Use the worker's
gnome-capture baseline/diff/freeze artifacts, rather than attributing the entire
large existing working-tree diff to this task. All other source is out of scope.
Read the scoped implementation and its callers, deadline/argv checks and tests
as needed. Earlier executor, native schema3, build70450, model and private-helper
reviews are closed; reopen only a concrete newly introduced regression.

Assess correctness, cross-process lock lifetime/ownership, pending asynchronous
writers, stale/partial/missing outputs, deadline propagation including contention
and decoding, failures/cleanup, exact image and identity acceptance, preservation
of original timestamps, and meaningful tests at actual production boundaries.
Do not manufacture marginal findings. Group concrete findings as Must-Fix,
Should-Fix, Nits with file:line, reachable problem and correct outcome. A zero
exit without the verdict is incomplete. End with exactly one verdict line:
STATUS: READY | NEEDS WORK | MAJOR ISSUES
