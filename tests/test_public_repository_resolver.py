from trait_architecture.public_repository_resolver import resolve_queue


def row(queue_id: str = "Q001", doi: str = "10.1002/ajb2.1182") -> dict[str, str]:
    return {
        "queue_id": queue_id,
        "study_id": "Example_study",
        "citation_or_doi": doi,
        "queue_status": "queued",
    }


def empty_response(url: str):
    return 200, {"data": []} if "datacite" in url else {"hits": {"hits": []}}


def test_generic_dryad_manifest_requires_study_doi_in_response() -> None:
    def fetch(url: str):
        if "datadryad.org" in url:
            return 200, {
                "data": [
                    {
                        "id": "dryad-example",
                        "attributes": {
                            "doi": "10.5061/dryad.example",
                            "relatedIdentifiers": [{"relatedIdentifier": "10.1002/ajb2.1182"}],
                            "url": "https://datadryad.org/stash/dataset/doi:10.5061/dryad.example",
                            "filename": "floral_traits.csv",
                            "download_url": "https://datadryad.org/stash/downloads/file.csv",
                        },
                    }
                ]
            }
        return empty_response(url)

    receipts, report = resolve_queue([row()], fetch_json=fetch)

    dryad = [receipt for receipt in receipts if receipt.repository == "Dryad"]
    assert len(dryad) == 1
    assert dryad[0].resolution_status == "manifest_recovered"
    assert dryad[0].file_name == "floral_traits.csv"
    assert report["counts_by_resolution_status"]["manifest_recovered"] == 1
    assert report["counts_by_resolution_status"]["not_found"] == 2


def test_unrelated_dryad_search_result_is_not_promoted_to_landing_receipt() -> None:
    def fetch(url: str):
        if "datadryad.org" in url:
            return 200, {
                "data": [
                    {
                        "id": "unrelated",
                        "attributes": {
                            "doi": "10.5061/dryad.unrelated",
                            "url": "https://datadryad.org/stash/dataset/doi:10.5061/dryad.unrelated",
                        },
                    }
                ]
            }
        return empty_response(url)

    receipts, _ = resolve_queue([row()], fetch_json=fetch)

    dryad = [receipt for receipt in receipts if receipt.repository == "Dryad"]
    assert len(dryad) == 1
    assert dryad[0].resolution_status == "not_found"
    assert "explicit study-DOI relation" in dryad[0].notes


def test_datacite_linked_dryad_doi_is_requeried_before_manifest_receipt() -> None:
    def fetch(url: str):
        if "api.datacite.org" in url:
            return 200, {
                "data": [
                    {
                        "id": "10.5061/dryad.exact",
                        "attributes": {
                            "doi": "10.5061/dryad.exact",
                            "url": "https://datadryad.org/dataset/doi:10.5061/dryad.exact",
                            "relatedIdentifiers": [{"relatedIdentifier": "10.1002/ajb2.1182"}],
                        },
                    }
                ]
            }
        if "datadryad.org" in url:
            assert "10.5061%2Fdryad.exact" in url
            return 200, {
                "data": [
                    {
                        "id": "exact",
                        "attributes": {
                            "doi": "10.5061/dryad.exact",
                            "url": "https://datadryad.org/dataset/doi:10.5061/dryad.exact",
                            "filename": "individual_panel.csv",
                            "download_url": "https://datadryad.org/download/individual_panel.csv",
                        },
                    }
                ]
            }
        return empty_response(url)

    receipts, _ = resolve_queue([row()], fetch_json=fetch)

    datacite = [receipt for receipt in receipts if receipt.repository == "DataCite"]
    dryad = [receipt for receipt in receipts if receipt.repository == "Dryad"]
    assert len(datacite) == 1
    assert datacite[0].dataset_doi == "10.5061/dryad.exact"
    assert len(dryad) == 1
    assert dryad[0].resolution_status == "manifest_recovered"
    assert dryad[0].dataset_doi == "10.5061/dryad.exact"
    assert dryad[0].file_name == "individual_panel.csv"


def test_zenodo_manifest_requires_an_eligible_source_relation() -> None:
    def fetch(url: str):
        if "zenodo.org" in url:
            return 200, {
                "hits": {
                    "hits": [
                        {
                            "id": "citation-only",
                            "metadata": {
                                "doi": "10.5281/zenodo.citation-only",
                                "related_identifiers": [
                                    {"identifier": "10.1002/ajb2.1182", "relation": "isCitedBy"}
                                ],
                            },
                            "files": [
                                {"key": "article.pdf", "links": {"self": "https://zenodo.org/files/article.pdf"}}
                            ],
                        }
                    ]
                }
            }
        return empty_response(url)

    receipts, _ = resolve_queue([row()], fetch_json=fetch)

    zenodo = [receipt for receipt in receipts if receipt.repository == "Zenodo"]
    assert len(zenodo) == 1
    assert zenodo[0].resolution_status == "not_found"
    assert "eligible supplement/derivation/part relation" in zenodo[0].notes


def test_zenodo_manifest_accepts_derived_package_relation() -> None:
    def fetch(url: str):
        if "zenodo.org" in url:
            return 200, {
                "hits": {
                    "hits": [
                        {
                            "id": "derived-package",
                            "metadata": {
                                "doi": "10.5281/zenodo.derived-package",
                                "related_identifiers": [
                                    {"identifier": "https://doi.org/10.1002/ajb2.1182", "relation": "isDerivedFrom"}
                                ],
                            },
                            "files": [
                                {"key": "individual_panel.csv", "links": {"self": "https://zenodo.org/files/individual_panel.csv"}}
                            ],
                        }
                    ]
                }
            }
        return empty_response(url)

    receipts, report = resolve_queue([row()], fetch_json=fetch)

    zenodo = [receipt for receipt in receipts if receipt.repository == "Zenodo"]
    assert len(zenodo) == 1
    assert zenodo[0].resolution_status == "manifest_recovered"
    assert zenodo[0].file_name == "individual_panel.csv"
    assert "Eligible Zenodo source relation" in zenodo[0].notes
    assert report["counts_by_resolution_status"]["manifest_recovered"] == 1


def test_endpoint_failure_is_recorded_without_blocking_other_routes() -> None:
    def fetch(url: str):
        if "datadryad.org" in url:
            raise TimeoutError("endpoint timed out")
        return empty_response(url)

    receipts, report = resolve_queue([row()], fetch_json=fetch)

    dryad = [receipt for receipt in receipts if receipt.repository == "Dryad"]
    assert dryad[0].resolution_status == "access_failed"
    assert "TimeoutError" in dryad[0].notes
    assert report["counts_by_resolution_status"]["access_failed"] == 1
    assert report["receipt_count"] == 3


def test_known_mendeley_handle_is_preserved_only_for_its_declared_study() -> None:
    receipts, _ = resolve_queue([row("Q002", "10.1186/s12862-024-02301-7")], fetch_json=empty_response)

    mendeley = [receipt for receipt in receipts if receipt.repository == "Mendeley Data"]
    assert len(mendeley) == 1
    assert mendeley[0].dataset_doi == "10.17632/2n4vgpvzgs.1"
    assert mendeley[0].resolution_status == "landing_page_only"
