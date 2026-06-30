import csv
from pathlib import Path

from trait_architecture.four_path_effects import audit_effect_registry


ROOT = Path(__file__).parents[1]
EFFECTS = ROOT / "empirical" / "four_path_effects" / "four_path_effect_registry.csv"
STUDY_ID = "Gross_Sun_Schiestl_2016_Gymnadenia_odoratissima"
EFFECT_ID = "Gross_Sun_Schiestl_2016_Gymnadenia_A_to_H_total_scent"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def test_gymnadenia_registers_one_analysis_ready_scale_specific_A_to_antagonism_effect() -> None:
    rows = [row for row in read_csv(EFFECTS) if row["study_id"] == STUDY_ID]
    report = audit_effect_registry(rows)

    assert report.invalid_records == 0
    assert len(rows) == 1
    row = rows[0]
    summary = report.summaries[0]
    assert row["effect_id"] == EFFECT_ID
    assert row["effect_role"] == "A_to_antagonism"
    assert row["effect_measure"] == "log_odds_ratio"
    assert row["causal_status"] == "observational"
    assert row["parameter_bridge_status"] == "scale_specific_only"
    assert float(row["effect_estimate"]) > 0
    assert summary.analysis_ready is True
    assert summary.bridge_ready is False
