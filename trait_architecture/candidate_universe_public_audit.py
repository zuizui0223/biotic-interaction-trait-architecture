"""Shallow public-route audit across the fixed 258-work M0 candidate universe.

This module deliberately separates discovery from evidence. It does not fetch
article PDFs, archive contents, supplements, or biological observations. For
each fixed bibliographic candidate it records only:

* the OpenAlex OA route retained in the fixed snapshot;
* DOI-exact Crossref metadata/content-link candidates; and
* Dryad/DataCite/Zenodo repository candidates from public metadata endpoints.

Repository and content links remain *candidates*. A later access/provenance
screen must verify that a link is publicly reachable and belongs to the focal
article before any table or effect extraction occurs.
"""

from __future__ import annotations

import csv
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .fixed_candidate_universe import CandidateSnapshotReceipt
from .public_article_source_scout import ArticleSourceReceipt, crossref_receipts, normalise_doi
from .public_repository_resolver import RepositoryReceipt, resolve_row


USER_AGENT = "biotic-interaction-trait-architecture candidate-universe-audit/0.1"
CANDIDATE_FIELDS = (
    "candidate_id", "title", "authors", "publication_year", "work_type", "doi",
    "seed_routes", "seed_query_ids", "is_open_access", "open_access_url",
    "metadata_match_score", "metadata_attraction_signal", "metadata_barrier_signal",
    "metadata_pollination_signal", "metadata_antagonist_signal", "metadata_recoverability_signal",
    "doi_status", "snapshot_oa_route", "crossref_metadata_status",
    "crossref_content_link_count", "crossref_pdf_link_count",
    "repository_manifest_candidate_count", "repository_landing_candidate_count",
    "repository_access_failed_count", "route_lane", "triage_score", "do_not_infer",
)
RECEIPT_FIELDS = (
    "candidate_id", "study_doi", "provider", "source_kind", "resolution_status",
    "request_url", "landing_page_url", "content_url", "content_type", "notes",
)


@dataclass(frozen=True)
class CandidateRouteSummary:
    doi: str
    crossref_metadata_status: str
    crossref_content_link_count: int
    crossref_pdf_link_count: int
    repository_manifest_candidate_count: int
    repository_landing_candidate_count: int
    repository_access_failed_count: int
    receipts: tuple[dict[str, str], ...]


class HostIntervalJsonFetcher:
    """Thread-safe public JSON fetcher with a minimum interval per host."""

    def __init__(self, min_host_interval_seconds: float = 0.30):
        if min_host_interval_seconds <= 0:
            raise ValueError("min_host_interval_seconds must be positive")
        self.min_host_interval_seconds = min_host_interval_seconds
        self._lock = threading.Lock()
        self._next_allowed: dict[str, float] = {}

    def __call__(self, url: str) -> tuple[int, Any]:
        host = urlparse(url).netloc or "unknown"
        with self._lock:
            now = time.monotonic()
            scheduled = max(now, self._next_allowed.get(host, now))
            self._next_allowed[host] = scheduled + self.min_host_interval_seconds
        delay = scheduled - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
        with urlopen(request, timeout=45) as response:  # nosec B310: fixed public metadata endpoints
            status = int(getattr(response, "status", response.getcode()))
            return status, json.loads(response.read().decode("utf-8"))


def _text(value: object) -> str:
    return str(value or "").strip()


def _bool(value: object) -> bool:
    return _text(value).lower() in {"true", "1", "yes", "y"}


def _signal_count(row: dict[str, str]) -> int:
    fields = (
        "metadata_attraction_signal", "metadata_barrier_signal",
        "metadata_pollination_signal", "metadata_antagonist_signal",
    )
    return sum(_bool(row.get(field)) for field in fields)


def _article_receipt_row(candidate_id: str, receipt: ArticleSourceReceipt) -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "study_doi": receipt.study_doi,
        "provider": receipt.provider,
        "source_kind": receipt.source_kind,
        "resolution_status": receipt.resolution_status,
        "request_url": receipt.request_url,
        "landing_page_url": receipt.landing_page_url,
        "content_url": receipt.content_url,
        "content_type": receipt.content_type,
        "notes": receipt.notes,
    }


