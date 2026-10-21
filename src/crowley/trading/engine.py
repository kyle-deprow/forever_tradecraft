"""The concurrent, one-market backtest loop."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from crowley.analysis.books import Book

from .accounts import Account
from .api import ItemFacts, Recipe, Strategy
from .data import validate_recipes
from .execution import ExecutionContext, release_mail, settle_expiry, settle_fills
from .market import Market


def _as_fraction(value: Any) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(str(value))


def _allocate_capital(capital: int, weights: Sequence[Any]) -> list[int]:
    if not weights or any(_as_fraction(weight) <= 0 for weight in weights):
        raise ValueError("weights must be positive")
    fractions = [_as_fraction(weight) for weight in weights]
    total = sum(fractions, Fraction(0))
    shares = [int(Fraction(capital) * weight / total) for weight in fractions]
    remainder = capital - sum(shares)
    for index in range(remainder):
        shares[index % len(shares)] += 1
    return shares


@dataclass
class BacktestResult:
    start_capital: int
    accounts: dict[str, Account]
    equity_curves: dict[str, list[tuple[float, Fraction]]] = field(default_factory=dict)
    total_equity_curve: list[tuple[float, Fraction]] = field(default_factory=list)
    times: tuple[float, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def strategies(self) -> dict[str, Account]:
        return self.accounts

    @property
    def total(self) -> list[tuple[float, Fraction]]:
        return self.total_equity_curve

    def report(self) -> dict[str, Any]:
        from .report import build_report

        return build_report(self)

    def summary(self) -> str:
        from .report import text_summary

        return text_summary(self.report())


def _mark_equity(account: Account, market: Market, t: float, sweep_index: int) -> Fraction:
    # Marks use the observed market, not the strategy-facing book after the
    # backtest's purchases have been netted out.  Otherwise buying the last
    # visible unit would erase the price used to value that same unit.
    purchased = market._purchased
    market.set_step(t, sweep_index, {})
    snapshots = market.view().items()
    market.set_step(t, sweep_index, purchased)
    holdings: dict[int, int] = {}
    for item_id, quantity in account.inventory_balance.items():
        holdings[item_id] = holdings.get(item_id, 0) + quantity
    for item_id, quantity in account.listed_units().items():
        holdings[item_id] = holdings.get(item_id, 0) + quantity
    for parcel in account.mail:
        for item_id, quantity in parcel.items.items():
            holdings[item_id] = holdings.get(item_id, 0) + quantity
    equity = Fraction(account.cash_balance + account.pending_cash())
    for item_id, quantity in holdings.items():
        snapshot = snapshots.get(item_id)
        if snapshot is None:
            continue
        if snapshot.fair is not None and snapshot.visible_min is not None:
            mark = min(snapshot.fair, Fraction(snapshot.visible_min))
        elif snapshot.visible_min is not None:
            mark = Fraction(snapshot.visible_min)
        else:
            mark = Fraction(0)
        equity += quantity * mark * (1 - Fraction(5, 100))
    return equity


def run_backtest(
    books: Mapping[int, Sequence[Book]] | Sequence[Book],
    statistics: Mapping[Any, Any] | None,
    facts: Mapping[int, ItemFacts],
    recipes: Sequence[Recipe],
    strategies: Sequence[Strategy] | Mapping[str, Strategy],
    weights: Sequence[Any] | Mapping[str, Any] | None,
    capital_copper: int = 200_000,
    start_t: float | None = None,
    end_t: float | None = None,
) -> BacktestResult:
    """Run all strategies through one shared sequence of recorded sweeps."""

    if isinstance(strategies, Mapping):
        strategy_list = list(strategies.values())
    else:
        strategy_list = list(strategies)
    if not strategy_list:
        raise ValueError("at least one strategy is required")
    names = [strategy.name for strategy in strategy_list]
    if len(set(names)) != len(names):
        raise ValueError("strategy names must be unique")
    if capital_copper < 0:
        raise ValueError("capital_copper cannot be negative")
    recipes = validate_recipes(recipes)
    from .data import precompute_statistics

    indexed_statistics = precompute_statistics(books) if not statistics else statistics
    market = Market(books, indexed_statistics, facts, recipes)
    all_times = market.times
    steps = tuple(
        (step, t)
        for step, t in enumerate(all_times)
        if (start_t is None or t >= start_t) and (end_t is None or t <= end_t)
    )
    if weights is None:
        weight_values = [Fraction(1) for _ in strategy_list]
    elif isinstance(weights, Mapping):
        missing = [name for name in names if name not in weights]
        if missing:
            raise ValueError(f"missing strategy weights: {missing}")
        weight_values = [weights[name] for name in names]
    else:
        weight_values = list(weights)
        if len(weight_values) != len(strategy_list):
            raise ValueError("weights must have one value per strategy")
    capital_shares = _allocate_capital(capital_copper, weight_values)
    shared_cooldowns: dict[str, float] = {}
    accounts = {
        name: Account(name, frozenset(strategy.professions), share, share, cooldowns=shared_cooldowns)
        for name, strategy, share in zip(names, strategy_list, capital_shares, strict=True)
    }
    if not steps:
        return BacktestResult(
            capital_copper,
            accounts,
            {name: [] for name in names},
            [],
            (),
        )
    ordered_accounts = [accounts[name] for name in names]
    purchased: dict[tuple[int, Any], int] = {}
    curves = {name: [] for name in names}
    total_curve: list[tuple[float, Fraction]] = []
    next_listing_id = 1

    for step, t in steps:
        market.set_step(t, step, purchased)
        context = ExecutionContext(
            market, ordered_accounts, t, step, purchased, next_listing_id=next_listing_id
        )
        settle_fills(context)
        settle_expiry(context)
        release_mail(context)
        order = list(range(len(strategy_list)))
        rotation = step % len(order)
        order = order[rotation:] + order[:rotation]
        for strategy_index in order:
            strategy = strategy_list[strategy_index]
            account = ordered_accounts[strategy_index]
            market.set_step(t, step, purchased)
            intents = strategy.decide(market.view(), account.account_view(t))
            if intents is None:
                continue
            for intent in intents:
                from .execution import execute_intent

                execute_intent(context, account, intent)
                next_listing_id = context.next_listing_id
                market.set_step(t, step, purchased)
        for name, account in accounts.items():
            curves[name].append((t, _mark_equity(account, market, t, step)))
        total_curve.append((t, sum((curves[name][-1][1] for name in names), Fraction(0))))

    return BacktestResult(capital_copper, accounts, curves, total_curve, tuple(t for _, t in steps))


__all__ = ["BacktestResult", "run_backtest"]
