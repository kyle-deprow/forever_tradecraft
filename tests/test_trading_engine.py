from __future__ import annotations

import time
from fractions import Fraction

import pytest

from crowley.analysis.books import Book, Group
from crowley.analysis.metrics import compute_metrics
from crowley.trading.accounts import Account
from crowley.trading.api import (
    Buy,
    Cancel,
    Craft,
    ItemFacts,
    Post,
    Recipe,
    VendorBuy,
)
from crowley.trading.data import precompute_statistics, validate_recipes
from crowley.trading.engine import run_backtest
from crowley.trading.execution import (
    CLICK_BUDGET,
    ExecutionContext,
    _consume_lots,
    deposit,
    execute_intent,
    obtainable_units,
)
from crowley.trading.market import Market
from crowley.trading.report import build_report
from crowley.trading.strategies.vendor_arb import VendorArbStrategy

ITEM = 7


def book(
    t: int,
    groups: list[tuple[str, int, int]],
    *,
    item_id: int = ITEM,
    sweep_id: int | str | None = None,
    ceiling: int | None = None,
    time_left: int = 100_000,
) -> Book:
    return Book(
        t=t,
        groups=[
            Group(result_id, Fraction(price), quantity, time_left) for result_id, price, quantity in groups
        ],
        ceiling=None if ceiling is None else Fraction(ceiling),
        item_id=item_id,
        sweep_id=sweep_id,
    )


def facts(
    *,
    sell: int = 0,
    bundle_size: int | None = None,
    bundle_price: int | None = None,
    stack: int = 20,
    item_id: int = ITEM,
) -> dict[int, ItemFacts]:
    return {item_id: ItemFacts(item_id, sell, bundle_size, bundle_price, stack, 0)}


class Script:
    def __init__(
        self,
        name: str,
        actions: dict[int, list[object]] | None = None,
        professions: frozenset[str] = frozenset(),
    ):
        self.name = name
        self.professions = professions
        self.actions = actions or {}
        self.views: list[tuple[int, int, dict[int, object]]] = []

    def decide(self, market, account):
        self.views.append((market.t, market.sweep_index, dict(market.items())))
        return self.actions.get(market.sweep_index, ())


def run(books, strategies, facts_value=None, recipes=(), capital=10_000, statistics=None):
    return run_backtest(
        books,
        {} if statistics is None else statistics,
        facts_value or facts(),
        recipes,
        strategies,
        None,
        capital,
    )


def two_sweeps(groups, *, item_id=ITEM, t0=0, t1=900, ceiling=None):
    return {
        item_id: [
            book(t0, groups, item_id=item_id, sweep_id=1, ceiling=ceiling),
            book(t1, groups, item_id=item_id, sweep_id=2, ceiling=ceiling),
        ]
    }


def test_obtainability_survives_next_sweep_and_respects_purchase_net_and_ceiling():
    books = {
        ITEM: [
            book(0, [("cheap", 10, 5), ("high", 20, 3)], sweep_id=1, ceiling=15),
            book(900, [("cheap", 10, 2), ("high", 20, 3)], sweep_id=2, ceiling=15),
        ]
    }
    market = Market(books, {}, facts(), ())
    purchased = {(ITEM, "cheap"): 1}
    market.set_step(0, 0, purchased)
    context = ExecutionContext(market, [], 0, 0, purchased)
    assert [(group.result_id, quantity) for group, quantity in obtainable_units(context, ITEM)] == [
        ("cheap", 1)
    ]

    gap_books = {
        ITEM: [
            book(0, [("cheap", 10, 5)], sweep_id=1),
            book(2_000, [("cheap", 10, 5)], sweep_id=2),
        ]
    }
    gap_market = Market(gap_books, {}, facts(), ())
    gap_market.set_step(0, 0, {})
    assert obtainable_units(ExecutionContext(gap_market, [], 0, 0, {}), ITEM) == []


def test_buy_is_cash_limited_and_levels_are_purchase_net():
    books = two_sweeps([("a", 30, 5)])
    buyer = Script("buyer", {0: [Buy(ITEM, 30, 5), Buy(ITEM, 30, 5)]})
    result = run(books, [buyer], capital=100)
    account = result.accounts["buyer"]
    assert account.counts["units_bought"] == 3
    assert account.cash_balance == 10
    assert account.rejections["cash"] == 1

    second = Script("second", {0: [Buy(ITEM, 30, 5)]})
    result = run(books, [Script("first", {0: [Buy(ITEM, 30, 2)]}), second], capital=200)
    assert second.views[0][2][ITEM].levels[0].quantity == 3


