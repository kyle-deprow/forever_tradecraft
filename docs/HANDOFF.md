# Forever Tradecraft handoff

Updated 2026-10-19 14:46 UTC. This is the active handoff. The exact preceding640-line
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

Latest fully parent-verified cycle **#113**:

- UID `beta-normal-alliance-1792420611-Arthur-0821`;
- start1792420611, finish1792421087:476s;428 observations/2,146 rows;
- 413 full/15 bounded, all428 `ok`, zero query failures;
- exactly900s after112;30.120801s finish-to-server receipt;
- original saved/server digest agreement, exact loaded ACK, pending0, reopened
  AH, normal0/inactive fence, zero speed and released controls;
- [scan proof](../.archive/executor-review/build-70450-onehundredthirteenth-scan-parent-verification.json)
  and [reopen proof](../.archive/executor-review/build-70450-onehundredthirteenth-ah-reopen-parent-verification.json).

Next ordinary deadline1792421511 (14:51:51UTC). Sole operator continues full
assisted900s chains until root has a concrete reviewed release ready. No native
or physical-input retry yet. Scans108..113 all have verified exact900s starts.
After106 a real WOW51900319 disconnect caused107 to start350s late; normal
reconnect succeeded without credentials. The old memory notification said8hours
ago; no new OOM cause is established. See archived links for exact proofs.

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

## Current blocker and implementation

Livegen37 requested update2 but captured3; recovery38 succeeded. Parent decoded
the retained offending PNG. Screenshot starts were1384.571ms apart; screenshot
work28.957ms. Timed identity work926.812ms plus another142.073ms deferred-owner
interval dominates. This does not establish Rust computation as a bottleneck.
[Live timing proof](../.archive/executor-review/native-live-budget-failure-gen37-parent-verification.json).

Isolated worktree:
`/home/dev/.cache/crowley/worktrees/native-identity-budget-20261019`, base1cbaadf,
offline venv. Exact allowed files:

- `src/crowley/session/{daemon,calibration,driver}.py`;
- `tests/test_session_runtime.py`;
- `tests/test_session_native.py`;
- `tests/test_native_calibration_operator.py`.

No Guardian, lease, binary/protocol, addon, Rust, helper, service, config or public
schema changes. Preserve fresh backend-pre/backend-post/runner-post identity
checks, full fallback checks and every owner/generation/lease/profile/B0/pixel/
CRC/ordinal/sequence/cadence/freshness guard. Only three approved redundant
identity resolutions may be removed for the exact deferred update provider.

Authoritative plans:

1. [Identity-budget base](../.archive/PLAN-native-identity-budget.md).
2. [Pre-ACK alignment correction](../.archive/PLAN-native-capture-ack-alignment.md),
   approved Sol R2/parent. This supersedes the failed pre-backend alignment.
3. [Current staged review closure](../.archive/PLAN-native-ack-review-closure.md),
   parent-approved to implement accepted Sol source-review findings; it is not
   itself a claim of Sol source approval.

Timing origin uses verified receipt hostS1 and publisher uptimeU1, then
`S1 + unsigned_delta(U_previous,U1)/1000 + 1.050` for eligible updates2..99.
Publisher callback drift is real: verified two-tick delta2014ms. Never accumulate
phase guard, restamp clocks, move independent ticks after capture, skip/retry an
ordinal mismatch or hide active work. Preserve pinned cases and900ms active
budget; count all actual validations/ACK admission and retry work. Held100 is
separately outside streaming work bound but retains every exact terminal proof.

**Current action: Luna implements the consolidated five-Must fix round.**
Sol formal source-review R1 was NEEDS WORK; parent accepted all findings:

1. Notify actual retained held100 evidence after all checks/resume_required and
   before resume; keep path/hash and `retained` ownership, never false release.
2. Bind the exact locally validated receipt to the anchor, avoiding a later
   mutable last-receipt reread. Test same-digest receipt substitution.
