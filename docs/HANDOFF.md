# Forever Tradecraft handoff

Written 2026-10-14 by the agent that started the project, for the agent taking over on the
server. Read this fully before changing anything. The user revoked `AGENTS.md` instructions;
reusable local workflows are under `.agents/skills/`. `docs/ARCHITECTURE.md` is the shorter
technical reference; this document adds requirements, history, research and next steps.

### Continuation on the server

The companion now retries stable SavedVariables after transport failures; successful
uploads are not repeated. The first-run item catalog and server delivery are implemented;
see [WATCHLIST.md](WATCHLIST.md) for the canonical data, coverage and management commands.
The scan plan is delivered in addon data and the Lua scanner now performs targeted,
bounded-depth format-2 sweeps with explicit per-item coverage and plan identity. The earlier
assumption that ForeverWowCraft has no backend history is not established; only its public
current plans were inspected. Recipe data must be verified against Forever's build rather
than copied from Classic.


### Post-crash continuation (2026-10-16 local / Oct 17 UTC)

The live repository is `/home/dev/repos/pegasus`; `/home/dev/repos/crowley` is
absent. The user revoked `AGENTS.md`. Preserve failed evidence. On Oct 17 the
user authorized a checkpoint commit and push to the new canonical public origin,
`https://github.com/kyle-deprow/forever_tradecraft`; the project is now Forever
Tradecraft, with existing Crowley package/addon interfaces retained. Luna operates and
implements, Sol reviews, and actual Claude CLI Opus reviews executor changes.
The detailed prior continuation is retained in
`.archive/executor-review/handoff-postcrash-before-throughput-summary-20261017.md`.
Treat the older sections below as history, not current runtime instructions.

**Checkpoint:** source, tests, tools, repository skills, plans and curated review
summaries were pushed to the new origin through `8ba9e0e` (initial snapshot
`c000f1f`, audit `214a4e0`, companion-unit portability `56787c8`, reviewed recipe
foundation and collection receipt `ae9129b`, recovery plans and corrected interval
evidence `60eca5f`, third scan/performance plans `f2d3f2b`, collection/performance
checkpoint `4540671`, reviewed addon timer fix `8c98469`, reviewed backup and
parent restore drill `ae02543`). Raw runtime logs, captures and
private configuration remain local. The companion unit now invokes the installed
tool without a checkout-specific working directory; parent systemd verification
passed. No runtime service was changed by this source fix.

**First current-release data:** original SavedVariables and format2 envelope
independently validated by parent for UID
`beta-normal-alliance-1792215846-Arthur-9942`, build70450/current plan:428queried,
2183positive-price rows,407full/21bounded, every reason `ok`. Sweep ran
1792215846→1792216326 (480s). Companion accepted it and wrote the exact UID into
Data.lua acknowledgements; second reload confirmed `cleared1`, loadedACKs1,
pending0 and storedsweeps0. The second sweep, UID
`beta-normal-alliance-1792217085-Arthur-3539`, ran1792217085→1792217561
(476s), queried428items and captured2296positive-price rows,407full/21bounded,
all reasons `ok`. Its companion upload and client-loaded exact-UID ACK also
completed. Original envelopes establish a1239s start interval; screenshot-based
click times and old chat status lines were not scan timestamps. Both uploads
were144s after completion. These useful ordinary sweeps have not met the900s
cadence or autonomous60s upload gate. Third UID
`beta-normal-alliance-1792218159-Arthur-9399` ran1792218159→1792218636 (477s),
queried428items, captured2304rows,410full/18bounded, all reasons `ok`. Parent
validated its original SavedVariables and matched the read-only server row,
received06:36:26.500347UTC. Operator verified its exact loaded ACK/pending0 in
fresh boot1792219198-693987. A prepared reload dispatch had earlier failed to
persist it; actual loading/new boot/disk change established the corrected reload.
The third start interval was1074s and upload350.5s after finish (pause/recovery
included). See `build-70450-third-scan-parent-verification.json`.
Ordinal148/item6371 completed in1s; its earlier stale
chat line did NOT establish a stalled scan. Parent receipt:
`.archive/executor-review/build-70450-first-scan-parent-verification.json`.
The first interval compared428items, with186showing observed listing/depth
changes; the second interval had187changed items. Depletion/replenishment are
liquidity proxies, not sales estimates;
grouped scope suppresses individual turnover metrics. Receipt:
`.archive/executor-review/build-70450-first-interval-parent-verification.json`.

Fourth UID `beta-normal-alliance-1792219323-Arthur-9845` completed428queries,
2321rows,409full/18bounded/1incomplete (item818, query_timeout). Its native818
result arrived one second after timeout and was correctly ignored while858was
current. Parent verified original envelope/trace/server row; operator confirmed
loadedACK boot1792220014-834954. Server receipt was56.581s after finish, meeting
the upload target for this ordinary sweep. Fifth UID
`beta-normal-alliance-1792220223-Arthur-1792` started exactly900s later on the
addon timer, completed428queries/2364rows/410full/18bounded/allok in473s.
Parent verified its envelope/server row and operator-preserved fresh loadedACK
receipt (boot1792220936-906810,pending0). Upload86.632s afterfinish missed the
target: Return was81.674s afterfinish, server receipt4.958s later. This is mainly
pre-dispatch orchestration delay, not evidence of a decoder computation limit.
Five completed sweeps captured11468price rows. Individual parent receipts are
under `.archive/executor-review/build-70450-{fourth,fifth}-scan-parent-verification.json`.
Operator is released to continue ordinary collection, targeting sixth due
1792221123 (07:12:03UTC), while executor source remains undeployed/unarmed.
That sixth timer did NOT start: same-boot fresh HUD at07:11:35showed scheduled,
AHopen,due1792221123;07:12:42and07:17:26showed ready,due0,AHopen,no active scan,
pending0 and the fifth loadedACK. Root verified installed Scanner.lua symlink/
sourceSHA `b2843e42d1edf4d9ed4df1b6214928cf12baadde03108b65fd10912fdfc0b218`.
Cause remains unknown; `Status.phase=scheduled` is derived from cooldown and is
not proof that a live timer exists. Existing `test_start_cadence_and_no_overlap`
reopens AH atdue, so it does not establish timer-alone behavior. Preserve this
failure and add actual timer observability/reproduction before claiming it fixed.
After bounded diagnostics, root authorized one safe close/reopen with proof of no
active query. This auto-started ordinary sixth sweep1792221571 (07:19:31UTC),
nextdue1792222471; no `/scan`, position unchanged. GUI owner continues collection.
Sixth UID `beta-normal-alliance-1792221571-Arthur-1952` completed at1792222047
in476s,428observations/2331rows/allok. Parent validated the original persisted
envelope and read-only DB row received07:28:35.886495UTC (68.886s afterfinish).
Return dispatch was65.108s afterfinish, then3.779s to server. Preserved fresh
boot1792222197-345235 confirms the exact loaded ACK/pending0. Six sweeps now
contain13799positive-price rows. Seventh was scheduled for1792222471 after one
verified AH reopen. See `build-70450-sixth-scan-parent-verification.json`.
The addon diagnostic reproduced an early callback consuming the only timer.
The remaining-cooldown rearm and bounded scheduling trace are now integrated
after parent166tests/Ruff and SolsourceR2READY. Exact ScannerSHA:
`75a8ca368ce1659d1c4a0e338770b11c2d0285161fb99478b2fdff23e98fee9e`.
Integration occurred after seventhloadedACK/pending0/AHclosed/noactive; GUI owner
is released to verify its reload then reopen AH. Internal retries remain quiet,
manual cooldown notices remain, and timer_create is logged after successful API
return. The actual live miss cause remains unknown; retain new scheduleTrace
on normal SavedVariables flushes. See `addon-schedule-parent-acceptance.json`.
Seventh parent original/DB/loadedACK verification confirms2249rows/allok,
900s timer-alone start, but164.907s upload after a recovered no-effect Return.
Eighth is the first full sweep on the reviewed scanner: UID
`beta-normal-alliance-1792223398-Arthur-0437`,479s,428observations/2134rows,
411full/17bounded/allok. Parent validated original envelope, all9scheduleTrace
events, read-only DB row, and loadedACK boot1792224024-834282/pending0.
Upload49.940s afterfinish meets60s. Eighth started927s afterseventh because the
reviewed reload/AH reopen crossed due by27s; autonomous qualification remains
pending. Eight sweeps total18182price rows. New trace proves actual timer
creation/callback/start plus finish rearm/cancellation; it does not prove the
previous miss's cause. Ninth timer-alone start1792224298 was operator-verified
after continuous AHopen/no input, exactly900s aftereighth. GUI owner is released
for ongoing ordinary collection without per-sweep approval.

Ninth UID `beta-normal-alliance-1792224298-Arthur-2114` is independently
verified against original payload, logical content digest, DB row and client
loadedACK boot1792224890-823442/pending0. It captured2121rows/428queries,
412full/16bounded/allok in476s. Timer-alone start was exactly900s aftereighth;
finish-to-server24.106s (18.760s before Return,5.346s transport/ingest).
Nine current-session sweeps total20303price rows. Tenth timer-alone start
1792225198 was operator-verified with continuous AHopen/no input; completion
and ACK are not yet claimed. Qualification remains operator-assisted.

Tenth UID `beta-normal-alliance-1792225198-Arthur-4827` is also parent-verified:
428queries/2090rows,412full/16bounded/allok,476s, exact900s timer-alone start.
The original logical content matches the DB/raw reference and the fresh exact
loadedACK boot1792225780-211734/pending0. Upload43.160s afterfinish meets60s.
Ten sweeps total22393price rows. New native C build attempt2 succeeded but its
compiled concurrent foreign-command test exposed blocked GApplication forwarding;
R5 is correcting nonblocking invocation admission and will preserve all prior
binaries/logs. It remains isolated and undeployed.

Eleventh UID `beta-normal-alliance-1792226098-Arthur-2671` is parent-verified:
428queries/2102rows,411full/17bounded/allok,479s, exact900s timer-alone start.
Original logical content matches DB/raw reference; fresh exact loadedACK
boot1792226752-118220/pending0. Upload98.261s afterfinish missed60s. Retain
this orchestration delay; it is not computation attribution. Eleven sweeps total
24495price rows. Sole operator is probing native API/UI capability read-only at
the normal quiet boundary before reopening AH; no protocol or binding changes.

