# Forever Tradecraft handoff

Updated 2026-10-19 16:46 UTC. This is the active handoff. The exact preceding640-line
handoff is preserved in [review-closure history](../.archive/executor-review/handoff-history-before-ack-review-closure-20261019T1439Z.md).
Earlier chronology is linked there. Historical pending statements are superseded
by the current state below.

## Objective and completion criteria

Build the launch-ready Crowley auction-house workflow for WoW Forever build70450.
The [watchlist](WATCHLIST.md) requires428 observations. Retain the cheapest20
**distinct unit-price levels**, all ties at each selected level, and explicit
missing/unknown values. Exactly20 levels without a higher witness is full;
never mix houses or item identities. Disappearance remains an uncalibrated
activity proxy, not confirmed sales. Buying, posting and cancelling are outside
this task. Recipe economics and trading/investment strategies follow collection.

A full cycle saves the original game payload, uploads it, receives the exact
server ACK, reloads it and verifies the reopened AH. Operational qualification
requires native calibration/recovery, genuine human input calibration and three
**autonomous900-second** full cycles. Current cycles are operator-assisted;
**zero autonomous qualification cycles are counted**.

## Authority and ownership

- Origin: https://github.com/kyle-deprow/forever_tradecraft . Routine recovery,
  installation, fixes, commits and pushes remain authorized. The user revoked
  AGENTS.md rules. Keep progressing until requirements are met.
- User prefers Luna implementation/game control, Sol review and actual CLI
  Opus review. Do not substitute another model or claim a review not performed.
- Sole live GUI owner: `/root/luna_live_recovery`. Root may inspect retained
  artifacts but must not operate/capture/input the GUI concurrently.
- Arthur remains stationary at Ironforge AH. No navigation/trading. Standard
  Wine desktop; Sunshine disabled. Character revival/login already completed.
- Implementation owner: `/root/luna_rust_matcher` in the isolated worktree below.
  Root owns docs, skills, final verification, installation and Git. Review worker:
  `/root/sol_final_composition_plan`.
- Never reset/stash/revert others or use `git add .`. Many untracked files are
  private. Stage only explicit reviewed files. No messages to outside parties.

## Live state and collection

Stable game identity: PID644491/start15495385, xid0x02e00001,
child0x2000011, fingerprint
`e84a459bda54c891092f049af9c523eb171588ce566a44123723d733baf6918a`.
1920x1080 client, telemetry crop80,48,256,256. DISPLAY:0; obtain fresh authority
and controller generation before mutation. Last native recovery was PAUSED38,
nativefalse/inputfalse; do not treat this historical generation as fresh.

Daemon service `crowley-session` is active, PID3891378 since10:08:17UTC.
No identity-budget/ACK-alignment candidate is installed. Assisted operation
continues while offline correctness/performance work proceeds.

Latest fully parent-verified cycle **#121**:

- UID `beta-normal-alliance-1792427811-Arthur-6177`;
- start1792427811, finish1792428287:476s;428 observations/1,999 rows;
- 412 full/16 bounded, all428 `ok`, zero query failures;
- exactly900s after120;34.339005s finish-to-server receipt;
- original saved/server digest agreement, exact loaded ACK, pending0, reopened
  AH, normal0/inactive fence, zero speed and released controls;
- [scan proof](../.archive/executor-review/build-70450-onehundredtwentyfirst-scan-parent-verification.json)
  and [reopen proof](../.archive/executor-review/build-70450-onehundredtwentyfirst-ah-reopen-parent-verification.json).

Next ordinary deadline1792428711 (16:51:51UTC). Sole operator continues full
assisted900s chains until root has a concrete reviewed release ready. No native
or physical-input retry yet. Scans108..121 all have verified exact900s starts.
After106 a real WOW51900319 disconnect caused107 to start350s late; normal
reconnect succeeded without credentials. The old memory notification said8hours
ago; no new OOM cause is established. See archived links for exact proofs.

Scans115 and118 reopening required separate fresh Auctioneer targets after
stale positions hovered another player. Parent combined the two retained receipts
with their original hashes, decoded both ACK/reopen pixels, and preserved the
failed stale-target attempt unchanged. This remains assisted evidence.

