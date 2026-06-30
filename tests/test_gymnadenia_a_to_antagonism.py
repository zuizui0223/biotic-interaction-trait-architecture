import io
import json
import math
import zipfile
from xml.sax.saxutils import escape

from trait_architecture.gymnadenia_a_to_antagonism import extract_gymnadenia_a_to_antagonism


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
    keys = [
        ["P1", "2015", "R1", "A"], ["P2", "2015", "R1", "A"],
        ["P3", "2015", "R1", "A"], ["P4", "2015", "R1", "A"],
        ["P5", "2015", "R1", "A"], ["P6", "2015", "R1", "A"],
        ["P7", "2016", "R1", "A"], ["P8", "2016", "R1", "A"],
        ["P9", "2016", "R1", "A"], ["P10", "2016", "R1", "A"],
        ["P11", "2016", "R1", "A"], ["P12", "2016", "R1", "A"],
    ]
    scent = ["0.1", "0.3", "0.6", "1.0", "1.8", "3.0", "0.2", "0.5", "0.9", "1.4", "2.2", "3.5"]
    eaten = ["0", "1", "1", "2", "3", "4", "0", "1", "2", "3", "4", "5"]
    floral_rows = [key + ["10", value] for key, value in zip(keys, scent)]
    herbivory_rows = [key + [value] for key, value in zip(keys, eaten)]
    files = {
        "Data__FloralTraitDifferences.xlsx": xlsx_bytes(
            ["PlantID", "Year", "Region", "Population", "NrFlowers", "TotalScentAmount_ngPerL"],
            floral_rows,
        ),
        "Data__HerbivoryDifferences.xlsx": xlsx_bytes(
            ["PlantID", "Year", "Region", "Population", "NrFlowersEaten"],
            herbivory_rows,
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
        ]}}
    return 404, {}


def test_predeclared_extractor_returns_one_aggregate_effect_without_rows() -> None:
    report = extract_gymnadenia_a_to_antagonism(
        dataset_doi="10.5061/dryad.example",
        fetch_json=fetch,
        fetch_bytes=lambda _: make_archive(),
    )

    effect = report["effect"]
    assert report["sample"]["included_rows"] == 12
    assert report["sample"]["population_year_strata"] == 2
    assert effect["effect_measure"] == "log_odds_ratio"
    assert effect["fit_converged"] is True
    assert math.isfinite(effect["effect_estimate"])
    assert effect["effect_ci_lower"] < effect["effect_ci_upper"]
    emitted = json.dumps(report)
    assert "P1" not in emitted
    assert "0.1" not in emitted
    assert "conditional observational association" in report["decision_boundary"]
