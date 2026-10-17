# Repeating-session acceptance

Status: implementation/re-review in progress; native acceptance has not started.
The editable CLI, private profile and user unit are staged; the unit is disabled
and inactive. No physical calibration or new qualifying sweep has occurred.
Contract: [repeating scans](../PLAN-repeating-scans.md).
Host/input facts: [canonical preflight](repeating-preflight.md).
Prior failed cadence attempt: [session pilot](scan-session-pilot.md).

Initial read-only parent baseline on 2026-10-15: deployed database has 8 accepted sweeps,
3,424 observations, and 11,139 captured rows. Companion is active/enabled;
`crowley-session.service` is not installed. Sunshine and fullscreen watcher are
inactive/disabled. No game input was sent during implementation/preflight.

Telemetry-free query baseline: accepted UID
`beta-normal-alliance-1792040351-Arthur-6643`, database sweep 6, 428 queried
observations, median duration 1 second and range 0–2 seconds. Native format-2
query timestamps have integer-second resolution. Sweeps 7 and 8 also have median
1 second over 428 queried observations each.

Pending evidence:

- Completed implementation, parent checks, and Sol final review.
- Sole-Luna operator bootstrap and measured native rendering/performance gate.
- Real non-game human key/click sample, attribution, and queued-action revocation.
  User has agreed to supply the sample when the test window is ready.
- Installed controller/service and selected-model reconnect evidence.
- Three new qualifying sweeps with exact payload, start/finish, coverage/category,
  upload/ack, and cadence evidence.
- Normal logout with stable empty disk queue, pause/restart/resume proof, and
  durable repeat-mode operation.

Do not count old sweeps, synthetic input, asserted calibration values, or isolated
transition tests as new native acceptance evidence.

## Parent verification of initial implementation

Normal suite: 161 passed, 15 database tests skipped (7.35 seconds). Ruff check,
format check (92 files), and whitespace check passed. Unrelated existing pytest
scratch-directory cleanup permission warnings and FastAPI/httpx deprecation were
observed; no deployed data or unrelated scratch directories were changed.

Read-only/fake-backend parent probes found unresolved production-path defects:

- An expected reload's temporary loading-screen decode error enters `BLOCKED`.
- Supplying numeric calibration assertions and source-ID sets without live
  measurement or a trace can reach `ARMED`.
- Driver takeover revocation leaves controller and journal state `SCANNING`.
- Actual generated Data.lua keys are `ackedScans`, `generatedAt`, `scanPlan`,
  `shoppingLists`; the new parser rejects that file as malformed.
- Parsing the preserved real XI2 preflight trace returns no sources or events.

These are diagnostic findings on the initial implementation, not native acceptance.
Final Sol review and a complete fix round are pending. No game input was sent.

## Correction-round checkpoints

The first final Sol review returned MAJOR ISSUES; the consolidated correction
contract is [REVIEW-repeating-scans-1.md](../REVIEW-repeating-scans-1.md).
Implementation is split between the lead engine worker and native boundary owner.
The native owner's first 8 focused tests and owned lint/format checks passed in
parent reproduction. A full captured raw/delivered key pair still caused its
guardian to revoke on the delivered record (device 3 versus device 5 for source
5); this and the other production native gaps were sent back together.

Parent's first full integration check after that split: 169 passed, 15 skipped,
1 failed. Targeted reproduction fails the three-cycle daemon/socket test with
`deadline expired in REOPEN` after UID `uid-1`; injected fake clock handling is
being corrected. Do not claim the revised lifecycle suite is passing until the
parent reproduces a stable complete tree. No native input or deployment occurred.


Next checkpoints: parent reproduced the corrected targeted engine/evidence suite
(3 passed) and revised native focused suite (16 passed), with owned native Ruff,
format and whitespace checks passing. Engine component review still returned
MAJOR ISSUES; see REVIEW-repeating-scans-engine-2.md. Lead is fixing those concrete
issues and wiring actual native providers; an independent Luna worker is adding
production regression tests. A separate Sol worker reviews the stable native
boundary. Whole-tree final checks and both live gates remain pending; no game
input, service installation, or new native sweep occurred.

Parent reproduced the independent engine regressions: 19 passed. After native
corrections, parent also reproduced all 18 independent native regressions (14.67
seconds). These are fake-backend regression results, not physical input or game
acceptance. Additional model-cancellation and CLI-supervision tests, component
re-review, whole-tree checks, actual production provider wiring, and the live
gates remain pending. The native review findings are recorded in
[REVIEW-repeating-scans-native-1.md](../REVIEW-repeating-scans-native-1.md).

