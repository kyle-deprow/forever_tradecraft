from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from crowley.core.recipes import (
    CRAFTING_PROFESSIONS,
    PROFESSIONS,
    RecipeFoundation,
    coverage_report,
    load_recipe_foundation,
    recipe_readiness,
    serialize_recipe_foundation,
    validate_normalized_artifact,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = REPO_ROOT / ".archive" / "executor-review"
RAW_MANIFEST_PATH = REVIEW_ROOT / "recipe-foundation-source-manifest-20261017.json"


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str]
    parent: _Node | None = None
    children: list[_Node | str] = field(default_factory=list)

    def text(self) -> str:
        return " ".join("".join(self._text_parts()).split())

    def _text_parts(self):
        for child in self.children:
            if isinstance(child, _Node):
                yield from child._text_parts()
            else:
                yield child


class _TreeParser(HTMLParser):
    _void_tags = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("document", {})
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag, {name: value or "" for name, value in attrs}, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in self._void_tags:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack[-1].children.append(
            _Node(tag, {name: value or "" for name, value in attrs}, self.stack[-1])
        )

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].children.append(data)


def _descendants(root: _Node):
    for child in root.children:
        if isinstance(child, _Node):
            yield child
            yield from _descendants(child)


def _matches_compound(node: _Node, selector: str) -> bool:
    pseudo = None
    pseudo_match = re.search(r":(first-child|nth-child\((\d+)\))$", selector)
    if pseudo_match:
        pseudo = pseudo_match.group(1)
        selector = selector[: pseudo_match.start()]

    attrs = re.findall(r"\[([a-zA-Z0-9_-]+)(?:=\"([^\"]*)\")?\]", selector)
    selector = re.sub(r"\[[^\]]+\]", "", selector)
    if any(name not in node.attrs or (value and node.attrs[name] != value) for name, value in attrs):
        return False

    id_match = re.search(r"#([a-zA-Z0-9_-]+)", selector)
    if id_match:
        if node.attrs.get("id") != id_match.group(1):
            return False
        selector = selector.replace(id_match.group(0), "")

    classes = re.findall(r"\.([a-zA-Z0-9_-]+)", selector)
    node_classes = set(node.attrs.get("class", "").split())
    if any(value not in node_classes for value in classes):
        return False
    selector = re.sub(r"\.[a-zA-Z0-9_-]+", "", selector)
    tag = selector.strip()
    if tag and tag != node.tag:
        return False

    if pseudo:
        if node.parent is None:
            return False
        siblings = [child for child in node.parent.children if isinstance(child, _Node)]
        position = siblings.index(node) + 1
        if pseudo == "first-child" and position != 1:
            return False
        if pseudo.startswith("nth-child") and position != int(pseudo_match.group(2)):
            return False
    return True


def _matches_selector(node: _Node, selector: str) -> bool:
    parts = selector.split()
    if not parts or not _matches_compound(node, parts[-1]):
        return False
    ancestor = node.parent
    for part in reversed(parts[:-1]):
        while ancestor is not None and not _matches_compound(ancestor, part):
            ancestor = ancestor.parent
        if ancestor is None:
            return False
        ancestor = ancestor.parent
    return True


def _select(root: _Node, selector: str) -> list[_Node]:
    return [node for node in _descendants(root) if _matches_selector(node, selector)]


def _parse_html(data: bytes) -> _Node:
    parser = _TreeParser()
    parser.feed(data.decode("utf-8"))
    parser.close()
    return parser.root


