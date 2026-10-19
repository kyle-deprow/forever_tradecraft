# Fix native helper chat-border OCR false positive

Live control-preflight on the accepted helper refused before input because the
reviewed closed-editor crop (460x37) produces `i` under tesseract --psm 7.
Fresh ordinary telemetry proves chatEdit inactive/unfocused/empty. Retained image
shows the right border at x445..447 and horizontal rules at y4,23,25.

1. First inspect measured retained closed and real typed-command captures from
   the sole GUI owner. Reproduce exact OCR; identify a geometry/preprocessing
   correction that removes decoration while preserving all command glyphs.
   Do not whitelist arbitrary OCR junk or skip closed/readback guards.
2. Change only tools/native_calibration_operator.py and its test module. Use an
   isolated worktree based on parent accepted four-file release. No GUI, addon,
   native/daemon/driver/runtime/Rust/config changes. Preserve parent and other edits.
   No commit/reset/stash/revert. Do not rebuild accepted matcher.
3. Keep production OCR and exact full-command equality. Retained actual image
   regression must prove closed-empty recognition and every available actual
   typed fixed command; a nonempty command remains rejected by the closed guard.
   Include geometry bounds and malformed/refusal coverage relevant to the fix.
   Keep private screenshots out of Git; public tests may use a small documented
   nonprivate derived crop if needed, or recreate border geometry independently
   while parent separately reproduces actual measured images.
4. Worker runs scoped tests and Ruff/diff; parent independently reproduces actual
   retained-frame OCR and focused tests before Sol plus actual Opus delta review.
   Do not rerun accepted 98/native100 fixture suite for a local geometry change
   unless implementation changes lifecycle behavior or focused checks fail.
5. Exact source hashes and passing reviews before parent copies to main, commits,
   pushes and sole GUI retries live preflight/native100/ordinary recovery.
   Physical user gate and three autonomous 900s loops remain subsequent gates.

Acceptance: actual closed crop yields empty with deterministic OCR, actual typed
commands retain exact equality, no guard bypass or guessed coordinates, bounded
small change and focused review. Distinguish real live evidence and synthetic tests.

## R2 live finding: qualify every fixed command

R1 e6cde...340f fixed empty and `/crowley agent recover`, but actual `/reload`
reads `Say {reload`; exact guard refused and escaped before submission. Preserve
private recovery receipt SHA4f5d5d29635098c628baaaee1c7634a0223d669304d78c229f8216db12924787.
Do not retry unchanged OCR. Sole GUI stages and retains ORIGINAL full frames plus
independent exact chatEdit for ALL FIXED_COMMANDS, no submission, and closes each.
R2 must run actual production capture/crop/OCR and exact guard across this entire
measured set, closed empty, and nonempty refusal before review/install/live retry.
Investigate one deterministic measured preprocessing approach; no per-command
fallback, fuzzy replacement or junk whitelist. A measured body-only crop excluding
channel-label decoration is an option only with explicit command-buffer contract
and all affected tests updated; preserve exact actual slash-command text equality.
If that changes `_chat` contract, run full affected helper suite once stable;
otherwise focused tests suffice. No native/Rust/controller/GUI ownership changes.
Parent independently reproduces all full frames; Sol+actualOpus bounded delta.
