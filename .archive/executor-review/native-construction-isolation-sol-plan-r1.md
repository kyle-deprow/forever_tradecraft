# Sol plan review R1 — native construction isolation

Plan reviewed: `.archive/PLAN-native-construction-isolation.md`

Verified SHA-256: `8b9fd740a252cf7319a8414d9557644936a199e618116befa77c2c2c089d2286`

Stage A is a safe, separable diagnostic slice. `LinuxProcStatusVmHwmReset5.finish_window` consumes the pending token, performs the final pinned-process reads, constructs and verifies the complete `NativeMemoryMeasurement`, and only then applies the unchanged limit at `src/crowley/session/calibration.py:1564-1611`. The proposed callback therefore cannot fabricate a measurement after a final-read or identity failure. The existing journal supplies the required private append-only substrate: deterministic `outcomeId` replay and conflict refusal at `src/crowley/session/journal.py:431-488`, and 0600 file publication with file and directory fsync at `src/crowley/session/journal.py:646-678`.

## Stage A — retain rejected measurements

### Must-Fix

None.

### Should-Fix

1. **Freeze the callback injection point and live binding checks in the implementation handoff.** The plan names the callback but leaves its route implicit (`.archive/PLAN-native-construction-isolation.md:30-43`). The two actual completion sites are `src/crowley/session/calibration.py:4539-4545,4625-4631`, while the daemon currently installs only the existing live hooks at `src/crowley/session/daemon.py:446-466`. The smallest four-file-compatible route is an optional typed rejection callback on `LinuxProcStatusVmHwmReset5`, supplied only by `SessionDaemon._ensure_native_memory_meter` at `src/crowley/session/daemon.py:967-990`; direct meters retain a `None` default. Before appending, the daemon callback should require `NATIVE_CALIBRATION`, call `measurement.verify()`, and match the measurement's PID, process start, executable, identity fingerprint, phase, and ordinal to the currently owned meter. Compute the exact existing failure string once and use that same value for both the archive and the eventual `CalibrationError`.

2. **Make the receipt derivation mechanically tied to the journal result.** `.archive/PLAN-native-construction-isolation.md:45-53` has the right payload and idempotency key, but implementation should define `measurement_sha256` as SHA-256 of canonical `measurement.to_dict()` JSON and construct the receipt from the object returned by `append_archive`, including its positive `archiveOrdinal`. `NativeMemoryMeasurementArchiveReceipt.verify()` should recompute the measurement digest and `outcomeId`, require the same ordinal and `durable is True`, and reject a wrong type or forged/mismatched receipt. Repeating the callback with the identical measurement must return the same ordinal; a conflicting payload with the same `outcomeId` must retain the journal's existing refusal.

3. **Keep archive-error reporting fixed and private.** When append or receipt verification fails, catch that diagnostic exception without changing or chaining it into the exact over-limit error. Record only a bounded fixed token through the daemon's private diagnostic channel; do not put an archive exception string, measurement, path, or receipt into `_native_handshake`, status, calibration evidence, or qualification counters. Add a production-wiring test for an invalid receipt as well as the planned append failure, and assert the original error text and nonqualification state in both cases.

### Nits

None.

**STATUS A: READY**

## Stage B — deferred Agent construction

Stage B remains deferred and is not required for Stage A.

### Must-Fix before any Stage B release

1. **Specify the SavedVariables/load-order state machine.** `Agent.lua` constructs the surface during file execution at `addon/Crowley/Agent.lua:517-522`; `ns.db` is not assigned until Core's `ADDON_LOADED` handler at `addon/Crowley/Core.lua:110-120`. The plan's “consume and clear before creating” wording at `.archive/PLAN-native-construction-isolation.md:84-90` therefore needs an exact sequence: inspect a strictly typed raw `CrowleyDB.nativeConstructionMode` before line 517 to decide whether construction is suppressed, retain an in-memory consumed token, then clear the persisted marker only after Core's earlier handler has installed `ns.db`. Define crash/reload behavior so a marker that was not durably cleared remains safely deferred, and prove the real TOC/load/handler order in the Lua harness.

2. **Name a real steady-world proof and construction trigger contract.** `.archive/PLAN-native-construction-isolation.md:91-104` currently delegates the decisive boundary to an unspecified “accepted visual proof” and operator action. Define the build-bound producer, closed evidence fields, identity/boot/scene/modal/character facts, freshness window, and daemon admission that establish the stable world immediately before reset. Also define who owns the single `/crowley agent construct` dispatch, how it is tied to the baseline-ready generation, and how the resulting publication proves that exact token was consumed. A sleep, zone string, ordinary crop, or unbound human assertion cannot establish this boundary.

### Should-Fix

None.

### Nits

None.

**STATUS B: NEEDS WORK (DEFERRED)**
