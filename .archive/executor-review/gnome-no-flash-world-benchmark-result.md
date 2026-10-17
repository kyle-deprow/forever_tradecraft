# GNOME no-flash world benchmark result

This is an eight-sample timing-feasibility result, not the native 100-frame
qualification. The reviewed private benchmark completed in the actual loaded
Arthur world scene and retained strict decoder and process-owner evidence.

## Recovery and scene binding

The first reviewed benchmark stopped after one character-select capture because
the expected HUD protocol was absent. Its receipt remains at
`~/.local/state/crowley/executor-evidence/gnome-no-flash-benchmark-20261017T034019791532Z-1144236/receipt.json`.
A fresh production capture showed Arthur selected with Enter World visible. The
control matched the measured template at MAE 0.0, center `[960,1002]`, and the
pointer query confirmed the verified game frame. One pinned XTEST button 1
pulse was held for 150 ms and released successfully. The next captures showed
the loading screen, then Arthur at Auctioneer Buckler. No more input was sent.

The strict-pair evidence is in
`~/.local/state/crowley/executor-evidence/runtime-relink/native-handshake-20261017T034722997643Z-pid1163776/receipt.json`.
It contains two fresh schema 3 frames for build 70450, Arthur, the configured
realm and house: boot `1792208608-703443`, sequences 224 and 225, normal phase,
ordinal zero, speed zero, and identical position
`(-4949.2001953125,-903.7000122070312,0)`.

## Reviewed eight-sample run

The run used script SHA
`c3c1e8707ffad75d37dc8e6e22dd22d6e32970ab33b0d6fea5dee6313fba0a8b`, the
accepted production driver and private GNOME Screenshot binary. Its complete
0600 receipt is
`~/.local/state/crowley/executor-evidence/gnome-no-flash-benchmark-20261017T034732774222Z-1164337/receipt.json`.
The daemon preflight read PAUSED generation 13 with calibration operation
`error`, and probed the shared capture lock free. All eight images completed
PNG validation at 1920x1080 and decoded as FRESH schema 3/build 70450 frames.
The boot remained `1792208608-703443`; sequences were 234, 236, 238, 240, 242,
244, 246, and 247. Every frame had speed zero and the same position as the
strict pair.

Each command had exactly one private binary owner acquisition and release.
Every owner PID matched the active backend process-group snapshot, had the
benchmark PPID and PGID equal to PID, and used binary SHA
`45750c8dca51a5f6ec5584be0e807a29a60284cca8a1cb5d13b8a2f45fde6af9`. The
canonical bus name was unowned before and after the run. Cleanup errors were
empty.

| Stage | Minimum | Median | Maximum |
|---|---:|---:|---:|
| First outer identity resolution | 0.146 s | 0.160 s | 0.194 s |
| Two identity resolutions inside capture | 0.307 s | 0.329 s | 0.374 s |
| `gnome-screenshot` command | 0.865 s | 0.877 s | 0.977 s |
| PNG completion wait | 0.046 s | 0.050 s | 0.064 s |
| Crop/decode residual after outer resolve and backend capture | 0.105 s | 0.110 s | 0.134 s |
| Full outer identity-to-strict-decode path | 1.809 s | 1.837 s | 2.026 s |

Subprocess identity queries (xdotool, xprop, and xwininfo) took 0.274–0.330 s
in aggregate per sample, median 0.293 s. The owner monitor adds measured
pre/post quiet-drain waits of 0.155–0.159 s and 0.150 s respectively, 0.306 s
combined at the median. These waits are already inside the reported backend
capture and full-path totals. They are shown separately to make the observer
cost explicit; no time was subtracted to claim a pass. The production-like
full path therefore did not demonstrate the one-second provider target. The
sub-second screenshot command alone is not sufficient evidence of one-Hz
feasibility.

First-call screenshot time was 0.865 s; calls 2–8 had a 0.878 s median. Full
outer-path first-call time was 1.817 s; calls 2–8 had a 1.841 s median. The
original stock CLI baseline was about 1.03 s, so this run observed a faster
CLI stage in-world, while the complete provider-like path remained above the
target. Eight observations do not qualify or replace the native 100-frame
test.

The expected GNOME recent-files side effect was recorded only as metadata:
`recently-used.xbel` grew from 495 to 503 bookmarks and from 326,833 to 332,737
bytes. No entry was read, restored, or edited. The final retained capture,
`sample-08.png`, shows Arthur stationary at Auctioneer Buckler with the world
UI loaded.
