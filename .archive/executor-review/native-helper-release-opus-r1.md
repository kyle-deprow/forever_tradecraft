Model ID: **claude-opus-5-5**

This was a read-only review: no edits, tests, GUI, config, service or git changes. I compared the two files against the composition worktree, and read Lua behavior from the d8 addon in `helper-addon-parent-composition-20261019`. That addon differs from the one in this worktree; the helper files are byte-identical.

## Previous findings: status
- **Sol Must-1 (pause response contract): fixed.** `tools/native_calibration_operator.py:3748-3793` now checks the immediate controller reply (PAUSED, newer generation, higher `leaseGeneration`) and then reads aggregate status. The `measurement-failure` case runs this through the real `Operator.run` and keeps the original error and the failed receipt.
- **Sol Should-1 (deadline): mostly fixed.** `operationDeadline` now uses `min` at `:3045-3052`, and the daemon sets it only once (`daemon.py:2259`). Problems remain; see Should-Fix 3.
- **Sol Should-2 (allocation hardening): code fixed, no tests.** The emitter abort, the Watchdog owner-start check and the cancellation FD whitelist are correct. The spawn always passes 10 arguments, so indexes 2/3/4/9 are valid.
- **Sol Must-2 and Must-3: only partly fixed.** Details below.

## Must-Fix
1. **`recover-restore` never runs restore** (`tests/test_native_calibration_operator.py:3790-3795`, `3648-3654`, `4540-4550`).
   - The compositor serves fixed payloads 0, 1 and 2 for the first three area captures. So the first `recovery_begin` capture is the B0 baseline with its fence inactive, and the daemon picks `ordinary_reload` (`daemon.py:2491-2495`).
   - `initial_payload_index` has no effect, and `restore_live` is never touched. The two recover cases take nearly the same time (18.37s vs 18.50s), which supports this.
   - **Fix:** serve the restore frame first, and assert `recovery_begin.kind` in both recover cases.
2. **`control-preflight` passes only because the fixture changes the scene itself**:
   - `agent defer` swaps in the post-reload `deferred` VM even though no reload happened (`:4294-4298`).
   - The helper's **construct** click is turned into a Lua Restore click, which Lua refuses (d8 `Agent.lua:622`). The fixture then swaps to `recovery_ordinary` anyway (`:4336-4357`).
   - `recovery_begin` sees the fixed "absent" payload #2.
   - `/crowley agent recover` and the Restore click both land on `recovery_ordinary`, and Lua refuses both (d8 `:561`, `:622`).
   - **Fix:** pick the click role from the dispatched pointer position, and change scenes only after Lua actually accepts an action.
3. **Post-success recovery uses a scene swap that no input caused** (`:4579-4584`).
   - After success, the finalized client still shows boot `native-construction:B0`. The checkpoint is set only at prepare (`daemon.py:2158-2165`), so the real daemon would pick **restore** (`:2475-2490`).
   - The real path (`/crowley agent recover` plus Restore on the finalized client) is therefore never exercised.
   - The pause at `:4571` calls the controller in-process, not public IPC, and nothing checks that the lease/Guardian generation advanced.

## Should-Fix
1. **`pressed-budget` fails earlier than its name says** (`:4481-4496`).
   - It refuses in `OwnedEmitter.__init__` (`:1230`) before anything is spawned. By then the chat-open Return has already been sent physically, and the injected deadline skips `_chat`'s whole-sequence budget check (`:3379-3388`).
   - The READY/watchdog/GO/PRESSED budget checks (`:1299`, `:1416`, `:1463`, `:1544`) are never reached.
   - None of the negative cases assert an empty action log or `reservation_cancelled`.
2. **Receipt hash checks prove nothing** (`:4626-4633`). They only check the 64-hex format, and the dependencies are passed in by the test itself.
   - Compare against the real template, producer, config and `gated_tool.digest` hashes, plus the R10d native module hashes.
   - The fresh operator also binds the old `screen` (`:4605`).
3. **The constructor click bound can still be widened** (`:3053-3060`). The phase deadlines are still overwritten on every reply.
   - Each `_recheck` inside `_click` (`:3439`/`:3446`/`:3451`) replaces the helper's release + 10s constructor bound (`:3435-3436`) with the daemon's provider start + 23s (`daemon.py:3846-3861`). That is past Lua's 10s release window.
   - **Fix:** take the minimum per key. Also add a direct test of the method, which the plan asked for.
4. **No tests for the new hardening branches** (`:1288-1290`, `:1600-1602`, `:1158-1197`). The X11Screen/OwnedEmitter/Watchdog/CancellationActor failure matrix from plan step 3 is missing.
5. **Recovery reloads don't use the real SavedVariables** (`:3566-3582`). They switch to clients booted from the pre-defer SavedVariables, not the ones written by the Restore/Finalize the helper dispatched.
   - As a result, d8's `restore_pending` path (first publish with the fence armed, then inactive) is never exercised.
   - The parent's 73 passing tests therefore say nothing about d8's restore readiness.

## Nits
- The aggregate `guardian` check (`:3777-3781`) can never trigger: `status_dict` has no `guardian` key, and `from_record` already rejects an armed Guardian (`:313`). The closure report's "aggregate Guardian unarmed" claim overstates what this check does. The new check in `_recover` (`:3809-3816`) only repeats `_adopt_handoff` (`:3105-3108`).
- `:4616-4617` only restate facts set up before the run. Assert the committed recovery boot and `reload_count` instead.

I also wrote these findings to `/home/dev/.claude/plans/read-only-scoped-final-helper-atomic-hartmanis.md`.

STATUS: NEEDS WORK
