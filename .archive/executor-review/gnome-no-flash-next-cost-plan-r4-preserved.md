# GNOME no-flash next-cost plan

Status: **R4 canonical private diagnostic harness integrated; pending Sol/Opus review**.
This document records the bounded diagnostic contract; it makes no one-Hz or native-100-frame
acceptance claim and does not change the accepted binary, driver, GNOME service,
desktop, or host configuration.

## Evidence pinned

The prior source and build provenance is the accepted private 41.0 no-flash build
described by [`gnome-no-flash-stage2-manifest.json`](gnome-no-flash-stage2-manifest.json).
The accepted stage2 build remains independently pinned by its preserved
manifest. The R4 diagnostic build is independently pinned by the canonical
[`gnome-no-flash-next-cost-manifest.json`](gnome-no-flash-next-cost-manifest.json):

- accepted stage2 executable: `/home/dev/.cache/crowley/gnome-no-flash-stage2-r1/prefix/bin/gnome-screenshot`
- accepted stage2 executable SHA-256: `45750c8dca51a5f6ec5584be0e807a29a60284cca8a1cb5d13b8a2f45fde6af9`
- upstream archive SHA-256: `4adb7dec926428f74263d5796673cf142e4720b6e768f5468a8d0933f98c9597`
- build configuration: `x11=disabled`; the only source change is the full-screen Shell `Screenshot` argument `TRUE /* flash */` to `FALSE /* flash */` in `src/screenshot-backend-shell.c`; window and area arguments remain unchanged.
- diagnostic root: `/home/dev/.cache/crowley/gnome-no-flash-next-cost-r1`; private executable SHA-256: `b988bc4c49251c7951805b0af6ad942dd82d50052feffd338f5f6b72d43b025c`; the private source retains that one no-flash change and adds markers only in `gnome-screenshot.c`, `screenshot-application.c`, `screenshot-config.c`, `screenshot-backend-shell.c`, and a new header.
- diagnostic source/build uses the same pinned Debian archive and Bookworm image, `-Dx11=disabled`, and is separate from the accepted stage2 root; the production host binary and capture driver remain stock/unchanged.

The exact eight-sample receipt is
`~/.local/state/crowley/executor-evidence/gnome-no-flash-benchmark-20261017T034732774222Z-1164337/receipt.json`
(SHA-256
`0b98d6835dfe26fb1a8823b44916baa1fc851aae7904c4bebfd0fdb0ea9b1182`). It is
`COMPLETED_TIMING_ONLY`, with strict fresh 1920x1080 PNGs and exact private
owner acquisition/release evidence. Its diagnostic timings are:

| Measured stage | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
| Private `gnome-screenshot -f` command | 0.865 s | 0.877 s | 0.977 s |
| Two identity resolutions inside capture | 0.307 s | 0.329 s | 0.374 s |
| Strict PNG completion wait | 0.046 s | 0.050 s | 0.064 s |
| Full outer identity-to-strict-decode path | 1.809 s | 1.837 s | 2.026 s |

The full-path receipt includes a median 0.306 s of benchmark owner-observer
quiet-drain waits, and the aggregate identity subprocess queries are a median
0.293 s. Those values are retained as measured overhead; no time is subtracted
to claim feasibility. The command timing alone is therefore insufficient for
the exactly-100-frame/one-Hz resource proof.

A prior two-run timing receipt,
`~/.local/state/crowley/executor-evidence/runtime-relink/capture-cost-r1-20261017T030305455816Z-pid1006255/receipt.json`,
provides the only current internal decomposition. It measured, per run,
1.0208--1.0376 s for the screenshot child, 0.0481--0.0546 s for completion
of the driver's staged PNG, approximately 0.143--0.150 s per identity
resolution, 0.113--0.114 s for crop/decode, and 1.629--1.641 s from capture
admission through strict decode. It did not instrument GNOME Screenshot
internals and used no strace or profiler.

## What the accepted source proves

The cost graph is explicit in the packaged GNOME 41.0 source under
`/home/dev/.cache/crowley/gnome-no-flash-stage2-r1/source-pristine`:

