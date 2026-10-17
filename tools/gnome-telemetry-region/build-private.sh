#!/usr/bin/env bash
set -euo pipefail

STAGE=${GNOME_TELEMETRY_REGION_STAGE:-/home/dev/.cache/crowley/gnome-telemetry-region-r2}
REPO=${GNOME_TELEMETRY_REGION_REPO:-$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)}
PREFIX="$STAGE/prefix"
BUILD="$STAGE/build"
SOURCE="$STAGE/source"
LOG="$STAGE/logs"
ORIG="$STAGE/gnome-screenshot_41.0.orig.tar.xz"
DEBIAN="$STAGE/gnome-screenshot_41.0-3.debian.tar.xz"
PATCH="$REPO/tools/gnome-telemetry-region/0001-typed-telemetry-area.patch"
EXPECTED_DEBIAN_SHA=3d185c0d1e8aab8381b9d530f12b4ae4c1049bd5054768197169a95fe2df5b9d
EXPECTED_PATCH_SHA=0a135ab39ca57e168602cc2ea0a1e403ae69268f6593c1ad41e8d0972c231b9e

export DEBIAN_FRONTEND=noninteractive
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
mkdir -p "$LOG"
chmod 700 "$STAGE" "$LOG"

printf '%s\n' '=== telemetry-region private build ===' | tee "$LOG/build.log"
printf 'repo=%s\nstage=%s\n' "$REPO" "$STAGE" | tee -a "$LOG/build.log"
sha256sum "$ORIG" "$DEBIAN" "$PATCH" | tee "$LOG/input-hashes.log"
test "$(sha256sum "$ORIG" | cut -d' ' -f1)" = 4adb7dec926428f74263d5796673cf142e4720b6e768f5468a8d0933f98c9597
test "$(sha256sum "$DEBIAN" | cut -d' ' -f1)" = "$EXPECTED_DEBIAN_SHA"
test "$(sha256sum "$PATCH" | cut -d' ' -f1)" = "$EXPECTED_PATCH_SHA"

rm -rf "$SOURCE" "$BUILD" "$PREFIX"
mkdir -m 700 "$SOURCE" "$BUILD" "$PREFIX"
tar -xf "$ORIG" -C "$SOURCE"
tar -xf "$DEBIAN" -C "$SOURCE/gnome-screenshot-41.0"
cd "$SOURCE/gnome-screenshot-41.0"
while IFS= read -r quilt_patch || test -n "$quilt_patch"; do
    test -z "$quilt_patch" && continue
    case "$quilt_patch" in \#*) continue ;; esac
    patch -p1 < "debian/patches/$quilt_patch"
done < debian/patches/series
patch -p1 < "$PATCH"
printf '%s\n' '=== source diff and hashes ===' | tee "$LOG/build.log"
find src -type f -print0 | sort -z | xargs -0 sha256sum | tee "$LOG/source-hashes.log"
find . -type f -not -path './debian/.pc/*' -print0 | sort -z | xargs -0 sha256sum > "$LOG/full-source-hashes.log"

meson setup "$BUILD" . --prefix="$PREFIX" --buildtype=release -Dx11=disabled 2>&1 | tee "$LOG/meson-setup.log"
meson compile -C "$BUILD" 2>&1 | tee "$LOG/meson-compile.log"
meson install -C "$BUILD" 2>&1 | tee "$LOG/meson-install.log"
printf '%s\n' '=== private binary metadata; no activation ===' | tee "$LOG/build.log"
sha256sum "$PREFIX/bin/gnome-screenshot" | tee "$LOG/private-binary.sha256"
file "$PREFIX/bin/gnome-screenshot" | tee "$LOG/private-binary.file"
ldd "$PREFIX/bin/gnome-screenshot" | tee "$LOG/private-binary.ldd"
"$PREFIX/bin/gnome-screenshot" --version 2>&1 | tee "$LOG/private-binary.version"
"$PREFIX/bin/gnome-screenshot" --help 2>&1 | tee "$LOG/private-binary.help"
find "$PREFIX" -type f -print0 | sort -z | xargs -0 sha256sum | tee "$LOG/private-tree.sha256"
binary_sha256=$(cut -d' ' -f1 "$LOG/private-binary.sha256")
patch_sha256=$(sha256sum "$PATCH" | cut -d' ' -f1)
container_digest=${GNOME_TELEMETRY_REGION_CONTAINER_DIGEST:-}
if [[ -n "$container_digest" ]]; then
    container_json="\"$container_digest\""
else
    container_json=null
fi
cat > "$STAGE/manifest.json" <<EOF
{
  "schema": 1,
  "producer": "gnome-screenshot",
  "version": "41.0",
  "archive_sha256": "4adb7dec926428f74263d5796673cf142e4720b6e768f5468a8d0933f98c9597",
  "debian_archive_sha256": "$EXPECTED_DEBIAN_SHA",
  "patch_sha256": "$patch_sha256",
  "binary_sha256": "$binary_sha256",
  "container_image_digest": $container_json,
  "configure": {"x11": "disabled", "buildtype": "release", "prefix": "$PREFIX"},
  "telemetry_options": {"branch": "ScreenshotArea", "flash": false, "exact_size": [256, 256]},
  "default_binding": "stock-full-desktop-unless-explicit-profile-capability",
  "logs": "$LOG"
}
EOF
printf '%s\n' '=== complete ===' | tee -a "$LOG/build.log"