**HUD implementation:** R2 parent host affected batch296passed/exit0; focused14,
compiled private producer harness and Ruff also passed. Namespace batch had
275passed/21failed (executable memfd EACCES), then hung in teardown; only the
identity-bound isolated wrapper was terminated. Actual Sol and Opus
(`claude-opus-5-5`, exit0) source reviews both NEEDS WORK. R3 source/binary are
frozen; parent reproduced19focused tests and compiled producer self-checks.
Parent rejected completion because the default daemon path was still not
composed with the real producer, and the diagnostic manufactured timing and
retirement evidence. Fresh `luna_region_closure` owns the narrow R4 closure in
`.archive/PLAN-region-composition-diagnostic-closure.md`: real default-daemon
composition, config/IPC-bound eight-sample diagnostic, and truthful retirement
evidence. Its composed test and eight-sample isolated runner passed, but parent
found the runner's second DesktopDriver/private lease violates live ownership.
The correction in `.archive/PLAN-region-owner-ipc-closure.md` uses capture IPC on
the existing owning daemon; Sol planR2READY released expanded implementation,
including narrow producer admission/revocation and bounded IPC framing.
Parent clarified the race test: stop winning before atomic admission prevents
exec; admission winning first releases its gate nonblocking, then stop during
real blocked Shell capture prevents publication/reaps the producer. Never block
inside Popen/gate release to invent an interleaving. Guardian remains unchanged.
No new live capture is released before parent/Sol/Opus review.
Capability remains default-off and undeployed.
Current native closure status: SolR4MAJOR ISSUES and actual CLI
claude-opus-5-5R4exit0/NEEDS WORK. Parent final focused16passed36.38s; broader
host317passed/1failed426.17s because private compiled fixtures shared the real
desktop's screenshot lock. The main native source stays frozen/uncommitted.
R5 works only in `/home/dev/.cache/crowley/worktrees/region-r5-20261017`, based
on8c98469 plus11hash-verified R3/R4 overlay files. Scope/accepted reviewer fixes
are in `.archive/PLAN-region-r5-lifecycle-closure.md`: C active-primary guard/new
private build, all production region captures Guardian-owned, immutable config
vs runtime anchors, precise final/failure receipts, cancellation/lock/FD and IPC
deadline evidence, isolated compiled fixtures and real supervised serving proof.
No new native opt-in or live executor release; do not deploy R4 from main.
R4 now validates a canonical hash of the whole loaded SessionConfig on the owner,
separate from caller raw-TOML provenance, and verifies the driver profile matches.
Parent's retained focused host run passed the genuine eight-sample happy path but
later failed: an owner protocol deadline expired before Shell, then the fixture
blindly mutated an absent sample and masked that refusal with a thread KeyError.
The worker is correcting external-fixture reporting and investigating under the
unchanged one-second deadline. Earlier hermetic316pass/2fail were missing private
input-tool fixture setup, not this failure. Preserve both kinds of evidence.

**Recipe foundation accepted:** three-file implementation, packaged normalized
manifest, nine-profession coverage (eight crafting plus Mining), two blocked
Mining/Cooking source-fact candidates. No numeric margins, strategy shopping lists
or network runtime. Parent23tests/Ruff/five frozen hashes and actual disposable
wheel install passed; SolsourceR1READY/no findings. See recipe-foundation parent
acceptance and source review under `.archive/executor-review/`, and
`docs/WATCHLIST.md`. Further recipe facts and a strategy engine remain to build.

**Recovery work:** a private manual snapshot at
`~/.local/state/crowley/market-backups/beta-20261017T061327Z` preserves a custom
database dump and raw archive, but is not restore-qualified. The revised
`.archive/PLAN-market-backup-restore.md` passed Sol plan R2. The recipe worker
now owns the three-file backup implementation and a real disposable restore
drill. Live database/resources stay read-only; restore writes and cleanup must
prove fresh disposable identities. One real happy-path drill now completed
`restore_verified`: PostgreSQL16.6/Timescale2.17.2,12sweeps/5136observations/
20243rows,12raw references/no orphans, both API probes,15passed operations.
Parent independently validated the canonical manifest/member hashes/private
receipt and absence of its exact disposable project after cleanup;53unit tests
passed. This is happy-path evidence, not final source acceptance.
The partial backup tool has exposed actual Docker inspection/state-transition
bugs in disposable drills; the worker is resolving them and preserving failures.
Root independently confirmed project `crowley-drill-13727fb39e3b4808` has no
remaining containers/volumes/network after its failed attempt. Source commit /
whole dirty-tree equality was removed as an unintended compatibility requirement;
those fields are provenance, while actual Compose/migrations/images/versions
remain pinned. The worker is reusing canonical snapshot
`beta-20261017T065805Z-1d88c6e603e3` rather than resnapshotting after every helper
change. Fixed failure-stage metadata must retain actual error categories without
secrets; no opaque retry loop or live/source writes.
Sol sourceR1 found four must-fixes: historical Docker IDs wrongly used as a
compatibility gate, incomplete actual target image/mount validation, partial
creation cleanup falsely verifiable, and shallow receipt success/type validation.
All four were corrected. SolsourceR2READY and parent88tests/Ruff/format/compile
passed. Parent executed the final reviewed tool against the same canonical
snapshot: new private receiptSHA3767f6b0edad98f80c56c914df6cd9cf7327c65d3a5abf2e2820577020670530
is restore_verified with15passed operations and12resolved raw references.
Parent revalidated manifest/archive/strict receipt success semantics and exact
project absence (containers/volumes/networks all empty). Historical receipt is
unchanged. Sanitized public proof: `market-backup-drill-summary-r2.json`.
Final tool/tests/docs are committedae02543. A new point-in-time snapshot
`beta-20261017T080304Z-88ac180be7ad` completed after eighth ingestion and passes
canonical manifest/COMPLETE/archive validation, manifestSHA
`a0f9b99c6eea2599ecd99ace139e3aab8c6843ad0f590c831c6b3c6568227c04`.
This latest snapshot is not separately restored; final-tool restore qualification
uses the earlier canonical snapshot and the retained new successful drill.

**Deterministic runtime / Rust:** offline Phase1 is integrated after Sol source
R2 READY (two review rounds) and parent15tests/Ruff/format/compile. It times the
actual public strict decoder and pure planners, retains wall and processCPU
separately, and bounds input/receipt reads. Real preserved frame100replays,
5warmups,0failures: strict decode p95 63.648ms wall/63.397ms processCPU;
planner CPU p95<=0.208ms. This is offline evidence, not a live bottleneck verdict.
Current decision is `insufficient_evidence`: accepted live source/config/producer
binding and paired capture/IPC/decode runs remain absent. The conditional Rust
prototype planning gate and required repeatability remain in
`.archive/PLAN-deterministic-runtime-performance.md`; no Rust source is created.
See `docs/RUNTIME_PERFORMANCE.md` and `runtime-performance-parent-acceptance.json`.
The static model-boundary audit is explicitly bound to preserved R4 source;
AH reopening with visual pointer movement has five possible model calls
(three named observations, anchor, post-motion refresh); an already-positioned
pointer can omit refresh. These are source minima, not measured runtime counts.
Future deterministic semantic observations need their own reviewed contract.
The bounded live instrumentation plan `.archive/PLAN-runtime-live-instrumentation.md`
is frozen after parent review at SHAcaabd905b1e591bb495715e3f8b6b68a31c2cda8d79f7ea08ccd58d5159f494d.
It follows accepted R5 native closure: exact owner/observer source/config/producer
binding, same-attempt decodeCPU, overlapping wall boundaries, all failures and
actual model counters. No Rust or production instrumentation is implemented yet.
Ordinary collection does not depend on that qualification.

**Next reduction of model dependence:** `.archive/PLAN-native-semantic-observations.md`
is a bounded proposal, not an implemented capability. Current native telemetry
cannot yet replace visual AH postconditions: authoritative world/current AH
visibility, blocking modal/error state and defined readiness are missing. A
read-only capability probe is delegated to the sole GUI operator at a normal
quiet collection boundary. The plan retains separate fresh anchor/gesture proof
and two-frame settlement; it never manufactures auctioneer identity from ahOpen.
No call removal or zero-model full-cycle claim is accepted.

**Beta deadline and priority (Oct 17):** the user reports four beta days remain.
Collect useful real market observations now, in parallel with executor work;
launch should begin with a prepared collection and strategy pipeline. Ordinary
bounded addon UI scans do not depend on autonomous executor qualification.
`luna_live_continuation` owns the real desktop and is released to inspect current
commands/state, open AH, validate the 428-item sweep, uploads and loaded ACKs,
and verify the addon’s 900-second scheduling and logout behavior. Do not arm the
unqualified controller. `sol_native_capability_plan` is auditing evidence that
expires with beta versus work that can finish offline, including launch cutover,
profession coverage and liquidity estimates. Preserve beta history; never assume
beta prices predict launch prices. Audit artifact:
`.archive/executor-review/beta-launch-readiness-audit-20261017.md`.
Parent verified Blizzard’s updated production-hardware stress test is October21
at14:00PDT/16:00Chicago; the old October19 URL redirects to the updated post.
Use that short window to probe exact launch realm/region/build identity.

**Autonomous qualification objective:** finish HUD/executor qualification and demonstrate three
real 428-item scans at seed/+900/+1800 seconds, uploads and loaded acknowledgements,
then clean closeout without a fourth scan. Five ordinary70450 sweeps completed;
the formal autonomous repeating-session qualification has not passed.
Native/resource, actual human input, camera and movement-basis gates remain.

**Last verified operation:** Arthur was in world beside Auctioneer Buckler,
stationary, AH closed; this scene may now be stale. Sole GUI owner is `luna_live_continuation`; root must not
capture or inject input concurrently. Root paused the controller at generation13;
native/input gates are false, terminal previous calibration error retained,
service running but DISABLED. Last verified daemon PID972882. Ordinary addon
collection is now released as above; autonomous scans, camera and CTM changes
remain unqualified. Verify runtime afresh.

Recovery and accepted deployment:

- Companion, editable uv tool and addon symlink point to `/pegasus`; companion is
  active. Lutris duplicate `--exec` repaired. Battle.net logged in.
- Private authentic Codex0.162.1 is selected in the private session profile;
  host-global0.163 is unchanged. Native binary SHA
  `628e35487d888a28f0427fc37501da529dd3d81fcbad7a2c3421c1e8670d92e1`.
  Location: `~/.cache/crowley/codex/0.162.1/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex`.
- Accepted native schema3 implementation is integrated, with three broad Sol/Opus
  rounds and narrow timing closure. See `PLAN-motion-observation-deadline-closure.md`,
  `source-freeze-native-capabilities-accepted-final-r3.json`, and
  `native-capabilities-integration-receipt.json` in `.archive/executor-review/`.
  Pure budget infeasibility preserves existing proof objects but refuses input;
  failed required native successors/state/interaction/lease/generation/setup clear
  both. Next intents still need fresh gates. Do not restore the old isolated tree
  over newer live release/capture fixes.
