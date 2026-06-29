"""Validation for the four-path floral interaction effect registry.

The registry is intentionally stricter than a narrative literature table.  Each
record corresponds to one reported effect of one directly measured floral trait
on one interaction outcome.  The module verifies that the claimed effect role
matches its trait module and outcome channel, that denominators/exposure are
retained, and that scale conversion is never assumed implicitly.

It does *not* compute a pooled meta-analysis. Effects on incompatible scales must
remain separated until a declared conversion model is justified.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping


REQUIRED_COLUMNS = {
    "effect_id",
    "study_id",
    "citation_or_doi",
    "plant_taxon",
    "study_context_id",
    "site_id",
    "sampling_period",
    "unit_of_analysis",
    "design_type",
    "trait_id",
    "trait_description",
    "trait_module",
    "trait_organ",
    "trait_scaling",
    "effect_role",
    "outcome_channel",
    "outcome_id",
    "outcome_description",
    "outcome_numerator",
    "outcome_denominator_or_exposure",
    "effect_measure",
    "effect_estimate",
    "effect_se",
    "effect_ci_lower",
    "effect_ci_upper",
    "effect_p_value",
    "model_family",
    "adjustment_set",
    "causal_status",
    "linkage_status",
    "raw_table_status",
    "parameter_bridge_status",
    "extraction_status",
    "notes",
}

ROLE_SPECS = {
    "A_to_pollination": ("A_flower", "pollination", "b_A"),
    "A_to_antagonism": ("A_flower", "floral_antagonism", "d_A"),
    "B_to_antagonism": ("B_flower", "floral_antagonism", "e_F"),
    "B_to_pollination": ("B_flower", "pollination", "c_D"),
}

EFFECT_MEASURES = frozenset(
    {
        "standardized_regression_slope",
        "log_response_ratio",
        "log_odds_ratio",
        "incidence_rate_ratio",
        "rate_ratio",
        "standardized_mean_difference",
        "fisher_z",
        "other_reported",
    }
)
DESIGN_TYPES = frozenset({"manipulation", "quasi_experimental", "observational"})
CAUSAL_STATUSES = frozenset({"manipulated", "quasi_experimental", "observational"})
LINKAGE_STATUSES = frozenset({"individual", "flower", "inflorescence", "plant_population", "patch", "network"})
RECOVERABLE_TABLES = frozenset({"supplement", "repository", "available", "author_provided"})
BRIDGE_STATUSES = frozenset(
    {
        "not_assessed",
        "scale_specific_only",
        "convertible_with_raw_table",
        "standardized_slope_ready",
    }
)
EXTRACTED_STATUSES = frozenset({"extracted", "verified"})
BRIDGE_READY = frozenset({"convertible_with_raw_table", "standardized_slope_ready"})


@dataclass(frozen=True)
class EffectRecordSummary:
    effect_id: str
    effect_role: str
    parameter_target: str
    analysis_ready: bool
    bridge_ready: bool
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class EffectRegistryAuditReport:
    summaries: tuple[EffectRecordSummary, ...]
    counts_by_role: dict[str, int]
    bridge_ready_counts_by_role: dict[str, int]
    invalid_records: int
    warnings: tuple[str, ...]


def _text(value: object) -> str:
    return str(value or "").strip()


def _has_value(value: object) -> bool:
    return bool(_text(value)) and _text(value).lower() not in {
        "na",
        "n/a",
        "none",
        "not_recorded",
        "not_assessed",
        "not_available",
    }


def _as_float(value: object, field: str) -> float:
    try:
        return float(_text(value))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be numeric when supplied") from error


def _require_columns(rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    missing = sorted(REQUIRED_COLUMNS.difference(rows[0]))
    if missing:
        raise ValueError(f"four-path effect registry missing columns: {', '.join(missing)}")


def _role_spec(row: Mapping[str, str]) -> tuple[str, str, str] | None:
    return ROLE_SPECS.get(_text(row.get("effect_role")))


def _uncertainty_present(row: Mapping[str, str]) -> bool:
    if _has_value(row.get("effect_se")):
        _as_float(row["effect_se"], "effect_se")
        return True
    if _has_value(row.get("effect_ci_lower")) and _has_value(row.get("effect_ci_upper")):
        lower = _as_float(row["effect_ci_lower"], "effect_ci_lower")
        upper = _as_float(row["effect_ci_upper"], "effect_ci_upper")
        if lower > upper:
            raise ValueError("effect_ci_lower cannot exceed effect_ci_upper")
        return True
    return False


def classify_effect_record(row: Mapping[str, str]) -> EffectRecordSummary:
    """Validate one effect record without making an ecological inference."""

    effect_id = _text(row.get("effect_id")) or "<missing effect_id>"
    role = _role_spec(row)
    warnings: list[str] = []
    if role is None:
        warnings.append("effect_role is not one of the four predeclared Part I paths.")
        target = "not_identified"
    else:
        expected_module, expected_channel, target = role
        if _text(row.get("trait_module")) != expected_module:
            warnings.append(f"effect_role requires trait_module={expected_module}.")
        if _text(row.get("outcome_channel")) != expected_channel:
            warnings.append(f"effect_role requires outcome_channel={expected_channel}.")

    for field in (
        "study_id",
        "citation_or_doi",
        "plant_taxon",
        "study_context_id",
        "site_id",
        "sampling_period",
        "unit_of_analysis",
        "trait_id",
        "trait_description",
        "trait_scaling",
        "outcome_id",
        "outcome_description",
        "outcome_numerator",
        "outcome_denominator_or_exposure",
        "model_family",
        "adjustment_set",
        "notes",
    ):
        if not _has_value(row.get(field)):
            warnings.append(f"missing {field}")

    design_type = _text(row.get("design_type"))
    if design_type not in DESIGN_TYPES:
        warnings.append("design_type must be manipulation, quasi_experimental, or observational.")
    causal_status = _text(row.get("causal_status"))
    if causal_status not in CAUSAL_STATUSES:
        warnings.append("causal_status must be manipulated, quasi_experimental, or observational.")
    linkage = _text(row.get("linkage_status"))
    if linkage not in LINKAGE_STATUSES:
        warnings.append("linkage_status must declare a permitted biological unit.")
    if _text(row.get("trait_organ")).lower() not in {"flower", "floral", "inflorescence", "capitulum", "reproductive_structure"}:
        warnings.append("trait_organ is not a declared floral/reproductive structure.")

    effect_measure = _text(row.get("effect_measure"))
    if effect_measure not in EFFECT_MEASURES:
        warnings.append("effect_measure is not in the declared scale vocabulary.")
    if not _has_value(row.get("effect_estimate")):
        warnings.append("missing effect_estimate")
    else:
        _as_float(row["effect_estimate"], "effect_estimate")
    try:
        uncertainty_present = _uncertainty_present(row)
    except ValueError as error:
        warnings.append(str(error))
        uncertainty_present = False
    if not uncertainty_present:
        warnings.append("missing effect uncertainty (SE or ordered confidence interval)")

    raw_table_status = _text(row.get("raw_table_status"))
    if raw_table_status not in RECOVERABLE_TABLES:
        warnings.append("raw_table_status is not recoverable")
    bridge_status = _text(row.get("parameter_bridge_status"))
    if bridge_status not in BRIDGE_STATUSES:
        warnings.append("parameter_bridge_status is not declared")
    extraction_status = _text(row.get("extraction_status"))
    if extraction_status not in EXTRACTED_STATUSES:
        warnings.append("effect has not reached extracted/verified status")

    analysis_ready = not warnings
    bridge_ready = analysis_ready and bridge_status in BRIDGE_READY
    return EffectRecordSummary(
        effect_id=effect_id,
        effect_role=_text(row.get("effect_role")) or "not_declared",
        parameter_target=target,
        analysis_ready=analysis_ready,
        bridge_ready=bridge_ready,
        warnings=tuple(warnings),
    )


def audit_effect_registry(records: Iterable[Mapping[str, str]]) -> EffectRegistryAuditReport:
    rows = [{key: _text(value) for key, value in record.items()} for record in records]
    _require_columns(rows)
    summaries: list[EffectRecordSummary] = []
    seen: set[str] = set()
    invalid = 0
    global_warnings: list[str] = []
    for row in rows:
        effect_id = _text(row.get("effect_id"))
        if not effect_id:
            invalid += 1
            global_warnings.append("Record without effect_id ignored.")
            continue
        if effect_id in seen:
            invalid += 1
            global_warnings.append(f"Duplicate effect_id ignored: {effect_id}")
            continue
        seen.add(effect_id)
        summaries.append(classify_effect_record(row))

    counts_by_role: dict[str, int] = {}
    bridge_counts: dict[str, int] = {}
    for summary in summaries:
        counts_by_role[summary.effect_role] = counts_by_role.get(summary.effect_role, 0) + 1
        if summary.bridge_ready:
            bridge_counts[summary.effect_role] = bridge_counts.get(summary.effect_role, 0) + 1
    return EffectRegistryAuditReport(
        summaries=tuple(sorted(summaries, key=lambda summary: summary.effect_id)),
        counts_by_role=dict(sorted(counts_by_role.items())),
        bridge_ready_counts_by_role=dict(sorted(bridge_counts.items())),
        invalid_records=invalid,
        warnings=tuple(global_warnings),
    )


def read_effect_registry(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def audit_effect_registry_file(path: str | Path) -> EffectRegistryAuditReport:
    return audit_effect_registry(read_effect_registry(path))


def effect_registry_report_to_dict(report: EffectRegistryAuditReport) -> dict[str, object]:
    return {
        "summaries": [asdict(summary) for summary in report.summaries],
        "counts_by_role": report.counts_by_role,
        "bridge_ready_counts_by_role": report.bridge_ready_counts_by_role,
        "invalid_records": report.invalid_records,
        "warnings": list(report.warnings),
    }
