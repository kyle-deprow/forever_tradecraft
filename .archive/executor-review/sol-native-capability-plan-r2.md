# Sol native capability plan review r2

Actual serving model: not verifiable from the session or repository metadata available to this reviewer.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

The revised plan closes the r1 findings at the reachable boundaries: `.archive/PLAN-native-motion-capabilities.md:117` and `.archive/PLAN-native-motion-capabilities.md:163` cover the direct `execute_motion_key` / `_execute_motion_key_with_frame` path reached from `src/crowley/session/cli.py:204`; `.archive/PLAN-native-motion-capabilities.md:127` defines observable clearing of both retained artifacts for initial, immediate-precommit, post-release, and successor failures; `.archive/executor-review/native-api-parent-verification.json:39` pins the six calls and arguments to retained evidence; `.archive/PLAN-native-motion-capabilities.md:68` fixes all tuple members to the existing nonphysical `[0,1000]` wire range; `.archive/PLAN-native-motion-capabilities.md:155` excludes CRS1 payload/framing code from the mutable fence; and `.archive/PLAN-native-motion-capabilities.md:229` supplies a strict quiesced schema-3 cutover with no compatibility window. The required producer, protocol, pixel-decoder, `MotionFrame`, default-daemon, admission, drift, and zero-input refusal regressions are feasible within the listed source/test fence without changing deadlines, resource limits, visual evidence, measured role displacement, or the shared two-unit ledger.

STATUS: READY
