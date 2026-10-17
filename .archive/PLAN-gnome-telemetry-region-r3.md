# GNOME telemetry-region R3 closure

R2 is frozen, committed as source in c000f1f, default-off, and not accepted or
deployed. Actual Sol and Claude Opus (`claude-opus-5-5`, exit0) source reviews
both require fixes. Read their complete reports:

- `.archive/executor-review/gnome-telemetry-region-sol-source-r2.md`
- `.archive/executor-review/gnome-telemetry-region-opus-r2.txt`
- Original contract: `.archive/PLAN-gnome-telemetry-region.md`

Do not edit R2 source while the parent's host verification is running. Parent
will explicitly release the edit fence when that process finishes. Preserve R2
binary/source receipts and failures. Do not operate the real desktop or change
private profiles/services. Ordinary beta collection runs independently.

## Owned files

Exactly the original telemetry-region source/test/tool fence: config.py,
driver.py, daemon.py under src/crowley/session; process_admission.py only if
essential; deploy/crowley-session.example.toml; the five named tests
test_session_{capture,native,motion_integration,preferences,driver_actions}.py;
the five existing tools/gnome-telemetry-region files. Review/build artifacts may
use gnome-telemetry-region-r3-* and a new private cache with that name. No addon,
model, input_tool, motion, calibration, controller, persistent DB, or unrelated
source edits. README and companion-unit portability work are a separate task;
do not overwrite them. No commit/reset/stash/revert/push.

## Required closure

1. Genuine C telemetry invocation must register locally and reject a remote
   canonical owner before GApplication forwards anything. A competing canonical
   owner must receive no forwarded request, Shell call, or output. The telemetry
   primary must reject foreign command lines while its request is active. Keep
   canonical uniqueness; do not use NON_UNIQUE or a fallback backend.
2. Read exactly one bounded newline ACK across fragmented stream reads, handling
   EINTR, EOF, overlong/trailing bytes and the existing deadline. Test the actual
   compiled producer with a valid fragmented ACK.
3. Preserve stock guardian admission-health semantics in the locked region
   admission block. An unhealthy watchdog must refuse before release/Shell.
4. Telemetry Shell/producer failure must terminate promptly, release/reap owned
   work and the capture lock, and preserve its actual error. Avoid waiting for a
   PNG until the whole deadline after EOF/exit. Do not forget an unconfirmed-live
   owned process; reuse the existing reaper/registry pattern. Preserve original
   request timestamps; record the actual pre-ACK bound separately.
5. Close the real compiled producer -> sealed memfd/admission -> X11Backend ->
   DesktopDriver/PixelDecoder -> default region-enabled SessionDaemon and
   NativeMotionProvider seam on an owned private bus/display with an external
   compositor fixture. Double only external desktop/Shell boundaries. Exercise
   bootstrap/native capture and stock model exclusion on that same opted-in
   daemon. Use a non-default supported canvas origin; do not weaken identity
   geometry to admit an unsupported child origin.
6. Add meaningful focused region regressions for exact owner/start/completion
   schema/identity, malformed or out-of-interval timestamps, digest/size/format
   mismatches, drift, deadlines, revocation after ACK and the locked pre-ACK
   boundary, retirement and registry cleanup. Do not duplicate stock-only tests
   and call them region coverage. Cover actual competing owner and failure EOF.
7. Reject forbidden short delay/file aliases, duplicates and noncanonical integer
   spellings consistently before any capture. Scrub real display/bus credentials
   from parser-only subprocess probes. Preserve strict argv construction.
8. Check in the exact cache-only container invocation and dependency list, require
   the pinned container digest, and record actual installed package versions in
   the manifest (or use pinned snapshots). Preserve all build logs (`tee -a`
   and proper pipeline failures). Build a new genuine R3 binary; do not mutate
   or overwrite R2 cache/evidence. Do not claim bit-identical rebuilds without
   evidence.
9. Implement the bounded paused eight-sample diagnostic in the existing harness
   file, not another CLI/tool. It must read actual paused controller status,
   actual loaded config and verified identity, use the real DesktopDriver region
   method plus strict PixelDecoder, predeclare eight one-second monotonic targets,
   preserve outer start/completion and child timestamps, require same boot and
   strictly increasing fresh sequences, and stop on a missing/NO_CHANGE/late
   sample without hidden retry. Report actual intervals and cleanup. It must not
   arm input, change the profile, simulate calibration gates, or run on the real
   display in this implementation round. Offline-test its validation boundaries.

Defer the fixture-only getattr nit in daemon unless it can be removed without
out-of-fence fixture changes; record it explicitly. The redundant /proc task
check is not group proof: actual getpgid and registered group remain required.

## Verification and completion

Run actual rebuilt producer self-test/self-check, focused new regressions first,
then the affected host batch, scoped Ruff/format/compile/diff checks. The parent
R2 host batch is the relevant broad reference; bubblewrap rejects both new and
protected executable memfds with EACCES, so do not repeat that known unsuitable
namespace or fake version checks. If a real CLI test requires pinning, use the
authentic private binary via an explicit fixture/config boundary and disclose it.
No production DB, real game/display, profile or service actions.

Freeze all owned source hashes, new binary and actual build inputs; map each
accepted finding to actual regression evidence, include R2->R3 delta and exact
results/remaining limitations. Complete the bounded implementation/build/test
outcome rather than stopping at a candidate patch. Parent reproduces tests and
uses the same reviewers before any opt-in live feasibility release.
