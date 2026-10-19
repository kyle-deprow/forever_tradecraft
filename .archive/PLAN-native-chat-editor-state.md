# Native chat editor state guard plan

Status: IMPLEMENTED, VERIFIED AND INSTALLED after Sol and actual Opus5.5
READY. Full helper89 and parent focused10 tests pass. Live native100 remains
a separate pending gate. This plan replaces
the rejected row-mask candidate after the fresh full-frame gate found two
counterexamples.

## Objective

Make the initial `NativeCalibrationOperator._chat` precondition decide whether
the fixed 460x37 capture shows a positively identified inactive/closed editor.
Only that state may proceed to physical input. An active editor, an unsupported
or malformed crop, a black/ambiguous crop, or a mixed visual signature must
refuse before OCR-as-command or any key event. Preserve the existing identity
validation that guards the capture itself.

The typed-command OCR path remains the accepted path byte-for-byte in behavior:
fixed crop `(40,7,400,13)`, grayscale conversion, threshold-45 cursor removal,
bicubic scale 3, tesseract `--psm 7`, normalization, and exact expected-command
comparison. The rejected candidate's row-zero mask is removed entirely from the
future implementation. No OCR whitelist, fuzzy replacement, punctuation repair,
per-command branch, relaxed exact comparison, or blanket binary state dependency
is allowed.

## Scope and baseline

Only these two MAIN source files may change after review:

- `tools/native_calibration_operator.py`;
- `tests/test_native_calibration_operator.py`.

The implementation starts from the accepted MAIN files, not the rejected worktree:

- helper SHA256
  `1cbc51f825fe775847733801354d80ad250201ac0b9e8c5eeb4842980dfad211`;
- test SHA256
  `56a5c50e6ebf071e7cb77defcf0ca28a6bcba01802386f192112ad5fa23d3314`.

No driver, daemon, decoder, addon, runtime, Rust, configuration, service,
GUI, schema, lease, or lifecycle change is in scope. The helper-only release
needs no service restart. Private original screenshots and receipts remain
outside Git.

## Evidence and rejected candidate

The fresh gen29 receipt is
`/home/dev/.local/state/crowley/executor-evidence/runtime-relink/chat-fixed-command-suite-gen29-20261019T081811826074Z/receipt.json`,
SHA256
`806c14992dea27eeab2f1445d82f7c2f299cb476c15ed7faafc6d4c484060e4a`.
The original 1920x1080 frames were cropped by production
`X11Screen.chat_crop=(30,938,460,37)`.

The rejected candidate changed the two source files to
`b784b58c5e6f0d33087f554d5535a1376ce761334c8d3699f956b760aa84c372` and
`bea08f61f77f127926d1c20ce036230b45afbff5992c2061c466dd175f556a25`.
Its full helper test passed 85 tests in 346.30 seconds, but the private fresh
gate passed only 22/24 cases:

- Case 6, `/crowley agent resume`, closed sequence 138, is visually an
  inactive transparent editor over player/world texture. The body-row counts
  above threshold 45 are
  `[158,38,44,62,78,106,110,103,104,112,115,110,112]`; row maxima are
  `[77,57,58,60,63,65,64,64,64,65,70,67,67]`. Production OCR returned
  `nn ee fs a eee`; the row-mask candidate returned
  `~ »o Sa has 7s _-`. The inactive frame must never be interpreted as a
  command.
- Case 8, active sequence 155, visibly contains exact `/reload`. The
  accepted OCR returns `/reload`; the row-mask candidate returns `reload`.
  The mask therefore changes active typed segmentation and cannot be repaired
  by a text substitution.

The private diagnosis is
`/home/dev/.local/state/crowley/executor-evidence/native-chat-border-r3-20261019T081910/fresh-gen29-diagnosis.txt`,
SHA256
`de2d3b380d2e86af7a2bdb5589f450b35f2abc2979fb3b9e8c7fc4b12edab1f8`.
The rejected full-test log is
`/home/dev/.local/state/crowley/executor-evidence/native-chat-border-r3-20261019T081910/full-native-helper.log`,
SHA256
`203fd64ff0ef0d756c4c194f642abdf7511890fc26ab72973eb7d19ad7095550`.

## Measured visual contract

All measurements below use grayscale pixels from the production 460x37 crop,
columns x=40..439. The existing body box starts at y=7. The visual guard uses
four fixed horizontal chrome rows outside OCR text: y=4, y=7, y=23, and y=25.

