# Sol executor click review, round3

Status: NEEDS WORK. Exact11 frozen hashes matched; parent132 click/policy and114
schema cases passed. Accepted improvements: staged-outcome recovery across four
bundle write boundaries, later holds, refreshed call-local receipts, cleanup
failure archival, public two-message continuation, CLI/native-construction gates.

Must fix:

- Overall schema lacks seq, and admission does not compare its stored generation
  or lease. Bind exact queue/seq/generation/lease before capture/anchor/intent,
  with separate drift regressions.
- Pre-input intent contains only hash/length/CRC. Retain and validate actual
  bounded rawFrameHex before motion, including decoded CRS/projection binding,
  and prove restart after dispatch before finalization retains it without retry.
- The public two-message queue has no non-mail successor. Add one and assert
  exact decoded public response/counter transition; private validation alone is
  insufficient.

Should fix:

- Add final blocking-capture races for pause, lease and durable-attempt changes,
  asserting no rate precommit or physical press. Generation alone is covered.

The public foreign-owner proof currently rejects capability mismatch in
mail_wait. Parent separately requires an empty-owner mail_items distinguishing
case. Luna Round4 owns these corrections; runtime scheduler still waits.
