from pathlib import Path

from trait_architecture.broad_source_availability import (
    filter_unscreened,
    rank_candidates,
    read_already_screened_dois,
    score_row,
)


def row(**updates: str) -> dict[str, str]:
    base = {
        "candidate_id": "openalex:W1",
        "title": "Example",
        "doi": "https://doi.org/10.1/example",
        "seed_routes": "floral_damage_traits",
        "publication_year": "2024",
        "open_access_url": "",
        "is_open_access": "False",
        "metadata_match_score": "3",
        "metadata_attraction_signal": "True",
        "metadata_barrier_signal": "False",
        "metadata_pollination_signal": "True",
        "metadata_antagonist_signal": "True",
        "metadata_recoverability_signal": "False",
        "candidate_status": "M0_candidate_needs_full_text",
    }
    base.update(updates)
    return base


def test_open_access_recoverable_candidate_goes_to_manual_screen_now() -> None:
    record = score_row(row(open_access_url="https://example.org/paper.pdf", is_open_access="True", metadata_recoverability_signal="True", metadata_barrier_signal="True", metadata_match_score="5"))

    assert record.source_availability_score >= 10
    assert record.next_screen_bucket == "public_fulltext_first"
    assert record.screen_priority == "manual_screen_now"
    assert record.candidate_status == "M0_source_availability_ranked"


def test_metadata_only_candidate_is_not_promoted() -> None:
    record = score_row(row(doi="10.1/example", open_access_url="", is_open_access="False", metadata_recoverability_signal="False"))

    assert record.next_screen_bucket == "metadata_only_doi_lead"
    assert record.screen_priority == "hold_for_later_public_probe"
    assert "do not infer evidence level" in record.notes


def test_ranking_prefers_accessible_sources_over_metadata_score_only() -> None:
    records = rank_candidates([
        row(candidate_id="openalex:low_access", metadata_match_score="5", doi="10.1/no", open_access_url=""),
        row(candidate_id="openalex:oa", metadata_match_score="3", open_access_url="https://example.org/paper.pdf", is_open_access="True", metadata_recoverability_signal="True", metadata_barrier_signal="True"),
    ])

    assert records[0].candidate_id == "openalex:oa"


def test_final_screened_queue_rows_are_excluded_from_manual_ranking(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    queue.write_text(
        "queue_id,citation_or_doi,queue_status\n"
        "Q1,https://doi.org/10.1/example,registered_D1_observational_panel\n"
        "Q2,10.1/keep,queued\n",
        encoding="utf-8",
    )
    excluded = read_already_screened_dois(queue)
    rows = [row(candidate_id="drop", doi="https://doi.org/10.1/example"), row(candidate_id="keep", doi="10.1/keep")]

    assert excluded == {"10.1/example"}
    assert [item["candidate_id"] for item in filter_unscreened(rows, excluded)] == ["keep"]