Stable integrated milestone: parent reproduced 221 passed and 15 database tests
skipped (31.08 seconds), Ruff check passed, all 102 files passed format check,
and `git diff --check` passed. Parent also reproduced all 34 focused native
tests after the readiness-handoff changes and all 21 independent engine
regressions, including model process-group cancellation and actual CLI socket
supervision. Both native readiness and integrated engine Sol reviews are still
in progress; no physical input gate, service installation, or new native sweep
has occurred.

Native readiness re-review returned MAJOR ISSUES and explicitly withheld the
human sample. The full correction contract is
[REVIEW-repeating-scans-native-2.md](../REVIEW-repeating-scans-native-2.md).
It found streaming final-release buffering, incomplete human-release collection,
window ancestry parsing, observer-liveness and typing/cancellation/release races,
plus unsupported CLI gate duration/readiness, construction baseline, anchor
provenance, and evidence invalidation. The native owner is fixing the complete
native batch; the integrated review is still running. Automated passes above
remain valid check results, not live readiness. No game input or installation
was performed.

Integrated engine review also returned MAJOR ISSUES; see
[REVIEW-repeating-scans-engine-3.md](../REVIEW-repeating-scans-engine-3.md).
Lead now owns the complete engine correction batch while native owner fixes its
complete batch and the independent regression owner adds public IPC/streaming
checks. Installation, promised human sample, and native sweeps remain pending.

Next native checkpoint: owner reported full native correction complete; parent
reproduced 38 focused native tests passing (12.24 seconds) and owned Ruff check.
This includes the expanded independent idle-pipe, observer-exit, ancestry, and
multi-character input cases. Independent engine owner reports 23 tests passing;
parent's concurrent combined run passed 44 cases with one obsolete restart
assertion, then parent reproduced the corrected restart/stale-generation case.
Native round-3 review is underway; lead is still completing engine corrections.

Native round-3 review again returned MAJOR ISSUES; see
[REVIEW-repeating-scans-native-3.md](../REVIEW-repeating-scans-native-3.md).
Native owner is correcting the complete batch. Parent reproduced the expanded
independent native suite during fixes: 28 passed, two failed (tamper detection
and unexpected modifiers). Its begin-to-dispatch revocation barrier now passes.
The plan now clarifies lazy control measurement, actual preconstruction
bootstrap signalling, and lead ownership of the selected Luna semantic visual
producer for bounded pending UI transitions. Deterministic waiting remains.
No physical calibration, installation, or new scan has occurred.

After continuation, parent verified the saved integrated tree with actual clean
process exit: 235 passed, 15 database tests skipped (40.04 seconds); Ruff check
passed and all 105 files passed format check. Prior focused native reproduction
was 46 passed (12.62 seconds). The interrupted lead's final changes retain the
shared capture through native measurement, clean intermediates, preserve the
final evidence capture, and explicitly close drivers/watchdogs in owned tests.
An engine finisher and independent native reviewer are auditing this checkpoint.
These remain automated results; human calibration, installation, reconnect and
three new native sweeps have not started.

Inert deployment preparation is now installed: the `crowley-session` executable
runs, private profile is mode0600 and parent-validated against exact plan/paths/
deadlines, runtime directory is mode0700, and the user unit is staged. Parent
verified `inactive` and `disabled`; no daemon or calibration was started.

Native round4 returned MAJOR ISSUES; the correction contract is
[REVIEW-repeating-scans-native-4.md](../REVIEW-repeating-scans-native-4.md).
A real harmless subprocess exposed the preexec admission deadlock that fake
Popen tests missed. Other blockers concern mandatory seals, baseline-before-
bootstrap ordering, genuinely admissible calibration tickets, expected details/
modifiers, empty watchdog holds, and one-use capture-bound anchors. Fresh
workers split dispatch/watchdog from calibration/evidence under exact file
ownership; no GUI or service activation is authorized by automated passes.

Fresh bounded corrections: parent reproduced six dispatch checks, including real
harmless process execution/cancellation and stale-epoch rejection, with actual
clean exit. Parent also reproduced 20 calibration tests (5.16 seconds), including
strict seals, baseline ordering, and certified managed-frame ancestry; owned
Ruff/format checks passed. Dispatch is being connected to the certified event
target set, and independent regression fixtures are being updated to complete
mandatory proof. The runtime integration still requires the real socket gate/
pause/resume path rather than direct controller calibration calls. No physical
input or controller activation occurred.

