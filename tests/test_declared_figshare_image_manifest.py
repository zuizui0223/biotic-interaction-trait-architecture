import io
import zipfile

from trait_architecture.declared_figshare_image_manifest import audit_declared_figshare_image_manifests


def make_archive() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("camera_black_2016-07-03_12-00-01.jpg", b"pixel-bytes")
        archive.writestr("camera_red_2016-07-03_12-01-01.jpg", b"pixel-bytes")
        archive.writestr("notes.txt", b"metadata")
    return buffer.getvalue()


def test_image_manifest_audit_emits_aggregate_counts_only() -> None:
    def fetch_json(url: str):
        assert url == "https://api.figshare.com/v2/articles/7314731"
        return 200, {
            "id": 7314731,
            "doi": "10.6084/m9.figshare.7314731.v10",
            "files": [{
                "name": "pollinator_2016.zip",
                "download_url": "https://ndownloader.figshare.com/files/12345",
            }],
        }

    report = audit_declared_figshare_image_manifests(
        figshare_article_id="7314731",
        archive_names=["pollinator_2016.zip"],
        fetch_json=fetch_json,
        fetch_bytes=lambda _: make_archive(),
    )

    archive = report["archives"][0]
    assert archive["member_file_count"] == 3
    assert archive["image_file_count"] == 2
    assert archive["filename_morph_token_counts"] == {"black": 1, "red": 1, "white": 0}
    assert archive["filename_timestamp_token_count"] == 2
    assert "camera_black" not in str(report)
    assert "does not emit image paths" in report["decision_boundary"]


def test_image_manifest_audit_rejects_unknown_archive_name() -> None:
    def fetch_json(_: str):
        return 200, {"id": 7314731, "files": []}

    try:
        audit_declared_figshare_image_manifests(
            figshare_article_id="7314731",
            archive_names=["missing.zip"],
            fetch_json=fetch_json,
            fetch_bytes=lambda _: b"",
        )
    except ValueError as error:
        assert "absent or ambiguous" in str(error)
    else:
        raise AssertionError("unknown archive must fail")
