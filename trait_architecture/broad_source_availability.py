"""Rank harvested M0 candidates by shallow public-source availability.

This module is intentionally broad and shallow. It does not read article text,
download full PDFs, inspect tables, or extract effects. It consumes the OpenAlex
harvest CSV and adds source-availability signals that can cheaply triage many
papers before expensive manual screening.

Availability score is a queueing heuristic only, never an evidence level.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


REQUIRED_COLUMNS = {
    "candidate_id",
    "title",
    "doi",
    "open_access_url",
    "is_open_access",
    "metadata_match_score",
    "metadata_attraction_signal",
    "metadata_barrier_signal",
    "metadata_pollination_signal",
    "metadata_antagonist_signal",
    "metadata_recoverability_signal",
    "candidate_status",
}


@dataclass(frozen=True)
class AvailabilityRecord:
    candidate_id: str
    title: str
    doi: str
    seed_routes: str
    publication_year: str
    metadata_match_score: int
    has_doi: bool
    has_openalex_oa_url: bool
    is_open_access: bool
    metadata_recoverability_signal: bool
    metadata_attraction_signal: bool
    metadata_barrier_signal: bool
    metadata_pollination_signal: bool
    metadata_antagonist_signal: bool
    source_availability_score: int
    next_screen_bucket: str
    screen_priority: str
    candidate_status: str
    notes: str


FIELDS = tuple(AvailabilityRecord.__dataclass_fields__)


def _text(value: object) -> str:
    return str(value or "").strip()


def _bool(value: object) -> bool:
    text = _text(value).lower()
    return text in {"true", "1", "yes", "y"}


def _int(value: object) -> int:
    try:
        return int(float(_text(value)))
    except ValueError:
        return 0


def read_harvest(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [{key: _text(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    if not rows:
        raise ValueError("harvest CSV is empty")
    missing = sorted(REQUIRED_COLUMNS.difference(rows[0]))
    if missing:
        raise ValueError(f"harvest CSV missing columns: {', '.join(missing)}")
    return rows


def score_row(row: dict[str, str]) -> AvailabilityRecord:
    has_doi = bool(_text(row.get("doi")))
    has_oa_url = bool(_text(row.get("open_access_url")))
    is_oa = _bool(row.get("is_open_access"))
    recoverability = _bool(row.get("metadata_recoverability_signal"))
    attraction = _bool(row.get("metadata_attraction_signal"))
    barrier = _bool(row.get("metadata_barrier_signal"))
    pollination = _bool(row.get("metadata_pollination_signal"))
    antagonist = _bool(row.get("metadata_antagonist_signal"))
    metadata_score = _int(row.get("metadata_match_score"))
    availability_score = 0
    availability_score += 2 if has_oa_url else 0
    availability_score += 1 if is_oa else 0
    availability_score += 1 if has_doi else 0
    availability_score += 2 if recoverability else 0
    availability_score += 1 if attraction and pollination else 0
    availability_score += 1 if antagonist else 0
    availability_score += 1 if barrier else 0
    availability_score += min(metadata_score, 5)

    if availability_score >= 10 and has_oa_url:
        bucket = "public_fulltext_first"
        priority = "manual_screen_now"
    elif availability_score >= 8 and recoverability:
        bucket = "repository_or_supplement_lead"
        priority = "manual_screen_next"
    elif has_oa_url and (pollination or antagonist):
        bucket = "oa_metadata_lead"
        priority = "manual_screen_if_capacity"
    elif has_doi:
        bucket = "metadata_only_doi_lead"
        priority = "hold_for_later_public_probe"
    else:
        bucket = "low_recoverability_metadata_only"
        priority = "defer"

    return AvailabilityRecord(
        candidate_id=row["candidate_id"],
        title=row["title"],
        doi=row.get("doi", ""),
        seed_routes=row.get("seed_routes", ""),
        publication_year=row.get("publication_year", ""),
        metadata_match_score=metadata_score,
        has_doi=has_doi,
        has_openalex_oa_url=has_oa_url,
        is_open_access=is_oa,
        metadata_recoverability_signal=recoverability,
        metadata_attraction_signal=attraction,
        metadata_barrier_signal=barrier,
        metadata_pollination_signal=pollination,
        metadata_antagonist_signal=antagonist,
        source_availability_score=availability_score,
        next_screen_bucket=bucket,
        screen_priority=priority,
        candidate_status="M0_source_availability_ranked",
        notes="Broad shallow triage only; do not infer evidence level, trait mapping, denominators, or effect estimates.",
    )


def rank_candidates(rows: Iterable[dict[str, str]]) -> list[AvailabilityRecord]:
    records = [score_row(row) for row in rows]
    return sorted(
        records,
        key=lambda row: (
            row.screen_priority != "manual_screen_now",
            row.screen_priority != "manual_screen_next",
            -row.source_availability_score,
            -row.metadata_match_score,
            row.publication_year,
            row.title,
        ),
    )


def write_outputs(records: list[AvailabilityRecord], out_dir: str | Path, *, top_n: int = 40) -> dict[str, object]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "broad_public_source_availability.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))
    with (output / "broad_public_source_manual_queue.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for record in records[:top_n]:
            writer.writerow(asdict(record))
    counts = Counter(record.next_screen_bucket for record in records)
    priorities = Counter(record.screen_priority for record in records)
    summary = {
        "candidate_count": len(records),
        "top_n_manual_queue": min(top_n, len(records)),
        "bucket_counts": dict(sorted(counts.items())),
        "priority_counts": dict(sorted(priorities.items())),
        "public_fulltext_first_count": counts.get("public_fulltext_first", 0),
        "repository_or_supplement_lead_count": counts.get("repository_or_supplement_lead", 0),
        "decision_boundary": "Availability ranking is a public-source triage heuristic only; it does not screen full text or register effects.",
    }
    (output / "broad_public_source_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    return summary
