"""Database and statistics loaders for the trading backtester."""

from __future__ import annotations

import json
import math
import os
from bisect import bisect_left, insort
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from decimal import Decimal
from fractions import Fraction
from heapq import heappop, heappush
from multiprocessing import get_all_start_methods, get_context
from pathlib import Path
from statistics import median
from typing import Any

from crowley.analysis.books import Book, load_commodity_books, valid_intervals
from crowley.analysis.time_to_sale import _reference

from .api import ItemFacts, Recipe


def _fraction_or_none(value: Any) -> Fraction | None:
    if value is None:
        return None
    if isinstance(value, Fraction):
        return value
    if isinstance(value, Decimal):
        return Fraction(value)
    return Fraction(value)


def _fixed_integer(value: Any, label: str) -> int:
    decimal = Decimal(str(value))
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{label} is not an integer fixed yield: {value!r}")
    return int(decimal)


def _books_mapping(books: Mapping[int, Sequence[Book]] | Sequence[Book]) -> dict[int, list[Book]]:
    if isinstance(books, Mapping):
        return {
            int(item_id): sorted(list(item_books), key=lambda book: (book.t, str(book.sweep_id)))
            for item_id, item_books in books.items()
        }
    grouped: dict[int, list[Book]] = {}
    for book in books:
        if book.item_id is None:
            raise ValueError("a sequence of books must carry item_id on every Book")
        grouped.setdefault(int(book.item_id), []).append(book)
    for item_books in grouped.values():
        item_books.sort(key=lambda book: (book.t, str(book.sweep_id)))
    return grouped


class _RollingMedian:
    """An exact incremental median over the active rolling slope set."""

    def __init__(self) -> None:
        self._lower: list[tuple[float, int]] = []
        self._upper: list[tuple[float, int]] = []
        self._values: list[float] = []
        self._alive: list[bool] = []
        self._side: list[bool] = []
        self._lower_live = 0
        self._upper_live = 0

    def _clean(self, heap: list[tuple[float, int]]) -> None:
        while heap and not self._alive[heap[0][1]]:
            heappop(heap)

    def _rebalance(self) -> None:
        self._clean(self._lower)
        self._clean(self._upper)
        while self._lower_live > self._upper_live + 1:
            neg_value, pair_id = heappop(self._lower)
            heappush(self._upper, (-neg_value, pair_id))
            self._side[pair_id] = True
            self._lower_live -= 1
            self._upper_live += 1
            self._clean(self._lower)
        while self._upper_live > self._lower_live:
            value, pair_id = heappop(self._upper)
            heappush(self._lower, (-value, pair_id))
            self._side[pair_id] = False
            self._upper_live -= 1
            self._lower_live += 1
            self._clean(self._upper)

    def add_many(self, values: Sequence[float]) -> list[int]:
        pair_ids: list[int] = []
        self._clean(self._lower)
        for value in values:
            pair_id = len(self._values)
            pair_ids.append(pair_id)
            self._values.append(value)
            self._alive.append(True)
            self._side.append(False)
            if not self._lower or value <= -self._lower[0][0]:
                heappush(self._lower, (-value, pair_id))
                self._lower_live += 1
            else:
                heappush(self._upper, (value, pair_id))
                self._side[pair_id] = True
                self._upper_live += 1
        self._rebalance()
        return pair_ids

    def remove_many(self, pair_ids: Sequence[int]) -> None:
        for pair_id in pair_ids:
            if not self._alive[pair_id]:
                continue
            self._alive[pair_id] = False
            if self._side[pair_id]:
                self._upper_live -= 1
            else:
                self._lower_live -= 1
        self._rebalance()

    def median(self) -> float | None:
        if not self._lower_live and not self._upper_live:
            return None
        self._clean(self._lower)
        self._clean(self._upper)
        if self._lower_live > self._upper_live:
            return -self._lower[0][0]
        return (-self._lower[0][0] + self._upper[0][0]) / 2


def _percentile_sorted(values: Sequence[Fraction], probability: Fraction) -> Fraction:
    position = probability * (len(values) - 1)
    lower = position.numerator // position.denominator
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower
    return values[lower] + (values[upper] - values[lower]) * weight


