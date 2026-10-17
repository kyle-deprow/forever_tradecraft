# GNOME no-flash next-cost diagnostic

The released, timing-only diagnostic completed successfully on 2026-10-17. It ran one sample and stopped after the first complete valid marker stream. This is a single-sample feasibility measurement, not 100-frame qualification.

## Preconditions and strict evidence

- Private run receipt: `/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark-20261017T042825821377Z-1280000/receipt.json` (`COMPLETED_TIMING_ONLY`, exit 0, one sample, no errors or cleanup errors).
- The verified client remained PID 641068/start 998749, outer XID `0x3200001`, child XID `0x2000011`, client 1920×1080 at the measured origin. The fresh pre-entry scene showed Arthur selected at character select. One pinned XTEST pulse was sent at the fresh exact Enter World match, pointer/target verified, and button-up completed. The next fresh image showed loading; after an 8-second bounded wait it showed Arthur in Ironforge beside Auctioneer Buckler. Those private images and pulse receipt remain in `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/`.
- Strict pair receipt: `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-handshake-20261017T042818739720Z-pid1279748/strict-pair-receipt.json`. Both samples were FRESH schema 3/build 70450 for Arthur, same boot `1792211238-176315`, sequences 49 and 52, identical position `(-4949.2001953125, -903.7000122070312, 0)`, speed 0.
- The benchmark’s own strict sample was FRESH schema 3, same boot, sequence 57, same position and speed 0. The full desktop PNG was 1920×1080, 1,619,477 bytes, and passed immediate Pillow `load()` decode; production post-child PIL PNG validation/decode measured 58.3 ms.
- The controller remained PAUSED generation 13 with calibration operation `error`; capture lock was free and the unit remained disabled. The diagnostic build was the reviewed private GNOME Screenshot 41.0 binary, SHA-256 `b988bc4c49251c7951805b0af6ad942dd82d50052feffd338f5f6b72d43b025c`, with X11 disabled; production driver SHA-256 was `14ae6be4a901a17e396e68ac4501238db3d1cc0118c8c34ad6f7107fbcfacfa7`.

## Capture and marker timing

The complete marker stream contained all 28 expected events in exact order, from `main_enter` through `run_return`, with one token and child PID 1280061. The command returned exit 0. The canonical screenshot D-Bus name was absent before and after the request; PID 1280061, process start `2120144`, executable hash/path, PPID 1280000, and PGID 1280061 proved that this admitted child uniquely acquired and released the name for this request. Final owner was absent. The owner observer and backend cleanup completed with no errors.

The measured screenshot command took 0.82085 s. Production backend capture took 1.43832 s, and the full outer-identity-to-decode path took 1.67419 s. Three identity resolutions measured 0.13147, 0.12560, and 0.12344 s; production post-child PIL PNG validation/decode measured 0.05829 s. The outer-minus-backend residual is0.23587s, including the first outer identity resolution0.13147s; the remaining crop/protocol-decode portion is approximately0.10440s. The0.23587s residual must not be labeled entirely post-capture decode. These are nested path measurements and are reported independently; no observer time is subtracted to claim a one-second pass. The benchmark explicitly records owner-observer pre/post drains of 0.15454/0.15012 s outside the screenshot command.

| Ordered interval | Duration (s) |
| --- | ---: |
| `command_start` → `main_enter` (`pre_main`) | 0.016478 |
| `main_enter` → `app_constructed` | 0.000381 |
| `app_constructed` → `startup_begin` | 0.001391 |
| `startup_begin` → `config_load_begin` | 0.054838 |
| `config_load_begin` → `config_load_end` | 0.000048 |
| `config_load_end` → `startup_config_loaded` | 0.000002 |
| `startup_config_loaded` → `startup_end` | 0.000123 |
| `startup_end` → `command_line_begin` | 0.000032 |
| `command_line_begin` → `config_parse_begin` | 0.000006 |
| `config_parse_begin` → `config_parse_end` | 0.000010 |
| `config_parse_end` → `screenshot_start_begin` | 0.000002 |
| `screenshot_start_begin` → `screenshot_start_end` | 0.000004 |
| `screenshot_start_end` → `command_line_end` | 0.000001 |
| `command_line_end` → `finish_capture_begin` | 0.000210 |
| `finish_capture_begin` → `shell_backend_begin` | 0.000025 |
| `shell_backend_begin` → `shell_dbus_call_begin` | 0.000048 |
| `shell_dbus_call_begin` → `shell_dbus_call_end` | 0.357151 |
| `shell_dbus_call_end` → `shell_pixbuf_load_begin` | 0.000006 |
| `shell_pixbuf_load_begin` → `shell_pixbuf_load_end` | 0.028970 |
| `shell_pixbuf_load_end` → `shell_temp_unlink` | 0.000393 |
| `shell_temp_unlink` → `output_file_replace_begin` | 0.000025 |
| `output_file_replace_begin` → `output_stream_ready` | 0.001824 |
| `output_stream_ready` → `output_png_save_begin` | 0.000005 |
| `output_png_save_begin` → `output_png_save_end` | 0.346718 |
| `output_png_save_end` → `recent_entry_begin` | 0.000006 |
| `recent_entry_begin` → `recent_entry_end` | 0.003883 |
| `recent_entry_end` → `app_release` | 0.000009 |
| `app_release` → `run_return` (`shutdown`) | 0.004047 |
| `run_return` → command end (`post_run_return_tail`) | 0.004210 |

The two largest measured application intervals were the Shell D-Bus call (0.35715 s) and PNG encode/write (0.34672 s). Startup’s GTK/libhandy interval was 0.05484 s; Shell-side PNG decode was 0.02897 s. The `recently-used.xbel` metadata changed from 509 bookmarks / 337,298 bytes to 510 / 338,046 bytes. The measured recent-entry interval was 3.9 ms, but release/shutdown and the file update are mixed application behavior; this evidence does not establish that all recent-file or shutdown work can be removed.

The direct timing evidence still exceeds the one-second full-path target (1.674 s). It isolates substantial cost in the Shell call and PNG write path, while the X11-disabled binary confirms this sample used the intended Shell API path. No 100-frame cadence or native-operation gate is claimed.