1. `src/gnome-screenshot.c:37-47` constructs a new
   `ScreenshotApplication` and enters `g_application_run` for every accepted
   command.
2. `src/screenshot-application.c:813-835` runs GTK/libhandy startup and
   `screenshot_load_config`. `src/screenshot-config.c:39-65` constructs
   `GSettings` and reads the saved directory, delay, pointer, format, and ICC
   settings. The noninteractive command parser then reads the auto-save
   directory at `screenshot-config.c:87-147`. The current path does not write
   settings: `screenshot_save_config` returns for noninteractive mode at
   `screenshot-config.c:68-85`.
3. `src/screenshot-application.c:637-690` parses the forwarded command and
   calls `screenshot_start`; `:535-565` holds the application and schedules
   `finish_take_screenshot`.
4. `src/screenshot-utils.c:35-70` selects the Shell backend first. Because the
   accepted build has X11 disabled, a Shell failure is terminal rather than an
   alternate capture path.
5. `src/screenshot-backend-shell.c:40-105` creates a Shell cache filename,
   performs synchronous `g_dbus_connection_call_sync` for
   `org.gnome.Shell.Screenshot`/`Screenshot`, loads the Shell-produced PNG with
   `gdk_pixbuf_new_from_file`, and unlinks the temporary Shell file. The source
   proves that the D-Bus call, Shell capture/write, local PNG read/decode, and
   temporary-file cleanup are all inside the child command, but it does not
   provide their individual durations.
6. `src/screenshot-application.c:481-533` starts the requested output save.
   `:344-371` uses asynchronous `g_file_replace_async`; `:294-342` opens the
   output stream and calls `gdk_pixbuf_save_to_stream_async`; `:200-217` waits
   for the save callback before releasing the application. This is a second
   PNG operation after the Shell's temporary PNG and is a plausible cost, not
   a measured conclusion.
7. Successful output calls `set_recent_entry` at
   `src/screenshot-application.c:74-105,115-127`, which invokes
   `gtk_recent_manager_add_full`, then releases the noninteractive application.
   The benchmark recorded the expected `recently-used.xbel` growth as metadata
   only. Its latency is unmeasured and must not be assumed to dominate.
8. The accepted driver separately performs identity resolution, waits for a
   complete strict PNG, crops and decodes the protocol frame. Those costs are
   in the production path and are not removable by keeping a GApplication
   alive.

The current evidence therefore proves a no-flash improvement over the stock
child timing and proves that the command plus driver path is still above the
one-second target in this diagnostic setup. It does **not** prove whether the
remaining child time is GTK/GApplication startup, the synchronous Shell call
(and Shell compositor/file work), local PNG read, output PNG encoding, recent
manager activity, or their interaction. PNG compression and recent-manager
work remain hypotheses until measured.

## Implemented causal instrumentation (no live run)

The private instrumentation fork was made from the accepted source archive and
built only in the new cache root. Any live measurement still requires separate
Sol/Opus review and release. Keep the existing false full-screen flash argument and
`-Dx11=disabled`; change only temporary timing markers in these private source
files:

- `src/gnome-screenshot.c`
- `src/screenshot-application.c`
- `src/screenshot-config.c`
- `src/screenshot-backend-shell.c`

Use `clock_gettime(CLOCK_MONOTONIC)` and fixed structured stderr records with
operation token, PID, and monotonic nanoseconds. Do not log pixels, paths, or
credentials. Mark these boundaries:

- process entry, application construction, `g_application_run` return;
- `screenshot_application_startup` and configuration load/parse completion;
- command-line dispatch, `screenshot_start`, and `finish_take_screenshot`;
- Shell backend entry, immediately before and after
  `g_dbus_connection_call_sync`;
- `gdk_pixbuf_new_from_file` entry/return and Shell temporary-file unlink;
- output file replace/open request, output stream save start, and
  `gdk_pixbuf_save_to_stream_finish` callback;
- `set_recent_entry` entry/return, application release, and `g_application_run`
return. The final marker precedes `g_autoptr` application cleanup; the harness
therefore reports any unmeasured child tail separately rather than calling the
`run_return` marker process exit.

