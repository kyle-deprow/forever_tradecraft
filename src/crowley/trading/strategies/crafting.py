"""Choose profitable recipe batches, craft from inventory, and replenish inputs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction

from crowley.trading.api import (
    AH_CUT,
    AccountView,
    Buy,
    Craft,
    Intent,
    MarketView,
    Post,
    Recipe,
    Strategy,
    VendorBuy,
    VendorSell,
)

from .common import (
    as_fraction,
    clears_vendor_floor,
    floor_fraction,
    held_quantity,
    item_inventory,
    marginal_purchase,
    target_sell_price,
    trustworthy_fair,
    vendor_purchase,
)

DEFAULT_PARAMS = {
    "name": "crafting",
    "professions": (),
    "floor_ratio": 0.9,
    "cap_ratio": 1.1,
    "buy_ratio": 0.75,
    "min_margin": 0.15,
    "max_spend_share": 0.5,
    "capacity_share": 0.25,
    "min_fair_n": 16,
    "max_band_width": 0.35,
}


@dataclass(frozen=True)
class _Source:
    item_id: int
    quantity: int
    kind: str
    unit_limit: int
    full_cost: Fraction


@dataclass(frozen=True)
class _Candidate:
    recipe: Recipe
    times: int
    cost: Fraction
    value: Fraction
    profit: Fraction
    sources: tuple[_Source, ...]


def _requirements(recipe: Recipe, times: int) -> dict[int, int]:
    result: dict[int, int] = {}
    for item_id, quantity in recipe.reagents:
        if quantity > 0:
            result[item_id] = result.get(item_id, 0) + quantity * times
    return result


def _projected_capacity(
    snapshot,
    held: Mapping[int, int],
    capacity_share: Fraction | int | float,
) -> int:
    assert snapshot.demand_units_per_day is not None
    cap = floor_fraction(as_fraction(capacity_share) * snapshot.demand_units_per_day)
    return max(0, cap - held.get(snapshot.item_id, 0))


class CraftingStrategy:
    def __init__(self, params: Mapping[str, object] | None = None) -> None:
        self.params = dict(DEFAULT_PARAMS)
        if params:
            self.params.update(params)
        professions = self.params.get("professions", ())
        if isinstance(professions, str):
            professions = (professions,)
        self.professions = frozenset(str(profession) for profession in professions)
        self.name = str(self.params.get("name", "crafting"))
        self._planned: tuple[int, int] | None = None

    def _trusted_outputs(self, recipe: Recipe, market: MarketView):
        outputs: dict[int, tuple[object, object, int]] = {}
        for item_id, quantity in recipe.outputs:
            snapshot = market.items().get(item_id)
            facts = market.facts(item_id)
            if (
                quantity <= 0
                or snapshot is None
                or facts is None
                or not trustworthy_fair(
                    snapshot,
                    min_fair_n=int(self.params["min_fair_n"]),
                    max_band_width=self.params["max_band_width"],
                )
            ):
                return None
            previous = outputs.get(item_id, (None, None, 0))[2]
            outputs[item_id] = (snapshot, facts, previous + quantity)
        return outputs or None

    def _source(self, market: MarketView, item_id: int, quantity: int) -> _Source | None:
        snapshot = market.items().get(item_id)
        facts = market.facts(item_id)
        ah = marginal_purchase(snapshot.levels, quantity) if snapshot is not None else None
        vendor = None if facts is None else vendor_purchase(facts, quantity)
        if ah is None and vendor is None:
            return None
        if ah is not None and (vendor is None or ah[0] <= vendor[1]):
            return _Source(item_id, quantity, "ah", ah[1], ah[0])
        assert vendor is not None
        return _Source(item_id, quantity, "vendor", 0, Fraction(vendor[1]))

    def _actual_purchase_cost(
        self,
        market: MarketView,
        source: _Source,
        inventory: Mapping[int, int],
    ) -> Fraction:
        missing = max(0, source.quantity - item_inventory(inventory, source.item_id))
        if missing == 0:
            return Fraction(0)
        if source.kind == "ah":
            return Fraction(missing * source.unit_limit)
        facts = market.facts(source.item_id)
        assert facts is not None
        purchase = vendor_purchase(facts, missing)
        return Fraction(10**30) if purchase is None else Fraction(purchase[1])

    def _candidate(
        self,
        recipe: Recipe,
        market: MarketView,
        account: AccountView,
        inventory: Mapping[int, int],
        held: Mapping[int, int],
        projected_cash: int,
        crafted_groups: set[str],
    ) -> _Candidate | None:
        if not recipe.professions.intersection(self.professions):
            return None
        outputs = self._trusted_outputs(recipe, market)
        if outputs is None:
            return None
        if recipe.cooldown_group is not None:
            if not account.cooldown_ready(recipe.cooldown_group):
                return None
            if recipe.cooldown_group in crafted_groups:
                return None
            max_times = 1
        else:
            max_times = 1_000_000_000
        for snapshot, _facts, quantity in outputs.values():
            max_times = min(
                max_times,
                _projected_capacity(snapshot, held, self.params["capacity_share"]) // quantity,
            )
        if max_times <= 0:
            return None

        best: _Candidate | None = None
        spend_limit = floor_fraction(as_fraction(self.params["max_spend_share"]) * max(0, projected_cash))
        for times in range(1, max_times + 1):
            sources: list[_Source] = []
            for item_id, quantity in _requirements(recipe, times).items():
                source = self._source(market, item_id, quantity)
                if source is None:
                    sources = []
                    break
                sources.append(source)
            if not sources and recipe.reagents:
                break
            purchase_cost = sum(
                (self._actual_purchase_cost(market, source, inventory) for source in sources),
                Fraction(0),
            )
            if purchase_cost > spend_limit:
                continue
            value = Fraction(0)
            for item_id, (snapshot, _facts, quantity) in outputs.items():
                target = target_sell_price(
                    snapshot,
                    floor_fraction(as_fraction(self.params["buy_ratio"]) * snapshot.fair),
                    floor_ratio=self.params["floor_ratio"],
                    cap_ratio=self.params["cap_ratio"],
                )
                value += quantity * times * target * (1 - AH_CUT) - market.deposit(
                    item_id, quantity * times, 24
                )
            cost = sum((source.full_cost for source in sources), Fraction(0))
            profit = value - cost
            if profit < cost * as_fraction(self.params["min_margin"]):
                continue
            candidate = _Candidate(recipe, times, cost, value, profit, tuple(sources))
            if best is None or (candidate.profit, candidate.times) > (best.profit, best.times):
                best = candidate
        return best

    def _craft_previous(
        self,
        market: MarketView,
        account: AccountView,
        recipes: Mapping[int, Recipe],
        inventory: dict[int, int],
        held: dict[int, int],
    ) -> tuple[list[Intent], set[str]]:
        if self._planned is None:
            return [], set()
        spell_id, planned_times = self._planned
        recipe = recipes.get(spell_id)
        if recipe is None or not recipe.professions.intersection(self.professions):
            self._planned = None
            return [], set()
        before = dict(inventory)
        available = 1_000_000_000
        for item_id, quantity in recipe.reagents:
            if quantity > 0:
                available = min(available, item_inventory(inventory, item_id) // quantity)
        if recipe.cooldown_group is not None:
            if not account.cooldown_ready(recipe.cooldown_group):
                available = 0
            else:
                available = min(available, 1)
        for item_id, quantity in recipe.outputs:
            snapshot = market.items().get(item_id)
            if snapshot is None or snapshot.demand_units_per_day is None:
                available = 0
                break
            available = min(
                available,
                _projected_capacity(snapshot, held, self.params["capacity_share"]) // quantity,
            )
        times = min(planned_times, available)
        if times <= 0:
            return [], set()
        for item_id, quantity in recipe.reagents:
            inventory[item_id] = item_inventory(inventory, item_id) - quantity * times
        for item_id, quantity in recipe.outputs:
            inventory[item_id] = item_inventory(inventory, item_id) + quantity * times
        for item_id in set(before) | set(inventory):
            held[item_id] = max(0, held.get(item_id, 0) + inventory.get(item_id, 0) - before.get(item_id, 0))
        groups = {recipe.cooldown_group} if recipe.cooldown_group is not None else set()
        return [Craft(recipe.spell_id, times)], groups

    def _purchase_intents(
        self,
        candidate: _Candidate,
        market: MarketView,
        inventory: Mapping[int, int],
    ) -> list[Intent] | None:
        purchases: list[Intent] = []
        for source in candidate.sources:
            missing = max(0, source.quantity - item_inventory(inventory, source.item_id))
            if missing == 0:
                continue
            if source.kind == "ah":
                purchases.append(Buy(source.item_id, source.unit_limit, missing))
                continue
            facts = market.facts(source.item_id)
            assert facts is not None
            purchase = vendor_purchase(facts, missing)
            if purchase is None:
                return None
            purchases.append(VendorBuy(source.item_id, purchase[0]))
        return purchases

    def decide(self, market: MarketView, account: AccountView) -> Sequence[Intent]:
        recipes = {
            recipe.spell_id: recipe for recipe in sorted(market.recipes(), key=lambda entry: entry.spell_id)
        }
        inventory = {item_id: item_inventory(account.inventory(), item_id) for item_id in account.inventory()}
        held = {item_id: held_quantity(account, item_id) for item_id in account.inventory()}
        for recipe in recipes.values():
            for item_id, _quantity in (*recipe.reagents, *recipe.outputs):
                held.setdefault(item_id, held_quantity(account, item_id))
        intents, crafted_groups = self._craft_previous(market, account, recipes, inventory, held)
        projected_cash = max(0, int(account.cash()))

        output_ids = sorted(
            {
                item_id
                for recipe in recipes.values()
                if recipe.professions.intersection(self.professions)
                for item_id, _quantity in recipe.outputs
            }
        )
        vendor_exits: list[tuple[int, int]] = []
        post_exits: list[tuple[Fraction, int, int, int]] = []
        for item_id in output_ids:
            snapshot = market.items().get(item_id)
            facts = market.facts(item_id)
            quantity = item_inventory(inventory, item_id)
            if (
                snapshot is None
                or facts is None
                or quantity <= 0
                or not trustworthy_fair(
                    snapshot,
                    min_fair_n=int(self.params["min_fair_n"]),
                    max_band_width=self.params["max_band_width"],
                )
            ):
                continue
            target = target_sell_price(
                snapshot,
                floor_fraction(as_fraction(self.params["buy_ratio"]) * snapshot.fair),
                floor_ratio=self.params["floor_ratio"],
                cap_ratio=self.params["cap_ratio"],
            )
            if not clears_vendor_floor(target, facts):
                vendor_exits.append((item_id, quantity))
                continue
            deposit = market.deposit(item_id, quantity, 24)
            proceeds = Fraction(quantity) * target * (1 - AH_CUT) - deposit
            post_exits.append((proceeds, item_id, quantity, deposit))

        for item_id, quantity in sorted(vendor_exits):
            facts = market.facts(item_id)
            assert facts is not None
            intents.append(VendorSell(item_id, quantity))
            inventory[item_id] = 0
            held[item_id] = max(0, held.get(item_id, 0) - quantity)
            projected_cash += facts.sell_price * quantity

        for _value, item_id, quantity, deposit in sorted(post_exits, key=lambda entry: (-entry[0], entry[1])):
            if deposit > projected_cash:
                continue
            facts = market.facts(item_id)
            assert facts is not None
            snapshot = market.items()[item_id]
            target = target_sell_price(
                snapshot,
                floor_fraction(as_fraction(self.params["buy_ratio"]) * snapshot.fair),
                floor_ratio=self.params["floor_ratio"],
                cap_ratio=self.params["cap_ratio"],
            )
            intents.append(Post(item_id, target, quantity, 24))
            projected_cash -= deposit
            inventory[item_id] = 0

        candidates: list[_Candidate] = []
        for recipe in recipes.values():
            candidate = self._candidate(
                recipe,
                market,
                account,
                inventory,
                held,
                projected_cash,
                crafted_groups,
            )
            if candidate is not None and self._purchase_intents(candidate, market, inventory) is not None:
                candidates.append(candidate)
        if not candidates:
            self._planned = None
            return intents

        candidate = max(candidates, key=lambda entry: (entry.profit, entry.times, -entry.recipe.spell_id))
        purchases = self._purchase_intents(candidate, market, inventory)
        assert purchases is not None
        self._planned = (candidate.recipe.spell_id, candidate.times)
        intents.extend(purchases)
        return intents


def build(params: Mapping[str, object] | None = None) -> Strategy:
    return CraftingStrategy(params)


__all__ = ["DEFAULT_PARAMS", "CraftingStrategy", "build"]