def test_fill_allocation_uses_demand_above_price_and_tie_order():
    books = {
        ITEM: [
            book(0, [("a", 50, 3), ("b", 80, 2)], sweep_id=1),
            book(900, [("a", 50, 3), ("b", 80, 2)], sweep_id=2),
            book(1_800, [], sweep_id=3),
            book(2_700, [], sweep_id=4),
        ]
    }
    # Both listings are posted at step 0; step 1 is intentionally quiet.  The
    # step-2 interval starts at sweep 1 and is therefore the first eligible one.
    first = Script("first", {0: [VendorBuy(ITEM, 4), Post(ITEM, 40, 4, 12)]})
    second = Script("second", {0: [VendorBuy(ITEM, 3), Post(ITEM, 60, 3, 12)]})
    result = run(
        books,
        [first, second],
        facts_value=facts(sell=100, bundle_size=1, bundle_price=1, stack=1),
        capital=2_000,
    )
    assert result.accounts["first"].counts["units_sold"] == 4
    assert result.accounts["second"].counts.get("units_sold", 0) == 0

    tie_books = {
        ITEM: [
            book(0, [("a", 80, 1)], sweep_id=1),
            book(900, [("a", 80, 1)], sweep_id=2),
            book(1_800, [], sweep_id=3),
        ]
    }
    a = Script("a", {0: [VendorBuy(ITEM, 1), Post(ITEM, 50, 1, 12)]})
    b = Script("b", {0: [VendorBuy(ITEM, 1), Post(ITEM, 50, 1, 12)]})
    result = run(
        tie_books,
        [a, b],
        facts_value=facts(sell=100, bundle_size=1, bundle_price=1, stack=1),
        capital=2_000,
    )
    assert result.accounts["a"].counts["units_sold"] == 1
    assert result.accounts["b"].counts.get("units_sold", 0) == 0


def test_invalid_intervals_and_post_eligibility_are_conservative():
    invalid = {
        ITEM: [
            book(0, [("a", 50, 1)], sweep_id=1),
            book(2_000, [], sweep_id=2),
        ]
    }
    seller = Script("seller", {0: [VendorBuy(ITEM, 1), Post(ITEM, 40, 1, 12)]})
    result = run(
        invalid,
        [seller],
        facts_value=facts(sell=100, bundle_size=1, bundle_price=1, stack=1),
        capital=1_000,
    )
    assert result.accounts["seller"].counts.get("units_sold", 0) == 0

    # The first interval starts in the posting sweep and cannot fill a listing
    # posted there; the second interval starts later and can.
    eligible = {
        ITEM: [
            book(0, [("a", 50, 1)], sweep_id=1),
            book(900, [("a", 50, 1)], sweep_id=2),
            book(1_800, [], sweep_id=3),
        ]
    }
    seller = Script("seller", {0: [VendorBuy(ITEM, 1), Post(ITEM, 40, 1, 12)]})
    result = run(
        eligible,
        [seller],
        facts_value=facts(sell=100, bundle_size=1, bundle_price=1, stack=1),
        capital=1_000,
    )
    assert result.accounts["seller"].counts["units_sold"] == 1


def test_mail_delay_expiry_and_cancel_deposit_accounting():
    assert deposit(100, 3, 12) == 45
    books = {
        ITEM: [
            book(0, [("a", 10, 1)], sweep_id=1),
            book(43_200, [("a", 10, 1)], sweep_id=2),
            book(46_800, [("a", 10, 1)], sweep_id=3),
        ]
    }
    strategy = Script("seller", {0: [VendorBuy(ITEM, 1), Post(ITEM, 20, 1, 12)]})
    result = run(
        books,
        [strategy],
        facts_value=facts(sell=100, bundle_size=1, bundle_price=1, stack=1),
        capital=1_000,
    )
    account = result.accounts["seller"]
    assert account.counts["expiries"] == 1
    assert account.inventory_balance[ITEM] == 1
    assert account.fees["deposits_lost"] == 15

    cancel_strategy = Script("canceller", {0: [VendorBuy(ITEM, 1), Post(ITEM, 20, 1, 12)]})
    cancel_result = run(
        two_sweeps([("a", 10, 1)]),
        [cancel_strategy],
        facts_value=facts(sell=100, bundle_size=1, bundle_price=1, stack=1),
        capital=1_000,
    )
    cancel_account = cancel_result.accounts["canceller"]
    listing_id = next(iter(cancel_account.listings_by_id))
    market = Market(two_sweeps([("a", 10, 1)]), {}, facts(sell=100), ())
    market.set_step(0, 0, {})
    context = ExecutionContext(market, [cancel_account], 0, 0, {}, next_listing_id=listing_id + 1)
    assert execute_intent(context, cancel_account, Cancel(listing_id))
    assert cancel_account.inventory_balance[ITEM] == 1
    assert cancel_account.fees["deposits_lost"] == 15


