# Pure mail-loop policy contract — phase C preparation

This is an offline policy seam only. It does not schedule, route, click, mint
leases/capabilities, write a journal, or authorize a protected operation. Runtime
wiring remains blocked until the reviewed phase-B controller/daemon/IPC changes
are ready.

## Public API

`crowley.session.mail_loop.admit_mail_cycle(snapshot, binding, boundary,
bounds) -> MailLoopDecision` requires the actual validated schema-6
`crowley.session.protocol.Snapshot` class and immutable caller-owned
observations:

- `MailLoopBinding`: process-local opt-in (`enabled`, default `False`),
  `generation`, exact `queue_id`, `seq`, `house`, and `character`. An enabled
  binding must have positive generation/sequence and non-empty identities.
- `MailLoopBoundary`: current process generation; explicit `session_mode` and
  repeat phase; controller evidence `ack_loaded_uid` and `status_last_uid`
  (empty means no ACK proof yet); durable seen ACK UIDs; unresolved action,
  reconciliation, stop, and closeout flags; optional last actual sweep start;
  and caller-supplied current time. `ack_loaded_uid` is a distinct controller
  proof, not a duplicate of the frame ACK array. The boundary does not
  duplicate frame pending, scanner, due, house, or character fields.
- `MailOperationBounds`: finite positive seconds for route to mailbox, retained
  mailbox world-click, each mail click, each mail postcondition wait, route back
  to auctioneer, guarded AH reopen, and safety margin.

The function is pure. Exact dataclass types, immutable collections, and all
operation-bound numeric fields are validated before semantic disabled/deferred
returns; malformed inputs raise `MailLoopPolicyError`. A disabled binding may
use only its zero/empty defaults, with exact integer types for `generation` and
`seq` and exact string types for `queue_id`, `house`, and `character` checked
before those sentinel comparisons (so `False`, `0.0`, and `None` are not
accepted as dry-run defaults).
Valid but inadmissible observations return a deferred `MailLoopDecision` with a
bounded reason. An admitted decision is advisory and carries no authority.

`MailLoopDecision` returns `admitted`, `deferred`, `reason`, exact queue/ACK
identity, `admitted_seq`, `mail_units`, `effective_due_at`, separate fixed
`latest_start_at` and `completion_deadline_at`, and expanded `MailBudget`.
`reason` is `admitted` only on success; callers must not infer a lease or
continuation from any other field.

## Admission matrix

Admission requires all of the following:

1. opt-in is enabled and its process generation equals the current boundary
   generation;
2. `session_mode == "repeat"` and repeat phase is exactly `WAIT_DUE`;
3. both controller ACK proofs are non-empty and exact
   (`ack_loaded_uid == status_last_uid`), the proof appears in the frame's
   authoritative `loaded.ackedIds`, and it is absent from the durable seen-ACK
   set;
4. the frame's authoritative `pending.ids` is empty and all unresolved
   action/reconciliation/stop/closeout flags are false;
5. the frame's authoritative scanner phase is exactly `ready` or `scheduled`;
6. the frame wall time is not later than caller `now`, and a positive actual
   prior sweep start is supplied and not later than `now`;
7. the validated frame has `ahOpen=true` and an executor with exact bound
   queue/sequence/house/character, `availability=valid`, current kind
   `mail_collect`, phase `ready`, and all in-flight/blocked/latched/ambiguous
   flags false;
8. the frame's top-level house key and context character independently match
   the binding, and current mail progress is exactly `workDone=0` and positive integer
   `workTotal`.

Frame `loaded.ackedIds`, `pending.ids`, scanner phase/due, wall time, house,
and context character are authoritative; no duplicated boundary copy is
trusted. A disagreement between controller ACK proofs defers as
`ack_status_mismatch`; an absent proof defers as `ack_missing`; a proof absent
from the loaded frame defers as `ack_wire_mismatch`.

The AH-side admission deliberately does not inspect `buttonVisible` or
`clickReady`; those are mailbox/open-frame facts for a later physical click.
It also does not treat either addon arm as authority and never infers a
capability.

The admitted sequence is exactly the current sequence. No successor action is
selected or budgeted. A repeated ACK is deferred even when every other field
is unchanged.

## Fixed budget and due boundary

The effective due is exactly:

```text
max(frame.scanner.dueAt, last_actual_start_at + 900 seconds)
```

No cadence is invented from `now`. For exactly `workTotal` current mail units:

```text
operational = route_to_mailbox
      + world_click
      + workTotal * (mail_click + mail_postcondition)
      + route_to_auctioneer
      + ah_reopen
total = operational + safety_margin
latest_start = effective_due - total
completion_deadline = effective_due - safety_margin
```

Both returned times are absolute and non-extendable. Admission fits when
`now + total <= effective_due`; at exact `now == latest_start`, the remaining
time to `completion_deadline` equals the complete operational budget (the
reserved margin is not spent). A later `now` returns `deferred` with reason
`insufficient_due_budget` and no state/input effect. Every future nested
operation must receive the minimum of its own bound and the unchanged cycle
completion deadline; that runtime rule is not implemented by this pure slice.

Normal ineligible modes (non-repeat session/phase, missing ACK or prior start,
wire/boundary disagreement, pending work, scanner state, or identity mismatch)
return bounded deferrals. Malformed types raise `MailLoopPolicyError`.
Boundary collections are exact immutable `frozenset` values; no mutable/list/
string substitute is coerced. Frame arrays remain the validated wire arrays.
Boolean/fractional current work counts defer defensively rather than being
coerced; numeric overflow in supplied bounds raises `MailLoopPolicyError`.

## Evidence boundary

`tests/test_session_mail_loop_policy.py` uses one actual Lua-produced schema-6
Snapshot decoded through the installed CRS1 decoder, with ACKs loaded into the
actual Lua Data.lua projection and due/pending/scanner/identity facts derived
from that frame, as a data-shape oracle. It also round-trips a codec-valid
`scanner.phase="ready"` frame and admits the current mail action. Negative
pending/scanner cases are codec-valid (`pending` metadata is coherent and
scanner uses `item`), not malformed wire shortcuts. It does not claim default
SessionIPC/runtime composition and does not operate a game or service. Runtime
tests and durable checkpoint/restart behavior belong to the later phase-C
wiring after phase B review.
