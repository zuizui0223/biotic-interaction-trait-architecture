import io
import zipfile

from trait_architecture.dalechampia_linked_panel import audit_package


def make_archive() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "LM_2006.txt",
            "population\tyear\tpatch\tblossom\tupper_bract_area\tresin_removal\tseed_predated\nLM\t2006\t1\t7\t12\t1\t2\n",
        )
        archive.writestr(
            "LM_2007.txt",
            "population\tyear\tpatch\tblossom\tstigmatic_pollen\tintact_seeds\nLM\t2007\t2\t3\t15\t20\n",
        )
        archive.writestr(
            "PA_2014.txt",
            "population\tyear\tpatch\tblossom\tresin_gland_area\tseed_predated\nPA\t2014\t2\t8\t8\t1\n",
        )
    return buffer.getvalue()


def fetch(url: str):
    if "api.datacite.org" in url:
        return 200, {
            "data": {
                "attributes": {
                    "titles": [{"title": "Using ecological context to interpret variation"}],
                    "relatedIdentifiers": [
                        {"relatedIdentifier": "10.1111/j.1600-0706.2013.20780.x", "relationType": "IsDerivedFrom"}
                    ],
                }
            }
        }
    if "/datasets/doi%3A10.5061%2Fdryad.example" in url:
        return 200, {"_links": {"stash:version": {"href": "/api/v2/versions/99"}}}
    if url == "https://datadryad.org/api/v2/versions/99":
        return 200, {"_links": {"stash:files": {"href": "/api/v2/versions/99/files"}}}
    if url == "https://datadryad.org/api/v2/versions/99/files":
        return 200, {
            "_embedded": {
                "stash:files": [
                    {"attributes": {"path": "LM_2006.txt"}},
                    {"attributes": {"path": "LM_2007.txt"}},
                    {"attributes": {"path": "PA_2014.txt"}},
                ]
            }
        }
    return 404, {}


def test_linked_data_audit_requires_explicit_provenance_and_reports_headers() -> None:
    schemas, report = audit_package(
        article_doi="10.1111/j.1600-0706.2013.20780.x",
        dataset_doi="10.5061/dryad.example",
        fetch_json=fetch,
        fetch_bytes=lambda _: make_archive(),
    )

    assert report["article_relation_status"] == "declared_related_article"
    assert report["article_relation_type"] == "IsDerivedFrom"
    assert report["manifest_file_count"] == 3
    assert report["schema"]["header_recovered"] == 3
    assert "population" in report["schema"]["linkage"]["repeated_candidate_linkage_fields_in_at_least_three_tables"]
    assert "blossom" in report["schema"]["linkage"]["repeated_candidate_linkage_fields_in_at_least_three_tables"]
    assert all("LM\t" not in row.column_names for row in schemas)


def test_unrelated_dataset_is_not_promoted_to_a_related_article() -> None:
    def no_relation(url: str):
        if "api.datacite.org" in url:
            return 200, {"data": {"attributes": {"titles": [{"title": "Other data"}], "relatedIdentifiers": []}}}
        return fetch(url)

    _, report = audit_package(
        article_doi="10.1111/j.1600-0706.2013.20780.x",
        dataset_doi="10.5061/dryad.example",
        fetch_json=no_relation,
        fetch_bytes=lambda _: make_archive(),
    )

    assert report["article_relation_status"] == "no_declared_article_relation"
    assert "cannot establish" in report["decision_boundary"]
