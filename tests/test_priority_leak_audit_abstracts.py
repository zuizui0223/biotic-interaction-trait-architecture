from trait_architecture.priority_leak_audit_abstracts import build_audit_abstract_packet


def row(candidate_id: str, doi: str, route: str) -> dict[str, str]:
    return {
        "audit_group": "priority",
        "route_family_audit": route,
        "audit_rank": "1",
        "candidate_id": candidate_id,
        "doi": doi,
        "title": candidate_id,
        "publication_year": "2020",
        "container_title": "Flower Journal",
        "landing_page_url": "",
        "source_queries": "AP01",
        "route_families": route,
        "metadata_A_signal": "true",
        "metadata_B_signal": "false",
        "metadata_P_signal": "true",
        "metadata_H_signal": "false",
        "metadata_W_signal": "false",
        "metadata_biology_context_term_count": "2",
        "shallow_screen_status": "priority_for_shallow_source_coding",
        "shallow_screen_reason": "test",
    }


def test_packet_preserves_all_audit_rows_and_caches_shared_doi() -> None:
    calls: list[str] = []

    def request_json(url: str) -> dict[str, object]:
        calls.append(url)
        return {
            "message": {
                "type": "journal-article",
                "title": ["Resolved title"],
                "container-title": ["Test Journal"],
                "issued": {"date-parts": [[2021]]},
                "abstract": "<jats:p>Measured <b>floral</b> response.</jats:p>",
            }
        }

    packet = build_audit_abstract_packet(
        [row("same-study-a", "10.1000/example", "A_to_pollination"), row("same-study-b", "10.1000/example", "A_to_antagonism")],
        request_json=request_json,
    )

    assert len(packet) == 2
    assert [entry["candidate_id"] for entry in packet] == ["same-study-a", "same-study-b"]
    assert [entry["route_family_audit"] for entry in packet] == ["A_to_pollination", "A_to_antagonism"]
    assert len(calls) == 1
    assert packet[0]["crossref_lookup_status"] == "success"
    assert packet[0]["crossref_abstract_text"] == "Measured floral response."
    assert packet[1]["crossref_published_year"] == "2021"


def test_packet_preserves_missing_doi_for_manual_follow_up() -> None:
    packet = build_audit_abstract_packet([row("no-doi", "", "B_to_pollination")])

    assert packet[0]["crossref_lookup_status"] == "not_attempted_missing_doi"
    assert packet[0]["crossref_abstract_available"] == "false"
    assert "No DOI was available" in packet[0]["source_packet_warning"]
