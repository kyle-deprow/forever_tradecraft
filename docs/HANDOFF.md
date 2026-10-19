# Forever Tradecraft handoff

Updated 2026-10-19 13:26 UTC. This is the active operational handoff. The exact
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
- Diagnostic release is installed after Sol R3 and actual Opus5.5 R3 READY,
  parent runtime14 checks and independent 135.08-second actual composition PASS.
  Controlled restart at10:08:17 UTC replaced PID781512 with3891378; fresh daemon
  state is PAUSED generation32/nativefalse/inputfalse/operationidle/handshakeidle.
- Assisted #99 is fully parent-verified. Its start interval was exactly900s;
  the parent also verified the closed-AH/pending0/ordinary boundary afterward.
- The helper contrast fix is installed after Sol R2 and actual Opus5.5 R2 READY.
  Parent independently verified live `/reload` readback and ordinary recovery at
  generation36 from retained original1920x1080 and derived460x37 images.
- Native measurement at generation37 got past the fixed chat commands, then
  requested update2 and observed3. The instrumented failure trace and offending
  PNG are retained and independently verified. No native100/input qualification.
- Recovery38 succeeded. Parent verified reopened AH/ordinary normal0/inactive
  fence/pending0/zero movement/released controls. Assisted #100 started1792408561,
  934s after #99 and34s late due to calibration; nextdue1792409461. Its428-item,
  2,015-row sweep finished with0 query failures; fullsave/ACK/reopen is now
  parent-verified. #101 through #106 are also fully parent-verified; all started
  on exact900s deadlines. After #106 the client disconnected (WOW51900319).
  Normal reconnect succeeded without credentials. Parent decoded retained reopen
  bytes: #107 started1792415211,350s late, and is now fully parent-verified.
  #108 started on its exact900s deadline1792416111; nextdue1792417011.
- Sole GUI operator continues assisted collection while Luna implements the
  Sol R2/parent-approved native identity-budget plan in an isolated worktree. No unchanged native retry or physical GTK gate.
  Obtain fresh controller state/generation before any future mutation.
- Current work must preserve fresh evidence generations, exact commands, and
  the physical game-window boundaries. Do not infer a live result from a stale
  screenshot, a private fixture, or an external OCR crop.

## Latest accepted collection

Parent verification #107 completed the operator-assisted scan for UID
`beta-normal-alliance-1792415211-Arthur-7147`:

- 428 observations, 2,098 rows, 413 full and 15 bounded, all `ok`;
- 485-second scan, 54.638861 seconds from finish to server receipt;
- 1250-second start interval after #106;350s late due to disconnect/recovery;
- exact saved-variable/server digest agreement and independently decoded exact
  loaded ACK/pending0, reopened AH, ordinary normal0/inactive fence, released
  controls and zero movement;
- [scan verification](../.archive/executor-review/build-70450-onehundredseventh-scan-parent-verification.json)
  and [reopen verification](../.archive/executor-review/build-70450-onehundredseventh-ah-reopen-parent-verification.json).

#108 started1792416111 on exact900s deadline; nextdue1792417011.
#106 is fully verified:428observations/2,098rows/416full12bounded/allok,
479s scan,31.627216s finish-to-serverreceipt,exact900s after105.
#105 is fully verified:428observations/2,067rows/416full12bounded/allok,
481s scan,22.672271s finish-to-serverreceipt,exact900s after104.
#104 is fully verified:428observations/2,061rows/415full13bounded/allok,
494s scan,38.780301s finish-to-serverreceipt,exact900s after103.
#103 is fully verified:428observations/2,074rows/414full14bounded/allok,
479s scan,61.907489s finish-to-serverreceipt,exact900s after102.
#102 is fully verified:428observations/2,091rows/416full12bounded/allok,
479s scan,55.017523s finish-to-serverreceipt,exact900s after101.
#101 is fully verified:428observations/2,054rows/416full12bounded/allok,
480s scan,53.081652s finish-to-serverreceipt,exact900s after100.
#100 is fully verified:428observations/2,015rows/417full11bounded/allok,
497s scan,53.210904s finish-to-serverreceipt,934s after99 due to calibration.
#99 is fully verified:428observations/2,054rows/418full10bounded/allok,
479s scan,62.218005s finish-to-serverreceipt,exact900s after98.

