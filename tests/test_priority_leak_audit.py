from trait_architecture.priority_leak_audit import build_audit_sample


def row(candidate_id: str, status: str, routes: str) -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "doi": "",
        "title": candidate_id,
        "publication_year": "2020",
        "container_title": "Flower Journal",
        "landing_page_url": "",
        "source_queries": "AP01",
        "route_families": routes,
        "metadata_A_signal": "true",
        "metadata_B_signal": "false",
        "metadata_P_signal": "true",
        "metadata_H_signal": "false",
        "metadata_W_signal": "false",
        "metadata_biology_context_term_count": "2",
        "shallow_screen_status": status,
        "shallow_screen_reason": "test",
    }


def test_audit_is_route_stratified_and_deterministic() -> None:
    rows = [
        row("p1", "priority_for_shallow_source_coding", "A_to_pollination"),
        row("p2", "priority_for_shallow_source_coding", "A_to_pollination"),
        row("n1", "biological_context_needs_route_screen", "A_to_pollination"),
        row("n2", "biological_context_needs_route_screen", "A_to_pollination"),
        row("h1", "priority_for_shallow_source_coding", "B_to_antagonism"),
        row("h2", "biological_context_needs_route_screen", "B_to_antagonism"),
    ]
    sample_a, summary_a = build_audit_sample(rows, per_route_per_group=1)
    sample_b, summary_b = build_audit_sample(rows, per_route_per_group=1)

    assert sample_a == sample_b
    assert summary_a == summary_b
    assert len(sample_a) == 4
    assert {entry["audit_group"] for entry in sample_a} == {"priority", "biological_nonpriority"}
    assert summary_a["availability_by_route_and_group"]["A_to_pollination"]["priority_for_shallow_source_coding"] == 2


def test_audit_does_not_promote_uncertain_records_to_nonpriority_biological_queue() -> None:
    rows = [
        row("u1", "metadata_context_uncertain", "A_to_pollination"),
        row("p1", "priority_for_shallow_source_coding", "A_to_pollination"),
        row("n1", "biological_context_needs_route_screen", "A_to_pollination"),
    ]
    sample, _ = build_audit_sample(rows, per_route_per_group=10)

    assert {entry["candidate_id"] for entry in sample} == {"p1", "n1"}
