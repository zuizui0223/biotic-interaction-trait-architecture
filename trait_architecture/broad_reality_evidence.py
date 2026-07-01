"""Build a high-recall literature corpus for real-world evidence checks.

The corpus is intentionally broader than the strict four-path effect registry.
It supports shallow study coding and later route-specific effect synthesis, while
keeping all biological claims conditional on source verification.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


CROSSREF_WORKS_URL = "https://api.crossref.org/works"
USER_AGENT = "biotic-interaction-trait-architecture broad-reality-evidence/0.1"
ROWS_PER_QUERY_DEFAULT = 200
MAX_ROWS_PER_QUERY = 1000
REQUEST_INTERVAL_SECONDS = 0.35
MAX_RETRIES = 3
RETRYABLE_HTTP_CODES = frozenset({408, 429, 500, 502, 503, 504})

REQUIRED_QUERY_COLUMNS = frozenset({
    "query_id", "route_family", "query_text", "primary_empirical_question", "expected_contribution",
})

A_TERMS = (
    "floral trait", "flower trait", "flower colour", "flower color", "floral colour", "floral color",
    "flower size", "floral display", "flower display", "floral scent", "floral fragrance", "nectar",
    "corolla", "petal", "flower shape", "floral morphology",
)
B_TERMS = (
    "floral defence", "floral defense", "flower defence", "flower defense", "floral chemistry",
    "flower chemistry", "floral trichome", "flower trichome", "corolla toughness", "flower toughness",
    "floral volatile", "nectar alkaloid", "floral toxin", "flower barrier",
)
P_TERMS = (
    "pollination", "pollinator", "visitor", "visitation", "pollen transfer", "pollen deposition",
    "pollen receipt", "pollen removal", "pollination success",
)
H_TERMS = (
    "florivory", "floral herbivory", "flower herbivory", "floral damage", "flower damage",
    "florivore", "flower predator", "seed predation", "pre-dispersal seed predation", "nectar robber",
    "nectar robbery", "pollen thief", "pollen theft",
)
W_TERMS = (
    "fruit set", "seed set", "reproductive success", "fitness", "viable seed", "seed production",
    "fruit production", "offspring", "fecundity",
)

CANDIDATE_FIELDS = (
    "candidate_id", "doi", "title", "authors", "publication_year", "work_type", "container_title",
    "publisher", "landing_page_url", "cited_by_count", "abstract_available", "source_queries",
    "route_families", "query_rank_min", "query_rank_max", "metadata_A_signal", "metadata_B_signal",
    "metadata_P_signal", "metadata_H_signal", "metadata_W_signal", "metadata_signal_vector",
    "metadata_review_signal", "discovery_status", "metadata_warning",
)
QUERY_REPORT_FIELDS = (
    "query_id", "route_family", "query_text", "requested_rows", "works_returned", "api_total_results",
    "status", "message",
)
_last_request_at = 0.0


@dataclass
class Candidate:
    candidate_id: str
    doi: str
    title: str
    authors: str
    publication_year: str
    work_type: str
    container_title: str
    publisher: str
    landing_page_url: str
    cited_by_count: str
    abstract_available: bool
    source_queries: set[str] = field(default_factory=set)
    route_families: set[str] = field(default_factory=set)
    query_ranks: list[int] = field(default_factory=list)
    metadata_A_signal: bool = False
    metadata_B_signal: bool = False
    metadata_P_signal: bool = False
    metadata_H_signal: bool = False
    metadata_W_signal: bool = False
    metadata_review_signal: bool = False

    def to_row(self) -> dict[str, str]:
        signals = (
            self.metadata_A_signal, self.metadata_B_signal, self.metadata_P_signal,
            self.metadata_H_signal, self.metadata_W_signal,
        )
        return {
            "candidate_id": self.candidate_id,
            "doi": self.doi,
            "title": self.title,
            "authors": self.authors,
            "publication_year": self.publication_year,
            "work_type": self.work_type,
            "container_title": self.container_title,
            "publisher": self.publisher,
            "landing_page_url": self.landing_page_url,
            "cited_by_count": self.cited_by_count,
            "abstract_available": str(self.abstract_available).lower(),
            "source_queries": ";".join(sorted(self.source_queries)),
            "route_families": ";".join(sorted(self.route_families)),
            "query_rank_min": str(min(self.query_ranks)) if self.query_ranks else "",
            "query_rank_max": str(max(self.query_ranks)) if self.query_ranks else "",
            "metadata_A_signal": str(self.metadata_A_signal).lower(),
            "metadata_B_signal": str(self.metadata_B_signal).lower(),
            "metadata_P_signal": str(self.metadata_P_signal).lower(),
            "metadata_H_signal": str(self.metadata_H_signal).lower(),
            "metadata_W_signal": str(self.metadata_W_signal).lower(),
            "metadata_signal_vector": "".join("1" if value else "0" for value in signals),
            "metadata_review_signal": str(self.metadata_review_signal).lower(),
            "discovery_status": "broad_candidate_needs_shallow_screening",
            "metadata_warning": (
                "Crossref metadata and query-route membership are discovery signals only; they do not establish measured traits, "
                "outcomes, causal effects, shared units, or model support."
            ),
        }


def _text(value: object) -> str:
    if isinstance(value, list):
        return " ".join(_text(item) for item in value)
    return str(value or "").strip()


def _plain_text(value: object) -> str:
    text = html.unescape(_text(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _lower_text(*values: object) -> str:
    return " ".join(_plain_text(value) for value in values).lower()


def _has_term(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def _normalise_doi(value: object) -> str:
    doi = _text(value).lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi.rstrip(" /.")


def _year(item: dict[str, Any]) -> str:
    for field in ("published-print", "published-online", "issued", "created"):
        value = item.get(field)
        if not isinstance(value, dict):
            continue
        date_parts = value.get("date-parts")
        if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list) and date_parts[0]:
            return _text(date_parts[0][0])
    return ""


def _authors(item: dict[str, Any]) -> str:
    names: list[str] = []
    for author in item.get("author", []) or []:
        if not isinstance(author, dict):
            continue
        name = " ".join(part for part in (_text(author.get("given")), _text(author.get("family"))) if part)
        if name:
            names.append(name)
        if len(names) >= 6:
            break
    return "; ".join(names)


def _candidate_id(doi: str, title: str, year: str) -> str:
    if doi:
        return f"doi:{doi}"
    digest = hashlib.sha256(f"{title.lower()}|{year}".encode("utf-8")).hexdigest()[:16]
    return f"crossref-title:{digest}"


def _request_json(url: str, params: dict[str, str]) -> dict[str, Any]:
    global _last_request_at
    for attempt in range(MAX_RETRIES + 1):
        wait = REQUEST_INTERVAL_SECONDS - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)
        request = Request(
            f"{url}?{urlencode(params)}",
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        )
        try:
            with urlopen(request, timeout=90) as response:  # nosec B310: public bibliographic endpoint
                _last_request_at = time.monotonic()
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Crossref response is not a JSON object")
            return payload
        except HTTPError as error:
            _last_request_at = time.monotonic()
            if error.code not in RETRYABLE_HTTP_CODES or attempt >= MAX_RETRIES:
                raise
            time.sleep(max(REQUEST_INTERVAL_SECONDS, 2.0 ** attempt))
        except URLError:
            _last_request_at = time.monotonic()
            if attempt >= MAX_RETRIES:
                raise
            time.sleep(max(REQUEST_INTERVAL_SECONDS, 2.0 ** attempt))
    raise RuntimeError("unreachable retry loop termination")


def read_query_registry(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [{key: _text(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    if not rows:
        raise ValueError("broad evidence query registry is empty")
    missing = REQUIRED_QUERY_COLUMNS.difference(rows[0])
    if missing:
        raise ValueError(f"query registry missing columns: {', '.join(sorted(missing))}")
    query_ids = [row["query_id"] for row in rows]
    if len(query_ids) != len(set(query_ids)):
        raise ValueError("query IDs must be unique")
    if any(not row["query_text"] or not row["route_family"] for row in rows):
        raise ValueError("each query needs route_family and query_text")
    return rows


def candidate_from_crossref_item(item: dict[str, Any], query: dict[str, str], rank: int) -> Candidate:
    doi = _normalise_doi(item.get("DOI"))
    title = _plain_text(item.get("title"))
    year = _year(item)
    abstract = _plain_text(item.get("abstract"))
    search_text = _lower_text(title, abstract)
    candidate = Candidate(
        candidate_id=_candidate_id(doi, title, year),
        doi=doi,
        title=title,
        authors=_authors(item),
        publication_year=year,
        work_type=_text(item.get("type")),
        container_title=_plain_text(item.get("container-title")),
        publisher=_plain_text(item.get("publisher")),
        landing_page_url=_text(item.get("URL")),
        cited_by_count=_text(item.get("is-referenced-by-count")),
        abstract_available=bool(abstract),
        source_queries={query["query_id"]},
        route_families={query["route_family"]},
        query_ranks=[rank],
        metadata_A_signal=_has_term(search_text, A_TERMS),
        metadata_B_signal=_has_term(search_text, B_TERMS),
        metadata_P_signal=_has_term(search_text, P_TERMS),
        metadata_H_signal=_has_term(search_text, H_TERMS),
        metadata_W_signal=_has_term(search_text, W_TERMS),
        metadata_review_signal=any(token in search_text for token in ("review", "meta-analysis", "meta analysis")),
    )
    return candidate


def merge_candidate(existing: Candidate, incoming: Candidate) -> Candidate:
    existing.source_queries.update(incoming.source_queries)
    existing.route_families.update(incoming.route_families)
    existing.query_ranks.extend(incoming.query_ranks)
    existing.metadata_A_signal = existing.metadata_A_signal or incoming.metadata_A_signal
    existing.metadata_B_signal = existing.metadata_B_signal or incoming.metadata_B_signal
    existing.metadata_P_signal = existing.metadata_P_signal or incoming.metadata_P_signal
    existing.metadata_H_signal = existing.metadata_H_signal or incoming.metadata_H_signal
    existing.metadata_W_signal = existing.metadata_W_signal or incoming.metadata_W_signal
    existing.metadata_review_signal = existing.metadata_review_signal or incoming.metadata_review_signal
    existing.abstract_available = existing.abstract_available or incoming.abstract_available
    for attribute in ("title", "authors", "publication_year", "work_type", "container_title", "publisher", "landing_page_url", "cited_by_count"):
        if not getattr(existing, attribute) and getattr(incoming, attribute):
            setattr(existing, attribute, getattr(incoming, attribute))
    return existing


def harvest_crossref(
    queries: Iterable[dict[str, str]],
    *,
    rows_per_query: int = ROWS_PER_QUERY_DEFAULT,
    request_json: Callable[[str, dict[str, str]], dict[str, Any]] = _request_json,
) -> tuple[list[Candidate], list[dict[str, str]]]:
    """Run high-recall Crossref bibliographic queries and deduplicate by DOI/title key."""

    if not 1 <= rows_per_query <= MAX_ROWS_PER_QUERY:
        raise ValueError(f"rows_per_query must be between 1 and {MAX_ROWS_PER_QUERY}")
    candidates: dict[str, Candidate] = {}
    reports: list[dict[str, str]] = []
    for query in queries:
        try:
            payload = request_json(
                CROSSREF_WORKS_URL,
                {
                    "query.bibliographic": query["query_text"],
                    "filter": "type:journal-article",
                    "sort": "score",
                    "order": "desc",
                    "rows": str(rows_per_query),
                },
            )
            message = payload.get("message")
            if not isinstance(message, dict):
                raise ValueError("Crossref response lacks message object")
            items = message.get("items")
            if not isinstance(items, list):
                raise ValueError("Crossref response lacks items list")
            for rank, item in enumerate(items, start=1):
                if not isinstance(item, dict):
                    continue
                candidate = candidate_from_crossref_item(item, query, rank)
                if not candidate.title:
                    continue
                if candidate.candidate_id in candidates:
                    merge_candidate(candidates[candidate.candidate_id], candidate)
                else:
                    candidates[candidate.candidate_id] = candidate
            reports.append({
                "query_id": query["query_id"],
                "route_family": query["route_family"],
                "query_text": query["query_text"],
                "requested_rows": str(rows_per_query),
                "works_returned": str(len(items)),
                "api_total_results": _text(message.get("total-results")),
                "status": "success",
                "message": "",
            })
        except Exception as error:
            reports.append({
                "query_id": query["query_id"],
                "route_family": query["route_family"],
                "query_text": query["query_text"],
                "requested_rows": str(rows_per_query),
                "works_returned": "",
                "api_total_results": "",
                "status": "query_failed",
                "message": str(error),
            })
    failed = [row["query_id"] for row in reports if row["status"] != "success"]
    if failed:
        raise RuntimeError("Crossref broad corpus retrieval incomplete: " + ", ".join(failed))
    return sorted(candidates.values(), key=lambda item: (item.title.lower(), item.doi)), reports


def summary(candidates: Iterable[Candidate], reports: Iterable[dict[str, str]]) -> dict[str, object]:
    candidates = list(candidates)
    reports = list(reports)
    vectors = Counter(
        "".join(
            "1" if signal else "0"
            for signal in (
                item.metadata_A_signal, item.metadata_B_signal, item.metadata_P_signal,
                item.metadata_H_signal, item.metadata_W_signal,
            )
        )
        for item in candidates
    )
    return {
        "corpus_version": "broad_reality_evidence_v2_crossref_seed",
        "source": "Crossref REST API",
        "query_count": len(reports),
        "raw_returned_records": sum(int(row["works_returned"] or 0) for row in reports),
        "unique_candidate_count": len(candidates),
        "route_family_counts": dict(sorted(Counter(route for item in candidates for route in item.route_families).items())),
        "metadata_signal_counts": {
            "A": sum(item.metadata_A_signal for item in candidates),
            "B": sum(item.metadata_B_signal for item in candidates),
            "P": sum(item.metadata_P_signal for item in candidates),
            "H": sum(item.metadata_H_signal for item in candidates),
            "W": sum(item.metadata_W_signal for item in candidates),
        },
        "metadata_signal_vector_counts": dict(sorted(vectors.items())),
        "abstract_available_count": sum(item.abstract_available for item in candidates),
        "review_language_signal_count": sum(item.metadata_review_signal for item in candidates),
        "interpretation_boundary": (
            "This is a high-recall bibliographic corpus. Query membership and title/abstract signals are not evidence that a study measured "
            "a floral trait or outcome, and they are not effect directions, effect sizes, causal claims, or model calibration values."
        ),
    }


def write_outputs(
    out_dir: str | Path,
    candidates: Iterable[Candidate],
    reports: Iterable[dict[str, str]],
) -> None:
    candidates = list(candidates)
    reports = list(reports)
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / "broad_reality_evidence_candidates.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS)
        writer.writeheader()
        writer.writerows(item.to_row() for item in candidates)
    with (destination / "broad_reality_evidence_query_report.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUERY_REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(reports)
    (destination / "broad_reality_evidence_summary.json").write_text(
        json.dumps(summary(candidates, reports), indent=2, sort_keys=True),
        encoding="utf-8",
    )
