from __future__ import annotations

import math

import pytest

from trait_architecture.broad_meta_analysis import (
    ORIENTATION,
    direction_map,
    effect_estimate,
    meta_analysis,
    validate_effect_rows,
)


def route_record(**overrides: str) -> dict[str, str]:
    row = {
        "record_id": "record-1",
        "study_id": "study-1",
        "study_cluster_id": "cluster-1",
        "doi": "10.1/example",
        "taxon": "Example plant",
        "route": "A_to_pollination",
        "trait_role": "A",
        "trait_class": "visual_signal",
        "outcome_class": "visitation_rate",
        "design_class": "observational",
        "source_basis": "abstract_and_fulltext",
        "reported_direction": "positive",
        "is_primary_sign_record": "true",
        "record_status": "included_for_direction_map",
        "context_note": "",
        "coder_id": "tester",
        "coding_date": "2026-07-01",
    }
    row.update(overrides)
    return row


def direct_effect(**overrides: str) -> dict[str, str]:
    row = {
        "effect_id": "effect-1",
        "study_id": "study-1",
        "study_cluster_id": "cluster-1",
        "doi": "10.1/example",
        "taxon": "Example plant",
        "route": "A_to_pollination",
        "trait_role": "A",
        "trait_class": "visual_signal",
        "outcome_class": "visitation_rate",
        "design_class": "observational",
        "effect_input_type": "reported_effect",
        "effect_metric": "log_response_ratio",
        "effect_value": "0.2",
        "standard_error": "0.1",
        "n_treatment": "",
        "n_control": "",
        "mean_treatment": "",
        "sd_treatment": "",
        "mean_control": "",
        "sd_control": "",
        "event_treatment": "",
        "non_event_treatment": "",
        "event_control": "",
        "non_event_control": "",
        "correlation_r": "",
        "n_total": "",
        "effect_orientation": ORIENTATION,
        "is_primary_effect": "true",
        "analysis_status": "eligible_for_quantitative_synthesis",
        "source_basis": "public_fulltext",
        "source_locator": "Table 1",
        "extraction_note": "",
    }
    row.update(overrides)
    return row


def stratum(**overrides: str) -> dict[str, str]:
    row = {
        "stratum_id": "AP_visual_visitation_lrr_observational",
        "route": "A_to_pollination",
        "trait_class": "visual_signal",
        "outcome_class": "visitation_rate",
        "effect_metric": "log_response_ratio",
        "design_class": "observational",
        "min_clusters_exploratory": "3",
        "min_clusters_stability": "5",
        "expected_effect_direction": "positive",
        "part_i_parameter": "b_A",
        "interpretation": "test",
    }
    row.update(overrides)
    return row


def test_direction_map_uses_independent_cluster_primary_records_only() -> None:
    rows = [
        route_record(record_id=f"record-{index}", study_id=f"study-{index}", study_cluster_id=f"cluster-{index}", reported_direction="positive")
        for index in range(1, 5)
    ] + [route_record(record_id="record-5", study_id="study-5", study_cluster_id="cluster-5", reported_direction="negative")]

    output = direction_map(rows)

    assert len(output) == 1
    result = output[0]
    assert result["independent_clusters"] == 5
    assert result["compatible_count"] == 4
    assert result["contradictory_count"] == 1
    assert result["direction_map_status"] == "mostly_compatible_with_channel_assumption"


def test_direction_map_rejects_two_primary_records_for_same_cluster_stratum() -> None:
    rows = [route_record(), route_record(record_id="record-2", reported_direction="negative")]

    with pytest.raises(ValueError, match="more than one primary sign record"):
        direction_map(rows)


def test_effect_conversions_recover_lrr_log_or_and_fisher_z() -> None:
    lrr = effect_estimate(direct_effect(
        effect_id="lrr",
        effect_input_type="group_means",
        effect_metric="log_response_ratio",
        effect_value="",
        standard_error="",
        n_treatment="20", n_control="20", mean_treatment="4", sd_treatment="1",
        mean_control="2", sd_control="1",
    ))
    assert math.isclose(lrr.value, math.log(2), rel_tol=1e-10)
    assert lrr.standard_error > 0

    log_or = effect_estimate(direct_effect(
        effect_id="or",
        effect_input_type="two_by_two",
        effect_metric="log_odds_ratio",
        effect_value="", standard_error="",
        event_treatment="20", non_event_treatment="10", event_control="10", non_event_control="20",
    ))
    assert math.isclose(log_or.value, math.log(4), rel_tol=1e-10)

    fisher = effect_estimate(direct_effect(
        effect_id="cor", effect_input_type="correlation", effect_metric="fisher_z",
        effect_value="", standard_error="", correlation_r="0.5", n_total="23",
    ))
    assert math.isclose(fisher.value, math.atanh(0.5), rel_tol=1e-10)
    assert math.isclose(fisher.standard_error, 1 / math.sqrt(20), rel_tol=1e-10)


def test_meta_analysis_pools_only_predeclared_compatible_cluster_effects() -> None:
    effects = [
        direct_effect(effect_id="effect-1", study_cluster_id="cluster-1", effect_value="0.20"),
        direct_effect(effect_id="effect-2", study_id="study-2", study_cluster_id="cluster-2", effect_value="0.25"),
        direct_effect(effect_id="effect-3", study_id="study-3", study_cluster_id="cluster-3", effect_value="0.15"),
        direct_effect(effect_id="wrong-stratum", study_id="study-4", study_cluster_id="cluster-4", trait_class="scent", effect_value="-0.9"),
    ]
    summaries, used, diagnostics = meta_analysis(effects, [stratum()])

    assert diagnostics["pooled_stratum_count"] == 1
    assert len(used) == 3
    summary = summaries[0]
    assert summary["analysis_status"] == "exploratory_random_effects"
    assert summary["independent_clusters"] == 3
    assert float(summary["pooled_effect"]) > 0
    assert summary["channel_assumption_comparison"] == "compatible_with_channel_assumption"


def test_meta_analysis_does_not_pool_two_cluster_stratum() -> None:
    effects = [
        direct_effect(effect_id="effect-1", study_cluster_id="cluster-1"),
        direct_effect(effect_id="effect-2", study_id="study-2", study_cluster_id="cluster-2"),
    ]
    summaries, used, diagnostics = meta_analysis(effects, [stratum()])

    assert summaries[0]["analysis_status"] == "insufficient_independent_clusters"
    assert used == []
    assert diagnostics["pooled_stratum_count"] == 0


def test_effect_validator_rejects_wrong_barrier_role_or_orientation() -> None:
    bad_role = direct_effect(
        route="B_to_antagonism", trait_role="A", trait_class="chemical_barrier",
        outcome_class="florivore_abundance", design_class="manipulation",
    )
    with pytest.raises(ValueError, match="trait role inconsistent"):
        validate_effect_rows([bad_role])

    bad_orientation = direct_effect(effect_orientation="unoriented")
    with pytest.raises(ValueError, match="not explicitly oriented"):
        validate_effect_rows([bad_orientation])
