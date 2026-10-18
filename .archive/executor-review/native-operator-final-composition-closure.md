# Native operator final composition closure (offline candidate)

Status: **candidate complete; development-only and unqualified**.

Worktree: `/home/dev/.cache/crowley/worktrees/native-operator-final-composition-20261018`.
Base: `03258f3`. Only the helper source and helper tests changed in this stage.
The six native/controller/daemon development inputs remain byte-identical to the
reviewed dependency manifest; they are not acceptance evidence.

Implemented closures:

- `X11Screen.wait_reload_boundary` now performs bounded profile-bound
  identity-before/capture/identity-after checks. `absence` uses the accepted
  strict Agent absence classifier on an exact-size private crop; `ordinary`
  decodes a fresh 256px status crop and requires a non-construction boot,
  normal ordinal zero, and an inactive schedule fence. Temporary captures are
  private and removed on every path. Measure uses `absence`; recovery uses
  `ordinary`.
- Reservation, operation, and constructor phase deadlines now remain a
  monotone minimum and reach the actual fixed emitters. Complete chat and
  click budgets are preflighted before physical dispatch; insufficient fixed
  action time refuses. Readiness, gate, action, and press acknowledgement waits
  use the remaining absolute bound while the independent watchdog release
  remains available after phase expiry.
- A canonical reply updates the local reservation expiry before dependent input.
  `CancellationActor.call` accepts an empty reservation ID only for
  `recovery_begin`. Terminal native failure requires a strictly newer PAUSED
  generation and calls fresh recovery with empty ID; the new canonical ID is
  adopted before recovery input.
- An indeterminate operation carrying an already-known reservation ID retains a
  bounded private cleanup horizon and exact ID for cancellation. Unknown initial
  admissions remain indeterminate and are never guessed or retried.

Validation:

- Explicit private-XDG helper suite: `51 passed, 2 warnings, 32.33s`.
- Focused actor/readiness/deadline/recovery groups passed; production readiness
  boundary, strict generation refusal, empty-ID recovery actor routing, and
  exact owner peer routing are covered.
- Ruff check and format check passed for both owned files.
- Python compileall passed for both owned files.

Owned final SHA256:

- `tools/native_calibration_operator.py`: `715138e50b600c08aac4c348831ce550328051e90a50703f1256d3f304f9e03e`
- `tests/test_native_calibration_operator.py`: `1f6d9137b6704a79d43d52393b357d0e7feb55ed2385f7568f61465800c02013`

Dependency SHA256s match the initial manifest exactly:

- `src/crowley/session/controller.py`: `81d377c40d86e0a495a19d665257805e0a79aba2f39adaca088c5f0c85ab819e`
- `src/crowley/session/daemon.py`: `8a483475f3963e1b007e3762b8395f14fb8c4b0b4d9f02a110f823d0b40b2ef1`
- `src/crowley/session/cli.py`: `df59d15c05fc1ae723b99927ce3cecefacd418442ffd08f8e4b75ee349041220`
- `tests/test_session_native.py`: `9b965c678bea35f6cd86231ed407e4433bead0a196093f702f09c602787b6292`
- `tests/test_session_native_regressions.py`: `09c980f99739283b9c86219293bce3d6db236d84b49213022f1ac83f0d689592`
- `tests/test_session_transitions.py`: `cdb4384f3408bb5b21a18445a2c5df8a74dcd271c812ba9b39f9eb171dfce331`

Limitations: the candidate was exercised offline with the copied development
dependencies and fixture adapters. It does not establish native acceptance,
live desktop qualification, or unattended scan qualification. Parent must
compose the accepted native source and perform the independent SessionDaemon /
SessionIPC composition review before any integration or live use.
