# Native throughput correction — bounded Sol architecture proposal

Status: **APPROVED FOR BOUNDED IMPLEMENTATION** under the user’s instruction to proceed and prior authorization to rewrite measured computation bottlenecks in Rust. Parent accepted Sol’s scoped architecture after independent failure/frame verification and private equivalence measurements. This is read-only architecture work against MAIN production commit `a2c655b2e9ad2b284484378179793749b810728a` and the installed production hashes recorded below. Implementation is authorized in an isolated checkout only. Root owns promotion after parent verification, Sol and actual CLI Opus approval. No new live attempt is authorized by this source plan.

## Evidence and decision

Generation 46 is a throughput miss rather than a protocol acceptance defect: requested `updates/4` captured valid `updates/5` after the publisher advanced by 2009 ms. On accepted ordinal 3, the three fresh full identity passes cost 215.202 ms, 348.342 ms, and 335.650 ms; provider decode cost 91.291 ms, cell validation 73.860 ms, runner decode 83.606 ms, and the admitted producer's ACK-to-return interval was only 43.716 ms. The full attempt ended after 1.380 s. Source bindings were unchanged and sequence/CRC/ordinal checks rejected the skipped frame correctly.

Removing only one identity pass would leave approximately 1.044 s of measured work and would discard a distinct temporal guard. Combining provider and runner decode without a separately reviewable equivalence proof would likewise weaken independent evidence. The smallest credible correction is therefore to preserve the backend-pre, backend-post, and runner-post boundaries but replace each `X11Backend.resolve_identity()` fanout with one fresh, pinned Rust observer invocation. Each invocation must perform all current process/window observations anew and return facts; Python remains responsible for the existing profile checks and fingerprint. There is no cache, fallback, retained identity result, or change to daemon/calibration call count.

The current Python process scan should also stage its exact `cmdline` discriminator before reading `stat`, `status`, `exe`, and `environ` for candidates. This is semantic-preserving and useful as a reference implementation, but it is not an independent release: the measured result must include the batched observer because `/proc` alone was about 68.8 ms over 646 processes and cannot close the demonstrated budget.

## Exact observer contract

Add a private component `native/x11_identity_observer` and hermetic builder patterned on the accepted template matcher. Build twice from a stable three-file source snapshot with the exact reviewed Rust toolchain, offline Cargo home, neutral cwd/environment, remapped paths, byte-identical release output, a private atomic publication, and a manifest containing the binary and all source hashes. Because direct X11 access cannot use an unreviewed Cargo download, use explicit FFI against locally snapshotted static X11/XCB link inputs; the builder must hash and copy every static archive/linker input into each private build snapshot and record their digests and the exact linker version in the publication manifest. No dynamic plugin or runtime-loaded observer dependency is allowed.

Add two optional private `DriverProfile` fields for the observer's absolute binary path and lowercase SHA-256. `load_config` accepts only both or neither and validates an explicitly supplied pair exactly as it does the telemetry producer. Keeping the pair optional at the data-class/config layer avoids changing fixture-only configs and non-X11 backends; it does **not** select a runtime fallback.

Use an explicit dependency/factory boundary:

- `X11Backend.__init__` retains the current Python resolver as the reference/test implementation and never auto-selects based on whether pins happen to exist. Existing fixture-heavy direct constructors therefore keep their exact behavior and do not need edits across the session suite.
- Add `X11Backend.production(profile, *, input_tool=None)`. This is the only production constructor. It requires both observer pins, opens/verifies/seals the observer, injects a `PinnedX11IdentityObserver`, and fails construction on any missing/bad pin. It must close the input-tool image and observer FD on partial construction failure.
- `DesktopDriver(..., backend=None)` must call `X11Backend.production(self.profile)`. An explicitly injected backend remains a deliberate test/dependency seam. The daemon's existing default `DesktopDriver(profile, ...)` therefore cannot start with a reference resolver or absent pins.
- Change production `X11Screen` in `tools/native_calibration_operator.py` to call `X11Backend.production(...)`. Thus the standalone helper also refuses before screen/input operation if the pin is absent or invalid.
- Store the selected resolver kind on the backend (`"reference-test"` or `"pinned-rust-v1"`) for assertions and private receipts. Never catch an observer error and retry the Python resolver. Close the observer's sealed FD with backend/driver shutdown, including constructor failure.

