# Sol source review: GNOME telemetry region R5

I reviewed the frozen candidate in `/home/dev/.cache/crowley/worktrees/region-r5-20261017` against the accepted R5 lifecycle plan and the preserved R4-to-R5 delta. I did not run tests or builds, use Git, or operate any live desktop, game, service, network, Docker, or database path.

The canonical freeze matches SHA-256 `307c6ef69ba4c8b7376af4307852b12fcb55a57da3c1df84c3ef1fc4ddda2bf2`. All twelve worktree files match the identities in that freeze:

- `deploy/crowley-session.example.toml`: `858ce9d1efa39855598481ecf35b06bdc783cdc66ba2e01486614f58be03fd82`
- `src/crowley/session/cli.py`: `259570fb2027000e6c77447bfb4db6bc31961b4f08f6ef1c77f17876f84afc36`
- `src/crowley/session/daemon.py`: `424befa98c279156da1e9cc724cbf76619ffc6edf325947ff905342791d6c111`
- `src/crowley/session/driver.py`: `75b38b74dca59256f76c7a783ef13a56a62d50f634611ef04162c61b1c4dbb81`
- `tests/test_session_capture.py`: `9bc94bd112dbc8b293374d80126876e88bb7eb45e4072ab34526b5db4a77e893`
- `tests/test_session_cli_motion.py`: `082f7f6be6ac5aaf987b2cc07e0175f8d07bc5b971cf96704c1279c9c9214ace`
- `tests/test_session_native.py`: `169d0d3b6068d3ae42e762b7f3059348b42b5d988f012c8c520603da0978e764`
- `tools/gnome-telemetry-region/0001-typed-telemetry-area.patch`: `0cccf95ff69cff91986ab783d6f70b4a75722d31d933d794237f2c8d63662225`
- `tools/gnome-telemetry-region/README.md`: `211bb10e327aa4259926fb0af3dce3f1bd672458290a6f9dfdfb333eb8de6c26`
- `tools/gnome-telemetry-region/build-private.sh`: `e47fd778444c3b710295a2c69533e7cdb116f64e49ea1fc24f7da5fbb34abb81`
- `tools/gnome-telemetry-region/manifest.example.json`: `c3d75241ea23aab295960f5aa5ca70c20aab3b9a47dfa3aeb7e507c8758993f5`
- `tools/gnome-telemetry-region/offline_harness.py`: `9e466409dfc592368c266baf239ff22f6591db9dbec7efc69db41e984e6fbe27`

The frozen plan (`87396c942452b4c6293c15d589faa58039d08319c967ae2814247c489fef7142`), R4 freeze (`2c1f7974cd69d0ef83852fe90c3ecd47f2047782735cc6e0d1a360b6360ff566`), isolation baseline (`a990b5a7f2999ac76cca127c5e3995168d7b91d3f94373c8949cbcd483fe0816`), manifest (`6f2a9f1752ff2b5ae3d3fe350fad044cf9867ac1d4af5785bb7c7be4bea9cf01`), and compiled binary (`7f7080c82f0c403373480ac24e0f5ec22587c04716e9dc081a897751e2db46b3`) also match the freeze. The inspected parent delta has SHA-256 `e80bf730a11420bd497783293a6189a636215ea8e00e369b452cc5f16230d2c9`.

The source closes the R4 lifecycle defects. The active-primary flag is set after the authenticated ACK and before asynchronous capture. All production native-region routes now enter the controller/Guardian/backend admission order, register before exec, retain registration through confirmed reap, and preserve stop/pause revocation. Callback-free capture is restricted to the explicit low-level fixture switch. Loaded configuration and the driver's copied profile are independent; runtime anchors no longer mutate configured profile identity. A previously capture-revoked backend refuses before request-directory creation, and no path clears revocation to admit the diagnostic. Success receipt publication is final-only, while failure evidence is captured under the motion fence and includes active and retired attempts. The runner preserves strict one-second qualification and treats the 250 ms extension only as evidence collection. The generic socket reader uses one absolute deadline. Stock model capture remains on the full-desktop route.

## Must-Fix

1. **The required compiled regression does not reach the repaired active-primary guard.** In `tests/test_session_native.py:643`, the alleged foreign ordinary command launches the same patched private producer with the same `XDG_RUNTIME_DIR` as the active capture. It therefore fails in `screenshot_reserve_canonical_invocation()` on the runtime `flock`; `tests/test_session_native.py:652` explicitly expects the `another screenshot invocation owns` error. No command line is forwarded to the active `GApplication`, so the test never executes the guard at `tools/gnome-telemetry-region/0001-typed-telemetry-area.patch:121` or proves that `telemetry_capture_active` set at line 156 blocks shared-option parsing. Removing or breaking that R5 flag would leave this regression green. This is reachable with an ordinary stock GNOME Screenshot binary, which does not know about the private producer's new flock but can address the same application ID, and it is the exact R4 regression the plan requires compiled private-bus evidence for. Keep the existing same-runtime flock check, then add a second ordinary invocation using a distinct owned mode-0700 `XDG_RUNTIME_DIR` while retaining the same explicit `DBUS_SESSION_BUS_ADDRESS` and display. Assert that it reaches the existing primary, fails with the active-capture refusal, creates no output, and causes no second Shell call. A malformed telemetry invocation can continue to prove the pre-parser flock boundary separately.

## Should-Fix

None.

## Nits

None.

STATUS: NEEDS WORK
