# Owned GTK gesture proof

`.archive/executor-review/owned-gesture-proof.py` is an executable verification helper for the canonical typed emitter, XI2 echo, and cancellation/release paths. It imports `build_pointer_motion_chain`, `X11Backend`, `DesktopDriver`, `OwnedGtkCalibrationWindow`, and the real XI2 parser at proof-run time. It never constructs `InputCalibrationEvidence`, arms the WoW input lease, asks for a human sample, records ambient input, or accepts arbitrary subprocess argv.

The intended sequence is:

1. Start one real calibration epoch with `DesktopDriver.begin_calibration_operation()`.
2. Create the owned GTK target with `OwnedGtkCalibrationWindow.create(startup_admission=driver.admit_calibration_target_process)`. The Guardian registers the actual helper process before its exec gate opens.
3. Start the production XI2 observer through `driver.start_input_observer(calibration=True, callback=...)` while the target remains in its registered Guardian bootstrap phase. Pre-ticket observer records are ignored so the helper never retains ambient input.
4. Issue the real `CalibrationTicket` after observer registration; ticket adoption binds the already-registered GTK bootstrap group. Focus the certified target and enable capture only after the ticket/focus boundary. During an actually admitted synthetic-motion phase, retain delivered non-XTEST Motion only when it targets the certified GTK event targets and has complete coordinates/modifiers. The phase then settles for the production 250 ms echo bound and calls the unchanged `InputCalibrationWorkflow._controlled_echo_proof` on the primary XTEST trace plus every forwarded Motion. That production method checks unique one-to-one coordinates, target, device pair, modifiers, and timestamp correlation. Unknown sources, unpaired echoes, out-of-target Motion, and any foreign Motion outside that phase revoke immediately; there is no source-ID allowlist or discarded-event path.
5. Before any next input phase, validate the ordered primary XTEST trace and complete controlled-echo proof. Dispatch pointer paths through the real `X11Backend._run` with `input_schema="pointer-motion"` and `expected_argv=tuple(actual_planned_chain)`. Dispatch the production click plan with `input_schema="single-click"`, its exact planned argv tuple, and `held_buttons={button}`. The delivered and raw press/release records are checked by the unchanged production `InputCalibrationWorkflow._validate_sequence`.
6. Compare actual XI2 timestamps, root/event coordinates, target XIDs, ordered delivered motion subsequence, endpoint, button detail, press dwell, release, registered process group, and held set. Cancellation cases revoke the real Guardian ticket mid-chain, require the chain process group to be reaped, and require the exact held button to be released on the actual observer and to pass the production sequence validator.

The binding attached to the planner dataclass is plan metadata derived from the live ticket and target certificate. It is not a capture, calibration evidence, human preference, or physical-input claim. The proof is synthetic-only and its claim is limited to canonical typed emitter dispatch, primary/echo attribution, and cancellation/release. It does not exercise D1 action completion waits, WoW camera or character motion, or human input. A future deliberate-human takeover sample would need a separately authorized run that calls the live `on_ready`/prompt/target path; this helper does not issue that prompt and does not wait for or record ambient input.

## Current production contract

The Guardian lifecycle now supports the required owned-target ordering:

- `OwnedGtkCalibrationWindow.create` registers the GTK process group as a calibration bootstrap group before releasing its gate.
- `driver.start_input_observer(calibration=True, callback=...)` is admitted while that bootstrap group is present and registers the real observer process.
- `driver.issue_calibration_ticket(target)` then publishes the exact ticket and adopts the registered GTK bootstrap group before focus and gesture dispatch.

The helper follows that source-ready order. Every mutating backend command carries the production typed schema (`pointer-motion` or `single-click`), its exact planned argv tuple, and the exact held-button set where applicable. A `BLOCKED` result remains possible for verified graphical prerequisites or a live admission failure and includes the actual Guardian group sets. It never falls back to a fake observer, fake evidence, ambient recording, a legacy generic input grammar, or an unrestricted subprocess.

The helper wraps the production GTK command callback with a passive recorder. It forwards the original arguments unchanged and returns the exact stdout, issuing no additional X11 queries. Stored `wmctrl` diagnostics contain only the admitted GTK PID/title rows plus the original response count/digest. Every production root-tree attempt produces a fresh summary of the owned client and its actual candidate frame branch; an absent or direct-root parent is `startup-unreparented`, never a certified frame or a reason to enumerate unrelated root children. Production frame/helper stats and properties are recorded when the strict verifier requests them. New diagnostic JSONL files remain mode `0600` in the owner-only evidence directory; historical failed captures remain unchanged.

