# Native semantic observations for the AH-open postcondition

Status: blocked on missing native facts. This is the smallest candidate for
removing routine Luna observations after native R5 acceptance; it authorizes no
implementation, build, test, deployment, GUI/input, profile, database, network,
or Git action. Existing user authorization remains in force. Later live work is
sequenced by parent technical review and the sole desktop operator.

## Current proof and the bounded target

The accepted static audit is
`.archive/executor-review/runtime-model-boundary-luna-audit.md` at SHA-256
`a188d3012403797a352537e37bb7766652bd64f4776ba777fd275bd87398ebd5`.
Its code-path counts are historical minima, not observed runtime counts. Final
implementation must rebase its citations and hashes on accepted R5 source.

`SessionDaemon._observe_addon_state` currently requires a fresh decoded frame,
matching character/realm, the requested `ahOpen` value, one Luna observation of
the visible facts, and a newer same-boot decoded frame after Luna. For
`auction_house_open`, `_check_named_facts` requires exactly:

```text
scene=world, character=<configured>, realm=<configured>,
modal=auction_house, code="", control=auctioneer_buckler, idle=true
```

The `open_ah` action first verifies a `world` observation, consumes a fresh
`MeasuredAnchor` for `auctioneer_buckler`, performs the admitted pointer gesture,
then requires two consecutive fresh `auction_house_open` observations before the
final named-action verification. The smallest removal is therefore the two
post-action Luna observations. The pre-action `world` observation and pointer
anchor discovery/refresh are separate contracts and remain unchanged.

## Facts actually available now

| required proof | current native source | verdict |
| --- | --- | --- |
| configured character and realm | `Agent.Snapshot().context`, from `UnitName("player")` and `GetRealmName()` | available, subject to existing strict equality |
| fresh boot, sequence, CRC, monotonic capture and X11 identity | strict decoded region frame plus driver identity | available |
| AH-open boolean | cached `ns.ahOpen`, set by `AUCTION_HOUSE_SHOW` and cleared by `AUCTION_HOUSE_CLOSED`/logout | useful event state, insufficient alone |
| `scene=world` | nonempty addon context and movement fields | missing: these do not exclude loading, disconnect, or an overlay |
| `modal=auction_house`, `code=""` | the same cached `ahOpen` event bit | missing: it does not prove current visibility or absence of a conflicting error/modal |
| `control=auctioneer_buckler` | no addon field or verified native API | unavailable from the addon; the fresh anchor proves this before input |
| `idle=true` | scanner phase, chat edit, combat/death and speed fields | missing: scanner idle is not visual/action readiness, and the current contract never defines a safe deterministic equivalent |

Accordingly, no call removal is ready. Constructing the missing strings from
`ahOpen`, remembered coordinates, a prior event, or the fact that the addon is
publishing would manufacture evidence. The addon may genuinely supply a fact
only through a snapshot-time native API or UI object whose meaning and presence
have first been verified on the actual build. An unavailable source publishes
`unknown` and cannot qualify the postcondition.

## Minimal truthful producer contract

First produce a bounded capability receipt for the accepted client build. It
must identify, without input, whether snapshot-time sources exist for all of:

1. player-in-world/current scene state;
2. current AH interaction type and actual AH surface visibility;
3. every blocking modal/error state relevant to this action, including its code;
4. a deterministic action-readiness state whose meaning replaces visual `idle`.

Candidate APIs or frame globals are hypotheses until that receipt shows their
exact return types, lifecycle across `AUCTION_HOUSE_SHOW`/closed, and behavior in
the relevant modal cases. Event callbacks alone do not satisfy the receipt. The
addon cannot truthfully publish `auctioneer_buckler` after the click unless an
actual API binds that named unit/control; otherwise control proof must remain in
the consumed pre-action `MeasuredAnchor` and the action contract must explicitly
compose it with the post-effect observation.

If every source is verified, make one atomic strict protocol migration. A new
exact `semantics` object uses tagged values, never permissive booleans:

```text
world:        {state: present|absent|unknown, source: <pinned enum>}
interaction:  {kind: auction_house|none|unknown, visible: true|false|unknown,
               source: <pinned enum>, eventEpoch: integer}
blockingModal:{state: none|present|unknown, kind: <bounded enum>, code: <bounded>}
readiness:    {state: ready|busy|unknown, reasons: <sorted bounded enum array>}
```

