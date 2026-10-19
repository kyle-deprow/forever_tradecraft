# Native chat OCR contrast normalization plan

Status: IMPLEMENTED AND INSTALLED after Sol R2 and actual Opus5.5 R2 READY.
Live native100 qualification remains pending; see release parent verification.
The initial experiment is independently reproduced; production candidate and
full helper checks plus source reviews remain mandatory before promotion.

## Objective

Make the fixed active-chat command readback stable across the small grayscale
variation observed in a real `/reload` capture. Keep exact command comparison,
active/inactive editor classification, identity checks, crop geometry, cursor
removal, resize, Tesseract mode, cleanup, and all input guards unchanged.

The proposed operation is one uniform grayscale normalization in
`NativeCalibrationOperator._ocr_file`, after the existing fixed body crop and
before the existing foreground probe:

```python
prepared = image.crop((left, top, left + width, top + height))
prepared = ImageOps.autocontrast(prepared, cutoff=1)
foreground_probe = prepared.point(lambda value: 255 if value > CHAT_OCR_THRESHOLD else 0)
```

The normalization therefore acts on the 400x13 OCR body only. It does not act
on the full 460x37 editor crop, the state-guard rows, or the source desktop
frame. The threshold remains 45, the cursor rule remains >=12 of 13 rows, the
scale remains 3 with bicubic resampling, Tesseract remains `--psm 7`, and
`normalize_ocr` plus exact expected-command comparison remain unchanged.

## Scope and baseline

Future implementation is limited to these two files:

- `tools/native_calibration_operator.py`;
- `tests/test_native_calibration_operator.py`.

Accepted helper/test baselines are
`4db338bdbf328c59be1020370c1570de2354d5f4a1fcc8c3fc5e78e50935021b` /
`c9d22c42c50259a9a6f3b6db694b85731764080f6b9c5c43577711881f30596d`.

No daemon/driver/decoder/diagnostics/runtime/Rust/addon/template/configuration/
service/GUI/lease/lifecycle change is in scope; no installation, restart, or
live input is authorized.

## Actual failure evidence

The retained failed crop is
`/home/dev/.local/state/crowley/native-calibration-operator/native-calibration-measure-deferred-20261019T101004837730Z-3935442-4cd44b6a/chat-f40ec7c2e1d3.png`, SHA256
`b273ce0fa7e38508139851fda14352a9fa81a3a2175f3252492bf3c0c6749f72`.
It is already the production 460x37 crop; it must not be cropped again.
The failure receipt is SHA256 `9b425b2face5ed2cb20f41083069ae5c76ef77138ab2539c3bb3c46b55190005`.

The accepted production path classifies this crop as `active` and returns
`reload` from `_ocr_file`, while the expected command was `/reload`. The
retained gen29 accepted canonical crop returns `/reload` and has the same
active state and the same cursor hot columns x45 and x46 at 13/13 foreground.
The failed and accepted full 460x37 rasters differ at 7,625 pixels, with an
absolute difference sum of 10,069 and maximum grayscale difference 4. The
7,625 count is over the full 460x37 raster, not the 400x13 body.

The accepted source is the gen29 original `cmd08-staged-01.png`; its
production canonical crop `cmd08-staged-01-canonical.png` is SHA256
`c63cdc66293e4de7a50d367fa4bfed4cf273189868c8094130749aaee619507f`.
The failed run did not retain its original 1920x1080 fullframe.

## Reproducible private experiment

The private matrix runner is
`/home/dev/.local/state/crowley/executor-evidence/native-chat-ocr-diagnosis-20261019/matrix_runner.py`, SHA256
`363c38fe3316fb0b8189897c91dcf6b60d99fbe5c5082e7ad3a7c910660d3ec3`.
Run it from the repository with:

```bash
PYTHONPATH=/home/dev/repos/pegasus uv run python \
  /home/dev/.local/state/crowley/executor-evidence/native-chat-ocr-diagnosis-20261019/matrix_runner.py
```

Its retained output `matrix_runner.json` is SHA256
`7ce09d406aaee77b28d988d290e848cf2485676669b29ce4a632d51ad9250d61`.
The gen29 receipt is SHA256 `806c14992dea27eeab2f1445d82f7c2f299cb476c15ed7faafc6d4c484060e4a`;
the earlier `r1.json` report is SHA256
`f6be2bafb059bd25ff37c7b4ee5c3e938bef805305fb09177b535780db6d1cc4`.
All private files are mode 600 under a mode 700 directory.

The runner reads each original 1920x1080 typed frame, applies the production
crop `(30,938,460,37)` exactly once, then runs baseline and candidate OCR.
It separately reads the already-cropped failed `/reload` artifact. It does
not edit source, inject text, use a command whitelist, or fuzzy-match output.

