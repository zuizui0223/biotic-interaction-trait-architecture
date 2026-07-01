"""Assess whether registered direction evidence discriminates Part I scenarios.

This is a sign-constraint audit only. It never fits coefficient magnitudes or
uses a direct route record as an estimate of the A×D mixed partial.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from typing import Iterable

from .model import ModelParameters


CHANNELS = {
    "A_to_pollination": ("attraction_gain", "positive"),
    "A_to_antagonism": ("attraction_tracking", "positive"),
    "B_to_antagonism": ("floral_defence_efficacy", "negative"),
    "B_to_pollination": ("defence_pollinator_cost", "negative"),
}

SCENARIO_FIELDS = (
    "scenario_id", "attraction_gain", "attraction_tracking", "floral_defence_efficacy",
    "defence_pollinator_cost", "attraction_defence_shared_cost", "functional_summary_cases",
    "modal_complementary_cases", "modal_substitutable_cases", "functional_form_robust_cases",
    "empirical_constraints_considered", "empirical_constraints_matched",
    "empirical_constraints_contradicted", "scenario_empirical_status",
    "regime_discrimination_status",
)
CONSTRAINT_FIELDS = (
    "scenario_id", "route", "trait_class", "outcome_class", "design_class",
    "observed_direction", "independent_clusters", "parameter_name",
    "scenario_expected_direction", "constraint_status",
)


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _int(value: object, field: str) -> int:
    try:
        result = int(_text(value))
    except ValueError as error:
        raise ValueError(f"{field} must be an integer") from error
    if result < 0:
        raise ValueError(f"{field} must be non-negative")
    return result


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


def declared_scenarios(config: dict[str, object]) -> list[tuple[str, ModelParameters]]:
    raw = config.get("parameter_scenarios")
    if not isinstance(raw, list) or not raw:
        raise ValueError("Part I config needs non-empty parameter_scenarios")
    base = ModelParameters()
    allowed = set(asdict(base))
    scenarios: list[tuple[str, ModelParameters]] = []
    seen: set[str] = set()
    for entry in raw:
        if not isinstance(entry, dict):
            raise ValueError("each parameter scenario must be an object")
        scenario_id = _text(entry.get("scenario_id"))
        overrides = entry.get("overrides", {})
        if not scenario_id or scenario_id in seen or not isinstance(overrides, dict):
            raise ValueError("scenario IDs must be unique and overrides must be objects")
        unknown = set(overrides).difference(allowed)
        if unknown:
            raise ValueError(f"unknown Part I parameter(s): {', '.join(sorted(unknown))}")
        scenarios.append((scenario_id, replace(base, **{key: float(value) for key, value in overrides.items()})))
        seen.add(scenario_id)
    return scenarios


def resolved_constraints(direction_rows: Iterable[dict[str, str]]) -> list[dict[str, object]]:
    """Keep only strata already directionally resolved under the existing map rule."""

    constraints: list[dict[str, object]] = []
    for row in direction_rows:
        status = _text(row.get("direction_map_status"))
        if status not in {"mostly_compatible_with_channel_assumption", "mostly_contradictory_to_channel_assumption"}:
            continue
        route = _text(row.get("route"))
        if route not in CHANNELS:
            raise ValueError(f"direction map route has no Part I channel: {route}")
        positive = _int(row.get("positive_count"), "positive_count")
        negative = _int(row.get("negative_count"), "negative_count")
        if positive == negative:
            raise ValueError("resolved directional stratum cannot have tied signs")
        coefficient, _ = CHANNELS[route]
        constraints.append({
            "route": route,
            "trait_class": _text(row.get("trait_class")),
            "outcome_class": _text(row.get("outcome_class")),
            "design_class": _text(row.get("design_class")),
            "observed_direction": "positive" if positive > negative else "negative",
            "independent_clusters": _int(row.get("independent_clusters"), "independent_clusters"),
            "parameter_name": coefficient,
        })
    return constraints


def scenario_sign(value: float, active_sign: str) -> str:
    if value < 0:
        raise ValueError("Part I channel parameters must be non-negative")
    return active_sign if value > 0 else "neutral"


def functional_signature(rows: Iterable[dict[str, str]]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = {}
    for row in rows:
        scenario_id = _text(row.get("parameter_scenario_id"))
        modal = _text(row.get("modal_sign"))
        robustness = _text(row.get("functional_form_class"))
        if not scenario_id or modal not in {"complementary", "substitutable", "neutral"}:
            raise ValueError("functional summary has invalid scenario or modal sign")
        tally = counts.setdefault(scenario_id, Counter())
        tally["total"] += 1
        tally[modal] += 1
        if robustness == "structurally_robust":
            tally["robust"] += 1
    return {
        key: {
            "total": value["total"],
            "complementary": value["complementary"],
            "substitutable": value["substitutable"],
            "robust": value["robust"],
        }
        for key, value in counts.items()
    }


def audit(
    *, config: dict[str, object], functional_rows: Iterable[dict[str, str]], direction_rows: Iterable[dict[str, str]]
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    scenarios = declared_scenarios(config)
    signatures = functional_signature(functional_rows)
    constraints = resolved_constraints(direction_rows)
    scenario_rows: list[dict[str, object]] = []
    constraint_rows: list[dict[str, object]] = []

    for scenario_id, parameters in scenarios:
        if scenario_id not in signatures:
            raise ValueError(f"functional summary lacks declared scenario {scenario_id}")
        signature = signatures[scenario_id]
        matched = contradicted = 0
        for constraint in constraints:
            coefficient, active_sign = CHANNELS[str(constraint["route"])]
            expected = scenario_sign(float(getattr(parameters, coefficient)), active_sign)
            status = "matches_directional_constraint" if expected == constraint["observed_direction"] else "contradicts_directional_constraint"
            matched += status == "matches_directional_constraint"
            contradicted += status == "contradicts_directional_constraint"
            constraint_rows.append({**constraint, "scenario_id": scenario_id, "scenario_expected_direction": expected, "constraint_status": status})
        empirical_status = (
            "excluded_by_current_directional_constraint" if contradicted else
            "directionally_compatible_not_magnitude_identified" if constraints else
            "no_resolved_empirical_constraint"
        )
        scenario_rows.append({
            "scenario_id": scenario_id,
            "attraction_gain": parameters.attraction_gain,
            "attraction_tracking": parameters.attraction_tracking,
            "floral_defence_efficacy": parameters.floral_defence_efficacy,
            "defence_pollinator_cost": parameters.defence_pollinator_cost,
            "attraction_defence_shared_cost": parameters.attraction_defence_shared_cost,
            "functional_summary_cases": signature["total"],
            "modal_complementary_cases": signature["complementary"],
            "modal_substitutable_cases": signature["substitutable"],
            "functional_form_robust_cases": signature["robust"],
            "empirical_constraints_considered": len(constraints),
            "empirical_constraints_matched": matched,
            "empirical_constraints_contradicted": contradicted,
            "scenario_empirical_status": empirical_status,
            "regime_discrimination_status": "not_identified_by_current_direction_only_evidence",
        })

    survivors = [row for row in scenario_rows if row["scenario_empirical_status"] != "excluded_by_current_directional_constraint"]
    has_complementary = any(row["modal_complementary_cases"] > row["modal_substitutable_cases"] for row in survivors)
    has_substitutable = any(row["modal_substitutable_cases"] > row["modal_complementary_cases"] for row in survivors)
    report = {
        "scope": "Sign-constraint audit of existing Part I scenarios using existing registered direction strata only.",
        "resolved_empirical_constraints": len(constraints),
        "constraint_routes": sorted({str(row["route"]) for row in constraints}),
        "declared_scenario_count": len(scenarios),
        "surviving_scenario_count": len(survivors),
        "excluded_scenario_count": len(scenario_rows) - len(survivors),
        "regime_discrimination": (
            "not_identified_current_constraints_allow_both_complementary_and_substitutable_scenarios"
            if has_complementary and has_substitutable else "partially_discriminated_by_current_constraints"
        ),
        "parameter_magnitude_status": "not_identified_from_direction_only_evidence",
        "boundary": (
            "A B_to_pollination sign constraint can exclude a zero or opposite pollination-cost channel, but cannot distinguish low from high positive defence_pollinator_cost or identify shared allocation cost."
        ),
    }
    return report, scenario_rows, constraint_rows


def write_audit_outputs(
    out_dir: str | Path, *, config_path: str | Path, functional_summary_path: str | Path, direction_map_path: str | Path
) -> dict[str, object]:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Part I config must be a JSON object")
    report, scenarios, constraints = audit(
        config=config,
        functional_rows=read_csv_rows(functional_summary_path),
        direction_rows=read_csv_rows(direction_map_path),
    )
    write_csv_rows(destination / "scenario_empirical_discrimination.csv", SCENARIO_FIELDS, scenarios)
    write_csv_rows(destination / "scenario_direction_constraints.csv", CONSTRAINT_FIELDS, constraints)
    (destination / "regime_discrimination_audit.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report
