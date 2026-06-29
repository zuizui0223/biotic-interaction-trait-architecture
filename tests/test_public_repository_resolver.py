from trait_architecture.public_repository_resolver import resolve_queue


def row(queue_id: str = "Q001", doi: str = "10.1002/ajb2.1182") -> dict[str, str]:
    return {
        "queue_id": queue_id,
        "study_id": "Example_study",
        "citation_or_doi": doi,
        "queue_status": "queued",
    }


def test_manifest_receipt_is_distinct_from_landing_and_not_found() -> None:
    def fetch(url: str):
        if "datadryad.org" in url:
            return 200, {
                "data": [
                    {
                        "id": "dryad-example",
                        "attributes": {
                            "doi": "10.5061/dryad.example",
                            "url": "https://datadryad.org/stash/dataset/doi:10.5061/dryad.example",
                            "filename": "floral_traits.csv",
                            "download_url": "https://datadryad.org/stash/downloads/file.csv",
                        },
                    }
                ]
            }
        return 200, {"data": []} if "datacite" in url else {"hits": {"hits": []}}

    receipts, report = resolve_queue([row()], fetch_json=fetch)

    dryad = [receipt for receipt in receipts if receipt.repository == "Dryad"]
    assert len(dryad) == 1
    assert dryad[0].resolution_status == "manifest_recovered"
    assert dryad[0].file_name == "floral_traits.csv"
    assert report["counts_by_resolution_status"]["manifest_recovered"] == 1
    assert report["counts_by_resolution_status"]["not_found"] == 2


def test_endpoint_failure_is_recorded_without_blocking_other_routes() -> None:
    def fetch(url: str):
        if "datadryad.org" in url:
            raise TimeoutError("endpoint timed out")
        return 200, {"data": []} if "datacite" in url else {"hits": {"hits": []}}

    receipts, report = resolve_queue([row()], fetch_json=fetch)

    dryad = [receipt for receipt in receipts if receipt.repository == "Dryad"]
    assert dryad[0].resolution_status == "access_failed"
    assert "TimeoutError" in dryad[0].notes
    assert report["counts_by_resolution_status"]["access_failed"] == 1
    assert report["receipt_count"] == 3


def test_known_mendeley_handle_is_preserved_only_for_its_declared_study() -> None:
    def fetch(url: str):
        return 200, {"data": []} if "datacite" in url else {"hits": {"hits": []}}

    receipts, _ = resolve_queue([row("Q002", "10.1186/s12862-024-02301-7")], fetch_json=fetch)

    mendeley = [receipt for receipt in receipts if receipt.repository == "Mendeley Data"]
    assert len(mendeley) == 1
    assert mendeley[0].dataset_doi == "10.17632/2n4vgpvzgs.1"
    assert mendeley[0].resolution_status == "landing_page_only"
