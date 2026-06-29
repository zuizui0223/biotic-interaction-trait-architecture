"""Inspect headers of title-validated Dryad CSVs without retaining raw rows.

The aim is structural screening: identify available tables, column names, and
candidate linkage fields before any model is fitted. This module downloads only
the initial bytes needed to parse a header line and writes no raw observations to
repository outputs.
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .title_validated_dryad_manifest import DryadManifestReceipt, probe_targets


USER_AGENT = "biotic-interaction-trait-architecture dryad-table-schema/0.2"
MAX_HEADER_BYTES = 131_072
CANDIDATE_KEY_TOKENS = (
    "plant", "individual", "id", "treatment", "block", "plot", "date", "site", "year",
)
DRYAD_API_DOWNLOAD_RE = re.compile(r"^https://datadryad\.org/api/v2/files/(\d+)/download$")


@dataclass(frozen=True)
class DryadTableSchema:
    target_id: str
    queue_id: str
    study_id: str
    dataset_doi: str
    file_name: str
    file_url: str
    schema_status: str
    delimiter: str
    column_count: int
    column_names: str
    candidate_linkage_columns: str
    notes: str


SCHEMA_FIELDS = tuple(DryadTableSchema.__dataclass_fields__)


def _text(value: object) -> str:
    return str(value or "").strip()


def _request_prefix(url: str, *, timeout: int, max_bytes: int) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/csv,text/plain,*/*"})
    with urlopen(request, timeout=timeout) as response:  # nosec B310: title-gated public file route
        return response.read(max_bytes)


def _public_file_stream_url(url: str) -> str:
    match = DRYAD_API_DOWNLOAD_RE.fullmatch(url)
    return f"https://datadryad.org/stash/downloads/file_stream/{match.group(1)}" if match else ""


def _download_prefix(url: str, *, timeout: int = 20, max_bytes: int = MAX_HEADER_BYTES) -> bytes:
    """Read a small prefix, trying Dryad's public stream when API download is denied."""

    try:
        return _request_prefix(url, timeout=timeout, max_bytes=max_bytes)
    except HTTPError as error:
        fallback = _public_file_stream_url(url)
        if error.code not in {401, 403} or not fallback:
            raise
        try:
            return _request_prefix(fallback, timeout=timeout, max_bytes=max_bytes)
        except Exception as fallback_error:
            raise RuntimeError(
                f"API download HTTP {error.code}; public file_stream fallback failed: "
                f"{type(fallback_error).__name__}: {fallback_error}"
            ) from fallback_error


def _header_from_bytes(raw: bytes) -> tuple[str, list[str]]:
    text = raw.decode("utf-8-sig", errors="replace")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("file prefix contains no non-empty line")
    sample = "\n".join(lines[:5])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
    except csv.Error:
        dialect = csv.excel
    header = next(csv.reader(io.StringIO(lines[0]), dialect=dialect))
    cleaned = [_text(value) for value in header]
    if not any(cleaned):
        raise ValueError("header row has no usable column names")
    return dialect.delimiter, cleaned


def _candidate_keys(columns: Iterable[str]) -> list[str]:
    keys: list[str] = []
    for column in columns:
        normalized = column.lower().replace("_", " ").replace("-", " ")
        if any(token in normalized for token in CANDIDATE_KEY_TOKENS):
            keys.append(column)
    return keys


def inspect_manifest_tables(
    receipts: Iterable[DryadManifestReceipt],
    *,
    download_prefix: Callable[[str], bytes] = _download_prefix,
) -> tuple[list[DryadTableSchema], dict[str, object]]:
    """Return one schema row for each manifest-recovered CSV, never raw data."""

    rows: list[DryadTableSchema] = []
    for receipt in receipts:
        if receipt.manifest_status != "manifest_recovered" or not receipt.file_name.lower().endswith(".csv"):
            continue
        try:
            raw = download_prefix(receipt.file_url)
            delimiter, columns = _header_from_bytes(raw)
            rows.append(DryadTableSchema(
                target_id=receipt.target_id,
                queue_id=receipt.queue_id,
                study_id=receipt.study_id,
                dataset_doi=receipt.dataset_doi,
                file_name=receipt.file_name,
                file_url=receipt.file_url,
                schema_status="header_recovered",
                delimiter=delimiter,
                column_count=len(columns),
                column_names=";".join(columns),
                candidate_linkage_columns=";".join(_candidate_keys(columns)),
                notes="Header only; no raw observations retained. Candidate linkage columns require semantic verification from README/methods.",
            ))
        except Exception as error:
            rows.append(DryadTableSchema(
                target_id=receipt.target_id,
                queue_id=receipt.queue_id,
                study_id=receipt.study_id,
                dataset_doi=receipt.dataset_doi,
                file_name=receipt.file_name,
                file_url=receipt.file_url,
                schema_status="table_access_failed",
                delimiter="",
                column_count=0,
                column_names="",
                candidate_linkage_columns="",
                notes=f"{type(error).__name__}: {error}",
            ))
    report = {
        "csv_manifest_rows": len(rows),
        "header_recovered": sum(row.schema_status == "header_recovered" for row in rows),
        "table_access_failed": sum(row.schema_status == "table_access_failed" for row in rows),
        "warning": "Column names and candidate keys are only a structural screen. They do not establish trait roles, linkage, denominators, causal interpretation, or an effect estimate.",
    }
    return rows, report


def inspect_targets(
    target_rows: Iterable[dict[str, str]],
    *,
    fetch_json: Callable | None = None,
    download_prefix: Callable[[str], bytes] = _download_prefix,
) -> tuple[list[DryadTableSchema], dict[str, object]]:
    """Resolve a title-validated manifest, then inspect only CSV headers."""

    kwargs = {"fetch_json": fetch_json} if fetch_json is not None else {}
    receipts, manifest_report = probe_targets(target_rows, **kwargs)
    schemas, schema_report = inspect_manifest_tables(receipts, download_prefix=download_prefix)
    return schemas, {"manifest": manifest_report, "schema": schema_report}


def write_schemas(out_dir: str | Path, rows: Iterable[DryadTableSchema], report: dict[str, object]) -> None:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "dryad_csv_header_schemas.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCHEMA_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
    (output / "dryad_csv_header_schema_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
