# Sol source review: native construction native R2

I reviewed the frozen candidate at
`/home/dev/.cache/crowley/worktrees/native-construction-native-r2-20261018`
against base `e6e17bb42474b0251365590e61b87c9307b447fe`, the complete Stage B R3
plan and closure amendment, the native implementation and operation-bound plans,
the entry map, and the R2 freeze/closure records. The review was limited to the
three owned production files and three owned test files, with their dependencies
read only. I made no candidate edit, ran no tests or builds, operated no GUI or
service, used no network, and performed no git mutation.

The supplied verification evidence establishes the frozen hashes/scope, scoped
static checks, 7 new focused tests, and the worker's 91 regression passes. The
parent's full three-suite run is **not green**: it stopped after 17 passes in an
unchanged compiled foreign-command guard, while the same two compiled tests pass
on main. I do not classify that failure as a candidate source regression, but it
also cannot be reported as full compatibility acceptance.

## Must-Fix

1. **The real configured native-region path cannot execute any PAUSED preflight
   or recovery capture.** `daemon.py:1073-1095` routes production construction
   observations through `_capture_native_frame_with_capture`, which reaches
   `_capture_native_region_for_identity`; when the pinned native region producer
   is enabled, `daemon.py:3160-3167` rejects `PAUSED` before dispatch. Control
   preflight requires `PAUSED` at `daemon.py:1223-1227`, recovery-begin requires
   it at `daemon.py:1380-1383`, and recovery-complete repeats that requirement at
   `daemon.py:1479-1482`. The added tests bypass the conflict by installing
   `_native_construction_observation_provider` (`test_session_native_regressions.py:4045-4047`
   and `4248-4250`). Consequently the production preflight and both production
   recovery phases fail before they can capture evidence whenever the accepted
   region adapter is configured. Pass an explicit, generation-bound expected
   state into the owned native capture admission and permit the region observer
   in exact `PAUSED` only for a live preflight/recovery reservation; cover the
   real configured capture adapter rather than the fixture-only provider.

2. **The promised single-owner admission is not linearized, and its lock order
   can deadlock an operator pause.** Construction methods hold
   `_native_construction_lock` and then enter the controller (`daemon.py:1216-1224`,
   `1378-1383`, `1466-1482`). `Controller.pause` holds the controller mutex while
   calling Guardian revoke (`controller.py:2069-2082`); the registered revoke
   callback then takes `_native_construction_lock` and writes the controller
   checkpoint (`daemon.py:814-829`). A pause racing a recheck, prepare, or
   recovery capture can therefore leave each thread waiting on the other's lock.
   The same ownership boundary is bypassable: legacy `native_bootstrap` is
   dispatched without a construction admission check (`cli.py:197-210`), and
   `start_calibration` checks the reservation at `daemon.py:868` but publishes
   `starting` only afterward under a different lock at `daemon.py:870-883`, so a
   prepare can race through its reciprocal check. Recovery admission also omits
   the required non-interaction-mode and active-calibration-operation checks
   (`daemon.py:1380-1405`). Establish one linearization point for prepare,
   legacy/deferred bootstrap, calibration, interaction/diagnostic admission, and
   recovery; do not call controller or Guardian blocking/revoke paths while
   holding the construction lock; and revalidate mode, operation, ticket, lease,
   identity, state, and generation after every blocking capture. Add barrier
   tests for pause-versus-recheck and prepare-versus-legacy-bootstrap/calibration.

3. **Deferred bootstrap is not a single atomic consume.**
   `native_construction_bootstrap` verifies the ID/kind/boot but never requires
   `reservationState == "prepared"` or predecessor
   `construction_prepared` (`daemon.py:1307-1320`). A duplicate call with the
   same returned values is accepted, rewrites the state to `running`, clears the
   finalize event, and resets the outer deadline to `now + 3130` at
   `daemon.py:1321-1331`. That both extends a non-refreshable deadline and can
   regress an in-flight handshake. Require the exact predecessor and make every
   repeated/skipped consume revoke local admission while preserving durable B0 as
   `recovery_required`; test a duplicate immediately after consume and during the
   runner, asserting that the original deadline never moves.

4. **Any decoder failure is treated as proof that Agent is absent.** In
   `_native_construction_capture`, every `ProtocolError` becomes
   `surface="absent"` (`daemon.py:1091-1109`). A corrupt CRC, malformed/stale
   CRS1 grid, unsupported frame, or genuinely ordinary pixels all take that same
   branch. Recovery-begin then accepts the result as the no-Agent case at
   `daemon.py:1410-1414`. The existing legacy bootstrap already demonstrates the
   required distinction by inspecting and rejecting an encoded but malformed
   surface (`daemon.py:1587-1623`). Reuse one strict absence classifier for the
   construction path: ordinary non-grid pixels may prove absence, while any
   encoded-looking or malformed Agent publication must refuse recovery. Add
   actual image tests for ordinary absence, bad CRC, malformed schema, and stale
   encoded grids.

