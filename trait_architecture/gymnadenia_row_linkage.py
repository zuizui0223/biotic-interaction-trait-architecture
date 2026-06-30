"""Audit row linkage in the public *Gymnadenia* package without emitting observations.

Only aggregate row counts, key overlaps, and denominator-consistency counts are
written. Individual trait, herbivory, and fitness values remain inside the
public source archive and are not retained by this repository.
"""

from __future__ import annotations

import json
import math
import re
import zipfile
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Any, Callable
import xml.etree.ElementTree as ET

from trait_architecture.dalechampia_linked_panel import (
    NS,
    _dataset_chain,
    _fetch_bytes,
    _fetch_json,
    _normalise_doi,
)


KEY_CANDIDATES = ("PlantID", "Year", "Region", "Population")
TABLE_NAMES = {
    "floral_traits": "Data__FloralTraitDifferences.xlsx",
    "herbivory": "Data__HerbivoryDifferences.xlsx",
    "reproductive_success": "Data__ReproductiveSuccessDifferences.xlsx",
    "pollinator_limitation": "Data__PollinatorLimitation.xlsx",
}
MAX_ROWS_PER_TABLE = 20_000


def _column_index(reference: str) -> int:
    letters = "".join(character for character in reference if character.isalpha())
    result = 0
    for character in letters:
        result = result * 26 + ord(character.upper()) - ord("A") + 1
    return result - 1


def _xlsx_cell_value(cell: ET.Element, shared: list[str]) -> str:
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        return "".join(cell.find("x:is", NS).itertext()) if cell.find("x:is", NS) is not None else ""
    value = cell.findtext("x:v", default="", namespaces=NS)
    if cell_type == "s" and value.isdigit() and int(value) < len(shared):
        return shared[int(value)]
    return value


def _xlsx_records(content: bytes) -> tuple[list[str], list[dict[str, str]], bool]:
    workbook = zipfile.ZipFile(BytesIO(content))
    shared: list[str] = []
    if "xl/sharedStrings.xml" in workbook.namelist():
        root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
        shared = ["".join(node.itertext()) for node in root.findall("x:si", NS)]
    sheets = sorted(name for name in workbook.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name))
    if not sheets:
        raise ValueError("xlsx has no worksheet")
    root = ET.fromstring(workbook.read(sheets[0]))
    rows = root.findall(".//x:sheetData/x:row", NS)
    if not rows:
        raise ValueError("xlsx has no rows")

    def read_row(row: ET.Element) -> dict[int, str]:
        values: dict[int, str] = {}
        for cell in row.findall("x:c", NS):
            reference = cell.get("r", "")
            if reference:
                values[_column_index(reference)] = _xlsx_cell_value(cell, shared).strip()
        return values

    header_cells = read_row(rows[0])
    headers = [header_cells[index] for index in range(max(header_cells) + 1)] if header_cells else []
    if not any(headers):
        raise ValueError("xlsx has no header values")
    records: list[dict[str, str]] = []
    truncated = False
    for row in rows[1:]:
        if len(records) >= MAX_ROWS_PER_TABLE:
            truncated = True
            break
        values = read_row(row)
        records.append({header: values.get(index, "") for index, header in enumerate(headers) if header})
    return headers, records, truncated


def _read_target_tables(archive: zipfile.ZipFile) -> dict[str, dict[str, object]]:
    available = {Path(member.filename).name: member for member in archive.infolist() if not member.is_dir()}
    tables: dict[str, dict[str, object]] = {}
    for label, expected_name in TABLE_NAMES.items():
        member = available.get(expected_name)
        if member is None:
            tables[label] = {"status": "missing", "file_name": expected_name, "headers": [], "records": [], "truncated": False}
            continue
        headers, records, truncated = _xlsx_records(archive.read(member))
        tables[label] = {
            "status": "read",
            "file_name": expected_name,
            "headers": headers,
            "records": records,
            "truncated": truncated,
        }
    return tables


def _shared_key_columns(left: dict[str, object], right: dict[str, object]) -> list[str]:
    left_headers = set(left["headers"])
    right_headers = set(right["headers"])
    return [column for column in KEY_CANDIDATES if column in left_headers and column in right_headers]


def _keys(records: list[dict[str, str]], columns: list[str]) -> list[tuple[str, ...]]:
    return [tuple(record.get(column, "").strip() for column in columns) for record in records if all(record.get(column, "").strip() for column in columns)]


def _table_summary(table: dict[str, object], key_columns: list[str]) -> dict[str, object]:
    records = table["records"]
    keys = _keys(records, key_columns) if key_columns else []
    counts = Counter(keys)
    return {
        "file_name": table["file_name"],
        "status": table["status"],
        "row_count": len(records),
        "row_limit_reached": table["truncated"],
        "key_columns": key_columns,
        "complete_key_rows": len(keys),
        "distinct_complete_keys": len(counts),
        "duplicate_complete_key_rows": sum(count for count in counts.values() if count > 1),
    }