def _fair_series_incremental(books: Sequence[Book]) -> list[dict[str, Any]]:
    """Calculate the exact rolling fair series while maintaining the slope set."""

    references = [_reference(book) for book in books]
    log_references = [None if reference is None else math.log(float(reference)) for reference in references]
    active: list[int] = []
    sorted_references: list[Fraction] = []
    slopes = _RollingMedian()
    pairs_by_observation: list[list[int]] = [[] for _ in books]
    result: list[dict[str, Any]] = []

    def slope(left: int, right: int) -> float:
        return (log_references[right] - log_references[left]) * 86400 / (books[right].t - books[left].t)

    for index, book in enumerate(books):
        window_start = book.t - 86400
        while active and books[active[0]].t < window_start:
            expired = active.pop(0)
            slopes.remove_many(pairs_by_observation[expired])
            pairs_by_observation[expired].clear()
            reference = references[expired]
            position = bisect_left(sorted_references, reference)
            sorted_references.pop(position)
        prior = index - 1
        if prior >= 0 and references[prior] is not None and window_start <= books[prior].t < book.t:
            values = [slope(other, prior) for other in active]
            pair_ids = slopes.add_many(values)
            for other, pair_id in zip(active, pair_ids, strict=True):
                pairs_by_observation[other].append(pair_id)
            active.append(prior)
            insort(sorted_references, references[prior])

        refs = sorted_references
        if len(refs) < 8:
            result.append(
                {
                    "value": None,
                    "band": {"p25": None, "p75": None},
                    "trend_per_day": None,
                    "n": len(refs),
                }
            )
            continue
        result.append(
            {
                "value": _percentile_sorted(refs, Fraction(1, 2)),
                "band": {
                    "p25": _percentile_sorted(refs, Fraction(1, 4)),
                    "p75": _percentile_sorted(refs, Fraction(3, 4)),
                },
                "trend_per_day": slopes.median(),
                "n": len(refs),
            }
        )
    return result


def _fair_series_worker(item: tuple[int, Sequence[Book]]) -> tuple[int, list[dict[str, Any]]]:
    item_id, books = item
    return item_id, _fair_series_incremental(books)


