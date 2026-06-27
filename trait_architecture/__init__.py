"""Qualitative simulations of attraction, defence, and reproductive assurance."""

from .model import Architecture, FitnessBreakdown, InteractionRegime, ModelParameters, fitness
from .regime_map import RegimeOptimum, classify_strategy, optimise_architecture, sweep_regimes

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
]
