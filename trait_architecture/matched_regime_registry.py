"""Audit study cards for the Part I matched floral-regime route.

The global trait/network route was deliberately retired after reproducible
source-coverage tests. This module prevents the replacement literature route
from degrading into an unstructured pile of papers: it classifies whether a
study can contribute only a seed, a one-channel ledger, an aligned two-channel
panel, or a direct Part I regime test.

No classification is a biological conclusion. In particular, ``D1`` means that
the *data structure* is suitable for a declared observation model; it does not
mean the study supports a particular theory scenario.
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
SEPARATE_MODULES = frozenset(
    {
        "independent",
        "separately_measured",
        "separate",
        "separately_measured_raw_not_recovered",
    }
)
COMPOSITE_ONLY_MODULES = frozenset({"composite_only", "conflated_composite"})


@dataclass(frozen=True)
class MatchedStudySummary:
    source_id: str
    evidence_level: str
    high_information: bool
    score: int
    missing_for_d1: tuple[str, ...]
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
    return bool(_normalise(value)) and _normalise(value).lower() not in {"none", "na", "unknown", "not_recorded"}


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


def _module_status(row: Mapping[str, str]) -> str:
    return _normalise(row.get("module_separation_status")).lower()


def _modules_separated(row: Mapping[str, str]) -> bool:
    """Return whether data contain separately measured A and B components.

    This can be true even when the public article analysed a composite and the
    underlying individual table is not yet available. In that situation the
    study stays M2 due to data recoverability, but it remains a legitimate D1
    reanalysis candidate after data acquisition.
    """

    return _module_status(row) in SEPARATE_MODULES


def _composite_only(row: Mapping[str, str]) -> bool:
    return _module_status(row) in COMPOSITE_ONLY_MODULES


def _channel_presence(row: Mapping[str, str]) -> tuple[bool, bool, bool, bool]:
    attraction = bool(_tokens(row.get("attraction_trait_ids")))
    barrier = bool(_tokens(row.get("barrier_trait_ids")))
    pollination = _has_value(row.get("pollination_response"))
    antagonist = _has_value(row.get("antagonist_response"))
    return attraction, barrier, pollination, antagonist


def _d1_missing(row: Mapping[str, str]) -> list[str]:
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
        missing.append("recoverable plant-level table")
    return missing


def _high_information(row: Mapping[str, str]) -> tuple[bool, int]:
    signals = (
        _full_text_read(row),
        _table_recoverable(row),
        _has_value(row.get("sampling_period")),
        _has_value(row.get("site_id")),
        _has_value(row.get("pollination_denominator")),
        _has_value(row.get("antagonist_denominator")),
        _linkable_unit(row),
        bool(_tokens(row.get("attraction_trait_ids"))) or bool(_tokens(row.get("barrier_trait_ids"))),
    )
    score = sum(signals)
    return score >= 4, score


def classify_matched_study_card(row: Mapping[str, str]) -> MatchedStudySummary:
    """Classify a pre-screened study card without inferring any ecological sign."""

    source_id = _normalise(row.get("source_id")) or "<missing source_id>"
    warnings: list[str] = []
    if not _full_text_read(row):
        warnings.append("Full text has not been read; metadata cannot establish a matched design.")
    if not _has_value(row.get("study_landscape_id")):
        warnings.append("No declared study landscape identity.")
    if not _has_value(row.get("sampling_period")):
        warnings.append("No declared sampling period.")
    if _composite_only(row):
        warnings.append("Attraction and barrier are available only as a composite; do not use it as an A_flower × B_flower test.")
    if _module_status(row) == "separately_measured_raw_not_recovered":
        warnings.append("A and B were measured separately, but a recoverable individual table is still required for D1 reanalysis.")

    attraction, barrier, pollination, antagonist = _channel_presence(row)
    d1_missing = _d1_missing(row)
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
        elif not d1_missing:
            level = "D1_direct_regime_model_candidate"
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
