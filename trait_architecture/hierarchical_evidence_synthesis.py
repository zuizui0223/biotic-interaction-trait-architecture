"""Build a layered evidence report without converting discovery records into effects.

The broad literature corpus is deliberately high recall.  This module keeps five
non-interchangeable evidence layers separate:

1. discovery candidates;
2. metadata triage and audit calibration;
3. source-adjudicated route/direction records;
4. numerically extractable effects; and
5. B-to-P full-text readiness.

The resulting report is an evidence architecture, not a prevalence estimator and
not a pooled meta-analysis.  In particular, the route-stratified audit is used to
show the observed behaviour of the priority screen in its sampled cohort only.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


CANDIDATE_REQUIRED = frozenset({"candidate_id", "route_families"})
SCREENED_REQUIRED = frozenset({"candidate_id", "route_families", "shallow_screen_status"})
AUDIT_REQUIRED = frozenset({
    "route_family_audit", "audit_group", "sampled_rows", "route_screenable_rows",
    "direct_route_present_rows", "direct_route_absent_rows", "unassessed_rows",
})
ROUTE_RECORD_REQUIRED = frozenset({
    "record_id", "study_cluster_id", "route", "trait_class", "outcome_class",
    "design_class", "reported_direction",
})
EFFECT_REQUIRED = frozenset({"effect_id", "study_cluster_id", "route", "analysis_status"})
FULLTEXT_REQUIRED = frozenset({
    "queue_id", "study_cluster_id", "doi", "outcome_layer", "comparability_cell",
    "full_text_state", "analysis_action",
})

LAYER_FIELDS = (
    "route", "candidate_records", "priority_records", "biological_context_records",
    "audit_sampled_rows", "audit_screenable_rows", "audit_direct_route_rows",
    "audit_unassessed_rows", "direction_records", "direction_study_clusters",
    "quantitative_effects", "fulltext_queue_records", "interpretation_boundary",
)
DIRECTION_FIELDS = (
    "route", "trait_class", "outcome_class", "design_class", "reported_direction",
    "record_count", "study_cluster_count",
)


class EvidenceInputError(ValueError):
    """Raised when a supplied evidence layer is missing its declared contract."""


def text(value: object) -> str:
    return str(value or "").strip()


def count_as_int(value: object) -> int:
    raw = text(value)
    if not raw:
        return 0
    try:
        return int(raw)
    except ValueError as error:
        raise EvidenceInputError(f"expected integer count, got {raw!r}") from error


def split_routes(value: object) -> list[str]:
    return [route for route in text(value).split(";") if route]


def read_rows(path: str | Path, required: frozenset[str]) -> list[dict[str, str]]:
    location = Path(path)
    with location.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = required.difference(fields)
        if missing:
            raise EvidenceInputError(
                f"{location} is missing required columns: {', '.join(sorted(missing))}"
            )
        return [{key: text(value) for key, value in row.items()} for row in reader]


def _route_counter(rows: Iterable[dict[str, str]], *, predicate=lambda row: True) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        if predicate(row):
            counts.update(split_routes(row.get("route_families")))
    return counts


def _audit_by_route(rows: Iterable[dict[str, str]]) -> dict[str, Counter[str]]:
    totals: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        route = row["route_family_audit"]
        totals[route]["sampled"] += count_as_int(row["sampled_rows"])
        totals[route]["screenable"] += count_as_int(row["route_screenable_rows"])
        totals[route]["present"] += count_as_int(row["direct_route_present_rows"])
        totals[route]["unassessed"] += count_as_int(row["unassessed_rows"])
    return totals


def _direction_by_route(rows: Iterable[dict[str, str]]) -> tuple[Counter[str], dict[str, set[str]]]:
    records: Counter[str] = Counter()
    clusters: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        route = row["route"]
        records[route] += 1
        cluster = row["study_cluster_id"]
        if cluster:
            clusters[route].add(cluster)
    return records, clusters


def _effect_by_route(rows: Iterable[dict[str, str]]) -> Counter[str]:
    """Count only effects that were actually extracted, never empty template rows."""
    return Counter(
        row["route"]
        for row in rows
        if row.get("analysis_status") in {"included", "included_primary", "effect_extracted"}
    )


def _fulltext_by_route(rows: Iterable[dict[str, str]]) -> Counter[str]:
    # The current full-text queue is deliberately B-to-P specific.  Keep the
    # function separate so future route-specific queues can extend the layer.
    return Counter({"B_to_pollination": len(list(rows))})


def build_hierarchical_summary(
    candidates: Iterable[dict[str, str]],
    screened: Iterable[dict[str, str]],
    audit: Iterable[dict[str, str]],
    route_records: Iterable[dict[str, str]],
    effects: Iterable[dict[str, str]],
    fulltext_queue: Iterable[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, object]]:
    """Build route-level and direction-level ledgers for all evidence layers."""
    candidates = list(candidates)
    screened = list(screened)
    audit = list(audit)
    route_records = list(route_records)
    effects = list(effects)
    fulltext_queue = list(fulltext_queue)

    candidate_counts = _route_counter(candidates)
    priority_counts = _route_counter(
        screened,
        predicate=lambda row: row.get("shallow_screen_status") == "priority_for_shallow_source_coding",
    )
    biological_context_counts = _route_counter(
        screened,
        predicate=lambda row: row.get("shallow_screen_status") == "biological_context_needs_route_screen",
    )
    audit_counts = _audit_by_route(audit)
    direction_counts, direction_clusters = _direction_by_route(route_records)
    effect_counts = _effect_by_route(effects)
    fulltext_counts = _fulltext_by_route(fulltext_queue)

    routes = sorted(
        set(candidate_counts) | set(priority_counts) | set(biological_context_counts)
        | set(audit_counts) | set(direction_counts) | set(effect_counts) | set(fulltext_counts)
    )
    layer_rows: list[dict[str, str]] = []
    for route in routes:
        audit_row = audit_counts.get(route, Counter())
        layer_rows.append({
            "route": route,
            "candidate_records": str(candidate_counts[route]),
            "priority_records": str(priority_counts[route]),
            "biological_context_records": str(biological_context_counts[route]),
            "audit_sampled_rows": str(audit_row["sampled"]),
            "audit_screenable_rows": str(audit_row["screenable"]),
            "audit_direct_route_rows": str(audit_row["present"]),
            "audit_unassessed_rows": str(audit_row["unassessed"]),
            "direction_records": str(direction_counts[route]),
            "direction_study_clusters": str(len(direction_clusters[route])),
            "quantitative_effects": str(effect_counts[route]),
            "fulltext_queue_records": str(fulltext_counts[route]),
            "interpretation_boundary": (
                "Candidate and audit counts are discovery/calibration layers; only source-adjudicated "
                "direction records support oriented route statements, and only extracted effects enter numerical synthesis."
            ),
        })

    grouped: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in route_records:
        grouped[(
            row["route"], row["trait_class"], row["outcome_class"],
            row["design_class"], row["reported_direction"],
        )].append(row)
    direction_rows: list[dict[str, str]] = []
    for key, rows in sorted(grouped.items()):
        direction_rows.append({
            "route": key[0], "trait_class": key[1], "outcome_class": key[2],
            "design_class": key[3], "reported_direction": key[4],
            "record_count": str(len(rows)),
            "study_cluster_count": str(len({row["study_cluster_id"] for row in rows if row["study_cluster_id"]})),
        })

    summary: dict[str, object] = {
        "schema_version": "hierarchical_evidence_synthesis_v1",
        "layer_boundaries": {
            "discovery": "Crossref candidate membership and metadata signals are retrieval evidence, not biological route evidence.",
            "triage_and_audit": "Priority and audit outcomes evaluate the screen within the sampled audit cohort; they are not extrapolated to corpus-wide prevalence.",
            "direction": "Only source-adjudicated records support a route and direction statement.",
            "quantitative": "Only compatible, source-located effect extractions are eligible for a numerical synthesis.",
            "fulltext": "The B-to-P queue is a source-resolution layer, not an additional evidence count or an effect-size dataset.",
        },
        "input_counts": {
            "candidate_records": len(candidates),
            "screened_records": len(screened),
            "audit_group_rows": len(audit),
            "source_adjudicated_direction_records": len(route_records),
            "effect_extraction_rows": len(effects),
            "b_to_p_fulltext_queue_rows": len(fulltext_queue),
        },
        "route_count": len(routes),
        "b_to_p_readiness": {
            "direction_study_clusters": len(direction_clusters.get("B_to_pollination", set())),
            "quantitative_effects": effect_counts["B_to_pollination"],
            "fulltext_queue_records": fulltext_counts["B_to_pollination"],
            "verdict": (
                "full-text source resolution required before any B-to-P numerical synthesis"
                if effect_counts["B_to_pollination"] == 0
                else "inspect compatible B-to-P effect strata before numerical synthesis"
            ),
        },
    }
    return layer_rows, direction_rows, summary


def _write_csv(path: Path, fields: tuple[str, ...], rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _markdown(layer_rows: Iterable[dict[str, str]], summary: dict[str, object]) -> str:
    rows = list(layer_rows)
    counts = summary["input_counts"]
    b_to_p = summary["b_to_p_readiness"]
    lines = [
        "# Hierarchical evidence synthesis v1",
        "",
        "## What this report does",
        "",
        "This report uses the full retrieved corpus without treating every retrieved paper as an effect size. "
        "It keeps discovery, screening calibration, source-adjudicated direction, numerical extraction, and B-to-P full-text resolution as separate evidence layers.",
        "",
        "## Layer counts",
        "",
        f"- Discovery candidate records: {counts['candidate_records']}",
        f"- Metadata-screened records: {counts['screened_records']}",
        f"- Route-by-audit-group rows: {counts['audit_group_rows']}",
        f"- Source-adjudicated direction records: {counts['source_adjudicated_direction_records']}",
        f"- Numeric effect-extraction rows: {counts['effect_extraction_rows']}",
        f"- B-to-P full-text queue records: {counts['b_to_p_fulltext_queue_rows']}",
        "",
        "## Route ledger",
        "",
        "| Route | Candidates | Priority | Biological-context | Audit sampled | Audit screenable | Audit direct | Direction clusters | Extracted effects | B-to-P full-text queue |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {route} | {candidate_records} | {priority_records} | {biological_context_records} | "
            "{audit_sampled_rows} | {audit_screenable_rows} | {audit_direct_route_rows} | "
            "{direction_study_clusters} | {quantitative_effects} | {fulltext_queue_records} |".format(**row)
        )
    lines.extend([
        "",
        "## B-to-P readiness",
        "",
        f"- Source-adjudicated B-to-P study clusters: {b_to_p['direction_study_clusters']}",
        f"- Extracted B-to-P effects: {b_to_p['quantitative_effects']}",
        f"- Full-text resolution queue: {b_to_p['fulltext_queue_records']}",
        f"- Current decision: {b_to_p['verdict']}",
        "",
        "## Interpretation boundaries",
        "",
        "- A high candidate count maps a research space; it is not evidence that the target route was measured.",
        "- The audit tests the priority screen in its own sampled cohort. It must not be used to estimate corpus-wide biological prevalence.",
        "- Direction records are descriptive source-coded anchors. They do not become shared effect sizes unless a compatible quantitative contrast is extracted.",
        "- B-to-P full-text queue entries are not additional independent studies; they are a controlled source-resolution layer for the existing direct records.",
    ])
    return "\n".join(lines) + "\n"


def write_hierarchical_outputs(
    out_dir: str | Path,
    layer_rows: Iterable[dict[str, str]],
    direction_rows: Iterable[dict[str, str]],
    summary: dict[str, object],
) -> None:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    _write_csv(destination / "evidence_layers_by_route.csv", LAYER_FIELDS, layer_rows)
    _write_csv(destination / "source_adjudicated_direction_cells.csv", DIRECTION_FIELDS, direction_rows)
    (destination / "hierarchical_evidence_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    (destination / "HIERARCHICAL_EVIDENCE_SYNTHESIS.md").write_text(
        _markdown(layer_rows, summary), encoding="utf-8"
    )
