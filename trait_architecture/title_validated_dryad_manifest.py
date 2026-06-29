"""Recover Dryad file manifests from explicitly title-validated dataset targets.

This module has a deliberately narrow gate: a dataset is eligible only when its
DataCite title exactly matches the predeclared expected title after conservative
normalisation. Source identity is therefore explicit before repository-specific
links are followed.

A recovered manifest still establishes only an inspectable file route. It does
not establish usable A/B traits, shared biological units, denominators, or a
four-path effect estimate.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen


DRYAD_BASE_URL = "https://datadryad.org"
USER_AGENT = "biotic-interaction-trait-architecture title-validated-dryad-manifest/0.2"
REQUIRED_COLUMNS = {
    "target_id", "queue_id", "study_id", "study_doi", "repository", "dataset_doi",
    "expected_dataset_title", "validation_rule", "status",
}


@dataclass(frozen=True)
class DryadManifestReceipt:
    target_id: str
    queue_id: str
    study_id: str
    study_doi: str
    dataset_doi: str
    expected_dataset_title: str
    observed_dataset_title: str
    title_match: str
    manifest_status: str
    datacite_request_url: str
    dryad_request_url: str
    landing_page_url: str
    file_name: str
    file_url: str
    notes: str


RECEIPT_FIELDS = tuple(DryadManifestReceipt.__dataclass_fields__)


def _text(value: object) -> str:
    return str(value or "").strip()


def _normalise_doi(value: object) -> str:
    value = _text(value).lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if value.startswith(prefix):
            value = value[len(prefix):]
            break
    return value.strip()


def normalise_title(value: object) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", _text(value).lower())).strip()


def _fetch_json(url: str, *, timeout: int = 12) -> tuple[int, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed public endpoints
        status = int(getattr(response, "status", response.getcode()))
        payload = json.loads(response.read().decode("utf-8"))
    return status, payload


def read_targets(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [{key: _text(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    if not rows:
        raise ValueError("title-validated dataset target table is empty")
    missing = sorted(REQUIRED_COLUMNS.difference(rows[0]))
    if missing:
        raise ValueError(f"title-validated dataset target table missing columns: {', '.join(missing)}")
    for row in rows:
        if row["repository"] != "Dryad":
            raise ValueError("only Dryad title-validated targets are currently supported")
        if row["validation_rule"] != "exact_normalized_dataset_title_match":
            raise ValueError("unsupported validation_rule")
        if row["status"] != "ready_for_manifest_probe":
            raise ValueError("only ready_for_manifest_probe targets may be run")
    return rows


def _datacite_title(payload: Any) -> tuple[str, str]:
    if not isinstance(payload, dict):
        return "", ""
    data = payload.get("data")
    attrs = data.get("attributes") if isinstance(data, dict) and isinstance(data.get("attributes"), dict) else {}
    titles = attrs.get("titles")
    if isinstance(titles, list):
        for item in titles:
            if isinstance(item, dict) and _text(item.get("title")):
                return _text(item["title"]), _text(attrs.get("url"))
    return _text(attrs.get("title")), _text(attrs.get("url"))


def _walk(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from _walk(value)
    elif isinstance(payload, list):
        for value in payload:
            yield from _walk(value)


def _absolute_url(value: object) -> str:
    value = _text(value)
    return urljoin(DRYAD_BASE_URL, value) if value else ""


def _href(payload: Any, relation: str) -> str:
    if not isinstance(payload, dict):
        return ""
    links = payload.get("_links") or payload.get("links")
    if not isinstance(links, dict):
        return ""
    value = links.get(relation)
    if isinstance(value, dict):
        value = value.get("href")
    return _absolute_url(value)


def _files(payload: Any) -> list[tuple[str, str]]:
    """Extract file name/download links, resolving Dryad's relative HAL URLs."""

    found: set[tuple[str, str]] = set()
    for node in _walk(payload):
        attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else node
        if not isinstance(attrs, dict):
            continue
        name = _text(
            attrs.get("filename") or attrs.get("file_name") or attrs.get("path") or attrs.get("name")
        )
        download = _absolute_url(attrs.get("download_url") or attrs.get("content_url"))
        if not download:
            links = node.get("_links") or node.get("links")
            if isinstance(links, dict):
                for key in ("stash:download", "download", "content"):
                    value = links.get(key)
                    if isinstance(value, dict):
                        value = value.get("href")
                    download = _absolute_url(value)
                    if download:
                        break
        if name and download:
            found.add((name, download))
    return sorted(found)


def _dryad_urls(dataset_doi: str) -> tuple[str, str]:
    return (
        f"{DRYAD_BASE_URL}/api/v2/datasets/{quote(f'doi:{dataset_doi}', safe='')}",
        f"{DRYAD_BASE_URL}/api/v2/datasets/{quote(dataset_doi, safe='')}",
    )


