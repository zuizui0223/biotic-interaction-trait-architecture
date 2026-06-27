"""Sensitivity analysis for qualitative trait-architecture regime maps.

The first regime-map core returns an optimum for one declared parameter vector.
This module asks a stricter question: across a finite collection of parameter
scenarios, is the association between attraction and defence among regime optima
consistently positive, consistently negative, mixed, or uninformative?

The result is a stability summary over *declared scenarios*, not a posterior
probability over natural systems. It is designed to prevent a single default
parameterisation from being reported as a general prediction.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import product
from math import sqrt
from typing import Iterable, Mapping

from .model import InteractionRegime, ModelParameters
from .regime_map import RegimeOptimum, sweep_regimes


class AssociationSign(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    ZERO = "zero"
    UNDEFINED = "undefined"


class StabilityStatus(str, Enum):
    STABLY_POSITIVE = "stably_positive"
    STABLY_NEGATIVE = "stably_negative"
    STABLY_ZERO = "stably_zero"
    MIXED = "mixed"
    INSUFFICIENT = "insufficient"


@dataclass(frozen=True)
class ParameterScenario:
    """One named, fully declared qualitative parameterisation."""

    scenario_id: str
    parameters: ModelParameters
    description: str = ""

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("scenario_id must be non-empty")


@dataclass(frozen=True)
class AssociationSummary:
    """Attraction-defence association across optima from one scenario."""

    scenario_id: str
    n_optima: int
    covariance: float | None
    correlation: float | None
    sign: AssociationSign
    strategy_counts: Mapping[str, int]


@dataclass(frozen=True)
class StabilityReport:
    """Cross-scenario sign stability and all scenario-level summaries."""

    summaries: tuple[AssociationSummary, ...]
    status: StabilityStatus
    sign_counts: Mapping[AssociationSign, int]


def _mean(values: tuple[float, ...]) -> float:
    return sum(values) / len(values)


def _covariance(x: tuple[float, ...], y: tuple[float, ...]) -> float:
    x_bar, y_bar = _mean(x), _mean(y)
    return sum((xi - x_bar) * (yi - y_bar) for xi, yi in zip(x, y)) / len(x)


def _correlation(x: tuple[float, ...], y: tuple[float, ...]) -> float | None:
    covariance = _covariance(x, y)
    x_var = _covariance(x, x)
    y_var = _covariance(y, y)
    if x_var == 0.0 or y_var == 0.0:
        return None
    return covariance / sqrt(x_var * y_var)


def _sign(value: float | None, *, tolerance: float) -> AssociationSign:
    if value is None:
        return AssociationSign.UNDEFINED
    if value > tolerance:
        return AssociationSign.POSITIVE
    if value < -tolerance:
        return AssociationSign.NEGATIVE
    return AssociationSign.ZERO


def summarise_scenario(
    scenario: ParameterScenario,
    *,
    pollinator_service: Iterable[float],
    floral_damage_pressure: Iterable[float],
    leaf_consumer_pressure: Iterable[float],
    resolution: int = 11,
    sign_tolerance: float = 1e-12,
) -> AssociationSummary:
    """Optimise across a regime grid and summarise A-D association.

    Covariance is computed across grid optima, so it describes co-occurrence of
    optimal trait investments under the declared environmental grid. It is not a
    within-population phenotypic covariance and must not be interpreted as one.
    """
    if sign_tolerance < 0:
        raise ValueError("sign_tolerance must be non-negative")
    optima = sweep_regimes(
        pollinator_service,
        floral_damage_pressure,
        leaf_consumer_pressure,
        scenario.parameters,
        resolution=resolution,
    )
    attraction = tuple(row.architecture.attraction for row in optima)
    defence = tuple(row.architecture.defence for row in optima)
    covariance = _covariance(attraction, defence) if len(optima) >= 2 else None
    correlation = _correlation(attraction, defence) if len(optima) >= 2 else None
    counts: dict[str, int] = {}
    for row in optima:
        counts[row.strategy] = counts.get(row.strategy, 0) + 1
    return AssociationSummary(
        scenario_id=scenario.scenario_id,
        n_optima=len(optima),
        covariance=covariance,
        correlation=correlation,
        sign=_sign(covariance, tolerance=sign_tolerance),
        strategy_counts=counts,
    )


def assess_sign_stability(
    scenarios: Iterable[ParameterScenario],
    *,
    pollinator_service: Iterable[float] = (0.0, 0.25, 0.5, 0.75, 1.0),
    floral_damage_pressure: Iterable[float] = (0.0, 0.25, 0.5, 0.75, 1.0),
    leaf_consumer_pressure: Iterable[float] = (0.0, 0.5, 1.0),
    resolution: int = 11,
    sign_tolerance: float = 1e-12,
) -> StabilityReport:
    """Classify whether A-D association sign is stable across scenarios."""
    scenario_tuple = tuple(scenarios)
    if not scenario_tuple:
        raise ValueError("at least one parameter scenario is required")
    ids = [scenario.scenario_id for scenario in scenario_tuple]
    if len(set(ids)) != len(ids):
        raise ValueError("scenario IDs must be unique")

    summaries = tuple(
        summarise_scenario(
            scenario,
            pollinator_service=pollinator_service,
            floral_damage_pressure=floral_damage_pressure,
            leaf_consumer_pressure=leaf_consumer_pressure,
            resolution=resolution,
            sign_tolerance=sign_tolerance,
        )
        for scenario in scenario_tuple
    )
    sign_counts: dict[AssociationSign, int] = {sign: 0 for sign in AssociationSign}
    for summary in summaries:
        sign_counts[summary.sign] += 1

    non_undefined = [summary.sign for summary in summaries if summary.sign is not AssociationSign.UNDEFINED]
    if not non_undefined:
        status = StabilityStatus.INSUFFICIENT
    elif len(set(non_undefined)) == 1:
        one = non_undefined[0]
        status = {
            AssociationSign.POSITIVE: StabilityStatus.STABLY_POSITIVE,
            AssociationSign.NEGATIVE: StabilityStatus.STABLY_NEGATIVE,
            AssociationSign.ZERO: StabilityStatus.STABLY_ZERO,
        }.get(one, StabilityStatus.INSUFFICIENT)
    else:
        status = StabilityStatus.MIXED

    return StabilityReport(
        summaries=summaries,
        status=status,
        sign_counts=sign_counts,
    )


def canonical_scenarios() -> tuple[ParameterScenario, ...]:
    """Small interpretable scenario set for the first sensitivity report.

    This is not a prior. The scenarios are deliberately contrasting mechanisms:
    defence that blocks pollinators, selective defence under antagonist tracking,
    weak attraction tracking, and a high-assurance setting.
    """
    baseline = ModelParameters()
    return (
        ParameterScenario("baseline", baseline, "Default qualitative scaffold."),
        ParameterScenario(
            "costly_defence",
            ModelParameters(defence_pollinator_cost=1.25, floral_defence_efficacy=0.45, leaf_defence_efficacy=0.45),
            "Defence strongly obstructs pollination and weakly prevents damage.",
        ),
        ParameterScenario(
            "guarded_attraction",
            ModelParameters(defence_pollinator_cost=0.05, attraction_tracking=1.75, floral_defence_efficacy=0.95, leaf_defence_efficacy=0.95),
            "Attractive displays draw antagonists, but defence selectively prevents damage.",
        ),
        ParameterScenario(
            "weak_tracking",
            ModelParameters(attraction_tracking=0.05, defence_pollinator_cost=0.70),
            "Attraction barely increases antagonism while defence has access cost.",
        ),
        ParameterScenario(
            "efficient_assurance",
            ModelParameters(assurance_gain=1.20, assurance_cost=0.05, assurance_outcross_dilution=0.02),
            "Reproductive assurance is cheap and effective under low pollination.",
        ),
    )
