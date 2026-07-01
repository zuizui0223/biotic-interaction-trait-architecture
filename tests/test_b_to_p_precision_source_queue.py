from pathlib import Path

from trait_architecture.public_repository_resolver import read_queue


ROOT = Path(__file__).parents[1]
QUEUE = (
    ROOT
    / "empirical"
    / "broad_reality_evidence"
    / "precision_expansions"
    / "source_audits"
    / "B_TO_P_BATCH_1_PUBLIC_SOURCE_QUEUE.csv"
)


def test_b_to_p_precision_source_queue_contains_only_explicit_resolution_targets() -> None:
    rows = read_queue(QUEUE)

    assert [row["queue_id"] for row in rows] == [
        "BPP1_Q001",
        "BPP1_Q002",
        "BPP1_Q003",
        "BPP1_Q004",
    ]
    assert [row["route"] for row in rows] == [
        "B_to_pollination",
        "B_to_pollination",
        "B_to_pollination",
        "B_to_antagonism",
    ]
    assert all(row["queue_status"] == "needs_repository_resolution" for row in rows)
