"""Qualitative simulations and empirical data contracts for trait architecture."""

from .model import Architecture, FitnessBreakdown, InteractionRegime, ModelParameters, fitness
from .network_audit import CoverageReport, audit_files, audit_network_coverage, report_to_dict
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
    "CoverageReport",
    "audit_files",
    "audit_network_coverage",
    "report_to_dict",
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
