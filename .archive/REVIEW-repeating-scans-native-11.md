# Native review round 11

Status: correction required following Sol native10 review (77 tests passed).
Same six owned files only: session driver.py, guardian.py, calibration.py,
input_events.py; tests/test_session_dispatch.py and tests/test_session_native.py.
No other source/tests, game input, live proc resets, services, data, or git actions.

1. Gate the completed 100-update p99 in resume_render in both the runner and
   verify_seal. Agent snapshots before recording the current publication, so
   held/100 omits update100 while resumed normal/0 contains updates1..100.
   Preserve exact held render as diagnostic evidence. Do not substitute or edit
   metrics to manufacture binding. Gate the actual completed window, excluding
   held/0 from the threshold. Real Agent regression: updates99 and100 each300ms
   must fail despite held/100 reporting low p99; malformed sealed resume and
   exact250ms boundary checks must remain strict.
2. Set active_window before the update begin_window call, as already done for
   construction. A post-reset identity check may fail after pending installation.
   Prove a real runner failure clears pending and an immediate same-meter retry
   succeeds, with durable failure/restoration handling retained.
3. Correct live wrong-executable regression: expected and running executables
   must have distinct canonical realpaths, and the wrong process must remain
   alive during identity rejection. /bin/sleep and /usr/bin/sleep are the same
   executable. Assert mismatch and confirmed cleanup/reaping.

Preserve prior fixes: sole durable restoration_required receipt, actual Agent
wrong/cached/skipped bytes, pinned original PID directory writes, exact native
limits/timestamps, XI2/GTK/tickets/scenes/generation/capture freshness, reaping.
Run the two owned strict suites using the three required warning filters, Ruff
check/format, compileall and diff check. Report exact new negative node IDs,
actual results and unresolved issues, then DONE only when frozen. Parent
reproduction and independent Sol re-review are required before live readiness.

Final Sol verdict READY, no findings. Production sources passed80strict tests
in144.42s (parent independently80in144.09s); a remaining test-only off-by-one
was corrected to identity check5 and now asserts pending ownership plus both
construction/update reset records at injection. Focused final Sol1passed13.48s.
Completed resume p99 and exact250ms boundary, actual wrong executable/reaping,
and post-reset failure cleanup/same-meter retry are all reviewed. This clears
only the six native files; daemon/controller integration and live gates remain.

## Reopened exact completed-window binding

Parent real-Agent counterexample after that verdict: make updates1and2 take
300ms, then publish one extra actual normal/0 after Resume before capture.
Runner accepts held p99=300.01, resumed p99=0.01, held updateCount103 and resumed
count105, sequences104->106. The later rolling window has dropped one slow
measurement; it no longer describes the exact100updates. Private reproducible
script /tmp/crowley-p99-resume-proof.py uses real Agent bytes/production decoder
and a disposable helper process, never the game.

Luna owns ONLY calibration.py and tests/test_session_native.py for this fix.
Require the first resumed normal/0 publication exactly after held100: sequence
plus1 and updateCount plus1, same boot, fresh original capture. Gate that frame's
completed p99; reject a missed later normal frame rather than accept a shifted
window. Enforce in runner and verify_seal. No new metrics, restamping, altered
Agent timings, relaxed limits or addon/driver/daemon changes. Runtime owner has
one separate driver clock expression; do not touch it. Add real-Agent earlyslow
updates1/2 plus laterresume regression, and sealed later-count/sequence rejects;
preserve exact250ms boundary and successful exact-firstresume. Run focused
native11 regressions, Ruff/format/compile; parent reproduction + independent
Sol narrow re-review before restoring READY. Full80tests run in final suite.

Final narrow Sol verdict READY, no findings. First-resume exact sequence/count
checks are enforced by runner and seal; real earlyslow/lateframe rejects.
Original decoder uses injected driver clock (direct321.25probe passed), with
no timestamp restamping. Focused5passed65.32s; preserved lifecycle/failure15
passed79.42s. Ruff/format/compile pass. Parent focused5 also passed as part
of its mixed run; final full suite is in progress.
Reviewed calibration SHA2561c509d1c711f12c6ebebbb545f2f7237bacd9f76b3af7265103dc5fb3b6937e1;
driver2543133e767c3535be8d5325724bbca96289db07396d7246deb7fb8950922918;
testnativee087e99f867f78255adc2529c22d72e231a10e5277635732628754c034c822ab.

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

Final narrow X11 correction Sol verdict **READY**, no findings. Independent
focused9tests passed0.13s under strict3/private lease; broader native
ancestry selection9pass. Frozen driver hash7ba522286caf6aaa8654c66a4ccb5fb3899e268b0d0b60f785679beefc07bae7,
calibration53909a8cf02bac7d6fb582a02d388f41e0ad6e12a0ca4dc057cc65a230704962,
nativeTestc03647803c00bb7a91cf7afd2235259c43eab612d9b595a8663eb0520097ac9e.
Parent real read-only identity resolution succeeded before clearance. Sole
Luna operator cleared to restart unarmed daemon, use fresh generations and
retry native calibration from fresh no-Agent/world/AHclosed boundary. No
new live measurement or physical sample is claimed by this review verdict.

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
