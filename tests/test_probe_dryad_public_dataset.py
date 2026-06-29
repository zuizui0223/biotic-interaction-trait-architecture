import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "probe_dryad_public_dataset.py"
SPEC = importlib.util.spec_from_file_location("dryad_probe", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_normalise_doi_handles_doi_urls() -> None:
    assert MODULE.normalise_doi("https://doi.org/10.5061/dryad.0J96d17") == "10.5061/dryad.0j96d17"


def test_file_record_detects_public_csv_download() -> None:
    record = MODULE._file_record_from_object(
        {
            "id": "file-1",
            "attributes": {
                "path": "plant_interactions.csv",
                "mimeType": "text/csv",
                "size": 100,
            },
            "links": {"stash:download": "https://datadryad.org/api/v2/files/file-1/download"},
        },
        "https://datadryad.org/api/v2/versions/1/files",
    )

    assert record is not None
    assert record["file_name"] == "plant_interactions.csv"
    assert record["tabular_candidate"] == "true"
    assert record["download_url"].endswith("/download")


def test_preview_tabular_file_records_headers_without_storing_rows(monkeypatch) -> None:
    record = {
        "file_name": "data.tsv",
        "file_id": "1",
        "mime_type": "text/tab-separated-values",
        "size_bytes": "123",
        "metadata_url": "https://example.test",
        "download_url": "https://datadryad.org/api/v2/files/1/download",
        "tabular_candidate": "true",
        "preview_status": "not_attempted",
        "detected_delimiter": "",
        "header_columns": "",
        "first_data_row_column_count": "",
    }
    monkeypatch.setattr(
        MODULE,
        "request_bytes",
        lambda url, timeout, max_bytes: ("success", b"plant_id\tflower_size\tvisit_count\nP1\t2.1\t3\n"),
    )

    result = MODULE.preview_tabular_file(record, 1)

    assert result["preview_status"] == "header_previewed"
    assert result["detected_delimiter"] == "tab"
    assert result["header_columns"] == "plant_id;flower_size;visit_count"
    assert result["first_data_row_column_count"] == "3"


def test_document_tree_only_queues_dryad_file_version_dataset_links(monkeypatch) -> None:
    root = "https://datadryad.org/api/v2/datasets/doi:10.5061%2Fdryad.test"
    version = "https://datadryad.org/api/v2/versions/123"
    files = "https://datadryad.org/api/v2/versions/123/files"
    responses = {
        root: {
            "data": {
                "attributes": {"title": "Test data"},
                "links": {"stash:version": version, "journal": "https://publisher.test/article"},
            }
        },
        version: {"data": {"links": {"stash:files": files}}},
        files: {
            "data": [
                {
                    "id": "f1",
                    "attributes": {"path": "table.csv", "size": 12},
                    "links": {"stash:download": "https://datadryad.org/api/v2/files/f1/download"},
                }
            ]
        },
    }
    monkeypatch.setattr(MODULE, "request_json", lambda url, timeout: ("success", responses[url]))

    metadata, docs, inventory = MODULE.discover_dryad_document_tree("10.5061/dryad.test", 1)

    assert MODULE.dataset_title(metadata) == "Test data"
    assert [url for url, _ in docs] == [root, version, files]
    assert len(inventory) == 1
    assert inventory[0]["file_name"] == "table.csv"
