from trait_architecture.castilleja_access_probe import (
    probe_castilleja_sources,
    probe_dryad_candidate,
    probe_pdf_link,
)


ARTICLE_DOI = "10.1111/j.0030-1299.2004.12641.x"
ARTICLE_TITLE = "Direct and indirect effects of pollinators and seed predators to selection on plant and floral traits"


def test_pdf_prefix_probe_requires_pdf_like_content() -> None:
    receipt = probe_pdf_link(
        "fixture",
        "https://publisher.example/article.pdf",
        fetch_prefix=lambda _url: (206, "https://publisher.example/article.pdf", "application/pdf", b"%PDF-1.7"),
    )

    assert receipt.resolution_status == "public_pdf_prefix_recovered"
    assert receipt.prefix_signature == "%PDF"


def test_pdf_access_denial_is_not_a_missing_article() -> None:
    from urllib.error import HTTPError

    def denied(_url: str):
        raise HTTPError(_url, 403, "Forbidden", hdrs=None, fp=None)

    receipt = probe_pdf_link("fixture", "https://publisher.example/article.pdf", fetch_prefix=denied)

    assert receipt.resolution_status == "access_denied_or_required"
    assert receipt.http_status == "403"


def test_dryad_candidate_requires_relation_or_exact_title() -> None:
    def unrelated(url: str):
        if "datadryad.org" in url:
            return 200, {"attributes": {"title": "Different data", "doi": "10.5061/dryad.other"}}
        if "api.datacite.org" in url:
            return 200, {"data": {"attributes": {"relatedIdentifiers": []}}}
        return 404, {}

    receipt = probe_dryad_candidate(
        dataset_id="1", article_doi=ARTICLE_DOI, article_title=ARTICLE_TITLE, fetch_json=unrelated,
    )

    assert receipt.resolution_status == "candidate_identity_unverified"


def test_dryad_candidate_accepts_exact_allowed_relation() -> None:
    def related(url: str):
        if "datadryad.org" in url:
            return 200, {"attributes": {"title": "Some data", "doi": "10.5061/dryad.related"}}
        if "api.datacite.org" in url:
            return 200, {
                "data": {
                    "attributes": {
                        "relatedIdentifiers": [
                            {"relatedIdentifier": ARTICLE_DOI, "relationType": "IsSupplementTo"}
                        ]
                    }
                }
            }
        return 404, {}

    receipt = probe_dryad_candidate(
        dataset_id="1", article_doi=ARTICLE_DOI, article_title=ARTICLE_TITLE, fetch_json=related,
    )

    assert receipt.resolution_status == "candidate_identity_verified_by_relation"
    assert receipt.article_relation == "IsSupplementTo"


def test_castilleja_probe_reports_no_full_text_when_all_pdf_routes_blocked() -> None:
    def blocked(_url: str):
        from urllib.error import HTTPError
        raise HTTPError(_url, 401, "Unauthorized", hdrs=None, fp=None)

    def no_dataset(url: str):
        if "datadryad.org" in url:
            return 404, {}
        return 404, {}

    receipts, report = probe_castilleja_sources(fetch_prefix=blocked, fetch_json=no_dataset)

    assert report["full_text_screen_allowed"] is False
    assert report["verified_repository_candidate"] is False
    assert sum(row.resolution_status == "access_denied_or_required" for row in receipts) == 2
