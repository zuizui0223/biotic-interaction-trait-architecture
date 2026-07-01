from collections import Counter
from pathlib import Path

from trait_architecture.broad_meta_analysis import direction_map, read_csv_rows


ROOT = Path(__file__).parents[1]
ROUTE_RECORDS = ROOT / "empirical" / "broad_reality_evidence" / "broad_route_records.csv"


def test_registered_direction_records_are_source_coded_and_not_quantitative_effects() -> None:
    rows = read_csv_rows(ROUTE_RECORDS)

    assert len(rows) == 12
    assert Counter(row["route"] for row in rows) == {
        "A_to_pollination": 5,
        "A_to_antagonism": 1,
        "B_to_antagonism": 3,
        "B_to_pollination": 3,
    }
    assert all(row["record_status"] == "included_for_direction_map" for row in rows)
    assert all(row["source_basis"] == "crossref_deposited_abstract" for row in rows)
    assert all(row["is_primary_sign_record"] == "true" for row in rows)


def test_registered_direction_map_has_no_poolable_stratum_yet() -> None:
    mapped = direction_map(read_csv_rows(ROUTE_RECORDS))

    assert len(mapped) == 10
    assert all(row["direction_map_status"] == "insufficient_directional_clusters" for row in mapped)
    b_to_p_foraging = next(
        row
        for row in mapped
        if row["route"] == "B_to_pollination"
        and row["outcome_class"] == "pollinator_preference_or_foraging"
    )
    assert b_to_p_foraging["independent_clusters"] == 2
    assert b_to_p_foraging["negative_count"] == 2
    assert b_to_p_foraging["compatible_count"] == 2