The owned GTK startup uses one admitted process and one finite deadline for identity publication, mapping/reparenting readiness and strict certification. Its initial mouse-relative placement request does not establish ownership. Actual native geometry/window and the existing pointer query must confirm the start is owned before any motion. Recognized initial incomplete states can wait within that deadline; malformed or contradictory facts fail immediately. Post-ready recertification has no startup grace period.

Each positive or cancellation proof chooses one distinct inset target from its own measured owned origin. The production trajectory and click planners receive that same pinned target; it is never recomputed from the post-motion pointer. This keeps a newly mouse-centered window from producing a zero or tiny path. A preparation seed in another window is unnecessary and cannot establish distinctness for the current window.

The pinned emitter identity is read from the constructed driver's `backend.input_tool` object. The helper does not infer an artifact from a module constant or a path. Driver construction, GTK-owner construction, recorder setup, target creation, observer startup, and ticket/focus setup all execute inside one cleanup boundary. If any stage fails before a `ProofContext` is returned, the owned recorder, GTK target owner, Guardian registrations, backend groups, and production lease are closed before the exception escapes; cleanup failures are retained in the raised proof error. The offline helper regression exercises the real admission callback shape and an observer-start failure with external GTK/XI2 doubles, and verifies the lease, registration, owner, and driver are all released.

