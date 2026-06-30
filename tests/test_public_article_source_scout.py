from trait_architecture.public_article_source_scout import audit_study_sources


DOI = "10.1111/example"


def fetch(url: str):
    if "api.crossref.org" in url:
        return 200, {
            "message": {
                "DOI": DOI,
                "title": ["Example article"],
                "URL": "https://doi.org/10.1111/example",
                "link": [
                    {
                        "URL": "https://publisher.example/article.pdf",
                        "content-type": "application/pdf",
                        "intended-application": "text-mining",
                    }
                ],
            }
        }
    if "api.openalex.org" in url:
        return 200, {
            "id": "https://openalex.org/W123",
            "title": "Example article",
            "open_access": {"is_oa": True},
            "best_oa_location": {
                "landing_page_url": "https://repository.example/landing",
                "pdf_url": "https://repository.example/article.pdf",
                "license": "cc-by",
            },
            "locations": [],
        }
    if "datadryad.org" in url or "api.datacite.org" in url or "zenodo.org" in url:
        return 200, {"data": [], "hits": {"hits": []}}
    return 404, {}


def test_scout_emits_separate_article_and_oa_receipts() -> None:
    receipts, report = audit_study_sources(
        study_doi=DOI,
        queue_id="Q999",
        study_id="Example",
        fetch_json=fetch,
    )

    assert any(row.source_kind == "article_metadata" and row.resolution_status == "metadata_recovered" for row in receipts)
    assert any(row.source_kind == "publisher_content_link" for row in receipts)
    assert any(row.source_kind == "open_access_location" and row.resolution_status == "public_fulltext_candidate" for row in receipts)
    assert report["has_public_pdf_candidate"] is True
    assert report["has_linked_repository_manifest"] is False


def test_scout_does_not_promote_publisher_metadata_to_public_fulltext() -> None:
    def no_oa(url: str):
        if "api.crossref.org" in url:
            return 200, {"message": {"DOI": DOI, "title": ["Example"], "URL": "https://doi.org/10.1111/example"}}
        if "api.openalex.org" in url:
            return 200, {
                "id": "https://openalex.org/W123",
                "title": "Example",
                "open_access": {"is_oa": False},
                "best_oa_location": None,
                "locations": [],
            }
        if "datadryad.org" in url or "api.datacite.org" in url or "zenodo.org" in url:
            return 200, {"data": [], "hits": {"hits": []}}
        return 404, {}

    receipts, report = audit_study_sources(
        study_doi=DOI,
        queue_id="Q999",
        study_id="Example",
        fetch_json=no_oa,
    )

    assert report["has_public_pdf_candidate"] is False
    assert any(row.provider == "OpenAlex" and row.resolution_status == "not_found" for row in receipts)
    assert all(row.resolution_status != "public_fulltext_candidate" for row in receipts if row.provider == "Crossref")