def _repository_receipt_row(candidate_id: str, receipt: RepositoryReceipt) -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "study_doi": receipt.study_doi,
        "provider": receipt.repository,
        "source_kind": "repository_metadata_candidate",
        "resolution_status": receipt.resolution_status,
        "request_url": receipt.request_url,
        "landing_page_url": receipt.landing_page_url,
        "content_url": receipt.file_url,
        "content_type": "",
        "notes": receipt.notes,
    }


def _summarize_doi(
    doi: str,
    candidate_id: str,
    fetch_json: Callable[[str], tuple[int, Any]],
) -> CandidateRouteSummary:
    article = crossref_receipts(doi, fetch_json=fetch_json)
    repository_input = {
        "queue_id": candidate_id,
        "study_id": candidate_id,
        "citation_or_doi": doi,
        "queue_status": "queued",
    }
    repositories = resolve_row(repository_input, fetch_json=fetch_json)
    receipts = [
        *(_article_receipt_row(candidate_id, item) for item in article),
        *(_repository_receipt_row(candidate_id, item) for item in repositories),
    ]
    metadata = next((item for item in article if item.source_kind == "article_metadata"), None)
    content = [item for item in article if item.source_kind == "publisher_content_link"]
    manifests = [item for item in repositories if item.resolution_status == "manifest_recovered"]
    landings = [item for item in repositories if item.resolution_status == "landing_page_only"]
    failures = [item for item in repositories if item.resolution_status == "access_failed"]
    return CandidateRouteSummary(
        doi=doi,
        crossref_metadata_status=metadata.resolution_status if metadata else "not_checked",
        crossref_content_link_count=len(content),
        crossref_pdf_link_count=sum("pdf" in _text(item.content_type).lower() for item in content),
        repository_manifest_candidate_count=len(manifests),
        repository_landing_candidate_count=len(landings),
        repository_access_failed_count=len(failures),
        receipts=tuple(receipts),
    )


def _route_lane(row: dict[str, str], summary: CandidateRouteSummary | None) -> str:
    if not normalise_doi(row.get("doi", "")):
        return "no_doi_for_endpoint_audit"
    if summary is None:
        return "endpoint_audit_not_returned"
    if summary.repository_manifest_candidate_count:
        return "verify_repository_identity_first"
    if _text(row.get("open_access_url")) or summary.crossref_content_link_count:
        return "verify_public_fulltext_access"
    if summary.repository_landing_candidate_count:
        return "verify_repository_metadata_identity"
    return "no_public_route_from_shallow_endpoints"


def _triage_score(row: dict[str, str], summary: CandidateRouteSummary | None) -> int:
    if summary is None:
        return 0
    # Accessibility/provenance leads dominate. Metadata signals are a tie-breaker,
    # never a claim about biological evidence quality.
    score = 0
    score += 100 * summary.repository_manifest_candidate_count
    score += 25 * int(bool(_text(row.get("open_access_url"))))
    score += 10 * summary.crossref_pdf_link_count
    score += 4 * summary.crossref_content_link_count
    score += 2 * summary.repository_landing_candidate_count
    score += int(_text(row.get("metadata_match_score")) or 0)
    score += _signal_count(row)
    return score


def _candidate_row(row: dict[str, str], summary: CandidateRouteSummary | None) -> dict[str, str]:
    lane = _route_lane(row, summary)
    return {
        "candidate_id": _text(row.get("candidate_id")),
        "title": _text(row.get("title")),
        "authors": _text(row.get("authors")),
        "publication_year": _text(row.get("publication_year")),
        "work_type": _text(row.get("work_type")),
        "doi": normalise_doi(row.get("doi", "")),
        "seed_routes": _text(row.get("seed_routes")),
        "seed_query_ids": _text(row.get("seed_query_ids")),
        "is_open_access": str(_bool(row.get("is_open_access"))),
        "open_access_url": _text(row.get("open_access_url")),
        "metadata_match_score": _text(row.get("metadata_match_score")),
        "metadata_attraction_signal": str(_bool(row.get("metadata_attraction_signal"))),
        "metadata_barrier_signal": str(_bool(row.get("metadata_barrier_signal"))),
        "metadata_pollination_signal": str(_bool(row.get("metadata_pollination_signal"))),
        "metadata_antagonist_signal": str(_bool(row.get("metadata_antagonist_signal"))),
        "metadata_recoverability_signal": str(_bool(row.get("metadata_recoverability_signal"))),
        "doi_status": "has_doi" if normalise_doi(row.get("doi", "")) else "missing_doi",
        "snapshot_oa_route": "candidate_present" if _text(row.get("open_access_url")) else "not_present",
        "crossref_metadata_status": summary.crossref_metadata_status if summary else "not_checked",
        "crossref_content_link_count": str(summary.crossref_content_link_count if summary else 0),
        "crossref_pdf_link_count": str(summary.crossref_pdf_link_count if summary else 0),
        "repository_manifest_candidate_count": str(summary.repository_manifest_candidate_count if summary else 0),
        "repository_landing_candidate_count": str(summary.repository_landing_candidate_count if summary else 0),
        "repository_access_failed_count": str(summary.repository_access_failed_count if summary else 0),
        "route_lane": lane,
        "triage_score": str(_triage_score(row, summary)),
        "do_not_infer": (
            "Route metadata only. Do not infer public accessibility, article-dataset identity, trait function, "
            "linked denominators, effect direction, or evidence level until the next access/provenance screen."
        ),
    }


