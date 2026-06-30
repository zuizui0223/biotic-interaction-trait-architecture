from trait_architecture.candidate_universe_public_audit import audit_candidates


def candidate(candidate_id: str, doi: str, oa_url: str = "") -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "title": f"Title {candidate_id}",
        "authors": "Author",
        "publication_year": "2024",
        "work_type": "article",
        "doi": doi,
        "seed_routes": "route",
        "seed_query_ids": "Q1",
        "is_open_access": "True" if oa_url else "False",
        "open_access_url": oa_url,
        "metadata_match_score": "4",
        "metadata_attraction_signal": "True",
        "metadata_barrier_signal": "True",
        "metadata_pollination_signal": "True",
        "metadata_antagonist_signal": "True",
        "metadata_recoverability_signal": "False",
    }


def fetch(url: str):
    if "api.crossref.org" in url:
        return 200, {
            "message": {
                "DOI": "10.1/example",
                "title": ["Example"],
                "URL": "https://doi.org/10.1/example",
                "link": [{"URL": "https://publisher.example/article.pdf", "content-type": "application/pdf"}],
            }
        }
    if "datadryad.org" in url:
        return 200, {"data": []}
    if "api.datacite.org" in url:
        return 200, {"data": []}
    if "zenodo.org" in url:
        return 200, {"hits": {"hits": []}}
    return 404, {}


def test_audit_marks_source_routes_as_candidates_not_evidence() -> None:
    rows, receipts = audit_candidates(
        [candidate("openalex:W1", "https://doi.org/10.1/example", "https://repository.example/article.pdf")],
        fetch_json=fetch,
        max_workers=1,
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["route_lane"] == "verify_public_fulltext_access"
    assert row["crossref_pdf_link_count"] == "1"
    assert row["repository_manifest_candidate_count"] == "0"
    assert "Do not infer" in row["do_not_infer"]
    assert any(item["source_kind"] == "publisher_content_link" for item in receipts)


def test_missing_doi_is_not_silently_dropped_from_fixed_universe() -> None:
    rows, receipts = audit_candidates([candidate("openalex:W2", "")], fetch_json=fetch, max_workers=1)

    assert len(rows) == 1
    assert rows[0]["route_lane"] == "no_doi_for_endpoint_audit"
    assert rows[0]["triage_score"] == "0"
    assert receipts == []
