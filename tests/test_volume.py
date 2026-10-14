from __future__ import annotations

import pytest

from crowley.core.volume import compare_observations, project_observation_variant, volume_report


def _row(
    result_id: int,
    quantity: int,
    *,
    price: tuple[int, int] = (100, 1),
    identity: str = "individual",
    seconds: int | None = 10_000,
    key: str = "1",
) -> dict:
    return {
        "resultID": result_id,
        "itemID": 1,
        "itemKey": key,
        "rawItemKey": {"itemID": 1, "itemLevel": 0, "itemSuffix": 0, "battlePetSpeciesID": 0, "bonusIDs": {}},
        "quantity": quantity,
        "unitPrice": {"numerator": price[0], "denominator": price[1]},
        "owners": {
            "names": {"Seller": True} if identity == "individual" else {},
            "totalNumberOfOwners": 1 if identity == "individual" else 0,
            "containsOwnerItem": False,
            "containsAccountItem": False,
            "identityKind": identity,
        },
        "timeLeft": {"kind": "exact", "seconds": seconds} if seconds is not None else {"kind": "unknown"},
    }


def _obs(start: int, rows: list[dict], *, kind: str = "item", coverage: str = "full") -> dict:
    return {
        "itemID": 1,
        "ordinal": 1,
        "kind": kind,
        "query": {"kind": "queried", "startedAt": start, "finishedAt": start + 10},
        "coverage": coverage,
        "sourceComplete": True,
        "cutoff": {"kind": "unbounded"},
        "higherPriceWitness": {"kind": "unknown"},
        "reasonCode": "ok",
        "rowCount": len(rows),
        "rows": {f"row:{i}": row for i, row in enumerate(rows, 1)},
    }


def test_individual_removal_is_unexpired_candidate():
    result = compare_observations(_obs(100, [_row(7, 3)]), _obs(110, []))
    assert result["valid"]
    assert result["observedIndividualRemovedUnits"] == 3
    assert result["eligibleIndividualSaleCandidateUnits"] == 3
    assert result["expirationPossibleUnits"] == 0


def test_grouped_scope_disables_individual_inference():
    before = _obs(100, [_row(7, 3, identity="grouped")])
    after = _obs(110, [_row(8, 3, identity="grouped")])
    result = compare_observations(before, after)
    assert result["groupedScope"]
    assert result["observedIndividualRemovedUnits"] == 0


def test_quantity_change_is_inconsistent_and_unknown_time_left_is_not_sale():
    before = _obs(100, [_row(7, 3, seconds=None)])
    after = _obs(110, [_row(7, 2, seconds=None)])
    result = compare_observations(before, after)
    assert result["inconsistentUnits"] == 3
    assert result["timeLeftUnknownUnits"] == 0


def test_commodity_fractional_price_buckets_report_churn():
    before = _obs(100, [_row(1, 5, price=(1, 2))], kind="commodity")
    after = _obs(110, [_row(2, 2, price=(1, 2))], kind="commodity")
    result = compare_observations(before, after)
    assert result["commodityDepletionUnits"] == 3
    assert result["aggregateCommodityChurnUnits"] == 3


def test_commodity_bounded_prefix_can_have_incomplete_source():
    before = _obs(100, [_row(1, 5, price=(1, 2))], kind="commodity", coverage="bounded")
    after = _obs(110, [_row(2, 2, price=(1, 2))], kind="commodity", coverage="bounded")
    for observation in (before, after):
        observation["sourceComplete"] = False
        observation["cutoff"] = {"kind": "price", "numerator": 1, "denominator": 2}
        observation["higherPriceWitness"] = {"kind": "known", "numerator": 2, "denominator": 1}
    result = compare_observations(before, after)
    assert result["valid"] and result["commonPriceScope"] == {"numerator": 1, "denominator": 2}


def test_failed_intervening_sample_does_not_create_zero_rate():
    first = _obs(100, [_row(7, 1)])
    failed = {
        **_obs(110, []),
        "coverage": "incomplete",
        "sourceComplete": False,
        "reasonCode": "query_timeout",
    }
    last = _obs(120, [])
    report = volume_report([last, failed, first], hours=1, end=130)
    assert report["saleCandidateUnitsPerHour"] is None
    assert "incomplete_observation" in report["excludedIntervals"]


