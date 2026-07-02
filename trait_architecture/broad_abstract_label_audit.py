"""Build and summarize a fixed-corpus audit for broad abstract labels.

The broad L1 evidence map intentionally uses high-recall abstract co-mention
labels.  This module creates a finite, reproducible human-adjudication packet to
estimate how often those labels actually describe flower-context A/B/P/H content.

It does not retrieve new candidates, change the fixed L1 corpus, turn abstracts
into effect sizes, or estimate a model parameter.  The audit is strictly a
calibration of the broad-label layer.
"""

from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Iterable


EDGE_FIELDS = {
    "A_to_pollination": "candidate_A_to_P",
    "A_to_antagonism": "candidate_A_to_H",
    "B_to_antagonism": "candidate_B_to_H",
    "B_to_pollination": "candidate_B_to_P",
    "joint_channels": "candidate_joint_channels",
}
EDGE_ORDER = tuple(EDGE_FIELDS)
CORE_EDGES = EDGE_ORDER[:4]
SOURCE_BUCKETS = ("empirical_nonreview", "other")
CONTROL_LABEL = "floral_no_predicted_edge_control"
DEFAULT_NONJOINT_TARGET = 25
DEFAULT_SEED = 20260702
BINARY_CODES = frozenset({"yes", "no", "uncertain", "not_applicable"})
STUDY_ROLE_CODES = frozenset({
    "empirical_direct", "empirical_indirect", "review_synthesis", "background_or_other", "uncertain",
})
CODING_STATUS_CODES = frozenset({"unreviewed", "reviewed"})

PACKET_FIELDS = (
    "audit_id", "candidate_id", "doi", "title", "publication_year", "work_type", "container_title",
    "publisher", "route_families", "source_queries", "shallow_screen_status", "source_bucket",
    "abstract_retrieval_state", "crossref_lookup_status", "crossref_abstract_available", "abstract_code_status",
    "floral_context_signal", "empirical_language_signal", "review_language_signal", "A_signal", "B_signal",
    "P_signal", "H_signal", "W_signal", "shared_cost_language_signal", "candidate_A_to_P",
    "candidate_A_to_H", "candidate_B_to_H", "candidate_B_to_P", "candidate_joint_channels",
    "audit_strata", "target_model_edges", "selection_mode", "crossref_abstract_text", "coding_warning",
)
CODING_FIELDS = PACKET_FIELDS + (
    "coding_status", "coder_id", "coding_date", "human_floral_context", "human_A", "human_B", "human_P",
    "human_H", "human_W", "human_flower_specific_B", "human_study_role", "human_shared_cost",
    "adjudication_note",
)
DESIGN_FIELDS = (
    "target_label", "source_bucket", "sampling_scope", "population_count", "selected_count", "sampling_method",
    "selection_seed", "selection_rule", "source_artifact_boundary",
)
PRECISION_FIELDS = (
    "target_label", "source_bucket", "sampling_scope", "population_count", "selected_count", "reviewed_count",
    "human_coherent_count", "observed_precision", "calibration_status", "interpretation_boundary",
)
COVERAGE_FIELDS = (
    "target_label", "raw_predicted_candidate_coverage", "reviewed_audit_records", "human_coherent_audit_records",
    "calibrated_candidate_coverage_mean", "calibrated_candidate_coverage_ci_low",
    "calibrated_candidate_coverage_ci_high", "calibration_status", "interpretation_boundary",
)
CONTROL_FIELDS = (
    "source_bucket", "population_count", "selected_count", "reviewed_count", "human_any_edge_count",
    "observed_undetected_edge_rate", "calibration_status", "interpretation_boundary",
)
COMPLETION_FIELDS = (
    "metric", "value", "interpretation_boundary",
)


class BroadAbstractAuditError(ValueError):
    """Raised when the fixed map packet or audit sheet violates its contract."""


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
            raise BroadAbstractAuditError(f"{location} missing required columns: {', '.join(sorted(missing))}")
        return [{key: text(value) for key, value in row.items()} for row in reader]


def source_bucket(row: dict[str, str]) -> str:
    return "empirical_nonreview" if is_true(row.get("empirical_language_signal")) and not is_true(row.get("review_language_signal")) else "other"