Retained active-empty full screenshots
`hud-live-20261017T124101681159Z/desktop.png`,
`124225785057Z/desktop.png`, `125627318385Z/desktop.png`, and
`125531629649Z/desktop.png` are private evidence. Their y=7 body row has
median 211, maximum 213, and all 400 pixels above 150. Their y=23 row has
median 227, maximum 232, and all 400 pixels above 150. Their desktop SHA256
values, in that order, are:

- `912d7d042b0133442bb4030ae0f73b45ced568f431cbca97a34c9173ee3b79de`;
- `6bef4713d44143ae525e762969331c5665d0f94678784e1a64e9fc3d511ca14e`;
- `627368e481572f3a916111da52bc004c2483007f6402b9d4ed6159bfead068f8`;
- `ff6bddce9ce11eab7731ef15893ab3dffc34aabace17e887c7564b5c6b69b18e`.

The active typed frames in gen29 have the same bright rows. The accepted
inactive closed frames, including the difficult case 2 and case 6, have these
measured medians:

| state | y=4 | y=7 | y=23 | y=25 |
|---|---:|---:|---:|---:|
| inactive baseline closed fixture | 67 | 34 | 61 | 66 |
| inactive case 1/3/4/5/7/8 | 67 | 35 | 61 | 66 |
| inactive case 2 | 75 | 42 | 69 | 74 |
| inactive case 6/world texture | 74 | 41 | 68 | 75 |
| active empty/typed | 147 | 211 | 227 | 146 |

The gen29 original case 6 full frame is
`cmd06-closed-01.png`, SHA256
`ec8b7ef5a1dcff40d4be39abb04cbebc1aeead44e67c955c6b41315bc7177c27`.
The gen29 original active `/reload` frame is
`cmd08-staged-01.png`, SHA256
`a595c5626a07ae5da44f1392e863008133b52426e51dba78c771822dabfe5055`.

These measurements support a positive four-row chrome signature. They do not
support treating every low-brightness image as closed.

## Proposed implementation

Add a small private classifier in `native_calibration_operator.py` that reads
the already captured 460x37 image and returns exactly `active`,
`inactive`, or raises `OperatorError` for `unknown`. It must first require
the exact crop dimensions and convert to grayscale. It must not resize, invoke
Tesseract, normalize OCR, inspect command characters, or use chatEdit telemetry.

The initial fixed-profile thresholds are:

- active: median(y=4) >= 130, median(y=7) >= 180,
  median(y=23) >= 180, median(y=25) >= 120, and at least 95% of both y=7
  and y=23 pixels are >= 150;
- inactive: median(y=4) in [50,100], median(y=7) in [20,60],
  median(y=23) in [45,90], median(y=25) in [50,100], with maximum y=7 and
  y=23 below 150;
- every other valid crop is unknown and refuses.

The active thresholds have margins below the measured minima (active y=4=147,
y=7=211, y=23=227, y=25=146). The inactive ranges include the accepted
grayscale fixtures, all ordinary closed gen29 frames, closed case 2, and the
world-texture case 6. The lower bounds reject an all-black/empty unsupported
crop; the upper bounds and paired rows reject the bright active chrome. A
future frame outside this measured profile must stop and be remeasured rather
than being widened automatically.

The classifier must be called immediately after the initial `_capture` in
`_chat`, before closed OCR or any physical key. Existing capture identity guards
remain in their current order.
An active result raises a specific active-editor refusal. An unknown result
raises a specific unknown-visual-signature refusal. An inactive result is the
only state that permits the precondition to continue. Closed-world pixels and
their OCR output are never interpreted as command text; the initial closed
capture is used only for the positive visual state guard.

The typed capture continues through the baseline `_ocr_file` unchanged and
must normalize to the exact fixed command. Active empty and active nonempty
captures are both refused at the initial precondition, before any Return or
type action. The state classifier may publish a bounded receipt event with the
state and measured row summaries, but it must not publish image paths, raw
pixels, or chat text.

For explicit offline orchestration tests that use synthetic non-chat paths, add
a constructor-injected `chat_state` seam whose production default is the
visual classifier. Existing fake OCR tests must explicitly inject an
`inactive` state or use the 460x37 UI fixture; there is no production fallback
that skips the guard. The focused OCR tests and actual composition fixture use
the default classifier and real 460x37 captures.

## Test and acceptance matrix