Generic parent verifier, only after the complete retained flow receipt exists:

```text
uv run python /home/dev/.local/state/crowley/executor-evidence/verify-assisted-cycle.py ORDINAL WORD_ORDINAL PRIOR_START RELATIVE_FLOW_RECEIPT
```

It verifies original saved bytes against the server and independently decodes
ACK/reopen pixels. Use a fresh ordinal; its public outputs are exclusive-create.
Private runtime flow receipts live under
`~/.local/state/crowley/executor-evidence/runtime-relink/`.

## Installed release and fixed assumptions

Accepted diagnostic release:
[verification](../.archive/executor-review/native-observation-diagnostics-release-parent-verification.json).
Current MAIN source SHA256:

- daemon: `4259e4de58b3b3d79f2fc595978907090a7f74666656a4af0c311a33602b0dad`;
- calibration: `3a91f4fe690cd820329fe2536fc03e5c7de24e4c20649efdf1a705b8c147c8fc`;
- driver: `ca0ca123d0fa09d8361c8632d9cc1c2c501d87adf99cb3cc268688dd4291a166`;
- helper: `63fd2b97e84f77b11f12f120dc0300e822611dcedce19213f5b949b40e657462`.

Helper editor-state/contrast correction is installed, reviewed Sol R2 and actual
Opus5.5 R2 READY, with parent reproduction. [Contrast release](../.archive/executor-review/native-chat-contrast-release-parent-verification.json).
Its full96-test result used an earlier test pin; the final test pin adds one
regression with18 focused passes. Do not claim a full97-test run.
The failed gen33 original fullframe was never retained; only its crop exists.

Chat contract remains exact sticky Say/1920x1080 geometry: chat crop30,938,460,37,
body ROI40,7,400,13 within it. Preserve the measured chrome/editor-state guard,
body-only preprocessing, cursor removal and exact typed-command equality.
Unknown/active-empty/inactive nonempty states refuse as specified; no fuzzy
OCR fallback or blanket telemetry replacement. Native bootstrap lacks a surface,
and held publication cannot provide all measure/resume chat checks.

The accepted Rust matcher/runtime and addon79 remain installed. No runtime
build, shell/Python matcher fallback or artifact substitution. Provenance and
release pins remain in the [Rust/helper verification](../.archive/executor-review/native-helper-rust-final-release-parent-verification.json).

## Frozen correction and release status

Livegen37 requested update2 but captured3. Parent decoded the rejected image:
screenshot starts1384.571ms apart, screenshot28.957ms, identity work926.812ms
plus142.073ms deferred-owner validation. This did not establish a Rust compute
bottleneck. [Live timing proof](../.archive/executor-review/native-live-budget-failure-gen37-parent-verification.json).

Approved scope: [identity budget](../.archive/PLAN-native-identity-budget.md),
[pre-ACK alignment](../.archive/PLAN-native-capture-ack-alignment.md), and
[parent closure checklist](../.archive/PLAN-native-ack-review-closure.md).
Only six source/test files. Preserve three fresh backend-pre/backend-post/
runner-post resolves and all identity/owner/lease/Guardian/generation/run/epoch/
B0/CRC/ordinal/cadence/deadline/cleanup guards. Only the three approved duplicate
identity resolves are removed on exact eligible deferred updates. No Guardian,
producer, addon, Rust, helper, service, configuration or public schema changes.

FINAL frozen worktree: `/home/dev/.cache/crowley/worktrees/native-ack-source-r2-20261019`,
base1cbaadf. Private manifest `native-ack-source-r2-20261019/final-freeze-r2.json`
uses key `files`. Original R7 worktree `native-identity-budget-20261019` is frozen
for comparison, not the candidate to install. Final SHA256:

