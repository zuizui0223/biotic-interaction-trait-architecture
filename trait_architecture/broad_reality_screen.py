"""Apply conservative metadata triage to the broad real-world evidence corpus.

This screen never determines whether a study measured a variable or found an
effect. It only separates likely biological flower-interaction candidates from
obvious non-biological retrieval noise before manual shallow coding.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Iterable


BIOLOGY_CONTEXT_TERMS = (
    "plant", "floral", "flower", "pollination", "pollinator", "pollen", "nectar", "corolla", "petal",
    "florivory", "florivore", "herbivory", "seed predation", "fruit set", "seed set", "reproductive success",
    "flower damage", "floral damage", "nectar robber", "pollen thief",
)
NONBIOLOGY_EXCLUSION_TERMS = (
    "algorithm", "optimization", "feature selection", "machine learning", "deep learning", "neural network",
    "robot", "wireless", "catalyst", "electrochemical", "nanoparticle", "battery", "photocatalytic", "zinc",
    "copper", "packaging", "ivf", "in vitro fertilization", "clinical", "image processing", "computer vision",
    "antenna", "scheduling",
)
SCREEN_FIELDS = (
    "metadata_biology_context_term_count",
    "metadata_nonbiology_exclusion_signal",
    "shallow_screen_status",
    "shallow_screen_reason",
)


def _bool(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _text(row: dict[str, str]) -> str:
    return f"{row.get('title', '')} {row.get('container_title', '')}".lower()


def screen_row(row: dict[str, str]) -> dict[str, str]:
    """Return deterministic metadata-only triage fields for one harvested record."""

    text = _text(row)
    biology_count = sum(term in text for term in BIOLOGY_CONTEXT_TERMS)
    exclusion_terms = [term for term in NONBIOLOGY_EXCLUSION_TERMS if term in text]
    trait_signal = _bool(row.get("metadata_A_signal")) or _bool(row.get("metadata_B_signal"))
    outcome_signal = _bool(row.get("metadata_P_signal")) or _bool(row.get("metadata_H_signal")) or _bool(row.get("metadata_W_signal"))

    screened = dict(row)
    screened["metadata_biology_context_term_count"] = str(biology_count)
    screened["metadata_nonbiology_exclusion_signal"] = str(bool(exclusion_terms)).lower()
    if exclusion_terms:
        screened["shallow_screen_status"] = "likely_nonbiological_retrieval_noise"
        screened["shallow_screen_reason"] = ";".join(exclusion_terms)
    elif biology_count >= 2 and trait_signal and outcome_signal:
        screened["shallow_screen_status"] = "priority_for_shallow_source_coding"
        screened["shallow_screen_reason"] = "biological_flower_context_plus_trait_and_outcome_metadata_signals"
    elif biology_count >= 2:
        screened["shallow_screen_status"] = "biological_context_needs_route_screen"
        screened["shallow_screen_reason"] = "biological_flower_context_without_complete_trait_outcome_metadata_pair"
    else:
        screened["shallow_screen_status"] = "metadata_context_uncertain"
        screened["shallow_screen_reason"] = "insufficient_biological_flower_context_in_title_or_container_metadata"
    return screened


def screen_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    return [screen_row(row) for row in rows]


def screen_summary(rows: Iterable[dict[str, str]]) -> dict[str, object]:
    rows = list(rows)
    priority = [row for row in rows if row["shallow_screen_status"] == "priority_for_shallow_source_coding"]
    return {
        "input_candidate_count": len(rows),
        "screen_status_counts": dict(sorted(Counter(row["shallow_screen_status"] for row in rows).items())),
        "priority_shallow_source_coding_count": len(priority),
        "priority_route_family_counts": dict(sorted(Counter(
            route
            for row in priority
            for route in row.get("route_families", "").split(";")
            if route
        ).items())),
        "interpretation_boundary": (
            "This metadata screen is a triage aid. Priority status does not establish that a paper measured a floral trait or outcome, "
            "reported a direction, or supports a model prediction. Source coding is still required."
        ),
    }


def read_candidate_rows(path: str | Path) -> tuple[list[dict[str, str]], list[str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
        return rows, list(reader.fieldnames or [])


def write_screen_outputs(
    out_dir: str | Path,
    rows: Iterable[dict[str, str]],
    base_fields: Iterable[str],
) -> None:
    rows = list(rows)
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    fields = list(base_fields) + list(SCREEN_FIELDS)
    with (destination / "broad_reality_evidence_screened.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with (destination / "broad_reality_evidence_priority.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(row for row in rows if row["shallow_screen_status"] == "priority_for_shallow_source_coding")
    (destination / "broad_reality_evidence_screen_summary.json").write_text(
        json.dumps(screen_summary(rows), indent=2, sort_keys=True), encoding="utf-8"
    )
