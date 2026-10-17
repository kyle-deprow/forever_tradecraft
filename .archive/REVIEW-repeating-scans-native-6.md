# Native review, round 6

Sol verdict: MAJOR ISSUES. All 75 scoped tests passed, but exact-host replay and
production repros establish the following blockers. No physical GTK sample or
game input is cleared.

## Must fix

1. XI2 device semantics and forwarded motion do not match the recorded host.
   Raw events print master(source); delivered events print source(source).
   The preflight Motion is device7(7), over Battle.net; button events are raw2(4)
   and delivered4(4). Calibration/runtime wrongly require delivered Motion's
   first field to be master2. The trace has no source4 Motion, so it does not
   prove any source7 echo. Guardian currently accepts a lone source7 Motion at
   old sealed coordinates, ignoring target/timestamps/current source4 event.
   Repro: unpaired_runtime_source7_admitted=True at runtime timestamp5000 with
   calibration timestamps9/11. Require current bounded-operation pairing by
   exact class/source/master, target, coordinates, modifiers and time; unknown
   motion remains closed. Never allowlist source7. Correct unsafe owned test.
2. XI2StreamParser emits Enter/Leave after device/time, before later windows and
   modifiers. Exact-trace replay yields missing child/modifiers and revokes a
   real click (Enter occurs between press/release). Complete fields per event
   class, including actual root x/y and event x/y forms when required; preserve
   final idle release without needing another EVENT or EOF.
3. Guardian permits calibration epoch/ticket/admission after forced physical
   release failure, with held=True/release_failed=True. Deny new operations until
   earlier holds/releases/process ownership are resolved. Current command's own
   published hold must not invalidate its existing ticket.
4. Backend command classification is an incomplete mutation denylist. Examples
   include xdotool exec, other desktop/window/XInput mutations and Xprop write
   forms. Use exact positive argv schemas for every allowed read/capture/mutation;
   no secondary executable or unsupported subcommand. Every input-producing public
   helper, including synthetic_target_key_click, must require explicit ticket;
   no compatibility self-issuance. Explicit operation boundary issues tickets.
5. NativeCalibrationRunner._bind_observation does not compare supplied metrics
   with render decoded from the SAME retained artifact. Repro admits verified
   metrics over unavailable/false pixels. Require exact schema/value equality
   before validation/sealing.
6. GTK show_human_prompt only writes a pipe; readiness does not prove label update.
   Child must ACK after processing label.set_text, then parent rechecks certificate
   before publishing readiness.
7. Delayed action is scheduled before synthetic preparation, shortening the
   advertised120s human window. Issue shared ticket before synthetic work, but
   schedule due action only after full synthetic proof, immediately around ACKed
   readiness, with full human timeout plus margin. Test advances clock during prep.
8. Driver reconnect graph still asks disconnect_dialog after dismiss ends in
   game_client; daemon producer uses game_client. One consistent scene throughout
   dismiss postcondition, reconnect precondition/facts/anchor validation.

## Should fix in this correction batch

- Consume preconstruction proof with age/current identity checks, not arbitrary
  finite timestamps. NativeRenderObservation needs original capture monotonic;
  repeated copied artifacts must not masquerade as fresh consecutive captures.
- build_measured_anchor must accept/seal ORIGINAL capture monotonic, not stamp
  driver NOW after model inference; enforce again at one-use admission.
- Postconditions require strictly newer capture sequence/time and same boot/identity,
  not merely a different capture ID.
- Close helper owner-death gaps: XI2 spawn/register is non-atomic, GTK isn't
  guardian registered. Use gated registration or parent-death semantics.
- Keep observer retry handle/ownership until confirmed stop/reap; don't unregister
  after swallowed termination failure.
- Replace guardian fork-after-threads with safe spawn/exec lifecycle (Python3.12
  deprecation emitted on normal tests).
- Remove unused native capture directory on success as well as failure.
- Remove dead direct reload action or implement consistently; strict nonboolean
  DriverProfile coordinates; remove duplicate modifier comparison.

## Verification context

Sol: native/dispatch43pass5.26s with thread/unraisable warnings as errors;
independent native32pass7.32s; Ruff/format/diff exit0. Harmless process tests passed
and left no owned helpers. Exact trace: /tmp/crowley-input-preflight-xi2.txt and
live-client/repeating-preflight.md. Unit inactive/disabled. No GUI/input/edits.
Strict peak gate correctly fails closed. Addon now conditionally measures via
collectgarbage isrunning/stop/restart; pinned live API semantics remain unproved.

## Ownership for this batch

One native implementation owner may change only session driver.py, guardian.py,
calibration.py, input_events.py, and owned test_session_dispatch.py/test_session_native.py.
Independent regression files remain exclusively their test owner. Coordinate original
capture-time API changes with daemon owner before integration checks. No GUI,
services/private configuration, deployed DB, commits or fabricated evidence.
