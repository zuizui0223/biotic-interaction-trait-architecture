from trait_architecture.parameter_envelopes import (
    readiness_report_to_dict,
    ready_parameter_overrides,
    validate_contracts,
)


def contract(target: str, role: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "contract_id": f"contract_{target}",
        "target_parameter": target,
        "effect_role": role,
        "effect_measure": "standardized_regression_slope",
        "causal_status": "manipulated",
        "calibration_status": "calibrated_envelope",
        "proxy_justification": "Declared direct floral outcome proxy.",
        "source_selector": "role-scale-causal stratum v1",
        "low": 0.1,
        "mid": 0.2,
        "high": 0.3,
    }
    row.update(overrides)
    return row


def summary(role: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "effect_role": role,
        "effect_measure": "standardized_regression_slope",
        "causal_status": "manipulated",
        "synthesis_status": "summarised",
    }
    row.update(overrides)
    return row


def all_contracts() -> dict[str, object]:
    return {
        "contracts": [
            contract("attraction_gain", "A_to_pollination"),
            contract("attraction_tracking", "A_to_antagonism"),
            contract("floral_defence_efficacy", "B_to_antagonism", low=0.2, mid=0.5, high=0.8),
            contract("defence_pollinator_cost", "B_to_pollination"),
        ]
    }


def all_summaries() -> list[dict[str, object]]:
    return [
        summary("A_to_pollination"),
        summary("A_to_antagonism"),
        summary("B_to_antagonism"),
        summary("B_to_pollination"),
    ]


def test_calibrated_contracts_with_matching_summaries_are_ready() -> None:
    payload = all_contracts()
    readiness = validate_contracts(payload, all_summaries())

    assert all(item.ready_for_empirical_sweep for item in readiness)
    overrides = ready_parameter_overrides(payload, readiness)
    assert overrides["low"] == {
        "attraction_gain": 0.1,
        "attraction_tracking": 0.1,
        "floral_defence_efficacy": 0.2,
        "defence_pollinator_cost": 0.1,
    }
    assert readiness_report_to_dict(readiness)["all_channels_ready"] is True


def test_missing_synthesis_summary_blocks_calibrated_contract() -> None:
    readiness = validate_contracts(all_contracts(), all_summaries()[:-1])
    blocked = [item for item in readiness if item.target_parameter == "defence_pollinator_cost"][0]

    assert blocked.ready_for_empirical_sweep is False
    assert "no compatible synthesised effect stratum found" in blocked.warnings


def test_out_of_bounds_defence_efficacy_blocks_contract() -> None:
    payload = all_contracts()
    payload["contracts"][2]["high"] = 1.2
    readiness = validate_contracts(payload, all_summaries())
    blocked = [item for item in readiness if item.target_parameter == "floral_defence_efficacy"][0]

    assert blocked.ready_for_empirical_sweep is False
    assert "floral_defence_efficacy envelope must lie in [0,1]" in blocked.warnings


def test_awaiting_synthesis_never_becomes_ready_just_because_a_summary_exists() -> None:
    payload = all_contracts()
    payload["contracts"][0]["calibration_status"] = "awaiting_synthesis"
    readiness = validate_contracts(payload, all_summaries())
    first = [item for item in readiness if item.target_parameter == "attraction_gain"][0]

    assert first.matching_summary_found is True
    assert first.ready_for_empirical_sweep is False
