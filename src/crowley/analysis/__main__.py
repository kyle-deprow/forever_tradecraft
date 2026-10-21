"""Command-line report for commodity time-to-sale analysis."""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from urllib.parse import parse_qs, urlparse

import psycopg

from .books import load_commodity_books
from .time_to_sale import evaluate_rules, validate


def _jsonable(value):
    if isinstance(value, Fraction):
        return value.numerator if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _refuse_live_default(database_url: str) -> None:
    parsed = urlparse(database_url)
    query_hosts = parse_qs(parsed.query).get("host", [])
    hosts = {parsed.hostname, *query_hosts}
    if hosts & {"127.0.0.1", "localhost", "::1"} and (parsed.port or 5432) == 5432:
        raise SystemExit("refusing the live local database at 127.0.0.1:5432")
    if "host=127.0.0.1" in database_url and "port=5433" not in database_url:
        raise SystemExit("refusing the live local database at 127.0.0.1:5432")


def _validation_line(label: str, report: dict) -> str:
    parts = []
    for name in ("cancellation_censored", "cancellation_unsold"):
        scoring = report[name]
        if scoring["single_class"]:
            parts.append(f"{name}: single-class, not informative")
        else:
            parts.append(f"{name} Brier model={scoring['brier_model']} baseline={scoring['brier_baseline']}")
    return f"validation {label}: " + "; ".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--house", required=True, help="explicit house key")
    parser.add_argument("--out", required=True, help="JSON report path")
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--tie-share", type=float, default=0.0)
    parser.add_argument("--split-t", type=float)
    args = parser.parse_args(argv)
    if args.stride < 1:
        parser.error("--stride must be positive")
    _refuse_live_default(args.database_url)

    with psycopg.connect(args.database_url) as conn:
        books = load_commodity_books(conn, args.house)
    tables = evaluate_rules(books, stride=args.stride, tie_share=args.tie_share)
    validation = validate(books, split_t=args.split_t, stride=args.stride, tie_share=args.tie_share)
    report = {
        "house": args.house,
        "parameters": {
            "stride": args.stride,
            "tie_share": args.tie_share,
            "split_t": validation["split_t"],
        },
        "items": tables,
        "validation": validation,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(_jsonable(report), handle, indent=2, sort_keys=True)
        handle.write("\n")

    undercut = []
    for item_id, rules in tables.items():
        metric = rules.get("undercut", {}).get(20)
        if metric is not None:
            undercut.append((item_id, metric["probabilities"].get(21600, 0.0)))
    undercut.sort(key=lambda pair: (-pair[1], str(pair[0])))
    print(f"items: {len(tables)}")
    print("P(undercut, q=20, sold within 6h):")
    for item_id, probability in undercut:
        print(f"  {item_id}: {probability:.6f}")
    for label in ("2h", "6h", "24h"):
        print(_validation_line(label, validation[label]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
