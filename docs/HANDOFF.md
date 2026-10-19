# Forever Tradecraft handoff

Updated 2026-10-19 07:12 UTC. This is the active operational handoff. The exact
617-line handoff that preceded this consolidation is preserved in the
[pre-consolidation history](../.archive/executor-review/handoff-history-before-consolidation-20261019T0707Z.md).

## Objective

Build the launch-ready Crowley auction-house workflow for WoW Forever (build
70450). The [catalog](WATCHLIST.md) has 428 required
observations.
The scan must retain the cheapest 20 distinct unit-price levels, retain all ties
at each selected level, keep missing and unknown values explicit, and never mix
houses or item identities. A successful operator-assisted run must save,
upload, receive the exact server ACK, reopen the auction house, and verify the
reopened state before it is counted.

Disappearance is an uncalibrated activity proxy, not a confirmed sale. Later
work covers verified Forever recipe economics, profession/flipping/investment
strategies, and launch monitoring after the collection contract is qualified.

The remaining operational qualification is three autonomous 900-second
save/upload/ACK/reopen cycles after calibration. The current automation collects
observations; no buying, posting or cancelling is part of this task.

## Authority and live state

- Origin: https://github.com/kyle-deprow/forever_tradecraft . Routine fixes,
  installation, recovery, commits and pushes remain authorized; do not re-ask.
  The user revoked AGENTS.md rules.
- The sole GUI/game operator is Luna worker `luna_live_recovery`.
- The game character is Arthur, stationary at the Ironforge auction house.
- Root must not operate the GUI concurrently with Luna. This handoff does not
  claim human, autonomous, calibration, or native100 qualification.
- The service is NATIVE_CALIBRATION at generation 25 as of 07:13 UTC,
  native/input flags false, native operation running with no reported error. Do not restart it merely
  to inspect this handoff.
- Current work must preserve fresh evidence generations, exact commands, and
  the physical game-window boundaries. Do not infer a live result from a stale
  screenshot, a private fixture, or an external OCR crop.

## Latest accepted collection

Parent verification #85 completed the operator-assisted scan for UID
`beta-normal-alliance-1792393363-Arthur-6760`:

- 428 observations, 2,111 rows, 412 full and 16 bounded observations, all 428
  with reason `ok`;
- 478-second scan, 21.977232 seconds from finish to the server receipt;
- exact saved-variable/server digest agreement and an independently decoded
  loaded ACK with pending 0, followed by verified auction-house reopening,
  fresh ordinary boot, normal native phase, inactive fence, released button,
  and zero movement;
- the scan/reopen receipts are public in
  [scan verification](../.archive/executor-review/build-70450-eightyfifth-scan-parent-verification.json)
  and [auction-house reopen verification](../.archive/executor-review/build-70450-eightyfifth-ah-reopen-parent-verification.json).

#85 started exactly 900 seconds after #84 and is fully saved/ACKed/reopened.
Live recovery and control preflight both passed. Luna is now running native100
at generation 25, then public pause and fresh ordinary recovery. See
[live preflight evidence](../.archive/executor-review/native-live-preflight-r2-parent-verification.json). Root will not mutate the controller while
Luna owns that chain. The next normal scan due time is `1792394263` (07:17:43);
calibration may intentionally replace it. Do not interrupt an active scan.

The latest private backup is `beta-20261019T071147Z-11a0798b1d0b`, independently
validated after #85 ingestion, directory mode 0700. Manifest SHA256:
`db5c48d13f1d67ea6efe55af2577e311d7df0fcde7050d7661513325fbda7828`.
See [backup verification](../.archive/executor-review/market-backup-20261019T071147Z-parent-verification.json).
Next hourly backup: 08:12 UTC. Prior isolated restore drill passed; repeat only
if new evidence warrants it. Raw backup data stays private.

## Accepted installed release

