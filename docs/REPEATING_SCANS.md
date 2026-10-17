# Repeating Crowley scans

`crowley-session` is the local durable controller for the existing format-2
Crowley addon and companion. It reads the lossless 128x128 telemetry surface,
parses the stable `Crowley.lua` payload, waits for the companion's exact UID
upload record, and verifies the exact `Crowley_Data/Data.lua` acknowledgement.
The normal mode repeats every 900 seconds. Validation mode stops after three
consecutive qualifying sweeps; the third acknowledgement goes directly to
closeout and does not start a fourth sweep.

The pinned profile is one Forever beta 70450 client: Arthur on Classic Beta PvE
2, Alliance, `enUS`, client `1.60.1`, interface 16001, addon `0.2.0`, and house
`beta-normal-alliance`. The status canvas is the physical crop
`(80,48,256,256)` inside the 1920x1080 game child. The GNOME panel and dock
therefore cannot cover the canvas. The model receives a separately verified
game-child crop and never receives a full desktop screenshot.

Copy the example TOML outside the repository and fill in the canonical
`plan_hash`/`plan_json` and the three durable paths:

```text
saved_variables = ".../WTF/.../SavedVariables/Crowley.lua"
companion_state = "~/.local/state/crowley/companion-state.json"
data_lua = ".../Interface/AddOns/Crowley_Data/Data.lua"
```

The companion's default state file is `~/.local/state/crowley/companion-state.json`
(or `$XDG_STATE_HOME/crowley/companion-state.json` when that environment variable
is set). Use that exact path in the session profile; the controller never creates a
second companion state file.

Keep the session journal at `~/.local/state/crowley/session.json` (or the matching
`$XDG_STATE_HOME` directory). It contains restart intent, intervention history,
and accepted evidence, so it must not live under `/run/user`.

Successful native calibration retains the final lossless review crop in the private
`native-evidence/` directory beside that journal with mode `0700`/`0600` permissions;
the temporary construction and update crops are removed after the runner consumes them.

The live X11 driver requires the configured `wowb.exe` WM class, one matching
client child, the measured geometry, foreground identity, and a process start
fingerprint. Configure the measured Wine prefix in the profile; leave
`xauthority` empty so the user service inherits the current session's
`XAUTHORITY` value. It captures through `gnome-screenshot`, crops only after identity
verification, and uses one XTEST injection path. Missing anchors, an identity
change, stale pixels, an unexpected XI2 event, a lost lease, or a missing
postcondition blocks the session.

Install the entry point and start the user service before running the socket gates.
The unit expects the executable installed by `uv tool install` at
`~/.local/bin/crowley-session`:

Build Crowley's private input tool from the pinned source archive in `vendor/`:

```text
uv run python tools/build_crowley_xdotool.py
```

Building requires `cc`, `make`, `readelf`, `objdump` and the development packages
`libx11-dev`, `libxtst-dev`, `libxinerama-dev`, `libxkbcommon-dev`. The builder
verifies the source checksum and publishes under `~/.cache/crowley/xdotool`.
It verifies an existing publication and rejects an invalid one. The native
backend requires this tool and screen zero (`:0` or `:0.0` on this machine).
The executable is copied into a sealed image shared with the release watchdog;
its digest is part of window and calibration identity.

Copy and review the filled profile before starting the service:

```text
uv tool install --editable /home/dev/repos/pegasus
mkdir -p ~/.config/crowley
cp deploy/crowley-session.example.toml ~/.config/crowley/session.toml
# edit and review ~/.config/crowley/session.toml before continuing
mkdir -p ~/.config/systemd/user
cp deploy/crowley-session.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now crowley-session.service
```

The daemon starts unarmed, so it is safe for the service to run while the
operator completes the native and input gates. If the repository is elsewhere,
install that checkout with `uv tool install --editable <repository>` and keep the
unit's executable path aligned with the resulting `~/.local/bin/crowley-session`
entry point.

The daemon starts without input ownership. The operator first starts a mode and
uses the daemon's own socket for the preconstruction boundary and two live gates:

```text
crowley-session --config ~/.config/crowley/session.toml status
crowley-session --config ~/.config/crowley/session.toml start --mode validation --generation <status-generation>
crowley-session --config ~/.config/crowley/session.toml native-bootstrap --generation <start-generation>
crowley-session --config ~/.config/crowley/session.toml native-calibrate --generation <start-generation>
crowley-session --config ~/.config/crowley/session.toml calibration-status
crowley-session --config ~/.config/crowley/session.toml input-calibrate --generation <start-generation>
crowley-session --config ~/.config/crowley/session.toml calibration-status
crowley-session --config ~/.config/crowley/session.toml resume --generation <input-calibration-generation>
```

