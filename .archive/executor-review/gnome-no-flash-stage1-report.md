# Private GNOME no-flash feasibility — Stage 1 / Stage 2 gate

Date: 2026-10-16 (local)

This is a read-only feasibility record for `.archive/PLAN-private-gnome-no-flash.md`. No source file, installed package, desktop setting, D-Bus service, running process, GUI, screenshot, or production capture was changed. Stage 2 was released for an exact private build, but the local machine does not have the required development toolchain, so no counterfeit/minimal build was attempted.

## Decision

The implementation target is legitimate and narrowly identified: keep GNOME Screenshot 41.0-3's Shell backend, changing only the three Shell `flash` arguments from `TRUE` to `FALSE`. The verified private build is currently **blocked** by missing build tools and development headers/libraries. No package installation or system modification is authorized by the plan. A later build can proceed only with a pre-existing private SDK/toolchain or an explicitly authorized dependency environment that matches the verified source.

The GNOME Shell 48.0 source was also verified for the consumer side, but rebuilding Shell is not a feasible substitute: the target is a client-side argument change and Shell's build requires the matching Mutter/GTK/GJS stack.

## Authoritative source and provenance

Private cache (mode 0700): `/home/dev/.cache/crowley/gnome-no-flash-stage1/`.

Official GNOME source archives and checksums fetched from `https://download.gnome.org/sources/` and verified against their accompanying SHA256 files:

| Artifact | SHA-256 |
| --- | --- |
| `gnome-screenshot-41.0.tar.xz` | `4adb7dec926428f74263d5796673cf142e4720b6e768f5468a8d0933f98c9597` |
| `gnome-screenshot-41.0.sha256sum` | `59e2d371e488f7b01173d873d58b024180e365e5dd5abc0f98213ad1ce68d536` |
| `gnome-shell-48.0.tar.xz` | `36aac2edcdc7588aaadb658cd4687df262b37ba0b667102dcbefbff0c2232bc3` |

The matching Ubuntu/Debian 41.0-3 source set was fetched from the official Ubuntu archive and extracted with `dpkg-source`:

| Artifact | SHA-256 |
| --- | --- |
| `gnome-screenshot_41.0-3.dsc` | `978f230fcd1d167a1368efedbf69ebfd963f12abf85ee84cddd29ee590815f2c` |
| `gnome-screenshot_41.0.orig.tar.xz` | `4adb7dec926428f74263d5796673cf142e4720b6e768f5468a8d0933f98c9597` |
| `gnome-screenshot_41.0-3.debian.tar.xz` | `3d185c0d1e8aab8381b9d530f12b4ae4c1049bd5054768197169a95fe2df5b9d` |

The Debian source lists these build dependencies: `appstream`, `debhelper-compat (= 13)`, `libglib2.0-dev (>= 2.35.1)`, `libgtk-3-dev (>= 3.10)`, `libhandy-1-dev (>= 1.5.90)`, `libxext-dev`, `libxml2-utils`, `libx11-dev`, and `meson (>= 0.50)`. `dpkg-source -x` verified the archive checksums and applied the three Debian patches. Its inline signature is present, but local GPG lacks the signing public key (`4D0BE12F0E4776D8AACE9696E66C775AEBFE6C7D`), so signature authenticity remains an explicit local limitation; no keyring was modified.

## Exact producer and consumer behavior

The pristine upstream and Ubuntu-extracted `src/screenshot-backend-shell.c` are byte-identical (SHA-256 `2abbdede110a4e01a0a7846db67551463210ddcae1d581b6cdce2d72403f22f4`). At lines 63, 72, and 80 it passes `TRUE /* flash */` for, respectively:

- `ScreenshotWindow`, parameters `(bbbs)`;
- `ScreenshotArea`, parameters `(iiiibs)`;
- `Screenshot`, parameters `(bbs)`.

The same function uses the default GApplication D-Bus connection and calls destination `org.gnome.Shell.Screenshot`, object `/org/gnome/Shell/Screenshot`, interface `org.gnome.Shell.Screenshot`, with synchronous timeout `-1`. On a successful call it decodes the Shell-created PNG with `gdk_pixbuf_new_from_file()` and unlinks that temporary file. `screenshot-utils.c` selects this Shell backend first and only falls back to X11 after a Shell-backend failure (or an explicit `GNOME_SCREENSHOT_FORCE_FALLBACK` setting); the proposed private binary must keep the Shell path and must not use that fallback as a substitute.

