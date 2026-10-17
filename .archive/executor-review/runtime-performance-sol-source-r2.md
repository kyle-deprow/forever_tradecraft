# Runtime performance Phase 1 source review R2

Reviewed only the four-file candidate in
`/home/dev/.cache/crowley/worktrees/addon-schedule-20261017` against canonical
plan SHA-256
`08479c262c6b36e152f6b6ceee8f714aa360633f83c9020ae5b4a5354447de80`
and R1 source review SHA-256
`b72ca4507826cf7d4cc152f48a6765d9240f7346c6aa4c6d1a1c6522d71347f0`.
The reviewed candidate hashes are:

- `tools/session_performance.py`: `23c0294b9037ef8edb39fd49d6af61a43216f4997298f590a6d92a838eb774fe`
- `tests/test_session_performance.py`: `a9133ed64f06591303f7c5849959cb4a281f16d1cc01afdbfa617fba756bab75`
- `docs/RUNTIME_PERFORMANCE.md`: `becbcbe0c6b9bf1154e1254661f5cc39f99dba87ae73f1c0c3d2ed38c3b62c5c`
- `.archive/executor-review/runtime-model-boundary-luna-audit.md`:
  `a188d3012403797a352537e37bb7766652bd64f4776ba777fd275bd87398ebd5`

The parent replay remains unchanged at SHA-256
`17df74e9da169cdec2f73894749a58837fb1ed1538c793dfadc8d5ba278c83b8`.
It records 100 successful strict decodes with no failures, p95 wall
63.647683 ms, p95 process CPU 63.396576 ms, and an honest
`insufficient_evidence` decision. It still provides no accepted live
source/config/producer binding, paired live intervals, or eligible runs and
does not support a Rust decision.

The R1 findings are closed:

1. `tools/session_performance.py:394-423` now binds the receipt read to one
   opened descriptor, checks device/inode/size before the capped
   `MAX_RECEIPT_BYTES + 1` read, rechecks the descriptor afterward, and refuses
   size or identity drift. `tools/session_performance.py:83-101` maps excessive
   JSON nesting to a fixed sanitized error. The focused growth and nesting
   regressions are at `tests/test_session_performance.py:313-335`, and
   `docs/RUNTIME_PERFORMANCE.md:19-30` describes the actual bound accurately.
2. `tests/test_session_performance.py:138-207` now exercises disagreement
   between valid binary pixels in one 2x2 cell, an advancing Lua-rendered
   sequence, stale-sequence refusal, unexpected and one-time-accepted boot
   changes, and a valid-CRC schema refusal. These tests reach the intended
   public decoder branches rather than substituting copied decoder logic.
   `docs/RUNTIME_PERFORMANCE.md:41-47` correctly separates those strictness
   regressions from the fresh-decoder timing replay at
   `tools/session_performance.py:292-298`.
3. `.archive/executor-review/runtime-model-boundary-luna-audit.md:6-24` binds
   its citations to the frozen primary R4 source. I independently matched the
   recorded hashes and line counts for daemon, driver, controller, model, and
   the three cited test files. The call-site and stable-boundary citations at
   `.archive/executor-review/runtime-model-boundary-luna-audit.md:34-88` now
   resolve to those exact files, including anchor measurement at
   `driver.py:5976-5982`, post-motion refresh at `driver.py:2545-2557`, and the
   three current named observations plus optional anchor/refresh costs for AH
   reopening. Static minima remain explicitly distinct from unknown runtime
   counts.

The public decode interval, separate PNG interval, process-CPU and monotonic
wall samples, ceil quantiles, null private substeps, bounded pure planners,
safe receipt diagnostics, and current `insufficient_evidence` result remain
coherent. The audit preserves both Luna anchor boundaries, makes no whole-cycle
zero-call claim, and proposes bounded future instrumentation and semantic-
provider review without changing production behavior or implementing Rust.

This was a read-only source review. I did not run tests, the CLI, the game,
Docker, a database, the network, or Git, and did not edit the candidate.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
