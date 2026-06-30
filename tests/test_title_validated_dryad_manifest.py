from trait_architecture.title_validated_dryad_manifest import probe_targets


def target() -> dict[str, str]:
    return {
        "target_id": "TV001",
        "queue_id": "Q001",
        "study_id": "Example_study",
        "study_doi": "10.1002/example",
        "repository": "Dryad",
        "dataset_doi": "10.5061/dryad.example",
        "expected_dataset_title": "Data from: Exact Study Title",
        "validation_rule": "exact_normalized_dataset_title_match",
        "status": "ready_for_manifest_probe",
    }


def title_metadata() -> dict:
    return {
        "data": {
            "attributes": {
                "titles": [{"title": "Data from Exact Study Title"}],
                "url": "https://datadryad.org/dataset/doi:10.5061/dryad.example",
            }
        }
    }


def test_exact_title_match_allows_manifest_recovery() -> None:
    def fetch(url: str):
        if "api.datacite.org" in url:
            return 200, title_metadata()
        if "datasets/doi%3A10.5061%2Fdryad.example" in url:
            return 200, {
                "_embedded": {
                    "stash:files": [
                        {
                            "attributes": {
                                "filename": "processed.csv",
                                "download_url": "https://datadryad.org/download/processed.csv",
                            }
                        }
                    ]
                }
            }
        return 404, {}

    receipts, report = probe_targets([target()], fetch_json=fetch)

    assert len(receipts) == 1
    assert receipts[0].title_match == "yes"
    assert receipts[0].manifest_status == "manifest_recovered"
    assert receipts[0].file_name == "processed.csv"
    assert report["counts_by_manifest_status"]["manifest_recovered"] == 1


def test_relative_dataset_version_and_files_links_are_followed() -> None:
    calls: list[str] = []

    def fetch(url: str):
        calls.append(url)
        if "api.datacite.org" in url:
            return 200, title_metadata()
        if "datasets/doi%3A10.5061%2Fdryad.example" in url:
            return 200, {"_links": {"stash:version": {"href": "/api/v2/versions/4805"}}}
        if url == "https://datadryad.org/api/v2/versions/4805":
            return 200, {"_links": {"stash:files": {"href": "/api/v2/versions/4805/files"}}}
        if url == "https://datadryad.org/api/v2/versions/4805/files":
            return 200, {
                "_embedded": {
                    "stash:files": [
                        {
                            "attributes": {"path": "Raw Floral Visitors.csv"},
                            "_links": {"stash:download": {"href": "/api/v2/files/77/download"}},
                        }
                    ]
                }
            }
        return 404, {}

    receipts, _ = probe_targets([target()], fetch_json=fetch)

    assert len(receipts) == 1
    assert receipts[0].manifest_status == "manifest_recovered"
    assert receipts[0].file_name == "Raw Floral Visitors.csv"
    assert receipts[0].file_url == "https://datadryad.org/api/v2/files/77/download"
    assert "https://datadryad.org/api/v2/versions/4805" in receipts[0].dryad_request_url
    assert "https://datadryad.org/api/v2/versions/4805/files" in calls


def test_every_next_page_in_dryad_file_manifest_is_retained() -> None:
    def fetch(url: str):
        if "api.datacite.org" in url:
            return 200, title_metadata()
        if "datasets/doi%3A10.5061%2Fdryad.example" in url:
            return 200, {"_links": {"stash:version": {"href": "/api/v2/versions/4805"}}}
        if url == "https://datadryad.org/api/v2/versions/4805":
            return 200, {"_links": {"stash:files": {"href": "/api/v2/versions/4805/files?page=1"}}}
        if url == "https://datadryad.org/api/v2/versions/4805/files?page=1":
            return 200, {
                "_links": {"next": {"href": "/api/v2/versions/4805/files?page=2"}},
                "_embedded": {
                    "stash:files": [
                        {"attributes": {"path": "flower_size.csv"}, "_links": {"stash:download": {"href": "/api/v2/files/1/download"}}}
                    ]
                },
            }
        if url == "https://datadryad.org/api/v2/versions/4805/files?page=2":
            return 200, {
                "_embedded": {
                    "stash:files": [
                        {"attributes": {"path": "seed.csv"}, "_links": {"stash:download": {"href": "/api/v2/files/2/download"}}}
                    ]
                }
            }
        return 404, {}

    receipts, _ = probe_targets([target()], fetch_json=fetch)

    assert {receipt.file_name for receipt in receipts} == {"flower_size.csv", "seed.csv"}
    assert all(receipt.manifest_status == "manifest_recovered" for receipt in receipts)


def test_title_mismatch_blocks_any_dryad_manifest_request() -> None:
    calls: list[str] = []

    def fetch(url: str):
        calls.append(url)
        return 200, {"data": {"attributes": {"titles": [{"title": "Different dataset"}]}}}

    receipts, _ = probe_targets([target()], fetch_json=fetch)

    assert receipts[0].manifest_status == "title_mismatch"
    assert len(calls) == 1
    assert "api.datacite.org" in calls[0]


def test_dryad_failure_remains_distinct_from_missing_title_validation() -> None:
    def fetch(url: str):
        if "api.datacite.org" in url:
            return 200, title_metadata()
        raise TimeoutError("Dryad endpoint timed out")

    receipts, _ = probe_targets([target()], fetch_json=fetch)

    assert receipts[0].title_match == "yes"
    assert receipts[0].manifest_status == "dryad_access_failed"
    assert "TimeoutError" in receipts[0].notes
