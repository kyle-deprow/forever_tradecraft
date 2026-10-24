# Sol mail-loop controls final Round6 review — READY

Scope reviewed: the two Must-Fix items from `sol-review-round5.md` in the
complete frozen `tests/test_session_mail_loop_controls.py`, current progress,
the exact one-file manifest, and the retained affected-case result. Previously
accepted race, resume, CLI, expiry, reserve, capability, frame/evidence,
projection/counter and Journal-envelope proofs were checked for preservation,
not reopened. Production source was not reviewed as a frozen candidate and no
pytest was run by Sol.

Frozen controls SHA-256 before and after the full review:

`b2ce7f33523a73300f9fbafd4e6d8efedd10a5c4942233e56ad17795c67c5ee6`

The manifest agrees with that hash. Device, inode, size, mtime, ctime and mode
also remained unchanged across the read.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

## Closed Round5 findings

- `_assert_unique_executor_artifact` enumerates every executor artifact with the
  exact nonempty outcome ID, requires exactly one match, requires the exact
  zero-padded `archiveOrdinal` filename, and compares the complete decoded
  payload with the JSON-canonical checked record. Direct outcomes invoke it;
  asynchronous cases invoke it separately for the physical parent and the new
  terminal observation.
- `_retain_driver_receipts` wraps the actual driver instance read-only, forwards
  arguments and the returned object unchanged, and retains only the invocation
  carrying the one-use click permit—the inner physical `DesktopDriver.run`, not
  its outer admission wrapper. Both direct failure/refusal records and async
  physical parents require exactly one such receipt and compare their durable
  receipt to its JSON-canonical call-local value. Async terminal observations
  retain the strict schema-level absence of `receipt`.
- The independent capability identity, actual daemon frame-record inputs,
  decoded raw bytes and SHA-256/length/CRC, full pre/post projections,
  result/counters, exact Journal envelope, unchanged async parent, exact parent
  references, and no-return/no-extra-input assertions remain in the affected
  cases.
- All 22 prior test parameterizations remain present, including public control
  races, staged/restart resume fences, CLI and malformed identity boundaries,
  fixed first-attempt expiry, coherent wall sampling and immutable overall-cycle
  future-work reserve.
- The retained focused log reports `4 passed, 18 deselected in 38.49s`. The
  unchanged prior full controls log reports `22 passed in 60.91s`. Sol did not
  rerun either command; parent default/source/composition verification remains a
  separate gate.

Status: **READY** for the frozen controls test slice.
