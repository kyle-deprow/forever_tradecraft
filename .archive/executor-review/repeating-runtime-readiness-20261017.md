# Repeating runtime readiness audit — 2026-10-17

Scope: current source at the supplied main revision `857a019`, the supplied live snapshot
(27 server sweeps, 62,348 rows; owner PID 501046 `PAUSED`, generation 16; user unit
inactive/disabled), and the four curated receipts named below. This was a read-only audit;
no current private configuration or live desktop state was inspected.

## Finding

The four-hour gap is a lifecycle gap, not an absent 15-minute engine. The daemon already
runs its owner turn every second (`src/crowley/session/daemon.py:5769-5772`) and the repeat
controller has the full due-scan pipeline. It adopts an addon-started scan or starts one
when `dueAt` arrives, opening the AH first when required
(`src/crowley/session/daemon.py:5383-5414`). It then verifies stable saved evidence,
upload, Data.lua publication, exact loaded ACK, and returns through `REOPEN`
(`src/crowley/session/daemon.py:5431-5609`).

Nothing currently owns the final always-on lifecycle: the live owner is deliberately
paused/unarmed and the systemd unit that would restart the daemon is disabled. A paused
owner returns before capture or action (`src/crowley/session/daemon.py:4917-4924`), and a
fresh process cannot reconstruct its process-local physical-input evidence
(`src/crowley/session/controller.py:1838-1852`). When the chat worker ends, no independent
process performs the one-time service-owner qualification and `resume`; therefore the
900-second loop never becomes eligible to run.

## Implemented automation and its remaining dependence

| Path | Implemented behavior | Remaining dependency |
|---|---|---|
| Normal repeat | Due detection, scan command/adoption, save/reload, upload/ACK, exact loaded-ACK qualification, and next-cycle reopen are implemented (`daemon.py:5383-5609`). Normal cadence through ACK does not call the model (`docs/REPEATING_SCANS.md:191-202`). | Requires a live armed service owner and an authenticated in-world client. |
| Login recovery | Four one-shot actions are journaled before dispatch and bounded to four attempts (`src/crowley/session/daemon.py:3668-3690`). Restart reconciliation does not replay uncertain menu input (`src/crowley/session/daemon.py:4962-5045`). | Every decision and named visual pre/postcondition uses the pinned Luna adapter. Credential prompts block (`docs/REPEATING_SCANS.md:191-202`); expired Battle.net authentication/launcher Play is outside the four in-client actions. |
| AH reopen | `REOPEN` waits for fresh `ahOpen`, dispatches `open_ah` once, and fails on its deadline (`src/crowley/session/daemon.py:5593-5611`). | Still uses fresh Luna-backed world/AH observations (`src/crowley/session/daemon.py:1761-1860`) and two fresh pointer-anchor measurements, including the post-move refresh (`src/crowley/session/driver.py:4842-4876`). The passive semantic/key route is planned but unimplemented (`docs/HANDOFF.md:118-129`). |
| Closeout | The engine adopts a racing scan, requires empty queues, arms the addon schedule fence, observes a newer same-boot frame, issues one logout, then verifies stable cleanup (`src/crowley/session/daemon.py:5612-5715`). | Logout still requires a Luna-backed named world precondition and character-select postcondition (`src/crowley/session/daemon.py:2096-2102`; `src/crowley/session/driver.py:3927-3948`). |
| Process/service recovery | The user unit restarts a failed daemon after five seconds (`deploy/crowley-session.service:5-15`); the socket and desktop leases exclude a second owner (`src/crowley/session/cli.py:383-424`). | Restart is intentionally unarmed and needs fresh process-local input qualification plus explicit `resume` (`docs/REPEATING_SCANS.md:162-170`). |

The daemon can therefore repeat without chat workers once qualified, but it is not yet a
zero-model routine. The current deterministic-offload plans do not authorize treating
cached coordinates, `ahOpen` alone, or an unknown launcher screen as proof.

## Exact unresolved gates to the service run

1. Restore the already-authorized account through normal Battle.net Play and reach the
   pinned Arthur/realm world. No credential request belongs in the engine.
2. Hand ownership from the manual PID to the systemd service; never overlap owners. Enable
   and start the existing unit, confirm its current display/Xauthority and exact private
   CLI/config bindings, then use only its public socket. The unit is safe while unarmed
   (`docs/REPEATING_SCANS.md:49-84`), but the last live batch showed that missing
   Xauthority prevents capture (`docs/HANDOFF.md:69-77`).
3. Put that service owner in `repeat` mode and complete its native bootstrap/native-100
   handshake. The gate requires the operator's `/crowley agent hold`, `measure`, and
   `resume` at the published boundaries and exactly updates 1..99 plus held/100
   (`docs/REPEATING_SCANS.md:112-148`). No curated receipt proves this for generation 16;
   the retained HUD receipt explicitly says `nativeQualification: false`
   (`.archive/executor-review/native-hud-schema3-parent-verification.json:1-31`).
4. Complete the same service process's physical-input calibration with one real operator
   key and click, then issue `resume` with the returned generation
   (`docs/REPEATING_SCANS.md:86-110,131-138`). The GTK owned-gesture proofs establish the
   executor/cancellation boundary, not a live WoW input gate
   (`.archive/executor-review/native-owned-proofs-r14-parent-verification.json:1-67`).
   The native eight-sample receipt proves the R6 capture path only; it has eight samples,
   not native-100 or input qualification
   (`.archive/executor-review/gnome-telemetry-region-r6-live-eight-parent-verification.json:7-27,72-85`).
5. Observe the service remain in `repeat`, pass one complete scan/ACK/reopen cycle, then
   retain three starts at 900±5 seconds for formal autonomous qualification
   (`docs/REPEATING_SCANS.md:233-238`). Scan 27 already proves 428 observations, 502-second
   completion, a 900-second prior interval, server receipt at 52.084 seconds, and later
   empty queues (`.archive/executor-review/build-70450-twentyseven-upload-parent-verification.json:3-27`).
   Its exact loaded-ACK frame was not retained (`...twentyseven-upload-parent-verification.json:29-30`);
   that limits formal evidence for scan 27, but does not block new collection or require
   historical recovery.

These are technical gates. The user already authorized the qualified repeating service;
no additional user approval is required. Native/input calibration still contains explicit
human evidence by design, and expired authentication still needs the normal operator path.

## Smallest next slice and priority

The smallest route to real progress is operational, not a new scan implementation: make
the existing systemd unit the sole owner, run native-100 and input calibration in that
same process, `resume` it in `repeat`, and leave it enabled. This directly removes the
“worker finished” dependency because `run_forever` and systemd then own the cadence and
restart loop. A tiny deterministic readiness command can follow: poll the public `status`
and `calibration-status` fields, refuse stale generations, and durably report exactly one
of `auth_required`, `native_operator_step`, `input_operator_step`, `ready_to_resume`, or
`running`. It may invoke existing public IPC transitions after their gates, but must never
type the three Agent commands, supply the human key/click, enter credentials, or bypass
fresh calibration. The public command surface and generation checks already exist
(`src/crowley/session/cli.py:53-168,323-363,795-834`).

While authentication is blocked, that readiness command/runbook and the accepted passive
AH semantic implementation can be prepared and reviewed offline. Live ACK evidence,
native-100, physical-input qualification, AH reopening, and the three-cycle service proof
must wait for the authenticated client. Priority after authentication is service-owner
handoff and live gates first; latency attribution and zero-model AH work should not delay
the next real 15-minute scan.

STATUS: NOT READY TO ARM; EXISTING REPEAT ENGINE READY FOR SERVICE-OWNER QUALIFICATION