After #99, sole operator closed the AH with one guarded Escape before calibration. Parent independently
decoded retained frame592deac4: ordinary normal0/inactive/pending0, exact99ACK,
AHclosed/speed0/released controls. This is the [fresh calibration boundary](../.archive/executor-review/native-chat-contrast-preflight-boundary-parent-verification.json).
That calibration replaced the ordinary100 deadline by34s; the actual gap is above.
#98 is fully verified:428 observations/2,063 rows/419full9bounded/allok,
476s scan,61.315347s finish-to-serverreceipt,exact900s interval after97.

#97 is fully verified: 428 observations, 2,070 rows, 417 full/11 bounded,
all `ok`, 483-second scan,62.376083s finish-to-serverreceipt and exact900s
start interval after #96.

#96 is fully verified: 428 observations, 2,083 rows, 416 full/10 bounded and
2 incomplete (`query_timeout`), with426 `ok` observations. It took543s and
25.491240s finish-to-serverreceipt. Its1258s start interval was358s late due
to calibration refusal/recovery. First reopen refused a player tooltip;
a separate fresh Auctioneer hover and guarded click succeeded. Both original
receipts remain unchanged and linked by compound parent proof.
#95 is fully verified: 428 observations, 2,077 rows, 419 full/9 bounded,
all `ok`, 480-second scan and exact900s interval after #94.

#92 and #93 are fully verified (428 observations/2,012 and2,014 rows).
#94 started900s after #93; its initial reopen hovered a player and failed,
then a fresh-point guarded pulse succeeded. Both original receipts are
preserved and linked by compound parent proof. #95 started900s after #94. #91 was fully verified before calibration: 428 observations/2,047 rows,
419 full/9 bounded, exact900s start interval after #90. Its first reopening
failed; a separate fresh-point click succeeded and both originals are preserved
in its compound parent proof. #92 started1773s after #91 (873s late) due to
native qualification and recovery. No autonomous cycles are counted.

#87 and #88 both started exactly 900 seconds after their predecessors and are
fully saved/ACKed/reopened. #86 had a 1,086-second interval, 186 seconds late
because of calibration cleanup. After #88 reopening proof, Luna closed the AH
for calibration; the parent independently decoded the retained final frame:
pending 0, exact #88 ACK loaded, ordinary normal/0, inactive fence, dueAt 0,
stationary and released controls. The ordinary #89 due time, `1792397149`
(08:05:49 UTC), may intentionally be replaced by calibration. Retain the actual
resulting gap. Root must not mutate the controller while Luna owns the live chain.

#89 actually started at `1792397292` (08:08:12 UTC), a 1,043-second interval
after #88 and 143 seconds late because of calibration cleanup. It is fully
saved/ACKed/reopened. Its next ordinary deadline is `1792398192` (08:23:12 UTC),
which may intentionally be replaced by the OCR evidence and calibration gates.

#90 actually started at `1792398296` (08:24:56 UTC), a 1,004-second interval
after #89, 104 seconds late after evidence collection. Its next deadline is
`1792399196` (08:39:56 UTC). Parent now verified its complete 428-observation,
2,077-row save/ACK/reopen chain, 416 full and 12 bounded observations, all ok.
#91 started exactly on that deadline, 900 seconds after #90; its next ordinary
deadline was `1792400096` (08:54:56 UTC). Its chain is complete. The AH is now
closed for calibration with exact #91 ACK, pending 0, normal/0, inactive fence,
closed chat, zero movement and released controls. Public state is PAUSED29.
Record the resulting calibration-related gap; do not count these as autonomous.

The latest private backup is `beta-20261019T111106Z-717ede9b8040`, independently
validated after #99 ingestion, directory mode0700. Manifest SHA256:
`0c1cd73c92f3f7f7eedb57df9a40b2687b44c8934816064b6638978a5150171e`.
See [backup verification](../.archive/executor-review/market-backup-20261019T111106Z-parent-verification.json).
Next hourly backup: 12:11 UTC. Prior isolated restore drill passed; repeat only
if new evidence warrants it. Raw backup data stays private.