Final strict-regression checkpoint: parent reproduced all 55 independent engine
and native cases (17.77 seconds), all eight updated dispatch cases (0.17 seconds)
including a real guardian-backed current-generation command, and the 20
calibration cases. The pinned Codex executable also works with the actual
systemd user-manager PATH. Native round5 review is underway on stable source;
lead is completing the socket-driven calibration/pause/resume/three-cycle test
and final fixture integration. The staged service is still disabled/inactive.

Native round5 again returned MAJOR ISSUES; see
[REVIEW-repeating-scans-native-5.md](../REVIEW-repeating-scans-native-5.md).
A real old-calibration-ticket race executed a harmless process after revoke;
capability-free synthetic/setup focus, planned rather than current watchdog
holds, missing retained anchor path, hard-zero modifier assumptions, unproven
forwarded motion, dropped termination ownership, and prompt/status ordering
remain in the complete native correction batch. Two owners are fixing dispatch
and calibration. Unknown source7 motion must remain closed unless actually
correlated; no broad whitelist is authorized.

Parent reproduced the revised runtime module: two passed (30.25 seconds), using
real IPC, the 101-frame runner, input workflow, takeover pause, explicit resume,
and three simulated cycles with fake hardware and fake Luna. It is regression
evidence, not native acceptance or clearance for the known native blockers.

### Continuation verification and engine round 4

Parent reproduced the completed calibration owner's tests: `tests/test_session_native.py`
passed 24 tests in 5.28 seconds (exit 0). The required production keyboard-profile
hooks and consumption were then completed by the dispatch owner. Parent reproduced
the combined dispatch/calibration suite: 40 passed in 5.04 seconds, exit 0. A follow-up
run promoted unhandled-thread and unraisable exceptions to errors and passed all
40 in 5.02 seconds; warnings were multiprocessing fork deprecations and unrelated
pre-existing pytest temporary-directory cleanup failures. Controller/evidence
and daemon fixes follow `../REVIEW-repeating-scans-engine-4.md` under the narrower
ownership recorded in the plan. Parent then reproduced the strict peak-field
native/dispatch suite: 43 passed in 5.35 seconds with thread/unraisable warnings
promoted to errors, exit 0. Controller/evidence/transition checks passed 21 tests
in 0.89 seconds, exit 0. Explicit-PAUSED process-restart evidence reuse remains
flagged for independent review. These checks establish code behavior only.
The installed user unit remains inactive and disabled; no controller daemon was
found. No new game input, physical calibration, or live qualifying sweeps occurred
during this continuation check.

The read-only database baseline remains eight sweeps (latest start 07:36:05 UTC,
finish 07:44:05 UTC). API health is OK and the companion is active. New acceptance
must use new UIDs rather than these historical sweeps.

Parent subsequently reproduced 56 independent regressions in 18.97 seconds with
thread/unraisable warnings as errors, exit 0. A later restart correction requires
both fresh gates and advances every existing journal's generation on new-owner
construction; its focused tests passed 23 in 0.95 seconds, exit 0. Runtime/addon
tests passed 89 in 49.37 seconds with the same strict warning settings, exit 0.

[Native round 6](../REVIEW-repeating-scans-native-6.md) is MAJOR ISSUES despite
75 scoped tests passing. Exact-host parser/attribution, release, command admission,
retained-pixel metrics, readiness/deadline and reconnect defects require correction.
One native owner owns the full batch; the daemon owner coordinates capture-time
provider changes. Controller/evidence review runs independently on stable files.
No physical input sample or service activation is cleared by these test results.

Parent database verification: all 15 server tests passed in 7.88 seconds, exit 0,
with thread/unraisable warnings as errors. Tests used a new TimescaleDB2.17.2-pg16
container, tmpfs storage, a random loopback-only port and verified crowley_test
database/user; the exact owned container was removed afterward. Initial setup
attempts stopped at a mount-metadata assertion and then a temporary-init-server
readiness race; the final check requires the main TCP server and verified SQL
identity. Deployed database schema/data were never used by the tests.

