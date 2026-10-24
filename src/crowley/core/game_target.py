"""The packaged, strict launch target used by operational consumers.

The target is deliberately independent of the watchlist loader.  Generation can
therefore read a stale catalog, bind its generated metadata to a newly selected
target, and only then enforce target/catalog coherence for runtime consumers.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

from .house import House

_BUILD_RE = re.compile(r"^(?P<version>\d+\.\d+\.\d+)\.(?P<build>\d+)$")
_HOUSE_RE = re.compile(r"^[a-z0-9]+-[a-z0-9]+-[a-z0-9]+$")
FIXED_COLLECTION_CADENCE_SECONDS = 900


class GameTargetError(ValueError):
    """Raised when the packaged target is not an exact operational contract."""


def _object(value: Any, expected: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GameTargetError(f"{where} must be an object")
    unknown = set(value) - expected
    missing = expected - set(value)
    if unknown:
        raise GameTargetError(f"{where} has unknown fields: {sorted(unknown)}")
    if missing:
        raise GameTargetError(f"{where} is missing fields: {sorted(missing)}")
    return value


def _string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise GameTargetError(f"{where} must be a non-empty string")
    return value


def _integer(value: Any, where: str, *, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise GameTargetError(f"{where} must be an integer >= {minimum}")
    return value


def _absolute_path(value: Any, where: str) -> str:
    path = Path(_string(value, where))
    if not path.is_absolute() or path == Path("/") or ".." in path.parts:
        raise GameTargetError(f"{where} must be an absolute non-root path without traversal")
    return str(path)


@dataclass(frozen=True)
class GameTarget:
    target_id: str
    full_build: str
    client_version: str
    native_build: str
    interface: int
    executable: str
    window_class: str
    product: str
    product_dir: str
    locale: str
    game_root: str
    wine_prefix: str
    region: str
    native_region_id: int
    ruleset: str
    realm: str
    faction: str
    house: str
    catalog_id: str
    catalog_revision: int
    cadence_seconds: int
    sweep_cap_seconds: int
    initial_price_levels: int
    route_provenance: str

    @classmethod
    def from_mapping(cls, raw: Any) -> GameTarget:
        top = _object(
            raw,
            {
                "schemaVersion",
                "targetId",
                "client",
                "installation",
                "context",
                "scan",
                "routeProvenance",
            },
            "target",
        )
        if (
            isinstance(top["schemaVersion"], bool)
            or not isinstance(top["schemaVersion"], int)
            or top["schemaVersion"] != 1
        ):
            raise GameTargetError("target.schemaVersion must be 1")
        target_id = _string(top["targetId"], "target.targetId")
        client = _object(
            top["client"],
            {"fullBuild", "interface", "executable", "windowClass", "product", "productDir", "locale"},
            "target.client",
        )
        full_build = _string(client["fullBuild"], "target.client.fullBuild")
        match = _BUILD_RE.fullmatch(full_build)
        if match is None:
            raise GameTargetError("target.client.fullBuild must be version.build")
        version = match.group("version")
        native_build = match.group("build")
        interface = _integer(client["interface"], "target.client.interface")
        executable = _string(client["executable"], "target.client.executable")
        window_class = _string(client["windowClass"], "target.client.windowClass")
        product = _string(client["product"], "target.client.product")
        product_dir = _string(client["productDir"], "target.client.productDir")
        if (
            product_dir in {".", ".."}
            or "/" in product_dir
            or "\\" in product_dir
            or Path(product_dir).is_absolute()
            or len(Path(product_dir).parts) != 1
        ):
            raise GameTargetError("target.client.productDir must be one relative path component")
        locale = _string(client["locale"], "target.client.locale")
        if locale != "enUS":
            raise GameTargetError("target.client.locale must be the supported enUS locale")
        installation = _object(top["installation"], {"gameRoot", "winePrefix"}, "target.installation")
        game_root = _absolute_path(installation["gameRoot"], "target.installation.gameRoot")
        wine_prefix = _absolute_path(installation["winePrefix"], "target.installation.winePrefix")
        context = _object(
            top["context"],
            {"region", "ruleset", "realm", "faction", "house", "nativeRegionId"},
            "target.context",
        )
        region = _string(context["region"], "target.context.region")
        ruleset = _string(context["ruleset"], "target.context.ruleset")
        realm = _string(context["realm"], "target.context.realm")
        faction = _string(context["faction"], "target.context.faction")
        native_region_id = _integer(context["nativeRegionId"], "target.context.nativeRegionId")
        house = _string(context["house"], "target.context.house")
        if not _HOUSE_RE.fullmatch(house):
            raise GameTargetError("target.context.house must be a lowercase region-ruleset-faction key")
        try:
            house_identity = House(region, ruleset, faction.lower())
        except ValueError as exc:
            raise GameTargetError(f"target.context house values are invalid: {exc}") from exc
        if house != house_identity.key:
            raise GameTargetError("target.context.house does not match region/ruleset/faction")
        scan = _object(
            top["scan"],
            {"catalogId", "catalogRevision", "cadenceSeconds", "sweepCapSeconds", "initialPriceLevels"},
            "target.scan",
        )
        catalog_id = _string(scan["catalogId"], "target.scan.catalogId")
        catalog_revision = _integer(scan["catalogRevision"], "target.scan.catalogRevision")
        cadence_seconds = _integer(scan["cadenceSeconds"], "target.scan.cadenceSeconds")
        sweep_cap_seconds = _integer(scan["sweepCapSeconds"], "target.scan.sweepCapSeconds")
        initial_price_levels = _integer(scan["initialPriceLevels"], "target.scan.initialPriceLevels")
        if cadence_seconds != FIXED_COLLECTION_CADENCE_SECONDS:
            raise GameTargetError(
                "target.scan.cadenceSeconds must use the fixed collection policy "
                f"{FIXED_COLLECTION_CADENCE_SECONDS}"
            )
        if sweep_cap_seconds > cadence_seconds:
            raise GameTargetError("target.scan.sweepCapSeconds cannot exceed cadenceSeconds")
        route_provenance = _string(top["routeProvenance"], "target.routeProvenance")
        return cls(
            target_id,
            full_build,
            version,
            native_build,
            interface,
            executable,
            window_class,
            product,
            product_dir,
            locale,
            game_root,
            wine_prefix,
            region,
            native_region_id,
            ruleset,
            realm,
            faction,
            house,
            catalog_id,
            catalog_revision,
            cadence_seconds,
            sweep_cap_seconds,
            initial_price_levels,
            route_provenance,
        )

    def validate_catalog(self, catalog: Any) -> None:
        """Reject a runtime catalog whose generated identity differs from target."""

        if catalog.id != self.catalog_id:
            raise GameTargetError("catalog id does not match the packaged target")
        if catalog.revision != self.catalog_revision:
            raise GameTargetError("catalog revision does not match the packaged target")
        if catalog.client_build != self.full_build:
            raise GameTargetError("catalog client_build does not match the packaged target")
        if catalog.initial_price_levels != self.initial_price_levels:
            raise GameTargetError("catalog initial_price_levels does not match the packaged target")


def _parse_target(text: str, source: str) -> GameTarget:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GameTargetError(f"{source} is not valid JSON") from exc
    return GameTarget.from_mapping(value)


def load_game_target(path: str | Path | None = None) -> GameTarget:
    if path is None:
        source = resources.files("crowley.data").joinpath("game_target.json")
        return _parse_target(source.read_text(encoding="utf-8"), str(source))
    target_path = Path(path)
    return _parse_target(target_path.read_text(encoding="utf-8"), str(target_path))


@lru_cache(maxsize=1)
def packaged_game_target() -> GameTarget:
    return load_game_target()


def target_catalog(catalog: Any, target: GameTarget | None = None) -> Any:
    """Return a catalog bound to target-generated metadata without I/O."""

    target = target or packaged_game_target()
    if catalog.id != target.catalog_id or catalog.revision != target.catalog_revision:
        raise GameTargetError("source catalog identity does not match the packaged target")
    return catalog.model_copy(
        update={"client_build": target.full_build, "initial_price_levels": target.initial_price_levels}
    )


def target_scan_plan(catalog: Any, target: GameTarget | None = None) -> dict[str, Any]:
    target = target or packaged_game_target()
    bound = target_catalog(catalog, target)
    return bound.scan_plan(cadence_seconds=target.cadence_seconds)


__all__ = [
    "GameTarget",
    "GameTargetError",
    "FIXED_COLLECTION_CADENCE_SECONDS",
    "load_game_target",
    "packaged_game_target",
    "target_catalog",
    "target_scan_plan",
]
