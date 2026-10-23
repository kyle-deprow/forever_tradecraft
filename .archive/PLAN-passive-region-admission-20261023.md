# Passive startup with the configured region producer

Base b769d576cc21ad00b888148373be76f6e6128ee2, installed R2.
Live public repeat start from PAUSED94 refused before input with:
`PAUSED native region capture requires a live recovery capability`.
The deployed profile enables the region producer. Existing R2 tests replaced
capture_status, so they missed its actual state/admission boundary.

## Outcome and ownership

Use the configured producer for read-only passive startup from the supported
STOPPED/PAUSED/BLOCKED entry states. Preserve normal state restrictions for generic
capture and native construction/recovery. Startup must not require an input lease,
legacy native/GTK proof, or a matching human record merely to read three frames.
Do not disable the configured producer or add a fallback capture backend.

Luna owns only src/crowley/session/daemon.py, tests/test_session_startup.py,
tests/test_session_native.py, tests/test_session_capture.py and, if necessary,
tests/test_session_runtime.py in the isolated passive-region-admission worktree.
Keep the correction small. Preserve identity/focus, controller generation/state,
stop/cancel, original absolute deadlines, registered Guardian observer ownership,
producer sealing and cleanup. Any private read-only admission scope must be
operation-bound and revoked when passive startup exits; it cannot admit input or
subsequent generic captures. No main edits, config/service/GUI, commits or pushes.
Read repository rules and local-game-control skill for producer/owner boundaries.

## Verification and review

Exercise the actual passive_startup -> capture_status -> configured native region
admission -> Guardian/producer route rather than replacing those methods. Cover
all supported entry states; advancing frames and NO_CHANGE; observer loss;
identity drift; generation/state/pause/stop races before producer admission; bounded
failure and process cleanup; and unchanged refusal of generic PAUSED/STOPPED capture.
Use existing private native producer fixtures where useful; report missing retained
artifact requirements honestly, do not fabricate native proof or start host GUI.

Run PYTHONPATH=src /home/dev/repos/pegasus/.venv/bin/python -m pytest -q
on changed test modules, or exact scoped native nodes plus full startup/runtime
as appropriate. Run Ruff check/format and git diff --check on changed files.
Preserve complete logs/exit files, frozen complete diff and SHA manifest under
private executor-evidence/passive-region-admission-20261023. Independent Sol review
and parent checks must pass before promotion, owner restart and Luna live retest.
Report DONE only when source, tests and immutable artifacts are complete.
