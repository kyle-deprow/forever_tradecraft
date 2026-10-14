"""Decoding of scans written by the Crowley addon, plus per-item summary statistics."""

from __future__ import annotations

import base64
import math
import zlib
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .house import House

SCAN_FORMAT = 1

# Share of the cheapest units averaged into market value (TSM-style "lowest listings").
MARKET_VALUE_SHARE = 0.15


class ScanFormatError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Listing:
    item_id: int
    item_key: str
    quantity: int
    buyout: int  # copper, whole auction; 0 = bid only
    min_bid: int
    bid: int
    time_left: int  # 1 short .. 4 very long
    owner: str  # empty when the seller is hidden

    @property
    def unit_buyout(self) -> float | None:
        return self.buyout / self.quantity if self.buyout else None


@dataclass(frozen=True, slots=True)
class ItemInfo:
    item_key: str
    name: str
    quality: int
    level: int


@dataclass
class Scan:
    scan_uid: str
    house: House
    house_source: str
    started_at: int
    finished_at: int
    context: dict[str, Any]
    listings: list[Listing]
    items: dict[str, ItemInfo]
    skipped: int


def decode_rows(payload: str) -> str:
    """Rows are raw-deflated (Enum.CompressionMethod.Deflate) then base64-encoded."""
    return zlib.decompress(base64.b64decode(payload), -zlib.MAX_WBITS).decode("utf-8")


def encode_rows(text: str) -> str:
    """Inverse of decode_rows; what the addon does in game. Used by tests and fixtures."""
    compressor = zlib.compressobj(wbits=-zlib.MAX_WBITS)
    return base64.b64encode(compressor.compress(text.encode("utf-8")) + compressor.flush()).decode()


def parse_rows(text: str) -> list[Listing]:
    """Rows: itemId,itemKey,quantity,buyout,minBid,bid,timeLeft,owner"""
    listings = []
    for line in text.split("\n"):
        item_id, item_key, quantity, buyout, min_bid, bid, time_left, owner = line.split(",")
        listings.append(
            Listing(
                item_id=int(item_id),
                item_key=item_key,
                quantity=int(quantity),
                buyout=int(buyout),
                min_bid=int(min_bid),
                bid=int(bid),
                time_left=int(time_left),
                owner=owner,
            )
        )
    return listings


def parse_scan(raw: dict[str, Any]) -> Scan:
    """Turn one entry of CrowleyDB.scans (as parsed from SavedVariables/JSON) into a Scan."""
    try:
        if raw["format"] != SCAN_FORMAT:
            raise ScanFormatError(f"unsupported scan format {raw['format']!r}")
        house_raw = raw["house"]
        listings = parse_rows(decode_rows(raw["rows"])) if raw["numRows"] else []
        if raw["numRows"] != len(listings):
            raise ScanFormatError(f"scan declares {raw['numRows']} rows but contains {len(listings)}")
        return Scan(
            scan_uid=raw["id"],
            house=House(house_raw["region"], house_raw["ruleset"], house_raw["faction"]),
            house_source=house_raw["source"],
            started_at=raw["startedAt"],
            finished_at=raw["finishedAt"],
            context=raw["context"],
            listings=listings,
            items={
                key: ItemInfo(item_key=key, name=info["n"], quality=info["q"], level=info["l"])
                for key, info in raw["items"].items()
            },
            skipped=raw["skipped"],
        )
    except ScanFormatError:
        raise
    except (KeyError, TypeError, ValueError, zlib.error) as exc:
        raise ScanFormatError(f"malformed scan: {exc!r}") from exc


@dataclass(frozen=True, slots=True)
class ItemStats:
    item_id: int
    item_key: str
    num_auctions: int
    total_quantity: int
    buyout_quantity: int  # units purchasable with buyout
    min_unit: float | None  # None when every auction is bid-only
    p10_unit: float | None
    p25_unit: float | None
    median_unit: float | None
    market_value: float | None


def _weighted_percentile(units: list[tuple[float, int]], fraction: float) -> float:
    """units sorted by price; returns the price at which `fraction` of quantity is reached."""
    target = max(1.0, fraction * sum(q for _, q in units))
    running = 0
    for price, qty in units:
        running += qty
        if running >= target:
            return price
    raise AssertionError("unreachable: target never exceeds total quantity")


def _market_value(units: list[tuple[float, int]]) -> float:
    """Quantity-weighted mean price of the cheapest MARKET_VALUE_SHARE of units (min 1)."""
    take = max(1, math.ceil(sum(q for _, q in units) * MARKET_VALUE_SHARE))
    remaining, spent = take, 0.0
    for price, qty in units:
        used = min(qty, remaining)
        spent += price * used
        remaining -= used
        if remaining == 0:
            break
    return spent / take


def compute_stats(listings: Iterable[Listing]) -> list[ItemStats]:
    groups: dict[str, list[Listing]] = defaultdict(list)
    for listing in listings:
        groups[listing.item_key].append(listing)

    stats = []
    for key, group in groups.items():
        units = sorted((lst.unit_buyout, lst.quantity) for lst in group if lst.buyout)
        priced = bool(units)
        stats.append(
            ItemStats(
                item_id=group[0].item_id,
                item_key=key,
                num_auctions=len(group),
                total_quantity=sum(lst.quantity for lst in group),
                buyout_quantity=sum(q for _, q in units),
                min_unit=units[0][0] if priced else None,
                p10_unit=_weighted_percentile(units, 0.10) if priced else None,
                p25_unit=_weighted_percentile(units, 0.25) if priced else None,
                median_unit=_weighted_percentile(units, 0.50) if priced else None,
                market_value=_market_value(units) if priced else None,
            )
        )
    return stats
