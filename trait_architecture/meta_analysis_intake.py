"""Gate the existing evidence layers and prepare a fixed meta-analysis intake.

This module is deliberately conservative.  It never treats a discovery candidate,
an abstract-direction record, or a full-text queue item as a numerical effect.

The key output is an intake table for *already source-adjudicated direction
anchors*.  Each anchor is either:

* matched to one exact, predeclared quantitative stratum and sent to primary
  source/numeric-field recovery; or
* retained in the direction map because its outcome/design cell is not a
  predeclared quantitative stratum.

This allows the current fixed literature corpus to support a reproducible
extraction programme without silently widening strata or adding new papers.
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
    """Raised for malformed layer-gate or intake inputs."""


def text(value: object) -> str:
    return str(value or "").strip()


def is_true(value: object) -> bool:
    return text(value).lower() in {"true", "1", "yes", "y"}


def read_rows(path: str | Path, required: Iterable[str]) -> list[dict[str, str]]:
    location = Path(path)
    with location.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = set(required).difference(fields)
        if missing:
            raise IntakeInputError(
                f"{location} missing required columns: {', '.join(sorted(missing))}"
            )
        return [{key: text(value) for key, value in row.items()} for row in reader]


def _validate_strata(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    rows = list(rows)
    seen: set[str] = set()
    required = set(STRATUM_FIELDS)
    for row in rows:
        missing = required.difference(row)
        if missing:
            raise IntakeInputError(f"stratum row missing columns: {', '.join(sorted(missing))}")
        identifier = text(row.get("stratum_id"))
        if not identifier or identifier in seen:
            raise IntakeInputError("stratum IDs must be present and unique")
        seen.add(identifier)
    return rows


def _screen_counts(rows: Iterable[dict[str, str]]) -> Counter[str]:
    return Counter(text(row.get("shallow_screen_status")) for row in rows)


def _primary_direction_anchors(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    validated = validate_route_records(rows)
    return [
        row for row in validated
        if row.get("record_status") == "included_for_direction_map"
        and is_true(row.get("is_primary_sign_record"))
    ]


def _stratum_lookup(rows: Iterable[dict[str, str]]) -> dict[tuple[str, str, str, str], dict[str, str]]:
    lookup: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (row["route"], row["trait_class"], row["outcome_class"], row["design_class"])
        if key in lookup:
            raise IntakeInputError("predeclared strata must not duplicate a route/trait/outcome/design cell")
        lookup[key] = row
    return lookup


def _fulltext_lookup(rows: Iterable[dict[str, str]]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        cluster = text(row.get("study_cluster_id"))
        if not cluster:
            continue
        if cluster in lookup:
            raise IntakeInputError("full-text queue cannot contain duplicated study_cluster_id values")
        lookup[cluster] = row
    return lookup


def _effect_cluster_counts(rows: Iterable[dict[str, str]]) -> dict[tuple[str, str, str, str], set[str]]:
    validated = validate_effect_rows(rows)
    counts: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    for row in validated:
        if row.get("analysis_status") != "eligible_for_quantitative_synthesis":
            continue
        if not is_true(row.get("is_primary_effect")):
            continue
        key = (row["route"], row["trait_class"], row["outcome_class"], row["design_class"])
        counts[key].add(row["study_cluster_id"])
    return counts


def build_intake(
    candidates: Iterable[dict[str, str]],
    screened: Iterable[dict[str, str]],
    audit: Iterable[dict[str, str]],
    route_records: Iterable[dict[str, str]],
    strata: Iterable[dict[str, str]],
    effects: Iterable[dict[str, str]],
    fulltext_queue: Iterable[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, object]]:
    """Create explicit layer-gate audit, exact-stratum intake, and capacity tables."""
    candidates = list(candidates)
    screened = list(screened)
    audit = list(audit)
    anchors = _primary_direction_anchors(route_records)
    strata = _validate_strata(strata)
    effects = list(effects)
    fulltext_queue = list(fulltext_queue)

    screen_counts = _screen_counts(screened)
    biological_queue = (
        screen_counts["priority_for_shallow_source_coding"]
        + screen_counts["biological_context_needs_route_screen"]
    )
    screened_total = len(screened)
    screened_hold = screened_total - biological_queue
    audit_screenable = sum(int(text(row.get("route_screenable_rows")) or 0) for row in audit)
    audit_unassessed = sum(int(text(row.get("unassessed_rows")) or 0) for row in audit)

    strata_lookup = _stratum_lookup(strata)
    fulltext_by_cluster = _fulltext_lookup(fulltext_queue)
    effect_clusters = _effect_cluster_counts(effects)

    anchor_counts: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    primary_confirmed: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    intake_rows: list[dict[str, str]] = []
    exact_anchor_count = 0

    for index, row in enumerate(anchors, start=1):
        cell = (row["route"], row["trait_class"], row["outcome_class"], row["design_class"])
        stratum = strata_lookup.get(cell)
        queue = fulltext_by_cluster.get(row["study_cluster_id"], {})
        if stratum:
            exact_anchor_count += 1
            anchor_counts[cell].add(row["study_cluster_id"])
            target_stratum = stratum["stratum_id"]
            match_status = "exact_predeclared_stratum"
            source_confirmed = text(row.get("source_basis")) in PRIMARY_SOURCE_BASES
            if source_confirmed:
                primary_confirmed[cell].add(row["study_cluster_id"])
                source_gate = "primary_source_confirmed"
                numeric_gate = "ready_for_numeric_field_check"
                intake_status = "numeric_extraction_candidate"
            else:
                source_gate = "primary_source_not_yet_confirmed"
                numeric_gate = "requires_primary_source_and_numeric_fields"
                intake_status = "core_source_resolution_queue"
            queue_id = text(queue.get("queue_id"))
            fulltext_state = text(queue.get("full_text_state")) or "not_enqueued"
            required_fields = (
                "treatment/control definition; effect-compatible response unit and denominator; "
                "independent-panel identity; n and variance/raw fields; exact source locator"
            )
            deficit = max(0, int(stratum["min_clusters_exploratory"]) - len(anchor_counts[cell]))
            priority = "P1" if deficit <= 1 else "P2"
            decision_reason = (
                "Exact predeclared route/trait/outcome/design cell. Extract one primary effect only after source and panel checks."
            )
        else:
            target_stratum = ""
            match_status = "no_exact_predeclared_stratum"
            source_gate = "direction_map_source_basis_retained"
            numeric_gate = "do_not_force_into_current_quantitative_strata"
            intake_status = "direction_map_only"
            queue_id = text(queue.get("queue_id"))
            fulltext_state = text(queue.get("full_text_state")) or "not_enqueued"
            required_fields = "No numerical extraction under current protocol unless a future separately declared stratum is justified."
            priority = "P3"
            decision_reason = (
                "The record remains valuable for the route/direction map, but its exact outcome/design cell does not match a predeclared quantitative stratum."
            )

        intake_rows.append({
            "intake_id": f"MAI{index:03d}",
            "record_id": row["record_id"], "study_id": row["study_id"],
            "study_cluster_id": row["study_cluster_id"], "doi": row["doi"],
            "taxon": row["taxon"], "route": row["route"], "trait_role": row["trait_role"],
            "trait_class": row["trait_class"], "outcome_class": row["outcome_class"],
            "design_class": row["design_class"], "reported_direction": row["reported_direction"],
            "source_basis": row["source_basis"], "target_stratum_id": target_stratum,
            "stratum_match_status": match_status, "source_gate_status": source_gate,
            "numeric_gate_status": numeric_gate, "intake_status": intake_status,
            "extraction_priority": priority, "fulltext_queue_id": queue_id,
            "fulltext_state": fulltext_state, "required_primary_source_fields": required_fields,
            "decision_reason": decision_reason,
        })

    capacity_rows: list[dict[str, str]] = []
    for stratum in strata:
        cell = (stratum["route"], stratum["trait_class"], stratum["outcome_class"], stratum["design_class"])
        direction_n = len(anchor_counts[cell])
        primary_n = len(primary_confirmed[cell])
        effect_n = len(effect_clusters[cell])
        min_exploratory = int(stratum["min_clusters_exploratory"])
        min_stability = int(stratum["min_clusters_stability"])
        if effect_n >= min_stability:
            status = "ready_for_stable_meta_analysis"
            action = "Run the predeclared random-effects model and report heterogeneity."
        elif effect_n >= min_exploratory:
            status = "ready_for_exploratory_meta_analysis"
            action = "Run only the exploratory model and label the estimate unstable."
        elif direction_n == 0:
            status = "no_direction_anchor_in_fixed_corpus"
            action = "Freeze this stratum as unpopulated; do not seek a pooled estimate under the current fixed corpus."
        elif primary_n == 0:
            status = "source_resolution_required"
            action = "Recover primary source and numeric fields for the exact-stratum anchor(s); no pooling until effect rows exist."
        else:
            status = "numeric_extraction_required"
            action = "Complete effect conversion and panel checks for the primary-source-confirmed anchor(s)."
        capacity_rows.append({
            "stratum_id": stratum["stratum_id"], "route": stratum["route"],
            "trait_class": stratum["trait_class"], "outcome_class": stratum["outcome_class"],
            "effect_metric": stratum["effect_metric"], "design_class": stratum["design_class"],
            "min_clusters_exploratory": stratum["min_clusters_exploratory"],
            "min_clusters_stability": stratum["min_clusters_stability"],
            "direction_anchor_clusters": str(direction_n),
            "primary_source_confirmed_clusters": str(primary_n),
            "numeric_effect_clusters": str(effect_n),
            "shortfall_to_exploratory": str(max(0, min_exploratory - effect_n)),
            "shortfall_to_stability": str(max(0, min_stability - effect_n)),
            "capacity_status": status, "recommended_action": action,
        })

    gate_rows = [
        {
            "gate_id": "G01", "layer_from": "L1_discovery", "layer_to": "L2_biological_screen",
            "input_universe": "all_deduplicated_candidates", "input_count": str(len(candidates)),
            "pass_count": str(biological_queue), "hold_count": str(screened_hold),
            "gate_status": "fixed_metadata_rule",
            "filter_rule": "Pass only priority_for_shallow_source_coding or biological_context_needs_route_screen; retain all other candidates as discovery-only.",
            "interpretation_boundary": "This is metadata triage, not evidence that a route was measured.",
        },
        {
            "gate_id": "G02", "layer_from": "L2_audit", "layer_to": "L3_source_adjudication",
            "input_universe": "frozen_route_stratified_audit_cohort", "input_count": str(len(audit)),
            "pass_count": str(audit_screenable), "hold_count": str(audit_unassessed),
            "gate_status": "audit_calibration_only",
            "filter_rule": "A route can be adjudicated only with a usable source; unassessed rows remain unresolved and are never coded absent.",
            "interpretation_boundary": "The audit is a calibration sample, not an exhaustive numerator/denominator for the direction registry.",
        },
        {
            "gate_id": "G03", "layer_from": "L3_direction_map", "layer_to": "L4_meta_intake",
            "input_universe": "primary_source_adjudicated_direction_anchors", "input_count": str(len(anchors)),
            "pass_count": str(exact_anchor_count), "hold_count": str(len(anchors) - exact_anchor_count),
            "gate_status": "exact_predeclared_cell_match",
            "filter_rule": "Require included primary sign record plus exact match on route, trait class, outcome class, and design class to a predeclared stratum.",
            "interpretation_boundary": "Nonmatching anchors remain evidence-map records and cannot be widened into a numerical stratum post hoc.",
        },
        {
            "gate_id": "G04", "layer_from": "L4_meta_intake", "layer_to": "L5_numeric_effect",
            "input_universe": "exact_predeclared_intake_anchors", "input_count": str(exact_anchor_count),
            "pass_count": str(sum(len(value) for value in effect_clusters.values())),
            "hold_count": str(exact_anchor_count - sum(len(value) for value in effect_clusters.values())),
            "gate_status": "primary_source_numeric_fields_required",
            "filter_rule": "Require primary-source confirmation, compatible treatment/control contrast, independent panel identity, oriented effect metric, and uncertainty/raw fields.",
            "interpretation_boundary": "A full-text queue or an abstract direction is not a numerical effect.",
        },
    ]

    summary = {
        "schema_version": "meta_analysis_intake_v1",
        "fixed_corpus_rule": "No candidate-retrieval expansion is required for this intake assessment.",
        "input_counts": {
            "candidates": len(candidates), "screened": len(screened), "audit_rows": len(audit),
            "primary_direction_anchors": len(anchors), "exact_predeclared_intake_anchors": exact_anchor_count,
            "direction_map_only_anchors": len(anchors) - exact_anchor_count,
            "primary_effect_clusters": sum(len(value) for value in effect_clusters.values()),
        },
        "meta_analysis_verdict": (
            "No predeclared stratum is currently poolable. The immediate fixed-corpus task is primary-source and numeric-field recovery for the exact-stratum intake anchors."
        ),
    }
    return gate_rows, intake_rows, capacity_rows, summary


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
        f"- Deduplicated discovery candidates: {counts['candidates']}",
        f"- Screened candidates: {counts['screened']}",
        f"- Primary direction anchors: {counts['primary_direction_anchors']}",
        f"- Exact predeclared quantitative-cell anchors: {counts['exact_predeclared_intake_anchors']}",
        f"- Direction-map-only anchors: {counts['direction_map_only_anchors']}",
        f"- Extracted primary numeric effects: {counts['primary_effect_clusters']}", "",
        "## Fixed decision", "",
        summary["meta_analysis_verdict"], "",
        "## Gates", "",
        "| Gate | From → to | Input | Pass | Held | Rule |", "|---|---|---:|---:|---:|---|",
    ]
    for row in gates:
        lines.append(
            f"| {row['gate_id']} | {row['layer_from']} → {row['layer_to']} | {row['input_count']} | {row['pass_count']} | {row['hold_count']} | {row['filter_rule']} |"
        )
    lines.extend(["", "## Exact-stratum core extraction queue", "", "| Priority | Stratum | Study cluster | Source gate | Numeric gate |", "|---|---|---|---|---|"])
    for row in intake:
        if row["intake_status"] == "core_source_resolution_queue" or row["intake_status"] == "numeric_extraction_candidate":
            lines.append(
                f"| {row['extraction_priority']} | {row['target_stratum_id']} | {row['study_cluster_id']} | {row['source_gate_status']} | {row['numeric_gate_status']} |"
            )
    lines.extend(["", "## Stratum capacity", "", "| Stratum | Direction anchors | Source-confirmed | Numeric effects | Exploratory gap | Status |", "|---|---:|---:|---:|---:|---|"])
    for row in capacity:
        lines.append(
            f"| {row['stratum_id']} | {row['direction_anchor_clusters']} | {row['primary_source_confirmed_clusters']} | {row['numeric_effect_clusters']} | {row['shortfall_to_exploratory']} | {row['capacity_status']} |"
        )
    return "\n".join(lines) + "\n"


def write_intake_outputs(
    out_dir: str | Path,
    gate_rows: list[dict[str, str]],
    intake_rows: list[dict[str, str]],
    capacity_rows: list[dict[str, str]],
    summary: dict[str, object],
) -> None:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    _write_csv(destination / "layer_gate_audit.csv", GATE_FIELDS, gate_rows)
    _write_csv(destination / "meta_analysis_intake_queue.csv", INTAKE_FIELDS, intake_rows)
    _write_csv(destination / "meta_analysis_stratum_capacity.csv", CAPACITY_FIELDS, capacity_rows)
    (destination / "meta_analysis_intake_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    (destination / "FIXED_CORPUS_META_ANALYSIS_FOUNDATION.md").write_text(
        _markdown(gate_rows, intake_rows, capacity_rows, summary), encoding="utf-8"
    )