## Accepted installed release

The accepted OCR/Rust release was promoted to main in commit `6874993`. The
new [cadence correction release](../.archive/executor-review/native-publication-cadence-release-parent-verification.json)
changes calibration.py and two native test files and has been installed with a
controlled service restart. Addon 79, the native lifecycle implementation,
Rust-backed matcher and runtime retain their accepted versions. They are
installed; their public release record is
[native-helper-rust-final-release-parent-verification.json](../.archive/executor-review/native-helper-rust-final-release-parent-verification.json).
The installed artifact has SHA256
`75b18bd04cc3a9248f99ecdca3a1cdebe6e0d89c4d33eaebd600788177bcd80c`, CLI help
exited 0.

Current accepted source pins are:

- helper `tools/native_calibration_operator.py`:
  `63fd2b97e84f77b11f12f120dc0300e822611dcedce19213f5b949b40e657462`;
- helper tests `tests/test_native_calibration_operator.py`:
  `190497551114ff44cc7a9acf42a4d2234d238b9b8131bf74b4b050cc47bbae0a`;
- runtime `tools/template_matcher_runtime.py`:
  `edc5242e9eaf864e98b78b9904b28f8fac51927cc90a6001047a32ab8d36700d`;
- runtime tests `tests/test_template_matcher_runtime.py`:
  `302f74f2098dbd8a2eb6f1d3f417e8fd757b89bf66a6d854e921008661dbfa69`.

The [diagnostic release](../.archive/executor-review/native-observation-diagnostics-release-parent-verification.json)
adds bounded private timings and mismatch evidence while retaining every native
check. Current daemon SHA256 is
`4259e4de58b3b3d79f2fc595978907090a7f74666656a4af0c311a33602b0dad`;
calibration SHA256 is
`3a91f4fe690cd820329fe2536fc03e5c7de24e4c20649efdf1a705b8c147c8fc`.
Source/test pins, reviews, worker and parent actual configured-producer proofs,
service identity and explicit diagnostic limitations are in that release record.
No identity optimization is installed. Actual instrumented timing evidence is
required before reviewing any removal of redundant identity checks.

The helper now includes the reviewed editor-state guard. Full helper tests
passed 89 tests with 5 existing warnings in 350.09 seconds; parent focused checks
passed 10. Sol and actual Opus5.5 returned READY. See
[editor-state release verification](../.archive/executor-review/native-chat-editor-state-release-parent-verification.json).
The prior OCR R2 verification remains historical evidence for its baseline.

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
whitelist, or a per-command fallback. The command allowlist remains fixed. The initial crop must positively match
the inactive chrome profile; active empty/nonempty, unknown and malformed crops
refuse before input. World texture behind the inactive editor is not OCRed as
a command. Open typed chat must equal the exact expected command body.
Chrome assumptions: grayscale rows y=4/7/23/25 over x=40..439; active medians
>=130/180/180/120 and >=380 pixels at least150 on rows7/23. Inactive medians
50..100/20..60/45..90/50..100 and rows7/23 maxima<150. Anything else refuses.

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

## Native publication correction and current chat blocker

Actual gen25 measure-deferred reached construction/hold/measure with all entered
commands accepted, then refused `native update 2 publication cadence is not 1Hz`.
Failure receipt SHA256 `2618bf9c290a1d23d8719224ee2ae6c21b86e6f9348210227becdb36d6a26ac2`,
private `~/.local/state/crowley/native-calibration-operator/native-calibration-measure-deferred-20261019T071310353967Z-3732709-9cb62643/receipt.json`.
Do not retry the unchanged measurement or claim native100 success.

Sole GUI paused25→26 and recovered through the canonical helper, receipt SHA256
`c9bfc62a57514accf87b14233b2186258f1da3183a260841999b04f050ece9c2`.
Fresh ordinary boot `1792394161-128257`, AH initially closed, fence inactive;
reopen and preserve assisted collection. #86 due07:17:43 was delayed by calibration;
retain its actual start/gap. Sticky operation/handshake errors remain historical.