def _fetch_related_payloads(
    dataset_payload: Any,
    dataset_url: str,
    fetch_json: Callable[[str], tuple[int, Any]],
) -> tuple[list[tuple[str, Any]], list[str], str]:
    """Follow Dryad's documented dataset → version → files chain once each."""

    payloads: list[tuple[str, Any]] = [(dataset_url, dataset_payload)]
    visited = {dataset_url}
    notes: list[str] = []

    version_url = _href(dataset_payload, "stash:version")
    if version_url and version_url not in visited:
        try:
            status, version_payload = fetch_json(version_url)
            if status >= 400:
                notes.append(f"version HTTP {status}")
            else:
                payloads.append((version_url, version_payload))
                visited.add(version_url)
        except Exception as error:
            notes.append(f"version {type(error).__name__}: {error}")

    for source_url, payload in tuple(payloads):
        files_url = _href(payload, "stash:files")
        if not files_url or files_url in visited:
            continue
        try:
            status, files_payload = fetch_json(files_url)
            if status >= 400:
                notes.append(f"files HTTP {status}")
            else:
                payloads.append((files_url, files_payload))
                visited.add(files_url)
        except Exception as error:
            notes.append(f"files {type(error).__name__}: {error}")
    return payloads, sorted(visited), "; ".join(notes)


def probe_target(
    row: dict[str, str],
    *,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
) -> list[DryadManifestReceipt]:
    dataset_doi = _normalise_doi(row["dataset_doi"])
    study_doi = _normalise_doi(row["study_doi"])
    datacite_url = f"https://api.datacite.org/dois/{quote(dataset_doi, safe='')}"
    base = {
        "target_id": row["target_id"], "queue_id": row["queue_id"], "study_id": row["study_id"],
        "study_doi": study_doi, "dataset_doi": dataset_doi, "expected_dataset_title": row["expected_dataset_title"],
        "datacite_request_url": datacite_url,
    }
    try:
        status, metadata = fetch_json(datacite_url)
        if status >= 400:
            raise RuntimeError(f"HTTP {status}")
        observed, landing = _datacite_title(metadata)
    except Exception as error:
        return [DryadManifestReceipt(
            **base, observed_dataset_title="", title_match="not_checked", manifest_status="datacite_access_failed",
            dryad_request_url="", landing_page_url="", file_name="", file_url="",
            notes=f"{type(error).__name__}: {error}",
        )]
    landing = landing or f"https://doi.org/{dataset_doi}"
    if normalise_title(observed) != normalise_title(row["expected_dataset_title"]):
        return [DryadManifestReceipt(
            **base, observed_dataset_title=observed, title_match="no", manifest_status="title_mismatch",
            dryad_request_url="", landing_page_url=landing, file_name="", file_url="",
            notes="DataCite title does not match the predeclared expected dataset title.",
        )]

    errors: list[str] = []
    for dataset_url in _dryad_urls(dataset_doi):
        try:
            status, dataset_payload = fetch_json(dataset_url)
            if status >= 400:
                errors.append(f"{dataset_url} HTTP {status}")
                continue
            payloads, visited, related_notes = _fetch_related_payloads(dataset_payload, dataset_url, fetch_json)
            files = sorted({file for _, payload in payloads for file in _files(payload)})
            route = ";".join(visited)
            if files:
                return [DryadManifestReceipt(
                    **base, observed_dataset_title=observed, title_match="yes", manifest_status="manifest_recovered",
                    dryad_request_url=route, landing_page_url=landing, file_name=name, file_url=url,
                    notes="Exact predeclared title matched DataCite metadata; Dryad dataset/version/files manifest chain recovered." + (f" Notes: {related_notes}" if related_notes else ""),
                ) for name, url in files]
            return [DryadManifestReceipt(
                **base, observed_dataset_title=observed, title_match="yes", manifest_status="landing_page_only",
                dryad_request_url=route, landing_page_url=landing, file_name="", file_url="",
                notes="Exact predeclared title matched DataCite metadata, but the Dryad dataset/version/files chain yielded no file metadata." + (f" Notes: {related_notes}" if related_notes else ""),
            )]
        except Exception as error:
            errors.append(f"{dataset_url} {type(error).__name__}: {error}")
    return [DryadManifestReceipt(
        **base, observed_dataset_title=observed, title_match="yes", manifest_status="dryad_access_failed",
        dryad_request_url=";".join(_dryad_urls(dataset_doi)), landing_page_url=landing,
        file_name="", file_url="", notes="; ".join(errors) or "Dryad endpoints did not respond.",
    )]


def probe_targets(
    rows: Iterable[dict[str, str]], *, fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
) -> tuple[list[DryadManifestReceipt], dict[str, object]]:
    target_rows = list(rows)
    receipts: list[DryadManifestReceipt] = []
    for row in target_rows:
        receipts.extend(probe_target(row, fetch_json=fetch_json))
    labels = sorted({receipt.manifest_status for receipt in receipts})
    return receipts, {
        "target_count": len(target_rows),
        "receipt_count": len(receipts),
        "counts_by_manifest_status": {label: sum(receipt.manifest_status == label for receipt in receipts) for label in labels},
        "warning": "A recovered manifest establishes only an inspectable data-file route. Trait functions, shared units, denominators, and quantitative four-path effects must be screened from table contents and methods.",
    }


def write_receipts(out_dir: str | Path, receipts: Iterable[DryadManifestReceipt], report: dict[str, object]) -> None:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "title_validated_dryad_manifest_receipts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECEIPT_FIELDS)
        writer.writeheader()
        for receipt in receipts:
            writer.writerow(asdict(receipt))
    (output / "title_validated_dryad_manifest_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
