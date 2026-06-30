from trait_architecture.public_dataset_link_validation import validate_candidates


def candidate() -> dict[str, str]:
    return {
        "candidate_id": "DL001",
        "queue_id": "Q001",
        "study_id": "Example_study",
        "study_doi": "10.1002/example",
        "repository": "Dryad",
        "dataset_doi": "10.5061/dryad.example",
        "link_status": "needs_exact_relation_validation",
    }


def test_exact_supplement_relation_and_file_manifest_are_required() -> None:
    def fetch(url: str):
        if "api.datacite.org" in url:
            return 200, {
                "data": {
                    "attributes": {
                        "titles": [{"title": "Example dataset"}],
                        "url": "https://datadryad.org/dataset/doi:10.5061/dryad.example",
                        "relatedIdentifiers": [
                            {"relatedIdentifier": "10.1002/example", "relationType": "IsSupplementTo"}
                        ],
                    }
                }
            }
        if "datasets/doi%3A10.5061%2Fdryad.example" in url:
            return 200, {
                "_embedded": {
                    "stash:files": [
                        {
                            "attributes": {
                                "filename": "traits.csv",
                                "download_url": "https://datadryad.org/download/traits.csv",
                            }
                        }
                    ]
                }
            }
        return 404, {}

    receipts, report = validate_candidates([candidate()], fetch_json=fetch)

    assert len(receipts) == 1
    assert receipts[0].validation_status == "link_validated_manifest_recovered"
    assert receipts[0].relation_type == "IsSupplementTo"
    assert receipts[0].file_name == "traits.csv"
    assert report["counts_by_validation_status"]["link_validated_manifest_recovered"] == 1


def test_citation_relation_does_not_validate_candidate_dataset() -> None:
    def fetch(url: str):
        return 200, {
            "data": {
                "attributes": {
                    "titles": [{"title": "Candidate dataset"}],
                    "relatedIdentifiers": [
                        {"relatedIdentifier": "10.1002/example", "relationType": "References"}
                    ],
                }
            }
        }

    receipts, _ = validate_candidates([candidate()], fetch_json=fetch)

    assert receipts[0].validation_status == "candidate_rejected"
    assert receipts[0].repository_request_url == ""


def test_datacite_failure_is_not_confused_with_candidate_rejection() -> None:
    def fetch(url: str):
        raise TimeoutError("DataCite timed out")

    receipts, _ = validate_candidates([candidate()], fetch_json=fetch)

    assert receipts[0].validation_status == "datacite_access_failed"
    assert "TimeoutError" in receipts[0].notes
