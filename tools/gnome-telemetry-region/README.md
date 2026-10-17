# Private GNOME telemetry-region producer

This directory contains the reviewed GNOME Screenshot 41.0 source patch and
reproducible private build recipe for Crowley's default-off native telemetry
capture. The producer accepts one typed `--telemetry-region` request with
four integer coordinates, uses the ordinary GNOME Shell `ScreenshotArea`
backend with `flash=FALSE`, and builds with `-Dx11=disabled`. It does not
change the stock full-screen, window, or interactive paths.

`build-private.sh` must run in the approved isolated Debian Bookworm container,
with only a new private build cache mounted at its exact path. Copy the
verified upstream/Debian archives and this patch, recipe, manifest, README,
and offline harness into that cache before the container starts; the host
repository itself is not mounted into the build container.
The container invocation installs the recorded build dependencies, including
`patch` and `xz-utils` for the pinned source archives; it installs no host packages, writes
no service or desktop settings, and does not activate a screenshot. The stage contains only the verified GNOME archive,
Debian patch archive, build outputs, logs, source hashes, and private prefix.

The Python driver opens the configured binary, verifies its owner/mode/hash,
copies the exact bytes into a sealed Linux memfd, and executes that retained
image through the positive process-admission wrapper. The child sends a
nonce-bound primary-owner receipt over the inherited capability pipe and waits
for the parent ACK before calling `ScreenshotArea`. The stock executable is
selected whenever the profile capability is absent.

The private binary's harmless checks are:

```text
gnome-screenshot --version
gnome-screenshot --help
python3 tools/gnome-telemetry-region/offline_harness.py --self-test --self-check
```

The reproducible R2 container command mounts only
`/home/dev/.cache/crowley/gnome-telemetry-region-r2` (read/write) and uses the
pinned
`debian@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858`
image, installs the dependencies listed above, and invokes the cache-side
`build-private.sh`. It does not mount the host repository, home directory,
display socket, Xauthority, service socket, or credentials. Set
`GNOME_TELEMETRY_REGION_CONTAINER_DIGEST` to that digest so the generated
stage manifest records the exact image identity. The prior R1 build mounted
the repository; that historical fact remains in its receipt and is not the
R2 reproducibility contract.

No live display, Shell call, input, service activation, profile binding, or
native-100 run is part of this offline build.
