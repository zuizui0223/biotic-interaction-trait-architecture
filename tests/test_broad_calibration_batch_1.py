from collections import Counter
from pathlib import Path

from trait_architecture.broad_meta_analysis import direction_map, read_csv_rows
from trait_architecture.broad_source_screening import validate_source_screening_matrix


ROOT = Path(__file__).parents[1]
BATCH_DIR = ROOT / "empirical" / "broad_reality_evidence" / "calibration_batches"


def test_batch_1_source_screening_snapshot_is_complete_and_explicit() -> None:
    rows = read_csv_rows(BATCH_DIR / "batch_1_source_screening.csv")

    validate_source_screening_matrix(rows)
    assert len(rows) == 24
    assert Counter(row["source_screen_status"] for row in rows) == {
        "included_for_source_coding": 19,
        "excluded": 4,
        "unassessed": 1,
    }
    assert all(row["source_access_status"] == "abstract_only" for row in rows)


def test_batch_1_direct_route_records_are_direction_only_and_do_not_create_b_to_p() -> None:
    rows = read_csv_rows(BATCH_DIR / "batch_1_route_records.csv")

    mapped = direction_map(rows)
    assert len(rows) == 8
    assert {row["route"] for row in rows} == {
        "A_to_pollination",
        "A_to_antagonism",
        "B_to_antagonism",
    }
    assert not any(row["route"] == "B_to_pollination" for row in rows)
    assert all(row["source_basis"] == "crossref_deposited_abstract" for row in rows)
    assert all(row["direction_map_status"] == "insufficient_directional_clusters" for row in mapped)
