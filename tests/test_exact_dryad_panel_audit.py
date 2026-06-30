import io
import zipfile

from trait_architecture.exact_dryad_panel_audit import audit_exact_dryad_panel


def make_archive() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "individual_panel.txt",
            "plant_id\tpopulation\tflower_scent\tfruit_count\tflower_count\n1\tA\t3\t4\t5\n",
        )
    return buffer.getvalue()


def fetch(url: str):
    if "api.datacite.org" in url:
        return 200, {
            "data": {"attributes": {
                "titles": [{"title": "Exact linked package"}],
                "relatedIdentifiers": [
                    {"relatedIdentifier": "10.1371/journal.pone.0147975", "relationType": "IsDerivedFrom"}
                ],
            }}
        }
    if "/datasets/doi%3A10.5061%2Fdryad.example" in url:
        return 200, {"_links": {"stash:version": {"href": "/api/v2/versions/99"}}}
    if url == "https://datadryad.org/api/v2/versions/99":
        return 200, {"_links": {"stash:files": {"href": "/api/v2/versions/99/files"}}}
    if url == "https://datadryad.org/api/v2/versions/99/files":
        return 200, {"_embedded": {"stash:files": [
            {"attributes": {"path": "individual_panel.txt"}},
        ]}}
    return 404, {}


def test_generic_exact_dryad_audit_preserves_header_only_boundary() -> None:
    schemas, report = audit_exact_dryad_panel(
        article_doi="10.1371/journal.pone.0147975",
        dataset_doi="10.5061/dryad.example",
        study_label="Gymnadenia_odoratissima",
        fetch_json=fetch,
        fetch_bytes=lambda _: make_archive(),
    )

    assert report["study_label"] == "Gymnadenia_odoratissima"
    assert report["article_relation_status"] == "declared_related_article"
    assert report["schema"]["header_recovered"] == 1
    assert "flower_scent" in schemas[0].column_names
    assert "\t3\t4\t5" not in schemas[0].column_names
    assert "does not establish trait roles" in report["decision_boundary"]
