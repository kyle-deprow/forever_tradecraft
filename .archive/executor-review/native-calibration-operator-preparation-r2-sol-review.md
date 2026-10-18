# Sol source review: native calibration operator preparation R2

Reviewed the two frozen, untracked candidate files at
`/home/dev/.cache/crowley/worktrees/native-calibration-operator-preparation-r2-20261018`
against the closed helper, composition, and ordinary-recovery contracts. The observed
SHA-256 values match the handoff: `8958a8ef...f589e` for the helper and
`3d8d0a3a...1b5b09` for its test. This was a read-only source review; I did not rerun
tests, builds, services, GUI input, or git operations. The reported 13-test pass is
therefore treated as supplied evidence. The frozen R3 native dependency's missing
`stateHistory` is deliberately excluded from the findings because R5 owns that fix.
This review does not qualify composition or live input.

## Must-Fix

1. **A successful measurement terminal record is rejected by the helper's own closed
   schema.** `tools/native_calibration_operator.py:136-137` omits `finalized` from
   `RESERVATION_STATES`, and `ReservationBinding.from_record` rejects every value
   outside that set at `tools/native_calibration_operator.py:256-259`. The actual
   dependency publishes a copied terminal reservation with
   `reservationState="finalized"` at `src/crowley/session/daemon.py:6388-6399`.
   Consequently, `_chat(... post_state="finalized")` cannot adopt the successful
   terminal reply and the real measure mode fails after Finalize. The fake client
   conceals this by leaving its binding in `prepared` for the entire sequence
   (`tests/test_native_calibration_operator.py:83-105,126-134`). Add the terminal
   value and validate an exact mode/phase matrix: prepared measure/preflight at
   prepare, consumed measure after bootstrap, recovery/recovery at handoff,
   finalized measure at construction completion, and recovered recovery at recovery
   completion.

2. **The production panel search rectangle points at the wrong part of the screen.**
   `_control_region` returns `(width - 244, height - 108, 220, 84)` at
   `tools/native_calibration_operator.py:1582-1590`. The frozen panel contract anchors
   a 220x84 panel to `TOPRIGHT` with a 24-pixel inset, which maps to top-left capture
   coordinates `(width - 244, 24, 220, 84)`, not the bottom-right rectangle used here.
   The tests use a 64x64 identity, causing `_control_region` to return `None` and the
   matcher to search the entire synthetic image, so they never exercise the production
   transform (`tests/test_native_calibration_operator.py:23-37,242-292`). Implement
   the explicit UI-to-capture transform, refuse unsupported geometry instead of
   silently widening to a global search, and test a full-size top-right layout.
   `require_dual_positive` must also reject any rectangle intersection, not only
   exactly equal boxes (`tools/native_calibration_operator.py:565-574`).

3. **Chat input still has blind and unguarded key edges.** `_chat` performs one daemon
   recheck and identity lookup, then immediately presses Return, types, OCRs, and
   presses Return again (`tools/native_calibration_operator.py:1592-1613`). The first
   Return has no fresh proof that chat is closed or that an existing buffer is empty;
   if chat is already active, it can submit unrelated text before OCR. There is also
   no fresh daemon/identity/focus guard immediately before typing or before the final
   submit after OCR and receipt I/O. The mismatch cleanup similarly sends Escape
   without a fresh guard (`tools/native_calibration_operator.py:1607-1611`). Prove the
   closed/empty pre-state, and repeat the canonical binding, deadline, identity, and
   foreground checks at every physical key edge. On drift, abandon without emitting a
   new key.

4. **Keyboard/type input is neither owner-death controlled nor bound to the configured
   graphical session.** Return, Escape, type, and mousemove are direct
   `subprocess.run` calls with inherited environment and no registered process group
   (`tools/native_calibration_operator.py:921-950,965-970`). The emitter subprocess
   also inherits the helper environment (`tools/native_calibration_operator.py:748-784`),
   and the watchdog receives `dict(os.environ)` at
   `tools/native_calibration_operator.py:1015-1031`. By contrast, the selected
   `X11Backend` queries with `profile.display` and its resolved Xauthority. A valid
   explicit config can therefore capture and verify one display while the helper
   sends input, or emergency release, to another. A helper kill can also leave a type
   child running or a keyboard key/modifier held because only the mouse emitter group
   and button 1 are published. Carry the exact profile-bound DISPLAY/XAUTHORITY to
   every input and release child, and give each keyboard action the same gated,
   acknowledged group/held-key ownership and exact cleanup as the button path.

