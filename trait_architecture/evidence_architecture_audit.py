"""Build and validate the all-258 study-design coding matrix.

This module uses the immutable PR #20 candidate snapshot as a retrieval corpus.
It creates one screening row per candidate work. The resulting matrix is for
source-verified design coding, not for effect-size meta-analysis.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from trait_architecture.fixed_candidate_universe import EXPECTED_CANDIDATE_COUNT


COMPONENT_STATUS = frozenset({
    "unassessed",
    "not_stated",
    "mentioned_not_measured",
    "measured_indirect",
    "measured_direct",
})
CODING_STATUS = frozenset({
    "unassessed",
    "abstract_coded",
    "fulltext_coded",
    "adjudicated",
})
SOURCE_BASIS = frozenset({
    "metadata_only",
    "abstract_metadata_available",
    "public_fulltext",
    "public_data",
    "fulltext_and_public_data",
})
MATRIX_FIELDS = (
    "candidate_id",
    "doi",
    "title",
    "authors",
    "publication_year",
    "work_type",
    "seed_routes",
    "seed_query_ids",
    "is_open_access",
    "abstract_available",
    "cited_by_count",
    "metadata_attraction_signal",
    "metadata_barrier_signal",
    "metadata_pollination_signal",
    "metadata_antagonist_signal",
    "metadata_recoverability_signal",
    "metadata_signal_vector",
    "coding_status",
    "source_basis",
    "A_flower_status",
    "B_flower_status",
    "P_status",
    "H_status",
    "W_status",
    "shared_biological_unit_status",
    "trait_outcome_effect_status",
    "denominator_or_exposure_status",
    "causal_design_status",
    "public_data_status",
    "max_evidence_level",
    "coding_note",
)
COMPONENT_FIELDS = (
    "A_flower_status",
    "B_flower_status",
    "P_status",
    "H_status",
    "W_status",
    "shared_biological_unit_status",
    "trait_outcome_effect_status",
    "denominator_or_exposure_status",
    "causal_design_status",
    "public_data_status",
    "max_evidence_level",
)


def _bool_text(value: object) -> str:
    return "true" if str(value or "").strip().lower() in {"true", "1", "yes", "y"} else "false"


def _metadata_vector(candidate: dict[str, str]) -> str:
    fields = (
        "metadata_attraction_signal",
        "metadata_barrier_signal",
        "metadata_pollination_signal",
        "metadata_antagonist_signal",
    )
    return "".join("1" if _bool_text(candidate.get(field)) == "true" else "0" for field in fields)


def initial_screening_rows(candidates: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """Return one unassessed evidence-architecture row per fixed candidate."""

    rows: list[dict[str, str]] = []
    for candidate in candidates:
        abstract_available = _bool_text(candidate.get("abstract_available"))
        row = {
            "candidate_id": str(candidate.get("candidate_id", "")).strip(),
            "doi": str(candidate.get("doi", "")).strip(),
            "title": str(candidate.get("title", "")).strip(),
            "authors": str(candidate.get("authors", "")).strip(),
            "publication_year": str(candidate.get("publication_year", "")).strip(),
            "work_type": str(candidate.get("work_type", "")).strip(),
            "seed_routes": str(candidate.get("seed_routes", "")).strip(),
            "seed_query_ids": str(candidate.get("seed_query_ids", "")).strip(),
            "is_open_access": _bool_text(candidate.get("is_open_access")),
            "abstract_available": abstract_available,
            "cited_by_count": str(candidate.get("cited_by_count", "")).strip(),
            "metadata_attraction_signal": _bool_text(candidate.get("metadata_attraction_signal")),
            "metadata_barrier_signal": _bool_text(candidate.get("metadata_barrier_signal")),
            "metadata_pollination_signal": _bool_text(candidate.get("metadata_pollination_signal")),
            "metadata_antagonist_signal": _bool_text(candidate.get("metadata_antagonist_signal")),
            "metadata_recoverability_signal": _bool_text(candidate.get("metadata_recoverability_signal")),
            "metadata_signal_vector": _metadata_vector(candidate),
            "coding_status": "unassessed",
            "source_basis": "abstract_metadata_available" if abstract_available == "true" else "metadata_only",
            "coding_note": "",
        }
        row.update({field: "unassessed" for field in COMPONENT_FIELDS})
        rows.append(row)
    validate_matrix(rows, expected_count=None)
    return rows


def validate_matrix(rows: Iterable[dict[str, str]], *, expected_count: int | None = EXPECTED_CANDIDATE_COUNT) -> None:
    """Validate matrix shape and prevent metadata cues from becoming coded evidence."""

    rows = list(rows)
    if expected_count is not None and len(rows) != expected_count:
        raise ValueError(f"expected {expected_count} rows, got {len(rows)}")
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        missing = [field for field in MATRIX_FIELDS if field not in row]
        if missing:
            raise ValueError(f"row {index} is missing fields: {', '.join(missing)}")
        candidate_id = row["candidate_id"].strip()
        if not candidate_id:
            raise ValueError(f"row {index} has blank candidate_id")
        if candidate_id in seen:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        seen.add(candidate_id)
        if row["coding_status"] not in CODING_STATUS:
            raise ValueError(f"row {index} has invalid coding_status")
        if row["source_basis"] not in SOURCE_BASIS:
            raise ValueError(f"row {index} has invalid source_basis")
        vector = row["metadata_signal_vector"]
        if len(vector) != 4 or any(character not in "01" for character in vector):
            raise ValueError(f"row {index} has invalid metadata_signal_vector")
        for field in COMPONENT_FIELDS:
            if row[field] not in COMPONENT_STATUS:
                raise ValueError(f"row {index} has invalid {field}")
        if row["coding_status"] == "unassessed" and any(
            row[field] != "unassessed" for field in COMPONENT_FIELDS
        ):
            raise ValueError("unassessed rows cannot contain inferred evidence components")


def metadata_baseline_summary(rows: Iterable[dict[str, str]]) -> dict[str, object]:
    """Summarize retrieval metadata only, explicitly without biological inference."""

    rows = list(rows)
    validate_matrix(rows, expected_count=None)
    signal_fields = (
        "metadata_attraction_signal",
        "metadata_barrier_signal",
        "metadata_pollination_signal",
        "metadata_antagonist_signal",
        "metadata_recoverability_signal",
    )
    return {
        "corpus_type": "fixed_retrieval_corpus",
        "candidate_count": len(rows),
        "work_type_counts": dict(sorted(Counter(row["work_type"] for row in rows).items())),
        "abstract_availability_counts": dict(sorted(Counter(row["abstract_available"] for row in rows).items())),
        "open_access_metadata_counts": dict(sorted(Counter(row["is_open_access"] for row in rows).items())),
        "metadata_signal_counts": {
            field: sum(row[field] == "true" for row in rows)
            for field in signal_fields
        },
        "metadata_signal_vector_counts": dict(sorted(Counter(row["metadata_signal_vector"] for row in rows).items())),
        "coding_status_counts": dict(sorted(Counter(row["coding_status"] for row in rows).items())),
        "interpretation_boundary": (
            "Counts in this file describe archived retrieval metadata. They do not establish that a paper measured a floral trait, "
            "a pollination response, floral antagonism, shared biological units, denominators, causal effects, or evidence level."
        ),
    }


def write_matrix(path: str | Path, rows: Iterable[dict[str, str]]) -> None:
    rows = list(rows)
    validate_matrix(rows)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_metadata_baseline(path: str | Path, rows: Iterable[dict[str, str]]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(metadata_baseline_summary(rows), indent=2, sort_keys=True),
        encoding="utf-8",
    )
