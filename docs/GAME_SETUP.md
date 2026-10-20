# Local WoW setup

The existing game is installed in `/home/dev/Games/world-of-warcraft`.
The beta client is `_classic_beta_/WowB.exe` inside that Wine prefix.
Keep its account data, WTF, Interface and registry files when repairing the runtime.

## Start the game

Use the **World of Warcraft** desktop entry or run:

```sh
/home/dev/.local/bin/crowley-world-of-warcraft
```

This starts the cached Battle.net installation with the restored Wine runtime.
The entry is `~/.local/share/applications/net.lutris.world-of-warcraft-1.desktop`;
it invokes the wrapper directly rather than depending on the deleted Lutris game
registration. It checks exact process identity, owner and prefix to avoid a
second beta client. Startup still requires the authenticated desktop session.

The reviewed recovery copies are [the wrapper](../.archive/executor-review/wow-restored-launcher-20261020.sh)
and [the desktop entry](../.archive/executor-review/wow-restored-20261020.desktop).
They document this machine's paths; preserve executable mode0700 on the installed
wrapper. Recovery evidence is linked below.

## Required runtime files

The Wine runtime is:

```text
~/.local/share/lutris/runners/wine/wine-11.16-staging-amd64-x86_64/
```

Its matching [maintainer release](https://github.com/Kron4ek/Wine-Builds/releases/tag/11.16)
provides `wine-11.16-staging-amd64.tar.xz`, SHA256:

```text
4b6bae7ba94652c49bb9527abb6428828fa05d6c16bc3aad5c46f10311276366
```

The prefix also references these directories under `~/.local/share/lutris/runtime/`:

- `dxvk/v2.6.2/`
- `vkd3d/v2.14/`
- `dxvk-nvapi/v0.9.0/`

Those are active game dependencies even though startup now uses Wine directly.
Deleting Lutris's data directory removes the runtime and leaves dangling DLL
links in the existing prefix. Check both `windows/system32` and `windows/syswow64`
after a repair. The system Wine9 installation is a different runtime.

## Verified recovery

The [2026-10-20 recovery proof](../.archive/executor-review/wow-runtime-restoration-parent-verification.json)
records the matching runtime checksum, resolved DLL links, cached Battle.net login,
Arthur in-world beside Auctioneer Buckler, five advancing normal HUD frames with
zero speed, and the tested desktop-entry duplicate guard. Registry, addon and
saved-variable backups remain private under Crowley's executor-evidence directory.

A new game process invalidates Crowley's old native/input calibration bindings.
Keep scans paused until fresh native and deliberate human input calibration pass.
