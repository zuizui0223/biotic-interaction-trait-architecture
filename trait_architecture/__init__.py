"""Qualitative simulations and empirical data contracts for trait architecture."""

from .ad_interaction_condition import (
    ADInteractionCondition,
    ADLocalRelation,
    attraction_defence_cross_partial,
    floral_pressure_threshold_for_complementarity,
)
from .matched_regime_registry import (
    MatchedStudyAuditReport,
    MatchedStudySummary,
    audit_matched_study_cards,
    audit_matched_study_cards_file,
    classify_matched_study_card,
    matched_study_report_to_dict,
)
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
from .trait_coverage_audit import (
    TraitCoverageAuditReport,
    TraitCoverageSummary,
    audit_trait_coverage,
    audit_trait_coverage_files,
    trait_coverage_report_to_dict,
)

__all__ = [
    "ADInteractionCondition",
    "ADLocalRelation",
    "attraction_defence_cross_partial",
    "floral_pressure_threshold_for_complementarity",
    "MatchedStudyAuditReport",
    "MatchedStudySummary",
    "audit_matched_study_cards",
    "audit_matched_study_cards_file",
    "classify_matched_study_card",
    "matched_study_report_to_dict",
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
    "TraitCoverageAuditReport",
    "TraitCoverageSummary",
    "audit_trait_coverage",
    "audit_trait_coverage_files",
    "trait_coverage_report_to_dict",
]
