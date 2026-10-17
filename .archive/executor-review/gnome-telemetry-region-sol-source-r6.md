# Sol source review: GNOME telemetry region R6

I reviewed the frozen candidate only in
`/home/dev/.cache/crowley/worktrees/region-r6-20261017`, using the exact
R5-to-R6 parent delta and the hash-verified R5 forwarding candidate as the
baseline. I did not run tests or builds, use Git, operate the desktop, or touch
runtime, service, network, Docker, database, or game state.

## Identity verification

- Final freeze
  `.archive/executor-review/gnome-telemetry-region-r6-final-freeze.json`:
  `61166a2a12adf1ad5861a7051f65f926791aeb004246ccdfd52b022877a8ef79`
- Final delta report
  `.archive/executor-review/gnome-telemetry-region-r6-final-delta.md`:
  `9d1efdac5ac31f1dcae8fe823caac1a776fededd9388b8253938646c9eb7bd60`
- Parent R5-to-R6 delta:
  `a60a36180c187e5d05f2694bf6d93659d6e8b673e5d96d7fb66339e82b8e22e2`
- Accepted amended R6 plan:
  `e7a96f4f9a8893d6d3f74565892775c75d85fc17bc4ffeecdc08e3ebdb95680e`

All ten candidate paths match the final freeze exactly:

- `deploy/crowley-session.example.toml`:
  `68b9d0400d1aaa887611f8fdf8ce6a21b56e33c63addb6bd022ade3574cab551`
- `src/crowley/session/daemon.py`:
  `4deab9e1b63aa2488b3f2d0e5b9b17dadd4c23bd8ec59e4cbbcfe704de0e3df0`
- `src/crowley/session/driver.py`:
  `f33c6b8ffc70263698c690c0572a7f7fa8a5f91aa9b66bfb0b250a0925f593d6`
- `tests/test_session_capture.py`:
  `3c4e4d267e1af0f3ddad9aa16df498c86d3a94cd3f0a4b2534dc76d2feff15e0`
- `tests/test_session_native.py`:
  `131b491df437dc52cdd48a6ab96a0f1b5f6129ee9b6f52980a7359d8399f10d3`
- `tools/gnome-telemetry-region/0001-typed-telemetry-area.patch`:
  `7b5c8eb9aeef0c59f3cad8cb83d7350d10bb5e86389c7234599dee819c190588`
- `tools/gnome-telemetry-region/README.md`:
  `e45b4d6fae85e9e771a2d4799fe41f998333a74420c1fae3ae66900b2169ad34`
- `tools/gnome-telemetry-region/build-private.sh`:
  `3098c0580efbd49988c9de440f55422e7c2902177a4d429d8228d9a89fe0c942`
- `tools/gnome-telemetry-region/manifest.example.json`:
  `e574620e3f818708b3118f279877bd2ecae61ef472961d8a0e89b60ece5ea7b9`
- `tools/gnome-telemetry-region/offline_harness.py`:
  `5e20d7560e63e9b6b3a731b3ddd8a95b08fba7ecdd3f2e5f9604129e7c7f5d0c`

The two protected R5 files are byte-identical between the predecessor and R6:
`src/crowley/session/cli.py` is
`259570fb2027000e6c77447bfb4db6bc31961b4f08f6ef1c77f17876f84afc36`
and `tests/test_session_cli_motion.py` is
`082f7f6be6ac5aaf987b2cc07e0175f8d07bc5b971cf96704c1279c9c9214ace`.
Independent direct comparison also confines the two amended paths to
`driver.py::_wait_for_complete_png` and the three corresponding helper tests.
The private binary and actual manifest match the final freeze at
`cb938cab1bd99dc088d05f6f55c8a0443401320755e2037633e7f9ac6dbe2396`
and `21bfe50a645a459c265edd756b65c11acdd96d85c04c8b0da69f905be2d9d866`.

## Closure assessment

- **Activation and action guards are complete.** The pinned upstream action
  table has exactly `about`, `help`, `quit`, `screen-shot`, and `window-shot`.
  The patch guards all five handlers at
  `tools/gnome-telemetry-region/0001-typed-telemetry-area.patch:161-239`
  and guards `GApplication::activate` at `:241-252`, using
  `telemetry_region_arg`, which is set before registration. Each guard returns
  before UI, shared-option parsing, or capture dispatch; the original telemetry
  command-line path and existing foreign-command-line guard remain intact.
