# Crafting listing policy and beta portfolio

User authorized remaining launch prep through Luna implementation/Sol review.
Station phase is reviewed READY. Comparable ten-pair empty-capability baseline
is complete, sealed in launch-readiness-20261023/gated-pair-summary.json.
Parent alone reads private raw reports; workers use aggregate evidence.

## Outcome/order

1. Add optional, strict crafting-only controls for listing duration, smaller
   demand-bounded exposure, and bounded aged-listing cancel/reprice behavior.
2. Preserve existing listing-control defaults exactly. New paper portfolio defaults
   change only per the parent amendment below. No registry, account/execution
   realism, capability gate, native/game/queue changes.
3. Test causal decisions and engine accounting with small synthetic cases.
4. Sol review, then parent independently verifies and replays a small fixed
   comparison grid on the same private beta dataset before recommending policy.
5. Root integrates portfolio recommendation and measured limitations into handoff.

## Exact Luna ownership

- src/crowley/trading/strategies/crafting.py
- tests/test_trading_listing_policy.py (new)
- docs/TRADING.md (policy usage/semantics only, no invented evidence)
- .archive/crafting-listing-policy-20261023/ (progress/evidence)

No other files; request parent scope amendment if a concrete blocker requires it.
Do not change baseline aggregate artifacts or read private raw data/credentials.

## Requirements

New params: listing_duration_hours default24, allowed12/24/48; post_horizon_hours
None by default (disabled) or finite positive <=48; reprice_after_hours None by
default (disabled) or finite positive; reprice_gap default0.05 strictly(0,1);
max_cancels_per_step default1 integer1..50 (reject bool); all numeric controls
reject bool, nonfinite, wrong type. No silently coerced strings or zero bounds.

Optional post horizon caps *aggregate currently listed* output per item to
floor(demand_units_per_day * capacity_share * horizon/24), subtract existing
listings, never force a unit when floor0. Keep the rest in inventory. This is
exposure control, not a claim of actual demand or physical auction stack size.
Use selected listing duration consistently for candidate cost and actual posts.
Do not alter crafting total-held capacity (inventory/listings/in_transit).

Optional repricing: inspect deterministic own listings only, trustworthy current
strictly-past fair/demand, age>=configured hours, at least1h before expiry, and
current target <= listing price*(1-reprice_gap) with strict price decrease.
Require replacement target clears vendor floor, replacement deposit affordable
and net after new deposit remains above vendor liquidation. Emit at most the
configured count ordered oldest then listingID. Do not cancel merely because a
new sweep arrived. Never model cancellation as free: execution remains existing
Cancel intent (lost remaining deposit); new posting pays deposit normally.
These are explicit experimental heuristics, not proven profitable decisions.

Do not emit a same-decision post that depends on a Cancel succeeding: defer
repricing canceled quantities until next sweep. Maintain existing rule that
newly crafted output cannot exit until next sweep. Existing holdings count even
when cancellation is emitted. Never mutate account views in strategy code.
Preserve capability gating and profession parity. Defaults must produce same
intents as before on representative cases.

Focused tests: horizon cap across active listings and multiple sweeps; zero cap;
invalid params; alternate durations both cost/posts; aged/undercut thresholds,
near-expiry/insufficientcash/untrusted/no-profitable-replacement refusals;
bounded deterministic cancels; no same-step cancel->post dependency; actual
engine Cancel accounting+repost deposit and shared time-budget behavior; current
craft deferred-exit behavior. Avoid redundant huge matrices/process fixtures.

## Verification

All pytest holds shared lock, pinnedCARGO:
flock /home/dev/.cache/r-pg.lock uv run pytest -n0 -q tests/test_trading_listing_policy.py tests/test_trading_strategies.py tests/test_trading_requirements.py tests/test_trading_engine.py
Use scoped Ruff check/format. Root independent check and full default<180s.
No DB reset, migrations, game/service/deployment, commits/pushes/resets/deletions.
DONE only implementation complete with changedfiles/checkoutputs/unresolvedissues.

## Parent portfolio amendment

Comparable beta baseline selects a provisional one-character paper portfolio,
not a live trade authorization. Additional exact ownership:
- src/crowley/trading/paper.py DEFAULT_STRATEGIES tuple ONLY
- tests/test_trading_paper.py focused default-selection tests ONLY

Set new-paper defaults in exact measured order to crafting_alchemy,
crafting_engineering,dip_reversion,vendor_arb, equal weights through existing
normalizer. Existing stored runs retain their original explicit strategies and
strict engine digest rules. Do not rewrite stored runs or touch DB. Explicit
historical/custom strategy lists remain available for research (no global
restriction on multi-character backtests). Verify actual default CLI paper-create
and direct create-run selection through mocked database boundary; prove two
primary professions and unchanged explicit override behavior. Add these tests to
focused command. Docs paper-default paragraph must match this provisional
portfolio and note empty capability defaults, beta/model/recipe/launch limits.
All listing-control defaults still stay exactly as before. Do not change live
paper service config or create a live run. Parent seals this source before
comparable policy replays; report optional controls are programmatic strategy
parameters, not falsely advertised persisted CLI paper parameters.

## Review correction: listing time versus step

Sol found existing internal Listing.posted_t stores a sweep index, while exposed
ListingView.posted_t and age-based strategies require seconds. Additional owned
production files:
- src/crowley/trading/accounts.py Listing fields/view ONLY
- src/crowley/trading/execution.py Post construction and fill eligibility/order ONLY
- src/crowley/trading/api.py ListingView timestamp documentation/types ONLY

Give Listing an explicit required posted_step for original interval eligibility
and priority. Store actual ExecutionContext.t in posted_t, and expose timestamp
seconds through ListingView, preserving fractional Context.t values consistently
for posted_t/expires_t. No inferred step/time
conversion or compatibility fallback. Keep settle_fills' strict original
posted_step<interval_start_step and step-based tie order unchanged. Update new
manual Listing fixtures with explicit posted_step. Preserve all accounting,
obtainability, same-interval exclusion and shared budget semantics.

Add nonzero epoch regression through actual execute_intent(Post)->Account view
->crafting repricer: below age threshold refuses, exact threshold admits if all
other conditions valid. Cover existing snipe age consumer via the same timestamp
view; do not alter its source/heuristic. Retain real engine same-interval/gappy
eligibility tests. Baseline replay must reproduce exact leading-pair outputs
after this correction (selected pair excludes snipe). No private data access.