def _record_value(record: dict[str, Any], field_path: str) -> Any:
    value: Any = record
    for part in field_path.strip("/").split("/"):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def _locator_value_for_path(field_path: str, expected_value: str, source_kind: str) -> Any:
    if field_path == "/profession":
        return expected_value.casefold()
    if field_path == "/source_build":
        return expected_value
    if field_path == "/recipe_id":
        match = re.search(r"(\d+)$", expected_value)
        assert match
        return int(match.group(1))
    if field_path.endswith("/item_id"):
        match = re.search(r"/item/(\d+)$", expected_value)
        if not match:
            match = re.search(r"/item/(\d+)$", expected_value.rstrip("/"))
        assert match, (field_path, expected_value)
        return int(match.group(1))
    if field_path.endswith("/quantity"):
        match = re.match(r"(\d+)\s+", expected_value)
        assert match, (field_path, expected_value)
        return int(match.group(1))
    if field_path.endswith("/optional"):
        return "optional" in expected_value.casefold()
    if field_path.startswith("/skill_gate/"):
        skill_match = re.fullmatch(r"Learn (\d+), yellow (\d+), green (\d+), grey (\d+)", expected_value)
        assert skill_match
        values = dict(
            zip(("minimum", "yellow", "green", "gray"), map(int, skill_match.groups()), strict=True)
        )
        return {"value": values[field_path.rsplit("/", 1)[1]], "status": "known"}
    if field_path == "/learnability/status":
        return "client_file_only" if "apprentice knows it" in expected_value.casefold() else "unknown"
    if field_path == "/learnability/evidence_kind":
        return "displayed_client_data" if source_kind == "bind_on_forever" else "unknown"
    if field_path.startswith("/acquisition/conditions/"):
        return expected_value
    raise AssertionError(f"no review-time field extractor for {field_path}")


def validate_review_snapshot_evidence(catalog: RecipeFoundation) -> None:
    """Check frozen local bytes, locator values, and the package's normalized projection."""
    raw_manifest = json.loads(RAW_MANIFEST_PATH.read_text(encoding="utf-8"))
    normalized = {key: value for key, value in raw_manifest.items() if key != "entries"}
    normalized["entries"] = [
        {key: value for key, value in entry.items() if key != "snapshot_path"}
        for entry in raw_manifest["entries"]
    ]
    assert catalog.source_manifest.manifest.model_dump(mode="json") == normalized

    for entry in raw_manifest["entries"]:
        snapshot = REPO_ROOT / entry["snapshot_path"]
        raw_bytes = snapshot.read_bytes()
        assert hashlib.sha256(raw_bytes).hexdigest() == entry["sha256"]
        root = _parse_html(raw_bytes)
        for locator in entry["locators"]:
            matches = _select(root, locator["selector"])
            assert len(matches) == 1, (entry["entry_id"], locator["locator_id"], len(matches))
            node = matches[0]
            if locator["value_kind"] == "attribute":
                actual = node.attrs.get(locator["attribute"])
            else:
                actual = node.text()
            assert actual == locator["expected_value"], (
                entry["entry_id"],
                locator["locator_id"],
                actual,
                locator["expected_value"],
            )

    entries = {entry.entry_id: entry for entry in catalog.source_manifest.manifest.entries}
    for recipe in catalog.recipes:
        record = recipe.model_dump(mode="json")
        for claim in recipe.provenance_claims:
            entry = entries[claim.manifest_entry_id]
            locator = next(locator for locator in entry.locators if locator.locator_id == claim.locator_id)
            for field_path in claim.field_paths:
                expected = _locator_value_for_path(field_path, locator.expected_value, entry.source_kind)
                assert _record_value(record, field_path) == expected, (
                    recipe.record_id,
                    field_path,
                    _record_value(record, field_path),
                    expected,
                )


def _raw_artifact() -> dict[str, Any]:
    resource = REPO_ROOT / "src" / "crowley" / "data" / "recipe_foundation.json"
    return json.loads(resource.read_text(encoding="utf-8"))


def _validate_modified(mutator) -> None:
    body = _raw_artifact()
    mutator(body)
    with pytest.raises(ValidationError):
        validate_normalized_artifact(json.dumps(body, ensure_ascii=False))


