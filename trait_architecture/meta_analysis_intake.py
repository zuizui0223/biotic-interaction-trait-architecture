"""Gate fixed-corpus evidence layers and prepare meta-analysis intake.

Discovery candidates, audit rows, direction anchors, full-text queues, and
numerical effects are distinct kinds of evidence.  This module preserves that
distinction and admits a direction anchor to quantitative intake only where it
matches one exact, predeclared route/trait/outcome/design cell.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from trait_architecture.broad_meta_analysis import (
    EFFECT_FIELDS,
    ROUTE_RECORD_FIELDS,
    STRATUM_FIELDS,
    validate_effect_rows,
    validate_route_records,
)

GATE_FIELDS = (
    "gate_id", "layer_from", "layer_to", "input_universe", "input_count", "pass_count",
    "hold_count", "gate_status", "filter_rule", "interpretation_boundary",
)
INTAKE_FIELDS = (
    "intake_id", "record_id", "study_id", "study_cluster_id", "doi", "taxon", "route",
    "trait_role", "trait_class", "outcome_class", "design_class", "reported_direction",
    "source_basis", "target_stratum_id", "stratum_match_status", "source_gate_status",
    "numeric_gate_status", "intake_status", "extraction_priority", "fulltext_queue_id",
    "fulltext_state", "required_primary_source_fields", "decision_reason",
)
CAPACITY_FIELDS = (
    "stratum_id", "route", "trait_class", "outcome_class", "effect_metric", "design_class",
    "min_clusters_exploratory", "min_clusters_stability", "direction_anchor_clusters",
    "primary_source_confirmed_clusters", "numeric_effect_clusters", "shortfall_to_exploratory",
    "shortfall_to_stability", "capacity_status", "recommended_action",
)

PRIMARY_SOURCE_BASES = frozenset({
    "publisher_full_text", "publisher_full_text_and_supplement", "author_accepted_manuscript",
    "institutional_repository_manuscript", "article_linked_public_dataset", "primary_source",
})


class IntakeInputError(ValueError):
    """Raised when a layer input is malformed or a gate cannot be evaluated."""


def text(value: object) -> str:
    return str(value or "").strip()


def is_true(value: object) -> bool:
    return text(value).lower() in {"true", "1", "yes", "y"}


def as_int(value: object) -> int:
    raw = text(value)
    if not raw:
        return 0
    try:
        return int(raw)
    except ValueError as error:
        raise IntakeInputError(f"expected integer value, got {raw!r}") from error


def read_rows(path: str | Path, required: Iterable[str]) -> list[dict[str, str]]:
    location = Path(path)
    with location.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = set(required).difference(fields)
        if missing:
            raise IntakeInputError(f"{location} missing columns: {', '.join(sorted(missing))}")
        return [{key: text(value) for key, value in row.items()} for row in reader]


def _validate_strata(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    rows = list(rows)
    seen_ids: set[str] = set()
    seen_cells: set[tuple[str, str, str, str]] = set()
    for row in rows:
        missing = set(STRATUM_FIELDS).difference(row)
        if missing:
            raise IntakeInputError(f"stratum missing columns: {', '.join(sorted(missing))}")
        identifier = row["stratum_id"]
        cell = (row["route"], row["trait_class"], row["outcome_class"], row["design_class"])
        if not identifier or identifier in seen_ids or cell in seen_cells:
            raise IntakeInputError("strata require unique IDs and unique exact route/trait/outcome/design cells")
        seen_ids.add(identifier)
        seen_cells.add(cell)
    return rows


def _primary_direction_anchors(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row for row in validate_route_records(rows)
        if row.get("record_status") == "included_for_direction_map"
        and is_true(row.get("is_primary_sign_record"))
    ]


def _stratum_by_cell(rows: Iterable[dict[str, str]]) -> dict[tuple[str, str, str, str], dict[str, str]]:
    return {
        (row["route"], row["trait_class"], row["outcome_class"], row["design_class"]): row
        for row in rows
    }


def _fulltext_by_cluster(rows: Iterable[dict[str, str]]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        cluster = text(row.get("study_cluster_id"))
        if cluster in result:
            raise IntakeInputError("full-text queue contains duplicate study clusters")
        if cluster:
            result[cluster] = row
    return result


def _numeric_effect_clusters(rows: Iterable[dict[str, str]]) -> dict[tuple[str, str, str, str], set[str]]:
    result: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    for row in validate_effect_rows(rows):
        if row.get("analysis_status") != "eligible_for_quantitative_synthesis":
            continue
        if not is_true(row.get("is_primary_effect")):
            continue
        cell = (row["route"], row["trait_class"], row["outcome_class"], row["design_class"])
        result[cell].add(row["study_cluster_id"])
    return result


def build_intake(
    candidates: Iterable[dict[str, str]],
    screened: Iterable[dict[str, str]],
    audit: Iterable[dict[str, str]],
    route_records: Iterable[dict[str, str]],
    strata: Iterable[dict[str, str]],
    effects: Iterable[dict[str, str]],
    fulltext_queue: Iterable[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, object]]:
    """Return layer gates, exact-cell intake, stratum capacity, and summary."""
    candidates, screened, audit = list(candidates), list(screened), list(audit)
    anchors = _primary_direction_anchors(route_records)
    strata = _validate_strata(strata)
    cell_to_stratum = _stratum_by_cell(strata)
    fulltext = _fulltext_by_cluster(fulltext_queue)
    effects_by_cell = _numeric_effect_clusters(effects)

    screen_counts = Counter(row.get("shallow_screen_status", "") for row in screened)
    biological_pass = (
        screen_counts["priority_for_shallow_source_coding"]
        + screen_counts["biological_context_needs_route_screen"]
    )
    audit_sampled = sum(as_int(row.get("sampled_rows")) for row in audit)
    audit_screenable = sum(as_int(row.get("route_screenable_rows")) for row in audit)
    audit_unassessed = sum(as_int(row.get("unassessed_rows")) for row in audit)

    anchor_clusters: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    primary_source_clusters: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    intake: list[dict[str, str]] = []

    for index, row in enumerate(anchors, start=1):
        cell = (row["route"], row["trait_class"], row["outcome_class"], row["design_class"])
        stratum = cell_to_stratum.get(cell)
        queue = fulltext.get(row["study_cluster_id"], {})
        if stratum is None:
            intake.update if False else None
            intake.append({
                "intake_id": f"MAI{index:03d}", "record_id": row["record_id"],
                "study_id": row["study_id"], "study_cluster_id": row["study_cluster_id"],
                "doi": row["doi"], "taxon": row["taxon"], "route": row["route"],
                "trait_role": row["trait_role"], "trait_class": row["trait_class"],
                "outcome_class": row["outcome_class"], "design_class": row["design_class"],
                "reported_direction": row["reported_direction"], "source_basis": row["source_basis"],
                "target_stratum_id": "", "stratum_match_status": "no_exact_predeclared_stratum",
                "source_gate_status": "direction_map_source_basis_retained",
                "numeric_gate_status": "do_not_force_into_current_quantitative_strata",
                "intake_status": "direction_map_only", "extraction_priority": "P3",
                "fulltext_queue_id": text(queue.get("queue_id")),
                "fulltext_state": text(queue.get("full_text_state")) or "not_enqueued",
                "required_primary_source_fields": "No quantitative extraction under current protocol unless a separately declared stratum is justified.",
                "decision_reason": "Exact outcome/design cell does not match a predeclared quantitative stratum.",
            })
            continue

        anchor_clusters[cell].add(row["study_cluster_id"])
        source_confirmed = row["source_basis"] in PRIMARY_SOURCE_BASES
        if source_confirmed:
            primary_source_clusters[cell].add(row["study_cluster_id"])
        current_anchor_n = len(anchor_clusters[cell])
        exploratory_gap = max(0, as_int(stratum["min_clusters_exploratory"]) - current_anchor_n)
        intake.append({
            "intake_id": f"MAI{index:03d}", "record_id": row["record_id"],
            "study_id": row["study_id"], "study_cluster_id": row["study_cluster_id"],
            "doi": row["doi"], "taxon": row["taxon"], "route": row["route"],
            "trait_role": row["trait_role"], "trait_class": row["trait_class"],
            "outcome_class": row["outcome_class"], "design_class": row["design_class"],
            "reported_direction": row["reported_direction"], "source_basis": row["source_basis"],
            "target_stratum_id": stratum["stratum_id"], "stratum_match_status": "exact_predeclared_stratum",
            "source_gate_status": "primary_source_confirmed" if source_confirmed else "primary_source_not_yet_confirmed",
            "numeric_gate_status": "ready_for_numeric_field_check" if source_confirmed else "requires_primary_source_and_numeric_fields",
            "intake_status": "numeric_extraction_candidate" if source_confirmed else "core_source_resolution_queue",
            "extraction_priority": "P1" if exploratory_gap <= 1 else "P2",
            "fulltext_queue_id": text(queue.get("queue_id")),
            "fulltext_state": text(queue.get("full_text_state")) or "not_enqueued",
            "required_primary_source_fields": "treatment/control definition; effect-compatible response unit and denominator; independent-panel identity; n and variance/raw fields; exact source locator",
            "decision_reason": "Exact predeclared route/trait/outcome/design cell; retain one primary comparison only after source and panel checks.",
        })

    exact_anchor_clusters = set()
    for clusters in anchor_clusters.values():
        exact_anchor_clusters.update(clusters)
    numeric_exact_clusters = set()
    for cell, clusters in effects_by_cell.items():
        numeric_exact_clusters.update(clusters.intersection(anchor_clusters.get(cell, set())))

    capacity: list[dict[str, str]] = []
    for stratum in strata:
        cell = (stratum["route"], stratum["trait_class"], stratum["outcome_class"], stratum["design_class"])
        direction_n = len(anchor_clusters[cell])
        source_n = len(primary_source_clusters[cell])
        effect_n = len(effects_by_cell[cell])
        exploratory = as_int(stratum["min_clusters_exploratory"])
        stability = as_int(stratum["min_clusters_stability"])
        if effect_n >= stability:
            status, action = "ready_for_stable_meta_analysis", "Run the predeclared random-effects model and report heterogeneity."
        elif effect_n >= exploratory:
            status, action = "ready_for_exploratory_meta_analysis", "Run only the exploratory model and label it unstable."
        elif direction_n == 0:
            status, action = "no_direction_anchor_in_fixed_corpus", "Freeze as unpopulated; do not create an ad hoc pool."
        elif source_n == 0:
            status, action = "source_resolution_required", "Recover primary source and numeric fields for the exact-cell anchor(s)."
        else:
            status, action = "numeric_extraction_required", "Convert a source-confirmed primary comparison after panel and uncertainty checks."
        capacity.append({
            "stratum_id": stratum["stratum_id"], "route": stratum["route"], "trait_class": stratum["trait_class"],
            "outcome_class": stratum["outcome_class"], "effect_metric": stratum["effect_metric"],
            "design_class": stratum["design_class"], "min_clusters_exploratory": str(exploratory),
            "min_clusters_stability": str(stability), "direction_anchor_clusters": str(direction_n),
            "primary_source_confirmed_clusters": str(source_n), "numeric_effect_clusters": str(effect_n),
            "shortfall_to_exploratory": str(max(0, exploratory - effect_n)),
            "shortfall_to_stability": str(max(0, stability - effect_n)),
            "capacity_status": status, "recommended_action": action,
        })

    exact_anchor_n = len(exact_anchor_clusters)
    gate_rows = [
        {
            "gate_id": "G01", "layer_from": "L1_discovery", "layer_to": "L2_biological_screen",
            "input_universe": "all_deduplicated_candidates", "input_count": str(len(candidates)),
            "pass_count": str(biological_pass), "hold_count": str(len(screened) - biological_pass),
            "gate_status": "fixed_metadata_rule",
            "filter_rule": "Pass only priority_for_shallow_source_coding or biological_context_needs_route_screen; keep the remainder as discovery-only.",
            "interpretation_boundary": "Metadata triage is not evidence that a route was measured.",
        },
        {
            "gate_id": "G02", "layer_from": "L2_audit", "layer_to": "L3_source_adjudication",
            "input_universe": "frozen_route_stratified_audit_cohort", "input_count": str(audit_sampled),
            "pass_count": str(audit_screenable), "hold_count": str(audit_unassessed),
            "gate_status": "audit_calibration_only",
            "filter_rule": "Adjudicate only rows with a usable source; unresolved rows remain unresolved rather than absent.",
            "interpretation_boundary": "The audit calibrates screen behaviour and is not an exhaustive denominator for the direction registry.",
        },
        {
            "gate_id": "G03", "layer_from": "L3_direction_map", "layer_to": "L4_meta_intake",
            "input_universe": "primary_direction_anchors", "input_count": str(len(anchors)),
            "pass_count": str(exact_anchor_n), "hold_count": str(len(anchors) - exact_anchor_n),
            "gate_status": "exact_predeclared_cell_match",
            "filter_rule": "Require included primary sign record and exact route, trait class, outcome class, and design class match to a predeclared stratum.",
            "interpretation_boundary": "A nonmatching anchor remains direction evidence and cannot be widened post hoc.",
        },
        {
            "gate_id": "G04", "layer_from": "L4_meta_intake", "layer_to": "L5_numeric_effect",
            "input_universe": "exact_predeclared_intake_anchors", "input_count": str(exact_anchor_n),
            "pass_count": str(len(numeric_exact_clusters)), "hold_count": str(exact_anchor_n - len(numeric_exact_clusters)),
            "gate_status": "primary_source_and_numeric_fields_required",
            "filter_rule": "Require primary source, compatible treatment/control contrast, independent panel, oriented metric, and uncertainty or raw fields.",
            "interpretation_boundary": "An abstract direction or a full-text queue entry is not an effect size.",
        },
    ]
    summary = {
        "schema_version": "meta_analysis_intake_v1",
        "fixed_corpus_rule": "No candidate-retrieval expansion is used for this capacity assessment.",
        "input_counts": {
            "candidates": len(candidates), "screened": len(screened), "audit_sampled_rows": audit_sampled,
            "primary_direction_anchors": len(anchors), "exact_predeclared_intake_anchors": exact_anchor_n,
            "direction_map_only_anchors": len(anchors) - exact_anchor_n,
            "primary_effect_clusters_for_exact_intake": len(numeric_exact_clusters),
        },
        "meta_analysis_verdict": "No predeclared stratum is currently poolable; recover primary-source numerical fields for exact-cell anchors before any synthesis.",
    }
    return gate_rows, intake, capacity, summary


def _write_csv(path: Path, fields: Iterable[str], rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        writer.writerows(rows)


def _markdown(gates: list[dict[str, str]], intake: list[dict[str, str]], capacity: list[dict[str, str]], summary: dict[str, object]) -> str:
    counts = summary["input_counts"]
    lines = [
        "# Fixed-corpus layer gates and meta-analysis intake v1", "",
        "## Current capacity", "",
        f"- Deduplicated candidates: {counts['candidates']}",
        f"- Frozen audit sampled rows: {counts['audit_sampled_rows']}",
        f"- Primary direction anchors: {counts['primary_direction_anchors']}",
        f"- Exact-stratum anchors: {counts['exact_predeclared_intake_anchors']}",
        f"- Direction-map-only anchors: {counts['direction_map_only_anchors']}",
        f"- Numeric effects for exact-stratum anchors: {counts['primary_effect_clusters_for_exact_intake']}", "",
        "## Gates", "", "| Gate | From → to | Input | Pass | Held |", "|---|---|---:|---:|---:|",
    ]
    for row in gates:
        lines.append(f"| {row['gate_id']} | {row['layer_from']} → {row['layer_to']} | {row['input_count']} | {row['pass_count']} | {row['hold_count']} |")
    lines.extend(["", "## Core numeric extraction queue", "", "| Priority | Stratum | Study cluster | Source gate | Numeric gate |", "|---|---|---|---|---|"])
    for row in intake:
        if row["intake_status"] != "direction_map_only":
            lines.append(f"| {row['extraction_priority']} | {row['target_stratum_id']} | {row['study_cluster_id']} | {row['source_gate_status']} | {row['numeric_gate_status']} |")
    lines.extend(["", "## Stratum capacity", "", "| Stratum | Direction anchors | Source-confirmed | Numeric effects | Exploratory gap | Status |", "|---|---:|---:|---:|---:|---|"])
    for row in capacity:
        lines.append(f"| {row['stratum_id']} | {row['direction_anchor_clusters']} | {row['primary_source_confirmed_clusters']} | {row['numeric_effect_clusters']} | {row['shortfall_to_exploratory']} | {row['capacity_status']} |")
    return "\n".join(lines) + "\n"


def write_intake_outputs(out_dir: str | Path, gate_rows: list[dict[str, str]], intake_rows: list[dict[str, str]], capacity_rows: list[dict[str, str]], summary: dict[str, object]) -> None:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    _write_csv(destination / "layer_gate_audit.csv", GATE_FIELDS, gate_rows)
    _write_csv(destination / "meta_analysis_intake_queue.csv", INTAKE_FIELDS, intake_rows)
    _write_csv(destination / "meta_analysis_stratum_capacity.csv", CAPACITY_FIELDS, capacity_rows)
    (destination / "meta_analysis_intake_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (destination / "FIXED_CORPUS_META_ANALYSIS_FOUNDATION.md").write_text(_markdown(gate_rows, intake_rows, capacity_rows, summary), encoding="utf-8")
