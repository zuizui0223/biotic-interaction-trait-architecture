"""Inspect workbook sheet names and header rows from article-declared Figshare files.

The audit resolves an exact Figshare accession and an exact filename from its
manifest, then emits only workbook structure and header strings. It never emits
data rows, identifiers, or numeric values from the workbook.
"""

from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from trait_architecture.declared_figshare_receipts import FIGSHARE_API
from trait_architecture.public_repository_resolver import _as_url, _fetch_json, _text


NS = {
    "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
USER_AGENT = "biotic-interaction-trait-architecture declared-figshare-header-audit/0.1"


def _fetch_bytes(url: str, *, timeout: int = 45) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # nosec B310: exact public manifest URL
        return response.read()


def _column_index(reference: str) -> int:
    letters = "".join(character for character in reference if character.isalpha())
    index = 0
    for character in letters:
        index = index * 26 + ord(character.upper()) - ord("A") + 1
    return index - 1


def _shared_strings(workbook: zipfile.ZipFile) -> list[str]:
    path = "xl/sharedStrings.xml"
    if path not in workbook.namelist():
        return []
    root = ET.fromstring(workbook.read(path))
    return ["".join(node.itertext()) for node in root.findall("x:si", NS)]


def _cell_text(cell: ET.Element, shared: list[str]) -> str:
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        inline = cell.find("x:is", NS)
        return "".join(inline.itertext()).strip() if inline is not None else ""
    value = cell.findtext("x:v", default="", namespaces=NS).strip()
    if cell_type == "s" and value.isdigit() and int(value) < len(shared):
        return shared[int(value)].strip()
    return value


def _sheet_paths(workbook: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook_xml = ET.fromstring(workbook.read("xl/workbook.xml"))
    relationships = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    targets = {
        relationship.get("Id"): relationship.get("Target", "")
        for relationship in relationships.findall("rel:Relationship", NS)
    }
    result: list[tuple[str, str]] = []
    for sheet in workbook_xml.findall("x:sheets/x:sheet", NS):
        name = sheet.get("name", "")
        relationship_id = sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id", "")
        target = targets.get(relationship_id, "")
        if target:
            result.append((name, "xl/" + target.lstrip("/")))
    return result


def _header_values(workbook: zipfile.ZipFile, sheet_path: str, shared: list[str]) -> list[str]:
    root = ET.fromstring(workbook.read(sheet_path))
    for row in root.findall(".//x:sheetData/x:row", NS):
        values: dict[int, str] = {}
        for cell in row.findall("x:c", NS):
            reference = cell.get("r", "")
            if reference:
                values[_column_index(reference)] = _cell_text(cell, shared)
        if values and any(values.values()):
            return [values.get(index, "") for index in range(max(values) + 1)]
    return []


def audit_declared_figshare_xlsx_headers(
    *,
    figshare_article_id: str,
    file_name: str,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
    fetch_bytes: Callable[[str], bytes] = _fetch_bytes,
) -> dict[str, object]:
    """Resolve one exact Figshare workbook and return sheet/header metadata only."""

    accession = _text(figshare_article_id)
    request_url = FIGSHARE_API + accession
    status, payload = fetch_json(request_url)
    if status >= 400:
        raise RuntimeError(f"HTTP {status}")
    if not isinstance(payload, dict) or _text(payload.get("id")) != accession:
        raise ValueError("Figshare response did not match declared article accession")
    matches = [item for item in payload.get("files", []) if isinstance(item, dict) and _text(item.get("name")) == file_name]
    if len(matches) != 1:
        raise ValueError("declared Figshare workbook name is absent or ambiguous")
    download_url = _as_url(matches[0].get("download_url"))
    if not download_url:
        raise ValueError("declared Figshare workbook has no public download URL")

    archive = zipfile.ZipFile(BytesIO(fetch_bytes(download_url)))
    shared = _shared_strings(archive)
    sheets = []
    for sheet_name, sheet_path in _sheet_paths(archive):
        if sheet_path not in archive.namelist():
            continue
        sheets.append({
            "sheet_name": sheet_name,
            "header_values": _header_values(archive, sheet_path, shared),
        })
    return {
        "figshare_article_id": accession,
        "figshare_dataset_doi": _text(payload.get("doi")),
        "file_name": file_name,
        "download_url": download_url,
        "sheet_count": len(sheets),
        "sheets": sheets,
        "decision_boundary": (
            "This audit emits workbook sheet names and header values only. It does not emit data rows, "
            "establish a shared unit, identify a trait role, or estimate a biological effect."
        ),
    }


def write_declared_figshare_xlsx_header_audit(out_dir: str | Path, report: dict[str, object]) -> None:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "declared_figshare_xlsx_header_audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
