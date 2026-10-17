# Auxiliary review round 4

Sol confirmed all addon, plan byte, fence, rendering, heap, chat, lock-order and
deployment corrections. One model parser defect remains; change model.py only.

The actual pinned codex-cli 0.162.1 JSONL exporter emits five completion usage
fields, including cache_write_input_tokens. Completed reasoning items have exact
id/type/text fields, not a Responses-style summary array. The exporter filters
reasoning from item.started; started items are tool/todo activity and are forbidden
at this tools-disabled boundary. Reject every item.started event here.

Correct those exact shapes, retaining all strict ordering, nonempty IDs, exactly
one structured final answer, failures/unknown/extras rejection and the exact benign
diagnostic exception. Update the main owner directly with the exact five usage
field names and completed reasoning shape for its complete lifecycle fixtures.

Do not claim verification against an installed trace without exercising it.
Run one minimal real pinned gpt-6-luna/low tools-disabled CLI request in a neutral
private directory using the existing authorized adapter flags/auth. Capture the
actual JSONL privately and prove the corrected parser accepts that full successful
stream. This is a CLI protocol smoke only: no game scene, recovery, GUI, tool,
service, credential or account action; never count it as live game acceptance.
Check negatives for the old invented summary/four-usage form and all started
items, plus the existing malformed/tool/duplicate/failure cases.

Only model.py is writable in this fix. Main tests remain the engine owner's
scope. No other source, git mutations, production data, service or game input.
Run scoped Ruff/format/compile and actual parser checks. Freeze and report exact
real smoke result/record shapes before final Sol re-review.

## Final re-review correction

Sol's next verdict is NEEDS WORK. The real trace passes and exporter shapes are
correct. Fix these remaining exact-boundary cases in model.py only:

- Type-check every event/item/recursive `type` as a string before set membership;
  array/object types must raise ModelError, never raw TypeError.
- Permit the exact benign diagnostic only after thread.started and before
  turn.started, matching the actual trace; reject later placement.
- Bound each nonnegative usage integer to Rust i64 maximum 2**63-1.
- Reject empty or whitespace-only completed reasoning text, which the actual
  exporter suppresses.

Check those negatives and the existing actual trace. No additional model request
is necessary. Coordinate durable regression cases with the main test owner.

The final enum audit also found structured answer action/state membership before
string checks in _parse/_parse_observation. List/object values must raise ModelError.
Audit every remaining set-membership input in model.py, including requested visual
state/control arguments, so this is one complete correction rather than a series
of equivalent type-order fixes. Exercise invalid scalar/list/object values across
both decision and observation schemas and retain real-trace success.

## Final result

Sol verdict: READY, no must-fix, should-fix or nits. Sol checked 179 malformed
structured-answer cases, 62 lifecycle/order/failure/tool/usage/item negatives,
valid diagnostic/reasoning/i64-boundary streams and the actual private CLI trace.
Final model.py SHA-256:
`4248357f703cefe07b3ce059a1a272d8ba3f51b13941f4065c448288bf50fccf`.
The parent independently reproduced the actual trace, 25 malformed answer cases
and the key lifecycle/i64/diagnostic boundaries. Addon 102-pass verification is
unchanged. Main and native integration still require their separate reviews.