A benchmark-only transparent wrapper may retain the child `CompletedProcess`
stderr returned by the existing exact-command harness. It must delegate
exactly once and add no D-Bus calls, retries, extra image reads, sleeps, or
subprocesses. The instrumentation fork must be independently hashed and its
stderr-marker overhead reported; the accepted production binary remains
untouched.

The implementation predeclares at most two ordinal captures; it does not retry
implicitly. A complete first marker stream ends the run. The first ordinal may be
followed by the already-authorized second only when the capture otherwise
completes and its marker stream is absent or incomplete. Malformed, extra, cross-PID, cross-token, out-of-order, or
non-monotonic markers stop immediately, as do identity, owner, decode, freshness,
cleanup, or process-admission failures. Successful `CompletedProcess` attempts
retain driver-decoded text stderr; backend exceptions record unavailable stderr
without creating an empty artifact or claiming failure-stage attribution. The harness retains the existing preflight, canonical-name
owner proof, executable/hash/PPID/PGID checks, shared capture lock, identity
checks, original capture timestamp, staged-file completion validation,
cancellation and attempt-directory retirement. Each successful capture is judged
independently by dimensions, complete lossless PNG decode, identity, and strict
frame freshness/sequence/position checks; no CRC or pixel equality is required
across live samples whose HUD may change. A same-capture pixel check remains
valid if a future decoder test requires it. No native operation or physical input
is needed for this cost measurement. A child cancellation must leave the
existing secure cleanup behavior intact; marker loss on cancellation is retained
as a diagnostic failure and never widens a deadline.

The marker protocol is literal `CROWLEY_GNOME_NEXT_COST_V1` with exact
`token`, child `pid`, event, and monotonic-nanosecond fields. The parser accepts
only the fixed event order/cardinality in the private harness and checks one token,
one PID, strict increasing timestamps, and no duplicate or unknown events. A
successful `CompletedProcess` retains driver-decoded text stderr; an unchanged
backend exception has no child stream available and is recorded as such.
Production stderr and the model boundary are untouched. The measurement should report, separately and without double-counting:

