"""Resolve public data-repository evidence before four-path effect extraction.

This module is deliberately receipt-first.  A repository hit is not an effect
estimate, and a landing page is not a recoverable table.  The resolver records
what can actually be recovered from a public endpoint:

``manifest_recovered``
    machine-readable file metadata are available;
``landing_page_only``
    a dataset or repository landing page is found but files are not enumerated;
``not_found``
    an endpoint responded but yielded no plausible repository object;
``access_failed``
    the public endpoint could not be queried reproducibly.

No raw table is downloaded here.  File acquisition and trait/outcome screening
remain a separate, predeclared step.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


USER_AGENT = "biotic-interaction-trait-architecture public-repository-resolver/0.1"
REQUIRED_QUEUE_COLUMNS = {"queue_id", "study_id", "citation_or_doi", "queue_status"}
ELIGIBLE_QUEUE_STATUSES = frozenset({"queued", "needs_repository_resolution"})


@dataclass(frozen=True)
class RepositoryReceipt:
    """One reproducible claim about data-repository discoverability."""

    queue_id: str
    study_id: str
    study_doi: str
    repository: str
    resolution_status: str
    request_url: str
    dataset_identifier: str
    dataset_doi: str
    landing_page_url: str
    file_name: str
    file_url: str
    notes: str


RECEIPT_FIELDS = tuple(RepositoryReceipt.__dataclass_fields__)


def _text(value: object) -> str:
    return str(value or "").strip()


def _normalise_doi(value: str) -> str:
    value = _text(value)
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if value.lower().startswith(prefix):
            value = value[len(prefix):]
            break
    return value.strip().lower()


def read_queue(path: str | Path) -> list[dict[str, str]]:
    """Read eligible four-path queue rows without changing their status."""

    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [{key: _text(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    if not rows:
        raise ValueError("four-path screen queue is empty")
    missing = sorted(REQUIRED_QUEUE_COLUMNS.difference(rows[0]))
    if missing:
        raise ValueError(f"four-path screen queue missing columns: {', '.join(missing)}")
    return [row for row in rows if row["queue_status"] in ELIGIBLE_QUEUE_STATUSES]


def _fetch_json(url: str, *, timeout: int = 45) -> tuple[int, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed public metadata endpoints
        status = int(getattr(response, "status", response.getcode()))
        payload = json.loads(response.read().decode("utf-8"))
    return status, payload


def _walk(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from _walk(value)
    elif isinstance(payload, list):
        for value in payload:
            yield from _walk(value)


def _as_url(value: object) -> str:
    text = _text(value)
    return text if text.startswith(("https://", "http://")) else ""


def _dryad_file_receipts(row: dict[str, str], request_url: str, payload: Any) -> list[RepositoryReceipt]:
    """Extract conservative Dryad-like file metadata from HAL/JSON:API payloads."""

    dataset_id = ""
    landing = ""
    dataset_doi = ""
    files: list[tuple[str, str]] = []
    for node in _walk(payload):
        attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else node
        if not isinstance(attrs, dict):
            continue
        dataset_id = dataset_id or _text(node.get("id") or attrs.get("id"))
        dataset_doi = dataset_doi or _normalise_doi(_text(attrs.get("doi") or attrs.get("identifier")))
        landing = landing or _as_url(attrs.get("url") or attrs.get("landing_page_url"))
        links = node.get("links") or node.get("_links")
        if isinstance(links, dict):
            for key in ("self", "html", "landing", "dataset"):
                candidate = links.get(key)
                if isinstance(candidate, dict):
                    candidate = candidate.get("href")
                landing = landing or _as_url(candidate)
        name = _text(attrs.get("filename") or attrs.get("file_name") or attrs.get("name"))
        download = _as_url(attrs.get("download_url") or attrs.get("url") or attrs.get("content_url"))
        if name and download:
            files.append((name, download))
    if files:
        unique = {(name, url) for name, url in files}
        return [
            RepositoryReceipt(
                queue_id=row["queue_id"], study_id=row["study_id"], study_doi=_normalise_doi(row["citation_or_doi"]),
                repository="Dryad", resolution_status="manifest_recovered", request_url=request_url,
                dataset_identifier=dataset_id, dataset_doi=dataset_doi, landing_page_url=landing,
                file_name=name, file_url=url,
                notes="Machine-readable file metadata recovered; table contents remain uninspected.",
            )
            for name, url in sorted(unique)
        ]
    if dataset_id or landing or dataset_doi:
        return [RepositoryReceipt(
            queue_id=row["queue_id"], study_id=row["study_id"], study_doi=_normalise_doi(row["citation_or_doi"]),
            repository="Dryad", resolution_status="landing_page_only", request_url=request_url,
            dataset_identifier=dataset_id, dataset_doi=dataset_doi, landing_page_url=landing,
            file_name="", file_url="",
            notes="Dryad-like record found but machine-readable file manifest was not recovered.",
        )]
    return []


def _datacite_receipts(row: dict[str, str], request_url: str, payload: Any) -> list[RepositoryReceipt]:
    """Return candidate data-object receipts from DataCite search results."""

    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        return []
    receipts: list[RepositoryReceipt] = []
    study_doi = _normalise_doi(row["citation_or_doi"])
    for item in payload["data"]:
        if not isinstance(item, dict):
            continue
        attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
        doi = _normalise_doi(_text(attrs.get("doi") or item.get("id")))
        title = ""
        titles = attrs.get("titles")
        if isinstance(titles, list) and titles and isinstance(titles[0], dict):
            title = _text(titles[0].get("title"))
        landing = _as_url(attrs.get("url")) or (f"https://doi.org/{doi}" if doi else "")
        related_text = json.dumps(attrs.get("relatedIdentifiers", []), sort_keys=True).lower()
        is_related = study_doi and study_doi in related_text
        if not is_related and study_doi and study_doi not in title.lower():
            continue
        receipts.append(RepositoryReceipt(
            queue_id=row["queue_id"], study_id=row["study_id"], study_doi=study_doi,
            repository="DataCite", resolution_status="landing_page_only", request_url=request_url,
            dataset_identifier=_text(item.get("id")), dataset_doi=doi, landing_page_url=landing,
            file_name="", file_url="",
            notes="DataCite record related to study DOI; inspect landing page or repository API for file manifest.",
        ))
    return receipts


def _zenodo_receipts(row: dict[str, str], request_url: str, payload: Any) -> list[RepositoryReceipt]:
    """Extract Zenodo record and file manifest if an exact study DOI is linked."""

    hits = payload.get("hits") if isinstance(payload, dict) else None
    records = hits.get("hits") if isinstance(hits, dict) else None
    if not isinstance(records, list):
        return []
    study_doi = _normalise_doi(row["citation_or_doi"])
    receipts: list[RepositoryReceipt] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        related = json.dumps(metadata.get("related_identifiers", []), sort_keys=True).lower()
        if study_doi and study_doi not in related:
            continue
        record_id = _text(record.get("id"))
        landing = _as_url(record.get("links", {}).get("html")) if isinstance(record.get("links"), dict) else ""
        files = record.get("files")
        if isinstance(files, list) and files:
            for file in files:
                if not isinstance(file, dict):
                    continue
                name = _text(file.get("key") or file.get("filename"))
                links = file.get("links") if isinstance(file.get("links"), dict) else {}
                download = _as_url(links.get("self") or links.get("download"))
                if name and download:
                    receipts.append(RepositoryReceipt(
                        queue_id=row["queue_id"], study_id=row["study_id"], study_doi=study_doi,
                        repository="Zenodo", resolution_status="manifest_recovered", request_url=request_url,
                        dataset_identifier=record_id, dataset_doi=_normalise_doi(_text(metadata.get("doi"))),
                        landing_page_url=landing, file_name=name, file_url=download,
                        notes="Machine-readable Zenodo file metadata recovered; table contents remain uninspected.",
                    ))
        elif record_id or landing:
            receipts.append(RepositoryReceipt(
                queue_id=row["queue_id"], study_id=row["study_id"], study_doi=study_doi,
                repository="Zenodo", resolution_status="landing_page_only", request_url=request_url,
                dataset_identifier=record_id, dataset_doi=_normalise_doi(_text(metadata.get("doi"))),
                landing_page_url=landing, file_name="", file_url="",
                notes="Zenodo record related to study DOI; file manifest unavailable in this response.",
            ))
    return receipts


def _mendeley_known_receipt(row: dict[str, str]) -> list[RepositoryReceipt]:
    """Emit a receipt only for explicitly known Mendeley Data dataset handles.

    The four-path queue currently records Rivea as screened, so this route mainly
    proves that an exact repository handle is preserved rather than guessed.
    """

    known_handles = {
        "10.1186/s12862-024-02301-7": "10.17632/2n4vgpvzgs.1",
    }
    study_doi = _normalise_doi(row["citation_or_doi"])
    handle = known_handles.get(study_doi)
    if not handle:
        return []
    token = handle.split("/")[-1].split(".")[0]
    version = handle.split(".")[-1]
    return [RepositoryReceipt(
        queue_id=row["queue_id"], study_id=row["study_id"], study_doi=study_doi,
        repository="Mendeley Data", resolution_status="landing_page_only",
        request_url="explicit_known_dataset_handle", dataset_identifier=token, dataset_doi=handle,
        landing_page_url=f"https://data.mendeley.com/datasets/{token}/{version}",
        file_name="", file_url="",
        notes="Exact dataset DOI was verified in prior full-text screening; file manifest is not scraped without a documented public endpoint.",
    )]


def _error_receipt(row: dict[str, str], repository: str, request_url: str, error: Exception) -> RepositoryReceipt:
    return RepositoryReceipt(
        queue_id=row["queue_id"], study_id=row["study_id"], study_doi=_normalise_doi(row["citation_or_doi"]),
        repository=repository, resolution_status="access_failed", request_url=request_url,
        dataset_identifier="", dataset_doi="", landing_page_url="", file_name="", file_url="",
        notes=f"{type(error).__name__}: {error}",
    )


def resolve_row(
    row: dict[str, str],
    *,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
) -> list[RepositoryReceipt]:
    """Resolve one queue row against documented metadata endpoints.

    The resolver intentionally records endpoint failure rather than silently
    omitting it; this distinguishes absent data from inaccessible data.
    """

    doi = _normalise_doi(row["citation_or_doi"])
    receipts: list[RepositoryReceipt] = []
    dryad_url = "https://datadryad.org/api/v2/search?" + urlencode({"query": doi})
    datacite_url = "https://api.datacite.org/dois?" + urlencode({"query": doi, "page[size]": "25"})
    zenodo_url = "https://zenodo.org/api/records?" + urlencode({"q": f'"{doi}"', "size": "25"})

    for repository, request_url, extractor in (
        ("Dryad", dryad_url, _dryad_file_receipts),
        ("DataCite", datacite_url, _datacite_receipts),
        ("Zenodo", zenodo_url, _zenodo_receipts),
    ):
        try:
            status, payload = fetch_json(request_url)
            if status >= 400:
                raise RuntimeError(f"HTTP {status}")
            found = extractor(row, request_url, payload)
            if found:
                receipts.extend(found)
            else:
                receipts.append(RepositoryReceipt(
                    queue_id=row["queue_id"], study_id=row["study_id"], study_doi=doi,
                    repository=repository, resolution_status="not_found", request_url=request_url,
                    dataset_identifier="", dataset_doi="", landing_page_url="", file_name="", file_url="",
                    notes="Endpoint responded, but no study-linked repository object was recovered.",
                ))
        except Exception as error:  # public endpoints differ in availability; record but do not abort other routes
            receipts.append(_error_receipt(row, repository, request_url, error))
    receipts.extend(_mendeley_known_receipt(row))
    return receipts


def resolve_queue(
    rows: Iterable[dict[str, str]],
    *,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
) -> tuple[list[RepositoryReceipt], dict[str, object]]:
    receipts: list[RepositoryReceipt] = []
    for row in rows:
        receipts.extend(resolve_row(row, fetch_json=fetch_json))
    counts = {label: sum(receipt.resolution_status == label for receipt in receipts) for label in (
        "manifest_recovered", "landing_page_only", "not_found", "access_failed",
    )}
    report = {
        "eligible_queue_rows": len(list(rows)) if not isinstance(rows, list) else len(rows),
        "receipt_count": len(receipts),
        "counts_by_resolution_status": counts,
        "warning": "Repository receipts establish discoverability only. They do not establish a recoverable trait→outcome effect, independent A/B traits, or a four-path evidence level.",
    }
    return receipts, report


def write_receipts(out_dir: str | Path, receipts: Iterable[RepositoryReceipt], report: dict[str, object]) -> None:
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    with (path / "public_repository_receipts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECEIPT_FIELDS)
        writer.writeheader()
        for receipt in receipts:
            writer.writerow(asdict(receipt))
    (path / "public_repository_resolution_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
