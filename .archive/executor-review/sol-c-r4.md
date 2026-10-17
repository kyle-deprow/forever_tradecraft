# C rereview

Reviewer: gpt-5.6-sol, xhigh, read-only. STATUS: NEEDS WORK.

Accepted Must-Fix:

1. Camera release still uses the old boolean gate, allowing press→release→held
   trace to complete. Require all held primary/echo motion before raw release;
   reject source motion once release begins.
2. Pointer/camera schemas still share a generic balanced gesture grammar that
   admits key operations and camera motion entirely before press. Separate
   positive grammars; camera needs one right press, actual held movement and
   its final release; pointer permits bounded moves/sleeps only.
3. Planned holds are discarded rather than retained as allowed expectations.
   Cross-check actual publication against the action and derive/verify exact
   typed-argv holds, preventing the watchdog from releasing a different key.
4. Empty exact game target certificates silently use generic ancestry. Reject
   empty certificates and use exact target membership only.

Accepted Should-Fix: production camera entrypoint negative cases for early
release, wrong ordering/coordinates/target, missing/late delivery and cancellation
during movement/hold; hold mismatch publication and native positive certificate
regressions. Happy-path-only coverage missed the remaining phase defect.

Level-zero keys, absolute driver deadlines, positioning trace, endpoint fields,
direct-root relationship and nonblocking IPC/fast stop otherwise looked coherent.
D1 remains a separate mutable scope. No live executor acceptance is established.
