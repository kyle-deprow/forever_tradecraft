"""Built-in strategy registry."""

from __future__ import annotations

from collections.abc import Mapping

from ..api import Strategy
from .vendor_arb import build as _build_vendor_arb

REGISTRY = {"vendor_arb": _build_vendor_arb}


def build(name: str, params: Mapping[str, object] | None = None) -> Strategy:
    try:
        factory = REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"unknown strategy name: {name}") from exc
    return factory(params)


def registered() -> tuple[str, ...]:
    return tuple(REGISTRY)


__all__ = ["REGISTRY", "build", "registered"]
