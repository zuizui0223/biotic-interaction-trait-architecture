import io
import zipfile

from trait_architecture.declared_figshare_xlsx_headers import audit_declared_figshare_xlsx_headers


def make_workbook() -> bytes:
    workbook_xml = '''<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Fitness" sheetId="1" r:id="rId1"/></sheets></workbook>'''
    relationships_xml = '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/></Relationships>'''
    sheet_xml = '''<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>PlantID</t></is></c><c r="B1" t="inlineStr"><is><t>Colour</t></is></c><c r="C1" t="inlineStr"><is><t>SeedSet</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>hidden</t></is></c></row></sheetData></worksheet>'''
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", relationships_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buffer.getvalue()


def test_declared_workbook_audit_returns_headers_without_data_rows() -> None:
    def fetch_json(url: str):
        assert url == "https://api.figshare.com/v2/articles/7314731"
        return 200, {
            "id": 7314731,
            "doi": "10.6084/m9.figshare.7314731.v10",
            "files": [{
                "name": "small_datasets.xlsx",
                "download_url": "https://ndownloader.figshare.com/files/12345",
            }],
        }

    report = audit_declared_figshare_xlsx_headers(
        figshare_article_id="7314731",
        file_name="small_datasets.xlsx",
        fetch_json=fetch_json,
        fetch_bytes=lambda _: make_workbook(),
    )

    assert report["sheet_count"] == 1
    assert report["sheets"] == [{"sheet_name": "Fitness", "header_values": ["PlantID", "Colour", "SeedSet"]}]
    assert "hidden" not in str(report)
    assert "does not emit data rows" in report["decision_boundary"]


def test_declared_workbook_audit_rejects_missing_file_name() -> None:
    def fetch_json(_: str):
        return 200, {"id": 7314731, "files": []}

    try:
        audit_declared_figshare_xlsx_headers(
            figshare_article_id="7314731",
            file_name="missing.xlsx",
            fetch_json=fetch_json,
            fetch_bytes=lambda _: b"",
        )
    except ValueError as error:
        assert "absent or ambiguous" in str(error)
    else:
        raise AssertionError("missing workbook must fail")
