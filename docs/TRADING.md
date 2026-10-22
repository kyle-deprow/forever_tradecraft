# Concurrent trading backtester

The backtester replays one explicitly selected house's recorded commodity books at
global sweep times. Each registered strategy receives its own account, but all
accounts share the same observed market, obtainability budget, fill allocation and
human-speed time budget.

At a step, valid previous intervals allocate bottom-walk demand to active listings;
then expired listings and delayed mail are processed. Strategies see the current
book and strictly-past statistics. Buys are limited to units that survive into the
next sweep, and observed levels are reduced by prior purchases. Posts reserve the
single D1 deposit formula, fills pay after the M1 mail delay, and expiry returns
unsold items after M2 while losing the unsold deposit share. Cancels return items
immediately and lose the remaining deposit. Vendor transactions and fixed-yield
crafts are accounted for directly.

The assumptions are:

- B1: a commodity unit is obtainable only when its price group is present at the
  current and next sweep and the next interval is valid.
- D1: deposit is `ceil(sell_price × quantity × 0.15 × duration_hours / 12)`.
- D2: a sold listing receives its deposit refund pro rata by units sold.
- M1: sale proceeds and refunds arrive after 3,600 seconds.
- M2: expired unsold units arrive after 3,600 seconds.

The shared per-step budget is 450 seconds (half of the planned 900-second cadence).
Each click consumes one second; a craft also consumes C1's `CRAFT_SECONDS = 3`
seconds per crafted unit. A craft may be truncated to the units that fit and is
recorded as `craft_truncated`; an intent with no time left is rejected with
`time_budget`. Units in delayed return mail remain held for capacity purposes.
The CLI's `--wind-down-hours` option defaults to 24 hours; during the final
selected-window interval, buys, vendor buys, and crafts are rejected as
`wind_down`, while posts, cancels, and vendor sells remain available. Rejected
intents do not consume the time budget. Reports include realized and equity
values both at wind-down start and at the end.

The backtest CLI's `--demand-share` option defaults to 1 and must be in `(0, 1]`. It
scales the observed above-price demand available to this backtest's own
listings: at price `p`, fills are capped at
`floor(demand_share × D(p))` after earlier own fills in price order. The
selected share is recorded in report metadata.

Equity uses a liquidity-aware mark. For each strategy and item, up to
`floor(0.25 × demand_units_per_day × 2)` units (zero when demand is unknown) are
marked at `min(fair, purchase-net visible minimum) × (1 − AH_CUT)` when those
values are available. Units beyond that two-day capacity are marked at the item's
vendor sell price, or zero when no item facts exist. Cash and pending cash are the
realized component; the report exposes both `equity` and `realized`.

The report also records `max_held_over_capacity` per strategy, calculated over the
step-by-step held-unit observations (inventory, listings, and mail) against the
strategy's capacity share, plus the five highest-ratio items. Only items with an
auction-house snapshot at that step are included; vendor-only and unobserved
items are excluded. Deposits held are not included in equity. Reports contain
strategy attribution and totals, cash/pending
realized value, marked holdings, fees, counts, rejection reasons, drawdown, an
equity curve, gold/day, and FIFO closed-trade summaries.

Commodity prices must be integral copper. Vendor supplies carry explicit bundle size
and bundle price facts; vendor buys round up to complete bundles. The CLI derives the
full client build from the selected sweeps (`client_version.client_build`), rejects
mixed-build selections, and supports `--build` when a time window is not enough to
select one build. The report records sweeps excluded by the time window and build
filter, plus sweeps without any loaded commodity book separately.

Known biases follow the source analysis: interval resolution hides within-sweep
activity, bottom cancellations can resemble demand, bounded ceilings censor activity,
and seller-selected observations are not random. The next-sweep survival rule is a
deliberately conservative availability assumption rather than a claim about live
inventory.

## Beta backtest results (2026-10-22)

House `beta-normal-alliance`, client build 1.60.1.70450, 236 recorded sweeps (2026-10-17 to 2026-10-21,
about 4.4 days of wall time with large collection gaps), 20 g starting capital split equally, 24 h wind-down
(no new acquisitions in the final 24 h), liquidity-aware marks. "Realized" is profit already back in cash after
the wind-down; "equity" adds remaining stock at the liquidity-aware mark. `demand_share` is the fraction of the
observed buyer demand above our price that our listings may capture (assumption S1); it stands in for
competitors reacting to our listings and for error in the bottom-walk demand estimate.

Portfolio of the seven strategies that were profitable in the all-strategy runs (2.86 g each):

| demand_share | realized profit | final equity | max drawdown |
|---|---|---|---|
| 1.0 | +207.0 g | 348.1 g | 30 % |
| 0.5 | +64.6 g | 106.5 g | 56 % |
| 0.25 | +19.9 g | 50.0 g | 53 % |

Realized profit per strategy (2.86 g start each):

| strategy | share 1.0 | share 0.5 | share 0.25 |
|---|---|---|---|
| crafting_alchemy | +100.98 | +20.80 | +1.13 |
| crafting_engineering | +35.43 | +19.13 | +6.60 |
| crafting_leatherworking | +56.35 | +9.99 | +3.88 |
| crafting_blacksmithing | +8.92 | +9.87 | +5.05 |
| crafting_tailoring | +4.26 | +3.58 | +2.07 |
| dip_reversion | +0.58 | +0.74 | +0.64 |
| vendor_arb | +0.49 | +0.49 | +0.49 |

Excluded after the all-strategy runs: `snipe_flip` (lost ~1.75 g of 1.82 g in every run — forfeited deposits
and vendor dumps; listings still cheap a full sweep later are mostly ones nobody wants), `crafting_cooking`
(crafted 321, sold 1), `crafting_first_aid` (ends holding unsold stock), `crafting_enchanting` (no eligible
recipe trades).

Read these as relative evidence, not forecasts: the beta economy and its prices will not carry over to the
fresh launch economy; recipe availability on Forever is not known from client data; demand comes from the
bottom-walk estimator (only ~6 % of it is explained by cancel-and-repost churn, but it is unvalidated against
true sales); and the half-period runs are not comparable to the full run because each half carries its own
24 h wind-down within a gappy ~2-day window.

## Paper trading

Paper runs are deterministic shadow ledgers over the immutable recorded sweeps. Create one with
`python -m crowley.trading paper-create --name NAME --house HOUSE`; `--start now` begins with the next
recorded sweep. The default portfolio is the seven profitable strategies listed above. Set
`CROWLEY_DATABASE_URL` or pass `--database-url` on each command.

Advance a run with `paper-step --name NAME`. Each invocation replays from the fixed start time, verifies all
previously stored final equity and decision records, and writes only new final steps in one transaction. The newest
step remains provisional until a later sweep arrives; `paper-status` labels its decision intents as pending because
their next-sweep outcome is not final. It refuses a changed
trading/analysis source digest or a client build change after the run start. Inspect the latest per-strategy equity,
realized copper, and decisions with `paper-status --name NAME`.

Paper runs default to `demand_share=0.5`; pass `--demand-share` to choose another value in `(0, 1]`.

Each `paper-step` replays the whole run. On the parent’s machine, 174 steps for seven strategies took about 220
seconds; replay cost is roughly linear in the number of 15-minute sweeps and exceeds the 15-minute cadence after
roughly a week of continuous sweeps. A new paper run, or a future checkpointing feature, is the remedy. A step that
takes more than 600 seconds prints a warning.

The supplied `deploy/crowley-paper-trading.service` and `.timer` run this step every fifteen minutes. They are
not installed automatically.