- **The regression reaches genuine RPC routes.** At
  `tests/test_session_native.py:624-834`, the real compiled producer is blocked
  in its Shell call while separate `gdbus` children invoke
  `org.freedesktop.Application.Activate`, both
  `org.freedesktop.Application.ActivateAction` actions, and both
  `org.gtk.Actions.Activate` actions. Exact primary-process diagnostics prove
  one activation and four action-handler entries. The unchanged area/stock
  call counts, absent action outputs, and successful original capture prove the
  calls did not dispatch another capture or UI path.
- **Forwarding cleanup covers the whole vulnerable interval.** The `try` starts
  before `capture_thread.start()` at `tests/test_session_native.py:635`; its
  `finally` at `:771-790` releases the Shell gate, joins the capture thread,
  and communicates with or kills every successfully started ordinary/RPC child.
  The backend-owned primary is reaped by the joined production capture path.
  This closes the prior Sol R5 R2 cleanup finding without changing production
  behavior.
- **The fake backend regression now reflects the production boundary.** At
  `tests/test_session_native.py:194-321`, a configured native region on a
  `RecordingBackend` is refused by the X11-only guard with zero region calls,
  while stock model capture remains covered. The positive route remains the
  compiled integration test.
- **Profile comparison is exact.**
  `src/crowley/session/daemon.py:134-147` compares every dataclass field. There
  are no runtime writes to `profile.anchor_fingerprints`; measured anchors stay
  in separate driver state, so removing the stale exclusion does not turn
  runtime evidence into configuration drift.
- **Pre-producer failure evidence remains truthful.** After the private request
  directory is created, `src/crowley/session/daemon.py:3628-3637` installs an
  exact `not_started` attempt with all three clocks null before external
  identity resolution. If that resolution fails, the existing failure path at
  `:3743-3815` preserves `identity_before_capture`, the original exception,
  the typed attempt, cleanup, bindings, and the durable owner receipt.
  `tools/gnome-telemetry-region/offline_harness.py:1067-1103` accepts only the
  exact null-clock form, and `:1282-1364` retains that owner failure before
  raising the outer IPC failure. It cannot be mistaken for capture entry or a
  completed sample.
- **The PNG publication TOCTOU is closed narrowly.** After one incomplete read,
  `src/crowley/session/driver.py:487-506` stores the poll result. Nonzero exit is
  still terminal. Clean exit permits exactly one validation bracketed by the
  existing epoch check; incomplete final bytes fail with the fresh diagnostic
  and invalid bytes remain terminal. There is no sleep, retry, fallback, or
  deadline change. The helper's return cannot publish a PNG: the caller at
  `driver.py:3029-3085` still requires the authenticated completion record,
  exact nonce/protocol/branch/rectangle/path binding, byte count and digest,
  exact dimensions, zero exit, post-capture identity, epoch checks, and the
  original absolute deadline before `os.replace`. The deterministic cases at
  `tests/test_session_capture.py:89-184` cover completion during `poll`, clean
  exit with still-truncated bytes, and revocation before the final read.

## Must-Fix

None.

## Should-Fix

1. **Add a direct regression for the new real-IPC `not_started` identity
   failure contract.**

   - Files: `src/crowley/session/daemon.py:3628-3639`,
     `tools/gnome-telemetry-region/offline_harness.py:1067-1092`, and
     `tests/test_session_native.py:1865-1937`
   - The existing pre-admission stop race does exercise a producer-not-started
     outcome, but it allows identity resolution to return, reports the later
     `region_capture` phase, calls IPC directly, and never asserts the
     `producer_attempt`. No current test would fail if the new
     `identity_before_capture` evidence reverted to `{}` and the harness again
     masked the owner error as malformed.
   - Correction: in the existing compiled paused-owner fixture, trigger a real
     external identity-resolution failure before producer entry and pass it
     through owner IPC and `run_paused_diagnostic`. Assert the retained owner
     phase and original error, exact `not_started` plus three null clocks,
     durable failure receipt, zero new Shell/admission/process activity, and
     clean owner state. Do not construct a synthetic owner response or weaken
     identity resolution in production.

## Nits

None.

The retained three-process and pre-fix serial PNG failures remain valid negative
evidence. The narrow helper correction and focused compiled passes do not prove
broad live reliability, and this review does not authorize deployment or live
opt-in.

STATUS: READY