`calibration.py:4600` compares consecutive observation capture times against
0.75..1.25 seconds before decoding and calls this publication cadence. The parent
independently decoded all 13 original frames from the ordinary-state timing
profile: publisher deltas were 1,000–1,012 ms, while the first consumer capture
gap was 567 ms. See the [profile verification](../.archive/executor-review/native-publication-clock-profile-parent-verification.json).
This proves the clocks differ; the original failed native update 1/2 captures
were not retained and their exact timing cannot be reconstructed.

Sol approved the [correction plan](../.archive/PLAN-native-publication-cadence.md)
with no findings. Luna worker `luna_rust_matcher` implemented only
`calibration.py`, the actual Lua runner tests, and the two necessary native-runner
stubs in the regression file, in the isolated worktree
`/home/dev/.cache/crowley/worktrees/native-publication-cadence-20261019`.
The correction compares strictly decoded publisher uptime using `unsigned_delta`
and retains the same inclusive 750–1,250 ms limits. Capture freshness/order,
all 100 ordinal/sequence/update-count checks, identity, boot, artifacts and
cleanup remain independent requirements. No schema, GUI, addon, driver, decoder,
Rust or configuration change is in scope.

The full native file passed 159 tests; the worker focused set passed 10. Parent
reproduction passed eight initial focused tests, both added failure tests and
the actual compiled helper success composition. Ruff, format, compile and diff
checks passed. Sol source reviews and actual Opus R2 are READY with no findings.
Opus R1 requested the now-added stalled-capture and held/100 cadence negatives;
production code did not change in that fix round. Installed calibration SHA256:
`20fe37ca1bc8b69cae1aa8f3ce559ac08f822bd666243e303f249f4857a4a3ae`.

A supplemental legacy runtime selection returned 2 passed and 7 fixture failures
before runner entry: one stale capture stub reproduced against baseline code,
and six default desktop lease refusals. These unchanged fixtures need separate
isolation/maintenance; do not claim that suite passed or weaken the live lease.
The actual compiled helper integration passed independently against the fix.

The accepted three files were committed and pushed as `7d33d11`, and the service
restarted after #88. Fresh gen27 preflight passed. Gen28 measure-deferred then
refused the first closed-chat readback before any key/text dispatch or native
sample. Public pause advanced to 29 and canonical recovery succeeded; parent
independently decoded the ordinary stationary post-recovery frame. See
[live refusal and recovery](../.archive/executor-review/native-publication-cadence-live-chat-refusal-parent-verification.json).

Exact production OCR on the retained failed crop returns `el a a ee`. The
empty text interior has no pixels above threshold 45 outside its first row;
that row contains the brighter frame border. Comparing an accepted closed crop
shows the same texture brightened by the composited background. Do not whitelist
the OCR output. The [R3 correction plan](../.archive/PLAN-native-chat-ocr-border-r3.md)
was approved after correcting the mask ordering, but its isolated candidate
failed the required fresh full-frame promotion gate. Parent checked 24 original
frames: 22 passed; closed case 6 still OCRed changing world/character texture as
text, and typed case 8 lost the visible slash from `/reload`. See the
[candidate rejection](../.archive/executor-review/native-chat-border-r3-rejection-parent-verification.json).

The rejected helper is preserved privately and remains only in
`/home/dev/.cache/crowley/worktrees/native-chat-border-r3-20261019`; MAIN now contains the separate accepted editor-state guard, not that rejected
candidate. Do not promote the rejected mask or mask more rows blindly.
Any revised implementation needs a reviewed plan, actual full-frame closed and
open-empty/nonempty evidence, meaningful refusal tests, full helper checks,
parent reproduction and Sol/actual Opus review. A helper-only correction needs
no service restart.
The failed attempt retained only a crop, so do not claim its full frame exists.

