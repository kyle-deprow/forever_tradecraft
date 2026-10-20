# Native observer R3: final source-contract corrections

Objective: close actual CLI Opus R2's two Should-Fix findings and three small,
reachable contract gaps jointly confirmed by parent and Sol. No deployment or
live calibration is authorized by this source phase. Preserve the existing
thirteen-file candidate and all guards. Prior final R2 passes/reviews remain
historical at their exact pins; new pins require fresh relevant verification.

## Ownership and scope

One existing Luna worker owns this bounded correction round. May edit ONLY:
- `native/x11_identity_observer/src/main.rs`
- `tools/build_x11_identity_observer.py`
- `tests/test_x11_identity_observer.py`
- `src/crowley/session/driver.py`
- `tests/test_session_driver_actions.py`
- `tests/test_session_native.py`
- `tests/test_native_calibration_operator.py`

Other six approved candidate files stay frozen; final manifest STILL includes
all thirteen existing files, including daemon. No dependencies, public IPC or
addon/telemetry schema changes. One private observer success fact is approved
below. Protected calibration/decoder/Guardian/input-tool/controller remain
byte-identical to MAIN. No other edits, commits/reset/stash/revert, GUI/capture/
input/live IPC/services/config/DB/kernel or external messages. Root owns plans,
Git, integration checks, installation and release.

Read the original observer plan, R1 correction/accepted-closure plans, compact
client-contract skill, and actual Opus R2 review before editing. R3 supersedes
prior 8+5 ownership only for the seven paths above.

## Corrections and decisive evidence

1. Build isolation: `refuse_ambient_cargo_configuration` must inspect the actual
Cargo build working directories and ancestors, immediately before each build.
The repository source walk alone misses `/tmp/.cargo/config(.toml)`. Use owned
private temp fixtures to plant a config above the REAL test build cwd; assert
refusal before Cargo execution for both config names. Do not create or mutate
host `/tmp/.cargo` or global Cargo configuration. Keep exact source/static/
linker snapshots, offline neutral tools, deterministic double build, publication
modes/atomicity/no-different-overwrite and source allowlist unchanged.

2. Fully verified window count: apply the established complete tree/parent/
geometry/client-child checks to EVERY title/class/PID candidate, then require
exactly one fully verified window; emit that count as `candidateWindowCount`.
Match actual reference acceptance; retain final selected binding/lifetime rereads
and refusal of ambiguity/query uncertainty. Actual Xvfb regressions: valid game
plus same-title/class/PID invalid-sized/nested/tree candidate still yields the
same complete identity/fingerprint in reference and Rust; two fully valid
windows refuse; no valid windows refuse. Avoid swallowing target uncertainty
as a successful identity. No input or X-server grab by production observer.

3. Capture one observer reference in resolve_identity and pass it to the pinned
resolver. Close racing after capture/before invoke must produce typed DriverError
through the existing observer lifecycle, never AttributeError or fallback.
Use a deterministic barrier with real owned sealed resources; prove child/FD
cleanup. Do not add a backend-wide lock or unrelated architecture.

4. Match actual pinned vendored xdotool `getwindowfocus` WM_STATE self/ancestor
semantics. Test with the ACTUAL pinned vendored executable on owned Xvfb, not
only the raw-XGetInputFocus shim: focus on descendant, WM_STATE on client/outer,
unrelated focused window, ordinary rawfocus with no WM_STATE. Read vendored
xdo.c:1181-1250 and cmd_getwindowfocus.c. IMPORTANT: sane ignores find's error;
when the valid parent walk reaches0 with no WM_STATE, original raw focus remains
in *window_ret. Match actual returned behavior; do NOT invent new no-WM_STATE
refusal or arbitrarily map focus to the expected game window. Bound traversal
and fail closed on real query/cycle uncertainty. Preserve foreground checks and
existing fingerprint semantics. Tests must detect using raw focus unconditionally.

5. Add exact typed success fact `outerParent`, observed/rechecked by Rust; Python
strict decoder requires it and independently asserts `outerParent == outerRoot`.
Keep it OUT of fingerprint inputs. Actual Xvfb equality plus missing/bool/wrong
parent negatives; maintain strict bounded duplicate-key/versioned protocol and
all three existing fresh identity barriers. Update only affected fixture facts.

Arbitration: unsupported-platform/future sealing fallback architecture (Nit2)
and unreachable missing-pin provenance branch / process-owned helper CLI FD
lifetime (Nit5) are deferred, not acceptance blockers. New concrete reachable
risk may be reported; do not expand this round speculatively.

## Verification and freeze

Run decisive new regressions, full `tests/test_x11_identity_observer.py`, focused
driver protocol/lifecycle tests and scoped Ruff/rustfmt/compile/diff checks.
Use private CARGO_TARGET_DIR, keep generated targets out of source. Record honest
actual results and private0700/0600 artifacts; binary0700. Resolve focused failures
before any broad work. Do NOT run another full composed13/broad matrix yourself;
root owns ONE fresh independent matrix after freeze, then Sol and actual CLI
Opus R3 review same pins. No GUI/live action or repeated unchanged native attempt.

Completion: requirement-to-test map; exact final thirteen-file manifest/hash;
private hermetic binary+path-bound manifest; checks with actual output; unresolved
issues. DONE only if all five corrections and decisive tests complete. Root will
inspect, independently verify and arbitrate reviews. No autonomous claim.