def test_metadata_change_excludes_interval():
    left = {
        "observation": _obs(100, [_row(7, 1)]),
        "envelope": {
            "house": {"key": "us-normal-horde"},
            "context": {"clientVersion": "1", "clientBuild": "a"},
            "planHash": "a",
        },
    }
    right = {
        "observation": _obs(110, []),
        "envelope": {
            "house": {"key": "us-normal-horde"},
            "context": {"clientVersion": "1", "clientBuild": "b"},
            "planHash": "a",
        },
    }
    assert "client_build_changed" in compare_observations(left, right)["excludedIntervals"]


def test_persistent_id_change_outside_common_cutoff_is_inconsistent():
    before = _obs(100, [_row(7, 3, price=(100, 1))], coverage="bounded")
    before["cutoff"] = {"kind": "price", "numerator": 100, "denominator": 1}
    before["higherPriceWitness"] = {"kind": "known", "numerator": 200, "denominator": 1}
    current = _obs(120, [_row(7, 3, price=(200, 1))])
    result = compare_observations(before, current)
    assert result["inconsistentUnits"] == 3
    assert result["eligibleIndividualSaleCandidateUnits"] is None


def test_exposure_uses_query_end_delta_and_expiry_uses_maximum_gap():
    before = _obs(100, [_row(7, 3, seconds=25)])
    current = _obs(120, [])
    result = compare_observations(before, current)
    assert result["comparedSeconds"] == 20
    assert result["expiryGapSeconds"] == 30
    assert result["expirationPossibleUnits"] == 3
    assert result["eligibleIndividualSaleCandidateUnits"] == 0


def test_variant_projection_keeps_whole_scope_grouping_guard():
    before = _obs(100, [_row(7, 3, key="1:l2"), _row(9, 2, identity="grouped", key="1:l3")])
    current = _obs(110, [_row(9, 2, identity="grouped", key="1:l3")])
    result = compare_observations(before, current, item_key="1:l2")
    assert result["groupedScope"]
    assert result["saleCandidateUnitsPerHour"] is None
    assert result["eligibleIndividualSaleCandidateUnits"] is None


def test_report_uses_whole_intervals_and_latest_independent_of_window():
    first = _obs(100, [_row(7, 1)])
    second = _obs(120, [])
    records = [
        {"observation": first, "envelope": {"startedAt": 100, "finishedAt": 110}},
        {"observation": second, "envelope": {"startedAt": 120, "finishedAt": 130}},
    ]
    report = volume_report(records, hours=1, end=115)
    assert report["latestObservation"] is second
    assert len(report["intervals"]) == 1
    assert "outside_window" in report["intervals"][0]["excludedIntervals"]
    assert report["freshness"] == -15


def test_report_projects_requested_variant_after_comparison_scope_checks():
    first = _obs(100, [_row(7, 1, key="1:l2"), _row(8, 2, identity="grouped", key="1:l3")])
    second = _obs(110, [_row(8, 2, identity="grouped", key="1:l3")])
    records = [
        {
            "observation": first,
            "envelope": {"startedAt": 100, "finishedAt": 110, "itemKey": "1:l2"},
        },
        {
            "observation": second,
            "envelope": {"startedAt": 110, "finishedAt": 120, "itemKey": "1:l2"},
        },
    ]
    report = volume_report(records, hours=1, end=120, item_key="1:l2")
    assert report["latestObservation"]["rowCount"] == 0
    assert report["intervals"][0]["groupedScope"]


def test_report_accepts_prior_query_start_outside_window_when_ends_are_contained():
    first = _obs(6000, [_row(7, 1)])
    first["query"]["finishedAt"] = 7000
    second = _obs(7000, [])
    second["query"]["finishedAt"] = 7100
    report = volume_report([first, second], hours=1, end=7100)
    assert report["intervals"][0]["valid"]
    assert report["intervals"][0]["comparedSeconds"] == 100