def test_packaged_resource_embeds_manifest_and_loads_without_archive_access() -> None:
    catalog = load_recipe_foundation()
    assert catalog.catalog_id == "forever-recipe-foundation"
    assert len(catalog.recipes) == 2
    assert (
        catalog.source_manifest.sha256 == "7da0a957d6d04a5e351a9cba7c54ef622d816fa519c0682501c481a114187378"
    )
    assert all(
        "snapshot_path" not in entry.model_dump(mode="json")
        for entry in catalog.source_manifest.manifest.entries
    )
    serialized = serialize_recipe_foundation(catalog)
    assert validate_normalized_artifact(serialized) == catalog
    assert serialized == json.dumps(
        catalog.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def test_pilots_retain_only_frozen_facts_and_recipe_side_blockers() -> None:
    catalog = load_recipe_foundation()
    by_profession = {record.profession: record for record in catalog.recipes}
    mining, cooking = by_profession["mining"], by_profession["cooking"]
    assert mining.recipe_id == 2657
    assert mining.output.item_id == 2840 and mining.output.quantity is None
    assert mining.reagents[0].item_id == 2770 and mining.reagents[0].quantity == 1
    assert {
        name: getattr(mining.skill_gate, name).value for name in ("minimum", "yellow", "green", "gray")
    } == {
        "minimum": 1,
        "yellow": 25,
        "green": 47,
        "gray": 70,
    }
    assert mining.learnability.status == "client_file_only"
    assert mining.acquisition.conditions == ["Needs a forge"]
    assert mining.readiness.codes == [
        "OUTPUT_QUANTITY_UNKNOWN",
        "LEARNABILITY_NOT_CONFIRMED",
        "COOLDOWN_UNKNOWN",
        "TRADEABILITY_UNKNOWN",
    ]

    assert cooking.recipe_id == 2538
    assert cooking.output.item_id == 2679 and cooking.output.quantity is None
    assert cooking.reagents[0].item_id == 2672 and cooking.reagents[0].quantity == 1
    assert {
        name: getattr(cooking.skill_gate, name).value for name in ("minimum", "yellow", "green", "gray")
    } == {
        "minimum": 1,
        "yellow": 45,
        "green": 65,
        "gray": 85,
    }
    assert cooking.learnability.status == "client_file_only"
    assert cooking.acquisition.conditions == ["Needs a cooking fire"]
    assert all(record.review_status == "blocked" for record in catalog.recipes)


def test_nine_profession_coverage_has_blockers_and_diagnostic_overlap() -> None:
    report = coverage_report(load_recipe_foundation(), first_run_item_ids={2840, 2672, 999999})
    rows = report["professions"]
    assert [row["profession"] for row in rows] == list(PROFESSIONS)
    assert len(rows) == 9
    assert [row["profession"] for row in rows if row["profession_kind"] == "crafting"] == list(
        CRAFTING_PROFESSIONS
    )

    by_profession = {row["profession"]: row for row in rows}
    assert by_profession["alchemy"]["total_records"] == 0
    assert by_profession["cooking"]["blocked"] == 1
    assert by_profession["cooking"]["output_quantity_coverage"] == {"known": 0, "unknown": 1, "total": 1}
    assert by_profession["cooking"]["reagent_quantity_coverage"] == {"known": 1, "unknown": 0, "total": 1}
    assert by_profession["cooking"]["first_run_overlap_item_ids"] == [2672]
    assert by_profession["mining"]["first_run_overlap_item_ids"] == [2840]
    assert by_profession["mining"]["blocking_reasons"]["LEARNABILITY_NOT_CONFIRMED"] == [
        "rfs-20261017-mining-2840-0"
    ]
    default_report = coverage_report(load_recipe_foundation())
    assert len(default_report["professions"]) == 9


def test_unresolved_recipe_ids_keep_stable_review_identity() -> None:
    data = _raw_artifact()
    mining = next(record for record in data["recipes"] if record["profession"] == "mining")
    stable_id = mining["record_id"]
    mining["recipe_id"] = None
    mining["unknowns"] = sorted([*mining["unknowns"], "recipe_id_unresolved"])
    mining["readiness"]["codes"].insert(0, "RECIPE_ID_UNRESOLVED")
    mining["provenance_claims"] = [
        claim for claim in mining["provenance_claims"] if claim["locator_id"] != "mining.recipe-id"
    ]
    result = validate_normalized_artifact(json.dumps(data, ensure_ascii=False))
    unresolved = next(record for record in result.recipes if record.profession == "mining")
    assert unresolved.record_id == stable_id
    assert unresolved.recipe_id is None
    assert unresolved.readiness.status == "blocked"
    assert unresolved.readiness.codes[0] == "RECIPE_ID_UNRESOLVED"


def test_displayed_client_data_cannot_confirm_server_learnability() -> None:
    body = _raw_artifact()
    record = body["recipes"][0]
    record["learnability"] = {
        "status": "confirmed_learnable",
        "evidence_kind": "displayed_client_data",
    }
    with pytest.raises(ValidationError, match="confirmed learnability requires server-observation"):
        validate_normalized_artifact(json.dumps(body, ensure_ascii=False))


def test_readiness_refuses_a_source_build_mismatch() -> None:
    catalog = load_recipe_foundation()
    mining = next(record for record in catalog.recipes if record.profession == "mining")
    mismatched = mining.model_copy(update={"source_build": "1.60.1.70425"})
    result = recipe_readiness(mismatched, catalog.target_client_build)
    assert result.status == "blocked"
    assert result.codes[:2] == ["SOURCE_BUILD_MISMATCH", "OUTPUT_QUANTITY_UNKNOWN"]


@pytest.mark.parametrize(
    "mutator",
    [
        lambda data: data.update(extra=True),
        lambda data: data["recipes"][0]["output"].update(quantity=1),
        lambda data: data["recipes"][0]["skill_gate"].update(orange={"value": 25, "status": "known"}),
        lambda data: data["recipes"][0]["cooldown"].update(status="none", seconds=1),
        lambda data: data["recipes"][0]["provenance_claims"][0].update(locator_id="missing.locator"),
        lambda data: data["source_manifest"].update(sha256="0" * 64),
        lambda data: data["recipes"][0]["output"].update(item_id=-1),
        lambda data: data["recipes"][1].update(record_id=data["recipes"][0]["record_id"]),
    ],
    ids=[
        "extra-key",
        "quantity-null-status",
        "unsupported-orange",
        "cooldown-state",
        "unbound-claim",
        "digest",
        "negative-item-id",
        "duplicate-record-id",
    ],
)
def test_strict_schema_rejects_malformed_fields_and_unbound_claims(mutator) -> None:
    _validate_modified(mutator)


def test_review_helper_verifies_raw_snapshot_boundary_and_exact_locators() -> None:
    catalog = load_recipe_foundation()
    validate_review_snapshot_evidence(catalog)
    assert len(catalog.source_manifest.manifest.entries) == 6


def test_review_helper_detects_a_record_value_detached_from_its_locator() -> None:
    catalog = load_recipe_foundation()
    mining = next(record for record in catalog.recipes if record.profession == "mining")
    bad_output = mining.output.model_copy(update={"item_id": 999999})
    bad_mining = mining.model_copy(update={"output": bad_output})
    bad_recipes = [bad_mining if record is mining else record for record in catalog.recipes]
    bad_catalog = catalog.model_copy(update={"recipes": bad_recipes})
    with pytest.raises(AssertionError, match="/output/item_id"):
        validate_review_snapshot_evidence(bad_catalog)


def test_contract_exposes_only_recipe_side_readiness() -> None:
    catalog = load_recipe_foundation()
    assert all(not hasattr(record, "market_quotes") for record in catalog.recipes)
    assert all(not hasattr(record, "margin") for record in catalog.recipes)
    assert all(record.readiness.status == "blocked" for record in catalog.recipes)