Sol approved the replacement
[editor-state plan](../.archive/PLAN-native-chat-editor-state.md). Implementation
is isolated in `/home/dev/.cache/crowley/worktrees/native-chat-editor-state-20261019`,
with only the helper and its tests in scope. It positively classifies four
measured chrome rows as active or inactive, refuses unknown/malformed/black
images before input, and keeps the original typed OCR unchanged.

Parent reproduced ten focused tests, independently decoded all 26 retained
original frames, verified exact typed OCR source preservation, and reran the
actual crop/classifier/OCR/chat-guard proof for all eight fixed commands,
active-empty/nonempty, unknown, mixed-signature and malformed refusals. Fresh gen29 active-empty and restored
closed frames are separately verified in
[current active-empty evidence](../.archive/executor-review/native-chat-active-empty-gen29-parent-verification.json).
These are UI/retained-frame proofs with fixture admission/identity context,
not live native100 qualification.

The first full helper run returned 9 failed/79 passed because synthetic entry
and composed fixtures lacked required editor chrome. Luna corrected fixtures
without relaxing production thresholds. Final full helper passed 89 tests,
5 existing warnings in 350.09s, log SHA256
`f7ecd8820bdfd157b2985fb2198477b57ec7416f4972a41f4e5bc9c2411949cd`.
Sol source review is READY after adding its required mixed-signature negative.
Actual Opus5.5 source review is READY, exit0, no Must/Should findings. The fix
was installed without a service restart. At that earlier release helper SHA256:
`4db338bdbf328c59be1020370c1570de2354d5f4a1fcc8c3fc5e78e50935021b`;
tests `90c9aecd8c766d3a91f98e9f4838529a8692fa6ba3eadbed46c67727ae035a75`.
The native159 clock-correction evidence remains historical; the publisher
checks are preserved by the installed diagnostic hooks. The helper test now
additionally asserts the real configured-producer timing composition.

The live chain reached update3, then refused requested4 observing5 at gen30.
Public pause returned31. See [live failure evidence](../.archive/executor-review/native-live-skipped-update-gen30-parent-verification.json).
Existing daemon cleanup removed per-update provider captures, so timings/root
cause cannot be reconstructed from those images. No blind retry: Luna verifies
ordinary recovery/assisted collection while offline diagnosis proposes bounded
private timing and failure-evidence retention before another native attempt.
The [observation-budget plan](../.archive/PLAN-native-observation-budget.md) is
approved by Sol and parent for diagnostic-only implementation. Removing
identity work requires actual instrumented timings and a separate reviewed delta.
Five synchronous full identity resolutions are present per update; prior component
measurements bound each near0.193..0.223s. This is a budget hypothesis, not direct
gen30 full-path timing proof. Assisted #92 resumed at1792400969 (09:09:29 UTC),
a1773s interval/873s late after #91. Parent decoded ordinary post-failure state;
loaded ACK list was cleared by native reload, so do not claim current #91 ACK.
No live
native100 success is claimed, and no human input is needed until native100 and
ordinary recovery pass.

## Typed OCR correction and pending live qualification

Gen33 `/crowley agent defer` was accepted, but typed `/reload` returned
`reload` from the unchanged production OCR before native runner entry. See
[refusal and ordinary recovery](../.archive/executor-review/native-chat-reload-refusal-gen33-parent-verification.json).
The failed original fullframe was not retained; its exact460x37 crop is private.
The parent independently reproduced the missing slash. The failed vs accepted
full crop differs by at most4 grayscale levels, with the same2 cursor columns.

