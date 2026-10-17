# Private GNOME no-flash benchmark execution plan

Status: review-only proposal. No capture, desktop action, service change, or
production binding is authorized by this document. Runtime requires a separate
parent release after Sol reviews the exact frozen script and this plan.

## Scope and artifact

The private GNOME Screenshot 41.0-3 binary changes one full-screen Shell API
argument (`flash=true` to `false`) and is built with `-Dx11=disabled`. The
reviewed binary hash is `45750c8dca51a5f6ec5584be0e807a29a60284cca8a1cb5d13b8a2f45fde6af9`;
the unchanged production driver hash is
`14ae6be4a901a17e396e68ac4501238db3d1cc0118c8c34ad6f7107fbcfacfa7`. The
private prefix contains only the genuine executable in `bin`; its service and
schema files are not selected. Do not change `XDG_DATA_DIRS` or
`GSETTINGS_SCHEMA_DIR`. Preserve the host's matching 41.0-3 schema.

The staged operator script is
`~/.local/state/crowley/executor-evidence/gnome-no-flash-benchmark-stage2.py`.
The current staged hash is
`c3c1e8707ffad75d37dc8e6e22dd22d6e32970ab33b0d6fea5dee6313fba0a8b` (mode
0600); the preserved R4 script snapshot is
`gnome-no-flash-benchmark-stage2-r4-9a5ec234.py` with hash
`9a5ec2345974bebfb5fdad6f605190e026004f6962e8e75518784bd67b1b5e9c`.
The prior R3 snapshot is
`gnome-no-flash-benchmark-stage2-r3-524fafd1.py` with hash
`524fafd1e49d0380447fd8565b6683f4380a09c3165fafd1c35123280992ff61`.
The earlier preserved R2 script snapshot is
`gnome-no-flash-benchmark-stage2-r2-4c0b163c.py` with hash
`4c0b163c05f19cacc31c650b987121c4fb42937720981ebb23594963d6c10481`.
Its inert default is self-check; live mode additionally requires the explicit
parent release token. The invocation under review is:

```text
uv run python /home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-benchmark-stage2.py --execute-reviewed-benchmark --release-token parent-reviewed-stage2-no-flash-benchmark
```

The script validates manifest, executable, source and process-local PATH
resolution before capture. PATH is its only intentional execution-path
environment change, alongside deriving the existing graphical session values
from the verified sole Xwayland/GNOME process and checking them against the
profile. It preserves the stock backend resolver, executable allowlist,
capture lock, timeout, PNG completion check, `_crop_capture_file`, and
`decode_native_capture`. The daemon hash/evidence-copy work is excluded from
the production-like timing; report that exclusion against the measured
1.629–1.641 s outer baseline.

## Preconditions and ownership proof

Before launch, verify the session is paused/error and no daemon capture is in
flight, the shared capture lock is free, the game process/window identity and
scene are unchanged, and the canonical `org.gnome.Screenshot` name is
unowned. The initial name may be allowed a short natural-release wait; never
kill, steal, or replace an existing owner. Do not start a separate service
process. Do not change daemon state, profile, service files, system settings,
source, or the private binary.

Start the read-only D-Bus monitor before sampling. It listens only to
`org.freedesktop.DBus.NameOwnerChanged` for the screenshot name. Queries go
only to destination `org.freedesktop.DBus`, using `GetNameOwner` and
`GetConnectionUnixProcessID`; no calls, introspection, or auto-start requests
go to `org.gnome.Screenshot`. A stock owner therefore cannot be auto-activated
by the observer.

Each production `gnome-screenshot -f <absolute-path>` command must begin and
end with the canonical name unowned and show exactly one acquisition and one
release within that command's measured interval. At acquisition time retain
the PID, process start, executable path/hash, PPID, PGID, and a snapshot of
`backend.active_process_groups`. Require the PID in that snapshot, PPID equal
to the benchmark process, and PGID equal to PID. Reject preexisting,
forwarded, reused, stock, changed, incomplete, or ambiguously timed owners.
The admitted backend uses a new session and `os.execv`, so the screenshot
child's process ID is its process-group ID. A timeout/refusal is a stop: with
X11 disabled, a Shell API refusal leaves the GApplication held, so the
unchanged backend's existing timeout kills/reaps it and the name is released.
No stderr warning check can observe this timeout, and no retry is allowed.

## Bounded benchmark

Use at most eight sequential capture paths, with starts at least 1.1 seconds
apart. The first slow path is labeled cold; subsequent paths remain separate
observations. For each sample perform one foreground `resolve_identity`, one
`backend.capture`, the production crop helper, and strict native decoding.
Keep the exact same game PID/start/XID/fingerprint, geometry, scene, and
stationary position. Never move, click, change camera, logout, or request an
extra screenshot. Never use a profiler, strace, extra polling, altered timeout,
or alternative screenshot backend.

Record monotonic and wall start/end, each backend command name/argc/status and
elapsed time, screenshot elapsed time, PNG completion validation time and
dimensions/size, crop/decode elapsed time, outer-to-decode elapsed time, owner
proof, bound identity, and strict decoder result. `NO_CHANGE` is a valid
repeated publication: record it with no fresh frame, do not count it as a
fresh timing result, do not retry it, and continue within the eight-call cap.
For `FRESH`, require unchanged boot, increasing sequence, fixed position, and
zero speed. A path over one second is retained as slow; it does not change the
production deadline and is not retried. Report whether steady-state has
demonstrated feasibility; this experiment cannot qualify the 100-frame gate.

The GTK screenshot application writes
`~/.local/share/recently-used.xbel` on shutdown. Record only existence, file
size, modification time, and bookmark count before and after. Do not read or
record bookmark contents, edit/restore the file, or claim all user state is
unchanged. This write occurs inside the screenshot command timing and should
be considered when comparing to the stock baseline.

## Stop and cleanup

Stop on any identity, focus, scene, geometry, capture lock, image decode,
decoder, process ownership, observer, or timeout failure. Retain one private
0700 directory with 0600 receipt and captures. Preserve exact failure text;
no hidden retry. At cleanup, close only an exact previously verified
benchmark-owned private screenshot PID after rechecking its unique name,
process start, executable, and hash. Send SIGTERM and wait a fixed bound; do
not escalate. Require the canonical name to return to its initial unowned
state. Close/reap only the monitor started by this benchmark. Report cleanup
failure rather than retrying. Do not claim package, settings, XBEL, daemon,
profile, or global state was restored unless individually evidenced.

Up to eight timing samples are feasibility evidence only. A path below one
second can motivate a separately reviewed 100-frame qualification; it does
not authorize calibration, daemon acceptance, or production binding.
