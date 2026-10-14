"""Auction house identity.

WoW Forever is realmless: a house is a (region, ruleset, faction) triple, where faction
includes the shared goblin "neutral" houses. Every scan is attributed to exactly one house.
"""

from __future__ import annotations

from dataclasses import dataclass

REGIONS = frozenset({"us", "eu", "kr", "tw", "cn"})
RULESETS = frozenset({"normal", "pvp", "rp", "hardcore"})
# Cut taken from the seller on a successful sale.
AH_CUT = {"alliance": 0.05, "horde": 0.05, "neutral": 0.15}


@dataclass(frozen=True)
class House:
    region: str
    ruleset: str
    faction: str

    def __post_init__(self) -> None:
        if self.region not in REGIONS:
            raise ValueError(f"unknown region {self.region!r}")
        if self.ruleset not in RULESETS:
            raise ValueError(f"unknown ruleset {self.ruleset!r}")
        if self.faction not in AH_CUT:
            raise ValueError(f"unknown faction {self.faction!r}")

    @classmethod
    def parse(cls, key: str) -> House:
        region, ruleset, faction = key.split("-")
        return cls(region, ruleset, faction)

    @property
    def key(self) -> str:
        return f"{self.region}-{self.ruleset}-{self.faction}"

    @property
    def ah_cut(self) -> float:
        return AH_CUT[self.faction]

    def __str__(self) -> str:
        return self.key
