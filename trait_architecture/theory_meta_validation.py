"""Validate the current theory-to-meta-analysis evidence boundary.

This module does not estimate new biological parameters. It checks that the
predeclared Part I robustness run reproduces from its configuration, then reads
the existing broad direction map and quantitative synthesis outputs to state
exactly which empirical checks are presently supported.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Iterable


DIRECTION_FIELDS = (
    "route", "trait_class", "outcome_class", "design_class", "expected_effect_direction",
    "independent_clusters", "positive_count", "negative_count", "mixed_count", "null_count",
    "not_reported_count", "evaluable_direction_count", "compatible_count", "contradictory_count",
    "compatible_fraction", "direction_map_status",
)
CHECK_FIELDS = DIRECTION_FIELDS + (
    "channel_validation_status",
    "validation_scope",
    "parameter_calibration_status",
)


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _int(value: object, field: str) -> int:
    try:
        number = int(_text(value))
    except ValueError as error:
        raise ValueError(f"{field} must be an integer") from error
    if number < 0:
        raise ValueError(f"{field} must be non-negative")
    return number


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return [{key: _text(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def write_csv_rows(path: str | Path, fields: Iterable[str], rows: Iterable[dict[str, object]]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def expected_part_i_dimensions(config: dict[str, object]) -> dict[str, int]:
    """Calculate the exact declared Part I grid size from its immutable config."""

    grid = config.get("phenotype_and_regime_grid")
    scenarios = config.get("parameter_scenarios")
    forms = config.get("functional_forms")
    if not isinstance(grid, dict) or not isinstance(scenarios, list) or not isinstance(forms, list):
        raise ValueError("Part I config lacks grid, scenarios, or functional forms")
    grid_keys = ("attraction", "defence", "assurance", "pollinator_service", "floral_damage_pressure")
    counts: list[int] = []
    for key in grid_keys:
        values = grid.get(key)
        if not isinstance(values, list) or not values:
            raise ValueError(f"Part I grid {key} must be a non-empty list")
        counts.append(len(values))
    case_count = math.prod(counts)
    if not scenarios or not forms:
        raise ValueError("Part I scenarios and functional forms must be non-empty")
    return {
        "case_count": case_count,
        "parameter_scenario_count": len(scenarios),
        "functional_form_count": len(forms),
        "evaluation_count": case_count * len(scenarios) * len(forms),
        "functional_form_summary_count": case_count * len(scenarios),
    }


def validate_part_i_run(config: dict[str, object], report: dict[str, object]) -> dict[str, object]:
    """Confirm that generated Part I dimensions exactly match the predeclared config."""

    expected = expected_part_i_dimensions(config)
    actual = {
        key: _int(report.get(key), f"Part I report {key}")
        for key in ("case_count", "evaluation_count", "functional_form_summary_count")
    }
    mismatches = {
        key: {"expected": expected[key], "actual": actual[key]}
        for key in actual
        if expected[key] != actual[key]
    }
    classes = report.get("parameter_envelope_class_counts")
    if not isinstance(classes, dict):
        raise ValueError("Part I report lacks parameter_envelope_class_counts")
    class_total = sum(_int(classes.get(name), f"parameter_envelope_class_counts.{name}") for name in (
        "structurally_robust", "conditional_majority", "mixed_or_sensitive",
    ))
    if class_total != expected["case_count"]:
        mismatches["parameter_envelope_class_total"] = {
            "expected": expected["case_count"], "actual": class_total,
        }
    return {
        "status": "reproduced" if not mismatches else "mismatch",
        "expected_dimensions": expected,
        "actual_dimensions": actual,
        "parameter_envelope_class_total": class_total,
        "mismatches": mismatches,
    }


def _channel_status(row: dict[str, str]) -> tuple[str, str]:
    status = row["direction_map_status"]
    if status == "mostly_compatible_with_channel_assumption":
        return (
            "directionally_consistent_in_restricted_stratum",
            "Channel-sign check only; not a whole-model or parameter-magnitude validation.",
        )
    if status == "mostly_contradictory_to_channel_assumption":
        return (
            "directionally_contradictory_in_restricted_stratum",
            "Restricted stratum contradicts the declared channel sign and must remain visible.",
        )
    if status == "mixed_or_context_dependent":
        return (
            "mixed_or_context_dependent",
            "No one directional conclusion is warranted for this stratum.",
        )
    if status == "insufficient_directional_clusters":
        return (
            "insufficient_directional_clusters",
            "Fewer than three evaluable independent clusters; do not validate a channel sign.",
        )
    raise ValueError(f"unknown direction_map_status: {status}")


def validate_direction_map(rows: Iterable[dict[str, str]]) -> list[dict[str, object]]:
    """Annotate existing direction strata without changing their statistical labels."""

    checks: list[dict[str, object]] = []
    for row in rows:
        missing = [field for field in DIRECTION_FIELDS if field not in row]
        if missing:
            raise ValueError(f"direction map lacks fields: {', '.join(missing)}")
        independent = _int(row["independent_clusters"], "independent_clusters")
        evaluable = _int(row["evaluable_direction_count"], "evaluable_direction_count")
        compatible = _int(row["compatible_count"], "compatible_count")
        contradictory = _int(row["contradictory_count"], "contradictory_count")
        if compatible + contradictory > evaluable:
            raise ValueError("direction map compatible and contradictory counts exceed evaluable count")
        status, scope = _channel_status(row)
        checks.append({
            **row,
            "channel_validation_status": status,
            "validation_scope": scope,
            "parameter_calibration_status": "not_calibrated_from_direction_only_evidence",
        })
    return checks


def validate_quantitative_summary(rows: Iterable[dict[str, str]]) -> dict[str, object]:
    """State whether any predeclared quantitative stratum is actually poolable."""

    rows = list(rows)
    required = {"analysis_status", "effect_count", "independent_clusters"}
    for row in rows:
        missing = required.difference(row)
        if missing:
            raise ValueError(f"quantitative summary lacks fields: {', '.join(sorted(missing))}")
    pooled = [row for row in rows if row["analysis_status"] != "insufficient_independent_clusters"]
    effect_count = sum(_int(row["effect_count"], "effect_count") for row in rows)
    return {
        "configured_strata": len(rows),
        "eligible_effect_count": effect_count,
        "pooled_strata_count": len(pooled),
        "status": "quantitative_synthesis_not_ready" if not pooled else "quantitative_synthesis_present",
        "boundary": (
            "Direction-only records cannot calibrate Part I magnitude parameters. "
            "Only a pooled compatible effect stratum can inform a standardized sensitivity envelope."
        ),
    }


def build_validation_report(
    *,
    part_i_config: dict[str, object],
    part_i_report: dict[str, object],
    direction_rows: Iterable[dict[str, str]],
    quantitative_rows: Iterable[dict[str, str]],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    part_i = validate_part_i_run(part_i_config, part_i_report)
    direction_checks = validate_direction_map(direction_rows)
    quantitative = validate_quantitative_summary(quantitative_rows)
    aligned = [row for row in direction_checks if row["channel_validation_status"] == "directionally_consistent_in_restricted_stratum"]
    contradictory = [row for row in direction_checks if row["channel_validation_status"] == "directionally_contradictory_in_restricted_stratum"]
    report = {
        "validation_scope": (
            "Current-data verification only: reproduce the predeclared Part I grid, inspect existing broad direction strata, "
            "and confirm whether any compatible quantitative synthesis is ready."
        ),
        "part_i_computation": part_i,
        "broad_direction_map": {
            "registered_strata": len(direction_checks),
            "restricted_directional_alignment_strata": len(aligned),
            "restricted_directional_contradiction_strata": len(contradictory),
            "aligned_strata": [
                {
                    "route": row["route"],
                    "trait_class": row["trait_class"],
                    "outcome_class": row["outcome_class"],
                    "design_class": row["design_class"],
                    "independent_clusters": _int(row["independent_clusters"], "independent_clusters"),
                    "expected_effect_direction": row["expected_effect_direction"],
                    "compatible_count": _int(row["compatible_count"], "compatible_count"),
                    "contradictory_count": _int(row["contradictory_count"], "contradictory_count"),
                }
                for row in aligned
            ],
        },
        "quantitative_meta_analysis": quantitative,
        "integrated_verdict": {
            "part_i_regime_map": (
                "reproduced" if part_i["status"] == "reproduced" else "failed_reproduction_check"
            ),
            "channel_sign_validation": (
                "limited_restricted_support_only" if aligned else "no_directional_stratum_reaches_minimum"
            ),
            "regime_level_empirical_validation": "not_evaluable_from_current_single-route_records",
            "parameter_magnitude_calibration": (
                "not_ready" if quantitative["status"] == "quantitative_synthesis_not_ready" else "available_for_review"
            ),
            "prohibited_claims": [
                "No universal attraction–barrier sign is validated.",
                "No model mixed-partial regime is empirically estimated from the current records.",
                "No Part I parameter magnitude is calibrated from direction-only evidence.",
            ],
        },
    }
    return report, direction_checks


def write_validation_outputs(
    out_dir: str | Path,
    *,
    part_i_config_path: str | Path,
    part_i_report_path: str | Path,
    direction_map_path: str | Path,
    quantitative_summary_path: str | Path,
) -> dict[str, object]:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    config = json.loads(Path(part_i_config_path).read_text(encoding="utf-8"))
    report = json.loads(Path(part_i_report_path).read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not isinstance(report, dict):
        raise ValueError("Part I config and report must be JSON objects")
    validation, checks = build_validation_report(
        part_i_config=config,
        part_i_report=report,
        direction_rows=read_csv_rows(direction_map_path),
        quantitative_rows=read_csv_rows(quantitative_summary_path),
    )
    write_csv_rows(destination / "theory_meta_directional_checks.csv", CHECK_FIELDS, checks)
    (destination / "theory_meta_validation.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True), encoding="utf-8"
    )
    return validation
