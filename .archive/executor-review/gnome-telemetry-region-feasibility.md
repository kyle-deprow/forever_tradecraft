# Telemetry region capture feasibility

Status: read-only architectural note. No source, build, desktop, D-Bus, input,
profile, or runtime state was changed.

## Verified current path

The live native provider resolves a fresh `WindowIdentity`, then
`daemon._capture_native_frame_with_capture` calls
`DesktopDriver.capture_client_crop_for_identity` and records the capture
monotonic timestamp before capture/crop/decode (`src/crowley/session/daemon.py`
975-1010). The driver currently admits exactly
`gnome-screenshot -f <absolute-stage-path>` (`driver.py` 2342-2377), waits for a
complete client-sized PNG, resolves identity again, checks the same fingerprint,
and atomically publishes the staged file before retiring its private attempt
directory. `capture_client_crop_for_identity` then crops the full desktop losslessly
using the verified client geometry and `canvas_crop` (`driver.py` 5699-5720,
5663-5695). The native decoder requires exactly the configured 256x256 crop
(`driver.py` 5730-5745). The current profile is client-relative
`canvas_crop=(80,48,256,256)`; identity resolution proves the client geometry and
currently requires its calibrated origin `(0,0)` (`driver.py` 1846-1870,
2004-2011).

The cached GNOME 41 source already has a genuine Shell D-Bus area method:
`screenshot-backend-shell.c` selects `ScreenshotArea` when its `GdkRectangle`
argument is non-null and sends `(x,y,width,height,flash,filename)` at lines
66-73, while full-screen uses `Screenshot` at lines 75-82. The interactive
selector fills that rectangle from `event->x_root`/`y_root` (global screen
coordinates) at `screenshot-area-selection.c` lines 43-46 and 115-118. The
current area branch still sends `flash=TRUE`; the accepted no-flash change only
covers full-screen, so an area experiment must explicitly review that behavior.
The rectangle is currently supplied only by the interactive area-selection path;
the noninteractive CLI path has no direct coordinate option. The existing driver allowlist also
accepts only the three-argument `gnome-screenshot -f path` form, so a caller
cannot request a region by bypassing the canonical client.

## Feasibility and required interface changes

A future private canonical-client change could request a 256x256 region, but it
would need to add a typed coordinate option to the GNOME Screenshot command path,
construct the `GdkRectangle` in the client, and keep the Shell `ScreenshotArea`
call as the sole producer. Coordinates would need to be derived from the fresh
identity and profile (`child_geometry.x + canvas_crop.x`,
`child_geometry.y + canvas_crop.y`) and sealed with the same identity/freshness
proof; hardcoded screen coordinates or a helper that calls Shell directly would
not satisfy the contract. The driver allowlist, exact argv proof, expected output
size, staged completion check, attempt-directory retirement, digest/evidence
retention, and native decoder boundary would all need reviewed updates. A
successful area result must be exactly 256x256 and losslessly decoded; a full
screen fallback would hide a producer failure and is disallowed.

This optimization applies only to telemetry/status frames. Model observations
continue using `_capture_model`, which requests the configured full model crop
from a full client capture (`daemon.py` 1915-1932); region capture cannot replace
that path. The native provider also retains the exact crop artifact and hash for
post-review evidence, so publication and cleanup semantics would remain part of
the change.

## Compression alternative and evidence needed

The GNOME Screenshot output path currently writes PNG through
`gdk_pixbuf_save_to_stream_async` with metadata options and no explicit PNG
compression level (`screenshot-application.c` 257-297). A minimal private
experiment could compare the installed GdkPixbuf PNG saver’s documented
lossless `compression` option at its default and a lower level, while checking
byte decode, dimensions, and pixels from the same capture. This is only useful if
next-cost markers show output encoding dominates; it cannot reduce the Shell
capture/read cost and may increase output size or alter metadata. It must not be
chosen from elapsed time alone.

Primary reference verified by parent: [GdkPixbuf save documentation](https://docs.gtk.org/gdk-pixbuf/method.Pixbuf.save.html)
defines the PNG `compression` option in the range0–9. This establishes the
available option, not its installed default or a measured performance gain.

The next decision should follow the reviewed marker result: compare the measured
Shell call/temp-PNG/read path and output encode path first, then benchmark one
private canonical area implementation against the unchanged full-screen telemetry
contract. Require per-capture identity, exact 256x256 dimensions, lossless pixel
validation, original admission timestamp, strict freshness/sequence checks,
retained hash/evidence, cancellation cleanup, and unchanged full-size model
captures. No region or compression optimization is qualified by this note.
