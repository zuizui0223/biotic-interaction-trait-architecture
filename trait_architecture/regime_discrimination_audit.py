"""Audit whether current directional evidence discriminates Part I scenarios.

The audit is deliberately narrow. It does not estimate a regime, fit parameters,
or treat an observed channel sign as a measurement of the A×D mixed partial.
It only asks whether a directionally resolved empirical channel stratum excludes
any of the already declared Part I parameter scenarios.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from typing import Iterable

from .model import ModelParameters


SCENARIO_FIELDS = (
    "scenario_id",
    "attraction_gain",
    "attraction_tracking",
    "floral_defence_efficacy",
    "defence_pollinator_cost",
    "attraction_defence_shared_cost",
    "functional_summary_cases",
    "modal_complementary_cases",
    "modal_substitutable_cases",
    "functional_form_robust_cases",
    "empirical_constraints_considered",
    "empirical_constraints_matched",
    "empirical_constraints_contradicted",
    "scenario_empirical_status",
    "regime_discrimination_status",
)
CONSTRAINT_FIELDS = (
    "route",
    "trait_class",
    "outcome_class",
    "design_class",
    "observed_direction",
    "independent_clusters",
    "parameter_name",
    "scenario_expected_direction",
    "constraint_status",
)

CHANNEL_PARAMETER = {
    "A_to_pollination": ("attraction_gain", "positive"),
    "A_to_antagonism": ("attraction_tracking", "positive"),
    "B_to_antagonism": ("floral_defence_efficacy", "negative"),
    "B_to_pollination": ("defence_pollinator_cost", "negative"),
}


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
            raise ValueError("scenario ids must be unique and overrides must be objects")
        unknown = set(overrides).difference(allowed)
        if unknown:
            raise ValueError(f"unknown scenario override(s): {', '.join(sorted(unknown))}")
        scenarios.append((scenario_id, replace(base, **{name: float(value) for name, value in overrides.items()})))
        seen.add(scenario_id)
    return scenarios


def resolved_direction_constraints(direction_rows: Iterable[dict[str, str]]) -> list[dict[str, object]]:
    """Return only empirically resolved strata that can constrain a channel sign.

    A stratum is usable only when the existing direction map already marks it
    mostly compatible or mostly contradictory, which requires >=3 evaluable
    independent clusters under the registered map rule.
    """

    constraints: list[dict[str, object]] = []
    for row in direction_rows:
        status = _text(row.get("direction_map_status"))
        if status not in {
            "mostly_compatible_with_channel_assumption",
            "mostly_contradictory_to_channel_assumption",
        }:
            continue
        route = _text(row.get("route"))
        if route not in CHANNEL_PARAMETER:
            raise ValueError(f"unmapped route in direction map: {route}")
        positive = _int(row.get("positive_count"), "positive_count")
        negative = _int(row.get("negative_count"), "negative_count")
        if positive == negative:
            raise ValueError("resolved directional stratum cannot have tied positive/negative counts")
        observed = "positive" if positive > negative else "negative"
        parameter_name, _ = CHANNEL_PARAMETER[route]
        constraints.append({
            "route": route,
            "trait_class": _text(row.get("trait_class")),
            "outcome_class": _text(row.get("outcome_class")),
            "design_class": _text(row.get("design_class")),
            "observed_direction": observed,
            "independent_clusters": _int(row.get("independent_clusters"), "independent_clusters"),
            "parameter_name": parameter_name,
        })
    return constraints


def parameter_channel_direction(parameter_value: float, active_direction: str) -> str:
    """Return the model's channel sign induced by a nonnegative channel coefficient."""

    if parameter_value < 0:
        raise ValueError("Part I channel parameters must be nonnegative")
    return active_direction if parameter_value > 0 else "neutral"


def scenario_signature_rows(functional_rows: Iterable[dict[str, str]]) -> dict[str, dict[str, int]]:
    """Summarise Part I modal signs by declared biological scenario."""

    counts: dict[str, Counter[str]] = {}
    for row in functional_rows:
        scenario_id = _text(row.get("parameter_scenario_id"))
        modal_sign = _text(row.get("modal_sign"))
        robustness = _text(row.get("functional_form_class"))
        if not scenario_id or modal_sign not in {"complementary", "substitutable", "neutral"}:
            raise ValueError("functional summary needs scenario ID and recognized modal sign")
        counter = counts.setdefault(scenario_id, Counter())
        counter["total"] += 1
        counter[f"modal_{modal_sign}"] += 1
        if robustness == "structurally_robust":
            counter["structurally_robust"] += 1
    return {
        scenario_id: {
            "total": counter["total"],
            "modal_complementary": counter["modal_complementary"],
            "modal_substitutable": counter["modal_substitutable"],
            "structurally_robust": counter["structurally_robust"],
        }
        for scenario_id, counter in counts.items()
    }


