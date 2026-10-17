# R5 to R6 activation/action closure

R6 is based on the hash-verified R5 forwarding candidate at `2a8d73e` and
keeps the R3/R5 caches, binaries, source freezes, and retained failures
immutable. The new build uses the separate cache
`/home/dev/.cache/crowley/gnome-telemetry-region-r6` and pinned image
`sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858`.

The compiled producer now rejects GApplication activation and each application
action route at the telemetry-process boundary before shared-option mutation,
capture, or UI. The native forwarding regression drives valid private-bus
`Activate`, `ActivateAction`, and `org.gtk.Actions.Activate` calls while a real
Shell capture is blocked, then releases and reaps every child. It retains the
exact primary guard diagnostics and checks that no extra area or stock capture
was admitted.

R6 also removes the stale profile-anchor exclusion from full profile
comparison, records pre-producer failures as typed `not_started` evidence, and
updates the stale fake-backend test to assert production X11-only refusal while
retaining the stock-model half. The R6 harness and examples point to the new
cache, binary, patch, and manifest hashes.

The prior three-way stress failure remains retained evidence: the guarded
capture PNG was not decodable at the producer exit boundary (`exit=0`) under
concurrent staged invocations. The R5 parent batch also retains its one stale
fake-backend test failure; no broad rerun was performed for R6.

The final uninstrumented compiled-default node reproduced the same boundary in
two bounded serial runs after the exact guard-output assertion was tightened:
one failed during `motion` after bootstrap and one during bootstrap itself.
Both failures report producer exit `0`, no producer stderr, and an undecodable
temporary `capture.png`; two diagnostic-wrapper runs passed. The likely narrow
boundary is the existing `_wait_for_complete_png` helper treating an observed
producer exit as terminal immediately after a failed decode, without a final
validation. `driver.py` is outside this R6 source scope, so the evidence is
retained for parent adjudication and no retry, sleep, deadline, or driver
change was introduced here.