- Reviewed release revision2 targets1.60.1.70450/interface16001. All544 catalog
  objects unchanged:428active (352core/76discovery),74research,42excluded;
  depth20, cadence900, sweep cap600, format2. CatalogSHA
  `90918db5cc912e889553b5ddd422b829f3c6cb3773ab6da56a2e79a5a8db04f3`;
  planSHA `f1745d85c071b350ebea242add2a7b38e3f53df5bcc8a6df1f19002f995a31d4`.
  Server image rebuilt/deployed, authenticated scan plan verified, private profile
  and companion Data.lua updated. Receipt `build-70450-parent-cutover.json`.
  Last unchanged DB:1plan/8sweeps/3424observations/11139capturedRows. New plan row
  arrives on ingestion; preserve historical rows and volumes.
- Parent release tests:264passed using authentic private CLI in bubblewrap.
  Host-global run remains241passed/23known CLI/lease failures; earlier native
  broad run870passed/24failed/15DBskipped. Do not claim full suite green.
- Model adapter fix removes orphan MCP override and permits only exact exit-zero
  `Reading additional input from stdin...\n` notice. Parent13tests and SolREADY;
  one actual retained-image observe request accepted in5.777s. This establishes
  model plumbing, not fresh action admission. `PLAN-model-cli-mcp-override.md`.

HUD/window facts (reverify identity before use):

- Sole WoW PID641068/start998749; outer0x03200001, child0x02000011. Measured outer
  1928x1092 and child1920x1080 both at0,0 are supported by existing resolver.
  Private outer profile rebound only; canvas `[80,48,256,256]`, model crop
  `[80,48,1760,984]` unchanged. Do not force fullscreen or compositor properties.
  Identity fingerprint `697fa4e6bc67468f8f189c7864b4072d4527c95aef78ed67cade9e5899a4ff86`.
- Actual strict schema3/build70450 pairs passed repeatedly. Latest corrected pair
  boot1792208608-703443, seq224→225, normal/0, speed0, position
  (-4949.2001953125,-903.7000122070312,0). Receipt under private runtime-relink
  `native-handshake-20261017T034722997643Z-pid1163776/`.
  Four-return speed units remain unverified. Routine texture/update observations
  are not the formal resource proof.
- Genuine150ms mouse-down/up entered world; earlier instantaneous click returned
  zero but remained at character select. Use actual pointer/target proof and
  finally release; do not infer dispatch success from return code.

Capture repair and current bottleneck:

- Accepted two-file capture completion fix: secure cross-process flock, private
  per-attempt directories, strict complete-PNG verification, epoch cancellation,
  atomic publication and late-writer retirement within existing deadlines.
  Parent42tests and static checks; SolREADY, actual Opus `claude-opus-5-5` exit0
  READY/no Must/Should. Rare filesystem-cleanup/test-strength nits remain deferred.
  `PLAN-gnome-capture-completion.md`, `gnome-capture-freeze-r2.json`, review logs.
  Live driverSHA `14ae6be4a901a17e396e68ac4501238db3d1cc0118c8c34ad6f7107fbcfacfa7`.
  Two real concurrent captures returned fully decoded images with matching identity.
- Stock production-like timing was1.629–1.641s total; GNOME CLI1.021–1.038s;
  21identity queries264–268ms. GNOME Screenshot41.0-3 hardcodes flashTRUE;
  official Shell48.0 awaits500ms animation. Settings delay already0.
- Genuine private GNOME41.0 fork built in isolated Docker, no host packages or
  desktop settings changed: exactly one full-screen flash boolean TRUE→FALSE,
  upstream `-Dx11=disabled` to prevent legacy fallback. Sol and actual Opus READY.
  Binary `~/.cache/crowley/gnome-no-flash-stage2-r1/prefix/bin/gnome-screenshot`,
  SHA `45750c8dca51a5f6ec5584be0e807a29a60284cca8a1cb5d13b8a2f45fde6af9`.
  Manifest `gnome-no-flash-stage2-manifest.json`; stock binary unchanged. This
  fork is NOT production-bound; production daemon still selects stock capture.
- Reviewed private benchmark script `~/.local/state/crowley/executor-evidence/gnome-no-flash-benchmark-stage2.py`,
  SHA `c3c1e8707ffad75d37dc8e6e22dd22d6e32970ab33b0d6fea5dee6313fba0a8b`:
  parent22offline tests/selfcheck and Solscript-r2READY. Exact private child must
  acquire/release canonical bus name inside its admitted backend request; passive
  observer queries bus daemon only. No alternate backend/caller bypass. Capture
  timestamps preserved; NO_CHANGE isn't fresh. Recent-file metadata audited,
  not restored. Max8 diagnostic captures, not native resource qualification.
- First run stopped after one invalid crop because game had returned to character
  select during idle. Failure retained; no valid throughput sample from that run.
  Normal one-pulse recovery and fresh strict pair preceded a NEW run immediately.
- NEW run completed8/8FRESH frames, boot1792208608-703443, seq234→247 increasing,
  speed0, same identity, every private owner verified, no errors/cleanup errors,
  final bus unowned. CLI median0.8773s (0.8651–0.9772); whole measured path
  median1.8368s (1.8094–2.0263), INCLUDING passive observer sleeps/overhead.
  This does NOT demonstrate one-second production feasibility. Receipt:
  `~/.local/state/crowley/executor-evidence/gnome-no-flash-benchmark-20261017T034732774222Z-1164337/receipt.json`.
- Separate private timing-instrumented genuine GNOME fork is BUILT; source and
  binary accepted by actual OpusR1. BinarySHA
  `b988bc4c49251c7951805b0af6ad942dd82d50052feffd338f5f6b72d43b025c`.
  Harness/doc corrections are now integrated canonicalR4, SHA
  `29b9ebf15705b68cbb43756b266e076700d2f845ab7ef405959264387d4ef0c6`.
  Root reproduced32offline tests/buildselfcheck and24recursivehashmatches.
  `gnome-no-flash-next-cost-freeze-r4.json`, parent-r4 receipt, plan/manifest/report
  and R2-to-R4delta are under executor-review. Separate cache root, no accepted
  stage2 or production changes. Solr3READY, actualOpusR2codeaccepted and
  R3documentationclosureREADY exit0. R5docsfreeze binds current explanations;
  release-r5 receipt records exactreview/model details and deferrednits. Sole
  operator released ONE bounded diagnosticrun; fresh characterselect recovery
  entered Arthur beside auctioneer again; pair and one diagnostic sample PASSED. Script stops after first completevalidtiming
  stream; second ordinal only for pure incomplete/missing first markers. It
  partitions pre-main/GTK/config/Shell/PNG/recent/shutdown/tail on one monotonic
  clock. Shutdown includes deferredrecent-fileflush and is not all removable
  by persistence. Failure stderr is explicitly unavailable through unchanged
  backend; success retains driverdecodedtext. No fabricated empty stream.
  No root capture/input overlap. Production capture remains stock and unarmed.

- Live causal diagnostic completed ONE fresh sample with all28markers, exact
  privateowner acquire/release, no errors/cleanup errors and finalbusNone.
  Receipt `~/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark-20261017T042825821377Z-1280000/receipt.json`,
  SHA `bfc3f7093c306ff7e2db451401dfa9c75a632d5b3efac2be9ebaafcab8cf95a7`.
  Parent independently verified stage sum, owner and frame; see
  `gnome-no-flash-next-cost-parent-live-verification.json` and live-result.md.
  Freshpair boot1792211238-176315, seq49→52; diagnosticseq57, schema3/build70450,
  speed0/sameposition. CLI0.82085s: Shellcall0.35715s, outputPNGencode/write0.34672s;
  GTKstartup0.05484, ShellPNGdecode0.02897, recentinmemory0.00388,
  mixedshutdown0.00405. Wholeouterpath1.67419s includes observerdrains0.30466s.
  Threeidentityresolutions0.13147/0.12560/0.12344s; postchildPIL0.05829s.
  Outer-minus-backend0.23587s INCLUDESouteridentity0.13147; actualcrop/protocol
  decode residual~0.10440s. No one-Hz or formal100 qualification.
- Coding Luna now owns PLAN ONLY `.archive/PLAN-gnome-telemetry-region.md`:
  inspect complete defaultnative100loop callbudget, compare compression-only
  with genuinecanonicalGNOME ScreenshotArea256×256 status-only capture, retain
  fullmodel/scene images. Include source-controlled smallpatch/rebuildrecipe,
  explicit opt-in privateexecutable binding, unchanged securecompletion/identity/
  timestamp/epoch/cancellation/evidence and strictschema paths. No source/build/
  runtime changes authorized yet. Solplan-r1NEEDSWORK confirmed514checkbudget;
  coding Luna revises exactrouting (bootstrap/native/status, fullmodelstock),
  retainedFD executable + nonce/pipe/livePID self-owner proof with parentACK,
  coordinatebasis gate and runnable paused8samplediagnostic. Compression-only
  branch is removed. Solplan-r2READY closes allfiveMust/twoShould. Full bounded
  offlineLunaimplementation/build/tests/canonicalfreeze NOW RELEASED. Finalplan
  SHAac1c8cbec750844c71c3eaade3f349ffc638d6d427e01c88d602d019e4a00b95;
  exactfilefence inplan, input_tool/motion/calibration/addon/model/CLI protected.
  Parent89-filebefore-snapshot `gnome-telemetry-region-parent-before.json`
  independently verifiedoldsourcehashes beforeedits. Worker must actuallybuild
  source-controlledgenuineprivateproducer+sealedimage/nonceACK, wire three
  HUD consumers, passfocusedchecks andfreezeownedcanonicalartifacts, notstop
  atdrafts. Parenttests/Sol+actualOpus beforelive. Sole operator holding; no
  GUI/capture/native attempt/profilemutation/daemonrestart/serviceenable released.

