# Native operator production-proofs: Sol source review

Reviewer configuration: `gpt-5.6-sol`; the resolved runtime model ID is not
exposed to this tool. Scope was the complete frozen helper pair only:
`tools/native_calibration_operator.py` at
`715138e50b600c08aac4c348831ce550328051e90a50703f1256d3f304f9e03e` and
`tests/test_native_calibration_operator.py` at
`ea4f561fa528afb6cf8b6d5052a3a11ed6bbf3faf4cf93fc5a1574dbabb08dcb`.
The six R7 native files remain unaccepted development inputs and are not
reviewed here. I did not run tests or builds. I accept as verification context
the parent's exact-byte fence, scoped checks, and private-XDG `58 passed in
43.68s` result (log SHA-256
`31cbf90dad7774af65c23c1ae09afe347e2c40c971c0cfb8b60597fd2ebe648f`), plus
the worker's `58 passed in 41.31s`; those results do not cover the paths below.

## Must

1. **The known-ID bootstrap cleanup horizon still ends at the old prepare
   expiry.** On an indeterminate operation,
   `tools/native_calibration_operator.py:1922-1940` assigns
   `max(current_deadline, now + 5)`. If the old prepare expiry is more than five
   seconds away, this adds no time after that expiry; the actor returns at
   `:1955-1958` before owner EOF can request exact cancellation of the
   server-extended same ID. Set the bounded cleanup horizon after the old bound,
   for example `max(current_deadline, now) + KNOWN_ADMISSION_CLEANUP_GRACE`, for
   the known-ID indeterminate bootstrap case. This remains cleanup-only and must
   permit neither admission retry nor dependent input. The purported regression
   at `tests/test_native_calibration_operator.py:3276-3378` times out the reply
   after 0.2 seconds and abandons the actor immediately, while the real default
   prepare expiry is about 45 seconds; it never crosses the old expiry. Make the
   real daemon issue a short but greater-than-grace old expiry, commit the long
   bootstrap extension, lose the reply, keep the owner alive strictly past the
   recorded old expiry, then close owner control and require one exact-ID cancel
   and bounded actor exit.

2. **Full `measure-deferred` terminal-error recovery is unreachable.** In
   `_await_calibration_terminal`, `calibration_status` may report `error`, but
   `_recheck()` runs first at
   `tools/native_calibration_operator.py:3289-3315`. The real daemon has already
   archived a construction terminal whose `reservationState` and handshake are
   `error`; `ReservationBinding` excludes that state (`:138-140`, `:268-271`)
   and actor recheck excludes an error handshake (`:1778-1789`). Recheck therefore
   raises before `_calibration_terminal_error` is set at `:3310-3315`, so
   `run()` skips pause/fresh recovery at `:3529-3545`. Handle a validated native
   operation `error` before construction recheck, preserve its causal error,
   then strictly status/pause to a newer PAUSED generation and call actor-owned
   `recovery_begin` with the empty ID. Give that fresh admission a new bounded
   request deadline instead of the closed measure reservation's deadline; keep
   the actor bound to the old known ID until the new canonical ID/expiry is
   ACKed. Do not make `error` a successful/terminal reservation state. Replace
   the direct-client test at `tests/test_native_calibration_operator.py:3381-3490`
   with a full `NativeCalibrationOperator.run()` regression through real
   `SessionIPC`, asserting the original failure remains the result/receipt while
   recovery reaches `recovered` with a new exact ID.

3. **Named phase deadlines do not reach chat input.** The helper records
   `providerDeadline`, `finalizeHookDeadline`, and `finalizeDeadline` at
   `tools/native_calibration_operator.py:2703-2738`, but `_chat()` always selects
   `_deadline()` without a phase at `:3029-3057` and passes that generic bound to
   physical dispatch at `:3058-3085`. Thus release/hold/measure/resume typing may
   outlive `providerDeadline`, and finalize typing may outlive
   `finalizeDeadline`; a later daemon refusal cannot undo emitted input. Map the
   four provider commands to `_deadline("provider")` and finalize to
   `_deadline("finalize")`, and carry that one absolute bound through the final
   recheck/identity gate, `FixedInput`, emitter READY/GO/PRESSED waits, and
   pre-dispatch watchdog ownership ACK. Safety release remains independent of an
   expired phase. Test one tick below each complete fixed sequence with the real
   sealed emitter/recorder and assert no GO/tool log/physical action; separately
   expire after possible press and prove exact release and reap.

4. **The required three-mode production composition is not proved.** The actual
   control and recovery operator tests at
   `tests/test_native_calibration_operator.py:2933-3170` still use `FakeScreen`
   and `FakeInput`; scene changes are not caused by owned dispatch. The measure
   test at `:3183-3273` calls only the client and accepts either complete or
   error. The compiled producer test at `:3173-3180` merely invokes a separate
   native test. The only production-readiness unit at `:903-933` covers absence
   with injected capture/classifier, not ordinary decoded readiness. Minimum
   acceptance proof is an isolated composed fixture using actual
   `SessionDaemon` + AF_UNIX `SessionIPC`, production
   `X11Screen.wait_reload_boundary`, `FixedInput`/`OwnedEmitter` and the sealed
   recorder, with external pixels/OCR/clocks as the only injections and scene
   advancement after acknowledged owned dispatch. It must cover: control
   preflight; standalone recover parameterized for `ordinary_reload` and
   `restore`; measure success through all 12 history states and actual
   `finalized`; the full error/new-PAUSED/empty-ID recovery above; ordinary
   readiness refusals for damaged/loading, identity drift, construction-prefixed
   boot, active fence, and wrong phase/ordinal; and the physical budget cases in
   Must 3. Reservations and successful replies must come only from the daemon.

## Should

- Tighten `_pause_after_terminal_error` at
  `tools/native_calibration_operator.py:3363-3398`: it currently accepts missing
  or malformed `calibrationOperation` and `guardian` objects. Require the paused
  operation mapping to be explicitly non-running for the same native generation
  and `guardian.armed is False` before fresh recovery.
- During active workflow, `_event()` at `:2539-2545` records a receipt write
  failure but permits later input. Propagate the first `ReceiptError` before the
  next physical gate; during protected cleanup, retain it without interrupting
  release/cancel/reap. Add an event-publication failure before first dispatch and
  assert zero dispatch plus failure receipt/exit behavior.
- Expand constructor rollback coverage beyond the lone watchdog readiness case
  at `tests/test_native_calibration_operator.py:2670-2692`: inject each
  X11Screen, OwnedEmitter, Watchdog, and CancellationActor allocation/start/READY
  failure and assert descriptors/specs close and no child remains. The reviewed
  rollback code is staged, but the promised failure matrix is absent.

## Nits

None.

STATUS: NEEDS WORK
