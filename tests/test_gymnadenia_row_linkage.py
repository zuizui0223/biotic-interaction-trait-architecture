import io
import json
import zipfile
from xml.sax.saxutils import escape

from trait_architecture.gymnadenia_row_linkage import audit_gymnadenia_row_linkage


def column_name(index: int) -> str:
    name = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def xlsx_bytes(headers: list[str], rows: list[list[str]]) -> bytes:
    def xml_row(row_number: int, values: list[str]) -> str:
        cells = []
        for index, value in enumerate(values):
            reference = f"{column_name(index)}{row_number}"
            cells.append(f'<c r="{reference}" t="inlineStr"><is><t>{escape(value)}</t></is></c>')
        return f'<row r="{row_number}">{"".join(cells)}</row>'

    sheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>'
        + xml_row(1, headers)
        + "".join(xml_row(index + 2, row) for index, row in enumerate(rows))
        + '</sheetData></worksheet>'
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return buffer.getvalue()


def make_archive() -> bytes:
    files = {
        "Data__FloralTraitDifferences.xlsx": xlsx_bytes(
            ["PlantID", "Year", "Region", "Population", "NrFlowers", "TotalScentAmount_ngPerL"],
            [["P1", "2015", "R1", "A", "10", "987.654"], ["P2", "2015", "R1", "A", "5", "123.456"]],
        ),
        "Data__HerbivoryDifferences.xlsx": xlsx_bytes(
            ["PlantID", "Year", "Region", "Population", "NrFlowersEaten", "AphidLoad"],
            [["P1", "2015", "R1", "A", "2", "1"], ["P2", "2015", "R1", "A", "8", "0"]],
        ),
        "Data__ReproductiveSuccessDifferences.xlsx": xlsx_bytes(
            ["PlantID", "Year", "Region", "Population", "NrFlowers", "NrFruits"],
            [["P1", "2015", "R1", "A", "10", "4"], ["P2", "2015", "R1", "A", "5", "3"]],
        ),
        "Data__PollinatorLimitation.xlsx": xlsx_bytes(
            ["PlantID", "Year", "Region", "Population", "Treatment", "NrFlowers", "NrFruits"],
            [["P1", "2015", "R1", "A", "control", "10", "4"], ["P2", "2015", "R1", "A", "supplemented", "5", "3"]],
        ),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def fetch(url: str):
    if "/datasets/doi%3A10.5061%2Fdryad.example" in url:
        return 200, {"_links": {"stash:version": {"href": "/api/v2/versions/99"}}}
    if url == "https://datadryad.org/api/v2/versions/99":
        return 200, {"_links": {"stash:files": {"href": "/api/v2/versions/99/files"}}}
    if url == "https://datadryad.org/api/v2/versions/99/files":
        return 200, {"_embedded": {"stash:files": [
            {"attributes": {"path": "Data__FloralTraitDifferences.xlsx"}},
            {"attributes": {"path": "Data__HerbivoryDifferences.xlsx"}},
            {"attributes": {"path": "Data__ReproductiveSuccessDifferences.xlsx"}},
            {"attributes": {"path": "Data__PollinatorLimitation.xlsx"}},
        ]}}
    return 404, {}


def test_row_linkage_audit_outputs_aggregate_counts_not_observations() -> None:
    report = audit_gymnadenia_row_linkage(
        dataset_doi="10.5061/dryad.example",
        fetch_json=fetch,
        fetch_bytes=lambda _: make_archive(),
    )

    overlap = report["pairwise_overlap"]["floral_traits_to_herbivory"]
    contract = report["herbivory_denominator_contract"]
    assert overlap["one_to_one_common_keys"] == 2
    assert contract["one_to_one_linked_rows"] == 2
    assert contract["numeric_nonnegative_outcome_with_positive_denominator"] == 1
    assert contract["eaten_exceeds_linked_flower_count"] == 1
    assert "987.654" not in json.dumps(report)
    assert "No observation rows or values are written." in report["decision_boundary"]
