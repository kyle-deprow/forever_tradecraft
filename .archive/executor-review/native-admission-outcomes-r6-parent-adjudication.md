# Parent adjudication: native admission outcomes R6

Status: rejected before full parent suite or external source review, 2026-10-18.
The worker freeze and closure remain historical candidate claims, not acceptance.
Root independently verified the six-file fence, base/source hashes, retained test
log hashes and scoped static checks. The actual compiled public PAUSED composition
test passed independently: 1 passed in 5.35 seconds, exit 0. This is real progress.

The pure absence classifier nevertheless accepts two parent-created images that
must not qualify as confirmed HUD absence. Both production PixelDecoder calls
raise ProtocolError. `_strict_native_absence_image` returns true for both:

- A completely black 256x256 RGB loading crop. SHA-256:
  `3b93f26267630963185ee67d8020972faee108a7bca80db725817e4680c9955c`.
- A genuine encoded Agent status image with combined header and payload damage:
  RGB (99,121,143) painted over rectangles (0,0,16,2) and (96,96,192,192).
  SHA-256: `d28917c2061dfb5f28ac28275d1e3a05c2f318e252e9d121d264c233408054ed`.

Private evidence is in
`~/.local/state/crowley/executor-evidence/runtime-relink/native-admission-outcomes-r6-parent-20261018/`:
`black-loading.png`, `encoded-header-and-payload-occlusion.png`,
`absence-counterexamples.json`, and `compiled-public.log`. No raw images are
published. The prepared full-suite runner in that directory was not executed.

The intact-magic or fully-binary-grid checks do not cover loading ambiguity or
combined damage. The required correction is conservative fragment recognition
and rejection of ambiguous/loading evidence with meaningful ordinary positives,
not a percentage threshold adjusted only to these examples. Missing public
operation/CLI and race/durable-failure coverage also remains required by the
original R6 plan. Follow-up is bounded in PLAN-native-r6-absence-coverage-fix1.md,
in a new worktree; this failed candidate stays frozen. No promotion or live native
qualification occurred.