def _validate_source_alignment(records: list[dict[str, str]], packet: list[dict[str, str]]) -> None:
    record_ids = [row["candidate_id"] for row in records]
    packet_ids = [row["candidate_id"] for row in packet]
    if len(record_ids) != len(set(record_ids)) or len(packet_ids) != len(set(packet_ids)):
        raise BroadAbstractAuditError("evidence records and abstract packet require unique candidate IDs")
    if set(record_ids) != set(packet_ids):
        raise BroadAbstractAuditError("evidence records and abstract packet must contain the same fixed candidate IDs")


def _allocate(population: dict[str, int], target: int) -> dict[str, int]:
    """Allocate a target sample across nonempty buckets with a five-item floor.

    Small frames are censused.  For larger frames, each nonempty bucket gets up to
    five records, then the remainder is apportioned by population size with a
    deterministic largest-remainder rule.
    """
    available = {bucket: count for bucket, count in population.items() if count > 0}
    total = sum(available.values())
    if total <= target:
        return dict(available)
    allocation = {bucket: min(count, 5) for bucket, count in available.items()}
    remaining = target - sum(allocation.values())
    if remaining <= 0:
        return allocation
    weights = sum(available.values())
    ideals = {bucket: remaining * available[bucket] / weights for bucket in available}
    for bucket in available:
        allocation[bucket] += min(available[bucket] - allocation[bucket], int(math.floor(ideals[bucket])))
    remaining = target - sum(allocation.values())
    order = sorted(available, key=lambda bucket: (ideals[bucket] % 1, available[bucket] - allocation[bucket], bucket), reverse=True)
    cursor = 0
    while remaining > 0:
        bucket = order[cursor % len(order)]
        if allocation[bucket] < available[bucket]:
            allocation[bucket] += 1
            remaining -= 1
        cursor += 1
    return allocation


def _sample_ids(rows: list[dict[str, str]], count: int, seed: int) -> list[str]:
    rows = sorted(rows, key=lambda row: row["candidate_id"])
    if count >= len(rows):
        return [row["candidate_id"] for row in rows]
    return sorted(random.Random(seed).sample([row["candidate_id"] for row in rows], count))


def _predicted_any_core_edge(row: dict[str, str]) -> bool:
    return any(is_true(row.get(EDGE_FIELDS[edge])) for edge in CORE_EDGES)


