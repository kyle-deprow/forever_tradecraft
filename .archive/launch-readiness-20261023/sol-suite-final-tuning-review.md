# Sol final-suite tuning review — READY

Scope reviewed: `.archive/PLAN-suite-final-tuning-20261024.md`, the updated
removal rationale and progress record, and the three paths frozen by
`suite-final-tuning-sha256.json`.  Production source was unchanged and was not
re-reviewed.  I did not run pytest, the game, services, or a database while the
parent full-suite verification was active.

All three frozen paths matched the manifest before and after this review.  Their
device/inode, size, timestamps, mode, owner, and SHA-256 were unchanged while
inspected.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

## Coverage-equivalence findings

The removed approximately 70-line
`test_daemon_async_terminal_clears_matching_cycle_continuation` contributed
four private-owner observations beyond its shared two-message Lua/IPC flow.
Each is retained at the same causal boundary in
`test_armed_mail_loop_requires_two_fresh_public_confirmations`:

| Removed observation | Retained composition boundary |
| --- | --- |
| First started click creates a non-null daemon token equal to the controller token. | `tests/test_session_mail_loop_composition.py:1755-1757`, immediately after the first real public confirmation. |
| Second started confirmation leaves daemon/controller token ownership equal. | `tests/test_session_mail_loop_composition.py:1806-1810`, immediately after the fresh second confirmation and second physical click. |
| The later asynchronous terminal clears both private tokens and enters `to_auctioneer`. | `tests/test_session_mail_loop_composition.py:1822-1829`, immediately after the real Lua mail event and daemon observation. |
| Ordinary completion reaches `WAIT_DUE` without stale-owner poisoning. | `tests/test_session_mail_loop_composition.py:1848-1855`, with both private tokens additionally required to remain `None`. |

The retained case is a strict superset of the deleted flow.  It still drives
the actual Lua mailbox events and public IPC, requires two fresh confirmations,
caps the action at exactly two physical clicks, preserves the one-second addon
gate, refuses competing input, validates both physical archives and the raw
receipt-free terminal observation, leaves the craft successor untouched,
completes the return/AH/Guardian lifecycle, and audits exact native deadline
origins.  No native, raw-evidence, receipt, click-rate, ownership, queue,
deadline, or normal-resume assertion was weakened.

## Parallel configuration and evidence

- `pyproject.toml` uses the explicit bounded setting `-n 16 --dist worksteal`;
  it does not use an unbounded/automatic worker count.
- The reviewed host reports 16 processors and about 23 GB available memory.
  `pytest-xdist` remains an explicit development dependency.
- `testpaths` remains `tests`; no marker, path, or item exclusion was added.
  Database suites retain their separately documented explicit serial override
  and are skipped by their existing environment gate in the plain default run.
- The affected retained default and armed composition cases passed with the
  configured 16-worker default: **2 passed in 54.83s**, external **55.04s**,
  with no skips.  Static, formatting, compilation, and diff checks are recorded
  green.

The parent bare default run is still the authoritative proof of the under-180s
whole-suite target.  Its completion is an integration/performance gate, not a
remaining defect in these three frozen changes.

Status: **READY**.
