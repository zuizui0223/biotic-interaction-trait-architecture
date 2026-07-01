from __future__ import annotations

from trait_architecture.theory_meta_validation import (
    build_validation_report,
    validate_part_i_run,
)


def config() -> dict[str, object]:
    return {
        "phenotype_and_regime_grid": {
            "attraction": [0.2, 0.8],
            "defence": [0.5],
            "assurance": [0.0],
            "pollinator_service": [0.2, 0.8],
            "floral_damage_pressure": [0.5],
        },
        "parameter_scenarios": [{"scenario_id": "one"}, {"scenario_id": "two"}],
        "functional_forms": [{"form_id": "linear"}, {"form_id": "saturating"}],
    }


def part_i_report() -> dict[str, object]:
    return {
        "case_count": 4,
        "evaluation_count": 16,
        "functional_form_summary_count": 8,
        "parameter_envelope_class_counts": {
            "structurally_robust": 0,
            "conditional_majority": 1,
            "mixed_or_sensitive": 3,
        },
    }


def direction_row(**overrides: str) -> dict[str, str]:
    row = {
        "route": "B_to_pollination",
        "trait_class": "chemical_barrier",
        "outcome_class": "pollinator_foraging_response",
        "design_class": "manipulation",
        "expected_effect_direction": "negative",
        "independent_clusters": "3",
        "positive_count": "0",
        "negative_count": "3",
        "mixed_count": "0",
        "null_count": "0",
        "not_reported_count": "0",
        "evaluable_direction_count": "3",
        "compatible_count": "3",
        "contradictory_count": "0",
        "compatible_fraction": "1.000000",
        "direction_map_status": "mostly_compatible_with_channel_assumption",
    }
    row.update(overrides)
    return row


def quantitative_row(**overrides: str) -> dict[str, str]:
    row = {
        "analysis_status": "insufficient_independent_clusters",
        "effect_count": "0",
        "independent_clusters": "0",
    }
    row.update(overrides)
    return row


def test_part_i_validation_reproduces_dimensions_from_declared_config() -> None:
    result = validate_part_i_run(config(), part_i_report())

    assert result["status"] == "reproduced"
    assert result["expected_dimensions"] == {
        "case_count": 4,
        "parameter_scenario_count": 2,
        "functional_form_count": 2,
        "evaluation_count": 16,
        "functional_form_summary_count": 8,
    }
    assert result["parameter_envelope_class_total"] == 4


def test_part_i_validation_marks_dimension_mismatch_without_hiding_it() -> None:
    wrong = dict(part_i_report())
    wrong["evaluation_count"] = 15

    result = validate_part_i_run(config(), wrong)

    assert result["status"] == "mismatch"
    assert result["mismatches"]["evaluation_count"] == {"expected": 16, "actual": 15}


def test_integrated_validation_keeps_direction_support_separate_from_calibration() -> None:
    report, checks = build_validation_report(
        part_i_config=config(),
        part_i_report=part_i_report(),
        direction_rows=[direction_row()],
        quantitative_rows=[quantitative_row()],
    )

    assert checks[0]["channel_validation_status"] == "directionally_consistent_in_restricted_stratum"
    assert checks[0]["parameter_calibration_status"] == "not_calibrated_from_direction_only_evidence"
    assert report["integrated_verdict"] == {
        "part_i_regime_map": "reproduced",
        "channel_sign_validation": "limited_restricted_support_only",
        "regime_level_empirical_validation": "not_evaluable_from_current_single-route_records",
        "parameter_magnitude_calibration": "not_ready",
        "prohibited_claims": [
            "No universal attraction–barrier sign is validated.",
            "No model mixed-partial regime is empirically estimated from the current records.",
            "No Part I parameter magnitude is calibrated from direction-only evidence.",
        ],
    }
    assert report["quantitative_meta_analysis"]["eligible_effect_count"] == 0
    assert report["quantitative_meta_analysis"]["pooled_strata_count"] == 0


def test_integrated_validation_preserves_contradictory_direction_stratum() -> None:
    report, checks = build_validation_report(
        part_i_config=config(),
        part_i_report=part_i_report(),
        direction_rows=[direction_row(
            route="A_to_pollination",
            expected_effect_direction="positive",
            positive_count="0",
            negative_count="3",
            compatible_count="0",
            contradictory_count="3",
            compatible_fraction="0.000000",
            direction_map_status="mostly_contradictory_to_channel_assumption",
        )],
        quantitative_rows=[quantitative_row()],
    )

    assert checks[0]["channel_validation_status"] == "directionally_contradictory_in_restricted_stratum"
    assert report["broad_direction_map"]["restricted_directional_contradiction_strata"] == 1
