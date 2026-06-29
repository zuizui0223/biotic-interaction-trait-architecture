from trait_architecture.dryad_table_schema import inspect_manifest_tables
from trait_architecture.title_validated_dryad_manifest import DryadManifestReceipt


def receipt(file_name: str, file_url: str) -> DryadManifestReceipt:
    return DryadManifestReceipt(
        target_id="TV001",
        queue_id="Q001",
        study_id="Example_study",
        study_doi="10.1002/example",
        dataset_doi="10.5061/dryad.example",
        expected_dataset_title="Data from: Example study",
        observed_dataset_title="Data from: Example study",
        title_match="yes",
        manifest_status="manifest_recovered",
        datacite_request_url="https://api.datacite.org/dois/10.5061/dryad.example",
        dryad_request_url="https://datadryad.org/api/v2/versions/1/files",
        landing_page_url="https://datadryad.org/dataset/doi:10.5061/dryad.example",
        file_name=file_name,
        file_url=file_url,
        notes="fixture",
    )


def test_csv_header_schema_retains_columns_but_not_rows() -> None:
    schemas, report = inspect_manifest_tables(
        [receipt("flower_traits.csv", "https://example.org/traits.csv")],
        download_prefix=lambda _: b"Plant_ID,Treatment,Flower_Size,Visitor_Count\nP1,control,10,3\n",
    )

    assert len(schemas) == 1
    schema = schemas[0]
    assert schema.schema_status == "header_recovered"
    assert schema.column_names == "Plant_ID;Treatment;Flower_Size;Visitor_Count"
    assert "Plant_ID" in schema.candidate_linkage_columns
    assert "Treatment" in schema.candidate_linkage_columns
    assert "P1" not in schema.column_names
    assert report["header_recovered"] == 1


def test_tsv_header_is_detected_and_table_access_failure_is_recorded() -> None:
    schemas, report = inspect_manifest_tables(
        [
            receipt("visitors.csv", "https://example.org/visitors.csv"),
            receipt("damage.csv", "https://example.org/damage.csv"),
        ],
        download_prefix=lambda url: (
            b"Plant\tFlorivory\tVisit_rate\nP1\t0.2\t5\n"
            if "visitors" in url
            else (_ for _ in ()).throw(TimeoutError("download timed out"))
        ),
    )

    assert schemas[0].delimiter == "\t"
    assert schemas[0].schema_status == "header_recovered"
    assert schemas[1].schema_status == "table_access_failed"
    assert "TimeoutError" in schemas[1].notes
    assert report["table_access_failed"] == 1
