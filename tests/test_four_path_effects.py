from trait_architecture.four_path_effects import audit_effect_registry


COLUMNS = [
    "effect_id",
    "study_id",
    "citation_or_doi",
    "plant_taxon",
    "study_context_id",
    "site_id",
    "sampling_period",
    "unit_of_analysis",
    "design_type",
    "trait_id",
    "trait_description",
    "trait_module",
    "trait_organ",
    "trait_scaling",
    "effect_role",
    "outcome_channel",
    "outcome_id",
    "outcome_description",
    "outcome_numerator",
    "outcome_denominator_or_exposure",
    "effect_measure",
    "effect_estimate",
    "effect_se",
    "effect_ci_lower",
    "effect_ci_upper",
    "effect_p_value",
    "model_family",
    "adjustment_set",
    "causal_status",
    "linkage_status",
    "raw_table_status",
    "parameter_bridge_status",
    "extraction_status",
    "notes",
]


def record(effect_id: str, **overrides: str) -> dict[str, str]:
    row = {column: "" for column in COLUMNS}
    row.update(
        {
            "effect_id": effect_id,
            "study_id": "Study_2026",
            "citation_or_doi": "10.example/test",
            "plant_taxon": "Example species",
            "study_context_id": "site_year_1",
            "site_id": "site_1",
            "sampling_period": "2026-05",
            "unit_of_analysis": "individual plant",
            "design_type": "manipulation",
            "trait_id": "flower_size",
            "trait_description": "standardized floral display area",
            "trait_module": "A_flower",
            "trait_organ": "flower",
            "trait_scaling": "z-scored within study",
            "effect_role": "A_to_pollination",
            "outcome_channel": "pollination",
            "outcome_id": "pollen_deposition",
            "outcome_description": "conspecific pollen grains deposited",
            "outcome_numerator": "pollen grains",
            "outcome_denominator_or_exposure": "stigmas sampled",
            "effect_measure": "standardized_regression_slope",
            "effect_estimate": "0.25",
            "effect_se": "0.08",
            "effect_ci_lower": "",
            "effect_ci_upper": "",
            "effect_p_value": "0.01",
            "model_family": "negative_binomial",
            "adjustment_set": "site and flowering date",
            "causal_status": "manipulated",
            "linkage_status": "individual",
            "raw_table_status": "repository",
            "parameter_bridge_status": "standardized_slope_ready",
            "extraction_status": "verified",
            "notes": "Trait and outcome measured on the declared plant-level unit.",
        }
    )
    row.update(overrides)
    return row


def test_valid_A_to_pollination_effect_is_analysis_and_bridge_ready() -> None:
    report = audit_effect_registry([record("effect_1")])
    summary = report.summaries[0]

    assert summary.effect_role == "A_to_pollination"
    assert summary.parameter_target == "b_A"
    assert summary.analysis_ready is True
    assert summary.bridge_ready is True
    assert summary.warnings == ()


def test_role_mismatch_is_rejected_even_with_a_numeric_effect() -> None:
    report = audit_effect_registry(
        [record("mismatch", effect_role="B_to_antagonism", trait_module="A_flower")]
    )
    summary = report.summaries[0]

    assert summary.analysis_ready is False
    assert "effect_role requires trait_module=B_flower." in summary.warnings


def test_missing_denominator_prevents_analysis_readiness() -> None:
    report = audit_effect_registry([record("no_denom", outcome_denominator_or_exposure="")])
    summary = report.summaries[0]

    assert summary.analysis_ready is False
    assert "missing outcome_denominator_or_exposure" in summary.warnings


def test_uncertainty_requires_se_or_ordered_interval() -> None:
    report = audit_effect_registry([record("no_uncertainty", effect_se="")])
    summary = report.summaries[0]

    assert summary.analysis_ready is False
    assert "missing effect uncertainty (SE or ordered confidence interval)" in summary.warnings


def test_nonrecoverable_effect_can_be_descriptive_but_not_analysis_ready() -> None:
    report = audit_effect_registry(
        [record("narrative", raw_table_status="not_available", parameter_bridge_status="scale_specific_only")]
    )
    summary = report.summaries[0]

    assert summary.analysis_ready is False
    assert summary.bridge_ready is False
    assert "raw_table_status is not recoverable" in summary.warnings


def test_audit_reports_role_counts_and_duplicate_ids() -> None:
    report = audit_effect_registry([record("duplicate"), record("duplicate")])

    assert report.invalid_records == 1
    assert report.counts_by_role == {"A_to_pollination": 1}
    assert report.bridge_ready_counts_by_role == {"A_to_pollination": 1}
