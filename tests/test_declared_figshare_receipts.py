from trait_architecture.declared_figshare_receipts import resolve_declared_figshare_queue


def row() -> dict[str, str]:
    return {
        "queue_id": "FS001",
        "study_id": "Example_study",
        "citation_or_doi": "10.1038/example",
        "declared_figshare_article_id": "7314731",
        "queue_status": "needs_repository_resolution",
    }


def test_exact_declared_figshare_accession_returns_manifest_without_rows() -> None:
    def fetch(url: str):
        assert url == "https://api.figshare.com/v2/articles/7314731"
        return 200, {
            "id": 7314731,
            "doi": "10.6084/m9.figshare.7314731",
            "url_public_html": "https://figshare.com/articles/dataset/example/7314731",
            "files": [
                {
                    "name": "supplementary_data.xlsx",
                    "download_url": "https://figshare.com/ndownloader/files/12345",
                }
            ],
        }

    receipts, report = resolve_declared_figshare_queue([row()], fetch_json=fetch)

    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt.repository == "Figshare"
    assert receipt.resolution_status == "manifest_recovered"
    assert receipt.dataset_identifier == "7314731"
    assert receipt.file_name == "supplementary_data.xlsx"
    assert "table contents remain uninspected" in receipt.notes
    assert report["counts_by_resolution_status"]["manifest_recovered"] == 1


def test_declared_accession_rejects_a_mismatched_figshare_response() -> None:
    def fetch(_: str):
        return 200, {"id": 9999999, "files": []}

    try:
        resolve_declared_figshare_queue([row()], fetch_json=fetch)
    except ValueError as error:
        assert "did not match declared article accession" in str(error)
    else:
        raise AssertionError("mismatched accession must fail")
