# Unblock the real input-calibration synthetic phase

The user is away and requests working calibration on return while collection
continues. Sole GUI owner remains Luna scanner. Input92 reached a correctly
certified GTK root child with valid pointer origin/post predicates but timed out
before human readiness. No further live attempt before reviewed repair.

## Observed evidence

Immutable private bundle:
`~/.local/state/crowley/executor-evidence/assisted-collection-luna-20261021/input-calibration-failure-92-20261022T201139Z/failure-index.json`.
Diagnostic SHA256 `3e3cad097d297bbb86afcbb04f0f2916c2107a7b4e3b38a8c734eb9358ef903e`.
Retained native stream has289 complete blocks and a partial final delivered key
release. It is not a complete replayable calibration proof. First divergence is
in calibration-only select_chat_all: pinned xdotool releases Control before a and
emits a duplicate raw Control release. The runtime action vocabulary explicitly
excludes select_chat_all; actual command typing uses allowlisted per-character
keys. Do not discard/reorder events to make the old proof pass.

## Scope and order

Worktree `/home/dev/.cache/crowley/worktrees/input92-keyboard-rehearsal-20261022`,
base1130c81. Read CLAUDE, HANDOFF, local-game-control and client-contracts skills.
Luna owns only:

- src/crowley/session/driver.py
- tests/test_session_dispatch.py
- tests/test_session_input_tool.py (adapt existing physical-hold fixture, retain security refusals)
- tests/test_session_keyboard_rehearsal.py (new focused module if needed)
- tests/test_session_native_regressions.py (only relevant synthetic/reader regressions)

Plan is read-only. No other source, parser, validator, protocol, Guardian, addon,
configuration, evidence-seal, timeout/threshold or source-pin changes. If a proven
producer fix requires another file, report the exact reason before editing it.
No host GUI/input/capture, live daemon IPC/restart, deployment, commit, reset or
changes to other agents' files. Private Xvfb and explicitly private session bus,
authority, leases and capture locks only; never global uinput or host activation.

1. Finish actual parser/validator and pinned native producer diagnosis. Distinguish
   the observed chord mismatch from the incomplete tail and any stdout buffering
   hypothesis. Preserve actual raw bytes; do not synthesize missing native fields.
2. Remove unused select_chat_all from calibration's required runtime vocabulary.
   Keep the actual runtime actions/commands fully covered and preserve exact raw/
   delivered sequence, identity, target, held-state and modifier validation. Do
   not add the unsupported chord as a public action or weaken its admission. Assert
   exact vocabulary equality: open_chat, submit_command, escape_command_buffer and
   each DesktopDriver.COMMANDS payload, plus sealed _expected_key_operation coverage
   for every runtime operation. Preserve generic left/right modifier-hold admission
   and revoked-ticket refusal tests using explicit test-only chord fixtures; do not
   mistake those recorder fixtures for required production calibration vocabulary.
3. Prove actual native event delivery through the synthetic phase on an owned
   private X11 target. Use the real pinned XTEST emitter, production observer,
   parser, keyboard-operation enumeration and strict synthetic validator/workflow.
   Keep the observer pipe open and idle after the final release: completion must
   not depend on a later event or EOF. Fix producer flushing only if established
   necessary; do not merely wait longer. Every external executable/launch change
   must preserve ownership, readiness, registration, termination and reaping.
   Current audit finds no producer/parser fix justified: actual raw+partial feeds
   289 events including final KeyRelease40, and pinned xinput uses line buffering.
   Limit driver edits to _calibration_keyboard_operations; report a newly proven
   defect before expanding that scope. Record observer process/reader alive at
   completion, with no subsequent event or EOF.
4. Exercise real workflow readiness without human input, then cleanup. An owned
   cancellation at the readiness callback may stop a private rehearsal; it is not
   human-input acceptance or live game qualification. Test no extra/missing key
   record acceptance and the actual dispatch path, not a fabricated passing list.
5. Freeze formatted source/test hashes and private evidence/report. Sol reviews
   independently; root reproduces focused checks and promotes at a completed
   scan/save/upload/exact-ACK boundary. Runtime driver changes require reviewed
   restart/source rebinding and fresh native proof; don't preserve stale proof.

## Verification and completion

Use root venv and worktree PYTHONPATH:

- `.venv/bin/python -m pytest -q tests/test_session_dispatch.py tests/test_session_input_tool.py tests/test_session_keyboard_rehearsal.py`
  (omit new filename only if not created; document equivalent actual native proof).
- `.venv/bin/python -m pytest -q tests/test_session_native_regressions.py -k 'synthetic_calibration or xi2_reader'`
- Ruff check/format for changed Python files; `git diff --check`.

Use `/home/dev/repos/pegasus/.venv/bin/python` and Ruff absolute paths in worktree.
Retain terminal results and private native proof with exact invocations/source
pins. No broad multi-minute operator suite unless a new unresolved concern needs
it. No host desktop interaction for a fixture. Report actual passed/failed counts,
real native-vs-modeled coverage, cleanup/process registries, remaining limits,
final diff/file hashes and exact files. DONE only when implementation and required
checks are complete; root owns commits/push. No claim of human readiness until
actual reviewed live attempt reaches it, and no human qualification while AWAY.