- R1offlineimplementation built binarySHA
  `248a445fbe4c382f71db37b480bb671759368595ca1cf91d6e78c4dc0e3c3bab`;
  workerreported284focusedtests/346.83s. Freeze/report `gnome-telemetry-region-r1-*`.
  Parent independentlypassed5newtargetedtests/selfharness/Ruff/allownedhashes
  and6intendedbaselinechanges, but sourcecheckpointNEEDSWORK: ACK/revocation
  admission race and no epoch callback duringprotocolwait; weak livekernel
  executable/parent/group checks; childtimestampcontainment missing; onlyfive
  newtests (fakewrapperrouting and Pythonproducer don'tprove genuineC/default
  binding); recipe/README admits forbiddenhostrepomount. No externalcode-review
  round spent yet onknownbadR1. Parentcheckpoint recorded separately.
  Coding Luna released R2fix withinexactexistingfence: preserveR1ownedBYTES,
  correct handshakelifecycle+kernelproof+timestamp, actualcompiledGNOMEprivate
  bus/display/compositorfixture, negatives and actualdefaultdaemon/provider tests,
  cache-onlycontainer/reproinvocationtruth, newprivate-r2build; finalcanonical
  tests/freeze/fullR1-to-R2delta. No live action/profile/service change authorized.



Next gates:

1. Resolve measured capture throughput without weakening identity, freshness,
   deadline, cancellation, global lease or source attribution. Review and test
   a concrete narrow change before another formal native attempt.
2. Read `docs/REPEATING_SCANS.md` and `PLAN-native-memory-measurement.md`.
   Formal identity-bound reset5 measurement requires construction<=5s/+128MiB,
   actual held0 reset, exactly100one-Hz ordinals (1..99 then held100), addon
   p99<=250ms/+16MiB, and actual fresh normal resume. No fake metrics, history
   skips, private lease, lifetime-HWM subtraction or recycled measurement proof.
   Accepted private handshake helper SHA
   `bf79d703cc9b98fc7e0842d119e69cbbfa5539f02456f8d5083d4629bdeee2d0`,
   spec/freeze-r3 and Solr3READY. Not yet live-qualified. Restart daemon unarmed
   before a new attempt if its old operation error would reject helper preflight;
   use actual persisted-state resume/gen, keep unit disabled.
3. Actual deliberate human key/click/motion sample requires user availability
   and real readiness callback. Earlier async question remains unanswered;
   never synthesize human input. Do independent technical work first.
4. Then installed capture/model latency, camera yaw, five-role movement basis
   within shared2unit travel ledger, and three real428item scans with uploads,
   loaded ACKs and closeout. Enable repeating/wakeup only after qualification.

### Resumed: HUD recovery and natural executors (2026-10-16 UTC)

User authorized HUD repair followed by realistic pointer, click, wait, key,
camera and local-waypoint executors. Use Luna implementation/game input,
Sol review and actual Claude Opus rounds. No commit, reset, stash or push is
currently authorized; preserve the large working tree and unrelated archives.

**Current action:** normal sole-client recovery plus read-only native API
observation released to the sole Luna operator under native-api-next-prompt.md.
Arthur must remain stationary/AHclosed; no camera/translation/CTM changes,
trades/services/source/git edits. All owned GTK modes now PASS independently:
seed, positive, cancel-midpath and cancel-midbuttonhold. Root verified receipt/
diagnostic digests0600, all43source hashes, exact tool image/all15seals, FIFO
raw/primary origin→endpoint transitions, button pairs/dwell, exact PID absence,
empty process/held registries and actual production global lease release.
Reports: native-gtk-seed-r14-parent-verification.json and
native-owned-proofs-r14-parent-verification.json. Positive39motionpairs/0.657s
vs planned0.765685s, click0.200s. Midpath stopped after1motion beforeendpoint;
midhold released after0.012s vs planned1.8s, bothreaped. Private receipts:
seed1792184834-2257756 SHA f6cfeac7ddfef6fa84922f4bf1776c46c4dd110e2b7b9756bd03c64859f5f746;
positive1792184928-2262688 SHA d32fa2556984dfe4564dd0f9c317fee5e1df90eeab88388936f0927ef04b98c4;
midpath1792184999-2267338 SHA 0eb1cf88f8c6598a5f66af1d6017273cfdae2f963a9d48ce2a202017ae5a1f73;
midhold1792185035-2269379 SHA 7a64b0d041ff01e17e64d4e7e94d5539baa1ddd8bfde66703ec022c47699cd15.
No game/human/camera/movement/cadence acceptance follows. Priorfailedreceipts
remain unchanged. Final43-path source-freeze-gtk-test-closure-r1.json remains
accepted by Opus14READY/Sol final-r3READY; no source task remains open.

Latest correction freeze: gtk-startup-reviewfix-r2.diff994lines/6paths against
exact reconstructed r3; source-freeze-gtk-startup-reviewfix-r2.json43paths, no
out-of-fence changes. Parent52GTK tests/2.14s +35helper tests/0.64s, global
Ruff/format236files/diffcheck pass. R13 Opus (claude-opus-5-5/CLIexit0) and Sol
NEEDS WORK findings were accepted in gtk-startup-r13-arbitration.md and completed
within the same five-file fence. Actual unmapped/ready lifecycle, exact per-query
deadline, alternate client identity, early process identity/known-child checks,
inert recorder errors, farthest targets and all-three-mode planner integration
are covered. Actual Opus r14 returned READY, no production defect. Test-only closure adds
exact partial/EOF errors, terminate/wait/reap and one cleanup, impossible fake
PIDs and a same-title tiny root sibling. Sol final-r3 approved those153lines.
Read-only preflight receipt readonly-preflight-gtk-startup-20261016T205738Z-2216155.json
SHAf4e9a569dec066816a162850cf3122937d306e00846a15b534e3a8ab365049d5
is0600/dir0700. Parent independently checked identity/tool/source/checkpoint;
command-line hashes normalize trailingNULs (readonly-gtk-r14-parent-verification.json).
Earlier754full regression remains the unrelated baseline.

Repository-move deployment repair: reinstalled the uv tool editable from current
/crowley using uv.lock-exported runtime constraints (FastAPI0.143.2→locked0.143.1);
installed crowley-session --help works and imports native-x11-3 from currentrepo.
Companion WorkingDirectory corrected to /crowley and service restarted active;
API /healthz200, sessionservice stillinactive/disabled/PAUSED. Crowley addon
symlink was dangling to /pegasus/addon/Crowley; atomically repointed to /crowley,
Agent/atlas hashes retained; Crowley_Data untouched. Records:
runtime-relink-parent-verification.json and addon-relink-parent-verification.json.
New client launched before addon-link repair, so addon load must be verified
before resource/native HUD calibration. Global API diagnostics remain valid.

Cached normal recovery succeeded: oldPID3125296/window exited before one launcher
Play. New sole WoWPID2284345/start32504898 reached Arthur, stationary beside
Auctioneer Buckler in Ironforge with AHclosed. No credentials/conflict/duplicate.
Actual partial API facts: CR_CTM true boolean false; CR_SPEED0,7,7,
4.7222218513489 then GetFramerate71.153266906738. Original0600screenshots
native-api-command-1-result.png SHAaa3f5f61fb7419623032a627fcea06b33763af9897d2a73594a40df250154729;
command-2-result SHA4bdf2b93e7a829b6aaf74107a21e9914e76c3b5624e554487adb9ee901b8b400.
Ground predicate types/results still being collected. Read-only source inventory
confirmed CTM/ground capability absent from Agent/protocol/MotionFrame; a strict
reviewed producer/consumer/admission amendment is needed before camera/movement.
Luna source worker has read-only source/primary-document research authority only;
no implementation yet. Preserve CRS1 capacity/deadlines/shared2unitledger.



The active repository is now /home/dev/repos/crowley; the old /pegasus path is
absent. Parent verified HEADad7def4 and every43-path frozen hash before resuming
there. Do not recreate the old alias. Use explicit current workdir for tools;
the parent Opus runner now derives its cwd from its own repository path.

Private receipt owned-gesture-proof-1792180878-1980816.json SHA
b8a41e519e02501e7014a0d04ce88a5f8d7e94b358bb904f86cd105dba23e572 and
diagnostic owned-gtk-diagnostics-1792180877-1980816.jsonl SHA
35b4f1f2613bc0892b596f6a1a36605b64f1f6f4773d97c86466939159861519 remain0600.
First stats showed IsUnMapped, client directroot and separate tiny Mutter frame;
later recorder stats showed IsViewable/real position/frame extents. The recorder
mistook root for frame and queried unrelated siblings; scope that diagnostic.
Fresh pointer1524,542 is outside the eventual target753,456/480x240. A canonical
owned-window placement is needed; never bootstrap-warp the pointer or accept root.
Parent verification: native-seed-r12-parent-verification.json. Preserve both failures.

**Final verification:** actual Claude CLI Opus r12 was claude-opus-5-5, exit0,
STATUS READY, with no production defect. Its test-strength suggestions and Sol's
isolated negative finding were closed in a test-only delta; Sol final-r4 is
READY with no findings. Reports: opus-executors-r12.txt and
sol-transition-final-r4.md under .archive/executor-review. Exact final43-path
freeze: source-freeze-transition-r12-test-closure-final-r1.json. All hashes match.
All40 paths outside the final three-test scope remain byte-identical to Opus's
approved implementation (r12-runtime-review-preservation.json).

Parent full strict DB regression parent-full-transition-r12 passed754tests in
558.95s/exit0, one existing Starlette/httpx deprecation. Final test-only assertions
passed25focused tests/1.27s/exit0 independently (parent-r12-test-closure.log).
Worker affected418passed and final22focusedpassed. Global Ruff, format226files
and gitdiffcheck pass. Owned disposable DB container was stopped/removed;
production DB untouched. No parent CLI/test session remains active.

The accepted transition interprets attached XTEST slave root/event/child as
origin evidence, delivered axes as endpoint, and raw as same-time FIFO ancestry.
Measured profile/root, exact query results, seal/replay, modifiers, CARD32 wrap,
click ordering, helper phases and refusal-before-input are covered. Keep the
existing finite evidence ages/deadlines, exact ownership, release/watchdog and
travel/resource limits. Active source contract is PLAN-xtest-motion-transition.md;
no coding worker has input authority or current source edits to perform.

Controller remains durably PAUSED/generation6, service stopped/disabled; API and
companion remain available. No qualifying70425 scan, production arming,
physical-human, camera/movement or repeating-scan acceptance is claimed. Latest
read-only preflight found sole WoW PID3125296/start27683142, outer0x1600001 at
1920x1080, Battle.net foreground and pointer1113,576. The inside-game scene is
unknown. The operator must verify fresh identity/environment/tool before input;
never click Play while that client exists. Private preflight receipt hashes are
retained in readonly-preflight-parent-verification.json.