Subsequent verification: the parent's combined native/runtime/addon run had 132
passes and one runtime input-retention failure; all 44 native tests passed with
all three strict warning filters active. Independent engine regressions passed
25 tests in 5.33 seconds, exit 0. The final controller batch passed 30 owned tests
but Sol's verdict remains MAJOR ISSUES; see
[unified engine round 6](../REVIEW-repeating-scans-engine-6.md). A fresh single owner
now owns the shared controller/daemon intent/recovery/qualification/archive/build
contract; the former split owners are completed. [Native round 7](../REVIEW-repeating-scans-native-7.md)
remains a separate full correction batch. Auxiliary CLI/model/addon/deploy review
runs separately on stable files. No live activation is cleared.

### Native measurement method and current correction batch

The parent reproduced the completed native round 7 implementation: 81 tests
passed in 19.17 seconds, exit 0, across dispatch, native calibration and independent
native regressions, with thread/unraisable/fork warnings promoted to errors.
Those results precede the subsequent measurement and session-fence changes.
Main engine, native measurement and auxiliary addon/CLI changes are currently
under implementation in disjoint scopes and require combined verification and
independent Sol review.

The [memory measurement clarification](../PLAN-native-memory-measurement.md)
replaces unprovable Lua peak claims with two controlled, reset kernel high-water
windows. On the verified owned game process, Luna archived historical accounting
durably before one authorized `clear_refs=5` capability check. The parent inspected
both private JSONL records and verified the successful two-byte write, unchanged
process identity and restrictive permissions. Historical VmHWM was 4,509,608 KiB;
post-reset VmHWM was 3,018,112 KiB, with RSS 3,016,416 KiB. This establishes host
capability only; construction and update-window performance remain unmeasured.
Lua heap samples are explicitly optional net diagnostics, not peak evidence.

The staged controller remains inactive and disabled. No game input, human
calibration sample or new live scan has occurred during this correction batch.

After the measurement refactor, the parent reproduced the stable auxiliary addon
suite: 94 passed in 16.18 seconds, exit 0, with all three strict warning filters.
The parent's owned native/dispatch suite passed 50 tests in 9.31 seconds, exit 0,
under the same filters. Independent regressions are being updated for the new
complete telemetry and memory evidence schema. Sol auxiliary review and final
controller integration remain pending. Parent inspection identified a fence-phase
integration mismatch and a process-directory pinning defect for review; these
passing suites do not clear live operation.

The parent subsequently reproduced 32 engine/runtime tests in 101.30 seconds,
exit 0, and the complete pre-correction suite: 296 passed, 15 database tests
skipped, 17 warnings in 152.78 seconds, exit 0, with all three strict warning
filters. Database tests have the separate disposable-container result above.
Repository Ruff check passed; format check reported 116 files already formatted;
tracked diff whitespace check passed. Sol auxiliary review still returned
MAJOR ISSUES: see [auxiliary round 2](../REVIEW-repeating-scans-auxiliary-2.md).
The passing suite did not catch the fence-frame integration failure, altered
canonical plan, started tool-event parser gap, or nonfinite heap samples.
Luna is correcting that full batch; native and engine reviews continue read-only.

Auxiliary round 2 corrections passed the parent's full addon check: 100 passed
in 15.41 seconds, exit 0, with the strict warning filters. Sol re-review is pending.
The new exact-plan validation exposes a legacy main-owned fixture at
tests/test_session.py:355; its synthetic 1..428 list must become the real canonical
catalog, without weakening validation. Native Sol review returned MAJOR ISSUES;
the complete [round 8 batch](../REVIEW-repeating-scans-native-8.md) covers process
directory pinning, actual durable pre-reset history, exact phase/ordinal/resume
proof, failure cleanup and actual observer executable readiness. Native fixes
are underway; the main engine review also includes its live callback/provider
portion. No live operation is cleared.

Native round 8 corrections passed the parent's owned suite: 56 passed in 9.77
seconds, exit 0, with the strict filters; Sol re-review remains pending. Main
engine review returned MAJOR ISSUES and its consolidated
[round 7 correction](../REVIEW-repeating-scans-engine-7.md) is underway. Auxiliary
re-review identified exact canonical JSON byte binding and pinned CLI lifecycle
format gaps; [round 3](../REVIEW-repeating-scans-auxiliary-3.md) corrects these and
is awaiting Sol re-review. Full current integration is not yet verified. The
repo skills now also require exact staged observations, final resume proof,
fresh-owner archive recovery at every write boundary, and executable readiness
rather than a live wrapper thread. Both skills passed quick_validate.

