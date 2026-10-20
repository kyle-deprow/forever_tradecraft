#!/bin/sh
set -eu
umask 077
DISPLAY_VALUE=:0
XAUTHORITY_VALUE=${XAUTHORITY:-}
if [ -z "$XAUTHORITY_VALUE" ]; then
    for candidate in /run/user/1000/.mutter-Xwaylandauth.*; do
        [ -r "$candidate" ] || continue
        XAUTHORITY_VALUE=$candidate
        break
    done
fi
[ -r "$XAUTHORITY_VALUE" ] || { printf '%s\n' 'No readable Xauthority for the active desktop.' >&2; exit 1; }
PREFIX=/home/dev/Games/world-of-warcraft
WINE=/home/dev/.local/share/lutris/runners/wine/wine-11.16-staging-amd64-x86_64/bin/wine
BATTLE_NET="$PREFIX/drive_c/Program Files (x86)/Battle.net/Battle.net.exe"
LOGDIR=/home/dev/.local/state/crowley/executor-evidence/wow-runtime-restore-20261020T233311Z
mkdir -p -m 0700 "$LOGDIR"
chmod 700 "$LOGDIR"
# Refuse a duplicate owned WoW client while allowing an existing cached
# Battle.net process to service the launch request. Match exact identity,
# argv0, owner, and prefix; do not scan arbitrary command text.
OWNER_UID=$(id -u)
EXPECTED_ARGV0='C:\Program Files (x86)\World of Warcraft\_classic_beta_\WowB.exe'
for proc in /proc/[0-9]*; do
    [ -r "$proc/comm" ] || continue
    [ "$(cat "$proc/comm" 2>/dev/null || true)" = 'WowB.exe' ] || continue
    [ -r "$proc/status" ] || continue
    [ "$(awk '$1 == "Uid:" { print $2; exit }' "$proc/status" 2>/dev/null || true)" = "$OWNER_UID" ] || continue
    [ -r "$proc/cmdline" ] || continue
    argv0=$(tr '\000' '\n' < "$proc/cmdline" 2>/dev/null | sed -n '1p')
    [ "$argv0" = "$EXPECTED_ARGV0" ] || continue
    [ -r "$proc/environ" ] || continue
    tr '\000' '\n' < "$proc/environ" 2>/dev/null | grep -Fqx "WINEPREFIX=$PREFIX" || continue
    printf '%s\n' "Owned WoW already running (pid ${proc##*/}); launch refused without creating a duplicate." >> "$LOGDIR/launcher.log"
    exit 0
done
exec env DISPLAY="$DISPLAY_VALUE" XAUTHORITY="$XAUTHORITY_VALUE" \
    WINEPREFIX="$PREFIX" WINEARCH=win64 WINEESYNC=1 STAGING_SHARED_MEMORY=1 \
    DXVK_CONFIG_FILE="$PREFIX/dxvk.conf" DXVK_HUD=compiler \
    DXVK_STATE_CACHE_PATH="$PREFIX" __GL_DXVK_OPTIMIZATIONS=1 \
    __GL_SHADER_DISK_CACHE=1 __GL_SHADER_DISK_CACHE_PATH="$PREFIX" WINEDEBUG=-all \
    "$WINE" "$BATTLE_NET" --exec='launch WoW' --exec='focus play'