Use the generation returned by each command. Native calibration keeps the
generation unchanged; the deliberate input sample revokes it and returns a new
paused generation, which is the value required by `resume`.
The `start` example assumes a fresh session. For a persisted `PAUSED` session
whose mode is already correct, use `resume` with the current generation instead.
If native calibration is missing, that resumes into `NATIVE_CALIBRATION` while
input stays unarmed. A rejected `start` does not establish that the generation
changed; inspect the actual state before repeating it.
The two calibration commands are supervised single-flight starts and return
within the normal five-second socket timeout. Poll `calibration-status` for the
readiness, completion result, or durable error before issuing the next gate.

Before `native-calibrate`, the authorized sole operator leaves the verified
client at the external bootstrap boundary where the new Agent surface has not
been constructed. While the controller remains in its unarmed
`NATIVE_CALIBRATION` state, issue `native-bootstrap` through the daemon socket.
That command captures the calibrated child crop and rejects an existing or
malformed status surface; it does not create addon textures or accept caller
metrics. Start `native-calibrate` while the client remains at this boundary.
The runner proves the absence capture, samples process `VmHWM`, and then
publishes `nativeBootstrapReady`; only after that visible signal should the
authorized operator perform the normal login or reload that loads Agent. The
runner waits for the actual fresh `normal/0` Agent frame, so the operator may
finish loading the addon after readiness is shown. It then publishes
`holdRequired`; issue `/crowley agent hold` and wait for the fresh `held/0`
frame before `measureReady` appears. Issue `/crowley agent measure` only after
`measureReady`; the runner waits for `updates/1`, then requires exactly ordinals
1 through 99 at one hertz and the final `held/100`. When `resumeRequired`
appears, issue `/crowley agent resume`; the runner allows held/100 while waiting
for a fresh same-boot `normal/0`. Native calibration measures the actual frame surface,
2,048 reused glyph textures, inverse effective-scale anchoring, lossless pixels,
update p99, and the exact Lua heap diagnostics described below. Input calibration creates a temporary private GTK target,
proves its PID/XID/focus and XTEST key/click sources, then waits for one real
operator key and click. A forwarded event that cannot be safely correlated
revokes the generation. There is no trace-only or caller-supplied source-ID
shortcut. A completed human sample is retained as sealed process-local
evidence while the controller remains durably `PAUSED`; only an explicit
`resume` may reconcile and arm it. The controller arms only after both sealed
live results pass.

The three Agent commands are game-local diagnostic controls. Use them only at
the matching status boundary; the session daemon never guesses or dispatches
them:

```text
/crowley agent hold
/crowley agent measure
/crowley agent resume
```

During `input-calibrate` the daemon proves the XTEST and guardian boundary. For
each pointer action later, immediately before dispatch, the executor re-resolves
the one client and invokes the native control-specific anchor producer for that
action from a fresh owned scene. Each producer
must return a fresh screenshot or addon visual proof naming the actual control,
its integer client coordinate, child ancestry, boot/identity, and capture
sequence. The original monotonic capture time stays bound to the retained
artifact through model inference and native sealing; it is never restamped
after decoding, and later native frames must be newer in both sequence and
capture time. Missing producer evidence, a generic world observation, configured
coordinates, incomplete fingerprints, or an identity mismatch fail closed.

The daemon's socket controls the same controller instance as its capture loop.
Every mutating request carries the current generation. `pause` and `stop` revoke
all held input and queued actions immediately; the journal preserves the current
pending phase and uncertain intent while an already-dispatched client operation
settles, but neither command starts a new save, reload, upload, acknowledgement,
logout, or cleanup action. `pause` remains durable across restart. `resume`
requires fresh reconciliation and, after a process restart, a fresh live input gate
because the prior target identity cannot be reconstructed from a boolean journal
flag. `closeout` is orthogonal to stop and may finish an already-running scan's
authorized evidence path, ending with exactly one `/logout`, followed by stable
empty `scans`/`sweeps` and empty Data.lua ack lists.

The closeout executor takes a new telemetry frame immediately before logout and
requires the scanner to be in its explicit `ready` or `scheduled` phase, an
empty pending queue, and the exact acknowledged UID. It then issues the exact
`/crowley session fence` command and waits for a newer frame from the same boot
with `scanner.scheduleFence.state = armed` before issuing one `/logout`. A
refused fence reports `scan_active`; item, owned, and blocked scanner phases
are never treated as idle. The addon invalidates its cooldown scheduling token
when the fence is armed, so a queued cadence callback cannot start a new sweep
while the client is leaving the world.

