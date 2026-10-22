# Owned GTK input target placement

Input80 proved the next boundary: origin (1809,43), certified owned hit XID,
but measured GTK client [1440,71,480,240]. The pointer is above the client.
No human readiness occurred. Previous certified-ancestry repair remains valid.

## Implementation order and scope

Use existing isolated worktree input-pointer-origin-20261022. Own only
`src/crowley/session/calibration.py`, `tests/test_session_native_regressions.py`,
and `tests/test_session_input_diagnostics.py`. Preserve prior reviewed changes.
Driver changes require concrete justification to root before extending scope.

1. Choose one deterministic owned GTK test surface that contains the current
   pointer in its actual client area (prefer undecorated/fullscreen). Resolve
   mapped/WM-settled actual geometry through existing certificate lifecycle,
   before measuring keyboard or dispatching pointer input. Preserve target
   process/start/WM ancestry, exact tickets, focus/Guardian, source attribution,
   all pre-input bounds and nonzero-motion checks, private entry and prompt.
2. Do not move/warp the pointer into a proof, widen bounds into decorations,
   accept arbitrary window ancestry, ask for early human input, or add alternate
   guessed placement paths. A refused/ignored surface setup must fail before
   probe input and preserve concrete evidence; cleanup must reap owned target.
3. Exercise real constructor/verification lifecycle for the observed top-edge
   origin, settled surface success, ignored/late setup refusal before probe,
   and owned cleanup. Include actual producer bounds admission where possible;
   script-string assertions alone do not prove this behavior.

## Verification and review

Use root repository virtualenv with worktree PYTHONPATH. Run affected target
startup/certificate regressions, all input diagnostic tests, and existing eight
producer bounds/ancestry regressions. Run Ruff check/format and git diff --check.
Only broaden tests if new concerns justify it. Freeze after all formatting and
publish exact hashes/results/limitations in a new private placement manifest.
Sol reviews the incremental placement diff against the prior accepted origin
patch, including lifecycle/order/failure cleanup and executable GTK assumptions.
Root independently verifies focused checks and promotes only accepted bytes.

No implementer GUI, host input, daemon IPC, restart, deployment, or git mutation.
The current GUI owner holds at PAUSED after terminal80 failure with AHclosed/
noactive and preserves immutable diagnostic. Root coordinates deployment/retry
only after review; resume assisted collection if user leaves or repair is delayed.
Human success and autonomous cycle qualification remain separate live acceptance.
