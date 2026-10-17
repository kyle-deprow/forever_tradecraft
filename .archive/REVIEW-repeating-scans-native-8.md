# Native review round 8

Sol verdict: MAJOR ISSUES despite 50 owned tests passing. Keep previously verified
XI2 attribution, takeover, ticket, scene, freshness and helper-reaping behavior.
The authoritative resource contract remains PLAN-native-memory-measurement.md.

## Required native corrections

1. Pin `/proc/PID` itself once, not `/proc` followed by repeated PID lookups.
   Resolve status/stat/exe/clear_refs relative to that PID directory descriptor.
   Prove replacement PID paths cannot redirect the write after identity checks.
2. The actual daemon callback must durably archive historical accounting before
   each clear_refs write. Returning from an identity-only callback is insufficient.
   Verify production callback persistence and failure-before-write, not list.append.
3. Require the requested phase and ordinal on every returned observation:
   construction normal/0, pre-window held/0, updates/1 through updates/99,
   final held/100, then a fresh normal/0 after operator resume. Ordinary normal
   publications cannot substitute for any measurement stage. Prove 1Hz cadence,
   exact sequence and ordinal continuity, and a fresh same-boot resume frame before
   input calibration. The daemon must expose actual operator-visible hold-required,
   measure-ready, resume-ready and failure/restoration status through its existing
   status/IPC path. Register returned capture artifacts before any validation.
4. Abort/consume pending memory windows safely after every failure and release
   every returned artifact. A failed run must not poison the next meter run or
   silently leave the Agent held without explicit restoration status. Preserve
   historical accounting already archived; do not pretend a reset can be undone.
5. Verify the actual resolved xinput executable has successfully replaced the
   admitted wrapper in the same registered PID before readiness/arm succeeds.
   A live Python reader thread or substituted sleep process is not readiness.

Also fix sealed workload boundaries: construction starts at the post-reset
bootstrap-release boundary, not its later finished capture. Revalidate exact two
windows, fixed 128/16 MiB limits, phase window ordinal 0 and workload ordinals
0→0 / 1→100. Correct stale frame-count comments/docs to include post-resume.

## Ownership and integration

Native owner: only driver.py, guardian.py, calibration.py, input_events.py,
test_session_dispatch.py and test_session_native.py under the established paths.
Engine owner: only its existing eleven files; actual daemon/provider/status and
durable journal archive integration, matching runtime fixtures and documentation.
Independent regression owner retains its two files. No cross-owner edits.

Native and engine owners must agree exact callback/status/provider interfaces
directly before implementation, then complete actual producers and consumers.
No undefined future callbacks, asserted operator actions or normal-frame shortcuts.
The production before-reset callback must complete a durable journal append before
returning; any failure prevents the reset syscall. Test that exact ordering with
the production owner and a harmless owned child or controlled proc fixture.

Run scoped and independent tests with thread/unraisable/fork warnings as errors,
then parent full suite, Ruff/format and independent Sol re-review. Include negative
normal/0-at-every-stage, wrong/skipped/old ordinal, absent resume, reset archive
failure, construction/provider validation failure, retry and actual executable
readiness tests. No game input, live reset, service activation, persistent data
edits, unrelated files or git mutation. Live acceptance remains outstanding.