The parent's final addon check passed 102 tests in 16.33 seconds, exit 0. Sol
confirmed the addon/plan/fence/heap/chat/deployment corrections; the remaining
parser format defect is addressed in auxiliary round 4. The parent independently
read the 0600 real pinned CLI trace at
`/tmp/crowley-model-aux4-direct-events.jsonl`, inspected event/item/usage key
shapes and successfully parsed the complete stream through LunaAdapter._parse.
It includes the exact diagnostic and five usage fields. This tools-disabled
neutral CLI protocol smoke dispatched no GUI or recovery action and is not game
acceptance. Sol final parser re-review is pending.

Native re-review found real-Agent counter/cadence and resume-prompt ordering
mismatches hidden by invented fixtures, plus missing failure tests and unproven
restoration. The complete [native round 9](../REVIEW-repeating-scans-native-9.md)
correction now requires a runner fixture using real Agent publication bytes and
production decoding. Engine round 7 continues with the corresponding live status
interfaces and crash-safe outcome/restart work. Repeating operation remains off.

Auxiliary final Sol verdict: READY with no findings. It exercised 179 malformed
answer cases and 62 lifecycle/failure/tool/order/usage negatives, plus the real
pinned CLI trace; the parent independently reproduced 25 malformed structured
answers and the actual trace. The final parser hash and review are recorded in
auxiliary round 4. The parent's native9 suite passed 57 tests in 19.85 seconds,
exit 0, but inspection found required runner-level negative/failure/retry tests
still absent. The native owner is completing that explicit test matrix before
Sol re-review; this is not live clearance. Main engine work remains active.

The parent reproduced native9's expanded 71-test suite in 71.44 seconds, then
the complete pre-correction snapshot: 332 passed, 15 database tests skipped,
17 warnings in 295.84 seconds, exit 0, with all strict filters. Ruff check,
format (122 files) and tracked whitespace checks passed. Sol still found the
concrete gaps in native round10 and engine round8; those batches remain open.

Manual setup is now real desktop evidence. Luna activated the existing client,
observed WOW51900319, attempted one normal reconnect, reached WOW51900308 and
blank login fields, then normally quit the exact game process. After verifying
zero clients, one authenticated Battle.net Play triggered automatic patching to
1.60.1.70425. The new sole client PID1413811/startticks25800394 entered Arthur
in Ironforge (24,72), Crowley disabled through normal AddOns UI, Auctionator/Data
still enabled and AH closed. No movement, trading, scans or addon bootstrap.
Private evidence includes native-preflight/manual-world-addons-confirm-20261016T024152Z.png
and manual-arthur-final-scene-20261016T024232Z.png under the Crowley state directory.
The [build refresh](../PLAN-client-build-70425.md) is necessary before calibrated
addon load. The session controller remains disabled/inactive. Current host memory
readings show about36.6GiB available and zero pressure; the persistent notification
alone does not establish a current shortage. Worker messaging capabilities were
also corrected: workers use actual task IDs when parent agent-name tools are absent.

The parent independently reproduced the refreshed addon/session/evidence suites:
130 passed, 16 known unrelated protected temporary-directory cleanup warnings,
20.39 seconds, exit0 with the three strict warning filters. This includes actual
Agent bytes decoded through the production decoder for unsupported runtime-client
blocked states. The runtime guard's final Sol re-review remains pending.
Native round11 and engine round8 remain open; controller inactive/disabled,
companion active. No new live calibration or qualifying scan is claimed.
Peer worker messaging is rejected by the app-server; the recovery owner now
publishes its exact API in CONTRACT-session-recovery.md for the daemon consumer.

Build70425 final Sol re-review is READY with no findings (addon107, focused4).
The parent rebuilt/recreated only the API server using --no-deps and the existing
compose env-file; health ok and authenticated scan-plan exactly matches source.
Companion normal restart published matching Data.lua; private0600 session profile
was atomically replaced/fsynced and validated through production load_config.
Unit restaged/reloaded, controller inactive/disabled. Source/API/Data/profile use
plan25b596810724d79e702fc4e6bd9ff5fb6d1238f2254b066d00f95625f1c88e56.
Data ack list remains empty, companion retains8historical UIDs, and read-only
production SQL independently confirmed8sweeps/3424observations/11139rows unchanged.
No game input, calibration or scan happened in this deployment.
Parent transition check34passed/16knownwarnings72.06s; first-pending-write proof
remains reopened because the fixture did not recreate the public controller from
disk alone. Native11 worker80passes now undergoing independent re-review.

