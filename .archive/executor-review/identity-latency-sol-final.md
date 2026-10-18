# Sol final closure review — native identity latency Stage 1

Candidate reviewed: `/home/dev/.cache/crowley/worktrees/identity-latency-final-20261017`

## Identity, scope, and evidence

- Base and merge-base are exactly `f213e1fdfb19621d0b5c267307b34eab8c6d22bf`.
- The worktree fence is exactly the three modified tracked files plus the new sidecar. No other tracked or untracked candidate path is present.
- Plan SHA-256 verified: `397bccaa859a7e39c31eef7555aa5f10764dd63329f118478e4004ac5ca2d685`.
- All final-freeze owned hashes verified:
  - `src/crowley/session/driver.py`: `ca0ca123d0fa09d8361c8632d9cc1c2c501d87adf99cb3cc268688dd4291a166`
  - `src/crowley/session/daemon.py`: `972c74057003bb13931cf257fffeaf6b77a802689814c4aa7c35b46c01bb23ae`
  - `tests/test_session_native.py`: `7a234b2f0ba4a2cd0ce9d155b3265dc91df6537c8fa914f87abcd1cea634cc37`
  - `tools/gnome-telemetry-region/identity_latency_sidecar.py`: `f7c8bbf52884d94f230878ac90efe0a29d798ec6ca7c30331c0402976b1fc30c`
- All six read-only reference hashes in `identity-latency-final-freeze.json` verified exactly.
- The parent expected-binding manifest is consistent and ready for the planned post-integration diagnostics: its SHA-256 is exactly `5a3e3311bbc5f4f601a906b637857a9de88160f357183512027006e5b929c67a`, its file mode is 0600, and its parent mode is 0700. Its driver and daemon hashes match this frozen candidate; its other five source hashes independently match the exact `f213e1f` blobs. Its raw config, semantic config, and producer hashes exactly match the parent-supplied independently verified pins (`0dde50b9...c12c3a1`, `947d61e1...a8af96e`, and `cb938cab...be2396`). This acceptance is only for the planned three private paused diagnostic samples after integration and the sole-Luna quiet restart; it makes no qualification or Rust-trigger claim.
- I reviewed the actual full tracked diff and the complete new sidecar. I ran no tests, builds, live GUI/input, service, restart, or sample commands. The frozen evidence reports the prior immutable R3 broad suite at 297 passing, final focused identity tests at 9 passing plus Ruff/static checks, and the actual compiled-owner composition at 1 passing in 57.59 seconds.

The requested R2 closures are present and coherent. Real owner identity refusal and cancellation artifacts are now asserted; owner post-capture identity and config drift keep their causal phase/error; final-source `KeyboardInterrupt` is persisted and propagated; cleanup faults restore the `ContextVar` for the next request; descriptor reads compare the full metadata tuple after the read and against the final path; config is rehashed after the accepted loader; event truncation is retained in sanitized samples; and the derived parent tail is emitted only when the response owner-return clock is within the parent request/receive bounds.

## Must-Fix

1. **Barrier records do not enforce the closed artifact shape and can carry arbitrary fields into the sanitized report.**
   - **Where:** `tools/gnome-telemetry-region/identity_latency_sidecar.py:401-413` and `:600-613`.
   - **Reachable behavior:** `validate_artifact` checks that each barrier is a dictionary with the expected barrier name, then constructs a separate five-key dictionary for `_duration_record`. It never checks the original barrier dictionary's key set. A descriptor-valid profile containing an extra barrier field such as `"error"` or `"path"` therefore passes validation, and `read_response_profile` copies the original `artifact["barriers"]` into the supposedly sanitized report. This violates the closed private artifact contract that rejects unknown fields and excludes raw errors and paths. Conversely, a barrier with the right `barrier` name but a missing timing key raises `KeyError` while indexing at lines 407-410; `read_response_profile` catches only `IdentityLatencyError`, so malformed diagnostic evidence can abort report construction instead of being classified `artifact_invalid`.
   - **Required correction:** require the original barrier object to have exactly `barrier`, `start_monotonic_ns`, `end_monotonic_ns`, `duration_ns`, and `outcome` before indexing or copying it. Add regressions showing that an extra raw field and a missing timing field are both rejected as `artifact_invalid` and never appear in the sanitized report.

## Should-Fix

None.

## Nits

None.

STATUS: NEEDS WORK
