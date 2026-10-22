"""Command line entry point for the trading backtester."""

from __future__ import annotations

import argparse
from contextlib import nullcontext
from decimal import Decimal
from fractions import Fraction

import psycopg

from .data import load_client_data, load_commodity_books, precompute_statistics
from .engine import run_backtest
from .report import text_summary, write_report
from .strategies import build


class _ReadOnlyLoaderConnection:
    """Let the analysis loader reuse the caller's already-open read-only block."""

    def __init__(self, connection):
        self._connection = connection

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def transaction(self):
        return nullcontext(self._connection)


def _weights(value: str | None) -> list[Fraction] | None:
    if value is None:
        return None
    parts = [part.strip() for part in value.split(",")]
    if not parts or any(not part for part in parts):
        raise ValueError("--weights must be a comma-separated list")
    return [Fraction(part) for part in parts]


def _row_value(row, key: str, index: int):
    return row[key] if hasattr(row, "keys") else row[index]


def _sweep_step_times(books) -> dict[int, int]:
    times: dict[int, int] = {}
    for item_books in books.values():
        for book in item_books:
            if book.sweep_id is None:
                continue
            if book.t != int(book.t):
                raise ValueError(f"book time must be whole seconds, got {book.t!r}")
            sweep_id = int(book.sweep_id)
            times[sweep_id] = max(times.get(sweep_id, int(book.t)), int(book.t))
    return times


def _select_sweeps(
    conn,
    house: str,
    start: float | None,
    end: float | None,
    build: str | None,
    books=None,
):
    rows = conn.execute(
        """
        SELECT ms.id, ms.started_at, ms.client_version, ms.client_build
        FROM market_sweeps AS ms
        JOIN houses AS h ON h.id = ms.house_id
        WHERE h.key = %s
        ORDER BY ms.started_at, ms.id
        """,
        (house,),
    ).fetchall()
    if not rows:
        raise RuntimeError(f"no market sweeps found for house {house!r}")
    step_times = _sweep_step_times(books) if books is not None else {}
    represented_rows = [row for row in rows if books is None or int(_row_value(row, "id", 0)) in step_times]
    excluded_without_books = len(rows) - len(represented_rows)
    window_rows = []
    for row in represented_rows:
        sweep_id = int(_row_value(row, "id", 0))
        if books is not None:
            timestamp = step_times[sweep_id]
        else:
            started_at = _row_value(row, "started_at", 1)
            timestamp = started_at.timestamp() if hasattr(started_at, "timestamp") else float(started_at)
        if (start is None or timestamp >= start) and (end is None or timestamp <= end):
            window_rows.append(row)
    selected = []
    for row in window_rows:
        full_build = f"{_row_value(row, 'client_version', 2)}.{_row_value(row, 'client_build', 3)}"
        if build is None or full_build == build:
            selected.append(row)
    if not selected:
        qualifier = f" and build {build!r}" if build else ""
        raise RuntimeError(f"no market sweeps match house {house!r}{qualifier}")
    builds = {
        f"{_row_value(row, 'client_version', 2)}.{_row_value(row, 'client_build', 3)}" for row in selected
    }
    if len(builds) != 1:
        joined = ", ".join(sorted(builds))
        raise RuntimeError(
            f"selected sweeps contain multiple client builds ({joined}); "
            "restrict --start/--end or use --build"
        )
    return rows, window_rows, selected, next(iter(builds)), excluded_without_books


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backtest concurrent auction-house strategies")
    subparsers = parser.add_subparsers(dest="command", required=True)
    backtest = subparsers.add_parser("backtest")
    backtest.add_argument("--database-url", required=True)
    backtest.add_argument("--house", required=True)
    backtest.add_argument("--capital-gold", type=Decimal, default=Decimal("20"))
    backtest.add_argument("--strategies", default="vendor_arb")
    backtest.add_argument("--weights")
    backtest.add_argument("--start", type=float)
    backtest.add_argument("--end", type=float)
    backtest.add_argument("--wind-down-hours", type=Fraction, default=Fraction(24))
    backtest.add_argument("--demand-share", type=Fraction, default=Fraction(1))
    backtest.add_argument("--build", help="full client build, for example 1.60.1.70450")
    backtest.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if args.command != "backtest":
        parser.error(f"unsupported command: {args.command}")
    names = [name.strip() for name in args.strategies.split(",")]
    if not names or any(not name for name in names):
        parser.error("--strategies must be a comma-separated list")
    try:
        strategies = [build(name) for name in names]
        weights = _weights(args.weights)
        capital = int(args.capital_gold * 10_000)
        with psycopg.connect(args.database_url) as conn:
            with conn.transaction():
                conn.execute("SET TRANSACTION READ ONLY")
                loader_connection = _ReadOnlyLoaderConnection(conn)
                all_books = load_commodity_books(loader_connection, args.house)
                (
                    all_sweeps,
                    window_sweeps,
                    selected_sweeps,
                    client_build,
                    excluded_without_books,
                ) = _select_sweeps(conn, args.house, args.start, args.end, args.build, all_books)
                selected_ids = {int(_row_value(row, "id", 0)) for row in selected_sweeps}
                books = {
                    item_id: [book for book in item_books if int(book.sweep_id) in selected_ids]
                    for item_id, item_books in all_books.items()
                }
                books = {item_id: item_books for item_id, item_books in books.items() if item_books}
                facts, recipes = load_client_data(loader_connection, args.house, client_build)
                represented_sweeps = len(all_sweeps) - excluded_without_books
                excluded_by_window = represented_sweeps - len(window_sweeps)
                excluded_by_build = len(window_sweeps) - len(selected_sweeps)
        statistics = precompute_statistics(books)
        result = run_backtest(
            books,
            statistics,
            facts,
            recipes,
            strategies,
            weights,
            capital,
            None,
            None,
            wind_down_hours=args.wind_down_hours,
            demand_share=args.demand_share,
        )
        result.metadata.update(
            {
                "client_build": client_build,
                "selected_sweeps": len(selected_sweeps),
                "excluded_sweeps_by_window": excluded_by_window,
                "excluded_sweeps_by_build": excluded_by_build,
                "excluded_sweeps_without_books": excluded_without_books,
            }
        )
        write_report(result, args.out)
        print(text_summary(result.report()))
    except (RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
