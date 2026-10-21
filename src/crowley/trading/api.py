"""Contract between the trading engine and its strategies.

Strategies see only this module's types: an immutable view of the market at one sweep
(strictly-past statistics only), a view of their own account, and the intents they may
emit. The engine owns execution, accounting and every realism rule. Neither side may
change this contract without changing both.

Money is integer copper. Prices in views may be Fractions (medians); intents carry
integer copper unit prices because the auction house only accepts whole copper.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Protocol

COPPER_PER_GOLD = 10_000
AH_CUT = Fraction(5, 100)
DURATIONS_HOURS = (12, 24, 48)


# -- market view ----------------------------------------------------------------------


@dataclass(frozen=True)
class Level:
    """Units at one unit price that this strategy could buy at this sweep."""

    unit_price: int
    quantity: int


@dataclass(frozen=True)
class ItemSnapshot:
    """One commodity's state at the current sweep.

    ``levels`` is the observed book at this sweep, ascending by price, net of units any
    strategy already bought in this backtest. It reveals nothing about the future: the
    engine decides privately which of these units a Buy can actually obtain, so a Buy may
    fill less than requested. ``visible_min``/``visible_units`` describe ``levels``.
    Every statistic below uses only books strictly before ``t``; None means not observable.
    """

    item_id: int
    t: int  # when this item's book was observed (within the current sweep)
    levels: tuple[Level, ...]
    visible_min: int | None
    visible_units: int
    fair: Fraction | None
    fair_band: tuple[Fraction, Fraction] | None
    fair_n: int
    trend_per_day: float | None
    demand_units_per_day: Fraction | None
    demand_eligible_seconds: float
    volatility_per_hour: float | None
    half_life_hours: float | None


@dataclass(frozen=True)
class ItemFacts:
    """Static client facts. A vendor sells ``vendor_bundle_size`` units for
    ``vendor_bundle_price`` copper; both are None unless the item is a known vendor supply
    (only those may be bought from a vendor). VendorBuy rounds up to whole bundles."""

    item_id: int
    sell_price: int
    vendor_bundle_size: int | None
    vendor_bundle_price: int | None
    max_stack: int
    bonding: int


@dataclass(frozen=True)
class Recipe:
    """A crafting recipe with fixed yields only (random-yield recipes are not offered)."""

    spell_id: int
    professions: frozenset[str]
    reagents: tuple[tuple[int, int], ...]
    outputs: tuple[tuple[int, int], ...]
    cooldown_group: str | None
    cooldown_seconds: int
    learn_evidence: str


class MarketView(Protocol):
    """One decision step per recorded sweep, taken when that sweep finished (``t``)."""

    t: int
    sweep_index: int

    def items(self) -> Mapping[int, ItemSnapshot]:
        """Commodities with an observed full or bounded book at this sweep."""
        ...

    def facts(self, item_id: int) -> ItemFacts | None: ...

    def recipes(self) -> Sequence[Recipe]: ...

    def deposit(self, item_id: int, quantity: int, duration_hours: int) -> int:
        """Copper deposit the engine charges for this post."""
        ...


# -- account view ---------------------------------------------------------------------


@dataclass(frozen=True)
class ListingView:
    listing_id: int
    item_id: int
    unit_price: int
    quantity_remaining: int
    posted_t: int
    expires_t: int


class AccountView(Protocol):
    name: str
    professions: frozenset[str]

    def cash(self) -> int:
        """Copper available to spend now."""
        ...

    def pending_cash(self) -> int:
        """Sale proceeds still in the mail."""
        ...

    def inventory(self) -> Mapping[int, int]:
        """Units owned and not listed, by item."""
        ...

    def in_transit(self) -> Mapping[int, int]:
        """Units owned but still in the mail (e.g. returning from an expired listing), by item.
        They are not yet usable, but they are held: count them against capacity."""
        ...

    def listings(self) -> Sequence[ListingView]: ...

    def cooldown_ready(self, cooldown_group: str) -> bool: ...


# -- intents --------------------------------------------------------------------------


@dataclass(frozen=True)
class Buy:
    """Buy up to ``quantity`` units, cheapest first, never above ``max_unit_price``."""

    item_id: int
    max_unit_price: int
    quantity: int


@dataclass(frozen=True)
class Post:
    item_id: int
    unit_price: int
    quantity: int
    duration_hours: int


@dataclass(frozen=True)
class Cancel:
    listing_id: int


@dataclass(frozen=True)
class VendorSell:
    item_id: int
    quantity: int


@dataclass(frozen=True)
class VendorBuy:
    item_id: int
    quantity: int


@dataclass(frozen=True)
class Craft:
    spell_id: int
    times: int


Intent = Buy | Post | Cancel | VendorSell | VendorBuy | Craft


class Strategy(Protocol):
    """Strategies are deterministic given their inputs and keep no hidden market state
    beyond what they derive from views; the engine executes intents in the order given."""

    name: str
    professions: frozenset[str]

    def decide(self, market: MarketView, account: AccountView) -> Sequence[Intent]: ...