The [contrast correction](../.archive/executor-review/native-chat-contrast-release-parent-verification.json)
is now installed after Sol R2 and actual Opus5.5 R2 READY. It applies uniform
body-only autocontrast cutoff1 after400x13crop and before unchanged threshold45,
preserving all editor, geometry, cursor, resize, Tesseract and exact-text guards.
Private retention holds up to four exact original fullframes with unique capture
sequence and hashes; eviction failure skips the new optional original. Failed
readback diagnostics bind the actual typed crop, state, source hash and capped
OCR after the existing Escape attempt, without masking refusal or cleanup.
Parent reproduced all8 recorded fullframe commands and the actualfailedcrop
through actual candidate seams, with substituted capture/input/identity/admission
context; exact retained original bytes were independently verified. This is not
live native100 qualification. Full helper96 passed in352.23s on the same source
and earlier testpin71f92973; finaltest19049755 has exactly one added test,
verified against that prior hash, and18 focused tests pass in WT and MAIN.
No97-test full-suite result is claimed. Production CLI interpreter imports the
exact promoted MAIN helper. No service restart occurred.
R1 review failures and closures remain in the public R1 record. One redundant
callback assertion nit is deferred; a separate successful real-classifier JSON
test covers it. Autocontrast may OCR darker inactive body texture as text;
initial admission uses unchanged raw460x37 state guard, never closed-state OCR.
The failed gen33 fullframe remains unavailable.


## Instrumented native budget blocker

Fresh control preflight36 succeeded with the promoted helper before native
resume37; the parent matched receipt14b1713c/source63fd2b97. The initial
preflight35 failed before any capture/command, then recovery36 cleared it; its
sanitized receipt retains only operator_failure, so do not invent a finer cause.

The [gen37 failure and recovery proof](../.archive/executor-review/native-live-budget-failure-gen37-parent-verification.json)
independently verifies sequence15/publisher uptime218361571/updates ordinal3
from the offending256x256 PNG while ordinal2 was requested. Source drift=false.
Actual screenshot starts were1384.571ms apart; screenshot work itself took28.957ms.
Timed identity checks on the cross-capture critical path total926.812ms, with
another142.073ms pre-poll interval containing deferred-owner revalidation.
Do not double-count backend identity spans inside the capture span. Lock-to-
screenshot setup117.511ms is not fully split into admission/spawn/protocol I/O.

The [identity-budget plan](../.archive/PLAN-native-identity-budget.md) is approved
by Sol R2 and parent; [approval evidence](../.archive/executor-review/native-identity-budget-plan-review-parent-verification.json). Implementation is isolated in
`native-identity-budget-20261019` at base1cbaadf with only daemon/calibration
and their two named test files in scope. It targets duplicate full-window resolves on the eligible
configured deferred X11 provider while retaining fresh backend pre/post and
independent runner-post checks plus all cheap owner/generation/lease/process/
profile/source/B0 and exact pixel/cadence/sequence guards. This is not installed.
Publisher750..1250ms validation is not consumer work budget; repeated1.1s work
would still skip1Hz updates. The estimated876ms path needs realistic jitter
coverage and the actual100-update gate. The trace does not show Rust scoring
as a compute bottleneck. Do not add another instrumentation-only round unless
an unanswered fact actually blocks the reviewed correction.

The first isolated candidate passed its real configured-producer100 integration
case (137.82s) but failed parent pre-review: its timing replay bypassed production
scheduling, the revocation regression did not synchronize at actual admission,
some cheap owner bindings were incomplete, and full composition trace assertions
had been reduced. Luna is correcting these in the same four-file scope. This
candidate is not installed or source-reviewed; its passing integration alone
does not qualify it. Preserve the first-run evidence separately from the fix.

Sol independently confirmed that the intermediate replay still inserted a
fixture-only alignment wait and bypassed `NativeCalibrationRunner.run()`.
It also added a non-evidence10ms charge and dropped0.040ms residual glue. The
correct reduced vector is876.026ms. An unaligned consumer can capture a duplicate,
then pay active retry costs exceeding900ms. Luna is replacing that replay with
the actual runner lifecycle and independent1000ms publisher, preserving its
genuine outcome. The [alignment amendment](../.archive/PLAN-native-identity-budget-alignment.md)
is approved by Sol R2 and parent; [approval evidence](../.archive/executor-review/native-identity-budget-alignment-plan-review-parent-verification.json).
Luna is implementing production alignment and the actual-run fixture within
the same four-file scope. Every new cheap validation and target calculation is
counted as active modeled work; only sleeper duration is wait. Numeric jitter
cases and the terminal held100 budget exception are pinned in the plan.
No source approval or installation yet. Assisted collection continues.

