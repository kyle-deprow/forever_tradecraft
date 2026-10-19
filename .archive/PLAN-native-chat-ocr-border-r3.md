# R3 native chat OCR border correction plan

Status: REJECTED at the fresh full-frame promotion gate. The isolated candidate
helper b784b58c passed 22 of 24 fresh cases but still OCRed world texture as text
in closed case 6 and dropped the visible slash in typed case 8 `/reload`.
The installed helper remains unchanged. See
`executor-review/native-chat-border-r3-rejection-parent-verification.json`.
Do not implement or promote this proposal without a revised reviewed plan.

This is a bounded candidate plan. Production source remains unchanged until
Sol review and parent release. The only implementation files are
`tools/native_calibration_operator.py` and
`tests/test_native_calibration_operator.py`.

## Evidence

The retained gen28 failure crop is 460x37, SHA256
`c481bd15cf2fcaae8eb06cc757c38fa1a3df13f4bb97b9cce6dea1facc011b62`. The
current production path returns raw `el a a ee\n`, normalized `el a a ee`,
before any input or native sample. The false foreground is in the first row of
`CHAT_OCR_BOX=(40,7,400,13)`; rows 8 through 19 have no pixels above the
existing threshold 45. The accepted closed frame has the same frame texture
below threshold. The difference is a measured brighter composited background,
not chat text, a cursor, or a lifecycle change.

The private retained suite uses original 1920x1080 frames and the production
`X11Screen.chat_crop=(30,938,460,37)`. The candidate was evaluated by cropping
those originals through that exact geometry, then using the existing OCR and
normalization path. It produced 8/8 empty pre-captures, 8/8 exact typed
commands for `/crowley agent defer`, `release`, `recover`, `hold`, `measure`,
`resume`, `finalize`, and `/reload`, and preserved every closed-state result.
The genuine nonempty `/reload` closed check remained nonempty and therefore
remains refused. The private suite receipt and raw frames remain outside Git.

The corrected ordering was measured on both retained lighting states. On the
bright failed crop, the body probe was 129 columns at 1/13 before masking and
400 columns at 0/13 after masking. The dark closed crop was 400 columns at
0/13 in both states. On the retained typed crop, the pre-mask probe had six
columns at 11/13 and two at 13/13; after masking those became six at 10/13
and two at 12/13. The existing 12/13 removal therefore still removes the two
tall cursor columns while the frame row cannot consume a glyph margin. No
bright same-scene typed frame is retained; that is a required live proof gate.

Current source pins are helper
`1cbc51f825fe775847733801354d80ad250201ac0b9e8c5eeb4842980dfad211` and test
`56a5c50e6ebf071e7cb77defcf0ca28a6bcba01802386f192112ad5fa23d3314`.

## Candidate change

Keep the fixed crop, grayscale conversion, bicubic scale, tesseract
invocation, normalization, exact command comparison, and the existing 12/13
cursor threshold unchanged. After the fixed grayscale body crop but before
building `foreground_probe`, erase only prepared row zero, which is absolute
crop row y=7. Then build the existing probe, remove columns at 12/13, resize,
and OCR as before. This ordering prevents the frame row from changing the
cursor/glyph count while preserving the existing margin.

Do not add OCR character whitelists, fuzzy replacement, punctuation filtering,
per-command behavior, relaxed closed guards, or binary substitution.

## Tests and gates

Add a self-contained regression for the measured row texture, empty closed
state, exact typed command, malformed geometry, and genuine nonempty closed
refusal. Follow the existing test convention for a small grayscale chat-only
fixture: the measured empty editor crop may be encoded in the test because it
contains only UI texture, with no desktop, chat history or private client state.
Keep original full frames, raw receipts and private client state outside Git.
Parent verification must
re-run all eight retained original full frames through the production crop and
candidate OCR, assert the private image/source hashes, and record raw and
normalized results. A fresh same-scene bright typed full-frame proof is
required before promotion; it must preserve exact command equality while the
bright closed frame remains empty.

Run the focused native helper tests, scoped Ruff/format/compile and diff checks
first, then the full helper file once the candidate is stable. Preserve source
pins, raw check logs and actual exits. Parent must reproduce the private
full-frame proof, then Sol and actual
Opus review the two-file delta before promotion. The accepted lifecycle/native
suite is not repeated for this preprocessing-only change unless a focused
failure shows lifecycle impact.

Before promotion, the sole GUI operator must finish assisted scan #89 and its
save/upload/ACK/reopen chain, then retain fresh original full frames of bright
closed chat and all eight exact staged commands in that scene, cancelling each
without submission. Use the existing bounded diagnostic and ordinary chatEdit
proof where available; this is not a binary substitution for all helper phases.
Parent must verify those original images through the exact production crop,
OCR, normalization and chat guards. A retained 460x37 crop is already cropped
and must enter OCR directly; never crop it again as if it were a full frame.
The initial invalid double-crop experiment is excluded from qualification.

Promotion requires the full helper check, focused parent reproduction, frozen
source pins, Sol and actual Opus READY, and the fresh full-frame evidence. This
helper-only installation needs no daemon restart. Use actual public status and
fresh generations for the next live qualification; no blind unchanged retry.

No daemon, driver, decoder, GUI, runtime, Rust, configuration, service, or
helper lifecycle changes are in scope.