## Matrix result and acceptance cases

The eight gen29 original typed frames are `/crowley agent defer`, `release`,
`recover`, `hold`, `measure`, `resume`, `finalize`, and `/reload`. Baseline
OCR is 8/8 on those accepted frames; the failed crop makes the combined
baseline 8/9. The candidate normalization is exact on all 8/8 accepted
frames and the failed crop, 9/9 combined.

The retained gen29 originals classify as active for all eight typed frames;
the pre frame and all eight post-Escape frames are inactive, and the current
active-empty crop is active. These states come from the production guard, not
OCR. Existing nonempty-active, unknown-black, mixed-chrome, malformed, and
nonempty-closed refusal tests remain required with zero input calls.

A future typed regression must include the sanitized failed texture and exact
`/reload`, while retaining all exact command cases. The private production
proof must run the eight original fullframes through the real crop/OCR seam,
retain the state guard, and record raw/normalized OCR only privately; no raw
screenshot or private path enters Git.

## Bounded original-frame retention

The failed run proves that retaining only the post-crop artifact loses context.
This implementation also adds a helper-only diagnostic seam retaining at most the last four
original 1920x1080 fullframes containing the chat per operation in a private
0700 directory, before `_capture` reuses or overwrites a crop path. Each needs
source SHA256, dimensions, label, and derived-crop/OCR use. Preserve the exact
original PNG bytes before crop-path overwrite; do not re-encode the original.
Test five or more chat captures to prove oldest-original eviction while the
last four remain valid and the current crop is unchanged. It is bounded and
diagnostic-only, cannot refuse cleanup or extend deadlines, and is not public.

Bind refusal diagnostics to the typed buffer that actually failed. Use an
operation-local strictly increasing capture sequence in fullframe and crop
filenames/metadata, so repeated labels cannot overwrite or misassociate them.
Record capture sequence, label/use=`typed_chat_readback`, exact original
fullframe SHA256, derived typed-crop SHA256, and `typed_editor_state` from the
derived460x37 typed crop (never the1920x1080 original, controller state, or a
later screen). Raw and
normalized OCR are each capped at256 Unicode codepoints, with truncation flags.
Artifacts and refusal records are0600 under0700; raw text and private paths
must never enter public RPC/status/journal events or Git reports.

Preserve the existing mismatch Escape attempt and causal OperatorError. Any
typed-state classification or diagnostic persistence is best-effort after the
Escape attempt, using the already retained typed image; injected classification
or write errors cannot mask mismatch, change input order, or skip cleanup.
Test repeated labels, sequence/hash association to the actual failed typed
buffer, exact cap/modes, and write/classification failure preserving Escape,
original refusal and cleanup. The failed gen33 fullframe remains unavailable
and must not be reconstructed or claimed.

## Verification gates

After review, implement the single normalization line and focused tests first.
Run the private matrix runner before freezing the two source hashes. Run the
focused chat/OCR tests, scoped Ruff format/check, Python compilation, and
`git diff --check`. Freeze both hashes and have the parent independently
reproduce the focused tests and private matrix.

Run the full helper test file once after focused checks are green (about 350s),
preserving stdout, exit status, command, source hashes, and private evidence.
Sol and actual Opus review the exact two-file delta; parent reproduction is
required before promotion. No live recovery, native calibration, restart, or
GUI action is part of this OCR gate.

## Risks and limits

Evidence covers one current theme and one failed crop without its original
desktop frame. Autocontrast is supported by nine cases, but future theme
coverage still needs full helper/private production proof; state classification
and exact guards remain unchanged, so unknown/active initial visuals refuse input.

## R1 review closure and measured inactive-body behavior

Sol R1 and actual Opus5.5 R1 both request changes. R2 must prove automatic
`run()` cancellation/input closure after diagnostic errors, exercise retention
write failure, classify the actual derived460x37 active typed crop, and keep
at most four originals even when eviction unlink fails. Evict before admitting
a new original; on eviction failure skip that new retention best-effort and
keep truthful metadata. Preserve interruption propagation during retention.
Record already-computed original hash/dimensions even if copying fails.

Autocontrast can turn darker inactive body texture into OCR text. The original
closed-empty fixture therefore does not retain its old OCR-empty behavior.
This is an explicit limitation: the production initial-editor guard classifies
the raw460x37 crop before input and never uses OCR to prove a closed editor.
Keep that state guard and its no-input refusal tests; name the affected tests
truthfully and assert the measured behavior rather than silently swapping a
fixture. The failed gen33 fullframe remains unavailable.
