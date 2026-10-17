"""Strict offline recipe facts and recipe-side readiness.

The installed loader validates only the normalized source manifest embedded in the
packaged JSON. Raw HTML snapshot verification belongs to the review test helper and
is never imported here.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date, datetime
from importlib import resources
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = 1
CATALOG_ID = "forever-recipe-foundation"
MANIFEST_VERSION = 2
TARGET_CLIENT_BUILD = "1.60.1.70450"

CRAFTING_PROFESSIONS = (
    "alchemy",
    "blacksmithing",
    "cooking",
    "enchanting",
    "engineering",
    "first-aid",
    "leatherworking",
    "tailoring",
)
PROFESSIONS = (*CRAFTING_PROFESSIONS, "mining")
PROFESSION_KIND = {profession: "crafting" for profession in CRAFTING_PROFESSIONS} | {"mining": "processing"}
SKILL_THRESHOLDS = ("minimum", "yellow", "green", "gray")
REFUSAL_CODES = (
    "RECIPE_ID_UNRESOLVED",
    "SOURCE_BUILD_MISMATCH",
    "OUTPUT_QUANTITY_UNKNOWN",
    "REAGENT_QUANTITY_UNKNOWN",
    "SKILL_GATE_UNKNOWN",
    "LEARNABILITY_NOT_CONFIRMED",
    "ACQUISITION_UNKNOWN",
    "COOLDOWN_UNKNOWN",
    "VENDOR_PRICE_UNKNOWN",
    "VENDOR_STOCK_UNKNOWN",
    "TRADEABILITY_UNKNOWN",
    "PROVENANCE_UNBOUND",
)

PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]
BuildString = Annotated[str, Field(pattern=r"^\d+\.\d+\.\d+\.\d+$")]
Sha256String = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class TextLocator(StrictModel):
    locator_id: Identifier
    selector: str = Field(min_length=1)
    value_kind: Literal["text"]
    expected_value: str = Field(min_length=1)
    field_paths: list[str]


class AttributeLocator(StrictModel):
    locator_id: Identifier
    selector: str = Field(min_length=1)
    value_kind: Literal["attribute"]
    attribute: str = Field(min_length=1)
    expected_value: str = Field(min_length=1)
    field_paths: list[str]


ManifestLocator = Annotated[TextLocator | AttributeLocator, Field(discriminator="value_kind")]


def _validate_field_paths(paths: list[str]) -> None:
    if paths != sorted(set(paths)):
        raise ValueError("field_paths must be sorted and unique")
    if any(not path.startswith("/") or path == "/" for path in paths):
        raise ValueError("field_paths must be non-root JSON pointers")


class SourceManifestEntry(StrictModel):
    entry_id: Identifier
    source_kind: Literal["bind_on_forever", "live_client_observation"]
    url: str = Field(min_length=1)
    sha256: Sha256String
    retrieved_at: str = Field(min_length=1)
    title: str = Field(min_length=1)
    claimed_build: BuildString
    locators: list[ManifestLocator]

    @field_validator("url")
    @classmethod
    def https_url_only(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("manifest source URLs must use HTTPS")
        return value

    @field_validator("retrieved_at")
    @classmethod
    def utc_timestamp(cls, value: str) -> str:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("retrieved_at must be an ISO timestamp") from exc
        if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
            raise ValueError("retrieved_at must be UTC")
        return value

    @model_validator(mode="after")
    def unique_sorted_locators(self) -> SourceManifestEntry:
        locator_ids = [locator.locator_id for locator in self.locators]
        if locator_ids != sorted(set(locator_ids)):
            raise ValueError("manifest locators must be sorted by unique locator_id")
        for locator in self.locators:
            _validate_field_paths(locator.field_paths)
        return self


class NormalizedSourceManifest(StrictModel):
    manifest_version: Literal[2]
    collection_id: Identifier
    target_client_build: BuildString
    entries: list[SourceManifestEntry]

    @model_validator(mode="after")
    def unique_sorted_entries(self) -> NormalizedSourceManifest:
        entry_ids = [entry.entry_id for entry in self.entries]
        if entry_ids != sorted(set(entry_ids)):
            raise ValueError("manifest entries must be sorted by unique entry_id")
        return self


def _canonical_json_bytes(value: BaseModel | dict[str, object]) -> bytes:
    body = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


class SourceManifestBinding(StrictModel):
    sha256: Sha256String
    manifest: NormalizedSourceManifest

    @model_validator(mode="after")
    def digest_matches_embedded_manifest(self) -> SourceManifestBinding:
        actual = hashlib.sha256(_canonical_json_bytes(self.manifest)).hexdigest()
        if actual != self.sha256:
            raise ValueError(
                f"normalized source manifest digest mismatch: expected {self.sha256}, got {actual}"
            )
        return self


class QuantityValue(StrictModel):
    quantity: PositiveInt | None
    quantity_status: Literal["known", "unknown"]

    @model_validator(mode="after")
    def quantity_matches_status(self) -> QuantityValue:
        if (self.quantity_status == "known") != (self.quantity is not None):
            raise ValueError("known quantities require a positive value; unknown quantities require null")
        return self


class Output(QuantityValue):
    item_id: PositiveInt


class Reagent(QuantityValue):
    item_id: PositiveInt
    optional: bool


class SkillValue(StrictModel):
    value: NonNegativeInt | None
    status: Literal["known", "unknown"]

    @model_validator(mode="after")
    def value_matches_status(self) -> SkillValue:
        if (self.status == "known") != (self.value is not None):
            raise ValueError("known skill values require a nonnegative value; unknown values require null")
        return self


class SkillGate(StrictModel):
    minimum: SkillValue
    yellow: SkillValue
    green: SkillValue
    gray: SkillValue

    @model_validator(mode="after")
    def known_values_are_monotonic(self) -> SkillGate:
        known = [
            getattr(self, name).value for name in SKILL_THRESHOLDS if getattr(self, name).status == "known"
        ]
        if known != sorted(known):
            raise ValueError("known skill thresholds must be monotonic from minimum through gray")
        return self


class Learnability(StrictModel):
    status: Literal["confirmed_learnable", "client_file_only", "server_gated", "unknown", "not_learnable"]
    evidence_kind: Literal["server_observation", "displayed_client_data", "source_item", "unknown"]

    @model_validator(mode="after")
    def evidence_does_not_overstate_learnability(self) -> Learnability:
        if self.status == "confirmed_learnable" and self.evidence_kind != "server_observation":
            raise ValueError("confirmed learnability requires server-observation evidence")
        if self.status == "client_file_only" and self.evidence_kind != "displayed_client_data":
            raise ValueError("client-file-only learnability requires displayed client evidence")
        if self.evidence_kind == "displayed_client_data" and self.status not in {
            "client_file_only",
            "unknown",
        }:
            raise ValueError("displayed client data cannot confirm server learnability")
        return self


class Cooldown(StrictModel):
    status: Literal["none", "known", "unknown"]
    seconds: PositiveInt | None
    shared_group: str | None

    @model_validator(mode="after")
    def cooldown_matches_status(self) -> Cooldown:
        if self.status == "none" and (self.seconds is not None or self.shared_group is not None):
            raise ValueError("no cooldown requires null seconds and shared_group")
        if self.status == "known" and self.seconds is None:
            raise ValueError("known cooldown requires positive seconds")
        if self.status == "unknown" and (self.seconds is not None or self.shared_group is not None):
            raise ValueError("unknown cooldown requires null seconds and shared_group")
        return self


class Acquisition(StrictModel):
    kind: Literal["trainer", "recipe_item", "vendor", "drop", "quest", "profession_window", "unknown"]
    status: Literal["confirmed", "client_data_only", "unknown", "not_applicable"]
    requirement_ids: list[PositiveInt]
    conditions: list[str]

    @model_validator(mode="after")
    def acquisition_state_is_coherent(self) -> Acquisition:
        if self.status == "confirmed" and self.kind == "unknown":
            raise ValueError("confirmed acquisition requires a known kind")
        if any(not condition.strip() for condition in self.conditions):
            raise ValueError("acquisition conditions must be non-empty strings")
        return self


class VendorComponent(StrictModel):
    item_id: PositiveInt
    quantity: PositiveInt | None
    quantity_status: Literal["known", "unknown"]
    price_amount: PositiveInt | None
    price_status: Literal["known", "unknown"]
    currency: Literal["copper", "silver", "gold", "token", "unknown"]
    vendor_id: PositiveInt | None
    stock_status: Literal["known_limited", "known_unlimited", "unknown"]
    conditions: list[str]
    provenance_claim_ids: list[Identifier]

    @model_validator(mode="after")
    def component_statuses_match_values(self) -> VendorComponent:
        if (self.quantity_status == "known") != (self.quantity is not None):
            raise ValueError("vendor quantity status does not match quantity")
        if (self.price_status == "known") != (self.price_amount is not None):
            raise ValueError("vendor price status does not match price_amount")
        if any(not condition.strip() for condition in self.conditions):
            raise ValueError("vendor conditions must be non-empty strings")
        if self.provenance_claim_ids != sorted(set(self.provenance_claim_ids)):
            raise ValueError("vendor provenance_claim_ids must be sorted and unique")
        return self


class BindingAndTradeability(StrictModel):
    output_status: Literal["tradeable", "bind_on_pickup", "bind_on_equip", "unknown"]
    reagent_restrictions: list[str]

    @model_validator(mode="after")
    def restrictions_are_explicit(self) -> BindingAndTradeability:
        if any(not restriction.strip() for restriction in self.reagent_restrictions):
            raise ValueError("reagent restrictions must be non-empty strings")
        return self


class ProvenanceClaim(StrictModel):
    claim_id: Identifier
    manifest_entry_id: Identifier
    locator_id: Identifier
    field_paths: list[str]
    reviewer: str = Field(min_length=1)
    reviewed_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")

    @field_validator("reviewed_on")
    @classmethod
    def valid_review_date(cls, value: str) -> str:
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("reviewed_on must be a valid ISO date") from exc
        return value

    @model_validator(mode="after")
    def claim_paths_are_explicit(self) -> ProvenanceClaim:
        if not self.field_paths:
            raise ValueError("a provenance claim must bind at least one field path")
        _validate_field_paths(self.field_paths)
        return self


class Readiness(StrictModel):
    status: Literal["ready_for_recipe_review", "blocked"]
    codes: list[
        Literal[
            "RECIPE_ID_UNRESOLVED",
            "SOURCE_BUILD_MISMATCH",
            "OUTPUT_QUANTITY_UNKNOWN",
            "REAGENT_QUANTITY_UNKNOWN",
            "SKILL_GATE_UNKNOWN",
            "LEARNABILITY_NOT_CONFIRMED",
            "ACQUISITION_UNKNOWN",
            "COOLDOWN_UNKNOWN",
            "VENDOR_PRICE_UNKNOWN",
            "VENDOR_STOCK_UNKNOWN",
            "TRADEABILITY_UNKNOWN",
            "PROVENANCE_UNBOUND",
        ]
    ]

    @model_validator(mode="after")
    def codes_have_contract_order(self) -> Readiness:
        if self.codes != [code for code in REFUSAL_CODES if code in self.codes]:
            raise ValueError("readiness codes must be unique and in fixed contract order")
        if (self.status == "blocked") != bool(self.codes):
            raise ValueError("blocked readiness requires codes; ready readiness has no codes")
        return self


class RecipeRecord(StrictModel):
    record_id: Identifier
    recipe_id: PositiveInt | None
    profession: Literal[
        "alchemy",
        "blacksmithing",
        "cooking",
        "enchanting",
        "engineering",
        "first-aid",
        "leatherworking",
        "tailoring",
        "mining",
    ]
    profession_kind: Literal["crafting", "processing"]
    output: Output
    reagents: list[Reagent]
    skill_gate: SkillGate
    learnability: Learnability
    cooldown: Cooldown
    acquisition: Acquisition
    vendor_components: list[VendorComponent]
    binding_and_tradeability: BindingAndTradeability
    source_build: BuildString
    provenance_claims: list[ProvenanceClaim]
    unknowns: list[
        Literal[
            "recipe_id_unresolved",
            "output_quantity",
            "reagent_quantity",
            "skill_gate",
            "learnability_server_gate",
            "acquisition",
            "cooldown",
            "vendor_price",
            "vendor_stock",
            "item_binding",
            "source_build_mismatch",
            "provenance_unbound",
            "intermediate_recipe",
        ]
    ]
    readiness: Readiness
    review_status: Literal["draft", "blocked", "verified", "superseded"]
    superseded_by: Identifier | None

    @field_validator("unknowns")
    @classmethod
    def unknowns_are_sorted_unique(cls, value: list[str]) -> list[str]:
        if value != sorted(set(value)):
            raise ValueError("unknowns must be sorted and unique")
        return value

    @field_validator("provenance_claims")
    @classmethod
    def claims_are_sorted_unique(cls, value: list[ProvenanceClaim]) -> list[ProvenanceClaim]:
        ids = [claim.claim_id for claim in value]
        if ids != sorted(set(ids)):
            raise ValueError("provenance claims must be sorted by unique claim_id")
        return value

    @model_validator(mode="after")
    def record_invariants(self) -> RecipeRecord:
        if self.profession_kind != PROFESSION_KIND[self.profession]:
            raise ValueError("profession_kind does not match profession")
        if self.learnability.status == "client_file_only" and self.acquisition.status == "confirmed":
            raise ValueError("client-file-only candidates cannot have confirmed acquisition")
        reagent_keys = [(reagent.item_id, reagent.optional) for reagent in self.reagents]
        if len({reagent.item_id for reagent in self.reagents}) != len(self.reagents):
            raise ValueError("reagent item IDs must be unique within a record")
        if reagent_keys != sorted(reagent_keys):
            raise ValueError("reagents must be sorted by item_id and optionality")
        vendor_keys = [(component.item_id, component.vendor_id or 0) for component in self.vendor_components]
        if vendor_keys != sorted(vendor_keys):
            raise ValueError("vendor components must be sorted by item_id and vendor_id")
        if self.superseded_by == self.record_id:
            raise ValueError("a record cannot supersede itself")
        if self.review_status == "superseded" and self.superseded_by is None:
            raise ValueError("superseded records require superseded_by")
        if self.review_status != "superseded" and self.superseded_by is not None:
            raise ValueError("superseded_by is only valid for superseded records")
        if self.recipe_id is None and self.review_status not in {"draft", "blocked"}:
            raise ValueError("an unresolved recipe_id requires draft or blocked review_status")
        if self.review_status == "blocked" and self.readiness.status != "blocked":
            raise ValueError("blocked review_status requires blocked readiness")
        if self.review_status == "verified":
            if self.recipe_id is None or self.readiness.status != "ready_for_recipe_review" or self.unknowns:
                raise ValueError("verified records require resolved IDs, ready status, and no unknowns")
            if self.learnability.status != "confirmed_learnable":
                raise ValueError("verified records require confirmed learnability")
            if self.output.quantity_status != "known" or any(
                reagent.quantity_status != "known" for reagent in self.reagents
            ):
                raise ValueError("verified records require complete known quantities")
        return self


class RecipeFoundation(StrictModel):
    schema_version: Literal[1]
    catalog_id: Literal["forever-recipe-foundation"]
    revision: PositiveInt
    target_client_build: BuildString
    reviewed_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    source_manifest: SourceManifestBinding
    recipes: list[RecipeRecord]

    @field_validator("reviewed_on")
    @classmethod
    def valid_review_date(cls, value: str) -> str:
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("reviewed_on must be a valid ISO date") from exc
        return value

    @model_validator(mode="after")
    def catalog_invariants(self) -> RecipeFoundation:
        if self.source_manifest.manifest.target_client_build != self.target_client_build:
            raise ValueError("catalog and source manifest target builds must match")
        record_ids = [record.record_id for record in self.recipes]
        if record_ids != sorted(set(record_ids)):
            raise ValueError("recipes must be sorted by unique record_id")
        records = {record.record_id: record for record in self.recipes}
        for record in self.recipes:
            self._validate_record(record, records)
        return self

    def _validate_record(self, record: RecipeRecord, records: dict[str, RecipeRecord]) -> None:
        if record.superseded_by is not None and record.superseded_by not in records:
            raise ValueError(f"{record.record_id}: superseded_by must name another record")

        entries = {entry.entry_id: entry for entry in self.source_manifest.manifest.entries}
        locators = {
            entry_id: {locator.locator_id: locator for locator in entry.locators}
            for entry_id, entry in entries.items()
        }
        claims: dict[str, ProvenanceClaim] = {}
        covered_paths: set[str] = set()
        for claim in record.provenance_claims:
            entry = entries.get(claim.manifest_entry_id)
            if entry is None:
                raise ValueError(f"{record.record_id}: provenance references an unknown manifest entry")
            locator = locators[claim.manifest_entry_id].get(claim.locator_id)
            if locator is None:
                raise ValueError(f"{record.record_id}: provenance references an unknown locator")
            if not set(claim.field_paths) <= set(locator.field_paths):
                raise ValueError(f"{record.record_id}: claim uses a field path not permitted by its locator")
            claims[claim.claim_id] = claim
            covered_paths.update(claim.field_paths)
            if "/source_build" in claim.field_paths:
                if (
                    entry.claimed_build != record.source_build
                    or locator.expected_value != record.source_build
                ):
                    raise ValueError(
                        f"{record.record_id}: source_build claim does not match manifest evidence"
                    )

        if record.learnability.status == "confirmed_learnable":
            observation_entries = {
                claim.manifest_entry_id
                for claim in record.provenance_claims
                if "/learnability/status" in claim.field_paths
                and "/learnability/evidence_kind" in claim.field_paths
            }
            if not any(
                entries[entry_id].source_kind == "live_client_observation" for entry_id in observation_entries
            ):
                raise ValueError(f"{record.record_id}: confirmed learnability needs a live observation claim")

        for component_index, component in enumerate(record.vendor_components):
            if not component.provenance_claim_ids:
                raise ValueError(f"{record.record_id}: vendor component needs provenance_claim_ids")
            for claim_id in component.provenance_claim_ids:
                claim = claims.get(claim_id)
                if claim is None or not any(
                    path.startswith(f"/vendor_components/{component_index}/") for path in claim.field_paths
                ):
                    raise ValueError(f"{record.record_id}: vendor component references unrelated provenance")

        known_paths = _known_factual_paths(record)
        if covered_paths != known_paths:
            missing = sorted(known_paths - covered_paths)
            extra = sorted(covered_paths - known_paths)
            details = []
            if missing:
                details.append(f"missing claims for {missing}")
            if extra:
                details.append(f"claims bind non-factual paths {extra}")
            raise ValueError(f"{record.record_id}: " + "; ".join(details))

        expected_unknowns = derive_unknown_reasons(record, self.target_client_build)
        allowed_extra = {"intermediate_recipe"}
        if (
            not set(expected_unknowns) <= set(record.unknowns)
            or set(record.unknowns) - set(expected_unknowns) - allowed_extra
        ):
            raise ValueError(f"{record.record_id}: unknowns do not match unknown fields")
        expected_readiness = recipe_readiness(record, self.target_client_build)
        if record.readiness != expected_readiness:
            raise ValueError(f"{record.record_id}: readiness is not the deterministic recipe-side result")


class QuantityCoverage(TypedDict):
    known: int
    unknown: int
    total: int


class CoverageRow(TypedDict):
    profession: str
    profession_kind: str
    total_records: int
    verified: int
    blocked: int
    draft: int
    superseded: int
    target_build_compatibility: dict[str, int]
    output_quantity_coverage: QuantityCoverage
    reagent_quantity_coverage: QuantityCoverage
    skill_gate_coverage: dict[str, int]
    learnability_coverage: dict[str, int]
    cooldown_coverage: dict[str, int]
    acquisition_coverage: dict[str, int]
    vendor_price_coverage: QuantityCoverage
    vendor_stock_coverage: dict[str, int]
    tradeability_coverage: dict[str, int]
    unresolved_recipe_ids: list[str]
    blocking_reasons: dict[str, list[str]]
    first_run_overlap_item_ids: list[int]


class CoverageReport(TypedDict):
    target_client_build: str
    professions: list[CoverageRow]


def _known_factual_paths(record: RecipeRecord) -> set[str]:
    paths = {"/profession", "/source_build", "/output/item_id"}
    if record.recipe_id is not None:
        paths.add("/recipe_id")
    if record.output.quantity_status == "known":
        paths.add("/output/quantity")
    for index, reagent in enumerate(record.reagents):
        paths.update({f"/reagents/{index}/item_id", f"/reagents/{index}/optional"})
        if reagent.quantity_status == "known":
            paths.add(f"/reagents/{index}/quantity")
    for name in SKILL_THRESHOLDS:
        if getattr(record.skill_gate, name).status == "known":
            paths.add(f"/skill_gate/{name}")
    if record.learnability.status != "unknown":
        paths.add("/learnability/status")
    if record.learnability.evidence_kind != "unknown":
        paths.add("/learnability/evidence_kind")
    for index, condition in enumerate(record.acquisition.conditions):
        if condition:
            paths.add(f"/acquisition/conditions/{index}")
    for index, component in enumerate(record.vendor_components):
        base = f"/vendor_components/{index}"
        paths.add(f"{base}/item_id")
        if component.quantity_status == "known":
            paths.add(f"{base}/quantity")
        if component.price_status == "known":
            paths.add(f"{base}/price_amount")
        if component.currency != "unknown":
            paths.add(f"{base}/currency")
        if component.vendor_id is not None:
            paths.add(f"{base}/vendor_id")
        if component.stock_status != "unknown":
            paths.add(f"{base}/stock_status")
        for condition_index, condition in enumerate(component.conditions):
            if condition:
                paths.add(f"{base}/conditions/{condition_index}")
    if record.binding_and_tradeability.output_status != "unknown":
        paths.add("/binding_and_tradeability/output_status")
    for index, restriction in enumerate(record.binding_and_tradeability.reagent_restrictions):
        if restriction:
            paths.add(f"/binding_and_tradeability/reagent_restrictions/{index}")
    return paths


def derive_unknown_reasons(record: RecipeRecord, target_client_build: str) -> list[str]:
    reasons: set[str] = set()
    if record.recipe_id is None:
        reasons.add("recipe_id_unresolved")
    if record.output.quantity_status == "unknown":
        reasons.add("output_quantity")
    if any(reagent.quantity_status == "unknown" for reagent in record.reagents):
        reasons.add("reagent_quantity")
    if any(getattr(record.skill_gate, name).status == "unknown" for name in SKILL_THRESHOLDS):
        reasons.add("skill_gate")
    if record.learnability.status in {"client_file_only", "server_gated", "unknown"}:
        reasons.add("learnability_server_gate")
    if record.acquisition.status == "unknown":
        reasons.add("acquisition")
    if record.cooldown.status == "unknown":
        reasons.add("cooldown")
    if any(component.price_status == "unknown" for component in record.vendor_components):
        reasons.add("vendor_price")
    if any(component.stock_status == "unknown" for component in record.vendor_components):
        reasons.add("vendor_stock")
    if record.binding_and_tradeability.output_status == "unknown":
        reasons.add("item_binding")
    if record.source_build != target_client_build:
        reasons.add("source_build_mismatch")
    return sorted(reasons)


def recipe_readiness(record: RecipeRecord, target_client_build: str) -> Readiness:
    reasons = set(derive_unknown_reasons(record, target_client_build))
    codes: set[str] = set()
    if record.recipe_id is None:
        codes.add("RECIPE_ID_UNRESOLVED")
    if record.source_build != target_client_build:
        codes.add("SOURCE_BUILD_MISMATCH")
    if record.output.quantity_status == "unknown":
        codes.add("OUTPUT_QUANTITY_UNKNOWN")
    if any(reagent.quantity_status == "unknown" for reagent in record.reagents):
        codes.add("REAGENT_QUANTITY_UNKNOWN")
    if any(getattr(record.skill_gate, name).status == "unknown" for name in SKILL_THRESHOLDS):
        codes.add("SKILL_GATE_UNKNOWN")
    if record.learnability.status != "confirmed_learnable":
        codes.add("LEARNABILITY_NOT_CONFIRMED")
    if record.acquisition.status == "unknown":
        codes.add("ACQUISITION_UNKNOWN")
    if record.cooldown.status == "unknown":
        codes.add("COOLDOWN_UNKNOWN")
    if any(component.price_status == "unknown" for component in record.vendor_components):
        codes.add("VENDOR_PRICE_UNKNOWN")
    if any(component.stock_status == "unknown" for component in record.vendor_components):
        codes.add("VENDOR_STOCK_UNKNOWN")
    if record.binding_and_tradeability.output_status == "unknown":
        codes.add("TRADEABILITY_UNKNOWN")
    if "provenance_unbound" in reasons:
        codes.add("PROVENANCE_UNBOUND")
    ordered = [code for code in REFUSAL_CODES if code in codes]
    return Readiness(
        status="blocked" if ordered else "ready_for_recipe_review",
        codes=ordered,
    )


def validate_normalized_artifact(text: str) -> RecipeFoundation:
    """Validate packaged JSON and its embedded normalized manifest without archive access."""
    return RecipeFoundation.model_validate_json(text, strict=True)


def load_recipe_foundation() -> RecipeFoundation:
    """Load and strictly validate the packaged recipe foundation resource."""
    resource = resources.files("crowley.data").joinpath("recipe_foundation.json")
    return validate_normalized_artifact(resource.read_text(encoding="utf-8"))


def serialize_recipe_foundation(catalog: RecipeFoundation) -> str:
    """Return deterministic compact JSON for a previously validated catalog."""
    return json.dumps(
        catalog.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _quantity_coverage(known: int, total: int) -> QuantityCoverage:
    return {"known": known, "unknown": total - known, "total": total}


def coverage_report(
    catalog: RecipeFoundation,
    *,
    first_run_item_ids: set[int] | None = None,
) -> CoverageReport:
    """Build stable nine-profession coverage; first-run overlap is diagnostic only."""
    if first_run_item_ids is None:
        # This read is diagnostic only. It never creates recipe edges or alters the catalog.
        from crowley.core.watchlist import load_catalog

        first_run_item_ids = {item.item_id for item in load_catalog().items}

    rows: list[CoverageRow] = []
    for profession in PROFESSIONS:
        records = [record for record in catalog.recipes if record.profession == profession]
        review_counts = Counter(record.review_status for record in records)
        target_compatible = sum(record.source_build == catalog.target_client_build for record in records)
        output_known = sum(record.output.quantity_status == "known" for record in records)
        reagents = [reagent for record in records for reagent in record.reagents]
        reagent_known = sum(reagent.quantity_status == "known" for reagent in reagents)
        skill_total = len(records) * len(SKILL_THRESHOLDS)
        skill_known = sum(
            getattr(record.skill_gate, name).status == "known"
            for record in records
            for name in SKILL_THRESHOLDS
        )
        skill_complete = sum(
            all(getattr(record.skill_gate, name).status == "known" for name in SKILL_THRESHOLDS)
            for record in records
        )
        learnability_counts = Counter(record.learnability.status for record in records)
        cooldown_counts = Counter(record.cooldown.status for record in records)
        acquisition_counts = Counter(record.acquisition.status for record in records)
        components = [component for record in records for component in record.vendor_components]
        vendor_price_known = sum(component.price_status == "known" for component in components)
        vendor_stock_counts = Counter(component.stock_status for component in components)
        tradeability_counts = Counter(record.binding_and_tradeability.output_status for record in records)
        unresolved = sorted(record.record_id for record in records if record.recipe_id is None)
        blockers: dict[str, list[str]] = {}
        for code in REFUSAL_CODES:
            matched = sorted(record.record_id for record in records if code in record.readiness.codes)
            if matched:
                blockers[code] = matched
        item_ids = {
            item_id
            for record in records
            for item_id in [record.output.item_id, *(reagent.item_id for reagent in record.reagents)]
        }
        rows.append(
            {
                "profession": profession,
                "profession_kind": PROFESSION_KIND[profession],
                "total_records": len(records),
                "verified": review_counts["verified"],
                "blocked": review_counts["blocked"],
                "draft": review_counts["draft"],
                "superseded": review_counts["superseded"],
                "target_build_compatibility": {
                    "compatible": target_compatible,
                    "mismatched": len(records) - target_compatible,
                    "total": len(records),
                },
                "output_quantity_coverage": _quantity_coverage(output_known, len(records)),
                "reagent_quantity_coverage": _quantity_coverage(reagent_known, len(reagents)),
                "skill_gate_coverage": {
                    "known_values": skill_known,
                    "total_values": skill_total,
                    "complete_records": skill_complete,
                    "total_records": len(records),
                },
                "learnability_coverage": {
                    status: learnability_counts[status]
                    for status in (
                        "confirmed_learnable",
                        "client_file_only",
                        "server_gated",
                        "unknown",
                        "not_learnable",
                    )
                },
                "cooldown_coverage": {
                    status: cooldown_counts[status] for status in ("none", "known", "unknown")
                },
                "acquisition_coverage": {
                    status: acquisition_counts[status]
                    for status in ("confirmed", "client_data_only", "unknown", "not_applicable")
                },
                "vendor_price_coverage": _quantity_coverage(vendor_price_known, len(components)),
                "vendor_stock_coverage": {
                    status: vendor_stock_counts[status]
                    for status in ("known_limited", "known_unlimited", "unknown")
                }
                | {"total": len(components)},
                "tradeability_coverage": {
                    status: tradeability_counts[status]
                    for status in ("tradeable", "bind_on_pickup", "bind_on_equip", "unknown")
                },
                "unresolved_recipe_ids": unresolved,
                "blocking_reasons": blockers,
                "first_run_overlap_item_ids": sorted(item_ids & first_run_item_ids),
            }
        )
    return {"target_client_build": catalog.target_client_build, "professions": rows}


__all__ = [
    "CATALOG_ID",
    "PROFESSIONS",
    "REFUSAL_CODES",
    "RecipeFoundation",
    "RecipeRecord",
    "coverage_report",
    "load_recipe_foundation",
    "recipe_readiness",
    "serialize_recipe_foundation",
    "validate_normalized_artifact",
]
