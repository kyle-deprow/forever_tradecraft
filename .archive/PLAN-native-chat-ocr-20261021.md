# Preserve exact slash recognition in native chat OCR

## Current objective and authority
User explicitly requires Luna-assisted scans every900seconds while unattended
controller fixes continue; collection takes precedence. Sole GUI owner is
luna_live_recovery. This work is OFFLINE ONLY: no captures, input, services,
config, native/recovery/calibration attempts or interruptions to assisted scans.
Luna implements/Sol reviews; parent owns final tests, deployment and Git.

## Actual evidence
Canonical recover70 refused before Return: command /reload, observed OCR lreload.
Existing native helper source at MAIN289235e: tools/native_calibration_operator.py
_ocr_file preprocesses CHAT_OCR_BOX=(40,7,400,13), autocontrast cutoff1,
removes almost-full-height cursor columns, BICUBICx3, Tesseract psm7. normalize_ocr
only folds case/whitespace. Do not coerce arbitrary OCR letters into slash.
Private source failure directory:
/home/dev/.local/state/crowley/native-calibration-operator/native-calibration-recover-20261020T235235763356Z-3137690-c15bc8e5
read chat-readback-00000002.json and receipt. Actual original fullframe SHA
c02cd057a53323d4870226910587a9388f3a90a5a8495fe123c2c55bbb787069;
derived460x37 crop SHA269634eb9956eec19ab2ff63e19df4798db7c44ed9edd50381e4b57dc06189d6.
Preserve exact original failure bytes and first reproduce current production
OCR result offline. Do not invent root cause from a visual guess alone.

## Ownership and implementation
Work ONLY /home/dev/.cache/crowley/worktrees/native-chat-ocr-20261021.
Own tools/native_calibration_operator.py restricted to _ocr_file image preparation/
OCR configuration and closely necessary fixed OCR constants; no _chat dispatch,
validators/admission/recovery/checkpoint/identity/watchdog changes.
Own tests/test_native_calibration_operator.py restricted to relevant chat OCR/
readback regression cases; may add exact actual chat-only PNG fixtures under
 tests/fixtures/native-chat-ocr/ (no fullframe chat history/account data).
No other edits; no commit/reset/stash/reverting others. No changes in MAIN,
installed runtime, private assisted GUI flows, source session modules, templates,
Rust, profile, addon, house/watchlist or qualification policy.

1. Reproduce old lreload from actual saved crop through actual production method
and actual installed Tesseract with explicit worktree imports. Verify image geometry/
hashes before interpretation. Inspect how cursor removal/interpolation changes
actual slash pixels and find smallest deterministic general recognition correction.
2. Retain strict exact normalized command equality and closed/active editor guard.
Use one supported recognition pipeline, no loop selecting whichever matches a
command, no expected-command hints, /reload exception or letter-to-slash aliases,
no weakened thresholds/ownership or bypassed submit guard. Don't rewrite missing
/ as accepted text. Correct actual image/text recognition rather than acceptance.
3. Actual retained crop must read /reload; all existing empty/closed/active crops,
longer command and sanitized prior-refusal regressions must remain discriminating.
Keep wrong text/prefix/suffix/mixed/unknown editor refusals and no-Return behavior.
Test real production cropping/OCR plus helper _chat readback/guard as appropriate,
not a mocked OCR string that assumes recognition. New current crop regression
must fail on old source. Test actual fixed commands and boundary glyphs affected
by any preprocessing change; do not unnecessarily add a broad OCR framework.
4. No live proof claimed. Do not clear owner64 durable nativeConstruction checkpoint;
IPC does not expose it, missing status field never proves clearance. Native helper
recovery after reviewed promotion will run only when it can coexist with assisted
collection without creating a data gap; parent/GUI owner coordinate separately.

## Verification/freeze
Use MAIN .venv Python with explicit WT/src PYTHONPATH + actual helper loaded from
WT absolute path (tests existing import uses repo root: verify binding). Never
reinstall shared editable environment. Actual Tesseract calls OMP_THREAD_LIMIT=1
as currently verified private environment, no timeout widening. Run all relevant
chat OCR/editor/readback/diagnostic/cleanup cases in the operator module and
necessary fixed command composition cases. Report exact commands/results/counts.
Avoid unrelated full Rust/native119 long suites unless a reachable concern needs
one; scope is preprocessing only and earlier full module gate already119pass.
Scoped Ruff/check+format, py_compile, git diff --check. Keep logs private0600/
dirs0700. Freeze exact owned changed-file hashes + manifest and DONE when complete.
Parent independently runs meaningful regressions, then Sol read-only review/fixloop.
Do not stop at a plan. If robust recognition cannot be achieved in the fence,
report actual reproduced constraint and proposed minimal scope change, not a bypass.