The journal records state, generation, action intent, expected boot, deadlines,
pending UID, accepted streak, rejected evidence, and sanitized telemetry. Exact
chat EditBox text is read back from `ChatFrameUtil.GetActiveWindow()` for one
command and is never persisted. Status is read-only. A process lifetime `flock`
protects the desktop lease and socket; a second daemon cannot unlink a live
socket or acquire the lease.

Login recovery is bounded to the configured `gpt-6-luna` adapter and four named
actions: `dismiss_disconnect`, `reconnect_game`, `select_arthur`, and
`enter_world`. The adapter runs Codex CLI `0.162.1` from a neutral directory with
`--ignore-user-config`, `--ignore-rules`, read-only ephemeral execution,
structured output, and installed tool-disabling flags. Normal cadence, scan,
upload, and acknowledgement work never invokes it. Credential prompts, model
substitution, tool events, schema errors, and unexpected CLI diagnostics block.
Each named action has a fresh visual precondition and fresh visual postcondition;
world and auction-house states additionally come from a new decoded addon frame.
The adapter reports only the bounded action or named visual facts, while the
daemon verifies character, realm, modal, control, and idle fields against the
configured profile.

The daemon status exposes the native handshake as `nativeHandshake` with
`state`, `holdRequired`, `measureReady`, `resumeRequired`, `resumeReady`,
`failure`, `restored`, `resumeBoundary`, and durable `archiveReceipts` fields.
The resume boundary is the verified held/100 proof published before the runner
requests a fresh normal frame. Each reset callback
archives the complete historical record and returns its verified receipt before
`clear_refs=5` is written; failed windows report a durable
`restoration_required` status and cannot arm input.

Each status frame carries the exact native render schema: a `luaHeap` object
using `collectgarbage_count` with before/after/net KiB values, plus
`nativePhase` (`normal`, `held`, or `updates`) and `nativeOrdinal` (0 through
100). An unavailable Lua measurement uses the explicit false/zero sentinel.
The native gate measures the actual construction and update windows with the
Linux reset5 process meter; it records the historical HWM before each reset,
the post-reset baseline, and the final HWM in two sealed memory records. The
runner crosses the owned hold, measure, and resume boundaries before accepting
the final capture, retains both complete memory measurements and the fresh
normal/0 resume frame, and rejects a stale or mismatched client identity.

The required automated checks are:

```text
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
```

Native acceptance still requires the measured gates, three new qualifying 428-ID
sweeps at starts `seed`, `seed+900±5`, and `seed+1800±5`, upload within 60
seconds of each finish, exact acknowledgement, zero pending queues after
closeout, and a demonstrated pause/restart/resume boundary. Native captures and
human takeover results are operator evidence; the harness and fake-clock tests
do not substitute for that live acceptance.

## Natural interaction commands

The motion executors use a separate interaction mode after the same native and
input gates pass. Enter it from the paused controller using its current generation;
read the returned status for the generation used by later requests:

```text
crowley-session --config ~/.config/crowley/session.toml interaction-start --generation <current-generation>
crowley-session --config ~/.config/crowley/session.toml motion-camera-calibrate --generation <interaction-generation> --delta-pixels 4
crowley-session --config ~/.config/crowley/session.toml motion-movement-calibrate --generation <interaction-generation>
crowley-session --config ~/.config/crowley/session.toml motion-key --generation <interaction-generation> --role move_forward --duration 0.08
crowley-session --config ~/.config/crowley/session.toml motion-camera --generation <interaction-generation> --delta-pixels 4
crowley-session --config ~/.config/crowley/session.toml motion-waypoint --generation <interaction-generation> --x <nearby-world-x> --y <nearby-world-y>
crowley-session --config ~/.config/crowley/session.toml interaction-stop --generation <interaction-generation>
```

Calibration measures actual camera response, then repeated forward/backward and
both strafe roles using fresh telemetry and visual route evidence. The technical
movement probe defaults to 0.03 seconds. Camera calibration accepts signed 4–8 pixel
drags. Waypoints require the measured mappings and remain within a cumulative
two-world-unit travel budget. Each physical action reserves fresh post-release
feedback; no progress, chat focus, stale evidence or cancellation stops it.
`interaction-stop` revokes without waiting behind an active motion request.
Scan scheduling remains idle in interaction mode.

The optional `pointer_profile`, `camera_profile` and `move_profile` configuration
fields select `"baseline"` or an absolute schema 2 profile path. The
`motion-profile build --demonstrations <numeric-json> --output <path>`,
`motion-profile show --profile <path>` and `motion-profile reset --profile <path>`
commands manage deliberately supplied summaries. See the
[executor architecture](ARCHITECTURE.md#natural-interaction-executors) for the
timing model. Numeric imports do not establish live human calibration. Current
live acceptance and deployment status are recorded at the top of
[HANDOFF.md](HANDOFF.md).