After a passing seed is inspected by root, native-owned-proofs-next-prompt.md
stages the whole positive/mid-path/mid-hold outcome. The amended GTK plan pins a
distinct target within each newly centered window; a seed in a previous window
cannot guarantee that. No extra preparation seeds are staged. Then follow
PLAN-motion-live-prerequisites.md for normal sole
client recovery/read-only API facts, full resource/physical-human calibration,
actual camera/local movement and separate repeating-scan acceptance. Source/tests
cannot substitute for those live measurements. Historical r10-r12 verification
notes are preserved in executor-review/HANDOFF-transition-r12-verification-notes.md;
PLAN-natural-executors.md is the short current roadmap.

**Verified HUD/native telemetry:** compact2048-glyph renderer,336x304 surface,
zero anchor, byte glyph origin80,48 and exact2x2 cells work with explicit
CLAMP/CLAMP/NEAREST. CRS1 capacity2048/payload2000/crop256 and resource budgets
are unchanged. Parent inspected two actual GNOME frames: boot1792138102-384196,
sequence119→122, CRC9e47f25f→a4710d05, build70425, valid position/facing/speed0,
combat/deadfalse, W/S/A/D/Q bindings. Captures/crops and
native-pair-verification.json remain private under
~/.local/state/crowley/executor-evidence (0700 directories/0600 files).
Sol and actual Opus renderer-r3/r4 approved the renderer; native pixels/CRC
passed. This is wire proof, not construction/update/memory/input calibration.
GNOME screenshots work; black scrot/XImage captures did not establish a hang.

**Canonical tool verified:** vendored xdotool commit
14ca26a2c95035f9c635a6a11d075e8d7d0d6529; private version4.20261016.1,
SHA2b789272e0c1a8f2b1303c3cb48a1753741dbedf9e9d597b7a85421f50821155.
Builder/provenance are in tools/ and vendor/. System xdotool absolute motion
used XWarpPointer; the fixed private tool uses XTEST on screen0. The ELF is
SHA-verified and pinned in memfd with all four seals; ordinary dispatch/release
and spawned watchdog share it. Actual native receipts prove that image, real
registered processes and complete cleanup under the production global lease.
No PATH/system-tool/session changes or alternate emitter are used.

**Native qualification awaits a fresh seed, not a desktop switch.**
One released seed-only run failed before any click: pointer873,576 moved to
1113,576 and post-query confirmed it over the owned GTK client. Complete
RawMotion type17/device2/source4/detail0 had endpoint valuators. Following
Motion type6/device4/source4 had the same timestamp303971237, native root/event
873,576 (origin), delivered axes1113,576 (endpoint), and owned frame child.
Only2events, no echo/observer violations. The old waiter correctly refused its
expected root-coordinate endpoint. Receipt
owned-gesture-proof-1792164209-827533.json is unchanged, SHA
7b328149a463526708e22d06e0e468404272a7b7ed96acbedffa342e8e1b7a0b.
Parent independently checked the receipt, absent exact owned processes, empty
held/process registries and actual global lease acquire/release afterward.

Matching official Xserver/XI2 sources establish attached-slave delivery before
master processing. xinput prints deviceid(sourceid), not always master(source).
Slave root/event and child belong to the previous pointer/origin; delivered
axes0/1 carry the new endpoint. The new contract requires already-owned initial
origin, strict next-index origin→endpoint transitions, paired same-time raw,
root-observer coordinates/XIDs, normalized latest-primary echo matching, and
exact post-query endpoint/window plus button ownership. No outside bootstrap
warp, root/axis OR fallback, raw-only endpoint, skipped samples or master-copy
whitelist. Physical-human relative motion retains separate semantics.

Actual profile capture confirms attached XTESTsource4/parent2, exactly two RelX/Y
axes0/1, relative mode, range-1..-1/resolution0, Enabled1/XTESTDevice1/identityCTM,
root/screen0=1920x1080 at0,0. Absolute endpoint semantics come from the pinned
absolute command and server source, not an advertised absolute axis range.
Complete captured command fixtures and selected native receipt fields are
executor-review/native-input-profile-observed.json and native-transition-observed.json.
Official source/protocol files, URLs and SHA provenance are retained in
executor-review/xwayland-24.1.6-source and xinput-1.6.4-source. Five serial
repetitions per read-only query measured sum-of-medians8.194ms and sum of
individual maxima8.640ms for profile/properties/hierarchy/root/pointer only;
this excludes capture/model/admission pipeline latency.

**Verification baseline:** full strict DB-enabled parent-full-r8 passed701tests
in532.26s, one existing Starlette/httpx deprecation warning; all43source hashes
matched afterward. A preceding686pass/1DBsetupdeadlock was a Timescale telemetry
worker versus schema-reset race, not leaked app connections. Both disposable
containers were removed after testing; production database/settings untouched.
Final test environment disabled Timescale background workers/telemetry while
retaining synchronous extension/hypertable/policy-registration tests; scheduled
compression execution was not tested.

A later tiny Guardian echo-proof timestamp fix and test closure passed204affected
checks (worker157.09s), parent48focused/5.21s, global Ruff/format203files/diff;
Sol-test-closure-r2 READY. Actual Opus r9 then found the upstream
InputCalibrationEvidence.verify_seal still rejected zero/wrap timestamps.
That seal repair and a real producer→seal→DesktopDriver.arm→Guardian test are
included in the active transition batch. Isolated direct-Guardian tests did not
prove that complete handoff. Source-freeze-r13-zero.json and the43-file
pre-transition-source-snapshot retain the exact pre-implementation baseline.
Use the strict hermetic runner with a private desktop lease and no installed
private artifact for tests; never use the production global lease in unit tests.

Natural executor source already includes deterministic curves/timing, click
dwell, response waits, typed bounded key holds, right-held camera phases,
preferences and local waypoints. Camera/movement require measured mapping and
fresh native/visual feedback. Waypoint admission is conservative under full2D
uncertainty and confirmation drift, with a two-unit cumulative cap, minimum-pulse
gap and finite deadlines; the outer cap does not guarantee every target is
reachable. Handedness-1 is refused. These source tests do not prove native
camera, movement, model latency or human takeover.

**Next gates:** complete parent regression and inspect frozen Sol/actual Opus
reviews; release one owned-GTK seed, then positive click and both
cancellation boundaries only after success. Preserve every failed receipt and
verify exact reaping/empty ledgers/global lease after each process exits. Then
recover the sole game normally and obtain the read-only native API facts in
[PLAN-motion-live-prerequisites.md](../.archive/PLAN-motion-live-prerequisites.md):
Click-to-Move accessor/result, all four GetUnitSpeed returns, frame timing and
ground predicates before a strict capability/wire amendment or movement/camera
input. Full native resource gates and a real deliberate-human readiness sample
remain necessary; synthetic events cannot supply that proof. No deadline or
resource-budget relaxation is authorized to hide a failure.

Original scan acceptance remains three fresh428-item sweeps at15-minute cadence,
real rows/coverage, upload within60s, exact acknowledgement/reopen and final empty
queues with no fourth sweep. Current catalog544items/428active352core76discovery,
depth20,cadence900,600s sweepcap. Build70425 planhash
25b596810724d79e702fc4e6bd9ff5fb6d1238f2254b066d00f95625f1c88e56.
Historical build70374 data remains preserved; it does not qualify70425.

Portable lessons stay in the existing two `.agents/skills/` workflows. Historical
operational notes are retained in executor-review/HANDOFF-pre-transition-notes.md;
current facts above and exact review artifacts take precedence. The Xorg
alternative stays parked: generic DIX explains this trace, and switching desktop
has not been performed or established as necessary.

### Deployment status (2026-10-15)

The game, companion, API and database run on Linux host `3080servermach`; the repository is
`/home/dev/repos/crowley`. WoW runs locally through Lutris/Wine from
`/home/dev/Games/world-of-warcraft/drive_c/Program Files (x86)/World of Warcraft/_classic_beta_`
(1.60.1 build 70374, interface 16001). Auctionator 341 is installed with full autoscan
disabled. Crowley is a repository symlink; generated `Crowley_Data` contains the 428-active-ID,
900-second, 20-price-level plan from the 544-entry catalog. Moonlight/Sunshine and the fullscreen watcher are
disabled. The companion is active. API health and migrations 001/002 were verified. Compose
commands from the repo root require `--env-file deploy/.env`.

**Latest client change (2026-10-16 UTC):** a normal relaunch after failed reconnect
triggered Battle.net's automatic update to **1.60.1.70425**. Luna returned Arthur
to Ironforge, stationary with AH closed and Crowley disabled through the normal
AddOns UI. The strict catalog/scanner/session target refresh passed final Sol
review and was staged to API, generated Data.lua and private0600 profile; see
[build70425 plan](../.archive/PLAN-client-build-70425.md). Do not load the old
70374 plan into a new automated run or rewrite historical70374 evidence. Native
calibration, physical input proof and new qualifying scans have not started.

The verified house is `beta-normal-alliance`. The database has eight accepted sweeps, 3,424
observations and 11,139 captured price rows. Full native verification sweep
`beta-normal-alliance-1792040351-Arthur-6643` ran from 2026-10-15 04:59:11 to 05:07:15 UTC
(484 seconds), queried all 428 active IDs with zero incomplete or unqueried items, and
captured 2,889 rows across 271 row-bearing IDs and 125,395 units. This includes 306 full
commodity observations (1,328 rows), 23 bounded commodity observations (460 rows), and 99
full item observations (1,101 rows), all under the correct house. Native item examples include
equipment 873 (`873:l40`), recipe 2555 (`2555:l15`), and containers 4238, 4240, 4241, 4245
and 5765 with captured prices.

A later scheduled sweep, `beta-normal-alliance-1792041251-Arthur-0169`, ran 05:14:11–05:19:36
UTC and stored 1,599 rows. It attempted 293 items (292 successful and one active query
interrupted by AH closure) and left 135 unqueried when the AH closed after 325 seconds. This
followed the first full verification; the later pilot below added two further full
sweeps. After the second reload, the addon reported two uploaded scans cleared and loaded
plan `0712de248d42` with 428 active IDs. A further normal reload persisted the cleared queue;
the parent independently verified zero pending scans on disk. Arthur was parked
at Buckler; the later pilot closed out to character select,
and the last observed game screen was disconnected. A fresh read-only preflight
found that same client alive behind the foreground Battle.net launcher; the game
screen was not visible, so its current scene was not established. The earlier
malformed 961-row sweep remains intact in private quarantine and was never ingested. The
earlier three-row item 2555 success used a cold level-zero SellSearch path and is not proof
of current item dispatch; the new item rows retain native levels and variant identity. Sol's
review was READY, and parent checks passed: 118 addon/core tests; normal suite 149 passed
with 15 DB tests skipped; Ruff and format checks passed. The isolated full database
run used a disposable TimescaleDB container, not deployed data. See the [live validation
record](../.archive/live-client/real-validation.md) for traces, chronology and preserved
payload hashes. The 544-entry catalog has 428 active IDs in the scan plan. Scans start every
900 seconds while AH-open; each sweep is capped at 600 seconds. SavedVariables upload after
`/reload` or logout; another reload loads companion acknowledgements.