5. **The watchdog can be killed before it proves exact physical release, and setup
   failure leaks it.** `release_now` and `close` send `S`, wait three seconds, then
   terminate the watchdog if it is still releasing
   (`tools/native_calibration_operator.py:1063-1078,1089-1115`). The reused watchdog
   intentionally retries termination/release until it succeeds, so killing it at that
   point can leave button 1 down. There is no completion acknowledgement for `S`.
   Also, a readiness failure after `Process.start()` raises directly from
   `Watchdog.__init__` without closing pipes/release capability or terminating and
   reaping the partially started child (`tools/native_calibration_operator.py:1005-1043`).
   Add an acknowledged cleanup-complete boundary and constructor rollback; never
   terminate the only exact-release actor while it still owns input.

6. **SIGKILL/owner loss releases the mouse but cannot revoke the daemon reservation or
   recovery ticket.** The independent child is only `_watchdog_entry` with input
   descriptors (`tools/native_calibration_operator.py:1015-1034`). Reservation/ticket
   cancellation exists only in the helper exception path
   (`tools/native_calibration_operator.py:1714-1728,1825-1835`), which cannot run after
   SIGKILL. The active admission therefore survives until daemon expiry, contrary to
   the required owner-death cleanup and second-actor exclusion. Add an independent,
   bounded parent-death cancellation path carrying only the admitted generation and
   reservation ID, while retaining the existing single Guardian/lease ownership.

7. **Phase deadlines are conflated, the addon release window is absent, and visual/input
   work can outlive its evidence.** `_record_operation_deadline` takes the minimum of
   every deadline ever present and never permits a later phase to replace it
   (`tools/native_calibration_operator.py:1383-1411`). Because the native handshake
   retains `constructorClickDeadline`, that click-only deadline continues to bound the
   101-measurement and Finalize phases and can make a correct run expire long after the
   click was completed. Conversely, the helper never records the `/crowley agent
   release` dispatch time or enforces the separate addon ten-second window before the
   Construct press (`tools/native_calibration_operator.py:1797-1799`). Fixed 2/8-second
   subprocess and ACK waits are not capped by the remaining published deadline
   (`tools/native_calibration_operator.py:748-814,843-874,921-950,1040-1087`). Finally,
   capture times are only written to the receipt; the pre-press path never rejects a
   template whose match/receipt/recheck work has aged past the five-second freshness
   bound (`tools/native_calibration_operator.py:1497-1579,1630-1642`). Track global and
   phase-specific deadlines separately, enforce `releaseDispatch + 10s`, cap every
   child/pipe wait by remaining time, and recheck capture age immediately before the
   press.

8. **The state-history implementation still cannot tolerate the transient states that
   motivated `stateHistory`.** `_await_state` succeeds only when the current tail
   equals the requested state (`tools/native_calibration_operator.py:1413-1426`). If
   Hold causes `updates_reset_archived` and the daemon reaches `measure_ready` before
   the next IPC poll, the validated history proves both transitions but `_chat` waits
   forever for the older tail (`tools/native_calibration_operator.py:1800-1806`). The
   same helper also takes no pre-dispatch history snapshot to prove that a requested
   post-state is causally newer (`tools/native_calibration_operator.py:1592-1616`).
   Accept a target proven in the immutable new history suffix, retain the current
   actionable tail, and bind post-action success to history appended after the actual
   submit boundary. Tests must advance on the injected submit, not on an unrelated
   recheck iterator.

9. **Terminal-error recovery is not implemented as contracted.**
   `_pause_after_terminal_error` checks only the old generation/state before pause and
   only `state == PAUSED` afterward; it does not require the newer generation,
   unarmed/idle Guardian, terminal operation, or no worker
   (`tools/native_calibration_operator.py:1730-1748`). It swallows failure and returns
   no new generation. The caller then attempts cancellation with the stale generation
   and exits; it never performs the admitted recovery handoff
   (`tools/native_calibration_operator.py:1825-1835`). Preserve the first native
   failure, require the complete newer PAUSED proof, adopt that generation, and begin
   the fixed recovery branch only after that proof. A failed pause must emit no chat
   or click and must remain visibly failed.

