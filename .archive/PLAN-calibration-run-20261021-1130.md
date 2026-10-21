# Calibration appointment: 2026-10-21, 11:30 America/Chicago

User requested a calibration run after a completed scan and is available at
11:30 AM Chicago time today: **2026-10-21T16:30:00Z** (CDT, UTC-05).
This is a dedicated calibration window; the preceding no-interruption collection
rule continues until the appointment preparation boundary. Resume collection
after the attempt. Do not promise a human prompt before synthetic readiness.

## Confirmed starting point

At 14:52 UTC, the public controller was PAUSED generation70 with native and input
calibration false. The durable journal omits the `nativeConstruction` key.
Check key membership: an explicit JSON null is malformed, not a cleared checkpoint.
Canonical recovery already succeeded at 10:08 UTC; never repeat recovery from an
old handoff's owner64 checkpoint. Read the actual journal and public state again
before changing controller state. The historical pre-human XI2 timeout remains
unexplained; installed private diagnostics must capture any new failure.

## Ownership and timing

`/root/luna_assisted_scanner` remains the sole GUI owner. Root and reviewers may
read retained evidence but must not capture, input, acquire the desktop lease,
change services, or perform an overlapping calibration. Use the existing pinned
tools, verified game identity, config, templates, and matcher.

1. Continue normal assisted scans until the first completed scan at or after
   **16:20 UTC**. Never interrupt an active sweep. Preserve original SavedVariables,
   upload it, and verify its exact loaded ACK. Leave AH closed after that reload
   while entering the dedicated calibration window; avoid reopening and starting
   another sweep. Verify AH closed and no active sweep before the next timer:
   closing AH cancels the timer; reopening past due can immediately start a scan.
   If a sweep runs past 16:30, finish it first and report the delay.
2. Recheck fresh ordinary game scene/process/focus, held input, private checkpoint,
   public state/generation, and reviewed source pins. Stage the entire reviewed
   helper invocation and cleanup before admission. No initial recovery is needed
   when the journal checkpoint remains absent.
3. Run fresh `control-preflight` using the actual PAUSED generation; require its
   successful public ordinary recovery and checkpoint absence. Then resume using
   the actual PAUSED generation. Require the returned native
   calibration state before `measure-deferred` with that exact generation.
   Historical successful helper durations were 157–161 seconds; these are not a
   guaranteed deadline. No bare shell timeout or signal-based interruption: the
   current helper does not perform canonical recovery on signal interruption.
4. After native success, use public pause with the returned current generation,
   then canonical recovery using pause's returned generation for the checkpoint
   created by that attempt. Recheck the journal: invoke recovery only for an actual
   valid checkpoint, never an absent or malformed one. Verify ordinary restored boot and checkpoint absence
   directly in the journal. Reconcile fresh state/generation before the next gate.
5. **At or after 16:30 UTC**, resume to the actual INPUT_CALIBRATION generation and
   invoke public `input-calibrate`. Poll public calibration readiness. Ask the user
   for the genuine key/click sample only when this actual prompt is ready. Do not
   launch an expiring human observation window early or fabricate human input.
6. On pre-human failure preserve the installed raw XI2 diagnostic artifact and
   exact predicate rejection. Do not blind-retry or request a human sample when
   readiness never occurred. On any failure complete supported ordinary recovery
   when its checkpoint requires it, then restore assisted collection.
7. The first genuine human event intentionally revokes the current generation and
   pauses the Guardian. Await the calibration operation's terminal result; do not
   resume during human observation. Read actual generation, native/input evidence,
   and journal. On successful calibration resume the actual PAUSED generation and
   verify the controller's ARMED/reconciliation/waiting transition before allowing
   unattended collection. Otherwise explicitly restore the authorized assisted
   path with fresh ordinary boot, exact loaded ACK, AH open and released input.
   Qualification still requires three new
   fully autonomous 900-second cycles with upload/ACK timing requirements.

## Scope, verification, and completion

This appointment changes no source, admission rules, config, accounts, prices,
watchlists, saved payloads, or bindings persistently. No purchases/posts/cancels,
general movement, service restart, or independent GUI owner. Restore the temporary
unsaved CTRL-F12 binding before a true user handback. Follow repository
local-game-control and client-contract skills.

Read-only Sol review must verify this runbook against the actual public API and
helper lifecycle before the live native attempt. Resolve concrete review findings
in this plan and the sole owner's staged command sequence. Preserve actual helper
receipts, exact state/generations, checkpoint transitions, original scan/ACK, and
post-attempt AH/schedule state. Appointment completion means a reported actual
calibration outcome and collection restored, not merely that the clock elapsed.