3. Carry one original bounded attempt deadline, preserve15s producer upper
   bound, and recheck shutdown/expiry under final Guardian lock after contention.
4. Charge actual old deferred validation142.073ms and separate final ACK
   admission0.500ms; phase951 must really protocol-fail.
5. Arm compositor entry markers and cover actual typed success/deadline/expiry/
   unhealthy/PID/process/epoch/finalACK races, exact zero/one ACK/capture and
   cleanup. Existing broad passes do not cover omitted paths.

[Formal review findings](../.archive/executor-review/native-capture-ack-sol-source-r1-review.json).
Closure-plan SHA `113a3513af6e15c169da1d6363f1192b5e81fb15ec59a54d3b6ebb7a682c3759`.
Worker must map every requirement to a named test/result before freezing again.

## Offline evidence and remaining review

Earlier candidates are partial/rejected, not installed or qualified:

- [Rejected phase-reanchored model](../.archive/executor-review/native-ack-model-reanchoring-parent-rejection.json).
- [Parent R1 gate](../.archive/executor-review/native-capture-ack-parent-r1-gate.json).
- [Frozen R2 compiled100 failure](../.archive/executor-review/native-capture-ack-parent-r2-compiled100-failure.json).

R2 worker focused15 tests passed145.01s. Parent twice reproduced8 semantic cases
with unchanged six-file pins. Exact long compiled100 node FAILED132.53s because
the observer omitted retained held100. Parent independently checked journal
held100/updateCount101/seq102 and normal0/resume seq103; this is partial journal
inspection, not a passing full gate. Parent preserved71 regular artifacts
outside pytest retention under private
`native-ack-parent-focused-r2-20261019T1420Z/failed-compiled100-artifacts`.
Full R2 source pins/snapshots/logs are in that private parent directory.
Worker logs: private `native-identity-budget-alignment-20261019/`.

Required exact long node after final focused checks, pins and milestone:

```text
tests/test_native_calibration_operator.py::test_actual_operator_measure_composes_x11_screen_daemon_and_agent[success]
```

Short six-second region compositor tests do not replace it. Retain the real
observer's exact construct0,held0,updates1..99,retained held100,resume0 sequence.
No fixture-manual spans/finish calls or unlogged test pipelines. Full private
logs and six-file pins before every long test; no unchanged blind reruns.

Sol must re-review fixed frozen source. **Actual Opus source review has not
started.** Its prepared private runner/prompt are under
`native-identity-budget-opus-r1-20261019/`; update input/prompt to final six-file
scope and current closure plan before launch. Requires actual
claude-opus-5-5/exit0/STATUS, no fallback; monitor attached process at most30s
intervals. Parent must inspect/reproduce relevant final checks and compiled100.

## Next live gates, in order

1. Complete focused/model/actual compiled checks and Sol plus actual Opus source
   approval. Finish current ordinary save/ACK/reopen chain; sole GUI owner closes
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

Latest validated private backup: `beta-20261019T141236Z-37ca1a7066b4`, through110
ingestion; directory0700, manifestSHA
`af0b06dba4009dc7aec3957057fa0fa9d972dfc5846c8411712b3b6017d6d283`.
[Backup verification](../.archive/executor-review/market-backup-20261019T1412Z-parent-verification.json).
Next hourly backup about15:12UTC. Prior isolated restore drill remains accepted.
API: `tools.market_backup.snapshot` then `validate_snapshot`; retain full
invocation output privately and publish only sanitized hash/coverage/mode proof.

Keep raw frames, receipts, SavedVariables, process/command logs and backup
contents private under existing state directories. Logs/files0600, directories
0700. Never edit game SavedVariables to make an upload pass. Retain original
source/import/process pins and truthful assisted/model/compiled/live labels.
Repository skills stay small and source controlled: client contracts and local
game control contain the demonstrated timing/fixture lessons.
