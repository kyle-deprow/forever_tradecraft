# Native memory measurement clarification

This replaces the earlier Lua transient-peak requirement and lifetime-HWM
subtraction in PLAN-repeating-scans.md. It changes the measurement method, not
the scan, takeover, coverage, cadence, or performance limits.

## Verified basis

Linux documents VmHWM as peak resident memory and clear_refs value 5 as resetting
that counter to current RSS. Its /proc/status accounting is approximate. See
[kernel documentation](https://www.kernel.org/doc/html/latest/filesystems/proc.html).
The [Lua 5.1 manual](https://www.lua.org/manual/5.1/manual.html) defines
collectgarbage("count") as current Lua-managed memory, not an allocator peak.

The sole Luna host operator verified reset5 on the exact owned WowB process,
kernel6.14.0-37-generic, with PID/start/executable/UID rechecks and a pinned proc
directory fd. Historical HWM was archived and fsynced before the one write.
HWM changed from4509608KiB to3018112KiB, with RSS3016416KiB. Evidence:
`~/.local/state/crowley/native-preflight/clear-refs-20261016T012018.550632Z-pid3509666.jsonl`.
This proves host capability only; it is not a construction or acceptance run.

## One authoritative resource method

Use `linux_proc_status_vmhwm_reset5` for two separate controlled windows:

1. Verify exact process/start/executable/window/Wine identity and Agent absence.
   Persist historical HWM/RSS, write exactly5 to that pinned process clear_refs,
   read post-reset HWM/RSS, then publish bootstrap-ready. After normal operator
   bootstrap, capture construction and require growth <=128MiB.
2. Hold Agent publication, prove a fresh held frame, preserve HWM/RSS, reset5
   again, read the second baseline, then release exactly100 one-Hz publications.
   End held and require HWM growth <=16MiB. Check identity at every boundary.

Never subtract a lifetime HWM or construction HWM from later lifetime HWM.
Do not require exact HWM/RSS equality. Reject unavailable/reset-denied capability;
there is no RSS-polling or net-delta fallback. Never use proc/mem, memory maps,
allocator injection, or unrelated process accounting. A reset changes accounting
only and discards historical HWM, so retain that value before every write.

Seal kernel release, method, PID/start/identity and each phase's historical HWM,
RSS before reset, completed reset timestamp, post-reset HWM/RSS, workload start/
end times and ordinals, final HWM/RSS, growth, and limit. Archive the complete
measurement dataclass, not a subset of fields. This bounds whole-process resident
growth within approximate kernel accounting; it does not attribute bytes to the
addon or include VRAM, swapped pages, or other Wine processes.

## Fixed telemetry schema

Render retains constructionSeconds, updateCount, updateP99Ms, textureCount,
effectiveScale, cellSize. Replace all luaTransient/Peak fields with:

- `luaHeap`: exact object `{method, available, beforeKiB, afterKiB, netKiB}`.
  Method is always `collectgarbage_count`; samples describe the last completed
  publication, with net=after-before. Available samples are finite; before/after
  are nonnegative and net may be negative. If the exact API is unavailable, emit
  available=false and all three numeric sentinels0 (unknown, not an estimate).
  Availability is diagnostic, not the resource gate. Leave GC behavior unchanged;
  remove isrunning/stop/restart/hooks and artificial peak witnesses.
- `nativePhase`: `normal`, `held`, or `updates`.
- `nativeOrdinal`: integer0..100. Normal has0. Held has0 before the update window
  or100 after it. Updates has1..99; the hundredth frame is held/100.

There is one schema and one diagnostic API; no compatibility aliases.

## Executable operator handshake

Agent normally publishes as before. Add exact diagnostic commands:

- `/crowley agent hold`: hold normal publication and publish one held/0 frame.
- `/crowley agent measure`: only from held/0, publish update1 and continue at1Hz
  through100; publish the last frame as held/100 and stop automatically.
- `/crowley agent resume`: restore normal publication, ordinal0.

These commands are for the sole authorized bootstrap operator while the controller
is unarmed, not cadence input or anti-AFK. Keep them out of the runtime command
allowlist. After construction, expose an operator-visible hold-required signal;
wait for actual held/0 pixels before the second reset. After that baseline is
durable, expose measure-ready. Count and retain exactly100 fresh same-boot
observations with matching ordinals. Missing/skipped/old frames fail the gate.
After the final measurement, expose resume-ready; normal publication must resume
before the input gate. No undefined callback or assumed operator action.

The native owner owns runner/meter/evidence and driver hooks; the main engine
owner owns actual provider/status integration and archive serialization; the
auxiliary owner owns Agent/commands/harness. Agree exact callback signatures
directly and publish them early. Existing file fences remain exclusive.

## Checks

Use an actual owned harmless child with a controlled allocate/free burst to prove
reset HWM preserves a transient after RSS falls; verify separate resets, identity
changes, denied writes, durable historical records and failure cleanup. Harness
tests prove100 exact updates/hold/resume, normal cadence unchanged, unavailable
and constant Lua counters honestly diagnostic, and no GC-state mutation. Strict
schema/negative tests and parent/Sol review precede real native acceptance.

## Confirmed live default-meter wiring correction

Actual deployed daemon now proves the no-Agent boundary, then native-calibrate
fails `native reset5 memory meter is not configured`. SessionDaemon's default
DesktopDriver leaves native_memory_meter=None; tests injected meters manually.
No baseline reset, Agent enable or new sweep occurred.

Luna owns only daemon.py, calibration.py, tests/test_session_runtime.py and
tests/test_session_native.py for this correction. Driver/controller/journal/
config/protocol/addon/other tests/docs and live config/services/data/game/git
are read-only. Preserve the final reviewed parser, timing, reset receipts,
PID identity checks, meter-failure cleanup and 100-update admission logic.

Wire the sole LinuxProcStatusVmHwmReset5 method into the actual default daemon
native operation using fresh verified live identity, actual Linux executable,
start ticks, UID and pinned proc-directory descriptor. Never confuse Windows
identity.executable with /proc/PID/exe. Create/open only on the verified target,
retain ownership through operation completion/cancel/failure, close owned handles
reliably and require fresh identity on retry. No unsafe eager process selection,
profile meter knobs, copied metrics, fallback or live kernel writes in tests.
Injected fixture meters remain test-owned; do not close foreign ownership.

Add a regression exercising default production construction/entrypoint without
manually assigning driver.native_memory_meter; prove actual native operation
receives an identity-bound meter and release on success/failure/retry. Use an
owned harmless child/disposable proc fixture as appropriate, never the game.
Keep externally visible handshake failure truthful when operation errors before
the first baseline (no perpetual 'running' after calibrationOperation error).
Run relevant native/default-wiring tests and complete runtime tests under private
CROWLEY_DESKTOP_LEASE and three strict warnings, Ruff/format/compile/diff. Freeze
DONE; independent narrow Sol review and parent reproduction before live retry.

The same production-path correction must cover distinct executable channels:
real WindowIdentity.executable is Windows `WowB.exe`, whereas the meter verifies
actual Linux `/proc/PID/exe` wine-preloader path. Current sealed native evidence
wrongly compares those directly; existing harness hid this by putting its Linux
helper path into WindowIdentity.executable. Bind both channels correctly with
PID/start/fingerprint and pinned Linux meter identity retained; test distinct
Windows and Linux values through completed sealed evidence. Do not disguise the
live window executable or relax process identity checks.