5. **The finalize boundary neither enforces its 30-second hook nor proves a
   post-admission publication.** After the runner reaches `resume_ready`,
   `run_native_calibration` waits for `_native_construction_finalize_event` until
   the 3130-second outer operation deadline (`daemon.py:5915-5925`); no
   30-second finalize-hook deadline is created. Finalize-admit later creates only
   its ten-second action deadline (`daemon.py:1363-1372`). The accepted final
   frame is checked for normal/0, boot, and fence, but never for a sequence newer
   than the resume observation or a capture time after finalize admission
   (`daemon.py:5929-5966`). Thus a late admission can remain valid for most of the
   outer envelope, and an already-visible frame can satisfy the transition. At
   `resume_ready`, record the exact resume sequence/capture and a finite
   `now + 30` hook deadline; finalize-admit must occur before that boundary and
   publish `min(hookDeadline, now + 10)`; the final observation must be strictly
   newer than resume and captured after admission before frame rebind and
   `native_calibrated`. Cover just-before, exactly-at, and just-after both
   deadlines plus a same-sequence/pre-admission negative.

6. **Recovery completion is not crash-safe at its durable write boundaries.**
   The method durably rebinds the new ordinary frame, writes it again through
   `observe_frame`, and only then clears B0 in three separate journal writes
   (`daemon.py:1507-1524`). A crash after either of the first two writes leaves a
   fresh owner with durable `recovery_required` plus the new ordinary boot on
   screen. Restart recovery accepts only absence, the prefixed construction boot,
   or the old B0 armed case (`daemon.py:1410-1422`), so it rejects that already
   proven new ordinary boot as unrelated and can never clear the checkpoint.
   Moreover, the ticket omits the begin sequence and lease facts
   (`daemon.py:1446-1455`), and completion never proves its capture monotonic time
   is later than begin. Add a controller-owned closed recovery commit that writes
   the validated frame trio and checkpoint removal atomically, then passes that
   same trio through `observe_frame`. Persist/validate the complete begin
   evidence and inject failures at every journal boundary with a fresh
   Controller and daemon to prove each state remains recoverable.

7. **No public private-IPC path can observe the required terminal `finalized`
   state.** The worker sets `_native_construction_handshake` to `finalized` and
   clears the reservation in the same locked block (`daemon.py:5977-5985`), while
   recheck requires the live reservation (`daemon.py:1334-1343`) and public
   status deliberately exposes only the legacy handshake (`daemon.py:7055-7097`).
   The composed test succeeds only by inspecting the daemon's private attribute
   (`test_session_native_regressions.py:4397`). A helper using the closed CLI/IPC
   contract therefore cannot record the twelfth state. Recovery-complete and
   cancel also discard the canonical record before returning and reply without
   the required `reservation`/native-clock shape (`daemon.py:1522-1533` and
   `1535-1552`). Preserve a bounded, non-admitting terminal record long enough
   for the exact reservation-bound recheck/ack, and return the canonical record
   in completion/cancel replies before cleanup. Test the terminal states only
   through `SessionIPC.dispatch` and the real parser request shapes.

## Should-Fix

1. **JSON `null` silently becomes checkpoint absence.** Controller load uses
   `value.get("nativeConstruction")` and treats `None` as a missing record
   (`controller.py:206-221`). A persisted `"nativeConstruction": null` is an
   invalid shape, but the next `_save` removes it at `controller.py:1020-1024`,
   allowing new preparation instead of failing closed. Distinguish key absence
   from a present null value and preserve the latter verbatim as invalid; add a
   fresh-owner null regression alongside the extra-key case.

2. **The deferred absence path mixes clocks, and the CLI can time out before a
   valid daemon reload-bound operation.** Reused `native_bootstrap` stamps its
   capture with `time.monotonic()` (`daemon.py:1581-1585`), while deferred
   freshness is evaluated with `self._native_clock()` (`daemon.py:2132-2137`).
   Use the one injected native clock throughout. Separately, every construction
   CLI command receives a fixed 60-second socket timeout (`cli.py:1025-1035`),
   although prepare/recovery use the configured reload deadline through 600
   seconds (`daemon.py:1247` and `1406`; `config.py:176-180`). With a valid
   deadline above 60 seconds, the client can report indeterminate timeout while
   the daemon later creates an unreachable reservation/checkpoint. Derive the
   transport bound from the applicable configured operation plus its existing
   margin, and test the allowed upper configuration boundary.

3. **The durable preconstruction proof does not record successful capture
   deletion.** `_native_bootstrap_proof` copies the path/hash/identity/time before
   the runner deletes the PNG (`daemon.py:2178-2198`); `release_native_capture`
   updates only the process-local handshake (`daemon.py:2289-2295`), which is
   later replaced by the short `finalized` record. The controller therefore
   archives no explicit deletion/clear result even though the closure requires
   the metadata and successful deletion fact to survive. Update the durable
   proof after release and assert after fresh controller reconstruction that the
   metadata remains, the deletion result is true, and the path is absent.

4. **The added tests cover a happy sequence rather than the closed acceptance
   surface.** Only two IPC shapes are exercised in
   `test_session_transitions.py:179-208`; the main callback test manually advances
   private callbacks (`test_session_native_regressions.py:4042-4163`), and the
   composed runner replaces the production capture boundary
   (`test_session_native_regressions.py:4291-4355`). There is no all-twelve-state
   wrong-edge matrix, exact parser coverage for all eight commands, real
   telemetry-region PAUSED capture, duplicate consume, restart at each durable
   recovery write, lock/barrier race, interaction-mode recovery refusal, corrupt
   absence image, or public terminal-state proof. Add those focused negatives;
   they are the shortest way to prevent the source failures above from passing
   another happy-path-only run.

## Nits

None.

The corrected 3130-second outer envelope itself matches the operation-bound
amendment, and legacy `native_bootstrap` remains a distinct request shape. Those
points do not close the production admission, finalize, and durable-recovery
defects above.

STATUS: MAJOR ISSUES
