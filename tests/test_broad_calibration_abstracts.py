from trait_architecture.broad_calibration_abstracts import build_abstract_packet


def batch_row(**overrides: str) -> dict[str, str]:
    row = {
        "queue_rank": "1",
        "candidate_id": "doi:10.1/example",
        "doi": "10.1/example",
        "title": "Example flower study",
        "focus_route_families": "A_to_pollination",
        "all_discovery_route_families": "A_to_pollination;B_to_pollination",
    }
    row.update(overrides)
    return row


def test_packet_recovers_plain_text_crossref_abstract_and_metadata() -> None:
    seen: list[str] = []

    def fake_request(url: str) -> dict[str, object]:
        seen.append(url)
        return {
            "message": {
                "type": "journal-article",
                "title": ["Recovered article title"],
                "container-title": ["Example Journal"],
                "issued": {"date-parts": [[2020, 1, 1]]},
                "abstract": "<jats:p>Floral colour increased pollinator <b>visitation</b>.</jats:p>",
            }
        }

    packet = build_abstract_packet([batch_row()], request_json=fake_request)

    assert seen == ["https://api.crossref.org/works/10.1%2Fexample"]
    assert packet[0]["crossref_lookup_status"] == "success"
    assert packet[0]["crossref_abstract_available"] == "true"
    assert packet[0]["crossref_abstract_text"] == "Floral colour increased pollinator visitation."
    assert "not alone establish" in packet[0]["source_packet_warning"]


def test_packet_preserves_failed_lookup_without_converting_it_to_absence() -> None:
    def failed_request(_: str) -> dict[str, object]:
        raise RuntimeError("temporary outage")

    packet = build_abstract_packet([batch_row()], request_json=failed_request)

    assert packet[0]["crossref_lookup_status"] == "failed"
    assert packet[0]["crossref_abstract_available"] == "false"
    assert packet[0]["crossref_abstract_text"] == ""
    assert "Lookup failed" in packet[0]["source_packet_warning"]
