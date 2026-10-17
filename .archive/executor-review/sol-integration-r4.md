# Sol focused D1 review, 2026-10-16

Actual gpt-5.6-sol/xhigh, read-only; STATUS: NEEDS WORK. Parent accepts both
material findings and the regression request. The preceding parent snapshot
passed50 strict hermetic checks in101.44s; tests did not cover these contracts.

1. daemon.py:2692-2694 stores the forward offset twice for left strafe.
   MovementBasis defines strafe_heading_offset as the residual from calibrated
   world-forward plus handedness*pi/2, and runtime already includes beta in
   world-forward. Subtract beta when deriving the stored residual. Correct the
   existing reflected test, which currently asserts the buggy residual equals
   beta, and assert runtime route heading matches the independently measured
   left vector at a nonzero native facing.
2. daemon.py:2565-2583 accepts calibration post-release feedback still reporting
   speed>.25; later settling travel is not included in measured displacement or
   cumulative budget, and the final role can seal while moving. The standalone
   pulse response at2874-2895 likewise reports completion while still moving.
   Fail closed on moving post-release feedback before accepting displacement/
   sealing/continuing, or observe through bounded stationarity and charge the
   complete displacement. Add actual installed-path regressions for both cases:
   no next role/basis seal and no successful normal-pulse completion.

The reviewer found the retained-owner shutdown, cleanup aggregation, focused
chat gate, minimum-pulse envelope, exact three stalls, confirmed pre-probe speed,
per-role facing and actual camera baseline drift repairs coherent.

No GUI, physical-human or native game executor proof follows from this review.