The accepted release was promoted to main in commit `6874993`. The native seven
file set and addon 79 remain unchanged. The Rust-backed matcher and runtime are
installed; their public release record is
[native-helper-rust-final-release-parent-verification.json](../.archive/executor-review/native-helper-rust-final-release-parent-verification.json).
The installed artifact has SHA256
`75b18bd04cc3a9248f99ecdca3a1cdebe6e0d89c4d33eaebd600788177bcd80c`, CLI help
exited 0, and no service restart is required.

Current accepted source pins are:

- helper `tools/native_calibration_operator.py`:
  `1cbc51f825fe775847733801354d80ad250201ac0b9e8c5eeb4842980dfad211`;
- helper tests `tests/test_native_calibration_operator.py`:
  `56a5c50e6ebf071e7cb77defcf0ca28a6bcba01802386f192112ad5fa23d3314`;
- runtime `tools/template_matcher_runtime.py`:
  `edc5242e9eaf864e98b78b9904b28f8fac51927cc90a6001047a32ab8d36700d`;
- runtime tests `tests/test_template_matcher_runtime.py`:
  `302f74f2098dbd8a2eb6f1d3f417e8fd757b89bf66a6d854e921008661dbfa69`.

The helper executable body is AST-identical to the reviewed and tested
comment-only predecessor. The final helper run passed 84 tests with 5 warnings
in 348.83 seconds. Parent focused checks passed 4 tests in 0.92 seconds. The
public [OCR R2 verification](../.archive/executor-review/native-chat-ocr-r2-final-parent-verification.json)
binds the installed helper/test pins, the retained-frame production proof,
and the qualification boundary. Sol and actual Opus both returned READY.

## Chat OCR contract and proof

The fixed OCR contract is measured for the 1920x1080 client with the sticky
`Say:` header. The body begins near x=45, the right border is near x=440, and
the body ROI `(40, 7, 400, 13)` is relative to the production chat crop
`(30, 938, 460, 37)`, not the full screenshot. The top rule
at y=7 is retained deliberately; glyph rows 20 and 21 are cut by the measured
box. The cursor probe is 11/13 against the tallest glyph/rule and erases at
12 or greater.

The production path is original full frame -> `X11Screen.chat_crop` ->
`_capture(crop=True)` -> the actual OCR and normalization -> `_chat`. It does
not use an externally converted crop, fuzzy replacement, an OCR character
whitelist, or a per-command fallback. The command allowlist remains fixed. Closed chat must normalize to empty. A nonempty
closed chat is refused before input. Open typed chat must equal the exact
expected command body.

All eight retained full-frame command cases passed through that production path:
`/crowley agent defer`, `release`, `recover`, `hold`, `measure`, `resume`,
`finalize`, and `/reload`. Each also passed the closed-empty and nonempty-closed
refusal guards. The private suite receipt and raw images remain private; the
public report above records the original-frame hashes and qualification limits.
A different channel label, client scale, border, cursor, or chat geometry
requires fresh measurement and qualification before using this contract.

## Runtime and native assumptions

The Rust matcher is a bounded release dependency used by the accepted runtime;
there is no runtime build, shell fallback, Python matching fallback, or
unreviewed artifact substitution. Runtime, binary, and source provenance remain
part of the receipt. The canonical installed artifact and source pins must be
verified before any future replacement.

The native control path requires the actual WoW Frames and the accepted
ownership/fence/recovery protocol. It verifies current identity and state,
requires empty chat before opening, and requires exact command text before
submission. A native movement result is not a live
readiness result: the preflight, `INPUT_CALIBRATION`, native100, pause, and
ordinary recovery gates below remain separate.

Binary chatEdit cannot replace this entire visual contract: release happens
with the Agent surface absent; measure/resume run while publication is held;
recover may start in restore_only without a surface. Do not repeat an all-chat
telemetry substitution without changing and qualifying that lifecycle.

The fixed OCR geometry is a sticky measured assumption, not a general chat
reader. Preserve the current body-only crop and threshold/scale preprocessing;
if the client layout changes, stop and remeasure from retained full frames.
Never replace an exact command guard with fuzzy text or a guessed interior box.