def audit_candidates(
    candidates: list[dict[str, str]],
    *,
    fetch_json: Callable[[str], tuple[int, Any]] | None = None,
    max_workers: int = 8,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Audit unique DOI routes once, then map results back to all candidate rows."""

    if max_workers < 1:
        raise ValueError("max_workers must be positive")
    fetcher = fetch_json or HostIntervalJsonFetcher()
    doi_to_anchor: dict[str, str] = {}
    for row in candidates:
        doi = normalise_doi(row.get("doi", ""))
        if doi and doi not in doi_to_anchor:
            doi_to_anchor[doi] = _text(row.get("candidate_id"))
    summaries: dict[str, CandidateRouteSummary] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_summarize_doi, doi, anchor, fetcher): doi
            for doi, anchor in doi_to_anchor.items()
        }
        for future in as_completed(futures):
            doi = futures[future]
            try:
                summaries[doi] = future.result()
            except Exception as error:
                summaries[doi] = CandidateRouteSummary(
                    doi=doi,
                    crossref_metadata_status="audit_failed",
                    crossref_content_link_count=0,
                    crossref_pdf_link_count=0,
                    repository_manifest_candidate_count=0,
                    repository_landing_candidate_count=0,
                    repository_access_failed_count=1,
                    receipts=(
                        {
                            "candidate_id": doi_to_anchor[doi], "study_doi": doi, "provider": "audit",
                            "source_kind": "batch_route_audit", "resolution_status": "audit_failed",
                            "request_url": "", "landing_page_url": "", "content_url": "", "content_type": "",
                            "notes": f"{type(error).__name__}: {error}",
                        },
                    ),
                )
    audit_rows = [_candidate_row(row, summaries.get(normalise_doi(row.get("doi", "")))) for row in candidates]
    audit_rows.sort(key=lambda row: (-int(row["triage_score"]), -int(row["metadata_match_score"] or 0), row["title"].lower()))
    receipts: list[dict[str, str]] = []
    for doi, summary in sorted(summaries.items()):
        receipts.extend(summary.receipts)
    return audit_rows, receipts


def write_audit(
    out_dir: str | Path,
    *,
    audit_rows: Iterable[dict[str, str]],
    receipts: Iterable[dict[str, str]],
    snapshot: CandidateSnapshotReceipt,
) -> dict[str, object]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = list(audit_rows)
    source_receipts = list(receipts)
    with (output / "fixed_258_candidate_source_audit.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with (output / "fixed_258_candidate_source_receipts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECEIPT_FIELDS)
        writer.writeheader()
        writer.writerows(source_receipts)
    lanes = sorted({row["route_lane"] for row in rows})
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "fixed PR #20 M0 universe; shallow public source-route metadata only",
        "snapshot": asdict(snapshot),
        "candidate_count": len(rows),
        "doi_count": sum(row["doi_status"] == "has_doi" for row in rows),
        "receipt_count": len(source_receipts),
        "counts_by_route_lane": {lane: sum(row["route_lane"] == lane for row in rows) for lane in lanes},
        "top_manual_screen_candidates": [
            {key: row[key] for key in ("candidate_id", "title", "doi", "route_lane", "triage_score", "metadata_match_score")}
            for row in rows[:75]
        ],
        "decision_boundary": (
            "This audit ranks public access/provenance leads. It does not establish that a source is accessible, "
            "that a repository package belongs to the article, or that any study supports M1/M2/D1/D2/D3."
        ),
    }
    (output / "fixed_258_candidate_source_audit_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return report
