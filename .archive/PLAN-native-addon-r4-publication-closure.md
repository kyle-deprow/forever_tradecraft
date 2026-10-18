# Native addon R4: complete publication transaction

This is the third and final scoped fix round, based on immutable R3. Preserve all
prior freezes. Read Sol R3 and earlier parent adjudication. Same eight-file addon
fence; new changes should be limited to Agent.lua and tests/test_addon.py unless
an exact callback dependency requires another already-owned file. No main code,
GUI/deployment/native/helper/config/commit/reset/stash changes.

1. Restore load has TWO publications: initial armed proof and required unarmed
   ordinary proof. BOTH must succeed before recovery is committed. Preserve the
   restore token/marker until the second succeeds. If second publication fails,
   restore an exact valid recoverable marker, re-arm native fence, detach scripts,
   hide every owned surface/texture, clear bytes, show enabled Restore, and retain
   nonordinary lifecycle. Test succeeds-first/fails-second at real serializer or
   telemetry boundary; then recover again through exact slash+button and new load.
2. Finalize must check its inactive-fence publication too. Tentatively release
   native fence, publish strictly, then commit marker removal/finalized lifecycle.
   On failure restore constructed marker/fence, return publication_error, preserve
   the reachable recovery route and never print accepted. Test that exact fault.
3. Close the named finite test gaps without changing marker grammar: every state
   crossed with attempts0/1/invalid; valid64-byte opaque token and65 invalid;
   number/wrong-type state/token; short/long/nonhex recovery nonces; all pre-load
   manual/event/timer/rearm entry paths; direct unconstructed Publish/Snapshot
   typed refusal with no counters/marker/frame changes. Use otherwise valid inputs
   so each named predicate is reached. Preserve all prior actual frame decode,
   template, visibility, nonce/load/attempt timer, publication and lifecycle cases.

Run full addon+companion suite, scoped static/compile/diff checks, and existing
four compiled frame/atlas checks. Parent repeats necessary tests and reviews the
exact delta. Sol and actual Opus review only combined remaining findings and new
regressions before native slice release. If another blocking condition remains
after this round, rescope instead of another blind full implementation loop.
