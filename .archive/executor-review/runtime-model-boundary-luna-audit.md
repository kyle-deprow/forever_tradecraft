# Deterministic runtime model-boundary audit

Status: candidate static audit; acceptance pending; no production or runtime
source was changed. Decision: `insufficient_evidence`.

Every source citation in this report was rechecked against the frozen primary
R4 source under `/home/dev/repos/pegasus/src`, rather than the older daemon in
this detached candidate worktree. A source-level code-path minimum describes
one successful branch; it is not an observed runtime count. Retries, polling,
settle rejection, recovery, and owner scheduling can increase it. No retained
journal records model method calls, so unknown runtime counts stay unknown and
are never represented as zero.

## Source and evidence identities

| artifact | SHA-256 | primary line count |
| --- | --- | ---: |
| `src/crowley/session/daemon.py` | `282e76c0c900efa17a7515f1bc785afafda3a8b80c6602aabe4ccafdad03f3a4` | 5339 |
| `src/crowley/session/driver.py` | `27b3bdf0c8fb323911eda86557296b9c36b8bd1ebdc20ac535a3301f2ce896f8` | 6683 |
| `src/crowley/session/controller.py` | `87f6c48b886ba2efbdabc30342ac29264b40dce69313ada55cae054bb761693f` | 3432 |
| `src/crowley/session/model.py` | `59a7a4f409ab6e9a47e066dc6495a89e621fc6ebc5e98c6021d5bf2d25be6efa` | 996 |
| `tests/test_session_runtime.py` | `9d634f603968e85c253dfc4116102deedb09fc18e2ed6b5542c3c1b0d2d64868` | 2265 |
| `tests/test_session_transitions.py` | `07ddff7b102698638ce13f75a8056d5597f1852cfa753c0b437321ddedcd8804` | 1813 |
| `tests/test_session_regressions.py` | `0f24d66b87879c241a9ad7c7a31e1b6473b7d14fef917b64bd70a9c6dd6efad2` | 1700 |
| fifth parent receipt | `6070e10a60fdd7b09cfae330315b13f005a1584ea6ef6aaf3fc04f810e6dabe7` | — |
| sixth parent receipt | `980e7b58b5ea5536ec2a651662b2bc242abb4f0c274fe3d679f4d5fb5460cd21` | — |
| seventh parent receipt | `42fcd33562bca54b424ad5ec285d9f634eef402bdd9159ab98677aeb89c51eab` | — |

These identities are measured-source and retained-evidence identities only.
They do not establish a reviewed live instrumentation contract. Remembered
coordinates, ignored modal state, fake identity, bypassed admission, and a
human-takeover path remain out of scope.

## Actual model call sites

| call site | primary source lines | call and condition | static interpretation |
| --- | ---: | --- | --- |
| `_measure_pointer_anchor` | `daemon.py:1236-1332` | A complete configured `MeasuredAnchor` at `1255-1272` returns without Luna. The fallback captures a fresh crop and calls `_observe_model` at `1327`. | 0 or 1 model observations; the fallback is model-assisted. |
| `_observe_addon_state` | `daemon.py:1613-1707` | Fresh native identity/boot/sequence/AH facts are checked at `1622-1651`; visual inference is called at `1659`; a newer native frame is required at `1677-1687`. | At least 1 model observation per accepted named addon observation. Poll and retry count is runtime-dependent. |
| `_observe_named_state` | `daemon.py:1710-1740` | `world` and `auction_house_open` delegate to `_observe_addon_state` at `1712`; other named scenes capture and call `_observe_model` at `1728`. | 1 model observation for a successful non-addon named scene; addon scenes use the preceding row. |
| `_observe_model` | `daemon.py:2004-2027` | The common wrapper passes the verified crop, requested facts, and finite timeout to `self.model.observe` at `2027`. | One adapter invocation per caller above; the wrapper does not poll. |
| `_recover_login` | `daemon.py:3434-3453` | `self.model.decide` is called at `3437`; the durable recovery budget is consumed before dispatch at `3442-3453`. | 1 decide per recovery decision, plus the selected named action's own boundaries. |
| `_observe_route` | `daemon.py:2286-2376` | Motion admission and a fresh native frame precede `self.model.observe_route` at `2341`. | 1 `observe_route` per successful route-evidence call. |
| `_observe_viewport` | `daemon.py:2378-2430` | Motion admission and a fresh native frame precede the strict provider call at `2397`. | 1 `observe_viewport` per successful viewport-evidence call. |

