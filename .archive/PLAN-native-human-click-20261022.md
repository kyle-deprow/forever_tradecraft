# Native calibration: shared human click execution

The live driver is blocked before native calibration. Current CLAUDE.md requires
curved, Fitts-timed, seeded/recorded gestures with submovements and endpoint
scatter, plus a hard minimum1.0second between automated game clicks. Native
calibration's FixedInput.click still moves directly and presses/releases. The
armed runtime driver cannot be called before input calibration. Repair this
bootstrap composition without weakening its admission or faking qualification.

## Scope and order

Luna implements offline in an isolated worktree based on current MAIN2e48728;
Sol reviews read-only. Root owns integration, deployment, live GUI coordination
and Git. No game operation, captures, services, config, addon changes, purchases,
posts or cancellations in implementation/review workers.

Owned files (only change those actually needed):
- `src/crowley/session/executor.py` (shared bounded planning/gesture contract).
- `src/crowley/session/driver.py` (pointer/click execution integration only).
- `src/crowley/session/pointer_execution.py` (optional shared execution primitive).
- `tools/native_calibration_operator.py` (existing technical click capability).
- `tests/test_session_executor.py` and `tests/test_session_driver_actions.py`.
- `tests/test_native_calibration_operator.py`.
- `tests/test_session_pointer_execution.py` (optional focused shared-path tests).

1. Derive a shared gesture execution path from existing executor plans and native
   emission primitives. Retain runtime Guardian/input-evidence checks. Bootstrap
   may use it only inside the existing native reservation, exclusive desktop
   lease, fresh template/identity guards and owned emitter/watchdog lifecycle.
   Do not add a runtime unarmed switch or second raw click bypass.
2. Generate bounded curved Fitts-timed samples, genuine bounded submovements,
   seeded variation, endpoint scatter and nonzero button dwell. Record the seed,
   selected endpoint and actual dispatched gesture/timing in the native receipt.
   Bind the endpoint to a certified clickable interior; a template's bounding box
   is not automatically a clickable region. Preserve exact endpoint checks by
   checking the frozen planned endpoint, never permitting arbitrary drift.
3. Enforce >=1.0second between actual automated game click presses in code,
   including helper-to-helper handoff and shared driver use where applicable.
   The limit has no user/config bypass. Account for waits before input admission.
   Use one canonical per-user-session timing-state resolver for daemon and helper,
   independent of caller-selected desktop lease paths. Keep the flock on a stable
   inode; update a separate state file atomically. Before any button GO, durably
   reserve a conservative next-allowed time covering the bounded in-flight action
   and spacing interval. A process death after physical press but before its
   receipt must not allow another immediate press. Refine timing only after the
   owned action/release is observed; failed publication refuses before press.
   Handle reboot/clock identity explicitly, and test real process death/handoff.
4. Preserve five-second click evidence, ten-second constructor and existing
   reservation/deadline limits. Refuse before dispatch when the complete gesture
   cannot fit. Recheck fresh identity, target ancestry, planned pointer endpoint
   and reservation immediately before press. Retain exact release/cancel/reaping
   on failure, including failures after movement or press. OS signals still stop
   future input rather than authorizing continued gesture/reload cleanup.
   Cover BOTH X11Backend pointer branches: the planned branch uses the shared
   path; the old raw-click branch refuses before input when no validated gesture
   is supplied. Cover native pointer parking too: its pre-template direct warp
   must become a bounded curved positioning plan preserving hover-free matching.
   Define a positive, bounded gesture argv grammar and a gesture-specific emitter
   timeout derived from plan movement+dwell+owned subprocess overhead; the old
   blanket two-second action limit cannot silently truncate a multi-step gesture.
   Check the complete timeout against admission/evidence deadlines before input;
   preserve existing budgets for non-pointer actions. No widened freshness limit.
5. Keep keyboard, text readback, native103-provider protocol, memory/qualification
   gates and controlled owned-GTK input qualification unchanged. Any unavoidable
   additional production file or protocol change requires a concrete parent
   scope decision before editing; report the actual boundary rather than bypass it.

## Verification and review

Tests must exercise actual execution and native-helper run/cleanup boundaries,
not only sample generation or monkeypatched success. Cover deterministic seed
replay and varying seeds; curved/submovement/scatter bounds; actual press spacing
and handoff; already-at-target and edge targets; stale template/identity/generation;
insufficient deadline before movement; failure before/after press; exact releases,
actor/watchdog termination and no false recovered/handback receipt. Preserve
existing real operator/daemon/Lua composition and its103 accepted updates.

Run scoped pytest for changed executor/driver/native tests, Ruff check/format on
changed files and diff-check. Retain complete actual results. Start with focused
tests and broaden for changed integration paths; do not run unrelated suites.
Deliver changed-file diff, exact checks/results, source hashes, source-derived
hotspot proof and unresolved risks. Do not commit. Root reproduces appropriate
checks; Sol READY at final hashes is required before live installation.
