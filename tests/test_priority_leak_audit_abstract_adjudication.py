from trait_architecture.priority_leak_audit_adjudication import PACKET
from trait_architecture.priority_leak_audit_overlay import materialize_abstract_adjudication


def packet_row(candidate_id: str, *, abstract: str, route: str = "A_to_pollination") -> dict[str, str]:
    row = {field: "" for field in PACKET}
    row.update({
        "audit_group": "priority",
        "route_family_audit": route,
        "audit_rank": "1" if candidate_id == "with" else "2",
        "candidate_id": candidate_id,
        "doi": f"10.1000/{candidate_id}",
        "title": candidate_id,
        "crossref_lookup_status": "success",
        "crossref_abstract_available": abstract,
    })
    return row


def override_present() -> dict[str, str]:
    return {
        "audit_group": "priority",
        "route_family_audit": "A_to_pollination",
        "audit_rank": "1",
        "candidate_id": "with",
        "doi": "10.1000/with",
        "source_screen_status": "included_for_source_coding",
        "source_access_status": "abstract_only",
        "study_type": "manipulation",
        "taxon": "Example plant",
        "primary_study_id": "with_study",
        "study_cluster_id": "with_panel",
        "screen_exclusion_reason": "",
        "route_screen_status": "direct_route_present",
        "route_screen_reason": "Direct comparison.",
        "source_locator": "Crossref deposited abstract",
        "coder_id": "tester",
        "coding_date": "2026-07-02",
        "coding_note": "Audit only.",
    }


def test_deposited_abstract_defaults_to_screened_target_route_absence() -> None:
    sheet = materialize_abstract_adjudication([packet_row("with", abstract="true")], [])

    assert sheet[0]["source_screen_status"] == "included_for_source_coding"
    assert sheet[0]["source_access_status"] == "abstract_only"
    assert sheet[0]["route_screen_status"] == "direct_route_absent"
    assert sheet[0]["primary_study_id"] == "10_1000_with"


def test_no_deposited_abstract_remains_unassessed() -> None:
    sheet = materialize_abstract_adjudication([packet_row("without", abstract="false")], [])

    assert sheet[0]["source_screen_status"] == "unassessed"
    assert sheet[0]["route_screen_status"] == "unassessed"


def test_explicit_overlay_replaces_default_without_changing_packet_fields() -> None:
    packet = [packet_row("with", abstract="true")]
    sheet = materialize_abstract_adjudication(packet, [override_present()])

    assert sheet[0]["title"] == "with"
    assert sheet[0]["route_screen_status"] == "direct_route_present"
    assert sheet[0]["study_cluster_id"] == "with_panel"