This makes missing or bad pins fatal at both shipped X11 entry points while leaving direct test construction stable. It also avoids a mode string or environment switch that could accidentally enable the reference implementation in production.

At backend construction, open the published binary with `O_NOFOLLOW`, require a private regular executable owned by the current UID, verify its digest, copy it into a sealed memfd, and retain that descriptor. Every identity resolution executes the verified FD with `cwd=/`, a closed environment containing only `DISPLAY`, `XAUTHORITY`, and `LC_ALL=C`, bounded pipes, a new process group, and the caller's existing absolute deadline. Timeout, cancellation, malformed output, nonzero exit, or close/reap failure raises `DriverError`; it never invokes the old CLI path.

Protocol v1 accepts only the configured title, class, Windows executable, Wine prefix, expected loader `wine-preloader`, outer/client dimensions, display, and a per-call 128-bit nonce. It emits one bounded record with exact keys and primitive facts: matching process count; candidate window count; PID/start/executable match/status name/loader/prefix; outer and child XIDs/geometries; root XID; exact direct-child set; focus XID; active-window XID; display; nonce; and observer binary digest. The observer must:

1. scan every numeric `/proc` entry, read `cmdline` first, and perform the existing exact-one configured executable occurrence test before reading `stat`, `status`, `exe`, and `environ` for a candidate;
2. still require exactly one fully verified candidate, `Name:` equal to the configured executable, `/proc/PID/exe` basename `wine-preloader`, the exact configured `WINEPREFIX`, and a fresh process start value;
3. open a new authenticated X11 connection, enumerate the complete root tree, find the exact title/class candidate, bind `_NET_WM_PID` to the one verified process, read outer/client geometry, require the existing root→outer→sole-client relationship, and read both input focus and `_NET_ACTIVE_WINDOW`;
4. return raw facts without deciding foreground/profile validity or computing the identity fingerprint.

Python rejects extra/missing/duplicate keys and mismatched nonce/digest, repeats every current uniqueness, geometry, tree, foreground, origin, PID/process, prefix, loader, display and configured-profile comparison, then constructs the same `WindowIdentity` payload and SHA-256 fingerprint. `resolve_identity()` remains the sole API, so backend-pre, backend-post, runner-post, owner/Guardian/generation/epoch checks, receipt binding, timestamps, CRC, sequence, cadence, held100/resume, cleanup and release behavior remain unchanged.

## Owned files

- New: `native/x11_identity_observer/{Cargo.toml,Cargo.lock,src/main.rs}`.
- New: `tools/build_x11_identity_observer.py` and `tests/test_x11_identity_observer.py`.
- Modify: `src/crowley/session/config.py` and `src/crowley/session/driver.py` for the optional paired private pins, explicit production factory, sealed runtime adapter, shutdown, and fact-to-`WindowIdentity` validation.
- Modify: `tools/native_calibration_operator.py` only to select the production factory and add the observer binary/source pins to its private receipt provenance.
- Test-file fence: `tests/test_session_native.py` for config pair/default/missing/bad-digest validation; `tests/test_session_driver_actions.py` for reference parity, production-factory refusal, no-fallback behavior, and boundary mutations; new `tests/test_x11_identity_observer.py` for the Rust protocol/build/actual-X11 component; and `tests/test_native_calibration_operator.py` for the real independent-1 Hz composed run and helper provenance. `tests/test_session.py` does not own config parsing and is not needed. `tests/test_session_input_tool.py` also need not change if the existing nonzero-screen rejection remains before observer loading.
- `daemon.py`, `calibration.py`, protocol/decoder, Guardian, addon, services, and public IPC/status schemas stay byte-identical.

Production source pins used for this proposal: driver `05e5ed98d0b94019aa29eb0f4bd6ac3174cf45dca93deb9059425eeb815738cc`, daemon `38cb1d125e77a05f118297f842db99b872496bd664e85a7011065f7689cdbbc5`, calibration `0e96f7f4d9fd6b25c04fc767e57e4c617b69f99cb165811d4bd2a07c8c1932fc`, decoder `badd6c3f469f0f13503d3aa8851e7d0dac416629f3974841593d6b42d2199739`, config `976717d23d18d6c37d7a3a280d532ba0cdc15e6d086896fc4781b6efdf6b94cb`.

