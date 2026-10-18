# Native addon admission and ordinary closure

Status: frozen from exact R4 with the two narrowly rescoped Opus R3 corrections.

`BeginRecovery` now distinguishes a real in-load pending restore from a malformed persisted marker. Malformed `restore_pending` markers, including invalid recovery nonce lengths, casing, characters, and attempts, stay untouched until the exact slash actor admits recovery and the real Restore callback writes its canonical pending marker. Accepted recovery arms the private native fence immediately; the next periodic frame carries the existing strict armed projection. Post-Finalize recovery is covered through that frame boundary.

Ordinary startup retains its allocated surface and periodic callback when the first telemetry publication transiently fails. `safePublish` records the diagnostic and the next actual update retries; the strict frame then decodes. Constructor allocation failures continue to clear the surface and refuse ordinary defer.

The final regression additions cover malformed-marker canonicalization, recovery nonce 23/25-byte boundaries, native boot identity across Construct/Finalize/Restore, auction-house schedule rearm, logout-fence defer refusal, and held/0 Resume not satisfying Finalize.

Verified:

- 242 addon and companion tests passed.
- 4 compiled atlas/frame smoke tests passed, with 63 deselected.
- Ruff check, Ruff format check, Python compileall, and `git diff --check` passed.

Only `addon/Crowley/Agent.lua` and `tests/test_addon.py` differ from the frozen R4 tree. No live qualification or source promotion is claimed.
