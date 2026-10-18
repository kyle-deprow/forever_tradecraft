# Native R6: close admission and durable outcomes in two stages

R5 is frozen/unaccepted despite parent316passes. Sol R5 full source review has
nine concrete Musts and a metadata correction. Root accepts those reachable
findings. Actual Opus R5 review is still active; root will consolidate additional
concrete findings when available. Do not repeat a whole new feature implementation.
This rescope has two explicit bounded implementation stages with production-path
proof before a final freeze. No deployment or live claim.

## Worktree / ownership

Root creates native-admission-outcomes-r6-20261018 from68e4236 and copies exact
six frozen R5 files. Only these same six may change:
src/crowley/session/controller.py, daemon.py, cli.py;
tests/test_session_native.py, test_session_native_regressions.py,
test_session_transitions.py. All other source/helper/addon/driver/Guardian/
calibration/inputtool/protocol/config/journal files are read-only. No GUI,
services/config/input/network/production data or git commit/reset/stash/revert.
Only MAIN executor-review/native-admission-outcomes-r6-closure.md and freeze.json
report writes. Preserve all earlier freezes. Existing public schemas/deadlines/
canonical14/request-keysets/legacy behavior outside admitted construction remain.

Read full Sol R5 source review and R5 consolidated/original correction plans.
Do not silently discard an accepted item or count raw dictionaries/private
attribute injection as production composition.

## Stage A: one immutable admission owner

Close Sol Must1/2/3/6/7 and their coverage:
- Snapshot under construction lock; release it for controller/identity/Guardian
  operations, then validate same immutable runID/epoch/reservation/deadline.
  Audit EVERY changed/default-path construction-lock call chain, including
  _check_native_poll_identity. No construction->controller inversion anywhere.
- Seal deferred-vs-legacy exact context at admission, before publishing starting
  or launching worker. Pass it immutably; worker never recomputes from mutable
  reservation and never falls back to legacy after revoke. All work after
  calibration-lock acquisition, including context lookup, is in one exception-
  safe lifetime that releases slot and reaches terminal operation status.
- Public legacy bootstrap rejects every live deferred/provisional admission.
  Extract a private exact-context-bound internal capture for deferred provider;
  no public IPC can populate its slot without reservation proof.
- Controller-first generation/state+construction owner validation encloses
  cancel's clear/terminal snapshot. No gen7 success after gen8 pause.
- Recovery polls revalidate current exact reservation/ticket/epoch before AND
  after captures/sleeps; PAUSED producer admission receives/checks the CALLER's
  exact immutable capability at actual exec-gate linearization. A cancelled old
  completion cannot borrow a later same-generation owner or keep capturing.

Prove via real thread/subprocess barriers: pause during native poll, deferred
start/pause before and after lock acquisition, legacy bootstrap collision,
cancel/pause, cancel/replacement during capture. Use real default configured
compiled PAUSED producer through public SessionIPC preflight/recovery, not manually
injected inflight or dictionary-only provider. Other fixture effects may remain
harmless/offline. Send actual Stage A focused results; continue Stage B without
routine approval. Do not run fullthree suites between source stages.

## Stage B: closed durable / terminal outcomes

Close Sol Must4/5/8 and remaining coverage9:
- Fast matching finalize_required admitted while resume callback returns is
  valid. Accept it alongside resume_ready and preserve its event/deadline.
  Revalidate immutable owner/controller fence each finalize wait boundary so
  pause unwinds promptly. Preserve30s hook/10s action and existing freshness.
- Recovery frame observation validation+checkpoint consumption are ONE closed
  durable commit. No second fallible observe_frame journal write can strand
  already-committed recovery before terminal publication. Factor shared private
  validation/read-only postcommit proof as needed, without weakening observe.
  Inject each real durable failure with failing owner alive through handler;
  fresh owner must find an honest recoverable checkpoint OR completed durable
  outcome, never a local live ticket with consumed checkpoint and no result.
- One bounded nonadmitting ID-bound terminal recorder covers success, cancel,
  revoke, expiry and failures before owners clear. Append failure history via
  publisher BEFORE state overwrite. Preserve first error, exact owner and
  immutable history. Return captured terminal objects rather than rereading
  mutable global history after releasing locks. Bound receipt count explicitly;
  do not grow dict forever or refresh old expiry. Keep canonical14 shape/private
  protocol and avoid introducing uncoordinated new helper reservation enums.