10. **Common runtime and receipt failures bypass required cleanup, while cleanup failure
    can still report success.** `receipt.begin()` is outside the protected `try/finally`
    (`tools/native_calibration_operator.py:1775-1780`), so a failure after creating the
    attempt but during its first write leaves the watchdog/tool open; `main` also skips
    its setup cleanup once `receipt.attempt` is non-`None`
    (`tools/native_calibration_operator.py:1966-1984`). The operational handlers catch
    only `OperatorError`, while production `DriverError`, `CalledProcessError`, and
    other boundary failures skip pause/cancel (`tools/native_calibration_operator.py:1831-1836`).
    Receipt writes inside an exception handler and `_flush_poll` can themselves raise
    before `input.close`, and an `input.close` failure on the successful path leaves
    `outcome="success"` and returns success (`tools/native_calibration_operator.py:1837-1848`).
    Put all acquired resources under one outer cleanup, normalize boundary failures,
    make receipt publication unable to suppress release/reap/revoke, preserve the
    first causal exception, and fail a nominal run when mandatory cleanup is
    unconfirmed.

11. **The durable receipt is not the required audit record.** `_source_bindings` hashes
    six imported modules and the producer binary, but omits the controller and daemon
    sources, addon/native source map, producer manifest, and local profile/config
    binding (`tools/native_calibration_operator.py:1897-1925`). Runtime events do not
    provide a precise pre/post input ledger, expected/current boot, daemon PID/start
    and profile binding, every admission/deadline result, terminal controller state,
    or cleanup/revocation result (`tools/native_calibration_operator.py:1128-1193`).
    Since actions are recorded only after dispatch, owner death can also leave no
    durable record that an input was attempted. Populate the closed receipt schema
    from the canonical binding and actual source artifacts, and durably ledger intent,
    dispatch, acknowledgement, release, and cleanup without storing private paths or
    environment contents.

12. **The focused tests do not exercise the promised production composition and hide
    the defects above.** The test named control-preflight actually constructs
    `MODE_RECOVER` (`tests/test_native_calibration_operator.py:430-450`), so the
    control-preflight mode is not run. The full sequence uses `FakeClient`,
    `FakeScreen`, and `FakeInput`; the client advances states on recheck calls and
    never publishes terminal `finalized` reservation state
    (`tests/test_native_calibration_operator.py:108-225,559-623`). The only subprocess
    emitter tests use `fork`, an arbitrary shell file, and no actual `Watchdog` or
    sealed `NativeReleaseSpec` (`tests/test_native_calibration_operator.py:504-557`).
    There is no production `main` setup/teardown, SessionIPC parser, profile environment,
    restore recovery, terminal pause/recovery, deadline edge, signal/SIGKILL,
    watchdog-ACK loss, late child, receipt-failure, ticket-revocation, or concurrent
    actor test. Replace orchestration fakes with the bounded production parser and
    actual acknowledged watchdog/pinned fixture composition, retaining injection only
    for clocks, captures, OCR, and explicit pinned artifacts.

## Should-Fix

1. **Calibration control replies are under-validated.** `_start_native_calibration`
   accepts any operation in `starting`/`running`, and `_await_calibration_terminal`
   accepts `complete`, without checking operation kind/generation or the expected
   controller generation/state (`tools/native_calibration_operator.py:1670-1712`).
   Require the exact native operation identity at start and every poll, then verify and
   record the expected terminal controller transition before reporting helper success.

2. **Receipt publication does not guarantee a complete durable write.**
   `ReceiptWriter.write` uses one unchecked `os.write` and fsyncs only the attempt
   directory (`tools/native_calibration_operator.py:1172-1193`). A short write can
   atomically publish truncated JSON, and the new attempt directory itself is not
   made durable in its parent. Write in a complete loop (or an equivalent bounded
   file API), verify the byte count, and fsync the receipt root after creating the
   attempt.

## Nits

None. The remaining findings affect reachable correctness, ownership, or required
evidence rather than style.

STATUS: MAJOR ISSUES