The parent reproduced native11 owned tests:80passed,16knownwarnings,144.09s,
exit0 under all3strict filters. Sol re-review remains in progress. A concurrent
global Ruff pass found only the daemon worker's actively edited runtime fixture
import/format changes; final static checks must be repeated after that file freezes.

Native final Sol verdict READY, no findings after final test-only correction.
Parent independently reproduced corrected post-reset branch1passed13.60s;
Sol1passed13.48s. The six native files are cleared; main daemon/controller
integration remains separately open and no live performance result is claimed.
Sole Luna operator assigned a bounded readiness refresh of the existing client,
with Crowley disabled/AH closed and no scans, movement, reload or keepalive.

The parent's final frozen recovery/independent suites passed116tests in107.68s,
16knownwarnings, exit0 with all3strict filters. This includes genuine public
fresh-controller disk-only qualification retry after first-marker failure,
the updated strict-evidence fixture, and33independent native regressions.
Consolidated Sol engine review has begun with frozen controller/journal; it must
wait for daemon/runtime freeze before reviewing that consumer and final verdict.
Luna readiness refresh returned Arthur from character select to Ironforge,
same sole PID1413811/start25800394, Crowley disabled/AH closed. Parent inspected
the private readiness-addon-state-20261016T0338Z.png confirming the addon state.

Interim Sol producer review: NEEDS WORK despite60strict passes. Confirmed live
memory mutation after first archive-marker failure can be persisted by normal
block/error handling, destroying the disk-only retry path. Read-only restart
qualification can also return to input phases without fresh gates. The whole
correction is in engine8's consolidated producer section and under Luna.
Menu proof contract corrected: menus have no Agent boot; actual fresh verified
named visual facts must resolve the exact existing intent before new input.

Daemon/docs now frozen for Sol consumer review. Runtime test ownership was
explicitly split to fresh Luna, plus one precisely authorized driver decode
clock argument using the existing injected clock at original observation time.
Post-decode timestamp rebinding was rejected/removed. Runtime real-Agent
operator fixture and negative matrix remain incomplete; global stdlib clock
patches were removed to preserve watchdog/socket timing. No live gate started.

Sol frozen consumer review found4must-fixes: pending UID incorrectly made idle
scanner busy; unresolved no-Agent logout could relog; ACK could complete then
skip full qualification; journal retry error could write BLOCKED over retry.
Daemon owner applied the complete batch and refroze source/docs. Ruff/format/
compile/diff pass, corrupt telemetry regression passes; strict loaded-ack
fixture now needs full saved evidence and is assigned to its existing owner.
Fresh runtime owner tests actual consumer cases and real native operator waits.
Sol also found positive scan restart compared a newly created Finish UID to
the pre-dispatch empty/old UID; active producer owner is correcting this in
the same consolidated batch. No controller arm or new live scan is claimed.

Final pre-live verification in progress: parent independently reproduced96
engine/independent tests (110.43s) before the final narrow dispatch/boot fixes.
Sol found actual daemon dispatch overwrote the SCAN attempt, empty-scan
rejection required nonexistent format2proof, and RECONCILE observe_frame
blocked expected save/ack/enter-world boot transitions. Luna corrected all3
in controller/transitions with durable restartReferenceBoot; focused27+runtime
neighbors2passed. All engine/runtime source is now frozen for final Sol review.
Runtime12tests (real Agent/operator negatives included) passed Sol78.23s.
Parent concurrent runtime run collided with the shared test lease;11failures
were lease contention, while focusednative5 passed. Final full verification now
uses a private test desktop lease; no production/game lock was changed.

Parent current disposable DB check:15passed/17knownwarnings8.44s using exact
crowley_test database/user on loopback33308 in owned tmpfs container
crowley-final-test-89b06e77. Container removed after exit0; production untouched.
Current Ruff check, format127files, tracked diff check and both skill validators
pass. Parent full strict suite is running with DB tests separately proven.
The native exact-firstresume timing-window correction is under final narrow
Sol review; the parent reproduced5focused native cases. Live gates/scans remain
unstarted, controller inactive/disabled, Crowley disabled.

Parent broad strict snapshot completed:399passed/15DBskipped/17warnings in
393.94s, exit0, with isolated private test lease. The15DBtests were separately
proven on the removed disposable container. This snapshot predates the final
pre-effect B0/pause/first-Agent, unusedmetadata-kind and modal-none correction;
it is not a claim that that remaining batch is verified. Native final narrow
Sol review is READY with exact source hashes recorded in native11.


