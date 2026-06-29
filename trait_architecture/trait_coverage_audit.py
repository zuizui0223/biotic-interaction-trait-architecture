"""Trait-specific coverage audit for a normalised trait-data receipt.

The global network audit asks whether a network bundle is broadly usable.  This
module answers the more specific question that must be settled before fitting a
trait model: for each predeclared functional trait, how many requested plants
and networks have a *direct* trait record, how many are represented only by
imputation, and does that trait pass the coverage gate?

The code deliberately does not infer biological function from a trait value.  It
uses the literature-first trait-role matrix as the source of candidate roles and
uses the receipt only to judge data readiness.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


MANIFEST_TAXON_COLUMNS = ("plant_taxon", "plant_taxon_as_reported")
REQUIRED_MATRIX_COLUMNS = {
    "trait_id",
    "functional_module",
    "evidence_grade",
    "global_availability",
    "provisional_role",
    "v1_decision",
}
REQUIRED_RECEIPT_COLUMNS = {
    "plant_taxon",
    "trait_id",
    "trait_value",
    "trait_unit",
    "trait_source",
    "trait_observation_level",
    "imputation_flag",
    "taxon_match_status",
}

TRUE_VALUES = frozenset({"1", "true", "yes", "y"})
DIRECT_MATCH_STATUSES = frozenset({"exact", "accepted_synonym"})
DIRECT_LEVELS = frozenset({"individual", "population", "species", "infraspecific"})
COVERAGE_CANDIDATE_DECISIONS = frozenset({"retain_pending_coverage", "hold_for_coverage_audit"})
PRIMARY_CANDIDATE_ROLES = frozenset({"primary floral attraction candidate", "primary leaf quality candidate"})


@dataclass(frozen=True)
class TraitCoverageSummary:
    """Coverage and decision for one functional trait on the requested plant set."""

    trait_id: str
    functional_module: str
    evidence_grade: str
    provisional_role: str
    v1_decision: str
    requested_plants: int
    direct_plants: int
    imputed_only_plants: int
    direct_coverage: float
    imputed_or_direct_coverage: float
    requested_networks: int
    trait_ready_networks: int
    trait_ready_network_fraction: float
    status: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class TraitCoverageAuditReport:
    """Trait-specific reports plus receipt-integrity findings."""

    summaries: tuple[TraitCoverageSummary, ...]
    unmatched_receipt_rows: int
    invalid_receipt_rows: int
    warnings: tuple[str, ...]


def _normalise(value: object) -> str:
    return str(value or "").strip()


def _as_bool(value: object) -> bool:
    return _normalise(value).lower() in TRUE_VALUES


def _assert_columns(rows: list[dict[str, str]], required: set[str], label: str) -> None:
    if not rows:
        raise ValueError(f"{label} is empty")
    missing = sorted(required.difference(rows[0]))
    if missing:
        raise ValueError(f"{label} is missing required columns: {', '.join(missing)}")


def _manifest_taxon_column(rows: list[dict[str, str]]) -> str:
    for name in MANIFEST_TAXON_COLUMNS:
        if name in rows[0]:
            return name
    expected = ", ".join(MANIFEST_TAXON_COLUMNS)
    raise ValueError(f"plant manifest must contain one of: {expected}")


def _network_sets(manifest: list[dict[str, str]], taxon_column: str) -> tuple[set[str], dict[str, set[str]]]:
    plants: set[str] = set()
    by_network: dict[str, set[str]] = defaultdict(set)
    for row in manifest:
        plant = _normalise(row.get(taxon_column))
        if not plant:
            continue
        plants.add(plant)
        for network in _normalise(row.get("network_names")).split(";"):
            network = network.strip()
            if network:
                by_network[network].add(plant)
    return plants, dict(by_network)


def _eligible_record(row: Mapping[str, str], requested_plants: set[str]) -> tuple[bool, bool, bool]:
    """Return ``(is_usable, is_direct, is_imputed)`` for one receipt record."""

    plant = _normalise(row.get("plant_taxon"))
    value = _normalise(row.get("trait_value"))
    match = _normalise(row.get("taxon_match_status")).lower()
    level = _normalise(row.get("trait_observation_level")).lower()
    imputed = _as_bool(row.get("imputation_flag"))

    usable = bool(plant and value and plant in requested_plants and match in DIRECT_MATCH_STATUSES)
    direct = usable and not imputed and level in DIRECT_LEVELS
    return usable, direct, usable and imputed


def audit_trait_coverage(
    plant_manifest: Iterable[Mapping[str, str]],
    trait_matrix: Iterable[Mapping[str, str]],
    trait_receipt: Iterable[Mapping[str, str]],
    *,
    plant_coverage_threshold: float = 0.60,
    network_coverage_threshold: float = 0.60,
    minimum_trait_ready_networks: int = 30,
) -> TraitCoverageAuditReport:
    """Audit every coverage-candidate trait against a requested plant manifest.

    A trait is ``ready_for_primary_analysis`` only when it has direct records for
    at least ``plant_coverage_threshold`` of requested plants and at least
    ``minimum_trait_ready_networks`` networks have direct records for at least
    ``network_coverage_threshold`` of their requested plant set.  This does not
    by itself certify a global backbone: the interaction and metadata audit still
    checks region count, source provenance, and interaction-layer integrity.
    """

    manifest = [{key: _normalise(value) for key, value in row.items()} for row in plant_manifest]
    matrix = [{key: _normalise(value) for key, value in row.items()} for row in trait_matrix]
    receipt = [{key: _normalise(value) for key, value in row.items()} for row in trait_receipt]

    _assert_columns(manifest, set(), "plant manifest")
    _assert_columns(matrix, REQUIRED_MATRIX_COLUMNS, "trait-role matrix")
    _assert_columns(receipt, REQUIRED_RECEIPT_COLUMNS, "trait receipt")
    if not 0.0 < plant_coverage_threshold <= 1.0:
        raise ValueError("plant_coverage_threshold must lie in (0, 1]")
    if not 0.0 < network_coverage_threshold <= 1.0:
        raise ValueError("network_coverage_threshold must lie in (0, 1]")
    if minimum_trait_ready_networks < 1:
        raise ValueError("minimum_trait_ready_networks must be positive")

    taxon_column = _manifest_taxon_column(manifest)
    requested_plants, plants_by_network = _network_sets(manifest, taxon_column)
    matrix_by_trait = {row["trait_id"]: row for row in matrix if row.get("trait_id")}
    candidate_traits = [
        row for row in matrix if row.get("v1_decision") in COVERAGE_CANDIDATE_DECISIONS and row.get("trait_id")
    ]

    direct_by_trait: dict[str, set[str]] = defaultdict(set)
    imputed_by_trait: dict[str, set[str]] = defaultdict(set)
    unmatched_receipt_rows = 0
    invalid_receipt_rows = 0

    for row in receipt:
        trait_id = row.get("trait_id", "")
        if trait_id not in matrix_by_trait:
            unmatched_receipt_rows += 1
            continue
        usable, direct, imputed = _eligible_record(row, requested_plants)
        if not usable:
            invalid_receipt_rows += 1
            continue
        plant = row["plant_taxon"]
        if direct:
            direct_by_trait[trait_id].add(plant)
        elif imputed:
            imputed_by_trait[trait_id].add(plant)
        else:
            invalid_receipt_rows += 1

    summaries: list[TraitCoverageSummary] = []
    global_warnings: list[str] = []
    if not plants_by_network:
        global_warnings.append("Manifest has no network_names; network-level trait readiness cannot be assessed.")

    for row in candidate_traits:
        trait_id = row["trait_id"]
        direct = direct_by_trait[trait_id]
        imputed_only = imputed_by_trait[trait_id].difference(direct)
        direct_rate = len(direct) / len(requested_plants) if requested_plants else 0.0
        inclusive_rate = len(direct | imputed_only) / len(requested_plants) if requested_plants else 0.0

        ready_networks = 0
        for plants in plants_by_network.values():
            network_rate = len(plants & direct) / len(plants) if plants else 0.0
            if network_rate >= network_coverage_threshold:
                ready_networks += 1
        network_fraction = ready_networks / len(plants_by_network) if plants_by_network else 0.0

        warnings: list[str] = []
        if direct_rate < plant_coverage_threshold:
            warnings.append("Direct plant coverage is below the declared threshold.")
        if not plants_by_network:
            warnings.append("Network readiness is unavailable because manifest network_names are absent.")
        elif ready_networks < minimum_trait_ready_networks:
            warnings.append("Fewer than the declared minimum number of networks meet direct trait coverage.")
        if imputed_only:
            warnings.append("Imputed-only records are reported separately and do not count toward direct coverage.")

        role = row.get("provisional_role", "")
        if row.get("v1_decision") == "hold_for_coverage_audit":
            status = "conditional_trait_requires_design_decision"
        elif direct_rate >= plant_coverage_threshold and ready_networks >= minimum_trait_ready_networks:
            status = "ready_for_primary_analysis" if role in PRIMARY_CANDIDATE_ROLES else "ready_for_conditional_analysis"
        else:
            status = "insufficient_direct_coverage"

        summaries.append(
            TraitCoverageSummary(
                trait_id=trait_id,
                functional_module=row.get("functional_module", ""),
                evidence_grade=row.get("evidence_grade", ""),
                provisional_role=role,
                v1_decision=row.get("v1_decision", ""),
                requested_plants=len(requested_plants),
                direct_plants=len(direct),
                imputed_only_plants=len(imputed_only),
                direct_coverage=direct_rate,
                imputed_or_direct_coverage=inclusive_rate,
                requested_networks=len(plants_by_network),
                trait_ready_networks=ready_networks,
                trait_ready_network_fraction=network_fraction,
                status=status,
                warnings=tuple(warnings),
            )
        )

    return TraitCoverageAuditReport(
        summaries=tuple(sorted(summaries, key=lambda summary: summary.trait_id)),
        unmatched_receipt_rows=unmatched_receipt_rows,
        invalid_receipt_rows=invalid_receipt_rows,
        warnings=tuple(global_warnings),
    )


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return [{key: _normalise(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def audit_trait_coverage_files(
    plant_manifest_csv: str | Path,
    trait_matrix_csv: str | Path,
    trait_receipt_csv: str | Path,
    **kwargs: object,
) -> TraitCoverageAuditReport:
    """Read the normalised CSV inputs and run :func:`audit_trait_coverage`."""

    return audit_trait_coverage(
        _read_csv(plant_manifest_csv),
        _read_csv(trait_matrix_csv),
        _read_csv(trait_receipt_csv),
        **kwargs,
    )


def trait_coverage_report_to_dict(report: TraitCoverageAuditReport) -> dict[str, object]:
    """Return a JSON-serialisable trait-coverage report."""

    return {
        "summaries": [
            {
                "trait_id": summary.trait_id,
                "functional_module": summary.functional_module,
                "evidence_grade": summary.evidence_grade,
                "provisional_role": summary.provisional_role,
                "v1_decision": summary.v1_decision,
                "requested_plants": summary.requested_plants,
                "direct_plants": summary.direct_plants,
                "imputed_only_plants": summary.imputed_only_plants,
                "direct_coverage": summary.direct_coverage,
                "imputed_or_direct_coverage": summary.imputed_or_direct_coverage,
                "requested_networks": summary.requested_networks,
                "trait_ready_networks": summary.trait_ready_networks,
                "trait_ready_network_fraction": summary.trait_ready_network_fraction,
                "status": summary.status,
                "warnings": list(summary.warnings),
            }
            for summary in report.summaries
        ],
        "unmatched_receipt_rows": report.unmatched_receipt_rows,
        "invalid_receipt_rows": report.invalid_receipt_rows,
        "warnings": list(report.warnings),
    }