RawMotion has one exact native contract. The installed `xinput 1.6.4`
formatter (`xinput-1.6.4/src/test_xi2.c`,
<https://gitlab.freedesktop.org/xorg/app/xinput/-/blob/xinput-1.6.4/src/test_xi2.c>)
prints `detail`, `flags`, accelerated/raw valuator pairs, and a blank-line
record terminator. The installed Xwayland package is `24.1.6-1ubuntu0.2`; its
matching Xserver `xwayland-24.1.6` source shows XTEST's MotionNotify path passing
detail `0` through raw conversion in
<https://gitlab.freedesktop.org/xorg/xserver/-/blob/xwayland-24.1.6/Xext/xtest.c>
and
<https://gitlab.freedesktop.org/xorg/xserver/-/blob/xwayland-24.1.6/dix/getevents.c>.
The parser, Guardian, calibration, and this helper therefore accept only
`RawMotion.detail == 0`.
A retained live seed receipt must include the complete raw block and following
delivered endpoint before any later input is allowed; seed-only remains
diagnostic and does not claim live calibration.

For every canonical source-4 Motion, the native root/event coordinates are the
pre-transition origin. The exact integer-valued valuator axes 0 and 1 are the
delivered endpoint used for trajectory, post-pointer, and echo checks. Raw and
primary records are consumed by one forward FIFO pair at a time; a primary
cannot be reused for a later raw record, and a forwarded echo must match the
latest accepted primary endpoint. The first delivered origin must equal the
fresh owned pointer query, and each following origin must equal the immediately
preceding accepted endpoint; the helper never skips or coalesces planned
samples. The helper preserves both coordinate forms
and the complete native text in its receipt so a failed trace remains
auditable.

The synthetic producer records an owned pointer query immediately before the
absolute move and an exact post-move query before the button phase. Both
windows must remain in the certified GTK target, the requested endpoint must
equal the measured post endpoint, and the query tuple is carried into the
sealed evidence alongside the canonical transition. An origin outside the
target fails before any motion command; the helper's seed mode follows the
same rule and never warps to manufacture an origin.

XI2 server timestamps are CARD32 values. Runtime pairing, Guardian arrival
ordering, calibration sequence and echo correlation, and helper duration checks
use forward/equal modulo-2^32 elapsed time with a half-range ambiguity reject.
Only an exact pending FIFO-head primary Motion may retain the later raw arrival
clock; no raw record or unrelated primary can move the clock backward. A
malformed RawMotion detail or valuator block fails at its native blank delimiter;
the private receipt retains the complete observer text and parser reason.

Gesture receipts include monotonic and wall-clock marks for observer startup/readiness, ticket issue, focus begin/end, capture enable, each input phase, and actual chain process-group publication. Accepted callbacks retain their arrival phase, local monotonic arrival time, XI2 source/master, server timestamp, and target XIDs. Callback contents before the existing ticket/focus capture boundary are discarded. A forwarded-motion candidate is retained only during a measured admitted synthetic-motion phase and must pass the unchanged production matcher before the next action. No foreign input is ignored or source-whitelisted. The server timestamp and local arrival time are recorded separately; comparisons use the production matcher’s own event timestamps, not an assumed clock mapping. Gesture receipts also record post-cleanup target/observer/chain reaping, empty Guardian/backend registries and held sets, and production lease release; any failure makes the result fail.

Every certificate or gesture receipt records both the module-level source hashes and the live driver instance identity. `sourceIdentity.inputToolSha256` hashes `src/crowley/session/input_tool.py`; the existing helper, calibration, driver and Guardian hash fields remain intact. `runtimeIdentity.driverInstanceVersion` comes from the constructed `DesktopDriver`. Its `inputTool` object records the actual private artifact version, executable SHA256, pinned upstream commit and archive SHA256, artifact paths, and the live memfd seal bits/names plus whether all four required seals are present. These values describe the emitter image held by that exact driver instance, rather than only the module constant.

## Execution after sole GUI authority transfers

Run from the repository root only after the parent explicitly transfers GUI authority to the operator. The `certificate-only` mode creates and certifies the real GTK target under the production global desktop lease, then closes the target and driver and records target/group reaping plus lease release. It does not start an observer or issue a ticket, focus call, capture, pointer/key/button action, or human prompt. It never substitutes an evidence-directory or test lease. If production owns the global lease, the attempt fails rather than using another path.

After source prerequisites are frozen and the parent authorizes the certificate run, use the verified display/Xauthority and owner-only evidence directory:

```sh
uv run python .archive/executor-review/owned-gesture-proof.py \
  --mode certificate-only \
  --display :0 \
  --xauthority /verified/path/to/Xauthority \
  --evidence-dir ~/.local/state/crowley/executor-evidence/owned-gesture-proof
```

For a separately authorized diagnostic seed, use `--mode seed-only` with the
same explicit display, Xauthority, and evidence directory. It measures the
pointer first, chooses a distinct certified interior endpoint, records the
complete raw/delivered trace and post-pointer position, and stops before any
click or hold. A process error, no-op, endpoint mismatch, unpaired raw record,
or observer violation is a failed diagnostic; it cannot produce calibration
acceptance.

The helper records the actual production lease path and source hashes in the private receipt. Its diagnostic log stores scoped summaries for desktop-wide wmctrl/tree responses and the production-owned client/frame/helper command results. An `unverified-parent` branch records a candidate that has not passed certification; it never grants ownership. The logger forwards each verification command's exact arguments and returns the original stdout unchanged.

Only a subsequent separately authorized run may use the synthetic motion/click proof modes. Those require their own complete production source freeze and are not implied by certificate-only success. For that later run, use the same verified display and Xauthority:

```sh
mkdir -p ~/.local/state/crowley/executor-evidence/owned-gesture-proof
chmod 700 ~/.local/state/crowley/executor-evidence/owned-gesture-proof
uv run python .archive/executor-review/owned-gesture-proof.py \
  --mode positive \
  --display :0 \
  --xauthority /verified/path/to/Xauthority \
  --evidence-dir ~/.local/state/crowley/executor-evidence/owned-gesture-proof
```

Run `cancel-midpath` and `cancel-midbuttonhold` separately with the same explicit display, Xauthority, and evidence directory. Each invocation creates only the owned GTK target, and cleanup closes that target, stops the owned observer, revokes any live ticket, releases the exact held set, confirms the registered child groups are gone, and writes a new mode `0600` JSON artifact in the `0700` directory. It does not focus, capture, or inject input into WoW.

Positive acceptance requires the artifact to show `PASS`, a real observer PID in the Guardian observer registry, real chain process groups observed during admission, ordered XI2 motion ending at the planned endpoint, timestamp duration within the bounded comparison window, one left-button press/release pair with measured dwell, no observer errors or violations, no cleanup errors, and no held input after cleanup. Mid-path acceptance additionally requires the chain to be live when revoked and to finish with its process group reaped before the planned endpoint. Mid-button-hold acceptance requires a real delivered press before revoke and a real delivered release after revoke, with the held set empty and the chain group reaped. Any observer or cleanup failure downgrades an otherwise successful run to `FAIL`.

`BLOCKED` means the production fence or the verified graphical prerequisites prevented a safe proof. `FAIL` means a requested proof invariant was violated. Neither status is a physical-human validation or a WoW input claim.

## Checks performed while preparing this artifact

No display was focused or injected. A separately authorized read-only preflight may retain one GNOME screenshot in the existing owner-only evidence directory; it does not transfer GUI authority to the proof helper. Only no-GUI helper checks are appropriate before authority transfer:

```sh
uv run python -m py_compile .archive/executor-review/owned-gesture-proof.py
uv run python .archive/executor-review/owned-gesture-proof.py --help
uv run ruff check .archive/executor-review/owned-gesture-proof.py
uv run ruff format --check .archive/executor-review/owned-gesture-proof.py
```

The offline production API/planner/builder smoke check imports the real modules, verifies current signatures and ticket fields, constructs an actual `OwnedWindow`/`CalibrationTicket`, resolves `xtest_sources`, builds pointer and click plans, and checks the seed, positive, cancellation-motion, click, and held-button argv against the canonical typed schema shapes without calling `_run`. It creates no GTK process, observer, display command, or Guardian. The full native modes require a separate sole-operator release and remain intentionally unrun during preparation.
