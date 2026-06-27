"""A minimal, deliberately qualitative trait-architecture fitness model.

The model maps a phenotype ``(A, D, R)`` and an interaction regime ``(P, H, L)``
to a decomposed fitness score. It is intended for regime-map simulation, not for
estimating absolute fitness in a particular species.

A = attraction investment
D = defence / access-limitation investment
R = reproductive-assurance investment
P = pollinator service
H = floral-herbivore or florivore pressure
L = leaf-cutter or leaf-consumer pressure

The key switch is the defence cost to pollination versus its damage-reduction
efficacy. When defence substantially obstructs pollination it creates an
attraction-defence trade-off. When defence selectively reduces damage while
preserving pollination, attraction and defence can co-occur.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp


def _unit_interval(value: float, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must lie in [0, 1]")


@dataclass(frozen=True)
class Architecture:
    """Investment in attraction, defence/access limitation, and assurance."""

    attraction: float
    defence: float
    assurance: float

    def __post_init__(self) -> None:
        _unit_interval(self.attraction, "attraction")
        _unit_interval(self.defence, "defence")
        _unit_interval(self.assurance, "assurance")


@dataclass(frozen=True)
class InteractionRegime:
    """Scaled external interaction pressures."""

    pollinator_service: float
    floral_damage_pressure: float
    leaf_consumer_pressure: float

    def __post_init__(self) -> None:
        _unit_interval(self.pollinator_service, "pollinator_service")
        _unit_interval(self.floral_damage_pressure, "floral_damage_pressure")
        _unit_interval(self.leaf_consumer_pressure, "leaf_consumer_pressure")


@dataclass(frozen=True)
class ModelParameters:
    """Dimensionless parameters for qualitative regime exploration.

    The defaults create an interpretable baseline rather than a calibrated
    biological system. Users should sweep plausible values before attaching an
    empirical interpretation to any regime boundary.
    """

    baseline_outcross: float = 0.10
    attraction_gain: float = 1.20
    defence_pollinator_cost: float = 0.45
    assurance_gain: float = 0.70
    floral_damage_baseline: float = 0.20
    attraction_tracking: float = 1.10
    floral_defence_efficacy: float = 0.75
    leaf_damage_baseline: float = 0.75
    leaf_defence_efficacy: float = 0.85
    attraction_cost: float = 0.22
    defence_cost: float = 0.24
    assurance_cost: float = 0.20
    attraction_defence_shared_cost: float = 0.10
    assurance_outcross_dilution: float = 0.10

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.floral_defence_efficacy > 1 or self.leaf_defence_efficacy > 1:
            raise ValueError("defence efficacies must lie in [0, 1]")


@dataclass(frozen=True)
class FitnessBreakdown:
    """Channel-specific score bookkeeping for one phenotype and regime."""

    outcross_benefit: float
    assurance_benefit: float
    floral_damage_loss: float
    leaf_damage_loss: float
    investment_cost: float

    @property
    def total(self) -> float:
        return (
            self.outcross_benefit
            + self.assurance_benefit
            - self.floral_damage_loss
            - self.leaf_damage_loss
            - self.investment_cost
        )


def fitness(
    architecture: Architecture,
    regime: InteractionRegime,
    parameters: ModelParameters = ModelParameters(),
) -> FitnessBreakdown:
    """Evaluate the qualitative fitness decomposition.

    Attraction raises pollinator-mediated gain. Defence reduces that gain through
    ``defence_pollinator_cost`` while reducing floral and leaf damage. Attraction
    can increase floral damage when antagonists track displays. Assurance gains
    value as pollinator service falls, but carries a small outcross-dilution term.
    """
    a, d, r = architecture.attraction, architecture.defence, architecture.assurance
    p = regime.pollinator_service
    h = regime.floral_damage_pressure
    l = regime.leaf_consumer_pressure

    pollination_access = exp(-parameters.defence_pollinator_cost * d)
    outcross_benefit = (
        p
        * (parameters.baseline_outcross + parameters.attraction_gain * a)
        * pollination_access
        * (1.0 - parameters.assurance_outcross_dilution * r)
    )

    assurance_benefit = (1.0 - p) * parameters.assurance_gain * r

    floral_exposure = parameters.floral_damage_baseline + parameters.attraction_tracking * a
    floral_damage_loss = h * floral_exposure * (1.0 - parameters.floral_defence_efficacy * d)

    leaf_damage_loss = l * parameters.leaf_damage_baseline * (1.0 - parameters.leaf_defence_efficacy * d)

    investment_cost = (
        parameters.attraction_cost * a * a
        + parameters.defence_cost * d * d
        + parameters.assurance_cost * r * r
        + parameters.attraction_defence_shared_cost * a * d
    )

    return FitnessBreakdown(
        outcross_benefit=outcross_benefit,
        assurance_benefit=assurance_benefit,
        floral_damage_loss=floral_damage_loss,
        leaf_damage_loss=leaf_damage_loss,
        investment_cost=investment_cost,
    )