Route and viewport calls are motion-only boundaries. Their callers are camera,
movement, pulse, delta, and waypoint paths; they are not reachable from the
stable scan, reload, upload/ACK, AH-reopen, or closeout branches audited here.

The pointer anchor path is separate from named-state inference. A native
provider is measured by `driver.py:4725-4758`; the refresh provider is
`driver.py:4760-4794`. A real X11 pointer action measures the named anchor just
before dispatch at `driver.py:5976-5982`, installs the motion refresh callback
at `driver.py:6278-6282`, and invokes it after motion at `driver.py:2545-2557`.
The daemon fallback behind that provider is `_measure_pointer_anchor` above.

## Stable action boundary table

The table has five columns deliberately: action, deterministic boundary,
model-assisted boundary, source-level minimum, and observed runtime. “Unknown”
means no journal or counter exists; it does not mean zero.

| action | deterministic boundary | model-assisted boundary | source-level code-path minimum | observed runtime |
| --- | --- | --- | --- | --- |
| Already-open scan start and monitor | `_advance` checks ready/due/AH/identity facts and starts the scan at `daemon.py:4948-4993`; `_command` persists intent and performs fresh EditBox readback at `daemon.py:1850-1946`. | None on the already-open branch. | 0 model calls. | Unknown; no real model counter or call journal. |
| Completion and reload-buffer verification | Completion consumes a new UID/finished time at `daemon.py:4979-4993`; quiet-save dispatch and decoder boot arm are `daemon.py:4995-5005`; stable SavedVariables verification is `daemon.py:5007-5020`. | None; decoder, file, UID, and boot checks are deterministic. | 0 model calls. | Unknown; receipts do not separate decoder or model stages. |
| Upload and loaded-ACK reconciliation | Upload and Data.lua witnesses are checked at `daemon.py:5021-5064`; ACK publication/reload and loaded UID plus pending exclusion are checked at `daemon.py:5066-5153`, with durable controller transitions at `controller.py:2660-2849`. | None; these are file, UID, boot, sequence, and pending-set facts. | 0 model calls. | Unknown; no stage journal records model counts. |
| AH reopen/start | Already-open `REOPEN` completes deterministically at `daemon.py:5157-5171`. A closed AH dispatches `open_ah` at `5172-5174`; named pre/post admission, two settled observations, and final verification are `daemon.py:4070-4173` with `WaitPolicy.settle_count=2` at `4094-4100`. | The named action has 3 visual `_observe_addon_state` calls (pre plus two settled post observations), each reaching `daemon.py:1659`. The pointer anchor adds a daemon fallback at `1327` when no native provider is accepted; pointer movement adds the refresh boundary at `driver.py:2545-2557`. | 3 with an accepted native anchor provider; **4 without refresh when the native-provider branch is unavailable**; **5 when pointer movement needs refresh and the native-provider branch is unavailable**. Native-provider and movement branch selection is runtime-unknown. | Unknown; existing fixtures do not count production adapter calls. |
| Closeout/recovery | Logout command precondition and dispatch are `daemon.py:1913-1931`; character-select cleanup evidence is `daemon.py:4790-4817` and `driver.py:3841-3849`; durable cleanup is `controller.py:3277-3304`. Login recovery is `daemon.py:3434-3453`. | Closeout has one named world pre-observation and one character-select post-observation. Recovery adds one `decide`, one named pre-observation, and two settled post-observations; optional anchor fallback/refresh follows the AH row. | Closeout 2. Recovery 4 with native provider, 5 without pointer refresh, or 6 with visual anchor fallback plus pointer movement. These are branch minima. | Unknown; no real model-call journal. |

