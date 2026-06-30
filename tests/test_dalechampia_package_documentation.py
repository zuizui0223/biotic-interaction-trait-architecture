import io
import zipfile

from trait_architecture.dalechampia_package_documentation import inspect_package_documentation


def make_archive() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("README.txt", "Upper bract area and resin were measured for each blossom.\n")
        archive.writestr("stash", "Dataset notes: pollen and seed predation variables are listed by population year.\n")
        archive.writestr("Phenotypic.Selection.LM.2006.Dryad.txt", "ID\tresin\tseeds_pred\n1\t2\t3\n")
    return buffer.getvalue()


def fetch(url: str):
    if "/datasets/doi%3A10.5061%2Fdryad.example" in url:
        return 200, {"_links": {"stash:version": {"href": "/api/v2/versions/99"}}}
    if url == "https://datadryad.org/api/v2/versions/99":
        return 200, {"_links": {"stash:files": {"href": "/api/v2/versions/99/files"}}}
    if url == "https://datadryad.org/api/v2/versions/99/files":
        return 200, {"_embedded": {"stash:files": [
            {"attributes": {"path": "README.txt"}},
            {"attributes": {"path": "stash"}},
            {"attributes": {"path": "Phenotypic.Selection.LM.2006.Dryad.txt"}},
        ]}}
    return 404, {}


def test_inspection_emits_only_name_whitelisted_documentation() -> None:
    report = inspect_package_documentation(
        "10.5061/dryad.example",
        fetch_json=fetch,
        fetch_bytes=lambda _: make_archive(),
    )

    assert report["documentation_record_count"] == 2
    records = report["records"]
    assert [record["file_name"] for record in records] == ["README.txt", "stash"]
    assert "Upper bract area" in records[0]["excerpt"]
    assert "ID\tresin" not in "\n".join(record["excerpt"] for record in records)
    assert "neither trait function nor an eligible four-path effect" in report["decision_boundary"]
