from trait_architecture.broad_calibration_batch import select_calibration_batch


def candidate(candidate_id: str, routes: str, *, abstract: str = "true", review: str = "false", rank: str = "1") -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "doi": candidate_id.removeprefix("doi:"),
        "title": f"Title {candidate_id}",
        "route_families": routes,
        "abstract_available": abstract,
        "metadata_review_signal": review,
        "query_rank_min": rank,
    }


def test_route_balanced_batch_keeps_route_coverage_and_deduplicates_candidates() -> None:
    rows = [
        candidate("doi:shared", "A_to_pollination;B_to_pollination", rank="3"),
        candidate("doi:ap", "A_to_pollination", rank="2"),
        candidate("doi:ah", "A_to_antagonism", rank="2"),
        candidate("doi:bh", "B_to_antagonism", rank="2"),
        candidate("doi:bp", "B_to_pollination", rank="2"),
        candidate("doi:joint", "joint_channels", rank="2"),
    ]

    batch = select_calibration_batch(rows, per_route=2)

    assert len({row["candidate_id"] for row in batch}) == len(batch)
    shared = next(row for row in batch if row["candidate_id"] == "doi:shared")
    assert shared["focus_route_families"] == "A_to_pollination;B_to_pollination"
    focus = set(route for row in batch for route in row["focus_route_families"].split(";"))
    assert focus == {"A_to_pollination", "A_to_antagonism", "B_to_antagonism", "B_to_pollination", "joint_channels"}


def test_batch_prefers_access_cues_over_review_signal_then_query_rank() -> None:
    rows = [
        candidate("doi:noabstract", "A_to_pollination", abstract="false", rank="1"),
        candidate("doi:review", "A_to_pollination", review="true", rank="1"),
        candidate("doi:primary", "A_to_pollination", abstract="true", review="false", rank="10"),
    ]

    batch = select_calibration_batch(rows, per_route=1)

    assert batch[0]["candidate_id"] == "doi:primary"
    assert batch[0]["coding_status"] == "unassessed"
