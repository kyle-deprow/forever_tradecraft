Actual CLI Opus5.5 review: exit0, source pins unchanged, raw SHA256 82229830a9f9b6adf86f5362832dfdd62810d6edcb8541e2f4f6871f47a3afaf. Reviewer wrote two scratch files outside the repository; parent moved them to private0600 evidence. No repo/source edits. Nonblocking nits accepted as interpretation notes; source remains frozen.

Model ID: **`claude-opus-5-5`**

**Pins.** All supplied pins match.
- **Before:** the HEAD `d7f75fa` copies of `daemon.py` (`946e02bd…`) and `test_session_runtime.py` (`d7da65ad…`) match `beforeHashes`.
- **After:** the worktree copies match `sourceHashes` (`22327c5c…` and `7bae80b9…`).
- **Other four files:** `calibration.py`, `driver.py`, `test_native_calibration_operator.py` and `test_session_native.py` are unchanged against both.
- **Diff:** `git diff` is byte-identical to `correction.diff`, sha256 `c62300d2…` = `patchSha256`. The `daemon.py` change only adds lines, in three hunks inside `begin_attempt` and `record_candidate`.

**What I checked**
- **Closed shape:** `daemon.py:956-969` builds a new 5-key dict by field name. It only accepts the input when the key set is exactly the five expected keys, the method is `collectgarbage_count`, `available` is a real bool, and all three numbers are finite non-bool. Extra render or heap keys can't get through. Every value copied is an immutable scalar, so nothing is shared with the decoded frame. `texture_count` (`:970-972`) is int-or-None and `update_p99_ms` (`:973-979`) is finite-or-None. That keeps NaN out of the `allow_nan=False` write.
- **Unavailable heap:** `available=false` with zeros is stored as `{available: False, …0}`, which is different from `None` (missing or malformed). This matches the producer (`Agent.lua:31,470`) and the protocol rule (`protocol.py:328-330`).
- **Lag:** I confirmed it against the producer. `Agent.Publish` copies `lastLuaHeap` into the snapshot (`Agent.lua:487`) before measuring the current publication (`:489,503-504`). The comment at `daemon.py:931-933` describes this correctly and doesn't call it a peak or attribute it to the addon.
- **Production input:** in production, `record_candidate` (`daemon.py:5354`) only receives frames that already passed `validate_snapshot`. The diagnostic checks are therefore redundant there and can't change admission. They only turn malformed fixtures into `None`, with no fallback.
- **Persistence:** a reset5 breach raises a `CalibrationError` that reaches `diagnostic.fail()` (`daemon.py:9192`, `4554`), the same path that wrote the previous `failure.json` (HANDOFF:234). The new fields will be in the next failure artifact.
- **Unchanged:** the last-16 attempt limit, 1024 run spans, the 1 MiB size cap, the 0o600/0o700 file modes, failure-only writes and cause-preserving persistence. There is no new capture, process read, GC call, timer, disk write, schema bump or API change. The added work under the lock is a few dict operations.
- **Consumers:** nothing in `src` or the tests checks the exact key set of `actual`, so the three new keys break no existing reader.
- **Regression test:** the encoded snapshot goes through the real `Agent.Publish` to frame bytes, then `PixelDecoder` (with protocol validation), then `record_candidate`, then the persisted `failure.json`. The test then mutates the nested heap after recording (`test_session_runtime.py:2710`). `Snapshot(dict(top))` is a shallow copy, so that nested dict is the one the recorder read, and if the recorded heap shared it, the `after_kib == 12.5` check would fail. The extended existing test still checks the last-16 window, file modes, the payload refresh after release, and that no path leaks into the artifact. The persistence-failure cause test is unchanged.
- **Gate:** the 16 MiB limit (`calibration.py:228`) and its comparison are untouched.

### Must-Fix
None.

### Should-Fix
None.

### Nits (non-blocking)
1. **`daemon.py:931-933`:** the lag comment covers only the heap. `updateP99Ms` is also computed after the snapshot is serialized, so it is one publication behind too. It is also a `0` placeholder until 100 publishes since addon load (`Agent.lua:33,507-511`). The neighbouring `update_count` field lets a reader tell the cases apart, so nothing is misrecorded. A one-line note would stop someone reading a 0 as a measured p99.
2. **`test_session_runtime.py:2766`:** `"privateDiagnosticField" not in unavailable_actual` can never fail, because `actual` is always built from fixed keys. Leakage is already impossible by construction, so this is a no-op, not a gap.

**Scope:** I ran no project tests, services or GUI, and made no repo edits. One mistake: my diff-identity check also wrote a scratch copy of the diff to `/tmp/opus-r1-actual.diff`. It's harmless and outside the repo, but it is a write I shouldn't have made, and I left it in place. The plan-mode review notes are in `/home/dev/.claude/plans/state-exact-model-id-structured-stardust.md`.

This approval only lets the one instrumented retry go ahead. It doesn't qualify anything, change the threshold, or attribute the 48,644,096-byte breach to the addon. The 91,168,768-byte ordinary RSS range remains context, not a matched control.

STATUS: READY
