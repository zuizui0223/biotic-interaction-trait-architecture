"""Grid optimisation and qualitative strategy classification for trait architectures."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

from .model import Architecture, InteractionRegime, ModelParameters, fitness


@dataclass(frozen=True)
class RegimeOptimum:
    """Fitness-maximising grid phenotype for one declared interaction regime."""

    regime: InteractionRegime
    architecture: Architecture
    fitness: float
    strategy: str


def _grid(resolution: int) -> tuple[float, ...]:
    if resolution < 2:
        raise ValueError("resolution must be at least two")
    return tuple(index / (resolution - 1) for index in range(resolution))


def classify_strategy(architecture: Architecture, *, low: float = 1 / 3, high: float = 2 / 3) -> str:
    """Assign an intentionally coarse qualitative strategy label."""
    if not 0 <= low < high <= 1:
        raise ValueError("require 0 <= low < high <= 1")
    a, d, r = architecture.attraction, architecture.defence, architecture.assurance
    if a >= high and d >= high and r >= high:
        return "guarded_attraction"
    if a >= high and r >= high:
        return "dual_insurance"
    if a <= low and r >= high:
        return "attraction_withdrawal"
    if a >= high and d <= low:
        return "open_attraction"
    if a <= low and d >= high:
        return "defence_first"
    return "mixed"


def optimise_architecture(
    regime: InteractionRegime,
    parameters: ModelParameters = ModelParameters(),
    *,
    resolution: int = 21,
) -> RegimeOptimum:
    """Find the highest-score phenotype in a reproducible finite trait grid.

    Ties are resolved lexicographically by the grid iteration order. This makes
    the result deterministic, but ties should be inspected rather than treated as
    a unique evolutionary optimum.
    """
    best_architecture: Architecture | None = None
    best_score: float | None = None
    for a, d, r in product(_grid(resolution), repeat=3):
        architecture = Architecture(a, d, r)
        score = fitness(architecture, regime, parameters).total
        if best_score is None or score > best_score:
            best_architecture = architecture
            best_score = score
    assert best_architecture is not None and best_score is not None
    return RegimeOptimum(
        regime=regime,
        architecture=best_architecture,
        fitness=best_score,
        strategy=classify_strategy(best_architecture),
    )


def sweep_regimes(
    pollinator_service: Iterable[float],
    floral_damage_pressure: Iterable[float],
    leaf_consumer_pressure: Iterable[float],
    parameters: ModelParameters = ModelParameters(),
    *,
    resolution: int = 21,
) -> tuple[RegimeOptimum, ...]:
    """Optimise a trait architecture for every point in a 3D interaction grid."""
    output: list[RegimeOptimum] = []
    for p, h, l in product(pollinator_service, floral_damage_pressure, leaf_consumer_pressure):
        output.append(
            optimise_architecture(
                InteractionRegime(p, h, l),
                parameters,
                resolution=resolution,
            )
        )
    return tuple(output)
