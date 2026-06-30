import csv
from pathlib import Path

from trait_architecture.four_path_effects import audit_effect_registry
from trait_architecture.matched_regime_registry import audit_matched_study_cards


ROOT = Path(__file__).parents[1]
EFFECTS = ROOT / "empirical" / "four_path_effects" / "four_path_effect_registry.csv"
CARDS = ROOT / "empirical" / "matched_flower_regime" / "matched_flower_study_cards.csv"
STUDY_ID = "Gorden_Adler_2018_Impatiens_capensis"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def test_impatiens_has_all_four_analysis_ready_observational_paths() -> None:
    rows = [row for row in read_csv(EFFECTS) if row["study_id"] == STUDY_ID]
    report = audit_effect_registry(rows)

    assert report.invalid_records == 0
    assert {row["effect_role"] for row in rows} == {
        "A_to_pollination",
        "A_to_antagonism",
        "B_to_antagonism",
        "B_to_pollination",
    }
    assert all(summary.analysis_ready for summary in report.summaries)
    assert all(summary.bridge_ready for summary in report.summaries)
    assert {row["causal_status"] for row in rows} == {"observational"}


def test_impatiens_is_d1_but_not_d2_or_d3() -> None:
    rows = [row for row in read_csv(CARDS) if row["source_id"] == STUDY_ID]
    report = audit_matched_study_cards(rows)

    assert len(report.summaries) == 1
    summary = report.summaries[0]
    assert summary.evidence_level == "D1_channel_mechanism_candidate"
    assert "total reproductive-fitness response" in summary.missing_for_d2
    assert "shared A_flower × B_flower cost/allocation estimate" in summary.missing_for_d3