def audit_regime_discrimination(
    *,
    config: dict[str, object],
    functional_rows: Iterable[dict[str, str]],
    direction_rows: Iterable[dict[str, str]],
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    """Assess current empirical directional constraints against every Part I scenario."""

    scenarios = declared_scenarios(config)
    signatures = scenario_signature_rows(functional_rows)
    constraints = resolved_direction_constraints(direction_rows)
    scenario_rows: list[dict[str, object]] = []
    constraint_rows: list[dict[str, object]] = []

    for scenario_id, parameters in scenarios:
        if scenario_id not in signatures:
            raise ValueError(f"functional summary has no rows for declared scenario {scenario_id}")
        signature = signatures[scenario_id]
        matched = 0
        contradicted = 0
        for constraint in constraints:
            value = float(getattr(parameters, str(constraint["parameter_name"])))
            _, active_direction = CHANNEL_PARAMETER[str(constraint["route"])]
            expected = parameter_channel_direction(value, active_direction)
            if expected == constraint["observed_direction"]:
                status = "matches_directional_constraint"
                matched += 1
            else:
                status = "contradicts_directional_constraint"
                contradicted += 1
            constraint_rows.append({
                **constraint,
                "scenario_id": scenario_id,
                "scenario_expected_direction": expected,
                "constraint_status": status,
            })
        if contradicted:
            empirical_status = "excluded_by_current_directional_constraint"
        elif constraints:
            empirical_status = "directionally_compatible_not_magnitude_identified"
        else:
            empirical_status = "no_resolved_empirical_constraint"
        scenario_rows.append({
            "scenario_id": scenario_id,
            "attraction_gain": parameters.attraction_gain,
            "attraction_tracking": parameters.attraction_tracking,
            "floral_defence_efficacy": parameters.floral_defence_efficacy,
            "defence_pollinator_cost": parameters.defence_pollinator_cost,
            "attraction_defence_shared_cost": parameters.attraction_defence_shared_cost,
            "functional_summary_cases": signature["total"],
            "modal_complementary_cases": signature["modal_complementary"],
            "modal_substitutable_cases": signature["modal_substitutable"],
            "functional_form_robust_cases": signature["structurally_robust"],
            "empirical_constraints_considered": len(constraints),
            "empirical_constraints_matched": matched,
            "empirical_constraints_contradicted": contradicted,
            "scenario_empirical_status": empirical_status,
            "regime_discrimination_status": "not_identified_by_current_direction_only_evidence",
        })

    surviving = [row for row in scenario_rows if row["scenario_empirical_status"] != "excluded_by_current_directional_constraint"]
    has_comp = any(row["modal_complementary_cases"] > row["modal_substitutable_cases"] for row in surviving)
    has_sub = any(row["modal_substitutable_cases"] > row["modal_complementary_cases"] for row in surviving)
    report = {
        "scope": (
            "Current-data discrimination audit only. Directional evidence is used to screen declared channel signs, "
            "not to estimate parameter magnitudes or the A×D mixed partial."
        ),
        "resolved_empirical_constraints": len(constraints),
        "constraint_routes": sorted({str(row["route"]) for row in constraints}),
        "declared_scenario_count": len(scenarios),
        "surviving_scenario_count": len(surviving),
        "excluded_scenario_count": len(scenario_rows) - len(surviving),
        "regime_discrimination": (
            "not_identified_current_constraints_allow_both_complementary_and_substitutable_scenarios"
            if has_comp and has_sub
            else "partially_discriminated_by_current_constraints"
        ),
        "parameter_magnitude_status": "not_identified_from_direction_only_evidence",
        "boundary": (
            "A matching B_to_pollination sign constrains the sign of defence_pollinator_cost only. "
            "It does not distinguish low from high obstruction, quantify shared cost, or select a complementarity/substitutability regime."
        ),
    }
    return report, scenario_rows, constraint_rows


def write_audit_outputs(
    out_dir: str | Path,
    *,
    config_path: str | Path,
    functional_summary_path: str | Path,
    direction_map_path: str | Path,
) -> dict[str, object]:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Part I config must be a JSON object")
    report, scenarios, constraints = audit_regime_discrimination(
        config=config,
        functional_rows=read_csv_rows(functional_summary_path),
        direction_rows=read_csv_rows(direction_map_path),
    )
    write_csv_rows(destination / "scenario_empirical_discrimination.csv", SCENARIO_FIELDS, scenarios)
    write_csv_rows(destination / "scenario_direction_constraints.csv", CONSTRAINT_FIELDS + ("scenario_id",), constraints)
    (destination / "regime_discrimination_audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return report
