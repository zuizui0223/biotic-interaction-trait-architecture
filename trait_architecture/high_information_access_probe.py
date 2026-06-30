"""Verify shallow access routes after the fixed-universe metadata audit.

This is the second, still non-semantic stage of the screening pipeline. It
operates on the 258-row audit produced in the same workflow and:

* probes at most three public article-content URLs per high-information empirical
  candidate using a small byte range;
* separately resolves exact record metadata for repository-manifest candidates;
* keeps PDF/HTML reachability distinct from article-dataset identity; and
* writes only access headers, signatures, and relation metadata.

It does not parse articles, inspect tables, download supplements/data archives,
assign trait functions, or estimate effects.
"""

from __future__ import annotations

import csv
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.error import HTTPError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from .public_article_source_scout import normalise_doi


USER_AGENT = "biotic-interaction-trait-architecture high-information-access-probe/0.1"
MAX_PREFIX_BYTES = 8192
MAX_CONTENT_URLS_PER_CANDIDATE = 3
ALLOWED_DATA_RELATIONS = frozenset({"issupplementto", "isderivedfrom", "ispartof"})
ACCESS_FIELDS = (
    "candidate_id", "study_doi", "source_label", "source_url", "final_url",
    "access_status", "http_status", "content_type", "prefix_signature", "notes",
)
IDENTITY_FIELDS = (
    "candidate_id", "study_doi", "provider", "candidate_locator", "request_url",
    "identity_status", "relation_type", "notes",
)
CANDIDATE_FIELDS = (
    "candidate_id", "title", "doi", "metadata_signal_count", "triage_cohort",
    "content_url_count", "public_pdf_prefix_count", "public_html_prefix_count",
    "access_denied_count", "repository_manifest_candidate_count", "repository_identity_verified_count",
    "next_lane", "do_not_infer",
)


@dataclass(frozen=True)
class AccessReceipt:
    candidate_id: str
    study_doi: str
    source_label: str
    source_url: str
    final_url: str
    access_status: str
    http_status: str
    content_type: str
    prefix_signature: str
    notes: str


@dataclass(frozen=True)
class RepositoryIdentityReceipt:
    candidate_id: str
    study_doi: str
    provider: str
    candidate_locator: str
    request_url: str
    identity_status: str
    relation_type: str
    notes: str


