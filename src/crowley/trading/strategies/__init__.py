"""Built-in strategy registry."""

from __future__ import annotations

from collections.abc import Mapping
from functools import partial

from ..api import Strategy
from .crafting import build as _build_crafting
from .dip_reversion import build as _build_dip_reversion
from .snipe_flip import build as _build_snipe_flip
from .vendor_arb import build as _build_vendor_arb

# One crafting strategy per crafting profession, named after the profession's client skill line.
CRAFTING_PROFESSIONS = (
    "alchemy",
    "blacksmithing",
    "cooking",
    "enchanting",
    "engineering",
    "first aid",
    "leatherworking",
    "tailoring",
)


def _crafting_for(profession: str, params: Mapping[str, object] | None = None) -> Strategy:
    merged = {"name": f"crafting_{profession.replace(' ', '_')}", "professions": (profession,)}
    merged.update(params or {})
    return _build_crafting(merged)


REGISTRY = {
    "vendor_arb": _build_vendor_arb,
    "snipe_flip": _build_snipe_flip,
    "dip_reversion": _build_dip_reversion,
    **{f"crafting_{p.replace(' ', '_')}": partial(_crafting_for, p) for p in CRAFTING_PROFESSIONS},
}


def build(name: str, params: Mapping[str, object] | None = None) -> Strategy:
    try:
        factory = REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"unknown strategy name: {name}") from exc
    return factory(params)


def registered() -> tuple[str, ...]:
    return tuple(REGISTRY)


__all__ = ["REGISTRY", "build", "registered"]