- `src/crowley/session/calibration.py`: `d342224339777e103b47aad008608f56f396711e5aff3999367286319990d26b`;
- `src/crowley/session/daemon.py`: `946e02bd467cecb7d720181e032bb54c2fc280076c884e406f680b51ab085d50`;
- `src/crowley/session/driver.py`: `05e5ed98d0b94019aa29eb0f4bd6ac3174cf45dca93deb9059425eeb815738cc`;
- `tests/test_native_calibration_operator.py`: `275854aca13bd70aff559e10268ed83624046f678a548bd1790de8b9eab0ee62`;
- `tests/test_session_native.py`: `9f0c99e21ade83aba9f74b8f245d2780f7d7a17a5b0d1c1e3e59bd7c74d24d8c`;
- `tests/test_session_runtime.py`: `a6eacc9c699757f0e0870937eec2ae2a320c2ecbd966ee2757003c0395097456`;

The receipt remains local through backend cleanup and is handed to eligible
provider calls once, finalized; generic backend keywords stay unchanged.
Held100 is reported retained only after both callback checks and successful
resume-required publication. Publisher alignment uses immutable first receipt
S1/U1 and prior decoded uptime, constant50ms guard, pre-ACK wait outside locks,
then synchronized controller/construction/Guardian/backend admission. Original
per-attempt/frame/operation/reservation deadlines never extend.

All independent parent offline gates PASSED on unchanged final six hashes:

- receipt/diagnostic/witness9 in1.90s; callback order and real-runner cleanup2
  in13.47s; actual compiled boundary matrix22 in57.33s;
- all seven actual-runner modeled scenarios in130.66s; positive active maxima
  882.576/888.576/889.076/882.576ms, phase951 naturally protocol-refuses;
  negative budgets961.576/1437.161ms; exact positive charge counts
  capability1085, target98, ACK98, glue99;
- genuine baseline56.30s: old refuses update4(received5), accepted3, max
  1384.569ms/glue4; reduced accepts99, max1435.161ms/glue119;
- exact compiled100 in136.20s, real observer103 accepted attempts including
  retained held100 and sealed path/hash; scoped Ruff/format/diff checks passed.

[Final parent proof](../.archive/executor-review/native-ack-final-r2-parent-verification.json).
Private independent source/logs/timelines: `native-ack-parent-r2-final-20261019/`;
verification WT `native-ack-parent-verify-20261019`. Worker exact gate136.22s,
focused runtime21/native23 and actual callback rejection130.80s also passed.
Exact long node (short compositor tests do not substitute):

```text
tests/test_native_calibration_operator.py::test_actual_operator_measure_composes_x11_screen_daemon_and_agent[success]
```

[Sol R3 READY](../.archive/executor-review/native-capture-ack-sol-source-r3-review.json),
all six pins checked before/after; no new Must/Should/Nits. Actual Opus R2
completed exit0 as `claude-opus-5-5`, six pins unchanged. It found production
correct, but returned NEEDS WORK for a test fixture publishing fake PGID999999
to a real watchdog kill list. [Full review](../.archive/executor-review/native-capture-ack-opus-source-r2-review.md).

The [final test safety correction](../.archive/PLAN-native-ack-watchdog-fixture-closure.md)
is frozen. Native test final SHA `dd50b41bad852eeabc01245ca356c153a0b48a51b739b98c73c21e06b5f22ad6`;
runtime test final SHA `d7da65ad2f1704357ef94e15c2acffb93dfdc5481df494fee5a403801723c96e`.
The other four R2 files above remain exact. An owned live group replaces the
fake PGID; finally restores/republishes all three injected fault states before
holder termination/reap, even after failure. Baseline outcomes and comment fixed.
Parent reproduced affected3 in8.69s, baseline in46.10s and scoped static checks.
Production/operator bytes and runtime AST outside baseline are unchanged:
[test-delta proof](../.archive/executor-review/native-ack-test-safety-parent-verification.json).
Earlier full100/seven-model evidence remains bound to original R2 test hashes.
[Sol R4 READY](../.archive/executor-review/native-capture-ack-sol-test-safety-r4-review.json); actual Opus R3 bounded test-delta review is running. No installation yet.
Private final freeze: `native-ack-source-r2-test-safety-r3-20261019/final-test-safety-r3.json`;
parent logs: `native-ack-test-safety-parent-20261019/`;
actual reviews: `native-ack-source-opus-r2-20261019/` and
`native-ack-test-safety-opus-r3-20261019/`.

