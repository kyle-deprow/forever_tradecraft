# Native readiness review, round 4

Sol: MAJOR ISSUES. 46 passing tests do not authorize human/GUI calibration.

1. Gated Popen DEADLOCKS: preexec_fn waits on pipe that parent writes only after
   Popen returns, but Popen waits for exec completion. Real /usr/bin/true test
   timed out after4s and left a child spinning on EOF. Use an EXECUTED wrapper
   process: Popen returns after exec of wrapper, register group under epoch
   fence, then release wrapper pipe; wrapper EOF exits immediately. Never wait
   in preexec_fn. Add real harmless process success/cancellation/orphan tests.
2. Input/native seals accept evidence_hash='' and skip recomputation; input
   canonical payload omits game identity/geometry. Empty events and native
   identity/start/capture/geometry are accepted. Require complete canonical hash
   covering EVERY fact, mandatory strict fields/capture proof and unconditional
   recomputation. No production compatibility branches for fake fixtures.
3. HWM sampled AFTER operator loads Agent. Correct order must be absence proof,
   actual baseline HWM, THEN externally visible bootstrap-ready, THEN operator
   loads, construction capture,100updates. Carry baseline/capture identity/hash
   in sealed preconstruction evidence. Provider and full capture binding are
   mandatory; remove optional/conditional production paths.
4. Due-action ticket was never admissible: queued unarmed gen0, rejects at due
   even with no human revoke. Introduce calibration-only admission valid solely
   for owned GTK target before takeover; prove valid positive control and stale
   old-ticket rejection before spawn after takeover. No game/launcher authority.
5. Guardian learns arbitrary first key detail, accepts absent delivered modifiers.
   Full detail999/no-modifier stream passed. Pin expected detail sequence and
   require exact modifier facts; remove --clearmodifiers or model its full actual
   release/restore semantics and owned holds.
6. Focus-only action publishes watchdog H(emptysets), leading infinite owner-death
   release retry. Separate active process groups and exact nonempty held inputs;
   watchdog must terminate active groups even when there are no held keys.
7. Anchors lack capture-path/hash canonical seal and are reusable after dispatch.
   Bind retained actual capture, identity/control/scene/bounds/target ancestry/
   time/generation/action; atomically consume on admission including failure.
   Remove obsolete all-six compatibility API (or strict isolated non-live helper).

Should fix: failed calibration can't retry because canceled state only resets
after successful arm; create fresh calibration-only epoch on explicit retry,
never revive old tickets. Clean consumed intermediate images immediately and
empty run dirs; retain final artifact. Report ordinary revoke release failures
through final callback/status, not only close. Tests must use complete fixture
evidence; do not weaken production validation to preserve thin private _issue
fixtures. Content changes, blank hashes and omitted required fields must fail.

Verified: GTK prompt/readiness after complete releases, streaming block flush,
observer death revoke, structural ancestry, identity, four-pixel and sameboot101
checks, provider shares exact capture+SHA with runner. No live action occurred.

## Bounded correction ownership

Fresh dispatch owner: driver.py,guardian.py and new tests/test_session_dispatch.py.
Fresh calibration owner: calibration.py,input_events.py,tests/test_session_native.py.
Lead integration owner (once reactivated): daemon/controller/CLI/model/config/
evidence/journal/docs/deploy existing fence, no native files. Independent tests
owner alone modifies its existing two regression files. Coordinate lifecycle
and exact interfaces directly; parent resolves dependency issues. Real harmless
process tests and fully strict fixture data are required, not only fakePopen.