def _overlap(left: dict[str, object], right: dict[str, object]) -> dict[str, object]:
    columns = _shared_key_columns(left, right)
    left_keys = _keys(left["records"], columns) if columns else []
    right_keys = _keys(right["records"], columns) if columns else []
    left_counts = Counter(left_keys)
    right_counts = Counter(right_keys)
    common = set(left_counts).intersection(right_counts)
    unique_common = {key for key in common if left_counts[key] == 1 and right_counts[key] == 1}
    return {
        "key_columns": columns,
        "left_complete_key_rows": len(left_keys),
        "right_complete_key_rows": len(right_keys),
        "distinct_common_keys": len(common),
        "one_to_one_common_keys": len(unique_common),
        "left_duplicate_complete_key_rows": sum(count for count in left_counts.values() if count > 1),
        "right_duplicate_complete_key_rows": sum(count for count in right_counts.values() if count > 1),
    }


def _number(value: str) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _herbivory_denominator_summary(floral: dict[str, object], herbivory: dict[str, object]) -> dict[str, object]:
    columns = _shared_key_columns(floral, herbivory)
    if not columns or "NrFlowers" not in floral["headers"] or "NrFlowersEaten" not in herbivory["headers"]:
        return {
            "status": "not_assessable_from_headers",
            "key_columns": columns,
            "reason": "Required linkage or outcome columns are missing.",
        }
    floral_map: dict[tuple[str, ...], dict[str, str]] = {}
    floral_counts: Counter[tuple[str, ...]] = Counter()
    for record in floral["records"]:
        key = tuple(record.get(column, "").strip() for column in columns)
        if all(key):
            floral_counts[key] += 1
            floral_map[key] = record
    herbivory_map: dict[tuple[str, ...], dict[str, str]] = {}
    herbivory_counts: Counter[tuple[str, ...]] = Counter()
    for record in herbivory["records"]:
        key = tuple(record.get(column, "").strip() for column in columns)
        if all(key):
            herbivory_counts[key] += 1
            herbivory_map[key] = record
    keys = {key for key in set(floral_counts).intersection(herbivory_counts) if floral_counts[key] == 1 and herbivory_counts[key] == 1}
    valid = 0
    invalid_order = 0
    missing_numeric = 0
    for key in keys:
        denominator = _number(floral_map[key].get("NrFlowers", ""))
        eaten = _number(herbivory_map[key].get("NrFlowersEaten", ""))
        if denominator is None or eaten is None or denominator <= 0 or eaten < 0:
            missing_numeric += 1
        elif eaten > denominator:
            invalid_order += 1
        else:
            valid += 1
    return {
        "status": "header_and_key_contract_checked",
        "key_columns": columns,
        "one_to_one_linked_rows": len(keys),
        "numeric_nonnegative_outcome_with_positive_denominator": valid,
        "eaten_exceeds_linked_flower_count": invalid_order,
        "missing_or_nonpositive_numeric_contract": missing_numeric,
        "timing_definition_status": "pending_article_methods_review",
        "decision_boundary": "Aggregate consistency is not an effect estimate and does not establish whether the flower-eaten count and flower count share the same observation window.",
    }


def audit_gymnadenia_row_linkage(
    *,
    dataset_doi: str,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
    fetch_bytes: Callable[[str], bytes] = _fetch_bytes,
) -> dict[str, object]:
    """Return aggregate linkage evidence for the Gymnadenia archive only."""

    dataset_doi = _normalise_doi(dataset_doi)
    file_names, version_url, archive_url = _dataset_chain(dataset_doi, fetch_json)
    archive = zipfile.ZipFile(BytesIO(fetch_bytes(archive_url)))
    tables = _read_target_tables(archive)
    floral = tables["floral_traits"]
    herbivory = tables["herbivory"]
    reproductive = tables["reproductive_success"]
    limitation = tables["pollinator_limitation"]
    return {
        "dataset_doi": dataset_doi,
        "version_url": version_url,
        "archive_url": archive_url,
        "manifest_file_count": len(file_names),
        "table_summaries": {
            "floral_traits": _table_summary(floral, KEY_CANDIDATES),
            "herbivory": _table_summary(herbivory, KEY_CANDIDATES),
            "reproductive_success": _table_summary(reproductive, KEY_CANDIDATES),
            "pollinator_limitation": _table_summary(limitation, KEY_CANDIDATES),
        },
        "pairwise_overlap": {
            "floral_traits_to_herbivory": _overlap(floral, herbivory),
            "floral_traits_to_reproductive_success": _overlap(floral, reproductive),
            "floral_traits_to_pollinator_limitation": _overlap(floral, limitation),
        },
        "herbivory_denominator_contract": _herbivory_denominator_summary(floral, herbivory),
        "decision_boundary": "No observation rows or values are written. This audit establishes only aggregate key overlap and numerical denominator consistency; article methods must still establish trait definitions and sampling timing before effect extraction.",
    }


def write_gymnadenia_row_linkage_audit(out_dir: str | Path, report: dict[str, object]) -> None:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "gymnadenia_row_linkage_audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
