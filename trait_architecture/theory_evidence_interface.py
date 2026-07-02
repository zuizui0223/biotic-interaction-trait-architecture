"""Map broad evidence states to the existing attraction-defence regime model.

The exact model equation is intentionally not changed here.  This module records
which empirical channels inform the *sign or context* of a model term and which
remain sensitivity-only axes.

It must not convert publication counts, keyword hits, or abstract-level direction
anchors into numerical values of b_A, d_A, e_F, c_D, c_AD, P, H, or c_R.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


INTERFACE_FIELDS = (
    "model_term", "exact_score_component", "required_empirical_channel", "broad_edge_candidate_records",
    "source_direction_clusters", "aligned_direction_clusters", "mixed_direction_clusters",
    "contradictory_direction_clusters", "evidence_status", "allowed_model_use", "not_identified",
    "connection_boundary",
)

TERM_REQUIREMENTS = (
    {
        "model_term": "b_A",
        "exact_score_component": "P*b_A*c_D*exp(-c_D*D)*(1-c_R*R)",
        "required_empirical_channel": "A_to_pollination",
        "expected_direction": "positive",
        "allowed_model_use": "Retain b_A >= 0 in biologically signed scenarios; leave magnitude as a sensitivity axis.",
    },
    {
        "model_term": "d_A",
        "exact_score_component": "H*d_A*e_F",
        "required_empirical_channel": "A_to_antagonism",
        "expected_direction": "positive",
        "allowed_model_use": "Retain d_A >= 0 as a possible display-tracking branch, but retain d_A = 0 and context-dependent scenarios.",
    },
    {
        "model_term": "e_F",
        "exact_score_component": "H*d_A*e_F",
        "required_empirical_channel": "B_to_antagonism",
        "expected_direction": "negative",
        "allowed_model_use": "Retain e_F >= 0 when B is an organ-matched floral barrier; leave magnitude as a sensitivity axis.",
    },
    {
        "model_term": "c_D",
        "exact_score_component": "P*b_A*c_D*exp(-c_D*D)*(1-c_R*R)",
        "required_empirical_channel": "B_to_pollination",
        "expected_direction": "negative",
        "allowed_model_use": "Retain c_D > 0 as a chemically conditional pollinator-cost branch; do not impose it as a universal defence property.",
    },
    {
        "model_term": "c_AD",
        "exact_score_component": "-c_AD",
        "required_empirical_channel": "matched_A_B_shared_allocation_or_cost",
        "expected_direction": "",
        "allowed_model_use": "Keep c_AD = 0 and c_AD > 0 as explicit sensitivity scenarios; do not calibrate from separate A and B literature.",
    },
    {
        "model_term": "c_R*R",
        "exact_score_component": "P*b_A*c_D*exp(-c_D*D)*(1-c_R*R)",
        "required_empirical_channel": "reproductive_assurance_outcross_dilution",
        "expected_direction": "",
        "allowed_model_use": "Keep as an explicit sensitivity axis; no active L1/L2 empirical module identifies this term.",
    },
)


class TheoryEvidenceInterfaceError(ValueError):
    """Raised when evidence-map and direction-registry contracts are malformed."""


def text(value: object) -> str:
    return str(value or "").strip()


def as_int(value: object) -> int:
    raw = text(value)
    return int(raw) if raw else 0


def read_rows(path: str | Path, required: set[str]) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [{key: text(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    if rows and not required.issubset(rows[0]):
        raise TheoryEvidenceInterfaceError("input table lacks required columns")
    return rows


def _broad_counts(edge_rows: Iterable[dict[str, str]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in edge_rows:
        result[text(row.get("model_edge"))] = as_int(row.get("broad_edge_candidate_records"))
    return result


def _direction_counts(route_rows: Iterable[dict[str, str]]) -> dict[str, Counter[str]]:
    clusters: dict[str, dict[str, str]] = defaultdict(dict)
    for row in route_rows:
        if text(row.get("record_status")) != "included_for_direction_map":
            continue
        if text(row.get("is_primary_sign_record")).lower() not in {"true", "1", "yes", "y"}:
            continue
        route, cluster = text(row.get("route")), text(row.get("study_cluster_id"))
        direction = text(row.get("reported_direction"))
        if route and cluster:
            clusters[route][cluster] = direction
    return {route: Counter(values.values()) for route, values in clusters.items()}


def build_interface(
    edge_rows: Iterable[dict[str, str]], route_rows: Iterable[dict[str, str]],
) -> list[dict[str, str]]:
    broad = _broad_counts(edge_rows)
    directions = _direction_counts(route_rows)
    output: list[dict[str, str]] = []
    for requirement in TERM_REQUIREMENTS:
        channel = requirement["required_empirical_channel"]
        expected = requirement["expected_direction"]
        counts = directions.get(channel, Counter())
        total = sum(counts.values())
        aligned = counts[expected] if expected else 0
        mixed = counts["mixed"]
        contradictory = 0
        if expected == "positive":
            contradictory = counts["negative"]
        elif expected == "negative":
            contradictory = counts["positive"]
        if channel not in directions:
            if channel in {"matched_A_B_shared_allocation_or_cost", "reproductive_assurance_outcross_dilution"}:
                status = "not_identified_in_active_L1_L2_program"
            else:
                status = "no_source_direction_anchor"
        elif total == 0:
            status = "no_source_direction_anchor"
        elif aligned and (mixed or contradictory):
            status = "conditional_directional_support"
        elif aligned:
            status = "directionally_aligned_low_cluster_support"
        elif mixed:
            status = "direction_unresolved_or_context_dependent"
        else:
            status = "direction_not_aligned_with_declared_model_branch"
        output.append({
            "model_term": requirement["model_term"],
            "exact_score_component": requirement["exact_score_component"],
            "required_empirical_channel": channel,
            "broad_edge_candidate_records": str(broad.get(channel, 0)),
            "source_direction_clusters": str(total),
            "aligned_direction_clusters": str(aligned),
            "mixed_direction_clusters": str(mixed),
            "contradictory_direction_clusters": str(contradictory),
            "evidence_status": status,
            "allowed_model_use": requirement["allowed_model_use"],
            "not_identified": (
                "Magnitude, interaction with environmental P/H states, and population covariance remain unidentified."
                if channel in directions else "No active direct empirical channel identifies this term."
            ),
            "connection_boundary": (
                "The exact mixed-partial equation is unchanged. Broad abstract coverage describes literature attention; "
                "source-direction anchors describe limited sign/context evidence; neither is a numerical parameter estimate."
            ),
        })
    return output


def write_interface(path: str | Path, rows: Iterable[dict[str, str]]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INTERFACE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