The [session pilot](../.archive/live-client/scan-session-pilot.md) added two complete
428-ID sweeps with 5,413 price rows and verified an empty disk queue after acknowledgement
and logout. It did not pass repeating-session acceptance: starts were 1,256 seconds apart,
and finish-to-upload took 312 and 217 seconds. Acknowledgements were actually published
immediately after HTTP acceptance; delayed operator observation contributed to the miss.
The editable `crowley-session` command, private configuration, and user service unit
are staged locally. The unit is disabled and inactive; no recurring controller is
operational. Production review still requires transition/restart/closeout safety,
complete retained evidence, and executable native input/rendering proof; see
[engine round 8](../.archive/REVIEW-repeating-scans-engine-8.md) and
[native round 11](../.archive/REVIEW-repeating-scans-native-11.md), plus
[auxiliary round 4](../.archive/REVIEW-repeating-scans-auxiliary-4.md).
Auxiliary, native and final engine scoped reviews are READY; live acceptance remains open.
The build70425 runtime admission guard now also rejects mismatched actual
`GetBuildInfo()` values before scheduling or querying; final independent review
is READY. Source/API/Data/profile agree on build70425 and plan hash
`25b596810724d79e702fc4e6bd9ff5fb6d1238f2254b066d00f95625f1c88e56`.
At the start of live calibration the service is manually active/unarmed and
disabled for recurrence; Crowley is initially disabled for the no-Agent baseline. All8stored
sweeps remain unchanged (3424observations/11139captured rows).
The [recovery contract](../.archive/CONTRACT-session-recovery.md) records the
implemented controller/daemon API. Final production engine review found no
remaining must-fix: pre-effect boot identity, menu proofs, exactly-once durable
qualification and live guardian rearming after pause are verified. The stale
restart fixture now includes the canonical pre-effect boot witness and passed
independent Sol review. All three scoped reviews are READY. Runtime12tests passed independent Sol; parent final qualification9
passed. The broad snapshot had400passes/15DBskips and that one fixture failure;
parent's corrected full strict suite passed402tests/15DBskips in389.41s
with all three strict warning filters and a private desktop lease.
The15database tests passed separately on a disposable container which was
removed; deployed data was untouched. Ruff/format/compile/diff checks pass.

The service is now manually active but disabled for recurrence. Parent socket
verified validation mode NATIVE_CALIBRATION/generation1, unarmed with no
native/input proof yet. The sole Luna operator is performing live calibration
from fresh verified Arthur-world/AHclosed/noAgent state. The live X11 header/child parser mismatch is fixed under
[the bounded plan](../.archive/PLAN-live-x11-tree.md). Native68+independent33
tests pass; parent and Sol each independently passed focused9. Narrow Sol
verdict READY; parent actual read-only identity resolution now succeeds.
After restart/explicit resume, actual no-Agent bootstrap passed at generation3.
Native calibration then found the default daemon never attached the reset5
memory meter (tests injected it manually). No baseline write/addon enable
occurred. Default production meter ownership, early error status and distinct Windows/
Linux identity proof are now corrected and passed final narrow Sol review
(READY, no findings). Parent28strict tests passed; Luna native68/runtime13/
independent33 and existing session suites passed. Sole Luna operator is cleared
for a fresh native attempt after restart/explicit resume, with no test load.
Use immediate bootstrap/calibrate chaining for the10s capture freshness limit. No physical sample, new qualifying sweep,
or recurring enablement is established. The current facts and remaining live
acceptance are in the [acceptance record](../.archive/live-client/repeating-session-acceptance.md).
Native memory acceptance follows the
[measurement clarification](../.archive/PLAN-native-memory-measurement.md): separate
reset kernel high-water windows, with Lua net heap samples as diagnostics only.
Host reset capability has been verified; the live performance windows have not.
The user authorized completing a durable local
repeating system; implementation follows the [reviewed contract](../.archive/PLAN-repeating-scans.md)
with Luna implementation and Sol review, then real rendering/input calibration and three
new full sweeps at 900±5-second starts with upload within 60 seconds. The controller must
pause on takeover and restart, and require explicit resume. Do not mark this capability
complete from the pilot or automated tests alone.

### Format-2 cutover

Before deploying this format-2 addon and server together, run the old addon against the old
server until its SavedVariables have been uploaded and acknowledged. Reload once to write the
old pending scans, let the companion write acknowledgements, then reload a second time and
confirm the old addon's pending queue is empty. Only after that acknowledgement check should
the addon and server be upgraded as one coordinated change. The new server accepts format 2
only; it preserves the already-flushed legacy rows and archives but has no legacy decoder or
full-scan fallback. If the old queue cannot be emptied, stop the cutover and fix that upload
path before collecting new sweeps.

---

## 1. What we are building and why

The user (Kyle) wants a private gold-making platform for the auction house in
**World of Warcraft: Forever**, plus an addon to act on it in game:

1. **Pull live AH data** and store retained observation history with explicit coverage.
2. **Make gold from it** using:
   - arbitrage, including faction houses vs neutral houses and vendor flips
   - high-demand items
   - ML prediction of price increases
   - anomaly detection
3. **Execute in game seamlessly** through the **Auctionator** addon: buy and sell lists the
   backend computes, ready to use the next time the user is at the AH.

The first milestone was the foundation: targeted scanning, retained observations, and the round
trip between game and server. Strategies come next.

### Explicit user requirements (from the conversation)
- **Private tool, single user.** No accounts or multi-tenancy, and no protection against
  poisoned crowdsourced data. Design so it *could* open up later, but don't build for that.
- **Current deployment:** game, companion, API and database run on the same Linux host.
  WoW is running locally through Lutris under Wine. Moonlight/Sunshine was a prior Steam
  Deck display/controller path on this host and is currently disabled.
- **The game runs on Linux under Wine.**
- **Region, ruleset and faction are chosen at scan time.** The user must be able to switch
  between houses freely. The database keeps each house separate and never mixes them.
- **No fallbacks** (strong preference, stated explicitly). Keep the codebase clean: assume
  one way things work, encode only that, let it fail loudly, and fix it if wrong. No
  "try A then B", no optional-dependency checks, no defaults that hide missing data, no
  multi-format decoders. Write every assumption down (see §6).
- The user is **in the Forever beta** and can test in game.
- Use subagents for investigation-heavy work.
- Commit or push only when the user asks.

---

## 2. Timeline (critical)

| Date | Event |
|---|---|
| 2026-09-12 | WoW Forever announced at BlizzCon |
| 2026-09-17 → **2026-10-21** | Beta. **The only chance to test the addon against a live AH before launch** |
| 2026-10-27 → 11-03 | Name reservation (no AH) |
| **2026-11-04, 3pm PT** | Launch. The user first thought it was "in two weeks"; the real date is Nov 4 |

Launch week is when prices are highest and most volatile (fresh economy, no WoW Token), so
the pipeline must be reliable before then and the first strategies ready.

---

## 3. Research findings (2026-10-14)

Three research agents covered the game, foreverwowcraft.com, and Auctionator plus the
addon data flow. Below, "confirmed" means from official or primary sources; the rest is
reported by fans or the press.

### 3.1 WoW Forever
- A third permanent WoW version alongside Modern and Classic. It's a reimagined original
  Azeroth: level 60 cap, new zones, a new Skyborne race. PC and Mac, included with the
  subscription. Confirmed.
- **Realmless** (confirmed by Wowhead from a Blizzard announcement). Players pick a region
  and a ruleset: Normal, PvP, RP, and Hardcore after launch. Factions can't group with each
  other.
- **AH structure** (reported): one house per (region, ruleset, faction), plus neutral goblin
  houses in Booty Bay, Gadgetzan and Everlook. Faction houses take a 5% cut, neutral 15%
  (Classic Era rules). Deposits are based on vendor price and lost if the item doesn't sell.
  Listing durations are reported inconsistently.
- **Client:** retail-derived. Blizzard said it shares "the vast majority of APIs available
  in 12.1.5". Beta interface 16001, build 1.60.x. The TOC suffix is currently `_Camelot`,
  which Blizzard says will be renamed. Some old globals such as `GetItemInfo` are gone; use
  `C_Item.*`. Midnight-style combat addon restrictions apply.
- **AH API:** retail-style (commodities bought by quantity), so `C_AuctionHouse` targeted
  item-key queries are used. Result event freshness, metadata and pagination behavior remain
  beta assumptions until a live client test.
- **No Blizzard Game Data API for Forever auctions.** Nothing documents one, and the client
  "exposes no API". All data has to come from in-game scans. The classic API was also
  unreliable (frequent 404s), and a realmless game doesn't fit its "connected-realm" model.
- **No WoW Token, no boosts.** Gold supply comes only from farming, so prices should start
  high and fall over the first weeks.
- **Temporary Economy Hold:** Blizzard freezes trade, mail and AH access for accounts with
  suspected real-money-trading gold flows, and warns of false positives. Very large or odd
  gold movements carry account risk. About 3,700 beta accounts were banned for RMT.
- **Reported economy notes:**
  - A vendor next to the Black Market AH sells Black Lotus and Arcane Crystal at 50g, which
    caps their price.
  - Black Market AH is bid-only, 100g–3,000g.
  - In beta, Dungeon Set 1 pieces sold around 100g, low-level blues 10–25g, raw materials
    for silver.
  - Beta gold and characters are wiped at launch.
- **Automation rules:** buying, bidding, posting and cancelling need a hardware event
  (a real click or key press), one protected call per click. Input injection, memory
  reading and unattended buying get accounts banned. Reading SavedVariables and writing
  addon data files from outside the game is the accepted pattern (TSM's desktop app does
  it).
- Sources include Wowhead, Blizzard news, Icy Veins, PC Gamer, warcraft.wiki.gg TOC_format,
  and the Blizzard forums.

### 3.2 foreverwowcraft.com (reference site)
- The public site describes profession leveling plans and player-provided auction data.
  Only its public pages and current plans were inspected; its backend, API, data retention,
  and ingestion implementation are not established. Treat older notes about static files,
  lack of history/API, and its internal item keys as unverified.