- Public actual SessionIPC/parser tests cover all8 command shapes and every
  predecessor edge; barriers cover real races above and fast finalize; configured
  public PAUSED preflight/recovery includes real compiled captures/PNG/decoder.
  Raw-dict callbacks may supplement, never substitute for these acceptance paths.

R5 freeze/closure history order is wrong: finalize_required belongs AFTER
resume_ready, immediately before finalized. Preserve historical R5 artifacts;
R6 records/tests must derive and assert actual correct12-state history, exact
entryshape/max16/nondecreasing clocks/no poll append. Bound terminal count too.

## Final verification / freeze

Run focused meaningful stage cases first, then FULL three native suites ONCE
AFTER finalsource (rerun only if a real edit/failure requires it). Authentic private
0.162.1 CLI explicitly configured; private0700 XDG; exact import origins/source
hashes and private logs. Scope Ruff/format/compile/diff to6files. Do not inflate
pass counts with a broad pre-final run or report absent coverage as completed.
Write exact candidate/base6hashes and literal actual coverage/remaining limits
in MAIN R6 closure/freeze. DONE only if this bounded source scope complete.
Parent independently verifies then Sol+actual Opus re-review before any promotion.

## Actual Opus R5 arbitration (completed21:37UTC)

Actual claude-opus-5-5 exit0, STATUS NEEDS WORK; full report is
executor-review/native-construction-native-r5-opus-review.txt. Root accepts its
3Must and these concrete Should corrections, deduplicated into existing stages:

- Must1/3 and Should4/5/6/10/12/13 duplicate accepted Sol/stage requirements.
- Must2: recovery-begin must strictly decode expectedConstructorBoot held/100
  (also held/updates allowed by actual addon recovery), then classify restore.
  Do not apply ordinary normal/0-only facts to construction lifecycle recovery.
  Ordinary B0/new ordinary branches retain normal/0+inactive-fence validation.
  Add actual encoded held/100 PNG+decoder rejection/recovery tests.
- Should7: check EVERY controller mutation admission/status result (checkpoint,
  rebind/observe/native_calibrated), under correct owner linearization. Never
  hand out a reservation lacking durable checkpoint or publish finalized after
  BLOCKED/nonadmitted calibration. Add real pause/resume/raced mutation negatives.
- Should11: cancel increments/revokes epoch AND clears exact inflight admission;
  cancelling while recovery-begin captures must prevent later ticket creation.
- Should8 accepted as conservative absence hardening: 90% intact-cell threshold
  alone is insufficient; reject damaged/partially occluded encoded fragments,
  black/loading/ambiguous surfaces. Keep same pure interface/no second decoder/
  guessed fallback. Add >10% damage/occlusion of actual encoded PNGs (including
  header and payload), ordinary retained images, malformed size/mode/corruption.
  Do not merely swap one arbitrary percentage to make tests pass or claim that
  a heuristic mathematically proves absence. Parent will inspect actual classifier
  and native ordinary/damaged fixtures before acceptance.
- Should9 partially accepted: NEVER re-stamp/relabel entry capture as a new
  post-reset proof. Both captures must actually occur/seal/delete. Remove the
  new capture-override identity-detection branch; driver/backend injection can
  supply fixtures through the same normal route. Existing explicit test-provider
  injection may supplement unit negatives, but is not default-path proof and
  cannot skip a required production capture. Full public configured capture
  acceptance remains mandatory as in stages A/B; do not delete unrelated legacy
  injection APIs solely because they support tests.

Reachable minor validity points while changing admissions: require held desktop
lease before issuing reservation, reject already-prefixed or >64byte B0 early,
make malformed expected image size/mode fail typed/closed rather than IndexError.
Do not add unrelated dead-code cleanup or host-CLI fixture portability refactor.
Freeze-history metadata correction applies to NEW R6 artifacts; historical R5
is preserved. Confirm old legacy behavior outside deferred admission; retain its
existing contract instead of accidentally imposing deferred proof changes.

Opus was prompted while parent suite was inflight; it is now conclusively green
316tests339.07s. That result does not resolve any above source/coverage findings.
