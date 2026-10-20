# Native observer: close accepted review requirements

The previous R1 correction was too broad for one worker and its completion map
omitted accepted requirements. This plan partitions the SAME thirteen files into
two disjoint owners. No new feature scope, dependencies, public IPC/telemetry
schema, calibration/decoder/Guardian/input-tool/addon edits or relaxed guards.
Root owns Git, docs, integration, installation and private evidence. No live GUI,
capture, IPC, services, configs, DB or game actions from either coding worker.
Do not commit/reset/stash/revert others. Keep source frozen until assigned.

Read `.archive/PLAN-native-identity-observer-review-r1.md`, original plan and the
compact client-contract skill. All earlier arbitrated deferrals still apply.

## Ownership and private protocol agreement

Owner A (`luna_rust_matcher`) owns ONLY:
`src/crowley/session/{config,daemon,driver}.py`,
`tools/native_calibration_operator.py`,
`tests/test_{native_calibration_operator,session_driver_actions,session_native,session_native_regressions}.py`.

Owner B owns ONLY `native/x11_identity_observer/{Cargo.toml,Cargo.lock,src/main.rs}`,
`tools/build_x11_identity_observer.py`, `tests/test_x11_identity_observer.py`.
No dependency downloads or lockfile dependency changes.

Private observer protocol: exact integer `protocolVersion:1` in request and all
success/error records, strict missing/wrong/type refusal. Existing process exit
code remains explicit success/failure status. Coordinate one typed `timingsNs`
success object with measured `proc`, `x11`, `total` unsigned integer durations.
Label nested/overlapping measurements honestly; do not invent additive totals.
A records parent spawn/write/drain/decode/total spans, carries Rust timings through
the exact existing caller/span/thread-bound observation evidence. Neither owner
edits the other's files; send schema/helper coordination directly to each other.

## Owner A: runtime, provenance and composed evidence

1. Unify request/write/drain/decode cleanup: always close all child pipes and reap
   owned processes on early write failures while preserving the causal error.
   Barrier-test close versus invoke and FD reuse; test failed Guardian/lease
   construction for zero observer FD growth. Keep bounded shutdown/deadlines.
2. Strictly validate helper observer manifest: private ownership/mode, no symlink,
   stable descriptor/path read, exact schema and source set, binary binding, and
   independent hashes of CURRENT reviewed repository bytes. Reject source/schema/
   mode/symlink/owner mismatches. Do not copy expected hashes from that manifest.
3. Positive `SessionDaemon(config)` with real valid observer pins/default
   `DesktopDriver(backend=None)`, no replacement of production factory.
4. Real published/sealed observer faults separately at backend-pre/backend-post/
   runner-post. Assert pre has zero producer dispatch, later faults reject and
   release owned capture, then restore real facts and prove fresh success.
   Preserve exact three causal invocations/nonces and all existing guards.
5. Diagnose parent current two failures from actual retained replies, not labels:
   success is BadWindow X_QueryTree resource0x400001; recovery_complete expired.
   Preserve fail-closed handling. Coordinate X11 fix with B. Correct modeled
   recovery/producer lifecycle and thread cleanup without stretching production
   deadlines or synchronizing the independent publisher to consumers.
6. Retain numerical per-call/per-boundary artifacts outside rotating pytest dirs.
   Compare total spans with retained gen46 aggregates215.202077/348.341799/
   335.649884ms. Historical substage/global topology were NOT retained. Actual
   raw process-count artifact is614; any >=646 stress is named conservative,
   not exact replay. Preserve max active<900ms and independent1Hz updates1..99,
   held100/resume0. Keep real same-actor forced finalize race and negatives.

## Owner B: observed facts, parity and hermetic publication

1. Implement strict wire version and measured Rust timing fields above.
2. Handle real X11 transient-window errors without default Xlib process abort.
   Reference-equivalent handling of unrelated vanished windows; relevant target/
   uniqueness/tree uncertainty refuses as bounded structured errors. Add actual
   transient-window regression. No server grabs or input/mutation of X state by
   the observer, no caching/fallback or skipped target validation.
3. Exact reference title semantics: `_NET_WM_NAME` then `WM_NAME` and accepted
   property types. Preserve absent active0, canonical/non-strict prefix/loader,
   both distinct WM_CLASS values, descendant/fully verified identity counting.
   Assert full production `WindowIdentity`/fingerprint parity on actual Xvfb
   cases, including unnamed client. Do not narrow reference acceptance.
4. Barrier-controlled actual process lifetime disappearance/replacement between
   initial and final facts; refuse mixed lifetime, then fresh restored success.
   No mocked returned facts or production test-only acceptance hooks.
5. Complete builder accepted hardening/tests: exact source allowlist including
   symlink negatives, stable snapshots, ambient Cargo refusal, neutral/offline
   tools, source/static/linker bindings, private durable atomic publication,
   different-byte overwrite refusal. Set manifest temporary mode0600 BEFORE
   replace. Keep generated targets private/out of source before final freeze.

## Verification and completion

First decisive small regressions; then isolated failing composition nodes with
`-x` until each passes. Do NOT repeatedly run all9 while failures are known.
Coordinate intermediate protocol changes before integrated runs. Each owner
reports an itemized covered/missing map with exact tests, results and retained
artifact paths. No generic green total substitutes for a listed requirement.
A owns the final integrated all9, fresh observer/driver/full-native group, real
same-actor race, affected runtime/constructor groups and scoped static checks;
B owns Cargo offline/locked, rustfmt, Xvfb and actual hermetic double-build.
Freeze source only after all requirements map to real evidence; retain exactly
the approved13 hashes INCLUDING daemon, plus separate unchanged runtime evidence.
Root independently checks final diff/build/tests, then Sol and actual CLI Opus
review the same pins. Neither offline proof nor later pass closes historical
failures without original causal evidence. DONE only when the assigned phase is
complete; no live qualification or full broad-suite claim from partial results.