## Canonical entrypoints

Use `/home/dev/repos/pegasus/.venv/bin/python` and
`/home/dev/.local/bin/crowley-session`, config `~/.config/crowley/session.toml`.
Helper: `/home/dev/repos/pegasus/tools/native_calibration_operator.py`.
Templates: `~/.local/state/crowley/executor-evidence/native-live-controls-20261019/templates.json`.
Matcher artifact root: `~/.cache/crowley/template-matcher/v1`.
Helper CLI takes `--generation CURRENT --config CONFIG --templates TEMPLATES
--matcher-artifact-root ROOT {recover,control-preflight,measure-deferred}`.
Use actual returned generations; never guess or replay an old transition.

## Next live gates

Run these gates in order, preserving the fresh generation and the exact command
history in each receipt:

1. Luna has completed #85 save/upload/ACK/reopen; parent independently verified
   the original payload, DB, exact ACK, ordinary state and released controls.
2. If a checkpoint exists, recover it first. A failed checkpoint recovery blocks
   the next calibration attempt until a fresh recovery attempt completes.
3. Run native control preflight, resume, and the measured native100 operation.
   Verify `INPUT_CALIBRATION`, native true, operation complete, finalization,
   the expected fences, and the resulting receipt before release.
4. Issue the public pause gate, then run fresh helper recovery and ordinary
   restore. Verify PAUSED/native true/input false, checkpoint cleared, and no
   stale operation or input action.
5. After native recovery succeeds, coordinate user availability. Resume into
   INPUT_CALIBRATION, then start public input-calibrate with its fresh generation.
   Wait for kind=input/state=running/readiness.ready=true and the visible owned
   GTK prompt. The human gate is in that separate GTK window, not WoW: real
   pointer motion, ordinary key press/release and button press/release. The first
   event intentionally pauses and increments generation; do not resume early.
   Wait approximately 120.5 seconds for operation complete, native/input both true
   and the evidence fingerprint. Never synthesize this gate.
6. Resume and reconcile the resulting state, then run three autonomous
   900-second full save/upload/ACK/reopen cycles. Record each generation,
   receipt, server ACK, and reopen decode independently.
7. Do not claim launch qualification until every gate and all three autonomous
   cycles have passed with retained evidence.

## Evidence and preservation

Use the public reports in `.archive/executor-review/` as the source of prior
release, source, review, and verification pins. Relevant records include:

- [paused installation verification](../.archive/executor-review/native-paused-install-parent-verification.json);
- [Rust/helper release verification](../.archive/executor-review/native-helper-rust-final-release-parent-verification.json);
- [OCR R2 production verification](../.archive/executor-review/native-chat-ocr-r2-final-parent-verification.json);
- [#85 scan verification](../.archive/executor-review/build-70450-eightyfifth-scan-parent-verification.json);
- [#85 reopen verification](../.archive/executor-review/build-70450-eightyfifth-ah-reopen-parent-verification.json);
- [latest backup verification](../.archive/executor-review/market-backup-20261019T071147Z-parent-verification.json).

Private raw frames, receipts, process logs, command histories, and backup
contents stay under their existing private evidence directories and must not be
copied into Git. Keep private logs mode 0600 and private backup directories mode
0700. Retain the exact pre/post source pins, command lines, import origins,
process results, and artifact digests for every new qualification run.

The archived pre-consolidation handoff preserves superseded chronology and
failed attempts. It is historical evidence, not a list of pending gates. When
new evidence supersedes a fact here, update this active handoff and add or link
the public verification record rather than restoring contradictory history.

Root owns Git; workers must respect their assigned source and desktop scopes.
Do not reset, stash, revert others, or use `git add .`; many untracked files are
private. All future live claims
must identify the owning operator, fresh generation, exact command sequence,
retained evidence, and whether the result is assisted or autonomous.
