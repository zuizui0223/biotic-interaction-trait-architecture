"""Qualitative simulations of attraction, defence, and reproductive assurance."""

from .model import Architecture, FitnessBreakdown, InteractionRegime, ModelParameters, fitness
from .regime_map import RegimeOptimum, classify_strategy, optimise_architecture, sweep_regimes
from .stability import (
    AssociationSign,
    AssociationSummary,
    ParameterScenario,
    StabilityReport,
    StabilityStatus,
    assess_sign_stability,
    canonical_scenarios,
    summarise_scenario,
)

__all__ = [
    "Architecture",
    "FitnessBreakdown",
    "InteractionRegime",
    "ModelParameters",
    "fitness",
    "RegimeOptimum",
    "classify_strategy",
    "optimise_architecture",
    "sweep_regimes",
    "AssociationSign",
    "AssociationSummary",
    "ParameterScenario",
    "StabilityReport",
    "StabilityStatus",
    "assess_sign_stability",
    "canonical_scenarios",
    "summarise_scenario",
]