Final integration snapshot: parent strict suite finished400passed/15DBskipped
with one failure in the restart-reconciliation fixture (373.61s). Independent
Sol inspection identified the fixture missing canonical pre-effect
`restartReferenceBoot`; production correctly refused to infer it from later
frame state. Luna is correcting only that fixture. The separately proven15DB
tests remain valid. Parent independently reproduced9qualification/recovered-ack
tests after the final guardian correction (3.83s); Ruff and format127files pass.
That correction restores normal live calibration/re-arm on explicit resume
before a repaired qualification can reach REOPEN. Sol final verdict pending.
Controller still STOPPED/generation0, service inactive, companion active; no
live calibration, new sweep, physical sample, or recurring enablement claimed.

2026-10-16 04:42UTC: final engine Sol verdict READY, no findings. Native and
auxiliary scoped verdicts remain READY. The corrected restart fixture exact
test passed independent Sol; Luna transition/regression84pass. Production
source hashes are frozen in engine8. Parent full strict suite is running.
The sole Luna operator is cleared to start the service unarmed and perform
real native calibration, then owned GTK synthetic readiness. No physical
sample, new sweep or recurring enablement has yet been established.

Parent final frozen full suite: **402passed/15DBskipped/17knownwarnings,
389.41s, exit0**, all three strict warning filters, private desktop lease.
The15DBtests separately passed on disposable TimescaleDB. No test process or
fixture load remains during actual native performance measurements.
Luna fresh scene proof was inspected by parent: Arthur at Ironforge24,72,
AHclosed/noAgent; screenshot mtime04:45UTC (private filename carries older
time suffix). Service started manually and remains disabled for recurrence.
Parent socket independently confirms validation mode NATIVE_CALIBRATION,
generation1, unarmed/nativefalse/inputfalse, no boot/sequence, idle handshake.
Luna is cleared for native-bootstrap/native-calibrate now. Physical sample,
new sweeps and enabled repeat mode remain unproven.

Live bootstrap reopened a concrete X11 parsing contract: actual
`xwininfo -id game -tree` identifies queried root in its header, then lists
only children as indented structural rows. Common parser ignored the header
and reported first child as root; verified game identity was therefore rejected
before any native baseline/reset. Parent confirmed actual class/title/PID,
1928x1092 outer and direct1920x1080 child all match. No profile relaxation,
addon enable or resource measurement occurred. Luna owns bounded correction
in driver/calibration/native tests under PLAN-live-x11-tree.md; prior CPU/
memory/guardian logic stays frozen. Native verdict reopens only for this
actual contract correction. Controller remains unarmed validation generation1.

Live X11 correction frozen for narrow Sol review. Parent inspected actual
header/row parsing and GTK caller, independently reproduced9focused tests
(0.12s), and executed READONLY production X11Backend.resolve_identity against
the private profile successfully: PID1413811, queried0x1800001, child0x1600011,
outer(0,0,1928,1092), child(0,0,1920,1080), matching foreground. Fingerprint
`c9da18940ecd9cd59a03fbb7a1993baa5d58b8679fc1030c3da5022dd0e2db94`.
Luna native68+independentnative33 passed with strict3/private lease. Parent
global Ruff/format128/compile/diff pass. First incomplete patch was corrected
for real quoted-name rows before review; no live clearance was issued for it.
No kernel baseline/reset, Agent enable, physical sample or scan yet.

Final narrow X11 correction Sol verdict **READY**, no findings. Independent
focused9tests passed0.13s under strict3/private lease; broader native
ancestry selection9pass. Frozen driver hash7ba522286caf6aaa8654c66a4ccb5fb3899e268b0d0b60f785679beefc07bae7,
calibration53909a8cf02bac7d6fb582a02d388f41e0ad6e12a0ca4dc057cc65a230704962,
nativeTestc03647803c00bb7a91cf7afd2235259c43eab612d9b595a8663eb0520097ac9e.
Parent real read-only identity resolution succeeded before clearance. Sole
Luna operator cleared to restart unarmed daemon, use fresh generations and
retry native calibration from fresh no-Agent/world/AHclosed boundary. No
new live measurement or physical sample is claimed by this review verdict.

