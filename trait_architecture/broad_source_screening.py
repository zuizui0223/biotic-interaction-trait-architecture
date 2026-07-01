"""Create a source-screening matrix without promoting metadata to evidence."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


SCREEN_FIELDS = (
    "candidate_id", "doi", "title", "discovery_route_families", "source_screen_status",
    "source_access_status", "study_type", "taxon", "primary_study_id", "study_cluster_id",
    "screen_exclusion_reason", "coder_id", "coding_date", "coding_note",
)
SOURCE_SCREEN_STATUSES = frozenset({"unassessed", "included_for_source_coding", "excluded"})
SOURCE_ACCESS_STATUSES = frozenset({"unassessed", "abstract_only", "fulltext_available", "data_available", "fulltext_and_data_available", "inaccessible"})


def _text(value: object) -> str:
    return str(value or "").strip()


def read_priority_candidates(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [{key: _text(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    required = {"candidate_id", "doi", "title", "route_families", "shallow_screen_status"}
    if rows and not required.issubset(rows[0]):
        raise ValueError("priority candidate CSV is missing required harvested fields")
    if any(row["shallow_screen_status"] != "priority_for_shallow_source_coding" for row in rows):
        raise ValueError("source screening matrix must be built from priority cohort only")
    return rows


def initial_source_screening_matrix(priority_candidates: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    candidates = list(priority_candidates)
    identifiers: set[str] = set()
    matrix: list[dict[str, str]] = []
    for candidate in candidates:
        candidate_id = _text(candidate.get("candidate_id"))
        if not candidate_id:
            raise ValueError("priority candidate has blank candidate_id")
        if candidate_id in identifiers:
            raise ValueError(f"duplicate priority candidate_id: {candidate_id}")
        identifiers.add(candidate_id)
        matrix.append({
            "candidate_id": candidate_id,
            "doi": _text(candidate.get("doi")),
            "title": _text(candidate.get("title")),
            "discovery_route_families": _text(candidate.get("route_families")),
            "source_screen_status": "unassessed",
            "source_access_status": "unassessed",
            "study_type": "",
            "taxon": "",
            "primary_study_id": "",
            "study_cluster_id": "",
            "screen_exclusion_reason": "",
            "coder_id": "",
            "coding_date": "",
            "coding_note": "",
        })
    validate_source_screening_matrix(matrix)
    return matrix


def validate_source_screening_matrix(rows: Iterable[dict[str, str]]) -> None:
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        missing = [field for field in SCREEN_FIELDS if field not in row]
        if missing:
            raise ValueError(f"source-screening row {index} missing fields: {', '.join(missing)}")
        candidate_id = _text(row["candidate_id"])
        if not candidate_id or candidate_id in seen:
            raise ValueError(f"source-screening matrix has duplicate or blank candidate_id at row {index}")
        seen.add(candidate_id)
        if row["source_screen_status"] not in SOURCE_SCREEN_STATUSES:
            raise ValueError(f"source-screening row {candidate_id} has invalid source_screen_status")
        if row["source_access_status"] not in SOURCE_ACCESS_STATUSES:
            raise ValueError(f"source-screening row {candidate_id} has invalid source_access_status")
        if row["source_screen_status"] == "unassessed" and any(
            _text(row[field]) for field in ("study_type", "taxon", "primary_study_id", "study_cluster_id", "screen_exclusion_reason")
        ):
            raise ValueError("unassessed source-screening rows cannot contain inferred source decisions")


def write_source_screening_matrix(path: str | Path, rows: Iterable[dict[str, str]]) -> None:
    rows = list(rows)
    validate_source_screening_matrix(rows)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCREEN_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
