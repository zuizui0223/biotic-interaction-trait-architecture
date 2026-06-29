"""Audit study cards for the Part I matched floral-regime route.

The global trait/network route was deliberately retired after reproducible
source-coverage tests. The matched-study route keeps studies as the unit of
integration, but structural matching alone does not identify the Part I mixed
partial. This module therefore distinguishes:

* M0/M1/M2: discovery, one-channel, and aligned-panel evidence;
* D1: all four directional interaction paths are estimable;
* D2: the linked unit also has a reproductive-fitness surface;
* D3: shared allocation cost is independently measured or calibrated.

No classification is a biological conclusion. In particular, D2/D3 identify a
*data structure suitable for a declared observation model*, not proof of
adaptation or a universal trait covariance.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping


REQUIRED_COLUMNS = {
    "source_id",
    "seed_route",
    "source_type",
    "citation_or_doi",
    "full_text_status",
    "linked_data_status",
    "study_landscape_id",
    "region",
    "site_id",
    "sampling_period",
    "unit_of_linkage",
    "plant_taxon_scope",
    "attraction_trait_ids",
    "barrier_trait_ids",
    "module_separation_status",
    "pollination_response",
    "pollination_denominator",
    "pollination_same_context",
    "antagonist_response",
    "antagonist_denominator",
    "antagonist_same_context",
    "site_time_alignment",
    "attraction_to_pollination_status",
    "attraction_to_antagonist_status",
    "barrier_to_antagonist_status",
    "barrier_to_pollination_status",
    "fitness_response",
    "fitness_denominator",
    "shared_cost_status",
    "raw_table_status",
    "trait_method_status",
    "phylogeny_or_population_structure_status",
    "extraction_status",
    "notes",
}

TRUTHY = frozenset({"1", "true", "yes", "y", "available", "exact", "overlap"})
DIRECT_ALIGNMENT = frozenset({"exact", "predeclared_overlap"})
LINKABLE_UNITS = frozenset({"individual", "plant_population", "patch", "network"})
RECOVERABLE_TABLES = frozenset({"supplement", "repository", "available", "author_provided"})
READ_FULL_TEXT = frozenset({"read", "available"})
SEPARATE_MODULES = frozenset({"independent", "separately_measured", "separate"})
ESTIMATED_EFFECTS = frozenset({"estimated", "manipulated", "modelled", "direct"})
SHARED_COST_IDENTIFIED = frozenset({"estimated", "allocation_measured", "calibrated"})


@dataclass(frozen=True)
class MatchedStudySummary:
    source_id: str
    evidence_level: str
    high_information: bool
    score: int
    missing_for_d1: tuple[str, ...]
    missing_for_d2: tuple[str, ...]
    missing_for_d3: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class MatchedStudyAuditReport:
    summaries: tuple[MatchedStudySummary, ...]
    counts_by_level: dict[str, int]
    invalid_cards: int
    warnings: tuple[str, ...]


def _normalise(value: object) -> str:
    return str(value or "").strip()


def _truthy(value: object) -> bool:
    return _normalise(value).lower() in TRUTHY


def _tokens(value: object) -> tuple[str, ...]:
    return tuple(token.strip() for token in _normalise(value).split(";") if token.strip())


def _has_value(value: object) -> bool:
    return bool(_normalise(value)) and _normalise(value).lower() not in {
        "none",
        "na",
        "unknown",
        "not_recorded",
        "not_estimated",
        "not_observed",
    }


def _require_columns(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("matched study-card registry is empty")
    missing = sorted(REQUIRED_COLUMNS.difference(rows[0]))
    if missing:
        raise ValueError(f"matched study-card registry missing columns: {', '.join(missing)}")


def _same_context(row: Mapping[str, str], prefix: str) -> bool:
    return _truthy(row.get(f"{prefix}_same_context"))


def _direct_alignment(row: Mapping[str, str]) -> bool:
    return _normalise(row.get("site_time_alignment")).lower() in DIRECT_ALIGNMENT


def _linkable_unit(row: Mapping[str, str]) -> bool:
    return _normalise(row.get("unit_of_linkage")).lower() in LINKABLE_UNITS


def _table_recoverable(row: Mapping[str, str]) -> bool:
    return _normalise(row.get("raw_table_status")).lower() in RECOVERABLE_TABLES


def _full_text_read(row: Mapping[str, str]) -> bool:
    return _normalise(row.get("full_text_status")).lower() in READ_FULL_TEXT


def _modules_separated(row: Mapping[str, str]) -> bool:
    """Return whether A_flower and B_flower were measured separately."""
    return _normalise(row.get("module_separation_status")).lower() in SEPARATE_MODULES


def _effect_estimated(row: Mapping[str, str], column: str) -> bool:
    return _normalise(row.get(column)).lower() in ESTIMATED_EFFECTS


def _shared_cost_identified(row: Mapping[str, str]) -> bool:
    return _normalise(row.get("shared_cost_status")).lower() in SHARED_COST_IDENTIFIED


def _channel_presence(row: Mapping[str, str]) -> tuple[bool, bool, bool, bool]:
    attraction = bool(_tokens(row.get("attraction_trait_ids")))
    barrier = bool(_tokens(row.get("barrier_trait_ids")))
    pollination = _has_value(row.get("pollination_response"))
    antagonist = _has_value(row.get("antagonist_response"))
    return attraction, barrier, pollination, antagonist


def _structural_missing(row: Mapping[str, str]) -> list[str]:
    attraction, barrier, pollination, antagonist = _channel_presence(row)
    missing: list[str] = []
    if not attraction:
        missing.append("attraction trait")
    if not barrier:
        missing.append("floral barrier/resistance trait")
    if attraction and barrier and not _modules_separated(row):
        missing.append("independent A_flower and B_flower measurement")
    if not pollination:
        missing.append("pollination response")
    if not antagonist:
        missing.append("floral-antagonist response")
    if pollination and not _has_value(row.get("pollination_denominator")):
        missing.append("pollination denominator")
    if antagonist and not _has_value(row.get("antagonist_denominator")):
        missing.append("antagonist denominator")
    if pollination and not _same_context(row, "pollination"):
        missing.append("pollination same-context confirmation")
    if antagonist and not _same_context(row, "antagonist"):
        missing.append("antagonist same-context confirmation")
    if not _direct_alignment(row):
        missing.append("exact or predeclared-overlap site-time alignment")
    if not _linkable_unit(row):
        missing.append("linkable unit")
    if not _has_value(row.get("trait_method_status")):
        missing.append("trait-method status")
    if not _table_recoverable(row):
        missing.append("recoverable linked table")
    return missing


def _d1_missing(row: Mapping[str, str]) -> list[str]:
    """Return gaps for the four-arrow channel-mechanism panel."""
    missing = _structural_missing(row)
    arrows = (
        ("attraction_to_pollination_status", "A_flower → pollination effect"),
        ("attraction_to_antagonist_status", "A_flower → floral-antagonist effect"),
        ("barrier_to_antagonist_status", "B_flower → floral-antagonist effect"),
        ("barrier_to_pollination_status", "B_flower → pollination effect"),
    )
    for column, label in arrows:
        if not _effect_estimated(row, column):
            missing.append(label)
    return missing


def _d2_missing(row: Mapping[str, str]) -> list[str]:
    """Return gaps for an observed conditional A×B fitness surface."""
    missing = _d1_missing(row)
    if not _has_value(row.get("fitness_response")):
        missing.append("total reproductive-fitness response")
    if _has_value(row.get("fitness_response")) and not _has_value(row.get("fitness_denominator")):
        missing.append("fitness denominator")
    return missing


def _d3_missing(row: Mapping[str, str]) -> list[str]:
    """Return gaps for comparison with every term in the exact score expression."""
    missing = _d2_missing(row)
    if not _shared_cost_identified(row):
        missing.append("shared A_flower × B_flower cost/allocation estimate")
    return missing


def _high_information(row: Mapping[str, str]) -> tuple[bool, int]:
    signals = (
        _full_text_read(row),
        _table_recoverable(row),
        _has_value(row.get("sampling_period")),
        _has_value(row.get("site_id")),
        _has_value(row.get("pollination_denominator")),
        _has_value(row.get("antagonist_denominator")),
        _has_value(row.get("fitness_response")),
        _linkable_unit(row),
        bool(_tokens(row.get("attraction_trait_ids"))) or bool(_tokens(row.get("barrier_trait_ids"))),
    )
    score = sum(signals)
    return score >= 4, score


def classify_matched_study_card(row: Mapping[str, str]) -> MatchedStudySummary:
    """Classify a pre-screened study card without inferring an ecological sign."""
    source_id = _normalise(row.get("source_id")) or "<missing source_id>"
    warnings: list[str] = []
    if not _full_text_read(row):
        warnings.append("Full text has not been read; metadata cannot establish a matched design.")
    if not _has_value(row.get("study_landscape_id")):
        warnings.append("No declared study landscape identity.")
    if not _has_value(row.get("sampling_period")):
        warnings.append("No declared sampling period.")
    if _has_value(row.get("module_separation_status")) and not _modules_separated(row):
        warnings.append("Attraction and barrier measures are not independent; do not use their composite as an A_flower × B_flower test.")
    if _has_value(row.get("fitness_response")) and not _has_value(row.get("fitness_denominator")):
        warnings.append("Fitness response lacks an at-risk denominator or exposure definition.")

    attraction, barrier, pollination, antagonist = _channel_presence(row)
    d1_missing = _d1_missing(row)
    d2_missing = _d2_missing(row)
    d3_missing = _d3_missing(row)
    high_information, score = _high_information(row)

    if not _full_text_read(row):
        level = "M0_candidate_needs_full_text"
    elif not (attraction or barrier or pollination or antagonist):
        level = "M0_no_relevant_empirical_channels"
    elif attraction and barrier and pollination and antagonist:
        aligned = (
            _same_context(row, "pollination")
            and _same_context(row, "antagonist")
            and _direct_alignment(row)
        )
        if not aligned:
            level = "M1_channels_not_aligned"
        elif not d3_missing:
            level = "D3_parameterized_score_candidate"
        elif not d2_missing:
            level = "D2_observed_fitness_surface_candidate"
        elif not d1_missing:
            level = "D1_channel_mechanism_candidate"
        else:
            level = "M2_aligned_two_channel_panel"
    elif (attraction or barrier) and (pollination or antagonist):
        level = "M1_single_channel_ledger"
    else:
        level = "M0_candidate_insufficient_channels"

    return MatchedStudySummary(
        source_id=source_id,
        evidence_level=level,
        high_information=high_information,
        score=score,
        missing_for_d1=tuple(d1_missing),
        missing_for_d2=tuple(d2_missing),
        missing_for_d3=tuple(d3_missing),
        warnings=tuple(warnings),
    )


def audit_matched_study_cards(cards: Iterable[Mapping[str, str]]) -> MatchedStudyAuditReport:
    rows = [{key: _normalise(value) for key, value in card.items()} for card in cards]
    _require_columns(rows)

    seen: set[str] = set()
    invalid = 0
    global_warnings: list[str] = []
    summaries: list[MatchedStudySummary] = []
    for row in rows:
        source_id = _normalise(row.get("source_id"))
        if not source_id:
            invalid += 1
            continue
        if source_id in seen:
            invalid += 1
            global_warnings.append(f"Duplicate source_id ignored: {source_id}")
            continue
        seen.add(source_id)
        summaries.append(classify_matched_study_card(row))

    counts: dict[str, int] = {}
    for summary in summaries:
        counts[summary.evidence_level] = counts.get(summary.evidence_level, 0) + 1

    return MatchedStudyAuditReport(
        summaries=tuple(sorted(summaries, key=lambda item: item.source_id)),
        counts_by_level=dict(sorted(counts.items())),
        invalid_cards=invalid,
        warnings=tuple(global_warnings),
    )


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def audit_matched_study_cards_file(path: str | Path) -> MatchedStudyAuditReport:
    return audit_matched_study_cards(_read_csv(path))


def matched_study_report_to_dict(report: MatchedStudyAuditReport) -> dict[str, object]:
    return {
        "summaries": [asdict(summary) for summary in report.summaries],
        "counts_by_level": report.counts_by_level,
        "invalid_cards": report.invalid_cards,
        "warnings": list(report.warnings),
    }
