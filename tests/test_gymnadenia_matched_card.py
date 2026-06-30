import csv
from pathlib import Path

from trait_architecture.matched_regime_registry import audit_matched_study_cards


ROOT = Path(__file__).parents[1]
CARDS = ROOT / "empirical" / "matched_flower_regime" / "matched_flower_study_cards.csv"
STUDY_ID = "Gross_Sun_Schiestl_2016_Gymnadenia_odoratissima"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def test_gymnadenia_is_M1_with_only_the_A_to_antagonism_path_estimated() -> None:
    rows = [row for row in read_csv(CARDS) if row["source_id"] == STUDY_ID]
    report = audit_matched_study_cards(rows)

    assert report.invalid_cards == 0
    assert len(report.summaries) == 1
    summary = report.summaries[0]
    assert summary.evidence_level == "M1_single_channel_ledger"
    assert "floral barrier/resistance trait" in summary.missing_for_d1
    assert "A_flower → pollination effect" in summary.missing_for_d1
    assert "B_flower → floral-antagonist effect" in summary.missing_for_d1
    assert "B_flower → pollination effect" in summary.missing_for_d1