- application startup/config/dispatch before the Shell call;
- synchronous Shell call duration (which includes Shell-side screenshot work
  from the client's point of view);
- local read/decode of the Shell PNG;
- output file open and lossless PNG encoding/write;
- recent-manager callback and application release;
- driver PNG completion, identity, crop, and decode costs.

This is sufficient to decide where a later reviewed optimization can help. It
cannot attribute work *inside* GNOME Shell; if the synchronous call dominates,
a separate GNOME Shell source measurement would be required and must preserve
pixel identity and the existing no-flash behavior.

## R4 canonical integration

R4 preserves the R2 and R3 evidence and predecessor files, while the canonical
harness is now the tested R4 implementation. Its manifest uses receipt schema 3
and kind `gnome-no-flash-next-cost-diagnostic`; live evidence, if separately
released, uses the distinct `gnome-no-flash-next-cost-benchmark-*` directory. The
process-local PATH prepend and `CROWLEY_NEXT_COST_TOKEN` injection are recorded,
and inherited XDG/GSettings variables remain unchanged.

`derive_intervals()` uses the marker nanoseconds and Python
`time.monotonic()` on the same Linux `CLOCK_MONOTONIC` clock. It requires command
start <= `main_enter`, `run_return` <= command end, exact order, no overlaps, and
interval sums equal to command elapsed time. It emits semantic adjacent buckets,
`pre_main`, and `post_run_return_tail`. Its
`sampled_empty_pair_total_s`/`sampled_empty_pair_max_s` fields describe only the
three named empty marker pairs; they are not a bound for all instrumentation.
`run_return` remains the `g_application_run` return marker, with deferred cleanup
tail measured separately.

The bounded loop stops after a complete first stream and consumes the second
ordinal only for a first otherwise-valid missing/incomplete stream. Malformed,
extra, cross-token/PID, out-of-order, or non-monotonic markers are nonretryable;
backend exceptions preserve their original error and record decoded stderr as
unavailable when the unchanged backend exposes no `CompletedProcess`.

## Persistent GApplication assessment

The installed service descriptor is the standard
`/usr/share/dbus-1/services/org.gnome.Screenshot.service`:

```ini
[D-BUS Service]
Name=org.gnome.Screenshot
Exec=/usr/bin/gnome-screenshot --gapplication-service
```

The accepted private binary uses the same canonical application ID and
`G_APPLICATION_HANDLES_COMMAND_LINE` (`screenshot-application.c:886-892`). A
persistent genuine private process could amortize application/GTK/config
startup, but it cannot remove the Shell call, Shell PNG creation, local read,
output encode, identity, or strict decoder work. It is therefore conditional on
the instrumentation proving startup/teardown is material.

It also changes the current security and cancellation contract. Production
remains bound to the host-stock `/usr/bin/gnome-screenshot`; it does not bind to
this private instrumented executable. Only the private diagnostic harness
prepends its private path and observes that benchmark child's canonical-name
ownership, active process group, wait, and cleanup. Those owner facts are
benchmark evidence and are not production-binding evidence. A persistent owner
would have a different PID/PPID/PGID from each request; a forwarded command can
outlive the client that initiated it; and a late Shell reply or output write
could survive request cancellation. Standard GApplication command forwarding
alone does not provide a per-request cancellation token, output retirement
barrier, or proof that requests are serialized. A service would require a new
reviewed request/owner protocol that preserves those properties, exact output
identity, and no late files. It must not be introduced as a hidden performance
shortcut, change the system service file, or use a wrapper/fake owner.

The next decision is therefore: instrument one exact child first; pursue a
persistent private GApplication only if its measured removable startup cost is
large enough and a separate review accepts the owner, cancellation,
serialization, and freshness protocol. If the Shell call or PNG work dominates,
keeping the process alive is not the causal fix and no one-Hz claim follows.

## Allowed artifacts and verification

The private implementation writes only source/build/evidence artifacts named
`gnome-no-flash-next-cost-*` under the private cache/evidence roots and the
accompanying executor-review manifest/report. The canonical harness is
`~/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark.py`;
its `--self-test` and `--self-check` are offline-only. The R4 candidate and
canonical harness are byte-identical and have the same SHA-256. This pass performed no
live capture, D-Bus activation, desktop input, profile/configuration change, or
production binding. It may not modify production source,
`/usr/share/dbus-1/services`, profile/configuration, host packages, GNOME
settings, the accepted binary, or live game/runtime state.

Before interpreting any markers, the reviewer must verify the private source
archive and one-line diff, source/archive/package hashes, private binary hash,
version/help/ELF dependencies, `x11=disabled`, exact argv, one owner
acquisition/release, no stock owner, no fallback, one fresh strict decoded PNG,
per-capture dimensions and lossless pixels, no stale-file acceptance, and complete
cleanup. The result remains diagnostic until the separate native resource proof
actually passes its own exact-100-frame and freshness requirements.

## Integrated R4 result

The private container build completed from the pinned Bookworm image with the
full dependency set inside the container only. The accepted private binary and
instrumented source remain unchanged while the canonical harness now carries the
R4 parser, interval derivation, bounded-attempt policy, and honest stderr fields. Version/help, ELF, `ldd`, source
diff, source-tree, package, binary, and build logs are retained under the new
cache root. Offline canonical harness self-tests pass 32/32, `--self-check` passes, and
`py_compile` passes. The R4 candidate, canonical harness, and canonical manifest
are bound to the exact hashes in `gnome-no-flash-next-cost-freeze-r4.json`.
The result is still diagnostic: no live marker stream or frame has been
collected, so GNOME Shell wait, PNG read/encode, recent-manager, and teardown
costs remain open unknowns. No one-Hz, native-100, or production qualification
claim is made.

### Open unknowns

- Fraction of the 0.877 s child command spent in GTK/GApplication/config setup.
- Fraction spent waiting for GNOME Shell versus Shell-side PNG generation/write.
- Cost of reading the Shell PNG and encoding the requested output PNG.
- Cost of recent-manager update and process/application teardown.
- Whether any persistent owner can satisfy the current per-request process,
  cancellation, serialization, and late-file safety contract without changing
  capture semantics.