After reviewed X11 fix, sole Luna operator restarted daemon (durable PAUSED
generation2), explicitly resumed to NATIVE_CALIBRATION generation3. Actual
native-bootstrap succeeded with surface absent and verified live PID/start/
window/fingerprint, private preconstruction capture. Native-calibrate then
errored before baseline: `native reset5 memory meter is not configured`.
Default SessionDaemon constructs DesktopDriver with meter=None; test fixtures
provided one manually. No reset5, addon enable or scan occurred. Runtime
calibrationOperation correctly says error but nativeHandshake remained running.
Luna owns the bounded production meter wiring/lifecycle/default-entrypoint
regression and truthful pre-baseline error status under the appended section
of PLAN-native-memory-measurement.md. Driver/parser/controller remain frozen;
GUI operator holds unarmed no-Agent boundary until reviewed correction.

Production meter correction is frozen for narrow Sol review. Daemon now
creates the identity-bound Linux reset5 meter at native-operation start and
closes its owned handle in finally, clearing the driver reference for retry;
injected test meters retain caller ownership. Native evidence retains Windows
window executable and independently binds consistent Linux measurement paths
through PID/start/fingerprint. Early error handshake is now truthful.
Parent inspected changes, reproduced28strict tests in34.87s (default-meter
failure/retry, actual Agent/reset5 child proof using distinct executable
channels, plus26restart regressions). Global Ruff/format128/diff pass. Luna
fullnative68/runtime13/independentnative33/session26+20 pass. No new game
interaction or kernel reset occurred; live service still has earlier code until
reviewed restart. Remaining review is narrow to this four-file correction.

Final default-meter correction Sol verdict **READY**, no findings. Focused
3tests passed76.55s, including injected-meter ownership lifecycle; source
review verifies default lazy creation/cleanup, truthful early errors and
distinct Windows/Linux sealed proof. Parent28strict tests passed34.87s.
Frozen daemon0080ea71222d0d99a223ee73476a8380cf9e4686f2cdee8e0abcd77b07ae2d4c,
calibrationf0b03ea0c7636b73001e4fc71298b685105205b0b19c78e6001a9b89e7dd58ee,
runtimeTest4321c4da561193ef79841f44257602163906f3824f6f83c0f5b603542a892cc6,
nativeTeste6cea1ea716a5b7bb8676877f90f19ce1cea59dcbd31729d9ca34c80c1799c69.
Tests ended before actual resource measurement. Sole Luna cleared for fresh
scene/restart/explicitresume and chained bootstrap/calibrate (10s freshness),
actual hold/100updates/resume and GTK readiness. Physical sample/new sweeps/
recurrence remain unproven; no kernel baseline had yet been taken.

Live corrected-meter attempt at generation5 reached actual bootstrapReady;
parent socket independently observed archiveReceipts1 and running operation.
First real construction reset baseline was therefore taken only after its
durable archive. No qualifying native proof resulted: constructor fresh frame
did not arrive within the provider bound; operation error and durable
restoration_required/restoredfalse were exposed, archive receipt retained.
No native pass/physical proof/new sweep is claimed. Sole Luna is diagnosing
actual addon/UI/capture state and preparing the normal operator route before
any new reset; distinguish late loading from malformed/absent surface.

Second actual generation5 attempt used staged RequiresReload UI; bootstrapReady
was reached, historical construction receipt77e64f... retained (baselineHwm
3815383040). Luna clicked the verified Reload UI after readiness; normal reload
completed. Native constructor then failed with missing unique screenshot
`/tmp/crowley-capture-i_5n4a23/desktop.png`. Operation reports error and
restoration_required/restoredfalse, no native pass. No further reset allowed
until actual screenshot exit/stdout/stderr/file-creation behavior and Agent
surface are diagnosed with bounded capture-only probes. Do not infer screenshot
completion from exit0 or hide this through a second capture backend.

USER-REQUESTED PAUSE: all game input stopped, sole GUI worker interrupted.
Parent exact CLI pause --generation5 succeeded ->PAUSED/generation6/streak0;
session service stopped and remains disabled. Companion/API left running.
Latest world observation ArthurIronforge24,72/AHclosed, HUD absent after
normal Crowley enable/reload; worker tried Esc and Alt+Z without restoring it.
No further game input/cleanup after pause. Capture-only probes4serial+2spaced
exit0/empty stdout+stderr/fileimmediate, ~0.95–1.01s each. Operator screenshot
may have overlapped active daemon capture; cause ofmissingPNG unproven.
No native pass, physical proof, new qualifying sweep or enabled recurrence.
