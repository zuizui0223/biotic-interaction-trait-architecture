"""Run the predeclared Part I functional-form robustness sweep.

The runner produces three linked outputs:

1. every local mixed-partial evaluation;
2. within-scenario sign stability across alternative functional forms; and
3. the sign envelope across all predeclared biological parameter scenarios.

This separation matters. Changing a response curve tests functional-form
robustness, whereas changing tracking, obstruction, or shared-cost coefficients
tests genuine biological parameter sensitivity. The outputs are qualitative and
must not be interpreted as empirical parameter estimates.

Usage:
    python scripts/run_part_i_robustness.py \
      configs/part_i_robustness_grid.json artifacts/part_i_robustness
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Iterable

from trait_architecture.model import ModelParameters
from trait_architecture.robustness import (
    FunctionalForm,
    MixedPartialResult,
    RobustnessCase,
    cartesian_cases,
    mixed_partial,
    summarise_case,
)


CASE_FIELDS = [
    "case_id",
    "parameter_scenario_id",
    "form_id",
    "attraction",
    "defence",
    "assurance",
    "pollinator_service",
    "floral_damage_pressure",
    "attraction_gain",
    "attraction_tracking",
    "floral_defence_efficacy",
    "defence_pollinator_cost",
    "attraction_defence_shared_cost",
    "attraction_saturation",
    "defence_half_saturation",
    "shared_cost_curvature",
    "antagonism_term",
    "pollination_obstruction_term",
    "shared_cost_term",
    "mixed_partial",
    "sign",
]
FUNCTIONAL_FORM_SUMMARY_FIELDS = [
    "case_id",
    "parameter_scenario_id",
    "attraction",
    "defence",
    "assurance",
    "pollinator_service",
    "floral_damage_pressure",
    "modal_sign",
    "non_neutral_form_count",
    "total_form_count",
    "modal_sign_agreement",
    "functional_form_class",
]
ENVELOPE_SUMMARY_FIELDS = [
    "case_id",
    "attraction",
    "defence",
    "assurance",
    "pollinator_service",
    "floral_damage_pressure",
    "modal_sign",
    "non_neutral_evaluation_count",
    "total_evaluation_count",
    "modal_sign_agreement",
    "envelope_class",
    "functional_form_robust_scenario_count",
    "parameter_scenario_count",
]


def _as_float_list(value: object, name: str) -> list[float]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a non-empty list")
    values: list[float] = []
    for item in value:
        try:
            values.append(float(item))
        except (TypeError, ValueError) as error:
            raise ValueError(f"{name} contains a non-numeric value") from error
    return values


def _read_config(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("robustness config must be a JSON object")
    return payload


def _functional_forms(config: dict[str, Any]) -> tuple[FunctionalForm, ...]:
    raw_forms = config.get("functional_forms")
    if not isinstance(raw_forms, list) or not raw_forms:
        raise ValueError("functional_forms must be a non-empty list")
    forms: list[FunctionalForm] = []
    seen: set[str] = set()
    for raw in raw_forms:
        if not isinstance(raw, dict):
            raise ValueError("each functional form must be an object")
        form = FunctionalForm(
            form_id=str(raw.get("form_id") or "").strip(),
            attraction_saturation=float(raw.get("attraction_saturation", 0.0)),
            defence_half_saturation=(
                None if raw.get("defence_half_saturation") is None
                else float(raw["defence_half_saturation"])
            ),
            shared_cost_curvature=float(raw.get("shared_cost_curvature", 0.0)),
        )
        if form.form_id in seen:
            raise ValueError(f"duplicate functional-form id: {form.form_id}")
        seen.add(form.form_id)
        forms.append(form)
    return tuple(forms)


def _parameter_scenarios(config: dict[str, Any]) -> tuple[tuple[str, ModelParameters], ...]:
    raw_scenarios = config.get("parameter_scenarios")
    if not isinstance(raw_scenarios, list) or not raw_scenarios:
        raise ValueError("parameter_scenarios must be a non-empty list")
    base = ModelParameters()
    allowed = set(asdict(base))
    scenarios: list[tuple[str, ModelParameters]] = []
    seen: set[str] = set()
    for raw in raw_scenarios:
        if not isinstance(raw, dict):
            raise ValueError("each parameter scenario must be an object")
        scenario_id = str(raw.get("scenario_id") or "").strip()
        if not scenario_id or scenario_id in seen:
            raise ValueError("parameter scenario ids must be non-empty and unique")
        overrides = raw.get("overrides", {})
        if not isinstance(overrides, dict):
            raise ValueError(f"overrides for {scenario_id} must be an object")
        unexpected = sorted(set(overrides).difference(allowed))
        if unexpected:
            raise ValueError(f"unknown ModelParameters field(s): {', '.join(unexpected)}")
        numeric_overrides = {key: float(value) for key, value in overrides.items()}
        scenarios.append((scenario_id, replace(base, **numeric_overrides)))
        seen.add(scenario_id)
    return tuple(scenarios)


def _cases(config: dict[str, Any]) -> tuple[RobustnessCase, ...]:
    grid = config.get("phenotype_and_regime_grid")
    if not isinstance(grid, dict):
        raise ValueError("phenotype_and_regime_grid must be an object")
    return cartesian_cases(
        attraction=_as_float_list(grid.get("attraction"), "attraction"),
        defence=_as_float_list(grid.get("defence"), "defence"),
        assurance=_as_float_list(grid.get("assurance"), "assurance"),
        pollinator_service=_as_float_list(grid.get("pollinator_service"), "pollinator_service"),
        floral_damage_pressure=_as_float_list(grid.get("floral_damage_pressure"), "floral_damage_pressure"),
    )


def _case_dimensions(case: RobustnessCase) -> dict[str, float | str]:
    return {
        "case_id": case.case_id,
        "attraction": case.attraction,
        "defence": case.defence,
        "assurance": case.assurance,
        "pollinator_service": case.pollinator_service,
        "floral_damage_pressure": case.floral_damage_pressure,
    }


def run(
    config: dict[str, Any],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    """Return evaluations, within-scenario summaries, and full-envelope summaries."""

    tolerance = float(config.get("neutral_tolerance", 1e-12))
    if tolerance < 0:
        raise ValueError("neutral_tolerance must be non-negative")
    forms = _functional_forms(config)
    scenarios = _parameter_scenarios(config)
    cases = _cases(config)
    case_rows: list[dict[str, object]] = []
    grouped_by_scenario: dict[tuple[str, str], list[MixedPartialResult]] = {}
    grouped_by_case: dict[str, list[MixedPartialResult]] = {case.case_id: [] for case in cases}

    for case in cases:
        for scenario_id, parameters in scenarios:
            scenario_results: list[MixedPartialResult] = []
            for form in forms:
                result = mixed_partial(case, parameters, form, tolerance=tolerance)
                scenario_results.append(result)
                grouped_by_case[case.case_id].append(result)
                case_rows.append(
                    {
                        **_case_dimensions(case),
                        "parameter_scenario_id": scenario_id,
                        "form_id": form.form_id,
                        "attraction_gain": parameters.attraction_gain,
                        "attraction_tracking": parameters.attraction_tracking,
                        "floral_defence_efficacy": parameters.floral_defence_efficacy,
                        "defence_pollinator_cost": parameters.defence_pollinator_cost,
                        "attraction_defence_shared_cost": parameters.attraction_defence_shared_cost,
                        "attraction_saturation": form.attraction_saturation,
                        "defence_half_saturation": "" if form.defence_half_saturation is None else form.defence_half_saturation,
                        "shared_cost_curvature": form.shared_cost_curvature,
                        "antagonism_term": result.antagonism_term,
                        "pollination_obstruction_term": result.pollination_obstruction_term,
                        "shared_cost_term": result.shared_cost_term,
                        "mixed_partial": result.mixed_partial,
                        "sign": result.sign,
                    }
                )
            grouped_by_scenario[(case.case_id, scenario_id)] = scenario_results

    by_id = {case.case_id: case for case in cases}
    functional_form_summaries: list[dict[str, object]] = []
    scenario_classes: dict[tuple[str, str], str] = {}
    for (case_id, scenario_id), results in sorted(grouped_by_scenario.items()):
        summary = summarise_case(results)
        scenario_classes[(case_id, scenario_id)] = summary.robustness_class
        functional_form_summaries.append(
            {
                **_case_dimensions(by_id[case_id]),
                "parameter_scenario_id": scenario_id,
                "modal_sign": summary.modal_sign,
                "non_neutral_form_count": summary.non_neutral_form_count,
                "total_form_count": summary.total_form_count,
                "modal_sign_agreement": summary.modal_sign_agreement,
                "functional_form_class": summary.robustness_class,
            }
        )

    envelope_summaries: list[dict[str, object]] = []
    for case_id, results in sorted(grouped_by_case.items()):
        summary = summarise_case(results)
        envelope_summaries.append(
            {
                **_case_dimensions(by_id[case_id]),
                "modal_sign": summary.modal_sign,
                "non_neutral_evaluation_count": summary.non_neutral_form_count,
                "total_evaluation_count": summary.total_form_count,
                "modal_sign_agreement": summary.modal_sign_agreement,
                "envelope_class": summary.robustness_class,
                "functional_form_robust_scenario_count": sum(
                    scenario_classes[(case_id, scenario_id)] == "structurally_robust"
                    for scenario_id, _ in scenarios
                ),
                "parameter_scenario_count": len(scenarios),
            }
        )
    return case_rows, functional_form_summaries, envelope_summaries


def _write_csv(path: Path, fields: Iterable[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _class_counts(rows: list[dict[str, object]], column: str) -> dict[str, int]:
    labels = ("structurally_robust", "conditional_majority", "mixed_or_sensitive")
    return {label: sum(row[column] == label for row in rows) for label in labels}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config_json")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    config = _read_config(args.config_json)
    rows, form_summaries, envelope_summaries = run(config)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "part_i_robustness_cases.csv", CASE_FIELDS, rows)
    _write_csv(
        out_dir / "part_i_functional_form_summary.csv",
        FUNCTIONAL_FORM_SUMMARY_FIELDS,
        form_summaries,
    )
    _write_csv(
        out_dir / "part_i_robustness_envelope.csv",
        ENVELOPE_SUMMARY_FIELDS,
        envelope_summaries,
    )
    report = {
        "case_count": len(envelope_summaries),
        "evaluation_count": len(rows),
        "functional_form_summary_count": len(form_summaries),
        "functional_form_class_counts": _class_counts(form_summaries, "functional_form_class"),
        "parameter_envelope_class_counts": _class_counts(envelope_summaries, "envelope_class"),
        "warning": "Outputs are qualitative diagnostics. Functional-form robustness and biological parameter sensitivity are reported separately.",
    }
    (out_dir / "part_i_robustness_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
