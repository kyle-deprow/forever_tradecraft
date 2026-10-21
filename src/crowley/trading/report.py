"""Per-strategy and aggregate backtest reports."""

from __future__ import annotations

import json
from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import Any

from .accounts import Account
from .engine import BacktestResult

COUNT_KEYS = (
    "units_bought",
    "units_sold",
    "units_vendored",
    "units_vendor_bought",
    "crafted",
    "crafts",
    "posts",
    "cancels",
    "expiries",
)
FEE_KEYS = ("ah_cut", "deposits_lost", "deposits_paid", "deposits_refunded")


def _value(value: Any) -> Any:
    if isinstance(value, Fraction):
        return value.numerator if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    if isinstance(value, Mapping):
        return {str(key): _value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_value(item) for item in value]
    return value


def _drawdown(
    curve: list[tuple[float, Fraction]], initial: Fraction = Fraction(0)
) -> tuple[Fraction, Fraction]:
    peak = initial
    largest = Fraction(0)
    largest_pct = Fraction(0)
    for _, equity in curve:
        if equity > peak:
            peak = equity
        if peak:
            drawdown = peak - equity
            if drawdown > largest:
                largest = drawdown
                largest_pct = drawdown / peak * 100
    return largest, largest_pct


def _trade_list(account: Account) -> list[dict[str, Any]]:
    return sorted(account.closed_trades, key=lambda trade: (trade["profit"], trade["t"]), reverse=True)[:10]


def _strategy_report(
    name: str, account: Account, curve: list[tuple[float, Fraction]], covered_days: Fraction
) -> dict[str, Any]:
    final_equity = curve[-1][1] if curve else Fraction(account.cash_balance + account.pending_cash())
    cash_and_pending = account.cash_balance + account.pending_cash()
    unrealized = final_equity - cash_and_pending
    realized = cash_and_pending - account.start_capital
    drawdown, drawdown_pct = _drawdown(curve, Fraction(account.start_capital))
    net_per_day = (final_equity - account.start_capital) / covered_days if covered_days else None
    counts = {key: account.counts.get(key, 0) for key in COUNT_KEYS}
    fees = {key: account.fees.get(key, 0) for key in FEE_KEYS}
    return {
        "name": name,
        "start_capital": account.start_capital,
        "final_equity": final_equity,
        "return_pct": None
        if account.start_capital == 0
        else (final_equity / account.start_capital - 1) * 100,
        "realized": realized,
        "unrealized": unrealized,
        "fees": fees,
        "counts": counts,
        "rejections": dict(sorted(account.rejections.items())),
        "clicks": account.clicks,
        "max_drawdown": drawdown,
        "max_drawdown_pct": drawdown_pct,
        "equity_curve": [{"t": t, "equity": equity} for t, equity in curve],
        "gold_per_day": None if net_per_day is None else net_per_day / 10_000,
        "top_closed_trades": _trade_list(account),
    }


def _sum_reports(
    reports: list[dict[str, Any]], curve: list[tuple[float, Fraction]], start: int
) -> dict[str, Any]:
    final_equity = curve[-1][1] if curve else Fraction(start)
    realized = sum((report["realized"] for report in reports), Fraction(0))
    unrealized = sum((report["unrealized"] for report in reports), Fraction(0))
    counts = {key: sum(report["counts"].get(key, 0) for report in reports) for key in COUNT_KEYS}
    fees = {key: sum(report["fees"].get(key, 0) for report in reports) for key in FEE_KEYS}
    rejections: dict[str, int] = {}
    for report in reports:
        for reason, count in report["rejections"].items():
            rejections[reason] = rejections.get(reason, 0) + count
    drawdown, drawdown_pct = _drawdown(curve, Fraction(start))
    covered_days = Fraction(curve[-1][0] - curve[0][0], 86400) if len(curve) > 1 else Fraction(0)
    return {
        "name": "total",
        "start_capital": start,
        "final_equity": final_equity,
        "return_pct": None if start == 0 else (final_equity / start - 1) * 100,
        "realized": realized,
        "unrealized": unrealized,
        "fees": fees,
        "counts": counts,
        "rejections": dict(sorted(rejections.items())),
        "clicks": sum(report["clicks"] for report in reports),
        "max_drawdown": drawdown,
        "max_drawdown_pct": drawdown_pct,
        "equity_curve": [{"t": t, "equity": equity} for t, equity in curve],
        "gold_per_day": None if not covered_days else (final_equity - start) / covered_days / 10_000,
        "top_closed_trades": sorted(
            (trade for report in reports for trade in report["top_closed_trades"]),
            key=lambda trade: trade["profit"],
            reverse=True,
        )[:10],
    }


def build_report(result: BacktestResult) -> dict[str, Any]:
    covered_days = (
        Fraction(result.times[-1] - result.times[0], 86400) if len(result.times) > 1 else Fraction(0)
    )
    strategies = [
        _strategy_report(name, account, result.equity_curves.get(name, []), covered_days)
        for name, account in result.accounts.items()
    ]
    return {
        "start_capital": result.start_capital,
        "covered_days": covered_days,
        "metadata": result.metadata,
        "strategies": {report["name"]: report for report in strategies},
        "total": _sum_reports(strategies, result.total_equity_curve, result.start_capital),
    }


def json_report(result: BacktestResult) -> str:
    return json.dumps(_value(build_report(result)), indent=2, sort_keys=True) + "\n"


def write_report(result: BacktestResult, path: str | Path) -> None:
    Path(path).write_text(json_report(result), encoding="utf-8")


def text_summary(report: Mapping[str, Any]) -> str:
    total = report["total"]
    return (
        f"total: start={_value(total['start_capital'])} copper, "
        f"final={_value(total['final_equity'])} copper, "
        f"return={_value(total['return_pct'])}%, clicks={total['clicks']}"
    )


__all__ = ["build_report", "json_report", "text_summary", "write_report"]