class HostIntervalFetcher:
    """Thread-safe shallow GET fetcher with a minimum interval per host."""

    def __init__(self, min_host_interval_seconds: float = 0.35):
        if min_host_interval_seconds <= 0:
            raise ValueError("min_host_interval_seconds must be positive")
        self.min_host_interval_seconds = min_host_interval_seconds
        self._lock = threading.Lock()
        self._next_allowed: dict[str, float] = {}

    def _wait(self, url: str) -> None:
        host = urlparse(url).netloc or "unknown"
        with self._lock:
            now = time.monotonic()
            scheduled = max(now, self._next_allowed.get(host, now))
            self._next_allowed[host] = scheduled + self.min_host_interval_seconds
        wait = scheduled - time.monotonic()
        if wait > 0:
            time.sleep(wait)

    def prefix(self, url: str) -> tuple[int, str, str, bytes]:
        self._wait(url)
        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/pdf,text/html,application/xhtml+xml,*/*",
                "Range": f"bytes=0-{MAX_PREFIX_BYTES - 1}",
            },
        )
        with urlopen(request, timeout=45) as response:  # nosec B310: source route is predeclared from prior metadata audit
            status = int(getattr(response, "status", response.getcode()))
            return status, response.geturl(), str(response.headers.get("Content-Type") or "").lower(), response.read(MAX_PREFIX_BYTES)

    def json(self, url: str) -> tuple[int, Any]:
        self._wait(url)
        request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
        with urlopen(request, timeout=45) as response:  # nosec B310: exact public repository metadata endpoint
            status = int(getattr(response, "status", response.getcode()))
            return status, json.loads(response.read().decode("utf-8"))


def _text(value: object) -> str:
    return str(value or "").strip()


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return [{key: _text(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def _is_pdf(content_type: str, prefix: bytes) -> bool:
    return prefix.startswith(b"%PDF") or "application/pdf" in content_type


def _is_html(content_type: str, prefix: bytes) -> bool:
    lowered = prefix.lstrip().lower()
    return "html" in content_type or lowered.startswith((b"<!doctype html", b"<html", b"<head"))


def probe_content_url(
    *,
    candidate_id: str,
    study_doi: str,
    source_label: str,
    source_url: str,
    fetch_prefix: Callable[[str], tuple[int, str, str, bytes]],
) -> AccessReceipt:
    try:
        status, final_url, content_type, prefix = fetch_prefix(source_url)
        signature = prefix[:4].decode("latin1", errors="replace")
        if _is_pdf(content_type, prefix):
            access_status = "public_pdf_prefix_recovered"
            notes = "Unauthenticated small response is PDF-like; title/page identity remains for the next screen."
        elif _is_html(content_type, prefix):
            access_status = "public_html_prefix_recovered"
            notes = "Unauthenticated HTML is reachable; it may still be a landing page or paywall."
        else:
            access_status = "non_article_content_returned"
            notes = "Endpoint responded but first bytes were neither PDF-like nor HTML-like."
        return AccessReceipt(
            candidate_id=candidate_id, study_doi=study_doi, source_label=source_label,
            source_url=source_url, final_url=final_url, access_status=access_status,
            http_status=str(status), content_type=content_type, prefix_signature=signature, notes=notes,
        )
    except HTTPError as error:
        status = "access_denied_or_required" if error.code in {401, 403, 429} else "http_error"
        return AccessReceipt(
            candidate_id=candidate_id, study_doi=study_doi, source_label=source_label,
            source_url=source_url, final_url="", access_status=status, http_status=str(error.code),
            content_type="", prefix_signature="", notes=f"HTTPError: {error}",
        )
    except Exception as error:
        return AccessReceipt(
            candidate_id=candidate_id, study_doi=study_doi, source_label=source_label,
            source_url=source_url, final_url="", access_status="access_failed", http_status="",
            content_type="", prefix_signature="", notes=f"{type(error).__name__}: {error}",
        )


def _article_urls(row: dict[str, str], receipts: Iterable[dict[str, str]]) -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = []
    oa_url = _text(row.get("open_access_url"))
    if oa_url:
        urls.append(("snapshot_open_access_url", oa_url))
    crossref = [
        receipt for receipt in receipts
        if receipt.get("source_kind") == "publisher_content_link" and _text(receipt.get("content_url"))
    ]
    crossref.sort(key=lambda item: ("pdf" not in _text(item.get("content_type")).lower(), _text(item.get("content_url"))))
    urls.extend(("crossref_publisher_content", _text(item["content_url"])) for item in crossref)
    selected: list[tuple[str, str]] = []
    seen: set[str] = set()
    for label, url in urls:
        if url not in seen:
            selected.append((label, url))
            seen.add(url)
        if len(selected) >= MAX_CONTENT_URLS_PER_CANDIDATE:
            break
    return selected


def _allowed_relation(value: object) -> str:
    relation = _text(value)
    return relation if relation.lower() in ALLOWED_DATA_RELATIONS else ""


def _related_identifier_relation(identifiers: object, article_doi: str) -> str:
    if not isinstance(identifiers, list):
        return ""
    for item in identifiers:
        if not isinstance(item, dict):
            continue
        value = normalise_doi(item.get("identifier") or item.get("related_identifier") or item.get("relatedIdentifier"))
        if value == article_doi:
            relation = _allowed_relation(item.get("relation") or item.get("relation_type") or item.get("relationType"))
            if relation:
                return relation
    return ""


def _zenodo_record_id(receipt: dict[str, str]) -> str:
    for field in ("content_url", "landing_page_url", "request_url"):
        match = re.search(r"/records/(\d+)", _text(receipt.get(field)))
        if match:
            return match.group(1)
    return ""


def verify_repository_identity(
    receipt: dict[str, str],
    *,
    fetch_json: Callable[[str], tuple[int, Any]],
) -> RepositoryIdentityReceipt:
    candidate_id = _text(receipt.get("candidate_id"))
    article_doi = normalise_doi(receipt.get("study_doi", ""))
    provider = _text(receipt.get("provider"))
    if provider == "Zenodo":
        record_id = _zenodo_record_id(receipt)
        if not record_id:
            return RepositoryIdentityReceipt(candidate_id, article_doi, provider, "", "", "unresolved_missing_record_id", "", "Zenodo receipt had no parseable record ID.")
        request_url = f"https://zenodo.org/api/records/{record_id}"
        try:
            status, payload = fetch_json(request_url)
            if status >= 400 or not isinstance(payload, dict):
                raise RuntimeError(f"HTTP {status}")
            metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
            relation = _related_identifier_relation(metadata.get("related_identifiers"), article_doi)
            if relation:
                return RepositoryIdentityReceipt(candidate_id, article_doi, provider, record_id, request_url, "exact_article_relation_verified", relation, "Exact DOI appears in an allowed Zenodo relation; file content remains uninspected.")
            return RepositoryIdentityReceipt(candidate_id, article_doi, provider, record_id, request_url, "article_relation_not_verified", "", "Record metadata did not show the focal DOI under an allowed data relation.")
        except Exception as error:
            return RepositoryIdentityReceipt(candidate_id, article_doi, provider, record_id, request_url, "identity_access_failed", "", f"{type(error).__name__}: {error}")
    if provider == "DataCite":
        match = re.search(r"doi\.org/(10\.[^\s/]+/.+)$", _text(receipt.get("landing_page_url")), flags=re.I)
        dataset_doi = normalise_doi(match.group(1)) if match else ""
        if not dataset_doi:
            return RepositoryIdentityReceipt(candidate_id, article_doi, provider, "", "", "unresolved_missing_dataset_doi", "", "DataCite receipt had no parseable candidate DOI.")
        request_url = f"https://api.datacite.org/dois/{quote(dataset_doi, safe='')}"
        try:
            status, payload = fetch_json(request_url)
            if status >= 400 or not isinstance(payload, dict):
                raise RuntimeError(f"HTTP {status}")
            data = payload.get("data")
            attrs = data.get("attributes") if isinstance(data, dict) and isinstance(data.get("attributes"), dict) else {}
            relation = _related_identifier_relation(attrs.get("relatedIdentifiers"), article_doi)
            if relation:
                return RepositoryIdentityReceipt(candidate_id, article_doi, provider, dataset_doi, request_url, "exact_article_relation_verified", relation, "Exact DOI appears in an allowed DataCite relation; file content remains uninspected.")
            return RepositoryIdentityReceipt(candidate_id, article_doi, provider, dataset_doi, request_url, "article_relation_not_verified", "", "DataCite metadata did not show the focal DOI under an allowed data relation.")
        except Exception as error:
            return RepositoryIdentityReceipt(candidate_id, article_doi, provider, dataset_doi, request_url, "identity_access_failed", "", f"{type(error).__name__}: {error}")
    return RepositoryIdentityReceipt(candidate_id, article_doi, provider, "", "", "unresolved_provider_or_locator", "", "No exact record-identity verifier is implemented for this receipt type.")


def _candidate_summary(row: dict[str, str], accesses: list[AccessReceipt], identities: list[RepositoryIdentityReceipt]) -> dict[str, str]:
    pdf = sum(item.access_status == "public_pdf_prefix_recovered" for item in accesses)
    html = sum(item.access_status == "public_html_prefix_recovered" for item in accesses)
    denied = sum(item.access_status == "access_denied_or_required" for item in accesses)
    verified = sum(item.identity_status == "exact_article_relation_verified" for item in identities)
    if pdf:
        lane = "bounded_fulltext_screen_pdf_candidate"
    elif html:
        lane = "verify_html_article_identity_before_text_screen"
    elif verified:
        lane = "repository_identity_verified_content_screen_pending"
    else:
        lane = "no_public_content_verified"
    return {
        "candidate_id": _text(row.get("candidate_id")),
        "title": _text(row.get("title")),
        "doi": normalise_doi(row.get("doi", "")),
        "metadata_signal_count": _text(row.get("metadata_signal_count")),
        "triage_cohort": _text(row.get("triage_cohort")),
        "content_url_count": str(len(accesses)),
        "public_pdf_prefix_count": str(pdf),
        "public_html_prefix_count": str(html),
        "access_denied_count": str(denied),
        "repository_manifest_candidate_count": str(len(identities)),
        "repository_identity_verified_count": str(verified),
        "next_lane": lane,
        "do_not_infer": "Access and record-relation checks only. Do not infer article table content, trait roles, denominators, linked units, effect values, or evidence level.",
    }


def run_access_probe(
    audit_rows: list[dict[str, str]],
    source_receipts: list[dict[str, str]],
    *,
    fetcher: HostIntervalFetcher | None = None,
    max_workers: int = 6,
) -> tuple[list[dict[str, str]], list[AccessReceipt], list[RepositoryIdentityReceipt], dict[str, object]]:
    if max_workers < 1:
        raise ValueError("max_workers must be positive")
    runtime = fetcher or HostIntervalFetcher()
    receipts_by_candidate: dict[str, list[dict[str, str]]] = {}
    for receipt in source_receipts:
        receipts_by_candidate.setdefault(_text(receipt.get("candidate_id")), []).append(receipt)
    high = [row for row in audit_rows if row.get("triage_cohort") == "high_information_empirical_candidate"]
    repository = [
        receipt for receipt in source_receipts
        if receipt.get("source_kind") == "repository_metadata_candidate"
        and receipt.get("resolution_status") == "manifest_recovered"
    ]
    jobs: list[tuple[dict[str, str], str, str]] = []
    for row in high:
        for label, url in _article_urls(row, receipts_by_candidate.get(_text(row.get("candidate_id")), [])):
            jobs.append((row, label, url))
    access: list[AccessReceipt] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(probe_content_url, candidate_id=_text(row["candidate_id"]), study_doi=normalise_doi(row.get("doi", "")), source_label=label, source_url=url, fetch_prefix=runtime.prefix): _text(row["candidate_id"])
            for row, label, url in jobs
        }
        for future in as_completed(futures):
            access.append(future.result())
    identities: list[RepositoryIdentityReceipt] = []
    unique_repository: dict[tuple[str, str, str], dict[str, str]] = {}
    for receipt in repository:
        key = (_text(receipt.get("candidate_id")), _text(receipt.get("provider")), _zenodo_record_id(receipt) or _text(receipt.get("landing_page_url")))
        unique_repository.setdefault(key, receipt)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(verify_repository_identity, receipt, fetch_json=runtime.json) for receipt in unique_repository.values()]
        for future in as_completed(futures):
            identities.append(future.result())
    access_by_candidate: dict[str, list[AccessReceipt]] = {}
    for receipt in access:
        access_by_candidate.setdefault(receipt.candidate_id, []).append(receipt)
    identities_by_candidate: dict[str, list[RepositoryIdentityReceipt]] = {}
    for receipt in identities:
        identities_by_candidate.setdefault(receipt.candidate_id, []).append(receipt)
    summary = [
        _candidate_summary(row, access_by_candidate.get(_text(row["candidate_id"]), []), identities_by_candidate.get(_text(row["candidate_id"]), []))
        for row in high
    ]
    summary.sort(key=lambda row: (row["next_lane"], row["title"].lower()))
    lanes = sorted({row["next_lane"] for row in summary})
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "high-information empirical content routes plus manifest-bearing repository candidates from fixed 258-source audit",
        "high_information_candidate_count": len(high),
        "content_url_probe_count": len(access),
        "repository_identity_probe_count": len(identities),
        "counts_by_next_lane": {lane: sum(row["next_lane"] == lane for row in summary) for lane in lanes},
        "public_pdf_prefix_candidates": [row for row in summary if row["next_lane"] == "bounded_fulltext_screen_pdf_candidate"],
        "decision_boundary": "A PDF prefix confirms only unauthenticated byte-level reachability. A repository relation confirms only metadata provenance. Neither result establishes article contents or empirical evidence.",
    }
    return summary, access, identities, report


def write_access_probe(
    out_dir: str | Path,
    summaries: Iterable[dict[str, str]],
    access: Iterable[AccessReceipt],
    identities: Iterable[RepositoryIdentityReceipt],
    report: dict[str, object],
) -> None:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "high_information_candidate_access_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS)
        writer.writeheader()
        writer.writerows(summaries)
    with (output / "high_information_candidate_access_receipts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ACCESS_FIELDS)
        writer.writeheader()
        for item in access:
            writer.writerow(asdict(item))
    with (output / "repository_identity_receipts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=IDENTITY_FIELDS)
        writer.writeheader()
        for item in identities:
            writer.writerow(asdict(item))
    (output / "high_information_candidate_access_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")