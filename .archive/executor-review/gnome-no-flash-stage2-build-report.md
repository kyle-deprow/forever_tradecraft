# Private GNOME no-flash build — Stage 2 result

Date: 2026-10-16 local. This record covers the private build released by the appended section of `.archive/PLAN-private-gnome-no-flash.md`. It does not authorize a live screenshot benchmark or production binding.

## Result

The genuine GNOME Screenshot 41.0-3 client built successfully in an isolated, temporary Debian Bookworm container. The source change is exactly one boolean in `src/screenshot-backend-shell.c`: the full-screen `Screenshot` call at source line 80 passes `FALSE /* flash */`. The `ScreenshotWindow` and `ScreenshotArea` calls at lines 63 and 72 remain `TRUE /* flash */` and are byte-identical to the pristine source. The build used `-Dx11=disabled`, so a Shell API failure cannot silently select the optional X11 fallback during the later reviewed benchmark.

No host package, source file, profile, setting, service file, D-Bus owner, GUI, screenshot, or runtime service was changed. The host-side checks invoked only `--version`, `--help`, `ldd`, and read-only D-Bus owner queries. No screenshot operation or service activation occurred.

## Reproducible private build

Private stage directory (host-owned, mode 0700):

`/home/dev/.cache/crowley/gnome-no-flash-stage2-r1/`

The only container bind mount was this new private directory, mounted at the same absolute path. The container was not privileged, had no Docker socket, host root, repository, display, or service mount, and used `--security-opt no-new-privileges`. Image:

`debian:bookworm` resolved to `debian@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858` (amd64, Debian GNU/Linux 12 Bookworm).

The final command was:

```sh
docker run --rm --network bridge --user 0:0 --security-opt no-new-privileges \
  --env HOST_UID=1000 --env HOST_GID=1000 \
  --mount type=bind,src=/home/dev/.cache/crowley/gnome-no-flash-stage2-r1,dst=/home/dev/.cache/crowley/gnome-no-flash-stage2-r1 \
  --workdir=/home/dev/.cache/crowley/gnome-no-flash-stage2-r1 \
  debian@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858 \
  /bin/sh /home/dev/.cache/crowley/gnome-no-flash-stage2-r1/build-container-r1.sh
```

The authoritative full build transcript is `logs/full-build-r1.log` (4,374 lines; SHA-256 `d8707a3426672ab8c97e7135819375f7724ba95e68ae769a628a43d12bf17152`). Meson setup, compilation, installation, binary metadata, package versions, source hashes, and ownership normalization all completed. A first exploratory metadata run with `-Dx11=enabled` stopped after a successful compile/install because the image lacked `file`; its complete evidence is retained under `logs/attempt-x11-enabled-r1/` and is not the accepted build.

## Source and patch provenance

The source came from the verified Ubuntu/Debian 41.0-3 extraction, preserving its existing Debian patch series. The authoritative source artifacts are under the stage directory:

| Artifact | SHA-256 |
| --- | --- |
| `gnome-screenshot-41.0.orig.tar.xz` | `4adb7dec926428f74263d5796673cf142e4720b6e768f5468a8d0933f98c9597` |
| `gnome-screenshot_41.0-3.dsc` | `978f230fcd1d167a1368efedbf69ebfd963f12abf85ee84cddd29ee590815f2c` |
| `gnome-screenshot_41.0-3.debian.tar.xz` | `3d185c0d1e8aab8381b9d530f12b4ae4c1049bd5054768197169a95fe2df5b9d` |
| Debian patch `application-Set-color-scheme-to-prefer-dark.patch` | `813910492fe7bd9d5509a414c937ad363473980cd1fbd086e60eee0c15e015f2` |
| Debian patch `meson-Bump-libhandy-version.patch` | `0433a6883d87516e14277d78fc2b612f86866d1ba7f9102860107dc93fac7ec9` |
| Debian patch `meson-remove-extraneous-positional-argument.patch` | `a8f557b1b378d5b0a32742aca412e3ad02d50a6f660cdb1b11e8faa3328fc2bf` |
| Debian patch `series` | `82a06aa9c35416cae0a3fe87fc0a6319d5bb54b3be324103e81abd97a4bb21c2` |

Pristine `src/screenshot-backend-shell.c` SHA-256 is `2abbdede110a4e01a0a7846db67551463210ddcae1d581b6cdce2d72403f22f4`. Patched source SHA-256 is `0b3d37896682aa244a24d11ae0b5282374451df27a45a5648f8660421d226f56`. `diff -qr` reports exactly that one source file differing; `logs/one-line-source.diff` records the single-line change.

## Container toolchain

The container installed only its own build dependencies from the signed Debian Bookworm repositories; the host apt/dpkg state was untouched. Recorded versions are in `logs/container-packages.log` and `logs/container-package-policy.log`:

```text
appstream 0.16.1-2+b1
ca-certificates 20250419~deb12u1
desktop-file-utils 0.26-1
file 1:5.44-3
gettext 0.21-12
gcc 4:12.2.0-3
libglib2.0-dev 2.74.6-2+deb12u9
libgtk-3-dev 3.24.38-2~deb12u3
libhandy-1-dev 1.8.1-1
libx11-dev 2:1.8.4-2+deb12u2
libxext-dev 2:1.3.4-1+b1
libxml2-utils 2.9.14+dfsg-1.3~deb12u6
meson 1.0.1-5
ninja-build 1.11.1-2~deb12u1
pkg-config 1.8.1-1
python3 3.11.2-1+b1
```

The compiler was GCC 12.2.0 (`cc (Debian 12.2.0-14+deb12u1) 12.2.0`); Meson was 1.0.1 and Ninja 1.11.1. Meson reported `x11: disabled`, and both X11 dependencies were skipped. The full apt update/install transcripts and apt source configuration are retained under `logs/`.

## Binary and host checks

Private prefix: `/home/dev/.cache/crowley/gnome-no-flash-stage2-r1/prefix/`.

- Binary: `prefix/bin/gnome-screenshot`
- SHA-256: `45750c8dca51a5f6ec5584be0e807a29a60284cca8a1cb5d13b8a2f45fde6af9`
- Build ID: `7256f8c318927a4538995241f65a1a8c8608790d`
- `--version`: `gnome-screenshot 41.0`
- `--help`: completed and retained in `logs/private-binary.help` and the host check log
- `ldd`: completed successfully against the existing host runtime libraries; output is retained in `logs/host-readonly-r1/host-checks.log`

The installed host `/usr/bin/gnome-screenshot` remains SHA-256 `cc7366f3f2130f3045807faf13e5382f592e4912d1c98fb7b7a9cfee2456ce86`; `dpkg -V gnome-screenshot` produced no output. The session D-Bus owner query reported no `org.gnome.Screenshot` owner both before and after the permitted version/help checks. This is an ABI/loadability and identity check only; it is not a screenshot or timing qualification.

## Review boundary

This build is ready for parent/Sol/Opus review of source provenance, the one-line diff, `x11=disabled` fail-closed configuration, caller identity, and the private binary hash. A separate reviewed benchmark must still prove that this genuine private executable owns the application boundary and that its full-screen Shell request reaches the intended Shell API. No live screenshot benchmark, D-Bus service transition, production profile binding, or one-Hz acceptance is claimed here.
