import pytest

from trait_architecture.model import ModelParameters
from trait_architecture.stability import (
    AssociationSign,
    ParameterScenario,
    StabilityStatus,
    assess_sign_stability,
    canonical_scenarios,
    summarise_scenario,
)


GRID = dict(
    pollinator_service=(0.0, 0.5, 1.0),
    floral_damage_pressure=(0.0, 0.5, 1.0),
    leaf_consumer_pressure=(0.0, 1.0),
    resolution=7,
)


def test_costly_defence_scenario_has_negative_ad_association() -> None:
    scenario = ParameterScenario(
        "costly",
        ModelParameters(
            defence_pollinator_cost=1.25,
            floral_defence_efficacy=0.45,
            leaf_defence_efficacy=0.45,
        ),
    )
    result = summarise_scenario(scenario, **GRID)
    assert result.sign is AssociationSign.NEGATIVE
    assert result.covariance is not None and result.covariance < 0


def test_guarded_attraction_scenario_has_positive_ad_association() -> None:
    scenario = ParameterScenario(
        "guarded",
        ModelParameters(
            defence_pollinator_cost=0.05,
            attraction_tracking=1.75,
            floral_defence_efficacy=0.95,
            leaf_defence_efficacy=0.95,
        ),
    )
    result = summarise_scenario(scenario, **GRID)
    assert result.sign is AssociationSign.POSITIVE
    assert result.covariance is not None and result.covariance > 0


def test_contrasting_scenarios_produce_mixed_sign_stability() -> None:
    report = assess_sign_stability(
        canonical_scenarios()[:3],
        **GRID,
    )
    assert report.status is StabilityStatus.MIXED
    assert report.sign_counts[AssociationSign.NEGATIVE] >= 1
    assert report.sign_counts[AssociationSign.POSITIVE] >= 1


def test_single_consistent_scenario_is_stably_negative() -> None:
    scenario = ParameterScenario(
        "costly",
        ModelParameters(defence_pollinator_cost=1.25),
    )
    report = assess_sign_stability((scenario,), **GRID)
    assert report.status is StabilityStatus.STABLY_NEGATIVE


def test_duplicate_scenario_ids_are_rejected() -> None:
    scenario = ParameterScenario("same", ModelParameters())
    with pytest.raises(ValueError, match="unique"):
        assess_sign_stability((scenario, scenario), **GRID)


def test_empty_scenario_collection_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one"):
        assess_sign_stability((), **GRID)