def test_multi_interval_deposit_refunds_use_cumulative_sold_quantity():
    books = {
        ITEM: [
            book(0, [("a", 50, 3)], sweep_id=1),
            book(900, [("a", 50, 3)], sweep_id=2),
            book(1_800, [("a", 50, 2)], sweep_id=3),
            book(2_700, [("a", 50, 1)], sweep_id=4),
            book(3_600, [], sweep_id=5),
        ]
    }
    strategy = Script("seller", {0: [VendorBuy(ITEM, 3), Post(ITEM, 40, 3, 12)]})
    result = run(
        books,
        [strategy],
        facts_value=facts(sell=100, bundle_size=3, bundle_price=3, stack=3),
        capital=1_000,
    )
    account = result.accounts["seller"]
    assert account.counts["units_sold"] == 3
    assert account.fees["deposits_refunded"] == 45
    assert account.fees.get("deposits_lost", 0) == 0
    assert account.pending_cash() == 3 * (40 * 95 // 100) + 45


def test_vendor_bundle_rounds_up_and_vendor_arb_sells_one_step_later():
    books = two_sweeps([("a", 50, 3)])
    fact = facts(sell=100, bundle_size=3, bundle_price=7, stack=20)
    buyer = Script("buyer", {0: [VendorBuy(ITEM, 1)]})
    result = run(books, [buyer], facts_value=fact, capital=100)
    account = result.accounts["buyer"]
    assert account.inventory_balance[ITEM] == 3
    assert account.cash_balance == 93

    result = run_backtest(books, {}, facts(sell=100), (), [VendorArbStrategy()], None, 1_000)
    account = result.accounts["vendor_arb"]
    assert account.cash_balance == 1_150
    assert account.counts["units_bought"] == 3
    assert account.counts["units_vendored"] == 3


def test_craft_profession_reagent_and_shared_cooldown_expiry():
    reagent, output = 8, 9
    recipes = (Recipe(22, frozenset({"alchemy"}), ((reagent, 2),), ((output, 1),), "daily", 3, "x"),)
    a = Script("a", {0: [VendorBuy(reagent, 4), Craft(22, 1)], 1: [Craft(22, 1)]}, frozenset({"alchemy"}))
    b = Script("b", {0: [VendorBuy(reagent, 2), Craft(22, 1)]}, frozenset({"alchemy"}))
    recipe_facts = {
        ITEM: ItemFacts(ITEM, 0, None, None, 5, 0),
        reagent: ItemFacts(reagent, 0, 2, 1, 2, 0),
        output: ItemFacts(output, 0, None, None, 5, 0),
    }
    books = {
        ITEM: [
            book(0, [("a", 10, 1)], sweep_id=1),
            book(900, [("a", 10, 1)], sweep_id=2),
            book(3_600, [("a", 10, 1)], sweep_id=3),
        ]
    }
    result = run(books, [a, b], facts_value=recipe_facts, recipes=recipes, capital=100)
    assert result.accounts["a"].counts["crafted"] == 2
    assert result.accounts["b"].rejections["cooldown"] == 1

    bad = Recipe(23, frozenset(), ((reagent, -1), (reagent, 1)), ((output, 0),), None, 0, "x")
    with pytest.raises(ValueError):
        validate_recipes((bad,))
    normalized = validate_recipes(
        (Recipe(24, frozenset(), ((reagent, 1), (reagent, 2)), ((output, 1), (output, 1)), None, 0, "x"),)
    )[0]
    assert normalized.reagents == ((reagent, 3),)
    assert normalized.outputs == ((output, 2),)


def test_click_budget_rotation_and_one_step_per_recorded_sweep():
    books = {
        ITEM: [book(100, [("a", 10, 1)], sweep_id=1)],
        8: [book(200, [("a", 10, 1)], item_id=8, sweep_id=1)],
    }
    first = Script("first", {0: [VendorBuy(ITEM, 1)] * (CLICK_BUDGET // 2 + 1)})
    second = Script("second")
    result = run(
        books,
        [first, second],
        facts_value={
            ITEM: ItemFacts(ITEM, 0, 1, 1, 20, 0),
            8: ItemFacts(8, 0, None, None, 20, 0),
        },
        capital=1_000,
    )
    assert result.times == (200,)
    assert len(first.views) == len(second.views) == 1
    assert first.views[0][2].keys() == {ITEM, 8}
    assert first.views[0][0] == 200
    assert first.views[0][1] == 0
    assert first.views[0][2][ITEM].t == 100
    assert first.views[0][2][8].t == 200

    class Ordering(Script):
        def decide(self, market, account):
            self.views.append((market.t, market.sweep_index, dict(market.items())))
            return ()

    a, b = Ordering("a"), Ordering("b")
    books = {ITEM: [book(0, [("a", 1, 1)], sweep_id=1), book(900, [("a", 1, 1)], sweep_id=2)]}
    run(books, [a, b], facts_value=facts(), capital=100)
    assert [entry[0] for entry in a.views] == [0, 900]
    assert [entry[0] for entry in b.views] == [0, 900]


def test_marks_equity_attribution_and_no_lookahead():
    books = {ITEM: [book(index * 900, [("a", 10, 20)], sweep_id=index) for index in range(10)]}
    observer = Script("observer")
    result = run(books, [observer], facts_value=facts(sell=0), capital=100)
    assert observer.views[0][2][ITEM].fair_n == 0
    assert observer.views[8][2][ITEM].fair_n == 8
    assert observer.views[8][2][ITEM].fair == 10

    buyer = Script("buyer", {0: [Buy(ITEM, 10, 1)]})
    idle = Script("idle")
    result = run(two_sweeps([("a", 10, 1)]), [buyer, idle], facts_value=facts(), capital=200)
    assert result.accounts["buyer"].cash_balance == 90
    assert result.accounts["idle"].cash_balance == 100
    assert result.total_equity_curve[0][1] == Fraction(399, 2)


def test_fractional_prices_and_summary_statistics_fail_loudly():
    fractional = {ITEM: [book(0, [("a", 10, 1)], sweep_id=1), book(900, [("a", 10, 1)], sweep_id=2)]}
    fractional[ITEM][0].groups[0] = Group("a", Fraction(21, 2), 1, 100_000)
    with pytest.raises(ValueError, match="not integral"):
        Market(fractional, {}, facts(), ())

    summary = compute_metrics(two_sweeps([("a", 10, 1)]))
    with pytest.raises(ValueError, match="indexed"):
        run_backtest(two_sweeps([("a", 10, 1)]), summary, facts(), (), [Script("x")], None, 100)


def test_fifo_profit_uses_exact_cost_and_net_proceeds():
    account = Account("x", frozenset(), 0, 0)
    account.add_inventory(ITEM, 2, unit_cost=Fraction(1, 1))
    account.add_inventory(ITEM, 1, unit_cost=Fraction(2, 1))
    _consume_lots(account, ITEM, 3, 5, 0, "auction")
    assert sum(trade["profit"] for trade in account.closed_trades) == 1
    assert sum(trade["proceeds"] for trade in account.closed_trades) == 5


def test_report_contains_required_fields_and_full_size_statistics_gate():
    result = run(two_sweeps([("a", 10, 1)]), [Script("observer")], facts_value=facts(), capital=100)
    strategy_report = build_report(result)["strategies"]["observer"]
    for key in (
        "start_capital",
        "final_equity",
        "realized",
        "unrealized",
        "fees",
        "counts",
        "clicks",
        "max_drawdown",
        "equity_curve",
        "gold_per_day",
        "top_closed_trades",
    ):
        assert key in strategy_report

    full = {
        item_id: [book(index * 900, [("a", 10, 20)], item_id=item_id, sweep_id=index) for index in range(240)]
        for item_id in range(330)
    }
    started = time.monotonic()
    statistics = precompute_statistics(full)
    assert len(statistics) == 330
    assert time.monotonic() - started < 10
