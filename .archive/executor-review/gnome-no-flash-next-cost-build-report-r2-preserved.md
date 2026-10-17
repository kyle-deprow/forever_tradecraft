# GNOME no-flash next-cost R1 build report

Status: FROZEN PRIVATE DIAGNOSTIC BUILD; no live capture performed.

This bounded pass built a private instrumented copy of the already accepted
GNOME Screenshot 41.0 no-flash source. It did not alter the accepted stage2
binary, production driver, host package set, D-Bus service, session profile,
GNOME settings, game, or desktop. It also did not activate D-Bus or perform a
screenshot/input action.

## Provenance

- New cache root: `/home/dev/.cache/crowley/gnome-no-flash-next-cost-r1` (private mode).
- Source archive: GNOME 41.0 `orig.tar.xz`, SHA-256
  `4adb7dec926428f74263d5796673cf142e4720b6e768f5468a8d0933f98c9597`.
- Debian source archive SHA-256:
  `3d185c0d1e8aab8381b9d530f12b4ae4c1049bd5054768197169a95fe2df5b9d`.
- Debian source descriptor SHA-256:
  `978f230fcd1d167a1368efedbf69ebfd963f12abf85ee84cddd29ee590815f2c`.
- Build image: `debian@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858`.
- Meson options: `--buildtype=release -Dx11=disabled`.
- Build dependencies were installed inside the isolated container only; no
  host packages were installed.
- The accepted full-screen Shell `Screenshot` flash argument remains `FALSE`;
  window and area flash arguments remain unchanged.
- Private binary: `/home/dev/.cache/crowley/gnome-no-flash-next-cost-r1/prefix/bin/gnome-screenshot`.
- Private binary SHA-256:
  `b988bc4c49251c7951805b0af6ad942dd82d50052feffd338f5f6b72d43b025c`.
- Version: `gnome-screenshot 41.0`; ELF Build ID
  `9c7c8653a6f204fc281e74810b162ce12bf649e4`.
- Accepted stage2 binary remains SHA-256
  `45750c8dca51a5f6ec5584be0e807a29a60284cca8a1cb5d13b8a2f45fde6af9`.

The source diff from the accepted no-flash source is limited to four C files
and one new marker header: `gnome-screenshot.c`,
`screenshot-application.c`, `screenshot-config.c`,
`screenshot-backend-shell.c`, and `crowley-next-cost-marker.h`. The complete
instrumented-tree hash list, one-line no-flash diff, source diff, compile/install
logs, package policy, ELF facts, version/help output, and dependency list are
under `gnome-no-flash-next-cost-r1/logs`.

The marker stream is exact `CROWLEY_GNOME_NEXT_COST_V1` records containing the
benchmark token, child PID, event name, and monotonic nanoseconds. Its fixed
successful sequence is encoded in the private harness and checked for one PID,
one token, exact order/cardinality, and strictly increasing timestamps. The
`run_return` marker is `g_application_run` return; it precedes final
`g_autoptr` cleanup, so any child tail after that marker is not misreported as
process-exit timing.

## Harness and offline verification

The private copied harness is
`/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark.py`.
It is bound to the new binary and to the unchanged production driver hash
`14ae6be4a901a17e396e68ac4501238db3d1cc0118c8c34ad6f7107fbcfacfa7`. It
predeclares at most two ordinals, retains every attempt and raw stderr, permits
the second only for an otherwise successful first capture with absent/incomplete
markers, and stops on malformed/extra/cross-PID/cross-token/out-of-order/
non-monotonic markers or any owner, identity, decode, freshness, or cleanup
failure. It keeps production stderr/model boundaries untouched and distinguishes
the private instrumented benchmark executable from the host-stock production
binary.

- `--self-test`: **25 passed** (offline marker, ownership, timestamp, and
  fail-closed guard cases).
- `--self-check`: **PASS** (manifest, binary hash/version, x11 gate, driver hash,
  executable directory, and production/private binding checks).
- `python3 -m py_compile` on the private harness: **PASS**.
- Private binary `--version` and `--help`: **PASS** inside build provenance;
  these did not activate screenshot capture.
- Ruff was unavailable in the host environment (`ruff: command not found`), so
  no Ruff result is claimed. No formatter was run against unrelated files.

## Boundary

`gnome-no-flash-next-cost-manifest.json` is the source/build/freeze manifest.
The private next-cost plan records the accepted marker and two-ordinal protocol.
There is no live receipt because this pass performed zero screenshot captures,
zero D-Bus activation, zero desktop input, and zero native/game operation. A
later live diagnostic requires separate review/release and must preserve the
per-capture strict PNG/identity/freshness checks; this artifact makes no
exactly-100-frame or one-Hz qualification claim.
