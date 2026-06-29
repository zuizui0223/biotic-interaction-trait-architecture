from trait_architecture.effect_synthesis import synthesise_effect_registry


COLUMNS = [
    "effect_id", "study_id", "citation_or_doi", "plant_taxon", "study_context_id",
    "site_id", "sampling_period", "unit_of_analysis", "design_type", "trait_id",
    "trait_description", "trait_module", "trait_organ", "trait_scaling", "effect_role",
    "outcome_channel", "outcome_id", "outcome_description", "outcome_numerator",
    "outcome_denominator_or_exposure", "effect_measure", "effect_estimate", "effect_se",
    "effect_ci_lower", "effect_ci_upper", "effect_p_value", "model_family",
    "adjustment_set", "causal_status", "linkage_status", "raw_table_status",
    "parameter_bridge_status", "extraction_status", "notes",
]


def record(effect_id: str, **overrides: str) -> dict[str, str]:
    row = {column: "" for column in COLUMNS}
    row.update(
        {
            "effect_id": effect_id,
            "study_id": f"study_{effect_id}",
            "citation_or_doi": "10.example/test",
            "plant_taxon": "Example species",
            "study_context_id": "site_year",
            "site_id": "site",
            "sampling_period": "2026",
            "unit_of_analysis": "individual plant",
            "design_type": "manipulation",
            "trait_id": "display",
            "trait_description": "standardized floral display",
            "trait_module": "A_flower",
            "trait_organ": "flower",
            "trait_scaling": "z-score",
            "effect_role": "A_to_pollination",
            "outcome_channel": "pollination",
            "outcome_id": "pollen",
            "outcome_description": "pollen deposition",
            "outcome_numerator": "pollen grains",
            "outcome_denominator_or_exposure": "stigmas sampled",
            "effect_measure": "standardized_regression_slope",
            "effect_estimate": "0.2",
            "effect_se": "0.1",
            "effect_ci_lower": "",
            "effect_ci_upper": "",
            "effect_p_value": "0.05",
            "model_family": "gaussian",
            "adjustment_set": "site",
            "causal_status": "manipulated",
            "linkage_status": "individual",
            "raw_table_status": "repository",
            "parameter_bridge_status": "standardized_slope_ready",
            "extraction_status": "verified",
            "notes": "one primary effect for this study and stratum",
        }
    )
    row.update(overrides)
    return row


def test_two_independent_same_scale_effects_receive_random_effects_summary() -> None:
    summaries, warnings = synthesise_effect_registry(
        [record("one", effect_estimate="0.2", effect_se="0.1"), record("two", effect_estimate="0.4", effect_se="0.2")]
    )

    assert warnings == ()
    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.effect_role == "A_to_pollination"
    assert summary.parameter_target == "b_A"
    assert summary.n_effects == 2
    assert summary.n_studies == 2
    assert summary.synthesis_status == "summarised"
    assert 0.2 < summary.random_effect_estimate < 0.4


def test_multiple_effects_from_one_study_block_simple_independent_synthesis() -> None:
    summaries, warnings = synthesise_effect_registry(
        [record("one", study_id="shared"), record("two", study_id="shared", effect_estimate="0.4")]
    )

    assert warnings == ()
    assert summaries[0].synthesis_status == "blocked_study_dependence"
    assert "multiple records from one study" in summaries[0].notes


def test_different_effect_scales_are_not_pooled() -> None:
    summaries, warnings = synthesise_effect_registry(
        [record("slope"), record("odds", effect_measure="log_odds_ratio", effect_estimate="0.4")]
    )

    assert len(summaries) == 2
    assert {summary.effect_measure for summary in summaries} == {
        "standardized_regression_slope",
        "log_odds_ratio",
    }
    assert all(summary.synthesis_status == "single_effect_no_between_study_inference" for summary in summaries)


def test_ratio_without_explicit_log_scale_is_not_silently_transformed() -> None:
    summaries, warnings = synthesise_effect_registry(
        [record("ratio", effect_measure="rate_ratio", effect_estimate="1.5")]
    )

    assert summaries == ()
    assert any("retained in registry but not pooled" in warning for warning in warnings)
