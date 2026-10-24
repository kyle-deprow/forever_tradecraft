# Mail terminal proof / recovery-test contract

Root owns this shared producer/test contract. Runtime Luna owns Controller and
Daemon plus existing unit tests. Recovery Luna owns only its new recovery test;
composition Luna owns only its new composition test. Driver source is accepted
and frozen. Do not depend on peer messaging availability.

Generic transition_mail_cycle must not grant entry to to_auctioneer. Only a
causal terminal observation of the exact admitted mail sequence may do so.
Keep physical click records separate from later receipt-free observations.

Required new Controller API (runtime producer implements):

```python
accept_mail_terminal(*, capability: MailCycleCapability,
                     outcome_id: str) -> dict[str, Any]
```

It accepts only this live process's exact cycle capability, looks up the already
durable executor outcome by stable outcome_id, and validates its immutable queue,
admitted sequence, original controller/lease epochs, actual raw-frame causal
evidence and successful status (dry_run or succeeded). Caller-supplied IDs or
dictionaries do not create proof. Reject absent, wrong-sequence, failed/refused,
foreign, malformed or merely started records without return-route permission.

For a directly terminal physical click, call accept_mail_terminal after the
real begin_executor_click/finalize_executor_click path has committed its exact
physical outcome. For later asynchronous success, the real owned observation
path commits its receipt-free terminal outcome first, then uses the same proof
gate. It may reuse the last physical pre/post evidence with exact unchanged
button ordinal/counters; it never invents another physical click.

Persist a bounded terminal outcome reference for audit and privately seal live
terminal authority for the cycle. Complete only from opening_ah, with this exact
admitted-sequence terminal proof plus actual fresh AH-open/mail-closed evidence.
A new owner can replay an already-staged complete/blocked outcome without input,
but cannot reconstruct live input/terminal authority from audit references.

Counts: admitted mailUnits is maxMessages, an immutable upper bound. Lua may
collect fewer messages, and dry_run collects none. Terminal proof settles the
budgeted action; it does not assert maxMessages were collected. Keep causally
observed progress separate from admitted maximum, stop reserving mail work only
after accepted terminal proof, and do not invent native counts after advancement
resets progress. Verify lastResult sequence/kind and exact terminal transition.

Recovery positive helpers must drive real Controller begin/finalize executor
methods with valid raw protocol evidence and an explicitly synthetic unit receipt
(no native physical claim), then call accept_mail_terminal with the real returned
outcome identity. Do not jump directly to to_auctioneer, set private progress to
expected values, or seed a staged completion. Negative cases must prove generic
or forged terminal advancement leaves controller/cycle state unchanged.

Keep the existing exact IPC contract and strict native freshness gates. A red
composition test does not justify acting on NO_CHANGE or stale CRS: diagnose
the simulated publisher's elapsed time/publication cadence versus actual runtime
before attributing a continuation failure or changing production behavior.

New terminal observations must not inherit the physical parent's Journal envelope
(archiveOrdinal, archivedAt, commitSequence) or receipt field. Give the new logical
outcome its own Journal envelope and exact physical-attempt/outcome reference.
Validate the original durable physical receipt through that reference; an observer
never creates another physical receipt. Every returned archiveOrdinal must match
its actual artifact filename, and its new commit follows the parent physical one.
Tests that mutate an archived observation locate it by exact outcomeId first,
then assert envelope identity before exercising the proof gate.
