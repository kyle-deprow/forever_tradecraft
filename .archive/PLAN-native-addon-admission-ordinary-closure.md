# Narrow rescope: recovery admission and ordinary publication

The broad addon implementation has completed three scoped fix rounds. R4's
publication changes are frozen. Opus R3 returned after that freeze with two
separate defects. Narrow this work to TWO functions and their regression tests,
not another full addon rewrite. Start from exact frozen R4 in a new final tree.
Own only addon/Crowley/Agent.lua and tests/test_addon.py. All other R4 bytes,
prior plans/freezes, daemon/helper/config/GUI/deployment/git are read-only.

1. BeginRecovery must refuse real in-load pending state (restoreInFlight or
   lifecycle == restore_pending), never infer admission from a malformed raw
   marker.state. Every malformed matrix marker, including raw restore_pending
   with uppercase/short/long/nonhex nonce or bad attempts/extra keys, must remain
   recoverable through the fixed recover slash and actual Restore callback.
   Preserve raw marker until Restore writes the canonical one. Plain ordinary
   with no marker still refuses; post-Finalize recovery still works.
2. On accepted recovery, arm the native fence immediately and refresh through
   Commands' existing path. Decode the next real periodic frame after post-
   Finalize recover and require the armed empty-reason projection.
3. Restore ordinary-load publication semantics: after createSurface succeeds,
   attach the periodic callback and use safePublish. A transient first ordinary
   publication failure must keep the surface and periodic retry; the next
   update_agent frame must strictly decode. Keep loud constructor-allocation
   failure diagnostics/refused defer. Do NOT weaken transactional first/second
   publications in deferred Construct/restore or checked Finalize.

Read actual Opus R3 report and root adjudication. R4 already covers the earlier
matrix gaps; verify its tests address Opus's concrete pairs/nonce lengths/64-byte
case, defer-under-logout refusal, AH-open rearm, held/0 Resume not enabling Finalize,
and exact prefixed/restored boot assertions. Add only named missing checks.

Run full addon+companion suite, scoped statics/diff and four frame/atlas smoke
checks. Freeze all eight final hashes, with only the two owned paths differing
from R4. Parent verifies, then Sol/actual Opus close the combined remaining delta.
No source promotion/native slice until accepted. No live qualification claim.