Earlier partial/rejected candidates remain historical evidence:
[Sol R1](../.archive/executor-review/native-capture-ack-sol-source-r1-review.json),
[Sol R2](../.archive/executor-review/native-capture-ack-sol-source-r2-review.json),
[Opus R1](../.archive/executor-review/native-capture-ack-opus-source-r1-review.md),
[parent arbitration](../.archive/executor-review/native-capture-ack-opus-source-r1-arbitration.json),
and [failed compiled100](../.archive/executor-review/native-capture-ack-parent-r2-compiled100-failure.json).
Earlier replay omitted0.167ms glue/retry wait and had an invalid reduced-mode
baseline; those outputs are superseded by the corrected parent proof. The
root-added dedicated full-run missing-callable test is explicitly deferred as
redundant with unchanged guard and actual callback-rejection cleanup; accepted
reject/post-notification failure and receipt propagation regressions remain.
Modeled receipt substitution uses the real provider with an external capture
fixture; it is not a concurrent real-C producer race proof.

## Next live gates, in order

1. Parent offline checks and Sol approval are complete; obtain actual Opus final
   source/test approval after the fixture correction. Finish current ordinary
   save/ACK/reopen chain; sole GUI owner closes
   AH with fresh pending0/ordinary/released evidence. Promote exact accepted six
   files and restart daemon while quiescent. Use new PID/generation, never stale
   bindings. Main has no conflicting changes in these six files since1cbaadf.
2. Canonically recover any existing checkpoint before new calibration. Run fresh
   native control preflight, resume and measured native100 with full evidence.
   Verify operation/finalization and native true. Failure requires preserved
   trace/frame, fresh pause, ordinary recovery/reopen; no unchanged blind rerun.
3. Public pause then canonical ordinary recovery: PAUSED/native true/inputfalse,
   checkpoint clear, no stale operation/action. **Only then ask user availability**
   for physical input calibration.
4. Resume INPUT_CALIBRATION and start input-calibrate with actual fresh generation.
   Wait kindinput/staterunning/readiness.ready and the separate owned GTK prompt.
   Require real human pointer motion, ordinary key press/release and button
   press/release. Never synthesize. First event intentionally pauses/gen++;
   do not resume early. Wait about120.5s for completion/native+input true.
5. Resume/reconcile and independently verify three autonomous900s full cycles.
   Do not claim launch qualification before every gate passes.

## Entrypoints, backups and preservation

Python `/home/dev/repos/pegasus/.venv/bin/python`; session CLI
`/home/dev/.local/bin/crowley-session`; config `~/.config/crowley/session.toml`.
Helper `tools/native_calibration_operator.py`; templates
`~/.local/state/crowley/executor-evidence/native-live-controls-20261019/templates.json`;
matcher root `~/.cache/crowley/template-matcher/v1`.
Helper options: `--generation CURRENT --config CONFIG --templates TEMPLATES
--matcher-artifact-root ROOT {recover,control-preflight,measure-deferred}`.
Use exact returned generations and canonical ownership/fence/recovery protocol.

Latest validated private backup: `beta-20261019T161201Z-50bfce1be0f0`, through118
ingestion; directory0700, manifestSHA
`0a1e4826c881f637453a2a444567f2bc2ac1f996104c72b0024bd960e5d6195c`.
[Backup verification](../.archive/executor-review/market-backup-20261019T1612Z-parent-verification.json).
Next hourly backup about17:12UTC. Prior isolated restore drill remains accepted.
API: `tools.market_backup.snapshot` then `validate_snapshot`; retain full
invocation output privately and publish only sanitized hash/coverage/mode proof.

Keep raw frames, receipts, SavedVariables, process/command logs and backup
contents private under existing state directories. Logs/files0600, directories
0700. Never edit game SavedVariables to make an upload pass. Retain original
source/import/process pins and truthful assisted/model/compiled/live labels.
Repository skills stay small and source controlled: client contracts and local
game control contain the demonstrated timing/fixture lessons.