## Decisive proof map

- **Construction and no fallback:** direct `X11Backend(...)` remains explicitly labeled reference-test. Both `DesktopDriver(backend=None)` and `X11Screen(...)` must fail before lease/input/capture when either production pin is missing, incomplete, unsafe, or mismatched. A valid pin selects `pinned-rust-v1`; an observer timeout, malformed output, or nonzero exit raises the original error with zero call into the reference resolver. Injected `RecordingBackend` and explicit reference X11 fixtures remain unchanged.
- **Semantic parity:** feed the existing resolver fixture matrix to old and new implementations and require byte-identical `WindowIdentity` fields/fingerprint for all accepted cases. Reject a second matching process/window, title/class/PID mismatch, process replacement between prefilter and full read, bad start/status/loader/prefix, changed outer/client geometry, reparenting, an extra direct child, root change, and invalid focus/active window.
- **Freshness at all three boundaries:** one actual provider attempt records three distinct observer nonces and invocation start/end times. Mutate exactly one process/window fact at backend-pre, backend-post, and runner-post in separate cases; each must fail at that boundary. Restore the fact and prove the next invocation rereads it. No prior result may satisfy a later boundary.
- **Dispatch and cleanup:** pre-capture identity failure produces zero producer ACK and zero ScreenshotArea invocation. Backend-post or runner-post failure preserves the one already-owned capture as diagnostic evidence, rejects the observation, retires/reaps the producer, releases the artifact through the normal path, and leaves input unarmed. Cancellation/deadline during observer execution kills and reaps its group and preserves the original error.
- **Real component:** build twice byte-identically, execute only the verified FD, and use an owned Xvfb window plus an owned `wine-preloader`-named fixture process whose argv/status/environment satisfy the production contract. Drive title/class/PID/tree/geometry/focus/active mutations against the actual Rust process and X server rather than mocked return dictionaries.
- **Independent 1 Hz regression:** extend `test_actual_operator_measure_composes_x11_screen_daemon_and_agent[success]` in `tests/test_native_calibration_operator.py` rather than adding a separate scripted provider. Its owned compositor must expose an actual title/class/PID/root→outer→client tree and an owned process whose `argv`, `Name`, loader basename, start and `WINEPREFIX` satisfy the production observer; remove the `backend.resolve_identity = lambda` substitution from this success case. Run the real `NativeCalibrationRunner.run` + exact daemon provider + compiled ScreenshotArea producer + actual Rust observer against an independently scheduled 1000 ms publisher. Require construct/held0, updates 1..99 with contiguous sequence/update counts/CRC and publisher cadence, retained held100, resume0, all releases/reaps, exactly three fresh identity invocations per eligible update, and the observer binary/source pins in the same sealed helper receipt. The publisher clock must not wait on the consumer. Every accepted update must finish with active work below 900 ms, no ordinal skips, and no patched global clock.
- **Performance qualification:** replay the immutable gen46 topology/process-count profile and publish per-invocation `/proc`, X11, process startup/protocol, and total spans. Then require the actual component test above on the target host. A synthetic speedup or one fast identity call is insufficient; use worst observed active update time. If the real maximum remains at or above 900 ms, report failure and separately review Rust frame validation/decode; do not relax cadence or remove a fresh boundary.

## Deferred only if still measured

The 73.860 ms Python 2×2 cell loop is a deterministic candidate, and the two decode passes total about 175 ms. They remain unchanged in this correction. A later Rust frame validator must first prove exact PNG/mode, cell, CRC, schema, and decoder parity while retaining two independently bound checks; it is not needed unless the accepted identity observer still misses the 900 ms active-work gate.


## Implementation order and verification

1. Read this complete plan and applicable client-contract skill. Build the fresh
   Rust observer, versioned bounded protocol and hermetic publisher first. Keep
   the reference resolver usable only through explicit reference/test construction.
2. Wire the mandatory production factory, paired profile pins, sealed execution
   adapter, complete fact validation and helper provenance. Preserve all existing
   native calibration/daemon/decoder/Guardian/addon files byte-for-byte. The helper
   may change only production-factory selection and observer provenance.