- **Ideas worth evaluating from the public product:**
  - Static JSON on a CDN, if we ever publish a site.
  - Costing that walks up the price ladder, so buying more units costs more.
  - Sell-probability weights: reagents 0.9, consumables 0.8, green gear 0.35, blue gear 0.5.
  - Auctionator import strings.
  - A 15-minute snapshot cooldown and a 5% AH cut.
- Its downloaded files are on the old machine only; don't rely on them.
- **Other Forever AH tools:** Hammerprice, Grimlight Auctions, AHledger (web plus sync app;
  counts 18 houses across US/EU/CN), auxForever, Forever Guide, bootybaybroker.com/forever.
  All rely on in-game scans because addons can't reach the network.

### 3.3 Auctionator (integration target)
The GitHub repo `github.com/Auctionator/Auctionator` returned 404 when we checked. We read
v321 (May 2026) from a downloaded copy. Key facts:
- **API** `Auctionator.API.v1.*`: the first argument is always a caller ID string (we use
  `"Crowley"`), and errors are raised as Lua errors. Functions we use or will use:
  - `ConvertToSearchString(caller, {searchString, isExact, maxPrice(copper), quantity, ...})`
  - `CreateShoppingList(caller, name, searchStrings)`: replaces any list with the same name.
  - Also available: `GetAuctionPriceByItemID` / `GetAuctionPriceByItemLink`,
    `MultiSearch` / `MultiSearchExact` (AH must be open), `RegisterForDBUpdate`, and
    `GetShoppingListItems` / `AlterShoppingListItem` / `DeleteShoppingListItem`.
- **Search string:** 14 fields separated by `;`:
  `"Name";category;minIlvl;maxIlvl;minLvl;maxLvl;minCLvl;maxCLvl;minPrice;maxPrice;quality;tier;expansion;quantity`.
  Prices here are in **gold** (copper / 10000, decimals allowed). Quotes around the name
  mean an exact match.
