"""Resolve exact Figshare accessions declared in a focal article's data statement.

The resolver accepts only an accession explicitly recorded in a source queue
from the article's public Data Availability statement. It never performs a
keyword search and never downloads table contents. It writes only file-manifest
metadata, preserving the distinction between a declared dataset location and a
recoverable trait-to-outcome effect.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

from trait_architecture.public_repository_resolver import (
    RepositoryReceipt,
    _as_url,
    _fetch_json,
    _normalise_doi,
    _text,
)


FIGSHARE_API = "https://api.figshare.com/v2/articles/"


def resolve_declared_figshare_row(
    row: dict[str, str],
    *,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
) -> list[RepositoryReceipt]:
    """Resolve one exact article-declared Figshare accession to manifest receipts."""

    accession = _text(row.get("declared_figshare_article_id"))
    if not accession:
        return []
    request_url = FIGSHARE_API + accession
    status, payload = fetch_json(request_url)
    if status >= 400:
        raise RuntimeError(f"HTTP {status}")
    if not isinstance(payload, dict) or _text(payload.get("id")) != accession:
        raise ValueError("Figshare response did not match declared article accession")

    study_doi = _normalise_doi(row["citation_or_doi"])
    dataset_doi = _normalise_doi(_text(payload.get("doi")))
    landing = _as_url(payload.get("url_public_html")) or f"https://figshare.com/articles/dataset/{accession}"
    files = payload.get("files")
    note = (
        "Exact Figshare accession was declared in the focal article's public Data Availability statement. "
        "Machine-readable file metadata recovered; table contents remain uninspected."
    )
    if isinstance(files, list) and files:
        receipts: list[RepositoryReceipt] = []
        for item in files:
            if not isinstance(item, dict):
                continue
            name = _text(item.get("name"))
            download = _as_url(item.get("download_url"))
            if name and download:
                receipts.append(RepositoryReceipt(
                    queue_id=row["queue_id"],
                    study_id=row["study_id"],
                    study_doi=study_doi,
                    repository="Figshare",
                    resolution_status="manifest_recovered",
                    request_url=request_url,
                    dataset_identifier=accession,
                    dataset_doi=dataset_doi,
                    landing_page_url=landing,
                    file_name=name,
                    file_url=download,
                    notes=note,
                ))
        if receipts:
            return receipts
    return [RepositoryReceipt(
        queue_id=row["queue_id"],
        study_id=row["study_id"],
        study_doi=study_doi,
        repository="Figshare",
        resolution_status="landing_page_only",
        request_url=request_url,
        dataset_identifier=accession,
        dataset_doi=dataset_doi,
        landing_page_url=landing,
        file_name="",
        file_url="",
        notes=(
            "Exact Figshare accession was declared in the focal article's public Data Availability statement, "
            "but this API response did not expose a file manifest."
        ),
    )]


def resolve_declared_figshare_queue(
    rows: Iterable[dict[str, str]],
    *,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
) -> tuple[list[RepositoryReceipt], dict[str, object]]:
    """Resolve a queue of exact article-declared Figshare accessions."""

    rows = list(rows)
    receipts: list[RepositoryReceipt] = []
    for row in rows:
        receipts.extend(resolve_declared_figshare_row(row, fetch_json=fetch_json))
    counts = {
        label: sum(receipt.resolution_status == label for receipt in receipts)
        for label in ("manifest_recovered", "landing_page_only")
    }
    return receipts, {
        "eligible_queue_rows": len(rows),
        "receipt_count": len(receipts),
        "counts_by_resolution_status": counts,
        "warning": (
            "A declared Figshare accession establishes a public source route only. "
            "It does not establish an eligible effect, trait role, common biological unit, or evidence level."
        ),
    }