The named-action minima exclude failed polls, rejected settle observations,
deadline retries, and repeated owner recovery. A rejected observation clears
the consecutive settle set at `daemon.py:4160-4169`; it cannot silently reuse
the earlier evidence.

## Test and journal evidence

The lifecycle fixture installs `_FixtureLunaAdapter` at
`tests/test_session_runtime.py:1320-1413` and replaces `daemon.model` at
`1444-1448`, but has no invocation counter. The durable runtime tests at
`1864-1902`, `1905-1974`, and `1977-2024` prove stable saved evidence,
restart uncertainty, and loaded-ACK refusal. Transition tests at
`816-849` and `904-960` require a fresh named postcondition and reject stale
evidence. Regression tests at `871-920`, `1158-1168`, `1185-1201`, and
`1369-1420` preserve upload/Data.lua ordering, corrupt-telemetry refusal,
intent-before-dispatch, and closeout fence ordering. Recovery tests at
`1444-1470` use a fixed decision iterator; they do not measure production
adapter calls.

No accepted execution journal records model method, stage, source, or duration
events. Static counts above therefore remain source minima only.

## Retained fifth, sixth and seventh parent receipts

These receipts are orchestration evidence, not model timing journals:

| receipt | completion/finish to Return dispatch | dispatch to server receipt | qualification caveat |
| --- | ---: | ---: | --- |
| fifth | 81.67367601394653 s | 4.9580559730529785 s | Finish-to-receipt was 86.63173198699951 s; a preserved completed HUD existed about 44 s before dispatch. |
| sixth | 65.10768294334412 s | 3.7788121700286865 s | Finish-to-receipt was 68.8864951133728 s; pre-dispatch delay exceeded the 60 s target without computation attribution. |
| seventh | 159.9986789226532 s for the successful dispatch | 4.908797979354858 s | Finish-to-receipt was 164.90747690200806 s; the first Return had same-boot/unchanged-file/no-UID evidence and causal focus attribution remained unproven. |

The fifth, sixth, and seventh records preserve no per-stage model interval.
Their long pre-dispatch periods include operator observation and orchestration;
they must not be attributed wholly to Luna or Python inference. They do show a
useful deterministic completion/readback/dispatch boundary to instrument next.

## Smallest next reviewed removal slice

The smallest semantically bounded candidate is the
`auction_house_open` named observation after a fresh native semantic provider
has been separately accepted. That provider would need to emit a fresh,
identity-bound boot/sequence record containing configured character/realm,
AH-open, visible scene/modal/control/idle facts, capture identity, and a
monotonic timestamp. Only then could the AH-open postcondition replace visual
inference while retaining `_check_named_facts`, generation/freshness checks,
and the two-observation settle rule. The pointer-anchor and post-movement
refresh boundaries remain separate. No production call is removed by this
audit, and no remembered coordinate, ignored modal, fake identity, bypassed
admission, or human takeover is proposed.

## Decision and limitations

`insufficient_evidence` is the only supported Phase 1 decision. The retained
receipts lack paired application-CPU and end-to-end intervals, accepted region
producer/config bindings, per-run eight-sample records, and model-call
counters. The offline tool cannot fill those gaps because it cannot capture or
instrument the live path. A future reviewed measurement slice must add a
matching region capture/IPC contract and a real model-call journal before
`plan_prototype` or `defer_rewrite` can be considered.

No tests were run for this static audit itself. The corrected offline
implementation and its tests are separately scoped to the three Phase 1
candidate files. Its local decoder hashes are measured-source identities only;
no caller-supplied `accepted=true` receipt can establish a reviewed binding.
Unavailable decoder substeps remain null rather than copied or reported as
zero. Acceptance of this audit and any live instrumentation contract remains
pending.
