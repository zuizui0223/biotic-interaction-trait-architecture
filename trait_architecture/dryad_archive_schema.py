"""Header-only fallback for a title-validated Dryad version archive.

Some public Dryad file-level API download routes can reject automated requests
while a version-level archive remains available. This module tries the archive
only after title-gated manifest recovery. It reads CSV headers in memory and
writes schema metadata, never raw rows or an archive copy.
"""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable
from urllib.request import Request, urlopen

from .dryad_table_schema import MAX_HEADER_BYTES, _candidate_keys, _header_from_bytes
from .title_validated_dryad_manifest import DryadManifestReceipt, probe_targets


USER_AGENT = "biotic-interaction-trait-architecture dryad-archive-schema/0.2"
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
VERSION_URL_RE = re.compile(r"^https://datadryad\.org/api/v2/versions/(\d+)$")


@dataclass(frozen=True)
class DryadArchiveSchema:
    target_id: str
    queue_id: str
    study_id: str
    dataset_doi: str
    version_archive_url: str
    file_name: str
    schema_status: str
    delimiter: str
    column_count: int
    column_names: str
    candidate_linkage_columns: str
    notes: str


SCHEMA_FIELDS = tuple(DryadArchiveSchema.__dataclass_fields__)


def _text(value: object) -> str:
    return str(value or "").strip()


def _version_url(receipt: DryadManifestReceipt) -> str:
    for url in receipt.dryad_request_url.split(";"):
        if VERSION_URL_RE.fullmatch(url):
            return url
    return ""


def _download_archive(url: str, *, landing_page_url: str, timeout: int = 45) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/zip,application/octet-stream,*/*",
            "Referer": landing_page_url,
        },
    )
    with urlopen(request, timeout=timeout) as response:  # nosec B310: title-gated public version archive
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_ARCHIVE_BYTES:
            raise ValueError(f"archive is larger than configured limit ({length} bytes)")
        content = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(content) > MAX_ARCHIVE_BYTES:
        raise ValueError("archive exceeded configured byte limit")
    return content


def inspect_archive_receipt(
    receipt: DryadManifestReceipt,
    *,
    download_archive: Callable[[str, str], bytes] | None = None,
) -> list[DryadArchiveSchema]:
    """Read CSV headers from one title-gated Dryad archive in memory."""

    version_url = _version_url(receipt)
    archive_url = f"{version_url}/download" if version_url else ""
    if not archive_url:
        return [DryadArchiveSchema(
            target_id=receipt.target_id, queue_id=receipt.queue_id, study_id=receipt.study_id,
            dataset_doi=receipt.dataset_doi, version_archive_url="", file_name="",
            schema_status="archive_route_not_identified", delimiter="", column_count=0,
            column_names="", candidate_linkage_columns="",
            notes="Manifest receipt did not retain a Dryad version endpoint.",
        )]
    downloader = download_archive or (lambda url, landing: _download_archive(url, landing_page_url=landing))
    try:
        content = downloader(archive_url, receipt.landing_page_url)
        archive = zipfile.ZipFile(io.BytesIO(content))
    except Exception as error:
        return [DryadArchiveSchema(
            target_id=receipt.target_id, queue_id=receipt.queue_id, study_id=receipt.study_id,
            dataset_doi=receipt.dataset_doi, version_archive_url=archive_url, file_name="",
            schema_status="archive_access_failed", delimiter="", column_count=0,
            column_names="", candidate_linkage_columns="",
            notes=f"{type(error).__name__}: {error}",
        )]

    rows: list[DryadArchiveSchema] = []
    for member in sorted(archive.infolist(), key=lambda item: item.filename):
        if member.is_dir() or not member.filename.lower().endswith(".csv"):
            continue
        try:
            with archive.open(member) as handle:
                prefix = handle.read(MAX_HEADER_BYTES)
            delimiter, columns = _header_from_bytes(prefix)
            rows.append(DryadArchiveSchema(
                target_id=receipt.target_id, queue_id=receipt.queue_id, study_id=receipt.study_id,
                dataset_doi=receipt.dataset_doi, version_archive_url=archive_url, file_name=member.filename,
                schema_status="header_recovered", delimiter=delimiter, column_count=len(columns),
                column_names=";".join(columns), candidate_linkage_columns=";".join(_candidate_keys(columns)),
                notes="Header only from public version archive; no raw rows or archive retained.",
            ))
        except Exception as error:
            rows.append(DryadArchiveSchema(
                target_id=receipt.target_id, queue_id=receipt.queue_id, study_id=receipt.study_id,
                dataset_doi=receipt.dataset_doi, version_archive_url=archive_url, file_name=member.filename,
                schema_status="header_parse_failed", delimiter="", column_count=0,
                column_names="", candidate_linkage_columns="",
                notes=f"{type(error).__name__}: {error}",
            ))
    if not rows:
        rows.append(DryadArchiveSchema(
            target_id=receipt.target_id, queue_id=receipt.queue_id, study_id=receipt.study_id,
            dataset_doi=receipt.dataset_doi, version_archive_url=archive_url, file_name="",
            schema_status="archive_no_csv", delimiter="", column_count=0,
            column_names="", candidate_linkage_columns="",
            notes="Archive was retrieved but contained no CSV members.",
        ))
    return rows


def _archive_group_key(receipt: DryadManifestReceipt) -> tuple[str, str, str]:
    """Identify one physical archive even when its manifest has many file rows."""

    return receipt.target_id, receipt.dataset_doi, _version_url(receipt)


def inspect_targets(
    target_rows: Iterable[dict[str, str]],
    *,
    fetch_json: Callable | None = None,
    download_archive: Callable[[str, str], bytes] | None = None,
) -> tuple[list[DryadArchiveSchema], dict[str, object]]:
    kwargs = {"fetch_json": fetch_json} if fetch_json is not None else {}
    receipts, manifest_report = probe_targets(target_rows, **kwargs)
    representatives: dict[tuple[str, str, str], DryadManifestReceipt] = {}
    for receipt in receipts:
        if receipt.manifest_status != "manifest_recovered":
            continue
        representatives.setdefault(_archive_group_key(receipt), receipt)

    rows: list[DryadArchiveSchema] = []
    for receipt in representatives.values():
        rows.extend(inspect_archive_receipt(receipt, download_archive=download_archive))
    labels = sorted({row.schema_status for row in rows})
    return rows, {
        "manifest": manifest_report,
        "archive_schema": {
            "unique_archives": len(representatives),
            "row_count": len(rows),
            "counts_by_status": {label: sum(row.schema_status == label for row in rows) for label in labels},
            "warning": "Archive headers are a structural screen only; they do not establish trait role, linkage, denominator, causal status, or a four-path effect estimate.",
        },
    }


def write_schemas(out_dir: str | Path, rows: Iterable[DryadArchiveSchema], report: dict[str, object]) -> None:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "dryad_archive_csv_header_schemas.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCHEMA_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
    (output / "dryad_archive_csv_header_schema_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
