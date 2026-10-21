# Concurrent trading backtester

The backtester replays one explicitly selected house's recorded commodity books at
global sweep times. Each registered strategy receives its own account, but all
accounts share the same observed market, obtainability budget, fill allocation and
human-speed click budget.

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

The 450-click step budget is shared by every strategy. Marks use the lesser of fair
value and visible minimum when both exist, after the auction-house cut; deposits
held are not included in equity. Reports contain strategy attribution and totals,
cash/pending realized value, marked holdings, fees, counts, rejection reasons,
drawdown, an equity curve, gold/day, and FIFO closed-trade summaries.

Commodity prices must be integral copper. Vendor supplies carry explicit bundle size
and bundle price facts; vendor buys round up to complete bundles. The CLI derives the
full client build from the selected sweeps (`client_version.client_build`), rejects
mixed-build selections, and supports `--build` when a time window is not enough to
select one build. The report records sweeps excluded by the time window and build
filter.

Known biases follow the source analysis: interval resolution hides within-sweep
activity, bottom cancellations can resemble demand, bounded ceilings censor activity,
and seller-selected observations are not random. The next-sweep survival rule is a
deliberately conservative availability assumption rather than a claim about live
inventory.