At13:00 the implementation worker was paused for a diagnostic checkpoint after
it kept editing/testing without returning requested status. The actual-run
selector reportedly exited1 after107.35s: aligned exactupdates1..99/held100/resume,
but first alternating-jitter transition1492.444ms active due one duplicate/retry;
later transitions882..889ms. No full output/first-shot timeline was retained.
The [reported failure record](../.archive/executor-review/native-alignment-jitter-reported-failure-parent-record.json)
distinguishes that report from independent runtime verification. Four current
files are parent-hashed in the private diagnostic snapshot125916Z. Sol is
assessing fixture versus production behavior read-only. No more implementation
edits/tests or source approval until that assessment; old redundant test PID
3888223 and parent3813817 have exited. Actual source Opus review has not started.

Separately, [post106 disconnect evidence](../.archive/executor-review/build-70450-post106-disconnect-parent-verification.json)
is byte- and visually verified by parent. Two strict watcher refusals preceded
the actual WOW51900319 screen. Its memory notification explicitly says8hours ago;
no new OOM event/cause is established. Sole GUI owner may reconnect normally,
including the already-authorized standard launcher path if required, then restore
Arthur at IF AH and full ordinary chains with fresh identity/generation evidence.

Sol completed that diagnostic assessment: admissions1s apart produce994ms
between shots in the pinned alternating vector. The pre-backend rolling target
is insufficient. The fixture also misplaces producer/glue charges, measures
provider acceptance rather than pixel sampling, and omits old deferred owner
validation. The new [capture ACK alignment plan](../.archive/PLAN-native-capture-ack-alignment.md)
is a draft under Sol review. It proposes a narrowly scoped private driver
pre-ACK hook and six named files; no production edits authorized yet. Luna may
correct ONLY the runtime fixture, parameterize the cases and retain one honest
logged alternating failure with all-shot timeline against preserved source.
All further long runs must retain exact output and pins; no phase/vector tuning.

Normal reconnect and Enter World succeeded without credentials. Parent verified
[reopen payload bytes](../.archive/executor-review/build-70450-post106-reconnect-parent-verification.json),
boot1792415028-366418/sequence169/ordinary normal0/inactive/pending0/speed0/AHopen
and107start1792415211. The receipt lacks per-capture monotonic timing, so this
does not establish independent freshness or calibration qualification. The
start interval after106 is1250s,350s late due to disconnect/recovery.

Parent independently reproduced the corrected alternating baseline at unchanged
six-file pins: [model failure verification](../.archive/executor-review/native-alignment-corrected-baseline-parent-verification.json),
max active1489.444ms, exact99updates/held100/resume. Second shot was995.540ms
after first and repeatedordinal1. Full0600log and timeline retained in private
`native-alignment-parent-alternating-20261019T131855Z`; runtime pin023cbf3c.
One identical sampler callback duplicated a single attempt's record; it is
documented and must be fixed before qualification, not counted as a new capture.

Sol rejected the ACK plan's first revision: Agent.lua recursively schedules
After(1), and verified live two-tick delta2014ms means an absolute1000ms schedule
can drift early. R2 is under review: verifiedS1/U1 and prior accepted publisher
delta plus constant50ms phase guard, realistic1007/[1000,1014] publisher cases,
explicit phase envelope, exact PID/one-shot ACK and nonblocking Guardian health
guard, separate final ACK admission cost. No production ACK implementation yet.

## Next live gates

Run these gates in order, preserving the fresh generation and the exact command
history in each receipt:

1. Review and implement the identity-budget correction within its exact scope;
   parent independently reproduces focused checks and actual configured-producer
   100-update composition, and Sol plus actual Opus approve the frozen sources.
   Keep assisted collection running in parallel. At the release boundary, finish
   the current save/upload/ACK/reopen chain and close AH with fresh ordinary
   pending0 evidence. Install exact accepted files and perform one controlled
   daemon restart while quiescent; use the fresh returned controller generation.
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
- [latest backup verification](../.archive/executor-review/market-backup-20261019T131230Z-parent-verification.json),
  independently validated through scan106; next hourly backup due about14:12 UTC.

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
