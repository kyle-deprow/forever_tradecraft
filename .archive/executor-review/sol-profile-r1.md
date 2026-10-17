# Profile review

Reviewer: gpt-5.6-sol, xhigh. Read-only; no tests or GUI operations.
Status: NEEDS WORK.

Accepted Must-Fix:

- Camera planning uses distance as target width, making difficulty always one.
  Use a real safe dimension or explicit validated width and verify replay over
  multiple drag distances/difficulties.
- MOVE pulse-ceiling aggregation includes zero-displacement demonstrations.
  Require measured positive displacement for movement learning.
- Profile saving can emit a nonbaseline/count-zero document rejected by loading.
  Validate the complete document before atomic replacement and preserve the old
  file on rejection.

Accepted Should-Fix: enforce role agreement between nonempty demonstrations and
their baseline, with an explicit policy for role-default construction.

Pointer difficulty fitting, peak curvature, executable budgets and strict schema2
are present; the existing daemon consumes MOVE max_duration. These observations
do not establish native executor behavior. Same Luna four-file owner fixes these;
main runtime source remains separately owned.

Separate GTK r2 rereview: READY, no findings. Strict geometry/native fixture/
property negatives resolved the prior review. Native acceptance still pending.