- **Import format** (paste into Auctionator's import box): one list per line,
  `ListName^item1^item2...`.
- Its own price database is thin: one minimum price and maximum quantity per day, partly
  stored as compressed binary (CBOR). **Don't use it as a data source**; Crowley stores targeted retained observations.
---

## 4. Design decisions (and why)

| Decision | Reason |
|---|---|
| In-game addon scan → SavedVariables → companion → server | Addons have no network or file I/O, and there's no official API. SavedVariables are written only on `/reload`, logout or exit |
| Server → companion → `Crowley_Data/Data.lua` → game | The only way to get data into the game. Addon files are read only at login or `/reload` |
| Companion **polls** file mtime and size, and waits until they hold still for one interval | Wine prefixes and network mounts make inotify unreliable, and we must never read a half-written file |
| Upload acknowledgement through `Data.lua` (`ackedScans`); the addon prunes acked scans on load and keeps at most 6 unacked | Keeps SavedVariables small without the companion ever writing to the game's own file |
| House = `(region, ruleset, faction)` with faction in alliance/horde/neutral. The key looks like `us-normal-horde`, is decided **in game at scan time** (auto-detected, overridable with `/crowley set`), and is stored on every scan | Realmless game, plus the user's requirement to switch houses freely. Raw client context is stored too so attribution can be audited |
| Items keyed by `itemKey` = item ID, plus `:s<suffix>` for random-suffix gear, `:b<sorted bonus ids>`, `:l<itemLevel>`, and `:p<battlePetSpeciesID>` when nonzero. Never by name | Names are locale-dependent and ambiguous (foreverwowcraft's weakness); raw key fields remain alongside the canonical key |
| Store the cheapest 20 distinct unit-price levels plus every row at the retained boundary | Preserves explicit bounded coverage and row identity without claiming whole-market supply |
| Public listing churn is a separate uncalibrated proxy; own Sold evidence is separate | A disappearance is not a confirmed sale and no sale probability is inferred |
| Rows are raw-deflated and base64-encoded in SavedVariables | Payload size depends on retained rows, variants, links and owners; the representative 428-item sample is documented in WATCHLIST.md |
| Python 3.12, FastAPI, psycopg3, **PostgreSQL 16 + TimescaleDB 2.17.2** | Python suits ML. Timescale gives time-partitioned tables plus compression for listing data |
| Docker Compose for db + server; the companion runs on the game machine under systemd | The companion must sit next to the Wine game folder |
| Single bearer token, compared in constant time | Single user over Tailscale |
| Database bound to localhost only; the API binds to `CROWLEY_BIND` (localhost or the Tailscale IP) | The only network surface is the API |
| SavedVariables parser written in pure Python, never executing Lua | The files come from the game folder |
| Raw scans archived as gzip JSON under `data_dir/raw/<house>/<day>/` | Stats and models can be recomputed from source |
| `Crowley` addon is symlinked from the repo; `Crowley_Data` is a real copied folder | Repo edits show up after `/reload`; companion writes must not dirty the repo |
| Auctionator and Crowley_Data are **hard** TOC dependencies | The no-fallback rule |
| Only the generic `Crowley.toc` (no `_Camelot`/`_Forever` copies) | The client loads the generic TOC when no flavor-specific one exists |

---

## 5. Current state

### Built and tested
```
addon/Crowley/          Core.lua (events, SavedVariables, prune), Context.lua (house detection),
                        Scanner.lua (targeted watchlist scan), Bridge.lua (Auctionator lists),
                        Probe.lua (/crowley probe), Commands.lua (/crowley ...)
addon/Crowley_Data/     Data.lua placeholder; the companion overwrites it
src/crowley/core/       savedvars.py (parser), scanformat.py (strict format-2 validation), volume.py, house.py, luawriter.py
src/crowley/server/     app.py (FastAPI), ingest.py, db.py (migration runner), migrations/001_init.sql
src/crowley/companion/  sync.py (poll/upload/write Data.lua), config.py, __main__.py (CLI)
deploy/                 docker-compose.yml, Dockerfile, .env.example, crowley-companion.service
tests/                  wow_harness.py runs the REAL addon Lua under Lua 5.1 (lupa) with a fake WoW API
```

- **In-game commands:** `/crowley scan [force]`, `status`, `set <region|ruleset|faction> <value|auto>`,
  `lists`, `probe`.
- **API** (every endpoint except `/healthz` needs `Authorization: Bearer <token>`):
  - `GET /healthz`
  - `POST /v1/scans`: upload a scan; idempotent on scan id.
  - `POST /v1/probes`
  - `GET /v1/houses`
  - `GET /v1/houses/{key}/latest?search=&limit=`
  - `GET /v1/houses/{key}/items/{item_key}/history?days=`
  - `GET /v1/houses/{key}/items/{item_key}/volume?hours=`
  - `POST /v1/addon-data`: returns `{generatedAt, ackedScans, scanPlan, shoppingLists}`.
    `shoppingLists` is always empty until the strategy engine exists.
- **Companion CLI:** `crowley-companion run|once|doctor|install-addon`.
  - Config is in `~/.config/crowley/companion.toml`, or the file named by
    `CROWLEY_COMPANION_CONFIG`. Fields: `wow_dir`, `server_url`, `api_token`,
    `poll_seconds`, `refresh_minutes`.
  - State is in `~/.local/state/crowley/companion-state.json`.
- **Tests:** the real Lua addon harness covers structured API calls, fresh result barriers,
  depth boundaries, paging, throttle/cap behavior, logout/closure, owned completion and
  SavedVariables lifecycle. Run `uv run pytest`; database tests require
  `CROWLEY_TEST_DATABASE_URL` as described in the README. A full native run verifies prices
  across all 428 active IDs, including commodities, recipes, containers and equipment. A
  later scheduled scan ended after 325 seconds when AH closed, leaving 135 items unqueried.
  Both saved scans were acknowledged and the second reload cleared the pending queue.

### Live client status
The installed beta client has successfully uploaded two `/crowley probe` captures after
reload. Native values include region 110, empty region name, realm `Classic Beta PvE 2`,
portal `test`, locale `enUS`, and faction `Alliance` in Ironforge. See §6 for remaining
assumptions and the linked live validation record for full native query verification.

### Not built yet
- Inferring sales from listings that disappear.
- The strategy engine and real shopping lists.
- The "next action" executor button.
- A dashboard.
- ML forecasting, anomaly detection, alerts.
- Backups and monitoring.

---

## 6. Client facts and assumptions to verify

Each one is encoded as the single path in the code. If one is wrong, fix that path; don't
add a second one.

| Assumption | Code | Symptom if wrong |
|---|---|---|
| **Live observed:** this Wine client's1920x1080 capture has UIParent1365.333374x768/effectiveScale1 while `GetPhysicalScreenSize()` incorrectly reports1280x800. The telemetry presentation profile is explicitly1920x1080; renderer origin/scale require native pixel proof | `Agent.lua`, driver profile | Stale physical-size API misaligns the status crop; reject invalid geometry rather than trying alternate mappings |
| **Renderer design:** zero-origin surface anchored TOPLEFT UIParent0,0; glyphs share its effective scale and include the pinned crop offset | `Agent.lua` | Removes parent-versus-self SetPoint offset ambiguity; real native crop proof still required |
| **Chosen asset:**16x51232bitRGBA TGA with bottom-left origin,256 LSB-first byte glyphs; source explicitly requests CLAMP/CLAMP/NEAREST plus pixel-grid snapping; harness uses recorded sampler arguments | `Textures/ByteAtlas.tga`, harness | All256glyphs/header verified in tests; actual native frames119→122 passed exact binary2x2cells and CRC; full resource/input gates remain pending |
| **Validation procedure:** normal full client restart after installing a new texture asset, before enabling and measuring Crowley | local game workflow | Reload-only validation may not discover a new file |
| **GTK readiness contract:** owned client must report one IsViewable map state and one valid `_NET_FRAME_EXTENTS`; only initial create may wait for recognized incomplete mapping/reparenting within its single deadline | `session/calibration.py` | Published XID alone can precede mapping; wrong/malformed facts fail hard and post-ready drift has no grace |
| **GTK placement request:** GTK3 MOUSE before show_all requests initial placement; certified native client rectangle and fresh pointer/window query determine actual ownership | `session/calibration.py`, owned proof helper | Window manager may constrain placement; refuse an outside origin without warping or accepting root |
| **Supported movement convention:** measured character-left must have handedness+1 relative to world-facing; reflected bases are refused before sealing or waypoint use | `session/daemon.py` | Unsupported convention fails explicitly; live70425 measurement is still required |
| **Waypoint admission:** one-pulse endpoint guarantee includes2D heading/speed uncertainty and full confirmation position/facing drift, minimum/profile limits and cumulative2-unit cap; exact admissibility is computed, including lower gaps | `session/daemon.py` | Infeasible requests are refused before camera/translation; source simulations do not establish game repeatability |
| Interface 16001; the plain `Crowley.toc` loads | `addon/*/*.toc` | Addon missing or marked out of date |
| `MakeItemKey`, `GetItemKeyInfo`, `SendSellSearchQuery`, matching result events and owned-query APIs exist | `Scanner.lua` | Lua error or explicitly incomplete observations |
| Search result events carry the active item key; stale, unrelated or no-payload events are ignored | `Scanner.lua` | The item remains incomplete until a matching response arrives or its timer expires |
| **Live observed:** `GetCurrentRegion()` returns 110 and `GetCurrentRegionName()` returns empty. **Code mapping:** 1=us, 2=kr, 3=eu, 4=tw, 5=cn, 110=beta | `Context.lua`, `house.py` | Unknown numeric IDs fail |
| **Live observed:** realm is `Classic Beta PvE 2`; `/crowley status` reports `beta-normal-alliance(auto)` after the correction. **Code behavior:** beta auto-attribution maps only that exact realm to normal and rejects other beta realms | `Context.lua`, `house.py` | Avoids merging unverified beta realms |
| **Assumption:** launch realm labels Normal, PvP, RP and Hardcore identify rulesets | `Context.lua` | Unknown names fail; verify against live launch behavior |
| English zone or subzone text identifies the neutral houses | `Context.lua` | Neutral scans saved under a faction house |
| Native probe exposes `C_EncodingUtil`, `C_AuctionHouse`, and `C_Item`; `C_RealmInfo` is absent and `C_GameRules` is present | `Probe.lua` | Surface presence is observed; API behavior remains to verify |
| Commodity `SendSearchQuery` and class-aware item dispatch produce matching native results | `Scanner.lua` | Verified by retained commodity, recipe, container and equipment prices in full sweep `beta-normal-alliance-1792040351-Arthur-6643` |
| **Live observed and fixed:** empty Lua tables serialize as `[]`; the native contract accepts that only for empty collections, requires objects for nonempty keyed collections, normalizes them to dictionaries, and rejects `{}` empty / nonempty arrays | `Scanner.lua`, `scanformat.py` | The earlier 422 row/count mismatch at `observations.3825.rows` is historical; the original scans now POST 200. No archive payload format changed |
| Full source-complete coverage at exactly N retained levels uses an unbounded cutoff and unknown witness; bounded coverage needs a strictly higher N+1 witness | `Scanner.lua` | Producer correction is accepted by strict validation and the latest commodity sweep ingested successfully |
| **Native/source verified, correction active:** attached XTEST slave Motion root/event coordinates and child identify the origin; delivered axes0/1 identify the endpoint under the sealed absolute-command profile. RawMotion is ancestry only | `input_events.py`, `guardian.py`, `calibration.py`; [transition plan](../.archive/PLAN-xtest-motion-transition.md) | Root-as-endpoint rejects valid input; endpoint ownership needs exact post-query and button child. No outside-origin bootstrap or raw-only proof |
| SavedVariables strings use `\n` or backslash-newline and `\ddd` escapes | `savedvars.py` | Companion stops with a parse error and line number |
| Auctionator v1 API as described in §3.3 | `Bridge.lua` | Lua error when the AH opens and lists exist |

**Beta checklist for the user:**
1. Install and configure the companion (§7).
2. In game, run `/crowley probe`, then `/reload`. The probe lands in the `client_probes`
   table. Inspect `probe->'namespaces'` and `probe->'context'`, including the realm string.
3. At an auctioneer, run `/crowley status`, check the house key and loaded plan, then
   `/crowley scan`. Wait for "sweep saved", then `/reload`.
4. Check the companion log and `GET /v1/houses`.
5. Repeat at a neutral house and on the other faction.
6. Keep one or two real raw format-2 sweeps from `data_dir/raw` as **test fixtures** (copy
   them into `tests/fixtures/`), and add a test that validates exact coverage and identity.

---

## 7. Deployment (server + separate game machine)

**On the server (database + API):**
```sh
git clone <repo> ~/repos/crowley && cd ~/repos/crowley
cp deploy/.env.example deploy/.env
# Fill in CROWLEY_API_TOKEN and CROWLEY_DB_PASSWORD:
#   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Set CROWLEY_BIND to the server's Tailscale IP: tailscale ip -4
chmod 600 deploy/.env
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d --build
curl http://<tailscale-ip>:8080/healthz
```
The first start logs a few "connection refused" errors while TimescaleDB restarts after
initializing. The pool retries, then applies migrations. That's normal.

**On the game machine (Linux + Wine):**
```sh
git clone <repo> ~/repos/crowley && cd ~/repos/crowley && uv sync
mkdir -p ~/.config/crowley && cat > ~/.config/crowley/companion.toml <<'TOML'
wow_dir    = "/home/<user>/.wine/drive_c/Program Files (x86)/World of Warcraft/<flavor folder, e.g. _forever_>"
server_url = "http://<server tailnet name or 100.x IP>:8080"
api_token  = "<same CROWLEY_API_TOKEN>"
TOML
uv run crowley-companion install-addon
uv run crowley-companion doctor
cp deploy/crowley-companion.service ~/.config/systemd/user/
systemctl --user daemon-reload && systemctl --user enable --now crowley-companion
```
- The game machine needs the repo because `install-addon` symlinks `addon/Crowley` from it
  (`REPO_ADDON_DIR` resolves relative to the editable install).
- The systemd unit assumes the repo is at `~/repos/crowley` and `uv` is at
  `~/.local/bin/uv`.
- Auctionator must be installed in the game.

**Operations:**
```sh
docker compose --env-file deploy/.env -f deploy/docker-compose.yml logs -f server
docker compose --env-file deploy/.env -f deploy/docker-compose.yml exec db psql -U crowley
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d --build    # redeploy after pulling code
docker compose --env-file deploy/.env -f deploy/docker-compose.yml down -v          # DESTROYS ALL DATA
```

---

## 8. Gotchas

- **Schema changes are now new migrations.** `001_init.sql` was edited in place during
  development because there was no real data. From the moment the server holds real data,
  add `002_*.sql` and so on. The runner applies files in name order and records them in
  `schema_migrations`.
- **Timing:**
  - SavedVariables are written only on `/reload`, logout or exit, so a scan reaches the
    server only after one of those.
  - `Data.lua` reaches the game only on the next login or `/reload`.
- **Cadence and caps:** starts are 15 minutes apart while the AH is open. A force scan starts
  the same serialized pipeline immediately but still respects the 100-message rolling throttle,
  30-second per-item budget, 10-page cap and 600-second sweep cap. Capped, timed-out, logout and
  closure work is retained as incomplete or unqueried coverage and the rotating cursor advances.
- **The companion is strict by design:** a parse error or a rejected upload (4xx/5xx) stops
  it, and systemd restarts it. Only connection failures are retried quietly. Fix the root
  cause rather than adding tolerance.
- **Test harness:** the lupa runtime uses `encoding="latin-1"` so Lua byte strings
  round-trip. Python callables cross the boundary as latin-1 `str`.
- `/v1/houses/{key}/items/{item_key}/history` defaults to the last 7 days.
- **Auctionator units:** `term.maxPrice` passed to the API is copper; the
  serialized search-string price field uses gold (copper/10000).
- **Neutral houses** cost 15%, not 5%. Every arbitrage calculation must use `House.ah_cut`.
- **Market reports:** new volume reports expose explicit coverage, bounded depth and null
  rates where grouping or evidence is unknown. Legacy `item_stats` rows remain historical and
  are not used for new observation comparisons.

---

## 9. Roadmap / future goals

Priority order:

1. **Beta verification (until 10-21):** run the §6 checklist, fix any wrong assumptions,
   and save real fixtures.
2. **Backups:** nightly `pg_dump` of the database plus a copy of the `crowley-raw` volume.
   Also alert or log loudly when no scan arrives for a house within N hours.
3. **Inferred sales:** compare consecutive scans of a house. An auction that disappears
   before its time-left band could have expired counts as a probable sale; one that
   expires doesn't. This gives sell-through rate and sales per day per item, which is the
   demand signal. Needs stable captured result IDs plus owner, quantity, price and variant
   identity across scans; Crowley currently reports this as an uncalibrated public-market
   proxy and never calls it confirmed sales.
4. **Strategy engine (server), each producing shopping lists in `/v1/addon-data`:**
   - **Vendor flip:** buyout per unit below the vendor sell price. Needs vendor prices;
     add a reviewed vendor-price table; client result fields do not provide vendor prices.
   - **Deals:** listings well below the house market value or a rolling median.
     Robust z-score / MAD.
   - **Faction vs neutral arbitrage:** buy in one house, sell in another, net of 5%/15% cuts
     and deposit risk. The neutral house is shared across factions, which makes it the
     natural bridge.
   - **Crafting margin:** needs recipe data.
   - **Depth-aware costing:** price up the ladder for multi-unit buys (foreverwowcraft's
     idea).
   - **Launch dynamics:** prices start high and fall as gold enters the economy. Sell into
     early demand and buy after it eases.
5. **Executor in game:** a "next action" button. One protected call per click, and each
   click checked against the strategy limits (max price, quantity) before it calls
   Auctionator or `C_AuctionHouse`. No automation of the clicks themselves; that's a ToS
   red line.
6. **Dashboard:** a minimal view of houses, deals and item history. Could be static JSON
   plus a small page, foreverwowcraft-style.
7. **ML and anomaly detection** once there are 1–2 weeks of history: price-direction
   forecasting (e.g. gradient boosting on lagged stats, quantity, sell-through, time of
   day / day of week), anomaly alerts, and alert delivery (push or mail).
8. **Account safety:** keep gold flows looking normal given the Economy Hold. Avoid huge
   single trades in launch week.

---

## 10. Working agreements

- No fallbacks (see §1). Write every new assumption into §6 / ARCHITECTURE.md.
- Match existing style: compact, commented where non-obvious, no speculative abstractions.
- Run `uv run ruff check . && uv run ruff format --check . && uv run pytest` before
  declaring work done. Run the database tests against a throwaway `crowley_test` database.
- Ask before committing or pushing, and before destructive operations
  (`down -v`, `TRUNCATE`, dropping data).

### Contributor workflow

Reusable agent skills are versioned in `.agents/skills/`; `AGENTS.md` routes workers to
the applicable instructions. `local-game-control` records GUI lessons, and
`crowley-client-contracts` records native API and serialization lessons. Keep related
lessons consolidated there instead of scattering duplicate guidance.