GNOME Shell 48.0's `js/ui/screenshot.js` accepts the same `flash` argument in all three methods and runs `flash ? this._flashAsync(screenshot) : null` in the `Promise.all` alongside the screenshot operation. `_flashAsync()` waits for `Flashspot.fire()`, whose `FLASHSPOT_ANIMATION_OUT_TIME` is `500` milliseconds. Passing `FALSE` bypasses that branch while preserving the screenshot operation, stream completion, and PNG output. This is the confirmed source location of the measured flash wait; no Shell source change is proposed.

## D-Bus/GApplication boundary

The installed service is:

```ini
[D-BUS Service]
Name=org.gnome.Screenshot
Exec=/usr/bin/gnome-screenshot --gapplication-service
```

The application constructs GApplication ID `org.gnome.Screenshot` with `G_APPLICATION_HANDLES_COMMAND_LINE`; `gnome-screenshot.c` enters through `g_application_run()`. Therefore a private executable cannot be identified merely by invoking a second process while the stock application owns the name: GLib may forward the invocation to the existing owner, and D-Bus activation explicitly names the installed `/usr/bin/gnome-screenshot`. A reviewed benchmark must prove that the private binary itself owns the application name and that the Shell screenshot call is issued by that process. It must not spoof an application ID, replace the service file, read another process's temporary PNG, or claim a no-flash result from the stock owner. During this stage, the name had no current session owner; no activation or service transition was triggered.

## Toolchain/dependency availability

Installed/runtime packages include `gnome-screenshot 41.0-3`, `gnome-shell 48.0-1ubuntu1.3`, GLib runtime `2.84.1-1ubuntu0.2`, GTK 3 runtime `3.24.49-2ubuntu1`, and libhandy runtime `1.8.3-2`. The installed binary is unchanged and has SHA-256 `cc7366f3f2130f3045807faf13e5382f592e4912d1c98fb7b7a9cfee2456ce86`; `dpkg -V gnome-screenshot` reports no mismatch.

Present: `gcc`, `make`, `pkg-config`, `dpkg-source`, `dpkg-buildpackage`, `appstream`, `libxml2-utils`, `libx11-dev`, and `libxext-dev`.

Missing: `meson`, `ninja`/`ninja-build`, `debhelper-compat`, `libglib2.0-dev`, `libgtk-3-dev`, and `libhandy-1-dev`. The corresponding GLib/GTK/libhandy headers and pkg-config files are absent. No `deb-src` entry is configured, and no matching private SDK/toolchain or cached development packages were found. Apt has candidates for the missing packages, but no package was installed and no apt state was changed. GNOME Shell's full matching development stack is also absent.

## Actionable private build route (not run)

Once a legitimate private dependency environment is available, preserve the pristine archives and Debian source extraction, apply only this source diff in a new private source tree, and build into a private prefix:

```diff
-                                     TRUE, /* flash */
+                                     FALSE, /* flash */
```

Apply this exact substitution at the three call sites above, then use the source's existing `x11` feature option (default `auto`) and a private build/prefix, for example:

```sh
dpkg-source -x /home/dev/.cache/crowley/gnome-no-flash-stage1/gnome-screenshot_41.0-3.dsc /path/to/private-source
meson setup /path/to/private-build /path/to/private-source --prefix=/path/to/private-prefix --buildtype=release
meson compile -C /path/to/private-build
meson install -C /path/to/private-build
```

Those commands were intentionally not run because the required tools and headers are unavailable. A valid result must retain the pristine archives, checksums, Debian patch series, exact one-file diff, compiler/build log, binary SHA-256, and `--version`/help output. It must then undergo the separate reviewed D-Bus ownership and same-production-path benchmark described by the plan. No system binary, D-Bus service file, GNOME setting, compositor, backend selection, screenshot geometry, decoder, freshness rule, or one-Hz requirement may be changed.

## Stage result

Source identification and no-flash mechanism: **verified**. Private build feasibility on this host: **blocked by missing toolchain/development dependencies**. No build or live benchmark is claimed. The next action is to supply or explicitly authorize a matching private dependency environment, then repeat review before any service transition or production binding.
