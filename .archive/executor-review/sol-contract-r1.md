# New scoped r5 C+D1 Sol contract review

Requested/launched gpt-5.6-sol/xhigh/fork none; serving ID unverified. Read-only
review verified all42 freeze-r9 hashes; no tests/edits. STATUS NEEDS WORK.

Must: shared RawMotionPairing.observe_delivered compares every queued timestamp
against first primary, rejecting valid FIFO raw11/raw12/primary11/primary12.
Guardian duplicates this check for echoes, so primary10/raw11/delayed-echo10/
primary11 revokes. Match FIFO head only, invoke pairing for measured primary
source only, preserve exact endpoint/target/path/modifier/echo checks. Add actual
consumer regressions for FIFO differing timestamps and delayed echo interleave.

Should: actual waypoint executor tests must cover admitted positive and negative
bearings at both .8 and1.2 response; existing extreme tests are straight and
nonzero test only positive refusal. Scalar prefilter error must not call1.4
the admissible range; actual2D bounds are heading-dependent with lower gap.
Root architecture/HANDOFF ranges already updated while review ran; daemon
message still needs repair. No functional D1 geometry defect found.

Verified C begin-epoch/stop fences, identity failure reaping/retry, idle RawMotion
parsing and bounded rawLines; D1 full2D speed/facing/position-ball admission,
conservative pre-camera proof, early mirrored refusal, native capture clock and
production consumer lifecycle fixture. C NEEDS WORK; D1 NEEDS WORK for explicit
test/diagnostic acceptance. No live qualification or compositor cause claimed.
