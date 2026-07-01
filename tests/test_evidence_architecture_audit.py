import json

import pytest

from trait_architecture.evidence_architecture_audit import (
    initial_screening_rows,
    metadata_baseline_summary,
    validate_matrix,
)


def candidate(**overrides: str) -> dict[str, str]:
    row = {
        "candidate_id": "openalex:W1",
        "doi": "10.1000/example",
        "title": "Example floral study",
        "authors": "Example Author",
        "publication_year": "2024",
        "work_type": "article",
        "seed_routes": "example",
        "seed_query_ids": "A01",
        "is_open_access": "true",
        "abstract_available": "true",
        "cited_by_count": "7",
        "metadata_attraction_signal": "true",
        "metadata_barrier_signal": "false",
        "metadata_pollination_signal": "true",
        "metadata_antagonist_signal": "false",
        "metadata_recoverability_signal": "false",
    }
    row.update(overrides)
    return row


def test_initial_matrix_retains_metadata_but_marks_all_evidence_unassessed() -> None:
    rows = initial_screening_rows([candidate(), candidate(candidate_id="openalex:W2", abstract_available="false")])

    assert rows[0]["metadata_signal_vector"] == "1010"
    assert rows[0]["source_basis"] == "abstract_metadata_available"
    assert rows[1]["source_basis"] == "metadata_only"
    assert all(row["coding_status"] == "unassessed" for row in rows)
    assert all(row["A_flower_status"] == "unassessed" for row in rows)
    assert all(row["max_evidence_level"] == "unassessed" for row in rows)
    validate_matrix(rows, expected_count=None)


def test_unassessed_row_cannot_promote_a_component_from_metadata() -> None:
    row = initial_screening_rows([candidate()])[0]
    row["A_flower_status"] = "measured_direct"

    with pytest.raises(ValueError, match="unassessed rows cannot contain inferred evidence components"):
        validate_matrix([row], expected_count=None)


def test_metadata_summary_is_explicitly_nonbiological() -> None:
    rows = initial_screening_rows([
        candidate(),
        candidate(candidate_id="openalex:W2", metadata_barrier_signal="true", metadata_antagonist_signal="true"),
    ])
    summary = metadata_baseline_summary(rows)

    assert summary["candidate_count"] == 2
    assert summary["metadata_signal_counts"]["metadata_attraction_signal"] == 2
    assert summary["metadata_signal_counts"]["metadata_barrier_signal"] == 1
    assert summary["metadata_signal_vector_counts"] == {"1010": 1, "1111": 1}
    assert "do not establish" in summary["interpretation_boundary"]
    json.dumps(summary)
