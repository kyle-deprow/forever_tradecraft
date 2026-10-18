# Native addon construction R4 closure

Status: frozen after the final publication transaction and marker-matrix closure.

R4 retains the pending recovery marker through both restore-load publications. The first frame is the armed proof; the second is a checked ordinary frame after the private native fence is released. A second-publication failure now detaches the update script, hides all owned textures, clears bytes, persists a valid failed recovery marker, rearms the private fence, and leaves the Commands-owned Restore control visible and enabled. The failed boot was recovered through the exact addon slash actor, Restore button, and fresh load in the real harness.

Finalize now performs its inactive-fence publication before deleting the constructed marker. A publication error returns `publication_error`, restores the constructed marker and private fence, and leaves the normal recovery route available; the test recovers through the same slash/button/fresh-load path.

The added finite tests cover every marker state with valid and invalid attempts, bounded 64-byte opaque tokens and 65-byte rejection, wrong-type state and token fields, short/long/non-hex recovery nonces, all safe pre-ADDON_LOADED manual/event/timer/rearm paths, and direct unconstructed Publish/Snapshot typed refusals without frame or marker mutation.

Verified:

- 239 addon and companion tests passed.
- 4 compiled atlas/frame smoke tests passed, with 63 deselected.
- Ruff check, Ruff format check, Python compileall, and `git diff --check` passed.

The result is an offline production-addon boundary check. Native client template availability, live callback delivery, pixels, and ReloadUI remain later live qualification gates. No main source, daemon/helper, GUI, deployment, service, config, or game changes were made.
