# Commodity time-to-sale analysis

The offline analysis uses only corrected format-2 commodity observations from
one explicitly selected house. It groups each observation by persistent
`result_id` price level, keeps exact rational unit prices, and compares
consecutive observations only when their start times are strictly increasing
and at most 1,260 seconds apart.

For each valid interval, the bottom walk examines retained groups from the
cheapest price upward. A depletion is counted as observed consumption only
when the walk reaches it; an expiry is skipped. Bounded observations use the
common ceiling of the two books. A hypothetical listing receives all observed
consumption above its price, and a configurable share of consumption at the
same price (`--tie-share`, default zero). A listing is censored when the chain
breaks, the book ceiling makes its price unobservable, the data ends, or the
24-hour horizon is reached.

The rule table evaluates an undercut price and reference prices at 0.8, 0.9,
1.0, 1.1, 1.25, and 1.5 times the 20th-cheapest unit. Quantities are 1, 20,
and 200. Kaplan–Meier estimates report the probability of a complete sale by
2, 6, 12, and 24 hours, together with starts, events, censoring, median sale
time, and the mean observed filled fraction at 24 hours.

Validation splits at the supplied epoch or at the median valid-interval start
time. Training replays stop at the split, so a training interval cannot use
test-period demand. Test examples are real price-level groups first seen in a
valid interval. They are bucketed by relative price and log-nearest quantity;
the report includes model and item-level-baseline Brier scores, equal-count
calibration bins, and per-bucket counts, using a quantity-conditioned
item-level baseline. It reports two outcome conventions:
`cancellation_censored` keeps `cancellation_or_expiry` as right-censoring,
while `cancellation_unsold` counts a cancellation before the horizon as an
observed not-sold outcome; other censor reasons remain unknown in both. The
second convention is useful as a sensitivity analysis, but cancellations are
seller-selected rather than random—unsold listings are more likely to be
cancelled—so treating them as unsold changes the estimand and does not remove
selection bias. Each scoring marks single-class results as not informative.

Run it with:

```sh
uv run python -m crowley.analysis \
  --database-url 'postgresql://user:password@db.example/crowley' \
  --house beta-normal-alliance \
  --out analysis.json
```

`003_item_unit_price_and_time_left.sql` must be recorded in
`schema_migrations`. The loader refuses older databases and refuses commodity
exact time-left values above 172800 seconds. The loader performs one read-only
transaction and never writes to the database.

Known biases are intentional: purchases of listings posted and bought between
sweeps are invisible and therefore understate demand; bottom cancellations can
look like purchases and overstate demand; the counterfactual assumes the new
listing does not change other sellers' behaviour; and interval-resolution event
times are upper bounds.
