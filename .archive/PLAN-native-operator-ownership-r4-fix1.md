# Ownership R4 fix1: concrete parent failures

R4 original is frozen; root creates native-calibration-operator-ownership-r4-fix1-20261018
with its exact two files and same exact six native R5 DEVELOPMENT files. Follow
original ownership R4 plan, two-file fence and all no-GUI/no-service/no-git rules.
No native acceptance or live release. This is one bounded ownership fix round.

Parent actual full helper run:32passed1failed15.07s, exact R4 hashes. Failure in
button owner-SIGKILL test: expected release was logged and emitter gone, but the
immediate watchdog kill(pid,0) assertion raced its final exit. Retained private
native-operator-ownership-r4-parent-20261018/helper-suite.log SHA
d7125fee6cdbe896af6b291335754cf658e72193bfe39b066db7c961fdcf053f.
Do not rerun unchanged or weaken release/reaping assertions. Wait a bounded
monotonic interval for the same exact PID/start identity's actual exit/reap;
check release and emitter termination independently. Retain complete real output.

Also finish these original ownership-stage requirements (not new scope):
1. _cancellation_entry currently returns on control EOF when /proc still shows
   the killed owner's start identity (zombie/not-yet-reaped race), skipping IPC.
   Treat abrupt EOF as cancellation ownership termination; only explicit normal
   stop/ACK disarms. Test owner killed but deliberately not joined/reaped until
   exact cancellation arrives. Keep bound-ID / PID-start reuse protection.
2. _arm_cancellation_actor stops old actor before new starts. Eliminate that
   unprotected admission/handoff window. Implement canonical acknowledged update
   to the independent actor or equivalently closed handoff without stale-ID
   cancellation of a newer run. Test death at prepare/bootstrap/new-expiry/
   recovery-gen-ID adoption boundaries. No arbitrary requests or retries.
3. Delayed-release test currently calls close in test owner and waits until
   actor exits; it does NOT prove helper interpreter exit is bounded while actor
   remains alive. Launch a real owner subprocess through production lifetime/
   cleanup, make release persistently unavailable long enough, require owner
   process nonzero bounded exit while independent actor remains alive, then
   enable exact release and observe actor completion. Do not kill the actor or
   fake release success. Ensure setup/readiness failure closes fd/spec/control
   resources; repeated handled signals and receipt begin/event/finish failure
   cannot skip required release/reap/cancel.
4. Current actual-owner test builds raw components in fixture helper; cancellation
   test creates actor in the surviving parent with a sleeping surrogate owner.
   Add production NativeCalibrationOperator/main lifetime composition proof:
   canonical admission arms actor, actual input holds after ACK, kill real helper,
   observe independent exact release AND same admitted IPC cancel. Include both
   key/button, handled TERM/HUP/INT and repeated signal during cleanup, using
   harmless sealed compiled fixtures/local real socket transport only.

Run focused owned cases then fullhelper once after finalsource; no full native/
performance suites. Scope statics, exact hashes/import origins/private logs and
MAIN executor-review/native-operator-ownership-r4-fix1.md report. State coverage
literally. No DONE until bounded stage complete; no live/full-native claims.