3. Run the semantic/mutation/build/real-X11 tests, then the actual compiled
   operator/daemon/Agent composition with an independent one-Hz publisher.
   Tests must exercise actual public constructors/default wiring. Never bypass a
   failed check by weakening the fixture or replacing real production methods.
4. Map every decisive proof above to its exact test and actual result. Run scoped
   Ruff/format/compile, cargo offline tests/build/clippy as appropriate, and
   git diff --check. Freeze all source/binary/test/log hashes privately.
5. Parent independently reviews source diff and reproduces meaningful checks;
   Sol and actual Claude CLI Opus perform source review. Luna owns bounded fixes.
   Root alone installs pinned observer/config/source at a freshly decoded closed
   AH boundary, restarts the session daemon and verifies default production wiring.
   Sole live operator later performs one fresh native100; human calibration and
   three autonomous900s cycles remain separate required gates.

Exact Python test scope: new tests/test_x11_identity_observer.py, existing
tests/test_session_driver_actions.py and tests/test_session_native.py, plus
tests/test_native_calibration_operator.py for composed cases. Relevant regression
checks include tests/test_session_native_regressions.py, tests/test_session_runtime.py
and tests/test_session_input_tool.py read-only. If a genuinely required fixture
change falls outside the owned files, stop that edit and report the causal seam
to root; do independent owned work while awaiting a fence adjustment. No broad
formatter or blanket suite loop. Existing tests must not be silently skipped.

Production methods may not fall back to reference CLI queries on missing pins,
observer failure, malformed output, cancellation or timeout. No cached identity
result, alternative decoder, widened ordinal/cadence tolerance, or consumer-driven
publisher schedule. Explicit test/reference construction is a named separate
mode, never a runtime recovery path. Preserve the current nonzero-display refusal
before observer loading. Any performance evidence is tied to exact reviewed
source/binary/toolchain and topology; report a missed900ms gate as failure.

No worker live GUI/capture/input/IPC, service/config installation, game movement,
trading, database writes, kernel writes, Git commit/reset/stash/revert/push, or
external messaging. Root owns Git and live promotion. Keep logs/raw artifacts
private0700/0600 and publish only sanitized reviewed evidence.


## Accepted scope extension: finalize/recheck race (2026-10-19 22:43UTC)

Actual Rust composition exposed a production race, independently confirmed by
Sol and parent source inspection. native_construction_recheck snapshots the
active reservation under its first lock, validates outside the lock, then
reacquires the lock. If the real finalize transaction moved that exact ID into
_native_construction_terminals meanwhile, the second branch raises unknown even
though the canonical terminal is already retained. Earlier passing runs missed
this window and do not close it.

Luna may additionally modify src/crowley/session/daemon.py ONLY in this recheck
terminal-read seam and a small canonical private reply helper if useful, plus
tests/test_session_native_regressions.py for decisive regression coverage.
When the exact active ID disappeared/changed, re-read its retained terminal
under the same lock. Require the stored controller generation equals the
requested generation; return the same deep-copied canonical reservation, public
handshake, clock and history as the existing first-lock terminal path. Unknown
ID, wrong generation and invalid active observations still refuse. No admission
weakening, new state mutation, changed finalize ordering or helper bypass.

Regression must pause only the recheck thread inside snapshot validation after
its first-lock snapshot. Let the real finalization transaction durably commit
native calibration and retain that exact finalized terminal before releasing
the barrier. The in-flight poll must return the canonical finalized record and
actual actor validator must accept it. Assert commit/terminal existence at the
barrier, not guessed poll counts. Also cover unknown ID, wrong-generation
terminal, and a different terminal ID; preserve later operator state and deep
copy semantics. Fixture timeouts fail the test rather than satisfying expected
production refusal. Reproduce the race refusal against the old seam if feasible.

Temporary environment-triggered raw RPC debug instrumentation must be removed
before source freeze; keep diagnostics private0700/0600. Re-run the full real
Rust composition at final source pins after removal, including the three fresh
nonces/active-time assertions. Parent reproduces the race/negative regressions
and real component/composition checks before Sol and actual CLI Opus review.
Live installation/calibration remains root/sole-operator owned after approval.
