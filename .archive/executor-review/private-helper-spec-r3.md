# Private native handshake helper r3

The private helper is frozen for review at
`/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-handshake-once.py`.
The R2 baseline was `dd4778b38802d2e68dacfd3b9f6453f03280cdaed3d6e79fef8084ca2d4349e4`;
the R3 source hash is recorded in `private-helper-freeze-r3.json`.

R3 changes only the Enter World action.  After the fresh screenshot/template
match and the existing identity plus `bootstrap_ready`/`nativeBootstrapReady`
guards, it moves the pointer to the matched root coordinates, rechecks the
identity and phase, queries actual root pointer coordinates and the X11 target,
and refuses before press if either differs or the target is outside the sealed
client target set.  It then rechecks identity and phase immediately before one
owned XTEST `mousedown 1`, holds for 150 ms, and releases with `mouseup 1` in
`finally`.  Once the helper admits the button as owned, release is attempted
without a phase/generation guard so revocation during the hold cannot leave the
button down.  The receipt records method, root coordinates, observed target,
outcome, and monotonic move/press/hold/release timings; a release error is
retained separately from the operation error.

The existing dynamic-generation, native-operation-kind, phase/flag, identity,
bootstrap TTL, readiness, chat, and no-extra-capture guards remain unchanged.
The exact 100-update phase still dispatches no helper capture or input.  The
helper has not been run against the live game, and no GUI input, native
bootstrap/calibration, kernel reset, service, profile, or runtime operation was
performed for R3.

The dry guard script remains
`.archive/executor-review/test_private_helper_guards.py`.  Its retained R2
status cases and handshake-entry sentinel passed, and R3 adds:

* guarded dispatch-order proof for identity/phase, move, post-move pointer,
  final identity/phase, press, hold, and unconditional release;
* wrong root-coordinate refusal before `mousedown`; and
* injected hold failure with the owned `mouseup` still dispatched.

The test uses fake status/backend/input hooks only.  Output is retained in
`private-helper-guards-r3.log` with exit marker `private-helper-guards-r3.exit`.