Add self-contained sanitized grayscale 460x37 fixtures derived from retained
UI-region evidence. A fixed chat-region fixture may retain the background
texture visible through the inactive editor, after confirming it contains no
chat history, account identity or other private text. No original desktop/full
game-world frame, private receipt, or raw client state enters Git. The test
changes must cover:

1. active-empty fixture: state `active`, `_chat` refuses before the first
   input call and before OCR-as-command;
2. active typed `/reload` and all eight fixed commands: state `active`,
   baseline OCR remains exact, and the initial guard refuses before input;
3. positive inactive baseline, closed case 2, and closed case 6/world-texture
   fixture: state `inactive`; the initial guard passes without interpreting
   OCR noise as a command;
4. unknown black crop, unsupported border signature, and malformed dimensions:
   state refusal occurs before OCR-as-command and before any input;
5. an active nonempty frame with a visible command is refused as active, proving
   the old nonempty-closed safety property without fuzzy OCR;
6. exact typed readback remains strict: missing slash, extra text, or OCR
   corruption raises the existing mismatch error and sends Escape only after
   the typed readback mismatch, never as a way to repair text.

The common offline helper fixture must retain actual input-call assertions. Fake
orchestration fixtures may use the explicit injected state seam, while the
visual contract tests must use the default classifier and exact image
dimensions. Update only the minimum existing fake screen/capture fixtures
needed to provide that seam; do not replace actual operator composition with a
fake state result.

The parent private proof must execute the actual production sequence:
original full 1920x1080 frame -> `X11Screen.chat_crop` -> `_capture(crop=True)`
-> visual closed guard -> `_chat` -> baseline OCR/normalization. Its private
input recorder may replace physical input, but the production screen crop,
capture path, state classifier, OCR, and exact guards must remain real. It must
prove, before any input:

- active empty refusal;
- active nonempty refusal;
- unknown/malformed refusal;
- inactive closed acceptance with no world-texture interpretation.

It must then prove all eight staged commands and `/reload` exact readbacks,
closed transitions, and nonempty-closed refusal behavior from original full
frames. An ordinary chatEdit value may corroborate a frame but cannot decide
the visual state, because release may occur with the Agent surface absent and
other phases may have no chat surface.

The private runner is to be created outside Git at
`/home/dev/.local/state/crowley/executor-evidence/native-chat-editor-state-r1-20261019/verify-editor-state-r1.py`.
Its invocation and output must record the worktree, source/test hashes, every
original-frame hash, crop geometry, classifier row summaries, OCR raw and
normalized output, input-call log, exit code, and import origin. Private
evidence must remain mode 0700 for directories and 0600 for files.

## Verification gates

Implement only after Sol and parent accept this plan. Before the long helper run,
run and preserve exact logs for:

```
cd /home/dev/.cache/crowley/worktrees/native-chat-editor-state-20261019
.venv/bin/python -m pytest -q tests/test_native_calibration_operator.py -k 'chat or ocr'
.venv/bin/ruff check tools/native_calibration_operator.py tests/test_native_calibration_operator.py
.venv/bin/ruff format --check tools/native_calibration_operator.py tests/test_native_calibration_operator.py
.venv/bin/python -m py_compile tools/native_calibration_operator.py tests/test_native_calibration_operator.py
git diff --check
```

The focused result must include the actual active-empty, active-nonempty,
inactive-world, and unknown refusal tests. Run the private original-full-frame
proof, then freeze and report both source hashes, private runner hash, command
lines and exits before starting the full helper file exactly once:

```
.venv/bin/python -m pytest -q tests/test_native_calibration_operator.py
```

Parent reproduces the focused checks and private proof, then Sol and actual
Opus review the two-file delta while the stable full helper check runs.
Promotion requires green
focused checks, green full helper tests, exact typed OCR for all eight commands,
all refusal/acceptance cases above, frozen source and private-runner hashes,
parent reproduction, and both reviews READY. No service restart or live native
claim follows from this helper-only change; live recovery, preflight,
native100, pause/recovery, and ordinary collection remain separate gates.

## Risks and stop conditions

The four-row thresholds are intentionally strict and profile-specific. Any new
client scale, border, theme, crop geometry, bright inactive frame, or dark
active frame is an unknown refusal until measured from fresh original frames.
Do not widen thresholds, add text repair, mask more rows, or use a stale
private crop to make a case pass. A failure in any active-empty, active
nonempty, inactive-world, malformed, or exact typed case stops promotion and
requires a revised plan.