def test_report_keeps_failed_intervening_record_outside_window_from_being_skipped():
    first = _obs(6990, [_row(7, 1)])
    first["query"]["finishedAt"] = 7000
    failed = {
        **_obs(5000, []),
        "query": {"kind": "unqueried"},
        "kind": "unknown",
        "coverage": "unqueried",
        "sourceComplete": False,
        "cutoff": {"kind": "unknown"},
        "higherPriceWitness": {"kind": "unknown"},
        "reasonCode": "logout",
    }
    second = _obs(7000, [])
    second["query"]["finishedAt"] = 7100
    records = [
        {"observation": first, "envelope": {"startedAt": 6990, "finishedAt": 7000}},
        {"observation": failed, "envelope": {"startedAt": 7001, "finishedAt": 3000}},
        {"observation": second, "envelope": {"startedAt": 7010, "finishedAt": 7100}},
    ]
    report = volume_report(records, hours=1, end=7100)
    assert len(report["intervals"]) == 2
    assert all(not interval["valid"] for interval in report["intervals"])
    assert all("outside_window" in interval["excludedIntervals"] for interval in report["intervals"])


def test_freshness_uses_actual_query_end_when_sweep_finishes_later():
    observation = _obs(7000, [])
    observation["query"]["finishedAt"] = 7010
    report = volume_report(
        [{"observation": observation, "envelope": {"startedAt": 7000, "finishedAt": 8000}}],
        hours=1,
        end=8000,
    )
    assert report["freshness"] == 990


def test_commodity_rates_use_commodity_exposure_and_aggregate_intervals():
    first = _obs(7000, [_row(1, 5, price=(1, 2))], kind="commodity")
    second = _obs(7010, [_row(2, 2, price=(1, 2))], kind="commodity")
    third = _obs(7020, [_row(3, 4, price=(1, 2))], kind="commodity")
    report = volume_report([third, first, second], hours=1, end=7030)
    assert report["commodityDepletionUnits"] == 3
    assert report["commodityReplenishmentUnits"] == 2
    assert report["commodityExposureSeconds"] == 20
    assert report["commodityDepletionUnitsPerHour"] == 540
    assert report["commodityReplenishmentUnitsPerHour"] == 360
    assert report["saleCandidateUnitsPerHour"] is None


def test_grouped_interval_is_excluded_from_individual_rate_exposure():
    first = _obs(7000, [_row(7, 2)])
    second = _obs(7010, [])
    third = _obs(7020, [_row(8, 2, identity="grouped")])
    report = volume_report([third, first, second], hours=1, end=7030)
    assert report["individualExposureSeconds"] == 10
    assert report["individualRateDenominatorHours"] == 10 / 3600
    assert report["eligibleIndividualSaleCandidateUnits"] == 2
    assert report["saleCandidateUnitsPerHour"] == 720


@pytest.mark.parametrize(
    ("before_key", "after_key"),
    [("requested", "other"), ("other", "requested")],
)
def test_persistent_id_variant_transition_counts_requested_units_as_unknown(before_key: str, after_key: str):
    before = _obs(100, [_row(7, 3, key=before_key)])
    after = _obs(110, [_row(7, 3, key=after_key)])
    result = compare_observations(before, after, item_key="requested")
    assert result["inconsistentUnits"] == 3
    assert result["unknownUnits"] == 3
    assert result["observedIndividualRemovedUnits"] == 0
    assert result["observedIndividualAddedUnits"] == 0
    assert result["eligibleIndividualSaleCandidateUnits"] is None


def test_variant_projection_does_not_mutate_source_rows():
    observation = _obs(100, [_row(7, 3, key="requested")])
    projected = project_observation_variant(observation, "requested")
    projected["rows"]["row:1"]["quantity"] = 99
    assert observation["rows"]["row:1"]["quantity"] == 3


def test_variant_projection_filters_after_numeric_row_ordering():
    observation = _obs(100, [])
    all_rows = {
        f"row:{index}": _row(
            index, index, price=(index, 1), key="requested" if index in {1, 2, 10} else "other"
        )
        for index in range(1, 13)
    }
    shuffled_rows = {
        key: all_rows[key]
        for key in ["row:1", "row:10", *[f"row:{i}" for i in range(2, 10)], "row:11", "row:12"]
    }
    observation["rows"] = shuffled_rows
    observation["rowCount"] = len(shuffled_rows)

    projected = project_observation_variant(observation, "requested")

    assert list(projected["rows"]) == ["row:1", "row:2", "row:3"]
    assert [row["unitPrice"]["numerator"] for row in projected["rows"].values()] == [1, 2, 10]
    assert list(observation["rows"]) == list(shuffled_rows)
