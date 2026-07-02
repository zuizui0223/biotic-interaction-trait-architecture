from trait_architecture.broad_abstract_corpus import build_broad_abstract_packet
from trait_architecture.broad_abstract_evidence_map import classify_rows, summarize_edges
from trait_architecture.theory_evidence_interface import build_interface


def response(abstract):
    return {
        "message": {
            "type": "journal-article",
            "title": ["Test title"],
            "container-title": ["Test journal"],
            "issued": {"date-parts": [[2024]]},
            "abstract": abstract,
        }
    }


def test_fixed_packet_keeps_nonabstract_l1_records_and_caches_doi():
    candidates = [
        {
            "candidate_id": "c1", "doi": "10.test/a", "title": "A", "abstract_available": "true",
            "shallow_screen_status": "priority_for_shallow_source_coding",
        },
        {
            "candidate_id": "c2", "doi": "10.test/a", "title": "B", "abstract_available": "true",
            "shallow_screen_status": "biological_context_needs_route_screen",
        },
        {
            "candidate_id": "c3", "doi": "10.test/c", "title": "C", "abstract_available": "false",
            "shallow_screen_status": "metadata_context_uncertain",
        },
    ]
    calls = []

    def request(url):
        calls.append(url)
        return response("<jats:p>Floral colour changed pollinator visitation.</jats:p>")

    packet = build_broad_abstract_packet(candidates, request_json=request)
    assert len(packet) == 3
    assert len(calls) == 1
    assert packet[0]["crossref_abstract_available"] == "true"
    assert packet[1]["crossref_abstract_text"] == packet[0]["crossref_abstract_text"]
    assert packet[2]["abstract_retrieval_state"] == "not_eligible_no_harvest_abstract"


def test_broad_map_separates_candidate_coverage_from_directional_support():
    packet = [
        {
            "candidate_id": "a", "doi": "10.test/a", "publication_year": "2024", "work_type": "journal-article",
            "route_families": "A_to_pollination", "source_queries": "AP02",
            "shallow_screen_status": "priority_for_shallow_source_coding",
            "abstract_retrieval_state": "looked_up_from_fixed_candidate_doi", "crossref_lookup_status": "success",
            "crossref_abstract_available": "true",
            "crossref_abstract_text": "We measured floral colour and pollinator visitation in a field experiment.",
        },
        {
            "candidate_id": "b", "doi": "10.test/b", "publication_year": "2024", "work_type": "journal-article",
            "route_families": "B_to_pollination", "source_queries": "BP02",
            "shallow_screen_status": "priority_for_shallow_source_coding",
            "abstract_retrieval_state": "looked_up_from_fixed_candidate_doi", "crossref_lookup_status": "success",
            "crossref_abstract_available": "true",
            "crossref_abstract_text": "Nectar alkaloid defence altered pollinator visitation in a floral manipulation.",
        },
        {
            "candidate_id": "c", "doi": "10.test/c", "publication_year": "2024", "work_type": "journal-article",
            "route_families": "B_to_antagonism", "source_queries": "BH02",
            "shallow_screen_status": "biological_context_needs_route_screen",
            "abstract_retrieval_state": "looked_up_from_fixed_candidate_doi", "crossref_lookup_status": "success",
            "crossref_abstract_available": "true",
            "crossref_abstract_text": "Floral trichomes reduced florivory in a field study.",
        },
        {
            "candidate_id": "d", "doi": "10.test/d", "publication_year": "2024", "work_type": "journal-article",
            "route_families": "B_to_antagonism", "source_queries": "BH02",
            "shallow_screen_status": "priority_for_shallow_source_coding",
            "abstract_retrieval_state": "looked_up_from_fixed_candidate_doi", "crossref_lookup_status": "success",
            "crossref_abstract_available": "true",
            "crossref_abstract_text": "Leaf trichomes reduced herbivory in a field study.",
        },
    ]
    records = classify_rows(packet)
    edges = summarize_edges(records)
    by_edge = {row["model_edge"]: row for row in edges}
    assert by_edge["A_to_pollination"]["broad_edge_candidate_records"] == "1"
    assert by_edge["B_to_pollination"]["broad_edge_candidate_records"] == "1"
    assert by_edge["B_to_antagonism"]["empirical_language_edge_candidate_records"] == "1"

    route_rows = [
        {
            "route": "B_to_pollination", "study_cluster_id": "bp1", "reported_direction": "negative",
            "record_status": "included_for_direction_map", "is_primary_sign_record": "true",
        },
        {
            "route": "A_to_pollination", "study_cluster_id": "ap1", "reported_direction": "mixed",
            "record_status": "included_for_direction_map", "is_primary_sign_record": "true",
        },
        {
            "route": "B_to_antagonism", "study_cluster_id": "bh1", "reported_direction": "negative",
            "record_status": "included_for_direction_map", "is_primary_sign_record": "true",
        },
    ]
    interface = {row["model_term"]: row for row in build_interface(edges, route_rows)}
    assert interface["c_D"]["evidence_status"] == "directionally_aligned_low_cluster_support"
    assert interface["b_A"]["evidence_status"] == "direction_unresolved_or_context_dependent"
    assert interface["c_AD"]["evidence_status"] == "not_identified_in_active_L1_L2_program"
    assert "not a numerical parameter estimate" in interface["c_D"]["connection_boundary"]