def precompute_statistics(
    books: Mapping[int, Sequence[Book]] | Sequence[Book],
) -> dict[int, list[dict[str, Any]]]:
    """Precompute one strictly-past metric point for every item and book.

    A point at index ``k`` is built from ``books[:k]`` for aggregate metrics:
    fair value is evaluated at the current book while demand and risk use only
    intervals whose end is strictly before it.  No current or later book is passed
    to those prefix metrics.
    """

    item_mapping = _books_mapping(books)
    if len(item_mapping) >= 64 and os.cpu_count() and os.cpu_count() > 1:
        context = get_context("fork") if "fork" in get_all_start_methods() else None
        with ProcessPoolExecutor(max_workers=min(8, os.cpu_count()), mp_context=context) as executor:
            fairs_by_item = dict(executor.map(_fair_series_worker, item_mapping.items()))
    else:
        fairs_by_item = {
            item_id: _fair_series_incremental(item_books) for item_id, item_books in item_mapping.items()
        }

    result: dict[int, list[dict[str, Any]]] = {}
    for item_id, item_books_sequence in item_mapping.items():
        item_books = list(item_books_sequence)
        intervals = valid_intervals(item_books)
        fairs = fairs_by_item[item_id]
        points: list[dict[str, Any]] = []
        covered = 0.0
        purchased_units = 0
        purchased_copper = Fraction(0)
        volatility_values: list[float] = []
        volatility_eligible = 0.0
        regression: list[tuple[float, float, float]] = []
        interval_index = 0
        for index, _book in enumerate(item_books):
            # A step-k view may use intervals ending strictly before book k.  Add
            # interval k-2 immediately before constructing the point.
            target = index - 1
            while interval_index < target:
                interval = intervals[interval_index]
                interval_index += 1
                if interval is None:
                    continue
                covered += interval.dt
                purchased_units += sum(quantity for _, quantity in interval.walk.consumed)
                purchased_copper += sum(
                    (unit * quantity for unit, quantity in interval.walk.consumed), Fraction(0)
                )
                before_ref = _reference(interval.before)
                after_ref = _reference(interval.after)
                if before_ref is not None and after_ref is not None:
                    change = math.log(float(after_ref)) - math.log(float(before_ref))
                    volatility_values.append(change / math.sqrt(interval.dt / 3600))
                    volatility_eligible += interval.dt
                    before_fair = fairs[interval_index - 1]["value"]
                    after_fair = fairs[interval_index]["value"]
                    if before_fair is not None and after_fair is not None:
                        before_deviation = math.log(float(before_ref)) - math.log(float(before_fair))
                        after_deviation = math.log(float(after_ref)) - math.log(float(after_fair))
                        regression.append((before_deviation, after_deviation, interval.dt))
            fair = fairs[index]
            demand_rate = None if covered <= 0 else Fraction(purchased_units) * 86400 / Fraction(str(covered))
            copper_rate = None if covered <= 0 else purchased_copper * 86400 / Fraction(str(covered))
            if len(volatility_values) > 1:
                average = sum(volatility_values) / len(volatility_values)
                variance = sum((value - average) ** 2 for value in volatility_values) / (
                    len(volatility_values) - 1
                )
                volatility = math.sqrt(variance)
            elif volatility_values:
                volatility = 0.0
            else:
                volatility = None
            if len(regression) > 1:
                x_bar = sum(row[0] for row in regression) / len(regression)
                y_bar = sum(row[1] for row in regression) / len(regression)
                denominator = sum((row[0] - x_bar) ** 2 for row in regression)
                slope = (
                    sum((row[0] - x_bar) * (row[1] - y_bar) for row in regression) / denominator
                    if denominator
                    else None
                )
            else:
                slope = None
            if slope is not None and 0 < slope < 1:
                half_life = math.log(0.5) / math.log(slope) * median(row[2] for row in regression) / 3600
            else:
                half_life = None
            demand = {
                "covered_seconds": covered,
                "eligible_covered_seconds": covered,
                "covered_days": Fraction(str(covered)) / 86400 if covered else Fraction(0),
                "purchased_units": purchased_units,
                "purchased_copper": purchased_copper,
                "purchased_units_per_day": demand_rate,
                "purchased_units_per_day_covered_seconds": covered,
                "copper_per_day": copper_rate,
                "copper_per_day_covered_seconds": covered,
                "units_per_day": demand_rate,
                "units_per_day_covered_seconds": covered,
            }
            risk = {
                "volatility": volatility,
                "volatility_per_hour": volatility,
                "eligible_covered_seconds": volatility_eligible,
                "volatility_eligible_covered_seconds": volatility_eligible,
                "reference_intervals": len(volatility_values),
                "mean_reversion_b": slope,
                "half_life_hours": half_life,
                "mean_reversion_intervals": len(regression),
            }
            points.append(
                {
                    "fair": fair,
                    "demand": demand,
                    "risk": risk,
                    "coverage": {"books": index + 1, "covered_seconds": demand["covered_seconds"]},
                }
            )
        result[int(item_id)] = points
    return result


def _catalog_vendor_supplies() -> set[int]:
    path = Path(__file__).resolve().parents[1] / "data" / "first_run.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    expected = "The reference route explicitly buys this supply from a vendor"
    return {
        int(item["item_id"])
        for item in catalog["items"]
        if item.get("status") == "excluded" and str(item.get("reason", "")).startswith(expected)
    }


def vendor_supply_ids() -> set[int]:
    """Return catalog item ids that are explicitly vendor supplies."""

    return _catalog_vendor_supplies()


def _row(row: Any, key: str, index: int) -> Any:
    return row[key] if isinstance(row, Mapping) else row[index]


