# Launch readiness checkpoint

Updated 2026-10-24. The authorized offline plan is complete through Luna
implementation, Sol review and independent parent verification. Publication to
origin/main was explicitly authorized by the user on 2026-10-24. The existing
suite-green worktree and beta evidence remain intact. No production migrations,
deployment/service changes, game input or gold arming were performed.

## Final verification

- Bare `uv run pytest`: **2455 passed,25 DB-gated skips,33 warnings**;
  **153.784s external wall time**, excluding lock wait, with16 bounded xdist
  work-stealing workers. All83 frozen source hashes remained unchanged.
  `parent-verification-final-r4.json`, `parent-default-final-r4-pytest.log`,
  `final-r4-source-sha256.json` are the final integrated authority.
- The shared-database parallel CLI guard correctly refused before collection
  (exit4). Final serial owned disposable DB/target/trading matrix: **178 passed,
  zero skips,34.076s**, including every default DB-gated case;
  `parent-database-final.json` / `.log`. Production remains migrations001–008.
- Final parent driver/pointer matrix:71 passed,1 warning,3.409s, four frozen
  hashes unchanged; `parent-mail-driver-round8.json` / `.log`.
- Scoped Ruff check/format passed for all72 changed/new Python files; compile
  checks and `git diff --check` passed. Generator `--check` and installed
  `crowley-session mail-loop-start --help` passed. Repository-wide archive lint
  has unrelated historical findings; no claim of an archive-wide clean run.
- Trading/analysis digest remains the reviewed comparison digest:
  `f89c428800bde8b90457838a5db61bbb191a4b6bf471f98059c06aad8f39953c`.
  See `parent-trading-digest-final.json`.

## Accepted implementation

- Suite:16 workers, five duplicate tests plus one forwarding helper removed;
  independent financial, identity, takeover, native-input and rate/cleanup
  oracles retained. Final duplicate lifecycle assertions were transplanted
  into the retained armed composition. No native marker exclusion. Standard
  pytest failed-only temporary retention prevents passed frame-heavy fixtures
  accumulating; existing data was not manually cleaned.
- Parallel fixture stability: all six Xvfb creators share allocation/readiness
  synchronization, released before test bodies. Revocation tests await physical
  cleanup before exercising a real late stale-generation call. Modeled typing
  preserves every key and semantic effect while publishing character-only HUD
  changes at actual capture/readback boundaries. Production timing is unchanged.
- The full-size330-item/240-sweep statistics computation and correctness checks
  remain. Its flaky local10s microbenchmark was deleted explicitly; caller-only
  CPU timing was rejected because it omitted child work. The external180s
  default-suite gate remains authoritative.
- Launch target: strict packaged JSON, reproducible generator/drift checks,
  coordinated Lua/TOCs/client export and staged config, alternate-plan actual
  producer/consumer ACK proof. Current values remain verified beta identity;
  launch facts are not guessed or relabeled.
- Trading: shared explicit immutable tool/category/focus gates in strategy and
  execution, paper capability metadata in new migration009 (disposable DB only).
  Bronze Tube requires focus1/category162, without an exact hammer/tool row.
  Comparable10 profession pairs/290 beta sweeps provisionally favor alchemy+
  engineering: +60.7899g realized,3512 modeled clicks,6.5528g lost deposits,
  52.88% drawdown. Final718.3512g equity includes637.5613g unrealized inventory.
  Three alternate listing policies returned less realized profit/more clicks;
  keep24h/exposure defaults and repricing off. This is not a launch forecast.
- Executor schema6: exact queue identity/arms/readiness/progress, strict schema5
  refusal and actual varied serialized payload proofs. Coordinated deployment
  is required at launch.
- Guarded click: exact private ownership, raw durable pre-intent bytes, refreshed
  call-local receipt/anchor, final semantic/rate checks, full curved motion and
  press/release, immutable staged outcomes and fresh-owner recovery.
- Mail runtime: process-local/off-by-default opt-in, once per exact loaded scan
  ACK; coherent full-work and return/AH budget; fresh confirmation per armed
  message; observe-only mail_wait; async terminal completion without another
  click. Durable exact raw pre/post proofs and receipt-free causal terminal
  observations, strict private capability and immutable recovery, start/stop
  races and staged/restart/resume fences are complete. Absolute bounds cover
  initial identity/capture/model/builder and nested physical input through
  readback. Matching continuation cleanup and ordinary fresh-Guardian rearm
  return collection to WAIT_DUE without a compensating public resume.
- Retained default unarmed and two-confirmation armed whole-cycle tests use
  actual Lua/pixel/public IPC/Guardian/input boundaries, measured mailbox facts,
  return walk/fresh mail-closed proof and guarded Jaxon/SoftTargetInteract/
  CTRL-F12 AH reopening. No world-click ahOpen path exists.

## Final reviews

All listed slices are Sol READY; review artifacts retain findings and scope:

- Runtime: `../mail-loop-20261023/sol-mail-runtime-final-review.md`.
- Composition: `../mail-loop-composition-20261024/sol-review-final.md` and
  `sol-composition-stability-review.md` in that directory.
- Controls: `../mail-loop-controls-20261024/sol-review-final6.md`.
- Recovery: `../mail-loop-recovery-20261024/sol-review-final.md`.
- Final suite compatibility/tuning: `sol-final-fixture-compat-review.md`,
  `sol-suite-final-tuning-review.md`, `sol-tmp-retention-review.md`,
  `sol-native-stability-r12-review.md`,
  `sol-statistics-benchmark-cleanup-review.md`.
- Driver Round8: Sol suite_review reported READY in the parent conversation;
  the parent independently reproduced71 passing cases on that four-file freeze.
  No separate reviewer-authored Round8 archive was supplied.

Earlier red runs and source freezes remain historical evidence, not current
acceptance. STATUS-before-final-completion-20261024.md and
STATUS-history-20261024.md preserve the prior checkpoints.

## Launch-only work

Read docs/HANDOFF.md and docs/LIVE_TRADING_TEST.md. The beta has ended; no game
operation until the November4 launch and relevant authorization. Record actual
launch identity/house/export, review staged configuration, back up and deploy
coordinated source/migrations at an authorized boundary. Remeasure routes and
button geometry; qualify focus/native input/takeover, callback/protected APIs,
mail timing, one supervised unarmed round trip and three autonomous900s
collection cycles. Gold tests require explicit authorization for the exact
queue. No live acceptance, retry permission or autonomy is inferred from offline
proofs; preserve uncertain journals and all private evidence.

All pytest/vitest uses flock /home/dev/.cache/r-pg.lock and pinned CARGO
/home/dev/.cache/crowley/rust-toolchain-1.85.1/toolchain/bin/cargo.
