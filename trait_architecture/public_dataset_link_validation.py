"""Validate candidate public dataset links before table inspection.

A dataset DOI discovered by a broad metadata search is only a *candidate*.  This
module requires an exact, permitted DataCite relation from the dataset record to
the target study DOI before querying a repository-specific manifest route.

The current implementation covers Dryad candidates. It records validation
results and file metadata only; it does not download a data table or create a
four-path effect record.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import quote
from urllib.request import Request, urlopen


USER_AGENT = "biotic-interaction-trait-architecture dataset-link-validation/0.1"
REQUIRED_CANDIDATE_COLUMNS = {
    "candidate_id", "queue_id", "study_id", "study_doi", "repository", "dataset_doi", "link_status",
}
ALLOWED_RELATION_TYPES = frozenset({"issupplementto", "isderivedfrom", "ispartof"})


@dataclass(frozen=True)
class DatasetLinkReceipt:
    candidate_id: str
    queue_id: str
    study_id: str
    study_doi: str
    repository: str
    dataset_doi: str
    dataset_title: str
    relation_type: str
    validation_status: str
    datacite_request_url: str
    repository_request_url: str
    landing_page_url: str
    file_name: str
    file_url: str
    notes: str


RECEIPT_FIELDS = tuple(DatasetLinkReceipt.__dataclass_fields__)


def _text(value: object) -> str:
    return str(value or "").strip()


def normalise_doi(value: object) -> str:
    doi = _text(value).lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi.strip()


def _fetch_json(url: str, *, timeout: int = 12) -> tuple[int, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed public metadata endpoints
        status = int(getattr(response, "status", response.getcode()))
        payload = json.loads(response.read().decode("utf-8"))
    return status, payload


def read_candidates(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [{key: _text(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    if not rows:
        raise ValueError("public dataset-link candidate table is empty")
    missing = sorted(REQUIRED_CANDIDATE_COLUMNS.difference(rows[0]))
    if missing:
        raise ValueError(f"public dataset-link candidate table missing columns: {', '.join(missing)}")
    for row in rows:
        if row["repository"] != "Dryad":
            raise ValueError("only Dryad candidates are currently supported")
        if not normalise_doi(row["study_doi"]) or not normalise_doi(row["dataset_doi"]):
            raise ValueError("study_doi and dataset_doi must be supplied")
    return rows


def _dataset_title(attributes: dict[str, Any]) -> str:
    titles = attributes.get("titles")
    if isinstance(titles, list):
        for item in titles:
            if isinstance(item, dict) and _text(item.get("title")):
                return _text(item["title"])
    return _text(attributes.get("title"))


def _exact_relation_type(attributes: dict[str, Any], study_doi: str) -> str:
    related = attributes.get("relatedIdentifiers") or attributes.get("related_identifiers")
    if not isinstance(related, list):
        return ""
    for item in related:
        if not isinstance(item, dict):
            continue
        target = normalise_doi(item.get("relatedIdentifier") or item.get("identifier"))
        relation = _text(item.get("relationType") or item.get("relation_type"))
        if target == study_doi and relation.lower() in ALLOWED_RELATION_TYPES:
            return relation
    return ""


def _walk(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from _walk(value)
    elif isinstance(payload, list):
        for value in payload:
            yield from _walk(value)


def _url(value: object) -> str:
    text = _text(value)
    return text if text.startswith(("https://", "http://")) else ""


def _manifest_links(payload: Any) -> list[str]:
    urls: list[str] = []
    for node in _walk(payload):
        links = node.get("links") or node.get("_links")
        if not isinstance(links, dict):
            continue
        for key, value in links.items():
            if "file" not in key.lower() and "stash:files" not in key.lower():
                continue
            href = value.get("href") if isinstance(value, dict) else value
            url = _url(href)
            if url:
                urls.append(url)
    return sorted(set(urls))


def _file_rows(payload: Any) -> list[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for node in _walk(payload):
        attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else node
        if not isinstance(attrs, dict):
            continue
        name = _text(attrs.get("filename") or attrs.get("file_name") or attrs.get("name"))
        download = _url(attrs.get("download_url") or attrs.get("content_url"))
        links = node.get("links") or node.get("_links")
        if not download and isinstance(links, dict):
            for key in ("download", "content", "self"):
                value = links.get(key)
                if isinstance(value, dict):
                    value = value.get("href")
                download = _url(value)
                if download:
                    break
        if name and download:
            found.add((name, download))
    return sorted(found)


def _dryad_dataset_urls(dataset_doi: str) -> tuple[str, ...]:
    encoded = quote(f"doi:{dataset_doi}", safe="")
    return (
        f"https://datadryad.org/api/v2/datasets/{encoded}",
        f"https://datadryad.org/api/v2/datasets/{quote(dataset_doi, safe='')}",
    )


def validate_candidate(
    row: dict[str, str],
    *,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
) -> list[DatasetLinkReceipt]:
    study_doi = normalise_doi(row["study_doi"])
    dataset_doi = normalise_doi(row["dataset_doi"])
    datacite_url = f"https://api.datacite.org/dois/{quote(dataset_doi, safe='')}"
    base = {
        "candidate_id": row["candidate_id"], "queue_id": row["queue_id"], "study_id": row["study_id"],
        "study_doi": study_doi, "repository": row["repository"], "dataset_doi": dataset_doi,
        "datacite_request_url": datacite_url,
    }
    try:
        status, payload = fetch_json(datacite_url)
        if status >= 400 or not isinstance(payload, dict):
            raise RuntimeError(f"DataCite HTTP {status}")
        data = payload.get("data")
        attributes = data.get("attributes") if isinstance(data, dict) and isinstance(data.get("attributes"), dict) else {}
        relation_type = _exact_relation_type(attributes, study_doi)
        title = _dataset_title(attributes)
        landing = _url(attributes.get("url")) or f"https://doi.org/{dataset_doi}"
        if not relation_type:
            return [DatasetLinkReceipt(
                **base, dataset_title=title, relation_type="", validation_status="candidate_rejected",
                repository_request_url="", landing_page_url=landing, file_name="", file_url="",
                notes="Dataset metadata does not contain an exact permitted relation to the target study DOI.",
            )]
    except Exception as error:
        return [DatasetLinkReceipt(
            **base, dataset_title="", relation_type="", validation_status="datacite_access_failed",
            repository_request_url="", landing_page_url="", file_name="", file_url="",
            notes=f"{type(error).__name__}: {error}",
        )]

    last_error = ""
    for dryad_url in _dryad_dataset_urls(dataset_doi):
        try:
            status, payload = fetch_json(dryad_url)
            if status >= 400:
                last_error = f"HTTP {status}"
                continue
            files = _file_rows(payload)
            for link in _manifest_links(payload):
                try:
                    link_status, link_payload = fetch_json(link)
                    if link_status < 400:
                        files.extend(_file_rows(link_payload))
                except Exception as error:  # retain dataset-level receipt below
                    last_error = f"manifest-link {type(error).__name__}: {error}"
            files = sorted(set(files))
            if files:
                return [DatasetLinkReceipt(
                    **base, dataset_title=title, relation_type=relation_type,
                    validation_status="link_validated_manifest_recovered", repository_request_url=dryad_url,
                    landing_page_url=landing, file_name=name, file_url=url,
                    notes="Exact DataCite relation validated; machine-readable Dryad file metadata recovered.",
                ) for name, url in files]
            return [DatasetLinkReceipt(
                **base, dataset_title=title, relation_type=relation_type,
                validation_status="link_validated_landing_only", repository_request_url=dryad_url,
                landing_page_url=landing, file_name="", file_url="",
                notes="Exact DataCite relation validated, but no Dryad file manifest was recovered from this endpoint.",
            )]
        except Exception as error:
            last_error = f"{type(error).__name__}: {error}"
    return [DatasetLinkReceipt(
        **base, dataset_title=title, relation_type=relation_type,
        validation_status="dryad_access_failed", repository_request_url=";".join(_dryad_dataset_urls(dataset_doi)),
        landing_page_url=landing, file_name="", file_url="",
        notes=last_error or "Dryad endpoint did not yield a response.",
    )]


def validate_candidates(
    rows: Iterable[dict[str, str]],
    *,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
) -> tuple[list[DatasetLinkReceipt], dict[str, object]]:
    candidate_rows = list(rows)
    receipts: list[DatasetLinkReceipt] = []
    for row in candidate_rows:
        receipts.extend(validate_candidate(row, fetch_json=fetch_json))
    statuses = sorted({receipt.validation_status for receipt in receipts})
    return receipts, {
        "candidate_count": len(candidate_rows),
        "receipt_count": len(receipts),
        "counts_by_validation_status": {status: sum(receipt.validation_status == status for receipt in receipts) for status in statuses},
        "warning": "Link validation and file-manifest recovery do not establish usable columns, denominators, trait functions, or a four-path effect record.",
    }


def write_receipts(out_dir: str | Path, receipts: Iterable[DatasetLinkReceipt], report: dict[str, object]) -> None:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "public_dataset_link_receipts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECEIPT_FIELDS)
        writer.writeheader()
        for receipt in receipts:
            writer.writerow(asdict(receipt))
    (output / "public_dataset_link_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