def _client_build(conn: Any, house_key: str) -> str:
    row = conn.execute(
        """
        SELECT ms.client_version, ms.client_build
        FROM market_sweeps AS ms
        JOIN houses AS h ON h.id = ms.house_id
        WHERE h.key = %s
        ORDER BY ms.started_at DESC, ms.id DESC
        LIMIT 1
        """,
        (house_key,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"no market sweeps found for house {house_key!r}")
    return f"{_row(row, 'client_version', 0)}.{_row(row, 'client_build', 1)}"


def _latest_export(conn: Any, client_build: str) -> tuple[int, str]:
    row = conn.execute(
        """
        SELECT id, client_build
        FROM latest_client_export
        WHERE client_build = %s
        ORDER BY loaded_at DESC, id DESC
        LIMIT 1
        """,
        (client_build,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"no latest client export for client build {client_build!r}")
    return int(_row(row, "id", 0)), str(_row(row, "client_build", 1))


def load_facts(conn: Any, house_key: str, client_build: str | None = None) -> dict[int, ItemFacts]:
    """Load migration-005 item facts for the build used by the house's sweeps."""

    client_build = client_build or _client_build(conn, house_key)
    export_id, _ = _latest_export(conn, client_build)
    vendor_ids = _catalog_vendor_supplies()
    rows = conn.execute(
        """
        SELECT item_id, sell_price, buy_price, vendor_stack_count, max_stack, bonding
        FROM client_items
        WHERE export_id = %s AND status = 'ok'
        ORDER BY item_id
        """,
        (export_id,),
    ).fetchall()
    # Items without an ItemSparse row (status 'no_sparse_row', assumption A5) have no client facts;
    # they are absent here, so MarketView.facts() returns None for them.
    facts: dict[int, ItemFacts] = {}
    for row in rows:
        item_id = int(_row(row, "item_id", 0))
        sell_value = _row(row, "sell_price", 1)
        stack_value = _row(row, "max_stack", 4)
        bonding_value = _row(row, "bonding", 5)
        if sell_value is None or stack_value is None or bonding_value is None:
            raise ValueError(f"client item {item_id} has status ok but missing facts")
        sell_price = int(sell_value)
        buy_price = _row(row, "buy_price", 2)
        bundle = _row(row, "vendor_stack_count", 3)
        max_stack = int(stack_value)
        bonding = int(bonding_value)
        if max_stack <= 0:
            raise ValueError(f"client item {item_id} has no positive max_stack")
        vendor_bundle_size: int | None = None
        vendor_bundle_price: int | None = None
        if item_id in vendor_ids:
            if buy_price is None or bundle is None or int(bundle) <= 0:
                raise ValueError(f"vendor supply {item_id} has no buy price or vendor stack count")
            vendor_bundle_size = int(bundle)
            vendor_bundle_price = int(buy_price)
        fact = ItemFacts(
            item_id,
            sell_price,
            vendor_bundle_size,
            vendor_bundle_price,
            max_stack,
            bonding,
        )
        facts[item_id] = fact
    return facts


def validate_recipes(recipes: Sequence[Recipe]) -> tuple[Recipe, ...]:
    """Validate the fixed-yield recipe shape before it can mutate an account."""

    def normalize(
        entries: Sequence[tuple[int, int]], label: str, spell_id: int
    ) -> tuple[tuple[int, int], ...]:
        totals: dict[int, int] = {}
        order: list[int] = []
        for raw_item_id, raw_quantity in entries:
            item_id = int(raw_item_id)
            quantity = int(raw_quantity)
            if item_id <= 0 or quantity <= 0:
                raise ValueError(f"recipe {spell_id} has non-positive {label} quantity")
            if item_id not in totals:
                order.append(item_id)
                totals[item_id] = 0
            totals[item_id] += quantity
        return tuple((item_id, totals[item_id]) for item_id in order)

    normalized: list[Recipe] = []
    for recipe in recipes:
        reagents = normalize(recipe.reagents, "reagent", recipe.spell_id)
        outputs = normalize(recipe.outputs, "output", recipe.spell_id)
        normalized.append(
            Recipe(
                spell_id=recipe.spell_id,
                professions=frozenset(recipe.professions),
                reagents=reagents,
                outputs=outputs,
                cooldown_group=recipe.cooldown_group,
                cooldown_seconds=int(recipe.cooldown_seconds),
                learn_evidence=recipe.learn_evidence,
            )
        )
    return tuple(normalized)


def load_recipes(conn: Any, house_key: str, client_build: str | None = None) -> tuple[Recipe, ...]:
    """Load fixed-yield recipes from the latest export matching the house's build."""

    client_build = client_build or _client_build(conn, house_key)
    export_id, _ = _latest_export(conn, client_build)
    recipes = conn.execute(
        """
        SELECT spell_id, cooldown_ms, category_cooldown_ms, category_name, learn_evidence
        FROM client_recipes
        WHERE export_id = %s
        ORDER BY spell_id
        """,
        (export_id,),
    ).fetchall()
    skill_rows = conn.execute(
        """
        SELECT spell_id, profession
        FROM client_recipe_skill_lines
        WHERE export_id = %s
        ORDER BY spell_id, profession
        """,
        (export_id,),
    ).fetchall()
    reagent_rows = conn.execute(
        """
        SELECT spell_id, item_id, count
        FROM client_recipe_reagents
        WHERE export_id = %s
        ORDER BY spell_id, item_id
        """,
        (export_id,),
    ).fetchall()
    output_rows = conn.execute(
        """
        SELECT spell_id, item_id, base_quantity, yield_kind
        FROM client_recipe_outputs
        WHERE export_id = %s
        ORDER BY spell_id, item_id
        """,
        (export_id,),
    ).fetchall()
    professions: dict[int, set[str]] = {}
    for row in skill_rows:
        professions.setdefault(int(_row(row, "spell_id", 0)), set()).add(str(_row(row, "profession", 1)))
    reagents: dict[int, list[tuple[int, int]]] = {}
    for row in reagent_rows:
        reagents.setdefault(int(_row(row, "spell_id", 0)), []).append(
            (int(_row(row, "item_id", 1)), int(_row(row, "count", 2)))
        )
    outputs: dict[int, list[tuple[int, int]]] = {}
    fixed: dict[int, bool] = {}
    for row in output_rows:
        spell_id = int(_row(row, "spell_id", 0))
        if str(_row(row, "yield_kind", 3)) != "fixed":
            fixed[spell_id] = False
            continue
        fixed.setdefault(spell_id, True)
        outputs.setdefault(spell_id, []).append(
            (
                int(_row(row, "item_id", 1)),
                _fixed_integer(_row(row, "base_quantity", 2), f"recipe {spell_id} output"),
            )
        )
    result: list[Recipe] = []
    for row in recipes:
        spell_id = int(_row(row, "spell_id", 0))
        if not fixed.get(spell_id, False) or not outputs.get(spell_id):
            continue
        category_ms = int(_row(row, "category_cooldown_ms", 2) or 0)
        spell_ms = int(_row(row, "cooldown_ms", 1) or 0)
        if category_ms > 0:
            group = _row(row, "category_name", 3)
            if not group:
                raise ValueError(f"recipe {spell_id} has a category cooldown without a category name")
            cooldown_group = str(group)
            cooldown_seconds = math.ceil(category_ms / 1000)
        elif spell_ms > 0:
            cooldown_group = str(spell_id)
            cooldown_seconds = math.ceil(spell_ms / 1000)
        else:
            cooldown_group = None
            cooldown_seconds = 0
        result.append(
            Recipe(
                spell_id=spell_id,
                professions=frozenset(professions.get(spell_id, set())),
                reagents=tuple(reagents.get(spell_id, [])),
                outputs=tuple(outputs[spell_id]),
                cooldown_group=cooldown_group,
                cooldown_seconds=cooldown_seconds,
                learn_evidence=str(_row(row, "learn_evidence", 4)),
            )
        )
    return validate_recipes(result)


def load_client_data(
    conn: Any, house_key: str, client_build: str | None = None
) -> tuple[dict[int, ItemFacts], tuple[Recipe, ...]]:
    """Load facts and recipes while the caller holds its read-only transaction."""

    client_build = client_build or _client_build(conn, house_key)
    return load_facts(conn, house_key, client_build), load_recipes(conn, house_key, client_build)


load_books = load_commodity_books


__all__ = [
    "load_client_data",
    "load_books",
    "load_commodity_books",
    "load_facts",
    "load_recipes",
    "precompute_statistics",
    "validate_recipes",
    "vendor_supply_ids",
]