The schema validator requires exact keys/types/enums and cross-field rules:
`ahOpen=true` agrees with a visible current AH interaction; `ahOpen=false` cannot
coexist with that interaction; `ready` requires world present, AH visible, no
conflicting modal/error, inactive chat edit, alive/out of combat, and every
verified readiness predicate. Do not equate scanner `ready`/`scheduled` with
this readiness. Preserve the raw constituents so `idle=true` is never asserted
from an opaque aggregate. Unknown or contradictory values remain valid telemetry
diagnostics but are ineligible action evidence.

The post observer may map a fully known record to `scene=world`,
`modal=auction_house`, `code=""`, and `idle=true`. It must take character/realm,
boot/sequence/CRC/capture time from that same decoded frame and bind the current
X11 identity/generation/target. Control remains a separate composite proof: the
driver must verify that this exact action consumed a fresh generation-bound
`auctioneer_buckler` anchor and an admitted XI2 gesture before it accepts the
semantic post-effect. Do not insert `control=auctioneer_buckler` into addon facts.

Two independently captured post frames must still have the same boot, strictly
increasing sequences/timestamps, the exact identity and generation, and fully
known equal semantic facts. The existing settle count, age limit, absolute wait
deadline, and rejected-observation reset remain unchanged.

## Proposed ownership if the capability receipt succeeds

Implementation begins only after accepted R5 and a parent-approved capability
receipt. Luna owns only:

- `addon/Crowley/Agent.lua` for snapshot-time tagged semantics;
- `src/crowley/session/protocol.py` for the exact schema/cross-field rules;
- `src/crowley/session/daemon.py` for the deterministic AH-open observer only;
- `src/crowley/session/driver.py` for explicit anchor-plus-post-effect composition;
- `tests/wow_harness.py`, `tests/test_addon.py`, and `tests/test_session.py`;
- `tests/test_session_runtime.py` and `tests/test_session_transitions.py`.

`Scanner.lua`/`Scanner.Status` remain unchanged: their phases cannot be promoted
to visual idle. No controller, Guardian, model, anchor provider, input, profile,
native producer/build, market, addon scheduling, or service change. A schema
migration must update producer, strict decoder fixtures, and consumer atomically;
there is no schema-3 fallback after cutover.

## Failure semantics and meaningful tests

Before cutover, retain the current Luna postcondition. After the reviewed atomic
cutover, missing/unknown/malformed/stale semantics fail closed; they never fall
back to Luna, reuse an older frame, retry the click, or relax named facts. A
post-input failure records the action phase, clears the settle run, revokes the
action generation through the existing path, releases held input/processes, and
requires ordinary recovery. It cannot turn `ahOpen` into success by itself.

Tests must cover the real Lua producer through strict framing/decoder and the
default daemon/driver path, including:

- cached `ahOpen=true` with hidden/unknown interaction, wrong scene, conflicting
  modal/error, busy/unknown readiness, wrong identity, and wrong character/realm;
- exact protocol rejection of missing/extra keys, invalid tags, contradictions,
  nonfinite/oversized fields, stale event epochs, and legacy schema after cutover;
- two fresh consecutive post frames, plus boot/sequence/timestamp reuse and a
  rejected middle frame that clears settlement;
- refusal when the matching anchor was absent, stale, wrong-control, reused, or
  not consumed by the admitted gesture; cancellation still releases everything;
- a successful post path with no Luna observation, and a counter assertion that
  the pre-world observation and anchor calls remain present as applicable;
- no-pointer-motion versus pointer-motion paths proving refresh stays separate;
  unknown semantics must not trigger another input or a Luna fallback.

Sol and actual Opus review every executor edit before parent integration. A later
sole-operator live qualification must show the exact accepted build/source and
two-frame postcondition without weakening R5/Guardian/human-proof fences.

## Honest remaining call counts

Removing only the two AH-open post observations leaves one Luna pre-world named
observation. With the current visual anchor fallback, add one Luna call for the
initial `auctioneer_buckler` anchor and another when pointer motion requires the
fresh post-motion refresh: source minimum 2 without pointer motion, 3 with it.
A separately accepted native anchor provider could reduce those anchor calls,
leaving the pre-world call; it is outside this plan. Retries remain runtime
dependent. This slice cannot support a zero-call AH reopen or full-cycle claim.

If any world/interaction/modal/readiness source remains unverified on the real
client, status stays `blocked_missing_native_fact`, the protocol is not migrated,
and the Luna postcondition remains in place.
