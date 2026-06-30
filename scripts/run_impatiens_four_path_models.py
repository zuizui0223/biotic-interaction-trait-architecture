"""Run the predeclared treatment-adjusted Impatiens pathway model screen.

Raw rows are read only in memory from the title-validated Dryad archive. Outputs
contain aggregate diagnostics, coefficients, and candidate effect rows only.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from dataclasses import asdict
from io import BytesIO
from pathlib import Path
from typing import Any

from trait_architecture.dryad_archive_schema import _download_archive, _version_url
from trait_architecture.impatiens_models import design_matrix, has_interaction, prepare_rows
from trait_architecture.standardized_ols import fit_ols_hc3
from trait_architecture.title_validated_dryad_manifest import probe_targets, read_targets


PROCESSED_SUFFIX = "Processed_Data.csv"


def _receipt(targets: list[dict[str, str]]):
    receipts, manifest = probe_targets(targets)
    for receipt in receipts:
        if receipt.manifest_status == "manifest_recovered" and _version_url(receipt):
            return receipt, manifest
    raise RuntimeError("no title-validated Dryad archive available")


def _processed(archive: zipfile.ZipFile) -> list[dict[str, str]]:
    member = next((item for item in archive.infolist() if item.filename.endswith(PROCESSED_SUFFIX)), None)
    if member is None:
        raise RuntimeError("processed table is absent")
    data = archive.read(member).decode("utf-8-sig", errors="replace")
    return [dict(row) for row in csv.DictReader(io.StringIO(data))]


def _phenology_field(config: dict[str, Any]) -> str:
    matches = [item["field"] for item in config["shared_adjustments"] if item.get("coding") == "zscore"]
    if len(matches) != 1:
        raise ValueError("config must declare exactly one zscore phenology adjustment")
    return matches[0]


def _run_model(
    model: dict[str, Any],
    rows: list[dict[str, str]],
    traits: dict[str, Any],
    phenology_field: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    a, b = traits["A_flower"], traits["B_flower"]
    prepared, omitted = prepare_rows(
        rows,
        outcome_field=model["outcome_field"], outcome_transform=model["outcome_transform"],
        attraction_field=a["field"], attraction_transform=a["transform"],
        barrier_field=b["field"], barrier_transform=b["transform"],
        phenology_field=phenology_field,
    )
    y, design, terms = design_matrix(prepared, interaction=has_interaction(model))
    result = fit_ols_hc3(y, design, terms)
    coeff = {item.term: item for item in result.coefficients}
    summary = {
        "analysis_id": model["analysis_id"], "outcome_field": model["outcome_field"],
        "outcome_transform": model["outcome_transform"], "phenology_field": phenology_field,
        "n_complete": result.n, "n_omitted": omitted, "r_squared": result.r_squared,
        "residual_df": result.residual_df, "coefficients": [asdict(item) for item in result.coefficients],
        "interpretation": model["interpretation"],
    }
    effects: list[dict[str, Any]] = []
    for role in model.get("effect_roles", []):
        term = "A_z" if role.startswith("A_") else "B_z"
        item = coeff[term]
        effects.append({
            "analysis_id": model["analysis_id"], "effect_role": role, "term": term,
            "outcome_field": model["outcome_field"], "effect_measure": "standardized_regression_slope",
            "effect_estimate": item.estimate, "effect_se": item.hc3_se,
            "effect_ci_lower": item.ci95_lower, "effect_ci_upper": item.ci95_upper,
            "effect_p_value_normal": item.p_value_normal, "n_complete": result.n,
            "causal_status": "observational_adjusted", "linkage_status": "individual_processed_panel",
            "raw_table_status": "title_validated_dryad_archive",
            "candidate_status": "requires_manual_effect_registry_review",
        })
    return summary, effects


def run(config_json: str, targets_csv: str, out_dir: str) -> dict[str, object]:
    config = json.loads(Path(config_json).read_text(encoding="utf-8"))
    receipt, manifest = _receipt(read_targets(targets_csv))
    archive_url = f"{_version_url(receipt)}/download"
    archive_bytes = _download_archive(archive_url, landing_page_url=receipt.landing_page_url)
    rows = _processed(zipfile.ZipFile(BytesIO(archive_bytes)))
    phenology = _phenology_field(config)
    summaries: list[dict[str, Any]] = []
    effects: list[dict[str, Any]] = []
    for model in config["pathway_models"]:
        summary, candidate = _run_model(model, rows, config["primary_trait_modules"], phenology)
        summaries.append(summary)
        effects.extend(candidate)
    for model in config["fitness_component_models"]:
        summary, _ = _run_model(model, rows, config["primary_trait_modules"], phenology)
        summaries.append(summary)
    report = {
        "study_id": config["study_id"], "study_doi": config["study_doi"], "dataset_doi": config["dataset_doi"],
        "archive_url": archive_url, "manifest": manifest, "analysis_scope": config["scope"],
        "primary_trait_modules": config["primary_trait_modules"], "model_summaries": summaries,
        "effect_candidates": effects, "guardrails": config["guardrails"],
        "warning": "These are predeclared treatment-adjusted observational candidate effects. They are not automatically inserted into the shared registry or treated as causal trait effects.",
    }
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "impatiens_four_path_model_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    fields = list(effects[0]) if effects else []
    with (output / "impatiens_effect_candidates.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(effects)
    return {"processed_rows": len(rows), "model_count": len(summaries), "candidate_effect_count": len(effects)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config_json")
    parser.add_argument("targets_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)
    print(json.dumps(run(args.config_json, args.targets_csv, args.out_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