def build_audit_packet(
    evidence_records: Iterable[dict[str, str]],
    abstract_packet: Iterable[dict[str, str]],
    *, seed: int = DEFAULT_SEED,
    nonjoint_target: int = DEFAULT_NONJOINT_TARGET,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    """Select a reproducible label-audit packet from the fixed broad map.

    All predicted joint-channel records are censused.  Each core edge samples up
    to ``nonjoint_target`` nonjoint positives, stratified into empirical/nonreview
    and other records.  Flower-context records with no predicted core edge form a
    negative-control stratum using the same target size.
    """
    records = list(evidence_records)
    packet_rows = list(abstract_packet)
    _validate_source_alignment(records, packet_rows)
    packet_by_id = {row["candidate_id"]: row for row in packet_rows}

    joined: list[dict[str, str]] = []
    for row in records:
        merged = {**row, **packet_by_id[row["candidate_id"]]}
        merged["source_bucket"] = source_bucket(merged)
        joined.append(merged)

    membership: dict[str, set[str]] = defaultdict(set)
    design: list[dict[str, str]] = []
    boundary = "The candidate universe is fixed. Selection is from the supplied broad-map artifact only; no discovery query is run."

    joint_rows = [row for row in joined if is_true(row.get(EDGE_FIELDS["joint_channels"]))]
    for edge in CORE_EDGES:
        for bucket in SOURCE_BUCKETS:
            census = [row for row in joint_rows if row["source_bucket"] == bucket]
            for row in census:
                membership[row["candidate_id"]].add(f"{edge}__{bucket}__joint_census")
            design.append({
                "target_label": edge, "source_bucket": bucket, "sampling_scope": "joint_census",
                "population_count": str(len(census)), "selected_count": str(len(census)), "sampling_method": "census",
                "selection_seed": str(seed),
                "selection_rule": "All predicted joint A+B+P+H records; these are included in every core-edge calibration partition.",
                "source_artifact_boundary": boundary,
            })

    for edge_index, edge in enumerate(CORE_EDGES, start=1):
        field = EDGE_FIELDS[edge]
        residual = [row for row in joined if is_true(row.get(field)) and not is_true(row.get(EDGE_FIELDS["joint_channels"]))]
        population = {bucket: sum(row["source_bucket"] == bucket for row in residual) for bucket in SOURCE_BUCKETS}
        allocation = _allocate(population, nonjoint_target)
        for bucket in SOURCE_BUCKETS:
            frame = [row for row in residual if row["source_bucket"] == bucket]
            selected = _sample_ids(frame, allocation.get(bucket, 0), seed + edge_index * 100 + SOURCE_BUCKETS.index(bucket))
            for candidate_id in selected:
                membership[candidate_id].add(f"{edge}__{bucket}__nonjoint_sample")
            design.append({
                "target_label": edge, "source_bucket": bucket, "sampling_scope": "nonjoint_sample",
                "population_count": str(len(frame)), "selected_count": str(len(selected)),
                "sampling_method": "census" if len(selected) == len(frame) else "stratified_simple_random_sample",
                "selection_seed": str(seed + edge_index * 100 + SOURCE_BUCKETS.index(bucket)),
                "selection_rule": f"Predicted {edge} records excluding predicted joint-channel records; stratified by empirical/nonreview language.",
                "source_artifact_boundary": boundary,
            })

    control = [
        row for row in joined
        if is_true(row.get("floral_context_signal")) and not _predicted_any_core_edge(row)
    ]
    control_population = {bucket: sum(row["source_bucket"] == bucket for row in control) for bucket in SOURCE_BUCKETS}
    control_allocation = _allocate(control_population, nonjoint_target)
    for bucket in SOURCE_BUCKETS:
        frame = [row for row in control if row["source_bucket"] == bucket]
        selected = _sample_ids(frame, control_allocation.get(bucket, 0), seed + 900 + SOURCE_BUCKETS.index(bucket))
        for candidate_id in selected:
            membership[candidate_id].add(f"{CONTROL_LABEL}__{bucket}__sample")
        design.append({
            "target_label": CONTROL_LABEL, "source_bucket": bucket, "sampling_scope": "control_sample",
            "population_count": str(len(frame)), "selected_count": str(len(selected)),
            "sampling_method": "census" if len(selected) == len(frame) else "stratified_simple_random_sample",
            "selection_seed": str(seed + 900 + SOURCE_BUCKETS.index(bucket)),
            "selection_rule": "Flower-context records with no predicted A→P, A→H, B→H, or B→P candidate edge.",
            "source_artifact_boundary": boundary,
        })

    selected_ids = sorted(membership)
    joined_by_id = {row["candidate_id"]: row for row in joined}
    audit_packet: list[dict[str, str]] = []
    for ordinal, candidate_id in enumerate(selected_ids, start=1):
        row = joined_by_id[candidate_id]
        strata = sorted(membership[candidate_id])
        target_edges = sorted({stratum.split("__", 1)[0] for stratum in strata if not stratum.startswith(CONTROL_LABEL)})
        modes = sorted({"census" if "census" in stratum else "sample" for stratum in strata})
        packet = {
            "audit_id": f"BAA{ordinal:03d}",
            "candidate_id": candidate_id,
            "doi": text(row.get("doi")), "title": text(row.get("title")),
            "publication_year": text(row.get("publication_year")), "work_type": text(row.get("work_type")),
            "container_title": text(row.get("container_title")), "publisher": text(row.get("publisher")),
            "route_families": text(row.get("route_families")), "source_queries": text(row.get("source_queries")),
            "shallow_screen_status": text(row.get("shallow_screen_status")), "source_bucket": row["source_bucket"],
            "abstract_retrieval_state": text(row.get("abstract_retrieval_state")),
            "crossref_lookup_status": text(row.get("crossref_lookup_status")),
            "crossref_abstract_available": text(row.get("crossref_abstract_available")),
            "abstract_code_status": text(row.get("abstract_code_status")),
            "floral_context_signal": text(row.get("floral_context_signal")),
            "empirical_language_signal": text(row.get("empirical_language_signal")),
            "review_language_signal": text(row.get("review_language_signal")),
            "A_signal": text(row.get("A_signal")), "B_signal": text(row.get("B_signal")),
            "P_signal": text(row.get("P_signal")), "H_signal": text(row.get("H_signal")),
            "W_signal": text(row.get("W_signal")),
            "shared_cost_language_signal": text(row.get("shared_cost_language_signal")),
            "candidate_A_to_P": text(row.get("candidate_A_to_P")),
            "candidate_A_to_H": text(row.get("candidate_A_to_H")),
            "candidate_B_to_H": text(row.get("candidate_B_to_H")),
            "candidate_B_to_P": text(row.get("candidate_B_to_P")),
            "candidate_joint_channels": text(row.get("candidate_joint_channels")),
            "audit_strata": ";".join(strata), "target_model_edges": ";".join(target_edges),
            "selection_mode": ";".join(modes), "crossref_abstract_text": text(row.get("crossref_abstract_text")),
            "coding_warning": (
                "Audit the abstract against the stated labels. The packet is a shallow source check, not a causal effect or model-parameter extraction."
            ),
        }
        audit_packet.append(packet)

    coding_sheet = [
        {
            **row,
            "coding_status": "unreviewed", "coder_id": "", "coding_date": "",
            "human_floral_context": "", "human_A": "", "human_B": "", "human_P": "", "human_H": "",
            "human_W": "", "human_flower_specific_B": "", "human_study_role": "", "human_shared_cost": "",
            "adjudication_note": "",
        }
        for row in audit_packet
    ]
    return audit_packet, coding_sheet, design


def _human_yes(row: dict[str, str], key: str) -> bool:
    return text(row.get(key)).lower() == "yes"


def human_coherent_edge(row: dict[str, str], edge: str) -> bool:
    """Return whether human coding supports a predicted broad edge label."""
    if not _human_yes(row, "human_floral_context"):
        return False
    if edge == "A_to_pollination":
        return _human_yes(row, "human_A") and _human_yes(row, "human_P")
    if edge == "A_to_antagonism":
        return _human_yes(row, "human_A") and _human_yes(row, "human_H")
    if edge == "B_to_antagonism":
        return _human_yes(row, "human_B") and _human_yes(row, "human_flower_specific_B") and _human_yes(row, "human_H")
    if edge == "B_to_pollination":
        return _human_yes(row, "human_B") and _human_yes(row, "human_flower_specific_B") and _human_yes(row, "human_P")
    if edge == "joint_channels":
        return (
            _human_yes(row, "human_A") and _human_yes(row, "human_B") and _human_yes(row, "human_flower_specific_B")
            and _human_yes(row, "human_P") and _human_yes(row, "human_H")
        )
    raise BroadAbstractAuditError(f"unknown edge: {edge}")


def _audit_membership(row: dict[str, str], target_label: str, bucket: str, scope: str) -> bool:
    key = f"{target_label}__{bucket}__{scope}"
    return key in set(filter(None, text(row.get("audit_strata")).split(";")))


def validate_coding_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    rows = list(rows)
    identifiers: set[str] = set()
    for row in rows:
        audit_id = text(row.get("audit_id"))
        if not audit_id or audit_id in identifiers:
            raise BroadAbstractAuditError("coding sheet requires unique audit_id values")
        identifiers.add(audit_id)
        status = text(row.get("coding_status")).lower()
        if status not in CODING_STATUS_CODES:
            raise BroadAbstractAuditError(f"invalid coding_status for {audit_id}: {status}")
        if status == "reviewed":
            for field in (
                "human_floral_context", "human_A", "human_B", "human_P", "human_H", "human_W",
                "human_flower_specific_B", "human_shared_cost",
            ):
                if text(row.get(field)).lower() not in BINARY_CODES:
                    raise BroadAbstractAuditError(f"reviewed {audit_id} has invalid {field}")
            if text(row.get("human_study_role")).lower() not in STUDY_ROLE_CODES:
                raise BroadAbstractAuditError(f"reviewed {audit_id} has invalid human_study_role")
    return rows


def _beta_projection_samples(correct: int, reviewed: int, population: int, seed: int, draws: int = 20_000) -> list[float]:
    if reviewed == population:
        return [float(correct)] * draws
    rng = random.Random(seed)
    alpha, beta = 1 + correct, 1 + reviewed - correct
    return [population * rng.betavariate(alpha, beta) for _ in range(draws)]


def _interval(values: list[float]) -> tuple[float, float]:
    values = sorted(values)
    return values[round((len(values) - 1) * 0.025)], values[round((len(values) - 1) * 0.975)]


def summarize_audit(
    coding_rows: Iterable[dict[str, str]], design_rows: Iterable[dict[str, str]], *, seed: int = DEFAULT_SEED,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    """Summarize audit completion, stratum precision, calibrated coverage, and controls.

    Calibrated coverage is only emitted when every selected record in a design
    partition is reviewed.  The result is a label-calibrated candidate-coverage
    estimate, not a count of confirmed causal studies.
    """
    coding = validate_coding_rows(coding_rows)
    design = list(design_rows)
    required_design = set(DESIGN_FIELDS)
    for row in design:
        missing = required_design.difference(row)
        if missing:
            raise BroadAbstractAuditError(f"audit design missing columns: {', '.join(sorted(missing))}")

    reviewed = [row for row in coding if text(row.get("coding_status")).lower() == "reviewed"]
    completion = [
        {"metric": "packet_records", "value": str(len(coding)), "interpretation_boundary": "Fixed-packet records selected for manual abstract adjudication."},
        {"metric": "reviewed_records", "value": str(len(reviewed)), "interpretation_boundary": "Only reviewed rows can contribute to calibration."},
        {"metric": "completion_fraction", "value": f"{len(reviewed) / len(coding):.6f}" if coding else "", "interpretation_boundary": "Do not compute a final calibrated coverage estimate until all selected partition rows are reviewed."},
    ]

    precision_rows: list[dict[str, str]] = []
    partition_samples: dict[tuple[str, str, str], tuple[int, int, int, int]] = {}
    for design_row in design:
        label = text(design_row["target_label"])
        bucket = text(design_row["source_bucket"])
        scope = text(design_row["sampling_scope"])
        population = int(text(design_row["population_count"]) or 0)
        selected = int(text(design_row["selected_count"]) or 0)
        matching = [row for row in coding if _audit_membership(row, label, bucket, scope)]
        if len(matching) != selected:
            raise BroadAbstractAuditError(f"design/sample mismatch for {label} {bucket} {scope}")
        matching_reviewed = [row for row in matching if text(row.get("coding_status")).lower() == "reviewed"]
        if label == CONTROL_LABEL:
            coherent = sum(any(human_coherent_edge(row, edge) for edge in CORE_EDGES) for row in matching_reviewed)
        else:
            coherent = sum(human_coherent_edge(row, label) for row in matching_reviewed)
        status = "complete" if len(matching_reviewed) == selected else "incomplete"
        precision_rows.append({
            "target_label": label, "source_bucket": bucket, "sampling_scope": scope,
            "population_count": str(population), "selected_count": str(selected), "reviewed_count": str(len(matching_reviewed)),
            "human_coherent_count": str(coherent),
            "observed_precision": f"{coherent / len(matching_reviewed):.6f}" if matching_reviewed else "",
            "calibration_status": status,
            "interpretation_boundary": (
                "Human coherence is a label-validity judgement for broad abstract coverage; it is not direct causal-effect confirmation."
            ),
        })
        partition_samples[(label, bucket, scope)] = (population, selected, len(matching_reviewed), coherent)

    coverage_rows: list[dict[str, str]] = []
    for edge_index, edge in enumerate(EDGE_ORDER, start=1):
        partitions = [row for row in design if text(row["target_label"]) == edge]
        raw_total = sum(int(text(row["population_count"]) or 0) for row in partitions)
        review_total = 0
        coherent_total = 0
        samples: list[float] = [0.0] * 20_000
        complete = True
        for partition_index, row in enumerate(partitions, start=1):
            key = (edge, text(row["source_bucket"]), text(row["sampling_scope"]))
            population, selected, reviewed_count, correct = partition_samples[key]
            review_total += reviewed_count
            coherent_total += correct
            if reviewed_count != selected:
                complete = False
                continue
            contribution = _beta_projection_samples(correct, reviewed_count, population, seed + edge_index * 1000 + partition_index)
            samples = [left + right for left, right in zip(samples, contribution)]
        if complete:
            low, high = _interval(samples)
            mean = sum(samples) / len(samples)
            status = "complete"
            mean_text, low_text, high_text = f"{mean:.3f}", f"{low:.3f}", f"{high:.3f}"
        else:
            status = "incomplete"
            mean_text = low_text = high_text = ""
        coverage_rows.append({
            "target_label": edge, "raw_predicted_candidate_coverage": str(raw_total),
            "reviewed_audit_records": str(review_total), "human_coherent_audit_records": str(coherent_total),
            "calibrated_candidate_coverage_mean": mean_text, "calibrated_candidate_coverage_ci_low": low_text,
            "calibrated_candidate_coverage_ci_high": high_text, "calibration_status": status,
            "interpretation_boundary": (
                "This is a label-calibrated estimate of broad abstract candidate coverage in the fixed corpus, not a count of direct causal studies or a biological effect size."
            ),
        })

    control_rows: list[dict[str, str]] = []
    for bucket in SOURCE_BUCKETS:
        key = (CONTROL_LABEL, bucket, "control_sample")
        if key not in partition_samples:
            continue
        population, selected, reviewed_count, coherent = partition_samples[key]
        control_rows.append({
            "source_bucket": bucket, "population_count": str(population), "selected_count": str(selected),
            "reviewed_count": str(reviewed_count), "human_any_edge_count": str(coherent),
            "observed_undetected_edge_rate": f"{coherent / reviewed_count:.6f}" if reviewed_count else "",
            "calibration_status": "complete" if reviewed_count == selected else "incomplete",
            "interpretation_boundary": (
                "This control estimates missed broad edge labels among flower-context abstracts; it does not estimate a corpus-wide causal null."
            ),
        })
    return completion, precision_rows, coverage_rows, control_rows


def _write_csv(path: Path, fields: Iterable[str], rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        writer.writerows(rows)


def write_audit_packet(out_dir: str | Path, packet: list[dict[str, str]], coding: list[dict[str, str]], design: list[dict[str, str]]) -> None:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    _write_csv(destination / "broad_abstract_label_audit_packet.csv", PACKET_FIELDS, packet)
    _write_csv(destination / "broad_abstract_label_audit_coding_sheet.csv", CODING_FIELDS, coding)
    _write_csv(destination / "broad_abstract_label_audit_design.csv", DESIGN_FIELDS, design)
    (destination / "README.md").write_text(
        "# Broad abstract label audit packet\n\n"
        "Code each row as `reviewed` only after assigning all human label fields. Use `yes`, `no`, `uncertain`, or `not_applicable` for binary fields. "
        "The packet is selected from a fixed broad-map artifact and is not a new literature search.\n",
        encoding="utf-8",
    )


def write_audit_summary(out_dir: str | Path, completion: list[dict[str, str]], precision: list[dict[str, str]], coverage: list[dict[str, str]], control: list[dict[str, str]]) -> None:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    _write_csv(destination / "broad_abstract_label_audit_completion.csv", COMPLETION_FIELDS, completion)
    _write_csv(destination / "broad_abstract_label_precision.csv", PRECISION_FIELDS, precision)
    _write_csv(destination / "broad_abstract_edge_coverage_calibrated.csv", COVERAGE_FIELDS, coverage)
    _write_csv(destination / "broad_abstract_negative_control.csv", CONTROL_FIELDS, control)
    (destination / "broad_abstract_label_audit_summary.json").write_text(
        json.dumps({"completion": completion, "precision": precision, "coverage": coverage, "control": control}, indent=2),
        encoding="utf-8",
    )
